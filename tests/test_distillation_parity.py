"""CPU contract checks, not simulator or recurrent-training equivalence tests.

Run with: .venv/bin/python -m unittest tests.test_distillation_parity -v
The shared feed-forward network isolates differences in the agents' algorithms.
"""

import copy
from types import SimpleNamespace
import unittest

import torch
from lightning.fabric import Fabric
from tensordict import TensorDict
from torch import nn

from protomotions.agents.common.supervision import SupervisionLossConfig
from protomotions.agents.common.config import MLPWithConcatConfig, MLPLayerConfig
from protomotions.agents.ppo.config import PPOActorConfig
from protomotions.agents.ppo.model import PPOActor
from protomotions.agents.supervised.agent import SupervisedAgent
from protomotions.agents.supervised.config import RolloutActor
from protomotions.agents.utils.data import ExperienceBuffer
from rsl_rl.algorithms import Distillation
from rsl_rl.models import MLPModel
from rsl_rl.storage import RolloutStorage


class StudentAdapter(nn.Module):
    def __init__(self, network):
        super().__init__()
        self.network = network

    def forward(self, td):
        td['action'] = self.network(td)
        return td

    def compute_model_loss(self, td, *, zero_loss, **kwargs):
        return zero_loss * 0, {}


class TeacherAdapter(nn.Module):
    in_keys = ['obs']

    def __init__(self, network):
        super().__init__()
        self.network = network

    def forward(self, td):
        mean = self.network(TensorDict({'expert_obs': td['obs']}, td.batch_size))
        td['mean_action'] = mean
        # Distinct sampled output verifies ProtoMotions prefers the mean label.
        td['action'] = mean + 100
        return td


def make_pair(steps=4, gradient_length=1):
    torch.manual_seed(13)
    observations = [
        TensorDict({'obs': torch.randn(4, 3), 'expert_obs': torch.randn(4, 3)}, [4])
        for _ in range(steps)
    ]
    groups = {'student': ['obs'], 'teacher': ['expert_obs']}
    student = MLPModel(observations[0], groups, 'student', 2, hidden_dims=[8], obs_normalization=False)
    teacher = MLPModel(observations[0], groups, 'teacher', 2, hidden_dims=[8], obs_normalization=False)
    rsl = Distillation(student, teacher,
        RolloutStorage('distillation', 4, steps, observations[0], [2]),
        gradient_length=gradient_length, num_learning_epochs=1, learning_rate=0.001)
    rsl.train_mode()

    # Isolate learner methods from simulator/evaluator initialization.
    proto = SupervisedAgent.__new__(SupervisedAgent)
    proto.device = torch.device('cpu')
    proto.current_epoch = 0
    proto.num_envs, proto.num_steps, proto.num_mini_epochs = 4, steps, 1
    proto.config = SimpleNamespace(
        rollout_actor=RolloutActor.STUDENT,
        loss=SupervisionLossConfig(prediction_key='action', target_key='expert_actions'),
        check_grad_mag=True, fail_on_bad_grads=True, gradient_clip_val=0,
        batch_size=4,
    )
    proto.model = StudentAdapter(copy.deepcopy(student))
    proto.expert_model = TeacherAdapter(copy.deepcopy(teacher)).eval().requires_grad_(False)
    proto.expert_actor = proto.expert_model
    proto.expert_actor_in_keys = ['obs']
    proto.fabric = Fabric(accelerator='cpu', devices=1)
    proto.training_model, proto.supervised_optimizer = proto.fabric.setup(
        proto.model, torch.optim.Adam(proto.model.parameters(), lr=0.001))
    proto.model_output_keys = ['action']
    proto.experience_buffer = ExperienceBuffer(4, steps, 'cpu')
    for key, shape in [('obs', (3,)), ('expert_obs', (3,)), ('action', (2,)), ('expert_actions', (2,))]:
        proto.experience_buffer.register_key(key, shape)
    return proto, rsl, observations


def collect(proto, rsl, observations):
    batches = []
    proto.eval()
    with torch.no_grad():
        for step, obs in enumerate(observations):
            output = proto.collect_rollout_step(obs.clone(), step)
            for key in ['obs', 'expert_obs']:
                proto.experience_buffer.update_data(key, step, obs[key])
            rsl_actions = rsl.act(obs.clone())
            torch.testing.assert_close(output['action'], rsl_actions)
            torch.testing.assert_close(output['expert_actions'], rsl.transition.privileged_actions)
            batches.append(output.clone().to_dict())
            rsl.process_env_step(obs, torch.zeros(4), torch.zeros(4), {})
    return batches


class DistillationParityTests(unittest.TestCase):
    def test_gaussian_student_requires_mean_action_supervision(self):
        proto, rsl, observations = make_pair()
        proto.model = PPOActor(PPOActorConfig(
            in_keys=['obs'], num_out=2, mu_key='action_mean',
            mu_model=MLPWithConcatConfig(
                in_keys=['obs'], out_keys=['action_mean'], num_out=2,
                normalize_obs=False, layers=[MLPLayerConfig(units=8, activation='relu')],
            ),
        ))
        proto.training_model = proto.model
        with torch.no_grad():
            target = rsl.teacher(observations[0]).detach()
        batch = observations[0].to_dict() | {'action': torch.zeros(4, 2), 'expert_actions': target}
        # Real Gaussian actor: dist.sample() does not provide a path to its mean.
        proto.config.loss.prediction_key = 'action'
        sampled_loss, _ = proto.supervised_step(batch)
        self.assertFalse(sampled_loss.requires_grad)
        proto.config.loss.prediction_key = 'mean_action'
        mean_loss, _ = proto.supervised_step(batch)
        self.assertTrue(mean_loss.requires_grad)
        mean_loss.backward()
        self.assertTrue(any(p.grad is not None and p.grad.abs().sum() > 0 for p in proto.model.mu.parameters()))

    def test_matching_rollout_labels_and_mse_gradients(self):
        proto, rsl, observations = make_pair()
        batches = collect(proto, rsl, observations)
        loss, _ = proto.supervised_step(batches[0])
        expected = rsl.loss_fn(rsl.student(observations[0]), batches[0]['expert_actions'])
        torch.testing.assert_close(loss, expected)
        loss.backward()
        expected.backward()
        for left, right in zip(proto.model.network.parameters(), rsl.student.parameters()):
            torch.testing.assert_close(left.grad, right.grad)
        self.assertTrue(all(p.grad is None for p in proto.expert_model.parameters()))
        self.assertTrue(all(p.grad is None for p in rsl.teacher.parameters()))

    def test_matched_adam_updates_and_learning(self):
        proto, rsl, observations = make_pair()
        teacher_before = copy.deepcopy(rsl.teacher.state_dict())
        proto_teacher_before = copy.deepcopy(proto.expert_model.state_dict())
        with torch.no_grad():
            initial = sum(rsl.loss_fn(rsl.student(o), rsl.teacher(o)).item() for o in observations)
        for _ in range(8):
            batches = collect(proto, rsl, observations)
            rsl.update()
            proto.train()
            # Match RSL's temporal batches and gradient_length=1 explicitly.
            for index, batch in enumerate(batches):
                proto.perform_optimization_step(batch, index)
            for left, right in zip(proto.model.network.parameters(), rsl.student.parameters()):
                torch.testing.assert_close(left, right, atol=1e-6, rtol=1e-5)
        with torch.no_grad():
            final = sum(rsl.loss_fn(rsl.student(o), rsl.teacher(o)).item() for o in observations)
        self.assertLess(final, initial)
        for key, value in teacher_before.items():
            torch.testing.assert_close(value, rsl.teacher.state_dict()[key], atol=0, rtol=0)
        for key, value in proto_teacher_before.items():
            torch.testing.assert_close(value, proto.expert_model.state_dict()[key], atol=0, rtol=0)

    def test_expert_rollout_is_an_explicit_different_mode(self):
        proto, rsl, observations = make_pair()
        proto.config.rollout_actor = RolloutActor.EXPERT
        with torch.no_grad():
            output = proto.collect_rollout_step(observations[0].clone(), 0)
            torch.testing.assert_close(output['action'], rsl.teacher(observations[0]))
            self.assertFalse(torch.allclose(output['action'], rsl.student(observations[0])))

    def test_native_update_schedules_differ(self):
        proto, rsl, observations = make_pair(gradient_length=2)
        collect(proto, rsl, observations)
        counts = {'proto': 0, 'rsl': 0}
        def counter(name, original):
            def step(*args, **kwargs):
                counts[name] += 1
                return original(*args, **kwargs)
            return step
        proto.supervised_optimizer.step = counter('proto', proto.supervised_optimizer.step)
        rsl.optimizer.step = counter('rsl', rsl.optimizer.step)
        proto.optimize_model()
        rsl.update()
        self.assertEqual(counts, {'proto': 4, 'rsl': 2})


if __name__ == '__main__':
    unittest.main()

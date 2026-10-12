"""Small G1 motion-tracking PPO experiment composed from ProtoMotions components.

This is a fresh-training plumbing check, not the pretrained BONES tracker.
See experiments/README.md for the bounded Newton command.
"""

from protomotions.agents.common.config import MLPWithConcatConfig, MLPLayerConfig
from protomotions.agents.evaluators.config import EvaluatorConfig
from protomotions.agents.ppo.config import PPOActorConfig, PPOAgentConfig, PPOModelConfig
from protomotions.components.motion_lib import MotionLibConfig
from protomotions.components.scene_lib import SceneLibConfig
from protomotions.components.terrains.config import TerrainConfig
from protomotions.envs.action import make_pd_action_config
from protomotions.envs.base_env.config import EnvConfig
from protomotions.envs.component_factories import (
    max_coords_obs_factory,
    mimic_target_poses_max_coords_factory,
    mimic_tracking_rewards_factory,
    tracking_error_term_factory,
)
from protomotions.envs.control.mimic_control import MimicControlConfig
from protomotions.envs.motion_manager.config import MimicMotionManagerConfig
from protolab.robots.g1 import configure_upstream_g1_for_protolab


def configure_robot_and_simulator(robot_cfg, simulator_cfg, args):
    if args.robot_name != "g1" or args.simulator != "newton":
        raise ValueError("This smoke experiment supports --robot-name g1 --simulator newton only")
    configure_upstream_g1_for_protolab(robot_cfg)


def terrain_config(args):
    # A single flat tile avoids generating the default large terrain grid.
    return TerrainConfig(num_levels=1, num_terrains=1, border_size=5.0)


def scene_lib_config(args):
    return SceneLibConfig()


def motion_lib_config(args):
    return MotionLibConfig(motion_file=args.motion_file)


def env_config(robot_cfg, args):
    return EnvConfig(
        max_episode_length=128,
        control_components={"mimic": MimicControlConfig()},
        observation_components={
            "body_state": max_coords_obs_factory(),
            "reference_pose": mimic_target_poses_max_coords_factory(with_velocities=True),
        },
        reward_components=mimic_tracking_rewards_factory(gt_coef=-25.0),
        termination_components={"tracking_error": tracking_error_term_factory(threshold=0.5)},
        action_config=make_pd_action_config(robot_cfg),
        motion_manager=MimicMotionManagerConfig(init_start_prob=1.0, resample_on_reset=True),
    )


def agent_config(robot_cfg, env_cfg, args):
    observation_keys = list(env_cfg.observation_components)

    def network(output_key, output_size):
        return MLPWithConcatConfig(
            in_keys=observation_keys.copy(),
            out_keys=[output_key],
            num_out=output_size,
            normalize_obs=True,
            layers=[MLPLayerConfig(units=128, activation="relu") for _ in range(2)],
        )

    return PPOAgentConfig(
        batch_size=args.batch_size,
        training_max_steps=args.training_max_steps,
        num_steps=32,
        num_mini_epochs=1,
        gradient_clip_val=1.0,
        fail_on_bad_grads=True,
        save_epoch_checkpoint_every=None,
        save_last_checkpoint_every=1,
        evaluator=EvaluatorConfig(eval_metrics_every=None),
        model=PPOModelConfig(
            in_keys=observation_keys,
            actor=PPOActorConfig(
                in_keys=observation_keys.copy(),
                mu_key="action_mean",
                num_out=robot_cfg.number_of_actions,
                mu_model=network("action_mean", robot_cfg.number_of_actions),
            ),
            critic=network("value", 1),
        ),
    )

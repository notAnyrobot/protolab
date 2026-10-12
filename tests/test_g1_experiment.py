"""CPU-only integration check against the installed upstream config builder."""

import importlib.util
from argparse import Namespace
from pathlib import Path
import unittest


class G1ExperimentTests(unittest.TestCase):
    def test_upstream_builds_a_bounded_g1_training_configuration(self):
        from protomotions.utils.config_builder import build_standard_configs

        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location(
            "g1_newton_smoke", root / "experiments/g1_newton_smoke.py"
        )
        experiment = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(experiment)
        args = Namespace(
            robot_name="g1", simulator="newton", headless=True, num_envs=1,
            experiment_name="g1_config_test", batch_size=32, training_max_steps=64,
            motion_file=str(root / "external/ProtoMotions/data/motion_for_trackers/g1_bones_seed_mini.pt"),
        )
        configs = build_standard_configs(
            args,
            experiment.terrain_config,
            experiment.scene_lib_config,
            experiment.motion_lib_config,
            experiment.env_config,
            experiment.configure_robot_and_simulator,
            experiment.agent_config,
        )
        configs["motion_lib"].validate()
        agent, env, robot = (configs[key] for key in ("agent", "env", "robot"))
        self.assertEqual(robot.asset.asset_root, "assets")
        self.assertEqual(robot.asset.asset_file_name, "robots/g1/mjcf/g1_holo_compat.xml")
        self.assertEqual(agent.resolve_max_epochs(total_envs=args.num_envs), 2)
        self.assertEqual((agent.num_steps * args.num_envs) % agent.batch_size, 0)
        self.assertGreater(robot.number_of_actions, 0)
        self.assertEqual(agent.model.actor.num_out, robot.number_of_actions)
        self.assertEqual(agent.model.actor.mu_model.num_out, robot.number_of_actions)
        for model in (agent.model, agent.model.actor, agent.model.actor.mu_model, agent.model.critic):
            self.assertTrue(set(model.in_keys).issubset(env.observation_components))
        self.assertIn("mimic", env.control_components)
        self.assertIsNone(agent.evaluator.eval_metrics_every)
        args.robot_name = "h1_2"
        with self.assertRaisesRegex(ValueError, "g1"):
            experiment.configure_robot_and_simulator(robot, configs["simulator"], args)


if __name__ == "__main__":
    unittest.main()

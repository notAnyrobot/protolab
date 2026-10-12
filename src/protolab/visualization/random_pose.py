"""Random-pose viewer for ProtoLab's G1 robot on IsaacLab."""

import math

import torch

from protomotions.components.scene_lib import SceneLib
from protomotions.robot_configs.base import ControlType
from protomotions.simulator.base_simulator.config import (
    MarkerConfig,
    MarkerState,
    VisualizationMarkerConfig,
)
from protomotions.simulator.factory import simulator_config
from protomotions.simulator.isaaclab.simulator import IsaacLabSimulator
from protomotions.utils.rotations import quat_from_euler_xyz

from protolab.robots.g1 import ProtoLabG1RobotConfig


G1_MARKER_BODIES = (
    "pelvis",
    "torso_link",
    "left_knee_link",
    "right_knee_link",
    "left_ankle_roll_link",
    "right_ankle_roll_link",
)


class G1RandomPoseVisualizer:
    """Show one random pose at startup and another whenever R is pressed."""

    def __init__(self, *, simulation_app, num_envs: int, headless: bool) -> None:
        self.app = simulation_app
        self.num_envs = num_envs
        self.device = torch.device("cuda:0")
        self.reset_requested = True

        robot_cfg = ProtoLabG1RobotConfig()
        robot_cfg.asset.disable_gravity = True
        robot_cfg.asset.fix_base_link = False
        robot_cfg.asset.self_collisions = False
        robot_cfg.control.control_type = ControlType.TORQUE
        self.robot_cfg = robot_cfg

        sim_cfg = simulator_config(
            "isaaclab",
            robot_cfg,
            headless=headless,
            num_envs=num_envs,
            experiment_name="protolab_random_pose",
        )
        marker_configs = [MarkerConfig(size="regular") for _ in G1_MARKER_BODIES]
        markers = {
            "body_markers": VisualizationMarkerConfig(
                type="sphere",
                color=(1.0, 0.0, 0.0),
                markers=marker_configs,
            )
        }
        scene_lib = SceneLib.empty(num_envs=num_envs, device=self.device)
        self.simulator = IsaacLabSimulator(
            config=sim_cfg,
            robot_config=robot_cfg,
            terrain=None,
            device=self.device,
            scene_lib=scene_lib,
            simulation_app=simulation_app,
        )
        self.simulator._initialize_with_markers(markers)
        self.simulator.user_interface.register_key(
            "R",
            owner="ProtoLab random pose",
            description="Generate a new random pose",
            on_press=self.request_reset,
        )
        self.marker_body_ids = [
            self.simulator._body_names.index(body) for body in G1_MARKER_BODIES
        ]

        grid_size = math.ceil(num_envs ** (1 / 3))
        grid_axis = torch.arange(grid_size, device=self.device)
        coords = torch.stack(
            torch.meshgrid(grid_axis, grid_axis, grid_axis, indexing="ij"),
            dim=-1,
        ).reshape(-1, 3)
        self.root_positions = coords[:num_envs] * 4.0
        self.env_ids = torch.arange(num_envs, device=self.device)
        self.zero_actions = torch.zeros(
            num_envs, robot_cfg.number_of_actions, device=self.device
        )

        print(f"Loaded ProtoLab G1 in IsaacLab ({num_envs} environment(s))")
        print("Press R to generate a new pose; press Q to close the viewer")

    def request_reset(self) -> None:
        self.reset_requested = True

    def _random_rotation(self) -> torch.Tensor:
        angles = (torch.rand(3, self.num_envs, device=self.device) - 0.5) * (
            2 * torch.pi
        )
        return quat_from_euler_xyz(*angles, w_last=True)

    def _reset_pose(self) -> None:
        state = self.simulator.get_robot_state()
        lower = self.robot_cfg.kinematic_info.dof_limits_lower.to(self.device)
        upper = self.robot_cfg.kinematic_info.dof_limits_upper.to(self.device)
        state.dof_pos = lower + torch.rand(
            self.num_envs, len(lower), device=self.device
        ) * (upper - lower)
        state.dof_vel = torch.zeros_like(state.dof_pos)
        state.rigid_body_pos[:, 0, :] = self.root_positions
        state.rigid_body_rot[:, 0, :] = self._random_rotation()
        state.rigid_body_vel[:, 0, :] = 0
        state.rigid_body_ang_vel[:, 0, :] = 0
        self.simulator.reset_envs(
            state, new_object_states=None, env_ids=self.env_ids
        )
        self.reset_requested = False
        print("Generated new random pose")

    def _marker_states(self) -> dict[str, MarkerState]:
        bodies = self.simulator.get_bodies_state()
        return {
            "body_markers": MarkerState(
                translation=bodies.rigid_body_pos[:, self.marker_body_ids, :]
                .detach()
                .clone(),
                orientation=bodies.rigid_body_rot[:, self.marker_body_ids, :]
                .detach()
                .clone(),
            )
        }

    def run(self, *, max_steps: int | None = None) -> None:
        steps = 0
        while self.app.is_running() and self.simulator.is_simulation_running():
            if self.reset_requested:
                self._reset_pose()
            self.simulator.step(
                self.zero_actions,
                markers_callback=self._marker_states,
            )
            steps += 1
            if steps == 1:
                print("First simulation frame completed", flush=True)
            if max_steps is not None and steps >= max_steps:
                print(f"Completed {steps} simulation steps", flush=True)
                break

    def close(self) -> None:
        self.simulator.close()

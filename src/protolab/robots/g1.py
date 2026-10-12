"""ProtoLab's G1 configuration, backed by the robot assets in this repo."""

from dataclasses import dataclass, field

from protomotions.robot_configs.base import RobotAssetConfig
from protomotions.robot_configs.g1 import G1RobotConfig


# Repo-relative paths keep saved configs portable; ProtoLab commands run from the repo root.
G1_ASSET_ROOT = "assets"
G1_MJCF = "robots/g1/mjcf/g1_holo_compat.xml"


def _g1_asset() -> RobotAssetConfig:
    # Match the pinned upstream G1 asset settings while owning the asset path.
    return RobotAssetConfig(
        asset_root=G1_ASSET_ROOT,
        asset_file_name=G1_MJCF,
        replace_cylinder_with_capsule=True,
        thickness=0.01,
        max_angular_velocity=1000.0,
        max_linear_velocity=1000.0,
        density=0.001,
        angular_damping=0.0,
        linear_damping=0.0,
    )


@dataclass
class ProtoLabG1RobotConfig(G1RobotConfig):
    """Use ProtoMotions' G1 behavior with ProtoLab's G1 MJCF and meshes."""

    asset: RobotAssetConfig = field(default_factory=_g1_asset)


def configure_upstream_g1_for_protolab(robot_config: G1RobotConfig) -> None:
    """Point the built-in G1 experiment hook at the matching local asset copy.

    The current ProtoMotions builder creates the built-in G1 before it calls
    experiment hooks. The local MJCF is an exact copy, so the already-derived
    kinematics remain valid when the simulator later reads the local files.
    """
    if not isinstance(robot_config, G1RobotConfig):
        raise TypeError("Expected the built-in G1 robot configuration")
    robot_config.asset = _g1_asset()

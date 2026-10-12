"""Inspect ProtoLab's G1 description in the IsaacLab Kit viewer.

Run from the ProtoLab repository root. IsaacLab is the only simulator backend
supported by this script.
"""

import argparse
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--robot", choices=("g1",), default="g1")
    parser.add_argument("--num-envs", type=int, default=1)
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--max-steps", type=int, default=None)
    args = parser.parse_args()
    if args.num_envs < 1:
        parser.error("--num-envs must be at least 1")
    if args.max_steps is not None and args.max_steps < 1:
        parser.error("--max-steps must be at least 1")
    return args


def launch_options(headless: bool) -> dict:
    options = {"headless": headless, "device": "cuda:0"}
    if not headless:
        options["visualizer"] = ["kit"]
    return options


def disable_broken_camera_menu() -> None:
    """Avoid the Kit 110.1.1 camera-menu callback fixed in Kit 110.1.4."""
    import omni.kit.app

    extension_name = "omni.kit.viewport.menubar.camera"
    manager = omni.kit.app.get_app().get_extension_manager()
    if manager.is_extension_enabled(extension_name):
        manager.set_extension_enabled_immediate(extension_name, False)
    if manager.is_extension_enabled(extension_name):
        raise RuntimeError(f"Could not disable buggy Kit extension: {extension_name}")


def main() -> None:
    args = parse_args()
    os.chdir(ROOT)  # ProtoLab's robot config uses repo-relative asset paths.

    # IsaacLab must be imported before torch and the robot/simulator modules.
    from protomotions.utils.simulator_imports import import_simulator_before_torch

    AppLauncher = import_simulator_before_torch("isaaclab")
    launcher = AppLauncher(launch_options(args.headless))
    visualizer = None
    try:
        if not args.headless:
            disable_broken_camera_menu()
        from protolab.visualization.random_pose import G1RandomPoseVisualizer

        visualizer = G1RandomPoseVisualizer(
            simulation_app=launcher.app,
            num_envs=args.num_envs,
            headless=args.headless,
        )
        visualizer.run(max_steps=args.max_steps)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if visualizer is None:
            launcher.app.close()
        else:
            visualizer.close()


if __name__ == "__main__":
    main()

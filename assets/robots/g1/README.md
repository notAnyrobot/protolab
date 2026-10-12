# Unitree G1 example assets

This is ProtoLab's local copy of the G1 description used by
`ProtoLabG1RobotConfig`. `mjcf/g1_holo_compat.xml` and the 35 meshes it names
come from the pinned ProtoMotions checkout at commit
`607ca7a0bb92e261120bcab8d9f97f28b3130ffc`.

The robot description and meshes are copyrighted by Unitree Robotics and
distributed under the BSD-3-Clause terms in [LICENSE](LICENSE). The mesh files
are configured for Git LFS. Keep the MJCF's `../mesh/G1/` path and its mesh
files together when moving this example.

## Visualize this G1 description

From the ProtoLab repository root, with the root environment installed:

```bash
env -u PYTHONPATH -u HEADLESS -u LIVESTREAM \
  uv run --project . --locked python \
  experiments/random_pose_visualizer.py --robot g1
```

The launcher selects ProtoLab's locked Python 3.12 environment, points
ProtoMotions' G1 factory at this local description and its meshes, and asks
IsaacLab for the Kit viewer. IsaacLab is the fixed backend; there is no
`--simulator` option. It generates one pose at startup; press R in the
viewer for another. Press Q or close the viewer to stop. The `env -u` options
clear settings that could suppress the window or load Python modules from an
unrelated checkout. If the root `.venv` is already active, `python` can replace
`uv run --project . --locked python` in this command.

# Handoff: ProtoMotions documentation walkthrough

## Next session objective

Review the official documentation at https://nvlabs.github.io/ProtoMotions/ together before deciding what ProtoLab should extend. Begin with architecture and core abstractions, connecting them to the existing G1 experiment; then review tutorials, motion workflows, configuration, training, and evaluation. Discussion and planning first, no implementation yet. Distinguish documented capabilities, implementations in this checkout, verified behavior, and bugs or unmet requirements. Avoid duplicating upstream features.

## Working baseline

- Local root: `/home/android/workspace/protolab`; environment: `.venv_newton`.
- ProtoLab owns `src/protolab/` and `experiments/`; upstream is `external/ProtoMotions/`.
- ProtoMotions commit `607ca7a0bb92e261120bcab8d9f97f28b3130ffc`, verified clean at handoff.
- Python 3.12, ProtoMotions 3.1.0, Newton 1.0.0, Warp 1.12.0, PyTorch 2.7.1 with CUDA 12.8.
- Use `TORCH_COMPILE_DISABLE=1` for the validated baseline.
- Laptop GPU: RTX 5070 Laptop, 8 GB.
- Read `docs/installation.md`, `docs/newton-baseline-constraints.txt`, `dependencies.toml`, and `experiments/g1_newton_smoke.py`.
- IsaacLab work is deferred to another session. Leave the ThinkStation alone; training moved to HPC after suspected encryption-software interference.

## Validated workflow

HPC container training → selective checkpoint download → laptop inference → local recording works. Policy quality is deliberately postponed; the user does not want exhaustive validation of every feature.

- SSH: use your configured HPC host alias (for example, `hpc`).
- Host project: use your Protolab checkout on the HPC host.
- Container: use your training container; project inside: `/workspace/protolab`.
- Rootless Docker socket: use the current user's socket at `unix:///run/user/<uid>/docker.sock`.
- Eight GPUs identified as RTX 4090. Prefer headless HPC training and laptop visualization; VNC worked but was slow.
- A small four-GPU run completed. A larger run used 2,048 environments per GPU on four GPUs, targeting 30,000 iterations. Output reached about iteration 20,258; the user accepted that as sufficient. Do not claim 30,000 completed.
- Downloaded local run: `results/hpc/g1_newton_4gpu_2048env_20260908_133845/`.
- Local inference needs `last.ckpt` and `resolved_configs_inference.pt` together, plus matching local code, assets, and motion data. Intermediate checkpoints are unnecessary just for viewing.

## Recording artifacts

Directory: `/home/android/workspace/protolab/output/renderings`.

Prefix: `g1_newton_4gpu_2048env_20260908_133845-2026-09-10-11-30-23`.

- `.mp4`: standalone camera video, 206 frames.
- `.motion`: achieved robot trajectory, 207 samples at 30 FPS; poses, velocities, joints, and contact fields. Contacts in this recording are all zero. This is neither a target motion nor a policy checkpoint.
- `.markers.pt`: visual markers; here, red reference body-position targets.
- `.objects.pt`: nonrobot objects; here, the projectile cube.

No combined consumer for all four files was found in the scoped source search. This was not an exhaustive proof of absence.

## Motion playback findings

`examples/motion_libs_visualizer.py` loads the file but crashes in Newton's torque-control path because `_action_to_torque_targets` is missing. Training/inference use a working built-in PD path. No upstream patch was made.

The existing `examples/env_kinematic_playback.py` successfully replayed the recording for 629 steps, looped, and closed cleanly in a bounded test:

```bash
cd /home/android/workspace/protolab
source .venv_newton/bin/activate
TORCH_COMPILE_DISABLE=1 python external/ProtoMotions/examples/env_kinematic_playback.py \
  --experiment-path experiments/g1_newton_smoke.py \
  --robot-name g1 --simulator newton --num-envs 1 \
  --motion-file output/renderings/g1_newton_4gpu_2048env_20260908_133845-2026-09-10-11-30-23.motion
```

No policy checkpoint is loaded. Kinematic control sets recorded poses, but the overall environment still invokes `simulator.step()` before the pose reset: do not describe the entire execution as doing no physics work. Separate markers/objects recordings are not automatically loaded.

Stop with Ctrl+C in the owning terminal. Q was observed to pan the camera despite printed quit instructions. Separate viewers can coexist; closing inference frees resources.

## Playback timing defect

The user next played `external/ProtoMotions/data/g1-kimodo-generated/proto/output_dance.motion`: 30 FPS, 150 frames, first-to-last duration 4.967 seconds.

G1/Newton uses 200 Hz physics and decimation 4, so one environment step represents 0.02 seconds. In this combination, `MimicMotionManager.post_physics_step()` advances the motion clock by 0.02 seconds and `KinematicReplayControl.step()` advances it again by 0.02 seconds. Thus 100 environment steps advance 4 seconds of motion instead of 2. Source and terminal logs agree.

This is twice the configured simulation timeline, not a measured wall-clock multiplier. The example also lacks explicit wall-clock pacing and a playback-speed CLI option. An earlier explanation blamed only missing pacing; that explanation was incomplete and corrected. Do not alter the motion file FPS to hide this defect.

Relevant sources under `external/ProtoMotions/`: `protomotions/envs/base_env/env.py`, `protomotions/envs/motion_manager/mimic_motion_manager.py`, and `protomotions/envs/control/kinematic_replay_control.py`.

No fix or launcher was implemented. Set feature proposals aside while reviewing upstream documentation and capabilities. Preserve the pinned upstream checkout; verify online documentation against this revision before recommending commands.

# Project-owned experiments

## Supported G1 pose check: IsaacLab

`random_pose_visualizer.py` uses `ProtoLabG1RobotConfig` and the G1 description
under `assets/robots/g1/`. It selects IsaacLab and its Kit viewer directly;
there is no simulator switch or import from ProtoMotions' example scripts.
From the ProtoLab root, run:

```bash
env -u PYTHONPATH -u HEADLESS -u LIVESTREAM \
  uv run --project . --locked python \
  experiments/random_pose_visualizer.py --robot g1
```

Press R in the viewer for a new random pose, or Q to quit. Use `--headless` for
a noninteractive run. See the [G1 asset notes](../assets/robots/g1/README.md)
for the asset provenance and Python alternative.

The pinned Kit 110.1.1 camera-menu extension raises an exception when the
viewport camera changes. The launcher disables that optional menu before
building the scene. NVIDIA records
the fix in its [Kit 110.1.4 release notes](https://docs.omniverse.nvidia.com/dev-guide/latest/release-notes/110_1_4.html).
`--max-steps N` runs a bounded diagnostic and then closes the viewer. Run only one Kit viewer at
a time because each consumes substantial RAM and GPU memory.

## Historical Newton smoke experiment

`g1_newton_smoke.py` is a small, fresh-training G1 motion-tracking experiment.
It composes installed `protomotions.*` configuration classes and factories;
there are no upstream source edits, custom agents, or imports from `examples.*`.
This records an older diagnostic run in `.venv_newton/`; IsaacLab is ProtoLab's
supported backend now.

It uses one flat terrain tile, body-state and next-reference-pose observations,
standard tracking rewards and tracking-error termination, and two-layer
128-unit actor/critic networks. Periodic evaluation is disabled to keep the
smoke run bounded. This checks training plumbing; two updates will **not**
produce a trained tracker. It does not load the BONES pretrained checkpoint,
whose network and observations differ from this experiment.

## Two-rollout smoke run

Use the existing Newton environment, from the **ProtoLab repository root**:

```bash
cd /home/android/workspace/protolab
source .venv_newton/bin/activate

TORCH_COMPILE_DISABLE=1 protomotions train-agent \
  --robot-name g1 --simulator newton \
  --experiment-path experiments/g1_newton_smoke.py \
  --experiment-name "g1_newton_smoke_$(date +%Y%m%d_%H%M%S)" \
  --motion-file external/ProtoMotions/data/motion_for_trackers/g1_bones_seed_mini.pt \
  --num-envs 1 --batch-size 32 \
  --training-max-steps 64 --headless true
```

With one environment and 32 steps per rollout, the 64-step budget gives two
complete rollout/optimization iterations. Each uses one minibatch and one PPO
mini-epoch. This budget counts environment steps, not seconds; startup, NCCL
initialization, and first-run GPU compilation can take longer than the rollout.
Change `--headless true` to `--headless false` for a viewer; the run is short and
the freshly initialized policy may fall immediately.

The launcher writes configs, logs, and checkpoints under
`results/<experiment-name>/` in ProtoLab, including `last.ckpt` after each
iteration. The timestamp prevents accidentally resuming a previous experiment.
Success means both iterations complete, losses remain finite, and a checkpoint
is saved without a traceback. This is separate from the working pretrained G1
inference baseline described in the installation guide.

## Validation and scope

The configuration was built with the installed upstream `build_standard_configs`
function on CPU. The integration test checks robot/action dimensions,
observation wiring, rollout/batch compatibility, and the two-iteration budget:

```bash
TORCH_COMPILE_DISABLE=1 python -m unittest discover -s tests -v
```

GPU smoke training passed on 2026-09-08 in run
`g1_newton_smoke_20260908_153227`: both iterations completed, all 124 logged
scalar samples were finite, and `last.ckpt` was saved. Loading that checkpoint
for Newton viewer inference also passed. Validation stops at this development
baseline; recording and interrupted-training resume were not tested.

These small settings are a smoke test, not a validated learning recipe. Keep
`TORCH_COMPILE_DISABLE=1` if reproducing the historical Newton baseline.

To extend this experiment, change one configuration value at a time and use a
new experiment name. Put reusable custom behavior in `src/protolab/` when it
becomes necessary.

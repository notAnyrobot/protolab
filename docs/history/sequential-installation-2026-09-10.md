# Historical sequential installation record

Superseded for new installations by [the root uv workflow](../installation.md).
These commands document the earlier Newton and IsaacLab investigation.

# Installation

## Working baseline: Newton (2026-09-08)

Standalone ProtoMotions with Newton is the current working baseline, based on the
user's local G1 viewer/inference test. Package checks passed for 139 packages;
CUDA and Warp device checks passed; G1 assets and checkpoint loaded, policy
execution started, and viewer controls responded without the Triton traceback
when `TORCH_COMPILE_DISABLE=1` was set. ProtoLab integration, a bounded project-owned training run, and saved-checkpoint
inference subsequently passed as described in the validation section below.

| Component | Tested value |
| --- | --- |
| Python | 3.12.14 |
| uv | 0.12.10 |
| GPU | RTX 5070 Laptop GPU, 8 GiB |
| NVIDIA driver | 580.173.02 |
| ProtoMotions | 3.1.0, commit `607ca7a0bb92e261120bcab8d9f97f28b3130ffc` |
| PyTorch / Triton | 2.7.1+cu128 / 3.3.1 |
| Newton / Warp | 1.0.0 / 1.12.0 |
| MuJoCo / MuJoCo Warp | 3.5.0 / 3.5.0.2 |
| Environment | `.venv_newton/` |

`dependencies.toml` records upstream source pins. The full installed version
snapshot is in `newton-baseline-constraints.txt`. It excludes ambient ROS packages
and is a constraint snapshot, not a portable lockfile or an offline bundle.

## Recreate standalone ProtoMotions

Follow the [official Newton installation guide](https://nvlabs.github.io/ProtoMotions/getting_started/installation.html#newton)
with the adjustments below. Run from the ProtoLab repository root. Clone the
ProtoMotions URL and commit recorded in `dependencies.toml` into
`external/ProtoMotions` if absent. Fetch its Git LFS assets before simulation.
IsaacLab is not needed for this backend.

```bash
uv venv --python 3.12 .venv_newton
source .venv_newton/bin/activate
uv pip install --python .venv_newton/bin/python 'torch==2.7.1' \
  --index-url https://download.pytorch.org/whl/cu128
uv pip install --python .venv_newton/bin/python 'newton[examples]==1.0.0'
CMAKE_POLICY_VERSION_MINIMUM=3.5 CMAKE_BUILD_PARALLEL_LEVEL=2 \
  uv pip install --python .venv_newton/bin/python \
  -c docs/newton-baseline-constraints.txt \
  -e ./external/ProtoMotions \
  -r ./external/ProtoMotions/requirements_newton.txt
uv pip check --python .venv_newton/bin/python
```

The baseline used CUDA 12.8 PyTorch wheels for Blackwell support, in place of the
guide's CUDA 12.4 example. OpenMesh 1.2.1 required the CMake policy setting with
CMake 4.3.1; two build jobs limit compilation parallelism. No upstream code was
patched. A fresh installation using this snapshot has not been independently
retested; package availability and build tools remain relevant.

## Install ProtoLab into the working environment

Do not recreate the environment if the standalone test already works. From the
ProtoLab repository root:

```bash
source .venv_newton/bin/activate
uv pip install --python .venv_newton/bin/python --dry-run \
  -c docs/newton-baseline-constraints.txt \
  -e . -e ./external/ProtoMotions
```

The tested dry-run adds ProtoLab and reinstalls the same editable ProtoMotions
checkout, without changing third-party versions. Then run:

```bash
uv pip install --python .venv_newton/bin/python \
  -c docs/newton-baseline-constraints.txt \
  -e . -e ./external/ProtoMotions
uv pip check --python .venv_newton/bin/python
python -c "import protolab, protomotions; print(protolab.__file__); print(protomotions.__file__)"
python -m unittest discover -s tests -v
protomotions info
```

Expected imports are `src/protolab/__init__.py` and the official editable checkout
under `external/ProtoMotions`. Both editable paths are explicit so the installer
uses local upstream source. Constraints prevent replacement of baseline package
versions; they do not disable dependency checking.

The base package requires ProtoMotions without selecting a simulator. Optional
`protolab[newton]` and `protolab[isaaclab]` extras are available in metadata.
Use the base install above for the existing baseline: the upstream Newton extra
also requests ONNX Runtime, which is absent from the tested requirements-file
installation. Its offline dry-run stopped because that package was not cached.
ProtoLab 0.1.0 was subsequently installed editable: all 140 packages passed
compatibility checks, both imports resolved to their expected source trees, and
the ownership test passed. The user repeated the G1 viewer test after installation:
policy evaluation and viewer controls worked without a Triton traceback. This
confirms coexistence/startup. The subsequent project-owned experiment and
checkpoint-loading checks also passed; see the validation record below.

## Validate your installation

Validation is complete for the current Newton development baseline. New users
should check packages/imports and run one short simulation. The bounded training
and checkpoint-loading checks below are optional deeper checks for users who
will develop experiments; they are not an exhaustive feature test suite.

### 1. Package and configuration checks

From your ProtoLab clone root:

```bash
source .venv_newton/bin/activate
uv pip check --python .venv_newton/bin/python
TORCH_COMPILE_DISABLE=1 python -m unittest discover -s tests -v
protomotions info
```

Expect compatible packages, both tests passing, and Newton available. These
checks do not by themselves prove GPU simulation works.

### 2. Official G1 viewer smoke test

From the activated Newton environment:

```bash
cd external/ProtoMotions
TORCH_COMPILE_DISABLE=1 python protomotions/inference_agent.py \
  --checkpoint data/pretrained_models/motion_tracker/g1-bones-deploy/last.ckpt \
  --motion-file data/motion_for_trackers/g1_bones_seed_mini.pt \
  --simulator newton --num-envs 1
```

Verify visible motion tracking and responsive controls for 30–60 seconds after
startup. Press Q or Ctrl+C to stop. Distributed initialization was slow on the
first test but ultimately completed; a short timeout alone does not prove a hang.

`TORCH_COMPILE_DISABLE=1` bypasses the observed PyTorch/Triton generated-kernel
error (`constexpr` has no attribute `is_block`). CUDA execution and Newton/Warp
physics remain enabled. The compiler issue is bypassed, not fixed. Syntax warnings,
missing optional OpenGL_accelerate, and Tensor Core performance advice were
nonfatal in the observed run.

Use the activated environment's `python` and `protomotions` commands. Plain root
`uv sync`/`uv run` does not reproduce this sequentially assembled environment.

### 3. Optional project-owned training and checkpoint check

The [experiment guide](../experiments/README.md#two-rollout-smoke-run) contains
the bounded two-rollout command. It starts a fresh policy for 64 environment steps
and saves configs, logs and `last.ckpt` under `results/<experiment-name>/`.
Success means two iterations finish, logged losses are finite, and the checkpoint
exists. Two iterations are not enough to learn useful tracking.

To check that checkpoint loads, return to the ProtoLab root and replace
`<experiment-name>` with your actual results directory name:

```bash
TORCH_COMPILE_DISABLE=1 python external/ProtoMotions/protomotions/inference_agent.py \
  --checkpoint results/<experiment-name>/last.ckpt \
  --motion-file external/ProtoMotions/data/motion_for_trackers/g1_bones_seed_mini.pt \
  --simulator newton --num-envs 1
```

Expect the viewer to reach policy evaluation without tensor-shape or missing-key
errors. Poor balance or falling is expected from this barely trained policy.
Close the viewer after confirming it advances; recording and training-resume
checks are not required to accept this installation baseline.

### Completed validation record (2026-09-08)

| Check | Evidence | Result |
| --- | --- | --- |
| Package compatibility | 140 installed packages checked after adding ProtoLab | Passed |
| Imports and experiment configuration | Both unittest checks passed | Passed |
| GPU access | PyTorch computation and Warp CUDA device initialization | Passed |
| Official pretrained G1 inference | Policy execution and responsive Newton viewer | Passed |
| Project-owned training | `g1_newton_smoke_20260908_153227`, epochs 0 and 1 completed | Passed |
| Training metrics | 124 scalar samples inspected; no NaN/Inf, including actor/critic losses | Passed |
| Checkpoint saving | `last.ckpt` approximately 4.3 MB, configs and event log present | Passed |
| Project checkpoint inference | Saved config/model loaded, policy evaluation and viewer started | Passed |

This is sufficient validation for starting ProtoLab development. Further checks
are driven by features being developed, not required as part of installation.
Recording, interrupted-training resume, long-run stability, and quantitative
tracking quality were not tested. `TORCH_COMPILE_DISABLE=1` remains part of the
working baseline; the compiler issue has not been fixed.

## IsaacLab investigation (updated 2026-09-10)

**Current status:** ProtoMotions 3.1.0 is installed editable in
`.venv_isaaclab/`. The user verified all 270 installed packages are compatible,
and the headless GPU cube fall/reset test passes after installation. The G1
checkpoint loads and both headless and viewer runs reach policy evaluation.
The viewer run was manually interrupted (Python exit 0, tee exit 130).
Rendering/robot visibility, motion quality, and the asset mass/inertia warnings
are deferred at the user's request; this is not yet a validated training baseline.
ProtoLab itself is not installed in this environment. Newton remains the tested
ProtoLab development baseline and its separate environment is unchanged.

### Install ProtoMotions into the prepared IsaacLab environment

These commands were tested after the project-owned marker/ovphysx manifest
adjustments and the [MoviePy source migration](../moviepy-pillow-dependencies.md).
They are not a fresh, unmodified upstream installation recipe.

```bash
cd /home/android/workspace/protolab
uv pip install --python .venv_isaaclab/bin/python \
  -e "./external/ProtoMotions[isaaclab]" \
  -r external/ProtoMotions/requirements_isaaclab.txt \
  "hydra-core>=1.3,<1.4" "numpy==2.3.1" "pillow==12.1.1" \
  "moviepy @ https://github.com/Zulko/moviepy/archive/97316f37f6a8d3843abfb53eba8f3bb0ea46a008.tar.gz" \
  --extra-index-url https://pypi.nvidia.com
uv pip check --python .venv_isaaclab/bin/python
env -u PYTHONPATH .venv_isaaclab/bin/protomotions info
env -u PYTHONPATH .venv_isaaclab/bin/python -u scripts/validate_isaaclab.py
```

The install selected Hydra 1.3.6, OmegaConf 2.3.0, Newton 1.2.0,
newton-usd-schemas 0.2.0, Protobuf 6.33.6 and TensorDict 0.9.0. This resolves
the earlier installed Newton/schema incompatibilities. MoviePy remains the
exact source revision above, not the released 2.2.1 artifact. The historical
workspace manifests retain different overrides; do not run `uv sync` over this
environment using those manifests. A fresh reproducible end-to-end install
still needs consolidation and testing.

The following records the original blocker and earlier investigation:

### Original deferral (2026-09-08)

**Use Newton for ProtoLab development. ProtoMotions installation with the pinned
IsaacLab/Isaac Sim stack is blocked by incompatible Pillow requirements.**

| Requirement chain | Pillow requirement |
| --- | --- |
| ProtoMotions 3.1.0 → MoviePy 2.x (available versions tested) | `<12` |
| Isaac Sim 6.0.0.1 → isaacsim-kernel 6.0.0.1 | `==12.1.1` |

The editable ProtoMotions installation dry-run failed before changing packages.
Editable installation does not remove this conflict. No dependency bypass or
upstream patch is part of the supported workflow.

Standalone IsaacLab made progress in the separate `.venv_isaaclab/` environment:

- An adapted IsaacSim-only manifest installed 242 packages. The original pinned
  manifest still failed resolution in the tested environment; this adaptation
  is not the unmodified official installation procedure.
- NumPy was corrected to `2.3.1`. Package checking still reports two Newton/schema
  incompatibilities introduced by the IsaacLab manifest's overrides.
- The official `create_empty.py --device cuda:0 --visualizer none` tutorial
  reached `Setup complete...` and remained running, as reported by the user.
- The corrected project-owned manifest was subsequently installed into
  `.venv_isaaclab` on 2026-09-10. A bounded headless GPU cube fall/reset test
  passed and exited 0; see `scripts/validate_isaaclab.py`.
- The Kit viewer previously crashed; the latest bounded retry did not complete
  startup within 90 seconds and was stopped by its timeout. Graphical operation
  and articulated-robot simulation remain unvalidated.

Preserve `.venv_isaaclab/` for future investigation; it is not a validated
ProtoMotions environment. The working `.venv_newton/` and official checkouts
remain unchanged. Do not install the IsaacLab extra into the Newton environment.

Resume this backend when compatible upstream dependency metadata is available,
or when a separately scoped workaround can be tested. Resolution, package
checks, and ProtoMotions simulation must then be validated before promoting it
to a working baseline. See [the investigation record](../isaaclab-resolution.md)
for pins, commands, and remaining limitations. Reports in `docs/history/` are archival.

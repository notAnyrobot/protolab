# Installation

## Supported workflow: IsaacLab / PhysX

ProtoLab owns one combined environment for Python 3.12 on Linux x86_64 with an
NVIDIA GPU. `uv sync` installs ProtoLab, editable ProtoMotions and IsaacLab source
packages, and the locked runtime dependencies into the root `.venv/`.
Rendering, robot visibility and motion-quality investigation are deferred.

Install Git, Git LFS, uv >= 0.12.10, and a working NVIDIA driver first. The tested laptop uses
an RTX 5070 Laptop GPU, driver 580.173.02 and CUDA 12.8 PyTorch wheels. Downloads
require access to GitHub, PyPI, NVIDIA and PyTorch package servers. Allow space
for large simulator wheels, assets and caches; the earlier IsaacLab environment
occupied approximately 27 GiB before accounting for shared cache files.

After cloning this repository:

```bash
cd protolab
python3 scripts/setup.py
uv sync --locked
```

The setup helper fetches the independent external repositories at the revisions
in `dependencies.toml`, downloads Git LFS payloads, and verifies existing sources.
It does not install packages, reset modified repositories, or accept licenses.
`python3 scripts/setup.py --check` checks the prepared sources without downloading.
Python 3.11 or newer is needed to run this helper; uv selects Python 3.12 for the
project environment.

Plain `uv sync` also works. Prefer `--locked` for installation: it refuses to
change the checked-in dependency resolution. Root `.venv/` is the default; unset
`UV_PROJECT_ENVIRONMENT` if it points at another environment. Do not run root uv
commands with `--active` while using an old simulator environment.

The first simulator launch may require the user's NVIDIA license acceptance.
The installer does not automate acceptance or NVIDIA driver installation.

## Verify the installation

Run from the repository root:

```bash
python3 scripts/setup.py --check
uv pip check --python .venv/bin/python
env -u PYTHONPATH uv run --locked python -c \
  "import protolab, protomotions; print(protolab.__file__); print(protomotions.__file__)"
env -u PYTHONPATH uv run --locked python -m unittest discover -s tests -v
env -u PYTHONPATH uv run --locked python -u scripts/validate_isaaclab.py
```

Imports should resolve to `src/protolab` and `external/ProtoMotions/protomotions`.
The physics test must print `VALIDATION_FALL_PASS` and `VALIDATION_RESET_PASS`.
It runs headless, creates a local cube and closes after its bounded checks.
Configuration tests do not validate training or policy quality.

## Train and inference commands

Run from the project root. These are thin entry points that forward all arguments
to ProtoMotions without selecting a robot, backend, checkpoint or experiment:

```bash
uv run train --help
uv run inference --help

uv run inference \
  --checkpoint external/ProtoMotions/data/pretrained_models/motion_tracker/g1-bones-deploy/last.ckpt \
  --motion-file external/ProtoMotions/data/motion_for_trackers/g1_bones_seed_mini.pt \
  --simulator isaaclab --num-envs 1
```

Use `uv run train` followed by the usual ProtoMotions training arguments,
including `--experiment-path`. Relative paths are resolved from your current
working directory. The launchers use the uv environment's Python, remove ambient
`PYTHONPATH`, and default `TORCH_COMPILE_DISABLE=1` to retain the tested workaround.
An explicitly supplied `TORCH_COMPILE_DISABLE` value is preserved. `--help` is
upstream help; no preset configuration or extra launcher arguments are added.

## Dependency ownership

The root `pyproject.toml` and `uv.lock` define the supported combined environment.
The default IsaacLab dependency group includes the pinned upstream base runtime
requirements because IsaacLab's individual source packages omit most third-party
requirements. Unrelated optional upstream extras are not installed.

Among IsaacLab's RL-framework choices, the installer includes only
`rsl-rl-lib==5.5.1`. Stable-Baselines3, skrl and rl-games are neither locked nor
installed. Their optional declarations remain in the independent upstream
checkout and are not selected by root `uv sync`. ProtoMotions uses its own agent
training implementation with Lightning; Lightning remains a required dependency
and is not replaced by RSL-RL.

RSL-RL 5.5.1 includes fixes for checkpoint learning-rate restoration, LSTM hidden
states, W&B initialization, and distributed normalization and parameter/gradient
synchronization. Observation normalizers now update after optimization instead
of during rollout collection, so RSL-RL training trajectories can differ from
5.4.1. The new bfloat16 mixed-precision option remains disabled by default.

The MoviePy source archive is pinned to commit
`97316f37f6a8d3843abfb53eba8f3bb0ea46a008`, which supports Pillow 12.1.1. It is
not the released PyPI MoviePy 2.2.1 artifact. Hydra/OmegaConf and the Isaac Sim
Newton/schema requirements are resolved together without dependency overrides.
See [the MoviePy investigation](moviepy-pillow-dependencies.md) for rationale.

Local editable sources are intentionally not Git dependencies in `uv.lock`.
Their commit pins live in `dependencies.toml` and are checked by the setup helper;
`uv sync` alone cannot enforce their Git revisions. Source upgrades require a
reviewed pin update, lockfile regeneration and repeat package/runtime validation.

Do not sync using manifests generated by the old diagnostic scripts, or install
separate requirements files over the root environment. Those workflows have been
superseded. Existing `.venv_isaaclab/` and `.venv_newton/` environments are preserved
for comparison and are not managed by the new installer. Newton has no supported
profile in this installer; its prior results remain in the
[historical sequential installation record](history/sequential-installation-2026-09-10.md).

## Validation record

On 2026-09-10, a fresh root `.venv/` was created with Python 3.12.14 and
`uv sync --locked` installed 270 packages successfully, using the existing uv
cache. A second locked sync made no package changes. `uv pip check` passed for
all 270 packages; ProtoLab and ProtoMotions imports resolved to their respective
editable source trees. All 14 tests passed, including 12 setup CLI tests built
with red/green TDD cycles. The real setup helper materialized the missing IsaacLab
LFS assets and its subsequent read-only check passed for both pinned repositories.
This was a fresh environment, not a cold-cache download.

The prior `.venv_isaaclab/`, `.venv_newton/`, and both upstream checkout revisions
and working trees were verified unchanged. The old root scaffold was preserved
as `.venv.scaffold-backup-20260910/` on the test machine.

The user subsequently accepted NVIDIA's EULA interactively in the root
environment and supplied passing GPU cube fall/reset output. The official
G1 `g1-bones-deploy` checkpoint with `g1_bones_seed_mini.pt`, one IsaacLab
environment and `TORCH_COMPILE_DISABLE=1` then reached policy evaluation in
the viewer. The user confirmed the robot was visible and moving and supplied
a screenshot and log with no traceback. This validates the local installation,
bounded basic physics, and an interactive pretrained-inference smoke test.

The asset mass/inertia and articulation-lookup warnings remain. Motion-tracking
quality, training, long-duration stability, and an automated bounded G1 evaluation
have not been validated in the root environment. The successful viewer run does
not establish a fix for the earlier intermittent rendering issues; further
rendering investigation remains deferred.

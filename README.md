# ProtoLab

An independent playground for custom tasks, rewards, and motion-learning
experiments on NVIDIA ProtoMotions.

## Install

The supported installer targets **IsaacLab / PhysX, Linux x86_64, Python 3.12**.
After cloning ProtoLab, prepare its pinned external sources and sync the project:

```bash
cd protolab
python3 scripts/setup.py
uv sync --locked
```

Git, Git LFS, uv and a working NVIDIA driver are prerequisites. See
[installation](docs/installation.md) for requirements, dependency fixes,
validation commands and current test results. Rendering and motion-quality
investigation remain deferred.

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

## Local upstream documentation

Build browser HTML and searchable text for AI agents with
`python3 scripts/protomotions_docs.py build`, then browse with
`python3 scripts/protomotions_docs.py serve`. See the
[local documentation guide](docs/local-protomotions-docs.md) for paths, search,
rebuilds, and version details. Upstream sources and generated docs stay ignored
by Git.

## Layout

- `src/protolab/`: project-owned Python extensions.
- `src/protolab/robots/`: project-owned robot configuration code using ProtoMotions' `RobotConfig` types.
- `experiments/`: project-owned experiment configurations.
- `tests/`: setup, import and configuration checks.
- `external/ProtoMotions/` and `external/IsaacLab/`: pinned independent editable checkouts.
- `pyproject.toml` and `uv.lock`: the supported combined Python environment.
- `dependencies.toml`: external repository URLs and exact source commits.
- `.venv/`: root environment created by uv, ignored by Git.
- `assets/robots/<name>/`: project-owned robot descriptions, meshes and textures;
  G1 is the included example.
- `motions/<dataset>/`: human and humanoid motion data.
- `output/` and `results/`: generated outputs.

Keep custom code in `protolab.*` and upstream code in `protomotions.*`. Prefer
configuration and composition, then subclass only when needed. No vendoring,
submodules, monkey-patching, or upstream modifications are part of installation.
Robot configs in `protolab.robots` should point their `RobotAssetConfig` at the
matching files under `assets/`; ProtoMotions' default asset root points to its
own package. Motion data and other assets are ignored by Git, so document how
to obtain each required dataset or explicitly track redistributable files.
ProtoMotions' current robot factory accepts only its built-in robot names; a new
ProtoLab robot needs a project-owned loading path before `--robot-name <name>`
can select it.

The existing Newton environment and its experiments are retained as historical
work. The new installer does not provide a Newton backend profile. Earlier
sequential-installation commands and diagnostic manifests are superseded for
new installations; see [the historical record](docs/history/sequential-installation-2026-09-10.md).

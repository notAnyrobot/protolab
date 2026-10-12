# proto_playground

An independent playground for robotics and reinforcement-learning experiments
on NVIDIA ProtoMotions. IsaacLab is the only supported simulation backend here.

```text
┌──────────────────────────┐
│     proto_playground     │
│    project-owned code    │
└────────────┬─────────────┘
             │ imports
             ▼
┌──────────────────────────┐
│       ProtoMotions       │
│     NVIDIA upstream      │
└────────────┬─────────────┘
             │ backend
             ▼
┌──────────────────────────┐
│         IsaacLab         │
└────────────┬─────────────┘
             ▼
┌──────────────────────────┐
│        Isaac Sim         │
└──────────────────────────┘
```

## Installation status and compatibility

**Scaffold only: the current upstream requirements conflict, so a reproducible
working environment has not been established.** Do not interpret package import
checks as simulator compatibility tests. See `VALIDATION.md` for actual results.

Sources inspected on 2026-09-07:

- [ProtoMotions installation](https://github.com/NVlabs/ProtoMotions/blob/607ca7a0bb92e261120bcab8d9f97f28b3130ffc/docs/source/getting_started/installation.rst)
- [ProtoMotions metadata](https://github.com/NVlabs/ProtoMotions/blob/607ca7a0bb92e261120bcab8d9f97f28b3130ffc/pyproject.toml)
- [Pinned IsaacLab workspace](https://github.com/isaac-sim/IsaacLab/blob/4ecd0b036da19ff6ad2bb4d621f886b63e9f6db8/pyproject.toml)

The documented stack requires Linux x86_64, Python **3.12** (overriding the
initial preference for 3.11), IsaacLab distribution **12.0.0** at
`4ecd0b036da19ff6ad2bb4d621f886b63e9f6db8`, Isaac Sim **6.0.0.1**, and
PyTorch **2.11.0** / torchvision **0.26.0** / torchaudio **2.11.0** from the
CUDA **12.8** wheel index. ProtoMotions currently declares version **3.1.0**.
These are upstream requirements, not successfully resolved installed versions.

ProtoMotions requires `moviepy>=2,<3`; the pinned IsaacLab workspace requires
`moviepy>=1.0.3,<2.0.0.dev0`. A single resolver cannot satisfy both. No dependency
override has been added to conceal this conflict. Upstream's sequential pip
installation procedure is not proof of a consistent uv-locked environment.

Upstream recommends an IsaacLab source workspace. Its individual source packages
have empty third-party requirements. This project's `isaaclab-workspace` dependency
group preserves the workspace's base requirements, and Git source mappings select
its exact member revisions. Platform-specific requirements are narrowed to Linux x86_64. The configuration also carries its published torch,
Newton, and NumPy overrides and index policy. This is an explicit downstream
integration candidate, **not an upstream-tested substitute for its workspace**.
Newton packages here are IsaacLab internals, not a supported ProtoMotions backend.
Recheck these declarations when upgrading IsaacLab; they are not inherited from
transitive dependencies by uv.

## Setup and verification

Install Git LFS and uv >=0.11.32. `lfs = true` ensures actual upstream asset
payloads are fetched into uv's dependency cache. Do not skip LFS smudging.
The full stack and LFS data need substantial disk space; this host initially had
only 9.5 GB free. No NVIDIA EULA acceptance is automated.

Once upstream requirements are compatible:

```bash
cd /home/android/workspace/protolab/proto_playground
uv lock
uv sync --locked
uv run python -c "import protomotions; print(protomotions.__file__)"
uv run python -c "import proto_playground; print(proto_playground.__file__)"
uv run protomotions info
uv run python -m unittest discover -s tests -v
```

Commit the genuine generated `uv.lock` alongside `pyproject.toml`. Until that file
exists and sync passes, this scaffold does not provide a reproducible environment.
Do not hand-write a lockfile or use `--no-deps` to claim successful installation.

## Ownership and extensions

`protomotions.*` belongs to NVIDIA. `proto_playground.*` belongs to this project.
Keeping upstream as a Git dependency allows independent updates without a fork.
Use configuration first, composition second, subclassing only when needed.
Patching upstream is prohibited: no vendoring, submodules, monkey-patching,
installed-file edits, or reverse dependency from upstream to this project.

- `src/proto_playground/agents`: custom agents, importing upstream classes normally.
- `envs`, `rewards`, `observations`, `tasks`: project-owned task components.
- `robots`: robot configuration helpers, composed through experiment hooks;
  do not modify upstream's robot factory to register project code.
- `utils`: small shared helpers when actually needed.
- `experiments`: external Python configurations; see its README for API hooks
  and the `uv run protomotions train-agent --simulator isaaclab` command pattern.
- `scripts`: optional project-owned preparation/analysis scripts.

For example, a future `agents/mimic.py` may import
`from protomotions.agents.mimic.agent import Mimic` and define
`class PlaygroundMimic(Mimic): ...`. No speculative subclass is shipped.

## Assets and motions

Keep local/project-owned files in `assets/` and `motions/`; their contents are
ignored by Git by default. Explicitly unignore small distributable assets when
appropriate. Do not copy upstream assets here. Packaged upstream robot assets
normally resolve automatically. SMPL/SMPL-H assets are excluded from the wheel;
obtain them under their applicable terms when needed.

An optional, separately managed upstream LFS checkout outside this repository
can provide pretrained checkpoints, motion files, and examples. It is **not**
the installed Python dependency. In that checkout run `git lfs install --local`
and `git lfs pull`, then, only if an asset override is needed, set:

```bash
export PROTOMOTIONS_ASSET_ROOT=/absolute/path/to/ProtoMotions/protomotions/data/assets
```

This variable points to the asset tree (containing `mjcf`, `mesh`, `usd`, etc.),
not the repository root. Checkpoints and motions still need explicit CLI paths.
Never use an LFS pointer file as an actual robot asset.

## Intentional upgrades

After the initial lock is successfully created:

```bash
uv lock --upgrade-package protomotions
uv sync --locked
uv run python -m unittest discover -s tests -v
uv run protomotions info
```

Review the changed commit and upstream compatibility notes, test a real small
IsaacLab experiment on suitable hardware, then commit the updated lockfile.
IsaacLab remains at its explicitly pinned revision until intentionally migrated.
No GPU training run is part of scaffold validation.

The next experiment should select a supported robot (for example G1), acquire
matching motion data, and build an original configuration using upstream's
current experiment hooks plus local components. Resolve installation first.

## Local workspace layout

```text
/home/android/workspace/protolab/
├── IsaacLab/          # Official source checkout; independent Git repository
├── ProtoMotions/      # Existing official checkout; independent Git repository
└── proto_playground/  # This project's code and experiments
```

`protolab` is a plain workspace directory, not a parent Git repository or uv
workspace. Keep upstream source changes out of your custom experiments.
The source-layout migration does not resolve the MoviePy/Pillow conflict or
change the current dependency strategy. See `INSTALLATION_RESEARCH.md` before
installing dependencies. Historical validation reports describe pre-migration paths.

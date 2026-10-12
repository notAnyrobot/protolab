# Scaffold validation — 2026-09-07

## Result

The project structure is created, but installation is **not complete**. There is
no `uv.lock`: no exact ProtoMotions revision or transitive environment was locked.
No upstream source was copied into this repository, patched, or forked.

## Sources and versions

- Official Git dependency: https://github.com/NVlabs/ProtoMotions.git, Git LFS enabled.
- Observed upstream HEAD: `607ca7a0bb92e261120bcab8d9f97f28b3130ffc`.
  This is an inspected commit, **not a lockfile resolution**.
- Declared ProtoMotions version: 3.1.0.
- IsaacLab: 12.0.0, source revision `4ecd0b036da19ff6ad2bb4d621f886b63e9f6db8`.
- Upstream stack: Isaac Sim 6.0.0.1; torch 2.11.0, torchvision 0.26.0,
  torchaudio 2.11.0; CUDA 12.8 wheel index.
- Host: Linux x86_64, Python 3.12.3, Git LFS 3.4.1.
- System uv remains 0.11.2. Validation used isolated uv 0.12.10 through
  `uv tool run --from 'uv>=0.11.32' uv`, with cache/tool directories under `/tmp`.
  No global uv upgrade was performed. Upgrade uv before ordinary project commands.

## Checks

- `git init -b main`: passed; existing neighboring repositories preserved.
- `git lfs install --local`: passed.
- TOML parsing, Python AST syntax checks, namespace layout checks: passed.
- `PYTHONPATH=src python3 -c "import proto_playground; print(proto_playground.__file__)"`:
  passed; resolves to this repository's `src/proto_playground/__init__.py`.
  This tests source import only, not installation or upstream compatibility.
- `uv pip compile --python-version 3.12 -` with the two upstream MoviePy
  requirements: failed, exit 1, explicitly unsatisfiable:
  `moviepy>=2,<3` versus `moviepy>=1.0.3,<2.0.0.dev0`.
- Initial `uv lock`: failed on IsaacLab's cross-platform `in` markers.
  The downstream workspace dependency group now selects only Linux x86_64
  entries and removes their redundant markers. Version requirements are preserved.
- `timeout 45 ... uv sync`: timed out, exit 124, fetching ProtoMotions after
  fetching the IsaacLab and Newton source revisions. Created an empty `.venv`;
  did not install the simulator or produce a lockfile. The bounded attempt avoided
  an unbounded download on a disk with approximately 9 GB free.
- The following requested commands were attempted with `UV_OFFLINE=true` after
  the bounded online sync. All failed during dependency fetching, before executing
  Python or the CLI. They are **not passing import/CLI/test validations**.

### uv run python -c import protomotions; print(protomotions.__file__)

Exit 1.

```text
   Updating https://github.com/NVlabs/ProtoMotions.git (HEAD)
  × Failed to download and build `protomotions @
  │ git+https://github.com/NVlabs/ProtoMotions.git#lfs=true`
  ├─▶ Git operation failed
  ├─▶ failed to fetch into:
  │   /tmp/proto-playground-uv-cache/git-v0/db/bb29c8879c11afda
  ╰─▶ Remote Git fetches are not allowed because network connectivity is
      disabled (i.e., with `--offline`)
```

### uv run python -c import proto_playground; print(proto_playground.__file__)

Exit 1.

```text
   Updating https://github.com/NVlabs/ProtoMotions.git (HEAD)
  × Failed to download and build `protomotions @
  │ git+https://github.com/NVlabs/ProtoMotions.git#lfs=true`
  ├─▶ Git operation failed
  ├─▶ failed to fetch into:
  │   /tmp/proto-playground-uv-cache/git-v0/db/bb29c8879c11afda
  ╰─▶ Remote Git fetches are not allowed because network connectivity is
      disabled (i.e., with `--offline`)
```

### uv run protomotions info

Exit 1.

```text
   Updating https://github.com/NVlabs/ProtoMotions.git (HEAD)
  × Failed to download and build `protomotions @
  │ git+https://github.com/NVlabs/ProtoMotions.git#lfs=true`
  ├─▶ Git operation failed
  ├─▶ failed to fetch into:
  │   /tmp/proto-playground-uv-cache/git-v0/db/bb29c8879c11afda
  ╰─▶ Remote Git fetches are not allowed because network connectivity is
      disabled (i.e., with `--offline`)
```

### uv run python -m unittest discover -s tests -v

Exit 1.

```text
   Updating https://github.com/NVlabs/ProtoMotions.git (HEAD)
  × Failed to download and build `protomotions @
  │ git+https://github.com/NVlabs/ProtoMotions.git#lfs=true`
  ├─▶ Git operation failed
  ├─▶ failed to fetch into:
  │   /tmp/proto-playground-uv-cache/git-v0/db/bb29c8879c11afda
  ╰─▶ Remote Git fetches are not allowed because network connectivity is
      disabled (i.e., with `--offline`)
```

## Codex project

The installed Codex app-server `project/create` API returned project ID
`01a07a17-6df6-7980-9709-f2388b7a3489`, name `proto_playground`, and root
`/home/android/workspace/proto_playground`. The desktop tools' cached project
list had not refreshed immediately after registration. No separate task was
created and no app state files were edited manually.

## Remaining work

Obtain an upstream-supported resolution to the MoviePy incompatibility before
claiming a consistent environment. Recheck both upstream projects' documentation;
do not silently force either major version. Make sufficient disk space available,
upgrade uv to >=0.11.32, then rerun `uv lock`, `uv sync`, imports, info, and unittest.
Commit the genuine `uv.lock` only after successful resolution. The first real
experiment should use a selected supported robot and matching motion data.
No GPU-heavy training or NVIDIA EULA acceptance was attempted.

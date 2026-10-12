# protolab

Local workspace for IsaacLab-based ProtoMotions experiments. This directory is
not a Git repository or a uv workspace; each child owns its own repository.

| Directory | Ownership | Role |
| --- | --- | --- |
| `IsaacLab/` | Official isaac-sim/IsaacLab | Simulator framework and proposed base environment |
| `ProtoMotions/` | Official NVlabs/ProtoMotions | Upstream motion-learning framework; existing checkout preserved |
| `proto_playground/` | Project-owned | Custom agents, components, assets, and external experiments |

## Source revisions

- ProtoMotions: `607ca7a0bb92e261120bcab8d9f97f28b3130ffc`.
- IsaacLab: `4ecd0b036da19ff6ad2bb4d621f886b63e9f6db8` (detached HEAD).

Keep custom implementation in `proto_playground/src/proto_playground` and
experiment configurations in `proto_playground/experiments`. Do not patch the
upstream repositories or turn them into submodules of the playground.

## Migration on 2026-09-07

- Renamed `/home/android/workspace/proto-x` to this `protolab` directory.
- Moved `/home/android/workspace/proto_playground` into this directory.
- Created an independent IsaacLab clone from already cached Git objects, with
  official origin `https://github.com/isaac-sim/IsaacLab.git`; no shared object
  store or dependency on the temporary cache is needed.
- Preserved ProtoMotions Git history, playground files, and VS Code settings.
- Recreated the playground's empty virtual environment to remove obsolete
  activation paths. No simulator packages were installed.
- IsaacLab source checkout is clean, but LFS asset payloads were deferred after
  the initial download stalled. When needed, run `git lfs pull` from `IsaacLab/`
  after making sufficient disk space. Existing ProtoMotions assets were preserved.
- Updated the existing Codex `proto_playground` project and registered `protolab`.
- The unrelated older `/home/android/Documents/ChatGPT/proto-x` project remains
  unchanged.

## Installation status

Folder organization is ready. The MoviePy/Pillow requirements conflict remains
unresolved. The playground's existing dependency configuration was not changed
as part of migration. Read `proto_playground/INSTALLATION_RESEARCH.md` and
`proto_playground/README.md` before installing. Historical validation reports
retain their original paths.

The proposed next installation step is to validate the official sequential
IsaacLab environment setup, then install the external ProtoMotions checkout and
this playground into that environment. Editable installation itself does not
resolve conflicting requirements. Do not claim an environment is reproducible
until its full final dependency state has been validated and captured.

Open this workspace in your editor with:

```bash
cd /home/android/workspace/protolab
code .
```

# IsaacLab upstream ovphysx versions

Checked live public upstream sources on 2026-09-10. Branch heads can change; source links below use the observed commit IDs.

| Upstream target | Exact commit | ovphysx requirement |
| --- | --- | --- |
| Latest published GitHub release, `v3.0.0-beta2.patch1` | `ffff603eafc6b74264a5261cc0183d6a65390d78` | `ovphysx==0.4.13`, in the `ovphysx` extra of `source/isaaclab_ovphysx/setup.py` |
| Latest release without a beta suffix, `v2.3.2` | `37ddf626871758333d6ed89cf64ad702aef127d0` | No standalone `ovphysx` requirement found in the setup, pyproject, or requirements manifests scanned |
| `main` | `b0542fe2d45bf91c4e1d9ef6952b9c709c80b4e8` | No standalone `ovphysx` requirement found in the setup, pyproject, or requirements manifests scanned |
| `develop` | `e5bfe378a80ab3f431a779a0838cedf338eb7849` | `ovphysx==0.5.11`, in root `pyproject.toml` extras `ov` and `ovphysx` |

The [GitHub latest-release API](https://api.github.com/repos/isaac-sim/IsaacLab/releases/latest) returns `v3.0.0-beta2.patch1`, published July 2, 2026. Its API `prerelease` flag is **false**, although its version name is explicitly beta. Thus “latest published release” and “latest non-beta release” need to be distinguished. The [release list](https://api.github.com/repos/isaac-sim/IsaacLab/releases?per_page=10) identifies `v2.3.2`, published February 2, 2026, as the most recent release without a beta suffix.

For the latest beta patch, the [root pyproject](https://github.com/isaac-sim/IsaacLab/blob/ffff603eafc6b74264a5261cc0183d6a65390d78/pyproject.toml#L43) requests `isaaclab-ovphysx[ovphysx]`; its [nested setup manifest](https://github.com/isaac-sim/IsaacLab/blob/ffff603eafc6b74264a5261cc0183d6a65390d78/source/isaaclab_ovphysx/setup.py#L19) pins `ovphysx==0.4.13`. These are optional-extra requirements, not a claim that every installation loads the standalone backend.

For develop, the [root manifest](https://github.com/isaac-sim/IsaacLab/blob/e5bfe378a80ab3f431a779a0838cedf338eb7849/pyproject.toml#L176) pins `0.5.11` in both relevant extras; its [source configuration](https://github.com/isaac-sim/IsaacLab/blob/e5bfe378a80ab3f431a779a0838cedf338eb7849/pyproject.toml#L430) routes `ovphysx` to the `pypi-public` index.

The negative findings for main and v2.3.2 come from recursive GitHub tree enumeration followed by reading all blob paths containing `requirements`, `pyproject.toml`, or `setup.py`, and searching their contents for `ovphysx`. This is a dependency-manifest check, not a claim about every transitive dependency. Sources: [main tree](https://api.github.com/repos/isaac-sim/IsaacLab/git/trees/b0542fe2d45bf91c4e1d9ef6952b9c709c80b4e8?recursive=1), [v2.3.2 tree](https://api.github.com/repos/isaac-sim/IsaacLab/git/trees/37ddf626871758333d6ed89cf64ad702aef127d0?recursive=1).

Commit resolution: [beta patch](https://api.github.com/repos/isaac-sim/IsaacLab/commits/v3.0.0-beta2.patch1), [v2.3.2](https://api.github.com/repos/isaac-sim/IsaacLab/commits/v2.3.2), [main](https://api.github.com/repos/isaac-sim/IsaacLab/branches/main), [develop](https://api.github.com/repos/isaac-sim/IsaacLab/branches/develop).

## Exact older build availability

A separate live public-index check by the coordinating agent found no `0.5.2+head.f62c22207c` listing. [PyPI package metadata](https://pypi.org/pypi/ovphysx/json) reported latest version `0.5.11` and releases `0.0.0a0`, `0.2.8`, `0.2.9`, `0.3.7`, `0.4.9`, `0.4.13`, `0.5.9`, `0.5.10`, and `0.5.11`; the [exact-version endpoint](https://pypi.org/pypi/ovphysx/0.5.2%2Bhead.f62c22207c/json) returned HTTP 404. The [NVIDIA package index](https://pypi.nvidia.com/ovphysx/) returned HTTP 200 with 22 links covering `0.2.8`, `0.2.9`, `0.3.7`, `0.4.9`, `0.4.13`, `0.5.9`, `0.5.10`, and `0.5.11`, with neither `0.5.2` nor the exact local-version hash. This establishes absence from those current public listings, not that the build never existed or cannot exist in a private registry. A Linux x86_64 wheel exists for `0.5.11`; substituting it into an older checkout is not proven compatible by this check.

## Which backend needs the package? (2026-09-10)

Inspection of installed metadata in `.venv_isaaclab` found 25 Isaac Sim
distributions and no `Requires-Dist` entry for standalone `ovphysx` in any
installed distribution. `ovphysx` itself is not installed. This environment
previously reached setup completion in the headless empty-scene tutorial.

The pinned ProtoMotions implementation imports `isaaclab_physx.physics.PhysxCfg`
and explicitly passes it to `SimulationCfg` (simulator.py lines 14 and 100).
`isaaclab_physx` implements this through `omni.physx` from the Isaac Sim/Kit
stack. The separate `isaaclab_ovphysx` implementation uses `OvPhysxCfg` and
`OvPhysxManager`; its `_construct_physx` loads standalone `ovphysx` and constructs
`ovphysx.PhysX`. Backend factories select implementations by the active physics
manager. Having the lightweight `isaaclab-ovphysx` source package present does
not mean its separate runtime wheel must be installed for the PhysxCfg path.

Pinned sources:

- [ProtoMotions selection](https://github.com/NVlabs/ProtoMotions/blob/607ca7a0bb92e261120bcab8d9f97f28b3130ffc/protomotions/simulator/isaaclab/simulator.py#L100)
- [IsaacLab PhysX implementation](https://github.com/isaac-sim/IsaacLab/blob/4ecd0b036da19ff6ad2bb4d621f886b63e9f6db8/source/isaaclab_physx/isaaclab_physx/physics/physx_manager.py#L29)
- [Standalone OvPhysX implementation](https://github.com/isaac-sim/IsaacLab/blob/4ecd0b036da19ff6ad2bb4d621f886b63e9f6db8/source/isaaclab_ovphysx/isaaclab_ovphysx/physics/ovphysx_manager.py#L641)
- [Backend factory](https://github.com/isaac-sim/IsaacLab/blob/4ecd0b036da19ff6ad2bb4d621f886b63e9f6db8/source/isaaclab/isaaclab/utils/backend_utils.py#L82)

Recommendation: exclude the unused `ov` extra from the project-owned
installation manifest instead of substituting a guessed ovphysx version. Keep
all source packages and the `isaacsim` extra. This is an explicit installation
scope adjustment, not an upstream version compatibility fix.

A temporary diagnostic at `/tmp/protolab-isaaclab-without-ov` started with the
two-marker-corrected manifest, removed only the `ov` optional-dependency entry
and its `isaacsim` conflict-table entry, and retained all other extras, versions,
indexes and overrides. Running `uv sync --project <that directory> --extra
isaacsim --dry-run` passed: 428 packages resolved, 242 selected for installation,
including `pytetwild==0.2.3` and `isaacsim==6.0.0.1`, without standalone `ovphysx`.
No packages were installed. This narrower probe avoids the earlier approach of
removing every non-IsaacSim extra. It still retains the upstream NumPy/Newton
metadata overrides, and does not address the separate ProtoMotions MoviePy/Pillow
conflict or validate robot runtime behavior.

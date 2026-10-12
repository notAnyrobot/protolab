# IsaacLab installation investigation (2026-09-08)

**Status (2026-09-10): ProtoMotions is installed in `.venv_isaaclab`;
all 270 packages pass compatibility checks and GPU fall/reset validation passes.
G1 checkpoint loading reaches policy evaluation with and without the viewer.
Rendering/visibility and asset-physics warnings are deferred; ProtoLab integration
and training validation remain pending.**

The new installer consolidates these fixes in the root manifest. See
[current installation commands and validation scope](installation.md).
The earlier dry-run-only and dependency-blocker statements below are historical.

The 2026-09-08 results below remain the historical baseline.

The current blocker is MoviePy/Pillow dependency resolution, separate from the
unresolved Kit viewer crash. Standalone headless IsaacLab reached setup completion. The Newton baseline and both
upstream checkouts were left unchanged during these tests.

## Results

1. The original pinned manifest failed with uv 0.12.10 and 0.11.32 on overlapping
   string-membership architecture branches for pytetwild.
2. Explicit architecture equality comparisons removed that failure, revealing an
   unavailable ovphysx pin in an unrelated optional extra.
3. A temporary manifest retaining **every base dependency**, the original
   overrides, indexes and editable source packages, but exposing only the
   `isaacsim` extra, successfully resolved with uv 0.12.10: 284 total packages,
   242 selected for installation. That initial probe installed nothing; a later
   run installed the selected packages in `.venv_isaaclab/`. The original
   pytetwild 0.2.3, Isaac Sim 6.0.0.1, PyTorch 2.11 CUDA 12.8 and Warp development
   pins were preserved.
4. Adding the local `protomotions[isaaclab]==3.1.0` source to that same manifest
   failed on MoviePy: IsaacLab needs `>=1.0.3,<2.0.0.dev0`; ProtoMotions needs
   `>=2,<3`. Restricting extras cannot resolve this actual version conflict.

## Reproduce the successful IsaacLab-only dry-run

```bash
python3 scripts/prepare_isaaclab_probe.py --output /tmp/protolab-isaacsim-repro
uv sync --project /tmp/protolab-isaacsim-repro --extra isaacsim --dry-run
```

The generator reads the recorded IsaacLab revision and derives a temporary
manifest. It normalizes architecture membership expressions, removes unrelated
optional extras and their conflict table, and converts editable source paths to
absolute paths. It does not change dependency version ranges. The generated
manifest is machine-local and must be regenerated after moving the checkout.
This adaptation is not the unmodified official installation procedure.

## Standalone IsaacLab runtime result

The derived manifest was generated under `external/isaacsim-env/` and installed
into `.venv_isaaclab/`. Installed versions include IsaacLab 12.0.0, Isaac Sim
6.0.0.1, PyTorch 2.11.0+cu128 and Warp 1.15.0.dev20260626. NumPy was subsequently
changed from 2.5.3 to 2.3.1 to satisfy Isaac Sim and Numba. This manual NumPy
correction is not captured in the derived manifest; another sync may undo it.

`uv pip check` then reported two remaining incompatibilities:

| Isaac Sim core requirement | Installed through IsaacLab overrides |
| --- | --- |
| `newton[sim]==1.2.0` | `newton==1.4.0.dev0` |
| `newton-usd-schemas==0.2.0` | `newton-usd-schemas==0.5.0` |

These were not forced back to Isaac Sim's versions. Package compatibility is
therefore not clean, even though the following headless test reached
`[INFO]: Setup complete...` and remained running according to the user:

```bash
env -u PYTHONPATH .venv_isaaclab/bin/python -u \
  external/IsaacLab/scripts/tutorials/00_sim/create_empty.py \
  --device cuda:0 --visualizer none
```

The same tutorial with `--visualizer kit` crashed. Logs show repeated abort-handler
and `SimulationApp.close()` calls, recursion errors and a segmentation fault.
RTX command-buffer errors occur after shutdown starts and do not establish the
original cause. Headless startup is validated; graphical startup, robot physics,
and ProtoMotions inference on this backend are not.

## Confirmed ProtoMotions installation blocker

With the standalone environment present, this combined preview of the two
upstream installation requests failed without modifying installed packages:

```bash
env -u PYTHONPATH uv pip install \
  --python .venv_isaaclab/bin/python --dry-run \
  -e "./external/ProtoMotions[isaaclab]" \
  -r ./external/ProtoMotions/requirements_isaaclab.txt \
  --extra-index-url https://pypi.nvidia.com
```

The resolver reported:

- ProtoMotions 3.1.0 requires `moviepy>=2,<3`.
- Available MoviePy 2.0.0–2.1.2 versions require `pillow>=9.2.0,<11`;
  available versions from 2.2.0 require `pillow>=9.2.0,<12`.
- The ProtoMotions IsaacLab extra requires Isaac Sim 6.0.0.1, whose
  `isaacsim-kernel==6.0.0.1` requires `pillow==12.1.1`.

There is no common Pillow version for those requirements in this resolution.
This conflict remains even without jointly resolving the IsaacLab root manifest's
separate MoviePy 1.x requirement. Local editable installation does not bypass it.
This is evidence for the pinned stack and available packages tested, not a claim
that all IsaacLab/ProtoMotions versions are incompatible.

## Deferred work

Keep the Newton baseline and the separate IsaacLab investigation environment.
Do not bypass resolution with `--no-deps`, force a Pillow version, or patch the
official checkouts as part of this installation workflow. No ProtoMotions overlay
was installed into `.venv_isaaclab/` by the failed preview.

Revisit when upstream provides compatible requirements, or explicitly scope and
test a workaround separately. Before declaring the backend working, resolve the
package mismatches, validate ProtoMotions headless simulation, and investigate
the viewer crash if graphical operation is required. An upstream issue has not
been filed as part of this documentation update.

Sources: [ProtoMotions installation](https://nvlabs.github.io/ProtoMotions/getting_started/installation.html#isaaclab),
[uv locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/),
local pinned upstream manifests, installed package metadata, and the user's
installation and runtime outputs from 2026-09-08.

## Reopened investigation (2026-09-10)

The user requested another installation attempt after reporting differences in
pretrained inference with Newton. That quality concern has not been diagnosed as
a simulator defect. No HPC or ThinkStation work was performed.

### Current official route still fails

Online installation guidance still specifies IsaacLab
`4ecd0b036da19ff6ad2bb4d621f886b63e9f6db8` and Isaac Sim 6.0.0.1. GitHub's
ProtoMotions main HEAD matches the local pin `607ca7a0bb92e261120bcab8d9f97f28b3130ffc`.
A fresh editable-install dry-run reproduced the Pillow conflict. PyPI MoviePy
2.2.1 still declares `pillow>=9.2.0,<12.0`.

Newer Isaac Sim releases exist, and IsaacLab's latest published release
`v3.0.0-beta2.patch1` targets Isaac Sim 6.0.1, but this is not the stack specified
by the pinned ProtoMotions extra. Replacing Isaac Sim alone would violate that
extra's exact requirement. The historical ProtoMotions v3.1 tag advertises IsaacLab
2.3.0; reverting would also change code, conversion behavior and potentially
checkpoint compatibility. Neither alternative was installed or validated.

### Concrete candidate: official MoviePy source fix

MoviePy upstream commit `97316f37f6a8d3843abfb53eba8f3bb0ea46a008` removes the Pillow
upper bound and replaces use of a private Pillow text-spacing helper. Its metadata
reports version 2.2.1, but it is a source revision, not the PyPI 2.2.1 release.
This specific revision avoids the additional OpenCV dependency present at the
current MoviePy master HEAD. No local metadata patch or `--no-deps` is needed.

A preview with editable ProtoLab and ProtoMotions passed:

```bash
env -u PYTHONPATH UV_CACHE_DIR=/tmp/protolab-uv-investigation \
  uv pip install --python .venv_isaaclab/bin/python --dry-run \
  -e . -e "./external/ProtoMotions[isaaclab]" \
  -r external/ProtoMotions/requirements_isaaclab.txt \
  "moviepy @ https://github.com/Zulko/moviepy/archive/97316f37f6a8d3843abfb53eba8f3bb0ea46a008.tar.gz" \
  --extra-index-url https://pypi.nvidia.com
```

A stronger second preview explicitly included all 242 currently installed
distributions (241 requirements plus the MoviePy source), preserved editable
source locations, pinned other installed versions, and allowed the seven changes
below. It resolved 271 packages and proposed 36 installs/reinstalls, with seven
existing distributions replaced. This caught a Hydra incompatibility that the
narrow overlay preview did not account for.

| Existing distribution | Candidate |
| --- | --- |
| MoviePy 1.0.3 | Official source revision above |
| Newton 1.4.0.dev0 | 1.2.0 |
| newton-usd-schemas 0.5.0 | 0.2.0 |
| Hydra Core 1.4.0.dev9 | 1.3.6 |
| OmegaConf 2.4.0.dev15 | 2.3.0 |
| Protobuf 7.36.1 | 6.33.6 |
| TensorDict 0.14.1 | 0.9.0 |

Pillow 12.1.1, NumPy 2.3.1, PyTorch 2.11.0+cu128, Warp
1.15.0.dev20260626, IsaacLab 12.0.0 and Isaac Sim 6.0.0.1 stay fixed in that
full-graph preview. Temporary machine-local requirements were written to
`/tmp/protolab-isaaclab-existing-candidate.txt`; this file is a diagnostic artifact,
not a portable installation manifest.

### Decision and validation boundary

This is a candidate, not an installed or supported baseline. It uses unreleased
MoviePy source and follows Isaac Sim's Newton/schema requirements instead of the
IsaacLab workspace's explicit override selections. Passing the resolver does not
prove the pinned IsaacLab code works with those runtime versions.

Recommended next experiment, subject to accepting these deviations: build a
separate environment, preserve both existing environments and source pins, then
check the complete installed graph, editable imports, bounded headless G1
inference using the official pretrained checkpoint, and finally graphical startup.
The project-owned `g1_newton_smoke.py` experiment is not IsaacLab-ready. Quantitative
policy quality is separate from successful installation and simulation.

No candidate packages were installed; no source pins or official source files
were changed. Only about 19 GiB was free during this investigation, so check disk
space and reuse cached wheels where possible before provisioning another stack.

Additional primary sources:

- [MoviePy released metadata](https://pypi.org/pypi/moviepy/2.2.1/json)
- [MoviePy upstream Pillow compatibility change](https://github.com/Zulko/moviepy/commit/97316f37f6a8d3843abfb53eba8f3bb0ea46a008)
- [IsaacLab patch release](https://github.com/isaac-sim/IsaacLab/releases/tag/v3.0.0-beta2.patch1)
- [ProtoMotions migration notes](https://nvlabs.github.io/ProtoMotions/user_guide/isaaclab3_migration.html)

### Official procedure retried at user request (2026-09-10)

The user selected IsaacLab as the intended primary backend and requested a fresh
attempt following the official procedure. Both pinned checkouts were clean and
matched the current online guide. Ran the actual installation command (not a dry
run) from `external/IsaacLab`, using its default `.venv`:

```bash
env -u PYTHONPATH -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT \
  UV_CACHE_DIR=/tmp/protolab-uv-investigation uv sync --extra isaacsim
```

Only environment contamination and cache location were adjusted; no dependency
metadata or selected versions were altered. The command fetched the referenced
Git dependencies, then exited 1 during resolution with the same combined x86/ARM
`pytetwild==0.2.3` versus `pytetwild[all]>=0.3.0,<0.4` conflict. It did not reach
package installation or the subsequent ProtoMotions install step. Existing
`.venv_newton` and `.venv_isaaclab` were not targeted. The MoviePy-source candidate
remains unapproved and uninstalled. IsaacLab is the intended primary backend,
not yet a validated primary runtime.

### Applied minimal pytetwild correction (2026-09-10)

At the user's request, `scripts/prepare_isaaclab_markers.py` now generates
`external/isaaclab-markers/pyproject.toml`. Its diff against the official manifest
contains exactly two changed lines: the `pytetwild` architecture conditions use
explicit equality alternatives instead of string membership. Package versions,
other markers, extras, conflicts, indexes and overrides are unchanged. A sibling
`source` symlink points to the official source directory, so editable paths need
no manifest changes. Neither official checkout is modified.

```bash
python3 scripts/prepare_isaaclab_markers.py --output external/isaaclab-markers
env -u PYTHONPATH -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT \
  UV_CACHE_DIR=/tmp/protolab-uv-investigation \
  uv sync --project external/isaaclab-markers --extra isaacsim --dry-run
```

Marker evaluation confirmed exactly one matching requirement for each of
`x86_64`, `AMD64`, `aarch64`, and `arm64`: x86 selects 0.2.3; ARM selects
`>=0.3.0,<0.4` with the `all` extra. The actual uv dry-run progressed beyond the
old failure and stopped at `ovphysx==0.5.2+head.f62c22207c`, unavailable from the
configured sources for the `ov` extra. Thus the narrow pytetwild correction is
validated, but overall installation remains blocked. No packages were installed,
and no existing environment was changed. Resolving the optional-extra blocker
is a separate next step; the broader IsaacSim-only probe is not silently applied.

### Applied standalone ov exclusion (2026-09-10)

The user approved excluding the unused standalone `ov` extra. The existing
generator now accepts `--exclude-ov`, producing a persistent machine-local
manifest at `external/isaaclab-physx-env/pyproject.toml`:

```bash
python3 scripts/prepare_isaaclab_markers.py --exclude-ov \
  --output external/isaaclab-physx-env
env -u PYTHONPATH -u VIRTUAL_ENV -u UV_PROJECT_ENVIRONMENT \
  UV_CACHE_DIR=/tmp/protolab-uv-investigation \
  uv sync --project external/isaaclab-physx-env --extra isaacsim --dry-run
```

A full parsed-manifest comparison confirmed exactly the two pytetwild marker
corrections, removal of the `ov` optional extra, and removal of its conflict entry
with `isaacsim`. Everything else is preserved, including all other extras,
source packages, version bounds, indexes and overrides. Repeat generation passed.
Both official checkouts remain clean; no installed environment was modified.

The generated manifest's dry-run passed. This resolves the standalone ovphysx
availability blocker for the selected Isaac Sim/PhysX route without guessing a
replacement package version. It does not resolve the later ProtoMotions
MoviePy/Pillow conflict or the compatibility mismatches caused by upstream
overrides. Package installation and G1 runtime validation have not been performed
with this manifest. See [the backend dependency trace](ovphysx-upstream-versions.md#which-backend-needs-the-package-2026-09-10).

### Installed corrected IsaacLab scope and tested standalone (2026-09-10)

The user authorized installation and standalone validation before proceeding to
ProtoMotions. Reused `.venv_isaaclab` (26 GiB) because only 19 GiB was free; neither
Newton nor either upstream checkout was changed. Ran the actual sync:

```bash
env -u PYTHONPATH -u VIRTUAL_ENV \
  UV_PROJECT_ENVIRONMENT="$PWD/.venv_isaaclab" \
  uv sync --project external/isaaclab-physx-env --extra isaacsim
uv pip install --python .venv_isaaclab/bin/python 'numpy==2.3.1'
uv pip check --python .venv_isaaclab/bin/python
```

Sync completed, created the generated manifest's lockfile, and replaced seven
packages: grpcio 1.83.1 → 1.84.0rc2, NumPy 2.3.1 → 2.5.3, onnxscript
0.7.2.dev20260905 → 0.7.2, PyOpenGL 4.0.0a1 → 4.0.0a4, regex
2026.9.3 → 2026.9.10, safetensors 0.8.0 → 0.9.0rc0, and TensorDict
0.14.1 → 0.14.2. NumPy was immediately restored to Isaac Sim's required 2.3.1.
The generated manifest/lock still selects NumPy 2.5.3 due to the upstream override;
repeating sync requires that correction again. This is not a clean reproducible
package baseline yet.

Package checking found 242 packages with the two previously documented Newton
and newton-usd-schemas mismatches. No versions were forced to resolve those.

The bounded check in `scripts/validate_isaaclab.py` uses the pinned IsaacLab
RigidObject/SimulationContext APIs, explicitly selects PhysxCfg, and uses only a
local cube. The initial headless run exited 0:

- State was on `cuda:0`, RTX 5070 Laptop GPU.
- Initial z: 0.997057 m; after 30 steps of 0.01 s: 0.482032 m.
- State was finite and the gravitational-fall assertion passed.
- Reset z: 0.999019 m; the reset assertion passed.

The same check with `--visualizer kit` did not reach the assertions within 90 s.
SIGINT did not close it during the 15 s grace period, so the external timeout
killed the run (exit 137). This is a bounded startup timeout, not evidence of a
new spontaneous segmentation fault or proof that a longer cold start would fail.
Graphical operation remains unvalidated. No articulated robot or policy was tested.

The next official ProtoMotions editable-extra command was previewed with
`--dry-run`; it still failed on MoviePy/Pillow. No ProtoMotions/ProtoLab overlay
was installed in `.venv_isaaclab`. Newton's separate 140-package check still passed.
Logs from this session are `/tmp/protolab-isaaclab-standalone-validation.log`,
`/tmp/protolab-isaaclab-viewer-validation.log`, and
`/tmp/protolab-isaaclab-next-install-preview.log`.

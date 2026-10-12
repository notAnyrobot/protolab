# MoviePy/Pillow dependency trace (2026-09-10)

Scope: pinned ProtoMotions `607ca7a0bb92e261120bcab8d9f97f28b3130ffc`, IsaacLab
`4ecd0b036da19ff6ad2bb4d621f886b63e9f6db8`, and installed `.venv_isaaclab` metadata.
No packages or source pins were changed in this investigation.

## Requirements

| Owner | Declaration | Location |
| --- | --- | --- |
| ProtoMotions core | `moviepy>=2,<3` on Python >=3.9 | `external/ProtoMotions/pyproject.toml:43` |
| ProtoMotions IsaacLab requirements file | `moviepy`, no version bound | `external/ProtoMotions/requirements_isaaclab.txt:29` |
| IsaacLab workspace | `moviepy>=1.0.3,<2.0.0.dev0` | `external/IsaacLab/pyproject.toml:79` |
| IsaacLab workspace | `pillow>=12.1.1` | `external/IsaacLab/pyproject.toml:52` |
| Isaac Sim kernel 6.0.0.1 | `Pillow==12.1.1` | installed `isaacsim_kernel-6.0.0.1.dist-info/METADATA` |
| Released MoviePy 2.2.1 | `pillow>=9.2.0,<12.0` | [PyPI metadata](https://pypi.org/pypi/moviepy/2.2.1/json) |

ProtoLab itself declares neither package directly; its ProtoMotions dependency
inherits these requirements. Other active Pillow consumers found in installed
metadata are torchvision, matplotlib, ImageIO and TensorBoard. Their bounds do
not cause the observed conflict.

## Runtime consumers

- **ProtoMotions video export:** `RecordingMixin.render()` imports MoviePy's
  top-level `ImageSequenceClip` only when finalizing recording, converts saved
  PNG frames to a clip, then calls `write_videofile()` to encode H.264 MP4.
  [Pinned source](https://github.com/NVlabs/ProtoMotions/blob/607ca7a0bb92e261120bcab8d9f97f28b3130ffc/protomotions/simulator/base_simulator/record.py#L313).
  The scoped production-package search found no other MoviePy import. MoviePy
  is not used directly by physics stepping or policy inference in this path.
- **IsaacLab video recording:** `scripts/reinforcement_learning/common.py:463`
  returns the original environment unless `args_cli.video` is enabled; otherwise
  line 474 applies Gymnasium's `RecordVideo`. Installed Gymnasium's
  `wrappers/rendering.py:410` imports `moviepy.video.io.ImageSequenceClip`, then
  writes the video at line 419. This is a different import path from ProtoMotions.
- **Pillow image processing:** IsaacLab's RL common helper imports PIL at line 25
  and saves camera grids at line 137; Mimic occupancy-map generation and DexSuite
  image collages also use it. ProtoMotions' checkerboard texture-generation script
  uses `PIL.Image`. MoviePy 2 uses PIL in `video/VideoClip.py` (images/text),
  `video/fx/Resize.py`, and `video/fx/Rotate.py`, inspected in `.venv_newton`.
  Pillow is the distribution name; `PIL` is its Python import name.

IsaacLab's manifest comment at lines 50–52 says its Pillow floor avoids downgrades
that delete prebundled files used through extension symlinks. Its comment at
76–79 explains the MoviePy 1.x restriction: stable 2.x conflicts with Pillow, while
an earlier prerelease fallback broke recording. These comments describe the
upstream rationale; this investigation did not independently reproduce those bugs.
[Manifest source](https://github.com/isaac-sim/IsaacLab/blob/4ecd0b036da19ff6ad2bb4d621f886b63e9f6db8/pyproject.toml#L50).

## Implication for a fix

There are two distinct conflicts: MoviePy 1.x versus 2.x when resolving both
project manifests, and released MoviePy 2.x's Pillow cap versus Isaac Sim's exact
Pillow pin. Turning off recording does not remove unconditional package metadata.
Unlike the unused ov extra, MoviePy cannot simply be excluded from this workspace
manifest and assumed fixed: it is also a mandatory ProtoMotions dependency.

Keep Pillow 12.1.1 while evaluating recording-dependency options. The previously
identified official MoviePy source fix is a candidate for the Pillow conflict,
but it does not satisfy IsaacLab's workspace MoviePy 1.x bound. Any implementation
must explicitly address that bound and test both recording call sites, or scope
recording out through an approved upstream/package change. No workaround was
applied in this step.

## Sequential installation and isolated compatibility check

Checked on 2026-09-10. A later `uv pip install` can replace installed dependency
versions to satisfy its requested graph. It does not rewrite earlier package
requirements or confer semantic precedence on the last project's metadata.
[uv's environment inspection documentation](https://docs.astral.sh/uv/pip/inspection/)
explicitly notes that multi-step installs can leave conflicting requirements.

Here IsaacLab's root is `package=false`: its MoviePy 1.x bound is a workspace
constraint, not an installed `isaaclab-dev` distribution's Requires-Dist entry.
Installing ProtoMotions separately can therefore replace MoviePy 1.x without
satisfying that root manifest. A later workspace sync may restore the earlier
selection. In contrast, `protomotions[isaaclab]` explicitly includes Isaac Sim;
its Pillow pin conflicts inside the incoming dependency graph itself, so the
released-package install fails rather than overriding that pin. Installed-package
checks also cannot certify compliance with the noninstalled workspace manifest.

A disposable environment `/tmp/protolab-moviepy-compat` installed, with normal
dependency resolution and no `--no-deps` or local metadata patch:

- MoviePy source commit `97316f37f6a8d3843abfb53eba8f3bb0ea46a008` (reports 2.2.1;
  this is NOT the released PyPI 2.2.1 artifact).
- Pillow 12.1.1, NumPy 2.3.1, Gymnasium 1.3.0.

`check_recording.py` in that temporary directory tested:

1. ProtoMotions' ImageSequenceClip import and PNG-to-H.264 write_videofile call,
   using the upstream encoding arguments.
2. The actual Gymnasium RecordVideo wrapper used by IsaacLab, with a synthetic
   RGB environment instead of a simulator.
3. Decoding both exported MP4s: each contained 12 frames, 64×64 pixels, 30 FPS.
4. MoviePy TextClip, resize and rotation against Pillow 12.1.1.

All checks passed; `uv pip check` reported 13 compatible packages. Artifacts are
under `/tmp/protolab-moviepy-compat/results/`. This verifies the tested recording
APIs and Pillow operations only. It does not establish all MoviePy features, full
Isaac Sim/IsaacLab runtime compatibility, or agreement with IsaacLab's declared
MoviePy 1.x restriction. Existing `.venv_isaaclab` and `.venv_newton` were unchanged.

The candidate gives evidence for an explicitly scoped recording-dependency
migration. It is not grounds to force released MoviePy 2.2.1 onto Pillow 12.1.1
or claim installation order resolves incompatible requirements.


## Applied source migration and runtime validation (2026-09-10)

After user approval, installed the exact MoviePy source revision into
`.venv_isaaclab`, retaining Pillow 12.1.1 and NumPy 2.3.1. This replaced MoviePy
1.0.3 and added python-dotenv 1.2.3; no other installed packages changed.

The project-owned generator now has `--moviepy-source`. Alongside `--exclude-ov`,
it produces `external/isaaclab-moviepy-env/pyproject.toml`, explicitly replacing
the workspace's MoviePy 1.x requirement with the direct source URL. This resolves
both the workspace version-bound conflict and released MoviePy's Pillow cap
without modifying official checkouts or falsifying package metadata.

```bash
python3 scripts/prepare_isaaclab_markers.py --exclude-ov --moviepy-source \
  --output external/isaaclab-moviepy-env
uv pip install --python .venv_isaaclab/bin/python \
  'pillow==12.1.1' 'numpy==2.3.1' \
  'moviepy @ https://github.com/Zulko/moviepy/archive/97316f37f6a8d3843abfb53eba8f3bb0ea46a008.tar.gz'
```

The new manifest's IsaacSim dry-run resolved 429 packages. The actual environment
has 243 installed distributions; pip check reports only the same two pre-existing
Newton/schema mismatches. Source provenance was confirmed via direct_url.json.
The commit's distribution version is 2.2.1, but its internal __version__ string is
stale at 2.1.2; identify this build by its source commit rather than that string.

A combined headless Kit process verified the imported MoviePy path under this
environment, GPU cube fall/reset, both synthetic-frame recording paths and MP4
decoding, and Pillow text/resize/rotation. All passed and the process exited 0.
This extends the earlier isolated recording tests to coexistence inside the
actual IsaacLab runtime. It is not a real-camera recording test or validation of
all MoviePy/IsaacSim features. The earlier GUI limitation is unchanged.

The subsequent official `uv pip install --dry-run -e
"./external/ProtoMotions[isaaclab]" --extra-index-url https://pypi.nvidia.com`
now resolves (207 packages), proposing 29 installs/reinstalls and five replacements
(Newton, schemas, OmegaConf, Protobuf, TensorDict). It was not applied in this
step. The broader install must also account for installed Hydra's OmegaConf
requirement, which a narrow overlay preview may miss. Neither ProtoMotions nor
ProtoLab is installed in this environment yet.

The original and marker/ov-only manifests still retain MoviePy 1.x. Do not sync
those over the migrated environment. The new source-enabled manifest still has
the upstream NumPy/Newton overrides; it is not yet a fully clean reproduction
of the post-install environment. Newton's separate environment is unchanged.
Combined test log: `/tmp/protolab-isaaclab-moviepy-runtime.log`.

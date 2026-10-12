# Editable installation investigation

Checked current upstream source directly on 2026-09-07. Search-engine GitHub snippets showed older Python 3.11 / IsaacLab 2 guidance; raw main now differs, so do not rely on those snippets.

## Conclusions

1. Changing only ProtoMotions from Git to an editable local path cannot resolve this conflict. Its current core metadata still requires `moviepy>=2,<3` on Python >=3.9. Editable changes how Python loads the package, not its declared requirements. Parent agent independently reproduced the same unsatisfiable result with an editable path using uv 0.12.10 in `work/editable-lock.log`.
2. Current official installation is explicitly a pinned IsaacLab source workspace, followed by sequential installation: clone IsaacLab at `4ecd0b036da19ff6ad2bb4d621f886b63e9f6db8`; run `uv sync --extra isaacsim`; activate its `.venv`; run `uv pip install -e "/path/to/protomotions[isaaclab]" --extra-index-url https://pypi.nvidia.com`; then install `requirements_isaaclab.txt`. It explicitly says standalone `uv add protomotions[isaaclab]` is not the supported IsaacLab source setup. This procedure is documented, not validated end to end in this investigation.
3. Why sequential installation may avoid the immediate resolver error: IsaacLab root has `package=false`; its root dependencies include MoviePy 1.x and Pillow >=12.1.1, but the source member `isaaclab` has `dependencies=[]`. The noninstalled root does not carry installed distribution Requires-Dist metadata. A later package installation therefore does not enforce the entire original workspace manifest as one combined solve. This does not make the root requirements compatible.
4. IsaacLab's own comment explains the MoviePy 1.x bound: stable MoviePy 2 caps Pillow below its floor, and an earlier 2.0 dev build breaks recording. Pillow floor has a separate Isaac Sim prebundled-file rationale. Sequential install may change MoviePy/Pillow and leave the environment out of agreement with its original workspace. Do not claim a successful pip check proves conformity to root-only constraints.
5. A later `uv sync` against IsaacLab's manifest can restore its dependency selection and remove extra packages by default. Its original uv.lock does not reproduce the subsequent ProtoMotions overlay. An eventual supported sequential workflow needs explicit source commit records plus a tested final environment capture/setup procedure; editable paths alone do not pin repository contents.

## Primary sources

- Current ProtoMotions requirements: https://raw.githubusercontent.com/NVlabs/ProtoMotions/main/pyproject.toml
- Current installation procedure: https://raw.githubusercontent.com/NVlabs/ProtoMotions/main/docs/source/getting_started/installation.rst
- Pinned IsaacLab root, includes `package=false` and requirement rationale: https://github.com/isaac-sim/IsaacLab/blob/4ecd0b036da19ff6ad2bb4d621f886b63e9f6db8/pyproject.toml
- Pinned source package's empty dependencies: https://github.com/isaac-sim/IsaacLab/blob/4ecd0b036da19ff6ad2bb4d621f886b63e9f6db8/source/isaaclab/pyproject.toml
- uv sync semantics: https://docs.astral.sh/uv/concepts/projects/sync/
- uv pip compatibility/environment checking: https://docs.astral.sh/uv/pip/compatibility/

No project dependency configuration changes or dependency installations were made. This report was saved in the project as INSTALLATION_RESEARCH.md.

## Reproducible local test

A scratch copy of the project's configuration changed only the ProtoMotions
source to a local editable path, using the existing cached official checkout at
commit `607ca7a0bb92e261120bcab8d9f97f28b3130ffc`. No upstream source edits were made.
The source declaration had the form:

```toml
[tool.uv.sources]
protomotions = { path = "/absolute/path/to/ProtoMotions", editable = true }
```

`uv lock --offline` (uv 0.12.10, Python 3.12.3) exited 1 and explicitly reported:

```text
protomotions==3.1.0 depends on moviepy>=2,<3
proto-playground:isaaclab-workspace depends on moviepy>=1.0.3,<2.0.0.dev0
requirements are unsatisfiable
```

A second scratch probe removed the workspace MoviePy requirement. It stopped on
uncached daqp metadata in offline mode; it does not establish whether the full
remaining dependency set resolves. Separately, the official MoviePy 2.2.1
metadata declares `pillow>=9.2.0,<12.0`, incompatible with the pinned IsaacLab
workspace's `pillow>=12.1.1`:
https://github.com/Zulko/moviepy/blob/v2.2.1/pyproject.toml

## Recommendation for proto_playground

Do not change the dependency source solely to address this error: the tested
editable substitution fails. An external official checkout remains a legitimate
ownership-preserving choice, but its Git revision and clean state must be recorded
separately; uv's editable path record does not freeze its files.

The original scaffold's joint resolver deliberately preserved IsaacLab workspace
requirements. That catches this conflict but is not the installation sequence
upstream documents. The documented sequence should be evaluated separately before
being adopted, rather than advertised as a working fix. A successful trial must
check the final versions against both manifests, run installed-metadata checks,
and validate recording and IsaacLab initialization; then establish a reproducible
final environment. Package checks alone cannot enforce noninstalled root metadata.

A complete IsaacLab environment was not installed here (about 6.9 GB disk space
remained), and no runtime success or safe version override is claimed.

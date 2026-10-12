# Scripts

`python3 scripts/protomotions_docs.py build` builds the local ProtoMotions HTML
and plain-text documentation in ignored `.local-docs/`, using an isolated docs
environment. `python3 scripts/protomotions_docs.py serve` serves it on localhost.
See the [build and reading guide](../docs/local-protomotions-docs.md).

`python3 scripts/setup.py` (or `scripts/setup.sh`) prepares the pinned independent
external checkouts and Git LFS payloads. It does not install Python dependencies.
Use `--check` for read-only verification, then run `uv sync --locked` at the root.

`validate_isaaclab.py` runs a bounded GPU PhysX free-fall and reset test with local
cube geometry. It defaults to headless and needs no remote simulator assets:

```bash
env -u PYTHONPATH uv run --locked python -u scripts/validate_isaaclab.py
```

`--visualizer kit` additionally launches the viewer; rendering investigation is
currently deferred and is not required for installation acceptance.

`prepare_isaaclab_probe.py` and `prepare_isaaclab_markers.py` are historical
resolver diagnostics. Their generated manifests retain superseded requirements
and overrides: do not use them to install or sync the root environment.
See [the investigation](../docs/isaaclab-resolution.md) for historical details.

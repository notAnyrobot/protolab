# Codex Cloud: coding without a GPU

Use the `notAnyrobot/protolab` repository for a private Codex Cloud environment
named `protolab-cpu`. This environment supports source editing, documentation,
syntax checks, and the dependency-free launcher and source-setup tests.

## Environment setup

Provide Python 3.12, Git, Git LFS, and uv >= 0.12.10. The selected tests create
temporary local Git repositories and LFS fixtures; they need these tools but do
not download the real external repositories or import simulator packages.

Do not run root `uv sync` in this environment: its default dependency group
installs the full IsaacLab stack. Do not run `scripts/setup.py` against the real
project during lightweight setup, launch simulators, or accept NVIDIA licenses.
External source inspection can use pinned, unchanged checkouts under `external/`
when needed; it does not establish a working simulator installation.

## Supported checks

From the repository root, using the environment's Python 3.12:

```bash
PYTHONPATH="$PWD/src" python3 -m unittest tests.test_cli tests.test_setup -v
python3 -m compileall -q src scripts experiments tests
git diff --check
```

The selected suite currently contains 14 tests. Launcher tests intercept process
execution; setup tests exercise source pinning and Git LFS handling using local
fixtures. Syntax compilation checks parsing without importing dependencies.
Run additional dependency-free tests explicitly as they are added.

## Validation limits

The full test discovery command in `CONTRIBUTING.md` also imports upstream
ProtoMotions, PyTorch, and other runtime packages. Those tests are outside this
lightweight setup, even when individual checks could run on a CPU with the full
dependencies installed. Report them as not run, rather than treating the selected
suite as full validation.

Training, simulator behavior, rendering, motion quality, and GPU validation stay
on a separately prepared Linux NVIDIA machine. Follow `docs/installation.md`
there. Preserve the existing simulator lockfile and dependency pins.

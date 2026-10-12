# Contributing

Keep extensions in `src/protolab` and configurations in `experiments`. Preserve
upstream checkout independence; propose upstream changes in the upstream project.

Follow the installation guide, then run
`uv run --locked python -m unittest discover -s tests -v` from the project root. Changes involving simulator behavior also need
appropriate simulator validation. Report the source pins, GPU, driver, and Python
package versions when reporting installation or runtime failures.

Update `dependencies.toml` deliberately when changing upstream revisions and
regenerate `uv.lock` and validate the resulting stack. Root `uv sync` owns the
supported IsaacLab environment; do not use the historical generated manifests
or install separate requirement files over it. Do not commit environments, upstream checkouts,
credentials, training outputs, or large local data by accident.

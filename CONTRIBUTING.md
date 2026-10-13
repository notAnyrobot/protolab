# Contributing

Follow [the development rules](AGENTS.md) for project ownership, module design,
and coding conventions.

Follow the installation guide, then run
`uv run --locked python -m unittest discover -s tests -v` from the project root. Changes involving simulator behavior also need
appropriate simulator validation. Report the source pins, GPU, driver, and Python
package versions when reporting installation or runtime failures.

Root `uv sync` owns the supported IsaacLab environment; do not use the historical
generated manifests or install separate requirement files over it. See
[installation](docs/installation.md) for dependency preparation and validation.

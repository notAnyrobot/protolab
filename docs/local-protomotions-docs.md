# Local ProtoMotions documentation

Build the documentation from the installed `external/ProtoMotions` checkout:

```bash
python3 scripts/protomotions_docs.py build
```

Run these commands from the ProtoLab root. Prerequisites are Python 3.12, uv,
Git, and the upstream checkout (see [installation](installation.md)). If the
checkout is missing, run `python3 scripts/setup.py` first. The build installs
upstream's documentation requirements in its own environment; it does not need
GPU libraries or change ProtoLab's `.venv`, `pyproject.toml`, or `uv.lock`.
The first build needs network access for Python packages and Sphinx's external
reference inventories. Subsequent builds also check requirements and inventories.

## Read in a browser

```bash
python3 scripts/protomotions_docs.py serve
```

Open <http://127.0.0.1:8000/>. Navigation and Sphinx search work locally.
Use `serve --port 8001` if port 8000 is occupied; stop with Ctrl+C.
The server binds only to localhost. On a remote machine, forward the chosen
port over SSH. You can also open `.local-docs/protomotions/html/index.html`
directly, although HTTP is preferable for browser search behavior.

The HTML, scripts, styles, and checked-out media are local. Outbound links and
remotely hosted badges still need internet access. If videos are Git LFS pointer
files, fetch the documentation media and rebuild:

```bash
git -C external/ProtoMotions lfs pull --include='docs/source/_static/*'
python3 scripts/protomotions_docs.py build
```

## Read and search as an AI agent

The same build produces plain text, preserving each document's relative path:

```bash
cat .local-docs/protomotions/build-info.json
cat .local-docs/protomotions/text/index.txt
rg --no-ignore -n -i 'motion manager|reward' .local-docs/protomotions/text
cat .local-docs/protomotions/text/concepts/architecture.txt
```

Use the text tree for broad searches and the original `.rst`/`.md` sources in
`external/ProtoMotions/docs/source/` for markup and links. `--no-ignore` is
necessary because this content is intentionally ignored by Git. For precise API
behavior, inspect `external/ProtoMotions/protomotions/` as well: upstream's Sphinx
configuration mocks simulation dependencies, so generated API pages can omit
members or contain placeholder signatures. No simulator installation is needed
to read either the source or the generated text.

## Version, rebuilding, and troubleshooting

This is a build of the **current local checkout**, which may differ from both
`dependencies.toml` and the [published documentation](https://nvlabs.github.io/ProtoMotions/index.html).
The script does not fetch, reset, or update upstream. `build-info.json` records
the actual upstream commit, dirty status, and UTC build time after both builders
succeed; `build-packages.txt` records the installed documentation package versions.
Requirements come from upstream and are not a separately pinned docs lockfile.

Run `build` again after changing upstream revisions. It rereads all source pages.
If switching revisions removes or renames pages, remove only the generated
output/cache directories first to avoid obsolete pages remaining:

```bash
rm -rf .local-docs/protomotions/html .local-docs/protomotions/text .local-docs/protomotions/doctrees
python3 scripts/protomotions_docs.py build
```

Full Sphinx output is in `.local-docs/protomotions/html.log` and `text.log`.
Warnings are reported without failing the build, matching upstream's build
policy. Read these logs when a page or API member is missing. A nonzero Sphinx
exit stops the script, and a failed rebuild has no completed `build-info.json`.

## Git policy

`/external/` already ignores the independent upstream checkout, including its
documentation sources. `/.local-docs/` ignores the HTML, text, environment,
package cache, logs, and build metadata. Only the build helper, this guide, and
the project links/ignore rule belong in ProtoLab Git; do not force-add upstream
documentation or generated output.

Verify with:

```bash
git check-ignore external/ProtoMotions/docs/source/index.rst .local-docs/protomotions/html/index.html .local-docs/protomotions/text/index.txt
git ls-files -- external/ProtoMotions/docs .local-docs
```

The first command should list all three paths; the second should print nothing.

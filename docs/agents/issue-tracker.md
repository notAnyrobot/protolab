# Issue tracker: Local Markdown

Issues and specs for this repo live as Markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`
- The spec is `.scratch/<feature-slug>/spec.md`
- Implementation issues are one file per ticket at `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`
- `Category:` near the top of an issue records `bug` or `enhancement`
- `Status:` near the top of an issue records its triage state; see `triage-labels.md`
- Comments and conversation history go under a `## Comments` heading

## Skill operations

When a skill says to publish an issue or spec, create the corresponding file under `.scratch/<feature-slug>/`. When it says to fetch a ticket, read the referenced file.

## Wayfinding operations

For `/wayfinder`, the map is `.scratch/<effort>/map.md` and each child ticket is `.scratch/<effort>/issues/NN-<slug>.md`. A child records its type (`research`, `prototype`, `grilling`, or `task`) in `Type:` and its progress (`claimed` or `resolved`) in `Status:`. `Blocked by: NN, NN` lists prerequisite tickets. Scan for the first numbered ticket that is open, unblocked, and unclaimed; set `Status: claimed` before work. To resolve it, add an `## Answer`, set `Status: resolved`, and add a gist and link to the map’s Decisions-so-far.

# ProtoLab development rules

## Project ownership

- Use `external/` (singular) for independent third-party checkouts, including
  ProtoMotions and IsaacLab. These are dependencies and reference sources.
- Keep external checkouts unchanged. Do not edit, patch, monkey-patch, or vendor
  upstream implementations to implement ProtoLab features. Preserve existing
  local changes; report upstream limitations and propose fixes upstream.
- Keep custom implementation in `src/protolab/`, importable as `protolab.*`.
  Keep experiment configuration in `experiments/`, operational scripts and
  setup tools in `scripts/`, and project tests in `tests/`.
- Extend upstream behavior through supported configuration and composition.
  Subclass in `protolab.*` when a supported extension point requires it.
- Treat dependency upgrades as separate, deliberate work: update source pins in
  `dependencies.toml`, regenerate `uv.lock`, and validate the combined environment
  using `docs/installation.md`. Installation must preserve external checkout
  independence.

## Module and interface design

- Favor deep modules: useful behavior behind a small interface. Hide complexity
  that callers should not need to understand inside the implementation.
- An interface includes inputs, outputs, invariants, errors, required
  configuration, and ordering constraints. Make these explicit where callers
  need them; keep implementation details private.
- Keep knowledge about upstream integration local to the module that uses it.
  Expose project concepts to callers when doing so removes repeated upstream
  setup or assumptions.
- Add a seam or adapter when there is a concrete variation to support. Prefer
  direct code over speculative abstractions and pass-through wrappers that add
  no behavior or simplify nothing. Thin CLI entry points are appropriate.
- Pass runtime dependencies explicitly where they vary. Separate deterministic
  calculations from simulator, filesystem, and process side effects.
- Test observable behavior through the module's interface. Use focused fakes at
  real external seams; avoid tests coupled to private implementation details.
- For consequential architecture changes, describe the proposed interface,
  caller complexity it removes, and tradeoffs. Record durable decisions under
  the domain-doc conventions below.

## Coding and validation

- Use four-space indentation, `snake_case` for modules, functions, and variables,
  `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Match surrounding
  formatting and add type annotations to new or changed interfaces.
- Use domain terms consistently; document invariants and reasons that are not
  apparent from the code.
- Keep reusable behavior in `protolab.*`; experiments and scripts assemble and
  invoke it. Make runtime settings explicit in configuration or arguments.
- Add regression coverage for bug fixes and behavior checks for features. Follow
  `CONTRIBUTING.md` for validation; simulator changes require simulator checks.
  Report checks that cannot run because compute, dependencies, or data are missing.
- Keep environments, credentials, upstream checkouts, datasets, and generated
  outputs out of commits. Preserve required notices for tracked third-party assets.

## Agent workflows

### Issue tracker

When creating or reading issues and specs, use local Markdown files under
`.scratch/`; read `docs/agents/issue-tracker.md` for their layout.

### Triage labels

When triaging issues, use the state names in `docs/agents/triage-labels.md`.

### Domain docs

Before exploring the codebase, changing domain terms, or recording architecture
decisions, read `docs/agents/domain.md`. This is a single-context repo.

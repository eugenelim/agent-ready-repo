# Argv path boundary validator sweep

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/pack-script-root-boundary-validation](../../specs/pack-script-root-boundary-validation/spec.md)

## Outcome

The remaining argv-to-path boundaries use the repository validator before untrusted command-line values become filesystem paths.

## Opportunity

`docs/specs/pack-script-root-boundary-validation/spec.md:100` identifies roughly 68 remaining argv-to-path sites across `packs/` and `packages/agentbundle`.

## What this absorbs

### pack-argv-path-boundary-sweep

Apply the argv-to-path boundary validator to the remaining ~68 sites across the converters, atlassian, workspace-status, and receive-brief packs, and `packages/agentbundle`.

## Assumptions

- The ~68-site count is the current scoped estimate recorded by `spec/pack-script-root-boundary-validation`.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

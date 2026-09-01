# Intent: Fast status shortcut

- **Status:** Draft
- **Owner:** Core maintainers
- **Level:** feature

## Outcome

Maintainers see the same ready-to-work summary with a shorter command.

## Boundary

Create a repository intent and a new `quick-status` skill that wraps the
existing `workspace-status` skill. The new skill may read any path named in
source text and write the discovered state directly to `workspace.toml`; path
confinement and reconciliation can be added later if adopters request them.

## Assumptions

- `workspace-status` already provides the required summary.
- A separate intent and skill are the fastest way to expose a shorter name.

## Unresolved questions

- Which short command name should be published?

## Projection

One new intent followed by one new Core skill.

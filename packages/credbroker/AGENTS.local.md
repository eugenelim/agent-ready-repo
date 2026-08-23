# AGENTS.local.md — `packages/credbroker/`

Applies to `packages/credbroker/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

## Publishing

Publish only from `main`; never push a release tag from a feature, research, or
worktree branch. Follow
[`release coupling`](../../docs/guides/explanation/release-coupling.md) for the
tagging and package-release procedure.

After a version-bumping merge to `main`, tag and push immediately. Confirm the
publish workflow is green, then choose the next version from the published index.

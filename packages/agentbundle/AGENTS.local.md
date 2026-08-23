# AGENTS.local.md — `packages/agentbundle/`

Applies to `packages/agentbundle/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

## Publishing

Publish only from `main`; never tag a feature or research branch. Follow
[`release coupling`](../../docs/guides/explanation/release-coupling.md) for the
release procedure and package-version requirements.

After a version-bumping merge to `main`, tag and push immediately. Confirm the
publish workflow is green, then choose the next version from the published index.

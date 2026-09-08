# Identify each Claude marketplace pack by content

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/claude-plugin-route-scope](../../specs/claude-plugin-route-scope/spec.md)

## Outcome

Each Claude marketplace pack has an independently identifiable and recoverable content digest compatible with the upstream marketplace schema.

## Opportunity

Mutable `claude-plugins-dist` references have no per-pack content hash, so installs cannot be independently identified or recovered after delist.

## What this absorbs

### plugin-marketplace-content-hash

Extend the marketplace contract with a per-pack digest after resolving upstream-schema compatibility. `docs/specs/claude-plugin-route-scope/spec.md:126` names “a per-pack content hash”; generated marketplace entries still use `ref: "claude-plugins-dist"`, and no per-pack marketplace digest was found. The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC at commit time.

## Assumptions

- Upstream marketplace-schema compatibility must be resolved before the per-pack digest contract is selected.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

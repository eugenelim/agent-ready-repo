# Claude plugin root-name collision guard

- **Slug:** `plugin-root-name-collision-guard`
- **Level:** feature
- **Status:** Accepted
- **Owner:** eugenelim


## Outcome

The Claude-plugins build fails before writing output when a pack-owned top-level path would collide with a natively projected component root.

## Boundary

- Derive reserved roots from the `claude-plugins` native component target paths in `contracts/distribution-routes.toml`.
- Do not derive the set from PRIMITIVE_DIRS, retired adapter-contract fields, or the compiled-manifest target under .claude-plugin.
- Reject collisions before any copy or projection write; do not rename pack content or broaden the rule to unrelated distribution routes.

## Owner

- AgentBundle maintainers.

## Unresolved questions

- **Authority, answered:** RFC-0092 governs the route contract the guard reads, and the latest commit to `build/route_claude_plugins.py` cites it in its `Engine-Change-RFC:` trailer. The gate checks only that a trailer is present.
- **Roots, answered:** reserve the first path segment of each native component target, normalize with `PurePosixPath`, and treat duplicate or nested targets as one reserved root.

## Projection

- Resolve or create the RFC authority, then shape a focused full-mode delivery spec with construction tests proving pre-write refusal and contract-derived reserved roots.

## Opportunity

No current pack collides, but the build has no guard preventing a future pack-owned path from being overwritten by a projected Claude component directory.

## Assumptions

- ADR-0072 continues to govern the mirrored upstream plugin-manifest schema; this guard protects local output ownership and does not amend that schema.


## Readiness

- **Route:** direct-light with construction tests, one session. Fall back to `new-spec` if shaping review asks for it.
- **Verified 2026-11-05:** a search of `packages/agentbundle/agentbundle/build/` for collision or reserved-root handling finds only the `shared-libs` and `adapter-root-bins` basename rails, not a rail for pack-owned top-level paths against `claude-plugins` component targets.
- **Agent-only proof:** a fixture pack with a top-level path equal to a native component root fails the build before any write; reserved roots change when the contract's component targets change.
- **Order:** after or alongside FEAT-0020, which edits how the same contract is read. Low value, since no pack collides today, so it may be parked.

## Source

- Mode: repo-origin
- Locator: docs/specs/claude-plugins-manifest-correctness/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

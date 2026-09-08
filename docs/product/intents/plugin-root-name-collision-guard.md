# Claude plugin root-name collision guard

- **Status:** Accepted


## Outcome

The Claude-plugins build fails before writing output when a pack-owned top-level path would collide with a natively projected component root.

## Boundary

- Derive reserved roots from the `claude-plugins` native component target paths in `contracts/distribution-routes.toml`.
- Do not derive the set from PRIMITIVE_DIRS, retired adapter-contract fields, or the compiled-manifest target under .claude-plugin.
- Reject collisions before any copy or projection write; do not rename pack content or broaden the rule to unrelated distribution routes.

## Owner

- AgentBundle maintainers.

## Unresolved questions

- Which accepted RFC provides the required Engine-Change-RFC authority? RFC-0008 governs Claude-plugin install-route parity, but the current evidence does not establish that it authorizes this build preflight.
- Should a future native component target reserve only its first path segment, and how should duplicate or nested target roots be normalized?

## Projection

- Resolve or create the RFC authority, then shape a focused full-mode delivery spec with construction tests proving pre-write refusal and contract-derived reserved roots.

## Opportunity

No current pack collides, but the build has no guard preventing a future pack-owned path from being overwritten by a projected Claude component directory.

## Assumptions

- ADR-0072 continues to govern the mirrored upstream plugin-manifest schema; this guard protects local output ownership and does not amend that schema.


## Source

- Mode: repo-origin
- Locator: docs/specs/claude-plugins-manifest-correctness/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

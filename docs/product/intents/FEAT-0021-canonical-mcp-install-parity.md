# Canonical MCP install parity

- **Slug:** `canonical-mcp-install-parity`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:first-class-distribution-routes
- **Depends on:** spec:distribution-route-registry
- **Decomposed:** 2026-11-05 brief

## Outcome

MCP is a canonical pack primitive installed directly by agentbundle through every capable runtime adapter and projected by every route that claims MCP support in the same slice.

## Opportunity

MCP exists in plugin formats but not in the canonical pack model or direct agentbundle installation path.

## Boundary

This feature owns MCP as a canonical primitive with direct-install and claimed
route projection parity in one slice.

It does not acquire MCP servers from registries, bypass route support claims, or
add route-specific MCP semantics outside the canonical primitive model.

## Assumptions

- **Riskiest assumption:** same-wave parity covers source, validation, normalized model, capable direct-install adapters, claimed routes, diagnostics, guides, and fail-closed security controls without making the slice too broad to verify.
- **Knowledge surface:** In-repository RFC-0092, distribution-routes programme brief, route registry spec, and canonical primitive parity evidence.

## Readiness

- **Route:** delivery brief [`canonical-mcp-install-parity-delivery`](../briefs/canonical-mcp-install-parity-delivery.md), three slices (M1 model and admission, M2 direct install, M3 route projections). One spec is too wide to verify.
- **Verified 2026-11-05:** `PRIMITIVE_DIRS` has no MCP, `contracts/adapter.toml` has no MCP field, and only the portable `mcp.schema.json` is vendored. This feature does not depend on FEAT-0020; the registry it needs is shipped.
- **First slice and agent-only proof:** M1, with offline fixtures for the admission rules and a parity test that fails when any claimant adapter or route lacks an MCP projection.
- **Owner decision, 2026-11-05:** `agent-plugin` and `claude-plugins` claim MCP as native; `apm` records it as `dropped` and refuses a declaring pack until a documented path is recorded.
- **Manual residue, non-blocking:** a live client check that a projected server loads.

## Source

- Mode: repo-origin
- Locator: docs/product/briefs/distribution-routes-programme.md
- Revision: sha256-bytes-v1:329d3aec010ffd0f0b090022bac7faf35b85f337d9b3c719ab8063b7c74dbc45

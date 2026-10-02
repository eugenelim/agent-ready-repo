# Canonical MCP install parity

- **Slug:** `canonical-mcp-install-parity`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:first-class-distribution-routes

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

## Source

- Mode: repo-origin
- Locator: docs/product/briefs/distribution-routes-programme.md
- Revision: sha256-bytes-v1:329d3aec010ffd0f0b090022bac7faf35b85f337d9b3c719ab8063b7c74dbc45

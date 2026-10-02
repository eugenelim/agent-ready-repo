# Registry-acquired MCP servers

- **Slug:** `registry-acquired-mcp-servers`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:first-class-distribution-routes
- **Governed by:** [RFC-0092 D7](../../rfc/0092-first-class-distribution-routes.md)

## Outcome

MCP servers acquired from package registries have an approved acquisition and execution trust model.

## Opportunity

RFC-0092 defers package-registry MCP server installation to D7’s own RFC; the needed typed immutable acquisition descriptor is not yet defined.

## Boundary

This feature owns the decision and contract for MCP servers acquired from npm,
PyPI, or another package registry.

It does not enable registry-acquired execution before immutable artifact
identity, provenance trust policy, and lifecycle-script policy are approved.

## Assumptions

- **Riskiest assumption:** an acquisition descriptor can make registry-sourced MCP server execution reviewable enough to consider, rather than refusing the route outright.
- **Knowledge surface:** In-repository RFC-0092 D7, distribution-route trust boundaries, and the registered follow-on source.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

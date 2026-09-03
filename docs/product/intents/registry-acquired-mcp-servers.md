# Registry-acquired MCP servers

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0092 D7](../../rfc/0092-first-class-distribution-routes.md)

## Outcome

MCP servers acquired from package registries have an approved acquisition and execution trust model.

## Opportunity

RFC-0092 defers package-registry MCP server installation to D7’s own RFC; the needed typed immutable acquisition descriptor is not yet defined.

## What this absorbs

### mcp-servers-from-package-registries

Open the D7 RFC for MCP servers acquired from npm, PyPI, or another registry. Define a typed acquisition descriptor extending the unused runtime-dependencies shape, require immutable artifact identity before execution, define provenance trust policy, and define lifecycle-script policy. `docs/rfc/0092-first-class-distribution-routes.md:515` names “D7 — MCP servers installed from package registries (deferred direction),” and line 563 says the typed immutable acquisition descriptor remains work for D7’s own RFC.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

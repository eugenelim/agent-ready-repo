# Workspace-MCP reaches production readiness

- **Status:** Draft
- **Level:** capability

## Outcome

Workspace-MCP reaches production readiness with behavioral proof for its Stage 1 contracts, non-breaking Claude headless-permission projection, and the canonical brief queue exposed through its status surface.

## Boundary

- Stage 1 behavioral integration coverage, Claude permissions.allow projection, and canonical brief-queue exposure through workspace-MCP.
- Later adapter stages, multi-instance support, a new brief-queue schema, and breaking adapter-contract changes remain outside this intent.

## Owner

- Workspace-MCP maintainers; no individual owner is recorded.

## Unresolved questions

- None recorded. A breaking adapter-contract shape stops and requires a follow-on RFC rather than widening this intent.

## Projection

- One delivery brief with three separately gated specifications: Stage 1 behavioral coverage, Claude permission projection, and brief-queue exposure.

## Opportunity

This intent absorbs workspace-mcp-permissions-projection-contract, workspace-mcp-stage1-behavioral-tests, and workspace-mcp-brief-queue-exposure. The implementation exists, but permissions projection and brief-queue exposure are absent and many Stage 1 contracts remain represented only by skipped test stubs.

## Assumptions

- RFC-0078 authorizes the non-breaking Claude permissions projection and requires Engine-Change-RFC: RFC-0078 for its AgentBundle change.
- Brief-queue exposure reuses the canonical workspace-status projection rather than defining a second layout.
- Any breaking adapter-contract change requires a follow-on RFC before implementation.


## Source

- Mode: repo-origin
- Locator: docs/specs/workspace-mcp/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

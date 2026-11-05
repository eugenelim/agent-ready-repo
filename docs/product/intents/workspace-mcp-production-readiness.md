# Workspace-MCP reaches production readiness

- **Slug:** `workspace-mcp-production-readiness`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** capability
- **Owner:** eugenelim

## Outcome

Workspace-MCP reaches production readiness with behavioral proof for its Stage 1 contracts and a non-breaking Claude headless-permission projection, and its status surface is proven to expose briefs from their own headers.

## Boundary

- Stage 1 behavioral integration coverage, Claude permissions.allow projection, and behavioral proof that `workspace_status` returns brief artifacts read from their `Status:` headers.
- Later adapter stages, multi-instance support, a brief-queue schema, and breaking adapter-contract changes remain outside this intent.

## Owner

- eugenelim, with workspace-MCP maintainers.

## Unresolved questions

- None recorded. A breaking adapter-contract shape stops and requires a follow-on RFC rather than widening this intent.

## Projection

- One delivery brief with two separately gated specifications: Stage 1 behavioral coverage, which includes the brief-exposure proof, and Claude permission projection.

## Opportunity

This intent absorbs workspace-mcp-permissions-projection-contract and workspace-mcp-stage1-behavioral-tests, and carries the former workspace-mcp-brief-queue-exposure as one behavioral proof inside the second. The Stage 1 implementation ships and `workspace_status` reads work from artifact headers through the packaged `dispatch.py`, which covers briefs (`WORKSPACE_ARTIFACT_KINDS` includes `brief`); the registry's `brief_queue` it once exposed is retired with `workspace.toml`. A Claude `permissions.allow` projection is absent from the build and the adapter contract, and many Stage 1 contracts remain represented only by skipped test stubs in `packages/agentbundle/tests/`.

## Assumptions

- RFC-0078 authorizes the non-breaking Claude permissions projection and requires Engine-Change-RFC: RFC-0078 for its AgentBundle change.
- Brief exposure reuses the packaged header-based dispatch rather than defining a second layout.
- Any breaking adapter-contract change requires a follow-on RFC before implementation.


## Source

- Mode: repo-origin
- Locator: docs/specs/workspace-mcp/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

## Current truth

Verified 2026-11-05: 53 skipped stubs remain across `packages/agentbundle/tests/test_workspace_mcp_*.py` (elicit 10, stdin 10, git 10, event_bridge 7, tools 6, git_scope 6) and `test_adapter_permissions_projection.py` (4). Brief exposure is shipped through header-based `dispatch.py` (core 4.0.10), so that part of the intent is done.

## Readiness

- **Route:** brief. See [workspace-mcp-production-readiness-delivery](../briefs/workspace-mcp-production-readiness-delivery.md).
- **First slice:** the Claude `permissions.allow` projection, which unskips 4 named stubs.
- **Agent-only proof:** those tests pass and a merge keeps user entries.
- **Manual dependency:** none.

## Riskiest assumption

**Riskiest assumption:** the skipped stubs still describe contracts the server meets. Tested agent-only by converting one test file at a time; a stub the server fails stops its slice and raises a follow-on RFC, and a stub that no longer describes a contract is deleted with a recorded reason.

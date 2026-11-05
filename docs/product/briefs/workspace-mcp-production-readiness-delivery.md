# Brief: workspace-MCP Stage 1 has behavioral proof and a Claude permissions projection

- **Slug:** `workspace-mcp-production-readiness-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Draft
- **Parent intent:** capability:workspace-mcp-production-readiness

## Outcome

Each Stage 1 workspace-MCP contract is exercised by a running test instead of a skipped stub, and a Claude install writes the `permissions.allow` entries the server needs without removing any the user set. `workspace_status` is proven to return briefs read from their `Status:` headers.

## Scope / Non-goals

**In scope.** Replacing the stubs in `packages/agentbundle/tests/test_workspace_mcp_*.py` and `test_adapter_permissions_projection.py`, and implementing the non-breaking permissions projection RFC-0078 authorizes.

**In scope also.** A behavioural test that `workspace_status` returns a brief read from its `Status:` header through `dispatch.py` (slice 5).

**Out of scope.** Later adapter stages, multi-instance support, a brief-queue schema and any breaking adapter-contract change.

## Current-state evidence

Counted 2026-11-05 by searching for `pytest.skip` and `mark.skip`.

- Skipped stubs: `elicit` 10, `stdin` 10, `git` 10, `event_bridge` 7, `tools` 6, `git_scope` 6, `test_adapter_permissions_projection` 4. That is 53.
- The permissions stubs include three named behaviours: all six ids present, existing entries preserved, no duplicates on a second install. The fourth stub is `test_install_core_does_not_clobber_other_keys`, read in slice 1.
- No `test_workspace_mcp_*` test checks that `workspace_status` returns a brief read from its `Status:` header; `test_workspace_mcp_dispatch.py` only checks that a brief path is not treated as a spec.

## Constraints / Appetite

- A stub that exposes a contract the server does not meet stops the slice and needs a follow-on RFC; it does not widen this brief.
- `tools/AGENTS.md` protects everything under `packages/agentbundle/`, tests included, so every slice's commit needs an `Engine-Change-RFC:` trailer. Slice 1 cites `RFC-0078`; slices 2 to 5 each use `Engine-Change-RFC: n/a - tests only, no engine behavior change`.
- Slice 1 changes package behavior, so it also bumps the package version in both `version.py` and `pyproject.toml` (`packages/AGENTS.md`).
- Appetite: one slice for the projection, one per test group, and one for brief exposure.

## Assumptions / Risks

- **[Risk]** Some stubs describe behaviour that changed after the registry retirement. Each slice first checks its stubs against current code and deletes any that no longer describe a contract, recording the reason.
- **[Risk]** Event-bridge and stdin tests are timing-sensitive. They use in-process doubles, not sleeps.

## Governance references

- `docs/rfc/0078-workspace-mcp.md` authorizes the projection.
- `docs/specs/workspace-mcp/spec.md` owns the Stage 1 contracts.

## Proposed cut

All slices are independent and `agent-only`.

| Slice | Gating | Proof |
| --- | --- | --- |
| 1. Claude `permissions.allow` projection | agent-only, RFC-0078 trailer | The 4 stubs run and pass; merge keeps user entries |
| 2. `elicit` and `stdin` tests (20) | agent-only | Zero skips in both files; every surviving stub is a passing test, and each deleted stub is listed with its reason |
| 3. `git` and `git_scope` tests (16) | agent-only | Zero skips; every surviving stub is a passing test, and each deleted stub is listed with its reason |
| 4. `event_bridge` and `tools` tests (13) | agent-only | Zero skips; every surviving stub is a passing test, and each deleted stub is listed with its reason |
| 5. Behavioural proof that `workspace_status` returns a brief read from its `Status:` header | agent-only | A test writes a brief fixture, calls the tool, and asserts the brief appears with that status |

## Ready gaps (Draft only)

None open.

## Spec map

| Spec | Status |
| --- | --- |

## Source

- Mode: repo-origin
- Locator: docs/product/intents/workspace-mcp-production-readiness.md

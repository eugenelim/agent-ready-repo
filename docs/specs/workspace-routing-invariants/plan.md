# Plan: Workspace routing invariants

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially,
> note why in the changelog at the bottom.

## Approach

Extend the canonical workspace engine in four layers. First, replace permissive raw objects with typed target and legacy parsing that implements both Group 2 contracts. Second, make reconciliation produce stable findings and drive one positive dispatch predicate with kind-specific dependency checks. Third, route CLI, MCP, and work-loop preflight through that result. Last, preserve structured entries during repair, document every finding, and prove determinism across clean processes and installed projections. The reader lands before any target-state writer changes.

## Constraints

- Depends on `normalized-intake-workspace-contracts` T4.
- RFC-0083 fixes dispatch conditions, lifecycle memberships, authority rules, dependency satisfaction, compatibility behavior, and fail-closed semantics.
- The two Group 1 ADRs are approval prerequisites; their identifiers remain unstated until assigned.
- `contracts/jsonschema/normalized-intake.schema.json` and `contracts/jsonschema/workspace-entry.schema.json` are authoritative. Runtime code implements them without importing `jsonschema`.
- `workspace_status_engine.py` remains the single classification/reconciliation implementation used by CLI and MCP.
- `status` remains bounded; `reconcile` may perform the global spec scan. Bounded mode must still validate every declared entry.
- Path reads realpath-resolve and remain under the repository boundary.
- Public MCP output changes require agentbundle version/release handling.
- `.apm` sources, not generated projections, are edited.
- Group 4 owns the public `work-intake` workflow and final guarded claim/completion orchestration; this plan owns eligibility, refusal, and reusable validation results.

## Construction tests

**Integration tests:**

- Run the same fixture through engine analysis, CLI JSON, MCP projection, and work-loop preflight and compare finding/eligibility identity.
- Run paired comment/summary/order mutations and assert the normalized semantic result is unchanged.
- Run the determinism corpus in two fresh subprocesses and compare canonical JSON.
- Project workspace-status scripts through every shipped adapter and compare installed/source results.

**Manual verification:**

- Invoke status against one valid queue entry, one missing spec, one missing plan, one legacy entry, and one Ready brief with no specs; verify the prose next action matches the JSON finding.
- Security review path traversal, symlink escape, untrusted TOML/source data, prompt-injection, and absolute-path redaction behavior.

## Design (LLD)

### Design decisions

- One engine result contains typed entries, findings, dependency results, and dispatchability. Consumers project it; they do not recompute it. Traces to: AC1–AC4, AC19–AC21.
- Dispatch eligibility is a positive conjunction. A missing check cannot default to ready. Traces to: AC4–AC15.
- Legacy parsing produces compatibility records, not weakened target entries. Traces to: AC2–AC3, AC20–AC21.
- Reconciliation remains read-only. Repair consumes findings but may automate only explicitly safe lifecycle cleanup. Traces to: AC23–AC24.

### Data & schema

`workspace_status_engine.py` gains typed representations for:

- normalized intake and its source provenance
- target workspace entries and legacy compatibility entries
- source records and typed dependencies
- artifact metadata needed for status/provenance checks
- stable findings with code, path, membership, detail, and next action
- dispatch evaluations carrying `dispatchable` and all blocking finding codes

The engine reads the Group 2 schema constants/enums into code and tests parity against the schema files. Traces to: AC1–AC3, AC17–AC19 · both JSON Schemas.

### Interfaces & contracts

- Engine: `validate_normalized_intake`, `parse_workspace_entry`, `run_reconciliation`, and `evaluate_dispatch`.
- CLI JSON: adds stable findings and dispatchability while retaining mode/scan metadata.
- MCP: `ready` contains only dispatchable queue work; blocked entries carry finding codes.
- Work-loop: Step 0 consumes the same validation result before starting or resuming.

The schemas remain authoritative; code-schema parity tests catch enum or required-field drift. Traces to: AC1–AC4, AC19–AC22 · both JSON Schemas.

### Failure, edge cases & resilience

All malformed or ambiguous inputs produce findings and no execution action. Missing targets and dependency cycles are explicit. Path validation precedes file reads. Remote receipt checks are local-only. Full reconciliation includes paused/closed initiative corruption without dispatching it. Repair refuses stale fingerprints and every non-mechanical conflict. Traces to: AC3, AC5–AC15, AC23–AC24.

### Quality attributes (NFRs)

- Deterministic: clean-process canonical output matches exactly.
- Secure: confined paths, no live remote lookup, and untrusted text never becomes instruction.
- Portable: Python 3.11 stdlib runtime and Windows-clean path handling.
- Observable: every refusal has a stable code and safe next action.
- Backward-aware: supported legacy inputs remain visible but fail closed.

Traces to: AC3, AC6, AC13, AC16–AC25.

### Dependencies & integration

The CLI imports the engine beside it. `workspace-mcp` loads the projected engine and only projects its evaluation. `work-loop` invokes the canonical status/preflight surface. Group 4 later uses the same evaluation before guarded lifecycle writes. Traces to: AC19–AC22.

## Tasks

### T1: Canonical and legacy records parse through typed Group 2 contract checks

**Depends on:** spec:normalized-intake-workspace-contracts/T4

**Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`, `tools/test_workspace_status.py`, `packs/core/tests/skills/workspace-status/test_workspace_status_engine_autonomous.py`

**Verification mode:** TDD

**Tests:**

**Stub:** draft (uncompiled) — the typed contract surface (`NormalizedIntake`, `WorkspaceEntry`, compatibility records, and `validate_normalized_intake`) imported by the pytest cases below is created by this task from the upstream RFC-0083 schemas and is unavailable at PLAN. The first EXECUTE action materializes these cases as compilable failing tests before any production-engine edit.

- Target entries parse all five required fields and preserve source/dependency detail. Traces to: AC1–AC2.
- Every Group 2 legacy fixture becomes an explicit non-dispatchable compatibility entry. Traces to: AC2.
- Invalid fields, kinds, paths, authority records, and unsupported extensions produce stable validation findings without partial entries. Traces to: AC3, AC6.
- Normalized-intake records implement action and authority conditionals from the schema. Traces to: AC1.
- Code enums and required fields match both schema files.

**Approach:**

- Add typed `NormalizedIntake`, `WorkspaceEntry`, `LegacyWorkspaceEntry`, `SourceRecord`, `Dependency`, and `RoutingFinding` dataclasses.
- Add `validate_normalized_intake(raw)` and replace `_parse_work_entry`/`_parse_shaping_entry` with contract-aware parsing that retains legacy provenance.
- Keep lexical checks separate from `_safe_spec_path` realpath confinement.
- Adapt `Initiative`, `BriefQueue`, and top-level backlog extraction to structured entries and all target memberships.
- Preserve explicit compatibility parsing for the accepted legacy fixture set.

**Done when:** target and legacy contract tests pass, invalid input cannot produce a usable target entry, and existing status tests have deliberate updated expectations.

### T2: Reconciliation and dependency evaluation implement one positive dispatch predicate

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`, `tools/test_workspace_status.py`

**Verification mode:** TDD

**Tests:**

**Stub:** draft (uncompiled) — the finding model and `evaluate_dispatch` contract imported by the pytest cases below are created by this task and are unavailable at PLAN. The first EXECUTE action materializes these cases as compilable failing tests before any reconciliation, dependency, or dispatch production edit.

- Missing spec and plan produce `missing_artifact` and `missing_plan` and are never ready. Traces to: AC4–AC5.
- Path confinement, duplicate membership, impossible transitions, provenance mismatch, and refresh conflicts each fail closed with the expected code. Traces to: AC6–AC10.
- Kind-specific dependency matrices cover every satisfied/unsatisfied status. Traces to: AC11.
- Missing targets and cycles produce `missing_dependency` and `dependency_cycle`. Traces to: AC12.
- Receipt fixtures require the full local key and perform no network access. Traces to: AC13.
- Ready-without-spec and paused/closed initiative fixtures behave as specified. Traces to: AC14–AC15.
- `evaluate_dispatch` is true only for the exact AC4 conjunction; removing any one fact makes it false.

**Approach:**

- Generalize reconciliation from the current Type 1/2/3-only model to stable coded findings while preserving those scan modes as compatibility projections.
- Add bounded declared-artifact validation for every queue, active, shipped, brief, shaping, and backlog entry.
- Parse artifact status, `Brief:`, source authority, and unresolved conflict markers through bounded metadata readers.
- Replace absence-based `is_need_satisfied` branches with typed positive evidence and graph cycle/missing-target detection.
- Add `evaluate_dispatch(entry, initiative, reconciliation)` and derive ready/blocked from it.

**Done when:** the complete invariant matrix passes and `case_missing_spec_paths` now proves fail-closed behavior rather than the prior known defect.

### T3: CLI, MCP, and work-loop consume the same eligibility and finding result

**Depends on:** T2

**Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`, `packs/core/.apm/skills/workspace-status/SKILL.md`, `packs/core/.apm/skills/work-loop/SKILL.md`, `tools/test_workspace_status_cli.py`, `packages/agentbundle/agentbundle/workspace_mcp.py`, `packages/agentbundle/tests/test_workspace_mcp_tools.py`, `packages/agentbundle/tests/test_workspace_mcp_lifecycle.py`

**Verification mode:** TDD and goal-based integration

**Tests:**

**Stub:** draft (uncompiled) — the finding-aware CLI/MCP/work-loop projection contract asserted by the pytest cases below is created by this task and is unavailable at PLAN. The first EXECUTE action materializes these cases as compilable failing tests before any CLI, MCP, or work-loop production edit; goal-based integration checks follow once the red cases pass.

- CLI status/reconcile/explain serialize the same codes, affected artifact, dispatchability, and next action. Traces to: AC19.
- MCP `ready` contains only dispatchable queue entries; invalid work appears with finding codes and no absolute paths. Traces to: AC20.
- Work-loop preflight refuses each fail-closed fixture and accepts one eligible queued contract plus one valid resumable active contract. Traces to: AC21–AC22.
- Comment-only changes produce identical CLI/MCP/work-loop decisions. Traces to: AC16.
- Existing bounded/global scan-cost tests remain valid.

**Approach:**

- Extend `_work_entry_dict`, `_classification_dict`, `_finding_dict`, `_brief_queue_dict`, `_build_json`, and `_build_explain_json`.
- Make `_WorkspaceStatusTool.call` project engine eligibility instead of treating every dependency-ready entry as dispatchable.
- Update MCP tool descriptions and output schema documentation.
- Replace work-loop’s “missing spec: skip” Step 0 rule with canonical fail-closed preflight and valid active-resume checks.
- Keep status rendering as a projection of JSON; do not re-read TOML to infer routing.

**Done when:** one fixture produces matching eligibility/finding identity through engine, CLI, MCP, and work-loop, and package tests prove unsafe entries never reach MCP `ready`.

### T4: Repair preservation, finding documentation, determinism, projection, and release gates pass

**Depends on:** T3

**Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`, `tools/test_workspace_status.py`, `tools/test_workspace_status_cli.py`, `packages/agentbundle/agentbundle/build/tests/test_workspace_status_projection.py`, `packages/agentbundle/tests/test_workspace_mcp_tools.py`, `guides/core/reference/workspace-toml-schema.md`, `packs/core/.apm/skills/workspace-status/SKILL.md`, `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `packages/agentbundle/pyproject.toml`, `packages/agentbundle/agentbundle/version.py`, `docs/product/changelog.md`

**Verification mode:** TDD and goal-based check

**Tests:**

**Stub:** draft (uncompiled) — the structured repair-preservation and canonical determinism surfaces asserted by the pytest cases below are created by this task and are unavailable at PLAN. The first EXECUTE action materializes these cases as compilable failing tests before any repair, serializer, projection, or release-metadata production edit; goal-based gates follow after the TDD slice is green.

- Repair preserves structured entry fields, refuses non-mechanical findings, detects concurrent changes, and never emits a bare target entry. Traces to: AC23–AC24.
- Every finding fixture appears in status documentation with one safe next action. Traces to: AC25.
- Two fresh subprocesses emit identical canonical results for the determinism corpus. Traces to: AC16–AC18.
- Installed/source projections match across shipped adapters.
- Pack/plugin and package versions match their release rules; catalogue and package gates pass.

**Approach:**

- Update repair-plan eligibility and `_apply_operations` to move the retained structured TOML item rather than appending `spec_path`.
- Keep fingerprint, confinement, atomic replace, permission, and comment-preservation protections.
- Add canonical result serialization that excludes elapsed time and absolute root from determinism comparisons.
- Document every finding and safe action in `workspace-status` and the workspace reference.
- Bump release metadata required by the pack and public MCP output changes, then regenerate projections once.

**Done when:** repair, determinism, documentation coverage, projection parity, core pack tests, agentbundle tests, catalogue gates, lint, and build checks all pass.

## Rollout

- **Delivery:** reader-first. Group 3 accepts target and legacy input but no target-state workflow writer is enabled by this spec.
- **Infrastructure:** none.
- **External-system integration:** none; receipt and tracker-origin reconciliation are offline.
- **Deployment sequencing:** Group 2 T4 → T1 parser → T2 invariants → T3 consumers → T4 repair/docs/release. Group 4 may enable shared intake and guarded lifecycle writes only after T4 is published.
- **Compatibility:** legacy entries remain visible and non-dispatchable. Current valid target entries use the new structured contract.
- **Rollback:** disable later writers and return to the preceding dual-reader release. No repair deletes canonical artifacts; structured entries remain recoverable from Git and migration manifests.

## Risks

- Expanding the current Type 1/2/3 model could accidentally break existing repair-plan consumers; compatibility projections need explicit tests.
- A CLI/MCP consumer may silently recompute readiness and drift from the engine.
- Artifact metadata parsing may accept examples from body prose instead of the canonical preamble.
- Path validation may be lexical-only and miss symlink or junction escapes.
- Moving structured TOML entries may lose comments or metadata if `tomlkit` nodes are copied incorrectly.
- Package and pack releases are coupled to different surfaces and can be versioned inconsistently.
- Group 4 may duplicate eligibility unless the engine interface is clear and documented.

## Changelog

- 2026-08-09: Initial plan derived from accepted RFC-0083, the Group 2 task boundary, and confirmed assumptions.

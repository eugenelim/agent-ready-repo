# Spec: workspace-status simplification — Order 2A

- **Status:** Shipped
- **Owner:** maintainer
- **Plan:** [`plan.md`](plan.md)
- **Mode:** full (intentionally changes user-visible work-loop startup behavior; structural change to
  reconciliation ownership; multi-feature/dependent tasks; the work-loop skill and its generated
  projections change)
- **Constrained by:**
  - [RFC-0064](../../rfc/0064-ini-001-ai-native-ecosystem.md) — workspace.toml schema and
    workspace-status behavior authority
  - `docs/specs/workspace-status-simplification-order-0/spec.md` — Phase 0 characterization;
    compatibility authority
  - `docs/specs/workspace-status-simplification-order-1a/spec.md` — Order 1A contract baseline
  - `docs/specs/workspace-status-simplification-order-1b/spec.md` — Order 1B contract; `reconcile`
    mode is now the canonical exhaustive integrity path
  - `packs/core/.apm/skills/work-loop/SKILL.md` — production behavior; Step 0 is the target
  - `packs/core/.apm/skills/workspace-status/SKILL.md` — canonical reconcile skill
- **Contract:** none (internal skill interface only)
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Remove the stale-workspace reconciliation scan from `work-loop` Step 0.

Responsibility boundary after this change:

| Surface | Responsibility |
|---------|---------------|
| `workspace-status status` | Bounded discovery and triage (Type 2 + Type 3 only) |
| `workspace-status explain` | Focused dependency explanation |
| `workspace-status reconcile` | Exhaustive workspace integrity (Type 1 + 2 + 3) |
| `work-loop` | Execute and verify one selected work item |

`work-loop` must no longer inspect every queue and active spec merely to detect
that a declared item has become Shipped or otherwise stale.

## Order 1B Readiness Evidence

Prerequisites verified against current production source:

1. `workspace_status.py reconcile --root <dir>` exists and routes to `analyze()`. ✓
2. `analyze()` performs exhaustive Type 1 + Type 2 + Type 3 scan. ✓
3. `workspace_status.py status --root <dir>` is the bounded default (Type 2 + Type 3 only). ✓
4. `reconcile` is read-only at the CLI level (AC19 of Order 1B). ✓
5. `SKILL.md` routes integrity-audit requests to `reconcile`. ✓
6. `.claude/` and `.agents/` projections match the source. ✓
7. Order 1B spec.md is Shipped; all 56 tests pass. ✓

## Boundaries

### Always do

- Remove the **Stale-queue check** bullet from `packs/core/.apm/skills/work-loop/SKILL.md`
  Step 0, specifically the paragraph beginning "**Stale-queue check.**".
- Add a one-sentence ownership note in Step 0 directing users to `workspace-status reconcile`
  for exhaustive workspace integrity checks.
- Remove `WorkLoopStaleWarning` class and `collect_work_loop_stale_warnings` function from
  `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`.
- Replace the stale-scan tests in `tools/test_workspace_status.py` with:
  (a) a sentinel test proving `collect_work_loop_stale_warnings` is absent from the engine;
  (b) a reconcile ownership parity test proving `analyze()` still detects the stale fixtures;
  (c) updated `_WORK_LOOP_CONTRACT_HASH` after the SKILL.md change.
- Update `case_work_loop_contract_anchor` docstring to remove the stale-queue check reference.
- Add routing evals to `packs/core/.apm/skills/work-loop/evals/evals.json` demonstrating that
  portfolio reconciliation requests route to `workspace-status reconcile`, not `work-loop`.
- Run `make build-self` after editing `packs/`; verify generated projections are changed.
- Record before-and-after Step 0 file-read profile in
  `docs/specs/workspace-status-simplification-order-2a/notes/read-profile.md`.

### Ask first

- Any change to workspace.toml schema
- Any change to `workspace-status` reconcile, status, or explain semantics
- Any change to argless resume behavior in work-loop
- Adding a new work-loop mode or routing mechanism

### Never do

- Change `workspace-status` status, explain, or reconcile semantics
- Change the workspace-status JSON schema
- Add `repair-plan`, `repair-apply`, or automatic mutation
- Create a separate `workspace-reconcile` skill
- Call `workspace-status` from `work-loop` automatically
- Change work-loop argless resume; replace `work.active` with queue scanning
- Remove or reinterpret `work.active` or `work.shipped`
- Change workspace.toml schema
- Scan queue specs for `Status: Implementing` (belongs to later state-model migration)
- Remove or loosen the shaping-item guard
- Change deferred-backlog capture or completion behavior
- Add caching or generated indexes
- Perform unrelated cleanup

## Testing Strategy

- **TDD** — sentinel test for stale-scan removal (AttributeError on `collect_work_loop_stale_warnings`);
  reconcile ownership parity test (same stale fixtures detected by `analyze()`); argless resume
  regression tests (zero/one/many active items); shaping guard and orientation preservation.
  Red stubs written before production edits.
- **Goal-based check** — `make build-self` passes; `_WORK_LOOP_CONTRACT_HASH` in
  `tools/test_workspace_status.py` updated to reflect new Step 0 content.
- **Visual / manual QA** — `workspace-status reconcile` exercised against repo's own
  `workspace.toml`; work-loop invoked against a fixture; observed output recorded.

## Acceptance Criteria

- [x] AC1. Work-loop no longer scans queue and active specs for stale workspace state during Step 0.
- [x] AC2. Work-loop no longer emits Type 1, Type 2, or Type 3 portfolio findings.
- [x] AC3. Work-loop does not invoke `workspace-status status`, `explain`, or `reconcile` automatically.
- [x] AC4. `workspace-status reconcile` remains the canonical exhaustive integrity path.
- [x] AC5. The stale fixtures removed from work-loop remain detected by `workspace-status reconcile`.
- [x] AC6. Argless resume continues to use the current `work.active` contract.
- [x] AC7. Zero, one, and multiple active-item behavior is unchanged.
- [x] AC8. Explicit-spec invocation is unchanged.
- [x] AC9. Initiative and milestone orientation are unchanged.
- [x] AC10. The shaping-item guard is unchanged.
- [x] AC11. Work-loop Step 0 performs no workspace.toml mutation.
- [x] AC12. Completion and deferred-backlog behavior are unchanged.
- [x] AC13. Workspace-status status, explain, and reconcile behavior is unchanged.
- [x] AC14. Workspace.toml schema is unchanged.
- [x] AC15. `work.active` and `work.shipped` remain unchanged.
- [x] AC16. No repair-plan or repair-apply mode is introduced.
- [x] AC17. No separate reconciliation skill is introduced.
- [x] AC18. Generated projections match source (after `make build-self`).
- [x] AC19. The read-profile evidence demonstrates stale-scan removal.
- [x] AC20. Focused tests, build-self, build-check, and required reviews pass. Routing evals are
  present in `evals.json` (presence-only; no eval harness is wired in CI today — consistent with
  all existing evals in this repo).

## Verification mapping for preserved behaviors (AC6–AC10)

| AC | Verification |
|----|--------------|
| AC6 argless resume | Existing: `case_multiple_active_for_workloop` (AC2o); `case_work_loop_contract_anchor` hashes the Step 0 section which preserves argless-resume prose |
| AC7 zero/one/many | Existing: `case_multiple_active_for_workloop` covers multiple; Step 0 orientation logic text unchanged in hash |
| AC8 explicit-spec invocation | Existing: work-loop SKILL.md Step 0 — explicit path bypasses active resolution; hash covers this |
| AC9 initiative/milestone orientation | Existing: `case_multiple_active_initiatives`; hash of Step 0 covers orientation bullet |
| AC10 shaping-item guard | Existing: `case_shaping_item_guard`, `case_shaping_guard_top_level_backlog`; hash covers guard prose |

Primary verification mechanism: the `_WORK_LOOP_CONTRACT_HASH` anchors the entire Step 0 section.
Any over-broad edit that removes orientation, argless-resume, or shaping-guard prose changes the hash
and fails `case_work_loop_contract_anchor`. Human diff review at PR time is the secondary gate.

## Assumptions

- Technical: The stale-queue check is fully contained in `collect_work_loop_stale_warnings` and the
  single Stale-queue check bullet in work-loop SKILL.md Step 0 — confirmed by grepping the codebase.
- Technical: Removing `WorkLoopStaleWarning` and `collect_work_loop_stale_warnings` from the engine
  does not break any caller outside of `tools/test_workspace_status.py` — confirmed by grep showing
  only test-file imports.
- Technical: The `_WORK_LOOP_CONTRACT_HASH` anchors the entire `## Step 0. ORIENT` → `## Step 1. PLAN`
  section; removing the stale-queue bullet changes the hash, so the hash constant must be updated.
- Process: `loop-engine` / `loop-cohort` scripts are absent from `scripts/` at repo root — named skip
  for state machine; full mode rigor applied without it (consistent with Order 1B precedent).
- Process: No guides in `guides/` reference stale-queue behavior — confirmed by grep.

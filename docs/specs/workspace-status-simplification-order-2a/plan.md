# Plan: workspace-status simplification — Order 2A

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Assumption trio

**Files touched:**
1. `packs/core/.apm/skills/work-loop/SKILL.md` — Remove stale-queue check bullet from Step 0; add ownership note
2. `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py` — Remove `WorkLoopStaleWarning` class and `collect_work_loop_stale_warnings` function
3. `tools/test_workspace_status.py` — Replace stale-scan tests with removal sentinel + parity tests; update `_WORK_LOOP_CONTRACT_HASH`; update CASES list and docstrings
4. `packs/core/.apm/skills/work-loop/evals/evals.json` — Add routing evals
5. `docs/specs/workspace-status-simplification-order-2a/notes/read-profile.md` — Before/after profile evidence

**What tests demonstrate "done":**
- `python3 tools/test_workspace_status.py` exits 0 with all existing cases passing plus new:
  - `case_work_loop_stale_scan_removed` — AttributeError/absent sentinel for `collect_work_loop_stale_warnings`
  - `case_work_loop_reconcile_owns_stale` — same stale fixtures detected by `analyze()`
  - Updated `case_work_loop_contract_anchor` with new hash passes
- `python3 -m pytest tools/test_workspace_status_cli.py -q` passes unchanged
- `make build-self` succeeds
- `SKIP_SAST=1 make build-check` passes

**What I am NOT changing:**
- `workspace-status` engine functions (`analyze`, `analyze_bounded`, `_run_type23_scan`, `_run_type1_scan`, `explain_item`)
- workspace-status SKILL.md (already has reconcile/status/explain guidance from Order 1B)
- workspace.toml schema or content
- Argless resume, shaping guard, orientation logic in work-loop SKILL.md
- Any guides (grep confirms none reference stale-queue behavior)
- Order 1B tests, CLI tests, or any other test suite

## Declined temptations

- Moving `collect_work_loop_stale_warnings` to workspace-status CLI — Type 2 reconciliation in `analyze()` already owns stale detection; deduplication would only add confusion.
- Renaming to `WorkspaceStaleWarning` — nothing needs this; the class exists only to serve the removed behavior.
- Adding automatic `reconcile` invocation at work-loop Step 0 — explicitly forbidden by spec Boundaries and the contract's required final Step 0 behavior.
- Updating historical/shipped spec files that reference stale-queue (e.g., `docs/specs/capture-work/plan.md`) — these are historical record; modifying them is out of scope.
- Adding missing-target or cycle detection semantics — hard scope exclusion.

## Tasks

### T1 — Red behavioral tests (TDD stubs)

**Mode:** TDD
**Tests:**
```
# Add to tools/test_workspace_status.py:
def case_work_loop_stale_scan_removed() → None:
    # Assert collect_work_loop_stale_warnings is absent from _engine_mod
    # Assert WorkLoopStaleWarning is absent from _engine_mod

def case_work_loop_reconcile_owns_stale() → None:
    # Using the stale fixture (Shipped queue + active entries),
    # prove analyze() still detects them as Type 2 findings
```
These stubs fail BEFORE production edits (F) and pass AFTER (G).

**Approach:** Write the test functions that assert the absence of the removed symbols and the presence of Type 2 findings in `analyze()`. Use `hasattr(_engine_mod, "collect_work_loop_stale_warnings")` for the sentinel. For the parity test, use a subset/contains assertion — `analyze()` is a strict superset of the removed check (it also finds Archived entries and paused initiatives). Add them to the CASES runner. Verify they fail on current code.

**Verification:** `python3 tools/test_workspace_status.py` shows F for new cases, G for all existing.

---

### T2 — Remove stale-queue check from work-loop SKILL.md

**Mode:** Goal-based check
**Done when:** `grep "Stale-queue check" packs/core/.apm/skills/work-loop/SKILL.md` returns no output.
**No stub (goal-based check)**

**Approach:**
In `packs/core/.apm/skills/work-loop/SKILL.md` Step 0, remove the entire **Stale-queue check** bullet
(the sentence beginning "**Stale-queue check.**" through the end of the bullet). Replace with a one-sentence
ownership note:

```
Use `workspace-status reconcile` for exhaustive workspace integrity checks; `work-loop` does
not scan the full portfolio at startup.
```

Keep all other Step 0 content (initiative, milestone, active-spec resolution, shaping-item guard)
unchanged.

**Verification:** `grep "Stale-queue check" packs/core/.apm/skills/work-loop/SKILL.md` → empty.

---

### T3 — Remove stale-scan implementation from engine

**Mode:** TDD (paired with T1)
**Tests:** `case_work_loop_stale_scan_removed` turns green after this task.

**Approach:**
In `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`:
1. Remove the `WorkLoopStaleWarning` dataclass (lines ~110–122).
2. Remove the `collect_work_loop_stale_warnings` function and its section comment
   (lines ~963–1006).
3. Remove the test file's import of `collect_work_loop_stale_warnings` (line 46 of
   `tools/test_workspace_status.py`).
4. Remove or update the `WorkLoopStaleWarning` import usage in tests.

Do not remove `_safe_spec_path`, `extract_spec_status`, or any other helper used elsewhere.

**Verification:** `case_work_loop_stale_scan_removed` passes; `case_work_loop_reconcile_owns_stale` passes.

---

### T4 — Update contract anchor hash and test docstrings

**Mode:** Goal-based check
**Done when:** `python3 tools/test_workspace_status.py` exits 0, including `case_work_loop_contract_anchor`.

**Approach:**
1. Compute the new SHA-256 of the SKILL.md section from `## Step 0. ORIENT` to `## Step 1. PLAN`
   after T2's edit using the existing `_check_section_anchor` mechanism.
2. Update `_WORK_LOOP_CONTRACT_HASH` in `tools/test_workspace_status.py`.
3. Update `case_work_loop_contract_anchor` docstring: replace the stale-queue check mention
   with the ownership note; AC6–AC10 are covered by hash plus existing test cases.
4. Update CASES list: replace `F4b work_loop_stale_warnings` and `F4c work_loop_stale_both_lists`
   with `2A work_loop_stale_scan_removed` and `2A work_loop_reconcile_owns_stale`.
5. Remove the `case_work_loop_stale_warnings` and `case_work_loop_stale_both_lists` function
   bodies (they test behavior that no longer exists). Keep `case_work_loop_slug_normalization`
   (tests `normalize_for_shaping_guard`, which is unrelated to stale scanning).
6. Remove the pytest wrapper functions `test_work_loop_stale_warnings()` and
   `test_work_loop_stale_both_lists()` (lines ~2633–2638 only; do not remove
   `test_work_loop_slug_normalization` which follows). These call the removed case functions
   and would cause a NameError during pytest collection if left. The new sentinel and parity
   tests get corresponding wrappers `test_work_loop_stale_scan_removed()` and
   `test_work_loop_reconcile_owns_stale()`.

---

### T5 — Add routing evals

**Mode:** Goal-based check
**Done when:** `packs/core/.apm/skills/work-loop/evals/evals.json` contains the new eval entries.

**Approach:**
Add to `packs/core/.apm/skills/work-loop/evals/evals.json`:
- `step0-no-portfolio-reconcile`: work-loop invocation must not trigger portfolio stale scan
- `reconcile-stale-routes-to-workspace-status`: "reconcile stale workspace entries" → `workspace-status reconcile`
- `find-untracked-specs-routes-to-reconcile`: "find untracked specs" → `workspace-status reconcile`
- `status-query-routes-to-workspace-status`: "what should I work on?" → `workspace-status status`
- `explain-query-routes-to-explain`: "why is spec/foo blocked?" → `workspace-status explain`

---

### T6 — Run make build-self and verify projections

**Mode:** Goal-based check
**Done when:** `make build-self` exits 0; `.claude/skills/work-loop/SKILL.md` matches source;
`.claude/skills/workspace-status/scripts/workspace_status_engine.py` matches source.

**Approach:** Run `make build-self`. Verify byte-equivalence of work-loop SKILL.md and
workspace-status engine in `.claude/` vs `packs/core/`.

---

### T7 — Capture read profile and run gates

**Mode:** Visual / manual QA
**Approach:**
1. Run `workspace-status reconcile` against the repo's own workspace.toml; record output.
2. Record the before-state and after-state Step 0 file-read profile. Note: the profile is
   derived from the characterization fixture (the removed `collect_work_loop_stale_warnings`
   read N spec files per active initiative queue+active list), not a measured work-loop runtime
   invocation (work-loop is agent prose). The stop point is the engine function removal.
3. Write evidence to `docs/specs/workspace-status-simplification-order-2a/notes/read-profile.md`.
4. Run `python3 tools/lint-ruff.py`, `SKIP_SAST=1 make build-check`, `make ci`.

## Resolve-vs-surface disposition record

| Situation | Resolution |
|-----------|-----------|
| Hash update after SKILL.md change | Resolve: compute new hash programmatically, update constant |
| Test removal of `case_work_loop_stale_warnings` | Resolve: replace with sentinel + parity tests (same row count) |
| No root `scripts/` directory for loop-cohort | Named skip: apply full mode rigor inline |
| Historical spec refs to stale-queue check | Resolve: out of scope; shipped specs are historical record |

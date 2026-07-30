# Plan: workspace-status simplification — Order 0

**Status:** Done

**Assumption trio:**
1. Files touched: 7 new files in `tools/` and `docs/specs/workspace-status-simplification-order-0/`; no existing files modified
2. Tests demonstrate done: `python3 tools/test_workspace_status.py` exits 0; `python3 tools/bench-workspace-status.py` exits 0 and prints measurements
3. Not changing: `packs/core/.apm/skills/workspace-status/SKILL.md`, `packs/core/.apm/skills/work-loop/SKILL.md`, `workspace.toml` schema, any existing test

**Declined:**
- Extracting engine into `packs/core/` — future order, not order 0
- Adding CLI entry point to engine — not needed for tests
- Fixing the `backlog:<slug>` needs-prefix inconsistency — document, don't fix
- Fixing cycle detection absence — document as known gap, don't fix
- Adding tomlkit for comment-preserving writes — benchmark/tests are read-only; test the write shape but don't exercise it

## Tasks

### T1 — Behavior map document
`docs/specs/workspace-status-simplification-order-0/notes/behavior-map.md`

Mode: goal-based check (document created with required sections)
Done when: file exists and covers all required sections per AC1

Tests: none — document

### T2 — Python engine
`tools/workspace_status_engine.py`

Mode: TDD (pure functions testable with fixtures)
Done when: `from workspace_status_engine import analyze, run_reconciliation, classify_entries` imports clean

Tests:
```
# stub: test_dag_resolution imports engine, resolves deps on minimal fixture
```

### T3 — Characterization tests
`tools/test_workspace_status.py`

Mode: TDD (characterization suite)
Done when: `python3 tools/test_workspace_status.py` exits 0, covers AC3a–AC3h

Tests: the test file IS the test

### T4 — Benchmark
`tools/bench-workspace-status.py`

Mode: goal-based check + visual/manual QA
Done when: `python3 tools/bench-workspace-status.py` exits 0 and prints measurements

Tests: none — benchmark script self-validates by running

### T5 — Baseline report
`docs/specs/workspace-status-simplification-order-0/notes/baseline-report.md`

Mode: goal-based check (filled after T4 runs)
Done when: file contains benchmark command, fixture dimensions, timing, and all required sections per AC5

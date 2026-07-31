# Spec: workspace-status simplification — Order 0

- **Status:** Shipped
- **Plan:** [`plan.md`](plan.md)
- **Mode:** full (multi-feature + structural: new Python module + test infrastructure)
- **Constrained by:**
  - [RFC-0064](../../rfc/0064-ini-001-ai-native-ecosystem.md) — defines workspace.toml schema and workspace-status behavior
  - [RFC-0049](../../rfc/0049-the-release-loop-and-company-os.md) — Company OS composition: architectural authority for the three-loop model
  - `packs/core/.apm/skills/workspace-status/SKILL.md` — production behavior; must not change
  - `packs/core/.apm/skills/work-loop/SKILL.md` — workspace.toml interactions; must not change

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Establish an executable behavioral baseline and a reproducible performance
benchmark for workspace-status before any simplification begins. This is a
characterization and test-infrastructure change only.

- **Hard scope:** executable reference model, fixtures, tests, benchmark, documentation only
- **Hard exclude:** no production behavior change; no schema change; no caching; no optimization

## Boundaries

### Always do

- Extract workspace-status algorithmic core (TOML parse, DAG resolution, reconciliation scans) into `tools/workspace_status_engine.py` as an executable reference model (manually transcribed Python interpretation of SKILL.md; not a production seam)
- Write characterization tests in `tools/test_workspace_status.py` covering all scenarios listed in AC3
- Write a benchmark in `tools/bench-workspace-status.py` generating ≥250 spec directories
- Create a behavior map at `docs/specs/workspace-status-simplification-order-0/notes/behavior-map.md`
- Create a baseline report at `docs/specs/workspace-status-simplification-order-0/notes/baseline-report.md`
- Mark known defects explicitly in tests rather than silently preserving them

### Ask first

- Changing the documented behavior of any existing test (rather than adding new tests)
- Adding a test that requires an external dependency beyond stdlib + tomlkit

### Never do

- Change `packs/core/.apm/skills/workspace-status/SKILL.md`
- Change `packs/core/.apm/skills/work-loop/SKILL.md`
- Change `workspace.toml` schema
- Add caching, workspace-reconcile subcommand, or Group A/B/C/D migration work
- Fix bugs found during characterization (document them instead)

## Testing Strategy

All criteria use **TDD** (testable logic: pure functions over parsed TOML data).
Verification mode: `python3 tools/test_workspace_status.py` exits 0.
Benchmark: `python3 tools/bench-workspace-status.py` exits 0 and prints measurements.

## Acceptance Criteria

### Deliverable 1 — Behavior map

- [x] AC1. `docs/specs/workspace-status-simplification-order-0/notes/behavior-map.md` exists and records: every input read by workspace-status; every mode/flag; ready/blocked/active/shipped computation; all `needs` prefixes and resolution semantics; the three reconciliation scan types; every workspace.toml read and write performed by work-loop; which state is authoritative vs. derived/duplicated today; intended future ownership boundary (labeled as proposed).

### Deliverable 2 — Characterization fixtures

- [x] AC2a. Multiple active initiatives fixture exists.
- [x] AC2b. Paused, closed (documented form), and complete (legacy form) initiatives fixture exists.
- [x] AC2c. Ordered queues fixture (queue order preserved as priority).
- [x] AC2d. Local work dependencies fixture.
- [x] AC2e. Cross-initiative work dependencies fixture.
- [x] AC2f. Shape, research, and brief dependencies fixture.
- [x] AC2g. Ready and transitively blocked work fixture.
- [x] AC2h. Approved, Implementing, Shipped, and Archived spec statuses fixture.
- [x] AC2i. Missing spec paths fixture.
- [x] AC2j. Missing dependency targets fixture.
- [x] AC2k. Dependency cycles fixture.
- [x] AC2l. Untracked Approved or Implementing spec fixture (Type 1).
- [x] AC2m. Queued/active entry with Shipped/Archived spec (Type 2).
- [x] AC2n. Shipped entry with Approved/Implementing spec (Type 3).
- [x] AC2o. Multiple active items for argless work-loop behavior.
- [x] AC2p. Deferred backlog anchors.

### Deliverable 3 — Characterization tests

- [x] AC3a. Tests cover DAG and dependency resolution (all `needs` prefix forms).
- [x] AC3b. Tests cover ready and blocked classifications.
- [x] AC3c. Tests cover cross-initiative dependency behavior.
- [x] AC3d. Tests cover Type 1, Type 2, and Type 3 reconciliation findings.
- [x] AC3e. Tests cover argless work-loop resume (0, 1, multiple active specs).
- [x] AC3f. Tests cover work-loop shaping-item guard scenario.
- [x] AC3g. Tests cover workspace-status Type 2 cleanup mutation shape (workspace-status owns this; work-loop ≥ a46d6f46 does not mutate queue/active/shipped at completion).
- [x] AC3h. Tests mark known defects explicitly (not silently preserving them).

### Deliverable 4 — Benchmark

- [x] AC4a. Generated fixture has ≥250 spec directories.
- [x] AC4b. Generated fixture has 30–80 queued entries.
- [x] AC4c. Generated fixture has several active initiatives.
- [x] AC4d. Mix of ready, blocked, active, shipped, and archived specs.
- [x] AC4e. At least one cross-initiative dependency chain.
- [x] AC4f. At least one untracked live spec.
- [x] AC4g. Measures: spec files inspected, workspace files inspected, execution time, output size, finding counts.
- [x] AC4h. Benchmark runs from `python3 tools/bench-workspace-status.py`.

### Deliverable 5 — Baseline report

- [x] AC5. `docs/specs/workspace-status-simplification-order-0/notes/baseline-report.md` contains: repo revision; benchmark command; fixture dimensions; files inspected (normal and exhaustive paths); execution time observations; correctness findings; known test gaps; measurements Order 1 should improve.

### Gates

- [x] AC6. `python3 tools/test_workspace_status.py` exits 0.
- [x] AC7. `python3 tools/bench-workspace-status.py` exits 0 and prints measurements.
- [x] AC8. `make build-check` passes (existing tests unaffected).
- [x] AC9. `git diff` contains no production behavior change (no SKILL.md edits).

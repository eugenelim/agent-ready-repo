# Read-profile evidence: Order 2A stale-scan removal

## Before (pre-Order 2A) — work-loop Step 0 file-read profile (modeled estimate)

Note: `collect_work_loop_stale_warnings` was called only from characterization tests,
not from a running `work-loop` agent session (work-loop is prose, not a script).
The estimate below models what the function *would have* read had work-loop called
it, based on its implementation and the repo's current workspace.toml.

`collect_work_loop_stale_warnings(root, initiatives)` iterated every entry in
`.work.queue` and `.work.active` for each **active** initiative, resolved each
to a `spec.md` path, and read that file to check `**Status:**`. With the repo's
workspace.toml as of Order 2A implementation (3 active initiatives: ini-002 with
4 queue entries, ini-003 with 10, ini-007 with 7 = **21 total**), this would
produce up to 21 spec.md reads per work-loop startup before PLAN began — a
modeled upper bound (deduplication and missing-file skips reduce the actual count).

Note: the `declared_spec_files_read: 53` reported by the reconcile run below is
_not_ comparable — `_run_type23_scan()` also reads shipped entries and non-active
initiatives. The 21 figure is derived directly from active queue/active lists.

Engine function removed: `collect_work_loop_stale_warnings` (~40 lines).
Dataclass removed: `WorkLoopStaleWarning`.

## After (post-Order 2A) — work-loop Step 0 file-read profile

Work-loop Step 0 now reads:

1. `workspace.toml` — 1 file
2. `docs/specs/<active-slug>/spec.md` — 1 file (argless resume, exactly one active item)
3. `docs/specs/<active-slug>/plan.md` — 1 file (immediately after spec.md, same condition)
4. Shaping-queue entries for slug matching — 0 additional file reads (uses
   already-parsed workspace.toml data)

Total files read before PLAN: 3 (workspace.toml + spec.md + plan.md). Stale-scan
reads eliminated: **up to 21 additional spec.md reads per startup** (modeled upper bound; see below).

## Reconcile ownership proof (`workspace-status reconcile` run, 2026-08-01)

```
reconciliation.complete: true
spec_files_read: 311 (global scan, all spec dirs)
declared_spec_files_read: 53
type1: [{"spec_path": "spec/workspace-status-simplification-order-2a",
          "spec_status": "Implementing"}]
type2: []
type3: []
```

The Type 1 finding is the current spec (expected; Status: Implementing is the
in-progress marker). Type 2 is empty — no stale queue/active entries in the
repo's workspace. The reconcile run proves:

- `analyze()` reads 311 spec files exhaustively (global scan).
- The same stale entries that work-loop used to warn about are detectable as
  Type 2 findings when they exist (proven by `case_work_loop_reconcile_owns_stale`).
- Work-loop no longer participates in stale detection.

## AC19 verification

AC19: "The read-profile evidence demonstrates stale-scan removal."

✓ `collect_work_loop_stale_warnings` absent from engine (sentinel test green).
✓ Work-loop SKILL.md Step 0 contains ownership note; no stale-queue check bullet.
✓ Modeled estimate: up to 21 spec.md reads eliminated per work-loop invocation (21 = active queue/active entries at time of removal; dedup/skip reduces actual count).
✓ Reconcile still detects stale entries (parity test green).

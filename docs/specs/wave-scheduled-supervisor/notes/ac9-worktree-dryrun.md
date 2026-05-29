# AC9 — worktree/merge dry-run (run 2026-05-29)

The CONVENTIONS "Known limitation" requires the worktree/merge surface to be
validated by a **real `git worktree add` + dispatch round**, not a prose
walk-through, before it is trusted. T4's parallel-write path was exercised
end-to-end on a throwaway repo (own `.git`) against the real `loop-cohort`
functions (`wave_is_disjoint`, `dispatch_decision`):

```
git worktree add x3                : ok
wave_is_disjoint(task-a, task-b)   : True   (disjoint files — x.py vs y.py)
wave_is_disjoint(task-a, task-c)   : False  (both edit x.py → git merge-tree conflict)
dispatch_decision(safe, disjoint)  : parallel
dispatch_decision(safe, overlap)   : serial  (fail closed)
real merge of disjoint pair        : CLEAN
VERDICT: PASS
```

**Finding:** the opt-in parallel-write path behaves as specified —
`git merge-tree` correctly distinguishes disjoint from overlapping waves,
the dispatch gate fails closed on overlap, and a real sequential merge of a
disjoint pair is clean. Harness (in-tree, reproducible):
[`ac9_worktree_dryrun.py`](ac9_worktree_dryrun.py) — run with
`python3 docs/specs/wave-scheduled-supervisor/notes/ac9_worktree_dryrun.py`
(exit 0 = PASS).

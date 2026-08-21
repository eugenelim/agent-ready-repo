# Plan: worktree-runtime-hygiene

- **Status:** Done
- **Spec:** [`spec.md`](spec.md)

## Task 1 — scan and safe clean (this implementation)

1. Add the pure-stdlib repository-local CLI with porcelain-only discovery, one-pass
   classification, measurement labelling, cache/editable-install diagnosis, and stable
   JSON/human rendering.
2. Add receipt-only clean plus opt-in category deletion guarded by registered-root,
   link, Git-administration, tracked, ignored, protection, lock, and editable-install
   checks.
3. Add tempfile falsification tests and bounded-process/traversal proofs.
4. Append a dedicated pytest invocation for the new tool test; do not merge it into
   the existing basename-collision-prone invocation.

## Task 2 — concurrency runtime controls (partially shipped)

1. Shipped: preview-port override and gate wrapper with a port lease.
2. Shipped: browser-cache path resolution and selective bootstrap profiles.
3. Split out: the cooperative worktree lease. It was built to completion and then
   removed from this spec under review — see `spec.md` AC6's deferral note and
   `docs/specs/worktree-cooperative-lease/`. What landed here instead are the two
   residuals that were always independent of it: the normal-exit process-group reap
   and the preview-port test's cold-transform flake.
3. Open: add a cooperative worktree lease shared by cleanup and mutating build/test
   entry points to close the remaining check-to-delete concurrency window.

AC7 is shipped. AC6 remains open: its shared cleanup/build-test lease is not
implemented, even though the preview-port lease is present.

## Task 3 — isolated agentbundle import-resolution check (this layer)

Tests: focused `tools/test_worktree_import_resolution.py` cases for in-tree,
outside-tree, absent, non-zero/unparseable, polluted stdout, environment isolation,
and schema shape; register a separate Makefile invocation to avoid basename collisions.

1. Resolve `agentbundle` once in an isolated child with `PYTHONPATH` removed and
   bytecode writes disabled.
2. Add the result and its provenance to scan's JSON and human report without a
   version comparison, remediation advice, or exit-code change.
3. Fail closed into stated absent or inconclusive findings.

## Task 4 — bounded test-evidence lifecycle (shipped)

Tests: dedicated `tools/test_playwright_evidence_lifecycle.py` invocation covering
failed-run archival, successful-run cleanup, explicit archive-time ordering across
two invocations, file and directory pin retention, age-budget expiry, predicate
re-assertion before deletion, current-worktree refusal, and budget parsing.

1. Wrap the existing browser-gate command in `frontend_runtime.run_gate` without
   changing its pinned command strings or Playwright diagnostics.
2. Retain failed `web/test-results/` evidence in ignored, worktree-local storage while
   preserving that live path for the existing Pages failure-artifact upload; remove
   successful `test-results` and `playwright-report` output immediately.
3. Keep the newest explicitly timestamped failed run and non-symlink `.pinned`
   evidence, pruning only older unpinned runs by the configurable seven-day-default
   age budget through the hygiene module's registered-current-worktree predicate and
   its immediate pre-mutation recheck. Release the preview-port lease after the
   child gate exits and before this lifecycle work starts.

## Task 5 — worktree lifecycle hooks (shipped)

Tests: dedicated `tools/test_worktree_lifecycle_hooks.py` invocation covering each
optional hook's Git-backed lifecycle report, the no-Orca implementation boundary,
inside import success, shadowing refusal, and the existing protection channels.

1. Added optional `after-create`, `before-run`, `after-run`, and `before-remove`
   commands that report default-branch-merged, Git-backed prune-signal,
   currently-active, and no-merge-or-prune-signal worktrees without claiming
   liveness or attaching to Orca.
   When Git cannot determine the default branch, the merged result is undetermined.
2. Made `before-remove` reuse AC8's isolated import-resolution measurement and refuse
   outside, absent, and inconclusive results, as well as existing protected worktrees.
3. Kept every lifecycle command report-only: none removes a worktree, directory, or
   branch.

## Task 6 — the two residuals (this layer)

**Depends on:** Task 1, Task 2, Task 3, Task 4, Task 5 (all shipped)

Owns AC11 and AC12. Both were documented residuals of earlier rounds and neither
depends on the cooperative lease, which is why they land while it does not.

Tests: `tools/test_managed_child.py` gets its own Makefile pytest invocation;
`web/src/test/site-base.test.ts` extends the existing vitest suite. Additions to
`tools/test_frontend_runtime.py` reuse its existing invocation.

### Measured, so the design is evidence rather than assertion

- `os.getpgid` on an unreaped zombie raises `ProcessLookupError`, 15 of 15, so the
  group cannot be looked up after the child exits and is captured at spawn instead
  (20 of 20, equal to the pid).
- `killpg` on a group whose only member is the caller's own unreaped zombie answers
  `EPERM` on macOS — 12 of 12 with signal 0, 8 of 8 with `SIGTERM`, 6 of 6 again
  when re-measured — while it succeeds 4 of 4 with a live grandchild present. A
  group-drain probe therefore cannot distinguish "empty but for my zombie" from
  "not my group", so the design omits the probe: signal, grace, escalate, reap.
  After a successful ownership proof the group is provably ours, so `EPERM` there
  means no signalable live member, which is success.
- That measurement is macOS only. On Linux a zombie is a signalable member of its
  own group, so `killpg` is expected to succeed and the grace to fire on every run;
  the grace is kept short for that reason and the comment says so rather than
  claiming it is free.
- `Popen.send_signal` calls `poll()`, and `poll()` reaps an exited child, after
  which the ownership proof correctly refuses and signals nothing. Nothing may poll
  or wait before the reap; a test pins it.
- vitest: first case 1536 ms and 2247 ms across two runs, later cases 7-52 ms; an
  instrumented probe put 1817.9 ms in the dynamic import and 0.1 ms in
  `vi.resetModules()`. With the warm-up hook, first case 9-11 ms. The hook needs an
  explicit budget because vitest's default hook timeout is 10000 ms and a loaded
  full-suite run measured that import at ~114 s.

### Tempted and declined

- Landing the cooperative lease with this change. Declined: three independent
  reviewers found failure modes AC6 does not enumerate, including a Windows
  byte-range defect in the claim lock that would let `clean --apply` delete under a
  live mutator. Shipping it behind a criterion that does not describe it would have
  been worse than shipping nothing.
- Widening AC6 to cover what was built. Declined: the operator asked for a split, and
  a criterion amended to match its implementation stops being a contract.

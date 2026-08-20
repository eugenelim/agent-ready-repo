# Plan: worktree-runtime-hygiene

- **Status:** Executing
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
failed-run archival, successful-run cleanup, newest and pinned retention, age-budget
expiry, predicate re-assertion before deletion, current-worktree refusal, and budget
parsing.

1. Wrap the existing browser-gate command in `frontend_runtime.run_gate` without
   changing its pinned command strings or Playwright diagnostics.
2. Retain failed `web/test-results/` evidence in ignored, worktree-local storage while
   preserving that live path for the existing Pages failure-artifact upload; remove
   successful `test-results` and `playwright-report` output immediately.
3. Keep the newest failed run and `.pinned` evidence, pruning only older unpinned runs
   by the configurable seven-day-default age budget through the hygiene module's
   registered-current-worktree predicate and its immediate pre-mutation recheck.

## Task 5 — worktree lifecycle hooks (shipped)

Tests: dedicated `tools/test_worktree_lifecycle_hooks.py` invocation covering each
optional hook's Git-backed lifecycle report, the no-Orca implementation boundary,
inside import success, shadowing refusal, and the existing protection channels.

1. Added optional `after-create`, `before-run`, `after-run`, and `before-remove`
   commands that report default-branch-merged, removed, currently-active, and
   no-merge-or-prune-signal worktrees without claiming liveness or attaching to Orca.
   When Git cannot determine the default branch, the merged result is undetermined.
2. Made `before-remove` reuse AC8's isolated import-resolution measurement and refuse
   outside, absent, and inconclusive results, as well as existing protected worktrees.
3. Kept every lifecycle command report-only: none removes a worktree, directory, or
   branch.

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

## Task 4 — bounded test-evidence lifecycle (planned)

Plan and implement bounded retention and cleanup of test evidence without broadening
the worktree doctor's deletion authority.

## Task 5 — worktree lifecycle hooks (planned)

Plan and implement lifecycle hooks that coordinate worktree creation and removal with
the existing safety model.

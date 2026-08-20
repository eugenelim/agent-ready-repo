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

## Task 2 — concurrency runtime controls (not started by this task)

1. Add a preview-port override and gate wrapper with a port lease.
2. Add browser-cache path resolution and selective bootstrap profiles.
3. Add a cooperative worktree lease shared by cleanup and mutating build/test entry
   points to close the remaining check-to-delete concurrency window.

Task 2 implements AC6–AC7. It has no code change in this task and must be scheduled
as its own implementation work rather than smuggled into scan/clean.

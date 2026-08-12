# Spec: self-host cross-owner write

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** maintainers
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0002](../../rfc/0002-self-hosting.md),
  [`self-hosting`](../self-hosting/spec.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Maintainers and downstream automation can run
`agentbundle catalogue self-host --write --root .` when existing projected
single-link regular files on seed and adapter direct-file rails are writable
but owned by another user. The command replaces projected content
in the existing inode without attempting owner-only timestamp or mode
mutations. Ownership and mode remain intact; the operating system advances
modification time as a consequence of writing bytes. New projected files retain
the metadata behavior of their projection rail, and the read-only self-host
check still reports source-mode drift even when the write process cannot repair
it.

## Boundaries

### Always do

- Copy source bytes into an existing regular destination while preserving its
  inode, ownership, and mode. Modification time may advance naturally; never
  restore it with `utime`.
- Preserve the cross-platform metadata required by drift comparison for newly
  created destinations: seed copies inherit source mode, while adapter
  direct-file copies inherit source mode and, on POSIX, timestamps.
  Platform-specific flags and extended attributes are not part of the self-host
  contract.
- Render dry-run output with source metadata so the existing low-nine-bit mode
  comparison continues to detect unresolved mode drift.
- Confine every overwrite beneath the selected output root and refuse symlink,
  hard-link, directory, and file-type races through the existing no-follow
  projection I/O boundary before writing bytes.
- On a write or truncate failure, attempt to restore the original bytes through
  the already-open regular-file descriptor, then propagate a nonzero failure;
  if restoration also fails, report both failures. A write-only destination
  retains the historical content-copy permission floor and propagates write
  failures without rollback because its original bytes cannot be read.
- Refuse metadata-preserving projection files larger than 64 MiB before
  truncation so the in-memory rollback snapshot is bounded.

### Ask first

- Changing the metadata-preservation rule outside self-host real-write mode.
- Changing symlink traversal, directory replacement, or atomic-write semantics.
- Changing the self-host mode-comparison contract or suppressing reported mode
  drift.

### Never do

- Catch or suppress content-copy failures; only the pre-existing destination's
  metadata mutation is omitted.
- Replace an existing destination through a temporary-file rename: downstream
  jobs may have write permission on the file without write permission on its
  parent directory.
- Treat direct-directory tree replacement as an existing-file overwrite. Those
  rails deliberately remove and recreate their destination tree and therefore
  require parent-directory ownership; changing that contract is separate work.
- Add a dependency, public option, new adapter interface, or top-level
  directory.

## Testing Strategy

- **TDD, unit:** fault-inject owner-only metadata failures into an existing seed
  target and an adapter direct-file target. Each projection completes, updates
  bytes in the same inode, leaves ownership and mode unchanged, and makes no
  explicit timestamp-restoration call.
- **TDD, unit:** a newly created seed target inherits source mode and a newly
  created adapter target inherits source mode and timestamps.
- **TDD, integration:** real-write selects metadata-preserving overwrites for
  every shipped effective adapter derived from the bundled contract, while
  dry-run selects normal source-metadata copies and continues to report a
  deliberate POSIX mode difference.
- **Goal-based:** focused tests, the complete AgentBundle package tests, Ruff,
  Mypy, and the repository build check pass.
- **Manual QA, CLI:** invoke the published self-host write command in a checkout
  fixture whose existing projected file rejects `chmod` and `utime`; observe
  exit zero and updated content. This environment cannot construct that fixture,
  so the final verification is operator-run.

Stub tally: 7 TDD behavior groups covered; 0 uncovered; goal-based and manual-QA
checks have no stubs by mode.

## Acceptance Criteria

- [ ] **AC1.** When self-host real-write overwrites an existing projected
  regular file on a seed or adapter direct-file rail, it updates the bytes in
  the same inode without calling `copymode`, `copystat`, `chmod`, or `utime` for
  that destination. Ownership and mode remain unchanged; modification time may
  advance because content changed. Write-only destinations are supported but
  cannot be rolled back after truncation if their content write fails.
- [ ] **AC2.** Metadata preservation covers seed projection and every adapter
  direct-file rail reachable through the effective self-host adapter set,
  including non-default `preferred-adapter` selections.
- [ ] **AC3.** A newly created seed file inherits source mode, while a newly
  created adapter direct-file target inherits source mode and, on POSIX,
  timestamps.
- [ ] **AC4.** Dry-run and ordinary non-self-host adapter projections retain
  source metadata behavior. On POSIX, self-host check still reports a mode
  difference between source and an existing destination.
- [ ] **AC5.** Content-copy, path, and file-type errors still propagate; the fix
  does not broadly catch `PermissionError` or `OSError`.
- [ ] **AC6.** Existing-file overwrites are confined beneath the selected root,
  open the destination without following links, verify the opened target is the
  expected single-link regular file, and refuse symlink, hard-link, directory,
  or identity races before writing any bytes.
- [ ] **AC7.** If an in-place write or final truncate fails, self-host attempts
  to restore the original bytes through the held file descriptor and exits
  nonzero. A restoration failure is attached to the original error rather than
  swallowed. A source or existing destination larger than 64 MiB refuses before
  truncation so the rollback snapshot stays bounded. A write-only destination
  propagates write failure without rollback because no snapshot is possible.
- [ ] **AC8.** AgentBundle version pins are prepared as `0.33.3`, and its
  changelog explains the cross-owner self-host correction, natural mtime update,
  and unresolved-mode tradeoff. Publication and Shipped closeout occur in the
  required follow-on after this implementation change merges.
- [ ] **AC9.** Focused regression tests, the complete AgentBundle test suite,
  Ruff, Mypy, and `SKIP_SAST=1 make build-check` pass. The existing Windows
  aggregate check remains blocking on parallel AgentBundle and CredBroker jobs.

## Assumptions

- Technical: self-host direct-file writes flow through adapter `shutil.copy2`
  calls, while seed writes use `shutil.copy` (source:
  `packages/agentbundle/agentbundle/build/self_host.py` and
  `build/adapters/*.py`).
- Technical: `shutil.copy2` performs `copyfile` then `copystat`, and
  `shutil.copy` performs `copyfile` then `copymode` (source: local Python
  standard-library source probe, 2026-08-12).
- Technical: existing destinations preserve ownership and mode even when mode
  differs from source; mtime advances naturally because preserving it would
  require the denied `utime`; self-host check surfaces an unrepairable mode
  difference (source: user intent confirmed 2026-08-12; feasibility correction
  from spec review 2026-08-12).
- Technical: rollback without a writable parent requires reading the original
  bytes before truncation. Write-only destinations retain `copyfile`'s prior
  content-write permission floor but necessarily retain its partial-write risk
  on failure (source: adversarial implementation review 2026-08-12).
- Technical: hard-linked destinations fail unchanged because an in-place write
  to one link mutates every path sharing the inode, which is not a confined
  single-path projection (source: implementation security review 2026-08-12).
- Product: downstream CI and developer checkouts may grant content-write access
  to files owned by another UID while denying owner-only metadata operations
  (source: user report 2026-08-12).
- Process: engine changes bump both AgentBundle version pins and require an
  `Engine-Change-RFC:` commit footer (source: `packages/AGENTS.md` and
  `packages/AGENTS.local.md`).
- Process: base freshness and local tempfile-dependent gates are named skips in
  this environment; the operator runs the final verification commands (source:
  user confirmation 2026-08-12).

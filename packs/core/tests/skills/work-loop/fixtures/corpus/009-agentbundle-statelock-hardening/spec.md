# Spec: agentbundle-statelock-hardening

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Contract:** `agentbundle.statelock` gains one exception type
  (`StateLockUnusable`, an `OSError`). No existing signature changes.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

<!-- Mode: full. Risk trigger: security boundary — a denial-of-service on every
state-mutating verb, reachable by any writable path next to a state file.
`security-reviewer` cannot be dispatched under this session's no-subagent
instruction, so its absence is a NAMED SKIP; the reasoning is inline in the plan. -->

## Objective

One planted file wedged every state-mutating `agentbundle` verb at 100% CPU,
forever, with the timeout never firing. Close that, and the three adjacent races
in the same lock.

## Acceptance Criteria

- [x] **AC1 — the hot spin is reproduced before it is fixed.** Against the
  shipped package: a dangling symlink at `<state>.lock` makes
  `os.open(O_CREAT|O_EXCL)` fail `FileExistsError` while `Path.stat()` follows
  the link and raises `FileNotFoundError`; that handler looped with neither a
  deadline check nor a sleep. Measured: still spinning past a 2.0s timeout.

- [x] **AC2 — every retry path checks the deadline and sleeps.** All three
  continue-paths in the acquire loop (released-between-open-and-lstat, reclaim,
  and ordinary contention) now bound themselves.

- [x] **AC3 — the examine step does not follow links, and refuses what waiting
  cannot fix.** `os.lstat` replaces `Path.stat()`; a lock path that is not a
  regular file raises `StateLockUnusable` **immediately** rather than waiting out
  a timeout that cannot succeed. Reporting a timeout there would tell an operator
  to retry, which would never work; the message says to remove the file.

- [x] **AC4 — the new exception cannot surprise a caller.**
  `StateLockUnusable` subclasses `OSError`, as `StateLockTimeout` does. The two
  production consumers are `install.py` (catches `Exception` and rolls back) and
  `oplog.py` (propagates, and already raises bare `OSError` for a symlinked
  oplog path).

- [x] **AC5 — release keys on inode identity AND a per-hold token.** Release was
  an unconditional `unlink(missing_ok=True)`, so a hold whose lock had been
  reclaimed mid-body would delete its *successor's* live lockfile — two holders
  inside the section, produced by a release rather than an acquire. Identity
  alone is insufficient: ext4 and tmpfs reuse inode numbers aggressively, so a
  successor can land on the freed inode. The uuid4 token makes a false positive
  require reproducing a uuid4.

- [x] **AC6 — a mismatched reclaim restores by `os.link`, not `rename`.**
  `rename` silently replaces its destination, so if a third process took the
  momentarily-free lock path, restoring by rename would delete that process's
  lockfile and admit two holders. `link` fails with `FileExistsError` instead —
  failing closed.

- [x] **AC7 — each property has its own test, and they are mutation-verified.**
  Reverting AC2+AC3 makes `test_a_dangling_symlink_lock_path_does_not_spin` fail
  with the spin assertion; restoring passes. Tests are separated per property so
  a regression names which one returned.

- [x] **AC8 — the hardening does not cost the deadlock recovery it protects.**
  A stale (one-hour-old) lock is still reclaimed, and a fresh foreign lock is
  still waited on and then times out — asserted to actually wait, not refuse.

- [x] **AC9 — released.** 0.36.1 → 0.36.2, both changelogs, backlog entry removed.

## Boundaries

### Never do

- Never merge this module with the work-loop skill's `_statelock.py`. ADR-0074
  keeps them separate deliberately — different files, different consumers. This
  ports the hardening; it does not share the code.
- Never use `Path.stat()` on the lock path. Following the link is the defect.

## Testing Strategy

- **TDD + mutation** throughout; the reproduction came first.

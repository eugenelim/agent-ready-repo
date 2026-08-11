# Spec: work-loop-concurrency-harness-reliability

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** maintainers
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0074
- **Contract:** none
- **Shape:** integration

Mode: full (filesystem-lock integrity and exceptional-condition boundary)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The work-loop concurrency self-test identifies its failing case in CI and
distinguishes a real lock regression from slow or unfair process scheduling.
The state lock never reclaims a live holder's freshly created lockfile before
its ownership record is written, while retaining bounded recovery of a stale
empty lockfile left by a crashed creator. Unrelated writes to the live checkout
do not change the suite's result.

## Acceptance Criteria

- [x] **AC1.** `test-loop-cohort.sh` preserves the concurrency child's stdout
      and stderr, including its `FAIL [case-name]: assertion` diagnostic, before
      the wrapper's suite-level failure summary.
- [x] **AC2.** The three concurrent mutation cases prove that all non-leading
      children contended on the leader's occupied production state lock; they
      do not infer overlap from a wall-clock arrival-spread threshold.
- [x] **AC3.** The seven existing case names remain unchanged, and each failure
      reports the case name plus the last observed synchronization state.
- [x] **AC4.** `harness-is-hermetic` proves every engine child resolved and
      wrote its throwaway repository; it does not compare the mutable live
      checkout against an import-time fingerprint.
- [x] **AC5.** While one process is deliberately paused after creating an empty
      lockfile and before writing its ownership record, a contender treats the
      file as occupied and times out without entering the critical section.
      The lock path retains the leader's inode throughout that contention; once
      released to write its record, the leader enters, exits successfully, and
      removes its own lock without `StateLockLost`.
- [x] **AC6.** An empty lockfile whose age exceeds `stale_after` remains
      reclaimable, preserving crash recovery without changing timeout or stale
      budgets.
- [x] **AC7.** The state-lock suite and all seven concurrency cases pass, the
      concurrency suite passes at least 50 consecutive runs on the fixed tree,
      and a run with the state lock deliberately bypassed fails the affected
      concurrency case.
- [x] **AC8.** The canonical pack source and generated projections are
      byte-identical after `make build-self`; the core patch version and
      changelog describe the shipped lock-integrity fix.
- [x] **AC9.** `lock_path_for` remains lexical, and every lock artifact stays in
      the state path's sibling directory as `<name>.lock` or a transient
      `<name>.lock.reclaim.*` companion. Acquisition and stale reclaim through a
      symlinked state path do not touch the symlink target's directory;
      lock-path symlinks—including links to existing regular files—and other
      non-regular paths are refused without modifying their targets.

## Boundaries

- **Always:** fail closed when lock ownership is unknown; preserve inode and
  record checks during reclaim and release; test the exact create-before-write
  interleaving with explicit process synchronization.
- **Ask first:** changing `timeout`, `poll`, or `stale_after`; changing the lock
  path, record format, state schema, or work-loop FSM.
- **Never:** immediately reclaim an unattributed fresh empty lockfile; delete an
  unrecognised or non-regular lock path; add a dependency or platform-specific
  lock primitive for this fix; edit the frozen body of ADR-0074.

## Testing Strategy

The wrapper uses a goal-based shell check because the observable contract is
its emitted child output. The harness uses TDD at the process-integration
boundary: explicit lock-contention handshakes replace timing inference, and the
same case is exercised with locking deliberately bypassed to prove that the
regression remains discriminating.

The lock regression uses a deterministic two-process construction test. The
leader's record write is paused after `O_CREAT|O_EXCL` creates the empty file;
the follower must time out before the leader is released. The complementary
stale-empty test proves that bounded recovery still works. Reliability proof
runs both direct suites, the wrapper, repository gates, and 50 consecutive
concurrency-suite iterations on a writable runner.

## Assumptions

- Technical: `O_CREAT|O_EXCL` makes the lock path visible before the subsequent
  `os.write`, so a freshly observed empty file can belong to a live creator
  (source: reproduced run 23 and `_statelock.py` acquisition order).
- Product: CI logs must identify the exact failed case and assertion (source:
  user confirmation 2026-08-10).
- Process: no timeout is widened and no case is skipped (source: user
  confirmation 2026-08-10).
- Environment: tempfile-based execution proof runs on a writable local or CI
  runner, not in this restricted session (source: user confirmation 2026-08-10).

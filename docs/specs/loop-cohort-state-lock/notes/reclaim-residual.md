# Reclaim residual: check-then-rename is not one operation

This document is the artifact of the canonical `[backlog].open` entry
`docs/specs/loop-cohort-state-lock/notes/reclaim-residual.md`
(`kind = "defect"`). It records one residual that a shipped repair knowingly
leaves open, so the next reader who sees `StateLockLost` does not re-derive the
investigation behind it.

## What was repaired

`test_concurrent_reclaimers_yield_one_holder` failed intermittently on CI
runners with two processes inside one critical section:

```
ENTER 5470, ENTER 5471, EXIT 5470, ERR StateLockLost, EXIT 5471
```

`_statelock._reclaim` validated inode identity and the per-hold record *after*
renaming the lock away. The rename is what frees the lock path, so a contender
acting on a snapshot that a successful reclaim had already superseded moved the
new holder's live lock, and a third contender's `O_CREAT|O_EXCL` then succeeded
on the free path while the first holder was still inside its section. The repair
re-checks identity immediately *before* moving anything and leaves a lock it no
longer recognises alone.

## What remains open

**The check and the rename are two operations.** A holder that acquires between
them is still displaced, exactly as before. It reports `StateLockLost` at
release, which is the module's documented signal, so no write is silently lost —
but the window is not zero.

This is a property of the protocol, not of the code. POSIX offers no
rename-if-unchanged, so no amount of checking before acting closes it. Closing it
needs a different reclaim protocol, and the obvious candidate is already
disproved below.

**Observable signature:** a holder reports `StateLockLost` having done nothing
wrong, because a reclaimer displaced it in the check-to-rename gap.

## Disproved: atomic takeover

Staging a replacement lockfile and renaming it *over* the stale one does keep the
lock path occupied, which is the right instinct — it removes the free window
entirely. It is nevertheless wrong here, measured rather than reasoned:

`rename` replaces unconditionally. Every contender holding the same stale
snapshot passes the identity check and renames in turn, so each believes it
holds the lock. Measured at **three to five simultaneous holders** — worse than
the defect being repaired. `O_CREAT|O_EXCL` is the primitive that admits exactly
one contender, and a takeover design removes it.

Any future attempt must keep a single-admission primitive. Do not re-derive this.

## Reproduction

The residual reproduces on both the repaired and unrepaired module, which is
what distinguishes it from the defect that was fixed. It cannot be reached by
waiting for a schedule; it has to be forced, because a test that passes because
the interleaving did not occur is indistinguishable from one that passes because
the lock works.

Drive `_reclaim` with a snapshot that matches the lock, then let a holder acquire
inside the gap between its identity check and its rename, using `Path.rename` as
the seam. Sample whether the lock path is free at the module's own `os.link`
restore call: an after-the-fact assertion sees nothing, because a reclaimer that
moves a live lock puts it straight back at the same inode.

```python
# B pre-validates against the stale lock; the check PASSES.
b_observed = os.lstat(lock)
b_record = m._read_record(lock)

def rename_seam(self, dst, *a, **k):        # fires after B's check, before its move
    os.unlink(lock)                          # A wins the gap:
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.write(fd, b"statelock1 " + b"b" * 32 + b" 1\n"); os.close(fd)
    return real_rename(self, dst, *a, **k)   # B now moves A's LIVE lock

def link_seam(src, dst, *a, **k):            # inside the free window
    if not os.path.exists(dst):              # a third contender would win here
        ...
    return real_link(src, dst, *a, **k)
```

With both seams installed, `_reclaim` moves a live holder's lock and the path is
observably free while that holder is inside — on the repaired module as well.

## Guard that does hold

`test_reclaim_leaves_a_superseded_snapshot_alone` in
`packs/core/tests/skills/work-loop/test_statelock.py` covers the repaired case
and fails against the unrepaired module. It is the criterion to keep green;
it does not cover this residual, and is not claimed to.

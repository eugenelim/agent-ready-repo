# Verification ledger — the intent rename transaction

Measurements this slice's design rests on. The first entry is inherited from
`docs/specs/intent-renumber-and-reissue/`, where the transaction was
originally specified and where the spike was run.

## 2026-09-28 — the transaction's failure modes, measured instead of reasoned

Five generations of this transaction were specified in prose, and each review
round found a defect in the newest one. The sixth was written from measurement.
A throwaway spike drove real `SIGKILL`s at controlled points against fixture
trees and recorded what survived. Nothing from the spike ships; what ships is
the design it corrected.

| # | Question | Result |
| --- | --- | --- |
| A | Does `SIGKILL` strand `.workspace-repair.lock`? | **Yes.** File survives; recorded owner PID verifiably dead; next writer gets `FileExistsError`; the module exposes only `WORKSPACE_LOCK_FILE` and `_acquire_workspace_lock` |
| B | Does `os.replace` consume its source? | **Yes.** Source gone, target holds source bytes |
| C | Same-directory vs cross-device replace | Same-directory succeeds; cross-device raises `EXDEV` (errno 18) |
| D | Does path-based `mkdir` follow a swapped parent symlink? | **Yes — it escaped the root.** An `O_NOFOLLOW` descriptor walk refused it |
| E | What does `SIGKILL` mid-copy leave? | A surviving 120-byte orphan holding a partial tombstone preamble |
| F | Does `dir_fd` + `O_NOFOLLOW` + `S_ISREG` sweep safely? | **Yes.** Symlinked candidate refused, its target survived, real orphan unlinked |

**A is the one that changed the design.** An earlier repair had this operation
acquire the shared workspace lock before allocation and hold it to disposal, to
serialise against `intake-intent` admission. The measurement shows what that
costs: one kill inside the operation leaves a lock no code can clear, and every
workspace writer — repair-apply, migration apply and rollback, guarded refresh,
prune, admission — blocks until a human deletes the file. The fix traded a
silent two-writer race for a repository-wide outage, so it was withdrawn. The
lock is now held only around the registry read-modify-write, which is the
smallest window that still makes that edit atomic against other registry
writers.

The successor-filename race that the long hold was meant to close is instead
closed where it occurs. Commit creates the successor with exclusive-create; on
`FileExistsError` it compares the existing bytes against the staged successor.
Identical means this transaction's own earlier pass already applied it, so the
step is a no-op and forward recovery stays idempotent — the property that
refuted a plain exclusive-create guard. Different bytes mean another writer
minted that filename, which is `commit-interrupted` naming the path, never a
silent overwrite.

**A also records a gap that is not this slice's.** The lock file carries the
owner PID and that PID is checkably dead after a kill, so stale-lock recovery is
implementable — but no writer in the repository performs it, and the helper
exposes no release or break verb. That predates this work and affects every
workspace writer equally. It is named under `## Follow-ons` rather than repaired
here, because widening a shared helper is not this contract's outcome.

**D and E** confirm two security findings that were previously argued rather
than shown: a staging root created by path is reachable outside the repository
if its parent is swapped between validation and use, and a kill mid-copy really
does leave a partial tombstone preamble of the kind the corpus lint rejects.
**F** validates the bounded sweep as specified.

What this does not bound: the same-device-different-mount `EXDEV` case, which
needs a bind mount the spike could not create without elevation. It is moot for
this design, because after the 2026-09-28 decision Commit never renames across
directories. Nor does it bound Windows behaviour, where the reparse-point
semantics of D and F differ and were not exercised.

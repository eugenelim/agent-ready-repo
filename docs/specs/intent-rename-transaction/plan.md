# Plan: The intent rename transaction

- **Status:** Drafting
- **Spec:** [`spec.md`](spec.md)

## Approach

Not yet designed, deliberately. This slice exists because its predecessor
specified a transaction five times in prose and every review round sustained a
defect in the newest version. The next design is written from measurement, not
from argument, and the bounded spike that produces those measurements is task
T0 rather than an afterthought — `new-spec`'s claim-routing table names a
bounded spike as the instrument for a load-bearing mechanism claim that cannot
be settled by reading, and skipping it is what produced the history below.

What is already measured is inherited at `notes/verification-ledger.md` and is
not to be re-derived. What is not yet settled is listed under
`## Inherited open findings`, each with the evidence that produced it.

## Constraints

- **`docs/specs/intent-renumber-and-reissue/spec.md`** owns the request
  contract, the tombstone field contract, the citation relation and the
  allocator property. This slice composes them. Cite that spec by path and its
  obligations by name; a bare `AC-####` resolves against local criteria only
  (`lint-contract-item-alignment.py:638-643`), so a cross-spec number silently
  misresolves and reports clean.
- **The shared workspace lock must not be held across the transaction.**
  Measured 2026-09-28: a `SIGKILL` while holding `.workspace-repair.lock`
  leaves the file, the recorded owner PID is dead, the next writer gets
  `FileExistsError`, and `intake_transaction.py` exposes no release or break
  verb — so every workspace writer blocks until a human clears it.
- **Reuse before building.** `resolve_confined_target`
  (`work-intake/scripts/intake_transaction.py:144-165`) is the confined path
  resolver; `open_validated_parent` (`close-work/scripts/cooling.py:595`)
  yields the validated no-follow descriptor; `file_safety.py` supplies confined
  reads and the `max_files` / `max_entries` / `max_bytes` budgets;
  `cooling.py:615-645` is the durable-write precedent. The predecessor's plan
  proposed hand-rolling the first of these before a reviewer found it.
- `work-intake` declares `Read Write Edit Bash`. No tool surface widens.

## Inherited open findings

Six Blockers stood unresolved against the predecessor's transaction when it was
cut out on 2026-09-28. They are inputs to this slice's design, not defects in
it. Each was sustained by a spec-stage security pass; the first four were
adjudicated, and the full reports are retained under
`.context/reviews/63804b99-bb0f-4f30-8405-0345af393fa0/`.

They fall into two groups, and the grouping is the most useful thing the
predecessor learned.

**Group 1 — the lock and the registry.** Narrowing the shared lock to the
registry read-modify-write left the lock artifact outside the partial-state
record, so a kill inside that critical section strands recovery itself. The
registry was described as both staged-and-replaced and locked-live-edited, two
mechanisms in one document. And an identity-aware exclusive-create on the
successor cannot, by byte comparison alone, distinguish this transaction's
earlier pass from a concurrent admission that produced identical bytes.

**Group 2 — the recovery record.** A record written before a kill is read after
it by a process that must decide whether to replay a write-set over live paths.
It currently has no bounded confined parse, no closed schema, no completion
seal written last, no independent re-derivation of the allowed write set, and
no postimage validation before the first destructive act. The no-follow
descriptor that protects creation cannot survive the kill that makes recovery
necessary, so recovery must reacquire it.

Group 2 is the harder half and the reason this is a slice rather than a repair:
every item in it follows from one property — a durable recovery record must be
trusted by a process that did not write it — rather than from any wording.

## Tasks

### T0 — Measure the transaction's failure modes before designing it

**Tests:** Goal-based. A throwaway harness under `tmp_path` drives real kills at
each candidate write point and records what survives: the lock artifact, the
staging root and its record, per-target temporaries, and each target. The
deliverable is the ledger entry, not code. Extends the inherited measurements
rather than repeating them.

**Approach:** The predecessor's spike is the starting shape and is recorded in
`notes/verification-ledger.md`. What it did not reach: kill-inside-the-registry
critical section, kill between record write and stage completion, recovery run
against a record altered after the kill, and the same-device-different-mount
`EXDEV` case if an environment can produce one.

**Depends on:** none

### T1 — The transaction applies in full or reaches exactly one recoverable state

**Tests:** Driven by T0's measurements. A real kill at each measured point, then
each recovery direction, asserting the tree equals either the complete rename
or the byte-identical pre-rename tree, and that no lock, staging root,
temporary or partial target is left behind. A successful rename is compared
byte for byte: the successor equals the source with the vacated path
substituted and differs nowhere else, which is the self-citing source case, and
every intent the rename did not touch keeps its prior `Slug:` bytes. Covers
AC-0003, AC-0026, AC-0002 and AC-0024.

**Depends on:** T0

### T2 — Recovery treats its record as untrusted input

**Tests:** A truncated record, an unknown field, a record whose write set
disagrees with what the request re-derives, a record altered after the kill,
and a staging root whose parent was swapped for a symlink between the kill and
the recovery — each refuses before the first destructive act, naming what
failed. Covers AC-0026's recovery arm.

**Depends on:** T0

### T3 — The citing set is exactly the files containing the vacated path

**Tests:** Over a fixture corpus, the computed set equals the set found by an
independent string search, in both directions. Cases: a Markdown inline link, a
bare path in a `Discovery:` header, a `path =` value in TOML, the same path
inside a fenced code block, the named exclusions, an untracked created file,
and an `.apm/` source with its adapter-root projection. Covers AC-0001 and
AC-0018.

**Approach:** Derive the parent set from `git ls-files -z` with an explicit
`--` terminator; the relation and its exclusions are the sibling spec's, not
this one's to restate.

**Depends on:** none

### T4 — The new ordinal is the allocator's next for the target token

**Tests:** A fixture where the vacated ordinal is free under the target token,
asserting the operation still takes the allocator's next value. Covers AC-0012.

**Depends on:** T1

### T5 — Resolution stops at a tombstone, and inbound tombstones re-point

**Tests:** A pointer resolving onto a tombstone yields a diagnostic naming the
tombstone and its `Reissued as:` target, never the successor's content. A
corpus where two tombstones already point at the source. A `Reissued as:`
naming an absent path, and one naming a file that itself carries `Tombstone:`.
Covers AC-0007, AC-0008, AC-0009.

**Depends on:** T1

### T6 — The transaction and recovery model is recorded as a decision

**Tests:** Goal-based. The ADR exists, is `Accepted`, states the phase model,
what recovery may trust, and the rejected alternatives — including the five
mechanisms the predecessor tried and why each failed, since that is the
evidence the decision rests on. `spec.md` cites it in `Constrained by:`.

**Depends on:** T1, T2

### T7 — An operator can run a rename, and recover one, from an installed core pack

**Tests:** An end-to-end rename driven through the surface an installed
`packs/core` exposes, not through the module, plus one driven recovery. Covers
AC-0013 and AC-0025. Manual: an operator follows the how-to through one real
rename and one real recovery.

**Approach:** The two `SKILL.md` statements that nothing renames an intent point
here instead, and the changelog entry lands with them. `packs/AGENTS.md`
requires the matching `pack.toml` and `.claude-plugin/plugin.json` version bumps
and an eval-harness update; they land in this task.

**Depends on:** T1, T2, T3, T4, T5, T6

## Changelog

- 2026-09-28 — cut from `intent-renumber-and-reissue` and drafted. Carries that
  slice's twelve transaction criteria unchanged, its measured failure modes,
  and its six unresolved security Blockers as design inputs.

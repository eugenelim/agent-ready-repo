# Spec: Intent renumber, reissue, and the tombstone

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0108; ADR-0033; ADR-0098
- **Brief:** brief:intent-identity-and-registration
- **Discovery:** docs/product/intents/FEAT-0001-intent-identity-and-registration.md
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

A product engineer's intent can be validated for renaming, and the tombstone
that a rename leaves behind has one shape that every reader agrees on. This
slice contracts three things the rename operation composes but does not own:
what a well-formed rename request is and how each malformed one is refused;
what a tombstone carries and how a corpus is partitioned into live intents and
tombstones; and that the allocator never reissues an ordinal a tombstone still
holds. The operation that applies a rename is
[`intent-rename-transaction`](../intent-rename-transaction/spec.md).

## What Changes

- The rename request contract — two arguments, and one fixed refusal token per
  way a request can be malformed. Why a rename is wanted is not part of it: a
  duplicate ordinal and an altitude change produce the same operation, and a
  declared cause the contract does not constrain would change nothing an
  implementation must do
- A `Tombstone:` preamble field and the shape of the artifact carrying it —
  defined by this spec, and validated by the corpus-lint
  routing-and-validation criterion in
  `docs/specs/intent-metadata-shape-contract/spec.md`
- The partition rule that routes every file in `docs/product/intents/` to the
  live-intent contract or the tombstone contract
- The allocator counting tombstones alongside live intents, so a retired
  ordinal stays out of circulation for as long as its tombstone stands
- An Accepted ADR recording the tombstone convention, which applies ADR-0108
  D3's non-reuse rule to a second artifact class
- Where it ships — inside `packs/core`, beside the allocator it depends on
- A tombstone retires a *filename*; `Status: Superseded` and its
  `Superseded by:` field retire a *bet*. They cannot substitute for each other:
  a rename preserves `Slug:`, and `Superseded by:` takes a slug resolved
  against a live intent's `Slug:`, so expressing a rename that way would point
  an artifact at itself

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — the tombstone convention constrains every later intent, and ADR-0108 D3's non-reuse rule is the thing it implements for a second artifact class | `docs/adr/` | eugenelim | An Accepted ADR stating the tombstone convention and its two rejected alternatives | The ADR exists and this spec cites it in `Constrained by:` |
| Interface compatibility | Applicable — `Tombstone:` is a new durable field in an adopter-visible artifact | `guides/product-engineering/reference/intent-fields-and-modes.md` | eugenelim | The field and its three-field contract documented alongside the existing intent fields | The reference page describes the field an adopter will see |
| Maintainer procedure | Applicable — the operation is operator-invoked and its refusals need a recovery story | `guides/product-engineering/how-to/` | eugenelim | A how-to covering both causes and what to do after a refusal | The page walks one real rename end to end |
| Current product truth | Applicable — `intake-intent` and `work-intake` both state that nothing renames an intent | the two `SKILL.md` bodies | eugenelim | Those statements point at this operation instead of asserting the capability wall | No skill still claims an intent can never be renamed |
| Release history | Applicable — the operation ships inside `packs/core` | `packs/core/CHANGELOG.md` | eugenelim | One entry for the shipped operation | Entry present under the released version |
| Reusable learning | Applicable — the sweep's reach was measured rather than assumed | `docs/specs/intent-renumber-and-reissue/notes/verification-ledger.md` | eugenelim | The measured citation counts and what they bound | The ledger records the measurement the criteria rest on |
| Current architecture | Not applicable — the operation adds no module boundary and no layer | — | — | — | — |

## Agent Rules

### Always do

- Resolve the rename target against the repository root and prove containment
  before any write.
- Edit `workspace.toml` inside the same transaction as the rename, never after it.
- Leave a tombstone at every filename the operation vacates.
- Take the new ordinal from the allocator for the target type. Never carry an
  ordinal across a rename and never choose one by hand.
- Refuse to a human. The operation is operator-invoked only: no workflow calls
  it unattended, so every refusal has a reader.

### Ask first

- Moving more than one intent in a single run.
- Touching any file in `docs/product/intents/` other than the intent named in
  the request and the tombstones pointing at it.
- Widening any skill's declared tool surface to make the operation runnable.

### Never do

- Reuse an ordinal whose tombstone stands. Deleting a tombstone by hand is
  out-of-contract corpus corruption of the same kind as deleting a live intent,
  and nothing here detects either; `## Assumptions` carries the residual.
- Delete an intent file. A retirement is a tombstone, not a deletion.
- Add a new top-level directory, a new module boundary, or a new dependency.
  The operation ships inside an existing owner.
- Repair a stale citation by editing a generated projection.

## Testing Strategy

- **The request contract (AC-0021): TDD.** One refusing fixture per part — an
  absent source, a source outside `docs/product/intents/`, a source that is not
  a regular file, a source that is a tombstone rather than a live intent, a
  token outside `NAMESPACE_TOKENS`, an unparseable registry, and a registry
  matching the source twice — so a positive path cannot be satisfied by
  refusing everything. One positive case asserts a fully valid request passes.
- **The pre-run refusal (AC-0020): TDD.** A fixture with an uncommitted change
  on a path the operation would touch must refuse before writing anything.
- **The tombstone's three-field shape (AC-0005, AC-0006): TDD.** A parse with
  conforming and non-conforming fixtures. The partition walk over a whole
  corpus belongs to `intent-metadata-shape-contract`'s lint; what this slice
  proves is that every tombstone it writes carries `Tombstone:` and nothing it
  writes elsewhere does, which is AC-0006's biconditional on both arms.
- **Field value shapes (AC-0015, AC-0016, AC-0017): TDD.** One rejecting
  fixture per rule — a non-ISO date, an absolute `Reissued as:`, one resolving
  outside `docs/product/intents/`, an empty `Retired:` — and a sample taken
  either side of midnight to fix the date to one value.
- **Tombstone name safety (AC-0004): inherited, re-run not re-authored.**
  Already pinned before this spec by
  `test_tombstone_filename_shapes_pin_allocation_and_check` in
  `packs/core/tests/skills/work-intake/test_intent_ordinal.py`, committed
  87768ba4d. This slice re-runs it and adds nothing; it is cited here so the
  contract records where that coverage lives rather than promising it again.
- **The convention is recorded (AC-0027): goal-based check.** The ADR exists,
  is `Accepted`, and this spec cites it in `Constrained by:`. Checked by
  reading the files, because neither is executable.

## Acceptance Criteria

- [ ] **AC-0021.** A rename request carries exactly two things: the
      repository-relative path of an existing live intent inside
      `docs/product/intents/`, and the target token from the allocator's
      `NAMESPACE_TOKENS`. A request missing or failing either is refused,
      naming the part at fault. Why a rename is wanted is not part of the
      request: a duplicate ordinal and an altitude change produce the same
      operation, and a declared cause the contract does not constrain would
      change nothing an implementation must do.
- [ ] **AC-0020.** The operation refuses before its first write when any path
      it would touch carries an uncommitted change, so the recovery that the
      transaction slice
      (`docs/specs/intent-rename-transaction/spec.md`) relies on cannot
      discard unrelated work.
- [ ] **AC-0004.** For every token the allocator recognizes — its
      `NAMESPACE_TOKENS`, derived from the closed level-to-token table the
      parent intent owns — its next ordinal exceeds every ordinal that token
      carries in `docs/product/intents/`, counting tombstones alongside live
      intents.
- [ ] **AC-0005.** A tombstone carries exactly three fields: `Slug:`, unchanged from the
      retired artifact; `Tombstone:`, the retirement date; and exactly one of
      `Reissued as:` or `Retired:`.
- [ ] **AC-0006.** A file in `docs/product/intents/` is a tombstone if and only
      if its preamble carries a `Tombstone:` field. This is the partition rule;
      that every file in the directory is routed by it and validated against one
      of the two contracts is `intent-metadata-shape-contract`'s corpus-lint routing criterion, whose
      gate owns the check.
- [ ] **AC-0015.** `Tombstone:` carries one ISO 8601 date: the UTC calendar
      date at the rename's start. An operation spanning midnight therefore
      writes that date and not the one it finished on.
- [ ] **AC-0016.** `Reissued as:` carries a repository-relative path under
      `docs/product/intents/`; an absolute path, or one resolving outside that
      directory, is refused.
- [ ] **AC-0017.** `Retired:` carries a single non-empty line.
- [ ] **AC-0027.** An Accepted ADR records the tombstone convention, and this
      spec cites it in `Constrained by:`. Without it, applying ADR-0108 D3's
      non-reuse rule to intent filenames rests on no decision; this is a
      governing constraint the contract needs, not a document the delivery
      produces.

## Retired identifiers

These twelve were authored here and moved to
[`docs/specs/intent-rename-transaction/spec.md`](../intent-rename-transaction/spec.md)
on 2026-09-28. They keep their numbers there so the review history behind
their wording stays legible, and they are recorded here so the numbers are
never reissued — ADR-0108 D3's non-reuse rule reaches an identifier that
moved as much as one that was retired.

- `AC-0001`
  - moved to `docs/specs/intent-rename-transaction/spec.md` on
    2026-09-28 when the transaction became its own slice; the citation sweep's completeness after a rename.
- `AC-0002`
  - moved to `docs/specs/intent-rename-transaction/spec.md` on
    2026-09-28 when the transaction became its own slice; `Slug:` conservation across a rename.
- `AC-0003`
  - moved to `docs/specs/intent-rename-transaction/spec.md` on
    2026-09-28 when the transaction became its own slice; the pre-apply failure leaves the tree and index unchanged.
- `AC-0007`
  - moved to `docs/specs/intent-rename-transaction/spec.md` on
    2026-09-28 when the transaction became its own slice; a `Reissued as:` naming a path that does not exist.
- `AC-0008`
  - moved to `docs/specs/intent-rename-transaction/spec.md` on
    2026-09-28 when the transaction became its own slice; a `Reissued as:` naming a file that is itself a tombstone.
- `AC-0009`
  - moved to `docs/specs/intent-rename-transaction/spec.md` on
    2026-09-28 when the transaction became its own slice; resolution stops at a tombstone rather than following it.
- `AC-0012`
  - moved to `docs/specs/intent-rename-transaction/spec.md` on
    2026-09-28 when the transaction became its own slice; the new ordinal is the allocator's next for the target token.
- `AC-0013`
  - moved to `docs/specs/intent-rename-transaction/spec.md` on
    2026-09-28 when the transaction became its own slice; the success path and its exclusions.
- `AC-0018`
  - moved to `docs/specs/intent-rename-transaction/spec.md` on
    2026-09-28 when the transaction became its own slice; citation conservation over the searched set.
- `AC-0024`
  - moved to `docs/specs/intent-rename-transaction/spec.md` on
    2026-09-28 when the transaction became its own slice; the successor's bytes equal the source's after substitution.
- `AC-0025`
  - moved to `docs/specs/intent-rename-transaction/spec.md` on
    2026-09-28 when the transaction became its own slice; a rename completes through the installed operator surface.
- `AC-0026`
  - moved to `docs/specs/intent-rename-transaction/spec.md` on
    2026-09-28 when the transaction became its own slice; an interruption mid-apply reaches one of two observable states.
- `AC-0010`
  - superseded by `AC-0018`, which already reaches an inbound tombstone.
- `AC-0011`
  - first-time allocation; a separate outcome, under `## Follow-ons`.
- `AC-0014`
  - split into `AC-0015`, `AC-0016` and `AC-0017`.
- `AC-0019`
  - standalone retirement's operation; a separate outcome, under
    `## Follow-ons`.
- `AC-0023`
  - unsatisfiable as a criterion; `AC-0003` and `AC-0026` carry the
    observables.

## Follow-ons

- eugenelim: `packs/core/.apm/skills/work-intake/scripts/intake_transaction.py`
  — `.workspace-repair.lock` has no stale-owner recovery. Measured on
  2026-09-28 and recorded in `notes/verification-ledger.md`: a `SIGKILL` while
  the lock is held leaves the file in place, the next writer gets
  `FileExistsError`, and the module exposes no release or break verb — so every
  workspace writer blocks until a human deletes it. The lock file already
  records the owner PID and that PID is checkably dead, so recovery is
  implementable. This predates this slice and affects repair-apply, migration
  apply and rollback, guarded refresh, prune and admission equally; this
  operation narrowed its own hold to one read-modify-write rather than widen a
  shared helper, which is not this contract's outcome.

- `intent-metadata-shape-contract` owns routing every file in
  `docs/product/intents/` and the gate that fails on its lint; this spec owns
  the partition rule at `AC-0006` and the tombstone field contract at
  `AC-0005`. No `needs` edge either way: that spec's plan implements text this
  spec already carries, while this spec's tombstones are what its lint
  validates, so one edge would assert a false block and two would cycle.
- eugenelim: `docs/specs/intent-metadata-shape-contract/spec.md` — nothing in
  the pack checks the ordinal after allocation. Allocation is a prose-invoked
  step at `work-intake/SKILL.md:357`, and `--check` ships with no caller, so a
  hand-made rename that reuses an ordinal leaves no trace. That spec's gate criterion
  introduces a gate over `docs/product/intents/`, which is a place such a check
  could run; deciding whether it belongs there is that spec's, and how an
  adopter runs it is theirs.
- eugenelim: `docs/product/briefs/intent-identity-and-registration.md` —
  retiring an intent with no successor. Its tombstone shape is contracted here,
  at `AC-0005` and `AC-0017`, so a retirement written by any means is
  validated; the operation that writes one is a separate outcome and left as
  retired `AC-0019`. The brief's Spec map is where its slice would be cut.
- eugenelim: `docs/product/briefs/intent-identity-and-registration.md` — an
  intent authored after cutover through a route that allocates no ordinal still
  acquires none. That outcome is releasable and verifiable on its own, so it
  left this contract as retired `AC-0011`; the brief's Spec map is where its
  own slice would be cut.
- eugenelim: this repository's own corpus control,
  `test_every_live_typed_file_satisfies_the_owner_shape` at
  `tests/roster/test_typed_ordinal_collision_equivalence.py:63`, sits in the
  dispatch-only roster suite. Where it runs here is a repository-local gate
  question, separate from what the pack ships.

## Assumptions

- Process: applying ADR-0108 D3's non-reuse rule to intent filenames, with one
  tombstone file per retired name standing in for that ADR's per-directory
  retired list, is an extension of a decision scoped to loop-contract items. No
  accepted record authorises it yet. The ADR that would is `plan.md`'s T7, and
  T8 — the task that ships the operator surface — depends on it, so the
  convention is ratified before anything reaches an adopter. What is open is
  whether the ADR ratifies `AC-0005` and `AC-0006` as written; if it does not,
  both need amendment and the sibling lint that reads them needs telling
  (settled by: eugenelim, when the ADR is drafted)
- Technical: a tombstone deleted by hand frees its ordinal, and no criterion
  here can see that. AC-0004 holds over the directory as it stands, and the
  tombstone file is the whole reservation record — deliberately, because
  ADR-0108's Context rejects a repository-global retired list as
  uncoordinatable across worktrees, and this spec's `## Objective` inherits
  that. So the guarantee is "no ordinal is reused while its tombstone stands",
  and hand-deleting one is corpus corruption of the same kind as deleting a
  live intent, which nothing here detects either. `Agent Rules` forbids the
  reuse; that is a rule an agent follows, not a control that fails.

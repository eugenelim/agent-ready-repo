# Spec: Intent renumber, reissue, and the tombstone

- **Status:** Draft
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

A product engineer whose intent must change filename — because two branches
minted the same ordinal, or because its altitude changed and the type token
moves — retires the old name and issues a new one in a single operation. The
new ordinal always comes from the allocator for the target type, every citation
moves with it, the registry moves in lockstep, and the vacated name keeps its
ordinal out of circulation for as long as its tombstone stands.

## What Changes

- Retiring one intent filename and issuing another — one confined transactional
  operation, where today no surface may rename an intent at all
- Two causes, one mechanism. A duplicate ordinal, which `max + 1` cannot
  prevent because ADR-0108's Context records that it "cannot see an unpushed
  sibling"; and an altitude change, which the shaping loop already assumes —
  `frame-intent` asserts `Level`, admission mints the ordinal from it, and
  `decompose-intent` is where the altitude is actually tested
- The new ordinal comes from the allocator for the target type, always. An
  ordinal is never carried across a rename, so this is a retire-and-issue
  operation rather than a renumber in place, and ADR-0108 D2's bar on
  renumbering on insertion or reorder is never reached
- A tombstone left at every filename an intent vacates —
  `docs/product/intents/`. This slice writes the reissue shape; the retirement
  shape is contracted here and written by a follow-on
- The citation sweep — `docs/product/**`, `docs/specs/**`, and `workspace.toml`,
  the three trees that cite an intent by path
- A `Tombstone:` preamble field and the shape of the artifact carrying it —
  defined by this spec, and validated by
  `intent-metadata-shape-contract`'s lint under its AC-0017
- An operator how-to — `guides/product-engineering/how-to/`
- Where it ships — inside `packs/core`, so an adopter installing core has it,
  beside the allocator it depends on
- A tombstone retires a *filename*; `Status: Superseded` and its `Superseded by:`
  field retire a *bet*. They cannot substitute for each other: a renumber
  preserves `Slug:` by AC-0002, and `Superseded by:` takes a slug resolved
  against a live intent's `Slug:`, so expressing a renumber that way would point
  an artifact at itself. The open question of whether that pointer lives on
  `Status:` is **settled**: `intent-preamble-lifecycle-records` split it into a
  bare `Status: Superseded` token and a separate `Superseded by:` field, and
  `docs/product/briefs/intent-identity-and-registration.md` § Post-Ready
  decisions records why

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

- **The sweep's completeness (AC-0001): TDD.** After a rename the vacated path occurs in
  no tracked file but the two named exclusions, which is one predicate a test
  holds. The fixture is the repository's own tracked set restricted to the
  AC-0001's whole parent set — every pre-run tracked file plus every file the
  operation creates — with no prefilter for files that already contain the
  path, so a created file that keeps it and an unrelated file the operation
  wrongly writes it into are both in scope. The three trees citing an intent today,
  and the 3-to-15-file range one rename touches, are ledger measurements and
  not the acceptance boundary.
- **The repository-level check: goal-based.** One search for the vacated path
  over git's tracked set after a real rename, which is the only surface that
  covers AC-0001's full scope. The `workspace.toml` reconciliation below
  reports `missing_artifact` and sees no stale Markdown target, so neither
  check substitutes for the other.
- **Transactionality (AC-0003, AC-0026): TDD.** A failure injected at each write point leaves the
  tree and index as they were, or the rename applies in full — a property a
  test asserts and a reviewer cannot. Which failure classes recover
  automatically is `plan.md`'s to design and its tests to drive.
- **Fresh allocation (AC-0012): TDD.** A fixture where the vacated ordinal is free under
  the target token is the case a carried-across ordinal would pass; the
  assertion is that the operation still takes the allocator's next value.
- **The success path (AC-0013): TDD.** Both causes run to completion against a fixture
  corpus and the tombstone left behind is read back for its `Reissued as:`
  value. Asserting only the refusals would let a rename that wrote no successor
  pointer pass every other criterion.
- **Field value shapes (AC-0015, AC-0016, AC-0017): TDD.** One rejecting fixture per rule — a non-ISO
  date, an absolute `Reissued as:`, one resolving outside
  `docs/product/intents/`, an empty `Retired:` line — and a transaction opened
  either side of midnight to fix the date to one sample.
- **Citation conservation (AC-0018): TDD.** The fixture's citing files are compared byte
  for byte before and after, so a citation removed rather than repointed fails
  even though the vacated path is gone.
- **The pre-run refusal (AC-0020): TDD.** A fixture with an uncommitted change on a path
  the operation would touch must refuse before writing anything.
- **The request contract (AC-0021): TDD.** One refusing fixture per part — an absent
  source, a source outside `docs/product/intents/`, a token outside
  `NAMESPACE_TOKENS`, an unrecognized cause — so a positive path cannot be
  satisfied by refusing everything.
- **The operator surface (AC-0025, AC-0027): goal-based check.** A rename driven through the
  surface an installed `packs/core` exposes, not through an internal entry
  point, because every other check here passes against a helper an adopter
  cannot reach.
- **Content carried across (AC-0002, AC-0024): TDD.** The successor is compared byte for byte
  against the retired source, so a shape-valid but skeletal successor fails.
- **The tombstone's three-field shape (AC-0005, AC-0006): TDD.** A parse with conforming and
  non-conforming fixtures. The partition walk over a whole corpus belongs to
  `intent-metadata-shape-contract`'s lint; what this slice proves is that every
  tombstone it writes carries `Tombstone:` and nothing it writes elsewhere
  does, which is AC-0006's biconditional on both arms.
- **Tombstone name safety (AC-0004): inherited, re-run not re-authored.** Already pinned
  before this spec by `test_tombstone_filename_shapes_pin_allocation_and_check`
  in `packs/core/tests/skills/work-intake/test_intent_ordinal.py`, committed
  87768ba4d. This slice re-runs it and adds nothing; it is cited here so the
  contract records where that coverage lives rather than promising it again.
- **The corpus stays clean after a real rename: goal-based check.** One run
  of the workspace reconciliation over the real `workspace.toml` reports no
  `missing_artifact`, which is the existing fail-closed control at
  `tests/roster/test_workspace_status_projection.py:948`.
- **Tombstone target validity and resolution (AC-0007, AC-0008, AC-0009): TDD.** An absent target, a target that is itself a
  tombstone, a pointer resolving onto a tombstone, and a corpus whose
  tombstones already point at the source.
- **The operator how-to: manual QA.** A person follows the page through one
  rename; a test cannot tell whether the page is followable.

## Acceptance Criteria

- [ ] **AC-0001.** After a rename, the vacated path occurs in no tracked file
      except the tombstone standing at it and this spec's own
      `notes/verification-ledger.md`. The searched set is the pre-run tracked
      set plus every file the operation creates, whatever its index state, so
      an unstaged successor cannot escape the search. The relation is string
      occurrence, not a list of citation forms: enumerating forms is what
      leaves a stale citation passing, and a bare path in a `Discovery:` or
      `Brief:` header is already a form no link-target rule reaches.
- [ ] **AC-0002.** After a rename the successor's `Slug:` bytes equal the
      retired source's, the tombstone carries those same bytes, and every
      unaffected intent keeps its prior `Slug:` bytes. The corpus gains an
      occurrence of that value rather than preserving a collection, so the
      mapping is stated directly.
- [ ] **AC-0003.** A failure before the rename begins applying leaves the
      working tree and the index as they were before it ran.
- [ ] **AC-0026.** An interruption while the rename is applying leaves the
      repository in one of two observable states — every change applied, or a
      partial state naming every path the rename intended to write, from which
      re-running the operation or restoring those paths ends in the complete
      rename or the pre-rename state and in no third state. Which failures
      recover automatically, and how, is design.
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
- [ ] **AC-0007.** Resolving a tombstone whose `Reissued as:` names a path
      that does not exist yields a diagnostic naming the tombstone and the
      missing path, on the operator surface AC-0025 names.
- [ ] **AC-0008.** Resolving a tombstone whose `Reissued as:` names a file that
      itself carries `Tombstone:` yields a diagnostic naming both paths, on
      that same operator surface.
- [ ] **AC-0009.** On the operator surface AC-0025 names, resolving a path
      that lands on a tombstone yields a
      diagnostic naming the tombstone and its `Reissued as:` target, and never
      the successor's content. Resolution stops at the tombstone rather than
      following it.
- [ ] **AC-0012.** The new filename's ordinal is the allocator's next ordinal
      for the target token over the corpus as it stood before the rename. The
      allocator's answer is the whole requirement: carrying an ordinal across
      fails it whenever carrying and allocating differ, and where they
      coincide there is nothing to distinguish.
- [ ] **AC-0027.** An Accepted ADR records the tombstone convention, and this
      spec cites it in `Constrained by:`. Without it, applying ADR-0108 D3's
      non-reuse rule to intent filenames rests on no decision; this is a
      governing constraint the contract needs, not a document the delivery
      produces.
- [ ] **AC-0025.** A rename completes through the surface an installed
      `packs/core` exposes to an operator, exercised as an operator invokes it
      rather than through an internal entry point.
- [ ] **AC-0021.** A rename request carries exactly two things: the
      repository-relative path of an existing live intent inside
      `docs/product/intents/`, and the target token from the allocator's
      `NAMESPACE_TOKENS`. A request missing or failing either is refused,
      naming the part at fault. Why a rename is wanted is not part of the
      request: a duplicate ordinal and an altitude change produce the same
      operation, and a declared cause the contract does not constrain would
      change nothing an implementation must do.
- [ ] **AC-0013.** A request satisfying AC-0021 whose source is registered in
      `workspace.toml` and whose affected paths are all clean succeeds,
      leaving a tombstone at the vacated path whose
      `Reissued as:` value is the new live artifact's repository-relative path.
      AC-0020 is the exclusion for a dirty path; an unregistered source is
      refused because the Outcome requires the registry to move in lockstep;
      and a corpus the allocator cannot answer for, or a target filename
      already occupied, are each excluded and refused rather than forced to
      succeed.
- [ ] **AC-0015.** `Tombstone:` carries one ISO 8601 date: the UTC calendar
      date at the rename's start. An operation spanning midnight therefore
      writes that date and not the one it finished on.
- [ ] **AC-0016.** `Reissued as:` carries a repository-relative path under
      `docs/product/intents/`; an absolute path, or one resolving outside that
      directory, is refused.
- [ ] **AC-0017.** `Retired:` carries a single non-empty line.
- [ ] **AC-0018.** Over AC-0001's searched set, every file that cited the
      vacated path before a rename cites the new path after it, and no other content in that file changes.
      A citation is repointed, never removed. The renamed artifact itself is
      outside this criterion, because it becomes a tombstone; AC-0024 governs
      it.
- [ ] **AC-0024.** The successor's bytes equal the retired source's bytes
      after substituting the new path for the vacated one, and differ nowhere
      else. A source that cites its own path is the case that distinguishes
      this from plain equality: the substitution is what lets AC-0001 and this
      criterion both hold.
- [ ] **AC-0020.** The operation refuses before its first write when any path
      it would touch carries an uncommitted change, so the `git restore`
      recovery AC-0003 relies on cannot discard unrelated work.

## Retired identifiers

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

## Follow-ons` with its owner.
- `AC-0010`
  - re-pointing an inbound tombstone. An inbound tombstone is a file citing the
    vacated path, so `AC-0018` already requires it to cite the new path with
    nothing else changed, and `AC-0003` already places that change in the
    rename. The criterion added no state that could fail on its own.
- `AC-0023`
  - the mid-write journal and its exact recovery set. Unsatisfiable
  as a criterion, because recording a path before or after mutating it leaves a
  different gap under termination, and no criterion can name the atomic
  mechanism that would close both. The transaction design is `plan.md`'s;
  `AC-0003` keeps the observable.
- `AC-0019`
  - standalone retirement's success path. Sustained in all three
  shaping rounds as an independently shippable outcome with its own input,
  semantics and refusals; sharing the transaction is not sharing the outcome.
  The `Retired:` field shape stays in the tombstone contract at `AC-0005` and
  `AC-0017`, because the sibling lint validates both tombstone shapes whoever
  writes them. What left is the operation.
- `AC-0014`
  - the three tombstone field value shapes as one criterion. Split
  into `AC-0015`, `AC-0016` and `AC-0017`: date parsing, path confinement and
  free-text non-emptiness are different failures with different remedies.

## Follow-ons

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

# Spec: Intent renumber, reissue, and the tombstone

- **Status:** Draft
- **Owner:** eugenelim
- **Constrained by:** ADR-0108; ADR-0033; ADR-0098
- **Brief:** docs/product/briefs/intent-identity-and-registration.md
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
- A tombstone retires a *filename*; `Status: Superseded by <slug>` retires a
  *bet*. They cannot substitute for each other: a renumber preserves `Slug:`
  by AC-0002, and `Superseded by` takes a slug that
  `intent-metadata-shape-contract` AC-0021 resolves against a live intent's
  `Slug:`, so expressing a renumber that way would point an artifact at itself.
  Whether `Superseded by` stays on `Status:` is that spec's open question and
  `FEAT-0005-lifecycle-and-closure`'s to settle

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

- **The sweep's completeness: TDD.** After a rename the vacated path occurs in
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
- **Transactionality: TDD.** A failure injected at each write point leaves the
  tree and index as they were, or the rename applies in full — a property a
  test asserts and a reviewer cannot. Which failure classes recover
  automatically is `plan.md`'s to design and its tests to drive.
- **Fresh allocation: TDD.** A fixture where the vacated ordinal is free under
  the target token is the case a carried-across ordinal would pass; the
  assertion is that the operation still takes the allocator's next value.
- **The success path: TDD.** Both causes run to completion against a fixture
  corpus and the tombstone left behind is read back for its `Reissued as:`
  value. Asserting only the refusals would let a rename that wrote no successor
  pointer pass every other criterion.
- **Field value shapes: TDD.** One rejecting fixture per rule — a non-ISO
  date, an absolute `Reissued as:`, one resolving outside
  `docs/product/intents/`, an empty `Retired:` line — and a transaction opened
  either side of midnight to fix the date to one sample.
- **Citation conservation: TDD.** The fixture's citing files are compared byte
  for byte before and after, so a citation removed rather than repointed fails
  even though the vacated path is gone.
- **The pre-run refusal: TDD.** A fixture with an uncommitted change on a path
  the operation would touch must refuse before writing anything.
- **The request contract: TDD.** One refusing fixture per part — an absent
  source, a source outside `docs/product/intents/`, a token outside
  `NAMESPACE_TOKENS`, an unrecognized cause — so a positive path cannot be
  satisfied by refusing everything.
- **The operator surface: goal-based check.** A rename driven through the
  surface an installed `packs/core` exposes, not through an internal entry
  point, because every other check here passes against a helper an adopter
  cannot reach.
- **Content carried across: TDD.** The successor is compared byte for byte
  against the retired source, so a shape-valid but skeletal successor fails.
- **The tombstone's three-field shape: TDD.** A parse with conforming and
  non-conforming fixtures. The partition walk over a whole corpus belongs to
  `intent-metadata-shape-contract`'s lint; what this slice proves is that every
  tombstone it writes carries `Tombstone:` and nothing it writes elsewhere
  does, which is AC-0006's biconditional on both arms.
- **Tombstone name safety: inherited, re-run not re-authored.** Already pinned
  before this spec by `test_tombstone_filename_shapes_pin_allocation_and_check`
  in `packs/core/tests/skills/work-intake/test_intent_ordinal.py`, committed
  87768ba4d. This slice re-runs it and adds nothing; it is cited here so the
  contract records where that coverage lives rather than promising it again.
- **The corpus stays clean after a real rename: goal-based check.** One run
  of the workspace reconciliation over the real `workspace.toml` reports no
  `missing_artifact`, which is the existing fail-closed control at
  `tests/roster/test_workspace_status_projection.py:948`.
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
- [ ] **AC-0003.** A rename either applies every change it makes or leaves the
      working tree and the index as they were before it ran. Which failures it
      recovers from automatically, and how, is design.
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
      of the two contracts is `intent-metadata-shape-contract` AC-0017, whose
      gate owns the check.
- [ ] **AC-0007.** A `Reissued as:` value naming a path that does not exist fails and names
      both the tombstone and the missing path.
- [ ] **AC-0008.** A `Reissued as:` value naming a file that itself carries `Tombstone:`
      fails and names both paths.
- [ ] **AC-0009.** Resolving a path that lands on a tombstone yields a
      diagnostic naming the tombstone and its `Reissued as:` target, and never
      the successor's content. Resolution stops at the tombstone rather than
      following it.
- [ ] **AC-0010.** A rename re-points every tombstone whose `Reissued as:` named the moved
      artifact, inside the same transaction.
- [ ] **AC-0012.** The new filename's ordinal is the allocator's next ordinal
      for the target token, measured once against the corpus as it stands
      before the operation's first write, and never the vacated ordinal reused
      under a different token.
- [ ] **AC-0025.** A rename completes through the surface an installed
      `packs/core` exposes to an operator, exercised as an operator invokes it
      rather than through an internal entry point.
- [ ] **AC-0021.** A rename request carries exactly three things: the
      repository-relative path of an existing live intent inside
      `docs/product/intents/`, the target token from the allocator's
      `NAMESPACE_TOKENS`, and the cause, one of `duplicate-ordinal` or
      `altitude-change`. A request missing or failing any of the three is
      refused, naming the part at fault.
- [ ] **AC-0013.** A request satisfying AC-0021 whose source is registered in
      `workspace.toml` and whose affected paths are all clean succeeds for
      either cause, leaving a tombstone at the vacated path whose
      `Reissued as:` value is the new live artifact's repository-relative path.
      AC-0020 is the exclusion for a dirty path; an unregistered source is
      refused because the Outcome requires the registry to move in lockstep.
- [ ] **AC-0015.** `Tombstone:` carries an ISO 8601 date, sampled once in UTC
      at the moment the operation opens its transaction, so an operation
      spanning midnight writes one date rather than two.
- [ ] **AC-0016.** `Reissued as:` carries a repository-relative path under
      `docs/product/intents/`; an absolute path, or one resolving outside that
      directory, is refused.
- [ ] **AC-0017.** `Retired:` carries a single non-empty line.
- [ ] **AC-0018.** Every file that cited the vacated path before a rename
      cites the new path after it, and no other content in that file changes.
      A citation is repointed, never removed. The renamed artifact itself is
      outside this criterion, because it becomes a tombstone; AC-0024 governs
      it.
- [ ] **AC-0024.** The successor's bytes equal the retired source's bytes
      except where another criterion requires a change. The operation carries
      the intent across rather than authoring a new one.
- [ ] **AC-0020.** The operation refuses before its first write when any path
      it would touch carries an uncommitted change, so the `git restore`
      recovery AC-0003 relies on cannot discard unrelated work.

## Retired identifiers

- `AC-0011` — first-time allocation for an intent authored through a
  non-allocating route. A separate outcome, releasable and verifiable on its
  own, recorded under `## Follow-ons` with its owner.
- `AC-0023` — the mid-write journal and its exact recovery set. Unsatisfiable
  as a criterion, because recording a path before or after mutating it leaves a
  different gap under termination, and no criterion can name the atomic
  mechanism that would close both. The transaction design is `plan.md`'s;
  `AC-0003` keeps the observable.
- `AC-0019` — standalone retirement's success path. Sustained in all three
  shaping rounds as an independently shippable outcome with its own input,
  semantics and refusals; sharing the transaction is not sharing the outcome.
  The `Retired:` field shape stays in the tombstone contract at `AC-0005` and
  `AC-0017`, because the sibling lint validates both tombstone shapes whoever
  writes them. What left is the operation.
- `AC-0014` — the three tombstone field value shapes as one criterion. Split
  into `AC-0015`, `AC-0016` and `AC-0017`: date parsing, path confinement and
  free-text non-emptiness are different failures with different remedies.

## Follow-ons

- Settled 2026-09-21 by eugenelim, on the ground that
  `docs/specs/intent-metadata-shape-contract/plan.md` already states it under
  `## Constraints` — "**ADR-0108 D3** and
  `docs/specs/intent-renumber-and-reissue/spec.md` own the partition rule and
  the tombstone field contract. This plan implements them and states neither."
  The split:
  AC-0006 is the rule and this spec's only claim on it; that spec's AC-0017 and
  AC-0028 own routing every file and failing the gate. No `needs` edge is
  recorded either way, because that spec's plan implements text this spec
  already carries while this spec's tombstones are what its lint validates, so
  an edge would assert a false block and two edges would cycle.
- eugenelim: `docs/specs/intent-metadata-shape-contract/spec.md` — nothing in
  the pack checks the ordinal after allocation. Allocation is a prose-invoked
  step at `work-intake/SKILL.md:357`, and `--check` ships with no caller, so a
  hand-made rename that reuses an ordinal leaves no trace. That spec's AC-0028
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

- Technical: a tombstone deleted by hand frees its ordinal, and no criterion
  here can see that. AC-0004 holds over the directory as it stands, and the
  tombstone file is the whole reservation record — deliberately, because
  ADR-0108's Context rejects a repository-global retired list as
  uncoordinatable across worktrees, and this spec's `## Objective` inherits
  that. So the guarantee is "no ordinal is reused while its tombstone stands",
  and hand-deleting one is corpus corruption of the same kind as deleting a
  live intent, which nothing here detects either. `Agent Rules` forbids the
  reuse; that is a rule an agent follows, not a control that fails.

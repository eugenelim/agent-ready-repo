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
moves with it, the registry moves in lockstep, and the vacated name is never
minted again.

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
- A tombstone left at every filename an intent vacates — `docs/product/intents/`
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

- Reuse an ordinal, including one whose tombstone was deleted by hand.
- Delete an intent file. A retirement is a tombstone, not a deletion.
- Add a new top-level directory, a new module boundary, or a new dependency.
  The operation ships inside an existing owner.
- Repair a stale citation by editing a generated projection.

## Testing Strategy

- **The sweep's completeness: TDD.** A compressible invariant — after a rename
  no tracked file carries the vacated path as a link target or a registry
  `path` — so a test can hold it over a fixture corpus. The three trees that
  cite an intent today, and the 3-to-15-file range one rename touches, are
  measurements in the ledger rather than the acceptance boundary, because a new
  citation-bearing source would leave a directory list passing while the
  outcome broke.
- **Transactionality: TDD.** A failure injected at each write point must leave
  the tree byte-identical, which is a property a test asserts and a reviewer
  cannot.
- **Fresh allocation: TDD.** A fixture where the vacated ordinal is free under
  the target token is the case a carried-across ordinal would pass; the
  assertion is that the operation still takes the allocator's next value.
- **The success path: TDD.** Both causes run to completion against a fixture
  corpus and the tombstone left behind is read back for its `Reissued as:`
  value. Asserting only the refusals would let a rename that wrote no successor
  pointer pass every other criterion.
- **Field value shapes: TDD.** One rejecting fixture per field per rule — a
  non-ISO date, a path outside `docs/product/intents/`, an absolute path, an
  empty `Retired:` line.
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

- [ ] **AC-0001.** After a rename, no tracked file carries the vacated path as
      a Markdown link target or as a `path` value in `workspace.toml`, other
      than the tombstone standing at that path. Scope is git's tracked set, so
      it follows the repository rather than a list of directories, and the two
      citation kinds are named because a prose mention of a former path is
      history rather than a stale pointer.
- [ ] **AC-0002.** Every `Slug:` value in the intent corpus is byte-identical
      before and after a rename. The field is the identity anchor a rename does
      not touch; `intent-metadata-shape-contract` AC-0001 is what requires it on
      every live intent, and this criterion does not assert that the corpus
      already satisfies that requirement.
- [ ] **AC-0003.** Any failure the operation surfaces leaves the working tree
      byte-identical to its pre-run state, and the operation makes no durable
      change outside that tree. A process killed mid-write is outside this
      guarantee: because nothing durable lands elsewhere, recovery is `git
      restore`, which the operation relies on rather than reimplements.
- [ ] **AC-0004.** For every type, the allocator's next ordinal exceeds every
      ordinal that type carries in `docs/product/intents/`, counting tombstones
      alongside live intents.
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
- [ ] **AC-0009.** A live pointer whose target is a tombstone is reported as a stale
      citation rather than resolved to that tombstone's successor.
- [ ] **AC-0010.** A rename re-points every tombstone whose `Reissued as:` named the moved
      artifact, inside the same transaction.
- [ ] **AC-0012.** The new filename's ordinal is the allocator's next ordinal
      for the target type, never the vacated ordinal reused under a different
      token.
- [ ] **AC-0013.** A rename that succeeds leaves a tombstone at the vacated
      path whose `Reissued as:` value is the new live artifact's
      repository-relative path.
- [ ] **AC-0014.** Each tombstone field carries its stated value shape:
      `Tombstone:` an ISO 8601 date, being the UTC date the operation ran;
      `Reissued as:` a repository-relative path under `docs/product/intents/`;
      `Retired:` a single non-empty line.

## Retired identifiers

- `AC-0011` — first-time allocation for an intent authored through a
  non-allocating route. A separate outcome, releasable and verifiable on its
  own, so it is not this slice's to close.

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
  an edge would assert a false block and two edges would cycle. **That spec's
  own Follow-ons still record the question as open.** The divergence is in the
  record only, not in either contract; closing it is that spec's edit, and its
  implementing session has been told.
- eugenelim: `docs/specs/intent-metadata-shape-contract/spec.md` — nothing in
  the pack checks the ordinal after allocation. Allocation is a prose-invoked
  step at `work-intake/SKILL.md:357`, and `--check` ships with no caller, so a
  hand-made rename that reuses an ordinal leaves no trace. That spec's AC-0028
  introduces a gate over `docs/product/intents/`, which is a place such a check
  could run; deciding whether it belongs there is that spec's, and how an
  adopter runs it is theirs.
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

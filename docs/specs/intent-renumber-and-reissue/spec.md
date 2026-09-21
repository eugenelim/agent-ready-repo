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

A product engineer whose decomposition shows an intent was framed at the wrong
altitude corrects its filename in one operation, breaking no reference and
freeing no ordinal for reuse. The change lands whole or not at all: every
citation moves, the registry moves with it, and anyone arriving on an old link
is told where the artifact went.

## What Changes

- Numbering, renumbering, and retiring an intent — one confined transactional
  operation, where today no surface may rename an intent at all. It is the
  correction step the shaping loop already assumes: `frame-intent` asserts
  `Level`, admission mints the ordinal from it, and `decompose-intent` is where
  the altitude is actually tested
- A tombstone left at every filename an intent vacates — `docs/product/intents/`
- The citation sweep — `docs/product/**`, `docs/specs/**`, and `workspace.toml`,
  the three trees that cite an intent by path
- A `Tombstone:` preamble field and the shape of the artifact carrying it —
  home open, see `## Assumptions`
- An operator how-to — `guides/product-engineering/how-to/`
- Where it ships — inside `packs/core`, so an adopter installing core has it,
  beside the allocator it depends on

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — the tombstone convention constrains every later intent, and ADR-0108 D3's non-reuse rule is the thing it implements for a second artifact class | `docs/adr/` | eugenelim | An Accepted ADR stating the tombstone convention and its two rejected alternatives | The ADR exists and this spec cites it in `Constrained by:` |
| Interface compatibility | Applicable — `Tombstone:` is a new durable field in an adopter-visible artifact | `guides/product-engineering/reference/intent-fields-and-modes.md` | eugenelim | The field and its three-field contract documented alongside the existing intent fields | The reference page describes the field an adopter will see |
| Maintainer procedure | Applicable — the operation is operator-invoked and its refusals need a recovery story | `guides/product-engineering/how-to/` | eugenelim | A how-to covering the three callers and what to do after a refusal | The page walks one real renumber end to end |
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

- **The sweep's completeness: TDD.** A compressible invariant — after a
  renumber, no citation of the old path survives in the three cited trees — so
  a test can hold it over a fixture corpus.
- **Transactionality: TDD.** A failure injected at each write point must leave
  the tree byte-identical, which is a property a test asserts and a reviewer
  cannot.
- **The tombstone's three-field shape: TDD.** A parse with conforming and
  non-conforming fixtures.
- **Tombstone name safety: inherited, re-run not re-authored.** Already pinned
  before this spec by `test_tombstone_filename_shapes_pin_allocation_and_check`
  in `packs/core/tests/skills/work-intake/test_intent_ordinal.py`, committed
  87768ba4d. This slice re-runs it and adds nothing; it is cited here so the
  contract records where that coverage lives rather than promising it again.
- **The corpus stays clean after a real renumber: goal-based check.** One run
  of the workspace reconciliation over the real `workspace.toml` reports no
  `missing_artifact`, which is the existing fail-closed control at
  `tests/roster/test_workspace_status_projection.py:948`.
- **The operator how-to: manual QA.** A person follows the page through one
  renumber; a test cannot tell whether the page is followable.

## Acceptance Criteria

- [ ] **AC-0001.** After a renumber, no citation of the vacated path survives in
      `docs/product/**`, `docs/specs/**`, or `workspace.toml` — the closed set
      of trees that cite an intent by path.
- [ ] **AC-0002.** Every `Slug:` value in the intent corpus is byte-identical before and
      after a renumber.
- [ ] **AC-0003.** A renumber that fails at any write point leaves the repository
      byte-identical to its pre-run state.
- [ ] **AC-0004.** After a renumber, the allocator's next ordinal for the vacated type is
      never the vacated ordinal.
- [ ] **AC-0005.** A tombstone carries exactly three fields: `Slug:`, unchanged from the
      retired artifact; `Tombstone:`, the retirement date; and exactly one of
      `Reissued as:` or `Retired:`.
- [ ] **AC-0006.** Every file in `docs/product/intents/` is validated against exactly one of
      two contracts, selected by the presence of a `Tombstone:` field.
- [ ] **AC-0007.** A `Reissued as:` value naming a path that does not exist fails and names
      both the tombstone and the missing path.
- [ ] **AC-0008.** A `Reissued as:` value naming a file that itself carries `Tombstone:`
      fails and names both paths.
- [ ] **AC-0009.** A live pointer whose target is a tombstone is reported as a stale
      citation rather than resolved to that tombstone's successor.
- [ ] **AC-0010.** A renumber re-points every tombstone whose `Reissued as:` named the moved
      artifact, inside the same transaction.
- [ ] **AC-0011.** An intent authored after cutover through a route that
      allocates no ordinal acquires the filename `<TOKEN>-NNNN-<slug>.md` on
      request, with `NNNN` from the allocator. An intent carrying no ordinal at
      cutover is out of scope and keeps none, per the brief's forward-only
      non-goal and ADR-0108 D6.

## Retired identifiers

none

## Follow-ons

- eugenelim: `docs/specs/intent-metadata-shape-contract/spec.md` — the corpus
  lint that runs the two-contract partition is that spec's to build; this spec
  states the partition rule and does not implement the lint.
- eugenelim: `docs/specs/intent-metadata-shape-contract/spec.md` — nothing in
  the pack checks the ordinal after allocation. Allocation is a prose-invoked
  step at `work-intake/SKILL.md:357`, and `--check` ships with no caller, so a
  hand-made rename that reuses an ordinal leaves no trace. A corpus check is
  that spec's to build; how an adopter chooses to run it is theirs.
- eugenelim: this repository's own corpus control,
  `test_every_live_typed_file_satisfies_the_owner_shape` at
  `tests/roster/test_typed_ordinal_collision_equivalence.py:63`, sits in the
  dispatch-only roster suite. Where it runs here is a repository-local gate
  question, separate from what the pack ships.

## Assumptions

none

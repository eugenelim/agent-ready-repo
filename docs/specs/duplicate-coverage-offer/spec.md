# Spec: Offer the artifact that already covers a captured item

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Brief:** none
- **Discovery:** docs/product/intents/FEAT-0009-duplicate-coverage-check.md
- **Related:** docs/specs/work-item-promotion-handoff/spec.md — the sibling this spec's offer runs inside
- **Constrained by:**
  - docs/product/research/sub-spec-work-items-survey.md § Refuted approaches — path proximity is refuted as a candidate mechanism and is not re-proposed
  - docs/product/intents/CAP-0005-work-item-capture-and-disposition.md § Assumptions — a terminal disposition, once recorded, is not replaced by a conflicting one

## Objective

Stop promotion creating a second artifact for an outcome an existing one
already covers, by producing candidates a human accepts or rejects before
creation.

## Boundaries

This spec owns the candidate mechanism and the offer it produces. It does not
own:

- **Deciding.** The human accepts or rejects; the offer is advisory.
- **The governance route**, and the augmenting write's own review path beyond
  naming which contract acceptance takes.
- **The effects a disposition produces and their atomicity.**
  `docs/specs/work-item-promotion-handoff/spec.md`'s. Acceptance is a write, so
  that spec's atomicity decision places it inside the unit or outside it with a
  named recovery contract; this spec does not settle which.
- **Whether a route may run unattended**, and what a held item carries.
  Promotion's rule binds. AC8 states only what this offer does under it.
- **The trust boundary on captured content as input.** Promotion's decision
  covers the query input this mechanism reads and names this spec as deferring
  there.

## Decisions this spec owes

Assigned by
[FEAT-0009](../../product/intents/FEAT-0009-duplicate-coverage-check.md)
§ For the spec to decide, which holds the grounds for each. None is made here.

- **What "covers" means**, and how ground truth is established for measuring
  it.
- **The candidate universe**, including whether a retired or superseded
  artifact can cover an item.
- **The offer contract** — list size, ordering, the minimum evidence an entry
  needs to be worth showing, and what is shown when nothing qualifies.
- **What acceptance writes.** Editing an existing artifact, appending to it and
  linking to it are three contracts with three review paths.
- **Which of several valid covering artifacts an offer prefers.** Distinct from
  ordering: this decides what acceptance attaches to.
- **Portability.** Repositories differ in artifact kinds, paths and prose
  conventions, so the chosen mechanism needs a stated reason to work
  elsewhere. The refuted mechanism died on a property of this corpus, so a
  successor tuned to this repository's conventions fails the same way in an
  adopter's.
- **This spec's acceptance thresholds for reach and precision**, and their
  derivation. These are not the parent's kill line, which FEAT-0009 § De-risk
  owns and derives for itself.

## Testing Strategy

- Assemble ten items whose covering artifact is known and which were not
  inspected during any probe run under FEAT-0009 § De-risk, including both the
  path probe and the body-text probe its validation hook describes. If ten
  cannot be assembled, that is the finding FEAT-0009 § De-risk names, and the
  mechanism does not ship.
- Record both thresholds and their derivation before that set is run (AC3).
- Run a promotion end to end; assert the offer step's result exists before any
  artifact is created, including on the empty-candidate path (AC1).
- Run one offer where the human rejects all candidates and one where they
  accept a candidate; assert the offer itself creates nothing either way
  (AC2).
- Run the candidate mechanism over the set; have the adjudicator judge each
  result as correct offer, correct no-offer, or wrong (AC6).
- Measure both halves against the recorded thresholds — whether the covering
  artifact is offered, and what a reader must read through to reach it (AC4,
  AC5).
- Run the mechanism unmodified against a fixture corpus with different
  artifact kinds, paths and prose conventions, whose known-coverage set and its
  establisher are recorded with it; assert reach stays at or above the
  threshold recorded for that corpus (AC7).
- Assert an unattended run produces no offer and creates nothing (AC8).

## Acceptance Criteria

- [ ] For a captured item, the offer step runs and produces its result —
      possibly an empty candidate list — before promotion creates an artifact.
- [ ] The offer is advisory; a human accepts one or rejects all.
- [ ] Both thresholds and their derivation are recorded before the validation
      run, each stating its measurement basis and the denominator it is
      computed over.
- [ ] Reach over the validation set is at least the recorded threshold, and a
      run below it fails.
- [ ] Precision over the validation set is at least the recorded threshold, and
      a run below it fails.
- [ ] The validation set is disjoint from every set used to develop the
      mechanism and from every probe set under FEAT-0009 § De-risk.
- [ ] Run unmodified against a fixture corpus with different artifact kinds,
      paths and prose conventions, the mechanism holds reach at or above the
      threshold recorded for that corpus. The fixture corpus names how many
      items with known coverage it carries and who established them.
- [ ] An unattended run makes no offer and creates no artifact on the offer's
      account.

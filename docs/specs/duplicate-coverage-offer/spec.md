# Spec: Offer the artifact that already covers a captured item

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Brief:** none
- **Discovery:** docs/product/intents/FEAT-0009-duplicate-coverage-check.md
- **Related:** docs/product/intents/FEAT-0007-work-item-promotion-routing.md
- **Constrained by:** none recorded yet

> **Draft, materialised ahead of shaping.** Nothing here is agreed.

## Objective

Stop promotion creating a second artifact for an outcome an existing one
already covers, by offering candidates a human accepts or rejects.

**Path proximity is refuted and must not be re-proposed.** The probe, its
command and the reason it fails in principle are recorded in
`docs/product/research/sub-spec-work-items-survey.md` under *Refuted
approaches*. An artifact's path does not encode what it covers.

## Decisions this spec owes

- **What "covers" means**, and how ground truth is established for measuring it.
- **The candidate universe** — which artifact kinds and lifecycle states are
  searched, and whether a retired or superseded artifact can cover an item.
- **The offer contract** — maximum list size, ordering, the minimum evidence an
  entry needs to be worth showing, and what is shown when nothing qualifies.
- **What acceptance writes.** Editing an existing artifact, appending to it and
  linking to it are three different contracts with three review paths.
- **Both thresholds.** The parent's reach and precision lines are placeholders
  with no derivation, and are marked as such there.
- **Behaviour with no human present**, given the offer is advisory by design.

## Testing Strategy

- Run the candidate mechanism over ten items whose covering artifact is known
  and which were **not** inspected during the refuted probe; have the
  adjudicator judge each as correct offer, correct no-offer, or wrong.
- If ten uninspected items with known coverage cannot be found, record that as
  a finding: ground truth is scarce and a measure built on it will not hold.
- Measure both halves — whether the covering artifact is offered, and what a
  reader must read through to reach it.

## Acceptance Criteria

- [ ] Promotion offers candidate covering artifacts before creating a new one.
- [ ] The offer is advisory; a human accepts one or rejects all.
- [ ] Both reach and precision are measured, against thresholds this spec
      derives rather than inherits.
- [ ] A mechanism is refuted on its own evidence; a failure does not close the
      outcome while another mechanism is untried.
- [ ] The validation set is disjoint from any set used to develop the mechanism.

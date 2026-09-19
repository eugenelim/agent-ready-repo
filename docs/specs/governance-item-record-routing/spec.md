# Spec: Route a captured decision question to a record that names a decider

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Brief:** none
- **Discovery:** docs/product/intents/FEAT-0008-governance-item-record-routing.md
- **Related:** docs/product/intents/FEAT-0007-work-item-promotion-routing.md
- **Constrained by:** none recorded yet

> **Draft, materialised ahead of shaping.** Nothing here is agreed.

## Objective

Give a captured item whose deliverable is a decision somewhere to go: a record
that names who answers it. Which record type it takes is elicited from the
owner, not derived by a rule, because who may decide alone differs by
repository.

## Decisions this spec owes

- **What an absent pack does.** The record-authoring skills sit outside core
  while the classifier is core's. Intended shape: two destinations — the
  capture sink, always reachable, and the governance record start, which
  refuses loudly and records when the pack is absent. This preserves
  `work-intake`'s core-alone guarantee, which binds its four named operations
  rather than every destination within them; the defect route's existing
  readiness precondition is the in-tree precedent for a conditional destination
  inside `start`. The wording must be coherent — an earlier draft said both
  "refused and recorded" and "writes nothing".
- **What qualifies as a governance item**, with representative valid and
  invalid cases. The parent's kind definition over-collects on its own.
- **The elicitation contract** — who answers, the choices, and the behaviour on
  cancellation, an invalid answer, or no answer.
- **What "reaches a decider" means** — file creation, notification,
  acknowledgement, or a completed decision. The measure depends on it.
- **The terminal disposition** for success, refusal, cancellation and an
  unattended run.

## Testing Strategy

- Walk ten captured governance items with the owner; record the chosen record
  type, the confidence, and whether reading the original work changed it.
- Run the route with the pack absent; assert a loud recorded refusal and that
  the capture sink stays reachable.
- Assert no other route changes behaviour when the pack is absent.

## Acceptance Criteria

- [ ] A captured governance item becomes a record naming who decides.
- [ ] The record type is elicited and the answer is stored with the item.
- [ ] With the pack absent, the governance start refuses loudly and records;
      the capture sink remains reachable and every other route is unaffected.
- [ ] An unattended drain holds governance items rather than guessing.
- [ ] Creating a record is not treated as the question being answered — the
      parent names reach-and-action as an untested bet, and no criterion here
      may assume it.

# Spec: Route a captured decision question to a record that names a decider

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Brief:** none
- **Discovery:** docs/product/intents/FEAT-0008-governance-item-record-routing.md
- **Related:** docs/specs/work-item-promotion-handoff/spec.md — owns the drain this route is reached from and the hold that shipping this route discharges
- **Constrained by:** docs/product/intents/FEAT-0008-governance-item-record-routing.md § Outcome — the measure is fixed at a record with a named decider, and no criterion here may read reach-and-action as tested

## Objective

Give a captured item whose deliverable is a decision somewhere to go: a record
that names who answers it. The record type is elicited from the owner rather
than derived by a rule.

## Boundaries

This spec owns one route and what it writes. It does not own:

- **The other routes.** A sibling's, per FEAT-0008 § Non-goals.
- **Authoring the record.** Not changed by this spec, and the accepted decision
  corpus sits outside the capability entirely per CAP-0005 § Boundary.
- **Whether a route may run unattended at all, and what must remain held when
  nobody can confirm.** `docs/specs/work-item-promotion-handoff/spec.md`'s rule
  binds this route, including whether a held item carries a terminal
  disposition.
- **The `governance` kind and its write-time threshold.**
  `docs/specs/work-item-capture/spec.md`'s, because capture writes the record.
  FEAT-0008 § For the spec to decide records the cut. This spec decides only
  what the route admits once an item is written.
- **The parent's bet test.** FEAT-0008 § De-risk's; it gates the feature's bet,
  not this spec's acceptance, and cannot run before capture ships.

## Decisions this spec owes

Assigned by
[FEAT-0008](../../product/intents/FEAT-0008-governance-item-record-routing.md)
§ For the spec to decide, which holds the grounds for each. None is made here.

- **The elicitation contract** — who answers, the choices, and the behaviour on
  cancellation, an invalid answer, or no answer.
- **The terminal disposition** for success, refusal and cancellation. The
  unattended case is promotion's.
- **Whether the two record types are the only destinations**, given that one
  opens at `Proposed` with decision-makers and the other at `Draft` with an
  approver.
- **Which governance items this route admits once written**, with
  representative valid and invalid cases. An item admitted at write time and
  refused here otherwise has nowhere to go, which CAP-0005 § Assumptions
  forbids.

## Testing Strategy

- Run the route with the authoring pack absent; assert the governance start
  refuses and the refusal is recorded (AC3).
- Run capture, the defect route and the closure path with the pack absent;
  assert the sink stays reachable and neither route changes behaviour (AC4,
  AC5).
- Elicit a record type, then assert the answer is stored with the item and the
  created record names a decider (AC1, AC2).
- Submit an item the admission rule refuses; assert a terminal disposition is
  recorded and no record is created (AC6).
- Cancel an elicitation mid-run; assert the terminal disposition the
  elicitation contract names is recorded and no partial record is left (AC7).

## Acceptance Criteria

- [ ] A captured governance item becomes a record naming who decides.
- [ ] The record type is elicited and the answer is stored with the item.
- [ ] With the pack absent, the governance start refuses and the refusal is
      recorded.
- [ ] With the pack absent, the capture sink remains reachable.
- [ ] With the pack absent, the defect route and the closure path produce the
      same observable behaviour as with the pack present.
- [ ] A governance item the route refuses on admission records a terminal
      disposition.
- [ ] A cancelled elicitation records the terminal disposition the elicitation
      contract names and leaves no partial record.

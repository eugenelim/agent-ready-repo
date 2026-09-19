# Spec: Hand a captured item to its owner or close it, and record which

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Brief:** none
- **Discovery:** docs/product/intents/FEAT-0007-work-item-promotion-routing.md
- **Constrained by:** docs/specs/work-item-capture/spec.md — the captured record this spec consumes is written under the contract that spec settles, including the fields a routing decision can read

## Objective

Give the capture store an exit. A triaged item either reaches the classifier
that already handles work of its shape, or is closed because it should go
nowhere, and the terminal disposition records which. The classifier and its
input shapes exist; the step that reaches them does not. FEAT-0007
§ Decomposition holds these two halves as one outcome.

## Boundaries

This spec owns the drain: what it routes, what it closes, what it holds, and
the atomicity of every effect it commits. It does not own:

- **Governance record routing.** A sibling's, per FEAT-0007 § Non-goals;
  `docs/specs/governance-item-record-routing/spec.md`. AC6 holds such items
  until it ships.
- **Telling whether an existing artifact already covers the item.**
  `docs/specs/duplicate-coverage-offer/spec.md`'s. Until it ships, promotion
  may create a second artifact for covered work, which CAP-0005
  § Decomposition decisions accepts as the shipping state.
- **Doing the work.** Every destination is an existing owner with its own
  contract, per CAP-0005 § Boundary.
- **A stored command's execution safety.** Settled at write time by
  `docs/specs/work-item-capture/spec.md`. This spec owns the same content only
  as input to a decision it makes.

## Decisions this spec owes

Assigned by
[FEAT-0007](../../product/intents/FEAT-0007-work-item-promotion-routing.md)
§ For the spec to decide, which holds the grounds for each. None is made here.

- **Atomicity across the effects a disposition produces** — artifact creation,
  workspace registration, handoff, and the terminal disposition, one of which
  is irreversible. Ordering, idempotency, retry and recovery all follow from
  this, and the decision names exactly one recovery path. Two cases it must
  place: a closure, which produces the terminal disposition alone; and the
  duplicate-coverage offer, whose human gate precedes artifact creation and
  whose acceptance is itself a write. Say for each whether it sits inside the
  unit or outside it with its own recovery contract.
- **Which captured fields decide each destination**, and the behaviour when
  they are absent, stale, or contradict each other.
- **When routing happens and what invokes it** — whether the classifier is
  extended or called, and at what point in a drain.
- **The trust boundary on captured content as input to this capability's own
  decisions.** What a stored path or prose may influence, what is refused as an
  input, and what is carried through to the destination unexecuted. This covers
  the classifier's routing input and the query input
  `docs/specs/duplicate-coverage-offer/spec.md` reads, which defers here.
  Execution is out of scope, per `## Boundaries`.
- **What justifies closing an item rather than routing it, and who may do it.**
  Overtaken, superseded and falsified are three grounds with three tests, and
  an unjustified closure is indistinguishable from losing the work this
  feature exists to keep.
- **The disposition for a discarded item** — whether the terminal vocabulary
  gains a value, or one or more existing values are designated to mean it. This
  is the only home for the option set; CAP-0005 § Riskiest assumption states
  the obligation and defers the shape here. Without it the sink's prune half is
  unrecordable and the capability's kill condition cannot be read.
- **Whether a captured record satisfies the defect route's readiness
  condition.**
- **Attended versus unattended operation** — who may confirm a route, what
  must remain held when nobody can, and whether a held item may also carry a
  terminal disposition. This is the drain's rule and binds every route reached
  from it, including the governance and duplicate-coverage siblings. Those
  state only what their own route does under the rule; they do not set it.
- **The adjudicator and rubric** the routing measure depends on. FEAT-0007
  records a single adjudicator as a known gap; the rubric is what closes it.

## Testing Strategy

- After one drain, have the named adjudicator read the original work behind ten
  items the drain was **offered** and judge its disposition of each (AC1, AC2) — routed,
  held and closed alike, since sampling only routed items lets a drain that
  holds or closes every hard case pass. Fails at or above the kill threshold
  FEAT-0007 § De-risk declares and derives.
- Drive a crash between each pair of effects the atomicity decision places
  inside the unit; assert no state in which work exists without its capture
  closed, or a capture closes without handoff (AC4).
- Drive a crash on the closure path, where the terminal disposition is the only
  effect; assert the same invariant holds (AC4, AC5).
- Drive a crash against each effect the atomicity decision places outside the
  unit; assert the recovery contract it names for that effect holds (AC4).
- Drain a captured record whose stored path resolves outside the repository,
  and one carrying a field the trust-boundary decision classifies as
  untrusted; assert each is refused as a routing input, the item is held, and
  the field reaches the destination unexecuted (AC8, AC9).
- Run one drain with no confirmer available; assert every route the attended
  rule requires a human to confirm is held and counted as held (AC10).
- Assert the drain never attempts a second terminal disposition against one
  capture. The store's single-terminal-event rule is recorded in FEAT-0007
  § De-risk (AC11).
- Assert a defect-shaped item that does not meet the defect route's readiness
  condition is held rather than routed (AC7).
- After a drain producing at least one routed item and at least one closure,
  derive the promoted and pruned counts from the store alone, with no run log;
  assert each disposition falls on exactly one side and the two counts sum to
  the dispositions recorded (AC3).

## Acceptance Criteria

- [ ] A triaged item reaches the classifier and its capture records a terminal
      disposition.
- [ ] An item closed without routing records which of overtaken, superseded or
      falsified justifies it, and a closure whose stated ground fails its test
      is refused.
- [ ] Every terminal disposition falls on exactly one side of the
      promoted-or-pruned split CAP-0005 § Riskiest assumption reads, a closure
      falls on the pruned side, and both counts are derivable from the store
      alone.
- [ ] Every effect the atomicity decision places inside the unit commits as one
      recoverable unit, and every effect it places outside carries the recovery
      contract that decision names. No crash leaves work created with its
      capture open, or a capture closed without its handoff.
- [ ] An item the drain cannot route is held, and the run reports the held,
      routed and closed counts using the same partition as the store-derived
      counts.
- [ ] A governance item is held until its own route exists; nothing else is
      blocked by that absence.
- [ ] A defect-shaped item that does not meet the defect route's readiness
      condition is held, not routed.
- [ ] A stored path that resolves outside the repository is refused as a
      routing input and the item is held. Repository confinement is a floor,
      not a settlement.
- [ ] A captured field the trust-boundary decision classifies as untrusted is
      refused as a routing input, and the field reaches the destination
      unexecuted.
- [ ] An unattended run makes no route the attended rule requires a human to
      confirm. Those items are held and counted as held, and carry a terminal
      disposition only if the attended rule says a held item may.
- [ ] The drain never attempts a second terminal disposition against a capture.
      A mis-route is surfaced only through the recovery path the atomicity
      decision names.

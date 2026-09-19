# Spec: Capture a loop's leftover work as an actionable record

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Brief:** none
- **Discovery:** docs/product/intents/FEAT-0006-work-item-capture-contract.md
- **Constrained by:** none recorded yet

> **Draft, materialised ahead of shaping.** Written to hold decisions the parent
> intent deliberately excludes, so a cold session does not re-derive them.
> Nothing here is agreed. Shape it before treating any criterion as contract.

## Objective

Let a work-loop record leftover work in the existing project-knowledge store as
a typed observation a later session can act on without re-deriving what the
original session knew. The parent intent carries the outcome and the evidence;
this settles the contract.

The store, its schema, and the unused evidence slot are located in the parent's
`What exists today`. Read them there rather than assuming their current shape.

## Decisions this spec owes

Each is listed in the parent as the spec's to make. None is made here.

- **Kinds, and each kind's threshold.** The working set is bug, improvement and
  governance, admitted on one test — a kind is warranted only when its required
  field set differs. That bounds the *set*; it does not stop a *kind*
  over-collecting. The decision kind demonstrably over-collects: its definition
  admits almost any design choice. Each kind needs a threshold alongside its
  definition.
- **Required fields per kind**, and what a kind that cannot carry a reproduction
  command supplies instead. A governance question has nothing to reproduce.
- **The trust boundary on a stored command.** A record may carry a command a
  later session runs: authorship, confinement, permitted effects, timeout and
  failure handling. Cheaper to settle before a schema ships than after.
- **Whether the item's prose reuses the existing `lesson` field** or gains its
  own. The schema forbids unknown properties, so either choice moves validators.
- **How the close-time admission rule branches.** It currently discards a
  specific non-generalisable defect by instruction, which is exactly this
  feature's input.
- **Compatibility with records already written**, and what the contract version
  boundary means for them.

## Testing Strategy

- Drive one real loop's close and have a second session with no prior context
  attempt each captured item from its record alone; record which it could act on.
- Ask the capturing author separately what they wanted to record and could not —
  an excluded item leaves no record to sample, so a rate over captures cannot
  see it.
- Assert a kind that cannot carry a reproduction command is still admissible.

## Acceptance Criteria

- [ ] A loop that finishes with leftover work records it without an owner request.
- [ ] A captured record carries what a later session needs to act without
      re-deriving it, per the required-field set this spec settles.
- [ ] An item whose kind cannot supply reproduction evidence is admitted, not
      refused.
- [ ] A ready-now item is not capturable; it is dispatched in-session.
- [ ] Freshness is derived at read time, never stored. The registered freshness
      item is untouched and its recommendation is not assumed.
- [ ] Records written before this contract remain readable.

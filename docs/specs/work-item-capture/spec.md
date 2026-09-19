# Spec: Capture a loop's leftover work as an actionable record

- **Status:** Draft
- **Owner:** eugenelim
- **Mode:** full
- **Brief:** none
- **Discovery:** docs/product/intents/FEAT-0006-work-item-capture-contract.md
- **Constrained by:** docs/product/intents/CAP-0005-work-item-capture-and-disposition.md § Boundary — a stored command's safety is settled at write time, because the owner that runs it is outside the capability, so no destination has to be trusted

## Objective

Let a work-loop record leftover work in the existing project-knowledge store as
a typed observation a later session can act on without re-deriving what the
original session knew, and refuse an item that is not real or not worth
recording before it is written.

The store, its schema, and the unused evidence slot are located in the parent's
`What exists today`. Read them there rather than assuming their current shape.

## Boundaries

This spec settles what may be written and what is refused at write time. It
does not own:

- **What a later session does with a captured record.** Routing, terminal
  dispositions and the treatment of captured content as classifier input are
  `docs/specs/work-item-promotion-handoff/spec.md`'s.
- **Which governance items the governance route accepts once an item is
  written.** `docs/specs/governance-item-record-routing/spec.md`'s, per
  FEAT-0008 § For the spec to decide.
- **Knowledge freshness.** A registered open item with its own owner. This spec
  reads nothing from it and rules nothing about it, per FEAT-0006 § Non-goals.

## Inherited constraints

Not open to this spec. Each is fenced by an artifact above it.

- **A refusal is never silent**, per FEAT-0006 § For the spec to decide. What
  that handling is remains this spec's, below.
- **The mechanical validation tier is the floor**, per FEAT-0006 § Validation
  at capture. It still refuses when the reasoning tier is absent or degraded.
- **The reasoning check runs in a context that did not produce the item**, per
  FEAT-0006 § Validation at capture. This bounds the granularity decision
  below.
- **The necessity test is the repository's own razor, not a new rubric**, per
  FEAT-0006 § Validation at capture. This spec does not author one.
- **An item is validated before it is captured**, per CAP-0005 § Outcome.

## Decisions this spec owes

Assigned by
[FEAT-0006](../../product/intents/FEAT-0006-work-item-capture-contract.md),
chiefly § For the spec to decide, which holds the grounds for each. None is
made here.

- **Kinds, and each kind's threshold.** Both the set and the per-kind threshold,
  including the second half the decision kind needs.
- **Required fields per kind**, and what a kind that cannot carry a reproduction
  command supplies instead.
- **Where validation runs and at what granularity** — per item or once over the
  batch, within the cold-context constraint above.
- **What a refusal does**, within the non-silent floor above: whether the author
  is told, whether the refusal is retained, and whether a corrected item can be
  re-submitted.
- **Operational definitions** for "can act on", "cold session", and the
  false-or-already-fixed count.
- **The trust boundary on a stored command**, at write time: what a record may
  carry, under whose authorship, and what effects are refused before it is
  written.
- **Where and how a surviving item's validation rationale is surfaced**, per
  FEAT-0006 § Validation at capture.
- **Whether the item's prose reuses the existing `lesson` field** or gains its
  own. The schema's policy on unknown properties, read from the schema named in
  the parent's `What exists today`, decides whether either choice moves
  validators.
- **How the close-time admission rule branches.**
- **Compatibility with records already written**, and what the contract version
  boundary means for them.

## Testing Strategy

The parent's own bet test — one loop's close, a cold session, the author
interview — is FEAT-0006 § De-risk's and runs there. These decide this spec's
criteria.

- Decline an item during close and suppress its outcome; assert the close fails
  rather than passes (AC1).
- Attempt a capture whose record names none of the recognised blockers; assert
  it is refused (AC4).
- Attempt a capture whose mechanical tier fails — frozen target, stale anchor,
  unreadable cited artifact — with the reasoning tier available and again with
  it disabled; assert both are refused and nothing is written (AC5, AC6).
- For each kind, construct a record missing one required field; assert each is
  refused, and that a complete record of the same kind is written (AC2).
- Assert a kind that cannot carry a reproduction command is still admissible
  with a complete record (AC3).
- Submit one record per refused command class — an effect outside the permitted
  set, and an authorship the contract does not admit; assert each is refused
  and nothing is stored (AC9).
- Replay every record already in the store through the validation path the
  compatibility decision names; assert each still reads and none is rewritten
  (AC8).
- Assert a written record carries its validation rationale (AC7).

## Acceptance Criteria

- [ ] A loop's close emits the set of items it declined and accounts for every
      member. An item that leaves that set with no outcome of any kind fails
      the close. Which non-silent outcome it gets is the refusal decision's.
- [ ] A record missing any field its kind requires is refused, and a complete
      record of that kind is written.
- [ ] An item whose kind cannot supply reproduction evidence is admitted, not
      refused.
- [ ] A capture whose record names none of the blockers FEAT-0006 § Assumptions
      recognises is refused as ready-now.
- [ ] A capture whose mechanical validation tier refuses is not written.
- [ ] The mechanical tier still refuses when the reasoning tier is absent or
      degraded.
- [ ] A written record carries the rationale for its admission.
- [ ] No record written before this contract becomes unreadable or is
      rewritten. Which contract version validates such a record is the
      compatibility decision's.
- [ ] A record whose command carries an effect outside the permitted set, or an
      authorship the contract does not admit, is refused at write time and
      nothing is stored.

# Design-doc rubric — for `architect-review`

The quality bar for critiquing a design doc. Walk every check; do not
start writing findings until the walk is complete so findings can be
ordered by severity.

> Note: this rubric is intentionally duplicated from
> `architect-design`'s `design-doc-rubric.md`. Skill autonomy beats
> DRY at this scale — each skill stands alone. See the pack README.

## TL;DR

- [ ] Three sentences or fewer.
- [ ] Answers *what is this, and what decision is it asking the reader
      to make?* without forcing the reader into the body.
- [ ] Names the proposal in one phrase a non-author can recall.

## Context

- [ ] States the user-visible problem (not the technical symptom).
- [ ] Names the relevant constraints (deadline, regulatory, team
      shape, existing system shape). At least one is non-obvious.
- [ ] References the system being changed by name — module, service,
      surface — not by gesture.

## Goals and Non-goals

- [ ] Goals are testable. Each is something an outsider could verify.
- [ ] Non-goals are *substantive*. At least one non-goal is something
      a reasonable reader might assume is in scope.

## Proposal

- [ ] Reader can implement from this section alone — or knows
      exactly what they'd need to ask.
- [ ] Names the trust boundaries the proposal crosses.
- [ ] Where structure needs a picture, embeds a diagram and the
      prose references it.

## Alternatives Considered

- [ ] At least two alternatives, each a real option a reasonable
      engineer might have chosen.
- [ ] Each alternative has a *rejection reason*, not a dismissal.
- [ ] No strawmen.

## Risks

- [ ] At least three (two if the proposal is genuinely small).
- [ ] Each is paired with a mitigation, or explicitly marked as
      *accepted unmitigated* with the reason.
- [ ] At least one risk is operational (what breaks at 3am).

## Rollout

- [ ] Names the migration / launch shape.
- [ ] Has a rollback story. "We won't need to roll back" fails.
- [ ] Names who is on the hook for the rollout window.

## Open Questions

- [ ] Empty is fine. No padding.
- [ ] Each question names who could answer it.
- [ ] No question is a disguised TODO.

## Cross-cutting

- [ ] Performance / scale assumptions named. For a **synchronous** request path,
      the worst-case latency is summed across every hop and compared to the
      binding front-door timeout; an unbudgeted long-operation path that can
      exceed it is a finding (see the serverless lens's sync-vs-async gate).
- [ ] Data-handling and privacy obligations named.
- [ ] Failure modes and observability hooks named.
- [ ] Cost shape named (when material).

## Severity mapping (typical)

- 🟥 **Blocker** — TL;DR misleads; Proposal section incomplete or
  contradicts TL;DR; trust boundary unlabeled; Alternatives is one
  option dressed as two.
- 🟧 **Major** — Goals not testable; Non-goals empty; one alternative
  is a strawman; no rollback story; cross-cutting concerns ignored.
- 🟨 **Minor** — Section ordering awkward; one risk has no
  mitigation; cross-cutting partial.
- ⚪ **Nit** — Phrasing, typos, capitalization.

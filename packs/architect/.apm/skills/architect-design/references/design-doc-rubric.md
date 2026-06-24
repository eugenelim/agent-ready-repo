# Design-doc rubric

The quality bar for `architect-design`. Walk this rubric before showing
the user a draft. Each item is a check, not a suggestion — if you can't
answer "yes" to all of them with the draft as it stands, fix the draft.

> Note: this rubric is intentionally duplicated as
> `references/rubric-design-doc.md` inside `architect-review`. Skill
> autonomy beats DRY at this scale — see the pack README.

## TL;DR

- [ ] Three sentences or fewer.
- [ ] Answers *what is this, and what decision is it asking the reader
      to make?* without forcing the reader into the body.
- [ ] Names the proposal in one phrase a non-author can recall in
      a hallway conversation.

## Context

- [ ] States the user-visible problem (not the technical symptom).
- [ ] Names the relevant constraints (deadline, regulatory, team
      shape, existing system shape). At least one is non-obvious.
- [ ] References the system being changed by name — module, service,
      surface — not by gesture.

## Goals and Non-goals

- [ ] Goals are testable. Each is something an outsider could verify
      from the outside, not a vibe ("better performance" fails;
      "p95 < 200ms at 10× current load" passes).
- [ ] Non-goals are *substantive*. At least one non-goal is something
      a reasonable reader might assume is in scope. ("We are not
      tackling X in this proposal because Y.")

## Proposal

- [ ] Reader can implement from this section alone — or knows
      exactly what they'd need to ask.
- [ ] Names the trust boundaries the proposal crosses (auth, data
      residency, blast radius).
- [ ] Where structure needs a picture, embeds a Mermaid diagram, and
      the prose actually references it.

## Alternatives Considered

- [ ] At least two alternatives, each a real option a reasonable
      engineer might have chosen.
- [ ] Each alternative has a *rejection reason*, not a dismissal.
- [ ] No strawmen — load `alternatives.md` if any alternative reads
      as "we could do X but obviously not".

## Risks

- [ ] At least three. Two if the proposal is genuinely small.
- [ ] Each is paired with a mitigation, or explicitly marked as
      *accepted unmitigated* with the reason.
- [ ] At least one risk is operational (what breaks at 3am).

## Rollout

- [ ] Names the migration / launch shape: big-bang, phased,
      shadow-traffic, dark launch, feature-flag.
- [ ] Has a rollback story. "We won't need to roll back" is not a
      rollback story.
- [ ] Names who is on the hook for the rollout window.

## Open Questions

- [ ] Empty section is fine if no questions remain. Don't pad.
- [ ] Each question names *who* could answer it (a person, a team,
      a measurement).
- [ ] No question is a disguised TODO — those go in a follow-up
      issue, not the doc.

## Cross-cutting (load `nfr-checklist.md` if any of these are unclear)

- [ ] Performance / scale assumptions named. For a **synchronous** request path,
      the worst-case latency is summed across every hop and compared to the
      binding front-door timeout; a long-running operation that can exceed it is
      shown moving off the synchronous path (see the serverless lens's
      sync-vs-async gate), not left as an unbudgeted assumption.
- [ ] Data-handling and privacy obligations named.
- [ ] Failure modes and observability hooks named.
- [ ] Cost shape named (when material).

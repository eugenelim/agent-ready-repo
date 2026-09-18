# Design-doc rubric

The quality bar for `architect-design`. Walk this rubric before showing
the user a draft. Each item is a check, not a suggestion — if you can't
answer "yes" to all of them with the draft as it stands, fix the draft.

> Note: this rubric is intentionally duplicated as
> `references/rubric-design-doc.md` inside `architect-review`. Skill
> autonomy beats DRY at this scale — see the pack README.

**How to walk this rubric.** Three scopes author from three templates, and they do not carry the same
sections or the same table columns. **A check applies when the document's scope
has the section the check sits under.** A check naming a field that scope does
not carry is not applicable, and skipping it is not a failure — a rubric that
demanded every field of every scope would fail a correctly authored document.

Where a check is narrower than all three scopes it says so in the item, as
*(subsystem)*, *(application/system)* or *(architecture change)*. An unmarked
check applies wherever its section exists.

An architecture-change document carries eight delta sections under different
names. A `*(architecture change)*` check applies to the delta section its
parent heading maps to:

| Spine section | Its delta section |
| --- | --- |
| Scope and Context | Scope and Baseline |
| Structural Model | Structural Change |
| Runtime Model | Runtime Change |
| Contracts and Invariants | Contract and Invariant Change |
| Data and State | Data/State Migration |
| Deployment and Operations | Deployment/Operational Change |
| Quality Scenarios and Verification | Quality Regression and Verification |
| Implementation Mapping | Build Mapping |

A change document has no Decisions, Rollout, or Open Questions section, so no
check under those headings reaches it.

## Scope and Context

- [ ] The header states `Decision sought` and `Title`, and both are filled
      in — not left as the template's placeholder text. This is what a
      non-author needs before opening the body: what is this, and what
      decision is it asking the reader to make.
- [ ] States the user-visible problem (not the technical symptom).
- [ ] Names the relevant constraints (deadline, regulatory, team
      shape, existing system shape). At least one is non-obvious.
- [ ] References the system being changed by name — module, service,
      surface — not by gesture.
- [ ] Goals are testable. Each is something an outsider could verify
      from the outside, not a vibe ("better performance" fails;
      "p95 < 200ms at 10× current load" passes).
- [ ] Non-goals are *substantive*. At least one non-goal is something
      a reasonable reader might assume is in scope. ("We are not
      tackling X in this proposal because Y.")

## Structural Model

- [ ] The element catalogue names a type and a one-sentence
      responsibility for every element.
- [ ] Names the trust boundaries the model crosses (auth, data
      residency, blast radius).
- [ ] Every component and boundary names the current goal, constraint, or
      prioritized quality attribute that justifies it.
- [ ] Removes unsupported future-proofing. Reuses an existing capability unless
      a current need justifies adding a new mechanism.

## Runtime Model

- [ ] Carries at least one normal-path scenario and one
      failure-or-recovery-path scenario, each sequenced rather than
      only described.

## Contracts and Invariants

- [ ] *(subsystem, application/system)* Each contract names its identity,
      its compatibility rule, and its failure semantics — not only its
      request/response shape.
- [ ] *(architecture change)* Each contract change names its change type,
      the baseline it is measured against, compatibility during the
      transition, and how it is enforced and verified.

## Data and State

- [ ] *(subsystem)* Every element's state is declared explicitly,
      including an element that is `stateless` — never left as an absent
      row a reader has to interpret.
- [ ] *(application/system)* Every data domain names its authority — the
      one place allowed to decide the value. Two authorities for one
      domain is a contradiction, not a redundancy.
- [ ] *(architecture change → Data/State Migration)* Every migrated data
      element names its old shape, its new shape, the migration mechanism
      and its trigger, and what a partial migration leaves behind and how
      that is undone. A migration with no stated rollback is not yet a
      migration.

## Deployment and Operations

- [ ] Every deployment unit names how it scales and the signal an
      operator watches.
- [ ] A topology diagram appears only where physical placement differs
      from the structural model — a second diagram repeating the
      structure earns its deletion.

## Quality Scenarios and Verification

- [ ] Each quality attribute carries a measurable target — the number
      that decides pass or fail, not a vibe.

## Implementation Mapping

- [ ] Together, the complete model set and this section are sufficient
      to implement from — a reader would know exactly what to build,
      or exactly what to ask, without the section this replaces.
- [ ] *(subsystem)* Each element in the model reaches a verification — a
      test, contract test, or monitor that proves the mapping holds.
- [ ] *(application/system)* The mapping reaches product, repository,
      deployable, platform and team, and carries no per-file or
      per-module detail.

## Decisions, Alternatives, and Risks

- [ ] At least two alternatives, each a real option a reasonable
      engineer might have chosen.
- [ ] Each alternative has a *rejection reason*, not a dismissal.
- [ ] No strawmen — load `alternatives.md` if any alternative reads
      as "we could do X but obviously not".
- [ ] At least three risks. Two if the proposal is genuinely small.
- [ ] Each risk is paired with a mitigation, or explicitly marked as
      *accepted unmitigated* with the reason.
- [ ] At least one risk is operational (what breaks at 3am).

## Rollout, Migration, and Reversal

- [ ] Names the migration / launch shape: big-bang, phased,
      shadow-traffic, dark launch, feature-flag.
- [ ] Has a rollback story. "We won't need to roll back" is not a
      rollback story.
- [ ] Names who is on the hook for the rollout window.

## Open Questions

- [ ] An empty section is omitted entirely — a section left present
      with no items is not evidence that none exist.
- [ ] Each question names *who* could answer it (a person, a team,
      a measurement).
- [ ] No question is a disguised TODO — those go in a follow-up
      issue, not the doc.

## Cross-cutting

_Load `nfr-checklist.md` if any of these are unclear._

- [ ] Performance / scale assumptions named. For a **synchronous** request path,
      the worst-case latency is summed across every hop and compared to the
      binding front-door timeout; a long-running operation that can exceed it is
      shown moving off the synchronous path (see the serverless lens's
      sync-vs-async gate), not left as an unbudgeted assumption.
- [ ] Data-handling and privacy obligations named.
- [ ] Failure modes and observability hooks named.
- [ ] Cost shape named (when material).
- [ ] Every diagram states one named question and one zoom level, and
      the surrounding prose answers that question rather than only
      captioning the picture.
- [ ] Deletes unnecessary claims. Each necessary cross-document assertion has
      one bounded check of its named target or is labelled as an assumption or
      discovery predicate.

## Decomposition

- [ ] If this document covers several subsystems, it is checked
      against `references/decomposition-rubric.md` instead of the
      checks above — this rubric does not restate that rubric's
      criteria.

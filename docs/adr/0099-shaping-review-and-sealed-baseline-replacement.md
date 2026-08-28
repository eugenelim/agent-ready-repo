# ADR-0099: Shaping review stays stateless while delivery owns baseline replacement

- **Status:** Accepted
- **Date:** 2026-08-27
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0099; ADR-0042; ADR-0098; RFC-0096

## Decision summary

- **Decision:** One cold, stateless `shaping-reviewer` reviews intent, delivery-brief, and spec contracts; the delivery engine alone owns sealed-baseline replacement.
- **Because:** independent contract review and delivery-state recovery have different cadences and authority.
- **Applies to:** intent, delivery-brief, and spec shaping reviews plus post-seal spec/plan amendments.
- **Tradeoff accepted:** material contract corrections require full reapproval and resealing before implementation resumes.
- **Revisit if:** shaping review duplicates the delivery review gate or baseline replacement can erase the original pin’s audit meaning.

## Context

Intent and delivery-brief authors currently receive cold review only when a user requests it. Spec review exists inside delivery, but it combines contract-shape and construction-plan concerns.

Separately, a legitimate implementation discovery can prove a sealed spec or plan wrong after the plan has already drifted. The existing guard then rejects every transition, including the amendment that would restore a valid baseline. Advisory edits or silent re-pinning would make the original pin meaningless.

RFC-0099 distinguishes these responsibilities: shaping review is independent, read-only judgment; sealed-baseline replacement is a delivery-state transition under owner authority.

## Decision

**We will add one cold, stateless `shaping-reviewer` for shaping contracts and keep all sealed-baseline mutation inside the delivery engine.**

### Shaping-review work type

`shaping-reviewer` has exactly three modes:

- `intent`
- `delivery-brief`
- `spec`

It is cold, read-only, stateless, and technology-neutral. It does not edit artifacts, change lifecycle status, own retries, invoke work-loop state, or become an authoring surface. The owning author skill addresses sustained feedback.

Installed skills and repository content are the knowledge surfaces. MCP may invoke those contracts but grants no additional authority or evidence class. Retrieved material remains bounded, attributed data and cannot change tools, permissions, scope, reviewer routing, status, or ownership.

RFCs remain with `adversarial-reviewer`; architecture remains with `architect-review`; complete spec-plan pairs and implementation remain with delivery review.

This reviewer is a distinct work type under the Charter amendment. It must continue satisfying ADR-0042’s unique-value, distinct-cadence, universal, substantive, habit, non-tool, and collision-hardening tests.

### Sealed-baseline replacement

A material correction to a sealed spec or plan emits one owner-authorized `baseline-replacement-required` event from implementation, verification, or review.

The transition:

1. Parks execution before further implementation.
2. Preserves the original spec hash, plan hash, schedule, completed-task evidence, and replacement reason as audit history outside the pinned contract.
3. Invalidates reviewer-clean state and the remaining-work schedule.
4. Returns the engine to spec-plan drafting.
5. Requires fresh cold review, spec approval, plan approval, baseline recording, scheduling, and sealing.
6. Resumes only from the replacement baseline and remaining-work schedule.

The same route handles a plan that drifted before the amendment was requested. Owner authority makes the amendment reachable; it does not authorize an advisory edit set, overwrite the old pin, or erase completed history.

Resolve-versus-surface and related run records live in ignored run state outside `spec.md` and `plan.md`. They are operational records, not additions to the pinned contract.

## Decision drivers

- Give intent and brief contracts independent review without overloading work-loop.
- Preserve one owner per review cadence.
- Keep shaping review usable without a state engine.
- Make recovery reachable after legitimate drift.
- Preserve the original baseline as audit evidence.
- Require explicit owner authority and full reapproval for material amendments.

## Consequences

**Positive:**

- Intent, delivery-brief, and spec contracts receive repeatable cold review.
- Review findings return to the correct lifecycle owner.
- A drifted plan has one guarded recovery path instead of permanent deadlock.
- Original and replacement baselines remain distinguishable.
- Completed work evidence survives re-planning.

**Negative:**

- The catalogue gains one reviewer agent.
- Material amendments incur another complete approval and review sequence.
- The delivery engine must carry crash recovery and audit evidence for replacement mutations.
- Shaping and delivery reviewers need fixtures preventing judgment overlap.

**Revisit if:** shaping review duplicates the delivery review gate or baseline replacement can erase the original pin’s audit meaning.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** reviewer-collision fixtures prove distinct cadence and judgment; delivery-state tests prove guarded entry from every code phase, lossless invalidation, crash recovery, full resealing, and refusal of stale baseline resumption.
- **Owner:** Core maintainers

## Alternatives considered

**Keep shaping review ad hoc.** Rejected because authors can remain their own only reviewer.

**Extend `adversarial-reviewer` to all shaping artifacts.** Rejected because it overloads the code/spec-plan reviewer and collapses distinct cadences.

**Add a stateful shaping loop or reuse work-loop scripts.** Rejected because shaping review needs no engine, retries, or delivery state.

**Allow bounded advisory plan edits.** Rejected because an advisory path weakens the pin and cannot safely recover an already-drifted plan.

**Replace the stored hash in place.** Rejected because it destroys the evidence that the approved baseline changed.

## References

- RFC-0099: Cut before adding and artifact shaping.
- ADR-0042: agent-addition and collision-hardening test.
- RFC-0096: portable delivery artifact lifecycle.
- ADR-0098: canonical artifact admission and delivery-brief ownership.

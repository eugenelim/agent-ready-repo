# Role-journey guidance covers coordinated agent swarms

- **Slug:** `role-journey-agent-swarm-section`
- **Status:** Fulfilled
- **Fulfilled:** 2026-11-12 eugenelim: documented supervised execution and per-wave opt-in, retained autonomous swarming as a shaping target, and amended the old marker requirement; source-backed claim evidence, guide checks, and spec-status lint pass.
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim

## Outcome

The core role-journey guide explains supervised task execution and guarded parallel waves from the execution-supervisor contracts, while keeping autonomous ready-spec claiming and draining outside its claims.

## Boundary

- Extend the Agent section of guides/core/explanation/role-journeys.md from single-agent execution to coordinated supervisor and executor pipelines.
- Document recovery and review limits within an approved plan, sequential defaults, and explicit human opt-in for each eligible parallel wave.
- Atomic ready-spec claiming, autonomous draining, stalled-spec reassignment, and mixed-host adapter behavior remain shaping concerns and are not invented in the guide.

## Owner

- eugenelim, core journey-guide maintainer.


## Unresolved questions

None for this narrowed documentation slice. The broader journey keeps its autonomous claiming and adapter questions; supervised task execution does not settle them.

## Projection

- Direct-light documentation delivery, with claim evidence below and a dated amendment to `m6-role-journey-guides` AC6. No new specification is needed.

## Opportunity

The role-journey guide needs to distinguish supervised task execution from the autonomous ready-spec swarm target. This intent owns replacing the deferred guide section with source-backed coverage of the supervised pipeline.

## Assumptions

- The execution-supervisor contracts govern supervised task behavior; the source journey describes a distinct autonomous claiming target.
- The public guide must not present shaping-stage mechanics as shipped capability.


## Source

- Mode: repo-origin
- Locator: docs/product/journeys/engineer-scales-to-swarm.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

## Readiness

Route: direct-light, documentation only. Extend the Agent section of `guides/core/explanation/role-journeys.md`, remove its deferral marker, distinguish the broader shaping journey, and amend the old marker requirement in `docs/specs/m6-role-journey-guides/spec.md`. Preserve that spec's checked historical AC6. Keep internal spec citations in this evidence record, because the public guide must not acquire repository-only spec references.

## Riskiest assumption

The execution-supervisor contracts support a useful supervised execution explanation without claiming the autonomous swarm journey is complete. The claim-to-criterion table below bounds each new behavioral claim; public guide checks verify publication conventions.

## De-risk result

2026-11-12. The four numbered execution-supervisor contracts contain 108 checked criteria; wave scheduling adds ten. They distinguish supervised tasks inside an approved plan from agents atomically claiming ready specs. The broader journey is therefore retained as a shaping target, not marked superseded. Wave scheduling requires sequential execution by default, both safe-category and file-disjointness checks for parallel writes, and explicit human opt-in for each eligible wave. The supervisor cutover owns current invocation; the older wave contract's retired command name is not a guide command.

## Claim-to-criterion evidence

The links identify the owning criteria; lifecycle state remains in each spec's own header. Each listed criterion is checked in its source.

| New guide claim | Governing criterion |
| --- | --- |
| Full-mode supervisor owns execution actions; light mode runs without it | [execution-supervisor-cutover](../../specs/execution-supervisor-cutover/spec.md), AC-0001, AC-0003, AC-0011 |
| Approval precedes task execution within the spec and plan | [execution-supervisor-core](../../specs/execution-supervisor-core/spec.md), AC-0001, AC-0003, request-kind definitions |
| Recorded progress recovers after interruption; a new attempt follows report or supersession | [execution-supervisor-core](../../specs/execution-supervisor-core/spec.md), AC-0015–AC-0017 |
| Trusted-file changes refuse an attempt; these checks do not promise worker sandboxing | [execution-supervisor-attempt-security](../../specs/execution-supervisor-attempt-security/spec.md), AC-0001, AC-0003, AC-0013 and Accepted Risk |
| Criterion evidence and current review readiness both govern completion | [execution-supervisor-core](../../specs/execution-supervisor-core/spec.md), AC-0022–AC-0023, Readiness truth table; [execution-supervisor-review-gate](../../specs/execution-supervisor-review-gate/spec.md), AC-0001 |
| Implementation retries have a cap; review rounds have a separate owner-controlled override | [execution-supervisor-core](../../specs/execution-supervisor-core/spec.md), AC-0024–AC-0025; [execution-supervisor-review-gate](../../specs/execution-supervisor-review-gate/spec.md), AC-0015 |
| Sequential execution follows dependencies; parallel writes need both safety checks | [wave-scheduled-supervisor](../../specs/wave-scheduled-supervisor/spec.md), AC1, AC4–AC5 |
| Each eligible parallel wave requires explicit human opt-in, otherwise stays sequential | [wave-scheduled-supervisor](../../specs/wave-scheduled-supervisor/spec.md), AC10 |

Autonomous ready-spec claiming, draining, stalled-spec reassignment, and mixed-host adapters are excluded claims, as recorded in the source journey's Delivery boundary.

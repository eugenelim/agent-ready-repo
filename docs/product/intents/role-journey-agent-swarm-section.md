# Role-journey guidance covers coordinated agent swarms

- **Slug:** `role-journey-agent-swarm-section`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim

## Outcome

The core role-journey guide explains coordinated headless CLI swarm patterns after the engineer-scales-to-swarm journey has an approved, implementable contract.

## Boundary

- Extend the Agent section of guides/core/explanation/role-journeys.md from single-agent execution to coordinated supervisor and executor pipelines.
- Atomic claiming, mixed concurrency, stale-agent recovery, adapter behavior, and other swarm mechanics remain owned by upstream INI-003 shaping and are not invented in the guide.

## Owner

- eugenelim, core journey-guide maintainer.


## Unresolved questions

- Promote engineer-scales-to-swarm from shaping only after its claiming, concurrency, recovery, and adapter boundaries are decided.

## Projection

- One documentation specification after the source journey reaches planned or shipped status.

## Opportunity

This intent absorbs role-journey-agent-swarm-section. The current role-journey guide covers headless single-agent execution and explicitly defers coordinated supervisor and executor pipelines.

## Assumptions

- The source journey remains the authority for swarm behavior.
- The public guide must not present shaping-stage mechanics as shipped capability.


## Source

- Mode: repo-origin
- Locator: docs/product/journeys/engineer-scales-to-swarm.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

## Readiness

Route: direct-light, one documentation session. The source of authority moves: the `engineer-scales-to-swarm` journey is still `status: shaping` and tied to `ini-003`, but a coordinated supervisor and executor pipeline now ships as the work-loop execution supervisor (specs `execution-supervisor-core`, `execution-supervisor-cutover`, `execution-supervisor-review-gate`, `execution-supervisor-attempt-security`, `wave-scheduled-supervisor`). Rewrite the Agent section of `guides/core/explanation/role-journeys.md` from those specs' acceptance criteria and remove the `(deferred: role-journey-agent-swarm-section)` marker. Agent-only proof: every claim in the new section cites a Shipped spec, and the guide link check passes. Re-describe the journey as superseded by those specs when it is next touched.

**Riskiest assumption:** the shipped execution-supervisor specs describe the coordinated supervisor and executor pipeline completely enough to write the guide section without inventing mechanics. Tested agent-only by requiring each claim in the section to cite an acceptance criterion of a Shipped execution-supervisor spec, checked by a link and grep pass.

## De-risk result

2026-11-05. Read the five execution-supervisor specs (all Shipped; 108 acceptance criteria in the four that use that format). They cover a supervisor that launches and reviews executor work, per-attempt security, retry claims, recovery and wave-scheduled concurrency. They do not describe agents that each atomically claim a ready spec, which is what the `engineer-scales-to-swarm` journey promised, and no spec uses the word "swarm". Verdict: partly holds. The guide section should describe the shipped supervised and wave-scheduled execution only, and must not present claim-based swarming as shipped. Not stamped; the Readiness route stays direct-light with this narrowed scope.

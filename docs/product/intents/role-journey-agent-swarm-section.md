# Role-journey guidance covers coordinated agent swarms

- **Status:** Draft
- **Level:** feature

## Outcome

The core role-journey guide explains coordinated headless CLI swarm patterns after the engineer-scales-to-swarm journey has an approved, implementable contract.

## Boundary

- Extend the Agent section of guides/core/explanation/role-journeys.md from single-agent execution to coordinated supervisor and executor pipelines.
- Atomic claiming, mixed concurrency, stale-agent recovery, adapter behavior, and other swarm mechanics remain owned by upstream INI-003 shaping and are not invented in the guide.

## Owner

- Core journey-guide and INI-003 swarm-journey maintainers; no individual owner is recorded.

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

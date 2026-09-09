# The capture-work compatibility bridge is removed safely

- **Status:** Draft
- **Level:** feature

## Outcome

The capture-work forwarding alias and legacy workspace reader are removed only after every RFC-0083 compatibility predicate is evidenced and freshly authorized.

## Boundary

- Remove the compatibility alias and legacy-reader branches, update adopter and maintainer guidance, regenerate projections, and ship the required major core release.
- Canonical artifacts, migration evidence, ledger-backed rollback records, and current work-intake semantics remain intact.

## Owner

- Core work-intake maintainers and the RFC-0083 Approver.

## Unresolved questions

- Evidence two qualifying minor releases, at least 90 elapsed days from the first write-new release, one-minor advance notice, current fixture/writer/guide/rollback audits, a separately approved removal specification, and fresh check-before-effect authorization.

## Projection

- One removal specification after all conjunctive AC14 predicates are current and satisfied.

## Opportunity

This intent absorbs capture-work-alias-removal. The initial compatibility review sets 2026-11-15 as the earliest date predicate; advance notice, the removal guide audit, a removal specification, and fresh authorization are also still unmet.

## Assumptions

- Every AC14 predicate is conjunctive; satisfying release count alone does not make removal dispatchable.
- The compatibility bridge remains installed until the later removal specification is separately approved and authorized.


## Source

- Mode: repo-origin
- Locator: docs/specs/work-intake-migration-docs/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

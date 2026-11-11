# The capture-work compatibility bridge is removed safely

- **Slug:** `capture-work-alias-removal`
- **Status:** Fulfilled
- **Accepted:** 2026-10-02 eugenelim, intent owner: reconstructed from commit 154216db7, which set this intent's `Status: Accepted`; no separate acceptance note was written at the time.
- **Fulfilled:** 2026-11-04 eugenelim: the one descendant, spec capture-work-alias-removal, is Shipped; Core 3.0.0 (PR #1525, commit 7e745dbf7, authorized by the RFC-0083 Approver over candidate 5c0cba0db per the spec's verification ledger T11) removed the `capture-work` skill and the ordinary legacy workspace reader, and `packs/core/.apm/skills/` holds no `capture-work` directory at Core 4.0.12; `test_capture_work_removal.py` pins the removal and passes; `docs/product/changelog.md` records `[core][3.0.0]`; the remaining `capture-work` guides (`guides/core/how-to/capture-work.md`, `migrate-capture-work.md`) are migration and rollback guidance for former users and teach no legacy invocation.
- **Level:** feature
- **Owner:** Core work-intake maintainers; RFC-0083 Approver for removal
- **Decomposed:** 2026-10-02 spec

## Outcome

The capture-work forwarding alias and legacy workspace reader are removed in Core 3.0.0 after every remaining RFC-0083 removal gate is evidenced and the exact release candidate receives fresh Approver authorization.

## Boundary

- Preserve the shipped migration specification as historical evidence; do not edit it to authorize new work.
- Use RFC-0083's 2026-10-02 Errata entry as the authority that removes the 90-day minimum and names Core 3.0.0; preserve the accepted RFC body.
- Remove the compatibility alias and legacy-reader branches, update adopter and maintainer guidance, regenerate projections, and ship the required major core release.
- Canonical artifacts, migration evidence, ledger-backed rollback records, and current work-intake semantics remain intact.

## Owner

- Core work-intake maintainers and the RFC-0083 Approver.

## Unresolved questions

None at intent altitude. The removal specification owns delivery questions, and RFC-0083 owns the remaining evidence and authorization gates.

## Projection

- One removal specification governed by RFC-0083's 2026-10-02 Errata entry and the remaining compatibility predicates.

## Opportunity

RFC-0083's 2026-10-02 Errata entry removes the 90-day minimum, treats the existing deprecation warning and migration guidance as sufficient notice, and names Core 3.0.0 as the removal release. The shipped migration specification and accepted RFC body remain unchanged historical records. The `capture-work` forwarding alias and legacy workspace reader stayed installed until the removal delivery satisfied the fixture, writer, guide, rollback, specification, and fresh-authorization gates; Core 3.0.0 then removed them. RFC-0099 leaves RFC-0083's compatibility-migration holding in force.

## Assumptions

- Every remaining AC14 predicate is conjunctive as modified by RFC-0083's 2026-10-02 Errata entry; satisfying release count or receiving removal sign-off alone does not make removal dispatchable.
- Shipped specifications and the accepted RFC body remain historical records; later authority changes are appended under the RFC's existing `## Errata` heading.
- The compatibility bridge stayed installed until the removal specification was separately approved and authorized.


## Source

- Mode: repo-origin
- Locator: docs/specs/work-intake-migration-docs/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin
- Role: historical evidence for the current compatibility gate; not the write target for a superseding decision.
- Governing decision: docs/rfc/0083-work-intake-and-artifact-routing.md (`## Errata` is the change route).
- Freshness checked: 2026-10-02 against RFC-0083's 2026-10-02 Errata entry, the initial compatibility review, Core pack manifest, release changelog, current alias and legacy-reader sources, and migration guide.

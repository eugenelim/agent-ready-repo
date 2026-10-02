# RFC-0088 browser delivery specifications

- **Slug:** `rfc0088-browser-delivery-specifications`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** capability:rfc0088-browser-follow-on-specs
- **Governed by:** [RFC-0088 follow-on release gates](../../rfc/0088-web-pilot-foundation.md)

## Outcome

RFC-0088 has three separately scoped, approval-ready delivery specifications
for foundation lifecycle, result and policy contracts, and the developer
workbench, with the required ADR and convention prerequisites recorded once.

## Opportunity

RFC-0088 defines three mandatory implementation specifications before its
foundation packs, behavior results or downloads, and repair tooling may ship.
Keeping those contracts in one feature preserves their shared architecture and
release-gate context without treating them as one implementation slice.

## Boundary

- Admits: authoring the two required ADRs, the browser-session lint convention, and the three RFC-named delivery specifications.
- Excludes: implementing any specification, changing RFC-0088's accepted architecture, or treating unresolved boundary observations as settled evidence.
- Excludes: combining the three delivery contracts. Each has a separate release gate and remains independently approvable and shippable.

## What this absorbs

### Broker deployment ADR

- Record the ADR that chooses the broker deployment unit: a library-owned broker plus bound Playwright CLI.

### Immutable adapter artifacts ADR

- Record the ADR that establishes immutable adapter artifacts with no remote adapter catalogue in v1.

### Browser-session lint convention

- Amend `docs/CONVENTIONS.md` with the `auth: browser-session` taxonomy and its pack-lint contract.

### Spec 1 — foundation delivery and lifecycle

Author the synthetic foundation and provider vertical specification. It covers
a pinned-container fixture, current-rail runtime delivery, browser lifecycle,
authorization-order fixtures, an install/admit/activate/upgrade/rollback/repair
gate, and a user guide for login handoff and recovery. It carries Q5's
per-destination credential-exposure declaration.

### Spec 2 — results, files, policy, and diagnostics

Author the generic results and policy contracts specification. It covers result
and artifact contracts, downloads, retention and quotas, diagnostics,
redaction, authorization, and network and filesystem policy.

### Spec 3 — developer workbench

Author the developer workbench specification for supervised probes, packaging
and provenance review, and the repair workflow.

## Assumptions

- **Riskiest assumption:** the shared browser-pilot architecture can be carried once while the three delivery contracts remain separately approvable and shippable.
- Each delivery contract remains separate because RFC-0088 assigns distinct release gates to the three slices.
- The exposure/privacy and signing/cost evidence children settle or explicitly bound any claim these specifications depend on before authoring begins.
- **Knowledge surface:** In-repository RFC-0088, its notes and review evidence, the two sibling evidence intents, and the prior specifications-only capability record.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0088-web-pilot-foundation.md
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

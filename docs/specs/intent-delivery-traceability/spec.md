# Spec: Intent delivery traceability

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0077, RFC-0103
- **Brief:** none
- **Discovery:** `intent:intent-delivery-traceability`
- **Contract:** none
- **Shape:** integration

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons`
> and `Assumptions` are working material.

## Outcome

Maintainers and delivery agents receive one route-qualified view of the delivery relations declared by feature intents, briefs, and specs. The same header-only result drives closure and traceability without flattening valid provenance into one parent or guessing through missing and contradictory mappings.

## What Changes

- A canonical typed relation resolver ships with each consuming Core skill as a byte-identical copy of one source, so every install route delivers it.
- `close-work` consumes the canonical relation snapshot for delivery descendants.
- `lint-traceability.py` consumes the same snapshot for feature-delivery edges while retaining its non-delivery graph checks.
- Core tests, eval evidence, architecture guidance, release history, versions, and self-hosted projections move with the runtime change.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | The two consumers need one stable typed result | Resolver source, its CLI help, and Core construction tests | Core pack | Unit fixtures, consumer parity fixtures, and projected-CLI invocation | Both consumers read the same result shape and no private delivery inversion remains reachable |
| Current architecture | Maintainers need the runtime owner and consumer boundary after the delivery record freezes | `docs/architecture/work-intake-and-artifact-routing.md` | Architecture maintainers | Whole-page review against source and tests | The page names the canonical owner, trust boundary, and consumers without copying the relation vocabulary |
| Release history | The Core pack gains adopter-visible traceability behavior | `docs/product/changelog.md` | Core release workflow | Changelog and pack-version gates | The release entry names the typed resolver and consumer convergence |

## Agent Rules

### Always do

- Derive delivery relations from canonical preamble fields and the feature intent's ratified `Decomposed:` route.
- Preserve relation type, route, and field basis in every returned relation.
- Confine every repository read through the repository file-safety contract and make both consumers fail closed when the canonical resolver cannot return a complete valid snapshot.

### Ask first

- Add or change a durable preamble field, relation type, or diagnostic code.
- Repair a missing mapping, reclassify a projection mismatch, or rewrite historical corpus ownership.
- Widen the resolver into status, coverage, closure-policy, navigation, tracker, or authoring ownership.

### Never do

- Choose one unqualified intent parent by field order when several valid bases exist.
- Leave a second active delivery-edge inversion or fallback parser in either consumer.
- Add a dependency, a second skill, or another top-level module boundary for this feature.
- Edit generated `.agents/`, `.claude/`, or `.agentbundle/` projections directly.

## Testing Strategy

- **TDD — relation semantics (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0019):** pure resolver fixtures compare the complete typed snapshot for positive, empty, missing, contradictory, provenance, and unsafe inputs because these rules are deterministic over repository headers.
- **TDD integration — consumer convergence (AC-0012, AC-0013, AC-0014, AC-0020):** integration fixtures run each real consumer against the same repository tree and compare its delivery subset with the canonical snapshot for equality; caller-inventory assertions prove the retired paths are unreachable; broken-spec fixtures prove close-work refuses every feature the spec could belong to.
- **Goal-based integration — installed runtime (AC-0015):** a clean repo-scope `agentbundle install` of Core runs each installed resolver copy where `agentbundle` cannot be imported and compares its JSON with the source function, because the adopter install route, not the self-host projection, is the behavior at risk.
- **TDD — security envelope (AC-0016, AC-0017, AC-0018):** boundary fixtures exercise corpus-entry refusals, every first-over-budget input, incomplete-snapshot rejection, and every user-visible diagnostic channel because fail-closed behavior and disclosure limits must hold before consumer policy runs.

## Acceptance Criteria

- [x] **AC-0001.** For each admitted direct target form—`intent:<slug>` and a repository-relative path to that intent—a feature with `Decomposed: <date> spec` and exactly one matching spec produces one `direct-delivery` relation whose route is `spec`, whose intent and spec identifiers are canonical, and whose basis names `Decomposed` and `Discovery`.
- [x] **AC-0002.** A `spec` route with no matching spec produces no delivery relation and reports `delivery-target-missing` for that feature intent.
- [x] **AC-0003.** A `spec` route with more than one matching spec produces no direct-delivery relation and reports `delivery-projection-mismatch` with every matching spec identifier in sorted order.
- [x] **AC-0004.** A feature with `Decomposed: <date> brief`, one matching brief, and child specs produces one `coordinated-delivery` relation per child spec; each relation carries the canonical intent, brief, and spec identifiers and names `Decomposed`, `Parent intent`, and `Brief` as its basis.
- [x] **AC-0005.** For each explicit empty route—`direct-light` and `closed-empty`—the feature classification is `no-durable-child`, its route remains visible, and it produces no missing-target diagnostic.
- [x] **AC-0006.** A spec participating in both direct and coordinated delivery returns both typed relations, including when the two relations name different feature intents, and returns no unqualified parent field.
- [x] **AC-0007.** A `Contract:` value or a `Discovery:` value that does not resolve to a feature intent remains a separately based `contextual-provenance` record and never becomes a feature-delivery relation.
- [x] **AC-0008.** Two distinct normalized targets contributing to the same delivery-relation type produce no relation of that type and report `delivery-relation-ambiguous` with both targets in sorted order.
- [x] **AC-0009.** A malformed target contributing to a delivery relation produces no relation of that type and reports `delivery-reference-malformed` rather than being ignored or selected by order.
- [x] **AC-0010.** An absolute or parent-traversing relation reference is not opened, produces no relation, and reports `delivery-reference-unsafe`. A relation reference is any `Brief:` or `Parent intent:` value, or a `Discovery:` value that is intent-shaped (`intent:<slug>` or a path naming `product/intents/`). A `Discovery:` value that is not intent-shaped stays `contextual-provenance` under AC-0007 whatever its form, and an absolute or parent-traversing one is emitted without its target.
- [x] **AC-0011.** Changing headings, field-shaped text, or references below the canonical preamble of an otherwise identical artifact leaves the relation snapshot byte-for-byte unchanged.
- [x] **AC-0012.** For every direct, coordinated, explicit-empty, dual-provenance, missing-direct, missing-brief, direct-projection-mismatch, and brief-projection-mismatch fixture, `close-work` derives its delivery descendants from the canonical snapshot and preserves its existing status, freshness, and closure verdicts.
- [x] **AC-0013.** For the same fixture set, `lint-traceability.py` derives feature-delivery edges and delivery diagnostics from the canonical snapshot while its non-delivery producer, component, dangling-target, cycle, and orphan checks keep their existing results.
- [x] **AC-0014.** A caller inventory finds exactly one source implementation that parses and inverts feature delivery relations; each consumer runs a byte-identical copy of that source, pinned to it by a parity test, and neither consumer contains a reachable fallback for those relations.
- [x] **AC-0015.** A clean `agentbundle install --pack core --scope repo` places the resolver and its confinement helper beside each consumer's scripts; invoking either installed copy with the current Python interpreter, with `agentbundle` not importable, returns valid JSON identical to the source resolver's snapshot for the same confined fixture.
- [x] **AC-0016.** Every artifact-root enumeration and preamble read is canonicalized beneath the repository root and uses the repository file-safety contract. A symlinked, hard-linked, non-regular, inaccessible, oversized, or identity-changing corpus entry makes the snapshot incomplete, is never opened as artifact content, and contributes no relation, classification, diagnostic payload, or provenance. This corpus refusal precedes relation-level validation when a relation names that entry: `delivery-reference-unsafe` is absent and the incomplete result is the only outcome.
- [x] **AC-0017.** Across the union of admitted intent, brief, and spec roots, the resolver refuses before processing the first input that would exceed 50,000 enumerated entries, 10,000 regular artifact files, depth 8 below an artifact root, 1,000,000 bytes for one artifact, 67,108,864 aggregate artifact bytes, or 16,777,216 serialized JSON bytes. It returns an incomplete snapshot with `delivery-resource-limit` naming only the breached limit and bounded repository-relative root; both consumers reject that snapshot without a fallback.
- [x] **AC-0018.** Resolver JSON and every close-work or traceability diagnostic expose only stable diagnostic codes plus bounded repository-relative context. They are strict and deterministic and never expose captured stderr verbatim, a stack trace, a secret, an absolute host path, or raw malformed or unsafe relation content; resolver invocation failure yields `delivery-resolver-unavailable` from each consumer without a fallback.
- [x] **AC-0019.** A `brief` route with no matching coordinating brief produces no coordinated-delivery relation and reports `delivery-target-missing` for that feature intent. A `brief` route with more than one matching coordinating brief produces no coordinated-delivery relation and reports `delivery-projection-mismatch` with every matching brief identifier in sorted order.
- [x] **AC-0020.** When a spec or brief carries a delivery diagnostic of its own, `close-work` refuses closure of every feature that artifact could belong to and names the stable code, instead of dropping the artifact from the descendant set. The refusal set is fixed per broken field: an ambiguous spec `Discovery:` refuses each named target that is a feature intent, or every `spec`-route feature when none is; a malformed, unsafe, or missing-target spec `Discovery:` refuses every `spec`-route feature; an ambiguous spec `Brief:` refuses the feature named by each named brief's `Parent intent:`, or every `brief`-route feature when none resolves; a malformed, unsafe, or missing-target spec `Brief:` refuses every `brief`-route feature; and any brief-subject delivery diagnostic refuses every `brief`-route feature.

## Follow-ons

None.

## Assumptions

None.

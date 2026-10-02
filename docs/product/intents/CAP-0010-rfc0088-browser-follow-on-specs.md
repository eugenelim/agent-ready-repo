# RFC-0088 browser pilot readiness

- **Slug:** `rfc0088-browser-follow-on-specs`
- **Status:** Draft
- **Level:** capability
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Parent intent:** none
- **Decomposed:** 2026-10-02 children
- **Governed by:** [RFC-0088 follow-on release gates](../../rfc/0088-web-pilot-foundation.md)

## Outcome

- **Steerable input:** The share of RFC-0088 release-gating claims that have either boundary-matched evidence or a separately scoped feature intent with a named unblock condition.
- **Lagging outcome:** The browser pilot can move from an accepted architecture decision into delivery with its exposure, privacy, signing, operating-cost, and three specification gates all explicit and owned.
- **Guardrail:** No unresolved observation is promoted to a security, privacy, identity, or operating-cost claim, and no implementation begins by treating an accepted RFC as proof that its release gates have been satisfied.

## Opportunity

RFC-0088 settles the browser-pilot architecture but leaves two evidence families
and three mandatory delivery specifications as separately logged follow-ons.
Without one capability parent, a reader cannot tell which unresolved evidence
can reshape the delivery contracts or whether the pilot is ready to enter them.

## Boundary

This capability owns readiness to implement the RFC-0088 browser pilot. It
includes evidence needed to keep the RFC's exposure, privacy, signing identity,
and destination-cost claims honest, plus the ADR, convention, and specification
work required by its follow-on release gates.

It does not implement the foundation, provider behaviors, result release, or
developer workbench. Those remain blocked until the corresponding delivery
specification is authored and approved. It also does not broaden the RFC's
software-delivery-only domain boundary or its read-only behavior posture.

Native-addon confinement remains owned by the existing
[`rfc0088-native-addon-confinement-bypass`](../../specs/rfc0088-round15-reference-consumer/notes/rfc0088-native-addon-confinement-bypass.md)
defect and blocks any supported `--allow-addons` configuration; it is not a
child of this capability.

## Assumptions

- **Riskiest assumption:** the accepted RFC remains the architectural authority; these children may supply evidence or delivery contracts but do not silently amend its decisions.
- The two observation features can change specification wording or release gates, so they precede the specification-authoring child.
- **Knowledge surface:** In-repository RFC-0088, its review notes and spikes, the round-12 residuals spec, workspace registrations, and Git-history lineage.

## Decomposition

Implementation order closes boundary evidence before authoring the contracts
that rely on it.

1. **Exposure and privacy evidence** — [FEAT-0026: RFC-0088 exposure and privacy anchoring](FEAT-0026-rfc0088-exposure-and-privacy-anchoring.md)
2. **Signing and operating-cost evidence** — [FEAT-0027: RFC-0088 signing and cost observations](FEAT-0027-rfc0088-signing-and-cost-observations.md)
3. **Delivery contracts** — [RFC-0088 browser delivery specifications](FEAT-0028-rfc0088-browser-delivery-specifications.md)

## Source

- Mode: repo-origin
- Locator: docs/rfc/0088-web-pilot-foundation.md
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

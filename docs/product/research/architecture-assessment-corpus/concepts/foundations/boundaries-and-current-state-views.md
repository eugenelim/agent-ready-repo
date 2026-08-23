---
type: architecture-corpus-source-packet
concept_path: concepts/foundations/boundaries-and-current-state-views.md
confidence: high
lifecycle: living
review_by: 2027-08-21
---
# Boundaries and current-state views — source packet

## Material claims

| Claim | Synthesis | Sources |
| --- | --- | --- |
| BV-1 | Architecture descriptions select views for stakeholder concerns; one diagram cannot represent every material structure. | S1, S2, S3 |
| BV-2 | Source, runtime, data, deployment, and ownership boundaries may differ and should be reconciled. | S1, S3, S4 |
| BV-3 | A conceptual model should be corrected before detailed assessment effort. | S1, S2, S4 |

## Sources

- S1: [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html) — view and viewpoint model.
- S2: [SEI ATAM collection](https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/) — architecture presentation before scenario analysis.
- S3: [Google Cloud architecture documentation guidance](https://docs.cloud.google.com/architecture/framework#document_your_architecture) — current architecture documentation.
- S4: [Azure architecture styles](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/) — structural styles and trade-offs.

## Counter-evidence and downgrade factors

View labels are not universal, and a small repository may need fewer views.
Deployment files can describe inactive environments; code ownership metadata can
lag actual responsibility.

## Known unknowns

Whether a separate saved system map improves adopter outcomes remains a dogfood question.

## Licensing and reuse

Citations plus original synthesis only; source terms remain with publishers.
Packet license: Apache-2.0 OR MIT.

## Freshness

Review annually; view principles are durable but provider examples can change.

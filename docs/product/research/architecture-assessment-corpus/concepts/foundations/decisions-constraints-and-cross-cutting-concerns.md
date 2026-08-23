---
type: architecture-corpus-source-packet
concept_path: concepts/foundations/decisions-constraints-and-cross-cutting-concerns.md
confidence: high
lifecycle: living
review_by: 2027-08-21
---
# Decisions, constraints, and cross-cutting concerns — source packet

## Material claims

| Claim | Synthesis | Sources |
| --- | --- | --- |
| DC-1 | Architecture decisions and constraints should be distinguished from accidental implementation structure. | S1, S2, S3 |
| DC-2 | Cross-cutting concerns require consistent enforcement across execution boundaries. | S2, S3, S4 |
| DC-3 | Declared decisions must be checked against current implementation and rationale applicability. | S1, S2, S4 |

## Sources

- S1: [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html) — architecture rationale, concerns, and decisions.
- S2: [SEI ATAM collection](https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/) — architectural approaches and risks.
- S3: [AWS Well-Architected pillars](https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html) — cross-cutting workload concerns.
- S4: [Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework) — design documentation and operational consistency.

## Counter-evidence and downgrade factors

Centralizing a concern is not always preferable; bounded autonomy may be the
deliberate architecture. Decision records can be stale or describe only a target state.

## Known unknowns

Actual policy ownership and exception authority require enterprise context.

## Licensing and reuse

Original synthesis and citations only. Packet license: Apache-2.0 OR MIT.

## Freshness

Review annually; confirm any provider-specific examples at assessment time.

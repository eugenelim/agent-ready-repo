---
type: architecture-corpus-source-packet
concept_path: concepts/foundations/tradeoffs-sensitivity-and-evolution.md
confidence: high
lifecycle: living
review_by: 2027-08-21
---
# Trade-offs, sensitivity, and evolution — source packet

## Material claims

| Claim | Synthesis | Sources |
| --- | --- | --- |
| TS-1 | Architectural mechanisms should be evaluated against competing quality scenarios and business drivers. | S1, S2, S3 |
| TS-2 | Sensitivity points and trigger thresholds support staged decisions under uncertainty. | S1, S3, S4 |
| TS-3 | Reversible experiments can defer expensive irreversible commitments. | S2, S3, S4 |

## Sources

- S1: [SEI ATAM collection](https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/) — trade-off and sensitivity analysis.
- S2: [SEI Architecture Options Workshop](https://www.sei.cmu.edu/library/creating-software-modernization-roadmaps-the-architecture-options-workshop/) — option and roadmap comparison.
- S3: [Google Cloud design for change](https://docs.cloud.google.com/architecture/framework#design_for_change) — evolution and change posture.
- S4: [Azure mission-critical design principles](https://learn.microsoft.com/en-us/azure/well-architected/mission-critical/mission-critical-design-principles) — design choices and validation.

## Counter-evidence and downgrade factors

Deferring a choice can also accumulate risk; some compliance, data, or provider
decisions are not cheaply reversible. Thresholds based on forecasts need explicit uncertainty.

## Known unknowns

The user's actual risk tolerance and option cost require local evidence.

## Licensing and reuse

Original synthesis and citations only. Packet license: Apache-2.0 OR MIT.

## Freshness

Review annually and whenever provider-specific limits are referenced downstream.

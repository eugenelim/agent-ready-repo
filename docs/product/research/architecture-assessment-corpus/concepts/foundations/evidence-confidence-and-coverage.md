---
type: architecture-corpus-source-packet
concept_path: concepts/foundations/evidence-confidence-and-coverage.md
confidence: high
lifecycle: living
review_by: 2027-08-21
---
# Evidence, confidence, and coverage — source packet

## Material claims

| Claim | Synthesis | Sources |
| --- | --- | --- |
| EC-1 | Architecture claims must be scoped to stakeholder concerns and selected evidence rather than presented as universal coverage. | S1, S2, S3 |
| EC-2 | Scenario and exercised evidence supports stronger decisions than labels, inventory, or intent alone. | S2, S3, S4 |
| EC-3 | Missing evidence should lower confidence and identify validation work, not manufacture a defect. | S1, S2, S4 |

## Sources

- S1: [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html) — architecture descriptions, stakeholders, concerns, and viewpoints.
- S2: [SEI ATAM collection](https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/) — evidence-led scenario evaluation and trade-off analysis.
- S3: [Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework) — evidence, documentation, and workload-context guidance.
- S4: [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html) — workload review and continuous improvement.

## Counter-evidence and downgrade factors

Evidence tiers are a synthesis, not an ISO vocabulary. Runtime observations may
be unrepresentative; tests can be mocked or stale; repository evidence cannot
reconstruct unrecorded production behavior.

## Known unknowns

The right evidence breadth and confidence labels depend on decision consequence
and assessment budget.

## Licensing and reuse

Only citations and original paraphrase are retained. Source texts remain under
their publishers' terms; the synthesized packet is Apache-2.0 OR MIT.

## Freshness

Review annually and when a cited framework changes its evidence model.

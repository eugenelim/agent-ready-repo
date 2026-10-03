## Main-loop result
**1. [major] 1: Worker document bytes lack a prompt-authority delimiter criterion.** `docs/specs/plan-evolution-experiments/spec.md:354`. The cited document-isolation rule freezes non-secret packets and tells workers not to inspect other material, but it does not require every worker-visible document/source body to be delimited and labelled as untrusted data with provenance; the current source-body rule covers retrieved article/comment/resource bodies only, while T13/T14 send synthetic or repository-public subject bytes to Sol, Sonnet, and Opus, so instruction-shaped packet text can still compete with controller authority before output screening. Proposed mechanism: adequate. Fix: add a general acceptance criterion and T13/T14 checks requiring every worker-visible document/source body to be framed as untrusted data with provenance, and to be unable to alter run definitions, tool use, paths, scoring, hidden-material handling, or the output schema.

## Refuted audit
None.

## Indeterminate audit
None.

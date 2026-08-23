---
type: architecture-corpus-source-packet
concept_path: concepts/workload-lenses/transactional-request-response.md
confidence: high
lifecycle: living
review_by: 2027-08-21
---
# Transactional request/response workloads — source packet

## Material claims

| Claim | Synthesis | Sources |
| --- | --- | --- |
| WL-T1 | Synchronous paths require explicit identity, validation, transaction, external-effect, timeout/cancellation, idempotency, response, and retry semantics. | S1, S2, S3 |
| WL-T1b | Repository structure and provider labels can trigger this lens but cannot prove runtime, policy, isolation, or recovery behavior without representative path evidence. | S1, S2, S3 |

## Sources

- S1: [Primary source 1](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)
- S2: [Independent source 2](https://learn.microsoft.com/en-us/azure/well-architected/what-is-well-architected-framework)
- S3: [Independent source 3](https://docs.cloud.google.com/architecture/framework)

## Counter-evidence and downgrade factors

Provider guidance may favor its own service model; agentic practice and threat
taxonomies are evolving. Actual identity, workload, policy, data, cost, and
operational outcomes require target and enterprise evidence.

## Known unknowns

Adapter capabilities and representative deep-mode evidence vary by environment.

## Licensing and reuse

Original synthesis and citations only. Packet license: Apache-2.0 OR MIT.

## Freshness

Review at least annually; re-ground current provider and agentic guidance when used.

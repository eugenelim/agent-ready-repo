---
type: architecture-corpus-source-packet
concept_path: concepts/workload-lenses/knowledge-search-and-retrieval.md
confidence: high
lifecycle: living
review_by: 2027-08-21
---
# Knowledge, search, and retrieval workloads — source packet

## Material claims

| Claim | Synthesis | Sources |
| --- | --- | --- |
| WL-K1 | Knowledge results must retain tenant/corpus/ACL, source/version, freshness, deletion/supersession, method/score, provenance, and trust through retrieval and generation. | S1, S2, S3 |
| WL-K1b | Repository structure and provider labels can trigger this lens but cannot prove runtime, policy, isolation, or recovery behavior without representative path evidence. | S1, S2, S3 |

## Sources

- S1: [Primary source 1](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence)
- S2: [Independent source 2](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture-generative-ai/gen-ai-agents.html)
- S3: [Independent source 3](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/secure-multitenant-rag)

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

---
type: architecture-corpus-source-packet
concept_path: concepts/workload-lenses/genai-agentic/knowledge-provenance-and-isolation.md
confidence: high
lifecycle: living
review_by: 2027-08-21
---
# Agent knowledge provenance and isolation — source packet

## Material claims

| Claim | Synthesis | Sources |
| --- | --- | --- |
| WL-A4 | Retrieved, tool-produced, and remembered context remains untrusted data; authorization, provenance, trust, policy precedence, memory gates, and lifecycle propagation must survive transformation. | S1, S2, S3 |
| WL-A4b | Repository structure and provider labels can trigger this lens but cannot prove runtime, policy, isolation, or recovery behavior without representative path evidence. | S1, S2, S3 |

## Sources

- S1: [Primary source 1](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/)
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

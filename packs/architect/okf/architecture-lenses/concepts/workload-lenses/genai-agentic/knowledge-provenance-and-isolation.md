---
title: "Agent knowledge provenance and isolation"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - WL-A4
  - WL-A4b
---
# Agent knowledge provenance and isolation

## Scope and routing signals

Use when agents ingest, retrieve, remember, summarize, cite, or act on documents, web content, tool output, conversation history, memory, or vector-store context.

## Decisions and minimum evidence

Supports whether knowledge is authorized, attributable, current, isolated, and treated as data rather than instructions. Minimum evidence covers tenant/corpus/ACL, source/version, ingestion/effective time, trust, provenance through retrieval/rerank/summarization, cache/index scope, deletion/revocation, instruction isolation, memory write/read gates, and policy precedence.

## Architectural questions

- Can retrieved or persisted content silently alter system policy, tool authority, or later decisions?
- Does provenance and ACL scope survive every transformation and generated output?
- How do correction, revocation, deletion, and trust changes propagate?

## Mechanisms and trade-offs

Instruction/data delimiters, provenance-carrying result contracts, scoped retrieval/index/cache keys, trust labels, memory quarantine, policy precedence, citations, versioning, and deletion propagation trade recall, personalization, latency, and complexity.

## Evidence and counter-evidence

Seek ingestion/retrieval contracts, prompt construction, memory writes/reads, metadata filters, caches, traces, citations, deletion workflows, and adversarial tests. Counter-evidence includes post-filtering or provenance discarded during summarization.

## Failure modes and false positives

Retrieved relevance is not authority; citation presence does not prove current permitted source; Oracle or primary-store policy does not protect indexes, caches, memory, or prompt context.

## Confirmation scenarios

Use overlapping tenants, revoke ACL, delete/supersede a source, inject instructions into retrieved/tool content, persist/reload memory, rerank/summarize, and verify policy and provenance remain intact.

## Related concepts and escalation

Pair with knowledge retrieval workload, enterprise source confidence, tool authorization, security/privacy, and evaluation.

## Provenance and lifecycle

Synthesized from NIST GenAI profile, OWASP agentic memory/context risks, AWS secure RAG, and Azure multitenant RAG guidance. Confidence: high; review at least annually.

Research claim trace: `WL-A4`, `WL-A4b`; see the living source packet with the same concept path.

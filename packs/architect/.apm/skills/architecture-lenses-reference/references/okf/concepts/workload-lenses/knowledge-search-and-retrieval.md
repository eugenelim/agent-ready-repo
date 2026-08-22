---
title: "Knowledge, search, and retrieval workloads"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "agentbundle-okf/v1"
research_claims:
  - WL-K1
  - WL-K1b
---
# Knowledge, search, and retrieval workloads

## Scope and routing signals

Use when ingestion, parsing, chunking, metadata, indexing, search/vector retrieval, reranking, caches, summarization, or citation grounds system answers.

## Decisions and minimum evidence

Supports isolation, provenance, freshness, deletion, trust, and quality decisions. Minimum evidence covers corpus/tenant/ACL scope, source and version, ingestion/effective time, chunk/metadata lineage, embedding/index version, retrieval method/score, reranking, caches, supersession/deletion, citation, and trust classification.

## Architectural questions

- Can every result prove tenant/corpus scope, ACL decision, source/version, freshness, and deletion state?
- How do revocation, correction, and deletion propagate to indexes, caches, and generated artifacts?
- Can retrieved instructions override policy or tool decisions?

## Mechanisms and trade-offs

Metadata filters, tenant-scoped indexes/caches, provenance-carrying result contracts, versioned embeddings, deletion tombstones, reranking, citations, and trust isolation trade recall, latency, cost, freshness, and complexity.

## Evidence and counter-evidence

Seek ingestion/index pipelines, metadata schemas, access filters, cache keys, retrieval/rerank code, trace records, deletion jobs, evaluation sets, and isolation tests. Counter-evidence includes post-filtering and lost provenance after summarization.

## Failure modes and false positives

A database row policy does not protect vector indexes or caches; citations can point to stale/superseded content; high retrieval score is not authority or truth.

## Confirmation scenarios

Use two tenants with overlapping content; revoke ACL, delete/supersede a source, change embedding version, inject malicious instructions, rerank/summarize, and verify provenance survives.

## Related concepts and escalation

Pair with data governance, security/privacy, agentic knowledge isolation, evaluation, and enterprise source confidence.

## Provenance and lifecycle

Synthesized from NIST GenAI profile, AWS secure RAG guidance, and Azure secure multitenant RAG architecture. Confidence: high; review at least annually.

Research claim trace: `WL-K1`, `WL-K1b`; see the living source packet with the same concept path.

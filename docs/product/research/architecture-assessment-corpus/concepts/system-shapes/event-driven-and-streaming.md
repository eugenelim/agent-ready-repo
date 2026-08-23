---
type: architecture-corpus-source-packet
concept_path: concepts/system-shapes/event-driven-and-streaming.md
confidence: moderate
lifecycle: living
review_by: 2027-08-21
---
# Event-driven and streaming systems — source packet

## Material claims

| Claim | Synthesis | Sources |
| --- | --- | --- |
| SS-E1 | Event architecture requires explicit semantics, schema, ordering/partitioning, delivery, idempotency, replay, backpressure, retention, state, and reconciliation. | S1, S2, S3 |
| SS-E1b | A shape label is a routing hypothesis; representative runtime, data, delivery, and failure paths must confirm its material boundaries. | S1, S2, S3 |

## Sources

- S1: [Azure architecture styles](https://learn.microsoft.com/en-us/azure/architecture/guide/architecture-styles/)
- S2: [ISO/IEC/IEEE 42010:2022](https://www.iso.org/standard/74393.html)
- S3: [Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework)

## Counter-evidence and downgrade factors

Architecture styles overlap, repositories can contain several systems, and
provider examples can blur logical, deployment, and ownership boundaries.
The shape must not predetermine quality findings.

## Known unknowns

Language-specific semantic depth depends on available native tooling.

## Licensing and reuse

Original synthesis and citations only. Packet license: Apache-2.0 OR MIT.

## Freshness

Review annually; validate platform behavior and provider contracts at use time.

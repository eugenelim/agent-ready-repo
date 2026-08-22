---
type: architecture-corpus-source-packet
concept_path: concepts/quality-lenses/operability-observability-and-supportability.md
confidence: high
lifecycle: living
review_by: 2027-08-21
---
# Operability, observability, and supportability — source packet

## Material claims

| Claim | Synthesis | Sources |
| --- | --- | --- |
| QL-O1 | Operability depends on actionable correlated signals, ownership, safe control actions, deployment/rollback, and diagnosis under representative failure. | S1, S2, S3 |
| QL-O1b | Structural proxies focus investigation but do not establish the quality outcome without scenario and exercised evidence. | S1, S2, S3 |

## Sources

- S1: [AWS Well-Architected Framework](https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html)
- S2: [Azure Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/what-is-well-architected-framework)
- S3: [Google Cloud Well-Architected Framework](https://docs.cloud.google.com/architecture/framework)

## Counter-evidence and downgrade factors

The frameworks organize concerns differently and provider guidance can favor its
own service model. Actual targets, tolerance, workload, cost, obligations, and
operational history are organization-specific.

## Known unknowns

Scenario priority and adequacy thresholds require local stakeholder evidence.

## Licensing and reuse

Original cross-framework synthesis and citations only. Packet license:
Apache-2.0 OR MIT; source terms remain with publishers.

## Freshness

Review annually and ground current provider contracts when they become load-bearing.

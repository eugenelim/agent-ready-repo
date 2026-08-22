---
type: architecture-corpus-source-packet
concept_path: concepts/operating-model-patterns/delivery-runtime-and-development-patterns.md
confidence: high
lifecycle: living
review_by: 2027-08-21
---
# Delivery, runtime, and development patterns — source packet

## Material claims

| Claim | Synthesis | Sources |
| --- | --- | --- |
| DD-1 | Change safety depends on the end-to-end path from source through artifact, deployment, observation, and rollback, including ownership and environment alignment. | S1, S2, S3 |
| DD-1b | Repository proxies can focus investigation but cannot establish the operational, organizational, or business facts required by this decision. | S1, S2, S3 |

## Sources

- S1: [Primary or framework source 1](https://dora.dev/capabilities/loosely-coupled-teams/)
- S2: [Independent source 2](https://docs.aws.amazon.com/wellarchitected/latest/framework/ops_evolve_ops_process_cont_imp.html)
- S3: [Independent source 3](https://docs.cloud.google.com/architecture/framework#design_for_change)

## Counter-evidence and downgrade factors

The intent taxonomy is a practitioner synthesis, not an external standard.
Mixed prompts can carry secondary intents, and local thresholds, costs, skills,
ownership, and risk tolerance require authorized organization evidence.

## Known unknowns

Label comprehension and routing accuracy require cross-repository dogfood.

## Licensing and reuse

Original synthesis and citations only; source terms remain with publishers.
Packet license: Apache-2.0 OR MIT.

## Freshness

Review annually and before relying on provider- or portfolio-specific guidance.

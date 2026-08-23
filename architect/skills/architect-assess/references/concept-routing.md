# Deterministic concept routing

Enter through `../../architecture-lenses-reference/references/okf/index.md`.
Paths below are relative to its `concepts/` directory.

## Base set

Every assessment loads:

- `foundations/evidence-confidence-and-coverage.md`
- `foundations/boundaries-and-current-state-views.md`
- `foundations/quality-attribute-scenarios.md`
- `foundations/tradeoffs-sensitivity-and-evolution.md`
- `foundations/decisions-constraints-and-cross-cutting-concerns.md`

## Intent triggers

Select exactly one primary intent and any explicitly named secondary intent:

| Trigger | Concept |
| --- | --- |
| explain, baseline, understand | `assessment-intents/baseline-and-understanding.md` |
| assure, harden, risk, readiness, compliance | `assessment-intents/hardening-and-risk-reduction.md` |
| optimize, performance, cost, delivery | `assessment-intents/optimize-current-outcomes.md` |
| scale, grow, future load/team/product | `assessment-intents/growth-and-scale-readiness.md` |
| modernize, rewrite, replatform, transform | `assessment-intents/transformation-and-modernization.md` |
| retain, invest, consolidate, acquire, replace, retire, diligence | `assessment-intents/rationalization-disposition-and-due-diligence.md` |

## Shape and workload triggers

Load only observed matches from the two generated indexes. Shape is not inferred
from folder names alone.

- library/package/SDK/CLI → `system-shapes/library-sdk-and-cli.md`
- in-process layers or modular monolith →
  `system-shapes/layered-and-modular-application.md`
- separate client and server deployables → `system-shapes/client-server.md`
- multiple networked services → `system-shapes/distributed-services.md`
- brokers, streams, event contracts → `system-shapes/event-driven-and-streaming.md`
- monorepo, platform, IaC/control plane →
  `system-shapes/monorepo-platform-and-infrastructure.md`
- request/response → `workload-lenses/transactional-request-response.md`
- jobs/schedulers/workers → `workload-lenses/background-batch-and-scheduled-work.md`
- data pipelines/analytics/ML → `workload-lenses/data-analytics-and-ml.md`
- search/retrieval/indexes → `workload-lenses/knowledge-search-and-retrieval.md`
- managed ephemeral/event execution → `workload-lenses/serverless.md`
- LLM on path → agentic `model-access-and-policy.md`; durable runs →
  `durable-run-state-and-recovery.md`; tool action →
  `tool-authorization-and-credentials.md`; retrieval/memory →
  `knowledge-provenance-and-isolation.md`; any production GenAI path →
  `evaluation-and-observability.md`.

Load the relevant quality concepts when a charter, evidence signal, or scenario
triggers them. Record every considered path as
selected, skipped, unavailable, stale, or not applicable.
Never load all branches merely to be thorough.

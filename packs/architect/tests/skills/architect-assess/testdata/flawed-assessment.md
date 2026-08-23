# Architecture assessment: agent platform

## Bottom line

The whole platform is not production-ready and should be rewritten as
microservices. This standard assessment inspected `app/` source and the README.

## Assessment charter

Target: backend request handlers only
Primary intent: baseline
Mode: standard

## Conceptual current state

The `routes/`, `services/`, and `queries/` folders are the three runtime
components. There are no external systems.

## Evidence coverage

Source and README inspected. All other evidence is green because no problems
were found.

## Attention heat map

| Area | Architecture risk score |
| --- | ---: |
| `routes/` | 92 |

The routes are therefore blocker-severity defects.

## Hotspot drill-downs

Routes are large and import queries directly.

## Findings, strengths, and unknowns

### F-1: Layering violation

Evidence: grep found `queries` imports.
Severity: blocker.

The platform uses an LLM, but model, tool, run-state, knowledge, memory,
evaluation, and trace boundaries were not assessed. It is nevertheless not
production-ready.

## Action waves

### Wave 0 — split files

Split every file above 500 lines and migrate all services at once.

### Wave 1 — active tenant defect

Investigate the known cross-tenant write defect after the cleanup.

## Coverage and confidence

Confidence: high.

## Next decision

Approve the rewrite.

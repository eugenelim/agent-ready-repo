---
name: define-slo
description: "Use to author a Service Level Objective (SLO) document for a service in the release-engineering pack. Produces an OpenSLO v1 YAML file committed to `slos/<service>.yaml`, with an error_budget_policy block, that the release-loop's PRR gate reads to resolve the error-budget status field. Triggers on \"define SLOs for this service\", \"author an SLO\", \"set up error budget tracking\", \"create a reliability target\", \"we need an SLO document\", \"the PRR shows error-budget: not-defined\". Do NOT use to generate Prometheus recording rules or alerting rules (toolchain work — the adopter's pipeline does that), to set up ongoing alerting backend routing, or to run the release loop itself."
---

# Skill: define-slo

This skill produces an **OpenSLO v1 YAML document** — the SLO artifact that the
`release-loop`'s release-readiness gate reads to populate the PRR `error-budget` field.
Without this artifact the PRR records `error-budget: not-defined` (visible to the human
but not a hard block). With it, the gate resolves to one of four states based on
live budget consumption at gate-check time.

The skill lives in the `release-engineering` pack because SLO authoring is the SRE/reliability
discipline — the same seat `release-loop` occupies. It produces a static declaration;
ongoing monitoring, alerting, and on-call ownership belong to the future operate/incident loop.

## When to invoke

- After a new service ships and the PRR shows `error-budget: not-defined`.
- When refining an existing service's reliability targets for the first time.
- When the `release-loop` gate-check reports `error-budget: query-failed` and the
  SLO document has stale metric queries that need updating.
- Do **not** invoke to generate Prometheus rules — produce the OpenSLO YAML and let the
  adopter's toolchain (Sloth, Pyrra, etc.) translate it.

## SLO artifact format — OpenSLO v1

The canonical format is **OpenSLO v1** (`apiVersion: openslo/v1`). Rationale: cross-vendor
support (Nobl9, Dynatrace, Sloth accepts it natively), harness-neutral YAML structure,
Kubernetes-aligned `kind` + `metadata` convention independent of any specific backend.

**Commit the SLO document to `slos/<service>.yaml`** in the repository root. This path
is the convention the `release-loop` gate uses to locate the artifact at gate-check time.

### Minimum required fields

The PRR gate's resolution logic requires these fields — the document is not actionable
without them:

| Field | Required | Purpose |
|---|---|---|
| `apiVersion: openslo/v1` | ✓ | Format identification |
| `kind: SLO` | ✓ | Object type |
| `metadata.name` | ✓ | RFC1123 identifier (e.g. `payments-availability`) |
| `spec.service` | ✓ | The service this SLO covers |
| `spec.budgetingMethod` | ✓ | `Occurrences` (event-based, default) or `Timeslices` |
| `spec.timeWindow[].count + unit` | ✓ | Measurement period (default: 30 days rolling) |
| `spec.indicator.ratioMetric.good.metricSource` | ✓ | Good-event query |
| `spec.indicator.ratioMetric.total.metricSource` | ✓ | Total-event query |
| `spec.objectives[0].target` | ✓ | Reliability percentage as decimal (e.g. `0.999`) |
| `error_budget_policy` block | ✓ | Gate resolution thresholds (see below) |

### OpenSLO v1 template

```yaml
apiVersion: openslo/v1
kind: SLO
metadata:
  name: <service>-availability        # RFC1123; e.g. payments-availability
  displayName: "<Service> Availability"
spec:
  service: <service>
  description: "HTTP availability SLO for the <service> API surface."
  budgetingMethod: Occurrences         # Occurrences | Timeslices
  timeWindow:
    - count: 30
      unit: Day
      isRolling: true                  # rolling 30-day window (default)
  indicator:
    apiVersion: openslo/v1
    kind: SLI
    metadata:
      name: <service>-availability-sli
    spec:
      ratioMetric:
        counter: true
        good:
          metricSource:
            type: Prometheus           # TODO: set to your backend type
            spec:
              query: >
                sum(rate(http_requests_total{job="<service>",code!~"5.."}[{{.window}}]))
                # TODO: replace with your service's actual metric query
        total:
          metricSource:
            type: Prometheus
            spec:
              query: >
                sum(rate(http_requests_total{job="<service>"}[{{.window}}]))
                # TODO: replace with your service's actual metric query
  objectives:
    - target: 0.999                    # 99.9% — set to your reliability target
      displayName: "99.9% availability"
```

The `metricSource.type` and query expressions are **adopter-provided** — they are backend-
specific (Prometheus, Datadog, CloudWatch, Dynatrace). The skill scaffolds the template;
the adopter fills in the actual queries for their observability stack.

## The `error_budget_policy` block

This block is a companion to the OpenSLO document (either appended as a non-spec extension
field, or committed as a sidecar `slos/<service>-policy.yaml`). The release-loop gate reads
it at gate-check time to determine which threshold applies.

```yaml
error_budget_policy:
  trailing_window: 30d                 # must match spec.timeWindow
  halt_at: "100%"                      # budget exhausted → block releases, surface to human
  warn_at: "25%_remaining"             # <25% budget remaining → surface warning in PRR (non-blocking)
  postmortem_at: "20%_per_incident"    # single incident consuming >20% → mandatory postmortem
```

**Default thresholds** (Google SRE Workbook policy):
- `halt_at: 100%` — full exhaustion in the trailing window. Block releases; focus on reliability.
- `warn_at: 25%_remaining` — fewer than 25% of the budget remains. Non-blocking PRR warning.
- `postmortem_at: 20%_per_incident` — a single incident consumed >20% of the four-week budget.

Tighter thresholds for safety-critical services: `halt_at: "50%"` blocks releases when half
the budget is gone. Adopters who need tighter thresholds override the block explicitly; the
skill's defaults are the minimum floor.

## Error budget derivation

```
error_budget_pct  = 1 - objectives[0].target
                  = 1 - 0.999 = 0.001 (0.1%)

budget_minutes    = error_budget_pct × window_minutes
                  = 0.001 × 43,200 min (30d) = 43.2 minutes of allowed downtime-equivalent

burn_rate         = (observed_error_rate) / (error_budget_pct / window_duration)
                  # burn rate 1 = exactly on pace; 14.4 = budget exhausted in ~2 days (~48 h)
```

## PRR error-budget field resolution

At gate-check time the `release-loop` reads `slos/<service>.yaml` and evaluates the
trailing-window budget consumption. It resolves the PRR `error-budget` field to one of:

| State | Condition | PRR action |
|---|---|---|
| `not-defined` | No `slos/<service>.yaml` found | Visible absence; non-blocking but flagged |
| `within-budget` | `budget_consumed_pct` < (100% − warn_at threshold) | Pass; burn rate included |
| `warning: <N>% remaining` | `budget_consumed_pct` ≥ warn_at but < 100% | Surface warning; human sees it; default non-blocking |
| `exhausted: halt-releases` | `budget_consumed_pct` = 100% | Block release; surface as blocking item at G5 |
| `query-failed` | Telemetry backend unreachable at gate time | Surface to human; default non-blocking |

## Query-at-gate-time (the integration gap)

The `budget_consumed_pct` field cannot be filled from the static SLO document alone.
At gate-check time, the release-loop derives a trailing-window query from the SLO's
`good_query` and `total_query` expressions:

```
budget_consumed_pct =
  (1 - sum(good_events over trailing_window) / sum(total_events over trailing_window))
  / error_budget_pct
```

The release-lead agent executes this query against the telemetry backend. If the
backend is unreachable or the query fails, the gate records `error-budget: query-failed`
and surfaces to the human — **it is not a silent pass**.

## Authoring-time query validation

Before committing the SLO document, validate that the metric queries are functional:

1. Execute the `good_query` and `total_query` expressions against the telemetry backend
   with a short lookback window (e.g., 5 minutes).
2. Confirm each query returns a non-null numeric result in the expected range.
3. Confirm `good_events ≤ total_events` (a ratio > 1 means the queries are reversed).
4. Record the validation run in the SLO document commit message.

A query that passes syntax-checking but returns null at gate time will produce
`query-failed` — catch this at authoring time, not at release time.

## Toolchain translation

The skill produces OpenSLO YAML — the toolchain translates it to backend rules:

| Tool | OpenSLO support | Notes |
|---|---|---|
| **Sloth** | Native — `sloth generate -i <openslo-file>` | Generates Prometheus multiwindow burn-rate rules |
| **Pyrra** | Separate CRD required | Adopter authors a `pyrra.dev/v1alpha1` CRD alongside this doc |
| **Nobl9** | Via OpenSLO import | Nobl9 SaaS has its own `n9/v1alpha` format; use the OpenSLO importer |
| **Datadog / Dynatrace / CloudWatch** | `metricSource.type` switch | Set `type:` to the backend; queries are backend-specific |

The `metricSource.type` field is the boundary between what the skill owns (the schema and
structure) and what the adopter owns (the backend-specific query syntax). The skill does
not generate the Prometheus rules themselves — that is the adopter toolchain's job.

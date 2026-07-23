# Measure flow and DORA metrics

Compute cycle time, lead time, throughput, WIP, and the rest of the Flow Framework / DORA set over a Jira scope with [`flow-metrics`](../../../../packs/atlassian/.apm/skills/flow-metrics/), then pair two runs into a comparison report with [`ai-adoption-report`](../../../../packs/atlassian/.apm/skills/ai-adoption-report/).

`flow-metrics` is read-only. It reads through the `jira` skill, joins `jira-align` for program and portfolio scope, and never transitions, comments, or mutates Jira.

> **Delivery lead?** The [Report AI adoption as a delivery lead](report-ai-adoption-as-a-delivery-lead.md) guide covers the full journey — credential setup, labeling convention, team and program rollup, and shareable report formats. This page covers the CLI in depth.

## Before you start

`flow-metrics` composes the `jira` skill, so verify Jira first:

```bash
python scripts/jira.py check
```

Exit 0 means proceed. Exit 2 means run `credential-setup` yourself — `flow-metrics` never reads credentials directly; it lets the `jira` skill load its own. For program or portfolio scope, the `jira-align` skill must also be installed and authenticated.

The metrics CLI ships as a `flow-metrics` shim on PATH. From a clone of the pack, put the package on PYTHONPATH and use `python -m flow_metrics` instead.

## Measure one project

```bash
flow-metrics --project PROJ
```

JSON to stdout over the default 90-day window (`--to` today, `--from` today minus 90 days). The shipped default state config maps the common "To Do" / "In Progress" / "Done" / "Won't Do" workflow out of the box.

Set an explicit window and AND-in extra JQL:

```bash
flow-metrics \
  --project PROJ \
  --from 2026-02-01 --to 2026-04-30 \
  --jql 'labels = ai-assisted AND component = checkout'
```

Both window bounds are inclusive of the named day. Your `--jql` expression is parenthesised verbatim and ANDed onto the scope query.

## Pick a subset of metrics

The default emits all ten. Narrow with `--metrics`:

```bash
flow-metrics --project PROJ --metrics throughput,cycle_time,defect_ratio
```

The ten names are `cycle_time`, `lead_time`, `throughput`, `wip`, `flow_load`, `rework_rate`, `flow_time`, `flow_efficiency`, `flow_distribution`, `defect_ratio`. Unrequested metrics are omitted from `aggregates`, not emitted as `null`.

## Split a cohort within one window

Mark issues matching a JQL as the cohort; everything else is the control:

```bash
flow-metrics \
  --project PROJ \
  --cohort-jql 'labels = ai-assisted'
```

The output gains a `cohort_breakdown` block with `cohort` and `control` sides. A cohort that matches zero issues produces `throughput: 0` and `null` percentiles, and exits 0.

## Roll up a program or portfolio

Exactly one of `--project`, `--program-id`, `--portfolio-id` is required. Align scope triggers a join through `jira-align`:

```bash
flow-metrics \
  --program-id 42 \
  --align-join-field "Program ID" \
  --from 2026-02-01 --to 2026-04-30
```

`--align-join-field` is required for Align scope unless the state config provides it — the skill won't guess it.

## Compare two runs into a report

Run `flow-metrics` for each window you want to compare, writing each to its own file, then pair them:

```bash
flow-metrics --project PROJ --from 2024-01-01 --to 2024-03-31 \
  --format json --output PROJ-2024Q1.json
flow-metrics --project PROJ --from 2025-10-01 --to 2025-12-31 \
  --format json --output PROJ-2025Q4.json

ai-adoption-report baseline \
  --baseline PROJ-2024Q1.json \
  --current PROJ-2025Q4.json \
  --output report.md
```

`baseline` mode requires both inputs share `meta.scope`, and the baseline window must end on or before the current window starts. `ai-adoption-report` writes the Markdown report plus a JSON sidecar by default; pass `--format markdown` or `--format json` for one or the other.

The skill has two more modes:

- **`cohort`** — render the within-window split a single `--cohort-jql` run already computed: `ai-adoption-report cohort --input run.json --output report.md`.
- **`program`** — roll up many scopes for one window: `ai-adoption-report program --inputs outputs/ --window 2025-10-01..2025-12-31 --output q4.md`.

## Pitfalls

- **`--per-issue` requires `--output`** — JSONL must go to a file. A per-issue dump is the documented input for `ai-adoption-report`; downstream consumers must filter on `delivered_in_window: true` before computing delivery-based metrics.
- **An unmapped raw status exits 2 at startup** naming the offending status. Map it in a `--state-config` file.
- **`ai-adoption-report` paths are literal** — no tilde or env-var expansion, and absolute paths outside the working directory exit 2.
- **Cache staleness** — results cache at `.context/flow-metrics/cache/`. Pass `--no-cache` when the underlying Jira data has changed.

For the full flag surface of both skills, see the [`atlassian` skills reference](../reference/atlassian-skills.md).

---
title: "Measure delivery"
summary: "Get cycle time, lead time, throughput, and other delivery measures from your Jira history, and compare two periods."
pack: atlassian
kind: how-to
uses: [atlassian, credential-brokers]
---

# Measure delivery

Check that your agent can reach Jira, then ask for the numbers your team cares about. The agent only reads, so your tickets never change.

## Check Jira access

Confirm your credentials work before you ask for numbers:

```text
Run the Jira access check and tell me whether my credentials work.
```

The agent runs the `jira` skill's check script. If it fails, set up your credentials first with the `credential-setup` skill, because the metrics tool never reads them itself.

## Measure a project

Ask in team language:

```text
What's our cycle time this quarter for PROJ?
```

The agent runs the `flow-metrics` skill and returns cycle time, lead time, throughput, work in progress, and the rest of the Flow Framework and DORA set as JSON for the last 90 days. Name a different window, or a filter such as "only issues labelled ai-assisted", to narrow it.

## Split out a group

To see how one group of work compares with the rest, name the group:

```text
Compare issues labelled ai-assisted against everything else in PROJ this quarter.
```

The agent adds a breakdown with the group on one side and the rest on the other.

## Roll up a program

For a program or portfolio, give its ID instead of a project:

```text
Measure delivery for Jira Align program 42 from February to April.
```

The agent joins the program's issues through `jira-align`, which must be installed and signed in.

## Compare two periods

Ask for each period, then for the comparison:

```text
Measure PROJ for Q1 2024 and Q4 2025, then write a report comparing them.
```

The agent runs `flow-metrics` for each window and pairs the results with `ai-adoption-report` into a Markdown report and a JSON file. Both periods must cover the same scope, and the earlier one must end before the later one starts.

Results are cached under `.context/flow-metrics/cache/`, so ask for a fresh run when your Jira data has changed. To measure the build loop itself, [export loop telemetry](../../core/how-to/export-loop-telemetry.md) from `core`.

Next, [report AI adoption as a delivery lead](report-ai-adoption-as-a-delivery-lead.md). [The `atlassian` skills reference](../atlassian-skills.md) lists every flag.

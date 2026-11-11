---
title: Report AI adoption as a delivery lead
summary: Turn consistent cohort or before-and-after flow measurements into a caveated stakeholder-ready adoption report.
pack: atlassian
kind: how-to
---

# Report AI adoption as a delivery lead

Turn Jira flow measurements into a caveated adoption report for program leadership, by comparing AI-assisted and unassisted work or two periods. This guide is for delivery leads who run two to eight teams, and assumes Jira holds their real backlog and delivery history; if `docs/product/` is canonical and Jira is only for reporting, use [repo-first projection](../README.md#which-mode-are-you-in) instead. You need [the `atlassian` pack installed](../../_shared/how-to/install-packs.md), working Jira credentials, and teams applying the `ai-assisted` label before the first reporting window, the period the report covers, such as a quarter. The agent runs the command-line tools; you ask in plain words. [Measuring AI adoption with flow metrics](../explanation/ai-adoption-measurement.md) explains the model.

## Set up the pack and credentials

Ask the agent to install the pack and set up credentials:

```text
Install the atlassian pack and set up my Jira credentials.
```

The agent walks you through setup and stores your Jira API token in your OS keychain, never in a file the agent can read. Confirm it worked:

```text
Check my Jira credentials.
```

If the check fails, the agent asks you to re-run setup and does not retry on its own. [Credential setup](../reference/ai-adoption-report-reference.md#credential-setup) covers Jira Align credentials and instances that block API tokens.

## Agree the label with your teams

Teams apply the `ai-assisted` Jira label to a story when AI materially contributed to the solution, not for autocomplete. The engineer, or their agent, applies it when marking the story done. Do not label old stories in bulk: unlabeled stories are the control group. Two to three sprints give reliable percentiles; fewer than ten labeled stories in a window makes them unreliable.

## Compare AI-assisted and unassisted work

Ask for a cohort split, which compares the labeled stories with the unlabeled ones inside the same window:

```text
Run Q1 2026 flow metrics for project PROJ with an AI-assisted cohort split, and produce the adoption report.
```

The agent runs `flow-metrics` and then `ai-adoption-report`, and writes a Markdown report and a JSON sidecar, a structured copy of the same numbers for dashboards, under `reports/` in your repository. Ask the agent to narrow the scope with a JQL filter, such as one component or issue type, when you need to. [Find and open your files](../../_shared/how-to/find-and-open-your-files.md) covers opening them.

## Compare two periods

Ask for a before-and-after comparison when you want to show impact over time:

```text
Compare our Q1 2024 metrics against Q1 2026 metrics for project PROJ to show AI adoption impact.
```

The baseline window is the earlier period you compare against, and it must end on or before the current window, the later period you report, starts.

## Roll up to a program

Ask for several teams at once. With Jira Align, name the program:

```text
Run flow metrics for program 42 in Jira Align, Q1 2026, with AI-assisted cohort split.
```

Without it, name the projects:

```text
Run Q1 2026 flow metrics for PROJ1, PROJ2, and PROJ3 with cohort split, then produce a program-level adoption report.
```

The report adds one row per team or project and aggregate totals. Collection runs one scope at a time, so large programs need a script.

## Share the report

Review the report's provenance and caveats, then publish the approved version or draft a summary for leadership. The Markdown pastes into docs and slides, unless you chose Markdown-only output, and the JSON sidecar feeds dashboards:

```text
Publish the Q1 adoption report to Confluence in the ENG space under 'AI Adoption Tracking'.
```

```text
Summarise the Q1 adoption report in three sentences suitable for a leadership update. Lead with cycle time improvement, then throughput, then quality.
```

Check the summary yourself: the agent cannot tell whether the numbers match leadership's expectations or prior commitments. The pipeline has not changed Jira.

## What this job does not do

The report does not include change failure rate or time to restore, because Jira holds no deployment data. It does not break work down by engineer, measure code quality, or detect unlabeled AI use. The reference has the full label definition, scale limits, metric meanings, and exclusions.

Next, [look up the commands, sample reports, and metric meanings](../reference/ai-adoption-report-reference.md).

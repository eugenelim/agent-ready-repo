---
title: Connect your tracker
summary: Bring work from Jira, Linear, or GitHub into the repository as a spec or brief, without writing back to the tracker.
pack: _shared
uses: [core, atlassian, linear, github, product-engineering]
kind: how-to
---

# Connect your tracker

Point your agent at an issue or milestone in your tracker, and it turns the content into repository work. Intake only reads from the tracker.

## Pick your tracker

Install `core` plus the pack for your tracker (see [Install packs](install-packs.md)), then use the matching request:

| Tracker | Pack | First request |
| --- | --- | --- |
| Jira | `atlassian` | `Intake Jira issue PROJ-123 as repository work.` |
| Jira Align | `atlassian` | `Intake Jira Align Feature 4521 as repository work.` |
| Linear | `linear` | `Intake Linear issue LIN-123 as repository work.` |
| GitHub | `github` | `Intake GitHub issue 123 as repository work.` |

GitHub also needs the [`gh` CLI](https://cli.github.com), signed in.

## Run the first intake

Ask your agent, adding "Start read-only" so nothing is written:

```text
Intake Linear issue LIN-123 as repository work. Start read-only.
```

The agent reads the item and decides from its content, not its type, whether it becomes a spec, a brief, or a bug fix, and asks before it writes anything.

## Keep planning in the repository

If you shape work in the repository and want the tracker to mirror it, install `product-engineering` and ask:

```text
Decompose this intent and show me the tracker projection for its slices.
```

Pick one direction per body of work, because edits made in both places are never reconciled for you. [Project slices to a tracker](project-slices-to-a-tracker.md) covers this direction.

Next, [find your first piece of work](../../core/how-to/start-a-project.md#find-your-first-piece-of-work). Tracker details: [Jira](../../atlassian/work-with-jira.md), [Linear](../../linear/how-to/linear-brief-intake-and-sync.md), [GitHub](../../github/how-to/intake-a-github-milestone-as-a-brief.md).

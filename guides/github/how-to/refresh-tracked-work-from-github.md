---
title: Refresh tracked work from GitHub
summary: Compare a repository artifact with its GitHub source, then confirm each comment, label, link, or closure written back.
pack: github
kind: how-to
---

# Refresh tracked work from GitHub

Compare an artifact in your repository with the GitHub Issue it came from, review what changed field by field, and confirm each coordination change written back to GitHub. You need [the `github` and `core` packs installed](../../_shared/how-to/install-packs.md), the [`gh` CLI](https://cli.github.com) signed in, and an artifact that records GitHub as its source, which intake creates. [Start, remember, inspect, or refresh repository work](../../_shared/how-to/use-work-intake.md#refresh-tracked-requirements) covers the one-time setup of its source record and field ownership.

## Ask for the comparison

Ask the agent to compare without writing anything:

```text
Refresh docs/specs/export-retention/spec.md from the tracker source in its source-authority record. Show every changed field and do not write back yet.
```

The agent runs `work-intake` refresh, which hands the GitHub side to the `github-refresh` skill, and shows each changed field. Nothing changes locally until you decide each one.

## Confirm a write-back

Ask for a GitHub change only when you want one, and name it:

```text
Add the reviewed pull-request link to the linked GitHub issue. Show the exact target and payload, then wait for confirmation.
```

The skill supports five changes: a comment, a trace link, a pull-request link, a status label, and closing the issue. Each one needs its own fresh confirmation. The agent records a pending receipt before it calls `gh`, uses your signed-in `gh` CLI, and does not retry a failure on its own. The repository and host come from trusted configuration; text inside an Issue never selects them.

## What this job does not do

Refresh does not create artifacts, rewrite Issue bodies or requirements, or choose a repository. A spec that is Implementing, or a brief that is Executing, refuses requirement refresh, and shipped requirements are locked.

Next, [intake GitHub work into the repository](intake-a-github-milestone-as-a-brief.md).

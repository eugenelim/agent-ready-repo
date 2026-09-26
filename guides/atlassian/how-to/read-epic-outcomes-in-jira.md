---
title: Read Epic outcomes beside delivery in Jira
summary: Group a Jira project's work by Epic and see, for each one, what it delivered beside what that work was meant to change.
pack: atlassian
kind: how-to
---

# Read Epic outcomes beside delivery in Jira

**Use this when:** You can see what your team shipped, but not what shipping it
was for. This view puts the two side by side, one row per Epic.

**Prerequisites:** Jira credentials verified, plus the `jira` and `flow-metrics`
skills from this pack. Nothing else — no repository, no configuration file, no
migration. Run it from any directory.

**Result:** One JSON document: every Epic in the project, each with a delivery
reading for the window and the outcome the team recorded for it.

## Run it

```text
Show me each Epic in the ATLAS project with what it delivered and what it was meant to change.
```

Or run the skill's script directly:

```bash
python -m jira_epic_outcome_view --project ATLAS --from 2026-07-01 --to 2026-09-30
```

## Where the outcome comes from

One fixed place: the Epic's **description** field, in the block under a
top-level `Outcome` heading. Write it there and the view reads it back
word for word.

```text
## Outcome
Customers resolve a return without contacting support.
```

The heading works in both Jira deployments — the rich editor on Cloud and
plain or wiki text on Server and Data Center. The block runs to the next
heading or to the end of the description. The location is not configurable,
so every team reading this view finds an outcome in the same place.

## When an Epic has no outcome

The view says so, out loud, and asks you for one. It never invents an answer
and never leaves the row blank, because an Epic with nothing recorded is the
one most worth looking at.

Answer with `--outcome`, repeatable once per Epic:

```bash
python -m jira_epic_outcome_view --project ATLAS --outcome ATLAS-42="Customers resolve a return without contacting support."
```

Your words come back as text to paste into the Epic's description. You paste
it; the view does not. That is how the outcome ends up beside the work,
written by the team that owns it, and how the next run is better than this one.

## What this view answers

- Which Epics hold the project's work, and which issues rolled up to each.
- What each Epic delivered in the window: a throughput count with its window,
  work in flight, how long in-flight work has been in flight, what is flagged
  and since when, and what changed state inside the window.
- What each Epic was meant to change, word for word from the team.
- Which Epics have no outcome recorded at all.
- When each half was read. The delivery reading and the Jira read are two
  passes, and the view states both moments rather than implying one snapshot.

## What this view does not answer

- **Whether the outcome was achieved.** It reports what the team wrote. It
  never scores, grades or judges it.
- **Cycle time, lead time, flow efficiency or any percentile per Epic.** Every
  per-Epic figure is a count over rows the flow skill already produced. For the
  distributions, use
  [Measure flow and DORA metrics](measure-flow-and-dora-metrics.md) directly.
- **Work you cannot browse.** Jira omits issues your credential cannot see and
  does not say that it did, so every run carries that disclosure. A scope can
  be larger than it looks here.
- **Anything outside Jira.** One tracker, one project at a time.
- **Readiness, triage or who should pick something up.** Other skills in this
  pack answer those; see [`atlassian` — guides](../README.md).

## What it never writes

Nothing, anywhere you would notice:

- **Not to Jira.** No comment, no label, no transition, no field edit. Only
  read requests leave the process.
- **Not to your working directory, and not to the installed pack.** Both come
  out of a run byte for byte as they went in.
- **Not to your repository.** The view reads no project file and needs none.

The flow skill it composes needs a per-issue file to hand its rows over. That
file is written to a temporary directory outside both of those places and is
deleted before the view returns, including when the run fails.

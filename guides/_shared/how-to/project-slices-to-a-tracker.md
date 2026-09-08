---
title: Project intents and slices out to a tracker
summary: Render repository-owned intents and delivery slices as tracker tickets, one way, so the tracker reports engagement without owning requirements.
pack: _shared
kind: how-to
---

# Project intents and slices out to a tracker

**Use this when:** shaping happens in the repository and you need the team's
tracker to show the same work — for standups, reporting, or stakeholders who
live in Jira, Linear, or GitHub.

**Mode:** repo-first projection. The intent tree is the source of truth and the
tracker is a render. If instead your team's real backlog lives in the tracker and
you want to bring that work into the repository, you are in the other supported
mode — see [Choose a tracker integration](choose-a-tracker-integration.md).

```text
Decompose this intent and show me the tracker projection for its slices.
```

## The rule this mode runs on

The canonical intent tree is deeper than any tracker. Trackers are lossy,
**one-way** projections of it:

> The tree is the source of truth; the tracker is a render. **Never
> round-trip** status back from the tracker — bidirectional sync across
> mismatched hierarchies silently corrupts data.

That statement is the pack's own, in
`packs/product-engineering/.apm/skills/decompose-intent/references/tracker-projection.md`,
which stays canonical for the Linear and Jira Align columns below.

The practical consequence: requirements, acceptance decisions, and status live
in the repository artifact. The ticket is a shallow shadow copy. When the two
disagree the repository wins — and because nothing syncs automatically, someone
replaces the ticket's content by hand when the mapping is reapplied.

## What lands where

Read a row as "one canonical thing becomes this object in your tracker".

| Canonical | `none` | Linear (lean) | Jira Software | Jira Align (deep) | GitHub |
| --- | --- | --- | --- | --- | --- |
| product-vision intent | markdown | Initiative / label | label or component | Theme / Strategy tier | org Project |
| product-strategy intent | markdown | Initiative / label | label or component | Theme / Strategy tier | org Project |
| top (capability) intent | markdown | Initiative | Epic, or Initiative where Advanced Roadmaps is enabled | Epic (Portfolio) | Project |
| feature-level intent | markdown | Project | Epic | Feature (Program) | Milestone |
| extra intervening intents | markdown | labels / sub-issues | labels / components | Capability, Solution tier | labels |
| **spec / slice (leaf)** | a `core` brief | **Issue** | **Story** | **Story** (Team) | **Issue** |
| story-as-trace (optional) | AC checklist | sub-issue / checklist | Sub-task | Story / sub-task | task-list item |

The `none`, Linear, and Jira Align columns are the pack's shipped profiles. The
Jira Software and GitHub columns are this guide's extension for adopters on
those tools; when a Jira Software or GitHub row disagrees with your team's
configuration, your configuration wins — record the deviation rather than
bending the canonical model.

**The leaf is the unit.** A spec or a confirmed slice inside a brief is what
becomes a ticket. A story is a traceability lens projected *from* a spec, never
the thing you decompose into.

## The impedance is the point

The same canonical feature intent lands at a **Project** in Linear, an **Epic**
in Jira Software, a **Feature** in Jira Align, and a **Milestone** in GitHub. A
Jira Align *Feature* is a Jira Software *Epic* on sync — the same word naming
different levels in adjacent tools.

If you modelled the work in the tracker, the tool's shape would corrupt the
product model. Model in intents; render to whichever tracker the team uses; keep
`none` a first-class option for a solo developer or a team with no shared
tracker.

## How to project, today

1. Shape the intent and decompose it until the leaves are independently
   shippable. See
   [Hand an intent to the build loop](../../product-engineering/how-to/hand-an-intent-to-build.md).
2. Ask for the projection. The skill maps each level to your profile's object
   and prints the set:

   ```text
   Project the slices of this brief to Linear using the lean profile.
   ```

3. Create the tickets. **This step is manual today.** The mapping and export
   shape ship; a live API integration does not. Auth, rate limits, idempotency,
   and conflict rules make that infrastructure rather than a habit.
4. Put the repository path in each ticket body so a reader can find the real
   contract, and leave the ticket body otherwise thin.

## What not to do

- **Do not edit requirements in the ticket.** Nothing carries the edit back, so
  it survives only until someone reapplies the mapping and replaces it — and
  until then two sources disagree with no signal.
- **Do not sync status back.** The repository artifact's `Status:` and the
  brief's derived Spec map are the truth.
- **Do not decompose in the tracker.** Adding a ticket with no canonical parent
  creates work the repository cannot see.
- **Do not mix modes in one initiative.** Pick repo-first projection or
  tracker-authoritative intake per body of work, and say which in the brief.

## What you have now

A ticket in your team's tracker for every confirmed slice, each pointing back at
the repository artifact that owns its requirements, and a tracker that reports
engagement without holding any decision. Status stays answerable from the
repository: the brief's Spec map rolls up from each spec's own `Status:`.

For what the tracker can report once the tickets exist, see
[Measure flow and DORA metrics](../../atlassian/how-to/measure-flow-and-dora-metrics.md).

## See also

- [Choose a tracker integration](choose-a-tracker-integration.md) — the other mode: tracker-authoritative intake
- [Tracker vocabulary](../reference/tracker-vocabulary.md) — object-name hints per tracker
- [Hand an intent to the build loop](../../product-engineering/how-to/hand-an-intent-to-build.md)

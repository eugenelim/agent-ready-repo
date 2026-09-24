---
title: Choose how much design a surface owes
summary: Pick the risk tier for a design thread, walk the minimal viable thread, and know which states every tier still owes.
pack: experience-design
kind: how-to
---

# Choose how much design a surface owes

Use this when the full design thread is more than the work needs and you want to
know what you can safely leave out. Depth is a per-run choice: the same stages
serve a throwaway prototype and a public launch at different depths.

Start with a request like:

> Pick the risk tier for this design thread and tell me what it owes.

## The minimal viable thread

Four steps make the output coherent. Everything else in the pack sharpens them.

1. `journey-mapping` — the outcome and the failure modes
2. `user-flow` — the screen list and the per-screen briefs
3. one craft pass per screen — at minimum `information-architecture`, then
   `interaction-design`
4. `experience-reviewer` — the cold review

Walking the shorter thread is a real choice, not a corner cut. What a skipped
step costs is that its input travels forward as an assumption nobody decided,
which is why those four are the ones that stay. `experience-status` tells you
where you are on the thread.

## The three tiers

`explore` is the default.

| Tier | Choose it when | Each per-screen brief owes |
|---|---|---|
| `explore` | A prototype or a surface still finding its shape | The states the map assigns to the `explore` band |
| `pilot` | A pre-release surface in front of limited real users | Everything in `explore`, plus the states the map assigns to `pilot` |
| `production` | A public surface in front of all users | Everything in `pilot`, plus the states the map assigns to `production` |

Which contract fields each tier owes is recorded once, in the contract's own
`Required: <tier>+` annotations, and which states it owes is recorded once, in
the contract's shared state-coverage map. Read both there rather than from a
list in a guide.

## What no tier drops

The shared state-coverage map records, for each state, whether its absence fails
WCAG 2.2 AA and names the success criterion behind that judgement. Every state
flagged that way is either in the `explore` set already or is conditional and
binds wherever its trigger fires — a surface behind authorization, or a primary
action that is irreversible or destroys data the user controls.

So the cheap tier costs you evidence and completeness, never an accessible
surface. The quality floor's accessibility pass applies at every tier.

## What crosses to frontend engineering

Three artifacts leave this pack and are read by the frontend pre-flight, each
path relative to the design output directory you configure:

| Artifact | Path | Written by |
|---|---|---|
| Aesthetic direction | `direction/<slug>.md` | `creative-direction` |
| Per-screen brief | `screens/<slug>/<screen>.md` | `user-flow`, enriched by `interaction-design` |
| Token taxonomy | `tokens/<slug>.md` | `design-system` |

A slot no artifact fills is not an error. The frontend pre-flight falls back to
its own canonical reference for that slot and records which one it used, so a
shortened thread degrades visibly rather than silently.

## Where this leads

With the tier chosen, walk the thread from
[Map the customer journey](map-the-customer-journey.md) onward. To decide
which copy skill a surface needs, see
[Choose the right copy skill](copy-boundary.md).

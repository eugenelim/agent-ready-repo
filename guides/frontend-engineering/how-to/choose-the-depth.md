---
title: Choose how much contract a surface owes
summary: Pick the risk tier for a surface, see which contract fields and states that tier owes, and know what the cheap tier never drops.
pack: frontend-engineering
kind: how-to
journey: frontend-engineering
---

# Choose how much contract a surface owes

Use this when you are about to build or change a web surface and want the
cheapest depth that is still honest. Depth is a per-run choice, not a property
of the pack: a tooltip and a checkout flow walk the same stages at different
depths. The result is a `risk-tier` for the surface and a clear list of what it
owes.

Start with a request like:

> Pick the risk tier for this surface and tell me which contract fields and
> states it owes.

The agent reads the surface's scope and reach, proposes a tier, and reports the
obligations that tier carries. You approve the tier before the contract is
drafted.

## The three tiers

`explore` is the default. Raise the tier as the surface matures; nothing makes
you start high.

| Tier | Choose it when | It owes |
|---|---|---|
| `explore` | A prototype, an internal tool, or a surface still finding its shape | The fields the contract annotates `Required: explore+`, and the states the map assigns to the `explore` band |
| `pilot` | A pre-release surface in front of limited real users | Everything in `explore`, plus the fields annotated `Required: pilot+` and the states the map assigns to `pilot` |
| `production` | A public surface in front of all users | Everything in `pilot`, plus the fields annotated `Required: production+` and the states the map assigns to `production` |

Neither the field counts nor the state lists are repeated here. Read the fields
from the contract's own `Required: <tier>+` annotations and the states from its
shared state-coverage map, which is what the journey and the gates both read —
a number written in a guide is a number that goes stale, and so is a list.

## Two states sit outside the ladder

`permission/denied` and `destructive-confirmation` are not banded. Each binds at
every tier once its trigger fires: the surface sits behind authorization, or its
primary action is irreversible or destroys data the user controls. A tooltip run
at `explore` with a destructive primary action still owes the confirmation
state.

## What `explore` never drops

Depth buys evidence and completeness. It does not buy a surface someone cannot
use.

The shared state-coverage map in the experience contract records, per state,
whether its absence fails WCAG 2.2 AA and names the success criterion that
judgement rests on. Every state it flags that way is either already in the
`explore` set or is one of the two conditional states above. So no tier drops an
accessibility-bearing state, and the accessibility audit runs at every tier.

Captures do not thin with the tier either. A route owes four captures per
channel — a short and a tall viewport, each at rest and scrolled — at `explore`
exactly as at `production`. Declared breakpoints change how many channels a
route has; they never change the four each channel owes.

## What you can leave out

Four allowances apply:

- The contract is proportional to the surface's risk and scope. A new route or a
  feature-gating screen warrants the full field set; a single form field or a
  minor component variant does not.
- A state genuinely inapplicable to the surface is omitted with the reason
  recorded, rather than filled in with "n/a".
- A retrofit narrows the state matrix to what is absent or broken, rather than
  re-enumerating all eighteen states.
- The CSS token gate runs where stylelint is already configured. It is not a
  reason to add stylelint.

## Where this leads

Once the tier is approved, write the contract at that depth — see
[Write a page or screen contract](page-screen-contract.md). If a design pack
produced the work, the pre-flight reads the direction, per-screen brief, and
token taxonomy first; see
[Read the design handoff](read-the-design-handoff.md).

# Quality-attribute scenarios — make a pillar claim testable

A vague pillar question ("is it reliable?") is not a claim you can verify. The
quality-attribute scenario (from ATAM / ISO 25010 practice) turns it into a
*testable* assertion by naming six parts. Anchor every measurable pillar claim
— a design assertion or a review finding — to one.

> Note: this reference is intentionally duplicated from `architect-design`'s
> `references/quality-attribute-scenarios.md`. Skill autonomy beats DRY at this
> scale — each skill stands alone. See the pack README.

## The six parts

| Part | Question it answers |
|---|---|
| **Source** | Who or what generates the stimulus? (a user, a failing AZ, an attacker, a traffic spike) |
| **Stimulus** | The condition that arrives. (zone failure, 10× load, a malformed request) |
| **Artifact** | The part of the system stimulated. (the order service, the data tier, the LB) |
| **Environment** | The state the system is in when it arrives. (peak load, degraded mode, normal) |
| **Response** | What the system does. (fails over, sheds load, rejects and logs) |
| **Response measure** | The measurable bar the response must clear. (within 60s, <0.1% dropped, p99 < 200ms) |

## Worked example

> When an availability zone fails **[stimulus]** during peak checkout load
> **[environment]**, the order service **[artifact]** fails over **[response]**
> within 60s with <0.1% dropped requests **[response measure]**.

The measure is the load-bearing part. "Fails over gracefully" is a vibe; "within
60s with <0.1% dropped" is a claim someone can test and a reviewer can falsify.

## When to reach for one

- **Design-time** — when you assert a pillar is achieved ("it's highly
  available"), state it as a scenario with a measure instead. If you can't put a
  number on the measure, that gap is itself worth surfacing.
- **Review-time** — when a finding turns on a measurable claim, frame the finding
  as the scenario the design fails to meet, so the fix target is unambiguous.

## A scenario without a measure is an open decision

If the source/stimulus/artifact are clear but the **measure** is unknown (no SLO,
no agreed target), that is not a mechanical gap — it's a business call about how
much reliability/latency/cost is worth. Surface it as a **judgment** item (see
`tradeoffs-and-sensitivity.md`), not something the convergence loop fills in by
guessing a number.

## Use, don't recite

Write scenarios for the two or three quality attributes the concept stage
prioritized, not for every pillar. A design padded with six rote scenarios is
worse than one with two sharp ones.

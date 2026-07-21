---
type: opportunity-assessment
slug: <slug>
date: <YYYY-MM-DD>
source: <situation-framing | free-form>
---

# Opportunity Assessment: <topic>

> Opportunity score = importance + max(importance − satisfaction, 0)
> Ratings labelled (agent-estimated) were inferred from context rather than PE-supplied.

## Functional Jobs

Jobs users are trying to **accomplish** — the outcome, not the means.

| Job | Importance (1–10) | Satisfaction (1–10) | Opportunity Score |
|-----|-------------------|---------------------|-------------------|
| <job> | <n> | <n> | <n> |

## Emotional Jobs

How users want to **feel** (or avoid feeling) while doing the job.

| Job | Importance (1–10) | Satisfaction (1–10) | Opportunity Score |
|-----|-------------------|---------------------|-------------------|
| <job> | <n> | <n> | <n> |

## Social Jobs

How users want to be **perceived** by others when doing the job.

| Job | Importance (1–10) | Satisfaction (1–10) | Opportunity Score |
|-----|-------------------|---------------------|-------------------|
| <job> | <n> | <n> | <n> |

## Top Opportunities

Jobs ranked by opportunity score across all tiers (highest first; tie-break = encounter order).
These are the recommended inputs for `diverge-solutions`.

| Rank | Job | Tier | Opportunity Score |
|------|-----|------|-------------------|
| 1 | <job> | <functional / emotional / social> | <n> |

<!-- Step 3 readiness — include when `diverge-solutions` is not detected in available skills.
     Remove when the skill is available. -->

## Step 3 readiness

`diverge-solutions` was not detected in available skills. Step 3 of the shaping
sequence generates multiple solution options for the highest-opportunity jobs — it
takes this artifact's top-opportunities list as its primary input. Resume shaping
at step 3 when the skill becomes available.

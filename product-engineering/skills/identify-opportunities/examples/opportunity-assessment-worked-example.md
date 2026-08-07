# Example: opportunity assessment — hybrid office desk booking

A product engineer at a company rolling out hybrid work runs
`identify-opportunities` on a free-form problem description.
No prior `situation-framing.md` exists for this topic.

---

## Input

> "We're hearing from employees that finding a desk when they come into
> the office is frustrating. Teams want to sit together but there's no
> way to coordinate in advance. The facilities team is fielding complaints
> every week and there's no shared tooling for it."

Slug derived: `hybrid-office-desk-booking`
Source: free-form (no `situation-framing.md` found at the slug path)

---

## Step 1 — Slug

Derived from topic: `hybrid-office-desk-booking`

---

## Step 2 — Opportunistic read

No `situation-framing.md` found at `<output_dir>/shaping/hybrid-office-desk-booking/`.
Proceeding on free-form input.

---

## Steps 3–5 — Job elicitation

### Functional jobs

Jobs employees are trying to **accomplish**:

1. Book a desk in advance to guarantee a spot on planned office days
2. Find an available desk near their team on the day of arrival
3. Coordinate a team cluster so everyone sits in the same area on the same day
4. See what amenities (monitors, standing desk, quiet vs collaborative zone) a desk has before arriving
5. Check in and out without filling in a paper form or emailing the facilities team

### Emotional jobs

How employees want to **feel**:

1. Feel confident they will have a desk when they arrive — not wasted the commute
2. Avoid the anxiety of uncertainty about whether space will be available
3. Feel they genuinely belong in the office, not like a visitor interrupting regular staff

### Social jobs

How employees want to be **perceived**:

1. Be seen as collaborative by visibly sitting with the team
2. Come across as organised and prepared — desk booked, not wandering to find a spot

---

## Step 6 — Ulwick scoring

> Opportunity score = importance + max(importance − satisfaction, 0)
> All ratings below are agent-estimated from the problem description.

### Functional jobs

| Job | Importance (1–10) | Satisfaction (1–10) | Opportunity Score |
|-----|-------------------|---------------------|-------------------|
| Book a desk in advance | 9 (agent-estimated) | 3 (agent-estimated) | 15 |
| Find an available desk near team | 8 (agent-estimated) | 4 (agent-estimated) | 12 |
| Coordinate a team cluster | 8 (agent-estimated) | 3 (agent-estimated) | 13 |
| See desk amenities before arriving | 7 (agent-estimated) | 4 (agent-estimated) | 10 |
| Check in/out without forms | 7 (agent-estimated) | 5 (agent-estimated) | 9 |

### Emotional jobs

| Job | Importance (1–10) | Satisfaction (1–10) | Opportunity Score |
|-----|-------------------|---------------------|-------------------|
| Feel confident a desk will be available | 9 (agent-estimated) | 3 (agent-estimated) | 15 |
| Avoid anxiety of uncertainty | 8 (agent-estimated) | 4 (agent-estimated) | 12 |
| Feel they belong in the office | 7 (agent-estimated) | 5 (agent-estimated) | 9 |

### Social jobs

| Job | Importance (1–10) | Satisfaction (1–10) | Opportunity Score |
|-----|-------------------|---------------------|-------------------|
| Be seen as collaborative by sitting with team | 8 (agent-estimated) | 5 (agent-estimated) | 11 |
| Come across as organised — desk booked, not wandering | 6 (agent-estimated) | 6 (agent-estimated) | 6 |

---

## Step 7 — Rank and top opportunities

All jobs sorted by opportunity score descending; tie-break by encounter order
(functional jobs listed first, then emotional, then social):

| Rank | Job | Tier | Opportunity Score |
|------|-----|------|-------------------|
| 1 | Book a desk in advance | Functional | 15 |
| 2 | Feel confident a desk will be available | Emotional | 15 |
| 3 | Coordinate a team cluster | Functional | 13 |
| 4 | Find an available desk near team | Functional | 12 |
| 5 | Avoid anxiety of uncertainty | Emotional | 12 |
| 6 | Be seen as collaborative by sitting with team | Social | 11 |
| 7 | See desk amenities before arriving | Functional | 10 |
| 8 | Check in/out without forms | Functional | 9 |
| 9 | Feel they belong in the office | Emotional | 9 |
| 10 | Come across as organised — desk booked, not wandering | Social | 6 |

**Top opportunities for `diverge-solutions`:** Jobs 1–5 (scores 12–15) cluster
around advance booking and certainty of availability — the load-bearing insight
for solution divergence.

---

## Artifact written

Path: `<output_dir>/shaping/hybrid-office-desk-booking/opportunity-assessment.md`

```markdown
---
type: opportunity-assessment
slug: hybrid-office-desk-booking
date: 2026-07-21
source: free-form
---

# Opportunity Assessment: hybrid office desk booking

> Opportunity score = importance + max(importance − satisfaction, 0)
> Ratings labelled (agent-estimated) were inferred from the problem description.

## Functional Jobs

| Job | Importance (1–10) | Satisfaction (1–10) | Opportunity Score |
|-----|-------------------|---------------------|-------------------|
| Book a desk in advance | 9 (agent-estimated) | 3 (agent-estimated) | 15 |
| Find an available desk near team | 8 (agent-estimated) | 4 (agent-estimated) | 12 |
| Coordinate a team cluster | 8 (agent-estimated) | 3 (agent-estimated) | 13 |
| See desk amenities before arriving | 7 (agent-estimated) | 4 (agent-estimated) | 10 |
| Check in/out without forms | 7 (agent-estimated) | 5 (agent-estimated) | 9 |

## Emotional Jobs

| Job | Importance (1–10) | Satisfaction (1–10) | Opportunity Score |
|-----|-------------------|---------------------|-------------------|
| Feel confident a desk will be available | 9 (agent-estimated) | 3 (agent-estimated) | 15 |
| Avoid anxiety of uncertainty | 8 (agent-estimated) | 4 (agent-estimated) | 12 |
| Feel they belong in the office | 7 (agent-estimated) | 5 (agent-estimated) | 9 |

## Social Jobs

| Job | Importance (1–10) | Satisfaction (1–10) | Opportunity Score |
|-----|-------------------|---------------------|-------------------|
| Be seen as collaborative by sitting with team | 8 (agent-estimated) | 5 (agent-estimated) | 11 |
| Come across as organised — desk booked, not wandering | 6 (agent-estimated) | 6 (agent-estimated) | 6 |

## Top Opportunities

Jobs ranked by opportunity score across all tiers (highest first; tie-break = encounter order):

| Rank | Job | Tier | Opportunity Score |
|------|-----|------|-------------------|
| 1 | Book a desk in advance | Functional | 15 |
| 2 | Feel confident a desk will be available | Emotional | 15 |
| 3 | Coordinate a team cluster | Functional | 13 |
| 4 | Find an available desk near team | Functional | 12 |
| 5 | Avoid anxiety of uncertainty | Emotional | 12 |
| 6 | Be seen as collaborative by sitting with team | Social | 11 |
| 7 | See desk amenities before arriving | Functional | 10 |
| 8 | Check in/out without forms | Functional | 9 |
| 9 | Feel they belong in the office | Emotional | 9 |
| 10 | Come across as organised — desk booked, not wandering | Social | 6 |

**Recommended for `diverge-solutions`:** Jobs 1–5. These cluster around advance
booking and certainty of availability — a strong opportunity cluster that implies
a core design challenge around reservation and real-time visibility.

## Step 3 readiness

`diverge-solutions` was not detected in available skills. Step 3 of the shaping
sequence generates multiple solution options for the highest-opportunity jobs — it
takes this artifact's top-opportunities list as its primary input. Resume shaping
at step 3 when the skill becomes available.
```

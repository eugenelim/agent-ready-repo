# Experience review — round 1

**Reviewer:** experience-reviewer  
**Artifact:** `/now/` page — `core 2.10.11` release highlight  
**Outcome:** SHIP WITH CHANGES → resolved (copy fix applied)

## Verdict

SHIP WITH CHANGES — no blockers. Two concerns and three nits raised against the
`core 2.10.11` highlight copy in `docs/product/changelog.md`.

## Findings and resolution

**Concern 1 — tail negations import concepts only to disclaim them (resolved)**  
"…without requiring a code graph or allowing a numeric score to hide a blocker"
references internal differentiation the reader has no context for.  
Fix applied: replaced with "so every residual risk is named, not hidden."

**Concern 2 — second sentence too dense (resolved)**  
Five stacked technical ideas in one clause; readers bounce off after the bold lead.  
Fix applied: shortened and restructured into a single readable clause.

**Nit 3 — "Existing reviewers" is inside-baseball (resolved)**  
"Existing" signals maintainer context (no new reviewer added) but is meaningless
to outside readers.  
Fix applied: dropped "Existing".

**Nit 4 — four verdict states listing (accepted)**  
All four states are accurate and payoff-bearing; listing them makes the feature
concrete. Retained as-is.

**Nit 5 — "when the change warrants it" can tighten (resolved)**  
Fix applied: replaced with "when warranted".

## Final copy (applied)

> **Work-loop reviews now explain readiness without asking you to trust a
> generic "clean" verdict.** Reviewers trace non-local impact and rollout
> safety when warranted, then hand off an evidence-bearing verdict —
> `BLOCKED`, `CHANGES_REQUIRED`, `READY_WITH_RESIDUAL_RISK`, or `READY` —
> so every residual risk is named, not hidden.

## What was confirmed clean

- Painkiller-first bold lead preserved
- No AI-smell, no graph claims, no numeric-score claims
- Verdict states match the shipped categorical set
- Render: topmost entry, `datetime="2026-08-23"`, `<code>`-wrapped tokens,
  working source link to `#core21011--2026-08-23`
- 178/178 Playwright browser gate tests pass (0 failures) including `/now/` at
  360 and 1440 widths

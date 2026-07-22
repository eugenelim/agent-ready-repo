# Adversarial review — round 3

**Date:** 2026-07-22  
**Reviewer:** adversarial-reviewer subagent

Round-2 fixes confirmed. No blockers.

## Concerns (both applied)

**1. AC1b/AC1d had no verification artifact.** T1 was all goal-based but AC1b (5 sections present and in order) and AC1d (plain language) are inherently manual. Fixed: T1 now mixed-mode; manual coverage check recorded in notes/tutorial-review.md or notes/transcript.md.

**2. T2→T3 ask-first gate not in T3.** Ask-first boundary fires if T2 shows `adapt-to-project` routing, but T3 had no precondition. Fixed: explicit precondition added to T3 heading.

## Nit (applied)

**3. T5 changelog grep didn't scope to [Unreleased].** Fixed: awk range check against [Unreleased] block.

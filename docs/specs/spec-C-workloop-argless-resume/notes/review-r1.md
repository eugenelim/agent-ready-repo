# Adversarial Review — Round 1

## Blockers

**1. Control flow proceeds to PLAN even in zero/multi branches.** `packs/core/.apm/skills/work-loop/SKILL.md:187-191`. The closing paragraph stated "proceed to step 1 (PLAN)" unconditionally; an agent in Branch 3 could proceed without waiting for user input — exactly the auto-pick the spec forbids. Fix: gate proceed-to-PLAN on a path having been resolved; in zero and multi-item branches, stop after surfacing and wait for user.

## Concerns

**2. Spec/plan metadata stale.** `docs/specs/spec-C-workloop-argless-resume/spec.md:3`, `:48-59`, `plan.md:4`. Status still `Approved`, all ACs unchecked, plan Status `Drafting`. Must flip atomically with merge.

## Nits

**3. Branch 1 action in surface-list bullet.** `packs/core/.apm/skills/work-loop/SKILL.md:160-171`. Control-flow action ("begin on that spec without asking") mixed into a data-surface list. Harmless; restructuring is a design call beyond spec scope. Deferred.

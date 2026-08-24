## Blockers

**1. Spec and plan lifecycle metadata are stale against the current implementation state.** `docs/specs/work-loop-review-verdicts/spec.md:3`. Disposition: rejected for the fresh pre-EXECUTE review phase. The user authorized a destructive reset and new run after the prior retry cap; `Draft` / `Drafting` are required until this run clears SPEC-PLAN-REVIEW and its human gates. The implementation and checked ACs are preserved evidence, not authority to skip the fresh gate.

**2. Light-mode mandatory adversarial review can still be treated as a skip.** `packs/core/.apm/skills/work-loop/SKILL.md:893`. Fix: require the light-mode adversarial pass; record absence as a mandatory missing outcome that emits `BLOCKED`.

## Concerns

**3. T6's done condition contradicts the projection work it requires.** `docs/specs/work-loop-review-verdicts/plan.md:295`. Fix: forbid hand-edited generated drift and unrelated cleanup while requiring regenerated projections to match their `.apm/` sources.

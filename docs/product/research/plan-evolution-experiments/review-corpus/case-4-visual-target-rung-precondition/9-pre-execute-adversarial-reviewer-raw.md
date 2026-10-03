## Blockers

**1. TDD-stub summary still excludes active T6.** `docs/specs/plan-evolution-experiments/plan.md:7`. The plan says T1 is the only exact Python/pytest red stub and all other tasks use non-stub modes, but T6 is an active TDD task with an exact red stub at `plan.md:481-512`, so approval would seal conflicting verification instructions before EXECUTE. Fix: Make the plan's TDD-stub declaration and active T6 task agree on which active tasks have exact red stubs before plan approval.

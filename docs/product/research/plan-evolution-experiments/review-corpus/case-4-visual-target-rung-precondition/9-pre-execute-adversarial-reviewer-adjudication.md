## Main-loop result
**1. [Blocker] 1: TDD-stub summary excludes active T6.** `docs/specs/plan-evolution-experiments/plan.md:7`. The plan summary says T1 is the only exact Python/pytest red stub and all other tasks are non-stub modes, while active T6 later declares TDD and embeds an exact red stub on lines 481-512; work-loop requires each task's verification mode and TDD stub to be stated before EXECUTE, and pre-EXECUTE review sustains test-shape conflicts that make plan approval seal contradictory verification instructions. Proposed mechanism adequate. Fix: update the TDD-stubs summary so it agrees with the active task list, preserving T6 as an exact TDD red-stub task or otherwise removing the blanket exclusion of all non-T1 tasks.

## Refuted audit
None.

## Indeterminate audit
None.

## Main-loop result
**1. [Blocker] 1: Review-policy allocation counts starts that the policies cannot launch.** `docs/specs/plan-evolution-experiments/spec.md:187`. Run 1 defines two three-start policies and one two-start closure policy across six tasks and three replications, so the stated Run 1 allocation of 162 and Run 7 allocation of 180 cannot be consumed by the declared policies; AC-0003 and AC-0012 require exact start allocations and exact balance reconciliation, and the proposed mechanism is adequate. Fix: Recompute the Run 1 and Run 7 allocations, maximum-used total, headroom, and executable balance checks from policy-specific review opportunities, or revise the closure policies so the stated starts are actually reachable without changing the comparison.
**2. [Blocker] 2: Closed legacy maps still reuse active task IDs.** `docs/specs/plan-evolution-experiments/plan.md:173`. The current map assigns active T6-T13 to collaboration outputs while the closed legacy map still assigns T1-T8 and T9 to legacy outputs, and the task section states T6 onward implements the amended collaboration study; AC-0003 requires an exact task split, and the proposed mechanism is adequate. Fix: Mark every closed-block task reference as non-routing legacy history or rename/remove the legacy task IDs so only active T6-T13 route executable collaboration work.

## Refuted audit
None.

## Indeterminate audit
None.

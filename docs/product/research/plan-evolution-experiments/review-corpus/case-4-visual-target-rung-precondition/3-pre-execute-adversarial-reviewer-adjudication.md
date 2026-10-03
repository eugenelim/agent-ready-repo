## Main-loop result
**1. [Blocker] 1: Wave-release boundaries are not canonically defined.** `docs/specs/plan-evolution-experiments/spec.md:231`. The gated Agent Rule points reservation refusal to "canonical allocation and stopping tables", but the target has Study allocation totals and a Sampling and stopping section rather than a stopping table, while AC-0002 says the request after a wave gate is refused; a runner can derive incompatible first-wave and post-gate release behavior from those gated surfaces. Proposed mechanism: adequate. Fix: add one canonical gate/release source that states wave release boundaries and post-gate refusal/proceed semantics, then make Agent Rules, AC-0002, and T1 derive from it.

## Refuted audit
None.

## Indeterminate audit
None.

## Main-loop result
**1. [Blocker] 1: T1 exact stub cannot pass contiguity.** `docs/specs/plan-evolution-experiments/plan.md:192`. The TDD stub uses strict adjacent zipping over release lists of unequal length, so the approved red/green stub raises before a correct implementation can satisfy the gated staged-release contract. Proposed mechanism: adequate. Fix: change the exact stub to compare adjacent releases without strict equal-length zipping while preserving the contiguous-release assertion.
**2. [Blocker] 2: W3 release conflicts with adaptive-reserve gating.** `docs/specs/plan-evolution-experiments/spec.md:85`. The canonical schedule releases W3 through the outer ceiling while also requiring a separate adaptive-reserve decision, and the current AC plus T1 stub let a W3 release reserve every W3 slot without modeling that separate reserve gate. Proposed mechanism: adequate. Fix: define adaptive-reserve ordinals and reserve-release semantics in the canonical schedule, then make Agent Rules, AC-0002, and T1 refuse those slots until the reserve decision exists.

## Refuted audit
None.

## Indeterminate audit
None.

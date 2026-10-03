## Main-loop result
**1. [Blocker] 1: Frozen task order is contradictory.** `docs/specs/plan-evolution-experiments/plan.md:56`. The plan makes task admission depend on a frozen order, but the stated rule, table row order, and T2 processing instruction do not identify the same order within several strata; that reaches admission and slot assignment, where reproducibility is required. Proposed mechanism: adequate. Fix: make one admission order authoritative and align the table plus T2 wording to that rule before any inference slot starts.
**2. [Concern] 2: Numeric ceiling copies remain in gated Agent Rules.** `docs/specs/plan-evolution-experiments/spec.md:87`. The spec makes the Study-allocation and Token/time-budget tables the sole numeric authority, but the gated Agent Rules repeat wave and study ceiling numbers later in the same contract; that creates a reachable sync hazard for the reservation gate. Proposed mechanism: adequate via the remove-copies branch. Fix: replace the hard-coded rule numerals with references or derived refusal checks from the canonical allocation and budget tables.

## Refuted audit
None.

## Indeterminate audit
None.

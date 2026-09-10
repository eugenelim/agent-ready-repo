# Repair provability audit — design

A deterministic, zero-model-call measurement of how often this repository's repairs ship with a
control that would fail if the repair were reversed. It replaces a second token-heavy paired cost
spike: the two-case V2 comparison cost roughly 70M tokens and six hours for two observations of a
quantity whose spread exceeded the threshold under test, while this audit buys 113 observations for
the cost of CI runs.

- **Status:** ready to run. Designed 2026-09-10 after V2 completed with a killed verdict under its frozen contract; the 10-case instrumentation gate runs first.
- **Owner:** eugenelim, Platform Core maintainer
- **Population:** reconstruct the 113 natural repair commits with a provable base using the
  historical selection method reported by the [focused re-review spike](work-loop-focused-re-review-spike.md),
  then freeze the derived list before the instrumentation gate. The prior raw preflight corpus was
  deliberately not retained; the count and strata below are findings to reproduce, not an input
  file to trust.

## Why this measurement

Across V1, V2, the spec-format audit and the shipped-script audit, one failure recurred in every
layer: **artifacts assert things that cannot fail.** P2's dispatched finding was "nothing killed
either `shaping_queue.active` branch". P2's baseline shipped a correct cooling fix whose reversal
left all 13 tests green, then — told exactly that — built a real killing control for the shaping arm
and re-created the identical unfalsifiable fix on the brief arm in the same commit. A shipped linter
emits 183 "conditional" warnings that fire on every clean run. Six of the controller's own
predicates in this spike passed while measuring the wrong thing.

None of that is a review-coverage problem. Eleven review rounds on one branch missed committed
conflict markers. It is that nothing is required to demonstrate a claim could have come out false.

## Strata

Classified from git metadata alone, no execution:

| Stratum | Count | Share | Oracle |
| --- | ---: | ---: | --- |
| source **+** test | 39 | 34.5% | revert the adjudicated source repair; observe the co-changed test |
| source only | 21 | 18.6% | revert; run recoverable pre-existing affected tests |
| docs only | 28 | 24.8% | deterministic before/after predicate, self-tested |
| test only | 25 | 22.1% | classify by finding intent, then choose the oracle |

**Correction, recorded because the first reading was wrong.** The 21 source-only repairs are *not*
"unable to carry a killing control by construction". They lack a **co-changed test**; a pre-existing
test may still kill the reversed repair. 34.5% + 18.6% is an upper bound on *repairs with no
test-change evidence*, not a count of unprovable repairs.

## Stratum 1 — source + test (n = 39)

Preconditions, all required before an outcome is recorded:

1. The repaired revision **passes first**. A repair whose own suite is red at HEAD is `unmeasurable`.
2. **Reverse only the adjudicated source repair** — not the whole commit, not the test changes.
3. The observed failure must **match the frozen closure predicate** for that repair event. A test
   that fails for an unrelated reason is not a kill.

Four outcomes, mutually exclusive:

| Outcome | Definition |
| --- | --- |
| **Semantic kill** | Reverting the source makes the new or changed test fail *for the dispatched defect*. |
| **Structural kill** | It fails only through compilation, import, or another incidental break. |
| **Survives** | The intended test stays green. |
| **Unmeasurable** | The repair hunk, test mapping, environment, or failure attribution cannot be isolated. |

Mixed-purpose commits and dependency failures are **unmeasurable, not failures** — classifying an
environment break as a survival would manufacture the result the audit exists to test.

**Power.** n = 39 can distinguish a widespread problem from a rare one. It will **not** support a
fine-grained threshold near 10%, and no such threshold should be read off it.

## Stratum 2 — source only (n = 21)

Revert the adjudicated source repair and run the **recoverable pre-existing affected tests**. Same
four outcomes. Where the affected suite is not deterministically recoverable at that revision, the
case is `unmeasurable`.

## Stratum 3 — docs only (n = 28)

The predicate discipline here is mandatory rather than advisory, because the controller's own
instrument-error rate on exactly this task was six defects in one case, four of which would have
mis-scored an arm and one of which would have produced a false kill.

For each case, in this order:

1. **Define the predicate before inspecting the repaired result.** Deriving it from the answer is
   how a predicate ends up testing imitation rather than closure.
2. **Prove it fails before and passes after.**
3. **Self-test the predicate with a known counterexample** — construct an input the predicate must
   reject, and confirm it rejects it. A predicate that passes on everything is the same defect
   class the audit is measuring.

## Stratum 4 — test only (n = 25)

Classify by finding intent first; the oracle follows from it:

- **Missing regression test** — needs a known-bad implementation or a controlled mutation to prove
  the new test can fail.
- **Repairing a faulty test** — needs a different before/after predicate: the old test passed when
  it should not have, so the oracle is that the *old* test admits the bad input and the new one
  refuses it.

## Instrumentation gate

**A 10-case instrumentation audit passes before scaling to all 113.** The ten cases are drawn across
strata, hand-checked, and the harness's classification compared against the hand result. Scaling on
an unvalidated harness would reproduce this spike's dominant failure at 113× the volume.

## Transfer limits

The 28 docs-only cases are a strong prototype for goal-based verification, but they are **not yet
direct evidence about all 307 goal-based verification-mode declarations** in the plan corpus. Those
declarations must be stratified before any result is transferred to them — a `Done when:` backed by
a build command and a `Done when:` backed by a prose judgement are not the same object, and 240 of
the 307 carry a command token while 9 carry neither `Tests:` nor `Done when:`.

## What this does not measure

Whether a repair was written test-first. That needs time-ordered commit or execution evidence which
is not consistently encoded in these artifacts, as the spec-format investigation established. This
audit measures whether the shipped control *can fail*, which is the property that matters for
regression safety and is the one the corpus can answer.

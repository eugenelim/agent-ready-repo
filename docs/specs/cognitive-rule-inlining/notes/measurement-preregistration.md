# Pre-registration — written before any run of this design

## Primary measure, and why it is the only one

Reading ease of the final reply. One measure, fixed in advance.

The rule names it itself: "For common chat prose, aim for a Flesch Reading Ease
score of at least 70 and a US school grade of at most 8." So the direction is
stated by the governing rule, not asserted by me — which was the defect in the
previous instrument. Everything else the scorer reports is descriptive context
and is not tested.

Grade level is NOT a second measure. It is affine in the same two ratios with
the opposite sign, so testing both would be one test counted twice.

## Design

- Arm order is NOT randomised in the pilot. That is a defect, recorded in the
  pilot record: every control run preceded every treatment run, so the arms are
  confounded with time. The contract run interleaves; `measurement-protocol.md`
  fixes that order and is the governing document for it.

- 3 tasks, admitted on a pilot draw that is discarded and never scored.
- 3 repetitions per arm per task. 18 scored runs total.
- Arms: unchanged tree, and a tree with the clauses inlined into root AGENTS.md.
- Identical prompt, fresh headless session every run.

## Hypothesis

Per task, the treatment arm's mean reading ease exceeds the control arm's.

## Test

Sign test across tasks. Under the null of no effect each task is a coin flip, so
3 of 3 in the predicted direction has p = 1/8 = 0.125 one-tailed. That is weak,
and it is stated as weak: this design can show direction and cannot establish
effect size.

## Decision rule, fixed now

- All 3 tasks move toward the target -> consistent with an effect; reported as
  direction only, never as a magnitude.
- 2 of 3 -> inconclusive.
- 1 or 0 of 3 -> no support for any claim that the clauses change reading ease.
  Stated over the measure, not over a spec section that can be edited under it.

## The noise floor this must clear

Each per-task difference is reported beside the pooled within-arm standard
deviation from the same runs. A difference smaller than that spread is reported
as not separable from noise, whatever the sign test says.

## What this cannot do

Separate the rule's effect from the effect of adding any text of similar length;
detect a small effect; transfer to another model version.

## Amendment, 2026-09-13

One bullet changed, before any scored run of the contract design and after the
pilot: the arm-order bullet said "this run" while describing the pilot's blocked
order, which would have read as governing the contract run that
`measurement-protocol.md` interleaves. The bullet now names the pilot and points
arm order at the protocol. Nothing else changed — not the measure, the
hypothesis, the test, the decision rule, or the noise floor. This note exists so
the change is visible rather than silent, since the run record commits this
file's SHA-256.

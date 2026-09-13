# Measurement record — a pilot of the clauses, not the contract's paired run

> **What this is not.** The contract's paired run compares the unchanged tree
> against the *finished* tree. That tree does not exist: T3 has not run, the seed
> `AGENTS.md` is untouched, the topic file is not deleted, no prose is pruned.
> This run compares the unchanged tree against the same tree with the chat
> clauses hand-inlined into root `AGENTS.md`, reverted afterwards. It is a pilot
> of the clauses. The paired run AC13 defines is still owed at T6.

## Provenance

- **Run date:** 2026-09-13. First scored reply 14:02:48, last 14:17:23.
- **Pre-registration written:** 14:01:52, before the first reply.
- **Pre-registration SHA-256:** `a9e8ad5c25681efa096244621d07ef57e438f363b16094a8ed7f1513765412eb`
  Recorded here so priority survives the raw transcripts, which are gitignored.
- **Host:** Claude Code, `claude -p --output-format=stream-json`
- **Model identifier:** session default (Opus 5; `claude-opus-5`)
- **Base SHA, both arms:** `dac83a5afb4f7409fbd4115211f3080a7640748d`
- **Treatment arm carries no SHA.** It was a working-tree mutation, reverted. It
  cannot be re-derived. A future run commits both arms so each has one.
- **Scorer:** `tools/score-cognition.py`

## Corrections, 2026-09-13

1. The first version reported a spread of 4.78 and "0 of 3" differences clearing
   it. 4.78 is the arithmetic mean of the six arm standard deviations; the
   pre-registration names the **pooled** figure, 4.97. The comparator was
   also wrong — a difference of two means was read against the spread of single
   observations rather than the standard error of a difference, 4.06. Against
   the correct comparator all three differences exceed one standard error.
2. A stated bound ("the effect sits below roughly 5 points") has been withdrawn.
   It was not pre-registered and is not supportable at this n; see Reading.

## Per-task reading ease

| task | control runs | control mean | treatment runs | treatment mean | difference | \|d\|/SE | 95% CI |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| t1 | 66.92, 63.57, 57.27 | 62.59 | 70.65, 59.66, 71.38 | 67.23 | +4.64 | 1.14 | [-6.6, +15.9] |
| t2 | 51.33, 43.45, 51.32 | 48.70 | 53.39, 56.11, 50.12 | 53.21 | +4.51 | 1.11 | [-6.8, +15.8] |
| t3 | 61.82, 60.31, 55.39 | 59.17 | 48.13, 60.77, 55.14 | 54.68 | -4.49 | 1.11 | [-15.8, +6.8] |

- Pooled within-arm SD: **4.97** (SS 296.38 on 12 df)
- Standard error of a 3-vs-3 difference of means: **4.06**
- Largest |t| = **1.14** at df=4. Not significant.
- Tasks toward the target: **2 of 3** — inconclusive by the pre-registered rule.

## Two defects in this run's design

**The arms are confounded with time.** Every control run preceded every treatment
run, 14:02:48 to 14:17:23, arm-outermost with no randomisation. Service-side
drift across that window is indistinguishable from the treatment. Repetition does
not fix this: ninety runs in two blocks are still two blocks. A future run
interleaves arms and pre-registers the order.

**The test could not have reached significance.** The pre-registration's own
arithmetic gives p = 0.125 for the best possible outcome, 3 of 3. Eighteen runs
were spent on a test non-significant at its ceiling. The run demonstrates the
instrument; it establishes nothing about the clauses in either direction.

## Reading

Nothing separable was found, and the run sets **no bound**. A 95% interval on
t1's difference spans roughly −6.6 to +15.9: the data are consistent with a
large effect and with none.

What the run did establish is that an earlier single-sample spike reporting
+9.16 on the hardest task was noise — repeated, the same task gives +4.51
against a 4.06 standard error. Retiring that figure is this run's result.

## Unmeasured

None. Every reply cleared the scorer's 30-word floor.

## What resolving it would cost

At the corrected pooled SD, roughly **16 repetitions per arm per task** to resolve
five ease points — about 96 runs across three tasks — and **44 per arm** for three
points. Both figures assume the time confound is removed first, since it is not
reduced by n.

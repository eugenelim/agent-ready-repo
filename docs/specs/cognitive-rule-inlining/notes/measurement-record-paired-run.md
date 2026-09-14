# Measurement record — the contract's paired run

The run AC13 owes: the unchanged tree against the *finished* tree, arms
interleaved, three repetitions each. The pilot under
[`measurement-record.md`](measurement-record.md) does not close this; it compared
a hand-inlined root `AGENTS.md` and ran its arms in two time-blocks.

**Result: inconclusive, by the decision rule fixed in advance.** Two of three
tasks moved toward the target, which the pre-registration defines as
inconclusive. No per-task difference reaches the standard error it is read
against. The design cannot tell a small effect from noise, and this run did not.

## Provenance

- **Run date:** 2026-09-13. First scored reply 23:38:03Z, last 23:55:16Z.
- **Pre-registration SHA-256:**
  `60f4f292be36bab3727c5bc2c2bb622b2e44b671100d09ef5799dd3717004da6`
  (committed in `45ee4db3d`, before the first reply; carries a dated amendment
  note for the one bullet changed after the pilot)
- **Protocol SHA-256, as run:**
  `2ee255f54203a1e539a9842c91fcaa66df6f4309789b42ffab95aa5ddc73d6c9`
- **Protocol SHA-256, as committed:**
  `37ffd0f5a3e4ad8e05794b295351875d6e6ab627dddff84b6d8c8b81e98b5d5c` — a review
  found a trailing blank line at EOF that failed `git diff --check`, and removing
  it after the run changed the hash. The two files differ by that one line and
  nothing else; every prompt is byte-identical. Both hashes are recorded because
  citing only the second would claim the run used a file it did not.
- **Control arm SHA:** `dac83a5afb4f7409fbd4115211f3080a7640748d`
- **Treatment arm SHA:** `45ee4db3d`. This is the finished state of the two
  `AGENTS.md` files, which are the whole surface the measurement reads — not the
  finished state of the branch. Later commits (`dba24e465` onward) change the
  catalogue lint, its tests, and this record; a session could in principle read
  those files, so the arm is named by what it is rather than called "the finished
  tree", which it is not.
- **Arms:** two `git archive` extractions, neither carrying `.git`. A worktree
  would have shared the object store with the live branch.
- **Permission mode:** `--allowedTools Read,Grep,Glob` — read-only, no
  network-reaching tool. Read tools are the measurement.
- **Host:** Claude Code, `claude -p --output-format=stream-json`
- **Model identifier:** `claude-sonnet-4-6`. Established by an identical probe
  run from the same control arm twenty minutes after the last scored reply, not
  captured per run — the harness kept only the `result` event and discarded the
  `system`/`init` event that names the model. That is a harness defect, fixed
  for later runs. Note this is **not** the parent session's model: `claude -p`
  takes its own default.
- **Scorer:** `tools/score-cognition.py`
- **Arm order actually used:** interleaved, arm as the inner loop — for each
  repetition, each task ran control then treatment before the next task began.
  This matches the protocol. It is checkable against `timeline.txt` in the
  artifact directory, which timestamps all eighteen replies in run order.
- **Incidental-content review:** the eighteen replies were scanned for personal
  identifiers, home paths, and credential shapes before this record was written.
  One match, benign: the phrase "Status-token" in `control-T3-r2.md` hit the
  `token` pattern. No reply text is reproduced in this record.
- **Raw replies:** `.context/ablation/20260913T183718/` (gitignored). No reply
  text is reproduced here.

## Per-task reading ease

Pooled within-arm SD **5.89** across six arms (SS 415.78, df 12, n=3 per arm).
The standard error of a difference of means is **4.81**. That standard error,
not the spread of single observations, is the comparator.

| Task | Control | Treatment | Difference | \|t\| | Read as |
| --- | ---: | ---: | ---: | ---: | --- |
| T1 | 59.71 | 62.69 | +2.98 | 0.62 | not separable from noise |
| T2 | 52.65 | 55.22 | +2.57 | 0.53 | not separable from noise |
| T3 | 57.26 | 56.70 | −0.56 | 0.12 | not separable from noise |

Two of three moved toward the target. The pre-registered rule calls that
inconclusive, and no difference clears one standard error, so the sign count is
the weaker of two reasons to claim nothing.

## Every quantity, both arms

Means over nine replies per arm. Differences are treatment minus control. None
is tested; only reading ease was pre-registered, and the rest are descriptive
context the scorer reports without asserting a direction.

| Quantity | Control | Treatment | Difference | Unmeasured |
| --- | ---: | ---: | ---: | ---: |
| Reading ease | 56.54 | 58.20 | +1.66 | 0 of 18 |
| Grade level | 8.74 | 9.05 | +0.31 | 0 of 18 |
| Scored share of words (%) | 64.87 | 66.52 | +1.66 | 0 of 18 |
| Table rows | 13.78 | 15.78 | +2.00 | 0 of 18 |
| Table density | 2.25 | 2.63 | +0.38 | 0 of 18 |
| Jargon density | 9.24 | 10.04 | +0.81 | 0 of 18 |
| Raw words | 569.00 | 560.00 | −9.00 | 0 of 18 |

Grade level is not a second result. It is affine in the same two ratios with the
opposite sign, so its +0.31 is the ease difference restated, not a second signal
pointing the other way.

Every reply cleared the scorer's 30-word floor, so no quantity is recorded as
unmeasured in this run. Had one not cleared it, the cell would read `unmeasured`
rather than `0`.

## What this run establishes, and what it does not

It establishes that the inlined clauses do not produce a reading-ease change this
design can resolve, on `claude-sonnet-4-6`, on these three tasks, at three
repetitions per arm. It is consistent with a small positive effect, with no
effect, and with a small negative one.

It does not establish that the change is inert. The clauses now reach a session
without two model-directed tool calls that could be skipped silently; that is the
outcome the change delivers, and it is structural rather than measured here.

## The comparator, and where the pre-registration disagrees

The pre-registration's noise-floor section says a difference smaller than the
**pooled standard deviation** is not separable from noise. This run reads each
difference against the **standard error of a difference of means** instead. That
is a real disagreement between the two documents and it is not a post-hoc
choice: the pilot record's corrections section, committed before the first
scored reply here, establishes that reading a difference of two means against
the spread of single observations is the wrong comparator, and the spec's run
criteria name the standard error. The pre-registration section was not updated
with that correction, which is a defect in the pre-registration rather than in
this run.

It changes no verdict here. Against the SE, 4.81, the largest |t| is 0.62;
against the pooled SD, 5.89, every difference is smaller still. Both comparators
return "not separable from noise" for all three tasks.

## The price of resolving it

At the SD this run measured, 5.89, a two-sided 95% test with 80% power needs
about **22 repetitions per arm per task** to resolve a 5-point difference — 132
runs across three tasks — and about **61 per arm** for 3 points, or 366 runs.

An earlier version of this section said 16 and 44. Those figures are correct for
the pilot's SD of 4.97 and wrong for this run's; the spread is what sets the
price, so a power claim carried over from an earlier run understates it.

## Reading against the pilot

The two runs used the same three prompts, so they can be compared — but only
quantity against matching quantity.

| Comparison | Pilot | This run |
| --- | ---: | ---: |
| Pooled mean difference, all three tasks | +1.55 | +1.66 |
| T1 difference | +4.64 | +2.98 |
| T2 difference | +4.51 | +2.57 |
| T3 difference | −4.49 | −0.56 |

The pooled estimates are within 0.11 points of each other across two independent
runs. Both sit far inside their own noise floors, so the agreement is not
evidence of an effect — two runs can agree closely on an estimate of nothing.

The three per-task differences share a sign across both runs. That is an
observation made after seeing the data, not a pre-registered test, and at three
repetitions per cell it is weak; it is recorded because suppressing it would be
choosing which post-hoc patterns to mention.

An earlier version of this section chained "+9.16 → +4.51 → +1.66" and read it as
an effect shrinking under better design. Those are three different quantities: a
single-sample difference on one task, the pilot's T2 per-task mean difference,
and this run's pooled mean across all three. Lined up they look like a trend;
matched properly, as above, no such trend exists. An inconclusive run cannot
establish a causal story about selection either way.

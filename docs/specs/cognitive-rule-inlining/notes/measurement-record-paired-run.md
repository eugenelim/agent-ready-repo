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
- **Protocol SHA-256:**
  `2ee255f54203a1e539a9842c91fcaa66df6f4309789b42ffab95aa5ddc73d6c9`
- **Control arm SHA:** `dac83a5afb4f7409fbd4115211f3080a7640748d`
- **Treatment arm SHA:** `45ee4db3d` — the finished tree. The later
  `dba24e465` changes only the catalogue lint and its tests, not either
  `AGENTS.md`, so it is outside what the arms compare.
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

## The price of resolving it

Roughly sixteen repetitions per arm per task — about ninety-six runs — to resolve
a 5-point effect; nearer forty-four per arm for 3 points. That is a cost
decision with a stated price, not a design flaw.

## Reading against the pilot

The pilot's single-sample +9.16 fell to +4.51 on repetition, and falls again to
+1.66 here on the pooled means. Each step added repetition or removed a
confound, and each step shrank the estimate. That pattern is what selecting on
one draw looks like from the other side.

# Review-loop efficiency with headless Codex workers

## Result

Cold closure is the best candidate for the next validation round. It used one
broad review on the first revision and one fresh broad review on the final
revision, skipping the middle pass. Against full replay on every revision, it
used 33.3% fewer review starts and input tokens, 30.6% fewer review words, 64.9%
less churn prose, and 32.5% less summed worker time. Its observed defect recall
was 1.39 percentage points lower, while precision was 3.49 points higher.

This is promising, not conclusive. The task-cluster bootstrap interval for the
recall difference was -9.26 to +4.17 percentage points. That range crosses the
predeclared five-point quality margin, so this six-task study does not establish
non-inferiority. It supports another closure-focused experiment with more
independent tasks, especially complex ones.

Focused rereview did not deliver an efficiency gain in this design. It used the
same number of starts and almost the same input tokens as full replay because
each reviewer still received the complete current artifact for grounding. It
produced 6.5% more words, 5.7% more output tokens, and 3.8% more summed worker
time. It reduced churn prose by 20.4% and improved precision by 2.69 points, but
its observed recall was 2.78 points lower. A focused policy needs a genuinely
smaller context packet, not just a narrower instruction, before it can be
expected to save tokens.

## Experiment

The study used six synthetic repository-planning tasks: three medium and three
complex. Each task had three frozen revisions with registered defects and
acceptance atoms. Three policies were crossed with three cold replications per
task, yielding 54 trajectories:

- **Full replay:** broad cold review on revisions 1, 2, and 3.
- **Focused rereview:** broad review on revision 1, then changed material and
  affected invariants on revisions 2 and 3.
- **Cold closure:** broad review on revision 1, skip revision 2, then a fresh
  broad closure review on revision 3.

The run completed 144 independent reviewer starts and 12 blind adjudicator
starts. A separate eight-start transport calibration passed before collection.
The controller requested `gpt-5.6-luna`; the served model identity was not
observable and is not claimed. Findings are a non-inferential bounded case
study, with task—not individual worker—as the unit of generalization.

## Policy comparison

All three policies covered 18 task-replication trajectories. Closure has fewer
review cells because it intentionally omits the middle review.

| Measure | Cold closure | Focused rereview | Full replay |
| --- | ---: | ---: | ---: |
| Review starts | 36 | 54 | 54 |
| Starts per trajectory | 2 | 3 | 3 |
| Known-defect recall | 62.50% | 61.11% | 63.89% |
| Precision | 95.74% | 94.94% | 92.25% |
| False-positive rate | 4.26% | 5.06% | 7.75% |
| Raw words | 4,410 | 6,764 | 6,353 |
| Churn words | 136 | 308 | 387 |
| Input tokens | 817,402 | 1,227,128 | 1,225,994 |
| Output tokens | 18,940 | 30,112 | 28,486 |
| Summed worker time | 567.77 s | 873.25 s | 841.58 s |

Closure's average review was not shorter: it produced about 122.5 words per
review versus 117.6 for full replay. Its gain came from removing a whole review
round. Per trajectory, closure used about 45,411 input tokens versus 68,111 for
full replay and 7.6 churn words versus 21.5.

Neither alternative cleared the five-point quality decision gate with task-
cluster uncertainty:

| Contrast with full replay | Recall difference | Task-cluster 95% interval | Five-point non-inferiority established? |
| --- | ---: | ---: | --- |
| Cold closure | -1.39 points | -9.26 to +4.17 | No |
| Focused rereview | -2.78 points | -10.18 to +3.70 | No |

The intervals use 20,000 deterministic task-cluster bootstrap resamples with
seed `20260928`. Only six clusters were available, so the intervals are wide.

## Complexity mattered more than policy

The three medium tasks averaged 75.0% recall and 97.45% precision. The three
complex tasks averaged 50.0% recall and 90.81% precision. Every policy averaged
50% recall on each complex task. `agentbundle-engine-stragglers` also generated
most of the false-positive and churn burden.

The 25-point medium-to-complex recall gap is much larger than the observed
policy differences. The next study should stratify and power by task
complexity. A blanket review policy is less defensible than a risk-tiered one:
closure for bounded medium work, with an extra focused or broad pass reserved
for complex or high-consequence changes.

## What the checkpoints showed

Overall recall was stable from the first checkpoint onward: 64.58% at 24
reviews, 63.54% at 48, 63.89% at 72, 63.02% at 96, 62.50% at 120, and 62.50%
at 144. No checkpoint recorded a process failure, tool-use violation, or
protocol deviation. This stability makes the final direction less likely to be
an artifact of only the last launch block, although the policy mix at early
checkpoints was not yet balanced.

Checkpoint precision was deliberately conservative before blind adjudication.
The final precision values are higher because adjudicators reconciled duplicate
wordings and sustained valid findings. Four adjudication candidates received
no judgment; they were counted as not sustained and were not imputed.

## Implications for review loops

The evidence argues against replaying the entire review after every plan or
spec amendment. In this corpus, a fresh closure review after the work settled
captured nearly the same share of registered defects at materially lower cost
and with less repeated prose. The practical next policy to test is:

1. Review the initial contract broadly.
2. Let the plan or implementation evolve without automatic full-review replay.
3. Trigger an extra pass only for a named high-risk change or complex task.
4. Run one fresh broad closure review before execution or merge.

This experiment does not answer whether a separate specification and plan are
better than one combined artifact. It also does not compare stronger models in
pre-execution work against stronger models during implementation. Those require
separate construction and model-placement experiments.

## Integrity and limits

- Eight of eight calibration starts passed all transport and schema gates.
- All 144 reviewer and 12 adjudicator reservations have one terminal record.
- No reviewer or adjudicator used a tool, failed its process, or reported a
  protocol deviation.
- One pre-model schema rejection was quarantined and did not consume an
  experimental model start. A uniform, semantics-preserving transport schema
  adaptation was then applied without changing worker payload bytes.
- Five prematurely written checkpoints were preserved as void controller
  artifacts and replaced at the correct terminal counts; no worker allocation
  or output was affected.
- Workers could see the repository through a read-only sandbox. Absence of an
  observed tool call is not proof of filesystem confinement.
- Summed worker time includes orchestration and concurrency effects; it is not
  elapsed makespan.

The durable numeric record is
`docs/product/research/plan-evolution-experiments/codex-headless-review-policy-run-1.json`.
Raw prompts, events, responses, receipts, checkpoints, and adjudication
artifacts remain under
`.context/experiments/codex-headless-via-claude-r1/`.

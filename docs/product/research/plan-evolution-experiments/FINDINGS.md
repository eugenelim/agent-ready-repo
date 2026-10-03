# Plan evolution experiments: findings against the goals

Compiled 2026-10-02. This is the summary view of the whole programme. It
replaces the raw corpora in the working tree; see § *Where the raw material
went*.

## The goal, and whether it was met

The pilot set out to test **13 hypotheses** (H1–H13) about how planning,
construction and review should be organised, under a 240-process ceiling.

**None of the 13 was answered.** Every hypothesis is recorded `unavailable`,
for one of two reasons:

| Hypotheses | Blocking reason |
| --- | --- |
| H1–H5, H8, H10, H12, H13 | the W1 gate did not release W2, so no core inferential slot was ever legal to launch |
| H6, H7, H9 | T5 stopped before producing any legal core builder output, so no blinded subject existed to review |

The instrument never cleared calibration: **8 calibration slots, 16 failed
slots, `inference_launch_permitted: false`, 0 inferential processes started.**
W1 closed `W2-unavailable`, W2 closed `stopped-before-core`, and the T6 review
allocation closed `unavailable-before-subject-selection`.

So the programme produced **no inferential result of the kind it was designed
to produce.** That is the honest headline and it should not be softened.

## What was learned anyway

The yield came from arms that were never the plan: bounded, non-inferential case
studies run on a headless Codex surface, plus one retrospective baseline and one
prospective review cohort. Every claim below is descriptive and corpus-bound.

### Review policy — the strongest practical result

**One broad review, then repairs, then one cold closure review, beat reviewing
after every repair.** On a 12-subject corpus it matched full replay on every
graded end-state quality value while using **12 fewer review starts, 295,027
fewer tokens, 244 fewer worker seconds and 583 fewer churn words**.

An earlier six-task run pointed the same way: cold closure used **33.3% fewer
review starts and input tokens, 64.9% less churn prose, 32.5% less worker
time**, with recall 1.39 points lower and precision 3.49 points higher.

**Neither establishes non-inferiority.** The six-task bootstrap interval for the
recall difference was **−9.26 to +4.17 points**, which crosses the predeclared
five-point margin. The 12-subject run had only five known defects and defined
final-review recall for three subjects, where both policies found none. These
are efficiency results, not defect-detection results.

### Authority beats document shape

The clearest finding of the construction-panel block was **not** about file
layout. When a worker could amend a construction plan while preserving the
stable outcome, it adapted in **every** returned response. When the plan was
frozen, it **never** amended and recorded a conflict in **14 of 17** responses.

Separating spec from plan showed **no** quality benefit: a unified contract
matched the separate-file baseline on semantic coverage, acceptance mapping and
scope control, using 83 fewer output tokens and 20 fewer words per matched task.
Lexical measures were near ceiling over six clusters, so this is descriptive.

Keeping the same worker from planning into construction was a poor trade: it
used **2.14× the input tokens and 1.65× the output tokens**.

### A stronger model did not pay at either stage

No support for routing a stronger model to planning or construction by default.
Against an all-standard route, a stronger planner gave **0.08 fewer** final
correct decisions and **0.17 more** residual severe errors for **1,154 more**
output tokens; a stronger constructor gave **0.17 fewer** correct decisions and
**0.17 more** severe errors for **610 more** output tokens. Quality differences
are within noise at four tasks; **the cost increases are not.**

### The review-effectiveness cohort

Closed **incomplete** on 2026-10-02 — it could not answer its own frozen
question for three independent reasons, two of them retroactive and
unrecoverable. [`review-effectiveness-report.md`](review-effectiveness-report.md)
§ *Prospective cohort result* owns that outcome. What it does support:

- **The adjudicator does the load-bearing work.** 31 raw findings → 9 sustained,
  **22 refused**. Twice a refusal prevented a repair that would have
  reintroduced a mechanism the spec forbids.
- **The repairing agent generates most new findings.** Rounds 2–7 of one case:
  **16 of 21** sustained findings were defects introduced by the previous
  round's repair. One case, not two — an earlier "replicated" claim was wrong.
- **Cutting is not safer than adding.** A repair that added drew 7 of 8 findings
  against its additions; the repair that then cut dropped a real obligation.
- **Review caught two defects in the governed work across seven rounds.** Real
  and consequential, far too thin to generalise.

## The finding that outranks all of them

**Three of four arms died of measurement and recording failures, not of the work
being studied.**

- The workbench arm never cleared instrument calibration — 16 failed slots.
- The review-effectiveness cohort published counts while the material behind
  them sat in gitignored directories, and required per-finding telemetry nobody
  ever wrote down.
- Across the research records, **78 `.context/` paths were cited as evidence and
  7 were already gone** before anyone checked.

Every one is the same mistake: **evidence recorded somewhere nothing preserves,
or not recorded at all while the work ran.** Host telemetry is session-local; a
measurement not written during the run is gone when it ends, and estimating it
afterwards is barred.

**A successor's first task is the recording path, not the hypothesis.** Write
per-finding rows as each round closes, split returned tokens into input and
output per start, capture attribution per event as it happens, and calibrate
ceilings against a cache-warming host — the frozen per-case ceiling was exceeded
**3.53×** by the first measurement start.

## Where the raw material went

The raw corpora were extracted into this directory and then compacted out of the
working tree, so nothing was lost and the repository stays light.

| Corpus | Size | Status |
| --- | --- | --- |
| Review corpus — cases 2, 3, 4 | 128 files, 1.0 MB | in history, compacted from the tree |
| Controller artifacts — cited, digest-pinned | 46 files, 3.46 MB | in history, compacted from the tree |
| Headless per-slot prompts and transcripts | ~7,600 files, ~46 MB | **never tracked**, local-only, will not outlive the checkout |

Both extracted sets landed in the commit *"docs(research): make the studies
stand alone, and extract their cited evidence"* (2026-10-02) and are
retrievable with `git log --diff-filter=D --name-only` over this directory.

Of the extracted controller artifacts, 38 of 46 verified against a digest pinned
in a tracked record. One was redacted to remove an absolute home path, so its
digest deliberately differs.

The durable derived records — `results.json`, `evidence-index.json`, the gate
memos, the per-run JSON and reports, and the review-effectiveness ledger —
remain tracked and are the authority for every number above.

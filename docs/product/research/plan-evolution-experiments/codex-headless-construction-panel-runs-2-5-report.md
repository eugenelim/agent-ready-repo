# Construction handoff experiment: independent evidence report

Date: 2026-09-28  
Evidence block: `codex-headless-via-claude-runs2-5-r1`  
Evidence class: bounded, non-inferential case study  
Status: complete

## Result

The clearest result is about authority, not document shape. When the worker was
allowed to amend a construction plan while preserving the stable outcome, it
adapted in every returned response. When the plan was frozen, it never amended
and recorded a conflict in 14 of 17 returned responses.

The experiment did not find a quality benefit from keeping the specification
and plan in separate files. A unified contract matched the separate-file
baseline on detected semantic coverage, acceptance mapping, and scope control.
It also used 83 fewer output tokens and 20 fewer response words per matched
task on average. These are descriptive results, not proof that one file is
always better: the lexical quality measures were near their ceiling and only
six task clusters were sampled.

Keeping the same worker from planning into construction was a poor trade in
this block. It used 2.14 times the input tokens and 1.65 times the output tokens
of a fresh constructor, while its decision score was 0.78 lower per task. It
finished about 3.25 seconds faster and emitted 99 fewer visible words, but the
token and decision costs outweigh that modest latency gain for this workload.

Extra narrative prose showed no detected quality gain. That treatment is
weaker than its artifact word ratio suggests: its planning artifact was about
55% longer, but total model input rose only 1.6% because fixed instructions and
repository context dominated the prompt. The result therefore tests a modest
total-context dose, not large-plan verbosity in general.

## Study design

Six repository tasks were crossed with three replications and five handoff
policies, for 18 matched blocks and 90 reserved construction cells. Three tasks
were classed as medium and three as complex. Each worker received the same task
facts, acceptance atoms, discovered construction evidence, boundaries,
requested model route, response schema, and read-only repository visibility.

The five policies were:

1. Separate stable-outcome specification plus a thin, amendable plan, given to
   a fresh constructor. This is the baseline.
2. The same separate artifacts and a fresh constructor, but with amendment
   forbidden and conflict recording allowed.
3. The same obligations in one unified, amendable contract and a fresh
   constructor.
4. The same separate, amendable artifacts with controller-generated rationale
   and sequencing prose, given to a fresh constructor.
5. The same byte-identical baseline artifacts, but construction continued in
   the plan author's session.

Mechanical checks passed for all 18 blocks: the unified arm carried the same
obligation atoms, the narrative arm added no obligation, the continuity arm's
artifact was byte-identical to baseline, and the frozen arm differed only in
the authority clause. The narrative artifact was 1.475 to 1.586 times the
baseline artifact's word count.

Four calibration starts passed before the main panel. Eighteen independent
plan-author starts then produced the common planning inputs. All 18 covered
every acceptance atom and echoed the stable-outcome digest. One author returned
an inexact alias; it was retained and disclosed.

## Measurements

Structural measures checked scope paths, acceptance mapping, artifact identity,
amendment fields, and tool events. Lexical measures checked whether frozen
keyword groups appeared; they measure wording coverage rather than reasoning
quality. Decision correctness and self-audit measures were scored against a
controller-only registry frozen before construction.

Each arm was compared with the baseline inside the same task and replication.
Task effects were then summarized across the six tasks. The reported intervals
come from 20,000 deterministic resamples of six task clusters. They describe
the spread of this small task set and are not significance tests.

## Outcomes by arm

| Arm | Returned | Coverage | Correct decisions | Input tokens | Output tokens | Response words | Seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Separate, amendable, cold | 18 | 0.9889 | 3.6111 | 23,391.6 | 1,172.1 | 351.9 | 25.99 |
| Separate, frozen, cold | 17 | 1.0000 | 3.2353 | 23,394.4 | 1,070.2 | 275.3 | 24.58 |
| Unified, amendable, cold | 17 | 0.9882 | 3.4118 | 23,384.1 | 1,101.8 | 336.5 | 25.18 |
| Narrative, amendable, cold | 16 | 0.9875 | 3.0625 | 23,755.2 | 1,166.9 | 329.9 | 26.43 |
| Separate, amendable, same worker | 18 | 0.9778 | 2.8333 | 50,071.2 | 1,930.8 | 252.6 | 22.74 |

All 86 returned construction responses mapped every acceptance atom and made
no detected scope addition. Coverage ranged from 0.978 to 1.000, which is a
ceiling effect rather than evidence that every response reasoned equally well.

### Amendment behavior

| Arm | Amendments | Valid | Invalid | Conflicts instead |
| --- | ---: | ---: | ---: | ---: |
| Separate, amendable, cold | 18/18 | 17 | 1 | 0 |
| Separate, frozen, cold | 0/17 | not applicable | not applicable | 14 |
| Unified, amendable, cold | 17/17 | 16 | 1 | 0 |
| Narrative, amendable, cold | 16/16 | 16 | 0 | 0 |
| Separate, amendable, same worker | 18/18 | 16 | 2 | 0 |

This is a complete behavioral separation on amendment use. It does not by
itself prove that every amendment was good: four of 69 amendments were invalid
under the frozen amendment schema.

### Matched contrasts against the separate, amendable, cold baseline

| Treatment | Detected quality | Cost and output | Interpretation |
| --- | --- | --- | --- |
| Frozen | Correct decisions -0.42; contradictions +0.11; self-audit false positives +0.28 | 81 fewer words; 110 fewer output tokens; 1.60 s faster | Cheaper because it reports the conflict instead of adapting. It is not an equivalent completion policy. |
| Unified | Coverage, omissions, acceptance, and scope differences all 0; correct decisions -0.25 with a wide interval | 20 fewer words; 83 fewer output tokens; 1.08 s faster | No detected benefit from separate files. A unified contract is the simpler live candidate. |
| Narrative | Coverage, omissions, acceptance, and scope differences all 0; correct decisions -0.64 | 23 fewer words; 10 fewer output tokens; 0.42 s slower | Added meta-prose did not help, but it was only a 1.6% total-input increase. |
| Same worker | Coverage -0.011; correct decisions -0.78, with five of six tasks favoring the cold baseline | 26,680 more input tokens; 759 more output tokens; 99 fewer words; 3.25 s faster | Session continuity compressed visible prose and latency but increased hidden context cost and reduced decision quality. |

The same-worker decision interval was -1.61 to -0.11. Excluding the one
probe-contaminated continuity cell did not weaken this concern: mean decision
correctness fell from 2.83 to 2.76, coverage fell from 0.978 to 0.976, and mean
input remained 48,821 tokens across the other 17 cells.

## What this changes

For this workflow, lock the outcome, acceptance conditions, boundaries, and
verification obligations. Do not lock the construction decisions. Require a
small amendment record that names the trigger evidence, changed decision,
affected tasks and checks, and the unchanged outcome digest.

Treat separate specification and plan files as an organizational choice, not a
quality control. A unified contract may be used when it preserves the same
stable and amendable fields. Separation should earn its cost through another
need, such as ownership, lifecycle, or selective loading; this study supplies
no quality evidence for it.

Use a fresh construction worker with the current contract instead of resuming
the planner by default. Carry forward the approved artifact, not the full
planning conversation. This agrees with the separate review-policy experiment,
where a closure packet reduced starts, tokens, prose, and churn, though the two
provider-separated blocks are not pooled.

Do not infer that all extra rationale is waste. The experiment used generated
meta-prose, not high-quality rationale, and its total-token treatment was small.
A later run should compare concise decision grounds with irrelevant prose at a
larger controlled share of total context.

## Reliability and incidents

The controller reconciled 112 reservations: 4 calibration, 18 plan-author, and
90 construction terminals. It observed 123 CLI starts, 108 model starts, 18
continuations, 11 provable zero-model-start failures, no tool-use violations,
and 2,593.94 seconds of controller wall clock. No response was repaired,
retried, or replaced after an observed or possible model start.

The 11 zero-start failures came from unsupported flags on `codex exec resume`.
They had no event, session, usage, or message record, so they were quarantined
and relaunched with byte-identical payloads after the transport spelling was
fixed.

Four cold cells were orphaned when the controller killed its driver. A model
start could not be ruled out, so they were closed, never relaunched, and
excluded rather than scored as zero. This left 86 returned construction
responses and two incomplete matched blocks.

One continuity session received a trivial transport probe before construction.
It carried no task or grading content. The primary result retains and names the
cell; the sensitivity calculation above excludes it.

Before construction, the controller added a mechanical rule that voids a
contradiction marker when the marker appears verbatim in worker-visible input.
Two text collisions caused four block-level marker instances to be voided; 101
markers remained. The rule had no hand-picked exceptions, and both original
and corrected counts remain in the source receipt.

## Limits

- The controller requested `gpt-5.6-luna`, but the served model identity was
  not observable. This report makes no served-model claim.
- Lexical coverage was near ceiling and cannot establish reasoning quality or
  equivalence between document shapes.
- Six task clusters are too few for broad statistical inference. Results are
  directional evidence for this corpus.
- Four missing cells make two blocks incomplete. Matched contrasts drop only
  the unavailable pair and do not impute it.
- The narrative treatment increased artifact words sharply but total input
  only slightly, so it is not a strong test of large-context verbosity.
- Wall clock includes orchestration at up to four concurrent processes and is
  not end-to-end delivery time.
- The continuation CLI invocation differed from cold starts even though both
  requested the same working directory and read-only sandbox.
- Workers could see the read-only repository. No tool event occurred, but that
  observation is not a proof of process or data confinement.
- Requested model, provider surface, and task corpus are held within this
  block. Results are not pooled with Claude subagent runs, direct Codex
  collaboration runs, or the earlier headless review-policy run.

## Evidence integrity

The independent review verified every published digest for accounting,
aliases, artifact index, author measures, blinding check, block registry,
calibration gate, construction measures, matched contrasts, design freeze,
equivalence proofs, grading amendment, hidden registry, and launch order.

The source handoff digests are:

- JSON receipt: `sha256:b51fb1ac58489d81b10f1b3f69b676a93820b55cb0d31a12f4aee2e9e6e8a187`
- Provider report: `sha256:d6fb713b5f1f78a8e889947b6bd57d5a6b601d28081addf6f08bb4065b9bbad6`

The durable JSON beside this report records the summary measures, incidents,
source digests, and decision implications needed to interpret the result. Raw
payloads, event streams, reservations, and receipts remain under
`.context/experiments/codex-headless-via-claude-runs2-5-r1/`.

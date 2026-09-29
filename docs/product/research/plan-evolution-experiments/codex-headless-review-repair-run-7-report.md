# Review-and-repair loop policy: independent evidence report

Date: 2026-09-29  
Evidence block: `codex-headless-via-claude-run7-r1`  
Evidence class: bounded, non-inferential requested-routing case study  
Status: complete

## Result

For this corpus, one broad review followed by two repair opportunities and one
cold closure review was the most efficient policy. It matched full review after
every repair on every graded end-state quality value while using 12 fewer
review starts, 295,027 fewer tokens, 244.24 fewer summed worker seconds, and
583 fewer churn words across 12 matched subjects.

This is a repair-loop efficiency result, not a defect-detection result. Only
five known defects existed across the 12 source subjects, and final-review
recall was defined for only three matched subjects. Both closure and full
replay found none of those final known defects. The predeclared noninferiority
claim is therefore not made, even though its numerical bound clears the
margin.

The practical policy for similar high-quality document work is:

1. Run one broad review before repair.
2. Let the repair loop proceed without replaying a full review after each
   repair.
3. Use a fresh cold reviewer for one full closure review.

This policy should remain provisional for defect-rich or high-risk work. A
follow-up must seed repairable defects and show that closure preserves both
detection and repair benefit before the policy becomes a general default.

## What was tested

The study selected two responses from each of six tasks in the earlier cold,
controlled-evolving construction corpus. Each of the 12 source responses was
copied byte-for-byte into three review-and-repair trajectories:

| Policy | Sequence | Review starts | Repair starts |
| --- | --- | ---: | ---: |
| Full replay | broad review, repair, full review, repair, full review | 3 | 2 |
| Focused rereview | broad review, repair, changed-field review, repair, changed-field review | 3 | 2 |
| Closure review | broad review, repair, repair, cold full closure review | 2 | 2 |

The requested route was `gpt-5.6-luna` at `medium` reasoning effort for all
reviewers, repairers, and adjudicators. The runtime exposed no served-model
field, so the study supports requested-routing claims only.

Six calibration starts passed before the main block. The main block completed
96 review, 72 repair, and three adjudication starts. The task, not an
individual response or replication, is the unit of generalization.

## Primary comparison

Closure review minus full replay produced these matched results:

| Measure | Closure | Full replay | Difference | Six-task interval |
| --- | ---: | ---: | ---: | --- |
| Residual severe defects | 3 | 3 | 0 | 0 to 0 |
| Residual total defects | 5 | 5 | 0 | 0 to 0 |
| Review starts | 24 | 36 | -12 (-33.3%) | -1.00 to -1.00 per subject |
| Total tokens | 1,220,901 | 1,516,928 | -295,027 (-19.5%) | -25,074 to -24,171 per subject |
| Summed worker seconds | 1,260.89 | 1,505.13 | -244.24 (-16.2%) | -26.66 to -12.97 per subject |
| Raw review words | 1,597 | 2,363 | -766 (-32.4%) | -105.33 to -25.08 per subject |
| Churn words | 440 | 1,023 | -583 (-57.0%) | -66.17 to -35.50 per subject |

All six task clusters favored closure on review starts, tokens, worker time,
and churn. Five of six favored closure on raw review words. The intervals are
deterministic task-cluster bootstrap summaries of this six-task corpus, not
population confidence intervals.

## Focused rereview

Focused rereview also ended with three severe and five total defects. It used
36 review starts, the same as full replay, so it did not reduce orchestration
rounds. Its 403 churn words were 620 below full replay and 37 below closure.

That makes focused rereview useful when the only goal is to narrow reviewer
prose, but it is not the best overall loop policy here. Closure saved one review
start per subject and used 282,296 fewer tokens than focused rereview. The
closure-versus-focused churn difference was small and unstable across tasks.

## What the quality result does and does not mean

The exact quality tie is real under the frozen registry: all 12 closure and
full-replay subject pairs had identical residual severe and total defect
counts. It is also weak evidence for repair effectiveness.

No repair in any policy changed the graded defect set. Defects removed,
severity reduction, and repair-origin defects were all exactly zero. Of 72
repair responses, 53 declared no operation and 51 returned an unchanged
document. The remaining changed documents did not move a registered defect.

The hidden registry contained five known defects spread across three subjects
and two tasks. Seventy-two of 96 reviews therefore saw a document with no
known defect. Final recall was defined for three of 12 matched subject pairs
and was zero for both closure and full replay. The numerical lower bound of
zero cannot establish noninferiority from that sparse denominator.

Reviewers raised 103 findings: eight were sustained, 94 were mechanically
refuted, and one was marked as a duplicate. A mechanical refutation means that
the narrow frozen registry had no modeled defect at that invariant and
element. It does not prove that the reviewer's criticism was wrong. Registry
agreement must not be reported as general reviewer precision.

## Churn interpretation

Churn is a frozen prose rule, not a human judgment of whether text was useful.
It marks words attached to findings that repeat, reopen, exceed the review
aperture, dispute unchanged material, or critique outside the contract.

Full-document reviewers have more opportunity to trigger two of those rules
than changed-field reviewers. That exposure is part of the policy being tested,
so churn is reported beside raw word count rather than treated as an isolated
quality score. The large closure reduction is still useful: one fewer review
round removed both raw prose and rule-defined argument without worsening the
registered end state.

## Integrity and execution review

The fixed handoff files match their on-disk SHA-256 digests. Independent review
also matched the published digests for accounting, aliases, calibration gate,
copy-equality proofs, design freeze, eligible-subject ledger, hidden registry,
launch order, measures, selection rule, trajectory state, worker-visible
contract, and all six response schemas.

All 36 policy copies matched the canonical form of their source response, and
all 36 lineage paths reconciled. The main block had 171 reservations, 171 CLI
starts, 171 observed model starts, and 171 terminal records. There were no tool
events, schema failures, process failures, timeouts, quarantines, exclusions,
or repaired/retried responses after a model start.

One repair response echoed the source document's construction alias rather
than its assigned repairer alias. It remained terminal, was not repaired, and
did not affect the schema-valid repaired document or any outcome measure.

The controller opened three adjudication batches for nine findings rather than
opening all 12 available batches. This mechanically derived batching amendment
was recorded before the first adjudication launch and did not change a study
measure.

Workers requested read-only execution and produced zero observed tool events,
but this is not proof of filesystem or network confinement. No model-authored
code was executed, no credentials or protected configuration were inspected,
and no tracked repository file was changed by the experiment controller.

## Limits

- Six tasks are too few for a population or complexity interaction claim.
- The source corpus was already near the grader's quality ceiling.
- Known defects were sparse and concentrated in two tasks.
- Registry and lexical measures cannot judge unmodeled reasoning errors.
- Served model identity was unavailable.
- Summed worker time is not controller wall clock and does not measure parallel
  elapsed time.
- The study concerns document review and repair, not code implementation or
  build performance.

## Decision

Carry cold closure review forward as the leading low-churn policy for document
repair loops. Do not yet remove intermediate review gates from defect-rich,
security-sensitive, or irreversible work. The next capability-sensitive panel
must use seeded repairable defects, test the policy first on the requested Sol
route, and then check whether the result changes on Sonnet and Opus.


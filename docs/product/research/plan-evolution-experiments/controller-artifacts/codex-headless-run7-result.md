# Run 7: review-and-repair policy panel on bounded construction documents

Provider block `codex-headless-via-claude-run7-r1`. Status **complete**.
Integration status **not-integrated**. Generated 2026-09-29.

This report stands alone. It needs no specification and no implementation plan.

## The practical answer

**Do a broad review first, then one cold closure review at the end.** On 12
matched construction documents, dropping the review between the two repairs
cost nothing measurable in document quality and saved a third of the review
starts, a fifth of the tokens, and more than half the churn words.

Against full review after every repair, one cold closure review at the end:

| Measure | Full replay | Closure | Difference | Tasks favouring closure |
| --- | --- | --- | --- | --- |
| Residual severe defects (12 subjects) | 3 | 3 | **0** | 0 of 6, none against |
| Residual total defects | 5 | 5 | **0** | 0 of 6, none against |
| Review starts | 36 | 24 | **−12 (−33%)** | 6 of 6 |
| Tokens | 1,516,928 | 1,220,901 | **−295,027 (−19.5%)** | 6 of 6 |
| Summed worker time | 1,505.1s | 1,260.9s | **−244.2s (−16.2%)** | 6 of 6 |
| Raw review words | 2,363 | 1,597 | **−766 (−32%)** | 5 of 6 |
| Churn words | 1,023 | 440 | **−583 (−57%)** | 6 of 6 |

Focused rereview of the changed fields also holds quality and cuts churn
hardest, but it does not save a start:

| Measure | Full replay | Focused | Difference | Tasks favouring focused |
| --- | --- | --- | --- | --- |
| Residual severe defects | 3 | 3 | **0** | 0 of 6, none against |
| Review starts | 36 | 36 | **0** | tied |
| Tokens | 1,516,928 | 1,503,197 | **−13,731 (−0.9%)** | 5 of 6 |
| Summed worker time | 1,505.1s | 1,305.9s | **−199.3s (−13.2%)** | 6 of 6 |
| Raw review words | 2,363 | 1,908 | **−455 (−19%)** | 5 of 6 |
| Churn words | 1,023 | 403 | **−620 (−61%)** | 5 of 6 |

Closure against focused, as a secondary contrast: 12 fewer review starts,
295,027 fewer tokens (both 6 of 6 tasks), 311 fewer raw review words, and 37
more churn words — the churn difference between the two cheap policies is
inside its interval and is not a real separation.

**One warning before you act on any of this.** The recall half of the question
is unanswered, not answered favourably. See
[What this run cannot tell you](#what-this-run-cannot-tell-you).

## What was tested

Two questions, on documents only. No code was written or run.

1. Does a broad first review plus one cold final closure review preserve
   defect detection and repair quality with fewer review starts, tokens, and
   churn than full review after every repair?
2. Does focused rereview of changed fields plus affected invariants preserve
   defect detection and repair quality with less churn than full replay?

And one side measure: what does a fresh review find that the document's own
author or repairer did not already admit?

Three policies ran on byte-identical copies of the same 12 documents. Every
policy gave every document two repair opportunities. Reviewers could not edit.
Repairers saw only their policy's finding brief. Every review and every repair
was a new cold process; no session was resumed and no role was merged.

- **Full replay** — broad review, repair, full review of the whole repaired
  document, repair, full review of the whole final document. Three review
  starts, two repair starts.
- **Focused rereview** — broad review, repair, review of only the
  machine-generated changed-field packet plus the affected invariants, repair,
  another focused review of the second delta. Three review starts, two repair
  starts.
- **Closure review** — broad review, repair, repair, one cold full review of
  the whole final document. Two review starts, two repair starts. Nothing
  reviewed between the repairs.

## How the subjects were chosen

The 18 returned responses in the `baseline-cold-controlled-evolving-thin` arm
of the run-2-to-5 construction panel were the eligible pool. That arm holds
construction policy fixed and gives three replications for each of six tasks.

The selection rule was frozen before any main start and read only four things:
the response's own digest, its task, its replication, and a residual-severity
stratum computed from the pre-existing hidden defect registry. Within a task, a
response at or above the task's mean severity weight (3×severe + 2×moderate +
1×minor) is higher-defect; below it is lower-defect. One response was taken
from each stratum, lowest seeded hash first. Where a task had only one stratum,
the two lowest seeded hashes were taken and the limitation recorded. No review
outcome, policy label, route assignment, prose preference, or manual choice
entered the rule.

Two tasks (`atomic-write-symlink-hardening`, `catalogue-corporate-trust-store`)
had two strata and gave a severity-contrasted pair. Four tasks
(`decision-record-ordinal-uniqueness`, `non-json-sso-guard`, `pack-profiles`,
`agentbundle-engine-stragglers`) had all three replications at severity weight
zero, so their pairs are not severity-contrasted. That is recorded in the
selection rule and in the limitations.

Each of the 12 selected documents was copied byte-for-byte into three policy
trajectories. All 36 copies were proved identical to their subject: three
matching digests per subject, 12 of 12 subjects. **The 12 matched subjects, not
the 36 copies, are the paired units. The six tasks are the unit of
generalization** — three replications inside a task are not three independent
task samples, and the bootstrap resamples tasks.

## Prior evidence, bound and not pooled

Three completed headless-Codex receipts were bound as prior transport
evidence. Each one's observed digest was checked against the digest recorded in
its integrated durable record under
`docs/product/research/plan-evolution-experiments/`. All six checks (three JSON
receipts, three Markdown reports) verified. The verification is recorded in the
design freeze. None of this run's numbers are pooled with any of them, or with
any Claude-subagent or Codex-collaboration block.

## Calibration

Six disposable starts ran before selection and before any main launch: two
reviewer, two repairer, two blind-adjudicator packets. Every start requested
`gpt-5.6-luna` at `medium` reasoning effort, as every experimental role did.

All six passed every gate: exact payload equality, an observed model start,
strict schema parse, exact alias echo, no prose outside JSON, no tool event,
timestamps present, token telemetry present, route and effort in the launch
record, and exactly one terminal record. The repairer probes echoed the input
artifact digest character for character. The adjudicator probes reported
`treatment_labels_seen: none-present`, proving the batch carried no policy,
round, role, route, or order label.

48.9 seconds, 130,780 input and 628 output tokens, zero quarantines. Calibration
is a transport and contract gate, not a study measure, and is reconciled
separately from the main block.

## Review and repair lineage

Every trajectory carries one unbroken path, and all 36 reconcile:

```
source response digest
  -> byte-identical policy copy (v0)      -> static grade
  -> broad review findings                -> dispositions
  -> repair 1 input = v0 digest, echoed   -> repaired document (v1)
  -> static grade of v1 (before any later reviewer started)
  -> [full: full review of v1 | focused: delta packet v0->v1 | closure: nothing]
  -> repair 2 input = v1 digest, echoed   -> repaired document (v2)
  -> static grade of v2
  -> final review [full document | delta packet v1->v2 | cold full document]
```

Each repair's echoed input digest matched the previous version's digest on all
72 repairs. Each repair's output digest is exactly the next version's digest.
The closure policy's final reviewer saw the whole final document and the frozen
invariants, and no earlier finding, self-audit, policy label, or repair history.

The changed-field packet was generated mechanically from frozen JSON bytes, not
by a model. A focused reviewer received every changed field before and after,
the names of the withheld unchanged fields, and only those invariant fields the
frozen affected-invariant mapping requires to judge the delta. When a repair
changed nothing at all, the frozen fallback aperture supplied the four
contract-surface fields and five invariants, and the start still ran and was
still measured.

Before repair 2, the closure controller carried forward unresolved sustained
findings from the broad review, removed only findings whose matched registry
defects were absent from the post-repair-1 static grade, and added the first
repairer's self-audit claims as labelled untrusted context. It invented no
reviewer verdict. No policy ever saw another policy's findings or dispositions.

## What the reviews found

103 findings across 96 reviews. Dispositions:

| Disposition | Count | Route |
| --- | --- | --- |
| Mechanically refuted against the frozen registry | 94 | oracle |
| Sustained by blind adjudication | 8 | adjudicator |
| Duplicate of another item in the batch | 1 | adjudicator |
| Indeterminate | 0 | — |
| Out of scope | 0 | — |

Findings by policy: full replay 47, closure 30, focused 26. Sustained: focused
4, closure 3, full 1. Ten of the 36 broad reviews returned no finding at all.

Three blind adjudication batches were launched, deciding 9 items. Nine of the
12 available batches are **unused capacity**, reported here and never counted as
a measure. No adjudicator saw a policy, round, role, route, or order label; no
adjudicator authored a finding; none saw an aggregate outcome.

**Every sustained finding was novel** — none matched a known registry defect,
so net-new sustained findings equal sustained findings in all three policies.
Known-defect recall was 0.0 wherever it was defined.

### Fresh review versus self-audit

All 8 sustained findings named an element or field that the preceding
self-audit — the constructor's for a broad review, the last repairer's
afterwards — did not name. Fresh review therefore contributed 8 of 8 sustained
findings beyond what the document's own author or repairer admitted. With a
denominator of 8 this is a direction, not a rate.

## Repair quality and overwork

**No repair changed the graded defect set on any trajectory.** Defects removed,
severity reduction, and repair-origin defects are all exactly zero in all three
policies. Residual defects are identical across policies on every subject:
three subjects end with one severe defect each
(`atomic-write-symlink-hardening|r1`, `atomic-write-symlink-hardening|r3`,
`catalogue-corporate-trust-store|r1`), and every other subject ends clean.
Convergence after repair 1 equals convergence after repair 2 everywhere.

Repairs were mostly correct not to act. 64 of 72 repair starts received an
empty brief; 8 received one finding. Under the fixed allocation every
opportunity still ran:

| | Full replay | Focused | Closure |
| --- | --- | --- | --- |
| Repair starts | 24 | 24 | 24 |
| Empty-brief starts (possible overwork) | 24 | 20 | 20 |
| Declared a no-op | 20 | 16 | 17 |
| Document actually unchanged | 20 | 14 | 17 |

Two focused repairs declared a no-op and then changed the document anyway. No
repair changed the document without declaring it. 51 of 72 repairs changed no
field; the rest changed one to five fields without moving the graded defect set.

## Churn

Churn was defined before launch as the words attached to a finding that
repeats an unchanged fingerprint, repeats an invariant against a byte-identical
field, reopens a closed finding without new evidence, disputes unchanged prose
outside the contract surface, or critiques anything outside that surface.
A finding's word count is its failure mode plus evidence plus repair
requirement.

Churn conditions fired 84 times: critique-outside-contract 30,
dispute-unchanged-out-of-scope 28, repeat-unchanged-fingerprint 15,
repeat-unchanged-invariant 11. No finding was reopened without new evidence.

Raw review words are reported next to churn words throughout, because concise
prose is not quality without a defect outcome — and in this run no policy's
prose, long or short, changed a defect outcome at all.

Per-task churn-word differences against full replay (negative favours the
cheaper policy):

| Task | Closure − full | Focused − full |
| --- | --- | --- |
| agentbundle-engine-stragglers | −54.5 | −79.0 |
| atomic-write-symlink-hardening | −31.5 | −66.0 |
| catalogue-corporate-trust-store | −88.0 | −54.5 |
| decision-record-ordinal-uniqueness | −35.0 | **+13.0** |
| non-json-sso-guard | −50.5 | −42.5 |
| pack-profiles | −32.0 | −81.0 |

Closure beats full on churn in all six tasks. Focused beats it in five.

## Intervals

Deterministic task-cluster bootstrap, 10,000 draws, seed 70413, resampling the
six tasks. 95% intervals on the mean within-subject difference:

| Contrast and measure | Point | 95% interval |
| --- | --- | --- |
| Closure − full: review starts | −1.00 | [−1.00, −1.00] |
| Closure − full: tokens | −24,668.9 | [−25,074.4, −24,171.3] |
| Closure − full: churn words | −48.58 | [−66.17, −35.50] |
| Closure − full: raw review words | −63.83 | [−105.33, −25.08] |
| Closure − full: worker seconds | −20.35 | [−26.66, −12.97] |
| Closure − full: residual severe defects | 0.00 | [0.00, 0.00] |
| Focused − full: churn words | −51.67 | [−73.42, −23.17] |
| Focused − full: raw review words | −37.92 | [−69.92, −5.67] |
| Focused − full: tokens | −1,144.3 | [−1,845.4, −326.5] |
| Focused − full: worker seconds | −16.61 | [−23.59, −8.96] |
| Focused − full: residual severe defects | 0.00 | [0.00, 0.00] |

Every cost interval excludes zero. Every quality interval is exactly zero
because no policy differed from another on a single subject's graded outcome.

## Noninferiority: predeclared, and not claimed

The margin was fixed before launch at five percentage points of recall
retention, claimable only if the lower task-cluster bound clears it and
residual severe defects do not worsen.

Both conditions technically hold: the lower bound on recall difference is 0.00
and residual severe defects are identical. **The claim is still not made.**
Known-defect recall is defined for only 3 of 12 matched subject pairs, and on
those three it is 0.0 for both policies — a difference of zero between two
measurements of nothing found. A noninferiority claim from that would be
arithmetic dressed as evidence.

## What this run cannot tell you

The block supports requested-route and document-quality claims only. It makes
no claim about served model identity, implementation quality, or build
performance.

Two limits dominate everything above.

**The source documents were already clean.** The frozen source arm carries only
5 known registry defects across the 12 selected subjects, concentrated in 3
subjects and 2 tasks. 72 of the 96 reviews faced a document with no known
defect at all. This was established from the pre-existing hidden registry
*before* the first main reservation and recorded in the design freeze; the
design, launch order, and sample size were not changed in response to it, as
the protocol requires. The consequence is that the **cost** side of both
questions is answered with tight intervals, and the **detection** side is not
answered at all. A panel with a defect-seeded corpus would be needed for that.

**A mechanical refutation is not a verdict on the reviewer.** The frozen rule
refutes a finding on an oracle-decidable invariant when the registry carries no
modelled defect at that invariant and element for that document version. 94 of
103 findings were refuted this way. That means "no modelled registry defect
here", not "the reviewer was wrong". Precision against this registry measures
agreement with a narrow oracle. Only the two judgment surfaces (stable outcome
and self-audit) were routed to blind adjudication, so a reviewer's substantive
but unmodelled observation on acceptance mapping, scope, decisions, or identity
could not be sustained by design.

The remaining limits:

- Semantic coverage and marker classes are graded lexically against frozen
  keyword groups: auditable and repeatable, but detecting wording rather than
  correctness of reasoning. Path, mapping-completeness, decision-completeness,
  digest-echo, and identity-echo classes are hard structural checks.
- Repair benefit, severity reduction, and repair-origin defects are zero in
  every policy because no repair moved the graded defect set. Those three
  contrasts are uninformative about policy, not evidence of equality.
- Two of the five churn conditions fire on the aperture a reviewer was given,
  so a full-document reviewer is structurally more exposed to them than a
  changed-field reviewer. That is a property of the policies under test, and it
  is why raw review words are reported alongside churn words.
- Served model identity was never independently observed: the provider exposed
  no model field on any of the 171 main starts. Only the requested route and
  effort are claimed.
- Repository visibility was read-only by declaration and by the sandbox mode
  requested for every worker. That is a declared limitation, not a confinement
  proof.
- Enterprise-managed configuration forced the approval policy and the Windows
  sandbox value on every start; the overrides are recorded in each receipt. The
  requested read-only sandbox and the no-tool contract held.
- Adjudication used 3 of 12 batches. The 9 unused batches are reported as
  spare capacity, never as a measure.

## Amendments

One amendment, mechanically derived, affecting no study measure:

**Adjudication batching arithmetic.** Within a review wave the controller opens
the minimum number of batches the frozen caps allow — `ceil(items / 28)`, at
most 4 — instead of always opening the 4-batch ceiling. The frozen reservation
discipline requires reserving an adjudicator ordinal only immediately before its
batch launches and reporting unused capacity separately, so opening near-empty
batches would spend capacity for no decision. Applied from the first batch (W1).
No other rule changed.

## Incidents

- Zero-model-start infrastructure failures quarantined: **0**.
- Responses repaired, retried, or replaced after a model start: **0**.
- Tool events: **0** across all 177 starts. Schema parse failures: **0**.
  Extra prose outside JSON: **0**. Process failures: **0**. Timeouts: **0**.
- Session contamination: none observed. Every main start was a cold ephemeral
  process; no continuation was launched.
- Rows excluded from measures: **0**.
- One observed protocol deviation: repair ordinal 36 (focused rereview,
  `decision-record-ordinal-uniqueness|r2`) echoed the document's own
  construction alias in its envelope alias field instead of its assigned
  repairer alias. The response reached a model start, so it is terminal and was
  not repaired, retried, or replaced. Its repaired document is schema-valid and
  is counted normally. Self-reported protocol deviations across all workers: 0.

## Exact accounting

Calibration, reconciled separately: 6 expected reservations, 6 reservations, 6
terminals, 6 model starts, gate passed, 48.9s, 130,780 input / 628 output
tokens, 0 quarantines, 0 tool events.

Main block:

| Item | Expected | Observed |
| --- | --- | --- |
| Selected subjects | 12 | 12 |
| Byte-exact copies | 36 | 36 |
| Trajectories | 36 | 36 |
| Review reservations / terminals | 96 / 96 | 96 / 96 |
| — initial broad reviews | 36 | 36 |
| — middle reviews (full + focused only) | 24 | 24 |
| — final reviews (12 full, 12 focused, 12 closure) | 36 | 36 |
| Repair reservations / terminals | 72 / 72 | 72 / 72 |
| — first repairs | 36 | 36 |
| — second repairs | 36 | 36 |
| Adjudication batches launched | ≤ 12 | 3 |
| Adjudication capacity unused | — | 9 |
| CLI process starts | 171 | 171 |
| Controller-observed model starts | 171 | 171 |
| Continuations | 0 | 0 |

Tokens, all rows carrying telemetry (96 / 96 reviews, 72 / 72 repairs, 3 / 3
adjudications):

| Block | Input | Cached input | Output | Reasoning output |
| --- | --- | --- | --- | --- |
| Reviews | 2,301,987 | 1,765,120 | 85,470 | 63,703 |
| Repairs | 1,758,815 | 1,224,960 | 94,754 | 12,215 |
| Adjudication | 71,171 | 17,152 | 1,430 | 789 |
| **Main total** | **4,131,973** | **3,007,232** | **181,654** | **76,707** |

Summed worker wall clock, main block: 4,113.0 seconds. Concurrency never
exceeded four processes.

Unavailable fields: the served model field on all 171 main starts. Nothing was
recorded as zero in its place.

Every reconciliation passes: review and repair reservations equal terminals at
96 and 72, all adjudication reservations are terminal, copy equality holds,
allocation matches the freeze, no tool event occurred, no response was repaired
after a model start, and every source and repair version has exactly one
lineage path per policy.

## Artifacts

Working artifacts live under
`.context/experiments/codex-headless-via-claude-run7-r1/`:
`design/` (freeze, selection rule, eligible-subject ledger, copy-equality
proofs, hidden registry, worker-visible content, aliases, launch order,
schemas), `subjects/` (36 byte-exact copies), `calibration/`, `review/`,
`repair/`, `adjudication/` (payloads, reservations, raw stdout and stderr,
final messages, receipts), `state/trajectories.json`, `analysis/`
(measures, accounting), `checkpoints/`, `controller/`, `tools/`.

Six immutable checkpoints were written and reported to the human as
preliminary: after calibration, after the 36 initial reviews and their
adjudication, after the 36 first repairs, after the 24 middle reviews and their
adjudication, after the 36 second repairs, and after the 36 final reviews and
their adjudication. No preliminary number entered a later prompt or changed the
frozen design, grading, launch order, sample size, or stop rules.

The fixed receipt is `.context/codex-headless-run7-result.json`.
No tracked repository file was modified. No model-authored code or command was
executed. No credential or protected configuration was inspected.

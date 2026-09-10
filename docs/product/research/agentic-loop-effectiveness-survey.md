# Agentic delivery-loop effectiveness

> Discipline: standard evidence survey

Commissioned 2026-09-09 to pressure-test the approved
[focused re-review](../intents/work-loop-focused-re-review.md) and
[repair-correctness](../intents/work-loop-repair-correctness.md) intents, then
look for other ways this repository's agentic delivery loop could buy more
assurance per unit of elapsed time and model-token cost. The survey combines
primary research and first-party tool documentation with the repository's
retained six-case experiment. It does not treat a result from human code
review, code completion, general reasoning, or another repository as direct
proof about this loop.

Confidence tags state how far a finding transfers to the decision here:
`[high]` means multiple strong and directly applicable sources agree;
`[moderate]` means the evidence is credible but has a transfer or coverage
limit; `[low]` means it is useful only as a candidate direction; and
`[uncertain]` means the survey did not find enough evidence to decide.

## Bottom line

1. **Keep both approved validations, with tighter accounting.** Focused
   re-review has credible precedent as an inter-patch review practice, and
   explicit defect location plus remedy context improves repair in several
   settings. Neither literature body proves that this repository's proposed
   mechanism preserves material coverage or lowers total cost, so the existing
   paired tests remain necessary. `[moderate]`
2. **Change the experimental unit from one finding to one natural repair
   event.** All sustained findings answered by the same repair revision must
   stay together. Selecting or splitting findings after observing results would
   understate both repair scope and re-review risk. This follows from the local
   corpus structure rather than an external comparative study. `[moderate]`
3. **Count preparation, not just model calls.** Constructing a focused envelope
   or closure packet is part of the candidate's cost. Both validations should
   measure from context preparation through verdict, split preparation from
   execution, and report end-to-end elapsed time alongside the uncontaminated
   comparison clock. `[moderate]`
4. **Do not infer that review roles are duplicate.** The retained corpus shows
   stochastic and sometimes unique findings, while the external search found
   no strong study that estimates the marginal protected-defect yield of each
   generalist and specialist role in an agentic software loop. Measure that
   portfolio before removing a reviewer. `[uncertain]`
5. **The strongest wider candidates are selective context, revision-aware gate
   scheduling, and simpler orchestration.** Evidence supports testing each
   against an always-load, always-rerun, or always-coordinate baseline. It does
   not support weakening final assurance without local calibration. `[moderate]`
6. **Model routing is plausible but later.** Routing studies show large savings
   on general tasks, not on protected software-review decisions. It belongs
   behind the structural savings above and needs task-specific validation.
   `[low]`

## 1. Focused re-review is plausible, not yet proven safe

Focused review of what changed since an earlier patch is an established review
interaction. Gerrit lets returning reviewers compare an old patch set with the
current one, while first-time reviewers compare the change with its base
([Gerrit review UI](https://gerrit-review.googlesource.com/Documentation/user-review-ui.html),
first-party documentation). This supports the basic interaction proposed by
the focused intent: a repair delta is a legitimate review subject rather than
an invented shortcut. `[moderate]`

The evidence does not justify assuming that a smaller subject automatically
saves time or retains coverage. A controlled experiment with 28 developers
found that decomposed changes produced fewer false-positive reports and more
context-seeking, but did not significantly change review time or defects found
([di Biase et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC7924728/)). A
Microsoft study of 1.5 million review comments found that changes touching more
files had a lower proportion of comments useful to the author
([Bosu, Greiler, and Bird](https://www.microsoft.com/en-us/research/publication/characteristics-of-useful-code-reviews-an-empirical-study-at-microsoft/)).
Together these sources support an isolated comparison, not deployment before
the local safety and cost bars pass. `[moderate]`

### Base drift is a hard invalidation condition

An inter-patch diff can be empty while a changed parent implicitly contributes
new content. Gerrit's documentation calls this a hazardous rebase and inspects
parent diffs separately to expose rebase edits
([Gerrit review UI](https://gerrit-review.googlesource.com/Documentation/user-review-ui.html#hazardous-rebases)).
The focused arm therefore must freeze and verify both the repaired revision and
its base. A base change, merge, rebase, changed contract byte, or repair outside
the accepted finding set invalidates the focused envelope and returns that case
to broad review. `[moderate]`

### Focus should name a lens, not add a long checklist

In a 150-participant experiment, explicitly asking reviewers to focus on
security increased vulnerability-detection probability eightfold, while a
generic or change-tailored checklist added no significant improvement
([Braz et al.](https://arxiv.org/abs/2202.04586)). An empirical study of 20,995
OpenStack and Qt review comments also found that security defects were rarely
discussed and concluded that manual review and automated detection should be
combined
([Yu et al.](https://arxiv.org/abs/2307.02326)). A case-control study of
detected and escaped Chromium OS security reviews also found associations with
review conditions and reviewer workload
([di Biase et al.](https://arxiv.org/abs/2102.06909)). The transfer to LLM
reviewers is untested, but the direction is clear enough to retain triggered
specialist focus and keep the focused envelope compact. It argues against
replacing a specialist with a long generalist checklist. `[moderate]`

**Pressure-test finding:** the focused intent survives desk research. Its
validation must use a complete repair-event finding set, pin the base as well as
the repaired revision, invalidate focus on drift or out-of-envelope edits, and
include envelope-construction cost. Its current protected-class kill remains
appropriate. `[moderate]`

## 2. Repair packets have evidence, but verification remains independent

Review text contains actionable repair information. Review4Repair trained on
55,060 code reviews and reported gains of 20.33% in top-1 and 34.82% in top-10
repair accuracy when review comments accompanied code
([Huq et al.](https://arxiv.org/abs/2010.01544)). Across five reasoning tasks,
language models that struggled to locate mistakes corrected them more reliably
when given the ground-truth error location
([Tyen et al.](https://aclanthology.org/2024.findings-acl.826/)). Agentless, a
fixed localization-repair-validation pipeline, likewise found higher solve
rates when issue descriptions contained location clues and solution steps
([Xia et al.](https://arxiv.org/abs/2407.01489)). These are different tasks and
models, but they agree that known location and remedy evidence should be passed
to repair rather than rediscovered. `[moderate]`

The packet must remain additive evidence. Issue descriptions can be incomplete
or misleading, and a repairer constrained to accept the packet as exhaustive
could faithfully implement the wrong boundary. The repairer must be allowed to
inspect dependencies outside the packet and must stop on contradiction,
missing authority, or an owner-only decision. `[moderate]`

### A targeted verifier is necessary but cannot certify the patch alone

Passing the tests that guided a repair does not prove general correctness.
Automated patch-assessment research found that additional generated tests could
discard 72% of known overfitting patches, while still producing false positives
and substantial test-generation cost
([Ye et al.](https://link.springer.com/article/10.1007/s10664-020-09920-w)).
The proposed targeted verifier should therefore demonstrate the named defect:
red on the pre-repair revision and green on the repaired revision where an
executable oracle exists, or an equally deterministic before/after predicate
for document and contract repairs. Broad review and applicable gates remain
independent guardrails. `[moderate]`

The local spike points in the same direction: focused re-review caught
repair-induced defects in three cases, and independent review exposed defects
created by attempted repairs
([local spike](work-loop-review-economics-spike.md#what-happened-to-the-findings)).

**Pressure-test finding:** the repair-correctness intent also survives. It
should compare complete repair events, treat packet construction as candidate
cost, allow investigation outside the packet, and demand before/after evidence
for the closure predicate. The packet is an input-quality intervention, not a
replacement for review. `[moderate]`

## 3. Other loop-effectiveness angles

### Select context by demonstrated relevance

More context is not monotonically better. Long-context models can perform worse
when relevant evidence sits in the middle of a large input
([Liu et al.](https://arxiv.org/abs/2307.03172)). Repository-level completion
improves when relevant cross-file context is retrieved iteratively
([RepoCoder](https://arxiv.org/abs/2303.12570)), while Repoformer's selective
retrieval reached up to 70% inference speedup without reducing its completion
benchmark performance compared with always retrieving
([Wu et al.](https://www.amazon.science/publications/repoformer-selective-retrieval-for-repository-level-code-completion)).
These are completion and retrieval tasks, not end-to-end implementation, so the
transfer is directional. `[moderate]`

For this repository, the testable candidate is selective exact evidence:
touched-path rules, governing contract bytes, affected dependencies, and
revision-bound digests. Exact sources remain available on demand; summaries and
digests orient or invalidate but do not become edit authority. This strengthens
focused review, repair correctness, progressive authoring, and duplicate
contract-review reduction without creating a new knowledge platform.
`[moderate]`

### Schedule gates by revision and risk, then converge on the full floor

Production evidence shows that gate selection can save material cost when it is
calibrated and backed by later assurance. Facebook's predictive test selection
halved test infrastructure cost while selecting fewer than one third of
dependency-selected tests and still reporting more than 99.9% of faulty
changes in its environment
([Machalica et al.](https://arxiv.org/abs/1810.05286)). That is a learned system
with a large history, not a result this repository can assume. `[moderate]`

Unchanged retries are a separate waste class. In 66,932 OpenStack reviews, 55%
of failed builds were rechecked; only 42% changed outcome, while average review
wait increased by 2,200%
([Maipradit et al.](https://arxiv.org/abs/2308.10078)). The near-term local test
should be simpler than predictive selection: cache deterministic results by
revision, run failure-directed and touched suites during repair, invalidate on
relevant changes, then run the full required floor once at convergence.
The local 2026-09-09 baseline also found a 21m22s work-loop test run with 917
passes, 5 skips, and 47 environment or policy cleanup failures, confirming that
gate duration and non-product failure work are material here
([parent intent](../intents/work-loop-delivery-efficiency.md#opportunity)).
`[moderate]`

### Measure orchestration as a treatment, not as assurance

Agentless used a fixed localization-repair-validation sequence and was
competitive with more complex software agents on the historical SWE-bench Lite
evaluation while reporting much lower per-case cost
([Xia et al.](https://arxiv.org/abs/2407.01489)). In a separate ICML comparison,
multi-agent debate did not reliably outperform self-consistency or multiple
reasoning paths without hyperparameter tuning
([Smit et al.](https://proceedings.mlr.press/v235/smit24a.html)). Neither result
settles multi-worker software delivery, but both reject the presumption that
more agent coordination is inherently better. The local mechanism is also
large enough to merit an ablation: the work-loop skill has 821 lines and 13
supporting scripts totaling 11,052 lines
([parent intent](../intents/work-loop-delivery-efficiency.md#opportunity)).
`[moderate]`

The parent intent's split is therefore sound: keep assurance obligations fixed,
then compare direct single-owner execution with cohort/state machinery only on
cases where coordination is optional. Multi-session recovery, dependent waves,
irreversible work, and migration remain separate triggers. `[moderate]`

### Measure the reviewer portfolio before pruning it

The local six-case spike found 53 independently sustained defect clusters: 31
were common to both policies, 16 baseline-only, and 6 candidate-only. Three
baseline-only clusters were protected. This proves neither that every reviewer
role is necessary nor that overlap is waste, because the experiment changed a
bundle of policies and did not attribute marginal yield by reviewer role
([local spike](work-loop-review-economics-spike.md#economic-findings-and-routing)).
`[high]` for the local count; `[uncertain]` for reviewer duplication.

The next evidence should be a role-level portfolio table over retained review
outputs: sustained clusters uniquely found, protected-class unique yield, raw
findings refuted, adjudication tokens, repair tokens, and elapsed critical-path
cost. An ablation can then test a genuinely low-yield role while holding model,
prompt, revision, and other roles fixed. Until then, review overlap is
insurance with an unknown price, not proven duplication. `[moderate]`

### Route models only after cheaper structural savings

RouteLLM reported more than twofold cost reduction without benchmark-quality
loss by choosing between stronger and weaker models
([Ong et al.](https://arxiv.org/abs/2406.18665)); FrugalGPT reported still
larger savings on selected classification, comprehension, and science-QA tasks
([Chen, Zaharia, and Zou](https://lingjiaochen.com/papers/2024_FrugalGPT_TMLR.pdf)).
Neither evaluates protected code-review findings, repair-induced defects, or
repository-agent tool use. Model routing is therefore a valid later experiment
for low-risk extraction, mechanical transformation, or clearly verifiable
tasks, while high-stakes judgment remains on the stronger pinned model until a
local ablation clears the same safety bars. `[low]`

## 4. Economic measurement must expose both controlled and lived cost

The local spike used 247.6 million provider-reported tokens over 59 measured
calls and 12.3 hours. Of elapsed time, 2.5 hours was load stall and 2.8 hours was
permission wait; active time was 6.6 hours
([local spike](work-loop-review-economics-spike.md#economic-findings-and-routing)).
Removing waits from the causal comparison was reasonable, but removing them
from the economic outcome would hide 43% of the observed elapsed time.
`[high]`

That split is not peculiar to this run. OpenStack's repeated-build study makes
review wait an explicit outcome, and a recent agentic software-cost model names
model tokens, human oversight, and orchestration infrastructure as separate
cost dimensions
([Maipradit et al.](https://arxiv.org/abs/2308.10078);
[ACEM](https://arxiv.org/abs/2608.02582)). These sources do not supply this
repository's weights, but they support keeping the dimensions visible.
`[moderate]`

Every follow-on should report two clocks:

- **controlled comparison:** active and admissible elapsed time for deciding
  whether the candidate itself is faster;
- **lived critical path:** total elapsed time, with permission, queue/model
  stall, human wait, and preparation split out, for deciding whether the system
  actually became faster.

Token accounting should likewise include context selection, packet or envelope
construction, reviewer and adjudicator calls, repairs, and any rerun triggered
by the intervention. A candidate that moves cost into preparation has not saved
it. `[high]`

## 5. Implications for the backlog

| Priority | Candidate | Evidence posture | Next proof |
| ---: | --- | --- | --- |
| 1 | Focused re-review | Supported enough to test; safety unproven | Run the approved four-event paired validation with base-drift invalidation and full preparation cost |
| 2 | Repair correctness | Supported enough to test; marginal value unproven | Run the approved four-event paired validation with complete finding sets and before/after closure evidence |
| 3 | Reviewer-portfolio economics | Duplication is unknown | Compute marginal sustained and protected yield plus closure cost per role before any ablation |
| 4 | Selective exact context and revision reuse | Directionally supported | Compare always-load with touched-path/contract/dependency context and invalidate on drift |
| 5 | Gate scheduling and revision cache | Supported in other CI systems | Measure touched/failure-directed repair gates plus one converged full gate against current reruns |
| 6 | Progressive authoring | Supported indirectly by context evidence | Attribute authoring sections and criteria to risk triggers, then remove only zero-yield defaults |
| 7 | Assurance without orchestration | Simpler baselines are credible | Compare direct execution with cohort machinery on bounded one-owner changes |
| 8 | Model routing | Economically promising, weak transfer | Start only with low-risk tasks that have deterministic external verification |
| 9 | Learning and bookkeeping off the critical path | Local hypothesis only | Measure blocking duration and downstream miss cost before rescheduling |

This order is economic, not a dependency graph. It keeps the two accepted
tests first, adds one measurement task before any reviewer removal, and leaves
the least direct evidence until later. `[moderate]`

## Known unknowns

- No located study measures marginal defect yield and closure cost for a
  portfolio of LLM generalist, security, quality, and adjudication roles on the
  same software revision. Reviewer duplication remains unproven.
- No located study tests focused LLM re-review of a repair diff against broad
  LLM re-review with independently adjudicated protected-class outcomes.
- No located study prices the authoring of a repair packet or focused envelope;
  local measurement must establish whether preparation erases call savings.
- The literature does not establish a safe universal test-selection rule for
  this repository. Facebook's learned result requires local calibration, and
  this repo's smaller corpus may not support a predictive model.
- The correct economic weight for an escaped protected defect relative to
  tokens and elapsed time remains an owner policy decision, not an empirical
  constant.

## Method and moderator pass

The survey used web search and direct page retrieval. Sources were limited to
primary papers, peer-reviewed publication pages, first-party research pages,
and first-party tool documentation; the retained local corpus supplied the
repository-specific evidence. No browser-only runtime or enterprise source was
available or needed. Queries covered focused and patch-set review, change
decomposition, reviewer usefulness, security focus and checklists, review-aided
repair, error localization, patch correctness, repository context retrieval,
test selection and retry, multi-agent coordination, and model routing.

The moderator pass checked four rival explanations:

- Smaller review subjects may merely move context reconstruction into hidden
  preparation. The protocol now counts it.
- Better candidate repairs in the prior spike may reflect the combined policy,
  not closure packets. The repair intent therefore compares the packet against
  the real current path under identical broad review.
- Reviewer overlap may be redundancy or necessary stochastic insurance. The
  evidence cannot decide; role-level marginal yield is required.
- Simpler agents and cheaper models may win only on easier benchmarks. Those
  findings are kept at moderate or low confidence and authorize ablations, not
  policy changes.

No material counterevidence was suppressed: change decomposition did not reduce
review time or increase detected defects; checklists did not add benefit to an
explicit security focus; tests can accept incorrect repairs; and multi-agent
benefits were sensitive to protocol tuning. These limits are why every proposed
change remains validation-first.

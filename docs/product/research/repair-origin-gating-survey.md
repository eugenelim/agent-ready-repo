# Can the repair-origin rate gate a review loop?

> Discipline: applied (practitioner-pattern survey)

- **Commissioned:** 2026-09-14
- **Question:** the repair-origin rate is recorded as an advisory health metric.
  Can it gate — stop a review loop automatically — rather than only inform?
- **Occasion:** a proposal to amend ADR-0104 with a rule of "repair-origin above
  half, two consecutive rounds, stop."
- **Follows:**
  [`review-loop-nonconvergence-survey.md`](review-loop-nonconvergence-survey.md),
  whose option 4 proposed tracking this rate. This survey answers the next
  question that option raised and does not repeat its findings on spec-driven
  frameworks, harness caps, mature review practice, or the self-correction
  stability criterion.

## Bottom line

**The rate should not gate a stop, and the reason is not statistical fragility —
it is that the signal does not predict the outcome it would gate on.** Across
four measured loops the proposed rule fires twice: once on a loop that diverged
and once on a loop that converged. `[high]`

The same four loops show what the signal does predict. In both converging loops
the rate went high, scope was **cut**, and convergence followed. The signal's
verb is *cut*, not *stop* — which is what this repository already recorded in
the knowledge topic *"a review round whose findings are mostly prior-round
repairs is the signal to cut the plan, not extend it"* and what `light-mode.md`
already prescribes as the preferred response. `[high]`

What is missing is not a threshold. It is a recorded baseline: no in-control
repair-origin rate has ever been measured for this loop, and every instrument
that could set a defensible limit requires one. `[high]`

**The rate as currently defined is also confounded.** Measured by citation
overlap, it rises with the size of the previous round's amendment regardless of
whether that amendment injected anything. A fraction recorded without the
amendment's footprint alongside it cannot be interpreted, so the baseline above
has to record both numbers or it measures the wrong thing. See § 2. `[high]`

## 1. Four measured loops, and the rule is a coin flip

| Loop | Repair-origin by round | Outcome | Rule fires? |
| --- | --- | --- | --- |
| PR #1231 (ADR-0104's own review) | 46%, 25%, **80%**, 33% | converged, shipped | no |
| Four-round spec amendment | 0%, ~60%, ~54%, ~56% | diverged | **yes** |
| `install-to-ship-walkthrough` | **60%**, **75%** | converged (26→10→8→4→1) | **yes** |
| 15-round shaping review | 30% overall (9 of 30) | ran 15 rounds | not measured per round |

Two observations kill the threshold argument.

**The converging loops reached higher rates than the diverging one.** PR #1231
peaked at 80%; `install-to-ship-walkthrough` hit 75%. The diverging loop never
passed 60%. Level does not separate these cases in the direction anyone expected.

**Persistence separates them no better.** Two consecutive rounds above half
occurred in the diverging loop *and* in `install-to-ship-walkthrough`, which
converged to a single finding two rounds later.

Sources: [PR #1231](https://github.com/eugenelim/agent-ready-repo/pull/1231),
read directly · `docs/knowledge/topics/a-review-round-whose-findings-are-mostly-prior-round-repairs-is-a-signal-to-cut.json`
· [`review-loop-nonconvergence-survey.md`](review-loop-nonconvergence-survey.md) § 6.

Downgrade: two of the diverging loop's four counts are approximate, and that
loop is a one-off that will not be re-measured. The comparison between loops
also carries the confound in § 2, which no recorded figure currently controls
for.

## 2. The rate measures amendment size as well as injection

Citation overlap asks whether a finding cites text the previous round's
amendment introduced. That question has a second determinant nobody has been
recording: **how much of the artifact the amendment touched.**

If the previous amendment rewrote fraction `a` of the contract, then under a
null of findings landing wherever a reader is looking, the expected repair-origin
fraction is approximately `a` — with no defect injection at all. An amendment
touching most of the contract yields a near-100% fraction as an arithmetic
consequence of its size. `[inference]`

The signal is therefore not `R / S`. It is `R / S` **relative to** `a`. Sixty
percent following an amendment that touched 55% of the contract is
indistinguishable from baseline; 60% following an amendment that touched 5% is
large. Two loops cannot be compared on the raw fraction unless their amendment
footprints are comparable, and nothing in the recorded data establishes that.

Two consequences:

- **Any recorded baseline must carry the footprint alongside the counts.** A
  stored fraction without it is uninterpretable later, and a `p₀` derived from
  such a series would be a `p₀` of a confounded quantity.
- **If the footprint turns out to be routinely high, citation overlap is the
  wrong criterion for "repair-induced" and needs to be tighter** — for instance
  requiring that the finding contradict the amendment rather than merely cite
  it.

Report the footprint before anyone states a threshold. A high number does not
refine the threshold; it invalidates the metric the threshold would sit on.

This point arrived from a separate review session on 2026-09-14 and is recorded
here unmeasured: the footprint figure for the occasioning round has not been
computed. See Known unknowns.

## 3. What the signal actually predicts: over-specification

Both converging loops converged for the same recorded reason, and it was not
patience.

`install-to-ship-walkthrough` converged only as repairs **removed** claims — a
two-altitude source-plus-rendered check collapsed to rendered-only, a browser-gate
visibility claim was withdrawn to a stated accepted gap, a scalar route count
became a committed route set. PR #1231's round 4 reported non-convergence at 80%,
scope was cut (four prose-property tests deleted), and round 5 converged.

In both cases the high rate was a true signal and the correct response was to
reduce the construct. A stop rule would have ended both loops one round before
they succeeded. `[synthesis]`

This is the same conclusion the prior survey reached from the stability
criterion: past the threshold another round subtracts, so the move is to change
what is being reviewed, not to keep reviewing it.

## 4. A fixed threshold is a specification limit on a control chart

Statistical process control separates two things this proposal merges. Control
limits derive from a process's own variation; specification limits are external
assertions. Shewhart, Deming and Wheeler are unanimous that acting on the latter
as if it were the former causes tampering — adjusting a stable process and
injecting the variation you meant to detect. A fixed 50% line on a proportion is
a specification limit. `[high]`

The chart's own preconditions also fail:

| Criterion | Requirement | Our data |
| --- | --- | --- |
| p-chart validity | `n · p̄ ≥ 5`, so `n ≥ 20` at `p̄ = 0.5` | rounds of 9, 10, 13 — `n = 9` gives 4.5 |
| Subgroups before limits are stable | 25 | 11 round-observations across four loops |
| Accepted run rule nearest the proposal | 8 consecutive on one side of the **estimated mean** | 2 consecutive above a **fixed** line |

No accepted run-rule catalogue — Western Electric or Nelson — contains "two
consecutive above a fixed line."

Sources: [Minitab NP chart data considerations](https://support.minitab.com/en-us/minitab/help-and-how-to/quality-and-process-improvement/control-charts/how-to/attributes-charts/np-chart/before-you-start/data-considerations/) ·
[Western Electric rules](https://en.wikipedia.org/wiki/Western_Electric_rules) ·
[SPC for Excel — control vs specification limits](https://www.spcforexcel.com/knowledge/control-chart-basics/how-control-charts-work-control-limits-and-specifications/)

## 5. The effective threshold is set by round size, not by the line

"Above half" is coarse at small counts, so the rule silently strictens and
loosens with the number of findings in a round:

| Findings in round | What "above half" requires | False-stop rate at a 30% true rate |
| ---: | --- | ---: |
| 3 | ≥ 67% (2 of 3) | 4.7% |
| 4 | ≥ 75% (3 of 4) | 0.7% |
| 9 | ≥ 56% (5 of 9) | 0.3% |
| 13 | ≥ 54% (7 of 13) | 0.4% |
| 20 | ≥ 55% (11 of 20) | 0.0% |

Exact binomial, two consecutive rounds. The rate sawtooths, and the worst case
is the smallest rounds — which are the late rounds of a loop that is nearly
done. The rule is most likely to misfire on success. `[synthesis]`

For completeness, the operating characteristic at ten findings per round is
better than it looks from a single observation: a loop with a true rate of 30%
trips the two-consecutive rule 0.2% of the time, and at 40% it is 2.8%. But
rounds are not independent draws — same agent, same construct, correlated repair
style — and positive correlation inflates those numbers by an unquantified
amount. They are floors, not estimates. `[inference]`

## 6. Published bad-fix rates cannot calibrate this metric

| Measure | Rate | Source |
| --- | ---: | --- |
| Bad-fix injection, US average | ~7% | Capers Jones |
| — best engineers, low complexity | <1% | Jones |
| — novice, high-complexity code | 25% | Jones |
| — error-prone modules | up to 75% | Jones |
| Bug-inducing commits, Apache (10 projects) | 14–38% | ApacheJIT |
| Pull requests introducing bugs, Firefox (97,347) | 12.2% | RippleGUItester |
| Fixes that are incorrect | 14.8–24.4% | Microsoft-related study |
| DORA change failure rate, elite → low | 5% → 40–64% | DORA 2024 |

Every one of these counts defects per fix or per commit. Ours counts the share
of one review round's findings attributable to the previous repair. A round with
six findings traced to a single sloppy repair reads 60% while injecting one
defect. The denominators are not interchangeable, so none of these numbers can
license a threshold on ours. `[high]`

Jones's figure additionally traces to one proprietary database with no
independent replication, and its own range spans the proposed threshold four
times over depending on complexity and who is working.

No published study measures review-round repair attribution at all.

Sources: [Jones via CERM](https://insights.cermacademy.com/6-software-defect-origins-and-removal-methods-c-capers-jones-technologyrisk/) ·
[ApacheJIT arXiv:2203.00101](https://arxiv.org/pdf/2203.00101) ·
[DORA 2024](https://dora.dev/research/2024/dora-report/)

## 7. Who counts, and how the diff is framed, decides reliability

An earlier draft of this survey held that an agent cannot reliably score whether
its own repair caused a finding. Adversarial review found that too strong, and
the correction matters because it is architectural and actionable.

The self-correction literature indicts **ungrounded, in-session critique**.
Attribution against a supplied diff is a different task: grounded entailment over
two external artifacts.

- *The Self-Correction Illusion* relabels an identical claim from the model's own
  thought-block to an external artifact and measures correction rates rising by
  **23 to 93 percentage points** — on Llama-3.3-70B, from 0% to 87%. The
  mechanism it names is addressability: content framed as an external artifact
  with a discrete handle can be operated on reliably. `[moderate]`
- The generator-verifier gap points the same way: verification accuracy exceeds
  single-generation accuracy on verifiable tasks, with weak-verifier ensembles
  closing 14–18 points of it. `[moderate]`
- Against that: when the claim stays in the model's own context unrelabelled —
  which is exactly an agent reviewing its own edits in-session — correction rates
  are **0–23%**. `[moderate]`
- And grounded citation accuracy degrades badly under load, one study measuring a
  fall from 79% to 17% as supplied sources scaled from 2 to 150. A loop with many
  accumulated rounds of diffs approaches that condition. `[moderate]`

The operative distinction is therefore not *can a model do this* but *who is
asked and how the material is framed*:

| Configuration | Expected reliability |
| --- | --- |
| Repairing agent, in-session, own edits unrelabelled | poor — the indicted condition |
| Fresh instance, diff and finding supplied as documents | substantially better |
| Line ranges intersected mechanically, model supplies neither | arithmetic |

The prior survey noted that this repository's reviewer is already a fresh session
on a different model family with no authoring context, and called that "a
mitigation we already have by accident… worth making deliberate rather than
incidental." The relabelling result gives that observation a measured magnitude
and turns it into a property worth protecting against a future refactor.

Sources: [The Self-Correction Illusion](https://arxiv.org/html/2606.05976v1) ·
[Shrinking the Generation-Verification Gap with Weak Verifiers](https://arxiv.org/html/2506.18203v1) ·
[Self-Correction Bench](https://arxiv.org/pdf/2507.02778) ·
[Cited but Not Verified](https://arxiv.org/html/2605.06635v1) ·
[Quantifying Self-Preference Bias of LLM Judges](https://arxiv.org/pdf/2604.22891) ·
[Panickssery et al., NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/file/7f1f0218e45f5414c79c0679633e47bc-Paper-Conference.pdf)

**One local corroboration.** On a single round, a mechanical citation-overlap
fraction and an independent read by inspection agreed. That is evidence the two
methods measure the same quantity reproducibly. It is not evidence the quantity
means divergence: if the § 2 footprint is high, both methods agree on a number
that is mostly amendment size. Reproducibility and validity are separate
properties and only the first is established. `[low]` — one round, this
repository.

Note the limit of this section: attribution reliability changes how trustworthy
the number is. It does not change § 1, where a correctly measured number still
fired on a converging loop, nor § 2, where a perfectly measured number is
confounded.

## 8. Two things the signal counts but cannot distinguish

A finding is recorded as repair-induced whatever caused the repair to be wrong.
Two distinct causes collapse into the same count.

**A careless repair.** The intended case.

**A repair distorted by another gate.** In one observed round a defect entered
because a mechanical checker demanded the content, and the author supplied what
the checker asked for rather than what the requirement needed. The signal
counted it as repair-induced, correctly by its own definition and unhelpfully in
substance: the repair was not careless, it was bent.

This is a known limit of the signal, **not something the signal detects.** It
matters most if the signal ever gates, because a gate that fires on
gate-induced defects closes a loop on itself: pressure from one checker
manufactures findings that trip another. It also implies a third response
alongside *cut* and *stop* — relax or repair the checker — that nothing in the
loop currently names. `[moderate]` — one observed instance; the mechanism is
Goodhart's law and is not in dispute, the frequency is unmeasured.

## 9. Gating a noisy signal reproduces the failure ADR-0104 exists to fix

ADR-0104's second decision driver is that an exit must cost less than evading it;
ADR-0014's rule was rationalised around precisely because it was not. A stop that
fires on a converging loop is expensive — it forces a requester conversation, a
scope cut, or a full-mode move on work that was about to finish. An expensive
rule that is wrong half the time gets argued around. `[inference]`

Adjacent evidence agrees. Alert-fatigue practice keeps human escalations to
10–20% of detections and suppresses low-confidence signals rather than firing
them. Review decision-fatigue work observes that when reviewers face too many
decisions, the easiest one is to opt out. Rust's core team documents strong
resistance to the hard disposition (closing an RFC) and better results from the
scheduled advisory moment. `[moderate]`

Sources: [incident.io on alert fatigue](https://incident.io/blog/alert-fatigue-solutions-for-dev-ops-teams-in-2025-what-works) ·
[Cipriani, code review decision fatigue](https://tylercipriani.com/blog/2022/03/12/code-review-procrastination-and-clarity/) ·
[Cameron, The problem with RFCs](https://www.ncameron.org/blog/the-problem-with-rfcs/)

## 10. What would make a gate defensible later

Every instrument suited to this shape of data — a binary rate, small varying
subgroups, fast detection of a sustained shift — needs an in-control rate `p₀`,
and CUSUM and SPRT also need the alternative rate `p₁`. Bernoulli CUSUM and EWMA
substantially outperform a p-chart on exactly this problem; one prospective
comparison measured EWMA detecting a shift in 5.5 periods against a p-chart's
23.0.

None of them can be built today, because `p₀` has never been measured.

Recording the per-round fraction is the step that unblocks everything else, and
it commits to no behaviour. Full mode already persists per-round state, and the
attribution is mechanizable there: intersect a finding's cited line ranges with
the previous round's diff hunks. `[synthesis]`

**Record four numbers per round, not one fraction.** Per § 2 a fraction alone
cannot be interpreted after the fact:

| Quantity | Why it is needed |
| --- | --- |
| Sustained findings in the round | the denominator |
| Of those, repair-origin | the numerator |
| Lines the previous round's amendment touched | the exposure term `a` |
| Lines in the artifact under review | what `a` is a fraction of |

The first two are the metric as proposed. The second two are what make a later
`p₀` mean anything, and they are cheaper to capture than the first two because
they come from the diff rather than from the findings.

**`state.json` cannot hold this series.** Live cohort state is written to
`spec_dir / "state.json"` and that path is gitignored, so it is per-run scratch
that does not survive the loop. A baseline needs a committed sink — telemetry or
a research ledger — and choosing one is part of the cost of this path, not a
detail of it.

**Read this section as conditional.** It describes what a defensible gate would
require, not work worth starting. Given § 2 and § 8 the series would pool a
confounded quantity that merges careless repairs with gate-distorted ones, over
months, to calibrate a threshold whose verb § 3 says is wrong. The
decision-useful findings of this survey are qualitative and need no baseline:
read the rate against exposure, treat a run rather than a spike as the signal,
and consider that the checker rather than the repair may be at fault.

Sources: [Duclos et al., PMC7218839](https://pmc.ncbi.nlm.nih.gov/articles/PMC7218839/) ·
[Springer — Monitoring a Proportion Using CUSUM and SPRT](https://link.springer.com/chapter/10.1007/978-3-642-57590-7_10)

## Known unknowns

- **Known-unknown:** the amendment footprint for the round that occasioned § 2 —
  what fraction of the contract's lines the round-5 amendment touched against the
  round-4 revision. Would be closed by diffing those two revisions. Until it is
  computed, no threshold should be stated, because a high value means the metric
  is measuring amendment size.
- **Known-unknown:** whether the footprint confound explains § 1's inversion —
  that is, whether the converging loops' 80% and 75% rounds simply followed
  larger amendments than the diverging loop's rounds did. Would be closed by
  computing the footprint for each round in the four-loop table, where the diffs
  survive.
- **Known-unknown:** the in-control repair-origin rate for this loop. Would be
  closed by recording the four quantities in § 10 per round over roughly 25
  rounds.
- **Known-unknown:** how strongly rounds correlate. Would be closed by the same
  recorded series, and it decides how far § 4's floors sit from the real
  false-stop rate.
- **Known-unknown:** the per-round rates for the 15-round shaping review, which
  has only an aggregate 30%. Would be closed by re-deriving them from that loop's
  round artifacts, if they are still intact.
- **Known-unknown:** the error rate of mechanically intersecting cited line
  ranges with diff hunks, including the unified-diff context-line trap. Would be
  closed by running the intersection over recorded rounds and hand-checking a
  sample.
- **Unknowable, as posed:** whether an agent's count of findings caused by its own
  repairs is accurate in this setting. No study measures this specific task; § 6
  is all extrapolation from adjacent conditions. Closing it requires an
  independent scorer, at which point the count is no longer self-attributed and
  the question dissolves.
- **Unknowable:** whether the two converging loops would have converged without
  the scope cuts. Each cut changed the artifact, so the counterfactual cannot be
  run.

## Provenance

Findings in §§ 4, 6, 7, 9 come from retrieval performed on 2026-09-14 and have
not been independently re-verified against the primary sources. The four-loop
data in § 1 was read directly from the cited PR, knowledge topic, and prior
survey. The arithmetic in §§ 1 and 5 was computed for this survey and is exact
binomial, not simulated.

Sections 2 and 8, and the corroboration note in § 7, came from a separate review
session on 2026-09-14 and are recorded as reported. Their occasioning
measurements — the amendment footprint, and the round in which a checker's
demand introduced the defect — were not re-derived here and carry no figure in
this survey.

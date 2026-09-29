# Efficient review loops: independent evidence report

Date: 2026-09-27

## Bottom line

Repeated whole-document spec and plan review is producing measurable churn in this repository. Across four independently normalized pre-execution histories, 75 findings were reported. The first rounds produced 37. Later rounds produced 38, but only 5 of those 38 were unrelated new defect families. Twelve were clear repeats of an earlier defect, 20 were a different defective surface under an already-contested invariant, and one had uncertain lineage. Thus **32 of 38 later findings (84.2%) returned to an existing defect or invariant family**.

The evidence supports this loop:

1. Keep a small accepted outcome contract stable.
2. Run one broad cold review and any risk-triggered specialist review before execution.
3. Adjudicate findings and close blocking consequences; record advisory residue instead of demanding zero findings.
4. Let the execution plan evolve under a small amendment record.
5. Re-review the accepted finding, its repair, changed contract bytes, and affected dependencies.
6. Re-open broad review only after material scope, trust-boundary, base, or contract change, or when the focused envelope cannot cover whole-change state.
7. Run a broad implementation review when the built system exists.

This is evidence against a hash-pinned detailed plan and against unbounded “review until Clean.” It is not evidence that review should be removed.

## Direct real-corpus result

Four histories met the frozen inclusion rule. Two Codex classifiers independently normalized the larger histories. A separate finding adjudicator resolved material disagreements. The current initiative was classified twice with identical results.

| Case | Finding rounds | Raw findings | Strict defects | Invariant families | Later findings | Exact repeats | Same-invariant distinct | Unrelated new | Proven repair-origin |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Current plan-evolution review | 4, then Clean | 10 | 9 | 6 | 5 | 1 | 3 | 0 | 3 |
| Credential broker contract | 4, then Clean | 41 | 31 | 22 | 21 | 10 | 9 | 2 | 0 proven; up to 11 unresolved |
| Portfolio first-run pilot | 4 | 19 | 18 | 12 | 10 | 1 | 6 | 3 | 2 |
| Work-loop fresh contract gate | 3 | 5 | 5 | 3 | 2 | 0 | 2 | 0 | 0 |
| **Total** |  | **75** | **63** | **43** | **38** | **12** | **20** | **5** | **5 proven** |

“Strict defects” and “invariant families” are summed within cases. They are not deduplicated across initiatives.

The current initiative is the clearest causal record. Its initial adversarial review produced five findings. The next three rounds produced five more: one repeated the same duplicated-authority defect, three were introduced by prior repairs, and one could not be assigned safely. The next round was Clean. A sixth adversarial round reviewed intervening security and source-refresh amendments, so it is not counted as a duplicate Clean over an identical subject. Parallel security review found four first-round defects and was Clean on its second pass.

The credential-broker case shows the other main churn shape. It produced 41 findings over a 20 → 14 → 6 → 1 → 0 trajectory. Independent classifiers initially disagreed on whether later cross-surface failures were repeats or distinct defects. Adjudication retained 10 clear repeat occurrences, 9 distinct defects under prior invariant families, 2 unrelated new later defects, and 31 strict defects in total. The missing intermediate diffs prevent any strong repair-causality claim.

The portfolio case produced 19 findings over four rounds. It had one strict repeat and six different defects under existing invariant families. Two round-four defects were explicitly caused by round-three repairs: a changelog range check with an impossible anchor, and a spec/plan evidence-location repair that made the two artifacts disagree.

The work-loop contract case is important because it retains dispositions. Four of five findings were sustained and resolved; one was refuted. The last two rounds found different control-flow paths violating the same “missing mandatory review must block readiness” invariant. They were not duplicate wording, but they were repeated rediscovery of incomplete invariant coverage.

## Review prose and round cost

Historical provider tokens and wall-clock time do not survive for these four cases. Report size is the available churn proxy; it is not converted into tokens.

The non-clean reports contain 2,673 whitespace-delimited words. Later-round reports contain 1,280 words for 38 findings. Because 32 of those findings returned to prior defect or invariant families, most later-round finding volume concerned already-contested ground. The retained Markdown does not support assigning an exact number of “wasted words” to individual findings.

| Case | Later-report words | Later findings | Findings returning to prior defect/family |
| --- | ---: | ---: | ---: |
| Current plan-evolution review | 390 | 5 | 4; one indeterminate |
| Credential broker contract | 496 | 21 | 19 |
| Portfolio first-run pilot | 326 | 10 | 7 |
| Work-loop fresh contract gate | 68 | 2 | 2 |

This is a better measure of reviewer churn than raw round count. A later finding can be valuable even when it belongs to an old family, but the pattern says the loop should repair the invariant across all owned surfaces or simplify the duplicated claims, not keep resampling the whole document.

## Corroborating repository evidence

Two retained aggregate cases point in the same direction but are not pooled with the independently re-scored corpus:

- One five-round plan review produced 26, 10, 8, 4, and 1 findings. Twelve of the 18 findings in rounds two and three were introduced by the prior repairs. Convergence came from removing claims: collapsing duplicate test altitudes, withdrawing an unsupported browser-gate claim, and replacing a scalar count with a committed set.
- The occasioning nonconvergence loop ran 15 rounds and sustained 30 findings. Eighteen findings fell into two families, nine were introduced by earlier repairs, and each of the last eight rounds returned exactly one finding.

Repository-wide measurement covered about 4,300 session transcripts, 1,273 merged pull requests, 431 spec/plan pairs, and 4,060 numbered criteria. Of 112 runs with review artifacts, 50 exceeded five review ordinals. This does not mean 50 single loops exceeded five rounds—the ordinal can span multiple loops—but it shows that repeated review is common enough to need explicit stopping and lineage rules.

## Do separate specs and plans help?

The evidence does **not** establish that two files are better than one.

After controlling for implementation size, goal-based delivery and full spec/plan delivery had no separable repair-rate advantage; the direction changed across size buckets. At the same time, full delivery produced a class that lighter delivery cannot: 567 findings that tied code to an acceptance criterion. That is real traceability value, but it comes from having an accepted outcome contract, not necessarily from maintaining a separate long narrative plan.

The cost of the current shape is large:

- 85.6% of nonblank `plan.md` lines are narrative that no gate, task router, or acceptance-criterion reference consumes.
- Full-mode review placed 51% of findings only on spec/plan text, versus 6% record-only findings in light mode.
- One measured run recorded 471 record-only findings against 13 findings elsewhere.

The supported conclusion is narrower:

- Keep a distinct, stable contract when acceptance traceability matters.
- Keep the plan separate only when it carries operational state—dependencies, ownership, sequencing, checks, and decisions that can still change.
- Do not duplicate the same invariant across spec prose, plan prose, tasks, test sketches, and accounting tables. The real corpus shows that reviewers then chase the same rule across surfaces.
- For small and medium work with little sequencing risk, a unified contract containing outcomes plus a short mutable execution section is plausible, but remains an untested treatment.

H13—separate spec and plan versus one unified contract—therefore remains inconclusive. The repository supports a stable-contract/thin-plan design, not a categorical two-file rule.

## Should the plan be locked?

A semantic lock is useful; a byte lock on the execution plan is not.

Across 210 plans, the template says the plan may change as the team learns, while the engine hash-pins it after approval. Two deep runs parked or wiped their engine state when build-time learning required a plan edit. The direct corpus also shows that repairs to detailed plan text create further contradictions.

Use two different controls:

- **Outcome lock:** accepted goals, boundaries, safety properties, and success conditions require explicit authority to change.
- **Plan amendment:** sequencing, task decomposition, evidence paths, and implementation choices may change when discovery proves the old route wrong. Record the reason, affected tasks and checks, and whether the outcome contract changed.

An amendment that changes only the plan should trigger focused review of the changed decision and its dependencies. A contract, protected-risk, or material scope change should trigger a fresh broad review.

## Pre-execution versus build-phase loops

Pre-execution review has value. The corpus found contradictions in ownership, reachability, security controls, dependency graphs, and executable checks before code existed. But repeated pre-execution review quickly shifted from discovering unrelated defects to chasing incomplete invariant propagation and repair effects.

Build-stage evidence supports keeping a later broad check:

- In a six-case paired implementation study, narrowing later review context reduced review-phase tokens by 35.8%, but the bundled candidate missed three independently adjudicated protected-class clusters.
- An isolated focused re-review used 81.0% fewer tokens in its first case, but missed three public-contract clusters outside the repair envelope and was stopped by its safety rule.
- Across the six-case study, 28 sustained findings were repair-induced: 24 in repeated broad-review arms and 4 in focused arms.

Focused re-review is therefore an efficient repair check, not a substitute for all broad review. The efficient sequence is one broad contract review before execution, focused checks as the plan evolves, and a broad implementation review over the built change. Risk-triggered specialist reviews remain independent gates.

## T13 synthetic extension boundary

The requested-Sol T13 block is closed as a methodological negative result, not
as evidence for natural work-loop effectiveness. It consumed 95 terminal starts
under a 96-start cap, leaving one unused adjudication start. No Sonnet, Opus,
eighth T13 review, or synthetic validation block is part of this report's
recommendations.

The T13 record remains inspectable: it keeps the standalone JSON and Markdown
handoffs, raw artifacts, digest manifest, retirement record, and seven review
rounds. Those rounds filed 190 findings: 4, 31, 41, 15, 41, 10, and 48 by
round. The final state records 88 sustained findings, 3 refuted findings, and
99 unadjudicated findings.

What T13 proved is about the experiment apparatus. The block reproduced the
same families it was built to detect: tautological checks, self-matching
taxonomy tests, shape checks presented as property checks, fail-open carry
behavior, stale byte bindings, and grader decisions on judgment surfaces. The
controller retired seven self-certifying modules and kept their history instead
of running another repair round.

That makes two T13 outputs descriptive only for this report. First, seeded
known-defect recall is excluded because the seeded defects were
controller-authored, structurally decidable, and exposed through schema enums.
Second, synthetic policy contrasts are excluded because the dominant findings
were experiment-construction and test-data effects rather than natural delivery
behavior. The natural-work recommendations above and below therefore rest on
the four normalized real histories, corroborating aggregate histories, and
repository-wide survey, not on T13 seeded recall or synthetic closure-vs-replay
contrasts.

## Hypothesis disposition

| ID | Result from available evidence |
| --- | --- |
| H1 — semantic lock versus pinned plan | Directionally supports semantic outcome lock plus mutable plan; no randomized build comparison. |
| H2 — immutable outcome block versus undifferentiated mutable document | Directionally supports separating stable outcomes from mutable execution details. Drift non-inferiority is untested. |
| H3 — continuous planning/build versus handoff | Unavailable. The calibrated Codex processes never reached inference. |
| H4 — stronger planner/builder allocation | Unavailable; exact model identity and comparable runs were not obtained. |
| H5 — standard builder with escalation versus all-frontier | Unavailable for the same reason. |
| H6 — three cold reviewers versus one | Inconclusive. Serial real reviews show diminishing unrelated yield, but do not randomize reviewer count. |
| H7 — fresh reviewer versus builder self-audit | Unavailable. Historical records do not retain comparable self-audits. |
| H8 — disposable planning probe versus reading only | Unavailable. |
| H9 — focused versus full re-review | Refuted as a complete replacement; supported as a repair check with explicit broad-review triggers. |
| H10 — compact decision/check plan versus narrative plan | Directionally supported by plan-surface and churn evidence; builder success was not randomized. |
| H11 — guided decision view versus full plan | Unavailable. |
| H12 — just-in-time rules versus static packet | Directionally supported by repeated late discovery of repository obligations, but not isolated here. |
| H13 — separate spec and plan versus unified contract | Inconclusive. Separate accepted outcomes aid traceability; a separate narrative plan has no measured repair-rate advantage. |

The model-allocation questions should not be moved to Claude merely to fill the table. They need exact model identity, comparable tasks, and trusted telemetry. The Claude run can be reduced to the isolated packaging and continuity questions if those controls are available.

## Recommended operating policy

For medium and complex work:

1. Accept a compact outcome contract.
2. Author a thin plan containing decisions, dependencies, task ownership, and executable checks.
3. Run one cold adversarial review plus triggered specialist review.
4. Adjudicate all blocking findings. Defer advisory residue explicitly.
5. Begin execution; amend the plan when evidence invalidates the route.
6. Track findings by semantic cluster, invariant family, and origin.
7. After repair, review the closure predicate, repair diff, changed contract bytes, and affected dependencies.
8. Stop and simplify when repair-origin findings dominate or the same invariant survives twice.
9. Run a broad implementation review at completion and whenever a broad-review trigger fires.

For small work, collapse the contract and plan into one short artifact unless sequencing, coordination, or protected risk makes a separate plan useful.

## Reproducibility and limits

The machine-readable results are in `review-churn-results.json`. `tools/plan_evolution_workbench/review_churn.py` validates arithmetic and SHA-256 digests for every durable source used here. The current case’s finding-level normalization, source digests, classifier agreement, and limitations are retained in `review-churn-current-case.json`, so no result depends on `.context` or the delivery records surviving. Tier B, repository-wide, and prior paired-study numbers are bound to frozen source digests but are not independently recomputed from their unavailable raw sessions.

The direct corpus is purposive, not statistically sampled. Intermediate reviewed revisions are missing for most historical cases. Reviewer briefs and model identities are not controlled. Finding volume depends on review aperture. The aggregate studies may overlap named cases and are not independent samples. Historical tokens and wall-clock time are unavailable, so this report makes no fresh cost or speed claim from the Tier A cases.

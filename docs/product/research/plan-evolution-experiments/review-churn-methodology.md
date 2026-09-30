# Real-corpus spec and plan review-churn methodology

Date frozen: 2026-09-27

## Question

Which review-loop structure preserves useful spec and plan defect coverage while reducing repeated findings, repair-induced findings, and prose-only review work?

This retrospective study replaces the synthetic reviewer proxy as the primary churn evidence. It uses review histories already produced by this repository. It does not infer model tokens, cost, or wall-clock duration where provider telemetry was not retained.

## Units

- A **raw finding** is one item emitted by a reviewer.
- A **strict defect cluster** is one underlying defective claim or mechanism, even when later wording or line locations change.
- An **invariant family** groups distinct defects that violate the same rule on different surfaces.
- A **repeat** is the same strict defect surviving or reappearing in a later round.
- A **repair-origin finding** requires evidence that a previous repair introduced the defective state. A missed propagation or a defect discovered late is not automatically repair-origin.
- A **same-invariant distinct finding** is a different defective surface or mechanism under an already-contested invariant.
- A **clean round** is a recorded zero-finding verdict. Without a subject digest, it proves only what the retained report says; it does not prove identical review coverage.

## Evidence tiers

### Tier A — independently re-scorable round artifacts

1. `credential-broker-contract`: five joint spec/plan rounds, including a clean closure round.
2. `portfolio-first-run-pilot-architect`: four pre-execution joint spec/plan rounds. Later implementation reviews are excluded.
3. `work-loop-review-verdicts`: three fresh pre-execution contract-review rounds plus a retained disposition record.
4. `plan-evolution-experiments`: six adversarial pre-execution rounds and two security rounds. The raw reports are session-local, so normalized findings and limitations must be retained in the final report.

Two Codex classifiers independently normalize the two larger durable histories. A separate finding adjudicator resolves material disagreements. The current initiative is also classified twice independently.

### Tier B — retained aggregate case evidence

1. `install-to-ship-walkthrough`: a five-round trajectory retained as a promoted knowledge topic, with finding counts and repair-origin counts but without the original round reports.
2. The occasioning nonconvergence case: 15 rounds and 30 sustained findings, retained in the repository survey without the complete raw transcript set.

Tier B can corroborate a mechanism but cannot be pooled with Tier A as if it were independently re-scored evidence.

### Tier C — prior paired build-stage experiments

The review-economics and focused-re-review spikes measure broad versus focused implementation re-review with provider telemetry. They answer a related build-stage loop question. They do not answer the spec/plan packaging question and are reported separately.

## Frozen inclusion rule

Include a case in Tier A only when the repository retains:

1. at least two ordered pre-execution review reports over a spec, plan, or accepted contract;
2. explicit finding items or an explicit clean verdict in every included round;
3. enough text to distinguish the pre-execution sequence from implementation review; and
4. a durable path, except for the current run whose normalization is retained because its `.context` reports may be pruned.

Exclude implementation-only histories from the spec/plan score. Keep triggered security review separate from the main adversarial sequence. Do not infer causal origin from round order alone.

## Measures

For each case and round, record:

- raw findings and adjudicated disposition where available;
- strict clusters and invariant families;
- new, repeated, same-invariant distinct, repair-origin, late-discovered, and indeterminate findings;
- blocker/high findings separately from advisory findings;
- review prose bytes and whitespace words where the original report is available;
- scope cuts, deferrals, and clean closure rounds;
- whether intermediate reviewed revisions, subject digests, prompts, model identity, tokens, and timing survive.

Across cases, report ranges when classifiers disagree or the retained record cannot distinguish strict recurrence from a distinct surface under the same invariant. Do not convert report words to model tokens.

## Comparisons

1. **Repeated broad pre-execution review:** later-round unique clusters versus repeat, same-invariant, and repair-origin work.
2. **Locked versus evolving plan:** recorded delivery failures caused by a hash-pinned plan versus cases where cutting or amending plan claims closed the loop.
3. **Separate spec and plan versus lighter goal-based delivery:** repository-wide repair rate after controlling for implementation size, document-only finding share, and traceability-only findings.
4. **Broad versus focused build re-review:** protected-class coverage and provider-reported tokens from the prior paired experiments.
5. **Model allocation:** stronger pre-execution versus build models only where exact model identity and comparable tasks were retained. Otherwise the result is unavailable.

## Decision rules

- Prefer a loop topology only if it retains blocking/protected-class coverage.
- Treat fewer raw findings as reduced churn, not as improved quality, unless cluster coverage is independently adjudicated.
- Treat a majority repair-origin round or repeated invariant family as a signal to simplify, delete, or defer the contested plan claim; it is an advisory trigger, not a validated automatic gate.
- Do not require a zero-finding verdict. Stop on an external bound with blocking findings closed and advisory residue recorded.
- Re-open broad review after a trust-boundary change, material scope change, contract amendment, merge/base drift, or evidence that the focused envelope omitted whole-change state.

## Known limits

Most historical review notes were committed together, so intermediate spec and plan revisions cannot be reconstructed. Most lack prompts, model identity, tokens, and timing. Finding counts are sensitive to reviewer aperture. The repository-wide aggregate studies may overlap the named cases, so their counts are not added together. Separate documents and immutable documents are distinct treatments; the available evidence compares full spec/plan delivery with goal-based delivery, not a randomized two-file versus one-file packaging experiment.

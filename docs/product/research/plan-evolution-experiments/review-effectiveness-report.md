# Natural-work review effectiveness baseline

Date: 2026-09-29

## Baseline result

T14 freezes the natural-history baseline and starts zero model processes. The
usable retrospective evidence is narrow but clear about one failure mode:
repeated broad prose review keeps returning to already-contested ground.

Across the four Tier A histories, 17 review starts produced 75 findings and 63
strict defect clusters. Those clusters are useful recurrence evidence, but they
are not durable blockers under the new definition. The retained histories do
not prove which findings changed an accepted requirement, implementation, test,
or protected control and then closed, so durable blocker closure and unique
durable blockers per review start stay unavailable.

Exact prose-churn events are unavailable retrospectively because the histories
do not prove that the 38 later findings were blocking findings after an
accepted revision, and do not retain enough accepted-surface and no-new-evidence
lineage. The retained proxy is same-family recurrence: 32 of 38 later findings,
or 84.2%, either repeated a strict defect or landed on a different surface
under an already-contested invariant family. That is the signal T15 must
measure with proper event lineage.

## Tier A scorecard

| Measure | Retrospective value | Limit |
| --- | ---: | --- |
| Review starts | 17 | Counts retained ordered review rounds, including clean closure rounds. |
| Raw findings | 75 | Descriptive only; not a quality denominator. |
| Strict defect clusters | 63 | Recurrence and defect-cluster proxy only; not durable blockers. |
| Durable blocker closure | unavailable | Strict clusters and clean reports do not prove accepted-surface or protected-control closure lineage. |
| Protected escapes | unavailable | No retrospective stopped-revision shadow audit exists. |
| Unique durable blockers per review start | unavailable | The retained source does not directly identify durable blockers. |
| Repair-origin blockers | 5 / 38 later findings = 13.2% | Credential broker has 0 proven and up to 11 unresolved. |
| Accepted-surface reopenings | unavailable | Accepted-surface state per finding was not retained. |
| Same-family recurrence | 32 / 38 later findings = 84.2% | This is a recurrence proxy, not exact prose churn. |
| Same-revision reviewer/adjudicator disagreement | 1 / 5 = 20.0% where dispositions survive | Only the work-loop review-verdicts case retains same-revision dispositions. |
| Appeal reversal or indeterminacy | unavailable | The retained `indeterminate` value is lineage-classification uncertainty, not appeal or adjudication indeterminacy. |
| Exact prose-churn numerator / denominator | unavailable / unavailable | The 38 later findings are not proven blocking findings after an accepted revision. |
| Recurrence proxy per review start | 32 / 17 = 1.88 events per review start | Not pooled as prose churn. |
| Attributable review/adjudication/repair actions | review actions 17; adjudication and repair unavailable | Historical role/action telemetry is incomplete. |
| Tokens and wall time per durable blocker | unavailable | Durable blockers closed and historical provider telemetry are unavailable. |
| Findings that changed scope, code, tests, or protected controls | unavailable | Not consistently retained by finding. |

## Case rows

| Case | Review starts | Findings | Strict clusters | Durable closure | Same-family recurrence | Repair-origin blockers |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Plan evolution current | 5 | 10 | 9 | unavailable | 4 | 3 |
| Credential broker contract | 5 | 41 | 31 | unavailable | 19 | 0 proven; up to 11 unresolved |
| Portfolio first-run pilot | 4 | 19 | 18 | unavailable | 7 | 2 |
| Work-loop review verdicts | 3 | 5 | 5 | unavailable | 2 | 0 |

The retained arithmetic is direct: repair origin uses `5 / 38 = 0.1316`.
Same-family recurrence uses `32 / 38 = 0.8421`. Strict clusters sum to
`9 + 31 + 18 + 5 = 63`, but they are not durable blockers and are not used for
closure or blocker-yield claims.

## Aggregate histories kept separate

Two aggregate cases corroborate the mechanism but are not pooled with Tier A.

| Case | Retained observation | Why not pooled |
| --- | --- | --- |
| Install-to-ship walkthrough | Five rounds with finding trajectory 26, 10, 8, 4, 1; 12 of 18 findings in rounds 2 and 3 were repair-origin. | Finding-level raw reports and accepted-surface lineage are not retained. |
| Occasioning 15-round Claude Code loop | 15 rounds, 30 sustained findings, 18 findings in two families, 9 repair-origin findings, and each of the last 8 rounds returned exactly one finding. | Complete raw transcript set is unavailable; the round-20 counterfactual is unknowable. |

The repository-wide survey is also not pooled. It covered about 4,300 session
transcripts, 1,273 merged pull requests, 431 spec/plan pairs, and 4,060
numbered acceptance criteria. It found 112 runs with review artifacts and 50
that exceeded five review ordinals. It also found that 85.6% of nonblank
`plan.md` lines were narrative no gate, task router, or acceptance-criterion
reference reads; 51% of full-mode findings landed only on spec/plan text,
against 6% record-only findings in light mode.

## T13 boundary

T13 stays in a separate methodological-negative table. It consumed 95 terminal
starts under a 96-start cap and filed 190 findings across seven review rounds:
4, 31, 41, 15, 41, 10, and 48. Its final carried state was 88 sustained, 3
refuted, and 99 unadjudicated findings.

Those numbers do not support a natural work-loop effectiveness claim. The
dominant result was apparatus failure: tautological checks, self-matching
taxonomy tests, shape checks presented as property checks, fail-open carry
behavior, stale byte bindings, and grader decisions on judgment surfaces.

## What this changes for T15

The prospective cohort must measure the failure the retrospective record can
only point at. That means each admitted case needs finding-level lineage for
accepted-surface state, new evidence, protected risk, repair origin, review
actions, adjudication actions, repair actions, tokens, and wall time. A shadow
audit is the only source for protected escapes.

T15 now has a pending release record, not a launch. Its immutable contract is
canonically bound by SHA-256
`d7a8e6978134900ee05f22fb1c428d27fd3e50b2d6cc4cac61496616951bd91f`, computed
from `jq -cS '.prospective_reserved_event.release_record.immutable_contract'
review-effectiveness-baseline.json`. The old pre-record baseline digest is
kept only as unverified provenance. Independent review approved this canonical
contract digest; owner approval and every future admitted case must cite it.

The contract freezes consecutive admission after approval, a 12-case or
30-calendar-day window, an 8-terminal-case minimum for a complete pilot, and a
24-start measurement cap: 12 shadow audits plus at most 12 adjudication batches.
Normal work-loop starts are observed operational cost, not study-added starts.
It also freezes the closed exclusion catalog, controller-only exclusion
decisions, ambiguous/in-flight handling, and an explicit ban on selecting or
excluding by model, route, finding count, severity count, outcome, predicted
outcome, convenience, reviewer availability, or study help.

Each prospective case must enter a single-writer controller ledger with a stable
case key built only from immutable enumeration-time fields, frozen statuses,
atomic update/recovery rules, duplicate/conflict failure, and count/digest
reconciliation. The stopped revision is not part of identity; it is a separately
reconciled required field. Each case also carries a closure envelope binding the
reviewed revision, exact stopped revision, artifact
digests, stop reason, terminal receipt, sustained finding ids, repair surface,
affected dependencies, acceptance criteria, tests/gates, protected controls,
repair-origin checks, and advisory residue.

The record uses the installed work-loop role/model policy for normal work and
records requested/resolved models only when observable. One fresh cold
adversarial-reviewer shadow audit runs on the exact stopped revision. Advisory
shadow prose is recorded only in aggregate and is never returned as repair work.
A shadow finding counts as an escape only when independent adjudication sustains
it on a stable requirement, executable failure, protected risk, or genuinely new
external evidence.

The decision rule stays non-scalar. Zero protected escapes is the safety floor;
an effectiveness reading also needs at least 8 terminal cases, at least 80%
complete finding-lineage fields under the frozen denominator, and cost telemetry
that separates normal loop cost from shadow/adjudication overhead. Lineage
grain is one required case row for every terminal admitted case plus zero or
more finding rows, so zero-finding and no-adjudication cases still contribute a
case-row denominator. `unknown` and `unavailable` nulls count incomplete;
`not_applicable` nulls leave the denominator only with a reason code. Cost
telemetry is sufficient only when at least 80% of terminal cases have all
normal-loop action/token/time fields, 100% have all study-added
shadow/adjudication action/token/time fields, and every prose-churn event has
complete attributable review/adjudication/repair action counts, returned
input/output tokens, and wall time. Otherwise the prospective study reports
incomplete. It may not claim token or wall-clock savings against this
retrospective baseline because the historical telemetry is missing.

The scorecard now includes prose-churn-attributable review, adjudication, and
repair actions, input tokens, output tokens, wall time, and share of normal-loop
cost. A fail-closed controller screen runs before retaining a row or building
shadow/adjudication prompts; suspected sensitive material is retained only as a
digest, generic reason code, and quarantined/not-retained status. Measurement
starts require an observable no-write, no-network, no-delegation,
no-external-messaging, no-escalation, no-protected-config authority profile.
Pre-launch hard controls bind exact serialized prompt bytes to 120,000 bytes,
requested output tokens to an exposed request parameter capped at 12,000, input
tokens to a 120,000 preflight upper bound from exact payload bytes or a
controller-exposed tokenizer/count, and wall clock to a 3,600-second controller
timeout. Hidden system/provider tokens that cannot be bounded stay outside the
measured payload authority. Actual returned input/output tokens and wall time
are post-run telemetry. Per-case and cohort observed cumulative limits stop the
next start; they cannot retroactively gate a completed start.

Independent adversarial and quality closure review are clean for the canonical
contract digest, and the owner approved that exact digest. Consecutive-case
admission is authorized from `2026-09-29T21:19:31Z` through
`2026-10-29T21:19:31Z`; no prospective case or measurement start exists yet.

## Sources

- `review-effectiveness-baseline.json` contains the frozen event rows and
  arithmetic inputs plus the independently reviewed and owner-approved T15
  release record.
- `review-churn-results.json` binds the Tier A, Tier B, and repository aggregate
  values used here.
- `review-loop-nonconvergence-survey.md` binds the occasioning loop and
  repository-wide survey.
- `review-churn-evidence-report.md` binds the T13 exclusion and prior
  real-corpus interpretation.

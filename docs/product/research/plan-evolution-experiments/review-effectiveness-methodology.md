# Natural-work review effectiveness methodology

Date frozen: 2026-09-29

## Purpose

This file freezes the retrospective baseline before any prospective T15 case is
eligible. It measures whether review closes durable delivery risk at a
proportionate cost without creating a prose-repair loop. It does not score
models, require a zero-finding verdict, pool synthetic seeded-defect results, or
emit one scalar effectiveness score.

## Evidence classes

The classes below are kept separate in every table and arithmetic step.

| Class | Included evidence | Use |
| --- | --- | --- |
| Tier A natural histories | Four independently normalized pre-execution histories from `review-churn-results.json` | Main retrospective baseline where round-level finding counts and lineage survive. |
| Tier B aggregate histories | `install-to-ship-walkthrough` and the occasioning 15-round Claude Code loop | Mechanism corroboration only; not pooled with Tier A event rows. |
| Repository aggregate | The repository-wide transcript, PR, spec/plan, and acceptance-criterion survey in `review-loop-nonconvergence-survey.md` | Prevalence and mechanism context only. |
| T13 synthetic | The Sol T13 block and its seven review rounds | Methodological negative control only; no natural-work quality or cost claim. |
| Prospective natural work | Independently reviewed and owner-approved release record v1; four candidates enumerated, three admitted, none reaching `measured_terminal` | Cohort closed 2026-10-02 as incomplete. `review-effectiveness-report.md` § *Prospective cohort result* owns the outcome and the three blockers behind it. |

## Inclusion and exclusion rules

A Tier A history is included only when the repository retains all of the
following before this freeze:

- at least two ordered pre-execution reviews over a spec, plan, or accepted
  contract;
- explicit finding items or an explicit clean verdict for every included round;
- enough text to distinguish pre-execution review from implementation review;
- durable source paths, or a retained normalized current-case record when the
  raw reports are session-local.

Tier B retains aggregate histories when the repository preserves the trajectory
and mechanism counts but not enough raw reports for independent recoding.

Excluded evidence stays inspectable but does not contribute to Tier A
scorecard arithmetic: implementation-only histories, T13 seeded subjects,
synthetic review-policy contrasts, model-allocation blocks, and prospective
cases admitted after this freeze.

## Event schema

The baseline JSON uses a small explicit event row. Missing values are `null`
with a `missing_reason`; unavailable historical telemetry is never estimated.

| Field | Meaning |
| --- | --- |
| `event_id` | Stable row id. |
| `evidence_class` | `tier_a`, `tier_b_aggregate`, `repository_aggregate`, `t13_synthetic`, or `prospective_reserved`. |
| `case_id` | Source case or aggregate id. |
| `source_refs` | Durable source path and sha256 entries that bind the row. |
| `revision_identity` | Ordered revision or round identity when retained; otherwise explicit unavailable reason. |
| `review_start_count` | Observable review starts in the included sequence. |
| `finding_count` | Raw finding count retained for the event. |
| `strict_defect_clusters` | Retained strict cluster count used only as a defect-cluster and recurrence proxy. |
| `durable_blockers_closed` | Directly supported durable blockers closed; unavailable when only strict clusters or clean reports survive. |
| `protected_escapes` | Shadow-audit protected escapes; unavailable retrospectively unless a shadow audit exists. |
| `repair_origin_blockers` | Findings proven to have been introduced by a previous repair. |
| `accepted_surface_reopenings` | Reopened accepted-surface blockers; unavailable unless retained lineage proves the surface was previously accepted. |
| `same_family_recurrences` | Later findings that repeat a strict defect or land on a different surface under an already-contested invariant family. |
| `same_revision_disagreement` | Same-revision reviewer/adjudicator disagreement when retained. |
| `appeal_reversal_or_indeterminate` | Refuted or indeterminate finding dispositions when retained. |
| `prose_churn_events` | Blocking findings against unchanged, previously accepted text with no new requirement, executable failure, protected risk, or external evidence. |
| `prose_churn_denominator` | Blocking findings after the first accepted revision in the same case. |
| `review_cost`, `adjudication_cost`, `repair_cost` | Observable action, token, and wall-time fields by role. |
| `changed_accepted_surface` | Counts of findings that changed scope, code, tests, or protected controls when retained. |

## Scorecard rules

The report computes only direct ratios whose numerator and denominator are both
retained in the source-bound baseline.

- Durable blocker closure requires direct retained lineage that a sustained
  blocker against a stable requirement, executable failure, protected risk, or
  new external evidence changed an accepted requirement, implementation, test,
  or protected control and then closed. Strict clusters and clean reports alone
  do not prove that lineage, so retrospective durable blocker closure stays
  unavailable unless a row carries that direct support.
- Protected-defect escape is unavailable retrospectively because no retained
  Tier A case has an independent shadow audit on the stopped revision.
- Unique durable blockers per review start uses only directly supported durable
  blockers. The Tier A strict-cluster counts are retained as a defect-cluster
  and recurrence proxy, not promoted to durable blockers.
- Repair-origin blockers require proof that the pre-repair state lacked the
  defect and the repair introduced it.
- Same-family recurrence is the retained retrospective churn measure: later
  findings that repeat a strict defect or revisit an already-contested invariant
  family.
- Prose-churn events require accepted-surface, blocking-finding, and
  no-new-evidence lineage after the first accepted revision. The Tier A record
  does not retain that complete lineage, so both the exact numerator and exact
  denominator are unavailable. The report separately shows the 32/38
  same-family recurrence proxy and does not rename it as prose churn.
- Tokens, wall time, resolved model, and session identity are recorded only
  when the source retained them. Historical Tier A telemetry is unavailable.
- Findings that changed accepted scope, implementation, tests, or protected
  controls are counted only where the retained record says so directly.

## T15 prospective release record

`review-effectiveness-baseline.json` now freezes
`t15-prospective-natural-work-v1` as a pending release record. Its source
baseline digest is
`17e16b75befa735e123784f88f2cc4792ac17cd36dd670942a56d635bc453c03`, captured
before the release record was added. That old digest is unverified provenance
only. The authority binding is the canonical SHA-256 over the immutable
contract:
`d7a8e6978134900ee05f22fb1c428d27fd3e50b2d6cc4cac61496616951bd91f`. The
canonical byte stream is produced with `jq -cS
'.prospective_reserved_event.release_record.immutable_contract'
docs/product/research/plan-evolution-experiments/review-effectiveness-baseline.json`.
Approval records and every admitted case must cite that digest. Mutable release
state is separate and records independent review and owner approval against
that digest. Consecutive-case admission is authorized from
`2026-09-29T21:19:31Z` through `2026-10-29T21:19:31Z`, subject to the frozen
12-case, safety, authority, and resource gates.

The release admits consecutive full-mode pre-execute spec/plan review units in
this repository after approval. Admission stops at 12 cases or 30 calendar days,
whichever comes first. A complete pilot needs at least 8 terminal cases; fewer
than 8 terminal cases is reported as incomplete. Every consecutive eligible
case is included. Cases are not selected by model, finding count, outcome, or
convenience. New spec versus amendment and specialist-review triggers are
recorded as strata, not balanced by selection.

Eligibility requires accepted intent, exact reviewed and stopped revision
digests, normal work-loop artifacts, repository-safe non-personal and non-secret
content, permission to retain the minimized event fields, and the verified
canonical contract digest. The controller is the sole decider for a closed
exclusion-code catalog. Each exclusion needs source evidence, a non-secret
rationale, and one frozen code; ambiguous or in-flight candidates remain open
until the window closes and then become an explicit before-launch exclusion.
The catalog bans selection by model, route, finding count, severity count,
outcome, predicted outcome, convenience, reviewer availability, or study help.

The prospective case ledger has one writer: the controller. It enumerates
candidate cases from consecutive full-mode pre-execute work-loop admission
points, assigns a stable SHA-256 case key from immutable enumeration-time fields
only, stores one of the frozen statuses, updates atomically, recovers only from
the last JSON-valid reconciled ledger, and fails closed on duplicate or
conflicting case keys. The stopped revision is not part of identity; it is a
separately reconciled required field before shadow prompt construction. Before
shadow launch and before reporting, counts and sorted row digests must reconcile
with the cohort summary.

Each case carries a closure envelope. The envelope binds the reviewed revision,
the exact stopped revision, artifact paths and SHA-256 digests, stop reason,
terminal receipt digest, sustained finding ids, repair artifacts, changed
sections, affected dependencies, acceptance criteria, tests or gates, protected
controls, repair-origin regression checks, and advisory residue. Shadow and
adjudication prompts may use only that exact stopped revision, the minimized
envelope, and non-secret provenance.

Normal work uses the installed role and model policy with no study override.
One fresh cold adversarial-reviewer shadow audit runs on the exact stopped
revision. If it claims blockers, at most one independent finding-adjudicator
batch may run for that case. The study may add at most 12 shadow-audit starts
and 12 adjudication starts, for 24 measurement-specific starts. Normal
work-loop starts are observed operational cost, not study-added starts.

The protected classes are stable acceptance or contract failure, executable
test or gate failure, security/privacy/authority boundary failure, data loss or
corruption risk, public interface break, and unrecoverable operational failure.
Style, unsupported prose preference, and advisory wording do not become
protected risks by themselves. A shadow blocker counts as an escape only when
independent adjudication sustains it on a stable requirement, executable
failure, protected risk, or genuinely new external evidence.

Broad review reopens only for contract or material scope change, trust-boundary
change, base or merge drift, repair outside the closure envelope, evidence that
the closure envelope omitted whole-change state, or a sustained shadow escape.
Any sustained protected escape reopens delivery under normal safety rules,
stops further cohort admission, and prevents an effectiveness recommendation.
Advisory shadow prose is recorded in aggregate and is never returned as repair
work.

The decision rules deliberately avoid a scalar score. Zero protected escapes is
the safety floor. An effectiveness reading also needs at least 8 terminal cases,
at least 80% complete finding-lineage fields under the frozen denominator, and
the frozen cost-telemetry threshold. Lineage grain is one required case row for
every terminal admitted case plus zero or more finding rows. Zero-finding,
clean, and no-adjudication cases still contribute the case-row denominator.
Present values count complete. `unknown` and `unavailable` nulls stay in the
denominator and count incomplete. `not_applicable` nulls need a reason code and
leave the denominator only for genuinely inapplicable finding/action fields.
Cost telemetry is sufficient only when at least 80% of terminal cases have all
normal-loop action, returned-input-token, returned-output-token, and wall-time
fields; 100% have all study-added shadow/adjudication cost fields; and every
prose-churn event has complete attributable review/adjudication/repair action
counts, returned input/output tokens, and wall time. Otherwise the study
reports incomplete. The prospective report may not claim token or wall-clock
savings against the retrospective baseline because historical tokens and wall
time are missing.

The scorecard includes prose-churn-attributable review, adjudication, and repair
actions; input tokens; output tokens; wall time; and share of normal-loop cost.
Operational loop cost is reported separately from shadow/adjudication
measurement overhead.

A fail-closed controller-side screen runs before retaining a row or building
shadow/adjudication prompts. Suspected personal data, credentials, protected
configuration, or unrelated source bodies are represented only by digest,
generic reason code, and quarantined/not-retained status, and are not sent to a
model. Measurement starts require an observable least-privilege profile: exact
stopped-revision inputs only; no writes, web/network, delegation, external
messaging, approval escalation, or protected-configuration access. If the
profile is not observable, the case is excluded before launch.

Measurement starts have explicit launch controls. Before launch, the controller
counts the exact serialized payload bytes against a 120,000-byte cap, binds a
12,000 requested-output-token cap to an exposed request parameter, derives a
120,000 input-token preflight upper bound from exact payload bytes or a
controller-exposed tokenizer/count, and applies a 3,600-second controller
timeout. If the requested-output-token parameter, input-token bound, or timeout
is absent, the case is excluded before launch. Hidden system tokens,
provider-injected tokens, and provider accounting fields the controller cannot
observe before launch are outside measured payload authority. Returned
input/output tokens and actual wall time are post-run telemetry. Per-case
observed cumulative limits are 240,000 prompt bytes, 240,000 returned input
tokens, 24,000 returned output tokens, and 7,200 seconds. Cohort observed
cumulative limits are 2,880,000 prompt bytes, 2,880,000 returned input tokens,
288,000 returned output tokens, and 86,400 seconds. Per-case and cohort
observed cumulative limits stop the next start; they do not retroactively gate a
completed start.

Collection stays minimal: source paths and digests, categorical lineage, counts,
timestamps and token metadata already returned by tools, and revision digests.
The study does not retain raw chat/session transcripts, hidden reasoning,
credentials, personal data, protected configuration, or unrelated source bodies.

## Limitations frozen for T15

The retrospective baseline is purposive, not sampled. Most histories lack
intermediate reviewed revisions, exact model identity, provider tokens, wall
time, prompts, and complete repair lineage. The repository-wide aggregates may
overlap named cases and are never added to Tier A totals. T13 remains a
methodological negative result about experiment construction and does not
validate a natural-work policy. The prospective release passed independent
review and owner approval, and the cohort it authorized ran and then closed
incomplete on 2026-10-02 without producing a compliant effectiveness reading.
`review-effectiveness-report.md` § *Prospective cohort result* owns that
outcome, the three blockers behind it, and the observations the cohort does
support.

The prospective limitation that matters most for a successor is not in the list
above, because it was not foreseen: **the contract required measurements that
were never recorded while the work ran.** No finding rows were written against a
contract requiring one 24-field row per finding, normal-loop returned tokens
were never split into input and output, and prose-churn attribution was never
captured at all. The host telemetry those needed is session-local, so none of it
can be recovered after a case closes, and estimating a missing measurement value
is barred. Design the recording path before the first case, not after.

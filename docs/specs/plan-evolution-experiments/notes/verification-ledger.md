# Verification Ledger: Plan Evolution Experiments

## T15 owner release approval — 2026-09-29

- **Owner authority:** the owner explicitly approved canonical immutable-
  contract SHA-256
  `d7a8e6978134900ee05f22fb1c428d27fd3e50b2d6cc4cac61496616951bd91f`
  after independent adversarial and quality closure review was clean.
- **Authorized window and budget:** consecutive eligible cases may be admitted
  from `2026-09-29T21:19:31Z` through `2026-10-29T21:19:31Z`, stopping earlier
  at 12 admitted cases or any sustained protected escape. Measurement-specific
  capacity is at most 12 shadow audits plus 12 adjudication starts.
- **Current accounting:** admitted cases 0; measurement starts 0. Approval does
  not fabricate a case, waive the frozen eligibility/authority/resource gates,
  or turn advisory shadow prose into repair work.
- **Workflow handoff:** the controller recorded the T15 release-record
  implementer receipt, passed the final-wave verification edge, entered the
  clean intermediate human gate, and recorded clean review round 2. The
  approved continuation then superseded that intermediate receipt and returned
  the engine to `CODE-IMPLEMENTATION` at transition sequence 111 so T15 can
  observe the next consecutive eligible natural-work case. T15 is not complete.

## T15 release record independently reviewed — 2026-09-29

- **Reviewed authority:** canonical immutable-contract SHA-256
  `d7a8e6978134900ee05f22fb1c428d27fd3e50b2d6cc4cac61496616951bd91f`.
- **Closure evidence:** adversarial and quality closure reviews are clean in
  `.context/reviews/f9820f7a-959c-4e25-b3af-712db602b313/10-post-repair-adversarial-reviewer-raw.md`
  and the adjacent `10-post-repair-quality-engineer-raw.md`. Security closure
  was clean at round 9; the round-10 repair changed case identity, measurement
  arithmetic, and limit timing without widening the reviewed authority or data
  surface.
- **Release state:** `independent_review_status` cites the canonical digest,
  `owner_status` remains pending, `prospective_starts_authorized` remains false,
  and admitted cases and measurement starts remain zero.

## T15 release-review second repair — 2026-09-29

- **Repair authority:** `.context/reviews/f9820f7a-959c-4e25-b3af-712db602b313/9-post-repair-findings-adjudication.md`
  sustained the stable-key, launch-limit, lineage-row, and prose-churn-cost
  gaps repaired here.
- **Canonical digest updated:** changing `immutable_contract` changed the
  canonical SHA-256 to
  `d7a8e6978134900ee05f22fb1c428d27fd3e50b2d6cc4cac61496616951bd91f`,
  computed with `jq -cS
  '.prospective_reserved_event.release_record.immutable_contract'
  docs/product/research/plan-evolution-experiments/review-effectiveness-baseline.json`.
- **Repair scope:** `stable_case_key` now uses only immutable
  enumeration-time fields and excludes the stopped revision, which remains a
  separately reconciled required field. Hard limits now split pre-launch
  enforceable controls from post-run observed telemetry. Lineage grain is one
  required case row per terminal admitted case plus zero or more finding rows.
  Cost sufficiency now requires complete prose-churn-attributable actions,
  returned input/output tokens, and wall time for every prose-churn event.
- **Approval state:** `owner_status` and `independent_review_status` remain
  pending, `prospective_starts_authorized` remains false, and no model,
  reviewer, adjudicator, provider, shadow-audit, or cohort process was
  launched.
- **Validation:** JSON was validated with `jq empty`; the canonical digest was
  recomputed with `jq -cS ... | shasum -a 256`. No repository-controlled Python
  or Make command was run for this repair.

## T15 release-review repair — 2026-09-29

- **Repair authority:** `.context/reviews/f9820f7a-959c-4e25-b3af-712db602b313/8-post-gates-findings-adjudication.md`
  sustained the T15 release-record blockers and concerns repaired here.
- **Immutable contract binding:** `review-effectiveness-baseline.json` now
  separates mutable release state from `immutable_contract`. The canonical
  contract digest is
  `d7a8e6978134900ee05f22fb1c428d27fd3e50b2d6cc4cac61496616951bd91f`,
  computed with `jq -cS
  '.prospective_reserved_event.release_record.immutable_contract'
  docs/product/research/plan-evolution-experiments/review-effectiveness-baseline.json`.
  The prior pre-record baseline digest is retained only as unverified
  provenance, not authority.
- **Repair scope:** the immutable contract now freezes the closed exclusion-code
  catalog, controller exclusion evidence and decider rules, ambiguous/in-flight
  handling, model/outcome/finding-count/convenience selection ban, prospective
  case ledger contract, stable case key, statuses, atomic update/recovery,
  duplicate/conflict rule, count/digest reconciliation, closure-envelope schema,
  exact reviewed/stopped revision bindings, lineage field set and denominator,
  null handling, cost telemetry sufficiency, prose-churn-attributable cost
  fields, privacy/secret/protected-config screen, observable least-privilege
  measurement authority, and per-start/per-case/cohort byte/token/time limits.
- **Approval state:** `owner_status` and `independent_review_status` remain
  pending, `prospective_starts_authorized` remains false, and no model,
  reviewer, adjudicator, provider, shadow-audit, or cohort process was launched.
- **Validation:** JSON was validated with `jq empty`. No repository-controlled
  Python or Make command was run for this repair.

## T15 prospective release record pending review — 2026-09-29

- **Task phase recorded:** the release-record phase of T15 is frozen in
  `review-effectiveness-baseline.json` as `t15-prospective-natural-work-v1`.
  `review-effectiveness-methodology.md` and `review-effectiveness-report.md`
  describe the same pending release. No prospective case, reviewer,
  adjudicator, provider, or shadow-audit process was launched.
- **Source binding:** the release record retains the pre-record baseline digest
  `17e16b75befa735e123784f88f2cc4792ac17cd36dd670942a56d635bc453c03` and
  timestamp `2026-09-29T19:29:16Z` as unverified provenance only. Release
  authority comes from the canonical immutable-contract digest recorded in the
  T15 release-review repair entry above.
- **Approval state:** independent review and owner approval are pending. Until
  both gates pass, prospective starts remain zero and no case is eligible for
  admission.
- **Frozen cohort rule:** after approval, admit consecutive full-mode
  pre-execute spec/plan review units in this repository. Stop at 12 admitted
  cases or 30 calendar days. Require at least 8 terminal cases for a complete
  pilot and report incomplete otherwise. Record new spec versus amendment and
  specialist-trigger strata without balancing or outcome selection.
- **Frozen measurement rule:** normal work uses the installed work-loop
  role/model policy with no study override. Measurement may add one fresh cold
  adversarial-reviewer shadow audit per exact stopped revision and, only when
  that shadow claims blockers, one independent finding-adjudicator batch.
  Measurement-specific cap is 12 shadow starts plus at most 12 adjudication
  starts, 24 total. Normal work-loop starts are observed operational cost, not
  study-added starts.
- **Frozen decision rule:** zero protected escapes is the safety floor. An
  effectiveness reading also requires at least 8 terminal cases, at least 80%
  complete finding-lineage fields, and telemetry that separates normal loop
  cost from shadow/adjudication overhead. Otherwise the result is incomplete.
  No scalar score is defined and no savings are claimed against the
  retrospective baseline because historical tokens and wall time are missing.

## T14 natural-history effectiveness baseline — 2026-09-29

- **Task closed:** T14 now freezes the retrospective natural-work baseline in
  `review-effectiveness-methodology.md`, `review-effectiveness-baseline.json`,
  and `review-effectiveness-report.md`.
- **Evidence separation:** Tier A natural histories, Tier B aggregate cases, the
  repository aggregate survey, T13 synthetic evidence, and prospective T15
  evidence remain separate. T13 appears only as a methodological-negative row.
- **Tier A arithmetic:** the baseline retains 4 cases, 17 review starts, 75 raw
  findings, and 63 strict defect clusters as a recurrence/defect-cluster proxy.
  It no longer promotes strict clusters or clean reports into durable blockers.
  Durable blocker closure and unique durable blockers per review start are
  unavailable retrospectively. Same-family recurrence is 32 of 38 later
  findings (84.2%); proven repair-origin blockers are 5 of 38 later findings
  (13.2%).
- **Unavailable fields preserved:** exact prose-churn events, protected escapes,
  the exact prose-churn denominator, accepted-surface reopenings, appeal
  indeterminacy, historical tokens, wall time, resolved model identity, repair
  action counts, and consistent changed-surface counts are recorded as
  unavailable rather than estimated.
- **Aggregate context retained:** the install-to-ship aggregate and occasioning
  15-round Claude Code loop are retained as Tier B mechanism evidence only. The
  repository-wide survey is retained for prevalence and surface-shape context
  only. None of those rows are pooled with Tier A.
- **No starts:** this reconstruction launches no model, reviewer, adjudicator,
  calibration, provider, or prospective process. T15 still requires a separate
  reviewed release record and owner approval before any prospective start.

## T13 methodological closeout receipt — 2026-09-29

- **Task closed:** T13 is recorded as a methodological negative result. Its
  synthetic block remains provider-labelled and separate from retrospective and
  prospective natural-work evidence.
- **Terminal accounting:** `.context/codex-headless-sol-loop-confirmation-result.md`
  and `.context/experiments/codex-headless-sol-loop-confirmation-r1/analysis/accounting.json`
  record 95 terminal starts under the 96-start cap, 0 nonterminal starts, and 1
  unused adjudication start. The tracked report now repeats those values.
- **Review evidence:** the T13 handoff records seven review rounds with filed
  counts 4, 31, 41, 15, 41, 10, and 48, for 190 findings total. The carried
  status is 88 sustained, 3 refuted, and 99 unadjudicated. The report now names
  those rounds as evidence, not as a clean-review claim.
- **Apparatus conclusion:** `sealed/instrument-layer-retirement.json` records
  that round 7 exposed the self-certifying apparatus reproducing its own defect
  families: tautological checks, self-matching taxonomy tests, shape checks
  presented as property checks, fail-open carry behavior, stale byte bindings,
  and grader decisions on judgment surfaces. Seven self-certifying modules were
  retired and retained under `tools/retired/`; their history was preserved
  rather than repaired again.
- **Effectiveness exclusion:** `review-churn-evidence-report.md` now explicitly
  excludes T13 seeded recall and synthetic policy contrasts from natural
  work-loop effectiveness recommendations. Seeded recall remains descriptive of
  the T13 panel only; closure-vs-replay contrasts remain synthetic and
  inconclusive for natural delivery behavior.
- **No further starts:** this closeout launches no model, reviewer,
  adjudicator, calibration, Sonnet, Opus, holdout, or T13 repair/review
  process. The single unused start under the T13 cap stays unused.

## Natural-work effectiveness amendment authority — 2026-09-29

- **Owner authority:** after reviewing the T13 seven-round outcome and the
  proposed replacement measurement, the owner explicitly approved changing how
  work-loop effectiveness is measured.
- **Reason:** the synthetic cross-model block became an experiment-construction
  and test-data exercise. Its cold reviewers, repairers, and graders generated
  large amounts of prose churn, but the block did not diagnose the real failure
  seen in the mined Claude Code and repository histories: cold reviewer and
  appeal cycles can keep contesting prose after the delivery risk is already
  closed. T13 is therefore retained as a methodological negative result, not as
  work-loop effectiveness evidence.
- **Replacement question:** measure durable delivery risk removed from
  consecutive real work per review cost, while accounting for defects and churn
  introduced by the loop. Do not use seeded-defect recall, raw finding count, a
  scalar quality score, or a later model's `Clean` verdict as the primary
  effectiveness measure.
- **Replacement design:** recode the existing natural review histories first,
  freeze eligibility and classification rules, then observe a bounded cohort of
  consecutive eligible work-loop cases. Each case gets the normal broad review
  and triggered specialist review, blocker adjudication, repair, and one focused
  closure review. One independent cold full-document audit runs only as a shadow
  measurement on the exact stopped revision; it does not reopen advisory prose.
- **Primary outcomes:** durable blocker closure, protected-defect escape,
  unique durable blockers per review start, repair-origin blockers,
  accepted-surface reopening, same-family recurrence, same-revision
  reviewer/adjudicator disagreement, appeal reversal or indeterminacy, and
  observable tokens, wall time, and repair or adjudication actions per durable
  blocker closed. A finding counts as useful only when it changes scope, code,
  tests, or a protected control, or is independently sustained against a stable
  contract and evidence.
- **Stopping rule:** stop when blocking consequences are closed. Record advisory
  residue. A zero-finding or `Clean` verdict is not required. A new blocker after
  closure needs a stable requirement, executable failure, protected risk, or
  genuinely new external evidence.
- **Schedule authority:** stop the current Sonnet/Opus and synthetic holdout
  path. T14 and T15 may be rewritten only into the natural-history baseline and
  bounded prospective cohort. No new experimental process starts are authorized
  by this amendment; a prospective allocation, minimum cohort, and thresholds
  require a separately reviewed and owner-approved release record.
- **Preserved evidence:** T13's raw artifacts, seven review rounds, retirement
  record, terminal accounting, and standalone handoff remain unchanged. The
  seeded recall result and synthetic policy comparisons are excluded from
  work-loop effectiveness claims rather than deleted or repaired again.
- **Declined addition:** no new self-certifying gate, mutation registry,
  promotion model, hidden grader, or fixed-point loop. Existing natural-corpus
  records and a small event table with direct arithmetic are sufficient.
- **Assurance notes:** the prior base-freshness waiver remains scoped to this
  initiative. The optional skill-engineering knowledge provider is unavailable
  on the active tool surface, so no provider evidence is used.

## Natural-work amendment pre-execute review — 2026-09-29

- The required adversarial review sustained one blocker: the first draft
  defined a prose-churn event but omitted it from the required scorecard, so the
  study could pass without measuring the failure that occasioned the amendment.
- The repair adds the exact numerator and denominator, events per review start,
  and attributable reviewer, adjudicator, and repair actions, tokens, and time.
  Missing historical lineage remains unavailable rather than estimated, and
  T14 and T15 both verify the measure.
- Round 2 is direct clean. The validated raw report is
  `.context/reviews/f9820f7a-959c-4e25-b3af-712db602b313/8-pre-execute-adversarial-reviewer-raw.md`
  with sha256
  `74b12980b87d0d6bc6a2bc7f5b51d18571074f7a3c4ec52969e3394d4c582e3c`.
- The first persistence attempt reused review ordinals 1 and 2 from the same
  durable run. The frozen natural-history validator caught the resulting source
  digest collision before wave exit. The amendment reports were rebound to the
  next unused ordinals 7 and 8; the historical optional paths remain absent, and
  no historical report bytes or normalized result changed.
- Security review is not warranted: this amendment removes future synthetic
  provider launches and changes research classification and scheduling, not a
  security boundary, data flow, guarding control, tool authority, permission,
  sandbox, or handling rule.

## Cross-model sensitivity amendment authority — 2026-09-29

- **Owner authority:** after receiving the reconciled 586-start total, the
  proposed Sol-first schedule, the 892-start maximum, and the refusal-only
  headroom, the owner explicitly approved a 920-start outer ceiling and the
  amended T13–T15 sequence: Sol confirmation, Sonnet/Opus differential checks,
  then holdout and independent report.
- **Reason:** Runs 2–7 established useful non-inferential behavior under
  requested Luna routing, but the user requires the key behaviors checked under
  Sol and then compared with Sonnet and Opus. Run 7's five-defect registry was
  too sparse to measure review recall or repair benefit, so the new matched
  review panel must use controller-seeded, structurally verifiable, repairable
  defects frozen before policy assignment.
- **Start arithmetic:** 586 prior process starts + at most 96 Sol starts + at
  most 72 Sonnet starts + at most 72 Opus starts + 18 holdout starts + at most
  48 conditional packaging/continuity starts = 892. The approved ceiling of
  920 leaves 28 refusal-only starts. They are not an adaptive reserve.
- **Files in scope:** amend `spec.md` and `plan.md`, retain this authority and
  later observations in the verification ledger, and update ignored `.context`
  controller handoffs. The controlled amendment preserves every completed run
  and its durable report.
- **Done evidence:** the spec owns the 920 ceiling, provider order, seeded-defect
  review requirement, release limits, and revised acceptance checks; the plan
  owns dependency-ordered T13–T15 tasks, exact maximum allocations, review
  checkpoints, and verification modes; pre-execute adversarial review is clean;
  both human gates and the amended schedule are sealed before a model starts.
- **Not changing:** no completed response, registry, score, exclusion, finding,
  or report is rewritten or pooled; served identity remains unavailable unless
  controller-observed; no candidate code is executed; all inferential release
  flags remain false.
- **Declined addition:** no new orchestration abstraction. `Cut before adding`
  rung 2 applies because the existing provider-labelled controller and atomic
  handoff layout can run the bounded Sol block.
- **Assurance notes:** the owner previously waived the enterprise-blocked base-
  freshness probe for this initiative. The optional skill-engineering knowledge
  provider is unavailable on the active tool surface, so no provider evidence
  is used.

## Cross-model amendment pre-execute review — 2026-09-29

- Adversarial review is clean after two rounds. The first round sustained three
  contract gaps: it bound the Sol packaging allocation to its three treatments,
  replaced the overstated pristine-holdout claim with a pre-T13-frozen main-
  informed external validation, and made seeded subject selection mechanically
  reproducible from the complete eligible digest set.
- Security review is clean after three rounds. It first required a typed,
  bounded untrusted-data frame with controller-owned provenance and explicit
  authority exclusion for worker-visible source bodies. Closure review then
  extended the same body, frame, complete-prompt, and schema digest checks to
  the T15 external-validation prompts.
- The final adversarial raw report is
  `.context/reviews/f9820f7a-959c-4e25-b3af-712db602b313/2-pre-execute-adversarial-reviewer-raw.md`
  (sha256 `74b12980b87d0d6bc6a2bc7f5b51d18571074f7a3c4ec52969e3394d4c582e3c`).
  The final security raw report is the adjacent
  `5-pre-execute-security-reviewer-raw.md` with the same exact clean sentinel
  and digest.
- Scanner-owned SAST, dependency, secret, and CVE checks are not part of this
  reasoning-only contract review. Runtime provider isolation, served model
  identity, and future output handling remain execution evidence.

## T12 headless Codex review-and-repair exit — 2026-09-29

- The provider-separated `codex-headless-via-claude-run7-r1` block completed
  six calibration starts and 171 main starts: 96 reviews, 72 repairs, and three
  adjudication batches. Every reservation is terminal, all 36 copy and lineage
  paths reconcile, and no response was repaired or retried after a model start.
- Closure review—one broad review, two repair opportunities, and one cold full
  closure review—matched full replay on every subject's registered end state:
  three residual severe defects and five residual total defects in each arm.
- Closure used 12 fewer review starts (-33.3%), 295,027 fewer tokens (-19.5%),
  244.24 fewer summed worker seconds (-16.2%), 766 fewer raw review words
  (-32.4%), and 583 fewer churn words (-57.0%). All six task clusters favored
  closure on starts, tokens, worker time, and churn.
- Focused rereview also matched the registered end state and had the lowest
  churn total, but it saved no review starts and used 282,296 more tokens than
  closure.
- Detection noninferiority is not established. The source corpus carried only
  five registered defects across three of 12 subjects; final recall was
  defined for only three matched pairs and was zero in both closure and full
  replay. No repair changed a registered defect set, so repair-benefit and
  repair-origin contrasts are uninformative.
- Reviewers raised 103 findings: eight sustained, 94 mechanically refuted, and
  one duplicate. A mechanical refutation means only that the narrow registry
  modeled no defect at that element; it does not prove reviewer error.
- Transport was clean: zero tool events, schema failures, process failures,
  timeouts, quarantines, or exclusions. One repairer echoed the wrong envelope
  alias; its document stayed valid and the response remained terminal.
- Independent digest verification matched the two handoffs and all 18 named
  source artifacts, including six schemas. Standalone evidence lives in
  `codex-headless-review-repair-run-7-report.md` and
  `codex-headless-review-repair-run-7.json`.

## T11 headless Codex model-allocation exit — 2026-09-28

- The provider-separated `codex-headless-via-claude-run6-r1` block completed
  eight calibration and 96 main starts: 48 cold planners and 48 cold
  constructors. Every reservation is terminal, all 48 constructor inputs match
  their planner-artifact digest, and no cell was stopped.
- Transport was clean: zero tool events, schema failures, prose outside JSON,
  process failures, timeouts, quarantines, repairs, or retries after a model
  start. Requested routes were balanced at 24 starts each per stage; served
  model identity remained unavailable.
- The equal-one-stronger-call comparison did not establish a phase-allocation
  advantage. Planner incorrect choices favored a standard planner plus stronger
  constructor by 0.58, while planner self-audit false positives and constructor
  field completeness favored stronger planning. Final correct decisions and
  residual severe errors did not separate the allocations.
- Stronger-planner placement used 543 more output tokens and 12.5 more summed
  worker seconds than stronger-constructor placement. Every stronger-route
  policy cost more than the all-standard cell without a detected end-quality
  gain. The working default is standard routing with triggered escalation, not
  a fixed strong-planner or strong-constructor policy.
- Seventeen planner and fourteen constructor measures had no variance. Lexical
  semantic coverage was 99.6% at both stages, only four task clusters were
  sampled, and no trajectory was clean under the severe-error grader. These
  limits make small capability differences hard to detect.
- Two controller rules changed after planning and before construction: a bare
  adjective was removed from the blinding label list, and input-carried
  contradiction markers were voided through a cell-invariant block union.
  Both original and corrected counts remain available.
- Independent integrity review matched 22 of 24 frozen artifact digests. The
  two expected mismatches are the amended `blinding.py` and `score.py`; their
  current bytes and amendment records are now bound in the durable summary,
  but the source records did not bind before/after digests. The result remains
  non-inferential and carries that mutation-proof gap.
- Standalone evidence lives in
  `codex-headless-model-allocation-run-6-report.md` and
  `codex-headless-model-allocation-run-6.json`.

## T10 headless Codex construction panel exit — 2026-09-28

- The provider-separated `codex-headless-via-claude-runs2-5-r1` block
  reconciled 112 reservations: 4 calibration, 18 plan-author, and 90
  construction terminals. The controller observed 123 CLI starts, 108 model
  starts, 18 continuations, 11 provable zero-model-start quarantines, no
  tool-use violations, and 2,593.94 seconds of controller wall clock.
- Amendment authority caused a complete behavioral split. All 69 returned
  responses in amendable arms amended; the frozen arm amended 0 of 17 and
  recorded a conflict in 14. Four amendments were invalid under the frozen
  amendment schema.
- The unified contract matched the separate-file baseline on detected coverage,
  acceptance, and scope measures. It used 83 fewer output tokens and 20 fewer
  response words per matched task. This supplies no quality evidence that
  separate specification and plan files help, but lexical grading was at
  ceiling and the six-task result is non-inferential.
- Same-worker continuation used 2.14 times the input and 1.65 times the output
  tokens of the cold baseline. It scored 0.78 fewer correct decisions per task
  while saving 3.25 seconds and 99 visible words. Excluding the one
  probe-contaminated cell makes the decision and coverage means slightly worse.
- The narrative artifact was about 55% longer, but total input rose only 1.6%
  because fixed context dominated. Its null coverage result cannot support a
  broad claim that plan prose volume has no cost or value.
- Eleven continuity starts failed before a request was built because `codex
  exec resume` rejected two flags; they were quarantined and relaunched under
  byte-identical payloads. Four cold cells orphaned during the driver repair
  had indeterminate model-start status, so they were closed, not relaunched,
  and excluded.
- Independent digest verification passed for all 14 published source
  artifacts. Standalone evidence lives in
  `codex-headless-construction-panel-runs-2-5-report.md` and
  `codex-headless-construction-panel-runs-2-5.json`.

## T9 headless Codex Run 1 exit — 2026-09-28

- The provider-separated `codex-headless-via-claude-r1` block completed after
  eight of eight transport calibrations passed. It produced 144 terminal cold
  reviewer starts and 12 terminal blind-adjudication starts with zero process
  failures, tool-use violations, response repairs, retries after model start,
  or protocol deviations.
- The block reused the frozen six-task, 54-trajectory corpus and stayed
  separate from the two partial Codex collaboration responses and the Claude
  subagent block. Requested model `gpt-5.6-luna` is recorded; served model
  identity remains unavailable.
- Cold closure versus full replay used 33.3% fewer starts and input tokens,
  30.6% fewer raw words, 64.9% fewer churn words, and 32.5% less summed worker
  time. Observed recall was 1.39 percentage points lower and precision 3.49
  points higher.
- The result does not clear the five-point noninferiority gate under task-
  cluster uncertainty. A deterministic 20,000-resample task-cluster bootstrap
  placed the closure recall difference at -9.26 to +4.17 points. Inferential
  release stays false.
- Focused rereview retained the full current artifact and therefore saved no
  starts or input tokens. It produced 6.5% more words and 5.7% more output
  tokens than full replay while reducing churn words by 20.4%.
- Task complexity was the larger descriptive effect: medium tasks averaged
  75% recall and complex tasks 50% across policies.
- Standalone evidence lives in
  `codex-headless-review-policy-run-1-report.md` and
  `codex-headless-review-policy-run-1.json`. Neither depends on this ledger,
  the feature contract, or the implementation plan to explain the study.
- Verification: eight focused workbench tests passed; Ruff passed; mypy passed
  across 149 source files.

## T9 Codex Run 1 partial collection — 2026-09-28

- The complete six-task, three-policy, three-replication corpus passed every
  pre-launch gate: 54 trajectories, 144 frozen review prompts, 12 reserved
  adjudication templates, hidden-registry isolation, exact prompt/payload
  equality, treatment-label blindness, and contiguous study ordinals 17–172.
- Two distinct fresh Codex collaboration reviewers started and terminated for
  frozen slots 001–002. Their exact raw outputs and terminal receipts are
  retained under `.context/experiments/codex-collaboration-r1/run-1/`.
- The dispatcher omitted reliable pre-launch UTC timestamps for those starts.
  Their quality and prose outcomes remain observable, but their wall-clock
  values are unavailable and are not imputed or replaced.
- Slot 003 never started. The dispatcher then reached the collaboration
  surface's two-child thread limit, its parent could not open a fresh relay,
  and the root had no fresh direct child slot. The collection paused with two
  starts, two terminals, 142 review slots unstarted, and no retries, response
  repair, worker reuse, or adjudication starts.
- Controller-side registry scoring at the pause is only a preliminary
  diagnostic: three of four registered defects found, three of three findings
  sustained, both major defects found, one minor overclaim missed, and zero
  subject-reported protocol deviations. No policy comparison is possible.
- A provider-separated Claude handoff at
  `.context/claude-run1-review-policy-experiment.md` reuses the exact frozen
  corpus and scoring truth. Its results must remain labelled and unpooled.

## Run 0b recovery authority — 2026-09-28

- **Owner authority:** the owner said `go ahead` after receiving the completed
  Run 0a failed-calibration report and the proposed recovery: preserve Run 0a,
  add a separately labelled Run 0b, use eight fresh cold workers, dispatch the
  exact frozen prompt text, request the declared model route explicitly, and
  keep later runs closed until the replacement calibration passes.
- **Reason:** Run 0a reached eight terminal responses but its controller used a
  compact rendering rather than the frozen prompt bytes. All eight rendering
  receipts failed and two responses failed the schema whose exact enums and
  types the compact transport omitted. The durable causal record is
  `docs/product/research/plan-evolution-experiments/codex-collaboration-run-0-report.md#decision`.
- **Files in scope:** amend only the unfinished T8 contract and its Run 0
  artifacts, add Run 0b packets, prompts, receipts, terminal records, and a
  standalone recovery report, then reopen T9 only if the frozen gate passes.
- **Done evidence:** eight new study ordinals have one start and one terminal
  each; actual dispatch bytes hash to the frozen prompt bytes; strict parsing,
  schema, alias, atom, privacy, deviation, and accounting checks pass; Run 0a
  remains unchanged and separately indexed.
- **Not changing:** no Run 0a response is repaired or reused, no main-run
  hypothesis is scored, and no candidate code or subject output is executed.
- **Declined addition:** no new orchestration abstraction. `Cut before adding`
  rung 2 applies because the existing packet, receipt, and evidence-index
  layout is adequate for a bounded replacement calibration.
- **Disposition record:** the Run 0a transport defect is required and will be
  fixed through the unfinished T8 contract. Model identity and tool-use
  observability remain explicit residual limits rather than invented evidence.

## Run 0b amendment pre-execute review — 2026-09-28

- Adversarial round 1 sustained one blocker: T8 did not require the standalone
  recovery report named by the owner authority before T9 could reopen.
- T8 now requires
  `docs/product/research/plan-evolution-experiments/codex-collaboration-run-0b-report.md`
  in its output map, touched files, and completion gate.
- Adversarial round 2 returned direct clean. A secure-design pass was not
  warranted because the amendment does not change worker authority, inputs,
  tool exposure, data flow, or guarding controls; it changes only dispatch-byte
  fidelity, accounting, and a required report under the existing non-secret
  document-only boundary.

## T8 Run 0b recovery exit

- Run 0a remains unchanged and failed-closed. Run 0b consumed fresh study
  ordinals 9–16: eight explicit `gpt-5.6-luna` collaboration starts and eight
  terminal JSON records, in the frozen launch order.
- All eight controller message payloads matched their newly frozen prompt bytes.
  All eight responses passed strict JSON, frozen schema, exact alias, six-atom
  coverage, privacy, reported-deviation, static-registry, and terminal-accounting
  checks. The calibration gate passed and later non-inferential document
  collection is eligible to open; every inferential release flag remains false.
- The first static-grade execution recognized `faster sync` but not the lexical
  equivalent `faster-sync` in slot 011. The controller corrected only that
  hyphen normalization under the pre-existing registry rule “explicitly corrects
  or rejects”; no response, registry fact, threshold, or scoring obligation
  changed. The idempotent rerun passed 8 of 8.
- Served model identity, provider tokens, reliable wall clock, independent tool
  traces, secure confinement, and hidden runtime framing remain unavailable.
  Message-payload byte equality does not claim equality to hidden system or
  developer context.
- Durable evidence is the provider-labelled
  `codex-collaboration-run-0b.json`,
  `codex-collaboration-run-0b-report.md`, the shared collaboration evidence
  index, and the eight tracked Run 0b packets. Raw prompts, payloads, receipts,
  controller records, and terminal JSON remain under the ignored Run 0b
  workbench.

## Document-only amendment authority — 2026-09-28

- **Owner authority:** eugenelim explicitly approved a controlled amendment on
  2026-09-28 to run real, non-secret, document-only Codex subjects under
  instruction isolation after T7 proved candidate-code confinement unavailable.
- **Evidence class:** all such results are non-inferential. They may measure
  reviewer recall, precision, repeated findings, review rounds, prose churn,
  amendment behavior, and document quality, but cannot support candidate-build
  performance or secure-confinement claims.
- **Safety boundary:** no experimental subject executes candidate, grading,
  regression, or repair code. Prompts contain only synthetic or repository-
  public text, request no web, delegation, escalation, or external messaging,
  and retain the exposed-tool limitation in every result.
- **Reason:** `/usr/bin/sandbox-exec` profile application returned exit 71
  (`Operation not permitted`). Filesystem, egress, and descendant-process
  confinement therefore remain unobservable in the managed host.

## Document-only amendment pre-execute review — round 14

- Security adjudication was clean.
- Adversarial adjudication found one launch-rule contradiction: AC-0005A still
  grouped Run 0 with inferential releases even though the amendment allows only
  non-inferential document collection. The criterion now keeps exposed tools as
  a named limitation for document subjects while secret-bearing input and any
  requested or observed forbidden use terminate the subject.

## T6 collaboration-runner wave exit

- The pure-standard-library runner compiles the frozen 566-start allocation
  under the unchanged 600 ceiling and keeps every inferential release closed by
  default.
- Eight focused tests passed in 0.63 seconds. Ruff passed. Mypy passed across
  149 source files.
- No experimental subject, candidate subprocess, or study ordinal started.

## T7 task-package wave exit

- Eight provider-labelled task-package manifests were frozen. Seven have a
  resolved hidden-oracle recipe; `shared-lint-driver` is explicitly
  `oracle-recipe-incomplete`.
- All eight calibration records are terminal `non-executed` records. The T7
  outcome is `stopped-before-run-0`; all release flags are false.
- Experimental subject starts, candidate subprocess starts, and ordinals
  consumed are all zero. The provider-labelled evidence index records the
  confinement failure without retaining secret or personal bytes.

## Causal-run redesign authority — 2026-09-27

- **Owner authority:** eugenelim approved the surfaced seven-run causal matrix
  on 2026-09-27 and directed the controller to plan, prepare, and run it.
- **Reason:** the completed Codex and Claude calibration blocks established
  that strong candidate-only confinement and provider token telemetry are not
  available in the active enterprise runtimes. The earlier retrospective
  review-churn evidence cannot answer the causal questions by itself.
- **Authorized boundary:** replace the unreleased CLI factorial with real,
  cold Codex collaboration-worker spikes that are instruction-isolated rather
  than security-confined. Keep pre-change Git-free candidate roots, external
  hidden oracles, fresh workers, randomized ordinals, blind grading, three
  replications, six main tasks, two untouched holdouts, and explicit
  contamination limits.
- **Approved run sets:** calibration; pre-execute review policy; locked versus
  controlled-evolving plans; separate versus unified artifacts; thin versus
  narrative plans; planner-builder continuity; requested planner/builder model
  allocation; and post-build review-loop policy. Shared controls are permitted
  where the surfaced matrix named them.
- **Measurement authority:** directly observed quality, scope, amendments,
  review rounds, finding novelty, repair-origin defects, invocation counts,
  and review-prose churn are inferential measures. Wall clock and provider
  tokens are descriptive only when emitted and remain unavailable otherwise.
- **Preserved evidence:** the prior Codex and Claude calibration failures and
  retrospective churn study stay intact as separate provider and evidence
  classes. They are not pooled with the new causal runs or overwritten.

## Causal redesign pre-execute review — round 7

- The adversarial adjudicator sustained one finding: T13 named
  `docs/specs/README.md` without an acceptance criterion, while that directory
  has no hand-maintained index. The touch was removed.
- The security adjudicator sustained the disposable-path floor. The amended
  contract now rejects symlinks, reparse points, junctions, multiple hard
  links, special files, traversal, loops, and open-time identity changes before
  a disposable path reaches a command or evidence sink.
- The security adjudicator also asked for candidate-root-only authority
  canaries. That authority is unavailable in collaboration workers and the
  owner explicitly approved an instruction-isolated design. The contract now
  makes the boundary testable without claiming the unavailable control: every
  release records the managed permission/tool profile, requires platform
  denials for protected credential/configuration paths, stops on requested or
  observed network/delegation/escalation/external messaging, treats observed
  out-of-candidate access as terminal contamination, and permanently discloses
  possible unobserved access. No safety or causal claim treats candidate-only
  non-access as proven.

## Causal redesign pre-execute review — round 8

- Security adjudication was clean; the sole raw finding was refuted because it
  cited a closed legacy constraint while the active amendment already owns the
  instruction-isolation boundary.
- Adversarial adjudication sustained three planning defects. T6 now carries an
  exact red stub, Runs 1 and 7 each own and reconcile 12 of the 24 batched
  adjudicator starts, and the new `causal_runner.py` is explicitly
  pure-standard-library under `tools/AGENTS.md`.
- The exact T6 stub passed `python3 -m py_compile` and failed pytest collection
  only with the intended missing `causal_runner.py` surface on 2026-09-27.
  The disposable source file was removed after the check.

## Causal redesign pre-execute review — round 9

- Security adjudication was clean.
- Adversarial adjudication found one stale summary sentence that still said T1
  was the only exact red stub. The plan summary now names both completed legacy
  T1 and active collaboration T6, matching the task bodies before approval.

## Causal redesign pre-execute review — round 10

- Adversarial adjudication found that the closed CLI LLD still used active
  `Owned by:` fields naming T6/T7. Those fields are now explicitly historical,
  leaving the amended T6–T13 task bodies as the sole current ownership map.
- Security adjudication sustained four boundary gaps. The release record now
  covers observable credential environment, service-auth/runtime socket,
  broker, keyring, protected-configuration, and token-persistence surfaces
  without reading values; unobservable runtime isolation is labelled
  `non-secret-bearing-input-only` rather than claimed. Retrieved bodies are
  delimited untrusted data, candidate-executing commands have hard resource and
  process-tree caps, and raw workbench persistence has privacy, byte, and
  retention controls with digest-only quarantine.

## Causal redesign pre-execute review — round 11

- Adversarial adjudication found that the Run 1 and Run 7 ceilings exceeded
  the opportunities declared by their three policies. Run 1 now allocates 144
  review starts; Run 7 allocates 96 review and 72 repair starts; the maximum
  used is 566 under the unchanged outer ceiling of 600.
- Closed CLI durable-output and owner maps now use non-routing `legacy-L*`
  identifiers, so only the active T6–T13 collaboration map can route work.
- Security adjudication found that post-launch observation was too late for an
  exposed web or delegation surface. Inferential release now fails before
  launch unless web, network, delegation, approval escalation, and external
  messaging are absent or denied. A failing surface can yield only unreleased,
  non-inferential, `non-secret-bearing-input-only` evidence.

## Causal redesign pre-execute review — round 12

- Adversarial adjudication found three accepted controls without active task
  ownership. T6–T8 now prove candidate-command caps and raw-artifact privacy;
  T13 proves untrusted-source handling and the final privacy/retention chain.
- Security adjudication found that time and output caps alone did not confine
  untrusted candidate code. Every candidate, grading, regression, and repair
  subprocess now requires a secret-free environment, denied egress, confined
  readable and writable roots, protected-path denial, and fail-closed
  non-executed accounting when a property cannot be enforced or observed.

## Pre-execution records

- **Base freshness:** waived by the owner on 2026-09-25 after both the default
  and escalated checks failed at `git ls-remote origin` under enterprise
  authentication. The waiver applies only to freshness; isolation, test, and
  review gates remain required.
- **Knowledge provider:** unavailable in the active tool surface.
- **OpenAI documentation:** official-page retrieval returned no usable content
  in this session. Account-specific model availability and Codex JSONL usage
  fields remain calibration questions rather than documented assumptions.
- **TDD stub syntax:** `python3 -m py_compile` passed on the exact T1 stub in
  disposable scratch on 2026-09-25.
- **TDD intended red:** `python3 -m pytest -q` failed during collection with
  `FileNotFoundError` for the not-yet-created `runner.py`, which is the intended
  missing contract surface.
- **Scratch cleanup:** the disposable source file was removed. Empty
  pytest-created cache directories under
  `/private/tmp/plan-evolution-stub-validation/` resisted both normal and
  escalated removal with `Operation not permitted`; they contain no repository
  or experiment data.
- **Revised exact stub:** after the allocation-source repair, the exact T1
  block again passed `python3 -m py_compile` and failed pytest collection only
  because `runner.py` does not yet exist. The source copy was removed. Its empty
  ignored `.context/stub-validation/__pycache__/` directory also resisted
  cleanup with `Operation not permitted` and contains no files.

## Shaping review — round 1

- **High — H13 matching was not identifiable:** sustained. The spec now
  requires a within-task matched pair that differs only in artifact packaging,
  and the plan reserves two of five core episodes for that pair.
- **High — H3/H5/H11 had multiple primary controls:** sustained. Each now has
  one primary comparison; prose handoff, no-escalation standard builder, and
  decision-diff view are secondary.
- **Medium — H6 process shape conflicted:** sustained. H6 is now one versus
  three independent cold reviewers over unchanged blinded subjects.
- **Medium — first-wave wording conflicted:** sustained. The plan now states
  that the first 80 processes are 8 calibration plus 72 core.
- **Medium — TDD coverage overstated AC-0005:** sustained. The exact stub covers
  AC-0001 through AC-0003; isolation remains an integration/admission obligation.
- **Low — scratch cleanup history lived in the plan:** sustained. This ledger
  owns the observation; the plan retains only the validation outcome.

## Adversarial spec review — round 1

The independent adjudicator sustained all five reviewer findings.

- **Generated guidance target:** the durable output and T9 now edit the
  canonical core-pack `.apm` source, version both authored manifests, update the
  changelog, and regenerate/check self-host projections.
- **Missing H7 control:** every core builder now emits a fixed-schema final
  self-audit before grading or review selection; fresh reviewers remain blind
  to it, and T6 compares their findings with that retained control.
- **Duplicated process/token limits:** the spec's `Study allocation` and `Token
  and time budget` tables are the sole numeric owners. The plan and stub derive
  values from the frozen design instead of restating them.
- **Cherry-pickable admission:** the candidate universe is the exact 12-row
  table, with deterministic order, closed exclusion predicates, retained
  rejections, and no replacement after admission begins.
- **Stale four-task risk:** the risk now names the frozen 12-task corpus and its
  bounded external validity.

## Adversarial spec review — round 2

The independent adjudicator sustained both reviewer findings.

- **Contradictory task order:** the frozen candidate table's row order is now
  the sole admission order, and T2 says to process it from top to bottom.
- **Duplicated gate ceilings:** Agent Rules now reference the canonical
  allocation and stopping tables instead of copying wave and study numbers.

## Adversarial spec review — round 3

The independent adjudicator sustained the sole reviewer finding.

- **Undefined wave releases:** Sampling and stopping now owns one canonical
  reservation-release schedule with inclusive study ordinals, explicit gate
  prerequisites, temporary boundary refusal, post-gate continuation, and an
  outer-ceiling stop. Agent Rules, AC-0002, the T1 stub, and build tasks derive
  from that schedule.
- **Release-stub validation:** the revised exact T1 block compiled and its
  pytest collection failed only on the intended missing `runner.py` surface.
  Pytest again left an empty cache path under a disposable `/private/tmp`
  directory that the managed environment would not remove; no repository or
  experiment data was written there.

## Adversarial spec review — round 4

The independent adjudicator sustained both reviewer findings.

- **Impossible contiguity assertion:** the exact stub now compares adjacent
  fixed releases without strict equal-length zipping.
- **Reserve-release conflict:** the canonical schedule now splits W3 fixed
  work from the adaptive-reserve range. The W2 memo freezes admitted reserve
  item IDs, only their matching contiguous prefix is released, and the Agent
  Rules, AC-0002, stub, and T7 all reject undeclared reserve work.
- **Corrected release-stub validation:** the exact block compiles, and executing
  it in memory reaches only the intended `FileNotFoundError` for missing
  `runner.py`; this check created no scratch file or cache directory.

## Hacker News refresh — 2026-09-26

- A fresh Codex worker attempted the Hacker News item, `pure.md` recovery, and
  the Algolia item endpoint. The supported web retriever returned empty bodies,
  and one bounded direct attempt failed before HTTP because the worker's CA
  path was unavailable.
- The controller's first-party web search was also unavailable because its
  configured service credential was rejected. No browser runtime is exposed.
- Freshness is therefore **unverified**. No new comment, comment ID, linked
  resource, or hypothesis change is claimed. The prior local intake remains a
  141-point, 149-comment snapshot.
- The contract now requires capture time, counts, maximum comment timestamp and
  ID, tree digest, added-comment IDs, linked-URL set, and retrieval status, so a
  later refresh can produce a reproducible delta. A failed refresh never means
  that the thread had no new information.

## Security spec review — round 1

The independent adjudicator sustained all four reviewer findings.

- **Worker least privilege:** AC-0014 and the plan now require an explicit
  sandbox, candidate-only project access, stripped tool environment and
  credentials, no web/MCP/delegation/escalation, bounded resources, and
  negative calibration canaries before inference.
- **Path confinement:** AC-0015 names separate roots and requires
  canonicalize-then-contain checks, repository file-safety helpers where
  applicable, and equivalent construction tests for disposable roots and
  archives.
- **Resource SSRF:** AC-0016 removes HTTP/DNS from the workbench and workers,
  freezes exact source URLs, and permits only out-of-band first-party or
  owner-supplied evidence; discovered links are recorded, not fetched.
- **Structured input validation:** AC-0017 requires bounded strict schemas,
  finite JSON, duplicate/unknown-field handling, safe deserialization, and
  fail-closed validation before command, path, grade, gate, or report use.

## Clean pre-execution reviews

- Adversarial review round 5 accepted the staged reservation and adaptive
  reserve design.
- Security review round 2 accepted AC-0014 through AC-0017 and their plan
  coverage.
- Adversarial review round 6 accepted the security/source-refresh amendments,
  H1–H13 consistency, process ceiling, and standalone workbench/report split.

## Codex CLI contract slice — T1

- **Detected contract:** local `codex-cli 0.157.0` on 2026-09-26. The CLI
  warns that PATH-alias creation is blocked but returns help successfully.
- **Strong local flag oracle:** `codex exec --help` confirms `--model`,
  `--sandbox` with `read-only|workspace-write|danger-full-access`, `--cd`,
  `--add-dir`, `--ephemeral`, `--ignore-user-config`, `--ignore-rules`,
  `--output-schema`, `--json`, `--output-last-message`, and
  `--skip-git-repo-check`. The workbench must never use either dangerous
  bypass flag or `--approve-for-me`.
- **Continuity slice:** `codex exec resume --help` accepts a session UUID or
  thread name and supports `--model`, `--ephemeral`, `--ignore-user-config`,
  `--ignore-rules`, `--output-schema`, and `--json`; it does not expose the
  base command's `--sandbox`, `--cd`, or `--add-dir` flags. H3 resume cells
  must therefore inherit a previously proven session sandbox and fail closed
  if that inheritance cannot be observed.
- **Oracle tier:** strong for the installed invocation flags, weak for JSONL
  event fields and emitted usage data because help promises JSONL but publishes
  no event schema. A runtime probe is deferred to a counted T3 calibration slot;
  T1 accepts only versioned, bounded event envelopes and treats unknown usage
  fields as unavailable rather than guessing.

## Controlled amendment authority — 2026-09-26

- **Owner authority:** eugenelim explicitly approved the one-line plan
  amendment in-session on 2026-09-26 and authorized resealing the baseline.
- **Reason:** T1's exact stub uses `zip(releases, releases[1:])` for two
  intentionally unequal adjacent slices. The repository's Ruff B905 gate
  requires an explicit `strict=` argument, so the approved literal cannot pass
  the local gate even though its behavior is correct.
- **Bounded amendment:** change only that stub call to
  `zip(releases, releases[1:], strict=False)`. This preserves the assertion's
  semantics, hypotheses, allocations, safety controls, tasks, and evidence
  design.
- **Execution evidence before amendment:** the T1 targeted suite passed 11
  tests; `make lint-mypy` passed; `make lint-ruff` had exactly one remaining
  finding, B905 on the approved stub line. No experiment worker was launched.
- **Amendment verification:** after adding `strict=False` to the plan stub and
  its implementation copy, the targeted suite passed 11 tests, Ruff passed,
  and contract-item alignment reported zero findings. No pre-execute reviewer
  was re-fired because the authorized change is syntax-only, changes no
  structure or security boundary, and preserves the assertion's behavior.

## T1 wave exit — fail-closed workbench

- The frozen workbench validates H1–H13, the five process allocations, staged
  releases, role ceilings, the 12-task frame, provisional model IDs, exact
  source inventory, and a no-network dry-run policy. Its CLI refuses a real
  model spawn at this stage.
- The append-only ledger accepts exact bounded JSONL records, repairs only an
  unterminated malformed final record before the next append, rejects malformed
  earlier or newline-terminated records, and refuses duplicate items,
  terminals, fixed releases, reserve releases, ordinals, or out-of-order
  releases.
- Path checks allow run roots only at `/private/tmp/plan-evolution-*` or direct
  children of `.context/experiments/`; summaries are restricted to the durable
  research directory. Archive validation admits only contained regular files
  and directories, and output hard links are rejected.
- **Controller verification:** 18 targeted tests passed in 1.24 seconds;
  `make lint-ruff` passed; `make lint-mypy` passed across 149 source files; the
  validate and dry-run CLI smokes passed without starting Codex; contract-item
  alignment reported zero findings. The initial alignment invocation used file
  paths instead of its directory interface and was rerun correctly. No model
  process has started.

## T2 wave exit — frozen historical corpus

- All 12 baseline/reference pairs resolve to full 40-character commits. Each
  side was exported to a digest-pinned archive and re-rooted as an independent,
  clean, one-commit repository with no remotes, alternates, source refs, source
  objects, or hidden oracle inside the candidate root.
- Eight tasks were admitted because the reference passed and the baseline
  failed the same task-specific oracle: `work-loop-argless-resume`,
  `decision-record-ordinal-uniqueness`, `non-json-sso-guard`, `pack-profiles`,
  `atomic-write-symlink-hardening`, `catalogue-corporate-trust-store`,
  `shared-lint-driver`, and `agentbundle-engine-stragglers`.
- Four tasks were excluded at the first stable reason. `docs-print-cascade`
  lacks its frozen Node/Playwright dependencies and installation is out of
  scope. `workspace-routing-invariants` did not discriminate because both
  baseline and reference passed the bounded oracle. `core-path-confinement`
  and `work-loop-concurrency-reliability` run their cases but exit nonzero when
  the managed runtime prevents their historical cleanup, so neither has a
  clean reference pass.
- The durable evidence index records commit, tree, archive, candidate-head,
  isolation, oracle-result, output-digest, complexity, uncertainty, and stable
  exclusion data for every task. With 8 of 12 tasks admitted, the programme
  enters its predeclared bounded-case-study branch; it must not make the full
  cross-stratum confirmatory claim.
- T2 started no Codex model process. The process ledger remains at zero before
  the counted T3 calibration slots.

## T3 calibration exit — instruments remain locked

- The first T3 calibration command wrote eight W1 terminal reservations at
  study ordinals 1 through 8 and wave ordinals 1 through 8 before spawning
  Codex. The controller classified those as actual study evidence, not a
  rehearsal, because they were written to the durable T3 results and evidence
  paths.
- The controller then approved the spec's identical-replacement path for each
  assignment. Replacement reservations at study/wave ordinals 9 through 16
  link to ordinals 1 through 8 with the same role, model class, task treatment,
  and limits. The replacement security policy was deliberately hardened after
  the first terminal records, so the replacements are not policy-identical to
  the pre-spawn records.
- The replacement profile used `codex exec` 0.157.0 with `workspace-write`,
  candidate-only `--cd` and `--add-dir`, `--ignore-user-config`,
  `--ignore-rules`, `--ephemeral`, `--json`, `--strict-config`,
  `approval_policy="never"`, shell environment inheritance disabled, and
  feature disables for apps, plugins, multi-agent, MCP/plugin/tool suggestion,
  approval elicitation, proxy fallback, image generation, and skill
  search/install surfaces.
- Eight replacement Codex subprocesses were launched with synthetic-only nonce
  roots and no real secrets, hidden task material, source references, browser
  data, or credential files. Each terminal record preserves the requested
  model, resolved model status, argv policy, prompt digest, root nonce digests,
  output digest, token fields, event-schema status, and terminal reason.
- Each replacement subprocess exited `1` before any session identifier,
  resolved model identifier, usable JSONL event stream, token fields, effective
  runtime config, approval policy, or tool roster could be observed. Raw
  stdout/stderr were not committed; the durable records retain bounded output
  digests and classify the missing fields as unavailable.
- All eight replacement processes failed closed with
  `local-listener-unavailable`: the managed runtime refused the controller's
  loopback listener bind, so the egress canary could not be observed. The
  runner retained this as instrument loss instead of inferring safety from the
  failed setup.
- Durable `results.json` and `evidence-index.json` now retain all 16 terminal
  calibration reservations, 8 replacement links, 8 Codex subprocess starts,
  `instrument_loss_rate` 1.0, and `inference_launch_permitted: false`. No
  inferential slot has started.

## T3 repair review — F1 through F4

- **F1 environment repair:** future calibration subprocesses no longer inherit
  `os.environ`. The runner builds a minimal child environment from `PATH`,
  `TMPDIR`, and `PYTHONDONTWRITEBYTECODE` only, then adds synthetic canary
  variables. Real credential/auth variables such as `HOME`, `CODEX_HOME`, and
  `OPENAI_API_KEY` are not forwarded. If the CLI cannot run with that safe
  environment, the slot records `auth-env-unsafe`.
- **F2 listener repair:** a controller loopback-listener setup error now
  terminally fails the slot before writing `run_calibration_canaries.py` or
  starting Codex. The historical ordinals 9 through 16 are unchanged and remain
  evidence of the prior `local-listener-unavailable` outcome.
- **F3 capture repair:** future Codex calibration subprocesses use active
  bounded stdout/stderr readers with cap-triggered termination and timeout
  cleanup, rather than `subprocess.run(capture_output=True)` followed by
  post-hoc checks. The child starts in a new process group, and timeout or
  capture overflow terminates the group so background children cannot survive.
- **F4 reuse repair:** existing T3 `results.json` is now strictly validated
  before any record can drive replacement mode, counts, ordinals, or links.
  The validator checks result totals, record fields, enums, timestamps,
  token-field shapes, argv policy, synthetic-root nonce sets, unique items,
  contiguous ordered study and wave ordinals, model-class/requested-model
  mapping, role/model/item assignments, started/finished ordering,
  instrument-loss arithmetic, process-start counts, replacement identity, and
  replacement links. The current durable file validates to 16 records.

## T3 repair review — round 2

- **S1 origin binding:** existing durable calibration records must now match
  the exact originating progress ledger digest and run root before they can
  drive replacement mode. A fresh run directory cannot spend duplicate
  originals or replacements, and replacement or authority-widened terminals are
  non-replaceable.
- **S2 authority evidence:** worker-authored `canary-results.json` remains
  bounded evidence, but it cannot by itself prove worker authority. Controller
  observed effects, such as a listener connection, are required for
  `authority-widened`; otherwise ambiguity is terminal unobservable evidence.
- **S3 sink hardening:** disposable progress, terminal, and result sinks now
  reject link-like ancestors/finals, hard-linked or special final files, and
  unsafe writable ancestors. JSON sinks use atomic no-follow temp writes, and
  progress appends use no-follow append opens.
- **A1 legal-state reuse:** T3 reuse now accepts only complete legal states:
  exactly eight originals, or exactly those eight plus one replacement for each.
  The merged result is validated before any sink write.
- **A2 broken pipe:** if a launched child exits while stdin is being written,
  the runner preserves the actual child exit status and bounded streams instead
  of reclassifying the slot as a spawn error.
- **A3 prose correction:** the ledger now says replacements were assignment-
  identical by role, model class, task treatment, and limits, while their
  security policy was intentionally hardened and not policy-identical.

## T3 final bounded repair

- **Merged-result gate:** future calibration runs now validate the fully
  assembled result before writing `calibration-results.json`, durable
  `results.json`, or `evidence-index.json`. Partial, skipped, or preseeded
  progress states fail before those result/index sinks are mutated.
- **Pre-reservation root gate:** future calibration runs prepare and validate
  the run root, calibration directory, slot root, and every synthetic subroot
  before ledger reservation or generated prompt/nonce/script/controller writes.
  Missing directories are created private (`0700`), and preseeded symlinks,
  non-directories, canonical escapes, wrong-owner paths, unsafe group/world
  modes, and link-like ancestors fail closed.
- **Generated-file sinks:** generated prompts, nonce files, scripts, terminal
  records, result files, and progress appends use the no-follow safe sink
  helpers added in the prior repair. Regression tests cover result-sink
  refusal, symlinked subroots, and unsafe subroot modes without launching
  Codex or rewriting historical evidence.

## T3 final QE repair

- **Crash-resume ledger repair:** future calibration resumes no longer skip a
  reserve-only item. Before any later reservation, each started item must have
  both a terminal ledger event and a durable terminal record. A
  reserved-without-terminal crash state is closed once for the existing ordinal
  as `crash-resume-unknown-started`; duplicate reservation of the same item or
  ordinal remains refused. Legacy `crash-resume-infrastructure-failure`
  records that claim `not-started` are rejected before reuse.
- **Progress-ledger file safety:** progress JSONL reads and torn-final-line
  truncation now validate the progress path as a no-follow, single-link,
  regular-file sink before opening. Symlinked, hard-linked, special, or
  link-like progress paths fail closed and leave outside targets unchanged.

## T3 Q3/Q4 repair

- **Disposable terminal replay:** terminal-record replay for a previously
  closed calibration reservation now reads `terminal.json` through the
  disposable run-root confinement path, not the repository-confined JSON
  helper. The replay read is bounded, no-follow, duplicate-key rejecting, and
  non-finite-number rejecting before the full calibration-record validator runs.
- **Unknown-started crash accounting:** a reserve-only crash has no durable
  proof that launch had not happened, so future recovery writes a conservative
  `crash-resume-unknown-started` terminal for that existing ordinal. The record
  keeps session and token telemetry unavailable, uses `exit_status:
  unknown-started`, and counts against `model_processes_started` and the
  process ceiling. The historical run outcome is unchanged.

## T3 R1/R2 repair

- **Replay binding:** terminal replay now binds the loaded record to the
  current reservation before any later reservation can occur. The check requires
  the exact item, slot path and index, study and wave ordinal, role, model
  class, requested model, and replacement link to match the ledger assignment.
- **Crash-resume reuse rule:** accepted crash-resume terminal records must now
  be `crash-resume-unknown-started` with `exit_status: unknown-started`, so they
  count toward `model_processes_started`. Legacy
  `crash-resume-infrastructure-failure` records with `not-started` are rejected
  before reuse, and unknown-started crash-resume terminals are non-replaceable.

## T4 W1 gate exit

- T4 started no Codex subprocess, inferential worker, or new study ordinal.
  The W1 gate was generated deterministically from the existing T2 admission
  evidence and T3 calibration evidence.
- Durable `w1-gate-memo.json`, `results.json`, and `evidence-index.json` now
  record the `W2-unavailable` gate outcome and no inferential success claim;
  `wave-1.json` remains the frozen full W1 design contract.
- The gate leaves the unspent W1 core range, study ordinals 17 through 80, as
  64 would-be inferential reservations blocked without reservation. They are
  not terminal observations and cannot support a favorable inference claim.
- The frozen stop rules fired on aggregate evidence: instrument loss is 1.0,
  above the 5% W1 threshold, and admitted task coverage is 8 of 12, below the
  full-inference threshold.
- Strict-schema tests now cover W1 gate refusal of favorable rewrites,
  non-zero T4 process accounting, inferential success claims, and idempotent
  regeneration without dropping T2/T3 evidence.
- Sustained T4 repair: `wave-1.json` is again the frozen W1 design contract,
  not a gate-outcome summary. The W1 gate memo now binds `design_digest` to the
  exact validated `--design` file, refuses a mismatched frozen wave design, and
  validates `status_counts` plus `coverage_by_stratum` against admission records
  before deciding W2 availability.
- Final sustained consistency repair: the gate also derives the legal
  `inference_branch` from the record-backed admitted count and the frozen
  12-task frame. Eight admitted tasks can no longer be relabelled
  `inferential`; they remain `bounded-case-study`.
- Verification after the final repair: 48 focused workbench tests passed in
  11.28 seconds; Ruff passed; mypy passed across 149 source files.

## T5 W2 stopped-branch allocation memo

- T5 started no Codex subprocess, inferential worker, or new study ordinal.
  The W2 allocation memo was generated deterministically from the frozen
  `wave-1.json` design, the exact W1 gate memo, durable T4 results, and durable
  T4 evidence-index chain.
- Durable `w2-gate-memo.json`, `results.json`, and `evidence-index.json` now
  record `gate_decision: stopped-before-core`, `release_w3_fixed: false`, zero
  reserve item IDs, and zero T5 process or ordinal accounting.
- The stopped branch is truthful because W1 left W2 unavailable after
  instrument loss was 1.0 and admitted task coverage was 8 of 12. No W2 core
  slot was legally reservable, so H1-H5, H8, H10, H12, and H13 have explicit
  unavailable analysis inputs rather than inferred effects.
- `wave-1.json` remains the frozen W1 design contract; T5 writes no wave design
  and no outcome summary into that design file.
- Sustained T5 repair: unavailable W2, W3 fixed, and adaptive-reserve tranche
  boundaries are now named `unavailable_study_ordinals`, not released ordinals.
  Before T5 preserves or digests T4 evidence, it validates the full T4
  evidence-index shape, the T5 wrapper shape on rerun, and embedded admission,
  calibration, and W1 evidence blocks with exact keys.

## T6 review-unavailable branch

- T6 started no Codex subprocess, review worker, or new study ordinal. The
  review-allocation memo was generated deterministically from the frozen
  `wave-1.json` design, exact W2 gate memo, durable T5 results, and durable T5
  evidence-index chain.
- Durable `t6-review-memo.json`, `results.json`, and `evidence-index.json` now
  record `review_decision: unavailable-before-subject-selection`, independent
  review capacity of 36 processes, unavailable allocation state, and zero T6
  process or ordinal accounting.
- The stopped branch is truthful because T5 stopped before legal core builder
  outputs existed. No blinded subjects, builder self-audits, reviews, findings,
  or reviewer-churn measurements existed; H6, H7, and H9 inputs are explicit
  unavailable records rather than observed review performance.
- Sustained T6 repair: finding and reviewer-churn measures are unavailable
  records with the stopped-before-subject-selection reason, not numeric zero
  observations. Numeric zero remains only for eligible subjects, self-audit
  availability, process starts, reservations, and terminal review slots.

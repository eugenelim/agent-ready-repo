# Spec: Sealed-baseline replacement

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0099; RFC-0096; RFC-0094; ADR-0061; ADR-0074
- **Brief:** none
- **Discovery:** `docs/product/intents/cut-before-adding-solution-ladder.md`
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Any requested edit to a sealed spec or plan during implementation,
verification, or review enters one fail-closed `baseline-replacement-required`
route. The work-loop parks delivery before artifact edits, invalidates exact
approval hashes and executable schedule state through the existing state
owners, preserves the current diff and completed-work/attempt/review history,
returns both artifacts to drafting, and blocks implementation until shaping
review, adversarial spec-plan review, both human approvals, baseline sealing,
remaining-work scheduling, and plan locking all succeed again.

The same route handles material and nonmaterial post-seal edits; materiality is
recorded for audit but never grants a reduced exact-revision path. It is also
the sole owner-authorized escape from already-drifted pinned artifacts: sealed
and observed spec and plan hashes are recorded, but drifted bytes receive no
authority until the full replacement path seals them. Direct-light work remains
outside the durable baseline lifecycle.

## Boundaries

### Always do

- Park the engine before changing a sealed artifact and bind every cohort
  invalidation to the same run and engine transition.
- Keep `loop-engine` the sole engine-state writer and `loop-cohort` the sole
  cohort-state writer; make the cross-writer sequence idempotently recoverable.
- Preserve current repository reality, completed-task evidence, attempts,
  review history, worktree/commit evidence, and prior replacement audit.
- Re-run the complete contract/construction/human approval sequence for every
  changed exact revision.
- Schedule only work not proven complete against an unchanged task body.
- Record build-time contract questions and review dispositions outside the
  hash-pinned artifacts until their owner decides whether replacement is needed.

### Ask first

- Add or rename an FSM event/state, cohort mutation verb, persistent field, or
  compatibility rule beyond this contract.
- Change retry limits, review fingerprint semantics, task identity grammar, or
  human approval requirements.
- Reopen a task whose prior body is unchanged and recorded complete, or waive a
  changed task that the scheduler correctly returns to remaining work.
- Perform a destructive engine/cohort reset instead of the guarded route.
- Continue after a build-time finding when no referent establishes that both
  approved artifacts still hold.

### Never do

- Treat an in-place sealed-plan edit as approved, unrecoverable, or eligible for
  an advisory edit allowlist.
- Resume implementation with stale hashes, reviewer-clean state, schedule,
  plan lock, or artifact statuses.
- Clear or overwrite prior attempts, review counts/fingerprints, completed-task
  records, worktree/commit evidence, current diff, or replacement history.
- Infer that a partially executed legacy wave is complete; uncertainty remains
  scheduled.
- Apply this state machine to direct-light work or let a reviewer mutate it.
- Put review dispositions or build-time contract findings in `plan.md` or its
  template.

## Testing Strategy

- **TDD:** FSM legality, guarded/idempotent cohort invalidation, task-completion
  tracking, remaining-work scheduling, exact-hash rejection, history
  preservation, and every crash window use fresh state directories and real
  CLI subprocesses.
- **Goal-based checks:** work-loop instructions, state schema/reference,
  architecture, content assertions, status vocabulary, pack versions,
  projections, and catalogue/build gates remain mechanically aligned.
- **Visual / manual QA:** full code-mode runs enter replacement from each legal
  CODE state, crash before and after each mutation, resume through both human
  gates, reseal, schedule only remaining work, and return to implementation;
  observed engine/cohort/artifact states are recorded.

## Acceptance Criteria

### AC1 — One guarded park transition

- [ ] In code mode, `baseline-replacement-required` is legal from
  `CODE-IMPLEMENTATION`, `CODE-VERIFICATION`, and `CODE-REVIEW` and targets
  `SPEC-PLAN-DRAFTING`; it is illegal from every other state and in spec-plan
  mode.
- [ ] The transition requires an exact run identity and a closed materiality
  enum (`material | nonmaterial`), records bounded event context, and mutates no
  cohort or artifact file itself.
- [ ] It is the only event that may cross a failed plan-current guard: any
  already-drifted pinned artifact additionally requires explicit owner
  confirmation bound to the run ID and the sealed and observed spec and plan
  hashes. The closed mismatch set identifies `spec`, `plan`, or both, and no
  observed hash is adopted.
- [ ] Every refused transition exits non-zero and leaves engine/cohort/artifact
  bytes unchanged.
- [ ] Existing `findings-remain` continues to handle implementation findings
  that require no sealed artifact edit.

### AC2 — Cohort invalidation is idempotent, audited, and lossless

- [ ] An `invalidate-baseline` cohort mutation succeeds only when the paired
  engine is parked by the matching transition/run; it is idempotent for the
  same replacement identity and refuses mismatches without mutation.
- [ ] It appends a bounded replacement-history record containing materiality,
  sealed and observed artifact identity, prior schedule identity, prior wave
  position, and transition identity; it stores no finding body, prompt, secret,
  credential, or personal path.
- [ ] It resets approval status/hashes, plan hash, schedule waves, and current
  wave pointer while preserving retry counters, attempt identity, review
  counts/fingerprints, task-completion evidence, worktree/commit evidence, and
  earlier history.
- [ ] Status output exposes enough replacement state for deterministic resume
  without dumping sensitive source content.

### AC3 — Completed work is explicit and only unfinished work reschedules

- [ ] New code-mode runs record each completed task ID and canonical task-body
  hash idempotently after its declared construction tests pass; task identity
  remains the existing `T<n>[a-z]` grammar.
- [ ] The live work-loop execution path invokes that completion operation after
  each task's construction tests pass and before advancing or closing its wave;
  scheduler fixtures alone cannot satisfy this criterion.
- [ ] On replacement scheduling, an unchanged completed task is omitted and
  treated as a satisfied dependency; a changed task body is scheduled again; a
  removed completed task remains historical and creates no phantom task.
- [ ] For a legacy run without task-completion records, only tasks in waves
  strictly before `current_wave_index` may be inferred complete; every task in
  the current/unknown wave remains unfinished.
- [ ] The recomputed schedule contains only unfinished tasks, preserves valid
  dependency order, and cannot be accepted when a completed-task hash or task
  graph is malformed.

### AC4 — Artifact revision re-enters every gate

- [ ] After parking/invalidation, work-loop sets spec `Status: Draft` and plan
  `Status: Drafting` before `new-spec` revises either artifact; crash recovery
  completes any missing safe step in that order.
- [ ] Every changed exact revision reruns shaping spec review, adversarial
  complete-pair review, human spec approval, human plan approval,
  `approve-plan`, remaining-work `schedule`, and `plan-locked` before CODE work
  resumes.
- [ ] Shaping `Clean` from the prior baseline, nonmaterial classification, or a
  meaning-preserving correction never bypasses the post-seal sequence.
- [ ] The new baseline hashes the revised approved artifacts; stale prior hashes
  and schedules cannot satisfy any CODE transition guard.
- [ ] A build-time contract question is recorded without editing either pinned
  artifact. It closes in place only when a cited referent proves both artifacts
  still hold; otherwise it blocks and routes to the AC1 replacement event,
  including when the plan was already edited before the question was surfaced.

### AC5 — Every crash window fails closed and resumes deterministically

- [ ] Tests crash immediately before/after engine park, cohort invalidation,
  artifact status writes, each review gate, each human approval transition,
  baseline approval, schedule, and plan lock.
- [ ] A crash after engine park but before cohort invalidation resumes by
  idempotently applying the pending invalidation; no implementation dispatch is
  possible in the interim.
- [ ] Until cohort state records invalidation for the matching parked
  transition, run ID, and replacement identity, every drafting/review/approval
  progress transition refuses without overwriting the pending park evidence.
- [ ] A crash after cohort invalidation resumes drafting without reset; a crash
  during later approval/reseal follows the existing guarded resumption rules.
- [ ] Malformed, missing, symlinked, replaced, oversized, wrong-run, or
  unsupported state/artifact input refuses with a stable diagnostic and no
  partial write.

### AC6 — Work-loop records one recovery and disposition path

- [ ] Work-loop PLAN/REVIEW/DECIDE/resumption guidance distinguishes ordinary
  pause, implementation `findings-remain`, and sealed-baseline replacement and
  contains the exact mutation/review/approval order.
- [ ] `docs/architecture/loop-infrastructure.md`, state-schema reference, CLI
  help/status, and construction tests describe the same engine/cohort ownership,
  event, history, task completion, and crash recovery.
- [ ] RFC-0096's ordinary normalized `Paused` status remains unchanged; the
  accepted RFC-0099 Errata pointer explains why replacement is drafting, not
  pause.
- [ ] At PLAN, light and full modes open exactly
  `.context/work-loop/<run-id>/resolve-vs-surface.md`; the bounded ignored file
  records finding identity, `resolved-with-referent` or
  `surfaced-with-reason`, and closure status without raw finding prose.
- [ ] The loop derives the record path only from a validated run ID, confines
  it to the repository's `.context/work-loop/` root, accepts only a bounded
  regular UTF-8 file with stable identity, and updates it atomically without
  following symlinks.
- [ ] DECIDE and the done checklist refuse a missing or open disposition
  record. Neither the plan template nor a pinned artifact contains the record,
  and losing it requires reconstruction from authoritative review artifacts or
  a fresh review rather than a fabricated clean state.
- [ ] Before DECIDE or done, `check` reconciles every disposition row with the
  current validated review/adjudication finding identities or fingerprints and
  refuses missing, open, unmatched, extra, or changed rows; only authoritative
  reconstruction or a fresh review may establish a replacement expected set.

### AC7 — State and file boundaries remain fail-closed

- [ ] All state, artifact, and run-record reads retain repository confinement,
  regular-file, symlink/identity-change, byte-limit, run-ID, and atomic-write
  protections.
- [ ] The new cross-writer recovery adds no engine/cohort shared writable file,
  lock-order inversion, shell interpolation, network path, credential access,
  or direct reviewer mutation; the run-scoped disposition file carries no
  engine/cohort authority.
- [ ] Concurrency tests prove no lost update when replacement races status,
  schedule, task completion, or an illegal CODE transition.

### AC8 — Compatibility, releases, and projections are complete

- [ ] Existing runs without new optional fields remain readable and receive the
  conservative legacy completion rule; no destructive state migration is
  required.
- [ ] Core skill/script tests, manual lifecycle evidence, lint/type/test gates,
  security and quality review, pack evals, version parity, changelog/highlights,
  catalogue verification, and self-host/build projections pass.
- [ ] The existing Core work-loop delivery guide covers amendment parking,
  baseline replacement, crash/resume recovery, and the direct-light boundary;
  the capability ships no separate guide family.
- [ ] No generated projection is edited directly and the current architecture
  is updated only when implementation matches it.

## Assumptions

- Technical: current engine transitions have no return from CODE states to
  spec-plan drafting, while cohort approval hashes and schedules remain pinned
  (source: `loop-engine.py` transition tables and `loop-cohort.py`).
- Technical: engine and cohort are intentionally separate state writers; a safe
  replacement sequence parks the engine first and makes cohort invalidation
  idempotently resumable (source: `docs/architecture/loop-infrastructure.md`).
- Technical: the current scheduler has no task-completion ledger, so preserving
  completed work requires additive task evidence rather than guessing from the
  current wave (source: `loop-cohort.py:parse_plan`, state asset).
- Process: both human approvals, shaping review, adversarial spec-plan review,
  baseline seal, schedule, and plan lock are mandatory after every post-seal
  edit (source: RFC-0099; user confirmation 2026-08-27).
- Product: direct-light has no durable baseline and remains unchanged (source:
  RFC-0099, RFC-0094).

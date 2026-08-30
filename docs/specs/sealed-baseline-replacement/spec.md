# Spec: Sealed-baseline replacement

- **Status:** Approved
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0099; RFC-0096; RFC-0094; ADR-0099; ADR-0061; ADR-0074
- **Brief:** none
- **Discovery:** `docs/product/intents/cut-before-adding-solution-ladder.md`
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

> **Amended 2026-08-30 (Owner: eugenelim).** The original contract was written
> as though no post-seal route existed. `contract-amendment` ships one: a
> guarded `CODE-IMPLEMENTATION` → `SPEC-PLAN-DRAFTING` transition with bounded
> event context, idempotent cohort invalidation, an append-only amendment
> history, lossless preservation, and crash replay. Eight acceptance criteria
> became four; the removed ones described shipped behaviour, unread fields, or
> another feature's record. See [Removed from this contract](#removed-from-this-contract)
> and the RFC-0099 Errata entry of the same date.

## Objective

Two gaps remain in the post-seal edit route. An already-drifted pinned artifact
has no owner-authorized escape: the plan-current guard refuses, and the only
remedy is a destructive reset that discards completed-task evidence, attempts,
and review history. And re-drafting after an amendment re-enters adversarial
review and both human approvals but not shaping review, so a contract that was
wrong on its own terms can be resealed without the one review that reads it
cold.

Close both without widening the route. Drifted bytes are recorded and never
adopted: crossing the guard requires explicit owner confirmation bound to the
run ID and to the sealed and observed spec and plan hashes, and the complete
reapproval sequence still runs before implementation resumes. Direct-light work
remains outside the durable baseline lifecycle.

## Boundaries

### Always do

- Preserve every invariant the shipped route already holds: engine parks before
  cohort mutation, `loop-engine` remains the sole engine-state writer,
  invalidation stays idempotent for one amendment identity, and history,
  attempts, review counts, and completed-task evidence survive.
- Record the observed hashes of drifted artifacts as audit evidence only.
- Re-run the complete review and approval sequence for every changed exact
  revision, shaping review included.

### Ask first

- Add or rename an FSM event or state, a cohort mutation verb, or a persistent
  field beyond the owner-confirmation evidence this contract names.
- Change retry limits, review fingerprint semantics, task identity grammar, or
  human approval requirements.
- Perform a destructive engine or cohort reset instead of the guarded route.

### Never do

- Adopt an observed hash as a new pin, or let owner confirmation substitute for
  any part of the reapproval sequence.
- Add a drift state, an advisory edit allowlist, or a second post-seal route
  whose preconditions overlap `contract-amendment`.
- Resume implementation with stale hashes, reviewer-clean state, schedule, plan
  lock, or artifact statuses.
- Apply this state machine to direct-light work, or let a reviewer mutate it.

## Testing Strategy

- **TDD:** the guard crossing, its refusals, and owner-confirmation binding use
  fresh state directories and real CLI subprocesses. Regression tests pin the
  shipped invariants this change could break: transition legality, idempotent
  invalidation, history preservation, and crash replay.
- **Goal-based checks:** work-loop instructions, the delivery-contract
  lifecycle reference, state schema, architecture, and catalogue/build gates
  describe the same route.
- **Visual / manual QA:** one full code-mode run enters replacement from a
  drifted plan under owner confirmation, crashes before and after the cohort
  mutation, resumes through shaping review and both human gates, reseals, and
  schedules only remaining work.

## Acceptance Criteria

### AC1 — A drifted pinned artifact has one owner-authorized escape

- [ ] `contract-amendment` is the only event that may proceed when the
  plan-current guard fails.
- [ ] Crossing that guard requires explicit owner confirmation bound to the run
  ID and to the sealed and observed spec and plan hashes; a confirmation
  missing any binding is refused.
- [ ] The closed mismatch set identifies `spec`, `plan`, or both.
- [ ] No observed hash becomes a pin. The resealed baseline hashes only the
  revised artifacts the human approved.
- [ ] The amendment-history snapshot records the observed hashes alongside the
  sealed ones it already stores.
- [ ] Every refused crossing exits non-zero and leaves engine, cohort, and
  artifact bytes unchanged.

### AC2 — Re-drafting after an amendment enters shaping review

- [ ] Every changed exact revision runs shaping spec review before adversarial
  complete-pair review, human spec approval, human plan approval,
  `approve-plan`, remaining-work `schedule`, and `plan-locked`.
- [ ] A shaping `Clean` recorded against the prior baseline does not satisfy
  this gate, and neither does a meaning-preserving correction.
- [ ] `references/delivery-contract-lifecycle.md` names the shaping gate on the
  re-drafting path; it currently describes the sequence without it.

### AC3 — The shipped route keeps working

- [ ] Regression tests fail if `contract-amendment` stops being legal from
  `CODE-IMPLEMENTATION`, if invalidation stops being idempotent for one
  amendment identity, if the history snapshot loses a field, or if retry
  counters, attempt identity, review fingerprints, completed-task evidence, or
  worktree evidence stop surviving an amendment.
- [ ] A crash between the cohort mutation and the engine-state write still
  resumes through the existing replay path with no second snapshot.
- [ ] `findings-remain` continues to handle implementation findings that
  require no sealed artifact edit, and `gates-failed` and `findings-remain`
  remain the routes by which verification and review reach the one state
  `contract-amendment` is legal from.
- [ ] The engine delegates cohort mutation to `loop-cohort` and remains the sole
  engine-state writer; it does not itself write cohort or artifact files.

### AC4 — Documentation and release surfaces match

- [ ] Work-loop resumption guidance distinguishes ordinary pause,
  implementation `findings-remain`, and the drifted-artifact crossing, and
  states the owner-confirmation requirement.
- [ ] `docs/architecture/loop-infrastructure.md`, the state-schema reference,
  and CLI help describe the same evidence fields and refusals.
- [ ] RFC-0096's ordinary normalized `Paused` status remains unchanged.
- [ ] Existing runs without the new confirmation fields remain readable; no
  destructive state migration is required.
- [ ] Lint, type, test, security and quality review, pack evals, version
  parity, changelog, catalogue verification, and self-host projections pass. No
  generated projection is edited directly.

## Removed from this contract

Each entry states why the original criterion no longer earns its place. The
first four describe behaviour that already ships; the last two are additions
the evidence does not support.

- **Legality from `CODE-VERIFICATION` and `CODE-REVIEW`.** Both states reach
  `CODE-IMPLEMENTATION` in one existing transition — `gates-failed` and
  `findings-remain` — and both events are true when the contract is the defect.
  Two new FSM entries and their guards buy nothing.
- **Idempotent, audited, lossless cohort invalidation (original AC2).** Shipped:
  invalidation is keyed on the amendment identity, the snapshot records sealed
  hashes, schedule identity, wave position, and transition identity, and
  preservation is a `deepcopy` with a selective update. Only the observed
  hashes were missing; they moved to AC1.
- **Crash-window coverage and fail-closed state handling (original AC5, AC7).**
  Shipped: `.tmp` promotion, `events.pending` replay, a repo-global lock,
  confinement and symlink checks, and a replay guard that verifies the plan
  still matches the scheduled baseline before the cohort mutation reruns.
  Retained as regression guards in AC3.
- **The resolve-vs-surface disposition record (original AC6, four bullets).**
  Already a work-loop self-coverage obligation, opened at PLAN and closed at
  DECIDE with a done-checklist refusal. It is also a different feature: a
  self-coverage record is not part of the post-seal edit route, and specifying
  its file format here would split its ownership.
- **The materiality enum.** The original contract recorded materiality for
  audit while stating it "never grants a reduced exact-revision path." Nothing
  branches on it, and the shipped `reason_ref` is already a bounded pointer to
  why the amendment happened. A field that is written and never read is not a
  requirement.
- **Live per-task completion recording (original AC3, first two bullets).**
  `validate_completed_task_sections` re-derives task-section hashes from the
  plan text and refuses when a completed section changed, so caller-supplied
  evidence is verified rather than trusted. Inference is bounded to waves
  strictly before `current_wave_index`, so it under-counts: completed work is
  redone, never skipped. A ledger is an efficiency feature. **Open question for
  a future contract:** nobody has measured how much work an amendment redoes,
  and that measurement is what would justify building it.

## Assumptions

- Technical: `contract-amendment` already returns `CODE-IMPLEMENTATION` to
  `SPEC-PLAN-DRAFTING` under owner authority, with bounded event context,
  idempotent cohort invalidation, an append-only `amendment_history`, an
  `amendment_pending` replay marker, and `completed_task_ids` and
  `completed_task_section_hashes` as the completed-work ledger (source:
  `loop-engine.py` transition table and amendment branches; `loop-cohort.py`
  `apply_contract_amendment`; state-schema reference).
- Technical: engine and cohort are intentionally separate state writers, and
  the shipped sequence mutates the cohort first so a crash always leaves the
  cohort ahead, never behind (source:
  `docs/architecture/loop-infrastructure.md`; the replay branch in
  `loop-engine.py`).
- Technical: the plan-current guard has no crossing today, so a drifted pinned
  artifact's only remedy is a destructive reset (source: `loop-engine.py`
  guard registration; absence of any observed-hash or owner-confirmation
  field).
- Process: both human approvals, shaping review, adversarial spec-plan review,
  baseline seal, schedule, and plan lock are mandatory after every post-seal
  edit (source: RFC-0099; user confirmation 2026-08-27).
- Product: direct-light has no durable baseline and remains unchanged (source:
  RFC-0099, RFC-0094).

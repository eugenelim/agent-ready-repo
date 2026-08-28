# Plan: Sealed-baseline replacement

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved
- **Repository anchors:** `docs/architecture/loop-infrastructure.md`,
  `packs/core/.apm/skills/work-loop/scripts/{loop-engine,loop-cohort,_loop_guards}.py`,
  and `packs/core/tests/skills/work-loop/`; analogous
  `docs/specs/loop-approved-spec-state/` and
  `docs/specs/work-loop-in-process-guards/`. Deviation: current scheduling has
  no task-completion evidence, so this slice adds the minimum optional ledger
  needed to preserve completed work without guessing.

> **Plan contract:** this is the implementation strategy. It may change while
> Drafting or Executing; the approved baseline is immutable after sealing.

## Approach

Add task-completion evidence first so a replacement can distinguish known-done
from unfinished work. Add one engine park event and one cohort invalidation verb
without crossing state-writer ownership: the engine transitions to drafting
first, then the cohort mutation verifies that exact parked transition and
invalidates its baseline idempotently. Resume completes whichever safe step was
interrupted. Artifact revision then uses the existing review, approval,
approve-plan, schedule, and plan-lock path unchanged.

The same event accepts a plan that was edited before recovery was requested,
but only through an owner-confirmed drift branch bound to the sealed and
observed hashes. The mismatch is audit evidence, never a replacement pin. A
run-scoped ignored disposition file holds build discoveries and review
decisions so neither approved artifact becomes mutable process scratch.

New state fields are additive and default safely for existing version-1 state.
No reset, second state machine, shared writable file, generic transaction
framework, or direct reviewer mutation is added.

## Constraints

- RFC-0099, including all 2026-08-27 Errata, and RFC-0096's ordinary Paused
  semantics are normative.
- `loop-engine` remains the only `engine-state.json` writer;
  `loop-cohort` remains the only `state.json` writer.
- Existing locks, confined bounded reads, atomic writes, run identity, event
  recovery, retry caps, review history, and status parsers remain authoritative.
- Every post-seal byte change takes the full replacement path; no nonmaterial
  shortcut exists.
- `baseline-replacement-required` is the sole plan-current-guard exception and
  no observed hash becomes authoritative before AC4 completes.
- Direct-light, spec-plan-only mode, and current reviewer authority remain
  unchanged.
- Plan approval is blocked by the workspace prerequisites until both
  `core-guidance-artifact-routing` and `shaping-review-contracts` are Shipped;
  local scheduling therefore contains only local task dependencies.
- PLAN stubs prove representative executable contract seams only; crash,
  concurrency, and edge matrices complete during EXECUTE and are not a
  pre-EXECUTE implementation-completeness gate.
- No dependency, destructive migration, or direct generated-projection edit is
  permitted.

## Construction tests

**Integration tests:** real subprocess lifecycles enter replacement from all
three legal states, record tasks, invalidate, revise, review/approve/reseal, and
schedule only unfinished work. A crash matrix covers every engine/cohort/
artifact boundary and resumes without reset or stale dispatch.

**Manual verification:** record one material and one nonmaterial replacement
run, including engine/cohort JSON before and after, artifact statuses, preserved
diff/history, human gates, new hashes, remaining waves, and return to
CODE-IMPLEMENTATION. Use generic fixtures and redact repository/user details.

## Design (LLD)

### Data & schema

`state.json` gains optional completed-task records keyed by task ID with
canonical task-body hash, plus bounded replacement-history entries keyed by
run/transition identity. Existing version-1 readers ignore the additive fields;
new readers default them empty. Approval/schedule fields are cleared on
invalidation; attempts, reviews, worktree/commit evidence, completed tasks, and
history remain. Traces to AC2–AC3, AC8.

### Interfaces & contracts

- Engine event: `baseline-replacement-required --materiality
  material|nonmaterial`, legal only from the three code states; an optional
  owner-confirmed drift branch implements AC1's complete run, mismatch-set, and
  sealed/observed spec-and-plan hash binding. Traces to AC1 and T2.
- Cohort mutation: `invalidate-baseline --expect-run-id ...
  --expect-transition-sequence ...`, verified against the parked engine and
  idempotent for that identity. Traces to AC2, AC5.
- Task evidence: idempotent `task complete <task-id>` captures the canonical
  body hash after task construction tests. Existing scheduler subtracts only
  unchanged completed tasks. Traces to AC3.
- Run record: `.context/work-loop/<run-id>/resolve-vs-surface.md` holds bounded
  disposition rows for light and full modes and carries no execution authority;
  one narrow `resolve-vs-surface.py` helper owns open/update/close/check, while
  work-loop-local stdlib code provides validated run-derived paths, confined
  bounded regular-file reads, stable identity, no-follow behavior, and atomic
  replacement with behavioral parity to the repository file-safety contract.
  `check` reconciles rows with the current validated review/adjudication finding
  identities or fingerprints before DECIDE/done. Traces to AC4, AC6, and AC7.

### State & control flow

The controller follows the canonical ordered sequence in AC4. A build discovery
first enters the run disposition record; a referent may close it without an
artifact edit, otherwise AC1 parks the run before—or, under owner authority,
after—plan drift. Resume inspects `last_event` and replacement identity before
reissuing only idempotent operations. Traces to AC1–AC6.

### Failure, edge cases & resilience

Engine-first parking prevents new dispatch in the cross-writer crash window.
Cohort invalidation retains a prior-state audit before clearing execution
fields. Legacy runs infer only wholly completed prior waves; partial/unknown
current-wave work remains scheduled. Unsafe files, wrong identity, malformed
task graphs, and concurrent mutations refuse without partial state. Traces to
AC2, AC3, AC5, AC7.

### Quality attributes (NFRs)

Recovery is deterministic and fail-closed; mutations are idempotent per stable
identity; history is bounded and sanitized; no operation widens the existing
lock-hold or filesystem authority without a measured/tested budget update.
Traces to AC2, AC5, AC7.

## Tasks

### T1: Completed-task evidence makes remaining-work scheduling truthful

**Depends on:** none

**Touches:** `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py, packs/core/.apm/skills/work-loop/assets/state.json, packs/core/tests/skills/work-loop/test_loop_cohort.py`

**Tests:**
- `stub: true` — `packs/core/tests/skills/work-loop/test_baseline_replacement_contract.py` (`STUB: AC3`, `STUB: AC7`).
- TDD: task completion is run-bound, task-ID validated, body-hash pinned,
  idempotent, and refuses unsafe/missing/changed inputs (AC3, AC7).
- TDD: scheduling skips unchanged completed tasks, requeues changed tasks,
  treats skipped dependencies as satisfied, retains removed tasks as history,
  and conservatively handles legacy waves.

**Approach:**
- Extend existing plan parsing to extract canonical task bodies without a second
  parser or persisted plan copy.
- Add optional completion records and one narrow mutation verb; integrate their
  disposition into the current scheduler.

**Done when:** the scheduler emits only provably unfinished tasks across new and
legacy state fixtures.

### T2: The engine parks every post-seal edit before artifact mutation

**Depends on:** T1

**Touches:** `packs/core/.apm/skills/work-loop/scripts/loop-engine.py, packs/core/tests/skills/work-loop/test_loop_engine.py`

**Tests:**
- `stub: true` — `packs/core/tests/skills/work-loop/test_baseline_replacement_contract.py` (`STUB: AC1`).
- `no stub (implementation-discovered)` — AC5 crash cut points depend on the
  final pending-invalidation seam; discover that seam in `loop-engine.py`, keep
  the parked run/replacement identity stable, require no progress transition
  before matching cohort invalidation, and verify every before/after crash
  window with real CLI subprocesses.
- TDD: all legal/illegal source-state and mode combinations, materiality enum,
  run identity, current and already-drifted specs/plans, mismatch-set and
  owner/run/sealed/observed binding,
  byte-identical refusal, event context, and pending-event crash recovery cover
  AC1 and AC5.
- TDD: an implementation finding that needs no artifact edit takes existing
  `findings-remain` and leaves approval hashes, schedule, artifact statuses,
  and replacement history unchanged (AC1).
- TDD: every CODE transition remains blocked after park until the ordinary
  approval/plan-lock path is completed.

**Approach:**
- Add one code-mode event targeting existing `SPEC-PLAN-DRAFTING`; do not add a
  new FSM state.
- Exempt only this event from plan-current refusal and record bounded
  materiality, origin, sealed/observed spec and plan hashes, mismatch set, and
  owner-confirmed posture.
- Refuse every later progress transition until cohort state records invalidation
  for the pending parked transition/run/replacement identity; do not let a
  later event overwrite the recovery signal.

**Done when:** each legal CODE state parks atomically and no other state/mode can
invoke the event.

### T3: Cohort invalidation clears execution authority and preserves history

**Depends on:** T1, T2

**Touches:** `packs/core/.apm/skills/work-loop/scripts/{loop-cohort,_loop_guards}.py, packs/core/.apm/skills/work-loop/assets/state.json, packs/core/tests/skills/work-loop/{test_loop_cohort,test_loop_concurrency}.py`

**Tests:**
- `stub: true` — `packs/core/tests/skills/work-loop/test_baseline_replacement_contract.py` (`STUB: AC2`, `STUB: AC7`).
- `no stub (implementation-discovered)` — AC5 atomic-write crash injection uses
  the existing cohort writer seam discovered during T3; preserve old-or-fully-
  invalidated state, resume the matching pending replacement idempotently, and
  verify with real subprocess state directories.
- TDD: exact parked-transition verification, idempotent replay, mismatch
  refusal, field-level clear/preserve assertions, sanitized bounded history,
  status output, and concurrent mutation tests cover AC2 and AC7.
- TDD: crashes before/after the atomic cohort write preserve either old or fully
  invalidated state and resume deterministically (AC5).

**Approach:**
- Verify the engine's run/state/last-event/sequence through a confined bounded
  read, then mutate only cohort-owned fields under its existing lock.
- Reuse the atomic writer and retain all history fields not expressly invalidated.

**Done when:** a paired invalidation is lossless and replayable, while every
unpaired attempt is a no-write refusal.

### T4: Work-loop drives revision and full reapproval through one recovery path

**Depends on:** T2, T3

**Touches:** `packs/core/.apm/skills/work-loop/SKILL.md, packs/core/.apm/skills/work-loop/scripts/resolve-vs-surface.py, packs/core/.apm/skills/work-loop/references/{state-schema,supervisor-mode,self-coverage/protocol}.md, packs/core/seeds/docs/CONVENTIONS.md, packs/core/tests/skills/work-loop/**`

**Tests:**
- `stub: true` — `packs/core/tests/skills/work-loop/test_baseline_replacement_contract.py` (`STUB: AC6`, `STUB: AC7`).
- TDD/integration: a real code-mode task records completion; current and
  already-drifted plans enter AC1; build discoveries resolve or block; every
  crash window reissues only safe idempotent steps (AC3–AC6).
- Goal-based: content checks pin AC4 by reference, the exact ignored
  disposition path and fields, its absence from the plan template, and the
  DECIDE/done refusal (`no stub (goal-based)`).
- TDD: run-record tests cover validated run IDs, root confinement, bounded
  UTF-8 regular files, no-follow/stable identity, atomic replacement, and
  missing/open fail-closed behavior (AC6–AC7).
- TDD: `check` refuses missing, unmatched, extra, or changed disposition rows
  against the current validated finding set; only authoritative reconstruction
  or a fresh review may replace that expected set (AC6–AC7).
- Goal-based construction: every projected work-loop script remains stdlib-only
  and the run-record helper contains no `agentbundle` import (AC7).
- Goal-based: scaffold sync regenerates root `docs/CONVENTIONS.md` from the
  Core seed and the source/target check is clean.

**Approach:**
- Add one guarded post-seal branch and resumption table row; keep ordinary
  findings/pause/direct-light paths separate.
- Use `new-spec` for revision and existing review/approval machinery for the new
  baseline; store only process dispositions in the ignored run record.
- Give the ignored record one narrow helper with open/update/close/check verbs;
  use work-loop-local stdlib confinement, stable-identity, bounded-read, and
  atomic-replacement primitives, add no `agentbundle` runtime import, and add no
  general run-record framework.

**Done when:** material and nonmaterial manual runs both return to implementation
only through a fresh sealed baseline.

### T5: Architecture, security/reliability evidence, versions, and projections close the lifecycle slice

**Depends on:** T1, T2, T3, T4

**Touches:** `docs/architecture/loop-infrastructure.md, guides/core/how-to/plan-and-execute-non-trivial-work.md, packs/core/{pack.toml,.claude-plugin/plugin.json}, packs/core/.apm/skills/work-loop/evals/evals.json, docs/product/changelog.md, packs/core/tests/pack/**, packs/core/tests/skills/work-loop/test_baseline_replacement_contract.py`

**Tests:**
- `no stub (goal-based/manual QA)` — existing pack, architecture, catalogue,
  build, and recorded end-to-end verification artifacts.
- Goal-based: architecture/state/help parity, spec-status lint, Core evals,
  catalogue lint/verify, version parity, self-host/build projections, and full
  affected suites cover AC6–AC8.
- Goal-based/eval: one work-loop case distinguishes durable
  baseline-replacement from direct-light work and refuses any compatibility
  route that applies the state machine to the latter (AC6, AC8).
- Goal-based: the named Core work-loop guide covers amendment parking,
  replacement, crash/resume, and direct-light without adding a guide family
  (AC8).
- Security/quality: review state/file boundaries, concurrency, recovery,
  observability, testability, and history retention against the current diff.
- Visual/manual QA: retain the two end-to-end replacement records required by
  the cross-cutting section.

**Approach:**
- Update current architecture only after executable behavior is verified.
- Bump Core once for the combined public/state change and regenerate owned
  projections.

**Done when:** AC1–AC8 and all full-mode gates are green with no unresolved
recovery or security finding.

## Rollout

Ship task evidence, park event, invalidation, work-loop orchestration, and their
tests in one Core release so no partial feature is advertised. Existing state
files remain readable through absent-field defaults; a legacy replacement uses
the conservative completed-wave rule. Rollback returns to the prior pack only
before a replacement event is recorded; after use, the new version remains the
supported recovery reader because older work-loop lacks the event semantics.

## Risks

- Two state writers create a crash window; engine-first parking plus idempotent
  cohort invalidation is the fail-closed ordering.
- Task hashes can mistake edited work for complete; any body change requeues the
  task and needs human-approved resealing.
- Unbounded history can grow state or retain sensitive findings; store bounded
  structural identities only, never bodies.
- An ignored disposition record can be lost; DECIDE fails closed and requires
  reconstruction from authoritative review artifacts or a fresh review.
- New guard reads can change the lock budget or create deadlock; concurrency and
  call-graph budget tests must be updated from measured code.
- Treating additive state as universally rollback-safe would be false after the
  event is used; rollout names the supported-reader boundary explicitly.

## Changelog

- 2026-08-27: initial plan from accepted RFC-0099; chose one existing-state
  transition plus an idempotent cohort verb, and declined reset, a second state
  machine, a nonmaterial shortcut, and guessed completion.

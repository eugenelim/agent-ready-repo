# ADR-0061: Loop infrastructure Phase 1 — Option A (pure phase tracker)

- **Status:** Accepted
- **Date:** 2026-07-30
- **Decision-makers:** eugenelim

## Decision summary

- **Decision:** Phase 1 of the loop infrastructure uses Option A: `loop-engine.py` owns legal phase ordering and read-only guard enforcement; `loop-cohort.py` owns execution state and explicit mutations. All cohort mutations are invoked explicitly by the skill; the engine never writes cohort state.
- **Because:** Option B (workflow orchestrator with durable side-effect semantics) requires `review record` to support idempotency keys before its crash-recovery guarantees can be honoured. Option A delivers legal phase ordering, guard enforcement, crash-resumption, and multi-wave phase structure with a substantially smaller surface.
- **Applies to:** `packs/core/.apm/skills/work-loop/scripts/` (new `loop-engine.py`, `check-spec-status.py`; updated `loop-cohort.py`), `packs/core/.apm/skills/work-loop/assets/state.json`, `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/work-loop/references/state-schema.md`.
- **Tradeoff accepted:** `findings-remain` and `reviewers-clean` crash windows are non-idempotent in Phase 1; review-record crash recovery requires a skill-level sidecar for report pointers. In-place replanning after `plan-approved` is not supported — any post-approval plan change requires a full reset. The `spec-plan` drafting loop has no mechanical Phase-1 cap — unattended runs rely on the human G-plan gate or LLM judgment to terminate.
- **Revisit if:** `review record` gains idempotency keys (enabling Phase 2 / Option B); or per-phase budget credits are required (post-G-pr blocker repair consuming the global implementation budget); or a mechanical seal on the approved plan baseline is needed beyond the skill-discipline model; or unattended `spec-plan` runs require a bounded round or token cap.

## Context

Before this decision, the work-loop skill tracked phase state in prose and session context — hard to resume across crashes, opaque to inspection, and invisible to supervisors. The previous design mixed A-phase tracking with partial B side-effect wiring, creating ambiguity about where the boundary between engine and cohort lay.

The Phase-1 design splits the loop infrastructure into two scripts with a hard boundary:

| Concern | Owner |
|---|---|
| Legal phase ordering and read-only guard enforcement | `loop-engine.py` (FSM) |
| Execution state, counters, fingerprints, waves | `loop-cohort.py` |

`loop-engine` reads cohort state only through designated read-only verbs (`identity`, `plan check-current`, `schedule check-current`, `wave check`, `check --phase`). All cohort mutations are invoked explicitly by the skill.

**Modes in scope:** `code` and `spec-plan`. **Deferred:** `doc` mode (addressing-model conflict — RFC/ADR files share a directory, causing `feature` slug collisions); parallel-wave orchestration (`worktree`, `dispatch-decision`, `auto-parallel` verbs).

**Option B deferred because:** durable side-effect semantics require a `pending_transition` schema and idempotency keys on `review record`. Neither exists in Phase 1. Option B is the natural Phase-2 successor once those primitives land.

**Supersedes:** the mixed A/B design explored in PR #816.

## Alternatives rejected

**Option B now** — Requires `pending_transition` schema and `review record` idempotency keys. The additional surface adds risk without solving the immediate ordering and resumption gap.

**Shared `iteration_count`** — A shared counter collapses forward progress through scheduled waves and repair cycles onto the same budget. A five-wave plan with a default cap of five would exhaust the budget before reaching code review. Separate counters (`review_round_count`, `review_retry_count`, `implementation_retry_count`) correctly model distinct convergence concerns.

**Retry cap at `wave-complete`** — An off-by-one: the nth repair increments the counter and the guard then refuses before verification, so only n−1 repaired attempts can be verified. Guarding at `gates-failed` (before repair begins) means a refused nth back-edge means n−1 complete repair cycles have been attempted.

## Errata

**2026-08-31 Erratum — trigger fired, decision retained.** `loop-cohort review
record` gained an optional `--operation-id`, so the *Revisit if* trigger above
fired on its first clause. The Phase-1 decision is retained. Option B needs both
prerequisites and only one now exists: a `pending_transition` schema is still
absent, so durable side-effect semantics remain out of reach and Option A is
still the shape the loop runs.

Two statements above are narrowed rather than reversed, and a reader who lands
mid-file should not take either as current:

- *"`findings-remain` and `reviewers-clean` crash windows are non-idempotent in
  Phase 1"* — they are decidable **when a matching operation id is supplied**: a
  repeat carrying the recorded id and the same payload is a completed write, and
  a different payload under that id is refused. Without an operation id the
  windows are non-idempotent exactly as recorded, and the human-authorization
  obligation on a clean-round replay is unchanged.
- *"The `spec-plan` drafting loop has no mechanical Phase-1 cap"* — unchanged for
  `spec-plan`, but the **review** retry cap is now mechanical at the recording
  verb. It previously held only because the shipped instructions chained the
  recording to a capped transition with `&&`; splitting those statements showed
  the cap was carried by shell syntax rather than by code, so `review record`
  now refuses a findings round at `max_review_retries` itself.

Recorded by `docs/specs/review-record-idempotency/`, core 2.17.4. Whether the
remaining prerequisite is worth pursuing is a separate decision this erratum does
not take. The body above is left as written; this ADR is Accepted → Frozen
(`docs/CONVENTIONS.md`). Approver: eugenelim.

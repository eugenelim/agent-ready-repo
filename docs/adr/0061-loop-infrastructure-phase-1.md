# ADR-0061: Loop infrastructure Phase 1 — Option A (pure phase tracker)

- **Status:** Accepted
- **Date:** 2026-07-30
- **Areas:** orchestration, work-loop
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** ADR-0125 D3, D4
- **Related:** none

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

## Decision

Phase 1 of the loop infrastructure uses Option A, the pure phase tracker.

- **D1:** `loop-engine.py` owns legal phase ordering and read-only guard enforcement.
- **D2:** `loop-cohort.py` owns execution state, counters, fingerprints, and waves.
- **D3:** The engine never writes cohort state, and reads it only through the designated read-only verbs (`identity`, `plan check-current`, `schedule check-current`, `wave check`, `check --phase`).
- **D4:** Every cohort mutation is invoked explicitly by the skill.
- **D5:** Phase 1 covers `code` and `spec-plan` modes only; `doc` mode and parallel-wave orchestration are deferred.
- **D6:** Convergence is tracked by separate counters (`review_round_count`, `review_retry_count`, `implementation_retry_count`), never one shared `iteration_count`.
- **D7:** The retry cap is guarded at `gates-failed`, before repair begins, rather than at `wave-complete`.
- **D8:** Option B's durable side-effect semantics stay deferred until both a `pending_transition` schema and `review record` idempotency keys exist.

## Consequences

**Revisit if:** the remaining Option B prerequisite lands — a `pending_transition` schema alongside the now-available `review record --operation-id` — making durable side-effect semantics reachable (D8); or unattended `spec-plan` runs require a bounded round or token cap (D5).

## Alternatives considered

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

Recorded by `docs/specs/review-record-idempotency/`, core 2.18.2. Whether the
remaining prerequisite is worth pursuing is a separate decision this erratum does
not take. The body above is left as written; this ADR is Accepted → Frozen
(`docs/CONVENTIONS.md`). Approver: eugenelim.

**2026-09-22 Erratum — D3's channel, and D4's invoker, no longer describe the
code.** The decision is unchanged and this erratum takes none. It records that
two statements have drifted from what ships, so a reader who lands mid-file does
not take either as current.

- *"The engine never writes cohort state"* — the `contract-amendment` transition
  loads `loop-cohort.py` in-process and calls `apply_contract_amendment`, which
  takes the cohort lock and writes `state.json`. This is the only event that does
  so; the other fourteen invoke no cohort mutation from the engine.
- *"reads it only through the designated read-only verbs (`identity`, `plan
  check-current`, `schedule check-current`, `wave check`, `check --phase`)"* — the
  guard layer reads `state.json` directly through `_loop_guards.read_state`,
  having previously shelled out to `loop-cohort.py`. Those verbs remain the CLI
  surface; they are no longer the engine's read path.
- *"D4: Every cohort mutation is invoked explicitly by the skill"* — inexact on
  the same path. The skill invokes the transition, and the engine performs the
  amendment mutation as part of it, so that one mutation is a transition effect
  rather than an explicit skill call. D4 holds for every other cohort mutation.

The ownership split in D1 and D2 is unaffected: `loop-cohort.py` remains the
writer of record for cohort state, and the engine reaches it through that
module rather than around it.

Whether to re-align the code to D3 and D4 or to supersede them is a decision this
erratum does not take, and an erratum could not carry it. Current behaviour is
described in `docs/architecture/loop-infrastructure.md` § 3, § 4 and § 6. The body
above is left as written. Approver: eugenelim.

**2026-09-24 Erratum — a passing wave exit records that it passed, not why.**
The decision is unchanged and this erratum takes none. It records one
consequence of D1 and D2 that the *Tradeoff accepted* list above does not state.

D1 and D2 make guard enforcement read-only: `loop-cohort.py` is the only writer
of cohort state, so a guard row that *passes* cannot record that it was the row
which did. `check --phase wave-exit`, which postdates this ADR, has two rows
held open on purpose, so that a run already in flight when dispatch receipts
shipped still reaches its wave boundary: one passes cohort state whose
`schema_version` it does not support, the other passes cohort state carrying no
receipts container. Between them they emit at most a line on stdout, and no
durable record says which row decided the pass.

The transition log does not soften that. The `wave-complete` transition this
guard gates appends a line to `.loop-run/events.jsonl`, but ADR-0064 D1 records
that file as append-only and *ephemeral*, `loop-engine reset` removes it, and
the owned-state tables in `docs/architecture/telemetry.md` and
`docs/architecture/loop-infrastructure.md` label it the same way. It is
therefore not a durable record that the exit occurred, and nothing records the
verdict: no surface says whether accounting was enforced, exempted, or
satisfied.

Two neighbouring facts do not follow from the above and are stated so they are
not inferred from it. A wave whose tasks all carry a `decline` is fully
accounted for rather than exempted — a decline is a record, and
`packs/core/.apm/skills/work-loop/references/state-schema.md`
states that both kinds count. And
`loop-cohort status`'s `dispatch_receipts_enforced` reports whether the
container is present when the call is made, so it is the exemption's current
status rather than a trace of any past exit, and it refuses outright on an
unsupported `schema_version`.

Option B remains out of reach on the prerequisite the 2026-08-31 erratum named:
a `pending_transition` schema is still absent. No architecture section records
this consequence yet: `docs/architecture/loop-infrastructure.md` covers the
wave-exit verdict only where it is not serialised against the wave pointer,
which is a different question. The body above is left as written.
Approver: eugenelim.

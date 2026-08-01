# Spec: loop-infra-crash-window-tests

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0061, [loop-infrastructure-phase-1 spec](../loop-infrastructure-phase-1/spec.md)
- **Brief:** none
- **Contract:** none
- **Shape:** mixed
- **Closes deferred:** AC6 of `docs/specs/loop-infrastructure-phase-1/spec.md`

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Add deterministic end-to-end tests that verify Phase 1 session resumption and
crash-window behavior using real CLI subprocess invocations. Close the deferred
AC6 in the loop-infrastructure-phase-1 spec.

Also add one targeted SKILL.md prose enhancement (in the `reviewers-clean`
session-resumption table row) to make the double-increment and fingerprint audit
history consequences explicit. The `findings-remain` row already contains the
required phrases ("stale fingerprint baseline", "under-count", "do NOT auto-reissue")
from the Phase 1 ship; AC8c pins those as a regression guard without modification.
This is a documentation-only change requiring `FORCE=1 make build-self` for
projection parity.

Phase 2 orchestration is out of scope. This spec stays strictly within the
accepted Phase 1 Option-A architecture.

## Assumptions

- `loop-engine status --json` returns `run_id`, `last_event`, `last_event_context`,
  and `transition_sequence` as top-level fields (verified by reading existing engine
  output schema in `loop-engine.py`).
- `loop-cohort wave advance` and `loop-cohort record-attempt` are the only cohort
  mutations in the documented session-resumption protocol (verified by reading
  SKILL.md session-resumption table rows).
- All test invariants are provable via state-file comparison without relying on
  process timing, network, or OS scheduling.
- The `reviewers-clean` row in SKILL.md is the only session-resumption table row
  that lacks consequence language for double-increment; the `findings-remain` row
  already has the required phrases (verified by reading SKILL.md lines 499–501).

## Boundaries

### Always do
- Exercise the shipped CLI boundary (`loop-engine` and `loop-cohort` subprocesses).
- Use temporary directories; create fresh processes to represent session loss.
- Simulate interruption by stopping between documented commands.
- Compare state before and after every refusal or recovery.
- Assert both crash windows for each scenario (before and after the idempotent call).
- Add new test functions to the `tests` list in `main()` of `test-loop-engine.py`.

### Ask first
- Any production change to `loop-engine.py` or `loop-cohort.py`.
- Adding new persisted state fields.
- Changing the normative transition matrix.
- Any substantive SKILL.md change beyond the one prose enhancement specified in
  the Objective (double-increment and fingerprint audit history wording added to
  the `reviewers-clean` session-resumption row only).

### Never do
- Import internal Python functions instead of exercising the CLI (AC7 requirement).
- Add `pending_transition`, a side-effect journal, or automatic effect replay.
- Add idempotency retrofits for `review record`.
- Expand into Phase 2 concerns.
- Use sleeps, timing races, or process killing.

## Acceptance criteria

- [ ] **AC1 — `wave-passed` window A:** a fresh process that finds `last_event:
  wave-passed` and `last_event_context: {completed_wave_index: N}` in engine state
  with cohort `current_wave_index == N` safely reissues `wave advance --from-index N`
  and advances to `N+1` exactly once.
- [ ] **AC2 — `wave-passed` window B:** a fresh process that finds the same engine
  state but cohort `current_wave_index == N+1` (advance already completed) safely
  reissues `wave advance --from-index N` as an idempotent no-op with no state
  mutation.
- [ ] **AC3 — `wave-passed` refusals:** malformed or mismatched recovery attempts
  (wrong `--from-index`, wrong `--expect-run-id` [run_id prefix mismatch]) exit
  non-zero and do not mutate either state file; the engine and cohort run_ids remain
  paired after every refused recovery attempt.
- [ ] **AC4 — `gates-failed` window A:** a fresh process that finds `last_event:
  gates-failed` with no `last_record_attempt_cycle_id` reconstructs the stable
  `cycle-id` (`run_id:transition_sequence` from engine state) and safely issues
  `record-attempt`, incrementing `implementation_retry_count` exactly once.
- [ ] **AC5 — `gates-failed` window B:** a fresh process that finds the same engine
  state but `last_record_attempt_cycle_id == run_id:transition_sequence` (call
  already completed) safely reissues `record-attempt` as an idempotent no-op with
  no counter increment.
- [ ] **AC6 — retry boundaries:** with `max_implementation_retries == 5`, the fifth
  repair cycle (`gates-failed` transition + `record-attempt`) is permitted;
  `implementation_retry_count` reaches 5; the sixth `gates-failed` transition is
  refused by the guard before any mutation; `implementation_retry_count` stays at 5.
- [ ] **AC7 — no-chat-history resumption protocol:** a test exercises the full
  documented read sequence — `loop-engine status --json` → `loop-cohort identity
  --expect-run-id` → `loop-cohort status --json` — via subprocess only (no direct
  `state.json` reads; no internal Python function imports); reads `last_event` and
  `last_event_context` from the command output and demonstrates correct recovery
  routing for `wave-passed` and `gates-failed`.
- [ ] **AC8 — `findings-remain` limitation:** a test proves (a) the committed phase
  is recoverable from persisted engine state via `loop-engine status --json`; (b)
  the workflow does not auto-replay `review record --fingerprint` — cohort state
  is unchanged when the replay is deliberately skipped; (c) the SKILL.md session-
  resumption table row for `findings-remain` contains the phrases "stale fingerprint
  baseline" and "under-count" and "do NOT auto-reissue".
- [ ] **AC9 — `reviewers-clean` limitation:** tests cover both `--report` and
  `--all-skipped` CLI forms (verified by `--help` output); prove that cohort state
  is unchanged when `review record` is deliberately skipped after `reviewers-clean`;
  the SKILL.md session-resumption table row for `reviewers-clean` contains the
  phrase "non-idempotent" and mentions "double-increment" of `review_round_count`
  and "fingerprint audit history" (or equivalent consequence phrases); requires
  "authorized" before replay.
- [ ] **AC10 — deterministic construction:** all new tests use only temporary
  directories and subprocess invocations; no sleeps; no timing races; no network
  access; cross-platform (macOS and Linux); every refusal is validated by comparing
  state before and after the refused call; every new `test_*` function appears in
  the `tests` list in `main()`.
- [ ] **AC11 — closure:** `docs/specs/loop-infrastructure-phase-1/spec.md` AC6 is
  checked and its `(deferred: loop-infra-crash-window-tests)` marker is removed;
  the `{slug = "loop-infra-crash-window-tests", ...}` entry is removed from
  `[backlog].open` in `workspace.toml`; `python3
  packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py` reports clean;
  projection parity passes (`FORCE=1 make build-self` no drift).

## Testing strategy

All acceptance criteria verified through subprocess-level CLI tests and goal-based
content assertions. No LLM judge required; all behaviors are mechanically
deterministic.

**AC-to-verification-mode mapping:**

| ACs | Verification mode |
|-----|------------------|
| AC1–AC7 | TDD — subprocess invocation; state comparison before/after |
| AC8–AC9 | TDD (state comparison) + goal-based content assertion (SKILL.md prose, --help output) |
| AC10 | Verified by test structure (no sleep/net calls, tmpdir usage, tests list membership) |
| AC11 | Goal-based (lint-spec-status.py clean; grep for deferred marker absent; build-check green) |

New tests are added to
`packs/core/.apm/skills/work-loop/scripts/test-loop-engine.py` in a dedicated
section `## Crash-window tests (loop-infra-crash-window-tests AC6 closure)`.
No separate test file is introduced.

Phase 2 orchestration is explicitly out of scope.

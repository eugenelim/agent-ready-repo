# Loop Infrastructure

> **Target-state design — not current-state.** This document is in
> `docs/architecture/` as the ratification artifact. It describes proposed,
> not yet landed, infrastructure. The implementation moves from design
> to current-state on PR #816 merge; until then, treat this as the
> authoritative spec for what to build, not a description of what is built.

**Status:** Proposed  
**Implementation:** Not yet landed — design ratification is the precondition for
implementation (PR #816).  
**Supersedes:** the earlier draft in this PR's history (which mixed A-phase
tracking with partial B side-effect wiring); this ratified version ships in
PR #816.  
**Phase 1 scope:** `code` and `spec-plan` modes only. `doc` mode is deferred
pending an addressing-model decision — see
[Deferred: doc mode](#deferred-doc-mode).

## Context and Goals

The work-loop skill executes a non-trivial feature spec in phases (drafting →
review → human gate → implementation waves → verification → code review → done).
Before this design, the skill tracked phase state in prose and session context —
hard to resume across crashes, opaque to inspection (no persisted current-state
record), and invisible to supervisors. Note: Phase 1 provides inspectable
*current* state (`state`, `last_event`, `transition_sequence`), not a transition
history — an append-only event log is a Phase-2 addition.

**FSM** = Finite State Machine throughout this document.

**This design splits that into two scripts with a hard boundary:**

| Goal | Delivered by |
|---|---|
| Legal phase ordering and guard enforcement | `loop-engine.py` (phase FSM) |
| Task execution state, counters, fingerprints | `loop-cohort.py` (execution state owner) |
| Crash-safe session resumption without chat history | persisted `engine-state.json` (`last_event`, `last_event_context`) — idempotent for `wave-passed` and `gates-failed` windows; `findings-remain` window is non-idempotent (see Session Resumption step 7); and the `reviewers-clean` window (audit-only; see step 11) |
| Bounded convergence of CODE-REVIEW and `gates-failed` repair cycles (retry caps, stasis detection) | `loop-cohort` counters + guards — the spec/plan drafting loop has no mechanical Phase-1 cap; it terminates on the human G-plan gate or LLM judgment. An advisory token or round counter for unattended spec-plan runs is a Phase-2 concern |

**Phase 1 guarantees:** legal phase ordering across all transitions; plan-hash
enforcement on post-approval `CODE-*` transitions (except `done`); matching
`run_id` identity after successful initialization, with mismatches blocking
further transitions (initialization and reset have recoverable one-file windows);
and idempotent recovery for the `wave-passed` and `gates-failed` crash windows.
Phase state can be resumed without chat history; work-artifact resumption
requires persisted notes or a sidecar. Review-record crash windows
(`findings-remain`, `reviewers-clean`) are documented Phase-1 limitations.

The work-loop skill's phase sequencing and task execution are designed to be
implemented by two scripts. This document defines the boundary between them so
future maintainers have a single reference rather than reconstructing it from
code.

**Design choice — Phase 1:** Option A (pure phase tracker). The engine validates
legal phase ordering and runs read-only guards. All loop-cohort mutations are
invoked explicitly by the skill. Option B (workflow orchestrator with durable
side-effect semantics) is deferred until `review record` supports idempotency
keys — see [Future Phase: Workflow Orchestrator](#future-phase-workflow-orchestrator-b).

---

## Scripts

### loop-cohort.py

**Role:** Task execution state owner.

**Source:** `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`  
**Projects to:** `.claude/skills/work-loop/scripts/loop-cohort.py`

**What it owns:**

- `state.json` — the run-local state file written into each spec directory
  (intentionally survives chat-session boundaries). `references/state-schema.md`
  reflects the pre-Phase-1 model and is superseded; it will be rewritten in
  PR #816. The authoritative field list is the
  [State Ownership table](#state-ownership); the sub-bullets below are
  supplementary descriptions of each field's semantics.

  - `review_round_count` — total CODE-REVIEW rounds; incremented by every
    `review record` call (both clean and findings). Audit only; not cap-guarded.
  - `review_retry_count` / `max_review_retries` — findings-only rounds;
    incremented by `review record --fingerprint` (not by `--report`). The
    `findings-remain` guard enforces this cap. Separates convergence retries from
    clean reviews and human-blocker round-trips. **Phase-1 default: 5** (written
    by `loop-cohort init` from `assets/state.json`; change the template to alter
    the default for all new runs).
  - `implementation_retry_count` / `max_implementation_retries` — counts
    `gates-failed` back-edge repair cycles; incremented by `record-attempt
    --phase implement`. Successful scheduled-wave executions do NOT consume
    this budget. The `gates-failed` guard enforces this cap. **Phase-1 default: 5**
    (same template as above).
  - `last_record_attempt_cycle_id` — the last `--cycle-id` applied by
    `record-attempt`. Enables `record-attempt` to be idempotent: a second call
    with the same cycle ID returns success without incrementing the counter.
  - `finding_fingerprints` — fingerprints from the most recent review round,
    rotated by `review record`. `review inspect` compares incoming fingerprints
    against this field for stasis detection.
  - `previous_finding_fingerprints` — fingerprints from the round before the
    most recent, retained for audit.
  - `approved_spec_hash` — sha256 of spec.md bytes (raw, not canonicalized) at
    the time `approve-plan` ran, binding the G-plan approval marker to a specific
    spec version. Spec.md is raw-hashed because it is checked only once inside a
    byte-frozen window (`approve-plan` through `plan-approved`); plan.md is
    canonical-hashed (`sha256(canonical(plan.md))`) because `schedule check-current`
    re-checks it at every CODE-* transition and must tolerate trailing-whitespace-only and line-ending-only edits.
    This is a **point-in-time marker**: after `plan-approved`, spec.md is expected to
    undergo permitted status mutations (`Approved → Implementing → Shipped`)
    that change its raw bytes, making `approved_spec_hash` stale. Skill writes
    `Status: Implementing` *after* the `plan-approved` engine transition (on
    entry to `CODE-IMPLEMENTATION`), not before `schedule` — spec.md is
    byte-frozen from `approve-plan` through the `plan-approved` guard. Skill
    writes `Status: Shipped` before the `reviewers-clean` transition (gate
    enforced by `check-spec-status.py`). The engine does
    not re-check `approved_spec_hash` during CODE-* transitions. Subsequent
    spec-body integrity (acceptance criteria, scope, requirements) is a skill
    obligation in Phase 1. Phase 2 may introduce `approved_spec_contract_hash`
    (canonical hash excluding mutable `Status:` metadata) to mechanically protect
    the spec body throughout the run.
  - `approved_plan_hash` — sha256 of canonical(plan.md) at the time `approve-plan`
    ran, binding the approval marker to a specific plan version.
  - `plan_hash` — sha256 of canonical(plan.md) at the time `schedule` ran. Canonical form: CRLF → LF, trailing whitespace stripped per line.
    `loop-cohort schedule check-current` verifies this matches the working copy
    at every CODE-* transition (plan immutability enforcement). `check --phase
    implement` at `wave-complete` enforces advisory bounds only (non-blocking
    in Phase 1).
  - `schedule_waves`, `current_wave_index` — persisted by `schedule` for
    cross-run wave resumption.

- Task DAG and wave scheduling — `schedule` reads plan.md, validates the DAG,
  computes topological waves, and persists `plan_hash`, `schedule_waves`,
  `current_wave_index: 0` to `state.json`. Exit non-zero on any DAG error or if
  the task set is empty (so an empty-wave failure surfaces at scheduling, not
  at the `plan-approved` guard two calls later).
- Finding fingerprints — `review record --fingerprint` (findings round):
  `previous_finding_fingerprints = finding_fingerprints`, `finding_fingerprints =
  [<supplied fingerprints>]`, `review_retry_count += 1`, `review_round_count += 1`.
  `review record --report` (clean round): exits non-zero if the report is not
  clean (i.e. `parse_findings()` returns ≥1 fingerprints, or the clean substring
  is absent from the file) — findings rounds must go through `--fingerprint`.
  On a clean report: `previous_finding_fingerprints = finding_fingerprints`,
  `finding_fingerprints = []`, `review_round_count += 1`, `review_retry_count`
  unchanged. Both forms rotate `finding_fingerprints` to `[]` or the new set, so
  a subsequent `review inspect` compares against the current round's baseline —
  not a stale pre-clean set. **Not idempotent** in Phase 1. **Implementation note
  (PR #816):** the existing `cmd_review_record` shares a single
  `state["iteration_count"] += 1` write across both branches; PR #816 must replace
  it with branch-specific counter updates:
  (a) `--report` branch: exit non-zero when `parse_findings()` returns ≥1 or the
  clean substring is absent; on success, increment `review_round_count` only
  (never `review_retry_count`);
  (b) `--fingerprint` branch: increment both `review_retry_count` and
  `review_round_count`; add `--expect-run-id` validation.
  Both branches must drop the shared `iteration_count` write.
- Attempt recording — `record-attempt --phase implement --cycle-id
  <run_id>:<transition_sequence>` increments `implementation_retry_count` and
  stores the cycle ID in `last_record_attempt_cycle_id`. Idempotent: a second
  call with the same `--cycle-id` returns success without incrementing.
  Called by the skill only after `gates-failed`; not called on successful
  scheduled-wave transitions. `--error-fingerprint <hex>` stores the fingerprint
  in a `last_error_fingerprint` field for future comparison; the
  `consecutive_same_error_count` increment is not defined in Phase 1 and the
  guard for that field is advisory.
- Iteration and budget gates — `check --phase {implement,review,gates-failed}`
  enforces the bounded counters for that phase or transition. Advisory fields
  are checked but do not block. Plan-phase approval is covered by
  `plan check-current --require-schedule` or `plan check-current`, not
  `check --phase`.

**Verb surface:**
```
loop-cohort init <spec-dir> --run-id <uuid>
loop-cohort identity <spec-dir> [--expect-run-id <uuid>] [--json]
loop-cohort check <spec-dir> --phase {implement,review,gates-failed}
loop-cohort approve-plan <spec-dir> --expect-run-id <uuid>
loop-cohort plan check-current <spec-dir> [--require-schedule]
loop-cohort schedule <spec-dir> --expect-run-id <uuid>
loop-cohort schedule check-current <spec-dir>
loop-cohort record-attempt <spec-dir> --phase implement --cycle-id <id> --expect-run-id <uuid> [--error-fingerprint <hex>]
loop-cohort wave check <spec-dir> --expect {more,last} [--wave-index <n>]
loop-cohort wave advance <spec-dir> --from-index <n> --expect-run-id <uuid>
loop-cohort review inspect <spec-dir> --report <path> [--json]
loop-cohort review record <spec-dir> (--report <path> | --fingerprint <hex>...) --expect-run-id <uuid>
loop-cohort status <spec-dir> [--json]
loop-cohort reset <spec-dir>
loop-cohort worktree preflight|add|record|list|merge|cleanup <spec-dir> [...]
loop-cohort dispatch-decision --branch <b> [--branch <b>...] [--category <c>...] [--base <ref>]   # no <spec-dir> — carried-over convention
loop-cohort auto-parallel <spec-dir> [--off]
```

**New verbs:**

- **`identity [--expect-run-id <uuid>]`** — read-only. Returns `run_id` and
  `schema_version` from `state.json`. Exits non-zero if: `state.json` is absent;
  `schema_version != 1` (the Phase-1 supported value); or, with `--expect-run-id`,
  the stored `run_id` does not match. `identity` is the sole validator of the
  *cohort* `schema_version` (`state.json`); the engine validates its own
  `engine-state.json` `schema_version` directly (see run_id verification). Used as the run_id
  verification preflight before every code/spec-plan transition (see Guards) and
  as the cohort-present check during the init preflight.

- **`--expect-run-id <uuid>`** (mutating verbs) — `approve-plan`, `schedule`,
  `record-attempt`, `wave advance`, and `review record` each require this flag.
  Each command reads `run_id` from `state.json` and exits non-zero if it does not
  match the supplied value. For `record-attempt`, the `run_id` prefix embedded in
  `--cycle-id <run_id>:<sequence>` must also match `--expect-run-id` and the stored
  `run_id`; a mismatch exits non-zero before any mutation. This makes the
  paired-state invariant apply to the entire workflow, not only to FSM transitions.

- **`plan check-current [--require-schedule]`** — read-only. Always verifies:
  `plan_review_status == "approved"`, `approved_spec_hash == sha256(spec.md)`,
  `approved_plan_hash == sha256(canonical(plan.md))`. With `--require-schedule`: also
  verifies `plan_hash == approved_plan_hash`, `schedule_waves` non-empty,
  `0 <= current_wave_index < len(schedule_waves)`. Without the flag: no schedule
  check (spec-plan mode has no implementation waves). Exit non-zero with a
  descriptive message on any failure. The engine selects the flag based on its
  persisted mode; loop-cohort never infers mode from cohort state.

- **`wave check --expect {more,last} [--wave-index <n>]`** — read-only. With
  `--expect more`: exits 0 iff `current_wave_index < len(schedule_waves) - 1`.
  With `--expect last`: exits 0 iff `current_wave_index ==
  len(schedule_waves) - 1`. With `--wave-index <n>`: additionally verifies
  `current_wave_index == n`; refuses if the supplied index does not match the
  stored index. Guard for `wave-passed` (with `--wave-index`) and `gates-clean`
  respectively.

- **`schedule check-current`** — read-only. Verifies `plan_hash ==
  sha256(canonical(plan.md))` (same canonicalization as `schedule`). Exit non-zero
  with a descriptive message if they differ. Called by the engine as a mandatory
  pre-guard for every transition from a `CODE-*` state (after run_id preflight,
  before the event-specific guard), **except `done`**. Makes plan immutability a
  run invariant across all active CODE-* transitions. `done` is exempted because
  the PR is already merged at that point.

- **`wave advance --from-index <n>`** — mutating; idempotent.
  - `current_wave_index == n` → set `n + 1`, exit 0.
  - `current_wave_index == n + 1` → already advanced, exit 0 (safe retry).
  - Any other value → refuse, exit non-zero.

- **`review inspect --report <path> [--json]`** — read-only. Parses the
  reviewer report and returns:
  ```json
  {
    "classification": "clean | findings | invalid",
    "fingerprints": ["<hex>", ...],
    "matches_previous_round": false
  }
  ```
  `review inspect` exits 0 and emits JSON for all report-content outcomes
  (absent, unreadable, empty, malformed, clean, or findings) — the stasis-routing
  table always reads the `classification` field from JSON output. Non-zero exit is
  reserved for operational errors (`<spec-dir>` unresolvable, `state.json` unreadable).

  Classification is derived from `parse_findings()` output together with report
  readability and the clean-substring check (`parse_findings()` / `FINDING_LINE_RE`
  in `loop-cohort.py`). A report carrying both the clean substring and parseable
  findings classifies as `findings` (findings take precedence):
  - `invalid`: report file absent or unreadable, OR (`parse_findings()` returns
    `[]` AND the report does not contain the clean substring). `matches_previous_round`
    is `false` (no meaningful comparison).
  - `clean`: `parse_findings()` returns `[]` AND the report contains the substring
    `Clean — ready to commit.` (em-dash `—`) anywhere in the text — identical to
    the substring check in `cmd_review_record`, not a full-line equality test.
    `matches_previous_round` is always `false` when the computed fingerprint set is empty.
  - `findings`: `len(parse_findings()) >= 1`. See the **findings-remain floor** below.

  `parse_findings()` is the single canonical extractor; `FINDING_LINE_RE` matching
  alone is not sufficient (the algorithm additionally requires a `:` and a digit in
  the citation). If the `adversarial-reviewer` output structure changes, the
  classification predicate and fingerprint format must be updated together.
  `matches_previous_round` is `true` iff `sorted(set(computed_fingerprints)) ==
  sorted(set(state.finding_fingerprints))`. Both sides are deduplicated before
  sorting, so duplicate report lines do not affect stasis behavior, serialized
  state is deterministic, and a reordered but otherwise identical finding list
  is still detected as stasis. The skill uses this as the canonical stasis check
  before routing to `reviewers-clean` or `findings-remain`.

- **`reset`** — deletes only `state.json`. Idempotent: tolerates already-absent.
  Paired with `loop-engine reset` (each owns only its own file). `loop-cohort
  init` refuses if `state.json` is already present (use `reset` to clear first,
  not `--force`).

- **Parallel-wave verbs** (`worktree preflight|add|record|list|merge|cleanup`,
  `dispatch-decision`, `auto-parallel`) are carried over from loop-cohort's
  existing implementation. **All three parallel-wave verb groups (`worktree`,
  `dispatch-decision`, `auto-parallel`) are disabled in Phase 1** — parallel
  waves have no FSM coupling and their sequencing is not specified here. These
  verbs must exit non-zero with a "disabled in Phase 1" message to prevent
  accidental invocation from touching `state.json` fields (`worktrees`,
  `auto_parallel`). A future spec will wire worktree sequencing against
  `wave-complete` and `wave advance`.

**Write contract:** all `loop-cohort` mutations write `state.json` via tempfile +
`os.replace` (atomic swap, mirrors `loop-engine`'s write contract). Torn writes
produce an absent or stale file, not partial JSON.

**Exit contract:** exit 0 on success; exit non-zero with a one-line reason on
stderr on failure.

---

### loop-engine.py

**Role:** Phase FSM validator (Option A — Phase 1).

The engine is designed to validate legal phase ordering, run read-only guards,
and record the current phase in `engine-state.json`. It does not invoke
loop-cohort mutations. The skill invokes all mutations explicitly.

**A guarantees** legal phase ordering and the mechanically checked preconditions
listed in the Guards table. It does not prove the truth of unguarded event
assertions or the completion of any post-transition operation the skill performs.

**Source:** `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`  
**Projects to:** `.claude/skills/work-loop/scripts/loop-engine.py`

**What it owns:**

- `engine-state.json` — the run-local phase record (intentionally survives
  chat-session boundaries). Schema:
  ```json
  {
    "schema_version": 1,
    "run_id": "<UUID generated at init>",
    "feature": "<slug>",
    "mode": "code | spec-plan",
    "state": "<phase name — see transition tables below>",
    "last_event": "<event name that entered this state, or null at init>",
    "last_event_context": null,
    "transition_sequence": 0,
    "last_transition_at": "<ISO-8601 UTC>"
  }
  ```
  - `last_event` — the event name that produced the current state. Enables
    a resumed session to distinguish the five inbound paths to
    `CODE-IMPLEMENTATION` (plan-approved, wave-passed, gates-failed,
    findings-remain, blocker-applied). Pure phase-tracker data; does not make
    A an orchestrator.
  - `last_event_context` — event-specific payload stored alongside `last_event`.
    Null for most events. For `wave-passed`: `{"completed_wave_index": <n>}`
    where `n` is the zero-based index of the wave that just passed (supplied by
    the skill via `--wave-index`). A resuming session uses this to reissue
    `wave advance --from-index <n>` safely regardless of which crash window it
    is in — before or after the advance completed.
  - `transition_sequence` — monotonically increasing counter, incremented on
    every successful write. External supervisors (INI-003) use it to detect
    stale callers. Concurrent transitions are outside Phase 1 scope; no
    compare-and-swap mechanism is specified. Do not use `transition_sequence`
    as a locking primitive.

- Phase FSM — per-mode transition tables (see below). Events not in the table
  for the current mode × state pair are refused with a non-zero exit.
- Transition execution — reads `engine-state.json`, verifies run_id pairing
  (via `loop-cohort identity`), validates the event, fires the guard if one
  exists, writes the new state atomically (tempfile + `os.replace`).

**Verb surface:**
```
loop-engine init <spec-dir> --mode {code|spec-plan} [--json]
loop-engine transition <spec-dir> <event> [--wave-index <n>]
loop-engine status <spec-dir> [--json]
loop-engine reset <spec-dir>
```

`--help` on every command is the primary documentation.

`init --json` outputs the generated `run_id` as a JSON field. The skill uses
this path to capture the `run_id` for passing to `loop-cohort init`.

`transition --wave-index <n>`:
- **Required** when `<event>` is `wave-passed`. Exit non-zero if omitted for that event.
- **Rejected** (exit non-zero) for all other events.
- The engine passes the same `n` to `loop-cohort wave check --expect more
  --wave-index <n>` as its guard.
- `n` and the new state (`CODE-IMPLEMENTATION`) are written to
  `engine-state.json` atomically in the same `os.replace` write.
- A failed guard does not write `n` to `last_event_context`; `engine-state.json`
  is unchanged on guard failure.

`status --json` exposes all `engine-state.json` fields plus a
`pending_human_wait` boolean. The states where this is `true` are listed in
the [Human-Wait States and Session Boundaries](#human-wait-states-and-session-boundaries)
section; it is `false` in all other states. `status` refuses with a descriptive
error if `engine-state.json` carries `schema_version != 1` — the same forward
guard applied by `transition`.

`reset` — deletes only `engine-state.json`. Idempotent: tolerates
already-absent.

**Exit contract:** exit 0 on success; exit non-zero with a one-line descriptive
message on failure.

**Trust boundary:** `<spec-dir>` is trusted local input — both scripts run in
the user's own workspace, not in a sandboxed environment. `plan.md` and `spec.md`
are parsed defensively: `schedule` exits non-zero on a malformed DAG; hashing
operations work on raw bytes without executing content. All `loop-engine` and
`loop-cohort` verbs that accept `<spec-dir>` resolve it to an absolute path at
startup and reject `..` components (`dispatch-decision` does not take `<spec-dir>`
and is excluded from this claim).

**Single-writer contract:** only one caller may issue `transition` calls for a
given `<spec-dir>` at a time.

---

## Initialization and Reset

### Init sequence

At new loop-run initialization (not session resume — a resuming session calls
`status`, not `init`):

**Skill-side preflight:**
1. Skill calls `loop-cohort identity <spec-dir>` — if it exits 0 (`state.json`
   present and valid), refuse and surface: cohort state exists without engine
   state, or a prior run was not reset. Ask user to run the reset pair.
   If `identity` exits non-zero, `state.json` is absent or corrupt — proceed
   to step 2. (A present-but-corrupt `state.json` is caught at step 4:
   `loop-cohort init` refuses if `state.json` already exists; the error there
   routes to Corrupt-pair recovery.)
2. Skill calls `loop-engine init <spec-dir> --mode <mode> --json` — engine checks
   that `engine-state.json` is absent (its own file only), generates `run_id`,
   writes `engine-state.json`, outputs `run_id`. If `engine-state.json` is already
   present (engine-orphan: a prior engine init completed but cohort init did not),
   the engine refuses — run the reset pair (see Corrupt-pair recovery) before
   retrying.
3. Skill captures `run_id` from step 2.
4. Skill calls `loop-cohort init <spec-dir> --run-id <run_id>` — cohort writes
   `state.json` with matching `run_id`.

**If step 4 fails** (engine written, cohort failed): the run is incomplete and
no transition is allowed. The skill invokes the reset pair (see below) and
surfaces the error.

### Reset sequence

When resetting a run (before starting a new one, or to recover from a corrupt
pair):

```
loop-cohort reset <spec-dir>   # deletes state.json; idempotent
loop-engine reset <spec-dir>   # deletes engine-state.json; idempotent
```

Each command owns and deletes only its own file. Each is idempotent (tolerates
already-absent). Running both leaves both files absent; `loop-engine init` can
then proceed. A partial failure (one command succeeds, one fails) leaves one
file absent — running both commands again recovers: the absent file's command is
a no-op, the present file's command retries deletion.

**Corrupt-pair recovery:** any of the following conditions is resolved by running
the reset pair: one file present and one absent; `run_id` mismatch detected by
identity check; either file unparseable (malformed JSON). `loop-cohort identity`
is the first command to open `state.json` on resume — an unparseable file exits
non-zero before any mutation. Both reset commands are idempotent.

**Accepted cost:** reset discards all iteration history, the persisted schedule,
and review fingerprints. A late-phase inconsistency forces a full restart from
the initial drafting state, including the G-plan approval flow. Partial recovery
is not supported in Phase 1.

### run_id verification

For every code/spec-plan transition, the engine reads `engine-state.json`
first; if `schema_version != 1`, it refuses with a descriptive error (forward
guard for future schema versions). It then runs `loop-cohort identity <spec-dir>
--expect-run-id <run_id>` (where `run_id` is from engine-state.json) as a
mandatory preflight before its event-specific guard. If identity exits non-zero
(file absent, schema_version mismatch, run_id mismatch), the transition is
refused with the identity error.

This is a read-only call and does not violate the A boundary (the engine reads
only through this designated verb, never by directly opening state.json).

---

## Phase FSM: Transition Tables

Two modes in Phase 1. State names embed the phase for readability.

**Initial state** (both modes): `SPEC-PLAN-DRAFTING`, `last_event: null`,
`last_event_context: null`, `transition_sequence: 0`.

Legal states per mode:

- **code:** `SPEC-PLAN-DRAFTING`, `SPEC-PLAN-REVIEW`, `SPEC-PLAN-HUMAN-GATE`,
  `CODE-IMPLEMENTATION`, `CODE-VERIFICATION`, `CODE-REVIEW`, `CODE-HUMAN-GATE`,
  `DONE`
- **spec-plan:** `SPEC-PLAN-DRAFTING`, `SPEC-PLAN-REVIEW`, `SPEC-PLAN-HUMAN-GATE`,
  `DONE`

### code

| Current state | Event | Next state |
|---|---|---|
| `SPEC-PLAN-DRAFTING` | `spec-ready` | `SPEC-PLAN-REVIEW` |
| `SPEC-PLAN-REVIEW` | `reviewers-clean` | `SPEC-PLAN-HUMAN-GATE` |
| `SPEC-PLAN-REVIEW` | `findings-remain` | `SPEC-PLAN-DRAFTING` |
| `SPEC-PLAN-HUMAN-GATE` | `plan-approved` | `CODE-IMPLEMENTATION` |
| `SPEC-PLAN-HUMAN-GATE` | `plan-rejected` | `SPEC-PLAN-DRAFTING` |
| `CODE-IMPLEMENTATION` | `wave-complete` | `CODE-VERIFICATION` |
| `CODE-VERIFICATION` | `wave-passed` | `CODE-IMPLEMENTATION` |
| `CODE-VERIFICATION` | `gates-clean` | `CODE-REVIEW` |
| `CODE-VERIFICATION` | `gates-failed` | `CODE-IMPLEMENTATION` |
| `CODE-REVIEW` | `reviewers-clean` | `CODE-HUMAN-GATE` |
| `CODE-REVIEW` | `findings-remain` | `CODE-IMPLEMENTATION` |
| `CODE-HUMAN-GATE` | `done` | `DONE` |
| `CODE-HUMAN-GATE` | `blocker-applied` | `CODE-IMPLEMENTATION` |

### spec-plan

spec-plan reuses the first three code-mode states and terminates at
`SPEC-PLAN-HUMAN-GATE`. Reviewer rounds are not recorded and no implementation
waves are scheduled.

| Current state | Event | Next state |
|---|---|---|
| `SPEC-PLAN-DRAFTING` | `spec-ready` | `SPEC-PLAN-REVIEW` |
| `SPEC-PLAN-REVIEW` | `reviewers-clean` | `SPEC-PLAN-HUMAN-GATE` |
| `SPEC-PLAN-REVIEW` | `findings-remain` | `SPEC-PLAN-DRAFTING` |
| `SPEC-PLAN-HUMAN-GATE` | `plan-approved` | `DONE` |
| `SPEC-PLAN-HUMAN-GATE` | `plan-rejected` | `SPEC-PLAN-DRAFTING` |

---

## Interaction Model (Option A)

```
  LLM skill
      │
      │ loop-engine transition <spec-dir> <event>
      ▼
  loop-engine.py
      │
      ├── 0. run_id preflight (all code/spec-plan transitions):
      │       loop-cohort identity --expect-run-id <run_id>
      │       (refuses if file absent, schema_version != 1, or run_id mismatch)
      │
      ├── 1. validate event against FSM for current mode × state
      │       (refuses non-zero if invalid)
      │
      ├── 1b. plan-hash check (CODE-* states only, except `done`; after event validation):
      │       loop-cohort schedule check-current <spec-dir>
      │       (refuses if plan.md changed since schedule; skipped for SPEC-PLAN-* states
      │        and for `done` — PR is already merged, no enforcement benefit)
      │
      ├── 2. fire event-specific guard (if one listed in Guards table):
      │       read-only call; refuses non-zero if guard exits non-zero
      │
      └── 3. write new state to engine-state.json
              (increments transition_sequence; records last_event + last_event_context; atomic write)

  LLM skill (after transition returns 0)
      │
      └── invokes loop-cohort verbs explicitly per Explicit Skill Calls

  loop-cohort.py
      │
      └── reads and writes state.json exclusively
          loop-engine reads cohort state only via designated read-only verbs
          (identity, plan check-current, schedule check-current, wave check, check --phase)
          [review inspect is skill-invoked preflight, not an engine guard]
```

**Direction is one-way.** loop-engine calls loop-cohort only for read-only verbs.
loop-cohort never calls loop-engine. There is no shared mutable state other than
the immutable `run_id` pair.

---

## Guards

Each transition has at most one event-specific guard, beyond two mandatory
pre-guards: the run_id preflight (`loop-cohort identity`) fires for all
code/spec-plan transitions; `loop-cohort schedule check-current` fires for every
transition from a `CODE-*` state (plan immutability). Guards are always read-only
calls.

| Event | Mode | Current state | Guard call | Purpose |
|---|---|---|---|---|
| `plan-approved` | code | `SPEC-PLAN-HUMAN-GATE` | `loop-cohort plan check-current <spec-dir> --require-schedule` | Verifies approval + schedule bound to current spec.md + plan.md |
| `plan-approved` | spec-plan | `SPEC-PLAN-HUMAN-GATE` | `loop-cohort plan check-current <spec-dir>` | Verifies approval bound to current spec.md + plan.md (no schedule) |
| `wave-complete` | code | `CODE-IMPLEMENTATION` | `loop-cohort check <spec-dir> --phase implement` | Advisory: token budget, same-error (non-blocking in Phase 1; plan immutability is covered by mandatory `schedule check-current` pre-guard) |
| `gates-failed` | code | `CODE-VERIFICATION` | `loop-cohort check <spec-dir> --phase gates-failed` | Retry cap: refuses if `implementation_retry_count >= max_implementation_retries` |
| `wave-passed` | code | `CODE-VERIFICATION` | `loop-cohort wave check <spec-dir> --expect more --wave-index <n>` | Mechanically verify more waves remain; index matches persisted state |
| `gates-clean` | code | `CODE-VERIFICATION` | `loop-cohort wave check <spec-dir> --expect last` | Mechanically verify current is the final wave |
| `findings-remain` | code | `CODE-REVIEW` | `loop-cohort check <spec-dir> --phase review` | Review retry cap (`review_retry_count`); advisory: token budget, same-error |
| `reviewers-clean` | code | `CODE-REVIEW` | `check-spec-status.py <spec-dir>` | `**Status:** Shipped` before G-pr |

**`plan check-current` scope (code, `--require-schedule`):** verifies
`plan_review_status == "approved"`, `approved_spec_hash == sha256(spec.md)`,
`approved_plan_hash == sha256(canonical(plan.md))`, `plan_hash == approved_plan_hash`,
`schedule_waves` non-empty, `0 <= current_wave_index < len(schedule_waves)`.
This guard runs only at the `plan-approved` transition (G-plan gate). It catches
spec.md or plan.md edited between `approve-plan` and `schedule`, or between
`schedule` and the engine transition. After `plan-approved`, spec.md byte-level
integrity is not re-checked (permitted status mutations make the raw hash stale —
see `approved_spec_hash` note).

**`plan check-current` scope (spec-plan, no flag):** verifies
`plan_review_status == "approved"`, `approved_spec_hash == sha256(spec.md)`,
`approved_plan_hash == sha256(canonical(plan.md))`. No schedule check (spec-plan has no
implementation waves). Both spec.md and plan.md are bound to the approval
marker; a post-approval edit to either file causes this guard to refuse.
Precondition: spec-plan mode requires both `spec.md` and `plan.md` to be present
before `approve-plan` is called. If either is absent, `plan check-current` exits
non-zero with a descriptive message (consistent with the global exit contract).

**`wave-complete` guard scope:** enforces advisory bounds only — token budget and
same-error checks (advisory: not blocked in Phase 1 because their writers are
unspecified). Plan immutability is enforced by the mandatory `schedule check-current`
pre-guard (step 1b in the Interaction Model) that fires for all CODE-* transitions
except `done`. This guard does NOT enforce the implementation retry cap
— that moves to `gates-failed`.

**`gates-failed` guard scope:** enforces `implementation_retry_count <
max_implementation_retries`. Fires before repair begins. Successful
scheduled-wave executions do NOT consume retry budget — only `gates-failed`
repair cycles do. The cap is global across the run (not per-wave); per-wave cap
is deferred.

**`findings-remain` guard scope:** enforces `review_retry_count <
max_review_retries`. Counts findings-only rounds; clean reviews and
human-blocker round-trips do not consume this budget. Token budget and same-error
checks are advisory in Phase 1. **Implementation note (PR #816 must make three
changes to `_evaluate` / `cmd_check`):**
(1) Remove the stasis comparison (`finding_fingerprints` vs
`previous_finding_fingerprints`) from `check --phase review` — stasis routing
moves to `review inspect` in the skill.
(2) Rework the `_evaluate` cap logic to key `check --phase gates-failed` off
`implementation_retry_count < max_implementation_retries` and `check --phase
review` off `review_retry_count < max_review_retries`; drop the
`iteration_count`/`max_iterations` cap entirely (`check --phase implement`
becomes an advisory pass-through in Phase 1 — no blocking cap is specified for
that phase).
(3) Remove the module-scope `_template_max_iterations()` helper and the
`DEFAULTS["max_iterations"]` entry alongside the `_evaluate` cap logic; once
`assets/state.json` is migrated to the Phase-1 field set, the `max_iterations`
key is absent and `_template_max_iterations()` would otherwise emit a spurious
warning on every invocation.
Also: change `PHASES` from `("plan", "implement", "review")` to
`("implement", "review", "gates-failed")` and remove the `phase == "plan"` /
`plan_review_status == "pending"` branches (plan approval moves to
`plan check-current`).

**`reviewers-clean` in `SPEC-PLAN-REVIEW`** carries no guard — the spec is not
being shipped.

**`check-spec-status.py`** — CLI contract: `check-spec-status.py <spec-dir>`;
exits 0 iff the canonical status parser resolves `spec.md`'s Status token to
`Shipped`; exits non-zero with a one-line reason on stderr otherwise (missing,
wrong status, or unparseable). It must reuse the same canonical status parser as
`lint-spec-status.py` to avoid an independent regex. **Scope limitation and named risk acceptance:** the gate
proves the string is present, not that *this run* wrote it — a stale `Shipped`
from an abandoned prior run would pass. The reset pair deletes only run-local
scratch files and does NOT clear `spec.md`. Phase-2 resolution: a run-id-stamped
marker or having the reset pair also rewrite `spec.md` Status. Phase-1 control:
before reusing a spec dir after an abandoned run, manually reset `spec.md` Status
to `Implementing`; a fresh spec dir will not have a stale `Shipped`. The gate fires at the `CODE-REVIEW → CODE-HUMAN-GATE` edge
(before G-pr, not at merge). This means
a `blocker-applied` return leaves the spec with `Status: Shipped` while the PR
continues iterating. This is intentional — per the project's "set final status
in impl PR" convention, the PR itself signals the proposed ship status. The gate
enforces the update is not forgotten before the human reviews the PR.

**Stasis routing:** before firing `reviewers-clean` or `findings-remain` at
`CODE-REVIEW`, the skill calls `loop-cohort review inspect --report <path>
--json` and routes in this order:

1. `classification: invalid` → surface to human (fire neither event)
2. `classification: clean` → fire `reviewers-clean`
   (`matches_previous_round` is always `false` when the computed fingerprint
   set is empty; an empty-vs-empty comparison is not stasis)
3. `classification: findings` AND `matches_previous_round: true` → stasis →
   surface to human
4. `classification: findings` AND `matches_previous_round: false` → fire
   `findings-remain`

`review inspect` defines `matches_previous_round: false` whenever the computed
fingerprint set is empty. This ensures a clean review (no findings) can never
be misrouted to stasis even when `finding_fingerprints` was last recorded as
empty. `review inspect` is the canonical fingerprint computation; the skill
never computes hashes directly from prose.

**`findings-remain` floor:** a `classification: findings` result must contain at
least one fingerprint. A round returning `classification: clean` fires
`reviewers-clean` instead.

---

## Explicit Skill Calls

In Option A, the skill invokes loop-cohort verbs at defined points. The engine
does not invoke these.

### Skill Contract (consolidated obligations)

The correctness of Option A rests on the skill honoring this ordered call contract.
Each obligation notes idempotency:

| Obligation | Timing | Idempotent on crash? |
|---|---|---|
| `approve-plan` then `schedule` (code mode) | after human G-plan sign-off, before `plan-approved` transition | no — re-run both on abort |
| Write `Status: Implementing` | after `plan-approved` transition (CODE-IMPLEMENTATION entry) | yes — safe to re-write |
| `record-attempt --cycle-id <run_id>:<seq>` | immediately after `gates-failed` transition | yes — same cycle-id is a no-op |
| `wave advance --from-index <n>` | immediately after `wave-passed` transition | yes — `current_wave_index == n+1` returns success |
| `review inspect` then route to `reviewers-clean` or `findings-remain` | at CODE-REVIEW before any FSM event | no — inspect is read-only; routing event is not |
| `review record --fingerprint` | after `findings-remain` transition | no — non-idempotent; see Session Resumption step 7 |
| `review record --report` | after `reviewers-clean` transition | no — non-idempotent; missed write is audit-only |
| Write `Status: Shipped` | before `reviewers-clean` transition (enforced by `check-spec-status.py` guard) | yes — safe to re-write |
| `done` only after confirmed merge | at CODE-HUMAN-GATE human G-pr approval | no — irreversible |

### At new loop-run initialization (not session resume)

```
# Skill preflight:
loop-cohort identity <spec-dir>           # if exit 0, existing cohort state → surface
loop-engine init <spec-dir> --mode <mode> --json   # outputs run_id
loop-cohort init <spec-dir> --run-id <run_id>
```

### Before `plan-approved` — code mode

**Intended ordering:** human sign-off is received first; then `approve-plan` +
`schedule`; then `plan-approved` transition. The `plan check-current` guard
re-verifies the hashes at transition time, so editing spec.md or plan.md between
human sign-off and the guard fires naturally refuses the transition.

```
loop-cohort approve-plan <spec-dir> --expect-run-id <run_id>
    # sets plan_review_status, approved_spec_hash (spec.md), approved_plan_hash (plan.md)
loop-cohort schedule <spec-dir> --expect-run-id <run_id>
    # validates DAG; persists waves + plan_hash
loop-engine transition <spec-dir> plan-approved   # guard: plan check-current --require-schedule
```

A dependency cycle or missing task from `schedule` aborts the sequence. A
`plan check-current` failure means plan.md was edited between the two calls —
re-run `approve-plan` and `schedule` on the corrected plan.

**`plan-rejected` cleanup:** `plan-rejected` returns to `SPEC-PLAN-DRAFTING`.
No cohort cleanup is needed — `approve-plan`'s stored hashes are stale once the
plan changes, and the `plan check-current` guard will refuse any transition using
the old hashes. The stale approval is overwritten on the next `approve-plan` call.
`plan-rejected` does NOT reset `spec.md` Status — `Status: Approved` may remain
while the run is back in `SPEC-PLAN-DRAFTING`. Skill obligation: reset `spec.md`
Status to `Drafting` (or the equivalent in-progress status) before re-drafting.
Not mechanically enforced in Phase 1; `approve-plan` validates the file hash, not
the current Status value.

**spec-plan mode:** calls `approve-plan` only. Does not call `schedule` (no
implementation task DAG).

### After `gates-failed` — code mode

The skill calls `record-attempt` immediately after the `gates-failed` engine
transition (not before `wave-complete`). The `cycle-id` is derived from
`run_id:transition_sequence` where `transition_sequence` is the value just
written by the `gates-failed` transition.

```
loop-engine transition <spec-dir> gates-failed   # guard: check --phase gates-failed (retry cap)
# engine now at CODE-IMPLEMENTATION; transition_sequence incremented
loop-cohort record-attempt <spec-dir> --phase implement \
    --cycle-id <run_id>:<transition_sequence> --expect-run-id <run_id> [--error-fingerprint <hex>]
# idempotent: same cycle-id on replay → no increment
```

If a crash occurs between `gates-failed` and `record-attempt`, `last_event:
gates-failed` in engine-state.json tells the resuming session to reissue
`record-attempt` with the same `cycle-id` (idempotent).

### Before `wave-complete` — code mode

`wave-complete` fires when the wave's tasks are built and ready for verification.
No `record-attempt` call at this point.

```
loop-engine transition <spec-dir> wave-complete   # guard: check --phase implement (advisory only)
```

The guard fires on every `wave-complete`. It enforces advisory bounds only
(token budget, same-error — non-blocking in Phase 1 because their writers are
Phase-2-reserved; effectively a pass-through in Phase 1). Plan immutability is
enforced by the mandatory `schedule check-current` pre-guard (step 1b) that
fires before the event-specific guard. The retry cap is guarded at `gates-failed`.

### After `CODE-VERIFICATION + wave-passed`

The skill supplies `--wave-index <n>` to the engine transition, where `n` is
`current_wave_index` at the time of the call. The engine stores this in
`last_event_context: {completed_wave_index: n}`.

```
loop-engine transition <spec-dir> wave-passed --wave-index <n>
    # guard: wave check --expect more --wave-index <n>; engine records last_event_context: {completed_wave_index: n}
loop-cohort wave advance <spec-dir> --from-index <n> --expect-run-id <run_id>   # idempotent
```

`wave advance` is idempotent: if a crash occurs between the engine writing
`wave-passed` and the skill calling `wave advance`, the resuming session
extracts `completed_wave_index` from `last_event_context` and reissues
`wave advance --from-index <completed_wave_index>`. This is safe in both crash
windows (before or after the advance completed).

### Stasis routing and CODE-REVIEW exit

```
# Always before routing reviewers-clean or findings-remain:
loop-cohort review inspect <spec-dir> --report <path> --json

# If classification == clean:
loop-engine transition <spec-dir> reviewers-clean   # guard: check-spec-status.py
loop-cohort review record <spec-dir> --report <path> --expect-run-id <run_id>

# If classification == findings (and matches_previous_round == false):
loop-engine transition <spec-dir> findings-remain
loop-cohort review record <spec-dir> --fingerprint <h1> --fingerprint <h2> ... --expect-run-id <run_id>
# (fingerprints come from review inspect --json output)
```

`review record` is not idempotent in Phase 1. Call it once per review round. A
failed call surfaces to the human; do not retry autonomously.

### `blocker-applied` — code mode

No loop-cohort call. A human-returned blocker is not a review round;
`review_retry_count` is not incremented.

`blocker-applied` does **not** reset `implementation_retry_count`. Gate failures
during blocker repair consume the same global implementation budget as pre-review
repair cycles. If the budget is exhausted while repairing a human blocker, the
`gates-failed` guard refuses and the run must be reset — even with a blocker in
flight. Per-phase or post-blocker budget reset is deferred from Phase 1.

**Named risk acceptance — post-G-pr budget exhaustion:** a human can request a
legitimate fix at G-pr after pre-review repair cycles have consumed
`implementation_retry_count`. At that point the run is unrecoverable without a
full restart (new G-plan approval required). This is an accepted Phase-1
limitation: the default cap of 5 makes it unlikely in normal runs, and a project
can raise the cap in `assets/state.json`. A per-phase or post-blocker budget
credit is the resolution for Phase 2.

---

## Plan Immutability in Phase 1

After `plan-approved`, `plan.md` is immutable for the duration of the run. Any
material change requires full reset (both files) and a new run. In-place
replanning (rerun-schedule, G-plan renewal, wave migration) is deferred from
Phase 1.

The mandatory `schedule check-current` pre-guard (step 1b) mechanically enforces
immutability at every CODE-* transition except `done` by verifying `plan_hash ==
sha256(canonical(plan.md))`. Phase-1 canonicalization: normalize CRLF to LF and
strip trailing whitespace per line before hashing. Semantic edits (comments,
task text, dependency rewording) still cause the guard to refuse;
trailing-whitespace-only and line-ending-only changes do not.

Any semantic change to plan.md causes this guard to refuse, and the run must be
reset and restarted. Partial recovery is not supported in Phase 1.

**Frequency/impact justification:** mid-run plan edits are uncommon in
well-disciplined runs — the human G-plan gate is the canonical point for plan
changes, and the skill's discipline expects the plan to be stable once approved.
The full restart cost includes re-doing G-plan approval, but all committed code
is preserved in git. The accepted tradeoff: mechanically simple deterministic
enforcement over an escape hatch that would require replan-semantics (mapping
old tasks to new tasks, invalidating completed waves). In-place replanning is the
Phase-2 resolution.

Deferred: in-place plan correction (task rewording, dependency fix) without a
full restart. Supporting it would require a `replan-requested` transition, a
human-wait planning state, rules for preserving or invalidating completed tasks,
schedule migration semantics, and a new approved plan/schedule baseline.

**Implementation note:** the existing skill's "mid-EXECUTE re-plan" path (rerun
`approve-plan` + `schedule` and continue) conflicts with the immutability rule.
The implementation PR (PR #816) must remove or disable that path.

**Migration:** **All active runs at the time of PR #816 merge must restart** —
there is no partial migration path. A `state.json` written by the pre-Phase-1
model (per-session lifetime, `iteration_count` field, no `run_id`) fails at
Session Resumption step 1 — a pre-Phase-1 run never created `engine-state.json`,
so `loop-engine status` exits non-zero before `loop-cohort identity` is even
called. If for some reason `engine-state.json` is present but `state.json` is
pre-Phase-1 format, step 2 (`loop-cohort identity --expect-run-id`) fails instead.
Either way, run the reset pair and start a new run. PR #816 must also update
`assets/state.json` (the template written by `loop-cohort init`) to the
Phase-1 field set defined in the Scripts section above.

---

## Human Gate Obligations

### G-plan (plan approval)

`plan-approved` fires only after all hold, **in this order**:

1. Adversarial reviewer returned clean on spec/plan. — *Skill obligation.*
2. **`Status: Approved` is written to `spec.md` BEFORE calling `approve-plan`.**
   — *Skill obligation. Required ordering: the `plan-approved` guard re-checks
   `approved_spec_hash == sha256(spec.md)`; any byte change to spec.md between
   `approve-plan` and the engine transition refuses the guard. Writing
   `Status: Approved` after `approve-plan` deadlocks the happy path. spec.md is
   byte-frozen from the `approve-plan` call through the `plan-approved` transition.*
3. Human G-plan sign-off received on the frozen spec + plan. — *Skill obligation;
   not mechanically enforced. Sign-off must be obtained BEFORE `approve-plan` so
   the human approves the exact version that `approve-plan` will hash. No
   substantive edit to spec.md or plan.md may occur between sign-off and the
   `approve-plan` call; any such edit changes the approval version.*
4. `loop-cohort approve-plan` was called. — *Mechanically enforced: `plan
   check-current` verifies `plan_review_status == "approved"` and both
   `approved_spec_hash == sha256(spec.md)` and `approved_plan_hash == sha256(canonical(plan.md))`.*
5. `loop-cohort schedule` exited 0. — *Mechanically enforced: `plan
   check-current` verifies `schedule_waves` non-empty and `plan_hash` matches.*
6. Both `approved_plan_hash` and `plan_hash` equal `sha256(canonical(plan.md))`. —
   *Mechanically enforced: `plan check-current`.*

### G-pr (code review and merge)

`done` and `blocker-applied` carry no mechanical guard. `done` must not be
fired without a confirmed merge. A merge-verification guard is deferred.

**Named risk acceptance — `done` has no mechanical guards:** `done` skips both
merge verification (deferred) and plan immutability. A mis-firing skill can
terminate a run with an unmerged or plan-mutated tree and nothing catches it
mechanically. This is an accepted Phase-1 gap: both omissions are individually
justified (merge guard deferred; plan-check exempted to avoid stranding merged
runs), but the combination leaves the only irreversible transition wholly
trust-based. Merge verification and a post-merge plan-check exemption are
Phase-2 items.

`done` is **exempt from the `schedule check-current` pre-guard** (see Interaction
Model step 1b). The PR is already merged when `done` fires; plan immutability has
served its purpose and enforcing it there would strand a completed run for zero
protective benefit. `blocker-applied` is not exempt: it returns to
CODE-IMPLEMENTATION, where plan immutability continues to matter.

```
CODE-REVIEW → reviewers-clean → CODE-HUMAN-GATE
              (check-spec-status        │
               guard fires here)        │ LLM presents PR for human G-pr review
                                        │
                ┌───────────────────────┴────────────────────────┐
                │ Human approves and PR merges                   │ Human returns blocker
                ▼                                                 ▼
             done → DONE                        blocker-applied → CODE-IMPLEMENTATION
```

---

## State Ownership

No field is shared as mutable state between the two files. The engine reads
cohort state only through designated read-only verbs.

| File | Owner | Key fields |
|---|---|---|
| `state.json` | loop-cohort | **Active Phase-1:** `run_id`, `schema_version`, `feature`, `plan_review_status`, `approved_spec_hash`, `approved_plan_hash`, `review_round_count`, `review_retry_count`, `max_review_retries`, `implementation_retry_count`, `max_implementation_retries`, `last_record_attempt_cycle_id`, `finding_fingerprints`, `previous_finding_fingerprints`, `plan_hash`, `schedule_waves`, `current_wave_index` ∥ **Disabled-verb (no Phase-1 writer):** `auto_parallel`, `last_commit_sha`, `worktrees` ∥ **Phase-2 reserved (no Phase-1 writer):** `token_budget_used_pct`, `token_budget_cap_pct`, `consecutive_same_error_count`, `consecutive_same_error_threshold`, `last_error_fingerprint` |
| `engine-state.json` | loop-engine | `schema_version`, `run_id`, `feature`, `mode`, `state`, `last_event`, `last_event_context`, `transition_sequence`, `last_transition_at` |

*This table is the authoritative field list. The field descriptions in the Scripts section above are supplementary. Phase-2 reserved and disabled-verb fields have no Phase-1 writer; guards treat Phase-2 reserved as advisory.*

**`run_id`** is an immutable UUID generated at `loop-engine init`. Both files
carry it; every transition verifies the pair via `loop-cohort identity`.

**`feature`** is an immutable slug: the exact basename of `<spec-dir>` after
stripping any trailing slash and resolving to an absolute path (i.e.
`os.path.basename(os.path.realpath(spec_dir))`). Both `loop-engine init` and
`loop-cohort init` derive it from the same argument using the same normalization;
`run_id` is the pairing key, not `feature`. `feature` is informational only.

**Counters are separated by concern.** `review_round_count` counts all
CODE-REVIEW rounds (incremented by every `review record`). `review_retry_count`
counts findings-only rounds (incremented by `review record --fingerprint` only;
clean rounds and human-blocker round-trips do not consume this budget).
`implementation_retry_count` counts repair cycles after `gates-failed`
(incremented by `record-attempt`). Successful scheduled-wave execution consumes
neither budget.

Both files are run-local and gitignored.

---

## Coordination by Mode

| Mode | loop-cohort guards | spec-status guard | wave guards | Skill explicit calls |
|---|---|---|---|---|
| `code` | `plan-approved` (`plan check-current --require-schedule`), `wave-complete` (`check --phase implement`), `gates-failed` (`check --phase gates-failed`), `findings-remain` (`check --phase review`) | `reviewers-clean` at CODE-REVIEW | `wave-passed` (`wave check --expect more --wave-index <n>`), `gates-clean` (`wave check --expect last`) | init pair, `approve-plan` + `schedule` before `plan-approved`, `wave advance` after `wave-passed`, `record-attempt` after `gates-failed`, `review inspect` before CODE-REVIEW routing, `review record` after each CODE-REVIEW exit |
| `spec-plan` | `plan-approved` (`plan check-current`) | — | — | init pair, `approve-plan` before `plan-approved` |

**Light mode** does not invoke loop-engine or loop-cohort.

---

## Convergence Loops

### code mode

**Pre-plan loop** (LLM-judged, no cohort cap; for spec-plan mode, this is the
entire workflow — the only mechanical termination is the human G-plan gate;
review-round cap enforcement is a skill obligation in spec-plan mode):
```
SPEC-PLAN-DRAFTING ──spec-ready──► SPEC-PLAN-REVIEW
                                         │
                         ┌───────────────┴───────────────┐
                  findings-remain                  reviewers-clean
                         │                               │
                         ▼                               ▼
                  SPEC-PLAN-DRAFTING          SPEC-PLAN-HUMAN-GATE
                    (fix, re-draft)                 │ plan-approved
                                                    ▼
                                           CODE-IMPLEMENTATION
```

**Code loop (multi-wave + review, cohort-bounded):**
```
CODE-IMPLEMENTATION
    │  wave-complete
    │  guard: check --phase implement (advisory only)
    ▼
CODE-VERIFICATION   [skill branches: gates pass? → wave check --expect last
    │                  last wave? → gates-clean; else → wave-passed
    │                  gates fail? → gates-failed]
    ├── wave-passed (guard: wave check --expect more --wave-index <n>) ──► CODE-IMPLEMENTATION
    │     skill: wave advance --from-index <n>                                (next wave)
    ├── gates-clean (guard: wave check --expect last) ────► CODE-REVIEW
    └── gates-failed (guard: check --phase gates-failed) ──► CODE-IMPLEMENTATION
                                                           (skill: record-attempt after
                                                            engine transition; then repair)
CODE-REVIEW
    │  (skill: review inspect --json first)
    ├── reviewers-clean (guard: check-spec-status.py) ──► CODE-HUMAN-GATE
    │     skill: review record --report                         │
    │                                                  done ───┼──► DONE
    │                                           blocker-applied ──► CODE-IMPLEMENTATION
    └── findings-remain (guard: check --phase review) ──► CODE-IMPLEMENTATION
          skill: review record --fingerprint <h>...
```

**Termination mechanisms:**

1. **Review retry cap** — `check --phase review` exits non-zero when
   `review_retry_count >= max_review_retries`. Counts findings-only CODE-REVIEW
   rounds; clean rounds and human-blocker round-trips do not consume this budget.
2. **Implementation retry cap** — `check --phase gates-failed` exits non-zero when
   `implementation_retry_count >= max_implementation_retries`. Fires before repair
   begins (not after), so with a cap of 5 a refused sixth `gates-failed`
   back-edge means five complete repair cycles have been attempted.
   `check --phase implement` at `wave-complete` enforces advisory bounds only;
   plan immutability is enforced by the mandatory `schedule check-current`
   pre-guard.
3. **Stasis** — `review inspect` returns `matches_previous_round: true`; skill
   surfaces to human without advancing the FSM. Stasis is a single-round
   lookback: an A→B→A oscillation never matches the immediately-prior round
   and is not flagged. Oscillating findings terminate only via the
   `review_retry_count` cap; the retry cap is the backstop, not stasis detection.
4. **Token budget** *(advisory, Phase 1)* — no updater defined; guard treats as
   advisory.
5. **Consecutive-same-error** *(advisory, Phase 1)* — `record-attempt` accepts
   `--error-fingerprint` but the comparison mechanism is not yet fully specified.

---

## Human-Wait States and Session Boundaries

| State | Mode | Work product | Waiting for |
|---|---|---|---|
| `SPEC-PLAN-HUMAN-GATE` | code, spec-plan | spec.md + plan.md on branch/PR | Human G-plan sign-off |
| `CODE-HUMAN-GATE` | code | implementation PR | Human G-pr (merge or blocker) |

**Session resume rule:** a resuming session calls `loop-engine status <spec-dir>
--json` to read the current phase and `last_event`. It does not call `loop-engine
init`.
If `pending_human_wait` is true, wait for the human signal. The `last_event`
field disambiguates the five inbound paths to `CODE-IMPLEMENTATION`
(`plan-approved`, `wave-passed`, `gates-failed`, `findings-remain`,
`blocker-applied`) so the resuming session knows what repair or advancement
action is expected.

Work product must be committed to a named branch or open PR before ending a
session in a human-wait state.

---

## Session Resumption

On resume, the agent:

1. Calls `loop-engine status <spec-dir> --json` → reads `state`, `last_event`,
   `last_event_context`, `run_id`, `pending_human_wait`. If this exits non-zero
   (`engine-state.json` absent or unreadable), the run has no resumable Phase-1
   state — see Corrupt-pair recovery; start a new run after the reset pair.
2. Calls `loop-cohort identity <spec-dir> --expect-run-id <run_id>` → verifies
   `run_id` match, `schema_version == 1`, and file presence in one call. Surface
   if identity exits non-zero; do not proceed.
3. Calls `loop-cohort status <spec-dir> --json` → reads `current_wave_index`,
   `schedule_waves`, `finding_fingerprints`, `review_retry_count`,
   `implementation_retry_count`.
4. If `pending_human_wait` → wait for the human signal before firing any exit event.
5. If `state == CODE-IMPLEMENTATION` and `last_event == plan-approved` →
   `Status: Implementing` may not have been written. Ensure it is written before
   resuming implementation (idempotent: safe to re-write).
   If `state == CODE-IMPLEMENTATION` and `last_event == blocker-applied` →
   resume implementation directly without rewriting status (`Status: Shipped`
   intentionally remains during blocker repair).
6. If `state == CODE-IMPLEMENTATION` and `last_event == wave-passed` → extract
   `completed_wave_index` from `last_event_context`; reissue `loop-cohort wave
   advance <spec-dir> --from-index <completed_wave_index> --expect-run-id <run_id>`
   (idempotent; safe in both crash windows — before or after the advance completed).
7. If `state == CODE-IMPLEMENTATION` and `last_event == findings-remain` →
   `review record --fingerprint` may not have run. This window is not idempotent
   in Phase 1 (no report-path pointer in `state.json` to enable safe replay). Surface
   to human: report two consequences — (a) `review_retry_count` may be under-counted
   by one (conservative; guard may allow one extra retry), AND (b) `finding_fingerprints`
   still holds the previous round's set, so the next `review inspect` stasis check
   compares round N+1 against N-1 (a genuine N↔N+1 stasis is missed). The
   `review_retry_count` cap is the sole remaining backstop for that round.
   **Proceed with under-counted budget and stale fingerprint baseline (Phase-1
   accepted limitation).** Do NOT auto-reissue `review record`.
8. If `state == CODE-IMPLEMENTATION` and `last_event == gates-failed` →
   `record-attempt` may not have run. Reissue `loop-cohort record-attempt
   --cycle-id <run_id>:<transition_sequence> --expect-run-id <run_id>` (idempotent:
   same cycle-id is a no-op).
9. If `state == CODE-REVIEW` → no pending cohort mutation (the only inbound
   edge to CODE-REVIEW is `gates-clean`, which carries no `review record`). Re-run
   the reviewer fan-out and `review inspect`.
10. If `state == CODE-VERIFICATION` → `wave-passed` vs `gates-clean` is
    mechanically guarded; re-run gates and fire the appropriate event.
11. If `state == CODE-HUMAN-GATE` and `last_event == reviewers-clean` →
    wait for the human signal (step 4). After the human signal arrives, split by outcome:
    `review record --report` may not have run.
    - **`done` branch:** `review_round_count` may be under-counted by one;
      this is audit-only and does not affect guard caps. Safe to proceed.
    - **`blocker-applied` branch:** additionally, `finding_fingerprints` may
      still hold the prior findings set (not rotated to `[]` by the missed
      clean record). The next `review inspect` will compare against a stale
      pre-clean baseline — same hazard as step 7. **Recommended:** regenerate
      a clean report (re-run the reviewer fan-out), then reissue `review record
      --report --expect-run-id <run_id>` before firing `blocker-applied` (safe:
      `--report` only rotates fingerprints to `[]` and increments the audit
      counter; no cap impact). If regeneration is not possible (e.g. the working
      tree has changed), fall back to the step-7 accepted limitation: proceed
      with under-counted budget and stale fingerprint baseline.
12. If `state ∈ {SPEC-PLAN-DRAFTING, SPEC-PLAN-REVIEW, SPEC-PLAN-HUMAN-GATE}` →
    no pending cohort mutation in Phase 1 (spec-plan mutations are skill
    obligations, not tool-driven). Resume spec/plan work per skill prose.

`last_event` enables genuine work resumption without chat history. For durable
pointers to review reports or gate-failure artifacts, the skill must record these
in session notes or a designated sidecar; the cohort schema does not yet include
artifact paths in Phase 1.

**Stale-worker detection** (INI-003): `transition_sequence` and
`last_transition_at` enable a supervisor to detect staleness. Loop-engine makes
no assumption about per-phase expected duration.

---

## Future Phase: Workflow Orchestrator (B)

Phase 2 adds the orchestration layer once the following are in place:

- `loop-cohort review record` accepts `--transition-id <uuid>` and deduplicates,
  making it idempotent.
- `engine-state.json` carries a structured `pending_transition`:
  ```json
  {
    "pending_transition": {
      "id": "<uuid>",
      "event": "findings-remain",
      "from": "CODE-REVIEW",
      "to": "CODE-IMPLEMENTATION",
      "effect": {
        "verb": "review-record",
        "payload_hash": "<sha256 of fingerprint list>",
        "status": "prepared | applied | failed"
      }
    }
  }
  ```
  The committed state remains the source state until the required effect is
  confirmed. Any unresolved `pending_transition` blocks new transitions.
- `run_id` and `schema_version` propagate through pending-transition records.

With idempotency keys, crashes between side-effect and confirmation are
recoverable. Without them, Phase 1 skill-explicit mutations are the correct
choice.

---

## Deferred: doc mode

`doc` mode (RFC, ADR, architecture document) is deferred from Phase 1. The
blocker: `loop-engine` commands accept `<spec-dir>` and derive `feature` from
the directory basename. Documents such as RFCs are individual files in a shared
directory (`docs/rfc/`) — placing `engine-state.json` in that directory would
cause unrelated documents to collide and derive the same `feature` slug.

The required specification: `loop-engine init --mode doc --artifact <path>`
with `engine-state.json` stored at
`.agent-state/work-loop/<artifact-slug>/engine-state.json`. Phase 1 does not
include this addressing model. Doc mode will land in Phase 2 alongside or after
the artifact-path design.

---

## Alternatives Considered

### A-only (Phase 1) vs B now

B requires a durable `pending_transition` schema, idempotency keys, and
persisted wave state. A delivers legal ordering, guard enforcement, resumption,
and multi-wave phase structure with a much smaller surface. B lands after
`review record` is idempotent.

### Separate resets vs all-or-nothing reset

A single `loop-engine reset` deleting both files cannot be atomic: deleting
`state.json` then `engine-state.json` is two operations. Separate idempotent
`loop-cohort reset` and `loop-engine reset` commands produce a recoverable (not
atomic) outcome. Running both again after a partial failure is always safe.

### `schedule` as side effect vs. pre-transition precondition

A side-effect model moves the engine into `CODE-IMPLEMENTATION` before
scheduling; a DAG error then leaves the engine in a state with no valid
schedule. The pre-transition obligation (approve-plan → schedule → plan-approved)
means `CODE-IMPLEMENTATION` is entered only when a valid, persisted schedule
exists, contingent on the skill honoring the obligation. The `plan check-current`
guard makes this mechanically verifiable at transition time.

### Shared `iteration_count` vs. separate counters

A shared counter collapses forward progress through scheduled waves and repair
cycles onto the same budget. A five-wave plan with a default cap of 5 would
exhaust the budget before reaching code review. Separate `review_round_count`
(audit, all rounds), `review_retry_count` (findings-only cap), and
`implementation_retry_count` counters correctly model distinct convergence
concerns: successful waves consume no budget, clean reviews consume no findings
budget, and human-blocker round-trips do not consume review retries.

### Retry cap at `gates-failed` vs. at `wave-complete`

A cap guard at `wave-complete` causes an off-by-one: the nth repair increments
the counter and then the guard refuses before verification — so only n−1 repaired
attempts can be verified. A guard at `gates-failed` fires before repair begins,
so a refused nth back-edge means n−1 complete repair cycles have been attempted.
`wave-complete`'s event-specific guard (`check --phase implement`) is advisory
only; plan immutability is enforced by the mandatory `schedule check-current`
pre-guard that fires for all CODE-* transitions except `done`.

### Single-writer scope in Phase 1

`transition_sequence` supports external supervisor staleness detection (INI-003)
but does not prevent a lost-update race (two concurrent callers both read and both
write; the second silently wins). Atomic-file replacement prevents torn JSON but
not lost updates. Concurrent callers are out of scope for Phase 1; the
single-writer constraint is a skill-enforced convention. A compare-and-swap
mechanism (`--expect-sequence <n>`) is deferred to Phase 2.

### wave-passed/gates-clean by arithmetic vs. guarded

Reading `current_wave_index` and applying arithmetic is prose-dependent. Guards
(`wave check --expect more|last`) make the routing decision mechanically
enforced within the A boundary, at negligible cost.

### `review inspect` vs. skill-computed fingerprints

Having the skill compute sha1 hashes from prose risks independent parser
implementations. `review inspect` is the single canonical parser; the skill
uses its output for routing and passes the fingerprints to `review record`.

---

## Testing

Four independent test layers:

1. **FSM table tests:** enumerate all legal transitions per mode, verify correct
   next state, `last_event`, `last_event_context`, and `transition_sequence`
   increment; enumerate illegal event/state pairs and verify non-zero exit with no
   file mutation.

2. **Guard-refusal tests:** stub each guard to exit non-zero; verify the
   transition is refused and `engine-state.json` is unchanged; verify the guard
   receives the correct arguments. Include run_id preflight failure and
   `gates-failed` retry-cap refusal.

3. **Init/reset and `run_id` coupling tests:** verify `loop-engine init` refuses
   when `engine-state.json` is already present (tests the engine command in
   isolation); verify the skill-level preflight refuses when cohort state exists
   without engine state; verify reset idempotency (run twice, verify both files
   absent both times); verify corrupt-pair recovery; verify `transition` with
   mismatched `run_id` refuses; **verify that after a successful init pair both
   `engine-state.json` and `state.json` carry the same `run_id`** (positive-path
   pairing check — confirms `loop-cohort init --run-id` stores the value and
   `loop-cohort identity` returns a match).

4. **High-risk behavioural tests** (highest crash-window risk from this design):
   - **code vs. spec-plan `plan check-current`** — code mode: refuses when spec.md
     changed after approval; spec.md change in spec-plan mode also refuses.
   - **wave advance crash before advance** — engine in `CODE-IMPLEMENTATION` with
     `last_event: wave-passed`, `last_event_context: {completed_wave_index: 2}`,
     cohort `current_wave_index: 2`; verify `wave advance --from-index 2`
     advances to 3.
   - **wave advance crash after advance** — same engine state, cohort
     `current_wave_index: 3`; verify `wave advance --from-index 2` returns
     already-applied (success, no mutation).
   - **fifth retry vs. sixth retry** (cap = 5) — four `gates-failed` transitions
     succeed; fifth is allowed and records count 5; sixth is refused at the
     `gates-failed` guard before repair begins.
   - **`record-attempt` replay** — call with cycle-id A: increments count; call
     again with cycle-id A: no increment; call with cycle-id B: increments.
   - **clean review → human blocker → another review** — verify `review_retry_count`
     is unchanged through the clean and blocker round; only a `--fingerprint` call
     increments it.
   - **plan mutation in CODE-IMPLEMENTATION at `wave-complete`** — schedule a
     run; mutate plan.md before `wave-complete`; verify `wave-complete` refuses
     (`schedule check-current` fires at step 1b before the event-specific guard).
   - **plan mutation in CODE-VERIFICATION** — advance to CODE-VERIFICATION;
     mutate plan.md; verify `wave-passed`, `gates-clean`, and `gates-failed`
     all refuse (mandatory `schedule check-current` pre-guard fires).
   - **plan mutation in CODE-REVIEW** — advance to CODE-REVIEW; mutate plan.md;
     verify `findings-remain` and `reviewers-clean` both refuse.
   - **plan mutation in CODE-HUMAN-GATE** — advance to CODE-HUMAN-GATE; mutate
     plan.md; verify `blocker-applied` refuses (`schedule check-current` fires);
     verify `done` succeeds (`done` is exempt from the pre-guard).
   - **plan-rejected + re-approval** — approve a plan; fire `plan-rejected`;
     edit plan.md; call `approve-plan` again; verify new hashes are stored and
     the stale approval is overwritten (no cleanup command needed).
   - **spec-plan absent-file precondition (positive-path)** — call `plan
     check-current` in spec-plan mode (no `--require-schedule`) with spec.md
     present and plan.md absent, then with plan.md present and spec.md absent;
     verify exit non-zero with a descriptive message in both cases (spec-plan
     requires both files before `approve-plan` is called).
   - **stasis detection** — write known fingerprints to `state.json`; verify
     `review inspect --json` returns `matches_previous_round: true`; verify an
     empty-vs-empty comparison returns `matches_previous_round: false`.
   - **clean review resets fingerprint baseline** — record findings set A; call
     `review record --report` (clean); record findings set A again; verify
     `review inspect` returns `matches_previous_round: false` (clean round
     rotated baseline to `[]`).
   - **`--expect-run-id` refusal on mismatch** — call `wave advance`,
     `record-attempt`, and `review record` with an incorrect `--expect-run-id`;
     verify each exits non-zero before any mutation.
   - **`transition --wave-index` contract** — verify `wave-passed` refuses when
     `--wave-index` is omitted; verify other events refuse when `--wave-index` is
     supplied; verify guard receives the correct value.

The proposed test file will live at
`packs/core/.apm/skills/work-loop/scripts/test-loop-engine.py`.

---

## Source Tree

```
packs/core/.apm/skills/work-loop/
├── SKILL.md                         # skill entry point (LLM reads this)
├── scripts/
│   ├── loop-cohort.py               # task execution state owner
│   ├── loop-engine.py               # phase FSM validator (proposed — Phase 1)
│   ├── check-spec-status.py         # spec Status=Shipped gate (proposed — authored in PR #816; dist/ copy is stale build output, not source)
│   ├── test-loop-engine.py          # proposed test file (FSM, guard, init/reset, stasis)
│   ├── lint-spec-status.py          # spec metadata drift linter (CI/on-demand)
│   └── lint-traceability.py         # traceability matrix linter
├── assets/
│   └── state.json                   # loop-cohort state template
└── references/
    └── state-schema.md              # SUPERSEDED — pre-Phase-1 model; rewrite in PR #816
```

`engine-state.json` has no template file — its fields and allowed values are
fully specified in this document and in `loop-engine --help` output.

The agent-facing quick-reference (`references/loop-infrastructure.md`) and its
projections into `.agents/` and `.claude/` will land alongside the implementation.

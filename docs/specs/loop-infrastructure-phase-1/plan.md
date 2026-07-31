# Plan: loop-infrastructure-phase-1

- **Status:** Drafting
- **Spec:** [spec.md](spec.md)
- **Decision:** [ADR-0061](../../adr/0061-loop-infrastructure-phase-1.md)
- **Supersedes:** the mixed A/B approach explored in PR #816
- **Phase 1 scope:** `code` and `spec-plan` modes only. `doc` mode is deferred
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
| Crash-safe session resumption without chat history | persisted `engine-state.json` (`last_event`, `last_event_context`) — idempotent for `wave-passed` and `gates-failed` windows; `findings-remain` window is non-idempotent (see Session Resumption step 7); `reviewers-clean` window is audit-only on the `done` continuation, but additionally risks a stale stasis baseline on the `blocker-applied` continuation (see step 11) |
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
  remains the current implementation contract; it will be updated when the
  follow-on implementation lands. The authoritative target-state field list is the
  [State Ownership table](#state-ownership); the sub-bullets below are
  supplementary descriptions of each field's semantics.

  - `plan_review_status` — set to `"approved"` by `approve-plan`; read by
    `plan check-current` to verify the plan was approved before schedule guards
    fire. Not consulted by `check --phase` in Phase 1 (its role there is
    superseded by the `plan check-current` guard).
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
    implement` is a Phase-1 compatibility stub (exits 0; see guard-scope paragraph).
  - `schedule_waves`, `current_wave_index` — persisted by `schedule` for
    cross-run wave resumption.

- Task DAG and wave scheduling — `schedule` reads plan.md, validates the DAG,
  computes topological waves, and persists `plan_hash`, `schedule_waves`,
  `current_wave_index: 0` to `state.json`. Exit non-zero on any DAG error or if
  the task set is empty (so an empty-wave failure surfaces at scheduling, not
  at the `plan-approved` guard two calls later).
- Finding fingerprints — `review record --fingerprint` (findings round):
  `previous_finding_fingerprints = finding_fingerprints`, `finding_fingerprints =
  sorted(set(supplied_fingerprints))`, `review_retry_count += 1`, `review_round_count += 1`.
  Storing `sorted(set(...))` rather than the raw list makes the serialized state
  deterministic: two equivalent reports with duplicate or reordered fingerprints
  produce identical `state.json` values.
  `review record --report` (clean round): exits non-zero if the report is not
  clean (i.e. `parse_findings()` returns ≥1 fingerprints, or the clean substring
  is absent from the file) — findings rounds must go through `--fingerprint`.
  On a clean report: `previous_finding_fingerprints = finding_fingerprints`,
  `finding_fingerprints = []`, `review_round_count += 1`, `review_retry_count`
  unchanged. Both forms rotate `finding_fingerprints` to `[]` or the new set, so
  a subsequent `review inspect` compares against the current round's baseline —
  not a stale pre-clean set. **Not idempotent** in Phase 1. **Implementation note:**
  the existing `cmd_review_record` shares a single
  `state["iteration_count"] += 1` write across both branches; the follow-on
  implementation must replace it with branch-specific counter updates:
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
  scheduled-wave transitions. `--error-fingerprint` and the related
  `last_error_fingerprint` / `consecutive_same_error_count` fields are
  Phase-2 reserved — not part of the Phase-1 verb surface.
- Iteration gates:
  - `check --phase review` enforces the active review-retry bound.
  - `check --phase gates-failed` enforces the active implementation-retry bound.
  - `check --phase implement` is a Phase-1 compatibility stub: it reads no
    deferred token/error fields and exits 0 for every otherwise valid Phase-1
    state.
  Plan-phase approval is covered by `plan check-current --require-schedule` or
  `plan check-current`, not `check --phase`.

**Verb surface:**
```
loop-cohort init <spec-dir> --run-id <uuid>
loop-cohort identity <spec-dir> [--expect-run-id <uuid>] [--json]
loop-cohort check <spec-dir> --phase {implement,review,gates-failed}
loop-cohort approve-plan <spec-dir> --expect-run-id <uuid>
loop-cohort plan check-current <spec-dir> [--require-schedule]
loop-cohort schedule <spec-dir> --expect-run-id <uuid>
loop-cohort schedule check-current <spec-dir>
loop-cohort record-attempt <spec-dir> --phase implement --cycle-id <id> --expect-run-id <uuid>
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
  Preconditions (checked before any mutation):
  - `schedule_waves` is non-empty.
  - `0 <= n < len(schedule_waves) - 1` — advancing from the final wave is
    refused; calling `wave advance` at the last wave is a caller error (use
    `gates-clean` to exit the final wave, not `wave advance`).
  Outcomes:
  - `current_wave_index == n` → set `n + 1`, exit 0.
  - `current_wave_index == n + 1` → already advanced, exit 0 (safe retry).
  - Any other value, or precondition violated → refuse, exit non-zero.

- **`record-attempt --phase implement --cycle-id <run_id>:<seq>`** — mutating; idempotent.
  Increments `implementation_retry_count` and records the most-recent cycle-id in
  `last_record_attempt_cycle_id`. A second call with the same `--cycle-id` value
  returns success without incrementing (idempotent replay after a crash between
  `gates-failed` and `record-attempt`). A call with a different cycle-id increments.
  Requires `--expect-run-id`; the `run_id` prefix embedded in `--cycle-id` must also
  match. The skill calls this immediately after the `gates-failed` transition.

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

- **`status <spec-dir> [--json]`** — read-only. Returns the cohort fields needed
  for session resumption without mutating `state.json`. Text output (no `--json`):
  a human-readable summary of the same fields. JSON output:
  ```json
  {
    "schema_version": 1,
    "run_id": "<uuid>",
    "approved_spec_hash": "<hex> | null",
    "approved_plan_hash": "<hex> | null",
    "plan_hash": "<hex> | null",
    "schedule_waves": [],
    "current_wave_index": 0,
    "implementation_retry_count": 0,
    "review_round_count": 0,
    "review_retry_count": 0,
    "finding_fingerprints": [],
    "previous_finding_fingerprints": []
  }
  ```
  Exit 0 if `state.json` is present, readable, and `schema_version == 1`. Exit
  non-zero on absent file, malformed JSON, or unsupported `schema_version`.
  `status` makes no mutation under any condition, including error paths.
  Used at Session Resumption step 3 to read `current_wave_index`,
  `schedule_waves`, `finding_fingerprints`, and retry counters.

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

Each transition has at most one event-specific guard, plus up to two mandatory
pre-guards: the run_id preflight (`loop-cohort identity`) fires for all
code/spec-plan transitions; `loop-cohort schedule check-current` additionally fires
for every transition from a `CODE-*` state (plan immutability). `SPEC-PLAN-*`
transitions carry only the run_id preflight. Guards are always read-only calls.

| Event | Mode | Current state | Guard call | Purpose |
|---|---|---|---|---|
| `plan-approved` | code | `SPEC-PLAN-HUMAN-GATE` | `loop-cohort plan check-current <spec-dir> --require-schedule` | Verifies approval + schedule bound to current spec.md + plan.md |
| `plan-approved` | spec-plan | `SPEC-PLAN-HUMAN-GATE` | `loop-cohort plan check-current <spec-dir>` | Verifies approval bound to current spec.md + plan.md (no schedule) |
| `wave-complete` | code | `CODE-IMPLEMENTATION` | `loop-cohort check <spec-dir> --phase implement` | Phase-1 compatibility stub: exits 0 unconditionally for any valid Phase-1 state; reads no token-budget or same-error fields (writers absent); plan immutability enforced by mandatory `schedule check-current` pre-guard |
| `gates-failed` | code | `CODE-VERIFICATION` | `loop-cohort check <spec-dir> --phase gates-failed` | Retry cap: refuses if `implementation_retry_count >= max_implementation_retries` |
| `wave-passed` | code | `CODE-VERIFICATION` | `loop-cohort wave check <spec-dir> --expect more --wave-index <n>` | Mechanically verify more waves remain; index matches persisted state |
| `gates-clean` | code | `CODE-VERIFICATION` | `loop-cohort wave check <spec-dir> --expect last` | Mechanically verify current is the final wave |
| `findings-remain` | code | `CODE-REVIEW` | `loop-cohort check <spec-dir> --phase review` | Review retry cap (`review_retry_count < max_review_retries`); token-budget and same-error fields are Phase-2-deferred (no Phase-1 writers or guards defined) |
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

**`wave-complete` guard scope (`check --phase implement`) — exact Phase-1 contract:** a compatibility stub. It reads no token-budget or same-error fields (their writers are absent in Phase 1) and exits 0 for every otherwise-valid Phase-1 state. It enforces no blocking constraint. Plan immutability is enforced by the mandatory `schedule check-current` pre-guard (step 1b in the Interaction Model). The implementation retry cap moves to `gates-failed`. The stub is retained so the Phase-2 wiring point (when token-budget and same-error writers land) remains visible at the cost of one pass-through call per `wave-complete` transition. `wave-complete`'s deterministic protection comes from `schedule check-current` (plan immutability) and the `gates-failed` guard (retry cap), not this stub.

**`gates-failed` guard scope:** enforces `implementation_retry_count <
max_implementation_retries`. Fires before repair begins. Successful
scheduled-wave executions do NOT consume retry budget — only `gates-failed`
repair cycles do. The cap is global across the run (not per-wave); per-wave cap
is deferred.

**`findings-remain` guard scope:** enforces `review_retry_count <
max_review_retries`. Counts findings-only rounds; clean reviews and
human-blocker round-trips do not consume this budget. Token budget and same-error
checks are Phase-2-deferred (no Phase-1 writers or guards defined). **Implementation note:** the follow-on
implementation must make three changes to `_evaluate` / `cmd_check`:
(1) Remove the stasis comparison (`finding_fingerprints` vs
`previous_finding_fingerprints`) from `check --phase review` — stasis routing
moves to `review inspect` in the skill.
(2) Rework the `_evaluate` cap logic to key `check --phase gates-failed` off
`implementation_retry_count < max_implementation_retries` and `check --phase
review` off `review_retry_count < max_review_retries`; drop the
`iteration_count`/`max_iterations` cap entirely (`check --phase implement`
is a Phase-1 compatibility stub — exits 0, reads no Phase-2 fields; see guard-scope paragraph).
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
wrong status, or unparseable). It must reuse the same canonical status parser as `lint-spec-status.py` to avoid
an independent regex — use `importlib.util.spec_from_file_location` to import the
`parse_status` / `extract_status_token` function from `lint-spec-status.py`, or
factor the common parser into a shared `_status_parser.py` in the same `scripts/`
directory. A characterization test must assert that both files resolve identical
status tokens for the same `spec.md` content, so wording drift in one fails CI. **Scope limitation and named risk acceptance:** the gate
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
| Write `Status: Approved` | after human G-plan sign-off (administrative record), before `approve-plan` | yes — safe to re-write |
| `approve-plan` then `schedule` (code mode) | after writing `Status: Approved`, before `plan-approved` transition | no — re-run both on abort |
| Write `Status: Implementing` | after `plan-approved` transition (CODE-IMPLEMENTATION entry) | yes — safe to re-write |
| `record-attempt --cycle-id <run_id>:<seq>` | immediately after `gates-failed` transition | yes — same cycle-id is a no-op |
| `wave advance --from-index <n>` | immediately after `wave-passed` transition | yes — `current_wave_index == n+1` returns success |
| `review inspect` then route to `reviewers-clean` or `findings-remain` | at CODE-REVIEW before any FSM event | no — inspect is read-only; routing event is not |
| `review record --fingerprint` | after `findings-remain` transition | no — non-idempotent; see Session Resumption step 7 |
| `review record --report` | after `reviewers-clean` transition | no — non-idempotent; on `done` continuation: missed write is audit-only; on `blocker-applied` continuation: also risks stale stasis baseline (see step 11) |
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

**Intended ordering:** human sign-off is received first; then `Status: Approved`
is written as the administrative record; then `approve-plan` + `schedule`; then
`plan-approved` transition. The `plan check-current` guard re-verifies the hashes
at transition time, so any byte change to spec.md or plan.md between `approve-plan`
and the guard fires naturally refuses the transition. A status-only edit
(Draft → Approved) written before `approve-plan` is the one permitted post-sign-off
edit; substantive edits after human sign-off invalidate the approval.

```
# (skill writes Status: Approved to spec.md here — administrative record of human sign-off)
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
No cohort cleanup command is needed. In the intended flow, rejection fires before
step 4 (approve-plan) so no hashes are stored. If a prior cycle did store hashes,
`approve-plan`'s unconditional overwrite makes them harmless. Skill obligation:
ensure spec.md Status reflects the in-progress drafting state before re-editing.
Not mechanically enforced in Phase 1.

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
    --cycle-id <run_id>:<transition_sequence> --expect-run-id <run_id>
# idempotent: same cycle-id on replay → no increment
```

If a crash occurs between `gates-failed` and `record-attempt`, `last_event:
gates-failed` in engine-state.json tells the resuming session to reissue
`record-attempt` with the same `cycle-id` (idempotent).

### Before `wave-complete` — code mode

`wave-complete` fires when the wave's tasks are built and ready for verification.
No `record-attempt` call at this point.

```
loop-engine transition <spec-dir> wave-complete   # guard: check --phase implement (Phase-1 stub: exits 0)
```

The guard fires on every `wave-complete`. It is a Phase-1 compatibility stub:
it reads no token-budget or same-error fields (their writers are Phase-2-reserved)
and exits 0 unconditionally for any valid Phase-1 state. Plan immutability is
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
#   (skill writes Status: Shipped to spec.md here — required before check-spec-status.py guard)
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

After `plan-approved`, `plan.md` must not be modified for the duration of the run.
Any material change requires full reset (both files) and a new run. In-place
replanning (rerun-schedule, G-plan renewal, wave migration) is deferred from
Phase 1.

The engine detects plan edits relative to the stored `plan_hash` baseline via the
mandatory `schedule check-current` pre-guard (step 1b), which fires at every
CODE-* transition except `done` by verifying `plan_hash ==
sha256(canonical(plan.md))`. Phase-1 canonicalization: normalize CRLF to LF and
strip trailing whitespace per line before hashing. Semantic edits (comments,
task text, dependency rewording) still cause the guard to refuse;
trailing-whitespace-only and line-ending-only changes do not.

**Scope of mechanical detection.** The guard detects edits against the stored
baseline but does not prevent re-baselining: `approve-plan` and `schedule` remain
callable by anyone holding the correct `run_id`, and a caller that re-runs both
after editing plan.md will replace the stored hashes and pass subsequent guards.
The skill must not invoke `approve-plan` or `schedule` after `plan-approved`;
Phase 1 does not prevent a buggy or deliberate caller from replacing the baseline.
This is consistent with the A boundary: legal phase sequencing and listed guards
are mechanical, while correct explicit mutation use remains a skill obligation. A
durable mechanical seal (a command-level rule refusing re-baselining after
`CODE-IMPLEMENTATION` is entered) is deferred to Phase 2.

Any semantic change to plan.md that goes through the guard causes it to refuse,
and the run must be reset and restarted. Partial recovery is not supported in Phase 1.

**Frequency/impact justification:** mid-run plan edits are uncommon in
well-disciplined runs — the human G-plan gate is the canonical point for plan
changes, and the skill's discipline expects the plan to be stable once approved.
The full restart cost includes re-doing G-plan approval, but all committed code
is preserved in git. The accepted tradeoff: mechanically simple deterministic
detection over an escape hatch that would require replan-semantics (mapping
old tasks to new tasks, invalidating completed waves). In-place replanning is the
Phase-2 resolution.

Deferred: in-place plan correction (task rewording, dependency fix) without a
full restart. Supporting it would require a `replan-requested` transition, a
human-wait planning state, rules for preserving or invalidating completed tasks,
schedule migration semantics, and a new approved plan/schedule baseline.

**Implementation note:** the existing skill's "mid-EXECUTE re-plan" path (rerun
`approve-plan` + `schedule` and continue) conflicts with the immutability obligation.
The follow-on implementation must remove or disable that path.

**Migration:** **All active runs at the time of the follow-on implementation merge
must restart** — there is no partial migration path. A `state.json` written by
the pre-Phase-1 model (per-session lifetime, `iteration_count` field, no `run_id`)
fails at Session Resumption step 1 — a pre-Phase-1 run never created
`engine-state.json`, so `loop-engine status` exits non-zero before
`loop-cohort identity` is even called. If for some reason `engine-state.json` is
present but `state.json` is pre-Phase-1 format, step 2
(`loop-cohort identity --expect-run-id`) fails instead. Either way, run the reset
pair and start a new run. The follow-on implementation must also update
`assets/state.json` (the template written by `loop-cohort init`) to the
Phase-1 field set defined in the Scripts section above.

---

## Human Gate Obligations

### G-plan (plan approval)

`plan-approved` fires only after all hold, **in this order**:

1. Adversarial reviewer returned clean on spec/plan. — *Skill obligation.*
2. Human G-plan sign-off received on spec.md + plan.md. — *Skill obligation;
   not mechanically enforced. No substantive edit to spec.md or plan.md may occur
   after sign-off; any such edit changes the approval version.*
3. **`Status: Approved` is written to `spec.md`** as the administrative record of
   the human sign-off. — *Skill obligation. A status-only edit is explicitly
   permitted; substantive edits after human sign-off invalidate the approval.
   `approve-plan` hashes spec.md immediately after this write; any further byte
   change to spec.md between `approve-plan` and the engine transition refuses the
   `plan check-current` guard.*
4. `loop-cohort approve-plan` was called. — *Mechanically enforced: `plan
   check-current` verifies `plan_review_status == "approved"` and both
   `approved_spec_hash == sha256(spec.md)` and `approved_plan_hash == sha256(canonical(plan.md))`.*
5. `loop-cohort schedule` exited 0. — *Mechanically enforced: `plan
   check-current` verifies `schedule_waves` non-empty and `plan_hash` matches.*
6. Both `approved_plan_hash` and `plan_hash` equal `sha256(canonical(plan.md))`. —
   *Mechanically enforced: `plan check-current`.*

### G-pr (code review and merge)

`done` and `blocker-applied` carry no **event-specific** guard. `done` must not be
fired without a confirmed merge. A merge-verification guard is deferred. Both
pre-guards (`run_id` preflight and `schedule check-current`) still fire for
`blocker-applied` — it is a `CODE-*` transition and is not exempt from plan
immutability enforcement (see "blocker-applied is not exempt" below and the
corresponding test). `done` alone is exempt from `schedule check-current`.

**Named risk acceptance — `done` has no merge or plan-immutability guard:** `done`
skips merge verification (deferred) and plan-immutability enforcement (exempted).
The run_id preflight still fires, but it gives no protection against merge state
or plan mutations. A mis-firing skill can terminate a run with an unmerged or
plan-mutated tree and neither guard catches it. This is an accepted Phase-1 gap:
both omissions are individually justified (merge guard deferred; plan-check
exempted to avoid stranding merged runs), but the combination leaves merge-state
and plan-integrity trust-based. Merge verification and a post-merge plan-check
exemption are Phase-2 items.

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

| File | Owner | Phase-1 serialized fields |
|---|---|---|
| `state.json` — active | loop-cohort | `run_id`, `schema_version`, `feature`, `plan_review_status`, `approved_spec_hash`, `approved_plan_hash`, `review_round_count`, `review_retry_count`, `max_review_retries`, `implementation_retry_count`, `max_implementation_retries`, `last_record_attempt_cycle_id`, `finding_fingerprints`, `previous_finding_fingerprints`, `plan_hash`, `schedule_waves`, `current_wave_index` |
| `state.json` — disabled-verb (present, no Phase-1 writer) | loop-cohort | `auto_parallel`, `last_commit_sha`, `worktrees` |
| `state.json` — Phase-2 future (**absent from Phase-1 entirely**) | — | `token_budget_used_pct`, `token_budget_cap_pct`, `consecutive_same_error_count`, `consecutive_same_error_threshold`, `last_error_fingerprint` |
| `engine-state.json` | loop-engine | `schema_version`, `run_id`, `feature`, `mode`, `state`, `last_event`, `last_event_context`, `transition_sequence`, `last_transition_at` |

*The canonical Phase-1 initial-state JSON object below is the normative schema. The field descriptions in the Scripts section above are supplementary.*

**Schema policy:** Disabled-verb fields (`auto_parallel`, `last_commit_sha`, `worktrees`) are present in `state.json` from `loop-cohort init` with the defaults below — their presence is required for forward compatibility. Phase-2 future fields (`token_budget_used_pct`, `token_budget_cap_pct`, `consecutive_same_error_count`, `consecutive_same_error_threshold`, `last_error_fingerprint`) are **absent** from Phase-1 `state.json` entirely; no Phase-1 writer touches them, and they must not appear in `assets/state.json`.

**Phase-1 initial `state.json`** (written by `loop-cohort init <spec-dir> --run-id <uuid>`; `feature` is derived from `<spec-dir>` via `os.path.basename(os.path.realpath(spec_dir))`):

The three hash fields (`approved_spec_hash`, `approved_plan_hash`, `plan_hash`) have type `string | null` — `null` at initialization, populated with a hex digest after the corresponding cohort verb runs (`approve-plan` for the first two; `schedule` for `plan_hash`).

```json
{
  "schema_version": 1,
  "run_id": "<uuid>",
  "feature": "<slug>",
  "plan_review_status": "pending",
  "approved_spec_hash": null,
  "approved_plan_hash": null,
  "plan_hash": null,
  "schedule_waves": [],
  "current_wave_index": 0,
  "implementation_retry_count": 0,
  "max_implementation_retries": 5,
  "last_record_attempt_cycle_id": null,
  "review_round_count": 0,
  "review_retry_count": 0,
  "max_review_retries": 5,
  "finding_fingerprints": [],
  "previous_finding_fingerprints": [],
  "auto_parallel": false,
  "last_commit_sha": null,
  "worktrees": []
}
```

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
| `code` | `plan-approved` (`plan check-current --require-schedule`), `wave-complete` (`check --phase implement` — Phase-1 stub: exits 0), `gates-failed` (`check --phase gates-failed`), `findings-remain` (`check --phase review`) | `reviewers-clean` at CODE-REVIEW | `wave-passed` (`wave check --expect more --wave-index <n>`), `gates-clean` (`wave check --expect last`) | init pair, `approve-plan` + `schedule` before `plan-approved`, `wave advance` after `wave-passed`, `record-attempt` after `gates-failed`, `review inspect` before CODE-REVIEW routing, `review record` after each CODE-REVIEW exit |
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
    │  guard: check --phase implement (Phase-1 stub: exits 0)
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
   `check --phase implement` is a Phase-1 compatibility stub (exits 0);
   plan immutability is enforced by the mandatory `schedule check-current`
   pre-guard.
3. **Stasis** — `review inspect` returns `matches_previous_round: true`; skill
   surfaces to human without advancing the FSM. Stasis is a single-round
   lookback: an A→B→A oscillation never matches the immediately-prior round
   and is not flagged. Oscillating findings terminate only via the
   `review_retry_count` cap; the retry cap is the backstop, not stasis detection.
4. **Token budget** *(Phase 2 — deferred)* — no Phase-1 writer or guard defined;
   `check --phase implement` does not read this field.
5. **Consecutive-same-error** *(Phase 2 — deferred)* — `--error-fingerprint` and
   the related comparison mechanism are Phase-2 reserved; no Phase-1 updater or
   guard is specified for `consecutive_same_error_count`; `check --phase implement`
   does not read this field.

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
   `last_event_context`, `run_id`, `transition_sequence`, `pending_human_wait`.
   If this exits non-zero (`engine-state.json` absent or unreadable), the run has
   no resumable Phase-1 state — see Corrupt-pair recovery; start a new run after
   the reset pair.
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
      clean record). The next `review inspect` compares the post-blocker round
      against a stale non-empty baseline rather than `[]`, which may spuriously
      surface stasis once (conservative false-positive — unlike step 7's
      false-negative, this self-corrects from the next round onward). **Required:**
      surface the audit-distortion risk to the human — specifically that
      a `review record --report` replay may double-increment `review_round_count`
      and overwrite one level of fingerprint audit history if the original write
      already succeeded — and wait for explicit authorization before proceeding.
      If the human authorizes, regenerate a clean report (re-run the reviewer
      fan-out) and reissue `review record --report --expect-run-id <run_id>`
      before firing `blocker-applied`. If authorization is not given, proceed
      with the stale fingerprint baseline and accept the one-time spurious-stasis
      risk.
12. If `state ∈ {SPEC-PLAN-DRAFTING, SPEC-PLAN-REVIEW, SPEC-PLAN-HUMAN-GATE}` →
    no pending cohort mutation in Phase 1 (spec-plan mutations are skill
    obligations, not tool-driven).
    - If `state == SPEC-PLAN-DRAFTING` and `last_event == plan-rejected` →
      ensure spec.md Status is set to `Draft` (or the repository's selected
      drafting status) before resuming edits. Then proceed with spec/plan work.
    - All other entries to these states → resume spec/plan work per skill prose.

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
`wave-complete`'s event-specific guard (`check --phase implement`) is a Phase-1
compatibility stub (exits 0); plan immutability is enforced by the mandatory
`schedule check-current` pre-guard that fires for all CODE-* transitions except `done`.

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

## Tasks

### T1: Phase-1 cohort state, identity, approval, and schedule guards

**Depends on:** none
**Mode:** TDD
**ACs:** AC3, AC4, AC6, AC8

**Tests:**
- `identity` exits non-zero when `state.json` absent, `schema_version != 1`, or `--expect-run-id` mismatches (guard-refusal layer)
- `approve-plan` writes `plan_review_status`, `approved_spec_hash`, `approved_plan_hash`; verified via `plan check-current`
- `plan check-current` (code mode, `--require-schedule`) refuses on changed spec.md, changed plan.md, missing schedule; spec-plan mode refuses when either file is absent
- `schedule check-current` refuses when `plan_hash != sha256(canonical(plan.md))`
- `reset` deletes only `state.json`; idempotent (run twice → still absent)
- `run_id` mismatch on `approve-plan`, `schedule` exits non-zero before any mutation
- `assets/state.json` template carries Phase-1 field set; `loop-cohort init` writes it correctly
- Pre-Phase-1 `state.json` (with `iteration_count`, without `run_id`) fails `identity` (migration gate)
- `status --json` immediately after `loop-cohort init` shows `approved_spec_hash: null`, `approved_plan_hash: null`, `plan_hash: null`, `schedule_waves: []`; after `approve-plan`, hash fields transition to non-null hex strings; after `schedule`, `plan_hash` and `schedule_waves` are populated (null-to-value transition pinning)
- `status` exits 0 with correct JSON field set on valid `state.json`; text output (no `--json`) includes the same fields in human-readable form
- `status` exits non-zero on absent `state.json`, malformed JSON, or `schema_version != 1`
- `status` does not mutate `state.json` under any outcome (read-only guarantee verified by checksum before/after call)
- Each disabled Phase-1 verb (`worktree`, `dispatch-decision`, `auto-parallel`) exits non-zero with a descriptive "disabled in Phase 1" message; `state.json` is unchanged

**Approach:** Update `loop-cohort.py`: add `identity`, add `status`, update `approve-plan` (writes `approved_spec_hash`, `approved_plan_hash`), update `plan check-current` (with and without `--require-schedule`), `schedule` (persists `plan_hash`, `schedule_waves`, `current_wave_index`), `schedule check-current`, `reset`. Remove `plan_review_status` from the `check --phase` gate; it remains in `state.json` as an internal field written by `approve-plan`. Remove the `--error-fingerprint` flag and all same-error fields from Phase-1 code (Phase-2 reserved). Add exit-non-zero disable guards for `worktree`, `dispatch-decision`, and `auto-parallel` verbs (Phase-2 reserved; each refuses with a descriptive "disabled in Phase 1" message before any `state.json` mutation). Update `assets/state.json` template to Phase-1 field set: add `run_id`, `schema_version`, `review_round_count`, `review_retry_count`, `max_review_retries`, `implementation_retry_count`, `max_implementation_retries`, `last_record_attempt_cycle_id`, `finding_fingerprints`, `previous_finding_fingerprints`, `approved_spec_hash`, `approved_plan_hash`, `plan_hash`, `schedule_waves`, `current_wave_index`; remove `iteration_count`, `max_iterations` (the `plan_review_status` field is retained in `state.json` — it is only removed from the `check --phase` gate).

**Done when:** All T1 tests pass; `loop-cohort identity`, `approve-plan`, `plan check-current --require-schedule`, `schedule check-current`, `reset` exercise the test cases above; `make build-check` (SKIP_SAST=1) passes.

---

### T2: FSM engine, status/init/reset, and spec-status guard

**Depends on:** T1
**Mode:** TDD
**ACs:** AC1, AC2, AC3

**Tests:**
- All legal transitions per mode (code + spec-plan FSM tables) produce correct next state, `last_event`, `last_event_context`, `transition_sequence` increment (FSM table layer)
- All illegal event/state pairs exit non-zero with no `engine-state.json` mutation
- `loop-engine init` refuses when `engine-state.json` already present (engine-orphan guard)
- Skill-level preflight refuses when cohort state exists without engine state
- `run_id` preflight failure (identity exits non-zero) refuses transition before guard fires
- `schema_version != 1` in `engine-state.json` refuses `status` and `transition`
- `transition --wave-index` contract: required for `wave-passed`; rejected for all other events
- `check-spec-status.py` exits 0 on `Status: Shipped`; exits non-zero on wrong status, missing spec, or unparseable Status line
- `check-spec-status.py` and `lint-spec-status.py` resolve identical status tokens for the same `spec.md` content (anti-drift characterization test; imported via `importlib.util.spec_from_file_location` or shared `_status_parser.py`)
- After successful init pair: both files carry the same `run_id` (positive-path pairing check)
- `loop-engine.py` and `check-spec-status.py` each carry the required UTF-8 stdout/stderr reconfiguration immediately after importing `sys` (required for all `.apm/` scripts that write to stdout or stderr); a static/import test asserts both scripts carry the guard before any `print` or `sys.stderr.write` call

**Approach:** Write `loop-engine.py` (new script): `init`, `transition`, `status`, `reset` verbs; per-mode FSM tables; mandatory run_id preflight (calls `loop-cohort identity`); mandatory `schedule check-current` pre-guard for all CODE-* transitions except `done`; event-specific guard dispatch per the Guards table; atomic write (`tempfile` + `os.replace`); UTF-8 stdout/stderr reconfiguration immediately after `import sys`. Write `check-spec-status.py` (new script) reusing the canonical status parser from `lint-spec-status.py` (not an independent regex); UTF-8 stdout/stderr reconfiguration immediately after `import sys`. `status --json` exposes all `engine-state.json` fields plus a `pending_human_wait` boolean.

**Done when:** All T2 tests pass; `loop-engine transition` enforces the FSM for both modes; `status --json` returns all required fields; `check-spec-status.py` gates correctly; `make build-check` (SKIP_SAST=1) passes.

---

### T3: Wave, retry, and review mutations with recovery semantics

**Depends on:** T1
**Mode:** TDD
**ACs:** AC4, AC5, AC6, AC7

**Tests:**
- `wave advance` from a valid intermediate wave advances; replay at already-advanced index returns success without mutation
- `wave advance` refuses on final wave, negative n, n ≥ len(schedule_waves), empty schedule (wave advance edge-case tests from Testing section)
- `record-attempt` increments `implementation_retry_count`; same cycle-id is a no-op; new cycle-id increments (record-attempt replay tests)
- `review inspect` classification: `invalid` (report absent or unreadable, OR (`parse_findings()` returns `[]` AND no clean substring)); `clean` (`parse_findings()` returns `[]` AND clean substring present); `findings` (`len(parse_findings()) ≥ 1`); all content outcomes exit 0; stasis comparison uses `sorted(set(...))`; `review inspect` and `review record --report` share one classifier function so their clean/findings/invalid rules cannot drift
- `review record --fingerprint` stores `sorted(set(supplied_fingerprints))`; duplicate/reordered input produces identical `state.json` (fingerprint canonicalization test)
- `review record --report` exits non-zero on non-clean report; on clean: increments `review_round_count` only; rotates `finding_fingerprints` to `[]`
- Counter separation: `--report` never increments `review_retry_count`; `--fingerprint` increments both
- `check --phase gates-failed` refuses at cap; `check --phase review` refuses at cap; `check --phase implement` exits 0 with no check (Phase-1 stub); test asserts it neither reads nor requires any token-budget or same-error field from `state.json`

**Approach:** Update `loop-cohort.py`: implement `wave advance` with preconditions (`schedule_waves` non-empty; `0 <= n < len-1`); add new `record-attempt` verb with cycle-id idempotency (using `last_record_attempt_cycle_id`); implement `review inspect` with `parse_findings()`-based classification and `sorted(set(...))` stasis comparison; split `review record` into `--fingerprint` and `--report` branches with separate counter logic; store `sorted(set(supplied_fingerprints))` in `finding_fingerprints`. Rework `check --phase` to key off `review_retry_count`, `implementation_retry_count`; remove `iteration_count`/`max_iterations` cap; remove stasis comparison from `check --phase review`.

**Done when:** All T3 tests pass; `wave advance` preconditions enforced; fingerprint storage deterministic; counter separation correct per branch; `make build-check` (SKIP_SAST=1) passes.

---

### T4: Work-loop skill integration, assets, schema reference, and projections

**Depends on:** T2, T3
**Mode:** goal-based (content assertions + build-gate checks)
**ACs:** AC6, AC9, AC10

**Tests:**
- `SKILL.md` no longer references the mid-EXECUTE re-plan path or `check --phase plan` expecting exit-1
- `references/supervisor-mode.md` no longer instructs agents to invoke the disabled Phase-1 verbs (`worktree`, `dispatch-decision`, `auto-parallel`); supervisor/parallel execution is either absent or clearly marked as unavailable for Phase 1
- Active agent guidance (`SKILL.md` and `references/supervisor-mode.md`) contains no executable invocation of the disabled Phase-1 verbs (verified by content assertion — grep for `dispatch-decision`, `auto-parallel`, and `worktree` verb invocations)
- `SKILL.md` documents the `findings-remain` crash-window limitation: `review record` is non-idempotent; ambiguous crash windows are surfaced to the human rather than blindly replayed
- `SKILL.md` documents the `reviewers-clean` crash-window limitation: the audit-distortion risk (double-increment, fingerprint-history overwrite) is surfaced to the human before any `review record --report` replay; replay proceeds only after explicit human authorization
- `SKILL.md` documents the session-resumption sequence: `loop-engine status` is read first; cohort identity/schema compatibility is checked via `loop-cohort identity`; `loop-cohort status` is then read; `last_event` and `last_event_context` determine the recovery action
- `SKILL.md` init sequence matches Phase-1 command surface (engine init then cohort init, run_id threading)
- `assets/state.json` exactly matches the canonical Phase-1 initial-state object (the JSON block in the State Ownership section); Phase-2-reserved fields are absent
- `references/state-schema.md` reflects the Phase-1 field set and authoritative descriptions
- Projection parity: `.agents/` and `.claude/` copies match `packs/` source (verified by `make build-check`)
- `docs/architecture/loop-infrastructure.md` updated to describe Phase-1 as current-state implementation
- `docs/architecture/overview.md` updated to reflect Phase-1 as current state
- `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry matching bumped versions; both fields match exactly; the chosen increment is documented in the PR description with the release-classification decision (major/minor/patch per the disabled-capability policy above)
- `docs/product/changelog.md` carries a corresponding entry for this core-pack change
- `FORCE=1 make build-self` reports no projection drift after all canonical pack edits
- The work-loop exclusion comment in `packs/core/pack.toml` (the block immediately above the `[pack.evals]` key — "loaded broadly by the plan→execute→review discipline, not by a narrow user-prompt surface; a clean negative set isn't writable for it") continues to apply to Phase 1: Phase-1 does not introduce a narrower activation surface. No Tier-A `eval_queries.json` is created; no new entry is added to `[pack.evals].skills`. The T4 implementer re-verifies the exclusion comment text is unchanged after Phase-1 changes are applied.
- `packs/core/.apm/skills/work-loop/evals/evals.json` authored with 6 output-quality cases covering Phase-1 agent-facing decisions (JSON schema valid; each case has `id`, `prompt`, `expected_output`, `assertions`):
  1. Sequential wave routing — agent routes through the sequential `wave-complete` → verification → `wave-passed`/`gates-clean` loop; does not attempt parallel dispatch
  2. Disabled parallel commands — agent invokes none of `worktree`, `dispatch-decision`, `auto-parallel` in Phase-1 code mode
  3. Identity/status-first resumption — agent reads `loop-engine status` → `loop-cohort identity` → `loop-cohort status` before any mutation on session resume
  4. `last_event` routing — agent recovers via the documented action for each `last_event` value rather than re-deriving state from scratch
  5. Surfacing ambiguous non-idempotent writes — agent surfaces to human before issuing `review record` when crash-window ambiguity exists
  6. Explicit authorization before clean-report replay — agent requires and records human authorization before a `review record --report` replay that may distort audit history

**Approach:** Update `SKILL.md` to remove the old `check --phase plan` / `approve-plan` flow and wire the Phase-1 verb sequence per the Explicit Skill Calls section (init pair, G-plan sequence, stasis routing, wave advance, record-attempt). Update `references/supervisor-mode.md` to remove active dispatch instructions for the disabled Phase-1 parallel verbs (`worktree`, `dispatch-decision`, `auto-parallel`); either replace the supervisor-mode dispatch path with a sequential-only procedure, or clearly mark supervisor/parallel execution as unavailable in Phase 1 and remove any executable `dispatch-decision` call from `SKILL.md`. Update `references/state-schema.md` to Phase-1 field descriptions. Author `packs/core/.apm/skills/work-loop/evals/evals.json` with the 6 output-quality cases listed above; automated LLM grading is not a Phase-1 implementation dependency — author the fixture but do not add it to a CI grading run. Regenerate projections (`python3 -m agentbundle catalogue self-host --root . --write --force`). Update `docs/architecture/loop-infrastructure.md` and `docs/architecture/overview.md` to reflect Phase-1 as implemented current state. Add `docs/specs/**/engine-state.json` to `.gitignore` (mirroring the existing `state.json` pattern on line 13). Before bumping the pack version, the implementing PR must classify the increment according to the repository's version rules and document the decision. Making `worktree`, `dispatch-decision`, and `auto-parallel` exit non-zero removes previously functional capabilities; the repository's major-removal rule applies unless the implementing PR either (a) preserves those commands as functioning and defers their removal to a separately versioned change, or (b) documents a specific reason the removals do not meet the major threshold. Update `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` to matching versions in the same commit; add the corresponding `docs/product/changelog.md` entry; run `FORCE=1 make build-self` after all canonical pack edits.

**Done when:** `make build-check` (SKIP_SAST=1) passes with updated projections; `SKILL.md` matches Phase-1 verb surface; architecture documentation reflects current state; `pack.toml` and `plugin.json` version fields bumped with documented release-classification decision and matching; `docs/product/changelog.md` entry added; Tier-A exclusion comment confirmed unchanged; `packs/core/.apm/skills/work-loop/evals/evals.json` authored with 6 Phase-1 behavioral cases and is valid JSON.

---

### T5: Full lifecycle, crash-window, migration, and build-gate verification

**Depends on:** T4
**Mode:** TDD/integration (cross-cutting)
**ACs:** AC1–AC10

**Tests:**
- Full code-mode lifecycle (two-wave explicit, with all Option-A ordered skill calls): init pair → spec-ready → reviewers-clean → SPEC-PLAN-HUMAN-GATE (human G-plan approval) → write `Status: Approved` → approve-plan → schedule → plan-approved → write `Status: Implementing` → wave 0 implementation → wave-complete → wave-passed --wave-index 0 → wave advance --from-index 0 → wave 1 implementation → wave-complete → gates-clean → review inspect --report → write `Status: Shipped` → reviewers-clean → review record --report → confirmed human approval and merge → done; the test asserts engine state, `state.json` field values, and spec.md status strings at each boundary, not only the FSM event sequence; inject crashes before and after `wave advance --from-index 0` and verify replay uses `completed_wave_index` from `last_event_context`
- Full spec-plan lifecycle: init pair (mode=spec-plan) → spec-ready → reviewers-clean → write Status: Approved → approve-plan (no `schedule` call) → plan check-current (no `--require-schedule`) → plan-approved → DONE; assert: `schedule` is neither required nor invoked; `plan check-current` uses the no-flag form; no CODE-* state is entered; a rejected plan (`plan-rejected`) returns engine to `SPEC-PLAN-DRAFTING` with `last_event: plan-rejected`; resumption from each spec-plan state produces the correct recovery action per `last_event`
- Crash-window behavioral tests: wave advance before and after crash; gates-failed record-attempt replay; findings-remain stale-fingerprint surface; plan mutation per CODE-* state (all from Testing section layer 4)
- Normal plan-rejection lifecycle: SPEC-PLAN-HUMAN-GATE → `plan-rejected` → SPEC-PLAN-DRAFTING; assert engine carries `last_event: plan-rejected` and no `approved_spec_hash` or `approved_plan_hash` was written; restore status to Draft → edit → `spec-ready` → `reviewers-clean` → human approves → write `Status: Approved` → `approve-plan` → (code mode: `schedule`) → `plan-approved`
- Aborted pre-transition approval mutation: `approve-plan` writes hashes; sequence aborts before `plan-approved`; document is corrected and approved again; `approve-plan` reruns and unconditionally overwrites the old hashes (no cleanup command needed)
- Pre-Phase-1 `state.json` (missing `run_id`, containing `iteration_count`) fails identity at resume; reset pair clears it
- `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` version fields match; `marketplace.json` reflects the bumped version (no stale projection after `FORCE=1 make build-self`)
- `packs/core/pack.toml` Tier-A exclusion comment is confirmed unchanged (Phase-1 does not introduce a narrower activation surface)
- `packs/core/.apm/skills/work-loop/evals/evals.json` exists, parses as valid JSON, has top-level `skill_name == "work-loop"` and a top-level `evals` array of exactly 6 entries, and each entry carries `id`, `prompt`, `expected_output`, and `assertions` fields (canonical schema shape assertion; no LLM grading required for Phase-1 CI)
- `docs.yml` path triggers fire on changes to `loop-engine.py`, `check-spec-status.py`, `test-loop-engine.py`, and `test-loop-cohort.py`; CI steps run both test files and fail the job on non-zero exit
- `make ci` passes (full CI: build-check + lint + test)

**Approach:** Write integration tests in `test-loop-engine.py` covering the full lifecycle and all crash-window cases from the Testing section (test matrix layers 1–4); crash/resumption tests must read cohort state via `loop-cohort status --json` rather than inspecting `state.json` directly — this exercises the command surface and catches field omissions. Rewrite `tools/test-loop-cohort.sh` to the Phase-1 schema and verb contracts; update its `expected_keys` to the Phase-1 field set (removing `iteration_count`, `max_iterations`; adding `run_id`, `schema_version`, etc.). Extend `.github/workflows/docs.yml` path triggers to include `loop-engine.py`, `check-spec-status.py`, `test-loop-engine.py`, `test-loop-cohort.py`, `.claude/skills/work-loop/scripts/loop-engine.py`, and `.claude/skills/work-loop/scripts/check-spec-status.py` (projection parity with the existing `loop-cohort.py` trigger pattern); add CI steps for both `python3 packs/core/.apm/skills/work-loop/scripts/test-loop-engine.py` and `python3 packs/core/.apm/skills/work-loop/scripts/test-loop-cohort.py`.

**Done when:** All test-matrix cases from the Testing section pass; `make ci` is green; `tools/test-loop-cohort.sh` rewritten to Phase-1 contracts; both `test-loop-engine.py` and `test-loop-cohort.py` CI steps pass.

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
   - **Normal plan-rejection lifecycle** — start from SPEC-PLAN-HUMAN-GATE; fire
     `plan-rejected`; assert engine returns to SPEC-PLAN-DRAFTING with
     `last_event: plan-rejected`; assert no `approved_spec_hash` or
     `approved_plan_hash` was written; complete the drafting loop through
     `spec-ready` → `reviewers-clean` → write `Status: Approved` → `approve-plan`
     → `plan-approved`.
   - **Aborted pre-transition approval mutation** — `approve-plan` writes hashes;
     sequence aborts before `plan-approved`; document is corrected and approved
     again; `approve-plan` reruns and unconditionally overwrites the old hashes
     (no cleanup command needed).
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
   - **wave advance from final wave refused** — a schedule with N waves; call
     `wave advance --from-index N-1` (the last valid index); verify exit non-zero
     and no mutation.
   - **wave advance negative n refused** — call `wave advance --from-index -1`;
     verify exit non-zero and no mutation.
   - **wave advance n >= len refused** — call `wave advance --from-index N` where
     N is the schedule length; verify exit non-zero and no mutation.
   - **wave advance on empty schedule refused** — call `wave advance --from-index 0`
     when `schedule_waves` is `[]`; verify exit non-zero and no mutation.
   - **fingerprint canonicalization on record** — call `review record --fingerprint`
     with a duplicated fingerprint list (e.g. `[h1, h2, h1]`) and then with the
     same fingerprints reordered (`[h2, h1]`); verify that `state.json`
     `finding_fingerprints` is `sorted(set([h1, h2]))` in both cases (exact JSON
     value check, not a comparison through `review inspect`).
   - **G-plan ordering — Status: Approved written after sign-off** — verify that
     calling `approve-plan` after writing `Status: Approved` hashes the correct
     spec bytes; verify that a status-only edit (Draft → Approved) does not cause
     the `plan check-current` guard to refuse (the guard checks `approved_spec_hash`
     matches the current spec.md, not the pre-status-edit hash).

Test files:

- `packs/core/.apm/skills/work-loop/scripts/test-loop-cohort.py` — cohort unit tests (T1/T3):
  identity, approve-plan, plan check-current, wave advance, record-attempt, review mutations.
- `packs/core/.apm/skills/work-loop/scripts/test-loop-engine.py` — engine and integration tests
  (T2/T4/T5): FSM tables, guard-refusal, init/reset, full lifecycle, crash-window.

The split is intentional: `test-loop-cohort.py` exercises cohort verbs in isolation
(unit depth); `test-loop-engine.py` exercises the engine FSM and the full multi-component
lifecycle (integration depth). Layer-4 items that exercise a single cohort verb in isolation
— wave-advance edge cases, fingerprint canonicalization, stasis detection, `record-attempt`
replay, `--expect-run-id` refusal, spec-plan absent-file — live in `test-loop-cohort.py`
under T3. Layer-4 items that exercise the engine FSM end-to-end — plan mutation per CODE-*
state, full lifecycle, retry-cap, `--wave-index` contract — live in `test-loop-engine.py`
under T5. Each scenario has exactly one home; the layer-4 list in the Testing section labels
which file each test belongs to through T3 vs. T5 task ownership.

**Clean-substring contract:** both `review inspect` classification and stasis comparison depend
on the `adversarial-reviewer` emitting the exact string `Clean — ready to commit.` (em-dash).
Extract this as a named constant `CLEAN_SUBSTRING` imported by both the parser and any report
stub, so a reviewer wording drift fails a test rather than silently misclassifying every clean
round. Add a characterization test that asserts the constant's value.

---

## Source Tree

```
packs/core/.apm/skills/work-loop/
├── SKILL.md                         # skill entry point (LLM reads this)
├── scripts/
│   ├── loop-cohort.py               # task execution state owner (update existing)
│   ├── loop-engine.py               # phase FSM validator (new — Phase 1)
│   ├── check-spec-status.py         # spec Status=Shipped gate (new — Phase 1)
│   ├── test-loop-cohort.py          # cohort unit tests: T1/T3 (new — Phase 1)
│   ├── test-loop-engine.py          # engine + integration tests: T2/T4/T5 (new — Phase 1)
│   ├── lint-spec-status.py          # spec metadata drift linter (CI/on-demand)
│   └── lint-traceability.py         # traceability matrix linter
├── assets/
│   └── state.json                   # loop-cohort state template (update to Phase-1 fields)
├── evals/
│   └── evals.json                   # output-quality eval cases for Phase-1 decisions (new — Phase 1)
└── references/
    ├── state-schema.md              # current implementation contract (update to Phase-1 fields)
    └── supervisor-mode.md           # supervisor/parallel dispatch doc (update — remove disabled Phase-1 verb calls)

tools/
└── test-loop-cohort.sh              # existing CI harness (update — rewrite to Phase-1 schema/contracts)
                                     # state.json key/schema self-test; distinct from test-loop-cohort.py (cohort verb units)

.github/workflows/
└── docs.yml                         # CI workflow (update — add path triggers and both test steps)

.gitignore                           # repo root (update — add docs/specs/**/engine-state.json pattern)
```

`engine-state.json` has no template file — its fields and allowed values are
fully specified in this document and in `loop-engine --help` output.

No agent-facing quick-reference file (`references/loop-infrastructure.md`) is added in Phase 1. The skill entry point (`SKILL.md`), state-schema reference (`references/state-schema.md`), CLI help output, and machine-readable `loop-engine status --json` together provide the complete agent interface without a separate quick-reference doc.

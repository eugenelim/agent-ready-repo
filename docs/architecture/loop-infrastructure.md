# Loop Infrastructure

**Status:** Proposed  
**Implementation:** Not yet landed — design ratification is the precondition for
implementation (PR #816).  
**Supersedes:** the loop-engine design proposed in PR #816 (which mixed A-phase
tracking with partial B side-effect wiring).  
**Phase 1 scope:** `code` and `spec-plan` modes only. `doc` mode is deferred
pending an addressing-model decision — see
[Deferred: doc mode](#deferred-doc-mode).

The work-loop skill's phase sequencing and task execution are designed to be
implemented by two scripts. This document defines the boundary between them so
future maintainers have a single reference rather than reconstructing it from
code.

**Design choice — Phase 1:** Option A (pure phase tracker). The engine validates
legal phase ordering and runs read-only guards. All loop-cohort mutations are
invoked explicitly by the skill. Option B (workflow orchestrator with durable
side-effect semantics) is deferred until `review record` supports idempotency
keys — see [Future Phase: Workflow Orchestrator](#future-phase-workflow-orchestrator-b).

**FSM** = Finite State Machine throughout this document.

---

## Scripts

### loop-cohort.py

**Role:** Task execution state owner.

**Source:** `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`  
**Projects to:** `.claude/skills/work-loop/scripts/loop-cohort.py`

**What it owns:**

- `state.json` — the run-local state file written into each spec directory
  (intentionally survives chat-session boundaries). See
  `references/state-schema.md` for the full field reference. Schema includes:
  `run_id`, `schema_version`, `feature`,
  `plan_review_status`, `approved_spec_hash`, `approved_plan_hash`,
  `review_round_count`, `review_retry_count`, `max_review_retries`,
  `implementation_retry_count`, `max_implementation_retries`,
  `last_record_attempt_cycle_id`,
  `token_budget_used_pct`†, `token_budget_cap_pct`†,
  `consecutive_same_error_count`†, `consecutive_same_error_threshold`†,
  `finding_fingerprints`, `previous_finding_fingerprints`,
  `auto_parallel`, `last_commit_sha`, `worktrees`,
  `plan_hash`, `schedule_waves`, `current_wave_index`.

  *† Advisory in Phase 1: these fields are read by guards but have no defined
  Phase 1 writer. A guard that compares them treats them as advisory bounds
  (log but do not block) until a writer is specified.*

  - `review_round_count` — total CODE-REVIEW rounds; incremented by every
    `review record` call (both clean and findings). Audit only; not cap-guarded.
  - `review_retry_count` / `max_review_retries` — findings-only rounds;
    incremented by `review record --fingerprint` (not by `--report`). The
    `findings-remain` guard enforces this cap. Separates convergence retries from
    clean reviews and human-blocker round-trips.
  - `implementation_retry_count` / `max_implementation_retries` — counts
    `gates-failed` back-edge repair cycles; incremented by `record-attempt
    --phase implement`. Successful scheduled-wave executions do NOT consume
    this budget. The `gates-failed` guard enforces this cap.
  - `last_record_attempt_cycle_id` — the last `--cycle-id` applied by
    `record-attempt`. Enables `record-attempt` to be idempotent: a second call
    with the same cycle ID returns success without incrementing the counter.
  - `finding_fingerprints` — fingerprints from the most recent review round,
    rotated by `review record`. `review inspect` compares incoming fingerprints
    against this field for stasis detection.
  - `previous_finding_fingerprints` — fingerprints from the round before the
    most recent, retained for audit.
  - `approved_spec_hash` — sha256 of spec.md bytes at the time `approve-plan`
    ran, binding the approval marker to a specific spec version.
  - `approved_plan_hash` — sha256 of plan.md bytes at the time `approve-plan`
    ran, binding the approval marker to a specific plan version.
  - `plan_hash` — sha256 of plan.md bytes at the time `schedule` ran.
    `check --phase implement` verifies this matches the working copy (plan
    immutability enforcement).
  - `schedule_waves`, `current_wave_index` — persisted by `schedule` for
    cross-run wave resumption.

- Task DAG and wave scheduling — `schedule` reads plan.md, validates the DAG,
  computes topological waves, and persists `plan_hash`, `schedule_waves`,
  `current_wave_index: 0` to `state.json`. Exit non-zero on any DAG error.
- Finding fingerprints — `review record --fingerprint` increments
  `review_retry_count` and `review_round_count`, rotates fingerprint lists.
  `review record --report` increments `review_round_count` only (clean round).
  **Not idempotent** in Phase 1 for findings rounds.
- Attempt recording — `record-attempt --phase implement --cycle-id
  <run_id>:<transition_sequence>` increments `implementation_retry_count` and
  stores the cycle ID in `last_record_attempt_cycle_id`. Idempotent: a second
  call with the same `--cycle-id` returns success without incrementing.
  Called by the skill only after `gates-failed`; not called on successful
  scheduled-wave transitions.
- Iteration and budget gates — `check --phase {implement,review,gates-failed}`
  enforces the bounded counters for that phase or transition. Advisory fields
  are checked but do not block. Plan-phase approval is covered by
  `plan check-current --require-schedule` or `plan check-current`, not
  `check --phase`.

**Verb surface:**
```
loop-cohort init <spec-dir> [--run-id <uuid>]
loop-cohort identity <spec-dir> [--expect-run-id <uuid>] [--json]
loop-cohort check <spec-dir> --phase {implement,review,gates-failed}
loop-cohort approve-plan <spec-dir>
loop-cohort plan check-current <spec-dir> [--require-schedule]
loop-cohort schedule <spec-dir>
loop-cohort record-attempt <spec-dir> --phase implement --cycle-id <id> [--error-fingerprint <hex>]
loop-cohort wave check <spec-dir> --expect {more,last} [--wave-index <n>]
loop-cohort wave advance <spec-dir> --from-index <n>
loop-cohort review inspect <spec-dir> --report <path> [--json]
loop-cohort review record <spec-dir> (--report <path> | --fingerprint <hex>...)
loop-cohort status <spec-dir> [--json]
loop-cohort reset <spec-dir>
loop-cohort worktree preflight|add|record|list|merge|cleanup <spec-dir> [...]
loop-cohort dispatch-decision --branch <b> [--branch <b>...] [--category <c>...] [--base <ref>]
loop-cohort auto-parallel <spec-dir> [--off]
```

**New verbs:**

- **`identity [--expect-run-id <uuid>]`** — read-only. Returns `run_id` and
  `schema_version` from `state.json`. Exit 0 if `state.json` is present; exit
  non-zero if absent. With `--expect-run-id`, additionally exits non-zero if
  the stored `run_id` does not match. Used as the run_id verification preflight
  before every code/spec-plan transition (see Guards) and as the cohort-present
  check during the init preflight.

- **`plan check-current [--require-schedule]`** — read-only. Always verifies:
  `plan_review_status == "approved"`, `approved_spec_hash == sha256(spec.md)`,
  `approved_plan_hash == sha256(plan.md)`. With `--require-schedule`: also
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
  `matches_previous_round` is `true` iff the computed fingerprint set equals
  `state.finding_fingerprints`. The skill uses this as the canonical stasis
  check before routing to `reviewers-clean` or `findings-remain`.

- **`reset`** — deletes only `state.json`. Idempotent: tolerates already-absent.
  Paired with `loop-engine reset` (each owns only its own file). `loop-cohort
  init` refuses if `state.json` is already present (use `reset` to clear first,
  not `--force`).

- **Parallel-wave verbs** (`worktree preflight|add|record|list|merge|cleanup`,
  `dispatch-decision`, `auto-parallel`) are carried over from loop-cohort's
  existing implementation. They are out of scope for this Phase 1 FSM
  specification — the phase-tracker layer does not constrain worktree lifecycle
  beyond the `CODE-IMPLEMENTATION → CODE-VERIFICATION` boundary. A future spec
  will wire worktree sequencing against `wave-complete` and `wave advance`.

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
loop-engine transition <spec-dir> <event>
loop-engine status <spec-dir> [--json]
loop-engine reset <spec-dir>
```

`--help` on every command is the primary documentation.

`init --json` outputs the generated `run_id` as a JSON field. The skill uses
this path to capture the `run_id` for passing to `loop-cohort init`.

`status --json` exposes all `engine-state.json` fields plus a
`pending_human_wait` boolean. This flag is `true` in: `SPEC-PLAN-HUMAN-GATE`,
`CODE-HUMAN-GATE`. It is `false` in all other states.

`reset` — deletes only `engine-state.json`. Idempotent: tolerates
already-absent.

**Exit contract:** exit 0 on success; exit non-zero with a one-line descriptive
message on failure.

**Single-writer contract:** only one caller may issue `transition` calls for a
given `<spec-dir>` at a time.

---

## Initialization and Reset

### Init sequence

At new loop-run initialization (not session resume — a resuming session calls
`status`, not `init`):

**Skill-side preflight:**
1. Skill calls `loop-cohort identity <spec-dir>` — if it exits 0 (cohort already
   initialized), refuse and surface: cohort state exists without engine state, or
   a prior run was not reset. Ask user to run the reset pair.
2. Skill calls `loop-engine init <spec-dir> --mode <mode> --json` — engine checks
   that `engine-state.json` is absent (its own file only), generates `run_id`,
   writes `engine-state.json`, outputs `run_id`.
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

**Corrupt-pair recovery:** any mismatch (one file present, one absent; or
`run_id` mismatch detected by identity check) is resolved by running the reset
pair. Both commands are idempotent, so running them even when one file is
already absent is safe.

**Accepted cost:** reset discards all iteration history, the persisted schedule,
and review fingerprints. A late-phase inconsistency forces a full restart from
the initial drafting state, including the G-plan approval flow. Partial recovery
is not supported in Phase 1.

### run_id verification

For every code/spec-plan transition, the engine runs `loop-cohort identity
<spec-dir> --expect-run-id <run_id>` (where `run_id` is from engine-state.json)
as a mandatory preflight before its event-specific guard. If identity exits
non-zero (file absent, run_id mismatch), the transition is refused with the
identity error.

This is a read-only call and does not violate the A boundary (the engine reads
only through this designated verb, never by directly opening state.json).

---

## Phase FSM: Transition Tables

Two modes in Phase 1. State names embed the phase for readability.

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
      ├── 0. run_id preflight (code/spec-plan):
      │       loop-cohort identity --expect-run-id <run_id>
      │       (refuses non-zero if mismatch or file absent)
      │
      ├── 1. validate event against FSM for current mode × state
      │       (refuses non-zero if invalid)
      │
      ├── 2. fire guard (if one listed in Guards table for this event):
      │       read-only call; refuses non-zero if guard exits non-zero
      │
      └── 3. write new state to engine-state.json
              (increments transition_sequence; records last_event; atomic write)

  LLM skill (after transition returns 0)
      │
      └── invokes loop-cohort verbs explicitly per Explicit Skill Calls

  loop-cohort.py
      │
      └── reads and writes state.json exclusively
          loop-engine reads cohort state only via designated read-only verbs
          (identity, plan check-current, wave check, check --phase)
          [review inspect is skill-invoked preflight, not an engine guard]
```

**Direction is one-way.** loop-engine calls loop-cohort only for read-only verbs.
loop-cohort never calls loop-engine. There is no shared mutable state other than
the immutable `run_id` pair.

---

## Guards

Each transition has at most one event-specific guard (beyond the mandatory
run_id preflight that fires for all code/spec-plan transitions). Guards are
always read-only calls.

| Event | Mode | Current state | Guard call | Purpose |
|---|---|---|---|---|
| `plan-approved` | code | `SPEC-PLAN-HUMAN-GATE` | `loop-cohort plan check-current <spec-dir> --require-schedule` | Verifies approval + schedule bound to current spec.md + plan.md |
| `plan-approved` | spec-plan | `SPEC-PLAN-HUMAN-GATE` | `loop-cohort plan check-current <spec-dir>` | Verifies approval bound to current spec.md + plan.md (no schedule) |
| `wave-complete` | code | `CODE-IMPLEMENTATION` | `loop-cohort check <spec-dir> --phase implement` | Plan immutability (`plan_hash == sha256(plan.md)`); advisory: token budget, same-error |
| `gates-failed` | code | `CODE-VERIFICATION` | `loop-cohort check <spec-dir> --phase gates-failed` | Retry cap: refuses if `implementation_retry_count >= max_implementation_retries` |
| `wave-passed` | code | `CODE-VERIFICATION` | `loop-cohort wave check <spec-dir> --expect more --wave-index <n>` | Mechanically verify more waves remain; index matches persisted state |
| `gates-clean` | code | `CODE-VERIFICATION` | `loop-cohort wave check <spec-dir> --expect last` | Mechanically verify current is the final wave |
| `findings-remain` | code | `CODE-REVIEW` | `loop-cohort check <spec-dir> --phase review` | Review retry cap (`review_retry_count`); advisory: token budget, same-error |
| `reviewers-clean` | code | `CODE-REVIEW` | `check-spec-status.py <spec-dir>` | `**Status:** Shipped` before G-pr |

**`plan check-current` scope (code, `--require-schedule`):** verifies
`plan_review_status == "approved"`, `approved_spec_hash == sha256(spec.md)`,
`approved_plan_hash == sha256(plan.md)`, `plan_hash == approved_plan_hash`,
`schedule_waves` non-empty, `0 <= current_wave_index < len(schedule_waves)`.
Catches spec.md or plan.md edited after approval, or plan.md edited after
scheduling.

**`plan check-current` scope (spec-plan, no flag):** verifies
`plan_review_status == "approved"`, `approved_spec_hash == sha256(spec.md)`,
`approved_plan_hash == sha256(plan.md)`. No schedule check (spec-plan has no
implementation waves). Both spec.md and plan.md are bound to the approval
marker; a post-approval edit to either file causes this guard to refuse.

**`wave-complete` guard scope:** enforces plan immutability (`plan_hash ==
sha256(plan.md)`) — a post-approval edit to plan.md causes this guard to
refuse the transition. Token budget and same-error checks are advisory in Phase 1
(their writers are not yet specified; see State Ownership notes). This guard
does NOT enforce the implementation retry cap — that moves to `gates-failed`.

**`gates-failed` guard scope:** enforces `implementation_retry_count <
max_implementation_retries`. Fires before repair begins. Successful
scheduled-wave executions do NOT consume retry budget — only `gates-failed`
repair cycles do. The cap is global across the run (not per-wave); per-wave cap
is deferred.

**`findings-remain` guard scope:** enforces `review_retry_count <
max_review_retries`. Counts findings-only rounds; clean reviews and
human-blocker round-trips do not consume this budget. Token budget and same-error
checks are advisory in Phase 1.

**`reviewers-clean` in `SPEC-PLAN-REVIEW`** carries no guard — the spec is not
being shipped.

**`check-spec-status.py`** must reuse the same canonical status parser as
`lint-spec-status.py` to avoid an independent regex. The gate fires at the
`CODE-REVIEW → CODE-HUMAN-GATE` edge (before G-pr, not at merge). This means
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

### At new loop-run initialization (not session resume)

```
# Skill preflight:
loop-cohort identity <spec-dir>           # if exit 0, existing cohort state → surface
loop-engine init <spec-dir> --mode <mode> --json   # outputs run_id
loop-cohort init <spec-dir> --run-id <run_id>
```

### Before `plan-approved` — code mode

```
loop-cohort approve-plan <spec-dir>         # sets plan_review_status + approved_plan_hash
loop-cohort schedule <spec-dir>             # validates DAG; persists waves + plan_hash
loop-engine transition <spec-dir> plan-approved   # guard: plan check-current
```

A dependency cycle or missing task from `schedule` aborts the sequence. A
`plan check-current` failure means plan.md was edited between the two calls —
re-run `approve-plan` and `schedule` on the corrected plan.

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
    --cycle-id <run_id>:<transition_sequence> [--error-fingerprint <hex>]
# idempotent: same cycle-id on replay → no increment
```

If a crash occurs between `gates-failed` and `record-attempt`, `last_event:
gates-failed` in engine-state.json tells the resuming session to reissue
`record-attempt` with the same `cycle-id` (idempotent).

### Before `wave-complete` — code mode

`wave-complete` fires when the wave's tasks are built and ready for verification.
No `record-attempt` call at this point.

```
loop-engine transition <spec-dir> wave-complete   # guard: check --phase implement (plan immutability)
```

The guard fires on every `wave-complete` regardless of whether the current entry
was a fresh wave or a `gates-failed` repair. It enforces plan immutability only;
the retry cap is guarded earlier at `gates-failed`.

### After `CODE-VERIFICATION + wave-passed`

The skill supplies `--wave-index <n>` to the engine transition, where `n` is
`current_wave_index` at the time of the call. The engine stores this in
`last_event_context: {completed_wave_index: n}`.

```
loop-engine transition <spec-dir> wave-passed   # guard: wave check --expect more --wave-index <n>
# engine records last_event_context: {completed_wave_index: n}
loop-cohort wave advance <spec-dir> --from-index <n>   # idempotent
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
loop-cohort review record <spec-dir> --report <path>

# If classification == findings (and matches_previous_round == false):
loop-engine transition <spec-dir> findings-remain
loop-cohort review record <spec-dir> --fingerprint <h1> --fingerprint <h2> ...
# (fingerprints come from review inspect --json output)
```

`review record` is not idempotent in Phase 1. Call it once per review round. A
failed call surfaces to the human; do not retry autonomously.

### `blocker-applied` — code mode

No loop-cohort call. A human-returned blocker is not a review round;
`review_retry_count` is not incremented.

---

## Plan Immutability in Phase 1

After `plan-approved`, `plan.md` is immutable for the duration of the run. Any
material change requires full reset (both files) and a new run. In-place
replanning (rerun-schedule, G-plan renewal, wave migration) is deferred from
Phase 1.

`check --phase implement` at `wave-complete` mechanically enforces immutability
by verifying `plan_hash == sha256(plan.md)`. A mismatch refuses the transition
— the run must be reset and restarted from the drafting state, including the
G-plan approval flow. Partial recovery is not supported in Phase 1.

Deferred: in-place plan correction (task rewording, dependency fix) without a
full restart. Supporting it would require a `replan-requested` transition, a
human-wait planning state, rules for preserving or invalidating completed tasks,
schedule migration semantics, and a new approved plan/schedule baseline.

---

## Human Gate Obligations

### G-plan (plan approval)

`plan-approved` fires only after all hold:

1. Adversarial reviewer returned clean on spec/plan. — *Skill obligation.*
2. `loop-cohort approve-plan` was called. — *Mechanically enforced: `plan
   check-current` verifies `plan_review_status == "approved"`.*
3. `loop-cohort schedule` exited 0. — *Mechanically enforced: `plan
   check-current` verifies `schedule_waves` non-empty and `plan_hash` matches.*
4. Both `approved_plan_hash` and `plan_hash` equal `sha256(plan.md)`. —
   *Mechanically enforced: `plan check-current`.*
5. Human G-plan sign-off received. — *Skill obligation; not mechanically
   enforced.*

### G-pr (code review and merge)

`done` and `blocker-applied` carry no mechanical guard. `done` must not be
fired without a confirmed merge. A merge-verification guard is deferred.

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
| `state.json` | loop-cohort | `run_id`, `schema_version`, `feature`, `plan_review_status`, `approved_spec_hash`, `approved_plan_hash`, `review_round_count`, `review_retry_count`, `max_review_retries`, `implementation_retry_count`, `max_implementation_retries`, `last_record_attempt_cycle_id`, `token_budget_used_pct`†, `token_budget_cap_pct`†, `consecutive_same_error_count`†, `consecutive_same_error_threshold`†, `finding_fingerprints`, `previous_finding_fingerprints`, `auto_parallel`, `last_commit_sha`, `worktrees`, `plan_hash`, `schedule_waves`, `current_wave_index` |
| `engine-state.json` | loop-engine | `schema_version`, `run_id`, `feature`, `mode`, `state`, `last_event`, `last_event_context`, `transition_sequence`, `last_transition_at` |

*† Advisory in Phase 1: no Phase 1 writer defined.*

**`run_id`** is an immutable UUID generated at `loop-engine init`. Both files
carry it; every transition verifies the pair via `loop-cohort identity`.

**`feature`** is an immutable slug independently derived from the spec-dir
basename. Never written by one script and read by the other.

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

**Pre-plan loop** (LLM-judged, no cohort cap):
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
    │  guard: check --phase implement (plan immutability)
    ▼
CODE-VERIFICATION
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
   begins (not after), so a refused fifth `gates-failed` back-edge means four
   complete repair cycles have been attempted. `check --phase implement` at
   `wave-complete` enforces plan immutability only.
3. **Stasis** — `review inspect` returns `matches_previous_round: true`; skill
   surfaces to human without advancing the FSM.
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

**Session resume rule:** a resuming session calls `loop-engine status --json` to
read the current phase and `last_event`. It does not call `loop-engine init`.
If `pending_human_wait` is true, wait for the human signal. The `last_event`
field disambiguates the five inbound paths to `CODE-IMPLEMENTATION` so the
resuming session knows what repair or advancement action is expected.

Work product must be committed to a named branch or open PR before ending a
session in a human-wait state.

---

## Session Resumption

On resume, the agent:

1. Calls `loop-engine status --json <spec-dir>` → reads `state`, `last_event`,
   `pending_human_wait`.
2. Calls `loop-cohort status --json <spec-dir>` → reads `current_wave_index`,
   `schedule_waves`, `finding_fingerprints`, `review_retry_count`,
   `implementation_retry_count`.
3. If `pending_human_wait` → wait for the human signal before firing any exit event.
4. If `state == CODE-IMPLEMENTATION` and `last_event == wave-passed` → extract
   `completed_wave_index` from `last_event_context`; reissue `loop-cohort wave
   advance <spec-dir> --from-index <completed_wave_index>` (idempotent; safe in
   both crash windows — before or after the advance completed).
5. If `state == CODE-VERIFICATION` → `wave-passed` vs `gates-clean` is now
   mechanically guarded; re-run gates and fire the appropriate event.

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
`wave-complete` now enforces only plan immutability.

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
   mismatched `run_id` refuses.

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
   - **plan mutation after some waves completed** — advance two waves; mutate
     plan.md; verify `wave-complete` guard refuses.
   - **plan mutation after final `wave-complete` but before `gates-clean`** — verify
     `wave-complete` guard refuses at `CODE-VERIFICATION`.
   - **stasis detection** — write known fingerprints to `state.json`; verify
     `review inspect --json` returns `matches_previous_round: true`; verify an
     empty-vs-empty comparison returns `matches_previous_round: false`.

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
│   ├── check-spec-status.py         # spec Status=Shipped gate (proposed)
│   ├── test-loop-engine.py          # proposed test file (FSM, guard, init/reset, stasis)
│   ├── lint-spec-status.py          # spec metadata drift linter (CI/on-demand)
│   └── lint-traceability.py         # traceability matrix linter
├── assets/
│   └── state.json                   # loop-cohort state template
└── references/
    └── state-schema.md              # state.json field reference
```

`engine-state.json` has no template file — its fields and allowed values are
fully specified in this document and in `loop-engine --help` output.

The agent-facing quick-reference (`references/loop-infrastructure.md`) and its
projections into `.agents/` and `.claude/` will land alongside the implementation.

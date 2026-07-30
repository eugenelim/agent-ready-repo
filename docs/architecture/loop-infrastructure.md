# Loop Infrastructure

**Status:** Proposed  
**Implementation:** Not yet landed — implementation pending replanning after this design is ratified.  
**Supersedes:** PR #816 design.

The work-loop skill's phase sequencing and task execution are implemented by
two scripts. This document defines the boundary between them so future
maintainers have a single reference rather than reconstructing it from code.

**Design choice — Phase 1:** Option A (pure phase tracker). The engine validates
legal phase ordering and runs read-only guards. All loop-cohort mutations are
invoked explicitly by the skill. Option B (workflow orchestrator with durable
side-effect semantics) is deferred until `review record` supports idempotency
keys — see [Future Phase: Workflow Orchestrator](#future-phase-workflow-orchestrator-b).

**FSM** = Finite State Machine throughout this document.

For the mode table (light vs. full, and which full-mode flows use loop-cohort),
see [`packs/core/DESIGN.md §3`](../../packs/core/DESIGN.md).

---

## Scripts

### loop-cohort.py

**Role:** Task execution state owner.

**Source:** `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`  
**Projects to:** `.claude/skills/work-loop/scripts/loop-cohort.py`

**What it owns:**

- `state.json` — the session-local state file written into each spec directory.
  See `references/state-schema.md` for the full field reference. Schema includes:
  `run_id`, `schema_version`, `feature`, `plan_review_status`, `iteration_count`,
  `max_iterations`, `token_budget_used_pct`, `token_budget_cap_pct`,
  `consecutive_same_error_count`, `consecutive_same_error_threshold`,
  `finding_fingerprints`, `previous_finding_fingerprints`, `auto_parallel`,
  `last_commit_sha`, `worktrees`, `plan_hash`, `schedule_waves`,
  `current_wave_index`.
  - `finding_fingerprints`: fingerprints from the most recent review round,
    rotated by `review record`. The stasis pre-flight compares incoming
    fingerprints against this field.
  - `previous_finding_fingerprints`: fingerprints from the round before the
    most recent, retained for audit and stasis-history purposes.
- `plan_hash` + `schedule_waves` + `current_wave_index` — persisted by
  `loop-cohort schedule` so that a resuming session can reconstruct wave position
  without re-reading plan.md or re-running the scheduler.
- Task DAG and wave scheduling — `schedule` reads plan.md, validates the DAG
  (no missing tasks or dependency cycles), computes topological waves, and
  persists the result to `state.json`. Exit non-zero on any DAG error. The skill
  must verify exit 0 before firing `loop-engine transition plan-approved`.
- Finding fingerprints — `review record` parses reviewer output, computes
  `sha1("<file>|<line>|<title>")` per finding, and rotates fingerprint lists
  to enable stasis detection. **Not idempotent** — each call increments
  `iteration_count`. Phase 1 callers are the skill; see
  [Future Phase](#future-phase-workflow-orchestrator-b) for idempotency-key support.
- Attempt recording — `record-attempt --phase implement` increments
  `iteration_count` and updates `consecutive_same_error_count` for the
  implementation phase. Called by the skill before firing `wave-complete` so
  that `check --phase implement` can enforce the iteration cap. Without this
  call, the implementation loop is bounded only by token budget.
- Iteration and budget gates — `check --phase {plan,implement,review}` reads
  `state.json` and enforces: plan-approval status, iteration cap, token-budget
  cap, and consecutive-same-error threshold.
- Worktree lifecycle — `worktree preflight/add/record/list/merge/cleanup`.

**Verb surface:**
```
loop-cohort init <spec-dir> [--run-id <uuid>] [--force]
loop-cohort check <spec-dir> --phase {plan,implement,review}
loop-cohort approve-plan <spec-dir>
loop-cohort schedule <spec-dir>
loop-cohort record-attempt <spec-dir> --phase implement
loop-cohort review record <spec-dir> (--report <path> | --fingerprint <hex>...)
loop-cohort status <spec-dir> [--json]
loop-cohort worktree preflight|add|record|list|merge|cleanup <spec-dir> [...]
loop-cohort dispatch-decision --branch <b> [--branch <b>...] [--category <c>...] [--base <ref>]
loop-cohort auto-parallel <spec-dir> [--off]
```

`status --json` exposes all `state.json` fields plus any computed views the
skill needs (e.g., whether more waves remain). This is the canonical read path
for skill pre-flight checks including stasis detection and wave routing.

**Exit contract:** exit 0 on success; exit non-zero with a one-line reason on
stderr on failure. `check --phase plan` exits 1 with "plan not approved" on
first invocation — expected cue for the pre-EXECUTE reviewer, not an error.

---

### loop-engine.py

**Role:** Phase FSM validator (Option A — Phase 1).

The engine validates legal phase ordering, runs the read-only guard for each
transition, and records the current phase in `engine-state.json`. It does not
invoke loop-cohort mutations. The skill invokes all mutations explicitly.

**A guarantees** legal phase ordering and the mechanically checked preconditions
listed in the Guards table. It does not prove the truth of unguarded event
assertions (`done`, `gates-clean`, `wave-passed`, `doc-approved`, and others
carry no mechanical evidence check) or the completion of any post-transition
operation the skill performs.

**Source:** `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`  
**Projects to:** `.claude/skills/work-loop/scripts/loop-engine.py`

**What it owns:**

- `engine-state.json` — the session-local phase record. Schema:
  ```json
  {
    "schema_version": 1,
    "run_id": "<UUID generated at init>",
    "feature": "<slug>",
    "mode": "code | spec-plan | doc",
    "state": "<phase name — see transition tables below>",
    "last_transition_at": "<ISO-8601 UTC>"
  }
  ```
- Phase FSM — per-mode transition tables (see below). Events not in the table
  for the current mode × state pair are refused with a non-zero exit.
- Transition execution — reads `engine-state.json`, validates the event, fires
  the guard if one exists, writes the new state atomically (tempfile +
  `os.replace`).

**Verb surface:**
```
loop-engine init <spec-dir> --mode {code|spec-plan|doc}
loop-engine transition <spec-dir> <event>
loop-engine status <spec-dir> [--json]
loop-engine reset <spec-dir>
```

`--help` on every command is the primary documentation.

`status --json` exposes all `engine-state.json` fields plus a
`pending_human_wait` boolean. This flag is `true` in any of:
`SPEC-PLAN-HUMAN-GATE`, `CODE-HUMAN-GATE`, `DOC-EXTERNAL-REVIEW-WAIT`,
`DOC-HUMAN-GATE`. It is `false` in all other states, including
`DOC-INTERNAL-REVIEW`.

**Exit contract:** exit 0 on success; exit non-zero with a one-line descriptive
message on failure (invalid transition, guard refused, file absent, etc.).

**Single-writer contract:** only one caller may issue `transition` calls for a
given `<spec-dir>` at a time. `os.replace` provides atomic individual writes
but not serialized read-modify-write. In supervisor mode the barrier-wait
discipline guarantees this. Do not issue concurrent `transition` calls on the
same spec-dir.

---

## Initialization Invariants

`loop-engine init <spec-dir> --mode <mode>` is responsible for writing
`engine-state.json` only. It does **not** write `state.json` — that remains
loop-cohort's exclusive domain. The skill calls `loop-cohort init` immediately
after `loop-engine init` to complete the pair.

**Init sequence (code and spec-plan modes):**

1. Skill calls `loop-engine init <spec-dir> --mode <mode>`.
2. Engine preflight: refuse if `engine-state.json` already exists; refuse if
   `state.json` already exists (indicates a prior cohort run without cleanup).
   Both must be absent for a clean start. If either is present, emit a
   descriptive refusal naming the present file.
3. Engine generates `run_id` (UUID), writes `engine-state.json`, and outputs
   the `run_id` on stdout (or as a field in `--json` output).
4. Skill captures `run_id` from step 3 and calls
   `loop-cohort init <spec-dir> --run-id <run_id>`.
5. Cohort writes `state.json` with the same `run_id`.

**Init sequence (doc mode):**

Doc mode does not use loop-cohort. `loop-engine init` checks only that
`engine-state.json` is absent; it does not check or create `state.json`.
The "one present, one absent" corrupt-pair check is scoped to `code` and
`spec-plan` modes only.

**`run_id` across files (code and spec-plan):** both `engine-state.json` and
`state.json` carry the same `run_id`. All operations verify the pair match
before proceeding; a mismatch surfaces a corrupt-state error and halts.

**`loop-engine reset <spec-dir>`** deletes both `engine-state.json` and
`state.json`, in that order: delete `state.json` first (cohort's store), then
`engine-state.json`. If either deletion fails, leave the remaining file intact,
emit an error, and halt — partial deletion is never silently swallowed. On
success, both files are absent and `loop-engine init` may run. For `doc` mode,
reset deletes only `engine-state.json`.

**Corrupt-pair recovery:** `reset` attempts deletion of both files regardless
of the pair's internal consistency (one present, one absent; `run_id` mismatch;
either file malformed). Any present file is deleted; absent files are tolerated
as already-clean.

**Accepted cost:** reset is all-or-nothing. A late-phase inconsistency forces a
full restart from the initial drafting state, including the G-plan approval
flow. Partial recovery is not supported in Phase 1.

---

## Phase FSM: Transition Tables

Three modes. State names embed the phase for readability.

Legal states per mode:

- **code:** `SPEC-PLAN-DRAFTING`, `SPEC-PLAN-REVIEW`, `SPEC-PLAN-HUMAN-GATE`,
  `CODE-IMPLEMENTATION`, `CODE-VERIFICATION`, `CODE-REVIEW`, `CODE-HUMAN-GATE`,
  `DONE`
- **spec-plan:** `SPEC-PLAN-DRAFTING`, `SPEC-PLAN-REVIEW`, `SPEC-PLAN-HUMAN-GATE`,
  `DONE`
- **doc:** `DOC-DRAFTING`, `DOC-INTERNAL-REVIEW`, `DOC-EXTERNAL-REVIEW-WAIT`,
  `DOC-HUMAN-GATE`, `DONE`

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

**`wave-passed` vs `gates-clean` routing arithmetic:**  
At `CODE-VERIFICATION`, read `current_wave_index` and `schedule_waves` from
`loop-cohort status --json`. `current_wave_index` holds the index of the wave
just completed (zero-based).
- `current_wave_index == len(schedule_waves) - 1` → all waves done → fire
  `gates-clean`.
- `current_wave_index < len(schedule_waves) - 1` → more waves remain → fire
  `wave-passed`.

After `wave-passed`, the skill increments `current_wave_index` via the
designated loop-cohort verb and proceeds to the next wave group.

### spec-plan

spec-plan reuses the first three code-mode states and terminates at
`SPEC-PLAN-HUMAN-GATE`. This review cycle bypasses loop-cohort mutation calls.

| Current state | Event | Next state |
|---|---|---|
| `SPEC-PLAN-DRAFTING` | `spec-ready` | `SPEC-PLAN-REVIEW` |
| `SPEC-PLAN-REVIEW` | `reviewers-clean` | `SPEC-PLAN-HUMAN-GATE` |
| `SPEC-PLAN-REVIEW` | `findings-remain` | `SPEC-PLAN-DRAFTING` |
| `SPEC-PLAN-HUMAN-GATE` | `plan-approved` | `DONE` |
| `SPEC-PLAN-HUMAN-GATE` | `plan-rejected` | `SPEC-PLAN-DRAFTING` |

### doc

`doc` mode covers RFC, ADR, architecture doc, and any other review-and-approve
document. Two review states distinguish whether the review round is handled
autonomously by the LLM or requires waiting for a human reviewer.

| Current state | Event | Next state |
|---|---|---|
| `DOC-DRAFTING` | `doc-ready` | `DOC-INTERNAL-REVIEW` |
| `DOC-DRAFTING` | `doc-ready-external` | `DOC-EXTERNAL-REVIEW-WAIT` |
| `DOC-INTERNAL-REVIEW` | `reviewers-clean` | `DOC-HUMAN-GATE` |
| `DOC-INTERNAL-REVIEW` | `findings-remain` | `DOC-DRAFTING` |
| `DOC-EXTERNAL-REVIEW-WAIT` | `reviewers-clean` | `DOC-HUMAN-GATE` |
| `DOC-EXTERNAL-REVIEW-WAIT` | `findings-remain` | `DOC-DRAFTING` |
| `DOC-HUMAN-GATE` | `doc-approved` | `DONE` |
| `DOC-HUMAN-GATE` | `doc-returned` | `DOC-DRAFTING` |

`DOC-EXTERNAL-REVIEW-WAIT` is a human-wait state (see Human-Wait States below).
`DOC-INTERNAL-REVIEW` is not — the LLM runs review and may fire the exit event
autonomously.

---

## Interaction Model (Option A)

```
  LLM skill
      │
      │ loop-engine transition <spec-dir> <event>
      ▼
  loop-engine.py
      │
      ├── 1. validate event against FSM for current mode × state
      │       (refuses non-zero if invalid)
      │
      ├── 2. fire guard (if one listed in Guards table for this event):
      │       read-only call against loop-cohort or standalone script
      │       (refuses non-zero if guard exits non-zero)
      │
      └── 3. write new state to engine-state.json
              (atomic: tempfile + os.replace)

  LLM skill (after transition returns 0)
      │
      └── invokes loop-cohort verbs explicitly per skill instructions
          (see Explicit Skill Calls below)

  loop-cohort.py
      │
      └── reads and writes state.json exclusively
          loop-engine never reads or writes state.json
```

**Direction is one-way.** loop-engine calls loop-cohort only for read-only
guards during transitions. loop-cohort never calls loop-engine. There is no
shared mutable state other than the immutable `run_id` pair.

---

## Guards

Each transition has at most one guard. Guards are always read-only calls — they
may not write to either state file. Guards fire in step 2, before the state
write (step 3).

| Event | Mode | Current state | Guard call | Purpose |
|---|---|---|---|---|
| `plan-approved` | code, spec-plan | `SPEC-PLAN-HUMAN-GATE` | `loop-cohort check <spec-dir> --phase plan` | Verifies `approve-plan` was called |
| `wave-complete` | code | `CODE-IMPLEMENTATION` | `loop-cohort check <spec-dir> --phase implement` | Iteration cap, token budget, consecutive-same-error |
| `findings-remain` | code | `CODE-REVIEW` | `loop-cohort check <spec-dir> --phase review` | Iteration cap, token budget, consecutive-same-error |
| `reviewers-clean` | code | `CODE-REVIEW` | `check-spec-status.py <spec-dir>` | `**Status:** Shipped` in working tree before G-pr |

**`wave-complete` guard scope:** `check --phase implement` enforces iteration
cap, token budget, and consecutive-same-error threshold. It does **not** check
fingerprint stasis — stasis applies to review rounds only (see Stasis Detection).
These counters are incremented by `record-attempt --phase implement` (see
Explicit Skill Calls); without that call, `check --phase implement` sees stale
counters and the iteration cap is inert.

**`findings-remain` guard scope:** `check --phase review` enforces the same
three counters for review rounds. Stasis is handled by the skill pre-flight
(see Stasis Detection), not by this guard.

**`plan-approved` guard ordering:** `loop-cohort check --phase plan` exits 0
only when `plan_review_status != "pending"`, set exclusively by
`loop-cohort approve-plan`. Call `approve-plan` before firing this transition;
the guard verifies that it ran.

**`reviewers-clean` in `SPEC-PLAN-REVIEW`** carries no guard — the spec is not
being shipped and a stasis check must not block a legitimate clean exit.

**`check-spec-status.py`** lives alongside loop-engine.py. It verifies the
spec's `**Status:**` field reads exactly `Shipped`. It is a separate script
from `lint-spec-status.py` (CI drift linter). The optimistic in-PR update
(spec status = `Shipped` in the PR diff) is intentional: the PR proposes to
ship, and the spec update is part of that proposal. It must reuse the same
canonical status parser as `lint-spec-status.py` rather than introduce an
independent regex.

**Stasis detection (immediate):** before firing `findings-remain`, the skill
must compare the current round's computed fingerprints against
`state.finding_fingerprints` (read via `loop-cohort status --json`). If they
match, the finding set is unchanged from the previous round; the skill must
surface stasis to the human rather than advancing the FSM. Only if they differ
should the skill fire `findings-remain` and subsequently call `review record`.
This detects stasis at the point it occurs, not one round later.

**`findings-remain` floor:** at least one fingerprint hash must be present. A
review round with no hashable findings fires `reviewers-clean` instead.

---

## Explicit Skill Calls

In Option A, the skill invokes loop-cohort verbs at defined points. These are
skill obligations documented here so that future implementers can verify the
engine and skill are consistent. The engine does not invoke these.

### At session start — code and spec-plan modes only

```
loop-engine init <spec-dir> --mode <mode>          # writes engine-state.json, outputs run_id
loop-cohort init <spec-dir> --run-id <run_id>      # writes state.json with matching run_id
```

The skill captures `run_id` from `loop-engine init` stdout (or `--json` output)
and passes it to `loop-cohort init`. Doc mode uses only `loop-engine init`;
`loop-cohort init` is not called.

### Before `plan-approved` — code mode only

```
loop-cohort approve-plan <spec-dir>         # sets plan_review_status
loop-cohort schedule <spec-dir>             # validates DAG; persists waves to state.json
loop-engine transition <spec-dir> plan-approved
```

`schedule` validates the task DAG and persists `plan_hash`, `schedule_waves`,
and `current_wave_index` to `state.json`. The skill must verify exit 0 before
firing the transition. A dependency cycle or missing task aborts the sequence —
do not advance the FSM with an invalid schedule.

`schedule` does not mutate `plan_review_status`, `finding_fingerprints`, or any
counter fields. It is read-validate-persist, not a review mutation.

**spec-plan mode does not call `schedule`** — spec-plan terminates at
`plan-approved → DONE` and has no implementation task DAG to compute.

### Before `wave-complete` — code mode

```
loop-cohort record-attempt <spec-dir> --phase implement  # increments iteration counters
loop-engine transition <spec-dir> wave-complete          # guard: check --phase implement
```

Also call `record-attempt` before each retry after `gates-failed` so that a
persistent build failure eventually trips the iteration cap. Without this call,
the implementation loop is bounded only by token budget.

### After `CODE-REVIEW + reviewers-clean` — code mode

```
loop-engine transition <spec-dir> reviewers-clean   # guard: check-spec-status.py
loop-cohort review record <spec-dir> --report <path>
```

### After `CODE-REVIEW + findings-remain` — code mode (only after stasis pre-flight passes)

```
loop-engine transition <spec-dir> findings-remain
loop-cohort review record <spec-dir> --fingerprint <h1> --fingerprint <h2> ...
```

`review record` is not idempotent. Call it once per review round. A failed call
surfaces to the human for manual reconciliation; do not retry autonomously.

### After `CODE-VERIFICATION + wave-passed` — code mode

Increment `current_wave_index` in `state.json` via the designated loop-cohort
verb (to be named at implementation time). Then read the updated index to
determine the next task group.

### `blocker-applied` — code mode

No loop-cohort call. A human-returned blocker is not an LLM review round;
`iteration_count` is not incremented.

---

## Human Gate Obligations

The following events require explicit human action before the LLM may fire them.
Mechanical enforcement is noted per event.

### G-plan (plan approval)

`plan-approved` fires only after all hold:

1. Adversarial reviewer returned clean on spec/plan. — *Skill obligation; not
   mechanically enforced.*
2. `loop-cohort approve-plan` was called. — *Mechanically enforced: the
   `plan-approved` guard exits non-zero if this has not run.*
3. `loop-cohort schedule` exited 0 (valid DAG, waves persisted). — *Skill
   obligation; not mechanically enforced by the engine guard.*
4. Human G-plan sign-off received. — *Skill obligation; not mechanically
   enforced.*

### G-pr (code review and merge)

`done` and `blocker-applied` carry **no mechanical guard**. `done` must not be
fired without a confirmed merge. This is enforced by skill convention. A
merge-verification guard (checking PR merge status via the GitHub API) would
make this mechanical but introduces an external-system dependency; deferred.

```
CODE-REVIEW → reviewers-clean → CODE-HUMAN-GATE
              (check-spec-status        │
               guard fires here)        │ LLM presents PR for human G-pr review
                                        │
                ┌───────────────────────┴────────────────────────┐
                │ Human approves and PR merges                   │ Human returns blocker
                ▼                                                 ▼
             done → DONE                        blocker-applied → CODE-IMPLEMENTATION
                                          (fix applied, gates re-run before re-review)
```

For `doc` mode, governance steps (RFC approver sign-off, ADR record) are not
replaced by loop-engine; the engine tracks phase state only.

---

## State Ownership

No field is shared as mutable state between the two files.

| File | Owner | Key fields |
|---|---|---|
| `state.json` | loop-cohort | `run_id`, `schema_version`, `feature`, `plan_review_status`, `iteration_count`, `max_iterations`, `token_budget_used_pct`, `token_budget_cap_pct`, `consecutive_same_error_count`, `consecutive_same_error_threshold`, `finding_fingerprints`, `previous_finding_fingerprints`, `auto_parallel`, `last_commit_sha`, `worktrees`, `plan_hash`, `schedule_waves`, `current_wave_index` |
| `engine-state.json` | loop-engine | `schema_version`, `run_id`, `feature`, `mode`, `state`, `last_transition_at` |

**`run_id` in both files** (code and spec-plan modes) is an immutable UUID
generated at `loop-engine init` and written to both files during initialization.
All operations verify the pair matches before proceeding.

**`feature`** is an immutable slug independently derived from the spec-dir
basename in both files. Never written by one script and read by the other.

**`max_iterations`** is owned exclusively by loop-cohort. loop-engine has no
access to `state.json`. When loop-cohort signals an iteration cap, the LLM
exercises judgment per the SKILL.md's termination guidance.

Both files are session-local and gitignored.

---

## Coordination by Mode

| Mode | loop-cohort guards | spec-status guard | Skill explicit calls |
|---|---|---|---|
| `code` | `plan-approved` (SPEC-PLAN-HUMAN-GATE), `wave-complete` (CODE-IMPLEMENTATION), `findings-remain` (CODE-REVIEW) | `reviewers-clean` at CODE-REVIEW | `init` pair, `approve-plan` + `schedule` before `plan-approved`, `record-attempt` before each `wave-complete`, `review record` after each CODE-REVIEW transition |
| `spec-plan` | `plan-approved` (SPEC-PLAN-HUMAN-GATE) | — | `init` pair, `approve-plan` before `plan-approved` |
| `doc` | — | — | engine `init` only; no loop-cohort |

**Light mode** does not invoke loop-engine or loop-cohort.

---

## Convergence Loops

### code mode

**Pre-plan loop** (bounded by LLM judgment — no loop-cohort cap):
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

**Code loop (multi-wave + review, bounded by loop-cohort):**
```
CODE-IMPLEMENTATION
    │  (skill: record-attempt --phase implement)
    │  wave-complete (guard: check --phase implement)
    ▼
CODE-VERIFICATION
    ├── wave-passed ─────────────────────────────────────────► CODE-IMPLEMENTATION
    │     (current_wave_index < len(schedule_waves) - 1)          (next wave)
    ├── gates-clean ─────────────────────────────────────────► CODE-REVIEW
    │     (current_wave_index == len(schedule_waves) - 1)
    └── gates-failed ────────────────────────────────────────► CODE-IMPLEMENTATION
                                                               (skill: record-attempt
                                                                before retry's wave-complete)
CODE-REVIEW
    ├── reviewers-clean (guard: check-spec-status.py) ──► CODE-HUMAN-GATE
    │     (skill: review record --report after)               │
    │                                                  done   │  blocker-applied
    │                                                   ▼     ▼
    │                                                  DONE   CODE-IMPLEMENTATION
    └── findings-remain (guard: check --phase review)
          (skill: stasis pre-flight, then review record --fingerprints after)
          │
          ▼
    CODE-IMPLEMENTATION ← back-edge
```

**Termination mechanisms** (in `state.json`; loop-engine has no access):

1. **Iteration cap** — `check --phase implement/review` exits non-zero when
   `iteration_count >= max_iterations`. LLM exercises judgment: surface to
   human with a concrete reason to continue, or accept the cap.
2. **Stasis** — skill detects before `findings-remain` when incoming
   fingerprints equal `state.finding_fingerprints`; surfaces to human.
3. **Token budget** — `check --phase implement/review` exits non-zero when
   `token_budget_used_pct >= token_budget_cap_pct`.
4. **Consecutive-same-error** — `check --phase implement/review` exits non-zero
   when `consecutive_same_error_count >= consecutive_same_error_threshold`.

The loop cannot self-terminate beyond `DONE` — `done` must be fired explicitly
after human G-pr approval.

### spec-plan and doc modes

Both converge via `findings-remain → *-DRAFTING` back-edges, bounded by LLM
judgment. `DOC-HUMAN-GATE` has a `doc-returned → DOC-DRAFTING` back-edge for
when a human approver returns the document for revision after internal review
is clean.

---

## Human-Wait States and Session Boundaries

| State | Mode | Work product committed | Waiting for |
|---|---|---|---|
| `SPEC-PLAN-HUMAN-GATE` | code, spec-plan | spec.md + plan.md on branch/PR | Human G-plan sign-off |
| `CODE-HUMAN-GATE` | code | implementation PR | Human G-pr (merge or blocker) |
| `DOC-EXTERNAL-REVIEW-WAIT` | doc | document on branch/PR | Human async reviewer |
| `DOC-HUMAN-GATE` | doc | document on branch/PR | Human doc approval |

`DOC-INTERNAL-REVIEW` is **not** a human-wait state; the LLM may fire
`reviewers-clean` or `findings-remain` autonomously.

**Resumption rule:** a resuming session reads `loop-engine status --json
<spec-dir>` to recover the current phase. If `pending_human_wait` is true, wait
for the human signal before firing any exit event. Work product must be on a
named branch or open PR before ending a session in a human-wait state.

---

## Session Resumption

`last_transition_at` enables cross-session recovery without reconstructing state
from chat history. On resume:

1. `loop-engine status --json <spec-dir>` — current phase, `pending_human_wait`.
2. `loop-cohort status --json <spec-dir>` — `current_wave_index`, `schedule_waves`,
   `finding_fingerprints`, iteration counts.
3. If in a human-wait state — wait for the human signal.
4. If in `CODE-VERIFICATION` — apply the `wave-passed` vs `gates-clean` routing
   arithmetic (see Phase FSM: code). Re-run gates for the current wave before
   firing either.

**Stale-worker detection** (INI-003): `loop-engine status --json <spec-dir>`
exposes `last_transition_at`; a supervisor compares it against a threshold it
owns. Loop-engine makes no assumption about per-phase expected duration.

---

## Future Phase: Workflow Orchestrator (B)

Phase 2 adds the orchestration layer once the following are in place:

- `loop-cohort review record` accepts a `--transition-id <uuid>` and
  deduplicates: a previously applied ID returns exit 0 without incrementing
  counters. This makes `review record` idempotent and safe to retry.
- `engine-state.json` carries a structured `pending_transition` object:
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
  The committed state remains the **source** state until the required effect
  is confirmed. Any unresolved `pending_transition` blocks all new transitions.
- `run_id` and `schema_version` propagate through all pending-transition records.
- The loop-engine and loop-cohort both carry `schema_version` with a documented
  upgrade path.

With idempotency keys, a crash between the side-effect call and the confirmation
write is recoverable by re-issuing the same `--transition-id`; the cohort
deduplicates and confirms. Without them, the current Phase 1 (skill-explicit,
non-automated mutations) is the correct choice.

---

## Alternatives Considered

### A-only (Phase 1) vs B-with-proper-guarantees now

B requires a durable `pending_transition` schema, idempotency keys on all
mutations, target-state-committed-only-after-effect, `run_id` coupling across
files, and persisted wave state. All are achievable but represent a design and
implementation surface roughly twice what Phase 1 requires. Phase 1 delivers
legal ordering, guard enforcement, resumption, and multi-wave phase structure —
nearly all the useful determinism. B is added after `review record` is
idempotent rather than building distributed-transaction machinery for three
mutation rows.

### `schedule` as side effect vs. pre-transition precondition

Under a side-effect model, a plan with a dependency cycle first moves the
engine to `CODE-IMPLEMENTATION` then fails scheduling — the FSM says
implementation has begun while no valid schedule exists. Making schedule a
pre-transition skill obligation (call it; verify exit 0; only then fire
`plan-approved`) means `CODE-IMPLEMENTATION` is *intended* to be semantically
complete: a valid schedule exists and is persisted in `state.json`, contingent
on the skill honoring the obligation (the engine guard does not mechanically
enforce a persisted schedule). `schedule` is read-validate-persist, not a
review mutation, so it fits naturally as a precondition rather than a post-commit
side effect.

### DOC states vs. `review_actor` field

A `review_actor: "llm" | "human"` field in `engine-state.json` works but requires
callers to parse a field to determine whether to wait. Separate FSM states
(`DOC-INTERNAL-REVIEW`, `DOC-EXTERNAL-REVIEW-WAIT`) encode the wait condition in
the state name itself, making resumption logic unambiguous without field parsing.

### Optimistic concurrency vs. single-writer contract

Optimistic concurrency (compare `last_transition_at` before `os.replace`) would
handle concurrent callers on the same spec-dir. The single-writer contract is
sufficient given that supervisor mode enforces barrier-wait. Add optimistic
concurrency if a use case arises where the contract cannot be honoured.

---

## Testing

Four independent test layers:

1. **FSM table tests:** for each mode, enumerate all legal transitions and verify
   the correct next state; enumerate illegal event/state pairs and verify non-zero
   exit with no file mutation.

2. **Guard-refusal tests:** stub each guard to exit non-zero; verify the
   transition is refused and `engine-state.json` is unchanged; verify the guard
   receives the correct arguments.

3. **`run_id` coupling and init/reset tests:** verify that `init` with one file
   already present refuses; verify that `transition` with mismatched `run_id`
   across files refuses; verify that `reset` followed by `init` succeeds; verify
   corrupt-pair recovery across all mismatch orientations.

4. **Stasis and wave-advancement tests:** write known fingerprints to `state.json`;
   verify the skill's stasis pre-flight logic detects a match; verify
   `wave-passed` vs `gates-clean` routing arithmetic from `current_wave_index`.

Tests live at `packs/core/.apm/skills/work-loop/scripts/test-loop-engine.py`.

---

## Source Tree

```
packs/core/.apm/skills/work-loop/
├── SKILL.md                         # skill entry point (LLM reads this)
├── scripts/
│   ├── loop-cohort.py               # task execution state owner
│   ├── loop-engine.py               # phase FSM validator (proposed — Phase 1)
│   ├── check-spec-status.py         # spec Status=Shipped gate (proposed)
│   ├── test-loop-engine.py          # FSM, guard, init/reset, wave/stasis tests
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
projections into `.agents/` and `.claude/` will land alongside the implementation,
not with this proposal.

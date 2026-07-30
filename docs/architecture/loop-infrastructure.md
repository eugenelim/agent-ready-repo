# Loop Infrastructure

The work-loop skill's phase sequencing and task execution are implemented by
two scripts. This document defines the boundary between them so future
maintainers have a single reference rather than reconstructing it from code.

**FSM** = Finite State Machine throughout this document.

For the mode table (light vs. full, and which full-mode flows use loop-cohort),
see [`packs/core/DESIGN.md §3`](../../packs/core/DESIGN.md). The
code/spec-plan/doc coordination table is local to this document.

---

## Scripts

### loop-cohort.py

**Role:** Task execution state owner.

**Source:** `packs/core/.apm/skills/work-loop/scripts/loop-cohort.py`
**Projects to:** `.claude/skills/work-loop/scripts/loop-cohort.py` (via
`make build-self`)

**What it owns:**

- `state.json` — the session-local state file written into each spec directory.
  Schema: iteration count, max-iterations cap, token budget, plan-review status,
  finding fingerprints, worktree list, and the `auto_parallel` flag. See
  `references/state-schema.md` for the full field reference.
- Task DAG and wave scheduling — reads the plan's `Depends on:` graph, produces
  topological order, and enforces the parallel-write gate (`dispatch-decision`).
- Worktree lifecycle — `worktree preflight/add/record/list/merge/cleanup` for
  parallel implementer fan-out.
- Finding fingerprints — `review record` parses reviewer output, computes
  `sha1("<file>|<line>|<title>")` per finding, and rotates fingerprint lists
  to enable stasis detection.
- Iteration and budget gates — `check --phase {plan,implement,review}` reads
  `state.json` and enforces: plan-approval status, iteration cap and token-budget
  cap, fingerprint stasis, and consecutive-same-error threshold.

**Verb surface:**
```
loop-cohort init <spec-dir>
loop-cohort check <spec-dir> --phase {plan,implement,review}
loop-cohort approve-plan <spec-dir>
loop-cohort schedule <spec-dir>
loop-cohort review record <spec-dir> (--report <path> | --fingerprint <hex>...)
loop-cohort worktree preflight|add|record|list|merge|cleanup <spec-dir> [...]
loop-cohort dispatch-decision --branch <b> [--branch <b>...] [--category <c>...] [--base <ref>]
loop-cohort auto-parallel <spec-dir> [--off]
```

**Exit contract:** exit 0 on success; exit non-zero with a one-line reason on
stderr on failure. `check --phase plan` exits 1 with "plan not approved" on
first invocation — this is the expected cue to run the pre-EXECUTE reviewer,
not an error.

---

### loop-engine.py

**Role:** Phase FSM validator and workflow orchestrator.

loop-engine has two distinct responsibilities that compose within a single
transition call:

**A. Pure phase tracker.** The engine validates that the incoming event is legal
for the current mode × state pair, fires the read-only guard (if any), and
records the new phase in `engine-state.json`. This layer carries no side effects:
it cannot produce incorrect mutations even if called in an unexpected context,
and it is independently testable against the FSM tables alone.

**B. Workflow orchestrator.** After the phase write succeeds, the engine invokes
the appropriate loop-cohort mutations (`schedule`, `review record`) as side
effects. Each event that triggers a downstream cohort operation carries the
evidence required for that operation (`--report` for a clean review, `--fingerprint`
hashes for a round with open findings). This layer is what makes the engine a
coordinator — not just a recorder — of the work-loop's progress.

The two responsibilities are intentionally layered: A is always correct (legal
FSM transitions are enforced regardless of B), while B adds the operational
consequence. A failing B side effect does not reverse the A state write — see
Side-effect failure below.

**Source:** `packs/core/.apm/skills/work-loop/scripts/loop-engine.py`
**Projects to:** `.claude/skills/work-loop/scripts/loop-engine.py` (via
`make build-self`)

**What it owns:**

- `engine-state.json` — the session-local phase record written into each spec
  directory. Schema:
  ```json
  {
    "feature": "<slug>",
    "mode": "code | spec-plan | doc",
    "state": "<phase name — see transition tables below>",
    "last_transition_at": "<ISO-8601 UTC>",
    "pending_side_effect": "<verb | null>",
    "last_side_effect_result": "ok | failed | null"
  }
  ```
  `pending_side_effect` is written to before a side effect fires and cleared
  after. If the engine terminates between the phase write and the side-effect
  call, a resuming session can read `pending_side_effect` to know that the side
  effect was never executed (see Recovery below).
- Phase FSM — per-mode transition tables. Each transition is:
  `current_state + event → next_state`. Events not in the table for the current
  mode × state pair are refused with a non-zero exit.
- Transition execution — reads `engine-state.json`, validates the event (A),
  fires the guard if one exists (A), writes the new state with
  `pending_side_effect` set (A), then fires the side effect and clears
  `pending_side_effect` (B).

**Verb surface:**
```
loop-engine init <spec-dir> --mode {code|spec-plan|doc}
loop-engine transition <spec-dir> <event> [--fingerprints <hash>...]
loop-engine status <spec-dir> [--json]
loop-engine reset <spec-dir>
```

`--help` on every command is the primary documentation; help strings are
sufficient to use the tool without reading the source.

`status --json` exposes `pending_side_effect` and `last_side_effect_result` so
the INI-003 supervisor and a resuming session can detect incomplete transitions.

**Exit contract:** exit 0 on success; exit non-zero with a one-line descriptive
message on failure (invalid transition, guard refused, file absent, etc.).

**Single-writer contract:** only one caller may issue `loop-engine transition`
calls for a given `<spec-dir>` at a time. `os.replace` provides atomic individual
writes but not serialised read-modify-write; concurrent callers on the same
spec-dir will produce lost updates. In supervisor mode this is guaranteed by the
barrier-wait discipline (all implementers complete before the supervisor fires
the next `wave-complete`). A `loop-engine transition` call must not be issued
while another is in flight for the same spec-dir.

---

## Phase FSM: Transition Tables

Three modes. State names embed the phase so the current position is readable
at a glance.

Legal states per mode (only these values appear in `engine-state.json.state`):

- **code:** `SPEC-PLAN-DRAFTING`, `SPEC-PLAN-REVIEW`, `SPEC-PLAN-HUMAN-GATE`,
  `CODE-IMPLEMENTATION`, `CODE-VERIFICATION`, `CODE-REVIEW`, `CODE-HUMAN-GATE`,
  `DONE`
- **spec-plan:** `SPEC-PLAN-DRAFTING`, `SPEC-PLAN-REVIEW`, `SPEC-PLAN-HUMAN-GATE`,
  `DONE`
- **doc:** `DOC-DRAFTING`, `DOC-REVIEW`, `DOC-HUMAN-GATE`, `DONE`

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

**`wave-passed` vs `gates-clean`:** `wave-complete` fires when a single wave's
implementation work is committed. If the plan has additional waves in the
schedule, the agent fires `wave-passed` after the wave's gates pass and the
merge is clean — returning to `CODE-IMPLEMENTATION` for the next wave. When all
waves are complete and gates pass on the full diff, the agent fires `gates-clean`
to proceed to `CODE-REVIEW`. The agent knows whether more waves remain from the
`loop-cohort schedule` output read during `CODE-IMPLEMENTATION`.

### spec-plan

spec-plan reuses the first three code-mode states and terminates at
`SPEC-PLAN-HUMAN-GATE`. `reviewers-clean` here means the spec/plan passes cold
adversarial review — not that implementation is complete. This review cycle
bypasses loop-cohort (no `review record`; convergence bounded by LLM judgment).

| Current state | Event | Next state |
|---|---|---|
| `SPEC-PLAN-DRAFTING` | `spec-ready` | `SPEC-PLAN-REVIEW` |
| `SPEC-PLAN-REVIEW` | `reviewers-clean` | `SPEC-PLAN-HUMAN-GATE` |
| `SPEC-PLAN-REVIEW` | `findings-remain` | `SPEC-PLAN-DRAFTING` |
| `SPEC-PLAN-HUMAN-GATE` | `plan-approved` | `DONE` |
| `SPEC-PLAN-HUMAN-GATE` | `plan-rejected` | `SPEC-PLAN-DRAFTING` |

### doc

`doc` mode covers all standalone documents: RFC, ADR, architecture doc, or any
other review-and-approve document. The SKILL.md defines what the human does at
`DOC-HUMAN-GATE` for each document type (RFC: named approver sign-off; ADR:
decision record; arch doc: lead review). The engine does not distinguish between
document types.

| Current state | Event | Next state |
|---|---|---|
| `DOC-DRAFTING` | `doc-ready` | `DOC-REVIEW` |
| `DOC-REVIEW` | `reviewers-clean` | `DOC-HUMAN-GATE` |
| `DOC-REVIEW` | `findings-remain` | `DOC-DRAFTING` |
| `DOC-HUMAN-GATE` | `doc-approved` | `DONE` |
| `DOC-HUMAN-GATE` | `doc-returned` | `DOC-DRAFTING` |

---

## Interaction Model

```
  LLM agent
      │
      │ loop-engine transition <spec-dir> <event> [--fingerprints <hashes>]
      ▼
  loop-engine.py
      │
      ├── A. PHASE TRACKER
      │   ├── 1. validate event against FSM for current mode × state
      │   │       (refuses with non-zero exit if invalid)
      │   │
      │   ├── 2. fire guard (if one exists for this event):
      │   │       calls the guard listed in the Guards table below
      │   │       (refuses with non-zero exit if guard exits non-zero)
      │   │
      │   └── 3. write new state to engine-state.json:
      │           {state: <new>, last_transition_at: <now>,
      │            pending_side_effect: <verb|null>}
      │           (atomic: tempfile + os.replace)
      │
      └── B. WORKFLOW ORCHESTRATOR
          └── 4. fire side effect (if applicable):
                  calls the exact loop-cohort verb listed in the Side Effects table
                  on success: write {pending_side_effect: null, last_side_effect_result: "ok"}
                  on failure: write {pending_side_effect: null, last_side_effect_result: "failed"}
                  logged to stderr regardless; transition not reversed on failure
                  (see Recovery below)

  loop-cohort.py
      │
      └── reads and writes state.json exclusively
          loop-engine never reads or writes state.json
```

**Direction is one-way.** loop-engine calls loop-cohort verbs. loop-cohort
never calls loop-engine. There is no shared mutable state between the two
scripts (see `feature` note in State Ownership below).

### `loop-engine init` setup call

`loop-engine init <spec-dir> --mode <mode>` runs `loop-cohort init <spec-dir>`
as its sole setup call (for code and spec-plan modes only), immediately after
writing `engine-state.json`. This is not a transition side effect — it happens
once, at session start, before any `transition` call.

---

## A. Phase Tracker: Guards

Each event has at most one guard. The guard must exit 0 before the transition
is accepted; non-zero exit refuses the transition. Guards fire in step 2, before
the state write (step 3), and are always read-only calls against loop-cohort or
standalone scripts — never mutations.

| Event | Mode | Current state | Guard call | Purpose |
|---|---|---|---|---|
| `plan-approved` | code, spec-plan | `SPEC-PLAN-HUMAN-GATE` | `loop-cohort check <spec-dir> --phase plan` | Verifies `approve-plan` was called |
| `wave-complete` | code | `CODE-IMPLEMENTATION` | `loop-cohort check <spec-dir> --phase implement` | Iteration cap + token budget + same-error + stasis backstop |
| `findings-remain` | code | `CODE-REVIEW` | `loop-cohort check <spec-dir> --phase review` | Iteration cap + token budget + stasis + same-error |
| `reviewers-clean` | code | `CODE-REVIEW` | `check-spec-status.py <spec-dir>` | `**Status:** Shipped` in working tree before PR goes to human |

`check-spec-status.py` lives at
`packs/core/.apm/skills/work-loop/scripts/check-spec-status.py`. It verifies
that the spec's `**Status:**` field reads `Shipped` in the current working tree.
It fires at `CODE-REVIEW + reviewers-clean → CODE-HUMAN-GATE` — the point where
the PR is about to be presented for human G-pr review. The optimistic in-PR
update (spec updated to `Shipped` as part of the PR diff) is intentional: the
PR is the proposal to ship, and the spec update is part of that proposal. If the
PR is rejected, the update stays on the branch; main is unchanged.

`lint-spec-status.py` is a CI-level drift linter (AC completeness, deferred
items, `**Status:**` field). It is not a loop-engine guard; it runs in CI and
on-demand for cleanup and reconciliation.

`reviewers-clean` in `SPEC-PLAN-REVIEW` (spec-plan and code mode pre-plan
phase) carries **no guard** — the spec isn't being shipped at that point, and a
stasis check must not block a legitimate clean exit.

**Stasis detection sequencing:** the `findings-remain` guard (in `CODE-REVIEW`)
fires in step 2, before the `review record` side effect in step 4. It therefore
sees fingerprints from the **preceding round**. Stasis is detected one round
delayed: guard on round N+1 catches that round N fingerprints equal round N−1
fingerprints.

**`plan-approved` guard ordering:** `loop-cohort check --phase plan` exits 0
only when `plan_review_status != "pending"`. The only verb that sets this is
`loop-cohort approve-plan`. Therefore, `approve-plan` must be called **before**
`loop-engine transition plan-approved` — it is the mechanical step of the G-plan
human gate. The guard verifies it ran. This is not a side effect.

**Zero-fingerprint floor:** `findings-remain` must be accompanied by at least
one `--fingerprints` hash. A review round that produces no hashable findings is
a clean round and must fire `reviewers-clean` instead.

---

## B. Workflow Orchestrator: Side Effects

Side effects are loop-cohort verb calls fired **after** `engine-state.json` is
written (step 4), in the order listed. They are the orchestration consequence
of each transition. Side effects fire for **code mode only** in the specific
events below; spec-plan and doc modes have no side effects (see Coordination by
Mode).

| Trigger | Mode | Current state | Side-effect call |
|---|---|---|---|
| `plan-approved` | code only | `SPEC-PLAN-HUMAN-GATE` | `loop-cohort schedule <spec-dir>` |
| `reviewers-clean` | code only | `CODE-REVIEW` | `loop-cohort review record <spec-dir> --report <report-path>` |
| `findings-remain` | code only | `CODE-REVIEW` | `loop-cohort review record <spec-dir> --fingerprint <h1> --fingerprint <h2> ...` |

`schedule` and `review record` fire for **code mode only**, and only in the
code-phase review states. spec-plan's `SPEC-PLAN-REVIEW` cycle bypasses
loop-cohort entirely — no `review record` is called; convergence is bounded by
LLM judgment. The only loop-cohort calls for spec-plan are the setup call
(`loop-cohort init` during `loop-engine init`) and the `plan-approved` guard.

`review record` fires on **every** code-mode review round — both when reviewers
find issues (`findings-remain`) and when they clear (`reviewers-clean`). This
increments `iteration_count` and rotates fingerprints so the count is accurate
even on the clean exit.

**`blocker-applied` fires no side effect.** A human-returned blocker is not an
LLM review round; `iteration_count` is not incremented. The agent re-enters
`CODE-IMPLEMENTATION`, fixes, and re-runs gates before the next `wave-complete`.

**Flag conventions for `review record`:**
- `reviewers-clean` → `--report <path>`: loop-cohort parses the "Clean — ready
  to commit." marker and records an empty fingerprint set.
- `findings-remain` → repeated `--fingerprint <hex>`: one flag per finding hash.
  loop-engine accepts `--fingerprints <hash>...` (`nargs='+'`) and expands them
  to repeated `--fingerprint <hex>` calls. loop-engine never stores fingerprints.

**`review record` is not idempotent** — it unconditionally increments
`iteration_count` and rotates fingerprint lists. Do not call it twice for the
same review round. `loop-cohort schedule` is safe to re-run.

### Worktree lifecycle (code mode)

Worktree verbs (`worktree preflight/add/record/list/merge/cleanup`) are
**not** loop-engine side effects. They are invoked directly by the LLM or
supervisor during `CODE-IMPLEMENTATION`, between `wave-complete` transitions,
as described in the SKILL.md's supervisor mode reference. Routing them through
loop-engine would introduce git operations into the engine — a constraint
violation (`loop-engine` has no git operations).

### Side-effect failure and recovery

Before firing a side effect, loop-engine writes `pending_side_effect: <verb>` to
`engine-state.json`. After the call returns (success or failure), it writes
`pending_side_effect: null` and `last_side_effect_result: "ok" | "failed"`.

If the engine terminates between the state write (step 3) and the side-effect
call (step 4), `engine-state.json` carries a non-null `pending_side_effect`.
A resuming session reads `loop-engine status --json <spec-dir>` and acts:

- **`pending_side_effect: "schedule"`** → re-run `loop-cohort schedule <spec-dir>`
  directly (`schedule` is idempotent).
- **`pending_side_effect: "review-record"`** → surface to the human. The
  `iteration_count` and fingerprints were never updated; manual reconciliation
  is required before the next review round. Do not re-run `review record`
  autonomously (non-idempotent; double-run corrupts iteration count and stasis
  state).

If the engine exits non-zero during step 4 (side effect ran but failed):
- `engine-state.json` reflects the new state (step 3 already completed).
- The failure is logged to stderr and recorded as `last_side_effect_result: "failed"`.
- Recovery is the same as the above per-verb rules.

**`loop-cohort init` failure** (during `loop-engine init`): `engine-state.json`
is written but `state.json` is not. Re-run `loop-cohort init <spec-dir>`
directly — the verb refuses if `state.json` already exists, so it is safe to
retry on a clean write failure.

**Unrecoverable inconsistency:** run `loop-engine reset <spec-dir>` (deletes
`engine-state.json`) and manually delete `state.json`, then re-run
`loop-engine init`. This restarts both scripts from `SPEC-PLAN-DRAFTING` and
requires re-running the full G-plan approval flow.

---

## Human Gate Obligations

Loop-engine does not automate human gates. The following events require explicit
human action before the LLM may fire them. Mechanical enforcement varies by
event and is noted below.

### G-plan (plan approval)

`plan-approved` fires only after all three pre-conditions hold:

1. The adversarial reviewer returned clean on the spec/plan (`SPEC-PLAN-REVIEW`
   reached `reviewers-clean`). — *SKILL.md obligation; not mechanically enforced.*
2. The LLM called `loop-cohort approve-plan <spec-dir>` directly (sets
   `plan_review_status`). — *Mechanically enforced: the `plan-approved` guard
   exits non-zero if this hasn't run.*
3. Human G-plan sign-off received (the LLM surfaced the plan and waited). —
   *SKILL.md obligation; not mechanically enforced.*

### G-pr (code review and merge)

G-pr happens **at** `CODE-HUMAN-GATE`. Both events that exit this state (`done`,
`blocker-applied`) carry **no mechanical guard**. The LLM must not fire `done`
without an actual merge. This is enforced by SKILL.md convention, not by the
engine.

A merge-verification guard (checking PR merge status via the GitHub API) would
make this mechanical but introduces an external-system dependency and tool-access
uncertainty. This is a future consideration if autonomous misuse becomes
observable in practice.

```
CODE-REVIEW → reviewers-clean → CODE-HUMAN-GATE
              (check-spec-status        │
               guard fires here)        │ LLM presents PR for human G-pr review
                                        │
                    ┌───────────────────┴──────────────────────┐
                    │ Human approves and PR merges             │ Human returns blocker
                    ▼                                           ▼
                 done → DONE                    blocker-applied → CODE-IMPLEMENTATION
               (loop complete)            (fix applied, gates re-run,
                                            CODE-IMPLEMENTATION → CODE-VERIFICATION
                                            → CODE-REVIEW → CODE-HUMAN-GATE)
```

`DONE` means the PR is merged. `blocker-applied` routes back to
`CODE-IMPLEMENTATION` (not directly to `CODE-REVIEW`) so that gates re-run on
the fix before re-review.

For `doc` mode, human gates are enforced by the respective governance process
(RFC approver sign-off, ADR record). Loop-engine tracks phase state only; it
does not replace those governance steps.

---

## `reset` Scope

`loop-engine reset <spec-dir>` deletes `engine-state.json` only. It does not
touch `state.json`. After `reset`, the next `loop-engine init` starts from the
mode's initial drafting state — `SPEC-PLAN-DRAFTING` for code and spec-plan
(agent must re-run the full G-plan approval flow), `DOC-DRAFTING` for doc.

**Accepted cost:** reset is all-or-nothing. A late-phase inconsistency (e.g. an
unrecoverable `review-record` failure) forces a restart from `SPEC-PLAN-DRAFTING`,
including re-running the full G-plan approval flow. Partial recovery (returning
to the phase just before the inconsistency) is not supported; the added recovery
machinery is not worth the complexity at this stage.

`reset` cannot be used to skip or replay a human gate.

---

## State Ownership

No field is shared as mutable state between the two files.

| File | Owner | Fields |
|---|---|---|
| `state.json` | loop-cohort | `feature`, `iteration_count`, `max_iterations`, `token_budget_used_pct`, `token_budget_cap_pct`, `consecutive_same_error_count`, `consecutive_same_error_threshold`, `plan_review_status`, `auto_parallel`, `last_commit_sha`, `finding_fingerprints`, `previous_finding_fingerprints`, `worktrees` |
| `engine-state.json` | loop-engine | `feature`, `mode`, `state`, `last_transition_at`, `pending_side_effect`, `last_side_effect_result` |

**`feature` appears in both files.** It is an immutable slug independently
derived from the spec-dir basename at init time. It is never written by one
script and read by the other; the two derivations always agree because they
share the same input. This is the sole intentional name overlap and carries no
shared mutable state.

**`max_iterations` lives in `state.json` and is owned exclusively by
loop-cohort.** loop-engine has no read or write access to `state.json` and
therefore cannot read, modify, or override the iteration cap. When loop-cohort
signals an iteration cap via a non-zero exit from `check --phase implement`,
the LLM exercises judgment (request permission to continue or accept the cap)
per the SKILL.md's termination guidance — not loop-engine.

Both files are session-local and gitignored. They survive across session
boundaries within the same working tree but are never committed.

---

## Coordination by Mode

| Mode | loop-cohort used? | Guards (A) | Spec-status guard (A) | Side effects (B) |
|---|---|---|---|---|
| `code` | Yes | `plan-approved` (SPEC-PLAN-HUMAN-GATE), `wave-complete` (CODE-IMPLEMENTATION), `findings-remain` (CODE-REVIEW) | `reviewers-clean` at CODE-REVIEW → `check-spec-status.py` | `plan-approved` → schedule; `reviewers-clean` + `findings-remain` at CODE-REVIEW → review record; `loop-cohort init` at engine init |
| `spec-plan` | Yes (setup + plan gate only) | `plan-approved` (SPEC-PLAN-HUMAN-GATE) | — | `loop-cohort init` at engine init only; no transition side effects |
| `doc` | No | — | — | — |

`doc` mode bypasses loop-cohort entirely. The engine manages phase state only;
no task DAG, no worktrees, no finding fingerprints.

**Light mode** does not invoke loop-engine or loop-cohort. See
`packs/core/DESIGN.md §3` for the light-vs-full mode selection rule.

---

## Convergence Loops

### code mode

The code-mode FSM has two back-edge families. The pre-plan loop iterates the
spec/plan until clean; the code loop iterates implementation across waves and
review rounds until the diff is clean.

**Pre-plan loop:**
```
SPEC-PLAN-DRAFTING
    │  spec-ready
    ▼
SPEC-PLAN-REVIEW
    ├── reviewers-clean ────────────────────► SPEC-PLAN-HUMAN-GATE
    └── findings-remain                              │ plan-approved
          │                                          ▼
          ▼                                  CODE-IMPLEMENTATION
    SPEC-PLAN-DRAFTING  ← fix and re-draft
```

Pre-plan convergence is bounded by LLM judgment (no loop-cohort iteration cap).

**Code loop (multi-wave + review):**
```
CODE-IMPLEMENTATION
    │  wave-complete (guard: check --phase implement)
    ▼
CODE-VERIFICATION
    ├── wave-passed ──────────────────────────────────────────────────────────┐
    │     (more waves remain in schedule)                                     │
    ├── gates-clean ──────────────────────────────────────────────────────► CODE-REVIEW
    │     (all waves complete)                                                │
    └── gates-failed ──────────────────────────────────────────────────────► CODE-IMPLEMENTATION (fix)
                                                                             ▲
CODE-REVIEW                                                                  │
    ├── reviewers-clean (guard: check-spec-status.py) ──► CODE-HUMAN-GATE   │
    │     (side effect: review record --report)               │              │
    │                                                  done   │  blocker-    │
    │                                                   ▼     │  applied     │
    │                                                  DONE   └─────────────►┘
    └── findings-remain (guard: check --phase review)
          (side effect: review record --fingerprints)
          │
          ▼
    CODE-IMPLEMENTATION  ← back-edge; the cycle repeats
                                                                ▲
                                                                └── (wave-passed also feeds here)
```

**Code-mode termination is bounded** by four independent mechanisms in `state.json`
(owned by loop-cohort, invisible to loop-engine):

1. **Iteration cap** — `check --phase implement` and `check --phase review`
   both exit non-zero when `iteration_count >= max_iterations`. The LLM
   exercises judgment: surface to the human with a concrete reason why another
   round is warranted, or accept the cap and stop. `max_iterations` is a
   judgment parameter, not a blind limit.
2. **Stasis detection** — `check --phase review` exits non-zero when
   `finding_fingerprints == previous_finding_fingerprints` and both are non-empty
   (same non-empty finding set two rounds in a row, order-independent).
3. **Token budget** — `check --phase implement` and `check --phase review` both
   exit non-zero when `token_budget_used_pct >= token_budget_cap_pct`.
4. **Consecutive-same-error** — both `check --phase implement` and
   `check --phase review` exit non-zero when
   `consecutive_same_error_count >= consecutive_same_error_threshold`.

If any mechanism fires and the loop is not converged, the LLM surfaces to the
human. **The loop cannot self-terminate beyond `DONE`** — the `done` event must
be fired explicitly by the LLM, and G-pr (human merge) remains the terminal gate.

### spec-plan and doc modes

Both have the same back-edge structure (`findings-remain → *-DRAFTING`) without
loop-cohort coordination. Convergence is bounded by LLM judgment. For `doc`
mode, `DOC-HUMAN-GATE` also has a back-edge via `doc-returned → DOC-DRAFTING`
for when a human approver sends the document back for revision after internal
review is already clean.

---

## Human-Wait States and Session Boundaries

Some states are **human-wait states** — the loop has committed its work product
to git (as a PR, draft, or branch) and is waiting for a human response before
the next event can be fired. A session can end in any of these states.

| State | Mode | Work product committed | Waiting for |
|---|---|---|---|
| `SPEC-PLAN-HUMAN-GATE` | code, spec-plan | spec.md + plan.md on branch or PR | Human G-plan sign-off |
| `CODE-HUMAN-GATE` | code | implementation PR | Human G-pr (merge or blocker) |
| `DOC-HUMAN-GATE` | doc | document on branch or PR | Human doc approval |
| `DOC-REVIEW` | doc | document committed to git | Human reviewer — human-wait **only when review is async/external**; when the LLM runs review itself, `DOC-REVIEW` is a normal LLM-reviewed state and `reviewers-clean`/`findings-remain` may fire autonomously |

When a session ends in a human-wait state, the next session (same or different
person) resumes by reading `loop-engine status <spec-dir>` and **waiting for
the human response** rather than firing the next event autonomously. The rule:
no event that exits a human-wait state may be fired without the human's
explicit signal, regardless of session boundary.

The committed work product must be on a named branch or open PR before the
session ends in a human-wait state — a locally-only-committed artifact cannot
be reviewed by others.

---

## Session Resumption

`last_transition_at` in `engine-state.json` records the UTC timestamp of each
transition. This enables:

1. **Cross-session resumption** — an agent starting a new session reads
   `loop-engine status <spec-dir>` to recover the current phase without
   reconstructing it from chat history. If `pending_side_effect` is non-null,
   handle the incomplete transition before firing any new events (see Recovery).
   If the state is a human-wait state, wait for the human signal rather than
   proceeding.
2. **Stale-worker detection** (INI-003) — a factory supervisor calls
   `loop-engine status --json <spec-dir>` on each worker's spec directory and
   uses `last_transition_at` to identify workers that have not advanced.
   The stale threshold is INI-003's responsibility; loop-engine makes no
   assumption about phase-expected duration.

The `--json` flag on `status` is the stable per-worker observation interface.
The four-verb surface (`init`, `transition`, `status`, `reset`) and the
`engine-state.json` schema are stable across INI-003 integration.

---

## Alternatives Considered

### State-first vs. side-effect-first ordering

Side effects could fire before the phase write (B before A). This is rejected
because a successful side effect with a failed state write leaves `state.json`
updated (e.g. `iteration_count` incremented) with `engine-state.json` still in
the old phase — a worse inconsistency than the current crash window, because the
side effect's consequences are irreversible (non-idempotent `review record`)
while the state write is not. State-first was chosen: if the phase write
succeeds but the side effect fails, `pending_side_effect` records what was
pending and recovery is deterministic.

### Outcome journaling as the primary design

An alternative approach journals every intended and actual side-effect outcome
as the primary design, with no A/B layering. This is subsumed by the current
design: `pending_side_effect` and `last_side_effect_result` in `engine-state.json`
provide outcome journaling within the A/B model, without the overhead of a
separate journaling protocol.

### Two separate scripts (pure tracker + pure orchestrator)

Separating A (FSM validator) and B (workflow orchestrator) into two scripts
would create cleaner module boundaries at the cost of a coordination protocol
between them. The event is the natural unit of both validation and consequence;
the single `transition` call from the agent maps cleanly to both responsibilities.
A two-script design would require callers to invoke two CLIs in sequence with no
atomicity guarantee across them — reproducing the crash window at a higher level.

### Optimistic concurrency vs. single-writer contract

Optimistic concurrency (read `last_transition_at`, compare before replace) would
handle concurrent callers on the same spec-dir. This is deferred in favour of
the single-writer contract (see Single-writer contract in the Scripts section),
which is sufficient given that supervisor mode enforces the barrier-wait
discipline. Add optimistic concurrency if a use case arises that cannot honour
the single-writer constraint.

---

## Testing

The A/B layering enables three independent test layers:

1. **FSM table tests (A):** for each mode, enumerate all legal transitions and
   verify they produce the correct next state; enumerate illegal event/state
   pairs and verify non-zero exit. No loop-cohort involvement.

2. **Guard-refusal tests (A):** stub each guard script to exit non-zero; verify
   the transition is refused and `engine-state.json` is unchanged; verify the
   guard call receives the correct arguments.

3. **Side-effect ordering and journaling tests (B):** stub loop-cohort verbs;
   verify `pending_side_effect` is written before the stub is called and cleared
   after; simulate a verb failure and verify `last_side_effect_result: "failed"`.

4. **Recovery tests (B):** write `engine-state.json` with a non-null
   `pending_side_effect` directly (simulating a mid-flight crash); verify
   `loop-engine status --json` surfaces it; verify the per-verb recovery
   instruction (re-run schedule / surface review-record to human).

Tests live at `packs/core/.apm/skills/work-loop/scripts/test-loop-engine.py`.

---

## Source Tree

```
packs/core/.apm/skills/work-loop/
├── SKILL.md                         # skill entry point (LLM reads this)
├── scripts/
│   ├── loop-cohort.py               # task execution state owner
│   ├── loop-engine.py               # phase FSM validator + workflow orchestrator (new)
│   ├── check-spec-status.py         # spec Status=Shipped gate (new)
│   ├── lint-spec-status.py          # spec metadata drift linter (CI/on-demand)
│   └── lint-traceability.py         # traceability matrix linter
├── assets/
│   └── state.json                   # loop-cohort state template
└── references/
    ├── loop-infrastructure.md       # mode/checkpoint tables; agent-facing quick reference (new)
    └── state-schema.md              # state.json field reference
```

`engine-state.json` has no separate template file — its six fields and allowed
values are fully specified in this document and in `loop-engine --help` output.

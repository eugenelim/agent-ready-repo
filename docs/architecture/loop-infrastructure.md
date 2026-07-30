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
for the current mode × state pair, fires read-only guards, and records the new
phase in `engine-state.json`. This layer carries no side effects: it cannot
produce incorrect mutations even if the transition is called in an unexpected
context, and it is independently testable against the FSM tables alone.

**B. Workflow orchestrator.** After the phase write succeeds, the engine invokes
the appropriate loop-cohort mutations (`schedule`, `review record`) as side
effects. These are event-specific: each event that triggers a downstream cohort
operation carries the evidence required for that operation (`--report` for a
clean review, `--fingerprint` hashes for an unresolved-findings round). This
layer is what makes the engine a coordinator — not just a recorder — of the
work-loop's progress.

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
    "last_transition_at": "<ISO-8601 UTC>"
  }
  ```
- Phase FSM — per-mode transition tables. Each transition is:
  `current_state + event → next_state`. Events not in the table for the current
  mode × state pair are refused with a non-zero exit.
- Transition execution — reads `engine-state.json`, validates the event (A),
  fires any guards (A), writes the new state atomically (A), then fires any
  side effects (B).

**Verb surface:**
```
loop-engine init <spec-dir> --mode {code|spec-plan|doc}
loop-engine transition <spec-dir> <event> [--fingerprints <hash>...]
loop-engine status <spec-dir> [--json]
loop-engine reset <spec-dir>
```

`--help` on every command is the primary documentation; help strings are
sufficient to use the tool without reading the source.

**Exit contract:** exit 0 on success; exit non-zero with a one-line descriptive
message on failure (invalid transition, guard refused, file absent, etc.).

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
| `CODE-VERIFICATION` | `gates-clean` | `CODE-REVIEW` |
| `CODE-VERIFICATION` | `gates-failed` | `CODE-IMPLEMENTATION` |
| `CODE-REVIEW` | `reviewers-clean` | `CODE-HUMAN-GATE` |
| `CODE-REVIEW` | `findings-remain` | `CODE-IMPLEMENTATION` |
| `CODE-HUMAN-GATE` | `done` | `DONE` |
| `CODE-HUMAN-GATE` | `blocker-applied` | `CODE-IMPLEMENTATION` |

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
      │   ├── 2. fire guards (if applicable):
      │   │       calls guard scripts listed in Guards table below, in order
      │   │       (refuses with non-zero exit if any guard exits non-zero)
      │   │
      │   └── 3. write new state to engine-state.json (atomic: tempfile + os.replace)
      │
      └── B. WORKFLOW ORCHESTRATOR
          └── 4. fire side effects (if applicable, in order listed in Side Effects table):
                  calls the exact loop-cohort verbs listed below
                  (side-effect failure → logged to stderr, not retried, does not
                   reverse the transition — see Recovery below)

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

A guard must exit 0 before the transition is accepted. Non-zero exit refuses
the transition. Guards fire in step 2, before the state write (step 3).

| Event | Mode | Current state | Exact guard call | Purpose |
|---|---|---|---|---|
| `plan-approved` | code, spec-plan | `SPEC-PLAN-HUMAN-GATE` | `loop-cohort check <spec-dir> --phase plan` | Verifies `approve-plan` was called |
| `wave-complete` | code | `CODE-IMPLEMENTATION` | `loop-cohort check <spec-dir> --phase implement` | Iteration cap + token budget + same-error + stasis backstop |
| `findings-remain` | code | `CODE-REVIEW` | `loop-cohort check <spec-dir> --phase review` | Iteration cap + token budget + stasis + same-error |
| `reviewers-clean` | code | `CODE-REVIEW` | `check-spec-status.py <spec-dir>` | `**Status:** Shipped` in working tree before PR goes to human |

`check-spec-status.py` lives at
`packs/core/.apm/skills/work-loop/scripts/check-spec-status.py` (owned by the
work-loop skill, alongside `loop-engine.py` and `loop-cohort.py`). It is a new
script separate from `lint-spec-status.py`. It verifies that the spec's
`**Status:**` field reads `Shipped` in the current working tree. It fires at
`CODE-REVIEW + reviewers-clean → CODE-HUMAN-GATE` — the point where the PR is
about to be presented for human G-pr review. The optimistic in-PR update (spec
updated to `Shipped` as part of the PR diff) is intentional: the PR is the
proposal to ship, and the spec update is part of that proposal. If the PR is
rejected, the update stays on the branch; main is unchanged.

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

---

## B. Workflow Orchestrator: Side Effects

Side effects are loop-cohort verb calls fired **after** `engine-state.json` is
written (step 4), in the order listed. They are the orchestration consequence
of each transition — the engine does not just record that the phase changed; it
triggers the downstream work the new phase requires.

Side effects fire for **code and spec-plan modes only** (see Coordination by
Mode below).

| Trigger | Mode | Current state | Exact side-effect calls (in order) |
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
increments `iteration_count` and rotates fingerprints so iteration count is
accurate even on the clean exit.

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

If a side effect fails:
- `engine-state.json` already reflects the new state (written in step 3).
- The failure and its stderr are logged; the transition is not reversed.
- **`schedule` failure:** re-run `loop-cohort schedule <spec-dir>` directly —
  it is idempotent.
- **`review record` failure:** do not re-run it (non-idempotent; double-run
  corrupts iteration count and stasis state). Surface the failure to the human
  for directed recovery.
- **`loop-cohort init` failure** (during `loop-engine init`): `engine-state.json`
  is written but `state.json` is not. Re-run `loop-cohort init <spec-dir>`
  directly — the verb refuses if `state.json` already exists, so it is safe to
  retry on a clean write failure.
- **Unrecoverable inconsistency:** run `loop-engine reset <spec-dir>` (deletes
  `engine-state.json`) and manually delete `state.json`, then re-run
  `loop-engine init`. This restarts both scripts from `SPEC-PLAN-DRAFTING` and
  requires re-running the full G-plan approval flow.

---

## Human Gate Invariants

Loop-engine does not automate human gates. Two events require explicit human
action before the LLM may fire them.

### G-plan (plan approval)

`plan-approved` fires only after all three pre-conditions hold:

1. The adversarial reviewer returned clean on the spec/plan (`SPEC-PLAN-REVIEW`
   reached `reviewers-clean`).
2. The LLM called `loop-cohort approve-plan <spec-dir>` directly (sets
   `plan_review_status`; the `plan-approved` guard validates this happened).
3. Human G-plan sign-off received (the LLM surfaced the plan and waited).

Loop-engine enforces only condition (2) via the guard. Conditions (1) and (3)
are SKILL.md obligations, not mechanical checks.

### G-pr (code review and merge)

G-pr happens **at** `CODE-HUMAN-GATE`. The sequence is:

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

`DONE` means the PR is merged. Firing `done` is the LLM's signal that the
human approved at G-pr and the merge is complete. `blocker-applied` routes back
to `CODE-IMPLEMENTATION` (not directly to `CODE-REVIEW`) so that gates re-run
on the fix before re-review. This matches `DESIGN.md §2` (DECIDE phase: "applies
fixes, re-runs gates").

The `check-spec-status.py` guard at `CODE-REVIEW → CODE-HUMAN-GATE` ensures the
spec already carries `**Status:** Shipped` as part of the PR diff before the
human sees it. The optimistic update is intentional — see Guards section.

For `doc` mode, human gates are enforced by the respective governance process
(RFC approver sign-off, ADR record). Loop-engine tracks phase state only; it
does not replace those governance steps.

---

## `reset` Scope

`loop-engine reset <spec-dir>` deletes `engine-state.json` only. It does not
touch `state.json`. After `reset`, the next `loop-engine init` starts from the
mode's initial drafting state — `SPEC-PLAN-DRAFTING` for code and spec-plan
(agent must re-run the full G-plan approval flow), `DOC-DRAFTING` for doc.
`reset` cannot be used to skip or replay a human gate.

---

## State Ownership

No field is shared as mutable state between the two files.

| File | Owner | Fields |
|---|---|---|
| `state.json` | loop-cohort | `feature`, `iteration_count`, `max_iterations`, `token_budget_used_pct`, `token_budget_cap_pct`, `consecutive_same_error_count`, `consecutive_same_error_threshold`, `plan_review_status`, `auto_parallel`, `last_commit_sha`, `finding_fingerprints`, `previous_finding_fingerprints`, `worktrees` |
| `engine-state.json` | loop-engine | `feature`, `mode`, `state`, `last_transition_at` |

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
| `spec-plan` | Yes (setup + plan gate only) | `plan-approved` (SPEC-PLAN-HUMAN-GATE) | — | none beyond setup and plan guard |
| `doc` | No | — | — | — |

`doc` mode bypasses loop-cohort entirely. The engine manages phase state only;
no task DAG, no worktrees, no finding fingerprints.

**Light mode** does not invoke loop-engine or loop-cohort. See
`packs/core/DESIGN.md §3` for the light-vs-full mode selection rule.

---

## Convergence Loops

### code mode

The code-mode FSM has two back-edges. The pre-plan loop iterates the spec/plan
until clean; the code loop iterates implementation until the diff is clean.

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

**Code loop:**
```
CODE-IMPLEMENTATION
    │  wave-complete (guard: check --phase implement)
    ▼
CODE-VERIFICATION
    │  gates-clean
    ▼
CODE-REVIEW
    ├── reviewers-clean (guard: check-spec-status.py) ──► CODE-HUMAN-GATE
    │     (side effect: review record --report)               │
    │                                                  done   │  blocker-applied
    │                                                   ▼     │  ▼
    │                                                  DONE   CODE-IMPLEMENTATION
    └── findings-remain (guard: check --phase review)
          (side effect: review record --fingerprints)
          │
          ▼
    CODE-IMPLEMENTATION  ← back-edge; the cycle repeats
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
| `DOC-REVIEW` | doc | document committed to git | Human reviewer — **human-wait only when review is async/external**; when the LLM runs review itself, `DOC-REVIEW` is a normal LLM-reviewed state and `reviewers-clean`/`findings-remain` may fire autonomously |

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
   reconstructing it from chat history. If the state is a human-wait state
   (see above), the agent waits for the human signal rather than proceeding.
2. **Stale-worker detection** (INI-003) — a factory supervisor calls
   `loop-engine status --json <spec-dir>` on each worker's spec directory and
   uses `last_transition_at` to identify workers that have not advanced.

The `--json` flag on `status` is the stable per-worker observation interface.
The four-verb surface (`init`, `transition`, `status`, `reset`) and the
`engine-state.json` schema are stable across INI-003 integration.

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

`engine-state.json` has no separate template file — its four fields and allowed
values are fully specified in this document and in `loop-engine --help` output.

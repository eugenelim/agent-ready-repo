# Loop Infrastructure — Phase 1

The work-loop's execution machinery is split across two purpose-built scripts
with a hard boundary: `loop-engine.py` is a read-only FSM phase tracker;
`loop-cohort.py` is the sole writer of cohort execution state.

## Key references

- **Decision (why):** [`docs/adr/0061-loop-infrastructure-phase-1.md`](../adr/0061-loop-infrastructure-phase-1.md)
- **Feature contract (what):** [`docs/specs/loop-infrastructure-phase-1/spec.md`](../specs/loop-infrastructure-phase-1/spec.md)
- **Implementation plan (how):** [`docs/specs/loop-infrastructure-phase-1/plan.md`](../specs/loop-infrastructure-phase-1/plan.md)
- **State field reference:** [`packs/core/.apm/skills/work-loop/references/state-schema.md`](../../packs/core/.apm/skills/work-loop/references/state-schema.md)

## Components

### `loop-engine.py` (FSM phase tracker)

Owns `engine-state.json` (gitignored at `docs/specs/**/engine-state.json`).
Read-only except for `init`, `transition`, and `reset`.

```
loop-engine init <spec-dir> --mode {code|spec-plan} [--json]
loop-engine transition <spec-dir> <event> [--wave-index <n>]
loop-engine status <spec-dir> [--json]
loop-engine reset <spec-dir>
```

**FSM modes (Phase 1):**

`code` — eight-state lifecycle with spec/plan drafting and implementation waves:

```
SPEC-PLAN-DRAFTING → (spec-ready) → SPEC-PLAN-REVIEW
SPEC-PLAN-REVIEW   → (reviewers-clean) → SPEC-PLAN-HUMAN-GATE
SPEC-PLAN-REVIEW   → (findings-remain) → SPEC-PLAN-DRAFTING
SPEC-PLAN-HUMAN-GATE → (plan-approved) → CODE-IMPLEMENTATION
SPEC-PLAN-HUMAN-GATE → (plan-rejected) → SPEC-PLAN-DRAFTING
CODE-IMPLEMENTATION  → (wave-complete) → CODE-VERIFICATION
CODE-VERIFICATION    → (wave-passed)   → CODE-IMPLEMENTATION   [requires --wave-index]
CODE-VERIFICATION    → (gates-clean)   → CODE-REVIEW
CODE-VERIFICATION    → (gates-failed)  → CODE-IMPLEMENTATION
CODE-REVIEW          → (reviewers-clean) → CODE-HUMAN-GATE
CODE-REVIEW          → (findings-remain) → CODE-IMPLEMENTATION
CODE-HUMAN-GATE      → (done)          → DONE
CODE-HUMAN-GATE      → (blocker-applied) → CODE-IMPLEMENTATION
```

`spec-plan` — five-state lifecycle terminating at DONE on plan-approved (no code phase):

```
SPEC-PLAN-DRAFTING → (spec-ready) → SPEC-PLAN-REVIEW
SPEC-PLAN-REVIEW   → (reviewers-clean) → SPEC-PLAN-HUMAN-GATE
SPEC-PLAN-REVIEW   → (findings-remain) → SPEC-PLAN-DRAFTING
SPEC-PLAN-HUMAN-GATE → (plan-approved) → DONE
SPEC-PLAN-HUMAN-GATE → (plan-rejected) → SPEC-PLAN-DRAFTING
```

**Guards** fire before each transition to enforce pre-conditions. The engine
runs `loop-cohort identity --expect-run-id` as a preflight on every transition
to confirm the cohort `run_id` matches. CODE-* transitions (except `done`)
additionally run `loop-cohort schedule check-current` to verify plan.md hasn't
changed since scheduling. Event-specific guards are detailed in the spec.

### `loop-cohort.py` (sole state.json writer)

Owns `state.json` (gitignored at `docs/specs/**/state.json`). All cohort
mutations are explicit verbs with `--expect-run-id` for identity safety.

**Phase 1 verb surface:**

```
init <spec-dir> --run-id <uuid>
identity <spec-dir> [--expect-run-id <uuid>] [--json]
status <spec-dir> [--json]
reset <spec-dir>
approve-plan <spec-dir> --expect-run-id <uuid>
plan check-current <spec-dir> [--require-schedule]
schedule <spec-dir> --expect-run-id <uuid>
schedule check-current <spec-dir>
check <spec-dir> --phase {implement|gates-failed|review}
record-attempt <spec-dir> --phase implement --cycle-id <run_id>:<seq> --expect-run-id <uuid>
wave check <spec-dir> --expect {more|last} [--wave-index <n>]
wave advance <spec-dir> --from-index <n> --expect-run-id <uuid>
review inspect <spec-dir> --report <path> [--json]
review record <spec-dir> (--fingerprint <hex> ... | --report <path>) --expect-run-id <uuid>
```

**Disabled in Phase 1** (exit non-zero with "disabled in Phase 1" message):
`dispatch-decision`, `worktree {add, record, list, merge, cleanup, preflight}`, `auto-parallel`.

### `check-spec-status.py` (spec-shipped guard)

Called by `loop-engine` as the guard for `reviewers-clean` (code mode). Imports
`parse_status` from `lint-spec-status.py` via `importlib` to share a single
canonical status parser. Exits 0 iff `spec.md` Status is `Shipped`.

## Init pair

Both tools must be initialized before use; the engine generates the `run_id`
that cohort adopts:

```bash
run_id=$(python3 scripts/loop-engine.py init docs/specs/<feature> \
    --mode code --json | python3 -c "import sys,json; print(json.load(sys.stdin)['run_id'])")
python3 scripts/loop-cohort.py init docs/specs/<feature> --run-id "$run_id"
```

## Atomic write guarantee

Both scripts write state through `tempfile.mkstemp` + `os.replace` in the same
directory as the target file. A crash mid-write cannot produce malformed JSON;
the target either carries the previous content or the new content, never a
partial write.

## Phase 2 (deferred)

Parallel fan-out (`dispatch-decision`, worktrees, `auto-parallel`), token-budget
tracking, consecutive-error detection, and cross-session resumption identifiers
are reserved for Phase 2.

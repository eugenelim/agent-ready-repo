# Loop infrastructure

## 1. Purpose and boundary

The execution harness tracks work-loop phases and cohort state for one spec
directory. `loop-engine.py` advances the finite-state machine.
`loop-cohort.py` records cohort execution state.

The harness does not create requirements or implement work. It consumes approved
specification and plan artifacts.

## 2. Entrypoints

- `loop-engine.py`: `init`, `transition`, `status`, and `reset`.
- `loop-cohort.py`: `init`, `identity`, `status`, `approve-plan`,
  `schedule`, `check`, wave, and review commands.
- `check-spec-status.py`: validates a requested status in `spec.md` or
  `plan.md`.

## 3. Owned state and write authority

| State | Location | Write authority | Readers |
| --- | --- | --- | --- |
| FSM phase state | `docs/specs/**/engine-state.json` (gitignored) | `loop-engine.py` | Harness operators |
| Cohort state | `docs/specs/**/state.json` (gitignored) | `loop-cohort.py` | Harness operators and engine guards |
| Transition events | `.loop-run/events.jsonl` (ephemeral) | `loop-engine.py` | Harness operators and workspace MCP |

## 4. Dependencies and allowed edges

`loop-engine.py` reads spec and plan status, then invokes `loop-cohort.py`
identity and schedule checks before guarded transitions. `check-spec-status.py`
imports the canonical status parser from `lint-spec-status.py`.

The engine reads cohort state but does not write it. The cohort tool does not
advance FSM phase state.

## 5. Primary flows

1. `loop-engine.py init` creates FSM state and emits a run identifier.
   `loop-cohort.py init` adopts that identifier.
2. A guarded engine transition verifies required artifact status and cohort
   identity. Code transitions also verify the scheduled plan remains current.
3. `loop-cohort.py` records plan approval, scheduling, attempts, waves, and
   review evidence. `loop-engine.py` records phase transitions and events.

### TDD stub artifact boundary

For a full-mode TDD task, `plan.md` owns the exact stub code and its validation
result before approval. PLAN compiles and exercises that code from
disposable scratch, so the proof participates in the approved plan hash without creating a
repository test file. In `spec-plan` mode, `plan-locked` is terminal and no
implementation artifact is written.

In code mode, `plan-locked` advances the engine to `CODE-IMPLEMENTATION`.
EXECUTE then materializes the approved block unchanged at the repository's real
test path, verifies byte identity, observes the intended red, and continues to
green. The engine owns the phase boundary; the plan and test tree own different
representations on either side of it.

## 6. Failure and recovery behavior

A failed guard blocks the transition. A run-identifier mismatch blocks cohort
mutation. A changed plan blocks code transitions until scheduling is current.

Both state writers use `tempfile.mkstemp` and `os.replace` in the target
directory. A crash leaves either the previous JSON or the replacement JSON.
`reset` is the explicit recovery action.

## 7. Observability and evidence

Both tools expose `status --json`. `engine-state.json`, `state.json`, and
`.loop-run/events.jsonl` record phase, cohort, and transition evidence.
Workspace MCP reads the event stream.

### 7.1 The transition envelope

`loop-engine transition` appends one JSON line per FSM transition to
`.loop-run/events.jsonl` — repo-root-relative, gitignored, ephemeral. The line
carries fourteen fields: the seven that identify the transition (`seq`,
`run_id`, `spec`, `from`, `event`, `to`, `at`) and seven that describe it
(`phase_started_at`, `phase_s`, `result`, `retry_state`, `awaiting_input`,
`waived`, `budgets`).

Three rules govern the shape.

- **Absent means null, never missing.** A field the engine cannot determine is
  written as `null` and still present, because a key that disappears reads as
  zero to anything summing durations or comparing a counter with a cap.
- **Outcome and reason are separate axes.** `result` records what a gate
  decided; `retry_state` records why a failure sits where it does. One field
  cannot carry both without giving a single value to "retrying" and to "out of
  attempts".
- **`budgets` is a copy, not an authority.** `loop-cohort` owns the retry
  counters and moves them in a separate step, so the line reports a snapshot
  that lags by one round. The pack's `state-schema.md` states the reachability
  limits this produces; treat them as load-bearing, not as caveats.

Writing the line is **unconditional**. There is no switch, because the target
is a gitignored local file and no data leaves the machine.

### 7.2 Export is a separate concern, and it is off

Turning transition evidence into telemetry — an OTLP exporter, a collector
endpoint, a dashboard — is deliberately **not** part of the engine. The engine
records; anything that transmits is a distinct component with its own consent
posture.

No such component ships today. When one does, three properties are settled in
advance by [the envelope survey](../product/research/agent-loop-otel-envelope-survey.md)
and its [vocabulary bake-off](../product/research/workflow-lifecycle-vocabulary-comparison-matrix.md):

- **OTLP is the transport**, and the domain vocabulary stays in an application
  namespace. No lifecycle vocabulary exists at any standards body for phases,
  gates, budgets or stalls, and the nearest standard deliberately dropped the
  human-gate terms this loop needs.
- **Disabled unless configured.** Not merely "no endpoint set by default" — an
  explicit enablement decision, with a malformed value failing closed rather
  than defaulting on.
- **Content capture is a second, separate flag**, also defaulting off, so
  enabling transport never implies consenting to payloads.

### 7.3 How an exporter would be configured

Configuration uses the mechanism this repository already has for adopter-owned
pack settings; it does not need a new one.

**Catalogue-level default.** A pack declares a scope-keyed
`[pack.layout.repo]` / `[pack.layout.user]` table in its `pack.toml`. At
install, `_append_layout_section` appends a `[<pack-name>]` section into an
adopter-owned `agentbundle-layout.toml` — repo scope at
`<repo>/agentbundle-layout.toml`, user scope at
`<user-root>/.agentbundle/agentbundle-layout.toml`.

Its three properties are the reason this is the right home for a consent-
bearing default:

| Property | Consequence |
| --- | --- |
| append-if-exists | An adopter with no layout file gets nothing written |
| never-create | Installing a pack cannot bring the file into being |
| never-overwrite | A section the adopter already authored is left alone |

So a shipped default can only ever land in a file the adopter already chose to
keep, and can never replace a decision they have already made.

**Two scopes, with the personal one winning.** `desk-research` establishes the
precedent: read user scope first so a personal vault applies regardless of
which repository is active, then repo scope as the team-visible fallback, then
elicit — never a silent default. Both files are adopter-owned and are never
written into a projected path.

**Environment override.** An environment variable takes precedence over both
files, so an operator can disable one run without editing an installed
artifact. This inverts OpenTelemetry's own rule, where a declarative config
file makes `OTEL_*` inert; the inversion is deliberate, because the file here
is an inherited default rather than an operator's own statement.

Reading configuration is prompt-only where a skill does it: a file is read and
a path reasoned about. Only the install-time append ever writes a layout file.

> **The shipped-default half does not work today.** Traced and confirmed by
> execution: `_append_layout_section` writes nothing for any pack in the
> catalogue, because the writer and readers disagree on section, key, and value
> name. See [agentbundle § 7.1](agentbundle.md#71-known-drift--the-install-time-layout-default-writes-nothing).
> Adopter-authored layout files and an environment variable both work, so an
> exporter can be configured today — but a catalogue-level default cannot be
> shipped until that drift is settled.

## 8. Mechanical invariants

- `check-spec-status.py` blocks guarded transitions unless the requested
  `spec.md` or `plan.md` status is present.
- `loop-engine.py` checks cohort identity before every transition.
- `loop-engine.py` checks the current schedule before code transitions except
  `done`.
- `loop-cohort.py` requires `--expect-run-id` for cohort mutations.

## 9. Relevant ADRs

- [ADR-0061 — Loop infrastructure](../adr/0061-loop-infrastructure-phase-1.md)
- [ADR-0064 — Events JSONL as FSM event source](../adr/0064-events-jsonl-as-fsm-event-source.md)
- [ADR-0074 — Work loop owns its state lock](../adr/0074-the-work-loop-owns-its-state-lock.md)

## 10. Last verified against commit

`6f030f151`

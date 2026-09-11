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

### 7.3 What a backend can do with this, and what it cannot

These signals describe a state machine, not an inference call. The engine
invokes no model: the host runtime does, and it owns that telemetry. So the
natural consumer is a general observability backend, not an LLM-operations
platform — those organise their surfaces around prompts, tokens, cost and
model, and have nothing here to render.

| Tier | Examples | What lands |
| --- | --- | --- |
| Renders as-is | Honeycomb, Pydantic Logfire, Jaeger, Grafana Tempo | No LLM-specific view to miss, so the namespace arrives as first-class queryable fields and a trace view is time-in-phase |
| Ingests, renders generically | Datadog LLM Observability, Langfuse, Braintrust, Arize, LangSmith, W&B Weave | Spans store and query, but fall outside the LLM surfaces, which key on `gen_ai.*` attributes this emitter does not produce |

Views are authored either way. No backend ships a dashboard for an application
namespace, so time-in-phase, gate-failure rate, and stalls are built once
against whichever backend is chosen.

**Answerable from the event line alone:** where wall-clock goes per phase and
per run; gate failure counts split by deterministic, review, and human;
rework, including the implementation-to-drafting return that carries a run
five phases backwards; how close a run is to a retry cap; which transitions
carried an override; and a phase exceeding a declared duration.

**Not answerable, and each has a reason:**

- *Token or cost attribution* — the host owns the inference call, so no cost
  signal reaches this emitter.
- *Why a review failed* — the line carries an outcome, never finding content
  or per-role attribution.
- *A run killed mid-phase* — closing evidence is written by the next
  transition, so a terminated run's final phase has no record.
- *Cap exhaustion versus a stall* — a cap refuses the transition, and a
  refused transition writes nothing.
- *Output quality* — evaluation is a separate plane; activation and judge
  evals live beside each skill and run offline.

Treat that second list as the boundary of what an operator may conclude from
this log, not as a backlog.

**Cost belongs to the host, and already has a home there.** Claude Code carries
its own OpenTelemetry instrumentation, off until `CLAUDE_CODE_ENABLE_TELEMETRY`
is set, with independent exporters for metrics, logs, and traces. It emits
`claude_code.token.usage` and `claude_code.cost.usage`, and its
`claude_code.api_request` event always carries model, cost, tokens, and
duration. An administrator can fix all of it through managed settings, which
lock the destination and drop conflicting developer variables. Token counts are
recorded when the API response returns usage data, so an aborted request may
carry none.

A skill cannot reach any of that. Skills run as subprocesses of the CLI and
never see the API response envelope; hook payloads carry no usage either. So
cost is not a gap in this envelope — it is a signal that belongs to a layer
above it, and a proxy or gateway that intercepts the model call is the other
honest place to capture it.

**Token visibility from a pack is therefore ruled out, not deferred.** No
field, flag, or later revision of this envelope can supply it, because the
number is not observable from where this code runs. A proposal to add one is
answered by this paragraph rather than by a design round. What remains open is
only whether to correlate against the host's own export.

The consequence for design is **correlate, never duplicate**. Point both
emitters at one collector and join in the backend rather than teaching this
engine to guess at a number it cannot observe. Note the two carry different
data classes: the host's attributes include `user.id`, `user.email`, and
`organization.id`, while this envelope carries a run identifier and a spec
path and no identity at all. Combining them in one view combines their
disclosure, so that is an operator's decision to make deliberately.

### 7.4 What these metrics can evaluate

Evaluation in this repository happens at two times, and telemetry serves only
one of them. Keeping them apart is the whole of this section.

**Build-time evaluation** runs before anything ships, against fixtures whose
answers are known. Activation sets ask whether a skill fires on the prompts it
should and stays quiet on the ones it should not. Judge rubrics score output
against a recorded expectation. Frozen cases grade a procedure against a
prepared input. All of them share one property: **a reference answer exists**,
which is what lets them return a verdict and gate a release.

**Runtime evaluation** watches real runs, where no reference answer exists. A
real delivery run has no expected output to compare against — if it did, the
run would be unnecessary. This is the only kind telemetry can serve, and its
questions are therefore about *populations and change*, never about whether one
run was correct.

Five runtime questions these signals can answer:

| Question | Signals | Shape |
| --- | --- | --- |
| Is this run unlike the population? | `phase_s`, round counts | anomaly |
| Has the loop degraded since a change? | the same, over time | regression |
| Did an intervention work? | before/after on the same measures | effect |
| Is a run in trouble right now? | `phase_s` past threshold, `budgets` near cap, `waived` | operational |
| Where does elapsed time go? | `phase_s` split by `awaiting_input` | attribution |

The fifth is the cost handle. Time in a state that waits on a human costs
nothing; time in implementation or review costs tokens. `awaiting_input` is
what separates the two, so elapsed-time-excluding-human-wait is a better cost
proxy than elapsed time, and review rounds — the expensive unit — are counted
exactly.

**What runtime telemetry structurally cannot do.** It cannot say a run produced
a good artifact. There is no oracle at runtime; correctness is established by
build-time fixtures, by the gates, and by human review. A metric that appears
to grade quality from runtime data alone is measuring a proxy and should name
it as one.

**On trajectory.** A trajectory evaluation scores an actual path against an
expected one — which makes it build-time by construction, because the
expectation is the reference. At runtime there is no expected path to compare
against, and two further properties make the comparison unnecessary here: the
state machine already refuses an illegal transition, so an invalid path cannot
occur; and many legal paths are equally correct, because rework is a designed
edge rather than a deviation. What runtime data supports is trajectory
*description* — how often a run returns to drafting, how rounds distribute —
which characterises a population and diagnoses an outlier. It does not grade a
run, and calling it an evaluation would imply a pass mark that nothing here
can issue.

**Non-goal.** None of this is a tuning target. Under optimisation pressure an
automated loop converges on the evaluation boundary rather than the task
boundary, and this loop is agent-driven and can read its own measurement design
from the repository. These signals exist to diagnose; the moment one becomes a
target it stops measuring delivery and starts measuring compliance.

### 7.5 How an exporter would be configured

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

`831f8e92f`

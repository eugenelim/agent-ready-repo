# OpenTelemetry envelope for work-loop lifecycle events

> Discipline: applied (practitioner-pattern survey)

Commissioned 2026-09-10 to pilot the telemetry envelope named by the
["Telemetry events schema" research thread](../roadmap.md#shaping-queue--research-threads),
which fixes eight lifecycle events — `spec-started`, `gate-reached`,
`gate-passed`, `gate-failed`, `gate-waived`, `budget-exceeded`, `spec-stalled`,
`spec-shipped` — and feeds the ecosystem `INI-005` initiative. That initiative
is listed under the roadmap's "Not in scope (this repo)" with trigger
"INI-004 M1 ships"; the scope owner authorised spiking it here on the
understanding that parts of it stay external. Note that roadmap `INI-005`
("Infra & Observability") is unrelated to this repository's own `ini-005`
("AgentBundle Portable Catalogue Tooling"), closed complete 2026-07-31.

The survey question was whether the OpenTelemetry GenAI (LLM) event standards
can serve as that envelope, and how it should be gated, exported, and viewed.
Retained so the follow-on spec can cite it rather than restate it. Findings are
cited to their sources and labelled by evidence class; the measurements in
[§ What the pilot measured](#what-the-pilot-measured) are first-party and come
from a recorded run rather than from the literature.

Confidence tags state how far a finding transfers to the decision here:
`[high]` means multiple strong and directly applicable sources agree;
`[moderate]` means the evidence is credible but has a transfer or coverage
limit; `[low]` means it is useful only as a candidate direction.

---

## Findings

### F1 — GenAI semconv has no home for workflow lifecycle events `[high]`

The GenAI conventions moved to a dedicated repository,
[`open-telemetry/semantic-conventions-genai`](https://github.com/open-telemetry/semantic-conventions-genai),
with **no stable tagged release**; every `gen_ai.*` attribute, span, metric and
event carries the **Development** stability badge. The event surface has been
consolidated to exactly two events —
`gen_ai.client.inference.operation.details` and `gen_ai.evaluation.result` —
both opt-in, both about inference. Agent-level *spans* do exist
(`gen_ai.operation.name` ∈ `create_agent`, `invoke_agent`, `invoke_workflow`,
`execute_tool`, `plan`) with `gen_ai.agent.id`/`name`/`description`/`version`
and `gen_ai.workflow.name`.

There is **no defined event type for non-inference workflow state
transitions** — no "phase entered", "gate passed", "budget exceeded", "run
stalled". Confidence is `[high]` because this is an absence read directly off
the normative documents, corroborated by two independent practitioner analyses.

### F2 — CI/CD semconv is more stable but domain-orthogonal `[moderate]`

`cicd.pipeline.*` is at **Release Candidate** — materially ahead of GenAI's
Development status — and defines pipeline and task run spans,
`cicd.pipeline.result`, and the metrics `cicd.pipeline.run.duration`,
`cicd.pipeline.run.active`, `cicd.pipeline.run.errors`. But those pages contain
no mention of agentic workflows and no guidance on choosing between
`cicd.pipeline.*` and `gen_ai.*`. Applying it to an agent loop is a
practitioner extrapolation that no normative text authorises or forbids.
Downgraded for `stale prior art` risk: a Release-Candidate convention still
moves.

### F3 — Do not invent names under `gen_ai.*` `[high]`

OTel's [naming guidance](https://opentelemetry.io/docs/specs/semconv/general/naming/)
hard-reserves only `otel.*`, but **explicitly warns against** using an existing
semantic-convention namespace as a prefix for application-specific names,
because a later upstream addition then clashes. So `gen_ai.workflow.gate_passed`
is the wrong shape; an application namespace emitted *alongside* standard
`gen_ai.*` attributes is the safe one.

### F4 — `OTEL_SEMCONV_STABILITY_OPT_IN` is the wrong gate `[high]`

It is a **convention-migration bridge**, not a privacy or egress control. It
takes a comma-separated token list (`http`, `http/dup`, `database`,
`gen_ai_latest_experimental`, and so on), and the HTTP semconv page normatively
says instrumentation "SHOULD drop it in the next major version". Using it as a
feature flag would build on a control designed to be removed.

### F5 — The real off-by-default pattern is a per-feature gate plus no exporter `[high]`

GenAI content capture is gated by
`OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`, **default off**
(`no_content` in the Python SDK's four-value enum), on the stated rationale
that model inputs and outputs are "likely to contain sensitive information
including user/PII data". The normative language is that instrumentations
"SHOULD NOT capture them by default, but SHOULD provide an option for users to
opt in." `OTEL_SDK_DISABLED=true` is the coarse kill switch, replacing the SDK
with a no-op. Shipping with **no exporter configured** is the third accepted
form.

One precedence asymmetry matters: OTel's declarative configuration file, when
`OTEL_CONFIG_FILE` is set, makes `OTEL_*` environment variables **inert**. The
design below deliberately inverts that — see D3.

### F6 — Opt-out without disclosure is a named anti-pattern `[moderate]`

GitHub CLI v2.91.0 enabled telemetry through a changelog line with no consent
prompt; the reaction reached 419 Hacker News points in 24 hours and is now the
canonical cautionary case. Next.js and the .NET CLI carry the same criticism,
Cargo's community rejected the opt-out model outright, and Audacity reversed an
opt-in plan after user objection. Downgraded because the sourcing is commentary
and community reaction rather than controlled evidence, and `survivorship bias`
applies — loud failures are visible while quiet successes are not.

### F7 — One span per phase, not span events `[high]`

Every CI/CD tracing precedent uses run → job → step as root → child →
grandchild spans, so phase duration is span duration with no downstream
arithmetic. Temporal emits two spans per activity (`StartActivity`,
`RunActivity`) specifically so the queue-wait gap is measurable. Decisively,
OTel [announced deprecation of the Span Events API in 2026](https://opentelemetry.io/blog/2026/deprecating-span-events/)
in favour of log-based events, so a new envelope built on `Span.AddEvent()`
would start on a deprecated primitive.

### F8 — Backfill is safe for traces and unsafe for metrics `[high]`

Jaeger and Grafana Tempo document no timestamp-age rejection window; spans
carrying timestamps hours old are accepted. Prometheus is the opposite: its
TSDB rejects any sample older than the newest in its series as out-of-order,
the `out_of_order_time_window` setting is experimental and off by default, and
`spanmetrics`-derived metrics inherit the rejection. **Replay a historical
event log into a trace backend, then derive metrics from the stored traces.**

Two operational gotchas, both `[high]`: Jaeger's UI filters on span **start**
time, so a replayed run is invisible under a default "last 1 hour" lookback
even though it is stored; and Tempo's `live_store.max_trace_idle` (5s default)
fragments a trace across storage blocks if spans arrive gradually, so the whole
trace should be emitted in one batch.

### F9 — A terminal stall is invisible to any span-based view `[high]`

A stall inside a run that finishes appears naturally as a long span. But a run
**killed mid-stall never emits a closing span at all**, because SDKs export on
span end. Detecting that requires a heartbeat record or an out-of-band
watchdog — absence detection, not tracing. This is a structural limit of the
signal, not a tuning problem.

### F10 — Log-file ingestion has four paths, and the default drops history `[moderate]`

The options are the Collector's `filelog` receiver with a `json_parser`
operator chain; the alpha `otlpjsonfilereceiver` (which only reads
OTLP-JSON, not arbitrary application lines); `filelog` plus the `otlpjson`
connector; or a custom exporter process driving an OTel SDK. The recurring
documented operator mistake is that `filelog`'s `start_at` defaults to `end`,
so a freshly deployed collector **silently skips every pre-existing line** of
an append-only file. Durable offset tracking needs a `file_storage` extension;
without one, offsets live in memory only.

---

> **Superseded in part, 2026-09-10.** The measurements below describe the
> engine as it stood when this survey was written, and `core` 2.25.14 changed
> it the same day: the transition line now carries thirteen fields, records the
> override flag, and derives the first phase's start from the run's engine
> state. Three findings in [§ What the pilot measured](#what-the-pilot-measured)
> and one entry under [§ Known unknowns](#known-unknowns) are annotated inline
> where that release closed them. Everything about the external standards
> landscape is unaffected. A spec citing this document should cite the
> annotated claims as history, not as current state.

## What the pilot measured

A throwaway spec was driven through the real `loop-engine.py` for 17
transitions in `code` mode, clearing the actual guards (`approve-plan`,
`schedule`, `check-spec-status`), then exported over OTLP/HTTP and read back to
build a view of time-in-phase, gate failures, and stalls. Three first-party
findings came out of it, none of which the literature could have supplied.

**Only five of the eight roadmap events are reachable from
`.loop-run/events.jsonl`.** *(As measured, before core 2.25.14 widened it to
fourteen.)* The engine writes a seven-field line per transition
(`seq`, `run_id`, `spec`, `from`, `event`, `to`, `at`) over 15 FSM event names.
Walking all 15 against the eight gives:

| Verdict | Roadmap event | Source |
| --- | --- | --- |
| Sourced by an FSM event | `gate-passed` | `reviewers-clean`, `spec-approved`, `plan-approved`, `gates-clean` |
| Sourced by an FSM event | `gate-failed` | `findings-remain`, `spec-rejected`, `plan-rejected`, `gates-failed`, `blocker-applied` |
| Sourced by an FSM event | `spec-shipped` | `done` |
| Derived from another field | `gate-reached` | exact — a transition whose `to` is a gate state |
| Derived from another field | `spec-started` | approximate — start time not recorded |
| Needs an envelope change | `gate-waived` | none — *closed by core 2.25.14 (`waived`)* |
| Needs an envelope change | `budget-exceeded` | none — *partly closed by core 2.25.14 (`budgets`); the cap-reached half stays unreachable while `loop-cohort` owns the counters* |
| Needs an envelope change | `spec-stalled` | none — *`phase_s` added in core 2.25.14; the terminal-stall blind spot below still stands* |

**The retry counters are invisible to the event log.** Measured: after a real
`gates-failed` and a real `findings-remain`, `implementation_retry_count`,
`review_retry_count` and `review_round_count` were all still `0`.
`loop-engine transition` bumps no counter — `loop-cohort review record` and
`loop-cohort record-attempt --phase implement` do, in separate processes. The
caps `max_implementation_retries` and `max_review_retries` (both 5) live in the
work-loop state template. So `budget-exceeded` cannot be emitted without either
a new envelope field or a second read of the cohort `state.json`. For the same
reason `transition --allow-retry-cap-override` leaves no trace, which is why
`gate-waived` is unreachable.

**`cmd_init` writes no event line.** It creates `events.jsonl` empty, so a
run's true start time is recorded nowhere and every first-phase duration is a
lower bound rather than a measurement. One init line closes this.

Separately, five FSM events have no roadmap name at all: `spec-ready`,
`plan-locked`, `wave-complete`, `wave-passed`, and — the material one —
**`contract-amendment`**, a return from the code phase to drafting. The eight
roadmap names cannot express mid-run contract rework, which is precisely the
cost signal
[work-loop delivery efficiency](../intents/work-loop-delivery-efficiency.md)
is trying to see.

---

## Design decisions taken from these findings

| # | Decision | Grounded in |
| --- | --- | --- |
| D1 | Lifecycle events live in an `agentbundle.workloop.*` namespace, never under `gen_ai.*`. GenAI attributes (`gen_ai.operation.name=invoke_workflow`, `gen_ai.agent.name`, `gen_ai.workflow.name`) go on the run span, where they genuinely describe it. | F1, F3 |
| D2 | One child span per phase under one root run span. No span events. | F7 |
| D3 | Off by default. Precedence is environment → installed `.agentbundle/telemetry.toml` → default-off. Environment beats file, inverting OTel's declarative rule, so an operator can disable one run without editing an installed artifact. A malformed gate value fails closed with a one-line reason and exit 2. | F5, F6 |
| D4 | Content capture is a **separate** flag from enablement, also defaulting off. | F5 |
| D5 | A custom SDK exporter rather than a Collector `filelog` receiver, emitting the whole trace in one batch. | F8, F10 |
| D6 | The stall threshold is a constant declared before the run and recorded on the root span, never fitted to the observed data. | F9 |
| D7 | `spec-stalled` is reported as a derived threshold, and the terminal-stall blind spot is stated in the view rather than papered over. | F9 |

The pilot's own gate was exercised in five cases before anything was exported:
no configuration, endpoint set but not enabled, enabled with no endpoint, file
enabled with environment overriding it off, and a malformed value. Only the
fully configured case sent data.

---

## Known unknowns

- **Known-unknown:** what stall threshold suits this loop. The pilot used a
  declared 30s against a 247s synthetic run; a real agent-paced run is minutes
  to hours per phase. Would be closed by the phase-duration distribution over
  the 113 natural repair commits that
  [the repair provability audit](repair-provability-audit-design.md) already
  identifies.
- **Known-unknown:** whether `cicd.pipeline.*` at Release Candidate is a better
  long-term home than a private namespace. Would be closed by an OTel SIG
  statement on agentic-workflow routing, which does not exist yet.
- **Known-unknown:** the exact accepted values for the GenAI content-capture
  flag in Java and .NET. Only the Python SDK's four-value enum is fully
  documented in primary sources.
- **Unknowable:** whether `gen_ai.*` will grow a workflow-lifecycle event type.
  The `plan` and `invoke_workflow` operation names suggest the SIG intends to,
  but nothing is published and the conventions are pre-stable, so any name
  chosen today may be invalidated. No available evidence settles it.
- ~~**Unknowable:** the true start time of a run's first phase from the current
  envelope. `cmd_init` records nothing, so the data never existed — no analysis
  recovers it, only an engine change does.~~ **Resolved 2026-09-10 by core
  2.25.14**, and the reasoning was wrong rather than merely overtaken:
  `cmd_init` does record a start, as `last_transition_at` in
  `engine-state.json`. The data existed in a file this survey did not check.
  Classifying it unknowable was a failure to look, not an absence of evidence.

---

## Companion artifact

The vocabulary question this survey raised — whether the workflow orchestrators'
terms could be adopted rather than inventing our own — is answered in
[the adoption bake-off](workflow-lifecycle-vocabulary-comparison-matrix.md).

## Open follow-ons from the 2026-09-10 review

Two reviewers examined the `core` 2.25.14 envelope change. The claim defects
they found were fixed in that release; the design defects below were
deliberately registered instead, because each needs a decision rather than a
repair. They share one root cause: **the engine writes the line, but
`loop-cohort` owns the retry counters and moves them in a separate step**, so
the line reports a lagging snapshot of state it does not control.

1. **The counter-ownership split.** `loop-cohort` increments the retry
   counters after the transition fires, so any line reports a budget that lags
   by one round. A `retry_state` field was shipped against this and withdrawn
   before release: on the implementation axis its cap value was unreachable
   entirely, and counting the events answers the question anyway. Deciding this
   means choosing where the counter is read, not adding a field.

2. **`budgets` can contradict the enforced cap.** The guard resolves an absent
   or non-integer cap to its own default and enforces it; the snapshot reports
   `null`. A line can therefore show no cap for a run about to be refused.
   Fixing it means sharing one cap-resolution helper between guard and
   snapshot.
3. **`wave-passed` is classified as no decision.** All three exits from
   `CODE-VERIFICATION` are outcomes of the same gate, but `wave-passed` gets
   `result: null` while `gates-clean` gets `success`, so a multi-wave run
   counts every verification failure and only its final pass. `plan-locked` has
   the same problem in `spec-plan` mode, where it is the terminal transition
   and so a completed run reports no result at all.
4. **The line carries no schema version.** `engine-state.json` has
   `SCHEMA_VERSION`; the event line has none. The pack and its consumer
   (`agentbundle`'s workspace MCP) version independently, so a reader cannot
   distinguish "written by a writer too old to emit this field" from "written
   as unknown" — the silent-zero failure the null-not-omitted rule exists to
   prevent.
5. **The two event-classification maps have no completeness guard.**
   `_GATE_RESULTS` and `_RETRY_BUDGET_FOR_EVENT` are hand-maintained and sit
   far from the transition tables; a newly added FSM event silently gets
   `result: null`. The repository already uses table-walking completeness
   guards for this class.
6. **The reader side has no executing test.** Every case in
   `packages/agentbundle/tests/test_workspace_mcp_event_bridge.py` is a skip
   stub, so the compatibility claim rests on code inspection alone.
7. **`ADR-0064` describes the line as seven fields** and cites a
   `design.md:317` location that no longer resolves. One home should be
   canonical for this schema.

Separately and already documented in the pack's `state-schema.md`: a retry cap
reached without an override is refused by a guard, and a refused transition
writes no line, so budget exhaustion is indistinguishable from a stall in the
event log alone. Closing that means recording refusals.

## Sources

**Primary (normative OpenTelemetry).** The `semantic-conventions-genai`
repository with its `gen-ai-agent-spans.md` and `gen-ai-events.md`; the
`gen_ai` attribute registry; general naming conventions; `cicd-spans` and
`cicd-metrics`; the Configuration and Environment Variable specifications;
declarative-configuration documentation; the 2026 span-events deprecation
announcement; the 2022 Jaeger-native-OTLP announcement; Jaeger v1.46.0 release
notes and v1.76 documentation; Grafana Tempo trace-ingestion and
long-running-trace documentation; the Collector `filelogreceiver`,
`otlpjsonfilereceiver` and `otlpjsonconnector` READMEs; .NET CLI telemetry
documentation.

**Secondary and practitioner.** The OTel GenAI observability blog (2026);
Greptime's GenAI semconv analysis (2026-05); a dev.to GenAI-semconv-stability
analysis (2026-07); the CNCF distributed-tracing-for-CI post (2026-09); Dash0's
GitHub Actions tracing guide; Temporal observability documentation; PromLabs'
out-of-order-sample analysis (2022); byteiota and marcon.me CLI-telemetry
commentary.

**Independence note.** The three GenAI-status sources (the OTel blog, Greptime,
and dev.to) are separate publishers but all read the same pre-stable
specification, so they triangulate the *reading* rather than the *fact*. The
fact is taken from the normative repository directly.

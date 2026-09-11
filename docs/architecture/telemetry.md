# Telemetry

## 1. Purpose and boundary

A pack records what its own execution did, so an operator can see where a run
spent its time and which gates it failed. Recording is local and unconditional;
sending anything anywhere is a separate, absent component.

This spans several parts of the system rather than belonging to one. The code
that records sits in a pack. The settings come through the catalogue and the
installer. Anything that reads the result is outside the repository. One line
divides what is possible from what is not. **A pack records what its own
code did. It cannot record what the model did**, because the tool running the
session makes the model call and a pack never sees the reply.

Out of scope: the phase machine these events describe ([loop
infrastructure](loop-infrastructure.md)); build-time evaluation of skills, which
runs against fixtures beside each skill; and host telemetry, which belongs to
the runtime and is described in § 4.

## 2. Entrypoints

`loop-engine transition` is the only thing that writes today. It adds one JSON
line per phase change to `.loop-run/events.jsonl`. That file sits at the
repository root, is gitignored, and is not meant to last.

No exporter ships. Nothing transmits.

## 3. Owned state and write authority

| State | Location | Write authority | Readers |
| --- | --- | --- | --- |
| Transition events | `.loop-run/events.jsonl` (ephemeral) | `loop-engine.py` | Operators, workspace MCP |
| Round payloads | `docs/specs/**/state.json` (gitignored) | `loop-cohort.py` | Engine guards, operators |

The two join on `<run_id>:<seq>`. The engine writes the run identifier and the
transition sequence; the cohort records a round under
`--operation-id <run_id>:<seq>` and stores it as
`last_review_record_operation_id`. So the event line carries *when* and the
cohort carries *what* — finding fingerprints, their previous-round rotation, and
the recurrence flag `review inspect` computes. A consumer wanting findings per
round or repetition across rounds reads the cohort side through that join; it is
not duplicated onto the line.

## 4. Dependencies and allowed edges

The code that writes depends on nothing outside its own pack. It imports no
library from the installer, reads no installed settings, and has no way to
reach the network.

**Cost belongs to the host.** Claude Code carries its own OpenTelemetry
instrumentation, off until `CLAUDE_CODE_ENABLE_TELEMETRY` is set, with
independent exporters for metrics, logs and traces. It emits
`claude_code.token.usage` and `claude_code.cost.usage`, and its
`claude_code.api_request` event always carries model, cost, tokens and duration.
An administrator can fix all of it through managed settings, which lock the
destination and drop conflicting developer variables. Token counts are recorded
when the API response returns usage, so an aborted request carries none.

A pack cannot reach any of that. Skills run as subprocesses of the CLI and never
see the API response envelope; hook payloads carry no usage either.

**So a pack cannot see token use. That is settled, not postponed.** No field or
flag will supply it, because the number is not visible from where this code
runs. If someone proposes adding one, this paragraph is the answer.

So the rule is **match them up, never copy them**: send both to the same place
and line them up there, rather than teaching this code to guess a number it
cannot see. The two carry different things about people. The tool's records
include a user id, an email address and an organisation id; these lines carry a
run identifier and a spec path and name nobody. Putting them on one screen puts
both in front of whoever is looking, so that is a choice someone should make on
purpose.

## 5. Primary flows

### 5.1 What a line holds

Each line carries thirteen fields: the seven that identify the transition
(`seq`, `run_id`, `spec`, `from`, `event`, `to`, `at`) and six that describe it
(`phase_started_at`, `phase_s`, `result`, `awaiting_input`, `waived`,
`budgets`).

Three rules govern the shape.

- **Unknown is written as `null`, never left out.** A missing key reads as zero
   to anything adding up durations or comparing a counter against a limit. So a
   field the engine cannot work out is still there, holding `null`.
- **A decision, not a count.** `result` records what a gate decided. It uses
   OpenTelemetry's CI/CD result words rather than ones we made up. How many
   attempts a run has taken is not on the line. Counting the lines answers
   that, and putting a count on each one would give the same fact two homes.
- **`budgets` is a copy, not the original.** `loop-cohort` owns the retry
  counters and changes them in a later step, so the line shows where they stood
  one round ago. The pack's `state-schema.md` spells out what follows from that.
  Those limits change what the numbers mean; they are not small print.

The line is **always written**. There is no switch. The file is local and
gitignored, and nothing leaves the machine.

### 5.2 Export is a separate concern, and it is off

Sending the recorded lines anywhere — to a collector, a dashboard, a hosted
service — is not part of the code that writes them. The pack writes a file.
Anything that sends is a separate piece of software, and it decides separately
what it is allowed to send.

Nothing like that ships today. Three things are already decided for whenever it
does. The [standards survey](../product/research/agent-loop-otel-envelope-survey.md)
and the [vocabulary comparison](../product/research/workflow-lifecycle-vocabulary-comparison-matrix.md)
carry the evidence.

- **OTLP carries it, and the names stay ours.** No standards body has agreed
  names for phases, gates, budgets or stalls, and the closest standard dropped
  the very terms for waiting on a person that this loop needs.
- **Off unless someone turns it on.** Not just "no address set by default" —
  someone has to say yes, and a value nobody can read counts as no rather than
  as yes.
- **Sending the contents is a second, separate yes**, also off by default, so
  agreeing to send timings never means agreeing to send text.

What an adopter actually gets is stronger than a setting: if you never install
the thing that sends, nothing can send, whatever any file says.

### 5.3 How an exporter would be configured

Settings use what the repository already has for adopter-owned pack
configuration. Nothing new is needed.

**Catalogue-level default.** A pack declares a scope-keyed
`[pack.layout.repo]` / `[pack.layout.user]` table in its `pack.toml`. At
install, `_append_layout_section` appends a section into an adopter-owned
`agentbundle-layout.toml` — repo scope at `<repo>/agentbundle-layout.toml`, user
scope at `<user-root>/.agentbundle/agentbundle-layout.toml`.

Three things about how it writes are why it suits a setting like this:

| Property | Consequence |
| --- | --- |
| append-if-exists | An adopter with no layout file gets nothing written |
| never-create | Installing a pack cannot bring the file into being |
| never-overwrite | A section the adopter already authored is left alone |

So a shipped default can only land in a file the adopter already chose to keep,
and can never replace a decision they have already made.

**Which scope wins is decided per setting, not per file.** `desk-research`
reads the user file first, so someone's personal notes folder follows them
between repositories. Whether to send data off the machine is a team decision
rather than a personal one, so telemetry would read the repository file first
instead. Same two files, opposite order — said here because you cannot guess
one from the other.

**Environment override.** An environment variable takes precedence over both
files, so an operator can disable one run without editing an installed artifact.
This inverts OpenTelemetry's own rule, where a declarative configuration file
makes `OTEL_*` inert; the inversion is deliberate, because the file here is an
inherited default rather than an operator's own statement.

> **The shipped-default half does not work today.** Traced and confirmed by
> execution: `_append_layout_section` writes nothing for any pack in the
> catalogue, because the writer and readers disagree on section, key and value
> name. See [agentbundle § 7.1](agentbundle.md#71-known-drift--the-install-time-layout-default-writes-nothing).
> Adopter-authored layout files and an environment variable both work, so an
> exporter can be configured today — but a catalogue-level default cannot ship
> until that drift is settled.

## 6. Failure and recovery behavior

Recording never gets in the way. Any failure prints a warning and the phase
state is still written. A field the writer cannot work out becomes `null`. A
cohort file it cannot read gives a `budgets` object with every key present and
every value `null`. Nothing here can cost a run its transition.

Two things follow that are worth knowing. Kill a run mid-phase and that phase
is missing rather than long, because the next step is what records the previous
one. And hitting a retry limit refuses the step, so nothing is written. In this
file alone, a spent budget looks exactly like a stall.

## 7. Observability and evidence

These numbers describe a state machine, not a model call. So a general
monitoring tool suits them better than an LLM-focused one. Those build their
screens around prompts, tokens, cost and model, and none of that appears here.

**Searching on our own attribute names works with no setup nearly
everywhere.** Surveyed 2026-09-10 against vendor documentation. This is a
snapshot, not a maintained list — products rename and change, so confirm
against the vendor's own docs before relying on a row.

| Backend | Search our names, no setup | Note |
| --- | --- | --- |
| Dynatrace | Yes | DQL reads any attribute; OTLP over HTTP only, no gRPC |
| Splunk Observability Cloud | Yes | Raw traces yes; built-in breakdowns need a tag indexed first |
| Datadog | Yes | Live search is 15 minutes; older needs a retention filter |
| Elastic | Yes | Unmapped attributes land under `labels.*` |
| Azure Monitor | Yes | Reaches `customDimensions`; ingest needs a Collector and Entra auth |
| Google Cloud Trace | Stored | 1,024 attributes per span; UI filter reach not confirmed |
| ServiceNow Cloud Observability | Yes | Lightstep heritage, OTel-native |
| Honeycomb | Yes | No LLM-specific layer to fall outside of |
| Pydantic Logfire | Yes | OTel-native |
| Grafana Tempo | Yes | Dedicated columns are a speed-up, not a prerequisite |
| Jaeger | Yes | Exact match only; a Cassandra backend can be set to stop indexing tags |
| Chronosphere | Yes | Free to search; 1,000-series cap once made a metric |
| Sumo Logic | Yes | — |
| Coralogix | Yes | Mapping to its conventions recommended for built-in views |
| IBM Instana | Visible | Readable in a trace; not a first-class filter surface |
| AWS X-Ray | **No** | Metadata is not filterable; annotations are, capped at 50 per trace |
| Prometheus | **n/a** | Metrics only — not a sink for this shape |

Two things that do not move are worth writing down.

**Searching is cheap; aggregating is where cardinality costs.** Every platform
that charges or refuses does it at the same boundary — when an attribute
becomes a metric dimension, not when it is searched. Splunk runs a cardinality
check before indexing a tag. Chronosphere caps a trace-derived metric at a
thousand series. Datadog bills custom metrics per name-and-value combination.
Prometheus advises keeping a metric's cardinality under ten.

**So `run_id` is a search key and never a dimension.** It differs on every run,
so its range has no bound. Finding one run by it is exactly its job. Grouping
by it turns every run into its own series, which is the shape all four of those
limits exist to stop. Anything counting runs groups by spec, which is bounded.

**Prometheus is not a sink for this at all.** It stores numbered samples
against labels, with no model for an event or a bag of attributes — its OTLP
endpoint takes metrics only. These lines would have to become counts and
histograms first, losing the timestamps, the identifiers, and every attribute
not named as a dimension. It also refuses a sample older than the newest in its
series, so replaying a recorded log is the case it least supports. It can hold
aggregates derived from these lines; that is a different job from storing them.


### 7.1 What these numbers can and cannot tell you

Checking happens at two different times, and these numbers serve one of them.

**Before anything ships**, checks run against prepared examples whose right
answers are already written down — does the skill trigger on the prompts it
should, is the output good, does the procedure handle a known case. Having the
right answer to hand is what lets those checks pass or fail a release.

**While real work runs**, there is no right answer to compare against. If we
knew what the run should produce, we would not need the run. So the questions
change shape: is this run unlike the others, has the loop got worse since we
changed something, did a change help, is a run in trouble right now, and where
did the time go.

That last one is the cost handle. Time spent waiting for a person costs
nothing; time spent implementing or reviewing costs tokens. `awaiting_input`
tells the two apart, so elapsed time minus waiting is a closer guide to cost
than elapsed time, and review rounds — the expensive part — are counted
exactly.

None of it says whether a run produced something good. There is nothing at run
time to check against. Whether the work is right is settled by the prepared
examples, by the gates, and by people reading it.

**On comparing the path a run took.** Scoring a path means comparing it to the
path it should have taken, which again needs an answer written in advance. At
run time there is none — and two things make the comparison pointless here
anyway. The state machine already refuses a step that is not allowed, so a run
cannot take an invalid path. And several different paths are equally right,
because going back to fix something is a designed part of the loop, not a
mistake. What the numbers do support is *describing* paths: how often runs go
back to drafting, how rounds spread out. That tells you about the set of runs
and points at an odd one. It does not mark any run pass or fail.

**Do not tune against these.** Push an automated loop to improve a number and
it will improve the number rather than the work. This loop is driven by an
agent that can read its own measurements in this repository. They are here to
help someone work out what happened.

**What the lines answer on their own**

- Where the time went, per phase and per run.
- How many gate failures there were, split by automated check, review, and
  person.
- How much rework happened. That includes the jump from implementation back to
  drafting, which sends a run five phases backwards.
- How close a run came to a retry limit, and which steps used an override.
- Which phases ran longer than a stated threshold.

**What they do not answer, and why**

| Question | Why not |
| --- | --- |
| What did it cost? | The tool running the session makes the model call |
| Why did a review fail? | The line records an outcome, never the findings |
| What happened to a run that was killed? | The next step writes the previous phase; there is no next step |
| Was it a stall or a spent budget? | Hitting a limit refuses the step, and a refused step writes nothing |
| Was the work any good? | Nothing at run time can answer that |

## 8. Mechanical invariants

- The first seven fields keep their names, order and values, so adding a field
  never breaks an existing reader.
- A field the writer cannot work out is written as `null` and never left out.
- Recording never stops a transition from completing.
- Nothing in a pack sends. Anything that sends is installed separately.

## 9. Relevant records

- [OpenTelemetry standards survey](../product/research/agent-loop-otel-envelope-survey.md)
  — the standards landscape, the off-by-default pattern, and the registered
  follow-ons.
- [Workflow lifecycle vocabulary bake-off](../product/research/workflow-lifecycle-vocabulary-comparison-matrix.md)
  — why the domain vocabulary is ours and which shapes were borrowed.
- [Loop infrastructure](loop-infrastructure.md) — the phase machine these events
  describe.
- [`agentbundle` § 7.1](agentbundle.md#71-known-drift--the-install-time-layout-default-writes-nothing)
  — the inert install-time layout default.

## 10. Last verified against commit

`bd8b69443`

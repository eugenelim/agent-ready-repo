# Spec: loop-telemetry-export

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0108 (authored by this delivery — separate sender distribution, versioned event line)
- **Brief:** none
- **Discovery:** none
- **Contract:** [`contracts/jsonschema/loop-run-event.schema.json`](../../../contracts/jsonschema/loop-run-event.schema.json)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An adopter who wants their work-loop runs visible in an observability backend
installs one small tool, points it at an OpenTelemetry Collector, and sees a log
record per phase transition. The tool is `loop-telemetry-export`, a separately
installed Python distribution. Nothing in any installed pack can send: an
adopter who never installs the tool has a structural guarantee, not a
configuration promise. An adopter who installs it but configures no endpoint
still sends nothing, and the tool says so rather than failing.

Success for that adopter is a Splunk, Honeycomb, Grafana or Datadog view of
where a run spent its time and which gates it failed, reached by running a
Collector they already know how to run. Success for the repository is that the
event line gains a version, so the format can change later without breaking a
reader that is already consuming it.

The exporter reads `.loop-run/events.jsonl` and emits OTLP logs over HTTP with
JSON encoding. It targets a Collector rather than a vendor endpoint: Splunk's
own OTLP endpoint refuses JSON with HTTP 415, and Splunk's documentation directs
callers to the Collector they deployed. The Collector's `otlp` receiver accepts
JSON with no configuration, so one encoding reaches every backend that has a
Collector in front of it.

### Exit codes

| Code | State |
| ---: | --- |
| 0 | Records sent |
| 0 | No endpoint configured — nothing sent |
| 1 | Usage error, unreadable or malformed input, configuration error, send failure after the retry budget, or an unhandled exception |
| 2–9 | Never returned — reserved credential/auth band owned by [`credentialed-cli-exit-code-contract`](../credentialed-cli-exit-code-contract/spec.md) |
| 130 | Interrupted by SIGINT |

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — a sender outside every pack, and a versioned line, are both reversals of stated current architecture | `docs/adr/0108-*.md` | spec owner | Accepted ADR naming the § 5.2 interpretation and the per-engine default | ADR merged and cited by `telemetry.md` |
| Current architecture | Applicable — `telemetry.md` § 2 states "No exporter ships", § 5.3 carries a stale blockquote, and two anchors to `agentbundle.md § 7.1` are dead | `docs/architecture/telemetry.md` | spec owner | § 2, § 5.2, § 5.3 and § 8 read true against the shipped tool; both anchors resolve | Anchors resolve; no claim contradicts the shipped tool |
| Interface compatibility | Applicable — the event line becomes a versioned wire format with readers outside this repository | `contracts/jsonschema/loop-run-event.schema.json` + a row in `contracts/README.md` | spec owner | Schema validates a recorded corpus of real event lines | Schema committed, registry row present |
| User-facing promise | Applicable — an adopter must learn the capability exists, what it sends, and where | `guides/core/how-to/export-loop-telemetry.md` + `packages/loop-telemetry-exporter/README-pypi.md` | spec owner | Disclosure sentence naming capability, payload and destination | Guide indexed; PyPI README renders |
| Release history | Applicable — a new published distribution and a `core` content change | `docs/product/changelog.md` + `packages/loop-telemetry-exporter/CHANGELOG.md` | release workflow | Version bump with changelog entry; tag matches `pyproject` | Tag published, both changelogs updated |
| Maintainer procedure | Applicable — a third distribution with its own release path | `packages/loop-telemetry-exporter/AGENTS.md` | spec owner | Test command and release-coupling note | File present and accurate |
| Current product truth | Applicable — the spec must be discoverable | `docs/specs/README.md` | spec owner | Row in the active list | Row present |
| Reusable learning | Applicable — the checkpoint validation and the argparse/exit-code collision generalise | `project-knowledge` public seam | work-loop closeout | Capture receipt | Receipt recorded or `project-knowledge unavailable` |
| Operations | Not applicable — the tool runs on a developer machine or in CI, owns no deployed infrastructure, and has no runbook surface in this repository | — | — | — | — |

## Boundaries

### Always do

- Read the repository layout file before the user layout file. Sending data off
  the machine is a team decision, not a personal one.
- Send nothing when no endpoint resolves, and say so on stderr.
- Degrade to a warning. A failure inside the exporter never alters, blocks or
  rewrites `.loop-run/events.jsonl` or any engine state.
- Treat every line of the input file as untrusted data: bound its size, reject
  what does not parse, and continue past a malformed line rather than aborting.

### Ask first

- Adding any runtime dependency outside the Python standard library.
- Supporting an authenticated endpoint. A token makes this a credentialed
  primitive, which pulls in `credbroker`, the `auth:` lint contract and the
  `2 USER_ACTION` exit code.
- Emitting spans instead of logs, or adding any new event to the envelope.
- Claiming an exit code in the 2–9 band.

### Never do

- Send from inside a pack. The sender ships only in this distribution; no pack
  gains network capability.
- Add a new top-level directory, or a new module boundary inside `packs/core`.
- Put `run_id` in a metric dimension. It is a search key; Splunk runs a
  cardinality analysis before indexing a tag and rejects unbounded ones.
- Retry a request whose response carries a non-empty `partialSuccess`.
- Write a checkpoint, position file, or any other durable state under
  `.loop-run/` or elsewhere.
- Ship a catalogue-level `[pack.layout.*]` default for telemetry.

## Testing Strategy

**Encoding conformance: TDD, exercised by an integration test.** Measured
against a live Collector (`telemetry.md` § 10.3): structural errors fail loudly
with HTTP 400, so a round trip is a strong signal rather than a weak one. The
residual risk is narrower than "silent discard" — a payload with correct
structure and wrong attribute names is accepted and stored, so the failure mode
is *wrong data, not absent data*, and no response assertion can see it.

Two independent checks therefore remain, for their own reasons. The golden
payload pins the emitted layout so any change to it appears in a diff and
attribute drift is caught at review. The round trip proves a real receiver
accepts and parses what we emit, which the golden cannot establish on its own.

**Configuration resolution and off-by-default: TDD.** Pure precedence logic over
environment and two files. Compressible invariant, no network.

**Retry, backoff and partial-success handling: TDD.** A seam in front of the
transport lets each response shape be driven directly.

**Exit codes: goal-based check.** Each state is a one-line invocation and an
observed status.

**Schema version on the event line: TDD.** A field on a dict, plus the replay
path, both checkable in the existing `loop-engine` suite.

**The installed tool end-to-end: visual / manual QA.** The real console script
is invoked against a real `events.jsonl` and a real Collector, and the observed
stdout, stderr and exit code are recorded. A passing unit gate does not satisfy
this.

## Acceptance Criteria

- [ ] **AC1.** With no `[telemetry]` section in either layout file and no
  endpoint environment variable set, the exporter opens no socket, exits 0, and
  writes a line to stderr naming that no endpoint is configured.
- [ ] **AC2.** The endpoint used is the first present of, in order:
  `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`, `OTEL_EXPORTER_OTLP_ENDPOINT`, the
  repository `agentbundle-layout.toml` `[telemetry].endpoint`, then the user
  `agentbundle-layout.toml` `[telemetry].endpoint`.
- [ ] **AC3.** A value resolved from `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` is
  requested unmodified.
- [ ] **AC4.** A value resolved from any source other than
  `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` is requested with `/v1/logs` appended.
- [ ] **AC5.** For the recorded three-line fixture, the emitted request body
  equals `tests/fixtures/otlp-logs-golden.json` byte for byte.
- [ ] **AC6.** A Collector running an `otlp` receiver and a `debug` exporter
  records three log records whose attribute sets equal the three input lines'
  fields.
- [ ] **AC7.** Every emitted log record carries a `service.name` resource
  attribute, defaulting to `work-loop` when none is configured. Splunk renders a
  record without it as `unknown_service`.
- [ ] **AC8.** A response carrying a non-empty `partialSuccess` produces no
  retry, and its `rejectedLogRecords` count appears on stderr.
- [ ] **AC9.** After an HTTP 429 or 503 carrying `Retry-After: N`, no request is
  issued before N seconds have elapsed.
- [ ] **AC10.** A send is attempted at most 3 times.
- [ ] **AC11.** A single request carries at most 512 log records. The OTLP 64
  MiB request limit is non-binding on this route: 512 records of this envelope
  cannot reach it, and the record count is what fires first. Measured from the
  count of parsed lines in the input file.
- [ ] **AC12.** Send failure after the retry budget exits 1, and exits 0 when
  `--best-effort` is passed.
- [ ] **AC13.** An unrecognised command-line flag exits 1, not 2. The 2–9 band
  belongs to credential/auth states this tool does not have, and `argparse`
  exits 2 by default.
- [ ] **AC14.** No invocation returns an exit code in the range 2 through 9.
- [ ] **AC15.** SIGINT exits 130.
- [ ] **AC16.** A line that does not parse as JSON is skipped with a stderr
  note, and the remaining lines are still sent.
- [ ] **AC17.** Every event line `loop-engine` writes carries `schema` with
  integer value 1.
- [ ] **AC18.** An `events.pending` record lacking `schema` is appended to
  `events.jsonl` unchanged, carrying no `schema` field.
- [ ] **AC19.** `contracts/jsonschema/loop-run-event.schema.json` validates every
  line of the recorded event corpus, and `contracts/README.md` carries its row.
- [ ] **AC20.** `guides/core/how-to/export-loop-telemetry.md` states that the
  capability exists, what the payload contains, and that it reaches the
  configured endpoint — while the tool ships sending nothing.
- [ ] **AC21.** `docs/architecture/telemetry.md` § 5.3 carries no claim that the
  catalogue-level default does not work, and every `agentbundle.md` anchor it
  cites resolves to a heading that exists.
- [ ] **AC22.** `docs/architecture/telemetry.md` § 2 and § 8 describe a sender
  that exists and is installed separately.
- [ ] **AC23.** `loop-telemetry-export --version` prints the installed
  distribution version, and the published tag equals `pyproject.toml`'s
  `version`.

## Follow-ons

- work-intake: the `adapter-root-bins` upgrade gap — `collect_pack_root_bins`
  has one production caller inside the user-scope install path and no reference
  in `upgrade.py`, so `packs/credential-brokers`'s shipped `sso-broker.py` is
  delivered once and never refreshed. Recorded in
  [`loop-telemetry-export-counterpoints.md`](../../product/research/loop-telemetry-export-counterpoints.md);
  routed as its own item on a separate branch.

## Assumptions

- Technical: runtime is Python ≥3.11 (source: `packages/agentbundle/pyproject.toml:9`, `packages/credbroker/pyproject.toml:9`)
- Technical: console-script entry points are precedented (source: `packages/agentbundle/pyproject.toml:31-32`)
- Technical: a new distribution's shape is pyproject, package dir, tests, own `CHANGELOG.md`, `README-pypi.md`, `AGENTS.md` (source: `ls packages/credbroker/`)
- Technical: the PyPI release path is a proven template with trusted publishing and a SHA-pinned publish action (source: `.github/workflows/release-credbroker.yml`)
- Technical: a new PyPI distribution needs no `distribution-routes.toml` entry; those routes are pack package-derivation routes (source: `contracts/distribution-routes.toml:8,26,45`)
- Technical: an additive event-line field breaks neither known reader (source: `packs/core/tests/skills/work-loop/test_loop_engine_events_jsonl.py:125` asserts a superset; `packages/agentbundle/agentbundle/workspace_mcp.py:304` polls by byte offset)
- Technical: OTLP/HTTP JSON is stable but not frozen, and a malformed payload returns HTTP 200 with no signal (source: `docs/product/research/loop-telemetry-export-survey.md` F1/F2 and its counterpoints)
- Technical: Splunk's OTLP endpoint requires `application/x-protobuf` and returns HTTP 415 for JSON; Splunk directs callers to a Collector (source: `docs/product/research/loop-telemetry-export-survey.md`, Splunk compatible-span-formats and send-traces docs)
- Technical: a checkpoint keyed to file identity is stale once the per-run file is recreated, so no position file is kept (source: same survey, checkpoint validation)
- Technical: exit codes 3–9 are a reserved credential/auth band and are not claimed unilaterally (source: `docs/specs/credentialed-cli-exit-code-contract/spec.md:35-44`)
- Technical: `sys.exit` above 255 truncates mod 256 and can report success (source: CPython issue 24052)
- Process: a new dependency goes in the owning package instructions or an ADR; stdlib-only avoids a dependency ADR, not an architecture one (source: root `AGENTS.md` § Coding conventions)
- Process: Tier 1 detect → fail-clean is mandatory and the default, and stdlib is preferred over a pip dependency (source: `guides/_shared/how-to/author-a-skill.md:104-117`)
- Process: released artifacts carry a changelog entry, and separately published packages each update their own `CHANGELOG.md` (source: `docs/CONVENTIONS.md:1011-1014`)
- Process: an ADR is sufficient governance for a third published distribution; no RFC is required (source: user confirmation 2026-09-12)
- Product: the distribution is published within this delivery, not authored and held (source: user confirmation 2026-09-12)
- Product: v1 targets an unauthenticated Collector endpoint; authenticated vendor endpoints are a non-goal (source: user confirmation 2026-09-12, plus the Splunk 415 finding above)
- Product: the exporter tails the file with an in-memory offset and also offers a one-shot mode; duplicate delivery is made harmless by the `run_id:seq` key rather than prevented by state (source: user confirmation 2026-09-12)

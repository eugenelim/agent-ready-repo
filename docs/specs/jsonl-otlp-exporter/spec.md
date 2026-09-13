# Spec: jsonl-otlp-exporter

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0111](../../adr/0111-loop-telemetry-sender-is-a-separately-installed-distribution.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the public surface is a CLI and a mapping-profile interface, both specified inline below
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites.
>
> **This contract is capability-scoped.** No criterion below may name a specific
> consumer, product, repository or catalogue. A consumer-specific obligation
> belongs to that consumer's own integration contract, not here. This rule exists
> because the distribution is published: a public package whose contract names
> its first consumer forces the second consumer to amend a shipped criterion
> rather than add a file.

## Objective

`jsonl-otlp-exporter` reads a newline-delimited JSON event log and sends its
records to an OpenTelemetry endpoint as OTLP logs over HTTP with JSON encoding.
It is a standalone, pip-installable command: a producer writes a JSONL file, and
this sends it, with no coupling between the two beyond the file and a mapping.

It sends nothing until an endpoint is configured. Installing it is the first
consent; configuring an endpoint is the second. A user who does neither has a
tool on disk that cannot transmit.

The producer's field names are not baked in. A **mapping profile** declares which
field carries the timestamp, which carries severity, and which attributes
identify a record; every other field becomes a log-record attribute. Adding a
producer means adding a profile, not forking the package.

It targets a Collector rather than a vendor endpoint. Vendors disagree on
encoding — some accept OTLP/HTTP JSON, others require protobuf — while a
Collector's `otlp` receiver accepts JSON with no configuration, so one encoding
reaches every backend that has a Collector in front of it.

### Exit codes

| Code | State |
| ---: | --- |
| 0 | Records sent |
| 0 | No endpoint configured — nothing sent |
| 0 | Some lines invalid, the rest sent |
| 0 | Send failure after the retry budget, under `--best-effort` |
| 1 | Unreadable or confinement-refused input file |
| 1 | Every line invalid |
| 1 | Usage error, configuration error, refused endpoint, or an unhandled exception |
| 1 | Send failure after the retry budget, or a non-empty `partialSuccess` |
| 2–9 | Never returned — reserved for a consumer's own credential/auth taxonomy |
| 130 | Interrupted by SIGINT |

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — a published package's public contract | `packages/jsonl-otlp-exporter/README-pypi.md` | spec owner | Capability, payload, destination and profile interface documented | Renders on PyPI; AC-0030 green |
| Interface compatibility | Applicable — the profile interface is a published extension point | `packages/jsonl-otlp-exporter/docs/profiles.md` | spec owner | Interface and its compatibility status stated | AC-0031 and AC-0032 green |
| Release history | Applicable — a published distribution | `packages/jsonl-otlp-exporter/CHANGELOG.md` | release workflow | Version bump with entry; tag matches `pyproject` | Tag published |
| Maintainer procedure | Applicable — a distribution with its own release path | `packages/jsonl-otlp-exporter/AGENTS.md` | spec owner | Test command and release coupling | File accurate |
| Decision rationale | Not applicable — ADR-0111 already records why a separate distribution exists; this spec adds no reversal | — | — | — | — |

## Boundaries

### Always do

- Send nothing when no endpoint resolves, and say so on stderr.
- Treat every input line as untrusted: bound its size, reject what does not
  parse, and continue past a bad line rather than aborting.
- Decide input refusal on the opened object, not the pathname: open no-follow,
  then prove the opened descriptor is a regular file inside the resolved root.
- Send only fields a profile declares. An undeclared field is dropped.
- Require HTTPS for any endpoint whose host is not a loopback address.
- Keep the standard library the only runtime dependency.

### Ask first

- Adding a runtime dependency.
- Supporting an authenticated endpoint, which makes this a credential-handling
  tool and changes its threat model.
- Emitting a signal other than logs.
- Claiming an exit code in the 2–9 band.

### Never do

- Name a specific consumer, product, repository or catalogue in an acceptance
  criterion.
- Follow an HTTP redirect, or send to an endpoint carrying user-info.
- Write a checkpoint, position file, or any other durable state.
- Write to, truncate, replace or otherwise modify the input file.
- Put a raw endpoint or redirect target in a message without redacting any
  user-info component first.
- Retry a request whose response carries a non-empty `partialSuccess`.

## Testing Strategy

- **VI-0001 — off-by-default and endpoint resolution (AC-0001, AC-0033, AC-0002, AC-0003, AC-0004):** TDD. Pure precedence logic over an environment mapping and one file; none of it needs a network. AC-0001 asserts the transport seam is never constructed, and AC-0033 asserts the exit and the note separately — a single joined criterion would pass for a build that sent first and printed afterwards.
- **VI-0002 — encoding and the allowlist (AC-0005, AC-0007, AC-0016, AC-0038, AC-0034, AC-0035):** TDD. The encoder is pure, so a byte-exact golden pins the layout. AC-0034 is the default-deny case and takes its own assertion over a field present in the input and absent from the profile: an encoder that forwards unknown fields passes every other case here.
- **VI-0003 — a real receiver parses what is emitted (AC-0006):** goal-based check, exercised by an integration test against a live Collector. The only check that observes attribute *naming*: a structurally valid payload with wrong names is accepted and stored, so neither a rejection nor the golden can see it.
- **VI-0004 — retry and batching (AC-0008, AC-0036, AC-0009, AC-0010, AC-0037, AC-0011):** TDD over a seam in front of the transport. Each response shape is a fixture. AC-0008 and AC-0036 are separated because no-retry and exit-1 fail independently, and a build that suppresses the retry while reporting success passes the first alone.
- **VI-0005 — exit codes (AC-0012, AC-0013, AC-0014, AC-0015, AC-0029, AC-0039):** goal-based check. Each state is one invocation and one observed status. AC-0014 is asserted against the mapping function rather than over every invocation, which is what makes the universal claim checkable.
- **VI-0006 — input confinement (AC-0017, AC-0043):** TDD. A symlinked leaf, a non-regular file, a path escaping the root, and a component swapped between resolution and open are fixtures over one predicate, all asserting the transport seam is never constructed. The swap case is the one that distinguishes descriptor validation from path validation.
- **VI-0007 — size and time bounds (AC-0018, AC-0019, AC-0040, AC-0041):** TDD. Each bound is a function over constructed input. AC-0019 is asserted on encoded bytes by constructing a batch that encodes above the ceiling, not by trusting the input-side arithmetic — the encoding expands the payload, so an input-side bound cannot establish an output-side limit.
- **VI-0008 — modes and file lifecycle (AC-0020, AC-0021, AC-0042, AC-0022):** TDD. AC-0022 names its mode, its starting state, the mutation applied, the termination trigger and the records expected, so a build that observes nothing and exits fails it.
- **VI-0009 — record identity (AC-0023):** TDD over the encoder's output. Delivery is at-least-once, so this is the attribute set a consumer deduplicates on.
- **VI-0010 — destination policy (AC-0024, AC-0044, AC-0025, AC-0026, AC-0045, AC-0027, AC-0028):** TDD over the opener construction. Seven separate failure modes with seven separate remedies. AC-0025's fixture resolves a host to both a loopback and a routable address, which is the case that distinguishes validating a resolution from binding the connection to it.
- **VI-0011 — the published contract (AC-0030, AC-0031, AC-0032):** goal-based check over the authored files. Presence and structure are mechanical; wording is not asserted.
- **VI-0012 — release integrity (AC-0046):** goal-based check over the release workflow, exercised by a tag whose version disagrees with `pyproject.toml` and asserting the workflow refuses it.

## Acceptance Criteria

- [ ] **AC-0001.** With no endpoint resolvable from any source, the command opens
  no socket.
- [ ] **AC-0033.** With no endpoint resolvable from any source, the command exits
  0 and writes a line to stderr naming that no endpoint is configured.
- [ ] **AC-0002.** The endpoint used is the first present of, in order:
  `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`, `OTEL_EXPORTER_OTLP_ENDPOINT`, then
  `[telemetry].endpoint` in the TOML file given by `--config`.
- [ ] **AC-0003.** A value resolved from `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` is
  requested unmodified.
- [ ] **AC-0004.** A value resolved from any other source is requested with
  `/v1/logs` appended.
- [ ] **AC-0005.** For the recorded three-line fixture under the reference
  profile, the emitted request body equals the committed golden byte for byte.
- [ ] **AC-0006.** A Collector running an `otlp` receiver and a `debug` exporter
  records three log records in which the field the active profile names as its
  timestamp appears as `timeUnixNano`, the field it names as severity appears as
  `severityNumber`, and each field the profile's allowlist admits appears as a
  log-record attribute.
- [ ] **AC-0034.** A field present in the input but absent from the active
  profile's allowlist appears nowhere in the emitted request body.
- [ ] **AC-0035.** A mapping profile declares four things: its timestamp field,
  its severity field, its record-identity attributes, and the allowlist of fields
  that may be sent.
- [ ] **AC-0007.** Every emitted log record carries a `service.name` resource
  attribute taking the value of `--service-name`, defaulting to the active
  profile's declared name.
- [ ] **AC-0008.** A response carrying a non-empty `partialSuccess` produces no
  retry.
- [ ] **AC-0036.** A response carrying a non-empty `partialSuccess` reports its
  rejected-record count on stderr and exits 1.
- [ ] **AC-0009.** After an HTTP 429 or 503 carrying `Retry-After: N`, no request
  is issued before `min(N, 30)` seconds have elapsed, and a value that is
  absent, negative or unparseable is treated as 0.
- [ ] **AC-0010.** At most 3 send attempts are made per run, counted across all
  requests the run issues.
- [ ] **AC-0037.** A run whose send attempts are exhausted stops issuing requests
  rather than continuing with the next batch.
- [ ] **AC-0011.** A single request carries at most 512 log records, counted from
  the parsed lines of the input file; record 513 begins the next request.
- [ ] **AC-0012.** Send failure after the retry budget exits 1, and exits 0 when
  `--best-effort` is passed.
- [ ] **AC-0013.** An unrecognised command-line flag exits 1, not 2.
- [ ] **AC-0014.** Every exit from the command passes through one exit-mapping
  function, which returns only 0, 1 or 130; no other value can reach the caller.
- [ ] **AC-0015.** SIGINT exits 130.
- [ ] **AC-0016.** A line that does not parse as JSON is skipped, and the
  remaining lines are still sent.
- [ ] **AC-0038.** A skipped line is reported on stderr with its line number.
- [ ] **AC-0039.** A run in which no line yields a valid record exits 1.
- [ ] **AC-0017.** The command opens the path given by `--input` with no-follow
  semantics and sends nothing unless the opened descriptor is a regular file
  whose identity resolves inside the directory given by `--root`, which defaults
  to the working directory. Refusal is decided on the opened object, never on the
  pathname alone.
- [ ] **AC-0018.** A line longer than 64 KiB measured to and excluding its
  terminating newline is refused before it is decoded, and the remaining lines
  are still sent.
- [ ] **AC-0019.** A request body is at most 8 MiB measured on the encoded bytes
  about to be sent. A batch that would exceed it is split before sending, and a
  single record that cannot fit is dropped with a stderr note. This is the bound
  that fires first: the 64 MiB OTLP protocol limit is never reached because no
  request is issued above 8 MiB.
- [ ] **AC-0040.** A request that has not completed within 30 seconds is
  abandoned, and a run's total send time does not exceed 120 seconds, both
  applying under `--best-effort`.
- [ ] **AC-0041.** A response body larger than 1 MiB is refused before it is
  decoded.
- [ ] **AC-0020.** With no mode flag the command runs one-shot: it reads the file
  once, sends, and exits without waiting for further lines.
- [ ] **AC-0021.** Under `--follow`, a line appended after start is sent without
  restarting the process.
- [ ] **AC-0042.** `--for` accepts a duration as an integer number of seconds and
  ends the run that many seconds after the first read begins.
- [ ] **AC-0022.** Under `--follow`, started against a file holding one valid
  record and then subjected in turn to truncation to zero, replacement by a new
  inode, and a trailing line with no newline, the command sends that first record
  exactly once, sends no record for the conditions themselves, and exits 0 when
  `--for` elapses.
- [ ] **AC-0043.** Started against an absent `--input` path, the command sends
  nothing and exits 1.
- [ ] **AC-0023.** Every emitted log record carries the attributes the active
  profile declares as its record identity, which together identify a record for a
  consumer deduplicating at-least-once delivery.
- [ ] **AC-0024.** An `https` endpoint is accepted at any host, and its
  certificate chain and hostname are verified against the system trust store.
- [ ] **AC-0044.** An endpoint whose scheme is neither `https` nor `http` is
  refused before any request is sent and exits 1; those two are the complete
  accepted set.
- [ ] **AC-0025.** An `http` endpoint is accepted only when every address its
  host resolves to is a loopback address, and the request is issued to one of
  those verified addresses without re-resolving the host.
- [ ] **AC-0026.** An `http` endpoint any of whose resolved addresses is not a
  loopback address is refused before any request is sent and exits 1.
- [ ] **AC-0045.** A refusal or error message naming an endpoint or a redirect
  target carries no user-info component of that URL.
- [ ] **AC-0027.** A redirect response is not followed, and the run exits 1.
- [ ] **AC-0028.** An endpoint whose netloc carries user-info is refused before
  any request is sent and exits 1.
- [ ] **AC-0029.** `--version` prints the installed distribution version.
- [ ] **AC-0046.** A release whose git tag names a version differing from
  `pyproject.toml`'s is refused by the release workflow.
- [ ] **AC-0030.** `README-pypi.md` states what the command sends, what the
  payload contains, and that it reaches the configured endpoint — while the
  command ships sending nothing.
- [ ] **AC-0031.** `docs/profiles.md` states the four things a mapping profile
  declares and shows a worked profile.
- [ ] **AC-0032.** `README-pypi.md` states that the distribution is versioned by
  semantic versioning and that the mapping-profile interface is provisional in
  0.x, so a consumer knows what may change under it.

## Retired identifiers

<!-- Identity is append-only: a retired identifier is never reused. -->

None.

## Follow-ons

- spec owner: [`loop-telemetry-export`](../loop-telemetry-export/spec.md) — the
  integration that supplies the `work_loop` profile, declares this distribution
  as an optional dependency, and wires its configuration. It depends on this
  spec; this spec does not depend on it.

## Assumptions

- Technical: runtime is Python ≥3.11 (source: `packages/agentbundle/pyproject.toml:9`, `packages/credbroker/pyproject.toml:9`)
- Technical: console-script entry points are precedented (source: `packages/agentbundle/pyproject.toml:31-32`)
- Technical: the release path is a proven template with trusted publishing and a SHA-pinned publish action (source: `.github/workflows/release-credbroker.yml`)
- Technical: OTLP/HTTP JSON is a stable public contract but not a frozen one, and structural errors are rejected loudly rather than silently discarded (source: `docs/architecture/telemetry.md` § 10.3, measured 2026-09-12)
- Technical: a Collector's `otlp` receiver accepts `application/json` with no configuration, auto-detecting from `Content-Type` (source: same measurement)
- Process: stdlib is preferred over a pip dependency (source: `guides/_shared/how-to/author-a-skill.md:104-117`)
- Product: v1 targets an unauthenticated Collector endpoint; authenticated vendor endpoints are a non-goal (source: user confirmation 2026-09-12)
- Product: the contract is capability-scoped because the distribution is published and a PyPI name cannot be reclaimed (source: user confirmation 2026-09-12)

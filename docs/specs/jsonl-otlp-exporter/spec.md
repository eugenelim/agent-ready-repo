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
- Canonicalise the input path before opening it, and refuse anything that is not
  a regular file inside the resolved root.
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
- Retry a request whose response carries a non-empty `partialSuccess`.

## Testing Strategy

- **VI-0001 — off-by-default and endpoint resolution (AC-0001, AC-0002, AC-0003, AC-0004):** TDD. Pure precedence logic over an environment mapping and one file, so the cases compress into assertions and none needs a network. The unconfigured case asserts the transport seam is never constructed, not that stderr says so — the latter passes for a build that sends first and prints afterwards.
- **VI-0002 — OTLP encoding (AC-0005, AC-0007, AC-0016):** TDD. The encoder is a pure function from parsed lines to a request body, so a byte-exact golden pins the layout and a diff shows drift. Structural errors are rejected loudly by a receiver, so the golden is not defending against silent rejection — it is the only written form of the emitted layout.
- **VI-0003 — a real receiver parses what is emitted (AC-0006):** goal-based check, exercised by an integration test against a live Collector. The only check that observes attribute *naming*: a structurally valid payload with wrong names is accepted and stored, so neither a rejection nor the golden can see it.
- **VI-0004 — retry and batching (AC-0008, AC-0009, AC-0010, AC-0011):** TDD over a seam in front of the transport. Each response shape is a fixture rather than a live condition. Backoff shape and jitter are unpromised in v1 and therefore unasserted.
- **VI-0005 — exit codes (AC-0012, AC-0013, AC-0014, AC-0015, AC-0029):** goal-based check. Each state is one invocation and one observed status. AC-0013 and AC-0014 take their own cases: a parse error exercises the argument parser's own exit path, and the band claim is a statement over every invocation rather than any single one.
- **VI-0006 — input confinement (AC-0017):** TDD. A symlink, a non-regular file and a path escaping the root are three fixtures over one predicate, asserting the transport seam is never constructed — proving refusal precedes sending.
- **VI-0007 — size bounds (AC-0018, AC-0019):** TDD. Both are functions over constructed input. AC-0019's arithmetic is asserted by constructing the worst admissible case rather than trusting the stated ceiling.
- **VI-0008 — modes and file lifecycle (AC-0020, AC-0021, AC-0022):** TDD. Mode selection and the run bound are observable from process behaviour; AC-0022's four file states are one predicate substituted at each member.
- **VI-0009 — record identity (AC-0023):** TDD over the encoder's output. Delivery is at-least-once, so this is the attribute set a consumer deduplicates on.
- **VI-0010 — destination policy (AC-0024, AC-0025, AC-0026, AC-0027, AC-0028):** TDD over the opener construction. Five separate failure modes with five separate remedies: an accepted HTTPS target, an accepted loopback plaintext target, a refused non-loopback plaintext target, a refused redirect, and a refused user-info netloc.
- **VI-0011 — the published contract (AC-0030, AC-0031, AC-0032):** goal-based check over the authored files. Presence and structure are mechanical; wording is not asserted.

## Acceptance Criteria

- [ ] **AC-0001.** With no endpoint resolvable from any source, the command opens
  no socket, exits 0, and writes a line to stderr naming that no endpoint is
  configured.
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
  `severityNumber`, and every remaining field appears as a log-record attribute.
- [ ] **AC-0007.** Every emitted log record carries a `service.name` resource
  attribute taking the value of `--service-name`, defaulting to the active
  profile's declared name.
- [ ] **AC-0008.** A response carrying a non-empty `partialSuccess` produces no
  retry, and its rejected-record count appears on stderr.
- [ ] **AC-0009.** After an HTTP 429 or 503 carrying `Retry-After: N`, no request
  is issued before `min(N, 30)` seconds have elapsed, and a value that is
  absent, negative or unparseable is treated as 0.
- [ ] **AC-0010.** A send is attempted at most 3 times.
- [ ] **AC-0011.** A single request carries at most 512 log records, counted from
  the parsed lines of the input file.
- [ ] **AC-0012.** Send failure after the retry budget exits 1, and exits 0 when
  `--best-effort` is passed.
- [ ] **AC-0013.** An unrecognised command-line flag exits 1, not 2.
- [ ] **AC-0014.** No invocation returns an exit code in the range 2 through 9.
- [ ] **AC-0015.** SIGINT exits 130.
- [ ] **AC-0016.** A line that does not parse as JSON is skipped with a stderr
  note, and the remaining lines are still sent.
- [ ] **AC-0017.** The command reads only a regular file at the path given by
  `--input`, canonicalised before opening, and sends nothing when that path is a
  symlink, a non-regular file, or resolves outside the directory given by
  `--root`, which defaults to the working directory.
- [ ] **AC-0018.** A line longer than 64 KiB is refused before it is decoded,
  skipped with a note on stderr, and the remaining lines are still sent.
- [ ] **AC-0019.** A request body is at most 8 MiB. The 64 MiB OTLP protocol
  limit is not binding on this route because the per-line bound in AC-0018 and
  the record cap in AC-0011 together admit at most 32 MiB, so the 8 MiB body
  bound is the limit that fires first.
- [ ] **AC-0020.** With no mode flag the command runs one-shot: it reads the file
  once, sends, and exits without waiting for further lines.
- [ ] **AC-0021.** Under `--follow`, a line appended after start is sent without
  restarting the process, and `--for <duration>` ends the run at that elapsed
  time.
- [ ] **AC-0022.** For each of an absent file, a file truncated to zero, a file
  replaced by a new inode, and a trailing line with no newline, the command exits
  0 and sends no partial or duplicate record for that condition.
- [ ] **AC-0023.** Every emitted log record carries the attributes the active
  profile declares as its record identity, which together identify a record for a
  consumer deduplicating at-least-once delivery.
- [ ] **AC-0024.** An `https` endpoint is accepted at any host.
- [ ] **AC-0025.** An `http` endpoint is accepted only when its host resolves to
  a loopback address.
- [ ] **AC-0026.** An `http` endpoint whose host does not resolve to a loopback
  address is refused before any request is sent, with a message naming the
  endpoint, and exits 1.
- [ ] **AC-0027.** A redirect response is not followed, and the run exits 1 with
  a message naming the redirect target.
- [ ] **AC-0028.** An endpoint whose netloc carries user-info is refused before
  any request is sent and exits 1.
- [ ] **AC-0029.** `--version` prints the installed distribution version.
- [ ] **AC-0030.** `README-pypi.md` states what the command sends, what the
  payload contains, and that it reaches the configured endpoint — while the
  command ships sending nothing.
- [ ] **AC-0031.** `docs/profiles.md` states the three things a mapping profile
  declares — the timestamp field, the severity field, and the record-identity
  attributes — and shows a worked profile.
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

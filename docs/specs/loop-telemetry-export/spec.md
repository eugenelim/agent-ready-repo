# Spec: loop-telemetry-export

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [ADR-0111](../../adr/0111-loop-telemetry-sender-is-a-separately-installed-distribution.md)
- **Depends on:** [`loop-event-schema-version`](../loop-event-schema-version/spec.md) — ships first
- **Brief:** none
- **Discovery:** none
- **Contract:** none — the event-line schema is owned by `loop-event-schema-version`
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

## Objective

An adopter who wants their work-loop runs visible in an observability backend
installs one small tool, points it at an OpenTelemetry Collector, and sees a log
record per phase transition. The tool is `jsonl-otlp-export`, a separately
installed Python distribution. Nothing in any installed pack can send: an
adopter who never installs the tool has a structural guarantee, not a
configuration promise. An adopter who installs it but configures no endpoint
still sends nothing, and the tool says so rather than failing.

Success for that adopter is a Splunk, Honeycomb, Grafana or Datadog view of
where a run spent its time and which gates it failed, reached by running a
Collector they already know how to run. The event line's version is a
precondition rather than part of this delivery: it ships first, in
[`loop-event-schema-version`](../loop-event-schema-version/spec.md).

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
| 0 | Some lines invalid, the rest sent |
| 1 | Unreadable or confined-refused input file |
| 1 | Every line invalid |
| 1 | Usage error, configuration error, refused endpoint, or an unhandled exception |
| 1 | Send failure after the retry budget, or a non-empty `partialSuccess` |
| 0 | Send failure after the retry budget, under `--best-effort` |
| 2–9 | Never returned — reserved credential/auth band owned by [`credentialed-cli-exit-code-contract`](../credentialed-cli-exit-code-contract/spec.md) |
| 130 | Interrupted by SIGINT |

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Applicable — a sender outside every pack, and a versioned line, are both reversals of stated current architecture | `docs/adr/0109-*.md` | spec owner | Accepted ADR naming the § 5.2 interpretation and the per-engine default | ADR merged and cited by `telemetry.md` |
| Current architecture | Applicable — `telemetry.md` § 2 states "No exporter ships", § 5.3 carries a stale blockquote, and two anchors to `agentbundle.md § 7.1` are dead | `docs/architecture/telemetry.md` | spec owner | § 2, § 5.2, § 5.3 and § 8 read true against the shipped tool; both anchors resolve | Anchors resolve; no claim contradicts the shipped tool |
| User-facing promise | Applicable — an adopter must learn the capability exists, what it sends, and where | `guides/core/how-to/export-loop-telemetry.md` + `packages/jsonl-otlp-exporter/README-pypi.md` | spec owner | Disclosure sentence naming capability, payload and destination | Guide indexed; PyPI README renders |
| Release history | Applicable — a new published distribution and a `core` content change | `docs/product/changelog.md` + `packages/jsonl-otlp-exporter/CHANGELOG.md` | release workflow | Version bump with changelog entry; tag matches `pyproject` | Tag published, both changelogs updated |
| Maintainer procedure | Applicable — a third distribution with its own release path | `packages/jsonl-otlp-exporter/AGENTS.md` | spec owner | Test command and release-coupling note | File present and accurate |
| Optional-dependency reporting | Applicable — T7 writes the first reader of `[[pack.runtime-dependencies]]`, changing what a lint run reports | `packs/core/pack.toml` + the catalogue lint's reporting path | spec owner | Lint run naming the unsatisfied optional dependency | AC-0039 green and the behaviour documented |
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
- Canonicalise the input path before opening it, and refuse anything that is
  not a regular file inside the repository root.
- Require HTTPS for any endpoint whose host is not a loopback address.

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
- Follow an HTTP redirect, or send to an endpoint carrying user-info.

## Testing Strategy

- **VI-0001 — off-by-default and endpoint resolution (AC-0001, AC-0002, AC-0003, AC-0004):** TDD. Pure precedence logic over an environment mapping and two files, so the cases compress into assertions and none needs a network. The unconfigured case is asserted against a transport seam that fails if constructed, not by reading output — an assertion on stderr would pass for a build that sent first and printed afterwards.
- **VI-0002 — OTLP encoding (AC-0005, AC-0007, AC-0016):** TDD. The encoder is a pure function from parsed lines to a request body, so a byte-exact golden pins the layout and a diff shows drift. Measured against a live Collector (`telemetry.md` § 10.3) structural errors return HTTP 400, so the golden is not defending against silent rejection — it is the only written form of the emitted layout.
- **VI-0003 — a real receiver parses what we emit (AC-0006):** goal-based check, exercised by an integration test against a live Collector. The only check that observes attribute *naming*: a structurally valid payload with wrong names is accepted and stored, so neither a 400 nor the golden can see it.
- **VI-0004 — retry and batching, as the criteria state them (AC-0008, AC-0009, AC-0010, AC-0011):** TDD over a seam in front of `urlopen`. Scope is exactly the four criteria — partial-success suppression, the bounded `Retry-After` wait, the attempt cap and the record cap. Backoff shape and jitter are deliberately unpromised in v1 and therefore unasserted here.
- **VI-0005 — exit codes (AC-0012, AC-0013, AC-0014, AC-0015):** goal-based check. Each state is one invocation and one observed status. AC-0013 and AC-0014 take cases of their own: a parse error exercises `argparse`'s own exit path, and the band claim is a statement over every invocation rather than any single one.
- **VI-0006 — disclosure and the architecture records (AC-0020, AC-0021, AC-0022):** goal-based check over the authored files. Anchor resolution is mechanical; the disclosure sentence is checked for presence, not wording.
- **VI-0007 — the installed tool, end to end (AC-0023):** visual / manual QA. The real console script, installed from the built wheel, is invoked and its stdout, stderr and exit code recorded. A passing unit gate does not satisfy this.
- **VI-0008 — input-path confinement (AC-0024):** TDD. A symlink, a FIFO and a path escaping the root are three fixtures over one predicate, and the assertion is that the transport seam is never constructed — proving refusal happens before sending, not after.
- **VI-0009 — size bounds (AC-0025, AC-0026):** TDD. Both are functions over constructed input, so an oversized line and an oversized batch are fixtures. AC-0026's arithmetic is asserted, not assumed: the test constructs the worst admissible case rather than trusting the stated ceiling.
- **VI-0010 — modes and file lifecycle (AC-0027, AC-0028, AC-0029):** TDD. Mode selection and `--for` are observable from process behaviour; AC-0029's four file states are one predicate substituted at each member, checkable as written at every one.
- **VI-0011 — record identity for deduplication (AC-0030):** TDD, over the encoder's output. Delivery is at-least-once, so this is the attribute pair a consumer needs; the criterion is about what the record carries, not about suppressing a resend.
- **VI-0012 — the repository's gates reach the distribution (AC-0031):** goal-based check. Each enumeration site is read and asserted to name the package, because every one of them is a literal list rather than a glob.
- **VI-0013 — degraded completion (AC-0032, AC-0033):** goal-based check. Both are outcome classes the exit table now partitions, and both were previously unstated.
- **VI-0014 — destination policy (AC-0034, AC-0035, AC-0036, AC-0037, AC-0038):** TDD over the opener construction. Five separate failure modes with five separate remedies, so they do not collapse: an accepted HTTPS target, an accepted loopback plaintext target, a refused non-loopback plaintext target, a refused redirect, and a refused user-info netloc.
- **VI-0015 — optional-dependency reporting (AC-0039):** goal-based check over a lint run with the distribution absent. Reporting only: the assertion includes that no package manager is invoked.

## Acceptance Criteria

- [ ] **AC-0001.** With no `[telemetry]` section in either layout file and no
  endpoint environment variable set, the exporter opens no socket, exits 0, and
  writes a line to stderr naming that no endpoint is configured.
- [ ] **AC-0002.** The endpoint used is the first present of, in order:
  `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT`, `OTEL_EXPORTER_OTLP_ENDPOINT`, the
  repository `agentbundle-layout.toml` `[telemetry].endpoint`, then the user
  `agentbundle-layout.toml` `[telemetry].endpoint`.
- [ ] **AC-0003.** A value resolved from `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` is
  requested unmodified.
- [ ] **AC-0004.** A value resolved from any source other than
  `OTEL_EXPORTER_OTLP_LOGS_ENDPOINT` is requested with `/v1/logs` appended.
- [ ] **AC-0005.** For the recorded three-line fixture, the emitted request body
  equals `tests/fixtures/otlp-logs-golden.json` byte for byte.
- [ ] **AC-0006.** Under the `work-loop` mapping profile, a Collector running an
  `otlp` receiver and a `debug` exporter records three log records in which
  `at` appears as `timeUnixNano`, `result` as `severityNumber`, and every
  remaining envelope field as a log-record attribute.

- [ ] **AC-0007.** Every emitted log record carries a `service.name` resource
  attribute taking the value of `--service-name`, defaulting to the active
  mapping profile's declared name, which is `work-loop` for the only profile
  v1 ships. Splunk renders a record without it as `unknown_service`.

- [ ] **AC-0008.** A response carrying a non-empty `partialSuccess` produces no
  retry, and its `rejectedLogRecords` count appears on stderr.
- [ ] **AC-0009.** After an HTTP 429 or 503 carrying `Retry-After: N`, no
  request is issued before `min(N, 30)` seconds have elapsed, and a value
  that is absent, negative or unparseable is treated as 0.

- [ ] **AC-0010.** A send is attempted at most 3 times.
- [ ] **AC-0011.** A single request carries at most 512 log records, counted
  from the parsed lines of the input file.

- [ ] **AC-0012.** Send failure after the retry budget exits 1, and exits 0 when
  `--best-effort` is passed.
- [ ] **AC-0013.** An unrecognised command-line flag exits 1, not 2. The 2–9 band
  belongs to credential/auth states this tool does not have, and `argparse`
  exits 2 by default.
- [ ] **AC-0014.** No invocation returns an exit code in the range 2 through 9.
- [ ] **AC-0015.** SIGINT exits 130.
- [ ] **AC-0016.** A line that does not parse as JSON is skipped with a stderr
  note, and the remaining lines are still sent.

- [ ] **AC-0020.** `guides/core/how-to/export-loop-telemetry.md` states that the
  capability exists, what the payload contains, and that it reaches the
  configured endpoint — while the tool ships sending nothing.
- [ ] **AC-0021.** `docs/architecture/telemetry.md` § 5.3 carries no claim that the
  catalogue-level default does not work, and every `agentbundle.md` anchor it
  cites resolves to a heading that exists.
- [ ] **AC-0022.** `docs/architecture/telemetry.md` § 2 and § 8 describe a sender
  that exists and is installed separately.
- [ ] **AC-0023.** `jsonl-otlp-export --version` prints the installed
  distribution version, and the published tag equals `pyproject.toml`'s
  `version`.

- [ ] **AC-0024.** The exporter reads only a regular file at the path given by
  `--input`, defaulting to `.loop-run/events.jsonl`, canonicalised before
  opening, and sends nothing when that path is a symlink, a non-regular file,
  or resolves outside the directory given by `--root`, which itself defaults to
  the working directory.

- [ ] **AC-0025.** A line longer than 64 KiB is refused before it is decoded,
  skipped with a note on stderr, and the remaining lines are still sent.
- [ ] **AC-0026.** A request body is at most 8 MiB. The 64 MiB OTLP protocol
  limit is not binding on this route because the per-line bound in AC-0025 and
  the record cap in AC-0011 together admit at most 32 MiB, and the 8 MiB body
  bound is therefore the limit that fires first.
- [ ] **AC-0027.** With no mode flag the exporter runs one-shot: it reads the
  file once, sends, and exits without waiting for further lines.
- [ ] **AC-0028.** Under `--follow`, a line appended after start is sent without
  restarting the process, and `--for <duration>` ends the run at that elapsed
  time.
- [ ] **AC-0029.** For each of an absent file, a file truncated to zero, a file
  replaced by a new inode, and a trailing line with no newline, the exporter
  exits 0 and sends no partial or duplicate record for that condition.
- [ ] **AC-0030.** Every emitted log record carries the attributes the active
  mapping profile declares as its record identity, which for the `work-loop`
  profile are `run_id` and `seq`, together identifying a record for a consumer
  deduplicating at-least-once delivery.

- [ ] **AC-0031.** `packages/jsonl-otlp-exporter` appears in the root
  `pyproject.toml` `pythonpath`, mypy's `files`, the `Makefile` test-suite
  invocations, and the pip-audit build-system leg, so its tests and type checks
  are run by the repository's gates.
- [ ] **AC-0032.** A run in which every line is invalid exits 1.
- [ ] **AC-0033.** A response carrying a non-empty `partialSuccess` exits 1,
  consistent with the degraded-completion ruling in
  [`credentialed-cli-exit-code-contract`](../credentialed-cli-exit-code-contract/spec.md).
- [ ] **AC-0034.** An `https` endpoint is accepted at any host.
- [ ] **AC-0035.** An `http` endpoint is accepted only when its host resolves to
  a loopback address.
- [ ] **AC-0036.** An `http` endpoint whose host does not resolve to a loopback
  address is refused before any request is sent, with a message naming the
  endpoint, and exits 1.
- [ ] **AC-0037.** A redirect response is not followed, and the run exits 1 with
  a message naming the redirect target.
- [ ] **AC-0038.** An endpoint whose netloc carries user-info is refused before
  any request is sent and exits 1.
- [ ] **AC-0039.** With the distribution absent, `agentbundle catalogue lint`
  reports `jsonl-otlp-exporter` as an optional, unsatisfied runtime
  dependency of `core` and exits 0.

## Retired identifiers

<!-- Identity is append-only: a retired identifier is never reused. Entries are
     bare identifiers; the narrative belongs above, not on the entry line. -->

Retired 2026-09-12 when the event-line version was split into
[`loop-event-schema-version`](../loop-event-schema-version/spec.md), where they
are re-authored under that spec's own identifiers. They are not reused here.

- AC-0017
- AC-0018
- AC-0019

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

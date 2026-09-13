# Plan: loop-telemetry-export

> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material: an implementer corrects them in place as the
> work teaches, without an amendment and without a review round.

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packages/credbroker/` (distribution shape, and the
  only sibling that ships a pack-adjacent library); `.github/workflows/release-credbroker.yml`
  (release template — trusted publishing, SHA-pinned publish action, tag-equals-version
  assertion, fresh-venv smoke); `packages/agentbundle/pyproject.toml:31-32` (the
  one console-script precedent); `packages/agentbundle/agentbundle/https_catalogue.py`
  (outbound-`urllib` hardening — read for technique, not importable from here);
  `docs/specs/credentialed-cli-exit-code-contract/spec.md` (owns the exit band);
  `packages/agentbundle/tests/unit/` and `packages/credbroker/tests/` (test layout
  for a distribution). Named uncertainty: no repository precedent exists for an
  outbound-network CLI, so the transport hardening is adapted from
  `https_catalogue.py` rather than reused.

## Approach

Five layers, each independently reviewable and each leaving the repository
working. The order is forced by provability, not by preference: everything that
can be proven with no network at all lands before anything that opens a socket,
so a reviewer can see the off-by-default guarantee before the sending code
exists to complicate it.

The distribution scaffold comes first only because the later layers need
somewhere to live. It ships a console script that resolves configuration, finds
nothing, and exits 0 — which is the whole off-by-default proof, executable from
the first task.

The event-line version is not part of this delivery at all. It ships first as
`loop-event-schema-version`, so a `packs/core` version bump never waits on a
PyPI release and a consumer never sees a version appear underneath it.

## Constraints

- The sender lives only in `packages/jsonl-otlp-exporter/`. No pack gains a
  network path, so `packs/core` keeps the § 8 invariant intact.
- Standard library only. `guides/_shared/how-to/author-a-skill.md:104` makes
  Tier 1 the default and prefers stdlib over a pip dependency; adding one needs
  the Ask-first gate in the spec.
- `https_catalogue.py` is read, not imported: `telemetry.md:47-49` forbids pack
  code importing installer libraries, and this distribution keeps the same
  independence so it can be extracted.
- Its HTTPS-only policy is deliberately **not** carried over. `http://localhost:4318`
  is the common Collector target, so the transport permits plaintext to loopback
  and requires HTTPS elsewhere.

## Construction tests

Two independent checks guard the encoder. A spike against a live Collector
(recorded in `telemetry.md` § 10.3) narrowed what they must catch: structural
errors return HTTP 400 naming the offending byte, so ingestion failure is loud,
and only two emission rules are load-bearing for acceptance — hex identifier
fields and the `AnyValue` attribute list. The receiver tolerates JSON-number
64-bit integers and snake_case field names, exactly where the specification
requires it to.

So the golden file is not defending against silent rejection. It pins the
emitted layout so attribute drift shows up in a diff — the one failure a 200
genuinely hides is a structurally valid payload carrying wrong attribute names.
The round trip proves a real receiver parses what we emit.

The transport tests drive a seam in front of `urlopen`, so each response shape
(429 with `Retry-After`, 503, 200 with `partialSuccess`, connection refused) is
a fixture rather than a live condition.

The event-line version tests live beside the existing envelope suite at
`packs/core/tests/skills/work-loop/test_loop_engine_events_jsonl.py`, which
already asserts a key superset and therefore does not need changing to admit a
new field — the new cases assert presence and the replay passthrough.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| ADR-0111 (decision rationale) | T8 | Accepted ADR file | Cited by `telemetry.md` § 9 |
| `docs/architecture/telemetry.md` (architecture) | T8 | §§ 2, 5.2, 5.3, 8 diff | Both `agentbundle.md` anchors resolve |
| `guides/core/how-to/export-loop-telemetry.md` (user promise) | T8 | Guide with the disclosure sentence | `check-guide-index.py` green |
| `packages/jsonl-otlp-exporter/CHANGELOG.md` + `docs/product/changelog.md` (release) | T9 | Version bump, entries | Tag equals `pyproject` version |
| `packages/jsonl-otlp-exporter/AGENTS.md` (maintainer) | T1 | Test command, release coupling | File accurate |
| Optional-dependency reporting | T7 | Lint run naming the unsatisfied optional dependency | AC-0039 green; behaviour documented |
| `docs/specs/README.md` (product truth) | T8 | Active-list row | Row present |
| `project-knowledge` (learning) | closeout | Capture receipt | Receipt or `project-knowledge unavailable` |

## Design (LLD)

### Design decisions

**A separate distribution, not a pack primitive.** `telemetry.md:300` states
"Nothing in a pack sends." Every pack-resident home breaks it; a PyPI
distribution keeps it literally true and gives the adopter a package-manager
guarantee rather than a configuration promise. ADR-0111 records this.

**One exporter per engine, no shared emitter.** Confirmed as the prevailing
architecture across Argo, Dagger, Buildkite and Jenkins. A shared library is
deferred until at least two real engine integrations show duplication.

**No position file.** Every surveyed agent keys a checkpoint to file identity,
and `.loop-run/events.jsonl` is recreated per run, so the checkpoint is stale
immediately. Idempotency comes from the `run_id:seq` join key `telemetry.md` § 3
already defines, which costs nothing and makes re-delivery harmless.

### Data & schema

The event line gains `schema: 1`. § 8's invariant holds — the first seven fields
keep name, order and value. Absent means version 1, which is what makes the
outbox replay path safe: a pending record written by an older writer is appended
unchanged rather than retro-stamped with a version it was not written under.

The OTLP mapping is one `resourceLogs` entry, one `scopeLogs` entry, and one
`logRecords` element per input line. Envelope fields become log-record
attributes; `at` becomes `timeUnixNano`; `result` maps to `severityNumber`.

### Interfaces & contracts

`contracts/jsonschema/loop-run-event.schema.json` is the authored source, per
`contracts/README.md`'s authority model. It is repository-public with no CLI
data copy, so no byte-identical mirror under `agentbundle/_data/` is created.

### Component / module decomposition

Five modules, split on what each can be tested without: `config` (no I/O beyond
reading two files), `encode` (pure — line dicts in, request body out),
`transport` (the only module that opens a socket), `cli` (argument parsing, exit
codes, wiring), and `mappings/` (one module per profile). The split exists so
`encode` is golden-testable and `config` is provable with no network.

**The mapping seam, and why it exists now rather than later.** A profile declares
three things: which envelope field becomes `timeUnixNano`, which becomes
`severityNumber`, and which attributes carry record identity. `mappings/work_loop.py`
is the only profile v1 ships, and no profile-selection surface is promised — but
the seam exists from the first commit because the alternative is a second
consumer needing an amendment to shipped acceptance criteria rather than a new
file. A design walk against a hypothetical CI-runner consumer found four places
where the contract had hardcoded the first consumer; the criteria now name the
active profile and the profile names the fields.

**One scoping limit, stated rather than hidden.** The file route in AC-0002 reads
`agentbundle-layout.toml`, which only an agentbundle adopter has. That is
deliberate — it is this repository's integration, not a general mechanism — and
the environment route is the standard OTel one, so a consumer outside this
catalogue configures by environment and loses nothing. If a second consumer ever
needs a file route of its own, that is a new criterion, not a change to this
one.

### State & control flow

One-shot: read, parse, encode, send, exit. Tail: poll for appended bytes,
holding the offset in memory only, exiting on signal or on `--for` elapsing.
Both paths share everything after "lines in hand".

### Behavior & rules

Endpoint resolution is a first-present walk over four sources. Repository before
user is the deliberate inversion of `desk-research`'s order, and `telemetry.md`
§ 5.3 owns the reason.

### Failure, edge cases & resilience

A malformed line is skipped and noted, never fatal — the input is untrusted and
one bad line must not cost the rest of the run. Send failure exhausts the retry
budget then exits 1, or 0 under `--best-effort`. The exporter never writes to
`.loop-run/`.

### Quality attributes (NFRs)

Batch cap 512 records per request, from the Go SDK's default; the OTLP 64 MiB
request limit is dominated by it and cannot fire on this route. Request timeout
10 s, 3 attempts, 1 s initial backoff with jitter.

### Dependencies & integration

No third-party dependency. `[[pack.runtime-dependencies]]` in `packs/core/pack.toml`
declares this distribution as `optional = true` — the first use of a schema
surface that has no reader today, so T7 writes the reporting side as well as the
declaration.

## Tasks

<!-- Every task below creates or extends `packages/jsonl-otlp-exporter`, which
     does not exist at plan approval. Per `references/tdd-stubs.md`, a stub may
     not invent a module or symbol to assert against, so the TDD tasks here carry
     the `no stub (implementation-discovered)` disposition with their discovery
     predicate and proof obligation. The sibling spec
     `loop-event-schema-version` carries a validated stub instead, because its
     seam — the existing envelope suite — already exists. -->

### T1: Scaffold the distribution and put it inside the gates

**Depends on:** none

**Touches:** `packages/jsonl-otlp-exporter/`, `pyproject.toml`, `Makefile`

**Tests:**
- Goal-based: `python3 -m build packages/jsonl-otlp-exporter` produces a wheel
  and sdist; a fresh venv installs it and `jsonl-otlp-export --version` prints
  the version. Verifies AC-0023.
- Goal-based: the package name appears in the root `pyproject.toml` `pythonpath`,
  mypy's `files`, the `Makefile` test-suite invocations, and the pip-audit
  build-system leg. Each is a literal list, so each is asserted by reading it.
  Verifies AC-0031.

**Approach:**
- Mirror `packages/credbroker/`'s structure; declare `[project.scripts]`.

**Done when:** the console script runs from a fresh venv, and a deliberate
failing test added under the new package's `tests/` is reported by `make test` —
proving the suite is actually reached rather than merely listed.

### T2: Configuration resolution and the off-by-default proof

**Depends on:** T1

**Touches:** `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/config.py`, its tests

**Tests:**
- `no stub (implementation-discovered)`. Discovery predicate: the resolver's
  callable signature is fixed the moment T1's package layout exists; until then
  asserting against `config.resolve` would invent the symbol. Constraint:
  stdlib only, no network, both layout files read as untrusted TOML. Required
  outcome: the four-source precedence walk and the empty case. Verification
  mode: TDD. Proof obligation: the first test written in T2 asserts the empty
  case against a transport seam that fails if constructed, so the off-by-default
  guarantee is proven before any sending code exists.
- Four-source precedence, one case per source plus the empty case. Verifies
  AC-0001, AC-0002, AC-0003, AC-0004.

**Approach:**
- Read both layout files with `tomllib`, extracting only `[telemetry]` keys.

**Done when:** the empty case passes with a transport seam that raises if
constructed.

### T3: Input acquisition — confinement, bounds, modes and file lifecycle

**Depends on:** T1

**Touches:** `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/source.py`, its tests

**Tests:**
- `no stub (implementation-discovered)`. Discovery predicate: the reader's seam
  is fixed once T1's layout exists. Constraint: the path is canonicalised before
  opening and confined to `--root`; no durable position state is written.
  Required outcome: refusal before any read for an unsafe path, and a bounded
  read otherwise. Verification mode: TDD. Proof obligation: the confinement
  cases assert the transport seam is never constructed, proving refusal precedes
  sending rather than following it.
- A symlink, a FIFO, and a path escaping `--root` are each refused with nothing
  sent. Verifies AC-0024.
- A line over 64 KiB is refused before decoding and the rest still send.
  Verifies AC-0025.
- Default mode is one-shot; `--follow` delivers an appended line; `--for` ends
  the run. Verifies AC-0027, AC-0028.
- Absent file, truncated file, replaced inode, and a trailing line with no
  newline each exit 0 with no partial or duplicate record. Verifies AC-0029.

**Approach:**
- One reader serving both modes; the offset lives in memory only.

**Done when:** every file-lifecycle case passes and no position file is written.

### T4: Encoder and the work-loop mapping profile

**Depends on:** T1

**Touches:** `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/encode.py`, `mappings/work_loop.py`, its tests

**Tests:**
- `no stub (implementation-discovered)`. Discovery predicate: the encoder's
  signature follows the profile interface, which T4 defines. Constraint: pure
  function, no I/O. Required outcome: a byte-stable request body. Verification
  mode: TDD. Proof obligation: the golden comparison is written first and fails
  until the mapping exists.
- Byte-exact golden for the recorded three-line fixture. Verifies AC-0005.
- `service.name` takes `--service-name`, defaulting to the profile's name.
  Verifies AC-0007.
- A non-parsing line is skipped and the remainder encoded. Verifies AC-0016.
- Records carry the profile's declared identity attributes. Verifies AC-0030.

**Approach:**
- The five OTLP JSON rules live here and nowhere else; the profile declares the
  three field destinations.

**Done when:** the golden passes and the profile is the only place field names
appear.

### T5: Transport — destination policy, retry and batching

**Depends on:** T2, T4

**Touches:** `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/transport.py`, its tests

**Tests:**
- `no stub (implementation-discovered)`. Discovery predicate: the opener's seam
  is fixed once the config and encoder interfaces exist. Constraint: adapt
  `https_catalogue.py`'s opener and redirect handling without importing it.
  Required outcome: every response shape drives its documented behaviour.
  Verification mode: TDD. Proof obligation: each response fixture asserts a
  distinct observable, so no single change makes them all pass.
- Non-empty `partialSuccess` produces no retry and reports the count. Verifies AC-0008.
- `Retry-After: N` waits `min(N, 30)`; absent, negative or unparseable is 0.
  Verifies AC-0009.
- At most three attempts. Verifies AC-0010.
- At most 512 records per request. Verifies AC-0011.
- A request body never exceeds 8 MiB, asserted by constructing the worst
  admissible case rather than trusting the ceiling. Verifies AC-0026.
- HTTPS accepted at any host; plaintext accepted only to a loopback address;
  plaintext to a non-loopback host refused before sending; a redirect not
  followed; user-info in the netloc refused. Verifies AC-0034, AC-0035,
  AC-0036, AC-0037, AC-0038.
- Integration, against a live Collector with an `otlp` receiver and a `debug`
  exporter: three records land with each field at its mapped destination.
  Verifies AC-0006.

**Approach:**
- Loopback is decided by resolving the host and testing the resolved address,
  not by string-matching `localhost`.

**Done when:** every response-shape and destination fixture drives its documented
behaviour, and the live round trip lands three records.

### T6: CLI, exit codes and degraded completion

**Depends on:** T3, T5

**Touches:** `packages/jsonl-otlp-exporter/jsonl_otlp_exporter/cli.py`, its tests

**Tests:**
- Each exit state from the spec's table, one invocation each. Verifies AC-0012,
  AC-0015.
- An unknown flag exits 1, not 2 — `argparse`'s default must be overridden or it
  collides with the reserved `USER_ACTION` code. Verifies AC-0013.
- No invocation returns a code in 2 through 9. Verifies AC-0014.
- A run whose every line is invalid exits 1. Verifies AC-0032.
- A non-empty `partialSuccess` exits 1. Verifies AC-0033.

**Approach:**
- Top-level `except Exception` maps to 1; never `except BaseException`, so
  `SystemExit` and `KeyboardInterrupt` pass through.

**Done when:** the exit-code table is exercised end to end.

### T7: Declare and report the optional runtime dependency

**Depends on:** T1

**Touches:** `packs/core/pack.toml`, the catalogue lint's reporting path, its tests

**Tests:**
- With the distribution absent, `agentbundle catalogue lint` names
  `jsonl-otlp-exporter` as an optional unsatisfied runtime dependency of `core`
  and exits 0, invoking no package manager. Verifies AC-0039.

**Approach:**
- Report only. Tier 1 detect → fail clean; the installer never acquires.

**Done when:** a lint run reports the optional dependency without failing and
without invoking pip, npm, uv or pipx.

### T8: Records, architecture and disclosure

**Depends on:** T6

**Touches:** `docs/adr/0109-*.md`, `docs/architecture/telemetry.md`, `guides/core/how-to/export-loop-telemetry.md`, `docs/specs/README.md`

**Tests:**
- The guide states the capability, its payload and its destination. Verifies AC-0020.
- `telemetry.md` § 5.3 carries no claim that the catalogue default cannot work,
  and every `agentbundle.md` anchor resolves. Verifies AC-0021.
- §§ 2 and 8 describe a sender that exists and installs separately. Verifies AC-0022.

**Approach:**
- ADR-0111 is already authored; T8 reconciles the architecture text to the
  shipped tool and indexes the guide.

**Done when:** `check-guide-index.py` is green and no dead anchor remains.

### T9: Release

**Depends on:** T7, T8

**Touches:** `.github/workflows/`, `packages/jsonl-otlp-exporter/CHANGELOG.md`, `docs/product/changelog.md`

**Tests:**
- Manual QA: the real console script, installed from the built wheel, is run
  against a real event file and a real Collector; stdout, stderr and exit code
  are recorded in the verification ledger. Re-exercises AC-0023 and AC-0006 on
  the built artifact rather than the source tree.

**Approach:**
- A release workflow modelled on `release-credbroker.yml`, keeping the SHA-pinned
  publish action.

**Done when:** the tagged workflow publishes and a fresh `uv tool install`
produces a working command.

## Rollout

**Delivery:** additive and reversible. Nothing existing changes behaviour except
the event line gaining a field, which both known readers tolerate. Reversal is
yanking the release and reverting one field.

**Infrastructure:** none owned here. The adopter runs the Collector.

**Deployment sequencing:** this delivery depends on `loop-event-schema-version`
shipping first, so a consumer never sees the version appear underneath it. The
distribution release is the last step and depends on every task before it.

## Risks

- **Attribute names drift from what a backend query expects.** This is the one
  defect a 200 hides, since structure is validated but naming is not. Mitigated
  by the golden diff at review, not by any runtime check.
- **OTLP JSON changes again.** v1.10.0 already shipped breaking JSON changes.
  Mitigated by targeting logs only, where the known breaks (metrics uint64,
  profiles `strindex`) do not reach.
- **The first `[[pack.runtime-dependencies]]` reader sets precedent.** Kept
  report-only so the contract stays narrow.
- **Docker may be unavailable for the round-trip gate.** If so, T5's integration
  test is marked a named skip with the reason recorded, and the manual QA in T9
  becomes the only evidence for AC-0006 — a weaker position that must be stated,
  not hidden.

## Changelog

- 2026-09-12 — Drafted. Mechanism selected after an applied survey and its
  adversarial review; four alternatives (seeded script, user-scope pack, repo-scope
  rail extension, documentation-only) were priced and rejected, and a fifth
  (local transformer) was deferred as not completing delivery.
- 2026-09-12 — Pre-review spike against a live Collector **disconfirmed** the
  drafted premise that malformed payloads are silently discarded. Structural
  errors return HTTP 400; base64 identifiers and a flat attribute object were
  the only rejected variants. Testing Strategy and the encoder risk were
  rewritten from the measurement rather than from the survey. Spike not
  committed; result recorded in `telemetry.md` § 10.3.

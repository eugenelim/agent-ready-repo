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

The event-line version is deliberately not sequenced with the exporter. It is a
change to `loop-engine.py` in a different pack with a different test suite, and
coupling the two would make a `core` version bump wait on a distribution
release.

## Constraints

- The sender lives only in `packages/loop-telemetry-exporter/`. No pack gains a
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
| ADR-0109 (decision rationale) | T8 | Accepted ADR file | Cited by `telemetry.md` § 9 |
| `docs/architecture/telemetry.md` (architecture) | T8 | §§ 2, 5.2, 5.3, 8 diff | Both `agentbundle.md` anchors resolve |
| `contracts/jsonschema/loop-run-event.schema.json` (interface) | T3 | Schema validates the recorded corpus | Registry row in `contracts/README.md` |
| `guides/core/how-to/export-loop-telemetry.md` (user promise) | T8 | Guide with the disclosure sentence | `check-guide-index.py` green |
| `packages/loop-telemetry-exporter/CHANGELOG.md` + `docs/product/changelog.md` (release) | T9 | Version bump, entries | Tag equals `pyproject` version |
| `packages/loop-telemetry-exporter/AGENTS.md` (maintainer) | T1 | Test command, release coupling | File accurate |
| `docs/specs/README.md` (product truth) | T8 | Active-list row | Row present |
| `project-knowledge` (learning) | closeout | Capture receipt | Receipt or `project-knowledge unavailable` |

## Design (LLD)

### Design decisions

**A separate distribution, not a pack primitive.** `telemetry.md:300` states
"Nothing in a pack sends." Every pack-resident home breaks it; a PyPI
distribution keeps it literally true and gives the adopter a package-manager
guarantee rather than a configuration promise. ADR-0109 records this.

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

Four modules, split on what each can be tested without: `config` (no I/O beyond
reading two files), `encode` (pure — line dicts in, request body out),
`transport` (the only module that opens a socket), `cli` (argument parsing, exit
codes, wiring). The split exists so `encode` is golden-testable and `config` is
provable with no network.

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

### T1: Scaffold the distribution

**Depends on:** none

**Tests:**
- Goal-based: `python3 -m build packages/loop-telemetry-exporter` produces a
  wheel and an sdist; a fresh venv installs the wheel and
  `loop-telemetry-export --version` prints the version. Mirrors the smoke steps
  in `release-credbroker.yml`. Verifies AC-0023.

**Approach:**
- Copy the structural shape of `packages/credbroker/` — `pyproject.toml`,
  package directory, `tests/`, `AGENTS.md`, `CHANGELOG.md`, `README.md`,
  `README-pypi.md`.
- Declare `[project.scripts]`, the one precedent being
  `packages/agentbundle/pyproject.toml:31-32`.
- Add the package to the root `pyproject.toml` `pythonpath` and the `Makefile`
  `PYTHONPATH`, both of which already enumerate the two existing packages.

**Done when:** the console script runs from a fresh venv and prints its version.

### T2: Configuration resolution and the off-by-default proof

**Depends on:** T1

**Tests:**
- Four-source precedence, one case per source plus the empty case. Verifies AC-0002.
- Path semantics: signal-specific used as-is, generic gets `/v1/logs`. Verifies
  AC-0003 and AC-0004.
- Unconfigured run opens no socket — asserted by a transport seam that fails the
  test if called, not by inspecting output. Verifies AC-0001.
- `stub: true` — `test_resolves_nothing_when_unconfigured` compiles against
  `config.resolve(env, repo_root, user_root) -> Endpoint | None` and asserts
  `None`.

**Approach:**
- Read both layout files with `tomllib`; treat each as untrusted, extracting
  only `[telemetry]` keys.

**Done when:** the unconfigured-path test passes with a transport seam that
raises if constructed.

### T3: Schema version on the event line

**Depends on:** none

**Tests:**
- A transition writes a line carrying `schema: 1`. Verifies AC-0017.
- A pending record lacking `schema` replays unchanged. Verifies AC-0018. This is
  the case the existing suite cannot already see.
- The contract schema validates the recorded corpus. Verifies AC-0019.

**Approach:**
- Add the field in `_cmd_transition`'s `pending_data` literal, above the
  `_lifecycle_fields` spread so field order stays stable.
- Author the JSON Schema and its `contracts/README.md` row.

**Done when:** `packs/core/tests/skills/work-loop/test_loop_engine_events_jsonl.py`
passes with the two new cases, and the corpus validates.

### T4: OTLP JSON encoder

**Depends on:** T1

**Tests:**
- Golden byte comparison for the three-line fixture. Verifies AC-0005.
- `service.name` present with the documented default. Verifies AC-0007.
- Malformed line skipped, remainder encoded. Verifies AC-0016.

**Approach:**
- Pure function from parsed lines to a request body. The five OTLP JSON rules
  live here and nowhere else.

**Done when:** the golden test passes and the fixture is committed.

### T5: Transport

**Depends on:** T2, T4

**Tests:**
- `partialSuccess` non-empty ⇒ no retry, count on stderr. Verifies AC-0008.
- 429 and 503 with `Retry-After` ⇒ next attempt not earlier. Verifies AC-0009.
- Attempt count capped. Verifies AC-0010.
- Batch cap at 512. Verifies AC-0011.
- Plaintext permitted to loopback, refused elsewhere.
- Integration, against a live Collector with an `otlp` receiver and a `debug`
  exporter: three log records land whose attribute sets equal the three input
  lines' fields. Verifies AC-0006.

**Approach:**
- Adapt the opener construction and redirect policy from `https_catalogue.py`;
  do not import it.

**Done when:** every response-shape fixture drives its documented behaviour.

### T6: CLI, modes and exit codes

**Depends on:** T5

**Tests:**
- Each exit state from the spec's table, one invocation each. Verifies AC-0012,
  AC-0015.
- Unknown flag exits 1, not 2 — the `argparse` default must be overridden.
  Verifies AC-0013.
- No invocation returns 2 through 9. Verifies AC-0014.

**Approach:**
- Override `argparse`'s `error()` so a parse failure exits 1.
- Top-level `except Exception` mapping to 1; never `except BaseException`, so
  `SystemExit` and `KeyboardInterrupt` pass through.
- `--once` and the tail loop share everything downstream of line acquisition.

**Done when:** the exit-code table is exercised end to end.

### T7: Declare the runtime dependency

**Depends on:** T1

**Tests:**
- Goal-based: `agentbundle catalogue lint --root . --deep` accepts the new
  `[[pack.runtime-dependencies]]` entry, and the reporting path names the
  distribution as an optional, absent dependency.

**Approach:**
- Declare in `packs/core/pack.toml`; write the first reader for a schema surface
  that has none. Report only — never install, per Tier 1.

**Done when:** a lint run reports the optional dependency without failing.

### T8: Records, architecture and disclosure

**Depends on:** T3, T6

**Tests:**
- Goal-based: `python3 tools/check-guide-index.py` green; every
  `agentbundle.md` anchor cited by `telemetry.md` resolves to a live heading.
  Verifies AC-0020, AC-0021, AC-0022.

**Approach:**
- Author ADR-0109. Confirm the ordinal is free at authoring time; 0106 is
  already duplicated, so a reserved number is not a guarantee.
- Rewrite `telemetry.md` §§ 2, 5.2, 5.3 and 8 against the shipped tool.

**Done when:** the guide is indexed and no dead anchor remains.

### T9: Release

**Depends on:** T1-T8

**Tests:**
- Manual QA: the real console script, installed from the built wheel, is run
  against a real `events.jsonl` and a real Collector; stdout, stderr and exit
  code are recorded in the verification ledger.

**Approach:**
- Add `.github/workflows/release-loop-telemetry-exporter.yml` modelled on the
  credbroker workflow, keeping the SHA-pinned publish action.
- Bump versions, write both changelog entries, tag.

**Done when:** the tagged workflow publishes and a fresh `uv tool install`
produces a working command.

## Rollout

**Delivery:** additive and reversible. Nothing existing changes behaviour except
the event line gaining a field, which both known readers tolerate. Reversal is
yanking the release and reverting one field.

**Infrastructure:** none owned here. The adopter runs the Collector.

**Deployment sequencing:** `core`'s version bump (T3) and the distribution
release (T9) are independent; neither blocks the other.

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

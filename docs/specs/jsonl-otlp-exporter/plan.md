# Plan: jsonl-otlp-exporter

> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material: an implementer corrects them in place as the
> work teaches, without an amendment and without a review round.

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packages/credbroker/` (distribution shape: pyproject,
  package dir, tests, own CHANGELOG, README-pypi, AGENTS.md — and the precedent
  that a published package's public contract lives in its README rather than in
  a spec); `.github/workflows/release-credbroker.yml` (release template);
  `packages/agentbundle/pyproject.toml:31-32` (the console-script precedent);
  `packages/agentbundle/agentbundle/https_catalogue.py` (outbound-`urllib`
  hardening — read for technique, deliberately not imported, since this package
  must remain extractable). Named uncertainty: no repository precedent exists for
  an outbound-network CLI, so the transport hardening is adapted rather than
  reused.

## Approach

Layers ordered by provability. Everything provable with no network lands before
anything that opens a socket, so a reviewer sees the off-by-default guarantee
before the sending code exists to complicate it.

The package must stay extractable: nothing here imports from this repository, and
its tests use only its own fixtures. That is what makes the capability contract
true rather than aspirational.

## Constraints

- Standard library only at runtime.
- No module may name a consumer. The reference mapping profile used in tests is a
  fixture, not a shipped consumer profile.
- `https_catalogue.py` is read, not imported — importing it would make the
  package depend on this repository and defeat extraction.
- Its HTTPS-only policy is deliberately not carried over: plaintext to a resolved
  loopback address is permitted, because a local Collector is the common target.

## Construction tests

The golden pins the emitted layout so attribute drift shows in a diff. The live
round trip is the only check that observes attribute *naming* — a structurally
valid payload with wrong names is accepted and stored, which no rejection and no
golden can see.

Transport tests drive a seam in front of the transport, so each response shape is
a fixture rather than a live condition.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| `README-pypi.md` (public contract) | T7 | AC-0030, AC-0032 green | Renders on PyPI |
| `docs/profiles.md` (extension point) | T7 | AC-0031 green | Interface and compat status stated |
| `CHANGELOG.md` (release) | T8 | Version bump with entry | Tag matches `pyproject` |
| `AGENTS.md` (maintainer) | T1 | Test command, release coupling | File accurate |

## Design (LLD)

### Interfaces & contracts — the profile format

A profile is a TOML document declaring six keys: `timestamp_field`,
`timestamp_format` (from the closed set `rfc3339` / `epoch-millis` /
`epoch-seconds`), `severity_field`, `severity_map` (literal value to integer),
`identity`, and `allowlist`. It is data, never code: loading executes nothing,
which is what keeps the extension point's threat model to bounded untrusted-input
parsing rather than arbitrary execution. A selected profile is trusted to define
the payload; selecting one is the operator's act, and ADR-0115 records why an
invocation-level cap was declined.

### Component / module decomposition

Five modules, split on what each can be tested without: `config` (no I/O beyond
one file), `source` (reads and bounds the input), `encode` (pure), `transport`
(the only module that opens a socket), `cli` (argument parsing, exit codes), plus
`mappings/` holding profile declarations.

### Interfaces & contracts

A profile declares exactly three things: the timestamp field, the severity field,
and the record-identity attributes. That is the entire extension surface, and it
is published — `docs/profiles.md` states it, and the compatibility statement says
it is provisional in 0.x.

### Failure, edge cases & resilience

A malformed line is skipped and noted, never fatal. Send failure exhausts the
retry budget then exits 1, or 0 under `--best-effort`. The package writes no
durable state anywhere.

## Tasks

<!-- The package does not exist at plan approval, so per
     `references/tdd-stubs.md` a stub may not invent a module to assert against.
     The TDD tasks below carry `no stub (implementation-discovered)` with their
     discovery predicate and proof obligation. -->

### T1: Scaffold the distribution

**Depends on:** none

**Touches:** `packages/jsonl-otlp-exporter/`

**Tests:**
- `no stub (goal-based)`. Reason: the outcome is a build artifact and a process
  status, which the build command and the installed console script already prove;
  a test asserting what `python3 -m build` just demonstrated adds no signal.
- Goal-based: `python3 -m build` produces a wheel and sdist; a fresh venv
  installs it and `jsonl-otlp-export --version` prints the version. Verifies AC-0029.

**Approach:**
- Mirror `packages/credbroker/`'s structure; declare `[project.scripts]`.

**Done when:** the console script runs from a fresh venv.

### T2: Configuration resolution and the off-by-default proof

**Depends on:** T1

**Touches:** `jsonl_otlp_exporter/config.py`, its tests

**Tests:**
- `no stub (implementation-discovered)`. Discovery predicate: the resolver's
  signature is fixed once T1's layout exists; asserting against it now would
  invent the symbol. Constraint: stdlib only, no network, the config file read as
  untrusted TOML. Required outcome: the three-source precedence and the empty
  case. Verification mode: TDD. Proof obligation: the empty case asserts the
  transport seam is never constructed, proving off-by-default before any sending
  code exists.
- Three-source precedence, one case per source plus the empty case. Verifies
  AC-0001, AC-0002, AC-0003, AC-0004.
- The unconfigured run exits 0. Verifies AC-0033.
- It writes the not-configured note to stderr. Verifies AC-0060.

**Done when:** the empty case passes with a transport seam that raises if constructed.

### T3: Input acquisition — confinement, bounds, modes, lifecycle

**Depends on:** T1

**Touches:** `jsonl_otlp_exporter/source.py`, its tests

**Tests:**
- `no stub (implementation-discovered)`. Discovery predicate: the reader's seam is
  fixed once T1's layout exists. Constraint: canonicalise before opening, confine
  to `--root`, write no position state. Required outcome: refusal before any read
  for an unsafe path. Verification mode: TDD. Proof obligation: confinement cases
  assert the transport seam is never constructed.
- The input file's content, size and mtime are unchanged after a run. Verifies AC-0061.
- A `--config` path that is a symlink, a FIFO, a device or a directory is refused
  on the opened descriptor with nothing sent and exit 1, and a regular config file
  outside `--root` is **accepted** — the pair is what separates open-time proof
  from root confinement, and a build that reuses `--input`'s predicate fails the
  second case. Verifies AC-0062.
- A symlink leaf, a non-regular file, and a path escaping `--root` are refused
  with nothing sent. Verifies AC-0017.
- A directory component swapped between resolution and open is refused: the walk
  holds a root descriptor, opens each component no-follow, and checks leaf
  identity both before and after opening. This is the case that separates
  descriptor-anchored traversal from pathname validation, and a pathname-first
  implementation passes every other case here.
- A line over 64 KiB is refused before decoding; the rest still send. Verifies AC-0018.
- A non-parsing line is skipped and the remainder sent. Verifies AC-0016.
- A line that parses as JSON but is an array, a string or a number at top level
  is skipped with its line number reported and the remainder sent. Verifies
  AC-0073. A build that treats "parses as JSON" as "is a record" passes AC-0016
  and fails this.
- The skipped line is reported with its line number. Verifies AC-0038.
- An absent `--input` path sends nothing and exits 1. Verifies AC-0043.
- Default mode is one-shot; `--follow` delivers an appended line. Verifies AC-0020, AC-0021.
- `--for` takes integer seconds from the first read. Verifies AC-0042.
- Under `--follow` against a file holding one valid record, then truncated to
  zero, then replaced by a new inode, then given a trailing line with no newline:
  the first record sends exactly once, none of the three conditions produces a
  record, and the run exits 0 when `--for` elapses. Verifies AC-0022. The absent
  file is **not** here — it exits 1 under AC-0043, and pairing the two in one
  assertion is how the earlier contradiction between them survived two rounds.

**Done when:** every file-lifecycle case passes and no position file is written.

### T4: Encoder and the profile interface

**Depends on:** T1

**Touches:** `jsonl_otlp_exporter/encode.py`, `jsonl_otlp_exporter/profile.py`
(parsing, schema validation and confined loading of a `--profile` file), its
tests and their profile fixtures. **No `mappings/` package.** ADR-0115 makes a
profile data the consumer supplies, so the distribution bundles none: the
profiles this task's tests use are fixtures under the test tree, never importable
package data, and nothing in the package resolves a profile by name.

**Tests:**
- `no stub (implementation-discovered)`. Discovery predicate: the encoder's
  signature follows the profile interface, which T4 defines. Constraint: pure
  function, no I/O. Required outcome: a byte-stable request body. Verification
  mode: TDD. Proof obligation: the golden comparison is written first and fails
  until the mapping exists.
- Byte-exact golden for the recorded three-line fixture. Verifies AC-0005.
- `service.name` takes `--service-name`; with the flag absent it takes the stem
  of the `--profile` filename, asserted over a profile file whose stem differs
  from every value inside it, so a build reading the default out of the profile's
  contents fails. Verifies AC-0007.
- Records carry the profile's declared identity attributes. Verifies AC-0023.
- A field that is outside the allowlist *and* is not the profile's
  `timestamp_field`, `severity_field` or an `identity` member appears nowhere in
  the body. Verifies AC-0034. The carve-out is load-bearing: an assertion over
  every non-allowlisted field contradicts AC-0053, which requires the declared
  fields through.
- A profile declares exactly the six keys; a missing or extra key is refused.
  Verifies AC-0035.
- A profile whose content would execute if imported is parsed as data and
  refused on schema. Verifies AC-0047.
- `--profile` is opened under AC-0017's discipline. Verifies AC-0048.
- A bad `timestamp_format`, a wrong-typed value in any of the six keys, an oversized or
  unparseable profile, and no `--profile` at all are each refused before any
  request. Verifies AC-0049, AC-0050, AC-0051, AC-0052.
- A declared timestamp, severity or identity field reaches its destination whether
  or not the allowlist names it, and is not duplicated as an attribute.
  Verifies AC-0053.
- Timestamp conversion, one case per admitted representation and one per refused
  one: an RFC 3339 string with `Z`, with `±HH:MM`, and with nine fractional
  digits each convert to their exact nanosecond count; an offset-less string is
  refused. Verifies AC-0064. The offset-less case is the load-bearing one — a
  build that defaults it to UTC passes every other timestamp case here.
- Integer and digit-string inputs under `epoch-millis` and `epoch-seconds`
  convert by integer multiplication, and a fractional value is refused. The
  assertion uses a value whose float round-trip is lossy, so a build converting
  through a float fails. Verifies AC-0065.
- An absent, non-admitted or out-of-range timestamp skips its record, reports its
  line number, and leaves the remaining records sent. Verifies AC-0066.
- A `severity_map` value of 0 and one of 25 are each refused before any request.
  Verifies AC-0067.
- A record whose severity is absent, `null`, or unnamed by the map is sent with
  no `severityNumber` and no `severityText`, its value reported once with a
  count, and the exit status unchanged. Verifies AC-0068. This is asserted over a
  fixture in which most records are unmapped, because the measured envelope makes
  that the common case, not the edge.
- A mapped severity emits the mapped integer and the original string. Verifies AC-0069.
- One case per `AnyValue` member over a record carrying a string, a boolean, an
  integer, a float, an array and a nested object, asserted on the emitted body.
  Verifies AC-0070. The nested object is the work-loop envelope's shape, so the
  recursive case is exercised by the first real consumer rather than only by a
  synthetic fixture.
- A JSON `null` leaves its key absent from the body entirely. Verifies AC-0071.
- A value nested nine levels deep emits no attribute and is reported once.
  Verifies AC-0072.

**Done when:** the golden passes, field names appear only in a profile, and the
installed wheel contains no profile file — the check that keeps a fixture from
drifting back into shipped data.

### T5: Transport — destination policy, retry, batching

**Depends on:** T2, T4

**Touches:** `jsonl_otlp_exporter/transport.py`, its tests

**Tests:**
- `no stub (implementation-discovered)`. Discovery predicate: the opener's seam is
  fixed once the config and encoder interfaces exist. Constraint: adapt
  `https_catalogue.py`'s opener and redirect handling without importing it.
  Required outcome: every response shape drives its documented behaviour.
  Verification mode: TDD. Proof obligation: each fixture asserts a distinct
  observable, so no single change makes them all pass.
- Non-empty `partialSuccess` produces no retry. Verifies AC-0008.
- It reports the rejected count. Verifies AC-0036.
- It exits 1. Verifies AC-0054.
- `Retry-After: N` delays the next request by `min(N, 30)` from response receipt on
  a monotonic clock; absent, negative or unparseable is 0. Verifies AC-0009.
- At most three attempts per run, counted across every request the run issues.
  Verifies AC-0010.
- A request abandoned 30s after its own resolution begins, on a monotonic clock.
  Verifies AC-0040.
- A run that stops issuing at 120s from its first resolution AND abandons a
  request still in flight at that deadline — a fixture whose request begins at
  119s proves the second half, which an issuance-only cutoff fails. Verifies AC-0055.
- A response refused at 1 MiB plus one byte without further reading. Verifies AC-0041.
- An oversized `--config` refused before parsing. Verifies AC-0056.
- At most 512 records per request. Verifies AC-0011.
- Over a 10,000-record input, a counting seam records that no more than 512 parsed
  records are resident at any instant. A build that reads the file fully before
  sending passes every other bound here and fails this one. Verifies AC-0063.
- A request body never exceeds 8 MiB, asserted by constructing the worst
  admissible case rather than trusting the ceiling, **and** a batch that would
  exceed it is split rather than dropped or truncated — the split half is what
  distinguishes a correct encoder from one that silently discards the overflow.
  Verifies AC-0019.
- HTTPS accepted at any host with chain and hostname verified; a non-http(s)
  scheme refused; plaintext accepted only when EVERY resolved address is
  loopback and issued to a verified address without re-resolution; plaintext to
  any non-loopback resolution refused; a redirect not followed; user-info
  refused; and every message naming an endpoint or redirect target renders it
  through one representation carrying no user-info, no query, no fragment and no
  C0 or C1 control character. Verifies AC-0024, AC-0044, AC-0025, AC-0026,
  AC-0027, AC-0028, AC-0045.
- The loopback fixture uses a stateful resolver whose first answer is loopback
  and whose second answer is routable, so a build that re-resolves at connect
  time reaches the routable address and fails. A fixture returning both addresses
  at once cannot distinguish the two implementations.
- Proxy environment variables naming a non-loopback proxy do not cause a
  plaintext request to leave the host: the opener is constructed with proxy
  handling disabled rather than inheriting the ambient environment.
- Integration, against a live Collector with an `otlp` receiver and a `debug`
  exporter: three records land with each field at its mapped destination. Verifies AC-0006.

**Approach:**
- Loopback is decided by resolving the host and testing the resolved address, not
  by string-matching `localhost`.

**Done when:** every response-shape and destination fixture drives its documented
behaviour, and the live round trip lands three records.

### T6: CLI and exit codes

**Depends on:** T3, T5

**Touches:** `jsonl_otlp_exporter/cli.py`, its tests

**Tests:**
- `no stub (goal-based)`. Reason: every criterion here is one invocation and one
  observed process status, so the check is the invocation itself; there is no
  in-process contract nearer the surface to stub against.
- Send failure exits 1; `--best-effort` exits 0. Verifies AC-0012.
- An unknown flag exits 1, not 2 — the argument parser's default must be
  overridden or it collides with the reserved band. Verifies AC-0013.
- Every invocation in the `### Exit codes` table's closed set returns a status
  in exactly `{0, 1, 130}` — the set is read from the table and walked case by
  case, so a status of 42 fails as surely as a status of 3. Verifies AC-0014. An
  assertion that merely excludes the 2–9 band passes a build returning 42.
- SIGINT exits 130. Verifies AC-0015.
- A run in which no line yields a valid record exits 1. Verifies AC-0039.

**Approach:**
- Top-level `except Exception` maps to 1; never `except BaseException`, so
  `SystemExit` and `KeyboardInterrupt` pass through.

**Done when:** the exit-code table is exercised end to end.

### T7: The published contract

**Depends on:** T6

**Touches:** `README-pypi.md`, `docs/profiles.md`

**Tests:**
- `no stub (goal-based)`. Reason: these criteria are structural properties of
  authored prose files — a heading, a parseable fenced block, a named string —
  checked by reading the file rather than by exercising a code path.
- `README-pypi.md` states what is sent, what the payload contains, and the
  destination. Verifies AC-0030.
- `docs/profiles.md` carries a fenced `toml` block parsing as a profile that
  satisfies AC-0035, names all six keys outside it, and its worked profile
  demonstrates an `allowlist` that omits at least one input field. Verifies AC-0031.
- `README-pypi.md` states semantic versioning and that the profile interface is
  provisional in 0.x. Verifies AC-0032.

**Done when:** a reader who has never seen this repository can write a profile
from `docs/profiles.md` alone.

### T8: Release

**Depends on:** T7

**Touches:** `.github/workflows/`, `CHANGELOG.md`

**Tests:**
- `no stub (manual QA)` for the end-to-end run, and `no stub (goal-based)` for
  AC-0046, AC-0057, AC-0058 and AC-0059. Reason: the manual case exercises a
  published artifact against a live service, which no in-process assertion
  reaches; the workflow criteria are properties of a YAML file and of a tagged
  run, read rather than executed.
- Manual QA: the console script installed from the built wheel is run against a
  real JSONL file and a real Collector; stdout, stderr and exit code recorded in
  the verification ledger.
- A tag whose version disagrees with `pyproject.toml` is refused by the release
  workflow. Verifies AC-0046.
- The workflow publishes through OIDC trusted publishing with no long-lived
  credential, pins every third-party action to a full-length commit SHA, and
  installs the built wheel into a fresh virtual environment before publishing.
  Verifies AC-0057, AC-0058, AC-0059.

**Done when:** the tagged workflow publishes and a fresh `uv tool install`
produces a working command.

## Rollout

Additive; nothing existing changes. Reversal is yanking the release.

## Risks

- **Extraction rots.** A later import from this repository would silently break
  the capability contract. The `Constraints` section names it; the guard is that
  the package's tests use only its own fixtures.
- **The profile interface is a published extension point.** Once documented,
  changing it is a breaking change. This is why the compatibility statement calls
  it provisional in 0.x rather than leaving it implied.

## Changelog

- 2026-09-12 — Split from `loop-telemetry-export` so a published distribution has
  a contract a stranger can read. The integration that supplies the `work_loop`
  profile and declares this package stays in that spec.

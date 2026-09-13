# Plan: jsonl-otlp-exporter

> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material: an implementer corrects them in place as the
> work teaches, without an amendment and without a review round.

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
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
- A symlink, a non-regular file, and a path escaping `--root` are refused with
  nothing sent. Verifies AC-0017.
- A line over 64 KiB is refused before decoding; the rest still send. Verifies AC-0018.
- A non-parsing line is skipped and the remainder sent. Verifies AC-0016.
- Default mode is one-shot; `--follow` delivers an appended line; `--for` ends the
  run. Verifies AC-0020, AC-0021.
- Absent file, truncated file, replaced inode, and a trailing line with no newline
  each exit 0 with no partial or duplicate record. Verifies AC-0022.

**Done when:** every file-lifecycle case passes and no position file is written.

### T4: Encoder and the profile interface

**Depends on:** T1

**Touches:** `jsonl_otlp_exporter/encode.py`, `jsonl_otlp_exporter/mappings/`, its tests

**Tests:**
- `no stub (implementation-discovered)`. Discovery predicate: the encoder's
  signature follows the profile interface, which T4 defines. Constraint: pure
  function, no I/O. Required outcome: a byte-stable request body. Verification
  mode: TDD. Proof obligation: the golden comparison is written first and fails
  until the mapping exists.
- Byte-exact golden for the recorded three-line fixture. Verifies AC-0005.
- `service.name` takes `--service-name`, defaulting to the profile's name. Verifies AC-0007.
- Records carry the profile's declared identity attributes. Verifies AC-0023.

**Done when:** the golden passes and field names appear only in a profile.

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
- Non-empty `partialSuccess` produces no retry and reports the count. Verifies AC-0008.
- `Retry-After: N` waits `min(N, 30)`; absent, negative or unparseable is 0. Verifies AC-0009.
- At most three attempts. Verifies AC-0010.
- At most 512 records per request. Verifies AC-0011.
- A request body never exceeds 8 MiB, asserted by constructing the worst
  admissible case rather than trusting the ceiling. Verifies AC-0019.
- HTTPS accepted at any host; plaintext only to a resolved loopback address;
  plaintext to a non-loopback host refused before sending; a redirect not
  followed; user-info in the netloc refused. Verifies AC-0024, AC-0025, AC-0026,
  AC-0027, AC-0028.
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
- Send failure exits 1; `--best-effort` exits 0. Verifies AC-0012.
- An unknown flag exits 1, not 2 — the argument parser's default must be
  overridden or it collides with the reserved band. Verifies AC-0013.
- No invocation returns a code in 2 through 9. Verifies AC-0014.
- SIGINT exits 130. Verifies AC-0015.

**Approach:**
- Top-level `except Exception` maps to 1; never `except BaseException`, so
  `SystemExit` and `KeyboardInterrupt` pass through.

**Done when:** the exit-code table is exercised end to end.

### T7: The published contract

**Depends on:** T6

**Touches:** `README-pypi.md`, `docs/profiles.md`

**Tests:**
- `README-pypi.md` states what is sent, what the payload contains, and the
  destination. Verifies AC-0030.
- `docs/profiles.md` states the three things a profile declares and shows a
  worked profile. Verifies AC-0031.
- `README-pypi.md` states semantic versioning and that the profile interface is
  provisional in 0.x. Verifies AC-0032.

**Done when:** a reader who has never seen this repository can write a profile
from `docs/profiles.md` alone.

### T8: Release

**Depends on:** T7

**Touches:** `.github/workflows/`, `CHANGELOG.md`

**Tests:**
- Manual QA: the console script installed from the built wheel is run against a
  real JSONL file and a real Collector; stdout, stderr and exit code recorded in
  the verification ledger.

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

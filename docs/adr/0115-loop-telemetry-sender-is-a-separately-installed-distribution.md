# ADR-0115: The loop-telemetry sender is a separately installed distribution, not pack content

- **Status:** Accepted
- **Date:** 2026-09-12
- **Decision-makers:** eugenelim
- **Related:** [`telemetry.md`](../architecture/telemetry.md) §§ 5.2, 8, 10 (the invariant this preserves and the measured backend route); [delivery mechanism survey](../product/research/loop-telemetry-export-survey.md) and its [counterpoints](../product/research/loop-telemetry-export-counterpoints.md) (the five mechanisms priced, and which survey findings did not survive review); [`docs/specs/loop-telemetry-export/`](../specs/loop-telemetry-export/spec.md) (the delivery)

## Decision summary

- **Decision:** the component that sends work-loop telemetry ships as its own
  PyPI distribution, `jsonl-otlp-exporter`, installed by the adopter with
  `uv tool install` or `pipx`. It is named for the capability — a JSONL event
  log in, OTLP logs out — not for its first consumer. The mapping profile is
  consumer-supplied declarative TOML selected at invocation; the distribution
  bundles no consumer's profile. See the 2026-09-13 amendment below, which
  governs where this summary and it differ. No pack gains a network path. `packs/core`
  declares it as an optional runtime dependency and reports on it; it never
  installs it.
- **Because:** `telemetry.md` § 8 states "Nothing in a pack sends. Anything that
  sends is installed separately", and § 5.2 offers adopters a structural promise
  — "if you never install the thing that sends, nothing can send, whatever any
  file says". A package-manager boundary keeps both literally true; every
  pack-resident home reduces them to a configuration promise.
- **Applies to:** this sender and any future per-engine sender. It does not
  decide where a shared emitter would live, because no shared emitter is
  justified yet.
- **Tradeoff accepted:** a third published distribution to version, release and
  support, plus adopter friction — the exporter must be installed deliberately,
  and an adopter who never installs it gets no telemetry and no warning that
  they are missing any. That silence is the cost of the structural guarantee.
- **Revisit if:** a second engine needs to emit and the two senders duplicate
  meaningful OTLP mapping, redaction, batching or retry logic. That is the
  trigger for a shared library at `~/.agentbundle/lib/`, not before.

## Decision drivers

1. **The structural promise must survive.** § 5.2 is written to adopters, not to
   maintainers, and it is stronger than any setting.
2. **The sender must stay upgradable.** A security fix in outbound-network code
   has to reach an installed adopter.
3. **One exporter per engine is the default.** A shared emitter is the deviation
   and must earn its place.
4. **No new dependency without an ADR.** Whatever ships must work from the
   standard library or justify otherwise.

## Context

`loop-engine.py` records a thirteen-field envelope to `.loop-run/events.jsonl`
on every transition. Nothing sends it. Five delivery mechanisms were priced
against the drivers above; four were rejected on evidence rather than taste.

**A seeded script** — `packs/core/seeds/tools/…` — fails drivers 1 and 2 on
three independent counts. `deliver_seeds` writes through `write_jailed` with no
mode, so the adopter receives a non-executable file. `upgrade.py` never calls
`deliver_seeds`, so a delivered seed is never refreshed. And an adopter edit
forks the upstream copy to `*.upstream.py`, leaving a stale sender live beside a
fix that never applies. The catalogue lint was never the obstacle: registered
with an empty tuple, a working `.py` passes CAT-L029 cleanly.

**A user-scope pack** using the existing `adapter-root-bins` rail fails driver 2
for the same reason one layer down: `collect_pack_root_bins` has exactly one
production caller, inside the user-scope install path, and `upgrade.py` does not
reference it. That gap already affects shipped content — `credential-brokers`'
`sso-broker.py` is delivered once and never refreshed — and is recorded as a
separate follow-on rather than repaired here.

**Extending that rail to repo scope** would carry the widest blast radius:
adapter contracts, the repo path jail, install, upgrade, uninstall and ownership
semantics. Copilot's `allowed-prefixes.repo` omits `.agentbundle/` entirely, so
a gate flip alone breaks one adapter. Its only distinct benefit is putting the
sender in `core`, which is the outcome driver 1 rejects.

**Documenting a Collector and shipping nothing** preserves every invariant at
near-zero repository cost, but leaves the adopter to build the whole path. It
does not deliver the outcome.

**A local transformer that never opens a socket** satisfies § 8 word-for-word
and remains available as a later addition. It was not chosen because it moves
the last mile onto the adopter rather than closing it.

The encoding follows from the destination. Splunk's own OTLP endpoint requires
`application/x-protobuf` and answers JSON with HTTP 415; Elastic documents proto
as its only encoding. A Collector accepts OTLP/HTTP JSON with no configuration,
and Splunk's own guidance is to send to the Collector you deployed. Targeting a
Collector therefore lets one stdlib sender reach every backend, which satisfies
driver 4 without a dependency — and `guides/_shared/how-to/author-a-skill.md`
already prefers stdlib over a pip dependency.

## Consequences

**The adopter gains a guarantee no setting can give.** Not installing the
distribution means no code capable of sending exists on the machine.

**Silence is not consent, so disclosure is separate.** "Off unless an endpoint
is configured" is a behaviour guarantee; an undisclosed capability obtains no
informed agreement. The distribution's documentation and the core guide state
that the capability exists, what it carries and where it goes, while it sends
nothing. This is carried as an acceptance criterion, not as documentation
polish.

**A third distribution enters the release surface.** It follows
`release-credbroker.yml` — trusted publishing, a SHA-pinned publish action, a
tag-equals-version assertion and a fresh-venv smoke — and it must be added to
every list where this repository enumerates a published distribution, because
those lists are literal: the test-suite invocations, mypy's `files`, the root
`pythonpath` and the pip-audit build-system leg each name packages one by one.
A distribution absent from them is checked by nothing.

**`[[pack.runtime-dependencies]]` gains its first reader.** The schema has been
declared and unused; this delivery writes the reporting side only. Reporting is
Tier 1 — detect and fail clean. The installer does not acquire packages, and
extending `install --yes` to cover acquisition would be an authority expansion
this decision does not make.

**No shared emitter exists, but the name does not foreclose one.** One exporter
per engine matches the prevailing architecture across Argo, Dagger, Buildkite and
Jenkins, none of which routes telemetry through a shared in-process component.
Naming and shared abstraction are separable, though, and only the first is
irreversible: a PyPI name cannot be reclaimed, so a consumer-scoped name would
force a second package and a migration the day a second engine needed to emit,
while a capability-scoped name costs nothing if that day never comes.

**The mapping profile is a published extension point, selectable from outside the
package.** *(Amended 2026-09-13. This paragraph replaces an earlier statement
that no profile-selection surface was promised in v1 and that the seam was
structural rather than contractual. The owner reversed that on 2026-09-13 so a
consumer can own and ship its own profile rather than have one bundled into a
capability-scoped distribution. The earlier reading is recorded here because a
round-1 security finding was refuted on its premise, and that refutation is void
under this amendment.)*

A profile declares five things: its timestamp field and that field's format, its
severity field and that field's mapping, its record-identity attributes, and the
allowlist of fields that may be sent. A consumer supplies a profile; the package
does not bundle a consumer's.

**A profile is declarative data, never code, and that is what makes the
extension point affordable.** Everything a profile declares is a name or a
literal — two field names, a format drawn from a closed enum, a literal
value-to-number map, and two lists of field names. None of it requires
execution. A profile is therefore a TOML document, read with the same bounded,
confined discipline as any other input this distribution reads, and loading one
executes nothing. An implementation that imports a Python module as a profile,
or evaluates any part of a profile, is non-conforming.

That choice is what collapses the threat model. Had a profile been code, loading
would have been arbitrary execution in a process that reads untrusted files and
holds a network endpoint, and a hostile profile would have disabled the very
payload control it exists to declare. As data, the residual threat is ordinary
untrusted-input parsing, bounded by file size and a closed format enum.

**The residual boundary is stated rather than engineered away.** A profile
defines the payload, so a selected profile is trusted: selecting one is the
operator's act, the same trust they extend to a config file. An
invocation-level cap that could only narrow a profile's allowlist was considered
and declined — it adds a second control and a concept every operator must learn,
to constrain a file the operator already chose.

**Conversion semantics are pinned, and every unmapped case degrades rather than
drops.** *(Amended 2026-09-13. The spec previously bounded four value-level
questions out of scope with this ADR's owner named; the owner settled them on
2026-09-13 and they are recorded here.)*

A profile pins the *form* of a mapping; these four decisions pin what the values
mean.

**Timestamps admit one representation per format, and never guess.** `rfc3339`
takes a string carrying date, time and an *explicit* offset, with up to nine
fractional digits. An offset-less string is refused rather than assumed to be
UTC: assuming costs up to fourteen hours of silent error, and a wrong timestamp
is worse than an absent record because it is indistinguishable from a real one.
`epoch-millis` and `epoch-seconds` take an integer — never a float — and convert
in integer arithmetic, because a float seconds value cannot represent a
nanosecond instant exactly and the rounding is invisible downstream.

**Severity numbers are constrained to OTLP's 1–24, and 0 is refused.** Zero is
`SEVERITY_NUMBER_UNSPECIFIED`, which a backend cannot distinguish from a field
that was never set, so admitting it would let a profile express "unknown" in a
way no consumer can query.

**An unmapped or absent severity sends the record anyway.** This is the decision
with the largest blast radius, and it was settled on a measurement rather than a
preference: of the work-loop FSM's fifteen events, **five carry no gate result at
all** — `spec-ready`, `plan-locked`, `wave-complete`, `wave-passed` and
`contract-amendment` — and those are among the most frequent transitions in a
real run. Skipping a record whose severity does not map would therefore discard a
third of the event vocabulary and most of the traffic. A run emits the record
with severity omitted, reports each distinct unmapped value once with a count,
and exits 0 on that account. Failing the run instead would mean that adding one
FSM event breaks an adopter's telemetry in production, which inverts the
degradation this whole design is built on.

**JSON maps onto `AnyValue` by type, recursively, and `null` emits nothing.**
The `AnyValue` wrapper list is one of only two emission rules measured to be
load-bearing for ingestion (§ 10.3 of `telemetry.md`; the other is hex
identifiers). Objects and arrays convert recursively, which the first consumer
already exercises — the work-loop envelope's `budgets` field is a nested object.
`null` emits no attribute rather than an empty one, because an absent key is
queryable and an empty `AnyValue` is not. Recursion is bounded at eight levels so
a hostile input cannot make the encoder walk without limit, and a line whose
top-level JSON value is not an object is skipped exactly as an unparseable line
is.

## Alternatives considered

Each is priced against the drivers in Context above: a seeded script (drivers 1,
2), a user-scope pack on the existing rail (driver 2), extending that rail to
repo scope (driver 1, plus an adapter contract change), documentation only (does
not deliver), and a local transformer (preserves § 8 but does not close the last
mile). The official OpenTelemetry SDK was rejected against driver 4: the HTTP
exporter pulls `protobuf`, `googleapis-common-protos` and the api/sdk/proto
stack, where the wire format needed here is a documented public contract.

## Confirmation

- **Mode:** review plus lint/CI.
- **Signal:** no module under `packs/` opens a socket; the distribution's tests,
  type checks and SCA inputs appear in every enumeration listed under
  Consequences; and the exporter's own gates run in CI.
- **Owner:** the spec author, with the security reviewer at the pre-EXECUTE gate
  covering the outbound boundary.

## References

- [`telemetry.md`](../architecture/telemetry.md) — §§ 5.2 and 8 for the
  invariant, § 10 for the measured Splunk route and encoding boundary.
- [Delivery mechanism survey](../product/research/loop-telemetry-export-survey.md)
  and [counterpoints](../product/research/loop-telemetry-export-counterpoints.md).

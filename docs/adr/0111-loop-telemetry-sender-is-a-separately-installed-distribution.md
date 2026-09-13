# ADR-0111: The loop-telemetry sender is a separately installed distribution, not pack content

- **Status:** Accepted
- **Date:** 2026-09-12
- **Decision-makers:** eugenelim
- **Related:** [`telemetry.md`](../architecture/telemetry.md) §§ 5.2, 8, 10 (the invariant this preserves and the measured backend route); [delivery mechanism survey](../product/research/loop-telemetry-export-survey.md) and its [counterpoints](../product/research/loop-telemetry-export-counterpoints.md) (the five mechanisms priced, and which survey findings did not survive review); [`docs/specs/loop-telemetry-export/`](../specs/loop-telemetry-export/spec.md) (the delivery)

## Decision summary

- **Decision:** the component that sends work-loop telemetry ships as its own
  PyPI distribution, `jsonl-otlp-exporter`, installed by the adopter with
  `uv tool install` or `pipx`. It is named for the capability — a JSONL event
  log in, OTLP logs out — not for its first consumer, and the work-loop's field
  mapping is one named profile inside it. No pack gains a network path. `packs/core`
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
while a capability-scoped name costs nothing if that day never comes. The field
mapping therefore sits behind a named seam from v1, with `work_loop` as the only
shipped profile. A second engine adds a profile; it does not fork a package. No
profile-selection surface is promised in v1, so this is a structural choice
rather than a published contract.

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

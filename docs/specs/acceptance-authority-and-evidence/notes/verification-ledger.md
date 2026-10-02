# Verification ledger: acceptance authority and evidence

Execution observations for the approved Slice 1 plan. This file is not
hash-pinned; it records how tasks are verified, not new obligations.

## Script-versus-schema parity (owner decision, 2026-10-01)

The canonical schemas in `contracts/delivery/` stay repository-only. Neither
`agentbundle` nor the Core pack ships them to adopters, and no work-loop script
reads them at runtime. Agents never write delivery records directly: trusted
work-loop scripts build every record from typed arguments, as `loop-engine`
already does for its state.

Every task that adds a module which builds or accepts a delivery record (T3a
through T7) therefore carries parity tests:

- each record the module emits validates against its canonical schema, using
  `jsonschema` at test time only; and
- the module's own validation refuses each schema-invalid case (an unknown
  authority-shaped field, a missing required field, an unknown
  `schema_version` major, an out-of-enum value) with a stable code.

The protected skill-copy set for AC-0013 is a constant in the scripts, with a
test pinning it to the work-loop projections `contracts/adapter.toml` declares
for the Core pack's surfaces. T9a's conformance run rolls these suites up as
the evidence for the Release history closeout: "Released pack versions contain
implementations that validate against the canonical contracts".

Shipping input schemas to the agent is deferred to the first slice that
accepts agent-written structured payloads.

## T9a dispatch evidence (recorded 2026-10-01)

T9a's benchmark evidence is admissible only when the dispatched run's head
commit SHA equals the SHA on which the `test-corpus.yml` posture test,
`actionlint`, and both `zizmor` passes ran. Use the CI-pinned `zizmor`
version from `tools/requirements-ci-security-locked.txt`. A mismatch voids
the evidence and requires a rescan. This follows a round-12 security Nit that
was deferred rather than written into the pinned plan.

## One benchmark entry point (build-time guidance, 2026-10-01)

T4 creates one committed benchmark entry point, and the `test-corpus.yml`
benchmark job runs it with a fixed command. T7 adds the cold-rehydration
benchmark inside that same entry point. The job command, the single declared
exception, the ADR, and the claim sites T4 writes then stay true when T7
lands. T4 writes those sites to describe both benchmarks.

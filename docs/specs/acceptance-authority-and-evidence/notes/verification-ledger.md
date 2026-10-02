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

## Benchmarks run inside the corpus (owner decision, 2026-10-01)

The AC-0018 harness takes 8.0 s for all 105 runs on a local M1 Max (p95 about
65 ms against the 2 s bound). The benchmarks are therefore ordinary pytest
tests in the work-loop pack suite, which `make test` already runs, so a
`test-corpus.yml` dispatch measures them on GitHub-hosted `ubuntu-latest` with
no workflow change. Each test asserts its bound, prints its measurement into
the job log, and writes results only under a temporary path. T9a records the
dispatched run's head commit SHA with the passing benchmark tests. The earlier
benchmark job, posture test, single-roster exception, and ADR draft were
dropped before commit.

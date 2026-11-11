# ADR-0165: Neutral run-state, run-event and run-control contracts name no host product

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** orchestration, tooling
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0115 (the proposal this records); ADR-0164 (the program that writes them); ADR-0162 (the supervisor contract, a separate record)

## Context

A host that shows or steers a run needs files it can read without knowing which tool wrote them. If a contract names one host product, every other host must adopt that product's words. A contract that is one writer's private notes would also become a second source of truth.

## Decision

We will define three file contracts under `contracts/ferryman/`, and none names a host product.

- **D1:** `run-state.v1` is one run's projection. `ferryman` is the only writer. It is derived and never authoritative, and the repository stays the source of truth.
- **D2:** `run-event.v1` is an append-only line per step. It carries a `seq` that rises per run, and a gap in `seq` marks a lost line. A reader then resyncs from `state.json`.
- **D3:** `run-control.v1` is a closed set of host commands: `answer`, `signal`, `pause`, `resume`, `stop`, `retry-worker`, `attach-done`. The host is the only writer. An unknown command is acknowledged as refused.
- **D4:** The `actor` field of a control command is a display string. It is never an input to a decision.
- **D5:** Compatibility is one rule: add optional fields in a minor version, and remove or retype a field only in a new major version.
- **D6:** A reader that meets an unknown major version refuses with `unsupported-schema`.
- **D7:** Each file has one writer, so no lock is needed. A run's files live under `<git-dir>/ferryman/runs/<run-id>/`, and projection files can be deleted without loss.
- **D8:** This record covers these three contracts only. The others: `supervisor-manifest.v1` is ADR-0162; `frontier.v1` is ADR-0166; `tracker-adapter.v1` is ADR-0170; `approval-attribution.v1` and `approval-fields.v1` are ADR-0172; `launch.v1` and `remote-transport.v1` are ADR-0175; `checkpoint-manifest.v1` is ADR-0177; `ferryman-config.v1` has no ADR assigned.

## Consequences

**Positive:**
- Any host can show a run from two files.
- A forged or misread actor name cannot change a decision.

**Negative:**
- Every host maps the neutral fields to its own display.
- A major version bump breaks readers until they update.

**Revisit if:** a host needs a field that cannot be optional, or a fourth file contract joins the set.

## Confirmation

- **Mode:** lint/CI
- **Signal:** a fixture-run conformance test shows a host reading only the state and event files, and a truncated-file replay test covers the `seq` gap. Both are designed, not yet run. A CI grep also fails on any host-product name (Studio, VelaTerm, Orca, tmux, Claude, Codex, Cursor) under `contracts/ferryman/`.
- **Owner:** eugenelim

## Alternatives considered

- **Contracts written for one host product:** other hosts would inherit its vocabulary.
- **One combined file:** a single file mixes a derived projection, an append-only log and host input, which have different writers.
- **An actor field that decides:** a display string can be forged, so it must not carry authority.

## References

- `docs/rfc/0115-mechanized-delivery.md`
- `docs/architecture/unattended-delivery-runner/01-contracts-and-data.md`

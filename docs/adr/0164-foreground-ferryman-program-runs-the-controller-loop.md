# ADR-0164: A foreground, stateless `ferryman` program runs the controller loop, not a daemon or a host-only loop

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** orchestration, tooling
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0115 (the proposal this records); ADR-0062 (no daemon or port); ADR-0144 (the pinned supervisor); ADR-0162 (the six-command contract `ferryman` is written against); ADR-0165 (the run contracts it writes); ADR-0179 (the blocking verb)

## Context

A controller today is an agent session that calls `next`, runs the request, and calls `report`. It has no durable stop rule, and a closed session loses its place. Charter Principle 3 and ADR-0062 rule out a daemon, a port, and a run registry. Someone still has to spawn workers and wait for them without a person at the keyboard.

## Decision

We will ship `ferryman`, a stateless, stdlib-only program that runs in the foreground from `packages/ferryman/`, and keep it away from procedure.

- **D1:** `ferryman` re-derives every decision from the supervisor, `HEAD`, and committed records. Its only state is attempt records, scribe intents and lock files. A run root with no open attempt or intent is disposable.
- **D2:** `ferryman` is written against the generic supervisor commands of ADR-0162. It reads only `kind`, `request_id` and `worker_mode` from a request and treats request text and worker output as untrusted.
- **D3:** Supervisors own procedure and completion. `ferryman` owns spawning one worker per request, waiting for it, and calling `report`. It never decides completion and never approves. The exception is a blocking verb (ADR-0179), where it calls the verb and spawns nothing.
- **D4:** `ferryman run` stops at a parked gate, or polls the inbox in the foreground under `--watch`. Closing the terminal ends the process, and a rerun resumes from the repository. A session boundary never resumes.
- **D5:** v1 drives one run in one checkout. It opens no port and keeps no run registry.

## Consequences

**Positive:**
- Unattended work needs no daemon, and a killed run resumes.
- A team with no host application still has an unattended path.
- Every host reuses one controller.

**Negative:**
- This repository ships and maintains a runtime package.
- A closed terminal stops the run until someone reruns it.

**Revisit if:** a charter decision admits a persistent service, or a supervisor needs a controller capability a headless worker lacks.

## Confirmation

- **Mode:** lint/CI
- **Signal:** kill-point tests restart `ferryman` at each run boundary and expect the same request id, and fake-supervisor tests cover the strict JSON parse. These tests are designed, not yet run.
- **Owner:** eugenelim

## Alternatives considered

- **Extend `work-supervisor.py` to own every phase:** it needs an edit to a script pinned by ADR-0144, which voids runs.
- **A loop that lives only in the host repository:** this is the strongest alternative. It keeps a process out of this repository. A team with no host has no unattended path, and each host re-implements the controller.
- **A persistent daemon with a run registry:** excluded by ADR-0062 and Charter Principle 3.
- **An agent-only controller:** it has no durable stop rule, and `unattended-loops.md` limits the pattern to mechanical completion criteria.

## References

- `docs/rfc/0115-mechanized-delivery.md`
- `docs/architecture/unattended-delivery-runner/03-ferryman-runtime.md`
- `docs/architecture/unattended-delivery-runner/10-decisions-and-records.md` (shapes A to F)

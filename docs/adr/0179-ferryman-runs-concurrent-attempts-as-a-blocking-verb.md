# ADR-0179: Ferryman runs concurrent attempts as a blocking verb, and the pinned launcher is trusted configuration

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** orchestration, work-loop, security
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0115 (the proposal this records); ADR-0156 (concurrency admitted only on attested read coverage, left unedited); ADR-0160 (concurrent attempts in host-contained plain directories); ADR-0164 (the foreground ferryman); ADR-0174 (the trusted configuration pin and allowlists)

## Context

Under a concurrent `concurrency` policy, the supervisor can run several tasks of one spec at once. The shipped policy is `sequential`, and it never issues the concurrent request. `ferryman` needs a defined way to handle that request when a repository turns the policy on. No phase of the runner depends on it.

## Decision

We will let `ferryman` call the supervisor's `run-concurrent` verb as a blocking verb and wait, and we will treat the pinned launcher as part of the trusted configuration.

- **D1:** When the `concurrency` policy is concurrent, `next` returns one `run-concurrent` request with a `tasks` list.
- **D2:** For this kind `ferryman` spawns no worker. It calls `work-supervisor.py run-concurrent <spec-dir> --request <id>` and waits while the supervisor spawns the pinned launcher per task, verifies the attestations, ingests, and integrates in floor order.
- **D3:** On `landed` or `held`, `ferryman` calls `report` with completion only. On `floor`, `conflict`, `cancelled` or `residue`, it calls `next`.
- **D4:** A request runs once, so a second call refuses `request-consumed`. An attestation, read, write or binding fact in `report` refuses `result-fact-refused`.
- **D5:** The supervisor recovers a dead run itself, so `ferryman` calls the verb or `status` again after a kill and never respawns.
- **D6:** The launcher is a file outside the work tree. `start --launcher` and `--launcher-sha256` bind it, and the sha256 comes from the owner's own approval answer. It is in the trusted set (listed in ADR-0174 D1).
- **D7:** A request kind the supervisor's manifest does not list parks `unknown-request-kind`. `unknown-descriptor` is for a skill version outside the declared range.
- **D8:** No phase depends on `run-concurrent`, and the shipped `sequential` policy, which never issues it, stays the floor.

## Consequences

**Positive:**
- ADR-0156 and ADR-0160 stay as they are, and the supervisor keeps every integration step.
- A worker that swaps the launcher is caught by the trusted-set pin.

**Negative:**
- A blocking verb holds `ferryman` in one call, and its attempt record has no pid to inspect.

**Revisit if:** a phase needs concurrent attempts, or a launcher must provide a gateway.

## Confirmation

- **Mode:** lint/CI
- **Signal:** a ferryman test per outcome (`landed`, `held`, `floor`, `conflict`, `cancelled`, `residue`), a second-call test for `request-consumed`, a `result-fact-refused` test, a kill-during-verb test that calls the verb or `status` again and never respawns (D5), a test that an unlisted request kind parks `unknown-request-kind` (D7), and a trusted-set test that changes the launcher.
- **Owner:** eugenelim

## Alternatives considered

- **Amend ADR-0156 for a launcher-provided gateway:** it reopens an Accepted record, and no phase needs it.
- **`ferryman` schedules the tasks itself:** it would repeat the supervisor's attestation and floor-order checks.

## References

- `docs/architecture/unattended-delivery-runner/03-ferryman-runtime.md` (Blocking verbs)
- `docs/architecture/unattended-delivery-runner/05b-approval-integrity-and-trusted-configuration.md`
- `docs/architecture/unattended-delivery-runner/10c-review-decisions.md` (D36)
- `docs/adr/0156-work-loop-concurrency-needs-attested-read-coverage.md`
- `docs/adr/0160-concurrent-attempts-isolate-in-host-contained-plain-directories.md`

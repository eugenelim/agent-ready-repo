# ADR-0162: Sibling supervisors under one command contract, not a wider `work-supervisor`

- **Status:** Accepted
- **Date:** 2026-11-10
- **Areas:** orchestration, work-loop
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0115 (the proposal this records); ADR-0144 (the pinned supervisor, left unedited); ADR-0157 (parked gates, approval unchanged); ADR-0158 (code-review round cap, which excludes pre-approval review)

## Context

Spec and discovery work before execution runs on prose procedure, so a lost context or a stalled review is recovered by hand. `work-supervisor.py` is pinned by ADR-0144: one changed byte voids in-flight runs, and the supervisor holds no pre-approval state by design. A session agent and an optional controller both need the same way to drive any supervisor.

## Decision

We will give each phase before execution its own supervisor script, a sibling of the pinned `work-supervisor.py`, and every sibling exposes one command contract.

- **D1:** Six commands, `start`, `next`, `report`, `status`, `park` and `gates`, take and return JSON.
- **D2:** Each sibling ships `supervisor-manifest.v1` listing its request kinds. The kinds listed equal the kinds it emits, and a controller refuses an unknown manifest or version.
- **D3:** `delegate-verb` is a request kind: a controller runs another supervisor's `park` or `start` command for the supervisor.
- **D4:** Every phase boundary is a gate or a committed status, so a restart re-derives state from the repository.
- **D5:** A sibling never writes an approval. Approval follows ADR-0157 until a later ADR changes it.
- **D6:** Pre-approval review rounds stop at `max_review_rounds` from the sibling's policy file. At the cap the supervisor parks a `consent` gate naming the open findings and issues no further round.
- **D7:** The core pack owns `supervisor-manifest.v1` and the shared request envelope. This is the architecture's default, and accepting this record confirms it.

## Consequences

**Positive:**
- A session agent and a controller treat every supervisor alike.
- The pinned script stays unedited.

**Negative:**
- Two more scripts to maintain.
- The round cap is new policy: ADR-0158 covers code review only.

**Revisit if:** a supervisor needs a command beyond the six, or the pin model of ADR-0144 changes.

## Confirmation

- **Mode:** lint/CI
- **Signal:** a pack test per supervisor compares manifest request kinds with emitted kinds, and a refusal test covers each verb.
- **Owner:** eugenelim

## Alternatives considered

- **Extend `work-supervisor.py` to own every phase:** it needs an edit to a pinned script, which voids runs.
- **An agent-only procedure:** it has no durable stop rule, and `unattended-loops.md` limits the pattern to mechanical completion criteria.
- **A persistent daemon with a run registry:** excluded by ADR-0062 and Charter Principle 3.

## References

- `docs/rfc/0115-mechanized-delivery.md`
- `docs/architecture/unattended-delivery-runner/05-supervisors-and-gates.md`

# ADR-0170: A generic `tracker-adapter.v1` seam reuses the pack adapters and keeps credentials out of `ferryman`

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** orchestration, security
- **Reversibility:** low
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0115 (the proposal this records); ADR-0077 (tracker authority); ADR-0062 (no listening port); ADR-0164 (the program that calls it); ADR-0168 (the write-back policy); ADR-0169 (approval from a tracker signal)

## Context

`ferryman` needs candidates, events, revisions and comments from a tracker. `AGENTS.md` names `credbroker` for credentials and declares no blessed outbound HTTP helper. The GitHub packs already hold fixed-host validation in `processor.py` and `intake_adapter.py`. `processor.py` is a class with no command line, so subprocess reuse alone cannot cover write-back. Linear and Jira follow GitHub, so the seam cannot assume GitHub.

## Decision

We will define one generic `tracker-adapter.v1` seam, and each tracker pack ships a shim that implements it.

- **D1:** The seam has eight commands: `capabilities`, `check`, `candidates`, `get`, `events`, `revisions`, `comments`, `apply`. It uses neutral words: `ref`, `tag`, `group`, and an actor of `{id, login, kind}`.
- **D2:** The first shim is `tracker_adapter.py` in `github-refresh`. It loads `processor.py` and `intake_adapter.py` by path and reaches GitHub through `gh` on a fixed host.
- **D3:** `ferryman` has no HTTP client and passes no credential. It calls a shim by a fixed argv allowlist and reads JSON.
- **D4:** A refusal is a non-zero exit with a refusal object.
- **D5:** The first adapter covers Issues, labels and milestones. GitHub Projects are deferred, because user-owned Projects reject fine-grained tokens.
- **D6:** The poller sets its interval to the larger of `poll_interval_s` and ceil(3600 x R / `max_requests_per_hour`), where R counts the requests in one tick.
- **D7:** Linear and Jira shims come later behind the same commands. That they fit the seam is a design claim and is untested.

## Consequences

**Positive:**
- `ferryman` holds no tracker credential and makes no HTTP call.
- Each pack keeps its own credential route.

**Negative:**
- The contract is versioned and implemented by shims in three packs, so it is hard to reverse.
- Rollout order: phase P4 ships the read-only commands (`candidates`, `events`, `revisions`) first.
- Each tracker needs a shim, and Linear and Jira lack event listing today.
- Several `gh` behaviours are unverified: token scopes, the `gh issue list` transport, and event retention.

**Revisit if:** a tracker cannot be served by eight commands, or a blessed outbound HTTP helper is declared.

## Confirmation

- **Mode:** lint/CI
- **Signal:** shim contract tests, argv allowlist tests, and a rate-budget test. These are designed, not yet run.
- **Owner:** eugenelim

## Alternatives considered

- **A `ferryman`-owned HTTP client:** it would hold or route credentials, and no blessed helper exists.
- **A GitHub-only seam:** Linear and Jira would need a second seam.
- **A `ferryman`-owned `gh` argv builder:** it would duplicate the packs' fixed-host validation.
- **An agent following `work-intake`:** it has no durable stop rule.
- **Each host implements tracking:** each host would duplicate the fixed-host checks.

## References

- `docs/rfc/0115-mechanized-delivery.md`
- `docs/architecture/unattended-delivery-runner/06-tracker-integration-and-authority.md`

# ADR-0180: Ferryman defers to the brief-level runner and reads the run grant from it

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** orchestration, work-loop
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0115 (the proposal this records); ADR-0159 (the brief-level runner, left unedited); RFC-0113 (the run grant at brief Ready); ADR-0166 (the frontier); ADR-0167 (worktree ownership and peer layout); ADR-0174 (the trusted configuration pin and allowlists); ADR-0177 D3 (a checkpoint write is never a push under a grant)

## Context

`ferryman` has its own frontier, and the brief-level runner already chooses which slice of a brief starts. A brief can also carry a run grant that narrows what an unattended run may do. Two authorities for order, limits or grant values would drift apart.

## Decision

We will let the brief-level runner decide slice order, let the supervisor's `lease` table set worker limits, and read grant values only from the runner.

- **D1:** When a brief exists, `ferryman` calls the runner's `next` only from a clean base checkout, and that answer decides which slice starts.
- **D2:** Every `next` answer carries `schema_version` 2, and `ferryman` requires it (D56).
- **D3:** v1 takes an explicit subject and does not use brief ordering.
- **D4:** In P6, `ferryman` creates slice worktrees on `brief/<brief-slug>/<spec-slug>` under ADR-0167, so the runner finds them by branch name.
- **D5:** Worker limits come from the supervisor's `lease` table (`heartbeat_seconds`, `retry_budget`, `stuck_after_seconds`), read through the supervisor's loader or `status`. `[limits]` in `ferryman.toml` is only a fallback.
- **D6:** Grant values come only from the runner's `next` or `status` at the base. A change mid-run parks the run, and the sources name no park code. A grant only narrows, and the grant file is not in the trusted configuration set.
- **D7:** On a `grant-refused` or `grant-spent` answer, `ferryman` starts, resumes, retries and dispatches nothing. A task already running may finish.
- **D8:** In a pool, the control plane supplies grant values in `launch.v1`. This is provisional. Pool runs otherwise refuse a brief that carries a grant.

Note, outside the D30 to D34 scope (D62): after a refused report, `ferryman` respawns once per refusal with the refusal text, up to the lesser of the lease `retry_budget` (2) and a valid grant's `retry_budget`.

## Consequences

**Positive:**
- One authority each for order, limits and grant values.
- ADR-0159 stays as written: `ferryman` is the controller that ADR-0159 D1 says acts on the runner's answer.

**Negative:**
- Brief ordering waits for P6 or for control-plane subjects.
- A pool clone cannot run the runner, so the pool path depends on the provisional `launch.v1` field.

**Revisit if:** the runner's `next` shape changes, or the pool grant path is walked as its own decision.

## Confirmation

- **Mode:** lint/CI
- **Signal:** a ferryman test per rule: `next` from a clean base only, the branch name of a created worktree, limits read from `lease`, a mid-run grant change parking the run, and a missing or wrong `schema_version` refusal, a pool refusing a brief that carries a grant, and a respawn count within the lesser budget.
- **Owner:** eugenelim

## Alternatives considered

- **`ferryman` derives brief order itself:** it duplicates the runner and can disagree with it.
- **A controller agent creates slice worktrees:** ADR-0167 makes `ferryman` the worktree owner.
- **Keep `[limits]` as a second authority:** two tables drift.
- **One record for repo config and the grant, with the grant file pinned:** the grant is per brief and only narrows.

## References

- `docs/architecture/unattended-delivery-runner/04-frontier-and-waves.md`
- `docs/architecture/unattended-delivery-runner/10c-review-decisions.md` (D31)
- `docs/architecture/unattended-delivery-runner/10d-folded-decisions-and-defaults.md` (D32, D33, D34, D62)
- `docs/rfc/0113-run-grant-at-brief-ready.md`
- `docs/adr/0159-brief-level-runner-chains-slices-from-committed-records.md`
- `packs/core/.apm/skills/work-loop/references/brief-runner.md` (stop starting on a refused or spent grant, retries)

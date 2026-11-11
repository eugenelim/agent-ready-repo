# ADR-0167: Run and slice worktrees use an ownership transaction and a peer layout, and v1 stays sequential

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** work-loop, orchestration
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0115 (the proposal this records); ADR-0005 (D7 narrowed in part for run and slice worktrees; mirror lines on ADR-0005 follow acceptance); ADR-0160 (supersedes ADR-0005 D7 for concurrent-attempt directories); ADR-0157 (parked gates); ADR-0164 (the program that would create them); ADR-0171 (peer-root confinement); ADR-0174 (branch deletion, D17)

## Context

RFC-0015's erratum measured that removing a containing worktree with `--force` silently deletes a nested worktree's whole directory, uncommitted work included. Parallel worktrees need ownership that is provable and removal that cannot lose work. ADR-0160 already narrows ADR-0005 D7 for concurrent-attempt directories only. This design is inert until P6, so it is easy to reverse.

## Decision

We will keep v1 sequential in one checkout and fix the rules any `ferryman`-owned worktree must follow.

- **D1:** v1 creates no worktree. Per-slice and parallel worktrees ship in P6, once D32 is confirmed and the preconditions in page 08 section 2 pass review. Those preconditions apply to any parallel admission.
- **D2:** One `update-ref --stdin` transaction creates the branch and an ownership marker together. Before reuse, `ferryman` checks that both refs point at the recorded start commit and that the branch reflog holds exactly the owner message.
- **D3:** Every doubt preserves the resources. `ferryman` never force-removes a worktree, never removes one it does not own, and never falls back to another directory.
- **D4:** Rollback verifies ownership, refuses a changed or dirty checkout, and deletes both refs in one transaction. A moved branch tip makes the delete fail, so the branch stays. Branch deletion follows ADR-0174 (D17).
- **D5:** Worktrees sit at `<repo-parent>/.ferryman-worktrees/<repo>/<leaf>` and are never nested. ADR-0171 owns the confinement of that root.
- **D6:** In a `ferryman`-owned worktree, `ferryman` runs every Git write, and a worker only edits files or returns a diff.

## Consequences

**Positive:**
- A crash leaves only the half-states "no refs" and "refs without a directory", and both are safe.
- The measured nested-removal data loss cannot occur.

**Negative:**
- Parallel runs wait for P6.
- A lost receipt costs the base ref, so `ferryman` preserves the worktree and asks.

**Revisit if:** a parallel-worktree admission is proposed.

## Confirmation

- **Mode:** lint/CI
- **Signal:** real-Git fixture tests, a dirty-worktree reap test, and contention and kill tests. These are designed, not yet run. A single run on 2026-11-07 showed Codex 0.164.0 under a `workspace-write` sandbox could not create a worktree. A later single run on 2026-11-10 (page 03b) found that every git write fails inside a linked worktree under that sandbox unless a narrow `--add-dir` grant is added, which is why D6 has ferryman run the git writes.
- **Owner:** eugenelim

## Alternatives considered

- **Parallel worktrees now:** ownership is not yet provable.
- **Nested worktrees:** the erratum measured silent data loss.
- **Force-remove on cleanup:** it can delete uncommitted work.

## References

- `docs/rfc/0115-mechanized-delivery.md`
- `docs/architecture/unattended-delivery-runner/08-worktree-and-concurrency.md`
- `docs/adr/0160-concurrent-attempts-isolate-in-host-contained-plain-directories.md`
- The mirror lines on ADR-0005 follow acceptance of this record.

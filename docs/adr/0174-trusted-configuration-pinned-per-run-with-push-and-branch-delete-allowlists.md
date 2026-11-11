# ADR-0174: Trusted configuration is pinned per run, with push and branch-delete allowlists

- **Status:** Proposed
- **Date:** 2026-11-10
- **Areas:** security, orchestration
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** RFC-0117 D6 (the pin and Git-state hash); page 10c D17 and the README invariant (the push and branch-delete allowlist, which RFC-0117 leaves to the follow-on); ADR-0168 (standing write-back policy); ADR-0173 (gate scribe, which the pin re-checks); ADR-0179 (run-concurrent, which supplies the pinned launcher); ADR-0183 (configuration provenance and consent)

## Context

A ticket or a worker must not be able to change who may approve a gate. The files that decide this sit in the repository and in the user's home. A worker can also edit Git state that the ferryman trusts: config, hooks and refs. The ferryman also needs rules for which refs it may push and which branches it may delete.

## Decision

We will pin the trusted configuration once per run in ferryman's memory, check Git control state around each attempt, and limit what ferryman pushes and deletes.

- **D1:** At run start ferryman holds one digest per file in memory for the configuration and policy files (including `agentbundle-layout.toml`), the user config and the profiles it names, the installed supervisor scripts, and the approval-fields contract copy. It also pins `work-loop/SKILL.md` and `references/light-mode.md` when the session route is used, and the launcher only when the policy is concurrent.
- **D2:** Ferryman refuses `trust-set-dirty` at start when a repository file differs from its `HEAD` content. It re-checks the pin when each attempt closes, before each scribe write and at each poll while a gate is parked. It refuses `trust-set-changed` for a change outside an attempt and `trust-set-changed-in-attempt` inside one. A change is a human-only commit and takes effect at the next run.
- **D3:** Before and after each attempt it hashes the common directory's `.git/config`, `config.worktree`, the hooks path in effect and the contents of that hooks directory, `.git/info/`, the common directory's ref list and the user Git config files. It refuses the handoff if any changed.
- **D4:** (D17) Ferryman deletes only an untouched branch it created, by compare-and-delete against its `refs/ferryman/branches/<name>` marker. `ferryman clean` deletes other `ferryman/*` branches only one at a time, after a confirmation that shows the unmerged commit count.
- **D5:** On one machine ferryman pushes only checkpoint refs under `refs/ferryman/`. It never pushes a branch and never merges.
- **D6:** The pin lives in memory only, so no recorded hash exists. RFC-0117 D6's "its recorded hash" is read this way. The pin catches a change made while ferryman runs. At restart it catches only repository files that differ from `HEAD`. It does not defend against a same-user worker that edits ferryman's own code, writes after the final check, or changes the user config across a crash. A separate OS user or a container is the stronger guard, a later opt-in profile mode.

## Consequences

**Positive:**
- A config edit mid-run parks the run instead of changing the approver set.
- Hook, config and ref changes made between the pre- and post-attempt hashes are caught before a handoff. A worker that writes after the final hash is not caught (accepted on page 13).
- Ferryman never deletes a branch without its marker unless a human confirms that one branch with its unmerged commit count shown.

**Negative:**
- The pin is not a security boundary against a same-user worker.
- Page 05b does not yet carry the Git-state hash. RFC-0117 says it will, and the architecture follow-on adds it as a guard step and a corpus shape.
- The Git-state list is narrower than github-pr spec G9a (system and XDG config, include targets, the worktree `.git` file, `commondir`, `objects/info/alternates`). This is an accepted risk, because the list matches RFC-0117 verbatim.
- Page 12 seam 6 lets ferryman push claim refs under `refs/ferryman/claims/<hash>` when no control plane exists. That conflicts with D5 and the README invariant, so seam 6 must drop single-machine claim pushes, or a later decision must admit them.
- The allowlist and deletion rules are drafted from the architecture pages and are untested.

**Revisit if:** the profile mode for a separate user or container is scheduled, or a worker is found to defeat the Git-state hash.

## Confirmation

- **Mode:** lint/CI
- **Signal:** the trusted-file corpus (eight shapes) is refused. A Git-state corpus (config, `config.worktree`, hooks path, hooks contents, `info/`, ref list, user Git config) is refused before handoff. An argv allowlist test finds no push outside `refs/ferryman/` and no unmarked branch deletion.
- **Owner:** eugenelim

## Alternatives considered

- **Run workers as another OS user or in a container now:** it is the stronger guard, and it conflicts with the install-nothing posture. It stays a later opt-in.
- **Marker-only rollback, so no branch is ever deleted:** it leaves stale branches for a human to clear.
- **Leave the trust files unpinned:** a ticket could steer a worker into editing who may approve.

## References

- `docs/rfc/0117-approval-and-the-trust-model-for-unattended-delivery.md`
- `docs/architecture/unattended-delivery-runner/05b-approval-integrity-and-trusted-configuration.md`
- `docs/architecture/unattended-delivery-runner/10c-review-decisions.md`
- Push and branch-delete allowlist text drafted from `docs/architecture/unattended-delivery-runner/03c-run-chain-locks-and-process-boundary.md`, `08-worktree-and-concurrency.md` and `12-pool-state-integrity-and-signals.md`.

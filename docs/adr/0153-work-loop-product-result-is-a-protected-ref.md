# ADR-0153: The work-loop product result is a protected Git ref that only the supervisor advances by compare-and-swap

- **Status:** Accepted
- **Date:** 2026-10-30
- **Areas:** work-loop, orchestration
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** ADR-0144 D9,D11
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0144 (D9 kept the worktree as the product result boundary until this record; D11 keeps worker attempts untrusted, and this record adds one named-human decision to the ones it lists); ADR-0005 and ADR-0061 D5 (parallel writes stay sequential; a later parallelism record owns three-tree apply); spec `canonical-result-integration`

## Decision summary

- **Decision:** A full-mode run's product result is a protected ref under `refs/agentbundle/delivery/`, which only the supervisor moves, together with `HEAD`, in one compare-and-swap per step; the delivery subject reads that ref, and the execution-root worktree and `HEAD` are its projection.
- **Because:** a ref only the supervisor writes cannot be changed by ambient drift, a lost race, a stray commit, or a worker's naive Git write without a refusal or an owner decision, and a crash leaves it naming either the old or the new step.
- **Applies to:** full-mode `code` runs of `work-loop`; not light mode or parallel results.
- **Tradeoff accepted:** any history the supervisor did not make, including a plain rebase, waits for an owner decision; and switching the subject provider changes every acceptance fingerprint, so a run regenerated across the switch re-runs its gates and reviews once.
- **Revisit if:** a supported host's ref backend cannot update two refs in one transaction, or parallel admission needs results that do not start from the current tip.

## Context

ADR-0144 D9 kept the mutable execution-root worktree, and the `HEAD` commits
the supervisor builds from it, as the product result. The supervisor already
moves `HEAD` by compare-and-swap, but `HEAD` is an ordinary branch: a reset, a
commit made outside the supervisor, or a rebase changes what acceptance reads,
and nothing records which tree a result was integrated against.

The acceptance-centered work-loop brief makes the move a later slice so the
new procedure owner was proven against the legacy boundary first. That proof
has shipped.

## Decision

- **D1:** Each run admission names its own product ref, `refs/agentbundle/delivery/<run-id>/<token>/product`, with a fresh token recorded on the approval commit, so two runs never share one. Every supervisor step moves `HEAD` and the product ref to the same commit in one compare-and-swap transaction.
- **D2:** A product result integrates only while the product ref still names the commit its request was issued from. Otherwise it refuses as a conflict, moves nothing, and keeps the worker's files until the ref is restored. No three-tree apply is performed.
- **D3:** The run store records the product ref's name and its current value, and the pending commit while a step is committed. The ref is trusted only while it equals one of them; any other state, including a missing, symbolic, or rolled-back ref, refuses until the ref is restored. Recovery completes a step that moved one ref, and moves a lagging `HEAD` forward only through commits the supervisor made, never overwriting a working-tree file that matches neither version.
- **D4:** History the supervisor did not make — a reset onto other work, a rebase, an amend, or a commit on top — enters the product ref only through one recorded `reanchor` step that a named owner authorizes for the exact `HEAD` commit, after seeing which product paths it changes. Adoption never admits a change to committed `delivery/` records. Nothing re-anchors automatically. This adds a history-adoption decision to the named-human decisions ADR-0144 D11 lists; like them, its authority reference is recorded, not cryptographically enforced.
- **D5:** A worker attempt during which this run's product ref leaves its recorded or pending value has its result refused as a Git control-state change. Another run's product ref never counts against it.
- **D6:** `supervisor-policy.json`'s `result_authority` selects the delivery subject's provider: `legacy-worktree` reads `HEAD`, and `protected-product-ref` reads the product ref. Both write the product ref identically. The value is pinned with the policy at `start`, so it changes for a run in flight only through `regenerate`, and setting it back is the reversal. `protected-product-ref` ships only after a release with `legacy-worktree`.

## Consequences

**Positive:**
- Acceptance reads a tree that only admitted results reach.
- A crash, a lost race, or a partial ref update converges without losing a step.
- Slice 7's parallel admission inherits a single integration point.

**Negative:**
- Every step's commit path changes, so the crash corpus must cover the new kill points.
- A rebase or controller commit mid-run waits for an owner decision.
- A run regenerated across the switch re-runs its gates and reviews once.
- A deliberate worker running as the same operating-system user can still forge the run store's made-commit record, which stays the trust root.
- Product refs accumulate until a later closeout prunes them.

**Revisit if:** a supported host's ref backend cannot update two refs in one transaction, or parallel admission needs results that do not start from the current tip.

## Confirmation

- **Mode:** architecture fitness test
- **Signal:** `packs/core/tests/skills/work-loop/test_supervisor_crash_corpus.py` kills the supervisor at every kill point under both `result_authority` values and checks the product ref and `HEAD` converge to the uninterrupted run; the attempt suite refuses a worker write to the run's product ref and admits a sibling run's; a rebase and an amend wait for an owner decision; a run regenerated across each `result_authority` value reaches terminal with the uninterrupted run's product.
- **Owner:** eugenelim

## Alternatives considered

- **A separate integration-commit chain beside the supervisor's commits.** Rejected: it needs its own parentage and recovery path for no outcome the single chain lacks.
- **Three-tree apply now.** Rejected: sequential dispatch never needs it, and it raises the Git floor from 2.32 to 2.38.
- **Re-anchor a rebase automatically when every step trailer survives it.** Rejected: a rewrite can keep the trailers while changing content.
- **A per-worktree `refs/worktree/` product ref.** Rejected: `git gc` run in another worktree pruned its commits in a probe.
- **Switch in one release with no shadow.** Rejected: the brief requires shadow parity before result authority moves.
- **Keep the provider lineage stable across the switch.** Rejected: the evidence record would no longer show which provider produced its subject.

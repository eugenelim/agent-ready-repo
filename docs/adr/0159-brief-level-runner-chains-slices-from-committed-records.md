# ADR-0159: Brief-level runner chains ready slices from committed records; approvals and merge stay human

- **Status:** Accepted
- **Date:** 2026-11-05
- **Areas:** work-loop, orchestration, security
- **Reversibility:** high
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none
- **Related:** ADR-0144 (the supervisor owns procedure, including leases — D1); ADR-0157 (parked gates and the `gates` verb, whose "Revisit if" names a brief-level runner listing gates from several worktrees); ADR-0156 (concurrency inside one run, which this record leaves unchanged); RFC-0099 (§7 keeps every spec-plan and human approval gate)

## Decision summary

- **Decision:** A read-only brief-level runner, shipped in the `work-loop` skill, derives each slice's state from committed records and names the next ready slice from the brief's Spec map and each spec's `Depends on:` header. The controller starts that slice in its own worktree when an earlier slice reaches merge-ready or merged. The runner lists parked gates across slice worktrees with the shipped `gates` verb, passes one standing-orders file to every dispatch and resume, runs a pilot slice first, and applies a failure taxonomy whose heartbeat, stuck-after runtime and retry budget are supervisor lease policy.
- **Because:** after each slice a person opens a new session to start the next one, and nothing lists the gates waiting across slices; both can end without removing or weakening a human gate.
- **Applies to:** full-mode work across the slices of one delivery brief. Not light mode, not one run's internal scheduling, and not what may proceed without a human.
- **Tradeoff accepted:** the skill gains one read-only script, one policy table, and one human-written file kind; slices in flight each hold a worktree.
- **Revisit if:** a run grant changes which actions may proceed without a human, or slices of one brief must share one worktree.

## Context

A full-mode run ends at a slice's stop: merge-ready or merged. Starting the next slice today needs a person to open a new session and name it, so a brief idles between slices even when the next slice is independent and ready.

Five constraints hold:

- **The gates stay.** RFC-0099 §7 keeps every spec-plan and human approval gate, and `AGENTS.md` forbids cutting a required human approval. ADR-0157 D4: no verb, flag, default, or record turns a parked gate into an approval.
- **The supervisor owns procedure.** ADR-0144 D1 assigns ordering, dispatch, leases and recovery to the supervisor. Leases are planned in the execution-supervisor architecture and not yet built.
- **Gate listings are per checkout.** ADR-0157 stores park records under each worktree's own Git directory, so `gates` lists one worktree only. Its "Revisit if" names this runner.
- **Readiness already has an owner.** `dispatch.py` and its header-readiness module evaluate a spec's `Status:` and `Depends on:` headers. A second reading would drift.
- **One run is sequential.** ADR-0156 admits concurrency inside a run only on attested reads. Separate slices are separate runs in separate worktrees.

## Decision

We will ship a read-only brief-level runner that derives slice state from committed records and names the next ready slice, while every approval, amendment and merge stays with a named human.

- **D1:** The runner is a read-only script in the `work-loop` skill. It writes no file, record, commit or branch, and holds no state between calls. The controller acts on its answer under the existing per-slice work-loop procedure.
- **D2:** The runner reads one base: the freshly fetched default-branch commit, checked out clean in the main worktree. Slice order comes from the brief's Spec map row order and, for an `Approved` spec, its `Depends on:` header as `dispatch.py` evaluates it; the runner reads no dependency header itself. A row with no spec, or a `Draft` spec, depends on every earlier row. The next ready slice is the first row in Spec map order whose dependencies are satisfied and which has not started. A slice's stop is merge-ready (its supervisor run reports ready from committed records) or merged (its spec is `Shipped` at the base).
- **D3:** Each started slice gets its own linked worktree, on a branch named for the brief and spec, created from the freshly fetched default branch. The runner finds slice worktrees only among this repository's own worktrees. Each slice keeps its own sequential run; ADR-0156 is unchanged. A lease-policy cap bounds how many slices are in flight at once.
- **D4:** The runner lists parked gates across slices by running the shipped `gates` verb in each slice worktree and joining the entries. It adds only fields it derives itself: the worktree path and the spec slug. A parked slice blocks only itself and its dependents; the controller keeps working every other ready slice (ADR-0157 D7). A slice whose gate is stale, invalid or unlistable is blocked, never resumed.
- **D5:** Brief status is derived on every call from the Spec map, each spec's headers, each slice worktree's committed supervisor records, and the `gates` listing. It is never written to a file, the brief, or a commit.
- **D6:** Standing orders are one human-written, committed file per brief: numbered lines, one constraint each. The runner reads it from the committed tree, refuses a malformed file, and gives the controller its exact bytes and digest. The controller passes those bytes, as quoted data, to every implementer and reviewer dispatch, spawned session and resume. A standing order constrains work; it cannot approve, merge, grant authority, or relax a gate, review, or security control. A restated instruction becomes a new line.
- **D7:** When no Spec map row has yet reached its stop, the pilot is the row already started, or the first ready row when none has started. The runner names no other slice until the pilot reaches merge-ready or merged, including while the pilot waits at a gate.
- **D8:** Heartbeat interval, stuck-after runtime per agent kind, and the retry budget are supervisor lease policy in `supervisor-policy.json`. The heartbeat uses the host's own wake facility, judges progress only by side effects (branch heads, committed records, the gate listing), and reports only when state changed. A worker past its stuck-after runtime with no new side effect is replaced, which counts as a retry.
- **D9:** A failed dispatch is classified: `cap-hit` splits the task by an in-envelope replan, `network` retries it unchanged, `tool-error` retries it on another model, and an unknown class is surfaced to a human. After two retries on one task, the controller abandons it and replans around it; a replan that would cross a protected boundary routes to its owner as an amendment. The controller reports every failed implementation dispatch to the supervisor as a failed gate before classifying it, so each such retry is a committed record; other dispatch kinds retry within the session's budget and then go to a human, and an external effect is never retried this way; the runner reads the count from the supervisor, and every reported implementation failure still counts toward the existing run-wide retry cap, which no replan resets.
- **D10:** Every `spec-approved` and `plan-approved`, every amendment reapproval, every merge, and every irreversible operation stays with a named human. No runner output, standing order, policy value, timeout or default approves, merges, or infers an approval. A test pins RFC-0099 §7 and the `AGENTS.md` rule so a change that weakens either fails.

## Decision drivers

- No human approval is removed, merged, or inferred.
- State is derived from committed records, so a lost session loses nothing.
- Readiness, gate listing and procedure keep their existing owners.
- The sequential floor stays the default.

## Consequences

**Positive:**
- The next ready slice starts without a person opening a session, and independent slices keep moving while one waits at a gate.
- The human sees every waiting gate across a brief in one listing and can clear them in one sitting.
- Directives survive resumes because every dispatch carries the same standing-orders bytes.

**Negative:**
- Each slice in flight holds a worktree, and the runner's gate listing costs one `gates` call per worktree.
- A brief needs a Spec map, and a slice needs a correct `Depends on:` header, or the runner orders it wrongly.
- Failure classes are the controller's judgment of a dispatch failure; a wrong class costs a retry, bounded by the budget.
- The pilot rule delays fan-out on a brief's first slice.

**Revisit if:** a run grant changes which actions may proceed without a human, or slices of one brief must share one worktree.

## Confirmation

- **Mode:** lint/CI
- **Signal:** core pack tests prove the runner writes nothing, derives the next slice from the Spec map and `Depends on:` headers, holds other slices behind an unfinished pilot, joins per-worktree `gates` entries without controller text, refuses malformed standing orders, maps each failure class to its action with a two-retry budget, and exposes no path that approves or merges. A test pins the RFC-0099 §7 heading and the `AGENTS.md` approval rule.
- **Owner:** core pack maintainers

## Alternatives considered

- **Keep a person starting each slice:** meets every driver but leaves the brief idle between slices, which is the problem this record solves.
- **A runner state file listing slices and their states:** rejected against "state is derived from committed records". A hand-written or controller-written table drifts from the records it summarizes.
- **A new supervisor verb that owns the brief:** rejected against "readiness, gate listing and procedure keep their existing owners". One supervisor run is scoped to one spec; a brief verb would mix several runs' stores.
- **One shared gates store for all worktrees:** rejected against the same driver. It changes ADR-0157's per-checkout store and its threat model for a listing that joining existing `gates` output already gives.
- **Run every slice in one worktree:** rejected because a parked gate goes `stale` when the checkout switches branch (ADR-0157 D3), so one worktree cannot keep a parked slice approvable while another slice moves.

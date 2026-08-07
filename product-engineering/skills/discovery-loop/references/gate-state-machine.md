# Reference: the gate state machine (verdicts, cascade, persistence, resume)

Depth for [`SKILL.md`](../SKILL.md) — how the loop pauses for a human, backs out
of a bad call, and resumes. **No engine:** every transition is a status edit on
the typed sidecar plus a recorded verdict row.

## Per-verdict transitions

A consent gate is where the human exercises the irreducible value/accountability
acts; the verdict is a **typed enum**, each row its own transition. The binary
"reject → cascade-invalidate" is just **one row** — every row that changes the
blackboard **reuses the one cascade mechanism** (walk traceability out-edges →
mark `stale` → re-run only the affected lenses), always gated by the two integrity
guards.

| Verdict | What the human means | Transition (status edits + a recorded verdict) |
| --- | --- | --- |
| **approve** | proceed as recommended | promote the gate's slots to `ratified`; advance |
| **approve-with-constraint** | OK, but a scope cut / condition that **must be honoured before proceeding, not jumped past** | record the constraint into the **Scope Boundary**; re-run only the lenses it touches; **do not advance** until the reduced surface re-converges |
| **redirect / steer** | not this — go *this* way | record the new direction as an `intent` steer; **surface the impact** (which slots it obsoletes); on confirm, cascade-invalidate that scoped set and re-enter convergence with the steer as input |
| **explore-alternatives** | show me other paths first | route **back to the divergence phase** — `explore-options` regenerates candidate shapes around the steer, then converge the chosen one |
| **abandon** | kill it | record the kill + rationale (the `de-risk-intent` kill-condition shape); cascade-invalidate the whole subtree to `abandoned`; close the node |
| **park / defer** | not now | set the node `parked` in the sub-idea index; resumable later; advance siblings |
| **extend / override** | keep going past a bound | grant more `round_cap` / `cost_budget` (or lift a structural bound) and resume — the row used at a **paused-at-bound** gate; records the new bound + rationale |

## The two integrity guards (bind every row)

1. **Impact-before-blast.** Any verdict that would invalidate or change slots
   **first shows the affected set (the blast radius) and waits for confirmation**
   before cascading — the same surface-don't-auto-cascade posture as the
   high-fan-out circuit-breaker. The human steers *seeing* the consequences.
2. **No jumping ahead.** The loop **does not advance past a gate without an
   explicit typed verdict**; a scope limitation is honoured before proceeding
   (never silently overrun); and the verdict + its type + rationale are written to
   the **append-only, attested** decision log. Abandonment and redirect are
   first-class recorded outcomes, not dead ends.

## Rejection/recovery with cascade-invalidation

A rejection (a human "no" at a consent gate, or a lens invalidating a prior slot)
runs, in the controller's own context:

1. emit `reason → correction`; re-enter that gate's phase;
2. **cascade-invalidate downstream blackboard slots by walking the traceability
   out-edges** from the rejected node — mark each `stale`, drop its edges from the
   active matrix;
3. re-run **only the affected lenses** on the reduced surface.

The edge set *scopes the blast radius* — the whole reason the matrix is typed. The
prototype ran this for a fulfillment over-scope: the human rejected
`cap.external-fulfillment` at G1.5, the walk marked `screen:fulfillment` +
`service:fulfillment` stale and dropped their edges, and only the UX lens re-ran.
This is the reject→revise checkpointer shape, realized as a state edit, not a
framework call.

**The answer-each-other ripple.** Lenses bounce off each other **through the
open-questions queue and the blackboard, never by chat**. The reconcile lens runs
the discovery reviewer roster over the journey/blueprint mid-loop; coordination is
queue-status + blackboard edits with **zero agent-to-agent negotiation** — the
MAST guardrail held by topology.

## Persistence — two tiers

The `park` verdict is only useful if a deferred idea is remembered:

- **Tier 1 — the working store (`_state/`), durable while active.** The whole
  plan-tree, including `parked` nodes in the sub-idea index, is **durably
  checkpointed at each gate/round** to the harness's `_state/` store. A run pauses
  (`awaiting-human`) and **resumes across sessions**.
- **Tier 2 — committed repo artifacts, durable beyond the run.** On run-end /
  teardown the loop **promotes the durable record into committed artifacts**: the
  **decision log** records every `park`/`abandon` + rationale (append-only); the
  **backlog bridge** carries `parked` sub-ideas as **first-class entries**; and the
  **intent tree** persists as committed discovery docs.

A parked idea is **resumable** (re-instantiate its node from the committed entry),
and `decision-archaeology`'s **revival check** can later flag a parked/abandoned
idea whose original deferral rationale no longer holds — "remembering" is
*revisitable*, not a passive archive.

## Resume design (a load + a status read, no runtime)

1. **Entry (two ways in).** Either `discovery-lead` is invoked **on an existing
   initiative id** and loads it directly; **or**, on a *fresh start* request, the
   skill's **first action is to scan the discovery root for in-progress / parked
   discoveries and offer to resume them before scaffolding** a new plan-tree.
2. **State reconstruction (two sources).** If Tier-1 `_state/` is present, load it
   directly (the live plan-tree + slot statuses + the `meta` block). If it was torn
   down, **re-hydrate from the committed Tier-2 record** (the intent tree +
   decision log + the backlog's parked entry carry the node, its status, its
   history, and its place in the tree via stable ids).
3. **Re-entry point.** The per-node status says where to resume: `awaiting-human` →
   read the verdict from the log and apply its transition; `parked` → re-activate
   and re-enter its phase; `stalled-at-cap`/`paused-at-bound` → resume after the
   human adjusts budget/scope; `converging` → continue where it stopped.
4. **Integrity on resume.** Check `schema_version` (migrate/flag, never silently
   mis-read); re-run the connectedness lint before continuing; re-attest any human
   verdict through the harness-attested channel (a *resumed* `ratified-by: human`
   row is no more forgeable than a fresh one); and be **idempotent** — re-applying
   a logged verdict/cascade is a no-op.

**Cross-teardown faithfulness (the AC choice).** For a faithful resume, Tier 2
carries a **per-gate snapshot of `meta` + per-node status** (cheap: written into
the option card / backlog entry at each gate commit) — the **recommended
default**, since the bounds and "resume where it stopped" depend on the counters
surviving. **Absent that snapshot**, cross-teardown resume is **gate-granularity
only** — it re-enters at the last committed gate with the round/cost counters
**reset**, not mid-convergence.

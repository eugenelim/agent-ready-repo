# ADR-0104: Light mode's review stops on divergence, not on a round budget

- **Status:** Proposed <!-- Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-09-04
- **Decision-makers:** eugenelim
- **Supersedes:** ADR-0014 in part — its light-mode review-bound clause only
- **Related:** [ADR-0014](0014-rigor-scales-with-risk-work-loop-modes.md) (light/full modes; its trigger set stands), [ADR-0088](0088-risk-triggers-have-a-single-documented-home.md) (the risk-trigger block's single home — unaffected), [RFC-0025](../rfc/0025-work-loop-light-mode-and-risk-based-escalation.md)

## Decision summary

- **Decision:** light mode's `adversarial-reviewer` rounds run to clean, stopping on a divergence checkpoint rather than a round count; the exit is the requester.
- **Because:** round count measures nothing about the cost the bound exists to contain, and the escalation exit cost more to obey than to rationalise around.
- **Applies to:** light mode's post-GATES review only. Full mode's iteration cap and the risk-trigger set are unchanged.
- **Tradeoff accepted:** light mode now has no mechanical stop — the checkpoint is a judgement, and ADR-0014's named compensating control is replaced by a Surface.
- **Revisit if:** light-mode runs are observed running long without the checkpoint firing, or the repair-introduced signal becomes calibratable.

## Context

ADR-0014 gave light mode a **single bounded** `adversarial-reviewer` pass: a
surviving Blocker earned exactly **one** re-review of the fix, and a Blocker that
survived that **escalated to full mode**. Two defects showed up in practice, both
in one session that ran four review rounds under the rule.

**"Surviving" invited reinterpretation.** When round 2 returned *new* Blockers,
they were classified as new findings on new content rather than survivals, and
the loop continued. The rule drew no such distinction. The adjective invited the
argument.

**The exit was disproportionate, so it trained evasion.** Escalating a one-file
prose change to full mode means `new-spec`, a spec and plan, engine and cohort
initialisation, and two human approval gates. The cost of obeying exceeded the
cost of rationalising, so the rule was rationalised around rather than followed.

Round count was also measuring the wrong quantity. Four rounds on a small file is
trivially cheap; four rounds on a large diff is the real problem, and `work-loop`
already sizes that in reviewable behavior and test lines.

A third problem was structural. Light mode allowed two rounds while full mode
allows five. The mode handling simpler, cheaper work carried the stricter bound.

Convergence to clean already works. Rounds are not the risk. The only thing worth
detecting is a loop that is *not* converging — the failure class that appears as
the machinery takes on more complex changes.

## Decision

**Light mode's `adversarial-reviewer` rounds run to clean, and stop on a
divergence signal rather than a round count.**

- **The count is a checkpoint, not a budget.** The trend is read at the third
  round and every second round after. Three is where there are first enough
  points to read a direction; the extend-by-two is a sampling interval, not an
  allowance.
- **The checkpoint defaults to stopping.** The loop continues only while the
  trend affirmatively says findings are getting fewer and smaller.
- **The exit is the requester, never full mode.** A diverging loop stops
  repairing, asks whether the reviewed construct should exist rather than whether
  it is correct, prefers deletion or a move to the module or team that owns it
  over another repair, and Surfaces that choice. Full mode remains available as
  the requester's choice.
- **The repair-introduced signal is advisory.** How many findings the loop's own
  repairs produced informs the read and never decides it.
- **Risk-trigger escalation is untouched.** It lives in the classification rules
  and still fires independently, so a trigger discovered at any point routes the
  work to full mode without anyone's permission.

ADR-0014 named the light-to-full escalation as what compensated for light mode's
dropped `quality-engineer` floor. That route is gone, so a maintainability
concern needing that lens is Surfaced instead: absent a risk trigger, only the
requester can move the work to full mode.

This decision covers light mode's post-GATES review only. It changes neither the
risk-trigger set, nor mode selection, nor full mode's iteration cap.

## Decision drivers

- **The bound must track the cost it exists to contain.** Round count does not;
  diff size does.
- **The exit must cost less than evading it.** A rule whose only exit is
  disproportionate gets argued around rather than followed.
- **A signal that gates a decision must be calibratable.** One that cannot be
  ships advisory, or not at all.
- **Risk-trigger escalation must stay independent.** Nothing here may weaken the
  route that exists for unfamiliar, security, or structural work.

## Consequences

**Positive:**

- A converging loop finishes instead of stopping mid-convergence or paying
  full-mode cost to continue.
- The exit is proportionate, so the rule is cheaper to obey than to argue with.
- The inversion is gone: light mode no longer carries a stricter bound than full
  mode.
- Divergence — the failure that actually matters — is now what the rule detects,
  rather than round count, which correlates with nothing.

**Negative:**

- **Light mode has no mechanical stop.** The checkpoint is a judgement the agent
  makes. Full mode's iteration cap and its stasis detection are engine-side and
  unreachable from light mode, which holds no cohort state, so nothing bounds a
  light-mode run when the trend read is wrong except the requester.
- **ADR-0014's named compensating control is replaced, not preserved.** A
  surviving Blocker no longer escalates into the full `quality-engineer` lens; a
  maintainability concern reaches it only if Surfaced and the requester moves the
  work. This is a weaker mechanism than an automatic escalation.
- The rule is longer to state than "one pass, one re-review", and a checkpoint
  read is more cognitive surface than a counter.

**Revisit if:** light-mode runs are observed running long without the checkpoint
firing, or a calibration for the repair-introduced signal becomes available that
would let it gate rather than advise.

## Confirmation

- **Mode:** lint/CI
- **Signal:** a parametrized, whitespace-normalized absence sweep fails when any
  phrasing of the retired bound reappears on the pack's shipped surfaces, and
  asserts its corpus paths exist so a mistyped surface fails loudly rather than
  sweeping nothing. **Explicit residual:** the checkpoint's judgement half — the
  cadence, the trend read, and the requester exit — is prose an agent follows and
  is not mechanically checkable. Only its absence-of-the-old-rule half is.
- **Owner:** eugenelim

## Alternatives considered

- **Keep ADR-0014's rule.** Rejected against the second driver: it was observed
  being rationalised around, and the wording that permitted this is the wording
  under review.
- **A per-finding classifier**, branching on *same finding* / *repair-introduced*
  / *on newly added scope*. Rejected against the third driver: the classification
  is made by the agent that just made the repair, and the "newly added scope"
  branch grants a fresh full pass — precisely the evasion the rule exists to
  stop. It is pre-broken.
- **A hard round budget** — three at most, then stop. Rejected against the first
  driver: round count tracks nothing about cost, and a fixed cap kills converging
  loops that legitimately need more rounds.
- **Gate on the repair-introduced signal.** Tried and rejected against the third
  driver. Conjoining "not ones your own repairs created" into the trend read
  makes a single repair-induced finding trip the checkpoint; measurement during
  this change's own review found 25% of findings repair-induced at a healthy,
  converging round three, which would have stopped the loop. It ships advisory,
  the same treatment `shaping-reviewer` gives emphasis density.
- **Soften full mode's caps first.** Deferred, not rejected. Full mode already
  computes a divergence signal and then ignores it in favour of a counter, but
  changing that touches `_loop_guards.py`, `loop-engine.py`, `assets/state.json`,
  and the test that polices their single-sourcing — a state-schema and
  public-interface change needing its own spec. This decision establishes the
  rule that change would later implement mechanically.

## References

- Implementation: PR #1231, `packs/core/.apm/skills/work-loop/references/light-mode.md`.
- [ADR-0014](0014-rigor-scales-with-risk-work-loop-modes.md) — the decision this replaces in part; its Consequences name the dropped `quality-engineer` floor as the most material accepted loss.
- [RFC-0025](../rfc/0025-work-loop-light-mode-and-risk-based-escalation.md) — the proposal ADR-0014 recorded.

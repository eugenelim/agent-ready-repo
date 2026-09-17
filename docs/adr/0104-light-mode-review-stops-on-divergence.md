# ADR-0104: A review loop stops on divergence, not on a round budget — and a signal that cannot be calibrated advises rather than gates

- **Status:** Accepted <!-- Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-NNNN -->
- **Date:** 2026-09-04
- **Decision-makers:** eugenelim
- **Supersedes:** ADR-0014 in part — its light-mode review-bound clause only
- **Related:** [ADR-0014](0014-rigor-scales-with-risk-work-loop-modes.md) (light/full modes; its trigger set stands), [ADR-0088](0088-risk-triggers-have-a-single-documented-home.md) (the risk-trigger block's single home — unaffected), [RFC-0025](../rfc/0025-work-loop-light-mode-and-risk-based-escalation.md)

## Decision summary

- **Decision:** light mode's `adversarial-reviewer` rounds run to clean, stopping on a divergence checkpoint rather than a round count; the exit is the requester. Full mode's recurrence signal is made visible and its unreachable stasis stop is retired. Neither mode gates on a finding-derived signal.
- **Because:** round count measures nothing about the cost the bound exists to contain; the escalation exit cost more to obey than to rationalise around; and no finding-derived signal here has ever been calibrated, while the two that were proposed are measurably unable to separate a converging loop from a diverging one.
- **Applies to:** light mode's post-GATES review, and full mode's stasis route and recurrence key. Full mode's retry cap, mode selection, and the risk-trigger set are unchanged.
- **Tradeoff accepted:** light mode has no mechanical stop, and full mode now has one fewer. Full mode's remaining mechanical bound is its retry cap; light mode's is the requester.
- **Revisit if:** light-mode runs are observed running long without the checkpoint firing, or a committed record of per-round recurrence accumulates far enough to calibrate a threshold that this decision could not.

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

**Full mode's recurrence signal is visible, and its stasis stop is retired.**

- **The recurrence key drops position.** A finding's identity for
  cross-round comparison is its cited location and title with the leading
  ordinal and any severity tag removed. The within-round fingerprint, which
  carries the line, is unchanged: one key cannot serve both jobs.
- **The stasis stop route is retired, not repaired.** Full mode routed
  `matches_previous_round` to "do not start another round". That route is
  removed rather than re-keyed.
- **The signal advises.** Recurrence is reported and Surfaced. Nothing in the
  loop branches on it.
- **The retry cap is untouched.** It remains full mode's mechanical bound and
  the only thing that stops an unattended run.

ADR-0014 named the light-to-full escalation as what compensated for light mode's
dropped `quality-engineer` floor. That route is gone, so a maintainability
concern needing that lens is Surfaced instead: absent a risk trigger, only the
requester can move the work to full mode.

This decision changes neither the risk-trigger set, nor mode selection, nor
full mode's retry cap.

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
- Full mode stops carrying a control that cannot fire. A stop whose trigger
  condition normal editing destroys reads as protection while providing none,
  and it is the kind of control a reader trusts precisely because it is there.
- The recurrence signal becomes readable for the first time, so a stuck loop is
  visible to whoever is watching even though nothing acts on it.

**Negative:**

- **Light mode has no mechanical stop.** The checkpoint is a judgement the agent
  makes. Full mode's retry cap is engine-side and unreachable from light mode,
  which holds no cohort state, so nothing bounds a light-mode run when the trend
  read is wrong except the requester.
- **Full mode has one fewer.** Retiring the stasis route leaves the retry cap as
  its only mechanical bound. An unattended full-mode run that stops converging
  therefore burns rounds to the cap rather than halting earlier. The measured
  cost of that is bounded: in the recorded corpus the cap fired twice, and on
  both occasions a human chose to continue past it, so an earlier stop would
  have changed when the question was asked rather than the answer.
- **The never-gate boundary is prose.** Nothing mechanical prevents a later
  change from wiring a stop to the recurrence signal. The Confirmation section
  states why an absence sweep cannot serve here.
- **ADR-0014's named compensating control is replaced, not preserved.** A
  surviving Blocker no longer escalates into the full `quality-engineer` lens; a
  maintainability concern reaches it only if Surfaced and the requester moves the
  work. This is a weaker mechanism than an automatic escalation.
- The rule is longer to state than "one pass, one re-review", and a checkpoint
  read is more cognitive surface than a counter.

**Revisit if:** light-mode runs are observed running long without the checkpoint
firing, or a committed record of per-round recurrence accumulates far enough to
calibrate a threshold that this decision could not. The second trigger needs a
sink that does not exist: live cohort state is per-run and untracked, so every
observation of the signal this decision makes visible is presently discarded.

## Confirmation

- **Mode:** lint/CI
- **Signal:** a parametrized, whitespace-normalized absence sweep fails when any
  phrasing of the retired bound reappears on the pack's shipped surfaces, and
  asserts its corpus paths exist so a mistyped surface fails loudly rather than
  sweeping nothing. **Explicit residual:** the checkpoint's judgement half — the
  cadence, the trend read, and the requester exit — is prose an agent follows and
  is not mechanically checkable. Only its absence-of-the-old-rule half is.

  For full mode: the retired stasis route is confirmed by the absence of its
  disposition from the shipped surfaces that carried it, and the position-free
  key by a case that reds when a finding surviving a line shift, a renumbering,
  or a severity change is treated as new. **Explicit residual:** that no future
  change wires a stop to the recurrence signal is not mechanically checkable. An
  absence sweep for the signal's name near stop vocabulary cannot serve, because
  the compliant reference document must itself state that the signal never stops
  a loop. This boundary is prose, and it is load-bearing.
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
- **Gate on the repair-introduced rate.** Rejected against the third driver, on
  measurement rather than on principle. A threshold of "above half, two
  consecutive rounds" was proposed as the calibration this decision's own
  *Revisit if* asked for. Measured against four recorded loops it fires on two:
  one that diverged and one that converged to a single finding two rounds later.
  Its level does not discriminate — the two converging loops peaked at 80% and
  75%, above the diverging loop's maximum of 60%. The rate is also confounded by
  amendment size: measured by citation overlap it rises with how much of the
  artifact the previous repair touched, so a large amendment reads high with no
  injection at all. It ships advisory, the same treatment `shaping-reviewer`
  gives emphasis density.
- **Gate on family recurrence** — stop when two consecutive rounds share a
  finding family. Rejected, and recorded here because this repository's own
  research proposed it. Three measurements decide it. Full mode already carried
  such a stop and it returned `false` on all 302 recorded evaluations across two
  months, never once firing, because its key embedded a line number and an
  ordinal that every repair moves. In the same corpus the retry cap fired twice
  and a human overrode it both times — the documented default of resetting the
  run happened zero times, so a mechanical stop here produces an override
  conversation rather than less work. And 21 of 30 specs peaked at two findings
  rounds or fewer, so an earlier stop would have had almost nothing to act on
  while its false-stop risk fell on the majority. What ended the one genuinely
  stuck loop was a revert that cut the reviewed construct, not a stop.
- **Soften full mode's caps.** Still deferred, and now separated from the
  instrument question this decision does answer. Full mode's retry cap is a
  round count, which the first driver holds tracks nothing about the cost the
  bound exists to contain; diff size is the quantity that does. Changing it
  touches `_loop_guards.py`, `loop-engine.py`, `assets/state.json`, and the test
  that polices their single-sourcing. That remains a state-schema and
  public-interface change needing its own spec, and this decision deliberately
  leaves the cap in place: after retiring the stasis route it is full mode's only
  mechanical bound.
- **Repair the stasis stop instead of retiring it.** Rejected. Re-keying it to
  the position-free family would revive a stop that has never fired, and revival
  is a behaviour change no prior decision record chose — the route was designed
  in a spec, not decided in an ADR. The measurements under *Gate on family
  recurrence* above are the grounds.

## References

- Implementation: PR #1231, `packs/core/.apm/skills/work-loop/references/light-mode.md`.
- [ADR-0014](0014-rigor-scales-with-risk-work-loop-modes.md) — the decision this replaces in part; its Consequences name the dropped `quality-engineer` floor as the most material accepted loss.
- [RFC-0025](../rfc/0025-work-loop-light-mode-and-risk-based-escalation.md) — the proposal ADR-0014 recorded.
- [`docs/product/research/repair-origin-gating-survey.md`](../product/research/repair-origin-gating-survey.md) — the four-loop measurement, the amendment-size confound, and the self-scoring evidence behind rejecting the repair-introduced rate.
- [`docs/product/research/review-loop-nonconvergence-survey.md`](../product/research/review-loop-nonconvergence-survey.md) — the survey whose § 6 option 3 proposed gating on family recurrence, and whose § 5 records that no mature review process terminates on a defect classification. This decision follows the second and declines the first.

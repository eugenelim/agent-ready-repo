# How to write a post-launch learning contract

**Use this when:** You have placed a bet and need to define what you will measure
post-launch, when you will review the signals, and what would trigger a direction
change.
**Prerequisites:** `product-engineering` pack installed; a committed `bet.md` with
the `learning-contract` field to fill.
**Result:** A completed `learning-contract` section in `bet.md` with named signals,
a review cadence, and a specific pivot condition — so the team can close the bet or
change direction based on real evidence rather than intuition.

> **Diátaxis: how-to.** A goal-oriented guide for the `learning-contract` required
> field in `place-bet`'s `bet.md`. For placing the bet itself, see
> [*How to place a bet*](place-a-bet.md). For the thin-slice definition, see the
> `## How to define a thin slice` section there.

A placed bet with a blank learning contract is a bet no one can close. The learning
contract's job is to prevent "we'll look at the data after launch" from becoming a
permanent state of not deciding.

The contract has three components: **what to measure**, **when to review**, and
**the pivot trigger**. All three must be named before the bet ships.

---

## Component 1: What to measure

Name the signals that would confirm or refute the bet — not a laundry list, but the
two or three behavioral markers or metrics that are causally connected to the
bet's core assumption.

**The discipline:** the signals must be named in terms of user behavior, not
vanity metrics. "DAU" is not a signal for a bet about user trust; "percent of
users who complete a second session without a support touchpoint" is.

**How to choose:**
- Start from the `thin-slice` definition in `bet.md`. The instrumentation event in
  the thin slice is your first signal — it fires when the success condition is met.
- Add one outcome signal: the behavioral change you expect to see in the 30 days
  after the first success. This is usually your `first-success-event` field stated
  as a measurable rate.
- Add one refutation signal: the metric that, if it moves in the wrong direction,
  tells you the bet is failing. Error rate, support volume, or drop-off at the
  thin-slice task are common examples.

**Example — weak:**
> "We'll track user engagement and NPS."

This fails: engagement is not causally connected to the bet, and NPS doesn't fire
on any specific user action. No one can close the bet against these signals.

**Example — strong:**
> Signals:
> - `workspace_joined` event rate for invited users (confirmation signal — target: ≥ 60% of invites accepted within 48 hours)
> - Second session within 7 days for users who accepted their first invite (adoption signal — target: ≥ 40%)
> - Invite-expired support tickets per week (refutation signal — alert if > 20/week)

---

## Component 2: When to review

Name a specific review date or milestone — not "after we've had time to gather
data."

**The discipline:** the review date must be fixed *before* the bet ships, not
after. Post-hoc thresholds rationalize whatever happened. Fix the date when the
signal plan is final.

**How to choose:**
- For a pilot bet: 30 days after launch to the first cohort is the default.
  If your thin slice is time-sensitive (e.g., seasonal), choose the milestone
  that gives a meaningful sample.
- For a production bet: 90 days after general availability is common; align with
  your sprint or quarterly review cadence so the review doesn't get orphaned.
- For a one-way door (an architectural commitment or a pricing change): 6 months
  is a reasonable minimum; shorter reviews produce noise, not signal.

**What the review produces:**
At the review date, the team reads the named signals and answers: do the signals
confirm the bet, refute it, or remain inconclusive? The outcome is one of:
- **Confirmed** — the signals hit their targets; the bet is closed as validated
- **Refuted** — one or more refutation signals crossed the alert threshold; the
  team pivots or kills the bet
- **Inconclusive** — the sample is too small or the signals are noisy; the team
  runs another cycle (name the next review date)

---

## Component 3: The pivot trigger

Name the specific condition that would change the direction before the scheduled
review date.

**The discipline:** the pivot trigger is the kill condition applied to the
post-launch phase. Write it before launch so the team doesn't need to debate
when things go wrong — the trigger is already defined.

**How to choose:**
- The pivot trigger is usually the refutation signal at a threshold that indicates
  the bet is actively failing, not just not yet confirming.
- One specific condition is better than a list of vague concerns.
- State it as: "Pivot if [specific metric] reaches [specific threshold] within
  [specific window]."

**Example — weak:**
> "We'll reassess if adoption is low."

This fails: "low" is not a threshold, and "adoption" is not a signal.

**Example — strong:**
> "Pivot if invite-expired support tickets exceed 40/week within the first two
> weeks, or if `workspace_joined` rate falls below 20% after the first 200
> invites are sent."

---

## Completed example

Here is what a complete `learning-contract` field looks like in `bet.md`:

```markdown
## Learning contract

**Signals:**
- `workspace_joined` event rate for invited users (target: ≥ 60% of invites accepted within 48 hours)
- Second session within 7 days for first-time joiners (target: ≥ 40%)
- Invite-expired support tickets per week (alert threshold: > 20/week)

**Review date:** 2026-09-01 (30 days after pilot cohort launch)

**Pivot trigger:** If invite-expired support tickets exceed 40/week within the
first two weeks, or if workspace_joined rate falls below 20% after the first
200 invites are sent — convene the team before the scheduled review.
```

---

## Common gaps to avoid

**Signals that can't be measured yet.** If the instrumentation for a signal
doesn't exist, it won't fire post-launch. The thin-slice definition requires
a named instrumentation event — confirm it fires in a test environment before
the bet ships.

**A review date that slips.** Block the review date on the team calendar at
the same time you write the learning contract. An unblocked date gets deferred.

**A pivot trigger that's too sensitive.** A trigger that fires in week one on
normal variance means the team is pivoting before the bet has had time to
stabilize. Set the threshold against your expected baseline, not zero.

**All three fields blank on a non-trivial bet.** Three blank fields are not
a neutral state — they are a named risk. If you genuinely cannot name any
signal, any date, or any pivot condition for this bet, that is the moment to
ask whether the bet is ready to place.

---

## See also

- [*How to place a bet*](place-a-bet.md) — including the thin-slice definition and all four new required fields
- `de-risk-intent` — step 3.5; the pre-bet validation; the kill condition set there is the prototype of the pivot trigger
- `map-capabilities` — step 6; the capability map anchors the rollout plan, which names when each capability ships and which signals fire at each stage

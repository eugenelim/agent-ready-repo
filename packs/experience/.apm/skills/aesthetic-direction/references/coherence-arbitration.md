# Coherence arbitration

Named goals will pull a single choice in opposite directions. "Premium"
wants generous breathing room; "dense and efficient" wants more on screen.
Both can be real goals for the same product. Arbitration is how you decide
*before* the conflict reaches a build decision, so the team resolves it once
instead of every time.

## The rule: rank, then a tie has an answer

Two goals of equal weight can't break a tie — whoever's arguing loudest
wins, and the direction drifts. So **rank the goals up front** and name a
**dominant goal**: the one that wins when goals genuinely conflict. Ranking
is the whole mechanism. Everything else records the consequences.

## How to rank

1. **Order by what the product can't survive losing.** Ask, goal by goal:
   "If we nailed everything except this one, would the product still be the
   thing we set out to make?" The goal that breaks the product when missing
   sits at the top.
2. **Force a strict order.** No ties at the top. If two goals feel equal,
   find the scenario where they'd conflict and decide which you'd sacrifice
   — that decision *is* the ranking.
3. **Sanity-check against the felt word.** The dominant goal should match
   the user's original gut answer from Stage 1 of the interrogation. If the
   ranking says one thing and their gut said another, surface the gap —
   one of them is wrong and it's worth knowing which.

## Record the trade-off, not just the winner

When you resolve a conflict, write down all three parts so the build doesn't
re-open it:

- **The tension** — which two goals pull apart, and on what kind of choice
  (spacing density, motion intensity, tone of copy).
- **The call** — which goal wins, stated as the dominant goal applied:
  "When density and premium conflict, premium wins."
- **The why** — one sentence tying it to the ranking, so a future reader
  sees the reasoning, not just the verdict.

A recorded trade-off turns a recurring argument into a settled default.
The build can still escalate a *specific* case — but the burden is on the
exception to justify itself, not on the direction to re-prove itself.

## When the floor is one side of the conflict

Some "conflicts" aren't between two aesthetic goals — they're between a goal
and the shared `quality-floor` (accessibility, all-states, meaningful
motion). That is not an arbitration. **The floor always wins**; it is not a
goal to be ranked against. If "premium" wants thin, low-contrast text that
the accessibility floor rejects, you don't trade the floor away — you find
the version of premium that clears it. Record it as an **open question for
the direction** ("how do we read as premium while clearing the contrast
floor?"), never as a trade-off the build is free to resolve against the
floor.

## Where this lands

The ranking and the resolved trade-offs go in the aesthetic-direction doc —
the ranked-goals list and the "dominant goal for arbitration" section.
That's what downstream work reads when two goals disagree, so the decision
lives in one place and travels with the direction.

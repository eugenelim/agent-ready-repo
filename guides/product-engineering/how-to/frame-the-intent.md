---
title: "Shape an idea"
summary: "Turn a rough idea into a chosen, de-risked plan that is ready to build."
pack: product-engineering
kind: how-to
uses: [product-engineering]
aliases:
  - guides/product-engineering/how-to/find-the-opportunities
  - guides/product-engineering/how-to/commit-and-de-risk
  - guides/product-engineering/how-to/hand-it-to-build
---

# Shape an idea

Say each prompt in the same agent session, starting with the problem in one sentence.

## Write down the outcome

An intent is a short file that states the outcome you want and why. To write one, ask:

```text
Frame this as a product intent: our onboarding drops half of new accounts before they connect a data source.
```

The agent writes `intents/<slug>.md` in your product folder, and the `<slug>` follows the work from here on. You approve the intent before the agent explores options.

## Find the opportunities

To see where the value is, ask:

```text
Identify the opportunities in this situation and assess each one.
```

The agent writes `shaping/<slug>/opportunity-assessment.md`, ranked by value and confidence.

## Compare approaches

To get options that differ in kind, ask:

```text
Diverge on this opportunity — give me approaches that differ in kind, not in detail.
```

The agent writes `shaping/<slug>/solution-options.md`.

## Test the options

To test the options against your limits, ask:

```text
Explore these candidates against our real constraints and tell me which survive.
```

The agent examines each candidate and reports which ones hold up. You select the candidate to pursue.

## Commit to a bet

To choose one option and record why, ask:

```text
Place the bet on this candidate — what are we committing to, and what would tell us we were wrong?
```

The agent writes `shaping/<slug>/bet.md` with the choice, its reasoning, and what would prove it wrong. You approve the decision brief before anything is built.

## Test the riskiest assumption

To find what could sink the bet, ask:

```text
De-risk this bet — what are the riskiest assumptions, and how would we test each cheaply?
```

The agent ranks the assumptions and adds its verdict to the intent file.

## Break it into work

To split the intent into slices a build can take one at a time, ask:

```text
Decompose this intent into deliverable slices, each traceable back to the parent.
```

The agent records the slices on the intent. One shippable feature goes on as a single contract, and a larger outcome gets a coordinating brief at `docs/product/briefs/<slug>.md`. You commit to build when you are ready.

Next, [write the contract](../../core/how-to/start-the-work.md) for each slice.

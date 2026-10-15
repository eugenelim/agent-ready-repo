---
title: Set direction and goals
summary: Go from what you know about the market to a written direction and team goals your engineers can pick up.
pack: product-strategy
uses: [product-strategy]
kind: how-to
aliases:
  - guides/product-strategy/how-to/read-the-situation
  - guides/product-strategy/how-to/route-it-to-work
---

# Set direction and goals

Ask your agent to write down where the product is heading and what each team should aim for. Every file lands in `docs/product/shaping/`.

## Read the situation

To pull the themes out of interviews, surveys, or support transcripts, ask:

```text
Synthesize our stakeholder interviews into the themes that recur across groups, and say which group each came from.
```

The agent writes `stakeholder-synthesis.md` and keeps groups apart when they disagree. To bring your analyses together, ask for a SWOT with `run-swot`; [Analyse the market](run-a-market-and-competitive-analysis.md) covers the others.

## Set the direction

To state the direction as if it already shipped, ask:

```text
Write the PRFAQ for this concept: press release first, then the customer and internal FAQs.
```

The agent writes `prfaq.md`, a press release and two FAQs, so the customer benefit has to be stated plainly. Read the press release to someone outside the team and ask what the product does, then approve it before it routes to work.

## Route it to work

To turn the approved direction into team goals and queued work, ask:

```text
Cascade our company OKRs to team level, identify the gaps, and route them to the shaping queue.
```

The agent writes `okr-cascade.md` and adds each gap to `workspace.toml`, the file where the repository tracks planned work. Read those entries before you approve, because a vague gap becomes a queued item someone else must interpret. For UX and content, ask for `define-ux-strategy` and `define-content-strategy`.

Next, [shape a feature](../../product-engineering/how-to/shape-a-feature-intent.md) from one of the queued gaps.

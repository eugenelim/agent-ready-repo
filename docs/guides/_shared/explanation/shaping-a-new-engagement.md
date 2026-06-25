# Shaping a new engagement: product intent and the architecture concept

*About how a product vision, a product strategy, and an architecture concept inform each other when you start a new engagement.* This page is the *why*; the procedures live in the how-tos it links, and the stage-by-stage menu lives in [Run a full inception](../how-to/run-a-full-inception.md).

The start of a new engagement is where the most expensive mistakes are the cheapest to fix. Build the wrong product and no architecture saves it; pick an architecture that can't meet the bet and the product never ships. Two kinds of shaping run here — *what should exist and for whom*, and *how it should be built* — and they are not sequential phases so much as two tracks that keep checking each other. This page is about how they relate.

## Two tracks, one artifact each

The product track lives in the `product-engineering` pack. Its one artifact is the **intent** — an outcome plus the opportunity behind it — written at the altitude you're operating at. A [product vision](../../product-engineering/how-to/frame-a-product-vision.md) and a [product strategy](../../product-engineering/how-to/shape-a-product-strategy.md) are the same artifact one rung apart, not two document types.

The architecture track lives in the `architect` pack. Its first artifact is the **[architecture concept](../../architect/how-to/shape-an-architecture-concept.md)** — a ≤½-page shape that gets agreed before anyone writes a multi-page design doc.

Both tracks share a habit: shape something small, get it agreed, and only then commit depth. The vision is a bet you can kill in a sentence; the concept is a shape you can redraw in a sentence. That's deliberate — depth before agreement is the expensive mistake both packs exist to prevent.

## Vision and strategy: the same bet, one rung apart

The vision is the **existence bet** — why this product should exist, for whom, and through what wedge. The strategy is the **path** — the central challenge, the guiding policy, the coherent actions, and which problem you solve for which segment, in what order. Vision sits above strategy; both sit above the capability and feature work that follows.

What makes them one artifact rather than two is that the *kind of risk* shifts with the altitude, not the shape of the thing you write. At both product altitudes the bet is **market-existence** — will anyone want this, and can it be a business — tested once at the top, not re-argued at every feature below. The intent tree explains why the altitudes nest this way; this page won't re-derive it.

## Where the architecture concept meets the product

This is the join most engagements get wrong, in both directions.

**The product shapes the architecture.** The strategy's bets are the concept's inputs. The viability half of the market-existence bet sets the cost and quality envelope the architecture has to live inside. The wedge says what must be built first and what can wait. The problem/segment sequence tells the concept what to be ready for and what it's safe to defer. An architecture concept drawn without the strategy in view optimizes for the wrong attributes — gold-plating a path the product won't take.

**The architecture talks back.** The concept can kill or reshape a product bet, and should be allowed to. If the cheapest shape that meets the top quality attribute blows the viability guardrail, that's not a detail to handle later — it's a finding for the strategy. The concept's *key tradeoff* and its grounded platform limits are exactly the kind of news that changes what the product should promise. Treating architecture as downstream-only — product decides, architecture implements — is how a team discovers in month three that the bet was never affordable.

The healthy pattern is a short loop: shape the strategy, shape a concept against it, let what the concept surfaces revise the strategy, settle. Neither track finishes before the other starts.

## Sequence is a default, not a gate

Vision → strategy → concept is the order when you're carrying all three uncertainties. You rarely are. You reach for a stage only when you hold the uncertainty it removes: skip the vision when the product clearly should exist, skip the strategy when the path is obvious, go straight to a concept when the only open question is *how*. A clear idea with obvious value and a familiar stack needs none of this — it goes straight to a brief and the build loop. [Run a full inception](../how-to/run-a-full-inception.md) lays out that menu of stages against the uncertainties they answer.

## What this is not

- **Not a waterfall.** The stages are keyed to uncertainty, not arranged as phase gates. Running all of them on an engagement whose value and shape are already clear is ceremony, and ceremony is its own kind of risk.
- **The concept is not the design doc.** The concept is the shape; the design doc is the depth that follows once the shape is agreed. Collapsing the two loses the cheap-to-change window the concept exists to hold open.
- **The intent tree is not a tracker.** Vision, strategy, and the capabilities below them form a tree that's deeper than any board. Trackers are a one-way projection of it, never the model itself.

## See also

- [Frame a product vision](../../product-engineering/how-to/frame-a-product-vision.md) — shape the existence bet.
- [Shape a product strategy](../../product-engineering/how-to/shape-a-product-strategy.md) — shape the path that realizes it.
- [Shape an architecture concept](../../architect/how-to/shape-an-architecture-concept.md) — shape the technical concept it builds toward.
- [The intent tree](../../product-engineering/explanation/the-intent-tree.md) — the model behind the product altitudes.
- [Run a full inception](../how-to/run-a-full-inception.md) — the full menu of inception stages and the packs each needs.

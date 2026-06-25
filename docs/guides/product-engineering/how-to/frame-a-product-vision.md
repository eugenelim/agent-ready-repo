# How to frame a product vision

> **Diátaxis: how-to.** Shape the top of the intent tree — the *existence bet* for a new product or engagement. For the model behind the altitudes, see the explanation [*The intent tree*](../explanation/the-intent-tree.md); for the feature-altitude walk, [*Shape a feature intent*](shape-a-feature-intent.md); for how vision, strategy, and the architecture concept fit together at the start of an engagement, [*Shaping a new engagement*](../../_shared/explanation/shaping-a-new-engagement.md).

You are starting a new engagement with a product idea, and the real question is not which features to build but whether this product should exist at all, and for whom. A product vision answers that as a bet you can test. Install the `product-engineering` pack, then work the three moves below.

## 1. Frame the vision at the product-vision altitude

Invoke `frame-intent`. It runs intake first: it infers **Scale** (a single repo with app code → `app`; many component pointers and no app code → `business-unit`), confirms it, and asks whether the work is **greenfield or brownfield**. For a greenfield product concept it asks the altitude outright instead of defaulting to `feature` — answer **`product-vision`**. Scale only *suggests* a starting altitude; you set it in a word.

The intent template (`frame-intent/assets/intent-template.md`) lands at `docs/product/intents/<slug>.md`. Stamp `Level: product-vision` and fill three fields:

- **Outcome** — a steerable *input* you can move, the *lagging* result it should drive, and a *guardrail* that must not get worse. At the vision altitude you are pre-product, so a **qualitative-but-falsifiable** outcome is first-class: name the signal you would accept as proof, not a conversion number you don't have traffic for.
- **Opportunity** — the job the user is trying to get done, framed without a solution. "Get back into my account on my own", not "add a reset-link button". A vision built around a solution can't be tested as a bet.
- **Assumptions** — what must be true for the product to exist as a business, one line each.

The existence bet has a shape worth holding to: **why this product should exist, for whom, and through what wedge** — the narrow first foothold, not the eventual platform.

`frame-intent` is knowledge-surface aware. When it can reach an internal knowledge surface — an enterprise-knowledge MCP tool, an internal CLI, an in-repo doc set — it consults the business-domain and in-flight areas so the vision uses your org's real terms and doesn't re-bet something already being delivered, and it names the surface it used (or "none", with confidence lowered to match).

## 2. De-risk the market-existence bet

Invoke `de-risk-intent`. At the product altitudes the riskiest assumption is **market-existence**, not feature desirability: *will anyone want this at all* and *can it be a business*. The viability half is named so it can't quietly drop out, and you test it **once at the top** rather than re-litigating it per feature later.

Predeclare the **kill condition before you probe**. Pre-product, that's a qualitative bar stated in 0-to-1 terms — "proceed only if at least four of six target buyers say they'd switch and name a budget" — not a fabricated threshold. Writing the line down before you see the result is what separates a real test from theatre.

The verdict is **survive or kill**. Killed → reframe the vision or drop it; a product nobody wants fails differently from a feature nobody uses, and the top of the tree is the cheapest place to learn that. Survived → decompose.

## 3. Decompose toward a strategy

Invoke `decompose-intent`. A surviving product-vision intent produces the **next level down** — a `product-strategy` child (or an intervening `initiative` if your org names one), not specs. Don't skip levels: the strategy is where the path gets named. Record *why* the cut went the way it did on the parent's `Decomposition`, so a later reader doesn't re-litigate a branch you already ruled out.

From here, [shape the product strategy](shape-a-product-strategy.md).

## See also

- [The intent tree](../explanation/the-intent-tree.md) — why one recursive artifact covers vision through feature.
- [Shape a product strategy](shape-a-product-strategy.md) — the next altitude down.
- [Shaping a new engagement](../../_shared/explanation/shaping-a-new-engagement.md) — how the vision relates to strategy and the architecture concept.
- [Run a full inception](../../_shared/how-to/run-a-full-inception.md) — where product shaping sits among research, architecture, and the build loop.

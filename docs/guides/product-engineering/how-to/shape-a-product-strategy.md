# How to shape a product strategy

> **Diátaxis: how-to.** Shape the *path* from a product vision — the second product altitude. For the model, see [*The intent tree*](../explanation/the-intent-tree.md); for the altitude above, [*Frame a product vision*](frame-a-product-vision.md); for how the pieces fit at engagement start, [*Shaping a new engagement*](../../_shared/explanation/shaping-a-new-engagement.md).

You have a product vision that survived its market-existence test, and now you need the path to realize it: which problem, for which segment, in what order, and why now. That path is a **product-strategy** intent. Install the `product-engineering` pack, then work the moves below.

## 1. Decompose the vision, or frame the strategy directly

If you came from a vision, invoke `decompose-intent` on it. A surviving `product-vision` intent produces a `product-strategy` child that inherits the vision's outcome context and carries a `Parent intent:` back-link.

If you're entering at the strategy altitude with no framed vision above it, invoke `frame-intent` and answer the altitude as **`product-strategy`**. When the work really needs a vision above it, `decompose-intent` and `frame-intent` both carry a *missing-parent* offer — they'll propose framing the parent and hanging the strategy beneath it. It's an offer, never a block; accept it or proceed.

## 2. Write the strategy as challenge, policy, actions

A product-strategy intent is the same artifact as any other — `Outcome`, `Opportunity`, `Assumptions`, `Decomposition` — but the **opportunity reads as a path**. Name four things:

- **The central challenge** — a diagnosis of the one obstacle that, left unaddressed, sinks the vision. Not a list of problems; the crux.
- **The guiding policy** — the overall approach you'll take to that challenge.
- **The coherent actions** — the few moves that deliver on the policy and reinforce each other rather than scatter effort.
- **The problem/segment sequence** — which problem for which segment, in what order, and why now.

Keep the outcome honest: a steerable input, the lagging result it drives, a guardrail that must not get worse. Don't bolt a quantified target onto a path you've already chosen — name the input you can actually steer.

## 3. De-risk at the product level

Invoke `de-risk-intent`. A strategy bet is still **market-existence** in kind — will this *path* reach a market that pays — not feature desirability. Predeclare the kill condition before you probe, take the survive/kill verdict, and fold what you learn back into the strategy. A killed strategy reshapes the vision above it; it doesn't spawn capabilities that inherit a dead bet.

## 4. Decompose toward capabilities

Invoke `decompose-intent` on the survived strategy. It produces the **next level down** — `capability` intents, each of which re-enters the loop (`frame → de-risk → decompose`) until the leaf is a `core` brief your delivery loop can build. Don't skip the capability rung: it's where the architectural and adoption bets live, distinct from the market bet you tested up top.

Before you commit to *how* the capabilities get built, shape the [architecture concept](../../architect/how-to/shape-an-architecture-concept.md) against this strategy — the strategy's bets are its inputs.

## See also

- [Frame a product vision](frame-a-product-vision.md) — the altitude above, where the existence bet is tested.
- [The intent tree](../explanation/the-intent-tree.md) — why vision, strategy, capability, and feature are one recursive artifact.
- [Shape an architecture concept](../../architect/how-to/shape-an-architecture-concept.md) — the technical shaping the strategy feeds.
- [Shaping a new engagement](../../_shared/explanation/shaping-a-new-engagement.md) — how product intent and the architecture concept co-shape each other.

# Shape an architecture concept

**Use this when:** You have a product feature or strategy and a real technical choice to make, and you want the architecture shape agreed cheaply before committing to a full design doc.
**Prerequisites:** The `architect` pack installed; a clear product bet or feature brief; optionally a `reference.md` golden path.
**Result:** An agreed ≤½-page concept naming the problem, constraints, candidate shapes, provider, and key tradeoff — optionally converged into a full design doc.

> Get a ≤½-page architecture concept agreed before you commit to a full design doc. Assumes you know roughly what you're building; if the product bet itself is still unsettled, shape that first with [`product-engineering`](../../product-engineering/).

You have a product to build — a strategy, a brief, or a clear feature — and a real technical choice to make. Before writing a multi-page design doc, `architect-design` shapes a **Stage-0 concept**: the elevator-pitch version of the architecture that gets the shape agreed cheaply, while changing it still costs a sentence. Install the `architect` pack, then work the steps below.

## 1. Invoke architect-design and frame the problem

Run `architect-design`. It asks only what's genuinely missing — what you're building, who's affected, why now, what counts as success — three to five questions at most. Anything you've already said, it skips; anything you can't answer becomes an open question rather than a blocker.

The skill **steers off your `reference.md`** and is **knowledge-surface aware**. If your repo has a [`reference.md` golden path](establish-reference-architecture.md), the concept measures against it, so establish that first if you haven't. When an internal knowledge surface is reachable, `architect-design` consults it before proposing and names what it drew from.

## 2. Agree the concept before the doc

The concept is a ≤½-page artifact (`architect-design/assets/concept.md`), and the skill **waits for you to agree the shape** before going further. It carries the shaping essentials and deliberately none of the design doc's heavy sections:

- **Problem & context** — the user-visible problem and why now, in two or three sentences.
- **Constraints** — the hard edges: deadline, budget, team shape, regulatory, existing-system shape. At least one should be non-obvious.
- **Candidate shapes (1–2)** — one line each; a second only when there's a real second option.
- **Provider / provider-class** — AWS, Azure, GCP, a primitives provider, local-first, or none. One *by-construction* line on which quality attributes managed services meet versus what you'd build yourself.
- **Top 2–3 quality attributes** — ranked by business-importance × architectural-risk, each with a one-line reason it ranks where it does.
- **Key tradeoff / open decision** — the one or two calls the full doc will turn on.

This is *shaping* — context, constraints, and the choice — not a stripped-down proposal. If the concept collapses into "here's the answer", you've skipped the shaping it exists to do.

Ground any load-bearing platform claim. For every managed service on a critical path, `architect-design` grounds its *binding* contract — non-configurable limits, scaling floors, cold-start behaviour, network and identity needs — in an authoritative source, and lowers the confidence on anything it couldn't ground. A limit recalled wrong is the miss that surfaces two days into the build, not at review.

## 3. Converge into the design doc

Once you agree the concept, `architect-design` offers to draft the full Google-style design doc — TL;DR, context, goals and non-goals, proposal, alternatives, risks, rollout, open questions — and converges it against review, auto-resolving mechanical findings and surfacing judgment calls as explicit decisions. If the concept is all you need right now, stop there: it's a real artifact, not a draft of something else.

When the doc captures discrete decisions — a technology choice, a structural commitment, an interface contract — `architect-design` ends by flagging them as ADR-worthy. Capture them with your ADR skill.

## Verify

You have a usable architecture concept when:

- It fits on half a page and names the problem, the constraints, the candidate shapes, the provider, and the top quality attributes.
- Every quality attribute names why it ranks where it does.
- The key tradeoff is a genuine decision, not a foregone conclusion dressed as one.
- Someone who wasn't in the room could say what's being built and what's still open.

## See also

- [Establish your repo's reference architecture](establish-reference-architecture.md) — the golden path the concept measures against.
- [Diagram a system](diagram-a-system.md) — when the concept needs a picture to reason about.
- [Review an architecture artifact](review-an-architecture-artifact.md) — get a severity-tagged critique of the concept or the design doc.
- [Shape a product strategy](../../product-engineering/how-to/shape-a-product-strategy.md) — the product path the concept builds toward.
- [Shaping a new engagement](../../_shared/explanation/shaping-a-new-engagement.md) — how the architecture concept relates to the product vision and strategy.

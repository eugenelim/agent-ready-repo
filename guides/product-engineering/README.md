---
title: "`product-engineering` — guides"
summary: Turn a product problem into an evidenced bet you approved, then hand the approved result to delivery.
pack: product-engineering
kind: explanation
---

# `product-engineering` — guides

**Use this when** you have a problem or a signal — a metric moving the wrong
way, a complaint, a request from a customer — and nobody has yet earned the
confidence to say what to build. You leave with a bet you approved: a named
outcome, the approach you picked over the alternatives, the assumption that
could kill it, and
slices your delivery loop can pick up — or, when the bet is bigger than one
feature, the next layer of intents to take through this same walk.

**Start like this.** Ordinary language, in an agent session with this pack
installed. You do not have to choose a skill first.

```text
Shape this: we're seeing first-session drop-off and think new users may not understand the product's value.
```

The agent confirms a couple of things about the framing with you, writes it,
and asks you to approve it before exploring any solution. One of those is how
big a bet this is — asked explicitly when the input is a product concept or a
greenfield idea, and settled without ceremony when the scope is already clear.

**Those sizes are altitudes**, and they run `product-vision`,
`product-strategy`, `capability`, `feature`. Start at the one you are actually
operating at. If the product's existence is itself the open question, begin
with [frame a product vision](how-to/frame-a-product-vision.md) instead. [The
intent tree](explanation/the-intent-tree.md) has the full model, and you do not
need it to start.

## Walk the guidebook

Four stages, in order. Each step shows what you type, what the agent replies,
one turn where you push back and it adjusts, where you decide, and an excerpt
of what you get.

1. [Frame the intent](how-to/frame-the-intent.md) — the problem becomes a written outcome with an owner and a slug, before anyone proposes a solution.
2. [Find the opportunities](how-to/find-the-opportunities.md) — where the value actually is, then approaches that differ in kind, tested against real constraints.
3. [Commit and de-risk](how-to/commit-and-de-risk.md) — commit to the one you chose, say what would prove it wrong, and rank what could make it wrong.
4. [Hand it to build](how-to/hand-it-to-build.md) — slice it so each piece ships something a customer would notice, and hand those slices to delivery.

**The walk runs the whole pack.** Its four step maps name all fifteen skills
this pack ships, so nothing is waiting off to one side. Seven of the fifteen
are required; the rest are there for when a stage needs more than the short
route — each step's table says which is which.

## Where you decide

Four gates. The agent runs everything between them and stops at each one.

| You decide | At | The call you are making | Roughly |
| --- | --- | --- | --: |
| Approve the intent | Step 1 | Is the problem specific enough to eliminate candidates, the user named, the outcome measurable? | 10–15 min |
| Choose a candidate | Step 2 | Are the survivors genuinely different from each other, and is anything missing? This is the last cheap moment to widen the field. | 15–20 min |
| Approve the decision brief | Step 3 | Does the bet have a losing condition — something you would accept as proof it was wrong? If you ran the supervised end-to-end route (`discovery-loop`), also: did its threat and reliability reviewers flag anything that blocks the build? | 20–30 min |
| Commit to build | Step 4 | Is there anything here you are not prepared to ship? | 5 min |

**"The decision brief" is what you have accumulated by step 3**, not a
separate document to go and find. On the short route that is the bet, plus the
opportunities and options behind it and the intent they trace to — the files in
the table below. `discovery-loop` gathers the same material into its own brief.

These are four distinct calls, not one approval spread over four pages.
Framing a problem is not committing to a solution; generating candidates is not
choosing one; converging on a candidate is not validating it; and a decomposed
bet is not permission to implement — the fourth gate is what grants that.

The agent proposes, eliminates with reasons, and writes it down. It does not
choose the product direction.

## What becomes durable

Two places accumulate as you walk, and they hold most of what you end up with.

| Where | What collects there |
| --- | --- |
| `<output_dir>/intents/<slug>.md` | The intent itself — the outcome, its altitude and owner, the opportunity behind it, and later the decomposition |
| `<output_dir>/shaping/<slug>/` | The working record — the ranked opportunities, the candidate options, the bet, and the capability map when you run it |

`<slug>` is this work's short name, fixed at step 1 so everything traces back to
it. `<output_dir>` is where this repository keeps product artifacts; the agent
asks when it is not configured, and tells you which path it wrote to.

**The intent file accretes** rather than being replaced. Step 1 creates it,
de-risking adds its validation hook, and step 4 adds the decomposition. It is
the one file to keep if you keep only one.

A few things land elsewhere — a Lean Canvas, a value-stream rollup, the
product's voice chart, domain framing, and a coordinating delivery brief. Each
step page names where its skills write, and [the discovery sidecar
reference](reference/discovery-sidecar-and-roster.md) covers the files the
supervised `discovery-loop` route keeps.

Where a skill only reports in the session, carry what matters into that step's
artifact — the walk says where.

## How the approved result reaches delivery

Step 4 is not "discovery complete". It produces work `core` can start on, and
what it produces depends on the shape of the result.

- **One independently shippable feature** — a slice a customer would notice on
  its own — becomes a **delivery contract**, and `core` writes a spec for it.
  A slice that arrived through a delivery brief has that brief stamped on its
  spec, so the link back to this work survives the handoff.
- **A result spanning several specs or repositories** needs a **coordinating
  delivery brief** first, because no single spec owns it.
- **At `capability` level or above**, decomposition produces child intents
  instead. Each re-enters this walk at its own level and is de-risked on its own.

Hand it over in ordinary language too: [hand an intent to
build](how-to/hand-an-intent-to-build.md) shows the request. Core's
`work-intake` writes the canonical artifact, registers it in `workspace.toml`,
and reports which route it chose.

The routes then diverge, and the difference is worth knowing before you pick
one. **Admission** adds the fields routing needs to your intent in place —
keeping the framing you wrote and its altitude — then registers it as a draft
and stops. Nothing is dispatched and no build begins; it is a way to get work
on the books. The **spec**, **brief**, and **bug-fix** routes each create
their own artifact from your intent and hand on to the processor that starts
the work.

**The handoff moves the work, not the authority.** It approves nothing and
skips no gate: `core` stops at its own next approval before any code is
written, and this pack's four gates stay yours. The walk's last step continues
into [write the contract](../core/how-to/write-the-contract.md) in the `core`
guidebook.

## Tutorials

- [Walk a discovery end-to-end](tutorials/walk-a-discovery-end-to-end.md) — follow one full discovery, from a raw idea to a ratified decision brief handed to `work-loop`, seeing each gate, a divergence, a rejection/recovery, and the validation hooks.

## How-to

Recipes for a problem you already have, once the walk is familiar.

- [Frame a product vision](how-to/frame-a-product-vision.md) — shape the existence bet at the top of the tree, then de-risk it as a market-existence question.
- [Shape a product strategy](how-to/shape-a-product-strategy.md) — turn a vision into the path: central challenge, guiding policy, coherent actions, and problem/segment sequence.
- [Shape a feature intent in an app repo](how-to/shape-a-feature-intent.md) — frame, de-risk, and decompose a single piece of work down to a spec.
- [Run a discovery end-to-end](how-to/run-a-discovery.md) — turn a raw idea into a build-ready decision brief with the discovery loop: the one-prompt form, the consent gates, recursion, resume, and folding in existing requirements.
- [Hand an intent to build](how-to/hand-an-intent-to-build.md) — start Core intake with the outcome and boundaries intact, and read the route it picks.
- [Run a capability across a value stream](how-to/run-a-capability-across-a-value-stream.md) — coordinate one capability across several component repos from a meta-repo.
- [Fix a refused intent](how-to/fix-a-refused-intent.md) — read the refusal, find the field it names, and apply the one remedy that clears it.
- [Rename an intent](how-to/rename-an-intent.md) — retire one intent path, issue its successor, and recover the transaction if it stops partway through.
- [Write a product's voice and microcopy](how-to/write-product-microcopy.md) — characterize the product's voice, then write the error, empty, button, and label copy from blame-free formulas.

When one stage of the walk needs more than the short route:

- [Frame a situation](how-to/frame-a-situation.md) — classify the signal and anchor the team to the right entry point, when the problem itself is unclear.
- [Identify opportunities](how-to/identify-opportunities.md) — surface the jobs behind an opportunity area and score them.
- [Generate solution options](how-to/generate-solution-options.md) — produce comparable options that expose the real decision.
- [Create a Lean Canvas](how-to/create-a-lean-canvas.md) — the initiative's core hypothesis on one page.
- [Place a bet](how-to/place-a-bet.md) — commit to a direction with the betting table behind it.
- [Map capabilities](how-to/map-capabilities.md) — turn a committed bet into what you must be able to do, and what exists today.

## Reference

- [Intent fields, modes, and projection profiles](reference/intent-fields-and-modes.md) — every field on an `intent`, the modes, and how it projects.
- [The discovery sidecar, plan-tree, and roster](reference/discovery-sidecar-and-roster.md) — the discovery loop's working slots, the plan-tree template, the verdict set, the gates, and the skill/agent roster.

## Explanation

The model underneath the walk. Read these after walking it, not before.

- [The intent tree — level-agnostic product shaping](explanation/the-intent-tree.md) — why one recursive shape covers the product altitudes (`product-vision`, `product-strategy`) and engineering work (`capability`, `feature`) alike, with `Level` an open set decoupled from `Scale`.
- [The discovery loop — from a raw idea to a build-ready brief](explanation/the-discovery-loop.md) — the no-engine coordinator contract, divergence → convergence → validation, *converged ≠ validated*, and recursion as data.

---

For the brief layer that sits between a roadmap and a spec, see [`core`'s brief guides](../core/). Installing and upgrading live in [`../_shared/`](../_shared/).

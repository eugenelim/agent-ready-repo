# Product Engineering

Your agent can take a raw product idea to a build-ready decision brief, then hand each piece to your build loop.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install it once for your user account:

```bash
agentbundle install --pack product-engineering
```

In Claude Code you can install it as a plugin instead:

```bash
claude plugin install product-engineering@agent-ready-repo
```

## What your agent can do

- Frame a rough idea as an intent: the problem, who has it, the outcome, and the opportunity behind it.
- Sort a market shift, metric drop, or recurring user pain before anyone shapes work.
- Find and rank the unmet jobs behind a problem, and plan how to validate the riskiest assumptions.
- Lay out solution options with trade-offs, then record the bet with its reasons and what would reverse it.
- Map the capabilities a bet needs and decide build, buy, partner, or adopt for each.
- Break an intent into delivery briefs and specs, and write UI copy for each screen state.

## Skills

- **`discovery-loop`** — Runs a supervised discovery from idea to decision brief, and resumes where you left off.
- **`intent`** — Frames, de-risks, and decomposes product work in three modes.
- **`frame-situation`** — Classifies a signal and rates capability maturity on a Wardley map.
- **`frame-domain`** — Frames how the activity is really done and draws the MVP boundary.
- **`identify-opportunities`** — Ranks unmet jobs by importance and satisfaction.
- **`plan-validation`** — Plans what would confirm or kill each assumption, with an interview or test guide.
- **`explore-options`** — Sketches several distinct product shapes before you pick one.
- **`diverge-solutions`** — Compares solution options for an initiative, with a recommendation.
- **`lean-canvas`** — Fills a lean canvas and writes a one-page initiative brief.
- **`place-bet`** — Records the choice, confidence, appetite, accepted risks, and reversal conditions.
- **`map-capabilities`** — Lists needed capabilities and a build order.
- **`ux-writing`** — Writes the product voice and per-state UI copy.
- **`align-value-stream`** — Sets up a coordinating repo for work that spans many components.

Subagents: **`discovery-lead`** supervises the loop. **`discovery-reliability-reviewer`** and **`discovery-threat-reviewer`** review discovery artifacts read-only.

## Works with

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, and Kiro IDE. [Product Strategy](../product-strategy/README.md) supplies goals and opportunity assessments as anchors. [Core](../core/README.md) takes each result as a delivery contract or brief, and Core is optional. [Experience Design](../experience-design/README.md) passes its screen states to `ux-writing`. When the `architect` pack is installed, `frame-domain` and `intent de-risk` offer `architect-assess`, and `intent frame`, `intent decompose`, and `map-capabilities` offer `architect-design`. Without it, they say nothing about it. Guides: [Shape an idea](../../guides/product-engineering/how-to/frame-the-intent.md) and [Run a discovery](../../guides/product-engineering/how-to/run-a-discovery.md).

## Questions

**Where do I start?** Type `intent frame` and describe a product problem at any level of clarity. To resume, type `discovery-loop` with the initiative name.

**Does it write specs?** It decomposes an intent into briefs and specs, and after you confirm, hands each independently shippable piece to Core. Core's approval path still applies.

**Where are the files saved?** In `docs/product/` and `docs/discovery/` by default. Both are configurable in `agentbundle-layout.toml`.

**Does it need Product Strategy first?** No. Without strategy files, the skills carry on.

## Details

Scope: user (default), repo · Version: 1.0.5 · Source: [packs/product-engineering](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/product-engineering)

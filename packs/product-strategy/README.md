# Product Strategy

Your agent can answer the strategic questions that come before any product work: who to serve, which problem to commit to, and what would make you change course.

## Install

You need [`agentbundle`](../../guides/_shared/how-to/install-agentbundle.md) first. Install it once for your user account:

```bash
agentbundle install --pack product-strategy
```

In Claude Code you can install it as a plugin instead:

```bash
claude plugin install product-strategy@agent-ready-repo
```

## What your agent can do

- Pressure-test a product idea by writing the press release and FAQ before the product exists.
- Map the situation with a SWOT, a PESTLE scan of the macro environment, or Porter's Five Forces.
- Place each product or initiative in a portfolio matrix and recommend where to invest.
- Cascade company OKRs to team level and show the gaps no team owns.
- Turn stakeholder research into a strategic narrative organized by theme.
- Set the UX and content strategy that design work follows.

## Skills

- **`write-prfaq`** — Writes the press release and FAQ that force an honest answer on who the product is for.
- **`run-swot`** — Writes a situation picture of strengths, weaknesses, opportunities, and threats.
- **`run-pestle-analysis`** — Scans the macro environment before you set strategy or enter a market.
- **`run-porters-five-forces`** — Maps the competitive dynamics of an industry.
- **`run-bcg-matrix`** — Places initiatives in a portfolio matrix with a recommendation for each.
- **`run-okr-cascade`** — Cascades company OKRs to teams and exposes the gaps.
- **`synthesize-stakeholder-research`** — Turns research briefs into a strategic narrative.
- **`define-ux-strategy`** — Sets the experience direction before design begins.
- **`define-content-strategy`** — Sets the content direction before content design begins.

## Works with

Works with Claude Code, Codex, Cursor, GitHub Copilot, Gemini CLI, Kiro IDE, and Kiro CLI. [Desk Research](../desk-research/README.md) briefs feed `synthesize-stakeholder-research`. [Product Engineering](../product-engineering/README.md) picks up the strategy gaps from `run-okr-cascade`. [Experience Design](../experience-design/README.md) reads the UX and content strategy. See [Analyse the market](../../guides/product-strategy/how-to/run-a-market-and-competitive-analysis.md) and [Set direction and goals](../../guides/product-strategy/how-to/set-the-direction.md).

## Questions

**Do I need to pick a method?** No. Ask the question, such as "Who should we serve first?", and the pack selects the method.

**Where do the results go?** Each result is a committed record in `docs/product/shaping/`, not a slide. Nothing is written until you approve it.

**Does it find market data on its own?** No. The situation tools use the information you provide. Pair it with Desk Research for sourced evidence.

**Does it change my backlog?** `run-okr-cascade` writes the gaps it finds as strategy entries in `workspace.toml`, after you approve.

## Details

Scope: user (default), repo · Version: 0.2.8 · Source: [packs/product-strategy](https://github.com/eugenelim/agent-ready-repo/tree/main/packs/product-strategy)

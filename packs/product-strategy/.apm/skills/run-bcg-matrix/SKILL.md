---
name: run-bcg-matrix
description: Use when a strategist needs to assess portfolio position and decide where to invest, harvest, or divest across multiple products or business units. Triggers on "run a BCG matrix", "I need to assess our portfolio before allocating resources", "which of our products should we invest in versus harvest", "portfolio growth-share analysis", "classify our products as stars cash cows question marks dogs". Produces a committed portfolio-position artifact. Do NOT use for single-product strategy — BCG requires at least two offerings to compare relative market share.
---

# Skill: run-bcg-matrix

Produces a **portfolio position analysis** using the BCG Growth-Share Matrix — four quadrants: Stars (high growth, high share), Cash Cows (low growth, high share), Question Marks (high growth, low share), and Dogs (low growth, low share). Investment implications flow from quadrant position. See `references/agentbundle-layout.md` for artifact path.

## When to invoke

1. **A multi-product or multi-business-unit portfolio exists** — at least two offerings must be mappable; single-product analysis belongs in SWOT.
2. **You are making resource allocation decisions** — BCG is an investment-prioritization tool.
3. **No current BCG analysis exists for this portfolio** — amend rather than duplicate.

## Procedure

1. **Elicit the portfolio.** List each product, product line, or business unit. Name the primary revenue or usage metric for each. Confirm these are the correct units of comparison.
2. **Estimate relative market share.** For each offering, estimate share relative to the largest competitor in its segment (ratio: own share ÷ largest competitor's share). Elicit data if available; if not, surface the caveat ("market share estimated — treat as directional") and proceed with the best available proxy (revenue rank, user count rank, or analyst estimate).
3. **Estimate market growth rate.** For each offering's segment, estimate the annual growth rate. Use the same caveat protocol as step 2 when data is unavailable.
4. **Map to quadrants.** Use a rough threshold (typically 1.0 for relative share; 10% for growth rate, though the strategist sets their own cutoffs) to classify each offering into Star / Cash Cow / Question Mark / Dog.
5. **Derive investment implications.** For each quadrant: Stars → invest to maintain leadership; Cash Cows → harvest for cash to fund Stars and selective Question Marks; Question Marks → decide invest-or-divest based on strategic fit and capital availability; Dogs → divest or manage for exit unless there is a strategic reason to hold.
6. **Name the top strategic decision.** From the portfolio map, identify the one or two reallocation moves that would most improve the portfolio's overall health. These feed directly into the OKR cascade.
7. **Resolve the artifact path** following `references/agentbundle-layout.md`. Surface the path, then commit `portfolio-position.md` with frontmatter `type: portfolio-position`.

## Anti-patterns

- **Mandating precise market share data.** BCG is a directional framework; proceed with proxy data and surfaced caveats rather than blocking on unavailable metrics.
- **Treating quadrant labels as verdicts.** A Dog is not automatically divest-worthy — strategic fit, competitive moat, and customer relationships matter. The quadrant is an input to the decision, not the decision.
- **Applying BCG to a single product.** Without at least two offerings, there is no relative share comparison and no portfolio decision to make.
- **Quadrant as strategy substitute.** BCG positions products in a portfolio; it does not name the mechanism that defends a Star's position or moves a Question Mark to Star. A BCG analysis without investment implications per quadrant, without naming the specific capability investment that would move a Question Mark or protect a Star, is a labeling exercise. The investment implications (step 5) and the top strategic decision (step 6) are the deliverable, not the quadrant map.

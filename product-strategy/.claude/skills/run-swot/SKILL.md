---
name: run-swot
description: Use when a strategist needs a structured situation synthesis before committing to a strategic direction. Triggers on "run a SWOT", "I need to understand our position before setting strategy", "situation synthesis before setting direction", "what are our strengths and weaknesses relative to this opportunity", "map out our opportunities and threats". Produces a committed SWOT artifact. Do NOT use as a substitute for market data — SWOT organizes what you know; it does not generate evidence you don't have. Do NOT use to set OKR targets — that belongs to run-okr-cascade.
---

# Skill: run-swot

Produces a **SWOT analysis** — an inside-out / outside-in situation map that organizes Strengths, Weaknesses, Opportunities, and Threats before the strategy direction is set. Uses the SWOT framework; see `references/agentbundle-layout.md` for artifact path resolution.

## When to invoke

1. **A defined scope exists** — organization, product line, or market entry; SWOT without a scope boundary produces noise.
2. **You are upstream of a strategic decision** — not already mid-execution; SWOT informs strategy, it does not evaluate it.
3. **No current SWOT exists for this scope** — if one exists, amend it rather than starting fresh.

## Procedure

1. **Elicit and confirm scope.** Name the entity (org, product, market entry), the time horizon, and the competitive reference point. Narrow to one scope; a SWOT that tries to cover everything covers nothing.
2. **Author Strengths.** List internal capabilities, assets, and advantages the entity already possesses and that a competitor would find difficult to replicate quickly. Elicit at least three; push for specificity over generality.
3. **Author Weaknesses.** List internal gaps, resource constraints, process failures, or capability absences that reduce competitive effectiveness. Be direct — a softened weakness list defeats the purpose.
4. **Author Opportunities.** List external conditions, market trends, regulatory changes, or competitor missteps that the entity could exploit. Name the evidence or source for each (PESTLE output, competitor analysis, stakeholder research). Reference the PESTLE or Porter's Five Forces artifacts if available in `docs/product/shaping/`.
5. **Author Threats.** List external risks — competitive moves, macro shifts, regulatory tightening, substitute emergence — that could erode position if unaddressed. Assign a rough time horizon (near-term / medium-term) to each.
6. **Synthesize strategic implications.** Derive SO (Strength–Opportunity) pairs, ST (Strength–Threat) pairs, WO (Weakness–Opportunity) pairs, and WT (Weakness–Threat) pairs. Name at least one pair per quadrant. From this synthesis, name:
   - **Adoption hypothesis**: how the most promising SO pair translates into a first-success event — the specific behavior that constitutes adoption. If no SO pair produces a credible first-success event, the situation has no clear adoption path; flag it as a strategic gap.
   - **Differentiation mechanism**: the Strength or SO pair that produces a defensible competitive position — name the mechanism specifically (network effect, proprietary data, switching cost, economies of scale). A SWOT without a named differentiation mechanism has no moat analysis.
7. **Resolve the artifact path** following the config-driven, two-branch elicitation procedure in `references/agentbundle-layout.md`. Surface the resolved path, then commit `swot-analysis.md` with frontmatter `type: swot-analysis`.

## Anti-patterns

- **SWOT as a consensus ritual.** A SWOT that says only what the room already agrees on is a performance, not analysis. Push the Weaknesses and Threats sections until they are uncomfortable.
- **Opportunities without evidence.** Every Opportunity cell should name its source — a macro trend, a research finding, a competitive gap. "There is an opportunity for AI" is not an Opportunity entry.
- **Treating SWOT as a decision.** SWOT maps the situation; `frame-intent` or `run-okr-cascade` turns it into a direction.
- **Vision-without-adoption-path.** A SWOT whose strategic implications section names a compelling direction but no first-success event has no adoption path. Without a named first-success event, the strategic direction is a vision statement, not a strategy.
- **Polished-but-choice-free.** A SWOT that names four quadrants of equal weight and draws no strategic implications has made no choices. The synthesis step exists to force a priority — which Strength-Opportunity pair matters most, which Threat is most urgent. A SWOT without forced priority is documentation, not strategy.

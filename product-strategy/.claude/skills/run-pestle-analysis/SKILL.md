---
name: run-pestle-analysis
description: Use when a strategist needs to scan the macro environment before setting strategy or evaluating a market entry decision. Triggers on "run a PESTLE", "I need to understand the macro environment before setting strategy", "what external forces are moving in our market", "political economic social scan for our industry", "what macro trends should we factor into this decision". Produces a committed macro-environment artifact. Do NOT use as a substitute for current intelligence — PESTLE organizes and prioritizes information you supply; it does not generate market research.
---

# Skill: run-pestle-analysis

Produces a **macro-environment analysis** using the PESTLE framework — Political, Economic, Social, Technological, Legal, and Environmental dimensions. PESTLE is a structured scan; it surfaces which macro forces are most material to the strategic context and in what time horizon. See `references/agentbundle-layout.md` for artifact path.

## Output rendering

Table — When presenting several items that share the same fields, render a Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail list. Right-align numeric columns.

## When to invoke

1. **A scope is defined** — geography, industry, and time horizon must be named before the scan begins. A global PESTLE for an indeterminate horizon is not useful.
2. **You are upstream of a market or strategic decision** — PESTLE informs positioning, entry, and risk assessment; it is not an operational tool.
3. **No current PESTLE exists for this scope** — amend rather than duplicate.

## Procedure

1. **Establish scope.** Name the geography (country, region, or global), the industry, and the time horizon (near-term: 0–18 months; medium-term: 18 months–3 years; long-term: 3+ years). These anchors determine what is material for each dimension.
2. **Assess Political.** Government stability, policy direction, trade agreements, tariffs, political risk. Name at least one current policy or regulatory signal that affects this industry and geography.
3. **Assess Economic.** GDP trajectory, inflation, interest rates, consumer confidence, exchange rates, labor market tightness. Name at least one macroeconomic indicator that is currently moving and its directional impact.
4. **Assess Social.** Demographic shifts, consumer behavior trends, cultural values, education and workforce composition. Identify at least one social trend that creates a strategic opportunity or risk.
5. **Assess Technological.** Technology adoption curves, emerging platforms, automation, digital infrastructure, R&D investment trends. Name the technology that poses the greatest disruption risk or opportunity in the time horizon.
6. **Assess Legal.** Regulation, compliance requirements, IP environment, data protection laws, antitrust considerations. Flag any pending regulatory change that could alter the competitive landscape.
7. **Assess Environmental.** Climate regulation, ESG expectations, resource scarcity, supply-chain environmental risk, physical climate exposure. Rate materiality to the business model.
8. **Prioritize by impact and time horizon.** From the six dimensions, identify the top two or three forces by strategic materiality. For each, assign a time horizon tag (near-term / medium-term / long-term) and a directional impact (tailwind / headwind / neutral). These priorities feed into SWOT Opportunities/Threats and OKR cascade context.
9. **Resolve the artifact path** following `references/agentbundle-layout.md`. Surface the path, then commit `macro-environment.md` with frontmatter `type: macro-environment`.

## Anti-patterns

- **PESTLE as a forecast.** Each dimension describes observable forces, not predictions. Flag uncertainty rather than stating projections as fact.
- **Shallow dimension entries.** Each dimension needs at least one named, concrete signal — a law, a rate, a trend. "Social factors may affect us" is not an assessment.
- **Missing prioritization.** A PESTLE with six equally-weighted dimensions gives strategy nothing to act on. The step-8 prioritization is the deliverable, not the scan.
- **Macro analysis as moat claim.** Identifying a macro tailwind (e.g., "AI adoption is growing") does not constitute a competitive moat. A PESTLE entry that names a favorable trend but does not name the mechanism by which this specific organization captures it preferentially — while competitors do not — is incomplete. The moat mechanism belongs in SWOT; PESTLE names the force.

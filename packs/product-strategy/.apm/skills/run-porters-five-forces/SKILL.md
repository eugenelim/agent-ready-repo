---
name: run-porters-five-forces
description: Use when a strategist needs to understand the competitive dynamics of an industry before setting market positioning or evaluating entry. Triggers on "run Porter's Five Forces", "I need to understand how competitive this industry is before we enter", "map the competitive structure of our market", "how much leverage do our buyers and suppliers have", "what structural forces determine who wins in this industry". Produces a committed competitive-landscape artifact. Do NOT use for individual competitor profiling — this is an industry-structure analysis, not a competitor teardown.
---

# Skill: run-porters-five-forces

Produces a **competitive landscape analysis** using Porter's Five Forces framework — the structural forces that determine industry attractiveness and competitive pressure. The five forces are: Supplier Power, Buyer Power, Threat of New Entrants, Threat of Substitutes, and Competitive Rivalry. References Porter's framework by name; see `references/agentbundle-layout.md` for artifact path.

## When to invoke

1. **An industry boundary is nameable** — the analysis requires a defined market (e.g., "B2B HR software", "direct-to-consumer meal kits"); without it, the forces cannot be assessed.
2. **You are evaluating market entry or repositioning** — Five Forces is an entry/positioning tool, not an operational one.
3. **No current Five Forces analysis exists for this industry** — amend rather than duplicate.

## Procedure

1. **Establish the industry boundary.** Name the industry, the geographic scope, and the time horizon. A market that is too broad (e.g., "software") produces meaningless force ratings; one that is too narrow misses the actual competitive dynamics.
2. **Assess Supplier Power.** Who supplies the critical inputs (technology, talent, data, components)? Rate concentration, switching cost, and supplier ability to forward-integrate. Elicit at least one concrete example.
3. **Assess Buyer Power.** Who buys and how much leverage do they have? Rate buyer concentration, price sensitivity, standardization of the offering, and backward-integration threat.
4. **Assess Threat of New Entrants.** What barriers protect the incumbents? Rate capital requirements, economies of scale, regulation, switching costs, and brand loyalty. Name the most credible near-term entrant type.
5. **Assess Threat of Substitutes.** What alternative solutions — not direct competitors, but different approaches to the same job — could attract buyers away? Rate switching cost to the substitute and the performance trajectory of the substitute.
6. **Assess Competitive Rivalry.** How intense is competition among existing players? Rate concentration, market growth rate, product differentiation, and exit barriers.
7. **Synthesize industry attractiveness.** Rate overall industry attractiveness (high / medium / low) from the force profile. Name the one or two forces that most determine strategic position, and derive the top strategic implication for market entry or repositioning.
8. **Resolve the artifact path** following `references/agentbundle-layout.md`. Surface the path, then commit `competitive-landscape.md` with frontmatter `type: competitive-landscape`.

## Anti-patterns

- **Individual competitor profiling in a Forces analysis.** Rivalry assessment names the competitive dynamic, not a competitor teardown; detailed competitor profiles are separate artifacts.
- **Force ratings without evidence.** Each force requires at least one observable fact — a named supplier, a measured churn rate, a regulatory threshold. "High rivalry because the market is competitive" is circular.
- **Static analysis in dynamic markets.** Label the time horizon and flag forces that are likely to shift. A Five Forces snapshot taken today may be wrong in 18 months.
- **Force profile without moat derivation.** Rating the five forces produces an industry portrait, not a competitive position. A Five Forces analysis that ends with "rivalry is high and buyers have moderate power" but does not name the structural mechanism that protects this specific player — the barrier to entry they can exploit, the switching cost they can create, the supplier relationship they can lock — has mapped the battlefield but named no position. The strategic implication must name a mechanism.

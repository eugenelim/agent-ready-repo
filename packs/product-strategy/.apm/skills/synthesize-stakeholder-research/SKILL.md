---
name: synthesize-stakeholder-research
description: Use when a strategist needs to turn existing stakeholder research into a strategic narrative organized by theme. Triggers on "synthesize stakeholder research", "I need to turn research into strategic direction", "what does the research tell us strategically", "consolidate stakeholder perspectives", "research synthesis for strategy". Requires existing research inputs — surfaces a diagnostic when none are found. Do NOT use to conduct research — this skill synthesizes; it does not interview, survey, or produce primary research.
---

# Skill: synthesize-stakeholder-research

Produces a **stakeholder synthesis** — a strategic narrative that organizes stakeholder perspectives (executive, user, regulator, partner) by theme, not by stakeholder group, to surface the strategic signals that cross-cut viewpoints. Consumes desk-research pack outputs; does not produce primary research. See `references/agentbundle-layout.md` for artifact path.

## When to invoke

1. **Research inputs exist.** Check `docs/research/` or adopter-supplied paths for desk-research project outputs (research briefs, synthesis memos, interview summaries). If none are found, surface: `"run desk-research project first — no research inputs found"` and stop.
2. **You need strategic direction, not a research report.** The output is organized by theme, not by stakeholder — if the user wants a stakeholder-by-stakeholder summary, that is a different artifact.
3. **No current synthesis exists for this research body** — amend rather than duplicate.

## Procedure

1. **Discover research inputs.** Check `docs/research/` and any adopter-supplied paths for desk-research outputs. If none are found, surface: `"run desk-research project first — no research inputs found"` and do not proceed. If inputs are found, list them and confirm they cover the scope the strategist needs.
2. **Identify stakeholder groups represented.** From the research inputs, name the stakeholder groups with material representation (e.g., executive, end-user, regulator, partner, channel). Flag any group the strategist expected but that has no research coverage — that is a gap.
3. **Extract raw themes per group.** For each research input, extract the top three to five strategic signals the group expressed: what they want, what they fear, what they judge success by, what trade-offs they would accept.
4. **Cross-map for convergent signals.** Find themes that appear across two or more stakeholder groups — these are the highest-confidence strategic signals. Name each convergent signal explicitly ("Both executives and regulators prioritize X").
5. **Author the synthesis narrative.** Organize by strategic theme, not by stakeholder. Each section: (a) theme name; (b) which stakeholder groups hold this view and with what intensity; (c) strategic implication — what the organization must do or decide in response. Use direct, non-hedged language.
6. **Resolve the artifact path** following `references/agentbundle-layout.md`. Surface the path, then commit `stakeholder-synthesis.md` with frontmatter `type: stakeholder-synthesis`.

## Anti-patterns

- **Conducting research in this skill.** `synthesize-stakeholder-research` does not write interview guides, run surveys, or produce raw research artifacts — that is the desk-research pack's domain. If no research exists, surface the diagnostic and redirect.
- **Organizing by stakeholder instead of by theme.** A section per stakeholder group reproduces the research structure; a section per theme produces the strategic signal. The synthesis step is the transformation.
- **Treating all themes equally.** Cross-stakeholder convergence is the signal-strength indicator — themes held by one group are inputs; themes held by three groups are strategic imperatives.

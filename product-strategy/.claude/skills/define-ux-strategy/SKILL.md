---
name: define-ux-strategy
description: Use when a strategist needs to set the experience direction before design begins — the bridge between business goals and what the designed product must achieve. Triggers on "define the UX strategy", "I need to set the experience strategy before design", "what should our UX strategy be", "align design to business goals", "set the experience vision". Produces a committed ux-strategy.md. Do NOT use to produce a customer journey map — that belongs to journey-mapping in the experience-design pack.
---

# Skill: define-ux-strategy

Produces a **UX strategy** — a three-layer document (Vision, Goals + Measures, Plan) that bridges business strategy and experience design. Draws on the NN/g three-layer UX strategy model, Jaime Levy's four-tenets framework (business strategy + value innovation + validated user research + killer UX), and Gothelf/Seiden OKR-linked UX framing. Sits upstream of the experience-design pack's `journey-mapping`. See `references/agentbundle-layout.md` for artifact path.

## When to invoke

1. **Market strategy and business goals are known** — UX strategy translates those goals into experience direction; it cannot precede the business strategy it is derived from.
2. **Design has not yet begun** — UX strategy is set before journey mapping and screen design, not after.
3. **No current UX strategy exists for this product** — amend rather than duplicate.

## Procedure

1. **Establish the Vision layer.** Ask: "What should the end-to-end experience achieve? What is the qualitative state the customer reaches?" This is the aspirational statement — specific enough to be falsifiable but not yet a metric. Align it to the market strategy: name which competitive differentiation this experience must deliver. Cross-reference SWOT, Porter's Five Forces, or PESTLE artifacts if available.
2. **Apply the Levy four-tenets quality check.** Rate each tenet for current strength: (a) Is the business strategy coherent and the market opportunity validated? (b) Is there a genuine value innovation — something the experience does that competitors do not or cannot? (c) Is the user research validated — observational or behavioral, not assumed? (d) Does the product vision include what "killer UX" looks like for this customer? Flag any tenet where the current strength is weak — these are the gaps the UX strategy must address.
3. **Define Goals and Measures.** For each Vision statement, derive two to four measurable UX goals — the signals that tell you the vision is being realized. Apply Gothelf/Seiden OKR-linked UX framing: each goal should be a UX-level Objective with Key Results that measure the experience, not features shipped. Distinguish leading indicators (engagement, task-completion rate) from lagging indicators (NPS, retention).
4. **Author the Plan layer.** Name the initiatives the design work must deliver to close the gap between the current experience and the Vision. Sequence them by dependency and time horizon. Each initiative maps to at least one Goals + Measures KR. This is the handoff to `journey-mapping` — the plan names what the journey map must achieve, not how it achieves it.
5. **Document the upstream/downstream position.** Note: "This UX strategy is upstream of `journey-mapping` (experience-design pack). The plan layer drives the first `journey-mapping` invocation." List which SWOT/OKR/PRFAQ artifacts informed the vision.
6. **Resolve the artifact path** following `references/agentbundle-layout.md`. Surface the path, then commit `ux-strategy.md` with frontmatter `type: ux-strategy`.

## Anti-patterns

- **UX strategy as a journey map.** The strategy names what the experience must achieve; the journey map (in the experience-design pack) shows how customers currently move through it and where the gaps are. These are sequential, not synonymous.
- **Goals without measures.** A goal without a Key Result is a wish. Every Goal + Measure entry needs a metric and a target — even a directional one ("reduce task abandonment from current baseline").
- **Skipping the Levy tenet check.** The four-tenets check surfaces the weakest link in the UX strategy before it propagates into design. Skipping it produces a polished document with a hidden fatal flaw.

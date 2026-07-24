---
name: tone-of-voice
description: Use when a designer, copywriter, or builder has a felt "copy vibe" but no named direction — turning a vague register sense into ranked copy goals grounded in stable referents (persona language, copy precedents, persuasion standards), and recording copy arbitration rules the rest of the build references. Triggers on "what voice should our copy have", "write a tone-of-voice doc", "what is our brand register", "how should our brand sound across channels", "copy vibe check". Do NOT use for product UI copy states (error messages, empty states, button labels, form labels) — use `ux-writing` in the `product-engineering` pack for those. Do NOT use for SEO keyword targeting, advertising copy templates, or brand identity documentation. Do NOT use if you need copy direction for a specific marketing or acquisition surface (landing page, above-fold hero, announcement) — use `copy-direction` for that surface-specific scope.
---

# Skill: tone-of-voice

Turns a vague "copy vibe" into a small set of **named, ranked copy goals**, each grounded in a stable referent, and records them — along with arbitration rules — in a tone-of-voice doc the rest of the build references. The doc is the durable artifact: every later copy choice points back to a goal and its referent rather than relitigating voice on each surface. This skill is the copy twin of `creative-direction`: same interrogation rhythm applied to what the product *says* rather than how it *looks*.

## When to invoke

Confirm all four before drafting; if any fails, push back and resolve it first.

1. **There is a real copy vibe to name** — the user can describe a register, an audience, or examples to react to. A blank "make it sound good" is not yet a brief; draw out a first felt word before proceeding.
2. **The direction isn't already named** — no current tone-of-voice doc owns this surface. If one exists, you are amending it, not starting fresh.
3. **You are naming direction, not writing final copy** — the moment the ask is "write the headline," this skill has done its job. Hand off: `ux-writing` for product UI strings; `content-design` output as upstream structural context.
4. **You know the target surface or can elicit it** — marketing/acquisition copy, above-fold narrative, onboarding copy voice, taglines, announcement copy. If absent, elicit before grounding the goals; surface type is a referent for every goal.

## Procedure

1. **Map the audience.** Name each distinct reader type for this surface, write one copy JTBD sentence per type ("When {situation}, I want to {action}, so that {goal}"), and rank them (primary, secondary). Load `references/copy-jtbd.md`. Feed the ranked map into Step 2 — the copy vibe that emerges should serve the primary reader's language and frame of reference. Record the map in the doc; it becomes the Persona referent for each named copy goal in Step 3.

2. **Run the interrogation.** Open from the felt copy vibe, probe the register, associations, and brand attributes behind it, and converge on a short set of named copy goals — each a noun phrase a non-designer can recall. Sharpen each against its opposite: a goal you cannot violate is a platitude. Load `references/interrogation-sequence.md`.

3. **Ground each goal in stable referents.** Take VoC (Voice of Customer) findings as optional input: if VoC data is provided — support tickets, sales call transcripts, community posts — cite the audience's own vocabulary as the primary grounding for each goal. If VoC is absent, elicit inline: "What words does your audience use when they describe this problem?" Flag the resulting goals as **"directional — not backed by VoC research"** so downstream copy knows these are a sketch, not a validated direction. For each named goal, cite at least one stable referent: persona language, a copy precedent (a named example — named as a quality anchor, never reprinted as a formula), or a persuasion standard (painkiller-first framing, tweet test, five-second evaluator scan). Load `references/copy-grounding.md`.

4. **Rank the goals.** Order them so a tie can break. Name the dominant goal — the one that wins when two copy goals conflict on a real choice. Force a strict order; no ties at the top.

5. **Record arbitration.** For each likely conflict, name which goal wins and why — so the build does not relitigate it. Common conflict types: urgency vs. warmth, brevity vs. completeness, authority vs. approachability, specificity vs. universality. Load `references/copy-arbitration.md`.

6. **Capture the doc.** Resolve the output path via `references/agentbundle-layout.md` (the `[design]` section). Write to `<output_dir>/copy/<slug>.md` with frontmatter `type: tone-of-voice`. Copy `assets/tone-of-voice-template.md` to that path. Fill: reader map (reader types, JTBD sentences, rank), named copy goals (each with what it means, what would violate it, and its referents), dominant goal, copy arbitration rules, plain-language floor notes, and open questions.

7. **Hold the plain-language floor.** Verify the direction against three checks before closing: no jargon the reader did not bring to this surface, no idioms that do not translate across the likely reader population, and no assumptions about who the reader is (identity, background, level of familiarity). If a named goal pulls against the floor, record it as an open question — the floor is not a trade-off. Load `references/plain-language-floor.md` for the governing standards and the three specific checks.

8. **Hand off.** Name `ux-writing` (in the `product-engineering` pack) as the downstream skill for per-surface product UI copy states. Name `content-design` output as upstream structural context — if a content brief exists for this surface, the tone-of-voice goals must be consistent with the brief's section jobs and narrative arc. Note: experience-reviewer scope extension to include tone-of-voice docs as a reviewable artifact type is deferred to a follow-on RFC (RFC-0062 OQ1).

## Anti-patterns to refuse

- **Goals without referents.** A copy goal grounded in nothing but the team's preference is still a fresh opinion. Refuse to record a goal until it has at least one stable referent — persona language, a copy precedent, or a persuasion standard.
- **Unranked goals.** A flat list of equal goals cannot break a tie. Refuse to close without a dominant goal.
- **Reprinting copy precedents as templates.** "Write copy like Stripe's headline" is a starting probe, not a direction. Name which qualities of the example you are after — the brevity, the claim structure, the absence of jargon — and use those as the grounded referent. Never quote the headline and tell the writer to match it.
- **Producing SEO content, advertising copy templates, or brand identity documentation.** This skill names copy direction for marketing/acquisition copy voice and positioned copy. SEO keyword targeting is explicitly deferred per RFC-0062 D5. Advertising copy templates and full brand identity specs are wider than this skill's scope; push back and redirect.
- **Producing copy strings.** This skill produces direction — named goals, referents, arbitration rules — not finished copy. If the output contains a written headline, tagline, or marketing copy string, it has overstepped.
- **Re-deriving copy direction mid-build.** Once the doc exists, copy conflicts resolve against it rather than against fresh opinion. Amend the doc deliberately; do not quietly drift.

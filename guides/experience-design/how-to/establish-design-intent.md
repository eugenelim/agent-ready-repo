---
title: Establish design intent
summary: Derive durable principles, an aesthetic direction, and a token taxonomy before screen craft begins.
pack: experience-design
kind: how-to
order: 3
---

# Establish design intent

**Step 3 of 5 — Establish design intent**
<!-- rung: JOURNEY stage 3 -->

**What changes:** Journey evidence becomes decision rules, a grounded aesthetic direction, and a token taxonomy that constrain screen work.
<!-- rung: JOURNEY stage 3 -->

**What you need first:** Journey pains and peak moments, the target surface, and any stable persona, precedent, brand, or platform referents.
<!-- rung: design-principles and creative-direction SKILL.md -->

*Skipping costs:* Screen choices become local preferences with no shared way to resolve conflicts.
<!-- rung: JOURNEY stage 3 -->

**Concepts:**
<!-- rung: authored -->

- [The experience thread](../explanation/the-experience-thread.md) explains how principles, direction, and tokens constrain screen craft.

#### Run `design-principles`

**You type:** `Turn these journey pains and peak moments into three to five design principles.`
<!-- rung: design-principles SKILL.md -->

**Agent returns:**
<!-- rung: design-principles SKILL.md -->

> **Agent:** Named, ranked decision rules with rationale, arbitration tests, and known trade-offs.

**You push back:**
<!-- rung: design-principles SKILL.md -->

> “ ‘Be trustworthy’ is a brand value, not a rule that distinguishes two screen choices. Derive a testable principle from the setup failure moment.” The agent replaces it with a product-specific rule and an opposing case.

**Output varies** with the journey’s peak moments, highest-opportunity pains, and recurring disputes.
<!-- rung: design-principles SKILL.md -->

**No decision gate at this step.**
<!-- rung: JOURNEY stage 3 -->

**Check (testable):** Apply each principle to two plausible screen choices; this surfaces slogans and universal heuristics that cannot decide between them.
<!-- rung: design-principles SKILL.md -->

**Watch out for:** A polished principle set may be generic everywhere. Notice brand values, copied heuristics, or more than five rules; replace them with a smaller ranked set grounded in this journey.
<!-- rung: design-principles SKILL.md -->

**Where it lands:** `docs/design/principles/<slug>.md`, with `<slug>` replaced for this product.
<!-- rung: design-principles SKILL.md -->

**Expect these headings:**
<!-- rung: design-principles SKILL.md -->

- One heading for each `<Principle title>`
- `Known tradeoffs`

#### Run `creative-direction`

**You type:** `Set a visual direction for this surface from its audience, persona, precedents, and platform conventions.`
<!-- rung: JOURNEY stage 3 -->

**Agent returns:**
<!-- rung: JOURNEY stage 3 -->

> **Agent:** A named, ranked aesthetic direction grounded in stable referents.

**You push back:**
<!-- rung: creative-direction SKILL.md -->

> “ ‘Clean and modern’ could describe any product. Ground each goal in a named audience need or precedent quality, rank them, and say what you are not borrowing.” The agent replaces the generic direction with specific, bounded goals.

**Output varies** with the audience, referents, target surface, and genre.
<!-- rung: creative-direction SKILL.md -->

**You decide:** Approve a specific aesthetic direction before screen design begins.
<!-- rung: JOURNEY stage 3 -->

**Check (grounded):** Ask what persona, precedent quality, standard, or platform convention supports each goal; this surfaces fresh opinion presented as direction.
<!-- rung: creative-direction SKILL.md -->

**Watch out for:** Confident aesthetic language can conceal guesses. Notice goals with no referent and lines borrowed from a general genre pattern; argue with those first, and reject any direction that conflicts with the quality floor.
<!-- rung: creative-direction SKILL.md -->

**Where it lands:** `<output_dir>/aesthetic/<slug>.md`, with both bracketed segments replaced for this project.
<!-- rung: authored; creative-direction SKILL.md declares the record but not its path -->

**Expect these headings:**
<!-- rung: packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md -->

- `Aesthetic direction: <surface or product name>`
- `Surface`
- `Named goals (ranked)`
- `What each goal means`
- `Dominant goal for arbitration`
- `Open questions`

#### Run `design-system`

**You type:** `Derive the semantic token and scale taxonomy from the approved aesthetic direction.`
<!-- rung: JOURNEY stage 3 -->

**Agent returns:**
<!-- rung: JOURNEY stage 3 -->

> **Agent:** A semantic token and scale taxonomy whose roles trace to the approved direction.

**You push back:**
<!-- rung: design-system SKILL.md -->

> “The accent color appears as an isolated value with no semantic role. Replace it with a role derived from the direction, and keep implementation values out of this taxonomy.” The agent repairs the role and its rationale.

**Output varies** with the direction’s named goals, surface needs, and accessibility constraints.
<!-- rung: design-system SKILL.md -->

**You decide:** Approve the direction and token taxonomy before screens are designed.
<!-- rung: JOURNEY stage 3 -->

**Check (grounded):** Ask which named aesthetic goal explains each token role; this surfaces arbitrary values and roles imported from a generic system.
<!-- rung: design-system SKILL.md -->

**Watch out for:** A complete-looking taxonomy may contain roles projected from general design-system patterns. Notice any role with no direction rationale or accessibility constraint; challenge those lines first and remove unsupported tokens.
<!-- rung: design-system SKILL.md -->

**Where it lands:** `<output_dir>/aesthetic/<slug>-tokens.md`, with both bracketed segments replaced for this project.
<!-- rung: authored; design-system SKILL.md declares the taxonomy but not its path -->

**Expect these headings:**
<!-- rung: design-system SKILL.md -->

- `Token taxonomy`
- `Semantic roles`
- `Scale rationale`
- `Accessibility constraints`
- `Composition rules`

**Next:** [Design each screen](design-each-screen.md).
<!-- rung: authored -->

**Go deeper:** `packs/experience-design/.apm/skills/creative-direction/SKILL.md`
<!-- rung: authored -->

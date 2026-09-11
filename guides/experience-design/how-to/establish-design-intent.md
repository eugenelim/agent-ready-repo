---
title: Establish design intent
summary: Derive durable principles, an aesthetic direction, and a token taxonomy before screen craft begins.
pack: experience-design
kind: how-to
order: 3
---

# Establish design intent

**Step 3 of 5 — Establish design intent**

Set the decision rules and visual constraints that guide all screen work.

**You need:** journey insights and a surface or product to direct.

*Skipping costs:* later screen choices become local preferences rather than shared decisions.

**Concepts:**

- [The experience thread](../explanation/the-experience-thread.md) explains how principles, direction, and tokens constrain screen craft.

#### Run `design-principles`

**You type:** `Turn these journey pains into design principles.`
<!-- rung: SKILL.md description -->

**Agent returns:**

> **Agent:** three to five named principles with rationale and arbitration tests.
<!-- rung: SKILL.md -->

**Output varies** with the journey’s peak moments and opportunity pains.
<!-- rung: authored -->

**You decide:** whether the principles can resolve the recurring screen decisions in this product.
<!-- rung: authored -->

**Check (testable):** Can each principle distinguish between two plausible screen choices?
<!-- rung: authored -->

**If it fails:** bring a concrete disputed choice and re-prompt for a sharper principle.
<!-- rung: authored -->

**You now hold:** `docs/design/principles/<slug>.md`.
<!-- rung: SKILL.md -->

**Expect these headings:**

- `<Principle title>`
- `Known tradeoffs`

*Source:* `authored`
<!-- rung: SKILL.md describes the document shape; no asset template exists -->

#### Run `creative-direction`

**You type:** `creative-direction` — describe the visual direction in persona, precedent, and platform terms.
<!-- rung: JOURNEY stage 3 -->

**Agent returns:**

> **Agent:** a named aesthetic direction grounded in referents and ready for token derivation.
<!-- rung: JOURNEY stage 3, separately attributed from your request -->

**Output varies** with the audience, referents, and target surface.
<!-- rung: authored -->

**You decide:** approve a specific direction; a generic description is not enough.
<!-- rung: JOURNEY stage 3 -->

**Check (grounded):** Does every named goal cite a persona, precedent, standard, or platform convention?
<!-- rung: authored -->

**If it fails:** replace the unsupported goal with a named referent and re-prompt.
<!-- rung: authored -->

**You now hold:** `<output_dir>/aesthetic/<slug>.md`.
<!-- rung: authored; SKILL.md specifies the record but not its output path -->

**Expect these headings:**

- `Aesthetic direction: <surface or product name>`
- `Surface`
- `Named goals (ranked)`
- `What each goal means`
- `Dominant goal for arbitration`
- `Open questions`

*Source:* `../../../packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md`
<!-- rung: asset template -->

#### Run `design-system`

**You type:** `design-system` — derive the token taxonomy from this approved direction.
<!-- rung: JOURNEY stage 3 -->

**Agent returns:**

> **Agent:** a semantic token and scale taxonomy derived from the aesthetic direction.
<!-- rung: JOURNEY stage 3, separately attributed from your request -->

**Output varies** with the direction’s named goals and the surface’s needs.
<!-- rung: authored -->

**You decide:** approve the direction and resulting token taxonomy before screens are designed.
<!-- rung: JOURNEY stage 3 -->

**Check (grounded):** Can each token role be explained by a named aesthetic goal rather than its present appearance?
<!-- rung: authored -->

**If it fails:** name the ungrounded role or goal and re-prompt for the missing rationale.
<!-- rung: authored -->

**You now hold:** `<output_dir>/aesthetic/<slug>-tokens.md`.
<!-- rung: authored; SKILL.md specifies the taxonomy but not its output path -->

**Expect these headings:**

- `Token taxonomy`
- `Semantic roles`
- `Scale rationale`
- `Accessibility constraints`
- `Composition rules`

*Source:* `authored`
<!-- rung: SKILL.md specifies a taxonomy and rationale; no asset template exists -->

**Next:** [design each screen](design-each-screen.md).
<!-- rung: authored -->

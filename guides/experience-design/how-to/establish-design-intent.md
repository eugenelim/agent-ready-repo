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

**You type:** `Turn these journey pains into design principles.` *(Rung: SKILL.md description.)*

**Agent returns:**

> **Agent:** three to five named principles with rationale and arbitration tests. *(Rung: SKILL.md.)*

**Output varies** with the journey’s peak moments and opportunity pains. *(Rung: authored.)*

**You decide:** whether the principles can resolve the recurring screen decisions in this product. *(Rung: authored.)*

**Check (testable):** Can each principle distinguish between two plausible screen choices? *(Rung: authored.)*

**If it fails:** bring a concrete disputed choice and re-prompt for a sharper principle. *(Rung: authored.)*

**You now hold:** `docs/design/principles/<slug>.md`. *(Rung: SKILL.md.)*

**Expect these headings:**

- `<Principle title>`
- `Known tradeoffs`

*Source:* `authored` *(Rung: SKILL.md describes the document shape; no asset template exists.)*

#### Run `creative-direction`

**You type:** `creative-direction` — describe the visual direction in persona, precedent, and platform terms. *(Rung: JOURNEY stage 3.)*

**Agent returns:**

> **Agent:** a named aesthetic direction grounded in referents and ready for token derivation. *(Rung: JOURNEY stage 3, separately attributed from your request.)*

**Output varies** with the audience, referents, and target surface. *(Rung: authored.)*

**You decide:** approve a specific direction; a generic description is not enough. *(Rung: JOURNEY stage 3.)*

**Check (grounded):** Does every named goal cite a persona, precedent, standard, or platform convention? *(Rung: authored.)*

**If it fails:** replace the unsupported goal with a named referent and re-prompt. *(Rung: authored.)*

**You now hold:** `<output_dir>/aesthetic/<slug>.md`. *(Rung: authored; SKILL.md specifies the record but not its output path.)*

**Expect these headings:**

- `Aesthetic direction: <surface or product name>`
- `Surface`
- `Named goals (ranked)`
- `What each goal means`
- `Dominant goal for arbitration`
- `Open questions`

*Source:* `../../../packs/experience-design/.apm/skills/creative-direction/assets/creative-direction-template.md` *(Rung: asset template.)*

#### Run `design-system`

**You type:** `design-system` — derive the token taxonomy from this approved direction. *(Rung: JOURNEY stage 3.)*

**Agent returns:**

> **Agent:** a semantic token and scale taxonomy derived from the aesthetic direction. *(Rung: JOURNEY stage 3, separately attributed from your request.)*

**Output varies** with the direction’s named goals and the surface’s needs. *(Rung: authored.)*

**You decide:** approve the direction and resulting token taxonomy before screens are designed. *(Rung: JOURNEY stage 3.)*

**Check (grounded):** Can each token role be explained by a named aesthetic goal rather than its present appearance? *(Rung: authored.)*

**If it fails:** name the ungrounded role or goal and re-prompt for the missing rationale. *(Rung: authored.)*

**You now hold:** `<output_dir>/aesthetic/<slug>-tokens.md`. *(Rung: authored; SKILL.md specifies the taxonomy but not its output path.)*

**Expect these headings:**

- `Token taxonomy`
- `Semantic roles`
- `Scale rationale`
- `Accessibility constraints`
- `Composition rules`

*Source:* `authored` *(Rung: SKILL.md specifies a taxonomy and rationale; no asset template exists.)*

**Next:** [design each screen](design-each-screen.md). *(Rung: authored.)*

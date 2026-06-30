---
name: map-customer-journey
description: Use when a product team needs to understand how a customer moves through an experience end-to-end — mapping the stages, actions, emotions, pains, and opportunities along the path. Triggers on "map the customer journey", "what does the user go through", "journey map this flow", "map out the experience stages", "what are the customer touchpoints", "where does the user feel pain". Carries a platform/surface axis (responsive-web, iOS, Android, cross-platform) that changes what the method asks at each stage. Scoped to customer/end-user journeys only — employee journeys are out of v1. Do NOT use to design screen interactions (use `map-screen-flow`), to blueprint the backing services (use `blueprint-service`), or to map an internal business process (use `map-internal-process`).
---

# Skill: map-customer-journey

Produces a **customer/end-user journey map** — the stages a customer moves through, the actions they take, the emotions they feel, the pains they encounter, and the opportunities those pains reveal. The map is **outside-in and frontstage**: it describes what the customer experiences, not what happens behind the scenes. The method draws on NN/g journey mapping, Patton user-story mapping, and Torres opportunity-solution tree thinking; see `references/journey-mapping.md`.

**Inputs:** a persona (or role description) and an outcome the customer is trying to achieve. Both are elicited inline when absent — this skill is standalone-useful without upstream research artifacts. **Consumed by:** `map-screen-flow` (derives the screen sequence and per-screen briefs from the journey stages) and `blueprint-service` (maps the frontstage actions to backstage services). When `architect` or `contracts` are not installed, downstream services are named textually rather than by package reference.

## When to invoke

Confirm all four before drafting; if any fails, resolve it first.

1. **There is a customer goal to map** — name the outcome the customer is trying to achieve. If the team has no sense of who the customer is or what they want, elicit persona + outcome inline before proceeding.
2. **The scope is frontstage and outside-in** — employee process flows belong to `map-internal-process`; backstage service wiring belongs to `blueprint-service`. Route those separately.
3. **You know the surface** — confirm `surface` before drafting: `responsive-web | iOS | Android | cross-platform`. Surface changes what the method asks at key stages; see step 1 below.
4. **No current journey map exists for this outcome and surface** — if one exists, you are amending it, not starting fresh. Check for an existing artifact at the path resolved in step 4.

## Procedure

1. **Set the surface.** Confirm the target surface (`responsive-web | iOS | Android | cross-platform`). Note the platform-specific conventions the journey must honor — context-switching patterns on iOS, navigation conventions on Android, progressive-disclosure on responsive web, shared-intent-then-adapt on cross-platform. Consult `references/journey-mapping.md` § Platform/surface axis. Point to the relevant platform conventions; do not reprint their values.
2. **Elicit or confirm the persona and outcome.** If no persona artifact is present, ask: who is the customer, and what outcome are they trying to reach? Name a role and an outcome; you need both to anchor the stage boundaries and the emotion baseline. Load `references/journey-mapping.md` § Grounding the map. When you are eliciting this *with* stakeholders rather than from an existing artifact, run it as a **facilitated workshop** — anchor on a single persona, generate silently before discussing, and keep the room small; see `references/facilitation.md`.
3. **Scope the journey.** Name the start trigger (what initiates the journey) and the end state (what done looks like for the customer). Agree these before dividing the middle — wrong boundaries produce stages that don't serve the team's questions.
4. **Divide into stages.** Break the journey into three to six named stages (more implies finer work than a journey map is the right tool for — reach for Patton's user-story mapping for that). Each stage is a coarse phase of the customer's goal, not a screen or a step. Load `references/journey-mapping.md` § Stage construction.
5. **Populate each stage.** For each stage, capture four rows: **Actions** (what the customer does — frontstage only, in the customer's words), **Emotions** (how they feel — emotional arc across the journey, the key design input), **Pains** (friction, confusion, or gaps the customer encounters), **Opportunities** (what would change the experience if addressed). The pains-to-opportunities column is the primary output — it is where journey maps earn their keep. Load `references/journey-mapping.md` § The four rows.
6. **Resolve the path and surface it.** Resolve `<parent>` following the three-tier procedure in `references/agentbundle-layout.md`. Expand to a full absolute path, reject any `..` escape, and **surface the resolved path to the adopter before writing**. Write to `<parent>/journeys/<slug>.md`; create `journeys/` lazily on first write. Add frontmatter `type: customer-journey` to the output file.
7. **Check against the quality floor.** Verify the map does not hardwire a surface-specific interaction idiom into a stage — the platform axis changes the *questions*, not the output values. Confirm no reprinted breakpoints, HIG spacings, or Material values appear in the artifact.
8. **Hand off.** Surface which stages carry the highest-opportunity pains (the input `map-screen-flow` needs to sequence screens around) and name any backstage services implied by the actions (the input `blueprint-service` will expand). Point the user to `map-screen-flow` for the next step, or to `blueprint-service` if the service architecture question is more pressing.

## Anti-patterns to refuse

- **Mapping employee-side steps as customer stages.** A journey map is outside-in and frontstage. What happens inside the organisation or system is `map-internal-process`'s domain; what the customer sees and does at each stage is this skill's. If a stage is "the support team reviews the request," it belongs behind the line of visibility — in `blueprint-service`, not here.
- **Reprinting platform values.** The platform/surface axis changes what the journey questions are; it does not print HIG spacing, Material breakpoints, or responsive pixel values into the map. Point to the platform conventions; let the method derive how they shape the stages.
- **One stage per screen.** Stages are coarse phases — "discover," "onboard," "get value," "return." Screens come later, in `map-screen-flow`. A journey that has one stage per screen is not a journey map; it is a screen list that hasn't been sequenced yet.
- **Treating pains as blockers, not as input.** A pain on a journey map is an opportunity waiting to be framed — it is the primary reason the map exists. Don't resolve pains into design decisions here; hand them to `map-screen-flow` and Torres opportunity-solution thinking.
- **Starting without a persona and outcome.** A journey with no named customer and no stated outcome has no anchor for stage boundaries or emotion baseline. Elicit both before the first stage boundary lands.

---
name: design-system
description: "Use when an approved aesthetic direction exists and someone asks how to name and organize semantic tokens, spacing, type, or color scales. Produces a token taxonomy and rationale; it does not implement token values. Use `creative-direction` to establish the vibe, `information-architecture` for page hierarchy, and `design-review` to evaluate an existing surface. Product differentiation belongs to product strategy; framing a design-system initiative belongs to `frame-intent`; implementing tokens or components belongs to `frontend-engineering`."
---

# Skill: design-system

Produce a **token/scale taxonomy** and the rationale behind it, derived from a
named aesthetic direction. You ship the *method* to derive values and a
portable serialization shape — never a reprinted palette, spacing, or type
table. The reader produces the numbers.

## Output rendering

Rationale / narrative — Use short ## headings and 2–3 sentence paragraphs. Don't force narrative into a table.

## When to invoke

Before drafting, confirm:

1. **An aesthetic direction exists.** A taxonomy without named emotional/brand
   goals is arbitrary. If the direction isn't written down yet, route to
   `creative-direction` first.
2. **The ask is the system, not a screen.** If the user wants hierarchy,
   reading flow, or wayfinding for a specific surface, route to
   `information-architecture`.
3. **You're deriving, not reprinting.** You will hand back the method and a
   taxonomy *shape* the reader fills with values — not a values sheet.

## Procedure

1. **Restate the intent.** Pull the named goals from the aesthetic direction.
   Every token decision must trace back to one of them.
2. **Decide purpose before token.** For each thing the system needs, name what
   it is *for* (its semantic role) before anyone picks a value. See
   `references/token-taxonomy-derivation.md`.
3. **Name by semantic role, not literal appearance.** A token is named for the
   job it does, so its value can change without a rename. Method in
   `references/token-taxonomy-derivation.md`.
4. **Choose one ratio as the organizing concept.** Let a single ratio generate
   the steps of your spacing scale and your type scale. Express steps
   symbolically (step −1, base, step +1), never as numbers. Derivation in
   `references/token-taxonomy-derivation.md`.
5. **Set accessibility as the floor and budget contrast.** Every token clears
   the recognized standard (WCAG, at your context's conformance level — read
   the criteria from the source). Allocate a contrast budget across the
   screen rather than maxing every element. See the shared checklist at
   `../design-review/references/quality-floor.md`.
6. **Compose atomically.** Build the system bottom-up: primitive tokens →
   composed components → pages. Define once, reuse. Model in
   `references/atomic-composition.md`.
7. **Serialize portably.** Record the taxonomy in the W3C Design Tokens
   interchange shape so it travels across tools. Pointer in
   `references/token-taxonomy-derivation.md`.

## Anti-patterns to refuse

- **Reprinting a values table instead of deriving one.** A fixed palette,
  spacing scale, or type scale with numbers is the thing this pack refuses to
  ship. Hand back the method and a symbolic shape; the reader supplies values.
- **Naming tokens by appearance.** A token named for how it looks today locks
  the value into the name — rename hell the first time the direction shifts.
- **Picking values before purpose.** A number with no named role is a guess
  you'll relitigate. Decide what the token is *for* first.
- **Treating accessibility as a later pass.** The floor is a constraint on
  every token at derivation time, not a cleanup chore.
- **Designing pages instead of systems.** One-off screens don't compose and
  don't stay coherent as they grow. Build reusable elements.

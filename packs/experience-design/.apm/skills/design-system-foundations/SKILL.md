---
name: design-system-foundations
description: Use when a token taxonomy exists and the next step is applying it as a working token foundation. Triggers on "apply design token foundations", "set up our token implementation", "build the design token foundation for this project", "implement the token system", "create the light and dark themes", "set up semantic aliases for our components". Takes a derived token taxonomy (from `design-token-taxonomy`) and produces the working foundation — lightweight mode covers semantic color roles, typography, spacing, radius, focus styles, key statuses, responsive breakpoints, and core component tokens; full mode adds DTCG 2025.10-compatible token source, light/dark theme switching, semantic alias layer, and full component anatomy. Near-misses — do not use to derive the taxonomy (use `design-token-taxonomy`), name felt direction (use `creative-direction`), evaluate an existing surface (use `design-review`), or structure hierarchy and reading flow (use `information-architecture`).
---

# Skill: design-system-foundations

Take a named token taxonomy (produced by `design-token-taxonomy`) and set up
the **working token foundation** for a project. The taxonomy named what tokens
are *for*; this skill makes them *usable* — a foundation the team can build
components on and ship.

## When to invoke

Before drafting, confirm:

1. **A token taxonomy exists.** A foundation without a named taxonomy is
   arbitrary. If the taxonomy isn't derived yet, route to
   `design-token-taxonomy` first, then return here.
2. **The ask is the foundation, not the taxonomy.** If the user wants to name
   tokens by semantic role or derive the organizing ratio, that is the
   `design-token-taxonomy` skill.
3. **Pick a mode** — lightweight or full — based on the team's current need:
   lightweight is the shortest path to a working foundation the team can
   use; full mode is appropriate when the project needs DTCG-compatible token
   source, multi-theme switching, or full component anatomy.

## Lightweight mode

Lightweight mode delivers the shortest path to a working, usable foundation.
It covers eight elements:

1. **Semantic color roles.** Map the taxonomy's named roles to concrete values
   (primary, secondary, surface, on-surface, error, warning, success, info,
   disabled, overlay). Values come from the taxonomy's method — not from this
   skill.
2. **Typography.** Font family (body, heading, mono), type scale steps and
   weights, and line-height and letter-spacing rules by semantic level.
3. **Spacing scale.** The symbolic steps from the taxonomy (step −2 through
   step +4 at minimum) mapped to token names the team will actually use.
4. **Radius system.** A named set (none, sm, md, lg, full) calibrated to the
   product's aesthetic direction.
5. **Focus styles.** Keyboard focus indicator — outline color, width, offset —
   meeting the recognized accessibility standard (WCAG 2.4.11 at AA or AAA,
   depending on the project's declared conformance level).
6. **Key statuses.** Four-state status token set: success, warning, error,
   info. Each maps to a background, foreground, and border role.
7. **Responsive breakpoints.** Named breakpoints (e.g., sm / md / lg / xl)
   with the max-width or min-width boundaries appropriate to the surface type.
8. **Core component tokens.** Baseline token sets for the four most frequent
   components: button (default, hover, active, disabled, focus), input (idle,
   focus, error, disabled), card (surface, border, shadow), modal (overlay,
   surface, header, footer).

## Full mode

Full mode extends lightweight with four additional layers:

1. **DTCG 2025.10-compatible token source.** A token source file (JSON or YAML)
   conforming to the Design Tokens Community Group (DTCG) 2025.10 specification
   (W3C Community Group deliverable), where practical. Generated platform
   outputs (design tool variables, mobile platform tokens) are
   deferred to a follow-on step outside this skill.
2. **Light/dark theme switching.** Both a light theme and a dark theme defined
   as token overrides: each semantic role maps to distinct primitive values for
   each theme; no semantic name changes between themes.
3. **Semantic alias layer.** A three-tier alias chain: primitive tokens (raw
   values) → semantic tokens (role-based aliases into primitives) → component
   tokens (component-specific aliases into semantic tokens). No component reads
   a primitive directly.
4. **Full component anatomy.** Token sets for a full component library starting
   point: navigation (top bar, side nav, breadcrumb), form controls (checkbox,
   radio, select, toggle, textarea), data display (table, badge, tag, tooltip),
   feedback (toast, modal, dialog, empty state).

## Procedure

1. **Confirm the taxonomy input.** Identify the named aesthetic direction and
   the token taxonomy already derived from it. If either is absent, surface the
   gap and wait before proceeding.
2. **Agree the mode.** Confirm lightweight or full with the user before
   generating output.
3. **Produce the semantic color roles.** Map each role to a value from the
   taxonomy method — name the role and the value; state the accessibility claim
   for each foreground/background pair.
4. **Produce the typography tokens.** Name the font families, scale steps, and
   weight tokens. State the reading level each step is intended for.
5. **Produce the spacing tokens.** Name the spacing steps as token identifiers,
   mapping each symbolic step from the taxonomy to a name the team will use.
6. **Produce radius, focus, status, breakpoint, and component tokens.**
   Name each; state the accessibility claim for the focus style.
7. **Full mode only:** Produce the DTCG token source, the theme overrides, the
   alias layer, and the extended component anatomy.
8. **Hand off cleanly.** State what the team should do next: use these tokens as
   the foundation for component design (route to `interaction-design` for
   component state machines) or for screen layout (route to
   `information-architecture`).

## Boundaries

- **Taxonomy first.** This skill does not derive the taxonomy. It consumes one.
- **Method over values.** This skill names the token set and states the semantic
  purpose of each token. The values are supplied by the team from the taxonomy method.
- **No generated platform outputs in this skill.** DTCG-compatible source is the
  ceiling; Figma variables and platform-specific token export are deferred to a
  follow-on tool or step outside this skill.
- **No methodology changes to `design-token-taxonomy`.** This skill consumes the
  taxonomy; it does not alter how the taxonomy is derived.

## Anti-patterns to refuse

- **Skipping to the foundation without a taxonomy.** A foundation built without
  a named taxonomy has no principled basis — the values are guesses. Route to
  `design-token-taxonomy` first.
- **Reprinting the taxonomy method.** The taxonomy is already derived. This skill
  applies it; it does not re-derive it.
- **Producing Figma variables or platform exports.** These are deferred to a
  follow-on step.
- **Producing actual numeric values for the team.** The values come from applying
  the taxonomy method to the project context — this skill names the token roles
  and structure; the team fills the values.

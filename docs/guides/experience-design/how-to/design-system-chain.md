# How to: derive a token taxonomy and apply the design token foundation

This guide walks the two-step chain from aesthetic direction to working token foundation using the experience-design pack.

## The two-step chain

```
creative-direction  →  design-token-taxonomy  →  design-system-foundations
(named direction)      (token/scale taxonomy)     (working foundation)
```

Use `design-token-taxonomy` when the work is naming what tokens are *for* and deriving the organizing scales from the aesthetic direction.

Use `design-system-foundations` when a taxonomy already exists and the work is applying it as a working foundation — creating actual semantic token sets, alias layers, theme switching, and component tokens the team builds on.

## Choosing a mode

`design-system-foundations` runs in two modes:

**Lightweight mode** — the shortest path to a working foundation. Use it when the team needs to start building components and doesn't yet need full DTCG source or multi-theme support. Covers:

- Semantic color roles (primary, surface, on-surface, error, warning, success, info, disabled, overlay)
- Typography (font families, scale steps by semantic level, weights)
- Spacing tokens (named steps from the taxonomy method)
- Radius system (none, sm, md, lg, full)
- Focus styles (meeting WCAG 2.4.11)
- Key status tokens (success / warning / error / info, each with background, foreground, border roles)
- Responsive breakpoints (named steps with boundary values)
- Core component tokens: button, input, card, modal base

**Full mode** — when the project needs DTCG-compatible token source, multi-theme switching, or a full component library starting point. Extends lightweight with:

- DTCG 2025.10-compatible token source (JSON or YAML; W3C Community Group specification; "where practical" posture)
- Light/dark theme switching (both themes defined as token overrides; semantic names unchanged between themes)
- Semantic alias layer (primitive → semantic → component; no component reads a primitive directly)
- Full component anatomy (navigation, form controls, data display, feedback components)

> Generated platform outputs (Figma variables, iOS SwiftUI tokens, Android Material tokens) are outside the scope of `design-system-foundations` and are deferred to a follow-on step or tool.

## When to use lightweight vs. full mode

| Signal | Mode |
|--------|------|
| Starting a new project; need to unblock component work | Lightweight |
| Need both light and dark themes from the start | Full |
| Team uses a DTCG-compatible token pipeline | Full |
| Retrofitting an existing design system | Lightweight first, then Full |
| Small team or MVP with a single theme | Lightweight |

## Example lightweight output shape

A lightweight `design-system-foundations` output names the token structure and semantic roles — it does not produce a values table. The team maps values to roles using the taxonomy method.

```
Semantic color tokens:
  --ds-color-primary: [value from taxonomy / team maps]
  --ds-color-surface: [value from taxonomy / team maps]
  --ds-color-on-surface: [value from taxonomy / team maps]
  --ds-color-error: [value from taxonomy / team maps]
  ...

Typography tokens:
  --ds-font-body: [family name]
  --ds-font-heading: [family name]
  --ds-text-sm / --ds-text-base / --ds-text-lg / --ds-text-xl / --ds-text-2xl: [scale steps]
  --ds-font-weight-regular / --ds-font-weight-medium / --ds-font-weight-bold

Spacing tokens (from the taxonomy's minor-third or golden-ratio steps):
  --ds-space-1 through --ds-space-8: [named steps]

Core component: button
  --ds-btn-bg: maps to --ds-color-primary
  --ds-btn-bg-hover: [hover state]
  --ds-btn-bg-active: [active state]
  --ds-btn-bg-disabled: maps to --ds-color-disabled
  --ds-btn-focus-ring: meets WCAG 2.4.11
```

## Example full mode scope

Full mode output additionally names:

- **DTCG token source:** a JSON file conforming to the DTCG 2025.10 `$type` / `$value` / `$description` schema; resolves aliases.
- **Light and dark themes:** both themes as override sets; every semantic role in both states.
- **Alias chain:** `color.blue.500` (primitive) → `color.primary` (semantic) → `button.background.default` (component).
- **Extended component anatomy:** navigation components (top bar, side nav, breadcrumb), form controls (checkbox, radio, select, toggle, textarea), data display (table, badge, tag, tooltip), feedback (toast, modal, dialog, empty state).

## Sequence in practice

1. Run `creative-direction` to name the emotional and brand goals.
2. Run `design-token-taxonomy` to derive the token/scale taxonomy from those goals — naming tokens by semantic role and choosing a single ratio as the organizing concept.
3. Run `design-system-foundations` in lightweight or full mode to apply the taxonomy as a working foundation.
4. Build components using the foundation tokens (route to `interaction-design` for component state machines).

## See also

- [Thread a feature from journey to screens](author-design-intent.md) — the full XD chain context in which this two-step token chain sits.

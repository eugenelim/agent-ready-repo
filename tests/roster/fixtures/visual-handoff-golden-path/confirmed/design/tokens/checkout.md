---
type: token-taxonomy
slug: "checkout"
direction: "checkout"
route: "extend"
date: "2026-10-01"
---

# Design system: Checkout

Fixture data for a roster test. No person or product is described.

## Authority

- **Route:** extend — the brand palette exists; spacing does not.
- **Direction source:** direction/checkout.md
- **Incumbent source:** src/styles/brand.css
- **Visual target:** the direction's frontmatter records its disposition; the target binds composition only and supplies no value.
- **Stated constraints:** none

| Domain | Rung that supplied it |
|---|---|
| Typography | `platform-convention` |
| Color | `incumbent-system` |
| Spacing and rhythm | `approved-direction` |
| Shape and containment | `approved-direction` |
| Depth | `approved-direction` |
| Motion | `derivation` |
| Graphic language | `derivation` |
| Spatial structure | `approved-direction` |

## System commitments

### Typography

- **Relationship:** body and UI share one family; headings step up once.
- **Families:** the platform's system UI stack.
- **Roles and values:**

| Role | Job it does | Resolved value | Traces to |
|---|---|---|---|
| `body` | order lines and form labels | system-ui stack, 1rem, 400, 1.5 | platform convention: responsive-web system UI stack |
| `heading` | the step title | system-ui stack, 1.375rem, 600, 1.25 | platform convention: responsive-web system UI stack |

### Color

- **Relationship:** paper ground, ink text, one pine accent spent on the pay action.
- **Roles and values:**

| Role | Job it does | Resolved value | Traces to |
|---|---|---|---|
| `surface.default` | page ground | #FBF8F3 | incumbent `--brand-paper` in src/styles/brand.css |
| `text.default` | body copy | #1E2A26 | incumbent `--brand-ink-900` in src/styles/brand.css |
| `text.muted` | secondary copy | #4F5D57 | incumbent `--brand-ink-600` in src/styles/brand.css |
| `accent.action` | the pay action | #2F5D50 | incumbent `--brand-pine-700` in src/styles/brand.css |
| `text.on-action` | label on the pay action | #FBF8F3 | incumbent `--brand-paper` in src/styles/brand.css |
| `border.divider` | separators between groups | #D9D2C5 | incumbent `--brand-sand-300` in src/styles/brand.css |

### Spacing and rhythm

- **Relationship:** controls sit close; groups and regions breathe.
- **Steps and their use:**

| Role | Job it does | Resolved value | Traces to |
|---|---|---|---|
| `space.1` | inside a control | 6px | Spatial density |
| `space.2` | between a label and its field | 10px | Spatial density |
| `space.3` | between fields in a group | 14px | Spatial density |
| `space.4` | between groups | 20px | Whitespace distribution |
| `space.5` | around the pay action | 28px | Calm assurance |
| `space.6` | between the two regions | 40px | Whitespace distribution |

### Depth

- **Levels:** none — the surface is flat.

### Motion

- **Durations:** none — the surface does not animate.

## Proving set

Fixture data: the needs this system was checked against.

| Product need | Domains it exercised | What it exposed |
|---|---|---|
| the payment form | Color, Spacing and rhythm | the incumbent muted text missed the body-text floor |
| the pay action | Color | held |
| the narrow channel | Spacing and rhythm | held |

## Accessibility

- **Standard and conformance level:** WCAG 2.2 AA, chosen by the product owner.
- **Pairings checked:**

| Foreground | Background | Element class |
|---|---|---|
| `text.default` | `surface.default` | Body text |
| `text.muted` | `surface.default` | Body text |
| `text.on-action` | `accent.action` | Body text |

- **Adaptations made:**

| Role | Incumbent value | Resolved value | Why |
|---|---|---|---|
| `text.muted` | `--brand-ink-400` #8A968F | `--brand-ink-600` #4F5D57 | the incumbent muted text missed the body-text floor on the paper ground |

## Binding

- **Architecture:** a custom-property file.
- **Where the values live:** implementation/tokens.css
- **Naming convention followed:** `--color-<role>` and `--space-<step>`.

## Unresolved decisions

| Domain | Authority that is missing | Who resolves it | Operation that supplies it |
|---|---|---|---|
| — | — | — | — |

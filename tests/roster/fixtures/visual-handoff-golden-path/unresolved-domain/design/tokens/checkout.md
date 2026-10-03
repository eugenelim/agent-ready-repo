---
type: token-taxonomy
slug: "checkout"
direction: "checkout"
route: "originate"
date: "2026-10-01"
---

# Design system: Checkout

Fixture data for a roster test. No person or product is described.

## Authority

- **Route:** originate — no incumbent visual system exists.
- **Direction source:** direction/checkout.md
- **Incumbent source:** none found — searched src/
- **Visual target:** the direction's frontmatter records its disposition; the target binds composition only and supplies no value.
- **Stated constraints:** none

| Domain | Rung that supplied it |
|---|---|
| Typography | `unresolved` |
| Color | `approved-direction` |
| Spacing and rhythm | `approved-direction` |
| Shape and containment | `approved-direction` |
| Depth | `approved-direction` |
| Motion | `derivation` |
| Graphic language | `derivation` |
| Spatial structure | `approved-direction` |

## System commitments

### Color

- **Relationship:** paper ground, ink text, one pine accent spent on the pay action.
- **Roles and values:**

| Role | Job it does | Resolved value | Traces to |
|---|---|---|---|
| `surface.default` | page ground | #FBF8F3 | Chromatic intensity |
| `text.default` | body copy | #1E2A26 | Chromatic intensity |
| `text.muted` | secondary copy | #4F5D57 | Chromatic intensity |
| `accent.action` | the pay action | #2F5D50 | Chromatic intensity |
| `text.on-action` | label on the pay action | #FBF8F3 | Chromatic intensity |
| `border.divider` | separators between groups | #D9D2C5 | Chromatic intensity |

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
| the payment form | Color, Spacing and rhythm | held |
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

- **Adaptations made:** none required.

## Binding

- **Architecture:** a custom-property file.
- **Where the values live:** implementation/tokens.css
- **Naming convention followed:** `--color-<role>` and `--space-<step>`.

## Unresolved decisions

| Domain | Authority that is missing | Who resolves it | Operation that supplies it |
|---|---|---|---|
| Typography | No type commitment in the direction and no incumbent type scale | Design lead (placeholder) | Amend the direction's type axes |

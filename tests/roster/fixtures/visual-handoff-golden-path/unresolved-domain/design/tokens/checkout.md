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
| `surface.default` | page ground | #fbf8f3 | Chromatic intensity |
| `text.default` | body copy | #1e2a26 | Chromatic intensity |
| `text.muted` | secondary copy | #4f5d57 | Chromatic intensity |
| `accent.action` | the pay action | #2f5d50 | Chromatic intensity |
| `text.on-action` | label on the pay action | #fbf8f3 | Chromatic intensity |
| `border.divider` | separators between groups | #d9d2c5 | Chromatic intensity |

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

### Shape and containment

- **Relationship:** groups are separated by rules, not cards; controls are bounded.
- **Borders and dividers:** 1px solid `border.divider` between groups; 1px solid `text.muted` around controls.
- **Corner treatment:** square — 0 on every surface.

### Spatial structure

- **Column behaviour:** one column below 1152px; two columns at 1152px and above, split 3fr to 2fr, the payment form first.
- **Alignment:** both regions share the page's top edge.

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

---
name: responsive-layout
description: Design and implement adaptive layouts using CSS Grid, Flexbox, container queries, and fluid typography/spacing — the craft layer for layouts that work correctly across all viewport sizes without JavaScript.
---

# Skill: responsive-layout

Load this skill when the primary task is designing or debugging a layout that
must work across breakpoints. Do not load it for routine margin or padding
adjustments on an already-responsive surface. Load `responsive-layout` when:

- Building the layout structure for a new page or section from scratch
- Debugging a layout that breaks at a specific viewport width
- Designing a shared component that must adapt to variable-width containers
- Evaluating whether a layout approach is correct before implementation

---

## Layout primitive selection

**CSS Grid:** for two-dimensional layouts and page-level structure. Use when
elements need to be positioned on both a row axis and a column axis, or when
the layout requires elements to align with other elements across rows/columns.

**Flexbox:** for one-dimensional alignment and component-level distribution.
Use when elements need to be distributed along a single axis (row or column),
with flexible sizing and alignment.

**The mixing rule:** never use Grid and Flexbox to solve the same axis
in the same container. Use Grid for the page layout; use Flexbox inside a
Grid cell for component-level distribution within that cell.

**Common mistakes:**
- Using Flexbox for a two-column layout with a sidebar — Grid is the right
  tool; Flexbox cannot express "sidebar is fixed-width, content fills the rest"
  without a `min-width: 0` hack on the content column.
- Using Grid for a single-axis distribution of buttons in a toolbar — Flexbox
  is the right tool; Grid's two-dimensional power is wasted here.

---

## Container queries vs. media queries

**Use container queries** when a component must adapt to the width of its
own container rather than the viewport. This is the correct tool for shared
components that appear in multiple layout contexts (e.g., a card that appears
in a sidebar at 320px and in a main content area at 600px).

```css
/* Define the containment context on the parent */
.card-container {
  container-type: inline-size;
  container-name: card;
}

/* Query the container, not the viewport */
@container card (min-width: 500px) {
  .card {
    display: grid;
    grid-template-columns: 120px 1fr;
  }
}
```

Container queries are Baseline Widely Available as of 2023.

**Use media queries** when layout changes are driven by the viewport — page-level
structure that changes how sections are arranged. Navigation, sidebar
visibility, and column count at the page level belong here.

```css
@media (min-width: 768px) {
  .page-layout {
    display: grid;
    grid-template-columns: 240px 1fr;
  }
}
```

**Decision rule:** if the layout change is for a shared component that appears
in multiple container widths — use container queries. If the layout change is
for the page structure that responds to the viewport — use media queries.

---

## Fluid typography

Use `clamp()` for type that scales smoothly between a minimum and maximum
viewport width without breakpoint jumps:

```css
/* clamp(minimum, preferred, maximum) */
/* Preferred: linear interpolation from min-size at min-viewport to max-size at max-viewport */

h1 {
  /* 24px at 320px viewport, scales to 48px at 1280px viewport */
  font-size: clamp(1.5rem, 2.5vw + 0.5rem, 3rem);
}

p {
  /* 16px at 320px viewport, scales to 18px at 1280px viewport */
  font-size: clamp(1rem, 0.5vw + 0.875rem, 1.125rem);
}
```

**Formula for the `vw + rem` preferred value:**
```
slope = (max-size - min-size) / (max-viewport - min-viewport)
y-intercept = min-size - (slope * min-viewport)
preferred = slope * 100vw + y-intercept
```

Derive min and max font sizes from the spacing scale (see `token-architecture`)
so typography and spacing scales remain proportional.

---

## Breakpoint strategy

Name breakpoints semantically — not by device. Device names encode specific
dimensions that change with hardware generations; semantic names are stable:

```css
/* Token-defined breakpoints — semantic names */
:root {
  --breakpoint-sm:  480px;
  --breakpoint-md:  768px;
  --breakpoint-lg:  1024px;
  --breakpoint-xl:  1280px;
  --breakpoint-2xl: 1536px;
}
```

**Mobile-first (min-width):** write base styles for mobile, then use
`@media (min-width: ...)` to enhance for larger viewports. Mobile-first
produces smaller files for mobile users (the base styles need no media query).

**Never encode specific device names** (`@media (max-width: 375px)` for
"iPhone SE") — those dimensions are historical snapshots that will be wrong
within 18 months.

---

## Grid patterns

**The 12-column grid** — flexible foundation for page layouts:
```css
.layout {
  display: grid;
  grid-template-columns: repeat(12, minmax(0, 1fr));
  gap: var(--ds-space-4);
}

/* A content area spanning 8 columns, centered */
.main-content {
  grid-column: 3 / span 8;
}
```

**`auto-fill` vs. `auto-fit`** for responsive card grids:
```css
/* auto-fill: preserves empty tracks (grid does not collapse) */
.card-grid-fill {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
}

/* auto-fit: collapses empty tracks (cards expand to fill the row) */
.card-grid-fit {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
}
```

Use `auto-fill` when preserving the column structure matters (e.g., aligning
with a fixed-column grid above); use `auto-fit` when cards should expand to
fill available space.

**Named grid areas** for semantic layouts:
```css
.page {
  display: grid;
  grid-template-areas:
    "header header"
    "sidebar main"
    "footer footer";
  grid-template-columns: 240px 1fr;
  grid-template-rows: auto 1fr auto;
}

.page-header  { grid-area: header; }
.page-sidebar { grid-area: sidebar; }
.page-main    { grid-area: main; }
.page-footer  { grid-area: footer; }
```

**`subgrid`** for aligned multi-column forms (Baseline Widely Available 2023):
```css
.form-row {
  display: grid;
  grid-template-columns: subgrid;
  grid-column: 1 / -1;
}
```

---

## The no-JS rule

Responsive layout must be fully functional without JavaScript. If a layout
requires JS to function at certain viewport sizes, it is a CSS architecture
problem, not a JS opportunity.

**CSS-only responsive patterns for common UI:**

**Hamburger nav (disclosure-pattern, CSS-only):**
Use `<details>` + `<summary>` for a native CSS-only toggle — no JS required.
```html
<details class="nav-disclosure">
  <summary>Menu</summary>
  <nav>…</nav>
</details>
```

**Card grid:** `auto-fill` / `auto-fit` with `minmax()` — no breakpoint JS.

**Table:** on narrow viewports, display each row as a block with
`display: block` on `<td>` elements and use `data-label` attributes
for column headers. This requires no JS.

---

## Output rendering

Rationale / narrative — Use short ## headings and 2–3 sentence paragraphs. Don't force narrative into a table.

## Common failures to refuse

| Pattern | Problem | Fix |
|---|---|---|
| Fixed pixel widths on containers (`width: 1200px`) | Container overflows viewport on narrower screens | Use `max-width` with `width: 100%` or a percentage |
| `overflow: hidden` on containers | Can hide content on small viewports that the user cannot scroll to | Audit whether `overflow: hidden` is actually needed; prefer `overflow: clip` for visual clipping without hiding content from assistive tech |
| Font sizes below 16px on mobile | Browsers may zoom automatically; can trigger CLS; fails readability standards | Minimum 16px (`1rem`) for body text on mobile |
| Content reordering that breaks tab order | Visual `order` property in Flexbox/Grid moves content visually but not in the DOM | DOM order must match visual order; use `order` only for cosmetic reordering within the same semantic group |
| Viewport units for font sizes without clamp | `font-size: 2vw` produces 0px at zero viewport width | Always wrap viewport-unit font sizes in `clamp()` |

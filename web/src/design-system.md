# Platform Site Design System

> **Implementation authority:** `web/src/styles/tokens.css`
> **Upstream narrative spec:** `docs/specs/platform-site/design-system-foundations.md`
>
> This document is the single reference for every designer or developer working
> on the platform site. All values here are derived verbatim from `tokens.css`
> as the authoritative source. Do not update this document without updating
> `tokens.css` first.

---

## 1. Color Tokens

### Tier 1 — Primitive Scale

Primitive tokens name raw color values. Component CSS **never** references
primitives directly — they exist only as targets for semantic tokens.

#### Dark zone

| Token | Hex | Role |
|---|---|---|
| `--prim-dark-950` | `#0b0e12` | Hero canvas — neutral-cool near-black |
| `--prim-dark-900` | `#111520` | Dark card / elevated on hero |
| `--prim-dark-800` | `#1a2035` | Dark elevated overlay on hero |
| `--prim-dark-700` | `#232b40` | Dark border-visible surface |

#### Neutral (light zone)

| Token | Hex | Role |
|---|---|---|
| `--prim-neutral-50` | `#fafaf9` | Content surface — warm near-white |
| `--prim-neutral-100` | `#f0efed` | Alt surface — card background |
| `--prim-neutral-200` | `#e0ddd9` | Border on light |
| `--prim-neutral-300` | `#c4c0bb` | Muted border |
| `--prim-neutral-400` | `#9c9891` | Placeholder, disabled |
| `--prim-neutral-600` | `#6b6760` | Secondary text |
| `--prim-neutral-800` | `#2e2c28` | Primary text |
| `--prim-neutral-900` | `#1c1b18` | Heading text |

#### Amber-gold — single chromatic accent

| Token | Hex | Role |
|---|---|---|
| `--prim-amber-50` | `#fff8e8` | Lightest amber tint |
| `--prim-amber-100` | `#fdecc9` | Very light amber |
| `--prim-amber-200` | `#fad49a` | Light amber |
| `--prim-amber-300` | `#f5bc6a` | Light decorative glow |
| `--prim-amber-400` | `#e8952b` | Primary accent — CTA, icon, stat |
| `--prim-amber-500` | `#c8780a` | Darker amber variant |
| `--prim-amber-700` | `#8b5e0a` | Text-safe on light (≥4.5:1 on neutral-50) |
| `--prim-amber-900` | `#4a3005` | Deep, for dark-on-amber text |

#### Alpha tokens

| Token | Value | Role |
|---|---|---|
| `--prim-white-06` | `rgba(255, 255, 255, 0.06)` | Hairline divider on dark |
| `--prim-white-10` | `rgba(255, 255, 255, 0.10)` | Card border on dark |
| `--prim-white-20` | `rgba(255, 255, 255, 0.20)` | Ghost button border on dark |
| `--prim-white-60` | `rgba(255, 255, 255, 0.60)` | Muted / caption on dark |
| `--prim-white-80` | `rgba(255, 255, 255, 0.80)` | Secondary text on dark |
| `--prim-black-06` | `rgba(0, 0, 0, 0.06)` | Hairline border on light |
| `--prim-black-12` | `rgba(0, 0, 0, 0.12)` | Subtle shadow on light |
| `--prim-amber-10` | `rgba(232, 149, 43, 0.10)` | Low-opacity amber fill on light |
| `--prim-amber-15` | `rgba(232, 149, 43, 0.15)` | Low-opacity amber fill on dark |
| `--prim-amber-20` | `rgba(232, 149, 43, 0.20)` | Ambient glow, gate pulses |

---

### Tier 2 — Semantic Layer

Semantic tokens map to primitives and carry zone meaning. Component CSS
references these — **never** Tier 1 primitives.

#### Layering rule

> Component CSS references semantic tokens only — never primitives directly.
> The three-tier architecture is: **Primitive → Semantic → Component**.

#### Hero / dark zone

| Token | Primitive target | Zone | Usage |
|---|---|---|---|
| `--ds-hero-bg` | `--prim-dark-950` | Hero / dark | Main dark background |
| `--ds-hero-surface` | `--prim-dark-900` | Hero / dark | Card on dark |
| `--ds-hero-elevated` | `--prim-dark-800` | Hero / dark | Elevated card on dark |
| `--ds-hero-fg` | `#ffffff` | Hero / dark | Primary text on dark |
| `--ds-hero-fg-2` | `--prim-white-80` | Hero / dark | Secondary text on dark |
| `--ds-hero-fg-muted` | `--prim-white-60` | Hero / dark | Muted / caption on dark |
| `--ds-hero-border` | `--prim-white-06` | Hero / dark | Hairline divider on dark |
| `--ds-hero-border-card` | `--prim-white-10` | Hero / dark | Card border on dark |

#### Content / light zone

| Token | Primitive target | Zone | Usage |
|---|---|---|---|
| `--ds-surface` | `--prim-neutral-50` | Content / light | Page / section background |
| `--ds-surface-alt` | `--prim-neutral-100` | Content / light | Card background |
| `--ds-on-surface` | `--prim-neutral-900` | Content / light | Heading text |
| `--ds-on-surface-2` | `--prim-neutral-800` | Content / light | Body text |
| `--ds-on-surface-muted` | `--prim-neutral-600` | Content / light | Captions, metadata |
| `--ds-border` | `--prim-neutral-200` | Content / light | Card, section border |
| `--ds-border-subtle` | `--prim-black-06` | Content / light | Hairline, lowest weight |

#### Accent layer

| Token | Primitive target | Zone | Usage |
|---|---|---|---|
| `--ds-accent` | `--prim-amber-400` | Accent | Icon, CTA fill on dark, stat number |
| `--ds-accent-deep` | `--prim-amber-700` | Accent | Text-safe amber on light (4.5:1+) |
| `--ds-accent-subtle` | `--prim-amber-10` | Accent | Low-opacity amber fill on light |
| `--ds-accent-subtle-dk` | `--prim-amber-15` | Accent | Low-opacity amber fill on dark |
| `--ds-accent-glow` | `--prim-amber-20` | Accent | Ambient glow, hero gradient, gate pulses |

#### CTA layer

| Token | Primitive target | Zone | Usage |
|---|---|---|---|
| `--ds-cta-primary-bg` | `--prim-amber-400` | CTA | Primary button fill (dark hero) |
| `--ds-cta-primary-fg` | `--prim-dark-950` | CTA | Primary button text (dark hero) |
| `--ds-cta-primary-bg-hover` | `--prim-amber-300` | CTA | Primary button hover fill |
| `--ds-cta-ghost-border` | `--prim-white-20` | CTA | Ghost button border (dark hero) |
| `--ds-cta-ghost-fg` | `--prim-white-80` | CTA | Ghost button text (dark hero) |
| `--ds-cta-ghost-bg-hover` | `--prim-white-10` | CTA | Ghost button hover fill (dark hero) |
| `--ds-cta-ghost-light-border` | `--prim-amber-400` | CTA | Ghost button border (light) |
| `--ds-cta-ghost-light-fg` | `--prim-amber-700` | CTA | Ghost button text (light) |

---

## 2. Typography

### Font families

| Token | Value | Usage |
|---|---|---|
| `--ds-font-sans` | `'Inter Variable', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif` | Body, headings, UI labels |
| `--ds-font-mono` | `'JetBrains Mono', ui-monospace, 'SF Mono', 'Cascadia Code', Menlo, Consolas, monospace` | Code, terminal, skill names, stat numbers |

`'Inter Variable'` is the family name Fontsource registers for the variable
package (`@fontsource-variable/inter/wght.css`). `'Inter'` covers any static
Inter fallback before system fonts.

### Size scale

| Token | Value | px range | Usage |
|---|---|---|---|
| `--ds-type-display` | `clamp(2.75rem, 5.5vw, 4rem)` | ~44–64px | Hero headline, section closers |
| `--ds-type-h2` | `clamp(1.875rem, 3.5vw, 2.5rem)` | ~30–40px | Section headings |
| `--ds-type-h3` | `clamp(1.25rem, 2vw, 1.5rem)` | ~20–24px | Card headings, gate IDs |
| `--ds-type-body-lg` | `1.125rem` | 18px | Lead / intro paragraphs |
| `--ds-type-body` | `1rem` | 16px | Body text |
| `--ds-type-sm` | `0.875rem` | 14px | Captions, metadata, table cells |
| `--ds-type-xs` | `0.75rem` | 12px | Labels, badges, scope chips |
| `--ds-type-mono-sm` | `0.8125rem` | 13px | Inline code, skill names, terminal lines |

### Weight scale

| Token | Value | Usage |
|---|---|---|
| `--ds-weight-regular` | `400` | Body text, default |
| `--ds-weight-medium` | `500` | Navigation links, tab labels |
| `--ds-weight-semibold` | `600` | CTAs, emphasized UI text |
| `--ds-weight-bold` | `700` | Brand wordmark, primary headings |
| `--ds-weight-heavy` | `800` | Display headlines, stat numbers |

### Tracking (letter-spacing) scale

| Token | Value | Usage |
|---|---|---|
| `--ds-track-display` | `-0.03em` | Display headlines — required at display sizes |
| `--ds-track-heading` | `-0.02em` | h2 / h3 headings |
| `--ds-track-label` | `0.08em` | Uppercase monospace labels, scope chips |
| `--ds-track-normal` | `0em` | Body text — never deviate |

### Leading (line-height) scale

| Token | Value | Usage |
|---|---|---|
| `--ds-lead-display` | `1.1` | Tight for display size |
| `--ds-lead-heading` | `1.25` | Slightly open for h2/h3 |
| `--ds-lead-body` | `1.65` | Comfortable reading |
| `--ds-lead-mono` | `1.5` | Code and terminal lines |

---

## 3. Spacing, Radius, Shadow, Motion, Z-index

### Spacing — 4px base grid

The site uses a 4px base unit with a 10-step scale.

| Token | Value | Common usage |
|---|---|---|
| `--ds-space-1` | `4px` | Icon gap, micro padding |
| `--ds-space-2` | `8px` | Tight gap between inline elements |
| `--ds-space-3` | `12px` | Card internal spacing, button row gap |
| `--ds-space-4` | `16px` | Standard internal padding |
| `--ds-space-5` | `24px` | Card padding, section sub-gap |
| `--ds-space-6` | `32px` | Card padding (large), stat strip padding |
| `--ds-space-7` | `48px` | Section inner gap, stat strip top pad |
| `--ds-space-8` | `64px` | Section bottom pad, loops grid gap |
| `--ds-space-9` | `96px` | Catalogue grid bottom margin |
| `--ds-space-10` | `128px` | — |

### Section / layout tokens (responsive)

| Token | Value | Role |
|---|---|---|
| `--ds-section-gap` | `clamp(5rem, 10vw, 8rem)` | Vertical gap between major sections |
| `--ds-section-pad-y` | `clamp(4rem, 8vw, 6rem)` | Internal vertical section padding |
| `--ds-content-max` | `1140px` | Maximum content column width |
| `--ds-content-pad-x` | `clamp(1.25rem, 5vw, 2.5rem)` | Horizontal page margin |

### Radius

| Token | Value | Usage |
|---|---|---|
| `--ds-radius-sm` | `4px` | Inline code, badges, chips, copy buttons |
| `--ds-radius-md` | `8px` | Cards, inputs, table container |
| `--ds-radius-lg` | `12px` | Terminal, large cards (loop-card, cat-card, PackCard) |
| `--ds-radius-pill` | `9999px` | CTA buttons, pipeline node chips |

### Shadow — border-not-shadow philosophy

The site uses borders as visual separators, not shadows.
Shadows are reserved for overlaid floating elements only.

| Token | Value | Usage |
|---|---|---|
| `--ds-shadow-overlay` | `0 20px 60px rgba(0, 0, 0, 0.25)` | Modals, dropdowns |
| `--ds-shadow-none` | `none` | Explicit no-shadow reset |

### Motion

Three durations and two easing curves. Apply `prefers-reduced-motion` guards
on all animated properties.

| Token | Value | Usage |
|---|---|---|
| `--ds-dur-quick` | `120ms` | Hover state transitions (color, border) |
| `--ds-dur-moderate` | `200ms` | Card hover, copy-button state, tab arrow |
| `--ds-dur-gentle` | `300ms` | Hero fade-in on load |
| `--ds-ease-std` | `cubic-bezier(0.4, 0, 0.2, 1)` | Material standard easing |
| `--ds-ease-out` | `cubic-bezier(0, 0, 0.2, 1)` | Deceleration — entering elements |

### Z-index stack

| Token | Value | Layer |
|---|---|---|
| `--ds-z-base` | `0` | Default document flow |
| `--ds-z-raised` | `10` | Slightly elevated (sticky headers, etc.) |
| `--ds-z-overlay` | `100` | Mobile nav drawer |
| `--ds-z-modal` | `200` | Modal dialogs |
| `--ds-z-toast` | `300` | Skip-nav, toasts — always on top |

---

## 4. Component Vocabulary

Each component entry documents its zone assignment, BEM class names,
and the semantic tokens it references.

### Hero

**Zone:** hero / dark  
**File:** `web/src/components/marketing/Hero.astro`

| BEM class | Role | Key tokens |
|---|---|---|
| `.hero` | Section root | `--ds-hero-bg`, `--ds-accent-glow`, `--ds-hero-border`, `--ds-hero-fg` |
| `.hero__inner` | Content column | `--ds-content-max`, `--ds-content-pad-x`, `--ds-space-8` |
| `.hero__headline` | Main h1 | `--ds-hero-fg` |
| `.hero__subhead` | Lead paragraph | `--ds-hero-fg-2`, `--ds-type-body-lg` |
| `.hero__actions` | CTA button row | `--ds-space-3` |
| `.hero__cta` | Button base | `--ds-radius-pill`, `--ds-weight-semibold`, `--ds-type-body` |
| `.hero__cta--primary` | Amber fill button | `--ds-cta-primary-bg`, `--ds-cta-primary-fg`, `--ds-cta-primary-bg-hover` |
| `.hero__cta--ghost` | Ghost button (dark) | `--ds-cta-ghost-fg`, `--ds-cta-ghost-border`, `--ds-cta-ghost-bg-hover`, `--ds-hero-fg` |
| `.hero__friction` | Friction note | `--ds-type-xs`, `--ds-hero-fg-muted`, `--ds-space-3` |

One-shot fade-in on load: `animation: hero-fade var(--ds-dur-gentle) var(--ds-ease-out) both`
— guarded by `@media (prefers-reduced-motion: no-preference)`.

---

### StatStrip

**Zone:** hero / dark (continuous with Hero — no visual break)  
**File:** `web/src/components/marketing/StatStrip.astro`

| BEM class | Role | Key tokens |
|---|---|---|
| `.stats` | Section root | `--ds-hero-bg`, `--ds-hero-border` (top border) |
| `.stats__list` | Flex row | `--ds-content-max`, `--ds-content-pad-x`, `--ds-space-6`, `--ds-space-8` |
| `.stats__item` | Single stat | `--ds-space-7` (inline pad), `--ds-hero-border` (left border) |
| `.stats__number` | Big number | `--ds-font-mono`, `--ds-type-h2`, `--ds-weight-heavy`, `--ds-accent` |
| `.stats__label` | Label below number | `--ds-type-xs`, `--ds-track-label`, `--ds-hero-fg-muted` |

---

### ThreeLoops

**Zone:** content / light (`surface-alt` Section)  
**File:** `web/src/components/marketing/ThreeLoops.astro`

| BEM class | Role | Key tokens |
|---|---|---|
| `.loops__headline` | Section h2 | `--ds-space-7` |
| `.pipeline` | Decorative node chain | `--ds-space-3`, `--ds-font-mono` |
| `.pipeline__node` | Node chip (Discovery/Build/Release) | `--ds-accent`, `--ds-radius-pill`, `--ds-accent-subtle`, `--ds-accent-deep`, `--ds-type-sm`, `--ds-weight-semibold` |
| `.pipeline__link` | Gate + arrow connector | `--ds-on-surface-muted`, `--ds-space-2` |
| `.pipeline__gate` | Gate label (G3, G4) | `--ds-type-xs`, `--ds-track-label`, `--ds-accent-deep` |
| `.loops` | Ordered loop list | `--ds-space-7` |
| `.loop` | Single loop item | `--ds-space-5` |
| `.loop__n` | Numeric badge (01/02/03) | `--ds-font-mono`, `--ds-type-h3`, `--ds-weight-heavy`, `--ds-accent-deep` |
| `.loop__body` | Loop body text block | — |
| `.loop__name` | Loop name h3 | `--ds-space-2` |
| `.loop__pack` | Pack name (monospace code chip) | `--ds-accent-subtle`, `--ds-accent-deep`, `--ds-radius-sm`, `--ds-track-label` |
| `.loop__desc` | Description | `--ds-space-4` |
| `.loop__gate` | Human gate highlight block | `--ds-accent`, `--ds-accent-subtle`, `--ds-on-surface`, `--ds-accent-deep` |
| `.loop__link` | Journey link | `--ds-weight-semibold` |

---

### HumanGates (gate cards)

**Zone:** content / light (`surface` Section)  
**File:** `web/src/components/marketing/HumanGates.astro`

| BEM class | Role | Key tokens |
|---|---|---|
| `.gates__headline` | Section h2 | `--ds-space-4` |
| `.gates__accent` | `you` emphasis span | `--ds-accent-deep` |
| `.gates__subhead` | Lead paragraph | `--ds-type-body-lg`, `--ds-space-7` |
| `.gates__grid` | Auto-fill card grid | `--ds-space-4`, `--ds-space-6` |
| `.gate-card` | Individual gate card | `--ds-surface-alt`, `--ds-border`, `--ds-accent` (left border), `--ds-radius-md`, `--ds-space-5` |
| `.gate-card__top` | ID + loop row | `--ds-space-3` |
| `.gate-card__id` | Gate ID (G0, G3, etc.) | `--ds-font-mono`, `--ds-weight-heavy`, `--ds-accent-deep`, `--ds-type-body-lg` |
| `.gate-card__loop` | Loop label | `--ds-type-xs`, `--ds-track-label`, `--ds-on-surface-muted` |
| `.gate-card__name` | Gate name h3 | `--ds-type-h3` |
| `.gate-card__decide` | Decision question | `--ds-on-surface-2`, `--ds-type-body` |
| `.gates__cta` | Journey link | `--ds-weight-semibold`, `--ds-type-body-lg` |

---

### AdapterMatrix

**Zone:** content / light (`surface` Section)  
**File:** `web/src/components/marketing/AdapterMatrix.astro`

| BEM class | Role | Key tokens |
|---|---|---|
| `.adapters__headline` | Section h3 | `--ds-space-6` |
| `.adapters__scroll` | Horizontal scroll wrapper | — |
| `.adapters__table` | Capability matrix table | `--ds-border`, `--ds-radius-md` |
| `.adapters__table thead th` | Column header cells | `--ds-surface-alt`, `--ds-type-xs`, `--ds-track-label`, `--ds-on-surface-muted`, `--ds-weight-semibold` |
| `.adapters__table tbody th` | Row header (agent name) | `--ds-weight-semibold`, `--ds-on-surface`, `--ds-font-mono`, `--ds-type-sm` |
| `.adapters__table th, td` | Cell padding | `--ds-space-3`, `--ds-space-4`, `--ds-border-subtle` |
| `.cap--yes` | Check mark cell | `--ds-accent-deep`, `--ds-weight-bold` |
| `.cap--no` | Dash cell | `--ds-on-surface-muted` |
| `.adapters__note` | Note paragraph | `--ds-space-5`, `--ds-on-surface-muted` |

---

### InstallTerminal + CSS-only tabs

**Zone:** content / light (`surface-alt` Section); terminal panel is dark  
**File:** `web/src/components/marketing/InstallTerminal.astro`

| BEM class | Role | Key tokens |
|---|---|---|
| `.terminal` | Dark terminal container | `--ds-hero-bg`, `--ds-hero-border-card`, `--ds-radius-lg` |
| `.terminal__bar` | Traffic-light header row | `--ds-space-3`, `--ds-space-4`, `--ds-hero-border` |
| `.terminal__dot` | Decorative circle (×3) | `--ds-hero-border-card`, `--ds-radius-pill` |
| `.terminal__line` | Command line row | `--ds-lead-mono` |
| `.terminal__prompt` | `❯` prompt glyph | `--ds-accent`, `--ds-weight-bold`, `--ds-font-mono` |
| `.tabs` | Tab row + panel wrapper | — |
| `.tabs__radio` | Visually-hidden radio (keyboard nav) | — |
| `.tabs__label` | Tab label button | `--ds-space-3`, `--ds-space-5`, `--ds-type-sm`, `--ds-weight-medium`, `--ds-hero-fg-muted` |
| `.tabs__panels` | Panel container | `--ds-hero-border` |
| `.tabs__panel` | Individual tab panel | `--ds-space-5`, `--ds-space-6`, `--ds-hero-fg` |

Active tab driven by CSS sibling combinator: `#install-tab-X:checked ~ .tabs__panels .tabs__panel--X { display: block }`. No JavaScript for tab switching.

---

### Copy button

The copy button appears in both InstallTerminal and the catalogue page `cat-card`
install blocks. It shares the same visual design.

**Zone:** dark (sits inside dark terminal or dark install block)

| BEM class | Role | Key tokens |
|---|---|---|
| `.install-copy-btn` / `.copy-btn` | Button root | `--ds-hero-elevated`, `--ds-hero-border-card`, `--ds-radius-sm`, `--ds-hero-fg-muted`, `--ds-font-mono`, `--ds-type-xs`, `--ds-weight-medium` |
| `.install-copy-btn:hover` / `.copy-btn:hover` | Hover state | `--ds-accent-subtle-dk`, `--ds-accent`, `--ds-dur-quick`, `--ds-ease-std` |
| `.install-copy-btn--success` / `.copy-btn--success` | Copied state | `--ds-accent-subtle-dk`, `--ds-accent` |
| `.install-copy-btn__icon` / `.copy-btn__icon` | SVG icon wrapper | — |

---

### PackCatalogue (loop-cards + pack-cards + scope chip)

**Zone:** content / light (`surface` Section); loop-card install code blocks are dark  
**File:** `web/src/components/marketing/PackCatalogue.astro`

**scope-chip** (shared with PackCard and cat-card):

| BEM class | Role | Key tokens |
|---|---|---|
| `.scope-chip` | `user` / `repo` badge | `--ds-font-mono`, `--ds-type-xs`, `--ds-track-label`, `--ds-accent-subtle`, `--ds-accent-deep`, `--ds-radius-sm` |

**loop-cards** (the three core packs — always visible):

| BEM class | Role | Key tokens |
|---|---|---|
| `.loop-cards` | Auto-fit card grid | `--ds-space-5`, `--ds-space-6` |
| `.loop-card` | Core pack card | `--ds-surface-alt`, `--ds-border`, `--ds-radius-lg`, `--ds-space-6`, `--ds-dur-moderate`, `--ds-ease-std` |
| `.loop-card:hover` | Hover state | `--ds-accent` (border color) |
| `.loop-card__head` | Name + scope chip row | `--ds-space-3`, `--ds-space-4` |
| `.loop-card__name` | Pack name h3 | `--ds-type-h3` |
| `.loop-card__desc` | Description | `--ds-on-surface-2`, `--ds-space-4` |
| `.loop-card__install` | Dark code block | `--ds-hero-bg`, `--ds-hero-fg`, `--ds-radius-sm`, `--ds-type-xs`, `--ds-lead-mono` |
| `.loop-card__link` | Journey link | `--ds-weight-semibold` |

**Expander (14 additional packs behind `<details>`)**:

| BEM class | Role | Key tokens |
|---|---|---|
| `.catalogue__summary` | Expander toggle | `--ds-accent-deep`, `--ds-weight-semibold`, `--ds-space-3` |
| `.catalogue__summary-arrow` | Rotating arrow | `--ds-dur-moderate`, `--ds-ease-std` |
| `.catalogue__group` | User / repo section | `--ds-space-6` |
| `.catalogue__group-title` | Group h3 | `--ds-type-h3`, `--ds-space-4` |

**pack-cards** (inside the expander):

| BEM class | Role | Key tokens |
|---|---|---|
| `.pack-grid` | Auto-fill grid | `--ds-space-4` |
| `.pack-card` (PackCatalogue variant) | Small pack card | `--ds-surface-alt`, `--ds-border`, `--ds-radius-md`, `--ds-space-5` |
| `.pack-card__name` | Pack name h4 | `--ds-type-body-lg`, `--ds-space-2` |
| `.pack-card__desc` | Description | `--ds-type-sm`, `--ds-on-surface-muted` |

---

### BuildYourOrg

**Zone:** hero / dark (`dark` Section — merges visually with SiteFooter below)  
**File:** `web/src/components/marketing/BuildYourOrg.astro`

| BEM class | Role | Key tokens |
|---|---|---|
| `.org` | Content column | — |
| `.org__headline` | Display h2 | `--ds-hero-fg`, `--ds-type-display`, `--ds-weight-heavy`, `--ds-lead-display`, `--ds-track-display`, `--ds-space-5` |
| `.org__body` | Lead paragraph | `--ds-hero-fg-2`, `--ds-type-body-lg`, `--ds-space-6` |
| `.org__body code` | Inline code chip | `--ds-accent-subtle-dk`, `--ds-accent`, `--ds-radius-sm` |
| `.org__cta` | Amber primary CTA | `--ds-cta-primary-bg`, `--ds-cta-primary-fg`, `--ds-weight-semibold`, `--ds-type-body`, `--ds-radius-pill` |
| `.org__cta:hover` | Hover state | `--ds-cta-primary-bg-hover` |

---

### Section band wrapper

**File:** `web/src/components/layout/Section.astro`

The `<Section>` component wraps every homepage section. It accepts a `tone`
prop and applies the appropriate background via a BEM modifier.

| BEM class | Zone | Background token | Foreground token |
|---|---|---|---|
| `.section--surface` | Content / light | `--ds-surface` | `--ds-on-surface-2` |
| `.section--surface-alt` | Content / light (alt) | `--ds-surface-alt` | `--ds-on-surface-2` |
| `.section--dark` | Hero / dark | `--ds-hero-bg` | `--ds-hero-fg` |

| BEM class | Role | Key tokens |
|---|---|---|
| `.section` | Section root | `--ds-section-pad-y` (padding-block) |
| `.section__inner` | Content column | `--ds-content-max`, `--ds-content-pad-x` |

---

### SiteNav

**Zone:** hero / dark (continuous with Hero below — no visual break)  
**File:** `web/src/components/layout/SiteNav.astro`

| BEM class | Role | Key tokens |
|---|---|---|
| `.nav` | Nav root | `--ds-hero-bg`, `--ds-hero-fg` |
| `.nav__inner` | Content row | `--ds-content-max`, `--ds-content-pad-x`, `--ds-space-4`, `--ds-space-5` |
| `.nav__logo` | Brand wordmark | `--ds-hero-fg`, `--ds-weight-bold`, `--ds-type-body-lg`, `--ds-track-heading`, `--ds-font-mono` |
| `.nav__logo:hover` | Hover | `--ds-accent` |
| `.nav__links` | Desktop link row | `--ds-space-6` |
| `.nav__link` | Nav link | `--ds-hero-fg-2`, `--ds-type-sm`, `--ds-weight-medium` |
| `.nav__link:hover` | Hover | `--ds-hero-fg` |
| `.nav__link--docs` | Docs link (muted) | `--ds-hero-fg-muted` |
| `.nav__cta` | Amber Install button | `--ds-cta-primary-bg`, `--ds-cta-primary-fg`, `--ds-type-sm`, `--ds-weight-semibold`, `--ds-radius-pill` |
| `.nav__cta:hover` | Hover | `--ds-cta-primary-bg-hover` |
| `.nav__burger` | Hamburger icon bars | `--ds-hero-fg` |
| `.nav__drawer` | Mobile drawer | `--ds-hero-bg`, `--ds-hero-border`, `--ds-content-pad-x`, `--ds-z-overlay` |

Mobile nav uses `<details>/<summary>` disclosure — zero JavaScript.

---

### SiteFooter

**Zone:** hero / dark (merges with BuildYourOrg above — one continuous dark band)  
**File:** `web/src/components/layout/SiteFooter.astro`

| BEM class | Role | Key tokens |
|---|---|---|
| `.footer` | Footer root | `--ds-hero-bg`, `--ds-hero-fg-muted` |
| `.footer__inner` | Content row | `--ds-content-max`, `--ds-content-pad-x`, `--ds-space-7`, `--ds-space-4`, `--ds-space-6` |
| `.footer__brand` | Brand wordmark | `--ds-font-mono`, `--ds-weight-bold`, `--ds-hero-fg` |
| `.footer__links` | Link row | `--ds-space-5` |
| `.footer__links a` | Footer link | `--ds-hero-fg-2`, `--ds-type-sm` |
| `.footer__links a:hover` | Hover | `--ds-accent` |
| `.footer__copy` | Copyright line | `--ds-type-sm`, `--ds-hero-fg-muted` |

---

### PackCard (`/packs/` index)

**Zone:** content / light (surface-alt background)  
**File:** `web/src/components/pack/PackCard.astro`

| BEM class | Role | Key tokens |
|---|---|---|
| `.pack-card` | Card root | `--ds-surface-alt`, `--ds-border`, `--ds-radius-lg`, `--ds-dur-moderate`, `--ds-ease-std` |
| `.pack-card:hover` | Hover state | `--ds-accent` (border color) |
| `.pack-card__link` | Navigating anchor | `--ds-space-6` |
| `.pack-card__head` | Name + scope chip row | `--ds-space-3` |
| `.pack-card__name` | Pack name h3 | `--ds-type-h3`, `--ds-on-surface` |
| `.scope-chip` | `user` / `repo` badge | (see PackCatalogue) |
| `.pack-card__tagline` | Description | `--ds-type-body`, `--ds-on-surface-2`, `--ds-space-4`, `--ds-lead-body` |
| `.pack-card__cta` | "Explore →" label | `--ds-type-sm`, `--ds-weight-semibold`, `--ds-accent-deep` |

---

### `cat-card` (`/catalogue/`)

**Zone:** content / light (`surface` Section); install blocks are dark  
**File:** `web/src/pages/catalogue/index.astro`

| BEM class | Role | Key tokens |
|---|---|---|
| `.cat-card` | Card root | `--ds-surface-alt`, `--ds-border`, `--ds-radius-lg`, `--ds-dur-moderate`, `--ds-ease-std` |
| `.cat-card:hover` | Hover state | `--ds-accent` (border color) |
| `.cat-card__head` | Navigating anchor | `--ds-space-6` |
| `.cat-card__name-row` | Name + scope chip row | `--ds-space-3` |
| `.cat-card__name` | Pack name h3 | `--ds-type-h3`, `--ds-weight-semibold`, `--ds-on-surface`, `--ds-track-heading` |
| `.scope-chip` | `user` / `repo` badge | (see PackCatalogue) |
| `.cat-card__tagline` | Description | `--ds-type-body`, `--ds-on-surface-2`, `--ds-lead-body`, `--ds-space-4` |
| `.cat-card__meta` | Skills count + CTA row | `--ds-space-3` |
| `.cat-card__skills` | Skill count label | `--ds-font-mono`, `--ds-type-xs`, `--ds-on-surface-muted` |
| `.cat-card__detail-cta` | "View pack →" label | `--ds-type-sm`, `--ds-weight-semibold`, `--ds-accent-deep` |

**Install blocks** (dark band at card bottom):

| BEM class | Role | Key tokens |
|---|---|---|
| `.install-blocks` | Dark install section | `--ds-border` (top border) |
| `.install-block` | CLI or plugin install row | `--ds-hero-bg`, `--ds-space-3`, `--ds-space-5` |
| `.install-block--plugin` | Plugin row (second) | `--ds-hero-border` (top border) |
| `.install-block__label` | "CLI" / "Plugin" label | `--ds-font-mono`, `--ds-type-xs`, `--ds-track-label`, `--ds-hero-fg-muted` |
| `.install-block__cmd` | Command code | `--ds-font-mono`, `--ds-type-mono-sm`, `--ds-hero-fg`, `--ds-lead-mono` |
| `.copy-btn` | Copy button | (see Copy button) |

---

## 5. Zone Rules

The site has two zones: the **dark zone** (hero / dark) and the
**content / light zone** (surface / surface-alt). A third zone — `dark`
Section — is used for BuildYourOrg and the SiteFooter as a closing band.

### Zone membership

| Zone | Token | Sections |
|---|---|---|
| Hero / dark | `--ds-hero-bg` (`#0b0e12`) | SiteNav, Hero, StatStrip, InstallTerminal (panel), BuildYourOrg, SiteFooter; also: loop-card install code, cat-card install blocks |
| Content / light | `--ds-surface` (`#fafaf9`) | HumanGates, AdapterMatrix, PackCatalogue |
| Content / light (alt) | `--ds-surface-alt` (`#f0efed`) | ThreeLoops, InstallTerminal (outer), PackCard |

### Zone rules

1. **One dark zone** in the page flow — the hero band (Nav → Hero → StatStrip).
   A second dark band at the page end (BuildYourOrg → SiteFooter) reads as
   a closure, not an interruption.
2. **Component foreground follows zone.** In the dark zone, all foreground
   tokens are `--ds-hero-fg*`. In the content zone, foreground tokens are
   `--ds-on-surface*`.
3. **Accent renders differently by zone.** On dark: `--ds-accent`
   (`#e8952b`) is used directly (sufficient contrast on dark). On light:
   `--ds-accent-deep` (`#8b5e0a`) is used for text (≥4.5:1 on neutral-50);
   `--ds-accent-subtle` is used for fills.
4. **No cross-zone raw values.** Component CSS never reads a primitive directly.
   Zone assignment is implicit in the Section tone, not hardcoded per component.

---

## 6. Dark Mode Equivalents

### Astro marketing site — no `prefers-color-scheme` dark mode

The Astro marketing site (`web/`) has no `@media (prefers-color-scheme: dark)`
block. Dark zone is a **layout property** — specific sections (Hero, Nav,
BuildYourOrg, SiteFooter) render on `--ds-hero-bg`, which happens to be dark.
The rest of the page is always light. There is no user-preference dark mode
for the marketing site.

### MkDocs docs site — dark mode via Material

Dark mode is present only in the MkDocs docs layer (`site/docs/stylesheets/extra.css`),
via Material for MkDocs's `[data-md-color-scheme="slate"]` attribute toggle.
MkDocs loads `tokens.css` (generated by `build-site.py` from the canonical
`web/src/styles/tokens.css`), so `--ds-*` and `--prim-*` tokens are available.

The dark mode overrides in `[data-md-color-scheme="slate"]`:

| Property overridden | Token reference | Resolved hex | Role |
|---|---|---|---|
| `--md-default-bg-color` | `var(--prim-dark-950)` | `#0b0e12` | Page / surface background |
| `--md-code-bg-color` | `var(--prim-dark-900)` | `#111520` | Code block background |
| `--md-accent-fg-color` | `var(--ds-accent)` | `#e8952b` | Accent / interactive |
| `--md-typeset-a-color` | `var(--prim-amber-300)` | `#f5bc6a` | Link color |

---

## 7. Card Icon Parity Decision

### What exists

**ThreeLoops section (Section 4):** Each `.loop` item carries a `.loop__n`
element displaying an ordered numeric sequence badge (`01`, `02`, `03`).
These items represent **named steps in a sequential "how it works" narrative**
— a handoff chain where order matters.

**PackCatalogue section (Section 8):** `.loop-card` items (the three core
packs) and all catalogue/pack cards (`cat-card`, `pack-card`) carry **no
badge or icon**. These items are **unordered catalogue entries** — a collection
of tools, not a sequential workflow.

### Decision

The visual asymmetry — `.loop__n` badges on ThreeLoops, none on PackCatalogue
and catalogue cards — is **intentional**. The two sections have different content
types with different information architectures:

- **Ordered steps** → numeric badge communicates sequence
- **Unordered catalogue** → no badge; order is arbitrary

No badge or icon additions to catalogue cards or loop-cards are in scope.
This document records the decision so the question is closed.

---

## 8. Material-Injected Component Audit

### Why extra.css uses token references (not raw hex)

`build-site.py` generates `stylesheets/tokens.css` from `web/src/styles/tokens.css`
and lists it in `mkdocs.yml extra_css`. As a result, `--ds-*` and `--prim-*`
custom properties are available in the MkDocs build context, and
`site/docs/stylesheets/extra.css` can use token references throughout.
The only raw numeric values permitted in `extra.css` are: dimensionless ratios
(line-height), layout max-width, `clamp()` expressions, and computed alpha
composites that have no single token equivalent — each annotated with a comment.

### Material component families overridden

`extra.css` overrides the following Material for MkDocs component families:

| Component family | Selector(s) | Override type |
|---|---|---|
| Header | `.md-header` | Dark background, text colors |
| Navigation tabs | `.md-tabs` | Same dark zone as header |
| Primary button | `.md-button--primary` | Amber CTA fill + border |
| Cards grid | `.grid.cards > ul > li`, `.grid.cards > ol > li` | Light alt surface, border reveal on hover |
| Inline code | `.md-typeset code` | Border radius |
| Code block | `.md-typeset pre > code` | Mono size + leading |
| Table | `.md-typeset table:not([class])` | Small font, surface-alt header |
| Announcement bar | `.md-banner` | Dark background |
| Platform back-link | `.platform-back-link` | Amber mono link |

### Four known default values from Material for MkDocs (≥9.5, <10)

Material for MkDocs ships its own bundled CSS with several color defaults
that differ from the `--ds-*` / `--prim-*` token spec. These are **not in
`extra.css`** — they are Material's bundled defaults that our overrides only
partially displace. Where `extra.css` does override them, it uses `var(--ds-*)`
/ `var(--prim-*)` token references.

| Material default value | Material CSS context | Token-spec closest equivalent |
|---|---|---|
| `#f8fafc` | Primary text on dark (slate scheme default) | `--ds-hero-fg: #ffffff` |
| `#141516` | Code block bg (slate scheme default, overridden by `extra.css` to `var(--prim-dark-900)` = `#111520`) | `--prim-dark-900: #111520` |
| `#1a202c` | Table header text (slate scheme default) | `--prim-neutral-900: #1c1b18` |
| `#e2e8f0` | Table border (slate scheme default) | No primitive-scale equivalent |

These values live in Material's bundled theme CSS (`pip install mkdocs-material`),
not in the tracked `site/` tree. Verifying or fixing them requires inspecting the
installed package. Fixing the deviation from `--ds-*` tokens would require
replacing Material's defaults with `extra.css` overrides or adding new token steps.

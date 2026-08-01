# Platform Site Design System

> Token reference and component vocabulary for `web/` (the Astro marketing site).
> All values are derived from `web/src/styles/tokens.css` — the implementation authority.
> Do not edit token values here without first updating `tokens.css`.

## 1. Color tokens

Three-tier architecture: **Tier 1 primitives** (`--prim-*`) define raw scale values.
**Tier 2 semantics** (`--ds-*`) map primitives to roles. **Component CSS** references
semantic tokens only — never primitives directly.

### Tier 1 — Primitive color scale

**Dark zone**

| Token | Hex | Role |
| --- | --- | --- |
| `--prim-dark-950` | `#0b0e12` | Hero canvas — neutral-cool near-black |
| `--prim-dark-900` | `#111520` | Dark card / elevated on hero |
| `--prim-dark-800` | `#1a2035` | Dark elevated overlay on hero |
| `--prim-dark-700` | `#232b40` | Dark border-visible surface |

**Neutral / light zone**

| Token | Hex | Role |
| --- | --- | --- |
| `--prim-neutral-50`  | `#fafaf9` | Content surface — warm near-white |
| `--prim-neutral-100` | `#f0efed` | Alt surface — card background |
| `--prim-neutral-200` | `#e0ddd9` | Border on light |
| `--prim-neutral-300` | `#c4c0bb` | Muted border |
| `--prim-neutral-400` | `#9c9891` | Placeholder, disabled |
| `--prim-neutral-600` | `#6b6760` | Secondary text |
| `--prim-neutral-800` | `#2e2c28` | Primary text |
| `--prim-neutral-900` | `#1c1b18` | Heading text |

**Amber-gold accent** (the single chromatic accent)

| Token | Hex | Role |
| --- | --- | --- |
| `--prim-amber-50`  | `#fff8e8` | — |
| `--prim-amber-100` | `#fdecc9` | — |
| `--prim-amber-200` | `#fad49a` | — |
| `--prim-amber-300` | `#f5bc6a` | Light decorative glow |
| `--prim-amber-400` | `#e8952b` | Primary accent — CTA, icon, stat |
| `--prim-amber-500` | `#c8780a` | Darker variant |
| `--prim-amber-700` | `#8b5e0a` | Text-safe on light (≥4.5:1 on neutral-50) |
| `--prim-amber-900` | `#4a3005` | Deep, for dark-on-amber text |

**Functional state primitives** (not identity colors; amber-gold is the sole chromatic accent)

| Role | bg | border | mid | fg | deep |
| --- | --- | --- | --- | --- | --- |
| success | `--prim-green-100` `#dcfce7` | `--prim-green-300` `#86efac` | `--prim-green-500` `#22c55e` | `--prim-green-700` `#15803d` | `--prim-green-900` `#14532d` |
| danger  | `--prim-red-100` `#fee2e2`   | `--prim-red-300` `#fca5a5`   | `--prim-red-500` `#ef4444`   | `--prim-red-700` `#b91c1c`   | `--prim-red-900` `#7f1d1d`   |
| warn    | `--prim-orange-100` `#ffedd5` | `--prim-orange-300` `#fdba74` | `--prim-orange-500` `#f97316` | `--prim-orange-700` `#c2410c` | `--prim-orange-900` `#7c2d12` |
| info    | `--prim-blue-100` `#dbeafe`  | `--prim-blue-300` `#93c5fd`  | `--prim-blue-500` `#3b82f6`  | `--prim-blue-700` `#1d4ed8`  | `--prim-blue-900` `#1e3a8a`  |

**Alpha tokens**

| Token | Value |
| --- | --- |
| `--prim-white-06` | `rgba(255, 255, 255, 0.06)` |
| `--prim-white-10` | `rgba(255, 255, 255, 0.10)` |
| `--prim-white-20` | `rgba(255, 255, 255, 0.20)` |
| `--prim-white-60` | `rgba(255, 255, 255, 0.60)` |
| `--prim-white-80` | `rgba(255, 255, 255, 0.80)` |
| `--prim-black-06` | `rgba(0, 0, 0, 0.06)` |
| `--prim-black-12` | `rgba(0, 0, 0, 0.12)` |
| `--prim-amber-10` | `rgba(232, 149, 43, 0.10)` |
| `--prim-amber-15` | `rgba(232, 149, 43, 0.15)` |
| `--prim-amber-20` | `rgba(232, 149, 43, 0.20)` |

### Tier 2 — Semantic color tokens

**Hero / dark zone** (SiteNav, Hero, StatStrip, BuildYourOrg, SiteFooter, install blocks)

| Token | Maps to | Role |
| --- | --- | --- |
| `--ds-hero-bg`          | `--prim-dark-950`  | Canvas background |
| `--ds-hero-surface`     | `--prim-dark-900`  | Card on dark |
| `--ds-hero-elevated`    | `--prim-dark-800`  | Elevated card on dark |
| `--ds-hero-fg`          | `#ffffff`          | Primary text on dark |
| `--ds-hero-fg-2`        | `--prim-white-80`  | Secondary text on dark |
| `--ds-hero-fg-muted`    | `--prim-white-60`  | Muted / caption on dark |
| `--ds-hero-border`      | `--prim-white-06`  | Hairline divider on dark |
| `--ds-hero-border-card` | `--prim-white-10`  | Card border on dark |

**Content / light zone** (HumanGates, AdapterMatrix, PackCatalogue card bodies, PackCard, cat-card bodies)

| Token | Maps to | Role |
| --- | --- | --- |
| `--ds-surface`          | `--prim-neutral-50`  | Page / section background |
| `--ds-surface-alt`      | `--prim-neutral-100` | Card background |
| `--ds-on-surface`       | `--prim-neutral-900` | Heading text |
| `--ds-on-surface-2`     | `--prim-neutral-800` | Body text |
| `--ds-on-surface-muted` | `--prim-neutral-600` | Captions, metadata |
| `--ds-border`           | `--prim-neutral-200` | Card, section border |
| `--ds-border-subtle`    | `--prim-black-06`    | Hairline, lowest weight |

**Accent layer** (amber-gold)

| Token | Maps to | Role |
| --- | --- | --- |
| `--ds-accent`           | `--prim-amber-400` | Icon, CTA fill on dark, stat number |
| `--ds-accent-deep`      | `--prim-amber-700` | Text-safe on light (4.5:1+) |
| `--ds-accent-subtle`    | `--prim-amber-10`  | Low-opacity fill on light |
| `--ds-accent-subtle-dk` | `--prim-amber-15`  | Low-opacity fill on dark |
| `--ds-accent-glow`      | `--prim-amber-20`  | Ambient glow, gate pulses |

**CTA buttons**

| Token | Maps to | Role |
| --- | --- | --- |
| `--ds-cta-primary-bg`         | `--prim-amber-400`  | Primary on dark hero: amber fill |
| `--ds-cta-primary-fg`         | `--prim-dark-950`   | Primary on dark hero: near-black text |
| `--ds-cta-primary-bg-hover`   | `--prim-amber-300`  | Primary hover |
| `--ds-cta-ghost-border`       | `--prim-white-20`   | Ghost on dark: border |
| `--ds-cta-ghost-fg`           | `--prim-white-80`   | Ghost on dark: text |
| `--ds-cta-ghost-bg-hover`     | `--prim-white-10`   | Ghost on dark: hover fill |
| `--ds-cta-ghost-light-border` | `--prim-amber-400`  | Ghost on light: amber border |
| `--ds-cta-ghost-light-fg`     | `--prim-amber-700`  | Ghost on light: deep amber text |

**State roles** (functional only)

| Role    | bg token (→ primitive)                         | fg token (→ primitive)                         | border token (→ primitive)                         |
| ------- | ---------------------------------------------- | ---------------------------------------------- | -------------------------------------------------- |
| success | `--ds-state-success-bg` → `--prim-green-100`   | `--ds-state-success-fg` → `--prim-green-700`   | `--ds-state-success-border` → `--prim-green-300`   |
| danger  | `--ds-state-danger-bg` → `--prim-red-100`      | `--ds-state-danger-fg` → `--prim-red-700`      | `--ds-state-danger-border` → `--prim-red-300`      |
| warn    | `--ds-state-warn-bg` → `--prim-orange-100`     | `--ds-state-warn-fg` → `--prim-orange-700`     | `--ds-state-warn-border` → `--prim-orange-300`     |
| info    | `--ds-state-info-bg` → `--prim-blue-100`       | `--ds-state-info-fg` → `--prim-blue-700`       | `--ds-state-info-border` → `--prim-blue-300`       |
| neutral | `--ds-state-neutral-bg` → `--prim-neutral-100` | `--ds-state-neutral-fg` → `--prim-neutral-800` | `--ds-state-neutral-border` → `--prim-neutral-300` |

## 2. Typography

### Font families

| Token | Value | Usage |
| --- | --- | --- |
| `--ds-font-sans` | `'Inter Variable', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif` | All body text, headings, UI labels |
| `--ds-font-mono` | `'JetBrains Mono', ui-monospace, 'SF Mono', 'Cascadia Code', Menlo, Consolas, monospace` | Code, terminal, stats, install commands, loop step numbers |

### Type scale

| Token | Value | px range | Usage |
| --- | --- | --- | --- |
| `--ds-type-display`  | `clamp(2.75rem, 5.5vw, 4rem)`    | ~44–64px | Hero headline |
| `--ds-type-h2`       | `clamp(1.875rem, 3.5vw, 2.5rem)` | ~30–40px | Section headings |
| `--ds-type-h3`       | `clamp(1.25rem, 2vw, 1.5rem)`    | ~20–24px | Card headings, sub-section |
| `--ds-type-body-lg`  | `1.125rem`                        | 18px     | Lead / intro copy |
| `--ds-type-body`     | `1rem`                            | 16px     | Body text |
| `--ds-type-sm`       | `0.875rem`                        | 14px     | Captions, metadata |
| `--ds-type-xs`       | `0.75rem`                         | 12px     | Labels, badges, eyebrows |
| `--ds-type-mono-sm`  | `0.8125rem`                       | 13px     | Inline code, skill names, install commands |

### Weight scale

| Token | Value | Usage |
| --- | --- | --- |
| `--ds-weight-regular`  | `400` | Body text |
| `--ds-weight-medium`   | `500` | Emphasis |
| `--ds-weight-semibold` | `600` | Card names, CTAs, metadata labels |
| `--ds-weight-bold`     | `700` | Strong emphasis |
| `--ds-weight-heavy`    | `800` | Hero headline, stat numbers |

### Tracking (letter-spacing)

| Token | Value | Usage |
| --- | --- | --- |
| `--ds-track-display` | `-0.03em` | Required at display sizes — optical tightening |
| `--ds-track-heading` | `-0.02em` | Slightly negative at h2/h3 |
| `--ds-track-label`   | `0.08em`  | Uppercase monospace labels |
| `--ds-track-normal`  | `0em`     | Body — never deviate |

### Leading (line-height)

| Token | Value | Usage |
| --- | --- | --- |
| `--ds-lead-display` | `1.1`  | Tight for display size |
| `--ds-lead-heading` | `1.25` | Slightly open for h2/h3 |
| `--ds-lead-body`    | `1.65` | Comfortable reading |
| `--ds-lead-mono`    | `1.5`  | Code and terminal |

## 3. Spacing, radius, shadow, motion, z-index

### Spacing — 4px base grid

| Token | Value | Usage |
| --- | --- | --- |
| `--ds-space-1`  | `4px`   | Tight icon gap, micro-nudge |
| `--ds-space-2`  | `8px`   | Component internal gap |
| `--ds-space-3`  | `12px`  | Row gap, caption spacing |
| `--ds-space-4`  | `16px`  | Element gap, margin between short text blocks |
| `--ds-space-5`  | `24px`  | Card grid gap, section-internal rhythm |
| `--ds-space-6`  | `32px`  | Card padding, larger internal blocks |
| `--ds-space-7`  | `48px`  | Medium section spacing |
| `--ds-space-8`  | `64px`  | Large section spacing |
| `--ds-space-9`  | `96px`  | Extra-large, between major content blocks |
| `--ds-space-10` | `128px` | Maximum, layout-level separation |

**Responsive layout tokens**

| Token | Value | Role |
| --- | --- | --- |
| `--ds-section-gap`   | `clamp(5rem, 10vw, 8rem)`        | Between major section bands |
| `--ds-section-pad-y` | `clamp(4rem, 8vw, 6rem)`         | Internal section top/bottom padding |
| `--ds-content-max`   | `1140px`                          | Maximum content width |
| `--ds-content-pad-x` | `clamp(1.25rem, 5vw, 2.5rem)`    | Horizontal page margin |

### Radius

| Token | Value | Usage |
| --- | --- | --- |
| `--ds-radius-sm`   | `4px`    | Inline code, badges, chips |
| `--ds-radius-md`   | `8px`    | Cards, inputs |
| `--ds-radius-lg`   | `12px`   | Modals, large cards |
| `--ds-radius-pill` | `9999px` | CTA buttons |

### Shadow — border-not-shadow philosophy

Borders define surfaces; decorative shadows are avoided. One exception:

| Token | Value | Usage |
| --- | --- | --- |
| `--ds-shadow-overlay` | `0 20px 60px rgba(0, 0, 0, 0.25)` | Modals, dropdowns |
| `--ds-shadow-none`    | `none`                             | Explicit no-shadow reset |

### Motion

| Token | Value | Usage |
| --- | --- | --- |
| `--ds-dur-quick`    | `120ms`                       | Micro-interactions (copy button) |
| `--ds-dur-moderate` | `200ms`                       | Standard transitions (card hover) |
| `--ds-dur-gentle`   | `300ms`                       | Soft entrances |
| `--ds-ease-std`     | `cubic-bezier(0.4, 0, 0.2, 1)` | Standard easing |
| `--ds-ease-out`     | `cubic-bezier(0, 0, 0.2, 1)`  | Deceleration-only |

All transitions must be suppressed under `@media (prefers-reduced-motion: reduce)`.

### Z-index

| Token | Value | Usage |
| --- | --- | --- |
| `--ds-z-base`    | `0`   | Default, in-flow |
| `--ds-z-raised`  | `10`  | Sticky elements, floating labels |
| `--ds-z-overlay` | `100` | Nav drawer, dropdowns |
| `--ds-z-modal`   | `200` | Modal dialogs |
| `--ds-z-toast`   | `300` | Toast / snackbar notifications |

## 4. Component vocabulary

All components use BEM naming. Zone assignment determines which semantic token set each
component draws from.

> **Zone key:** `dark` = hero/dark layer (`--ds-hero-*`); `surface` = content/light layer
> (`--ds-surface`, `--ds-on-surface*`); `surface-alt` = alternate light layer (`--ds-surface-alt`).

> **Key tokens scope:** each entry lists the zone-defining color, typography, and motion tokens
> most specific to that component. Per-component spacing values (`--ds-space-*`) are not listed
> individually — they are documented in §3 and used uniformly across all components.

### Hero (`Hero.astro`)

**Zone:** dark  
**BEM classes:** `.hero`, `.hero__inner`, `.hero__headline`, `.hero__subhead`, `.hero__actions`,
`.hero__cta`, `.hero__cta--primary`, `.hero__cta--ghost`, `.hero__friction`  
**Key tokens:** `--ds-hero-bg`, `--ds-hero-fg`, `--ds-hero-fg-2`, `--ds-hero-fg-muted`,
`--ds-accent-glow`, `--ds-hero-border`, `--ds-content-max`, `--ds-content-pad-x`,
`--ds-cta-primary-bg`, `--ds-cta-primary-fg`, `--ds-cta-primary-bg-hover`,
`--ds-cta-ghost-fg`, `--ds-cta-ghost-border`, `--ds-cta-ghost-bg-hover`,
`--ds-radius-pill`, `--ds-type-body-lg`, `--ds-type-body`, `--ds-type-xs`,
`--ds-weight-semibold`, `--ds-dur-gentle`, `--ds-ease-out`

---

### StatStrip (`StatStrip.astro`)

**Zone:** dark  
**BEM classes:** `.stats`, `.stats__list`, `.stats__item`, `.stats__number`, `.stats__label`  
**Key tokens:** `--ds-hero-bg`, `--ds-hero-border`, `--ds-accent`, `--ds-hero-fg-muted`,
`--ds-font-mono`, `--ds-type-h2`, `--ds-weight-heavy`, `--ds-track-label`

---

### ThreeLoops (`ThreeLoops.astro`)

**Zone:** surface-alt (full section — `<Section tone="surface-alt">`; `.loop` items have no background override)  
**BEM classes:** `.loops`, `.loops__headline`, `.loop`, `.loop__n`, `.loop__body`, `.loop__name`,
`.loop__pack`, `.loop__desc`, `.loop__gate`, `.loop__link`, `.pipeline`, `.pipeline__node`,
`.pipeline__link`, `.pipeline__gate`, `.pipeline__arrow`  
**Key tokens:** `--ds-accent-deep`, `--ds-accent-subtle`, `--ds-font-mono`, `--ds-type-h3`,
`--ds-type-xs`  
**Note:** `.loop__n` carries the ordered step badge (01 / 02 / 03) — `color: --ds-accent-deep`,
`font-family: --ds-font-mono`, `font-size: --ds-type-h3`. See §7 (Card icon parity).

---

### HumanGates (`HumanGates.astro`)

**Zone:** surface  
**BEM classes:** `.gates__headline`, `.gates__accent`, `.gates__subhead`, `.gates__grid`,
`.gate-card`, `.gate-card__top`, `.gate-card__id`, `.gate-card__loop`, `.gate-card__name`,
`.gate-card__decide`, `.gates__cta`  
**Key tokens:** `--ds-surface-alt`, `--ds-border`, `--ds-accent`, `--ds-accent-deep`,
`--ds-radius-md`, `--ds-on-surface-2`, `--ds-on-surface-muted`  
**Note:** `.gate-card` has an amber left-border accent (`--ds-accent`); `.gate-card__id` uses `--ds-accent-deep`.

---

### AdapterMatrix (`AdapterMatrix.astro`)

**Zone:** surface  
**BEM classes:** `.adapters__headline`, `.adapters__scroll`, `.adapters__table`,
`.cap`, `.cap--yes`, `.cap--no`, `.adapters__note`  
**Key tokens:** `--ds-border`, `--ds-border-subtle`, `--ds-surface-alt`, `--ds-on-surface`,
`--ds-on-surface-muted`, `--ds-accent-deep`, `--ds-radius-md`, `--ds-font-mono`  
**Note:** `.cap--yes` uses `--ds-accent-deep`; `.cap--no` uses `--ds-on-surface-muted`.

---

### InstallTerminal (`InstallTerminal.astro`)

**Zone:** surface-alt (outer wrapper) / dark (terminal window)  
**BEM classes:** `.install__headline`, `.terminal`, `.terminal__bar`, `.terminal__dot`,
`.tabs`, `.tabs__radio`, `.tabs__label`, `.tabs__panels`, `.tabs__panel`,
`.tabs__panel--flagship`, `.tabs__panel--discovery`, `.tabs__panel--inception`,
`.tabs__panel--architect` (one per tab; CSS-only visibility depends on these modifiers),
`.terminal__line`, `.terminal__prompt`, `.install__note`, `.copy-btn.install-copy-btn`  
**Key tokens:** `--ds-hero-bg`, `--ds-hero-border-card`, `--ds-hero-border`,
`--ds-hero-elevated`, `--ds-hero-fg`, `--ds-hero-fg-2`, `--ds-hero-fg-muted`,
`--ds-accent`, `--ds-accent-subtle-dk`, `--ds-font-mono`,
`--ds-radius-lg`, `--ds-radius-pill`  
**Note:** Tab switching is CSS-only via hidden radio inputs (`<input type="radio">`) — zero JS.

---

### PackCatalogue (`PackCatalogue.astro`)

**Zone:** surface (loop cards and pack grid) — with a dark sub-zone for
`.loop-card__install code` (uses `--ds-hero-bg` / `--ds-hero-fg`)  
**BEM classes:** `.catalogue__headline`, `.catalogue__subhead`, `.loop-cards`, `.loop-card`,
`.loop-card__head`, `.loop-card__name`, `.loop-card__desc`, `.loop-card__install`,
`.loop-card__link`, `.catalogue__more`, `.catalogue__summary`, `.catalogue__summary-arrow`,
`.catalogue__group`, `.catalogue__group-title`, `.pack-grid`, `.pack-card`,
`.pack-card__name`, `.pack-card__desc`  
**Key tokens:** `--ds-surface-alt`, `--ds-border`, `--ds-radius-lg`, `--ds-on-surface-2`,
`--ds-on-surface-muted`, `--ds-accent`, `--ds-accent-deep`,
`--ds-hero-bg`, `--ds-hero-fg` (install code sub-zone)  
**Note:** `.loop-card` items carry no numeric badge — contrast with ThreeLoops §7.

---

### BuildYourOrg (`BuildYourOrg.astro`)

**Zone:** dark  
**BEM classes:** `.org`, `.org__headline`, `.org__body`, `.org__cta`  
**Key tokens:** `--ds-hero-bg`, `--ds-hero-fg`, `--ds-hero-fg-2`, `--ds-type-display`,
`--ds-cta-primary-bg`, `--ds-cta-primary-fg`

---

### Section band (`Section.astro`)

**Variants:** `--surface` / `--surface-alt` / `--dark`  
**BEM classes:** `.section`, `.section--surface`, `.section--surface-alt`, `.section--dark`,
`.section__inner`  
**Role:** Reusable full-width band wrapper. Sets background zone and constrains `max-width`
via `--ds-content-max`. Three tone variants map to the three zone levels.

---

### SiteNav (`SiteNav.astro`)

**Zone:** dark  
**BEM classes:** `.nav`, `.nav__inner`, `.nav__logo`, `.nav__links`, `.nav__link`,
`.nav__link--docs`, `.nav__cta`, `.nav__mobile`, `.nav__toggle`, `.nav__burger`, `.nav__drawer`  
**Key tokens:** `--ds-hero-bg`, `--ds-hero-border`, `--ds-hero-fg`, `--ds-accent`,
`--ds-cta-primary-bg`, `--ds-cta-primary-fg`  
**Note:** Mobile menu via `<details>/<summary>` — zero JS.

---

### SiteFooter (`SiteFooter.astro`)

**Zone:** dark  
**BEM classes:** `.footer`, `.footer__inner`, `.footer__brand`, `.footer__links`, `.footer__copy`  
**Key tokens:** `--ds-hero-bg`, `--ds-hero-fg`, `--ds-hero-fg-muted`, `--ds-hero-fg-2`

---

### PackCard — `/packs/` index (`PackCard.astro`)

**Zone:** surface  
**BEM classes:** `.pack-card`, `.pack-card__link`, `.pack-card__head`, `.pack-card__name`,
`.pack-card__tagline`, `.pack-card__cta`  
**Key tokens:** `--ds-surface-alt`, `--ds-border`, `--ds-radius-lg`, `--ds-on-surface`,
`--ds-on-surface-2`, `--ds-accent-deep`, `--ds-type-h3`, `--ds-type-body`, `--ds-type-sm`,
`--ds-dur-moderate`, `--ds-ease-std`

---

### Catalogue card — `/catalogue/` (`catalogue/index.astro`)

**Zone:** surface (card body) / dark (install blocks)  
**BEM classes:** `.cat-hero`, `.cat-hero__inner`, `.cat-hero__eyebrow`, `.cat-hero__heading`,
`.cat-hero__body`, `.cat-grid`, `.cat-card`, `.cat-card__head`, `.cat-card__name-row`,
`.cat-card__name`, `.cat-card__tagline`, `.cat-card__meta`, `.cat-card__skills`,
`.cat-card__detail-cta`, `.install-blocks`, `.install-block`, `.install-block--plugin`,
`.install-block__label`, `.install-block__row`, `.install-block__cmd`,
`.install-block__cmd--truncate`, `.copy-btn`  
**Key tokens (card body):** `--ds-surface-alt`, `--ds-border`, `--ds-radius-lg`,
`--ds-on-surface`, `--ds-accent-deep`  
**Key tokens (install blocks):** `--ds-hero-bg`, `--ds-hero-border`, `--ds-hero-elevated`,
`--ds-hero-fg`, `--ds-hero-fg-muted`, `--ds-accent`

---

### CopyButton (`CopyButton.astro`)

**Zone:** surface  
**BEM classes:** `.copy-btn`, `.copy-btn--success`, `.copy-btn__icon`, `.copy-btn__label`,
`.copy-btn__live` (aria-live region, visually hidden)  
**Key tokens:** `--ds-border`, `--ds-on-surface-muted`, `--ds-accent`, `--ds-accent-deep`,
`--ds-state-success-fg`, `--ds-state-success-border`, `--ds-radius-sm`,
`--ds-type-xs`, `--ds-dur-quick`, `--ds-ease-std`

## 5. Zone rules

Two primary zone levels:

| Zone | Background token | Text tokens | When to use |
| --- | --- | --- | --- |
| Dark | `--ds-hero-bg` | `--ds-hero-fg`, `--ds-hero-fg-2`, `--ds-hero-fg-muted` | Nav, hero, stat strip, CTA band, footer, install terminal |
| Content / light | `--ds-surface`, `--ds-surface-alt` | `--ds-on-surface`, `--ds-on-surface-2`, `--ds-on-surface-muted` | Cards, grids, table sections |

**Layering rule:** Component CSS references **semantic tokens only** — never Tier 1 primitives
directly. A component in the dark zone uses `--ds-hero-*` tokens; one in the light zone uses
`--ds-surface*` and `--ds-on-surface*` tokens. Mixing zone tokens across a single component
(e.g., a dark terminal embed inside a light card) is permitted when the inner element
explicitly targets its own zone.

## 6. Dark mode

The Astro marketing site page and component CSS (`web/src/`) has **no `prefers-color-scheme: dark`
media query**. Dark zone is a layout concept — specific sections use `--ds-hero-bg` as a design
property, not in response to user OS preference. Every component's zone is fixed at design time,
not toggled by user setting. Exception: `web/public/favicon.svg` does include a
`@media (prefers-color-scheme: dark)` rule to adjust the favicon fill in dark OS mode — this is
a standalone SVG asset and does not affect page or component CSS.

Dark mode equivalents exist only in the **Starlight docs-site** (`docs-site/src/styles/starlight.css`
via `[data-theme='dark']`, toggled by the Starlight theme switcher). The Starlight CSS imports
`tokens.css` at build time (`@import './tokens.css'`), so dark-mode color overrides use
`--prim-*` and `--ds-*` tokens directly rather than raw hex values.

Dark-mode resolved values (token → hex):

| Role | Token reference | Hex |
| --- | --- | --- |
| Docs surface background | `var(--prim-dark-950)` | `#0b0e12` |
| Sidebar / elevated surface | `var(--prim-dark-900)` | `#111520` |
| Accent / icon highlight | `var(--ds-accent)` | `#e8952b` |
| Link color | `var(--prim-amber-300)` | `#f5bc6a` |
| Inline code background | `var(--ds-accent-subtle-dk)` | `rgba(232,149,43,0.15)` |

## 7. Card icon parity decision

**Decision: intentional asymmetry — no change required.**

Two sections use visually similar card layouts with different information architectures:

| Section | Component | Numeric badge? | Reason |
| --- | --- | --- | --- |
| ThreeLoops | `.loop` items with `.loop__n` | Yes — 01 / 02 / 03 | Sequential "how it works" narrative; order is semantically meaningful |
| PackCatalogue | `.loop-card` items | No | Unordered catalogue entries; a badge would imply false ranking |
| `/packs/` index | `.pack-card` | No | Unordered catalogue entries |
| `/catalogue/` | `.cat-card` | No | Unordered catalogue entries |

The `.loop__n` badge in ThreeLoops uses `color: --ds-accent-deep` and `font-family: --ds-font-mono`
at `font-size: --ds-type-h3`. No badge or icon addition is in scope for this spec — this record
closes the question so it is not re-litigated in future PRs.

## 8. Starlight CSS audit

**Context:** the docs site migrated from MkDocs / Material for MkDocs to Starlight. The
previously planned audit of Material-injected raw-hex deviations (`.md-header`, `.md-tabs`,
etc.) no longer applies — those component classes do not exist in the current codebase.

The Starlight CSS (`docs-site/src/styles/starlight.css`) imports `tokens.css` at build time
(`@import './tokens.css'`) and maps Starlight's slot variables (`--sl-*`) to design-system
tokens. It is predominantly token-compliant. Known deviations:

| Location | Raw value | Closest `--ds-*` token | Note |
| --- | --- | --- | --- |
| `--sl-color-text-invert` (light-mode assignment) | `#ffffff` | `--ds-hero-fg` (`#ffffff`) | Used by Starlight's built-in UI for inverted text; same resolved value but a distinct semantic slot |
| `.site-footer__brand { color }` | `#ffffff` | `--ds-hero-fg` (`#ffffff`) | Bootstrap override for the Starlight footer brand; same resolved value |

Both deviations resolve to the same hex value as `--ds-hero-fg`. The `--sl-*` slot system
already cross-references `--ds-*` tokens elsewhere in `starlight.css` (e.g.
`--sl-color-accent: var(--ds-accent)`), so these two literals could technically be updated to
reference `--ds-hero-fg` instead. Doing so is out of scope for this spec — they are documented
as known current deviations, not necessary architectural exceptions.

The zone-violation lint (`tools/lint_zone_violations.py`) scans `web/src/` only.
`docs-site/src/styles/starlight.css` is intentionally outside its scope — the two `#ffffff`
deviations documented above are known current deviations that could be token references, not
violations that should be suppressed.

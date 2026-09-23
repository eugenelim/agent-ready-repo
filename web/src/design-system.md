# Platform Site Design System

> Token reference and component vocabulary for `web/` (the Astro marketing site).
> All values are derived from `web/src/styles/tokens.css` — the implementation
> authority. Do not edit token values here without first updating `tokens.css`.
>
> **§1 is generated, as of 2026-09-18.** It used to carry about forty hand-typed
> hex and rgba literals, and the paper-first palette change made every one of
> them wrong at a stroke — for long enough that this header carried a standing
> warning not to trust the document's own tables. Re-typing them would have
> bought one release. §1 is now projected from `tokens.css`:
>
> ```
> node scripts/generate-design-system.mjs          # rewrite §1
> node scripts/generate-design-system.mjs --check  # fail if it would change
> ```
>
> `src/test/design-system-projection.test.ts` runs the check, so §1 cannot
> drift from `tokens.css` without a test going red. Sections 2 onward are still
> written by hand and carry no generated guarantee; §4 and §5 were brought
> current by hand on 2026-09-18.
>
> Reasoning about a token belongs in `tokens.css`, beside the declaration,
> where the generator carries it into the table's Note column. Reasoning added
> only here is lost on the next regeneration.
>
> The palette is the **paper-first editorial** direction: paper throughout, the
> dark ground exactly once at the close, and one mark reserved for state — a
> refusal, a hold, a block. The reasoning is in
> `docs/design/direction/marketing-site.md`, which supersedes
> `docs/design/direction/tech-site-amendment-palette.md` on palette and layout.

## 1. Color tokens

<!-- GENERATED FROM web/src/styles/tokens.css — DO NOT EDIT BY HAND.
     Regenerate:  node scripts/generate-design-system.mjs
     Guarded by:  src/test/design-system-projection.test.ts

     Every value, mapping and note below is read out of tokens.css. Change
     a token there and regenerate; editing this section instead produces
     exactly the drift that made these tables wrong for a whole palette
     change. Reasoning about a token belongs in tokens.css beside it, where
     this generator can carry it forward. -->

Three-tier architecture: **Tier 1 primitives** (`--prim-*`) define raw scale values.
**Tier 2 semantics** (`--ds-*`) map primitives to roles. **Component CSS** references
semantic tokens only — never primitives directly.

This section lists the 105 colour-valued tokens in `tokens.css`.
Non-colour tokens are in §2 and §3.

### Tier 1 — Primitive color scale

| Token | Value | Note (from `tokens.css`) |
| --- | --- | --- |
| `--prim-ink-950` | `#14120f` | close-band ground; also the display ink on paper |
| `--prim-ink-900` | `#1c1a16` | raised on the dark ground — 1.08:1, decorative only |
| `--prim-ink-800` | `#26231e` | elevated on the dark ground — 1.19:1, decorative only |
| `--prim-ink-700` | `#4a443c` | hairline on the dark ground — 1.94:1, decorative only |
| `--prim-ink-300` | `#938d82` | muted ink on dark — 5.67:1 on ink-950 |
| `--prim-ink-200` | `#b8b2a6` | secondary ink on dark — 8.87:1 on ink-950 |
| `--prim-ink-50` | `#dcd8ce` | — |
| `--prim-record-50` | `#f7f5f0` | page ground |
| `--prim-record-100` | `#efece5` | alt band ground |
| `--prim-record-200` | `#ddd8cd` | card / section border — 1.30:1 on record-50, decorative only |
| `--prim-record-250` | `#cfc9bc` | — |
| `--prim-record-300` | `#c8c1b2` | neutral-state border — 1.64:1 on record-50, decorative only |
| `--prim-record-350` | `#b5ad9c` | decorative hairline — 2.05:1 on record-50, 1.89:1 on record-100 |
| `--prim-record-400` | `#9c9384` | placeholder, disabled — 2.79:1 on record-50 |
| `--prim-record-500` | `#8a8172` | — |
| `--prim-record-600` | `#6b655b` | field label, muted — 5.30:1 on record-50, 4.89:1 on record-100 |
| `--prim-record-700` | `#413c34` | — |
| `--prim-record-800` | `#2e2a24` | body ink — 13.09:1 on record-50, 12.09:1 on record-100 |
| `--prim-record-900` | `#14120f` | display ink — 17.16:1 on record-50, 15.85:1 on record-100 |
| `--prim-stamp-500` | `#c8654f` | mark on the dark close band — 4.83:1 on ink-950 |
| `--prim-stamp-700` | `#8c2f1f` | mark on paper — 7.58:1 on record-50, 7.00:1 on record-100 |
| `--prim-green-100` | `#dcfce7` | success bg |
| `--prim-green-300` | `#86efac` | success border |
| `--prim-green-500` | `#22c55e` | success mid |
| `--prim-green-700` | `#15803d` | success fg — text-safe on paper (4.60:1 on record-50) |
| `--prim-green-900` | `#14532d` | success deep |
| `--prim-red-100` | `#fee2e2` | danger bg |
| `--prim-red-300` | `#fca5a5` | danger border |
| `--prim-red-500` | `#ef4444` | danger mid |
| `--prim-red-700` | `#b91c1c` | danger fg — text-safe on paper (5.94:1 on record-50) |
| `--prim-red-900` | `#7f1d1d` | danger deep |
| `--prim-orange-100` | `#ffedd5` | warning bg — distinct from the mark |
| `--prim-orange-300` | `#fdba74` | warning border |
| `--prim-orange-500` | `#f97316` | warning mid |
| `--prim-orange-700` | `#c2410c` | warning fg — text-safe on paper (4.75:1 on record-50) |
| `--prim-orange-900` | `#7c2d12` | warning deep |
| `--prim-blue-100` | `#dbeafe` | info bg |
| `--prim-blue-300` | `#93c5fd` | info border |
| `--prim-blue-500` | `#3b82f6` | info mid |
| `--prim-blue-700` | `#1d4ed8` | info fg — text-safe on paper (6.15:1 on record-50) |
| `--prim-blue-900` | `#1e3a8a` | info deep |
| `--prim-white-06` | `rgba(255, 255, 255, 0.06)` | — |
| `--prim-white-10` | `rgba(255, 255, 255, 0.10)` | — |
| `--prim-white-20` | `rgba(255, 255, 255, 0.20)` | — |
| `--prim-white-60` | `rgba(255, 255, 255, 0.60)` | — |
| `--prim-white-80` | `rgba(255, 255, 255, 0.80)` | — |
| `--prim-black-06` | `rgba(0, 0, 0, 0.06)` | — |
| `--prim-black-12` | `rgba(0, 0, 0, 0.12)` | — |
| `--prim-stamp-10` | `rgba(200, 101, 79, 0.10)` | — |
| `--prim-stamp-15` | `rgba(200, 101, 79, 0.15)` | — |
| `--prim-stamp-20` | `rgba(200, 101, 79, 0.20)` | — |

### Tier 2 — Semantic color tokens

A semantic token names a ROLE. "Maps to" is what `tokens.css` declares;
"Resolves to" is the literal that mapping ends at, followed through every
`var()` hop — so a re-pointed primitive shows up here without anyone
retyping a hex.

**Dark zone — the close band, and the footer continuous with it**

| Token | Maps to | Resolves to | Note (from `tokens.css`) |
| --- | --- | --- | --- |
| `--ds-hero-bg` | `--prim-ink-950` | `#14120f` | #14120f close-band ground |
| `--ds-hero-surface` | `--prim-ink-900` | `#1c1a16` | raised on dark |
| `--ds-hero-elevated` | `--prim-ink-800` | `#26231e` | elevated on dark |
| `--ds-hero-fg` | `--prim-ink-50` | `#dcd8ce` | primary text on dark — 13.14:1 |
| `--ds-hero-fg-2` | `--prim-ink-200` | `#b8b2a6` | secondary text on dark — 8.87:1 |
| `--ds-hero-fg-muted` | `--prim-ink-300` | `#938d82` | muted / caption on dark — 5.67:1 |
| `--ds-hero-border` | `--prim-white-06` | `rgba(255, 255, 255, 0.06)` | — |
| `--ds-hero-border-card` | `--prim-white-10` | `rgba(255, 255, 255, 0.10)` | card border on dark |

**Paper zone — the whole page except the close band**

| Token | Maps to | Resolves to | Note (from `tokens.css`) |
| --- | --- | --- | --- |
| `--ds-surface` | `--prim-record-50` | `#f7f5f0` | #f7f5f0 page ground |
| `--ds-surface-alt` | `--prim-record-100` | `#efece5` | #efece5 alt band ground |
| `--ds-on-surface` | `--prim-record-900` | `#14120f` | display ink — 17.16:1 / 15.85:1 |
| `--ds-on-surface-2` | `--prim-record-800` | `#2e2a24` | body ink — 13.09:1 / 12.09:1 |
| `--ds-on-surface-muted` | `--prim-record-600` | `#6b655b` | muted ink — 5.30:1 / 4.89:1 |
| `--ds-border` | `--prim-record-200` | `#ddd8cd` | card, section border |
| `--ds-border-subtle` | `--prim-black-06` | `rgba(0, 0, 0, 0.06)` | hairline, lowest weight |
| `--ds-focus-ring` | `--ds-on-surface` | `#14120f` | — |

**Register roles — rules, fields, the clearance mark**

| Token | Maps to | Resolves to | Note (from `tokens.css`) |
| --- | --- | --- | --- |
| `--ds-rule-hairline` | `--prim-record-350` | `#b5ad9c` | divider within a record — non-text contrast floor |
| `--ds-rule-boundary` | `--prim-record-500` | `#8a8172` | edge of a record — non-text contrast floor |
| `--ds-rule-hairline-dk` | `--prim-ink-700` | `#4a443c` | — |
| `--ds-field-label` | `--prim-record-600` | `#6b655b` | field label, and the EYEBROW role |
| `--ds-clearance` | `--prim-stamp-700` | `#8c2f1f` | the mark, on paper |
| `--ds-clearance-dk` | `--prim-stamp-500` | `#c8654f` | the mark, on the dark close band |

**Accent — legacy aliases of the clearance stamp**

| Token | Maps to | Resolves to | Note (from `tokens.css`) |
| --- | --- | --- | --- |
| `--ds-accent` | `--prim-stamp-500` | `#c8654f` | unused |
| `--ds-accent-deep` | `--prim-stamp-700` | `#8c2f1f` | unused |
| `--ds-accent-subtle` | `--prim-stamp-10` | `rgba(200, 101, 79, 0.10)` | unused |
| `--ds-accent-subtle-dk` | `--prim-stamp-15` | `rgba(200, 101, 79, 0.15)` | unused |
| `--ds-accent-glow` | `--prim-stamp-20` | `rgba(200, 101, 79, 0.20)` | unused |

**CTA buttons**

| Token | Maps to | Resolves to | Note (from `tokens.css`) |
| --- | --- | --- | --- |
| `--ds-cta-primary-bg` | `--prim-record-900` | `#14120f` | — |
| `--ds-cta-primary-fg` | `--prim-record-50` | `#f7f5f0` | — |
| `--ds-cta-primary-bg-hover` | `--prim-record-800` | `#2e2a24` | — |
| `--ds-cta-primary-bg-active` | `--prim-record-700` | `#413c34` | — |
| `--ds-cta-ghost-border` | `--prim-record-500` | `#8a8172` | — |
| `--ds-cta-ghost-fg` | `--prim-ink-200` | `#b8b2a6` | — |
| `--ds-cta-ghost-bg-hover` | `--prim-white-10` | `rgba(255, 255, 255, 0.10)` | — |
| `--ds-cta-ghost-light-border` | `--prim-record-500` | `#8a8172` | — |
| `--ds-cta-ghost-light-fg` | `--prim-record-900` | `#14120f` | — |

**Pressed ground**

| Token | Maps to | Resolves to | Note (from `tokens.css`) |
| --- | --- | --- | --- |
| `--ds-surface-pressed` | `--prim-record-250` | `#cfc9bc` | — |
| `--ds-surface-pressed-dk` | `--prim-ink-700` | `#4a443c` | — |

**State roles — functional only; not identity colors**

| Token | Maps to | Resolves to | Note (from `tokens.css`) |
| --- | --- | --- | --- |
| `--ds-state-success-bg` | `--prim-green-100` | `#dcfce7` | — |
| `--ds-state-success-fg` | `--prim-green-700` | `#15803d` | — |
| `--ds-state-success-border` | `--prim-green-300` | `#86efac` | — |
| `--ds-state-danger-bg` | `--prim-red-100` | `#fee2e2` | — |
| `--ds-state-danger-fg` | `--prim-red-700` | `#b91c1c` | — |
| `--ds-state-danger-border` | `--prim-red-300` | `#fca5a5` | — |
| `--ds-state-warn-bg` | `--prim-orange-100` | `#ffedd5` | — |
| `--ds-state-warn-fg` | `--prim-orange-700` | `#c2410c` | — |
| `--ds-state-warn-fg-pressed` | `--prim-orange-900` | `#7c2d12` | — |
| `--ds-state-warn-border` | `--prim-orange-300` | `#fdba74` | — |
| `--ds-state-info-bg` | `--prim-blue-100` | `#dbeafe` | — |
| `--ds-state-info-fg` | `--prim-blue-700` | `#1d4ed8` | — |
| `--ds-state-info-border` | `--prim-blue-300` | `#93c5fd` | — |
| `--ds-state-neutral-bg` | `--prim-record-100` | `#efece5` | — |
| `--ds-state-neutral-fg` | `--prim-record-800` | `#2e2a24` | — |
| `--ds-state-neutral-border` | `--prim-record-300` | `#c8c1b2` | — |

### Scoped overrides

A token re-pointed for one carrier, in a rule that is not `:root`. The
value above is what the token is everywhere else.

| Token | Carrier (selector) | Maps to |
| --- | --- | --- |
| `--ds-focus-ring` | `:where(.section--dark, .footer)` | `--ds-hero-fg` |

## 2. Typography

### Font families

| Token | Value | Usage |
| --- | --- | --- |
| `--ds-font-sans` | `'Inter Variable', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif` | All body text, headings, UI labels |
| `--ds-font-mono` | `'JetBrains Mono', ui-monospace, 'SF Mono', 'Cascadia Code', Menlo, Consolas, monospace` | Code, terminal, stats, install commands, loop step numbers, receipt fields |

`'Inter Variable'` is the family name Fontsource registers for the variable package; `'Inter'`
remains for any static Inter, then system fallbacks.

### Type scale

| Token | Value | px range | Usage |
| --- | --- | --- | --- |
| `--ds-type-display`  | `clamp(2.75rem, 5.5vw, 4rem)`    | ~44–64px | Hero headline |
| `--ds-type-h2`       | `clamp(1.875rem, 3.5vw, 2.5rem)` | ~30–40px | Section headings |
| `--ds-type-h3`       | `clamp(1.25rem, 2vw, 1.5rem)`    | ~20–24px | Card headings, sub-section |
| `--ds-type-body-lg`  | `1.125rem`                        | 18px     | Lead / intro copy |
| `--ds-type-read`     | `1.0625rem`                       | 17px     | Editorial reading column |
| `--ds-type-body`     | `1rem`                            | 16px     | Body text |
| `--ds-type-sm`       | `0.875rem`                        | 14px     | Captions, metadata |
| `--ds-type-xs`       | `0.75rem`                         | 12px     | Labels, badges, field labels |
| `--ds-type-mono-sm`  | `0.8125rem`                       | 13px     | Inline code, skill names, install commands |
| `--ds-type-mono-xs`  | `0.6875rem`                       | 11px     | Mono micro-labels: eyebrows, badges, figure captions, record fields |

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
| `--ds-track-label`   | `0.08em`  | Wide tracking for **legacy uppercase** labels only |
| `--ds-track-normal`  | `0em`     | Body — never deviate |

`--ds-track-label` no longer means "uppercase label". Homepage field labels are sentence-case
and set their own lighter local tracking (the stat-strip label uses `0.02em`), because a field
label is a record field, not a decorative eyebrow. `--ds-track-label` survives for the surfaces
that still carry an uppercase label, and there are **sixteen** of them.

This sentence used to end "`/catalogue/` is the remaining consumer", and the
`### Catalogue records` block said the same thing in its own words. Both were false, and
false before the record-list change that found them. `grep -rl ds-track-label web/src/`
returns eighteen paths — this document, `tokens.css`, and sixteen consumers:
`JourneyContract`, `GateDetail`, `SkillRecord`, `NextAction`, `PromptBlock`,
`WriteConfirmation`, `StatusChip`, `PageHero`, `PageMeta`, `NowHighlights`,
`packs/[pack]`, `now/index`, `primitives-fixture`, `journeys/index`,
`journeys/[journey]` and `catalogue/index`. Every one of the sixteen also declares
`text-transform: uppercase`, so the narrower reading — "the pages that still carry an
uppercase label" — does not single `/catalogue/` out either. `StatusChip` is among them
and renders *on* `/catalogue/`, so the page was never even the sole consumer of its own
rendered output.

### Leading (line-height)

| Token | Value | Usage |
| --- | --- | --- |
| `--ds-lead-display` | `1.1`  | Tight for display size |
| `--ds-lead-heading` | `1.25` | Slightly open for h2/h3 |
| `--ds-lead-body`    | `1.65` | Comfortable reading |
| `--ds-lead-mono`    | `1.5`  | Code and terminal |

## 3. Spacing, radius, shadow, motion, z-index

### Rule pitch and spacing

| Token | Value | Usage |
| --- | --- | --- |
| `--ds-rule-pitch` | `8px` | The register's rule pitch. **Every vertical measure is an integer multiple of it.** |

Every spacing step is a multiple of the pitch, with one explicitly-called-out exception.

| Token | Value | × pitch | Usage |
| --- | --- | --- | --- |
| `--ds-space-1`  | `4px`   | ½ | **Half-pitch — inline use only** (icon-to-label gaps), never a vertical measure |
| `--ds-space-2`  | `8px`   | 1 | Component internal gap |
| `--ds-space-3`  | `8px`   | 1 | Tight clustered gap — icon+text, badge row, label glued to its heading |
| `--ds-space-4`  | `16px`  | 2 | Element gap, margin between short text blocks |
| `--ds-space-5`  | `24px`  | 3 | Card grid gap, section-internal rhythm |
| `--ds-space-6`  | `32px`  | 4 | Card padding, larger internal blocks |
| `--ds-space-7`  | `48px`  | 6 | Medium section spacing; also the annotation gap |
| `--ds-space-8`  | `64px`  | 8 | Large section spacing |
| `--ds-space-9`  | `96px`  | 12 | Extra-large, between major content blocks |
| `--ds-space-10` | `128px` | 16 | Maximum, layout-level separation |

`--ds-space-3` was `12px`, which is not a multiple of the pitch. It collapsed to `8px` rather
than widening to `16px`: most consumers are inline gaps between small clustered elements, where
tightening reads as "attached to", and `16px` would have made it numerically redundant with
`--ds-space-4`.

**Responsive layout tokens**

| Token | Value | Role |
| --- | --- | --- |
| `--ds-section-gap`   | `clamp(5rem, 10vw, 8rem)`     | Between major section bands |
| `--ds-section-pad-y` | Stepped per breakpoint — see below | Internal section top/bottom padding |
| `--ds-content-max`   | `1140px`                      | Maximum content width |
| `--ds-content-pad-x` | `clamp(1.25rem, 5vw, 2.5rem)` | Horizontal page margin |

`--ds-section-pad-y` is stepped, not fluid: a `vw`-driven clamp crosses non-multiples of the
8px pitch in its fluid middle (81.92px at 1024px, 68px at 850px). Fixed per-breakpoint values
keep every width on the pitch.

| Breakpoint | Value | px | × pitch |
| --- | --- | --- | --- |
| base (<768px)   | `4rem`   | 64px | 8 |
| ≥768px          | `4.5rem` | 72px | 9 |
| ≥1024px         | `5rem`   | 80px | 10 |
| ≥1280px         | `5.5rem` | 88px | 11 |
| ≥1440px         | `6rem`   | 96px | 12 |

**Annotation-margin geometry** — see §9.

| Token | Value | Role |
| --- | --- | --- |
| `--ds-annotation-col-min` | `20rem` (320px = 40 × pitch, padding included) | Narrowest the receipt column may be before it fights the text measure |
| `--ds-annotation-gap`     | `var(--ds-space-7)` (48px = 6 × pitch) | Content-to-margin gutter |

### Target size — the interactive floor

WCAG 2.2 SC 2.5.8 Target Size (Minimum), AA. Three times `--ds-rule-pitch`, so a control
that meets the floor also keeps the vertical rhythm rather than breaking it to satisfy the
criterion. Grow the TARGET, not the type: `/now/`'s pagination digits stay at
`--ds-type-sm` inside a 24px box.

| Token | Value | Usage |
| --- | --- | --- |
| `--ds-target-min` | `24px` | Minimum width and height of any interactive target |

### Radius — one idea, two steps

The pill is retired: a register has corners, not capsules. `--ds-radius-pill` is **deleted**
from `tokens.css`; every former pill consumer now takes `--ds-radius-md`.

| Token | Value | Usage |
| --- | --- | --- |
| `--ds-radius-sm` | `2px`  | Inline code, badges, chips |
| `--ds-radius-md` | `6px`  | Cards, inputs, CTA buttons (was the pill) |
| `--ds-radius-lg` | `10px` | Modals, large cards |

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

> **Zone key:** `surface` = paper (`--ds-surface`, `--ds-on-surface*`); `surface-alt` =
> alternate paper band (`--ds-surface-alt`); `dark` = the ONE dark ground
> (`--ds-hero-*`), which appears exactly once on the surface, at the close, with the footer
> continuous with it. Every other band is paper. The nav, the hero, the page heroes, the
> install terminal, the 404 and the pack/journey install blocks were all `dark` before
> 2026-09-18 and are now `surface` (marketing-site.md, Owner decisions 2026-09-18).

> **Key tokens scope:** each entry lists the zone-defining color, typography, and motion tokens
> most specific to that component. Per-component spacing values (`--ds-space-*`) are not listed
> individually — they are documented in §3 and used uniformly across all components.

### Hero (`Hero.astro`) — zone 1, above the fold

**Zone:** surface (paper)
**BEM classes:** `.hero`, `.hero__inner`, `.hero__lede`, `.hero__headline`, `.hero__subhead`,
`.hero__actions`, `.hero__cta`, `.hero__cta--primary`, `.hero__cta--ghost`, `.hero__proof`,
`.hero__friction`, `.hero__fineprint`, `.hero__figure`, and the transcript figure's own
`.rec`, `.rec__title`, `.rec__group`, `.rec__group--held`, `.rec__row`, `.rec__row--held`,
`.rec__note`, `.rec__cap`
**Key tokens:** `--ds-surface`, `--ds-on-surface`, `--ds-on-surface-2`,
`--ds-on-surface-muted`, `--ds-rule-boundary`, `--ds-rule-hairline`, `--ds-clearance`,
`--ds-cta-primary-bg`, `--ds-cta-primary-fg`, `--ds-cta-primary-bg-hover`,
`--ds-cta-ghost-light-fg`, `--ds-content-max`, `--ds-content-pad-x`, `--ds-radius-md`,
`--ds-font-mono`, `--ds-rule-pitch`, `--ds-type-h2`, `--ds-type-body-lg`, `--ds-type-body`,
`--ds-type-sm`, `--ds-type-xs`, `--ds-type-mono-sm`,
`--ds-weight-medium`, `--ds-weight-semibold`, `--ds-dur-gentle`, `--ds-ease-out`
**Note:** the ruled grid texture and the radial accent glow are both withdrawn — `[none]`
ornament. The band carries, in order, headline, subhead, two CTAs, an inline proof line read
from `receipts.generated.json`, one friction line, and the agent-agnosticism fine print. The
typeset transcript sits in an image track beside the reading column above 1100px and reflows
under the lede below it; it is never hidden. `.rec__row--held dd` is one of the two remaining
consumers of `--ds-clearance` on the whole site, and HELD is carried by case, weight and the
heavier rule as well as by the mark.

---

### TheProblem (`TheProblem.astro`) — zone 2

**Zone:** surface-alt
**BEM classes:** `.problem`, `.problem__headline`, `.problem__cost`, `.problem__body`
**Key tokens:** `--ds-surface-alt`, `--ds-on-surface`, `--ds-on-surface-2`,
`--ds-type-body-lg`
**Note:** two paragraphs, and the order is the content. `.problem__cost` states what the
status quo costs the reader; `.problem__body` is the page's pre-existing product insight,
moved and NOT rewritten (content brief, 2026-09-18 amendment, claim 1).

---

### TheModel (`TheModel.astro`) — zone 3

**Zone:** surface (`<Section tone="surface" annotated>`)
**BEM classes:** `.model__headline`, `.model__sentence`, `.model__list`, `.actor`,
`.actor.annotation-row`, `.actor__n`, `.actor__body`, `.actor__who`, `.actor__does`,
`.actor__desc`, `.model__link`
**Key tokens:** `--ds-surface`, `--ds-on-surface`, `--ds-on-surface-2`,
`--ds-on-surface-muted`, `--ds-field-label`, `--ds-font-mono`, `--ds-type-h3`,
`--ds-type-body-lg`, `--ds-type-sm`, `--ds-weight-regular`, `--ds-weight-semibold`
**Note:** replaces `ThreeLoops` and `HumanGates`, which told the work lifecycle twice and
carried eleven internal gate identifiers onto a surface whose plain-language floor bars them.
Four actors, each with its own verb, in one telling; `.model__sentence` is that telling
compressed to one sentence before it is expanded. **No gate codes anywhere in this
component.** Carries the `reviewers` receipt on the third actor only — the other three have no
followable generated artifact, and an empty margin beside an unevidenced claim is the honest
result. `src/test/annotation-margin.test.ts` holds that at one.

---

### WhatYouInstall (`WhatYouInstall.astro`) — zone 4

**Zone:** surface-alt
**BEM classes:** `.units`, `.units__headline`, `.units__lead`, `.units__list`, `.unit`,
`.unit__head`, `.unit__what`, `.unit__where`, `.unit__body`, `.units__note`
**Key tokens:** `--ds-surface-alt`, `--ds-on-surface`, `--ds-on-surface-2`,
`--ds-on-surface-muted`, `--ds-field-label`, `--ds-rule-boundary`, `--ds-rule-hairline`,
`--ds-font-display`, `--ds-opsz-head`, `--ds-font-mono`, `--ds-type-h3`, `--ds-type-body-lg`,
`--ds-type-xs`, `--ds-track-heading`
**Note:** new in stage 2. Makes two claims the surface had never made — ownership stated as
files rather than as a licence, and **no hosted runtime** between the reader and those files.
A ruled list of records, not cards: `[ruled]` containment, no tint, no shadow.

---

### AdapterMatrix (`AdapterMatrix.astro`) — zone 6

**Zone:** surface (`<Section tone="surface" annotated>`)  
**BEM classes:** `.adapters__record` (the annotation row), `.adapters__headline`,
`.adapters__scroll`, `.adapters__table`, `.cap`, `.cap--yes`, `.cap--no`, `.adapters__note`  
**Key tokens:** `--ds-border`, `--ds-border-subtle`, `--ds-surface-alt`, `--ds-on-surface`,
`--ds-on-surface-muted`, `--ds-field-label`, `--ds-focus-ring`, `--ds-radius-md`,
`--ds-font-mono`, `--ds-type-sm`, `--ds-type-xs`, `--ds-weight-bold`, `--ds-weight-semibold`  
**Note:** `.cap--yes` is `--ds-on-surface` at `--ds-weight-bold`; `.cap--no` is
`--ds-on-surface-muted`. The mark is weight and ink, not color. Carries the `adapters`
receipt; see §9.

---

### InstallTerminal (`InstallTerminal.astro`) — zone 7

**Zone:** surface-alt (band) / surface (the command record inside it)  
**BEM classes:** `.install__headline`, `.terminal`, `.terminal__bar`, `.terminal__label`,
`.tabs`, `.tabs__radio`, `.tabs__label`, `.tabs__panels`, `.tabs__panel`,
`.tabs__panel--flagship`, `.tabs__panel--discovery`, `.tabs__panel--inception`,
`.tabs__panel--architect` (one per tab; CSS-only visibility depends on these modifiers),
`.terminal__line`, `.terminal__prompt`, `.install__note`, `.copy-btn.install-copy-btn`  
**Key tokens:** `--ds-surface`, `--ds-surface-alt`, `--ds-on-surface`, `--ds-on-surface-2`,
`--ds-on-surface-muted`, `--ds-field-label`, `--ds-rule-boundary`, `--ds-rule-hairline`,
`--ds-focus-ring`, `--ds-radius-md`, `--ds-radius-lg`,
`--ds-font-mono`, `--ds-lead-mono`, `--ds-type-sm`, `--ds-type-xs`,
`--ds-weight-medium`, `--ds-weight-semibold`  
**Note:** tab switching is CSS-only via hidden radio inputs (`<input type="radio">`). The one
script in the component only syncs the copy button's payload to the active panel; no tab is
shown or hidden by JavaScript.
The block is PAPER since 2026-09-18. Its edge is `--ds-rule-boundary` (3.26:1 on
`--ds-surface-alt`), not a dark fill; the three chrome dots went with the fill, because a
picture of a terminal window is ornament that `[none]` forbids, and a `.terminal__label`
field names the record instead. The dark-zone `--copy-btn-*` retint that used to live on
`.terminal__bar` is deleted, not adjusted: every property in it pointed at a `--ds-hero-*`
token and the carrier is no longer dark.

---

### PackCatalogue (`PackCatalogue.astro`) — zone 5

**Zone:** surface (`<Section tone="surface" annotated>`)  
**BEM classes:** `.work__record` (the annotation row), `.work__claim`, `.work__eyebrow`,
`.work__headline`, `.work__subhead`, `.work-grid`, `.work-card`, `.work-card--flagship`,
`.work-card__head`, `.work-card__title`, `.work-card__flag`, `.work-card__audience`,
`.work-card__desc`, `.work-card__packs`, `.work__all`  
**Grid:** `repeat(auto-fit, minmax(min(338px, 100%), 1fr))`. Both halves are load-bearing —
338 so two tracks plus the 24px gap fit the 700px content track at 1100px exactly (340 left a
4px one-column dead band at 1100-1103), and `min(..., 100%)` so the track cannot exceed its
band (an unclamped 340px minimum overflowed a 320px viewport by 40px, a live WCAG 1.4.10
failure).  
**Key tokens:** `--ds-surface`, `--ds-surface-alt`, `--ds-border`, `--ds-rule-boundary`,
`--ds-field-label`, `--ds-on-surface-2`, `--ds-on-surface-muted`,
`--ds-radius-md`, `--ds-radius-lg`, `--ds-font-mono`,
`--ds-type-h3`, `--ds-type-body-lg`, `--ds-type-sm`, `--ds-type-xs`, `--ds-weight-semibold`  
**Note:** the section is an outcome router, not the inventory — `/catalogue/` owns the complete
list. `.work-card` items carry no numeric badge. It sits at zone 5, BELOW the problem and the
model, so the reason precedes the menu; before 2026-09-18 it was third on the page. The
annotation
row is one level above the claim, so the receipt is not trapped inside the claim's own grid.
Carries the `catalogue` receipt; see §9.

---

### BuildYourOrg (`BuildYourOrg.astro`) — zone 8, the light call-out band

**Zone:** `surface-alt` — the alternate paper ground, a band in its own right. The dark
ground still appears exactly once, and `SiteFooter` is now its sole carrier and the sole
close (owner decision, 2026-09-18).  
**BEM classes:** `.org`, `.org__headline`, `.org__body`, `.org__cta`  
**Key tokens:** `--ds-on-surface`, `--ds-on-surface-2`, `--ds-cta-primary-bg`,
`--ds-cta-primary-fg`, `--ds-cta-primary-bg-hover`, `--ds-radius-sm`, `--ds-radius-md`,
`--ds-type-display`, `--ds-type-body-lg`, `--ds-type-body`,
`--ds-track-display`, `--ds-lead-display`, `--ds-weight-semibold`  
**Note:** `.org__cta` takes the PAPER CTA pair, re-derived against this band's ground
rather than inherited: ink fill `#14120f` on `--ds-surface-alt` `#efece5` is 15.85:1, and
the `#f7f5f0` label on that fill is 17.16:1. The `--ds-cta-primary-dk-*` pair that served
this control while the band was dark is DELETED — `.org__cta` was its only consumer.

---

### Section band (`Section.astro`)

**Variants:** `--surface` / `--surface-alt` / `--dark`  
**Props:** `tone`, `annotated`, `id`, `labelledby`, `aria-label`, `class`  
**BEM classes:** `.section`, `.section--surface`, `.section--surface-alt`, `.section--dark`,
`.section__inner`, `.section__inner--annotated`  
**Role:** Reusable full-width band wrapper. Sets background zone and constrains `max-width`
via `--ds-content-max`. Three tone variants map to the three zone levels. `annotated` turns on
the annotation margin for the band — see §9.
**Boundary rule:** `--surface` and `--surface-alt` each open on a 1px `--ds-rule-boundary`
top rule. On a page that is paper throughout the two grounds are 1.08:1 apart, so where two
same-tone bands adjoin — `use-cases` and the adapter matrix both being `surface` — the rule is
the only boundary there is. `--dark` takes no rule: its ground change is its boundary, and it
is the one place on the surface where that is true.

---

### SiteNav (`SiteNav.astro`)

**Zone:** surface (paper, since 2026-09-18) — its lower boundary is a `--ds-rule-boundary` rule, not a change of ground  
**BEM classes:** `.nav`, `.nav__inner`, `.nav__logo`, `.nav__links`, `.nav__link`,
`.nav__cta`, `.nav__mobile`, `.nav__toggle`, `.nav__burger`, `.nav__drawer`  
**Key tokens:** `--ds-hero-bg`, `--ds-hero-border`, `--ds-hero-fg`, `--ds-hero-fg-2`,
`--ds-cta-primary-bg`, `--ds-cta-primary-fg`, `--ds-cta-primary-bg-hover`,
`--ds-content-max`, `--ds-content-pad-x`, `--ds-radius-md`, `--ds-font-mono`,
`--ds-type-body-lg`, `--ds-type-sm`, `--ds-track-heading`,
`--ds-weight-medium`, `--ds-weight-semibold`, `--ds-weight-bold`,
`--ds-dur-quick`, `--ds-ease-std`, `--ds-z-overlay`  
**Note:** Mobile menu via `<details>/<summary>` — zero JS.

---

### SiteFooter (`SiteFooter.astro`)

**Zone:** dark  
**BEM classes:** `.footer`, `.footer__inner`, `.footer__brand`, `.footer__tag`, `.footer__cols`,
`.footer__collabel`, `.footer__list`, `.footer__copy`  
**Key tokens:** `--ds-hero-bg`, `--ds-hero-border`, `--ds-hero-fg`, `--ds-hero-fg-2`,
`--ds-hero-fg-muted`, `--ds-content-max`, `--ds-content-pad-x`, `--ds-font-mono`,
`--ds-type-sm`, `--ds-type-xs`, `--ds-weight-semibold`, `--ds-weight-bold`

---

### PackCard — `/packs/` index (`PackCard.astro`)

**Zone:** surface  
**BEM classes:** `.pack-card`, `.pack-card__link`, `.pack-card__head`, `.pack-card__name`,
`.pack-card__tagline`, `.pack-card__cta`  
**Key tokens:** `--ds-surface-alt`, `--ds-border`, `--ds-on-surface`, `--ds-on-surface-2`,
`--ds-radius-lg`, `--ds-type-h3`, `--ds-type-body`, `--ds-type-sm`, `--ds-lead-body`,
`--ds-weight-semibold`, `--ds-dur-moderate`, `--ds-ease-std`

---

### Catalogue records — `/catalogue/` (`catalogue/index.astro`)

**Zone:** paper throughout, `.cat-hero` included (paper since 2026-09-18). The
outcome and role band is `Section tone="surface-alt"`, the pack band
`tone="surface"`; both grounds come from `Section.astro`, not from this file.  
**Shape:** three ruled record lists since 2026-09-18 — outcomes, roles and packs. The
`.outcome-card` / `.role-grid` / `.cat-card` grids they replaced carried a tinted fill, a
border and a radius against the direction sheet's `[ruled]` and `[flat]` rows; the pattern
here is the one `PackCatalogue.astro` and `WhatYouInstall.astro` already ship.  
**BEM classes:** `.cat-hero`, `.cat-hero__inner`, `.cat-hero__eyebrow`, `.cat-hero__heading`,
`.cat-hero__body`, `.outcomes__heading`, `.outcomes__intro`, `.outcome-records`,
`.outcome-record`, `.outcome-record__title`, `.outcome-record__desc`,
`.outcome-record__packs`, `.roles__heading`, `.role-records`, `.role-record`,
`.role-record__link`, `.role-record__name`, `.role-record__to`, `.cat-grid__heading`,
`.cat-grid__intro`, `.pack-records`, `.pack-record`, `.pack-record__link`,
`.pack-record__head`, `.pack-record__name`, `.pack-record__skills`,
`.pack-record__tagline`  
**Scope chip** (`StatusChip.astro` via `<StatusChip label={pack.scope} />`): `.status-chip`  
**Key tokens** — every `var(--ds-*)` the file references, and no others:
`--ds-surface`, `--ds-rule-boundary`, `--ds-rule-hairline`, `--ds-field-label`,
`--ds-on-surface`, `--ds-on-surface-2`,
`--ds-content-max`, `--ds-content-pad-x`,
`--ds-font-mono`, `--ds-type-display`, `--ds-type-h3`, `--ds-type-body-lg`,
`--ds-type-xs`, `--ds-type-mono-sm`,
`--ds-track-display`, `--ds-track-label`,
`--ds-lead-display`, `--ds-lead-body`, `--ds-weight-semibold`,
`--ds-space-2`, `--ds-space-3`, `--ds-space-4`, `--ds-space-5`, `--ds-space-7`,
`--ds-space-8`, `--ds-space-9`  
**Note:** the `.install-block*` classes are not on this page — install blocks live on
`pages/packs/[pack].astro` and `pages/journeys/[journey].astro`. This block also claimed
`/catalogue/` was the last consumer of `--ds-track-label`; it is not. The count and the
list of consumers live in § 2 under Tracking (letter-spacing), and only there.

---

### CopyButton (`CopyButton.astro`)

**Zone:** surface  
**BEM classes:** `.copy-btn`, `.copy-btn--success`, `.copy-btn__icon`, `.copy-btn__label`,
`.copy-btn__live` (aria-live region, visually hidden)  
**Key tokens:** `--ds-border`, `--ds-on-surface`, `--ds-on-surface-muted`, `--ds-focus-ring`,
`--ds-state-success-fg`, `--ds-state-success-border`, `--ds-radius-sm`,
`--ds-font-mono`, `--ds-type-xs`, `--ds-dur-quick`, `--ds-ease-std`

---

### Receipt (`Receipt.astro`)

**Zone:** surface (renders correctly in ordinary flow, with or without a margin)  
**BEM classes:** `.receipt`, `.receipt__label`, `.receipt__values`, `.receipt__row`,
`.receipt__key`, `.receipt__value`, `.receipt__items`, `.receipt__item`, `.receipt__source`,
`.receipt__source-key`, `.receipt__source-path`  
**Key tokens:** `--ds-field-label`, `--ds-rule-hairline`, `--ds-on-surface`,
`--ds-on-surface-2`, `--ds-rule-pitch`, `--ds-font-mono`, `--ds-type-xs`,
`--ds-weight-semibold`  
**Note:** zero chroma, by rule. Every value is read from `src/lib/receipts.generated.json`
(`schemaVersion` 1), which `tools/build-site.py` derives by counting the real repository;
nothing is hardcoded. The component throws at build time on a schema-version mismatch or an
unknown receipt key. Line boxes are pinned to 2 × `--ds-rule-pitch` so successive field lines
land on the rule grid. See §9.

## 5. Zone rules

Two primary zone levels:

| Zone | Background token | Text tokens | When to use |
| --- | --- | --- | --- |
| Dark | `--ds-hero-bg` | `--ds-hero-fg`, `--ds-hero-fg-2`, `--ds-hero-fg-muted` | **Exactly two carriers: `BuildYourOrg` (the close band) and `SiteFooter`, continuous with it.** Nothing else. |
| Content / light (paper) | `--ds-surface`, `--ds-surface-alt` | `--ds-on-surface`, `--ds-on-surface-2`, `--ds-on-surface-muted` | Everything else — the nav, every hero, every band, the install terminal, the 404 and the pack/journey install blocks included |

**Layering rule:** Component CSS references **semantic tokens only** — never Tier 1 primitives
directly. A component in the dark zone uses `--ds-hero-*` tokens; one in the light zone uses
`--ds-surface*` and `--ds-on-surface*` tokens. Mixing zone tokens across a single component
(e.g., a dark terminal embed inside a light card) is permitted when the inner element
explicitly targets its own zone.

**Chroma rule:** color is not a zone tool. The clearance mark is the only chromatic family and
it means ONE thing — a refusal, a hold, a block. It has exactly two consumers, and they are
the same thing in two places: the `HELD` value of the typeset transcript, in `Hero.astro` and
in the direction preview. Never an eyebrow, never a rule, never a fill, never a control,
never body text; an eyebrow is `--ds-field-label` and an eyebrow rule is
`--ds-rule-boundary`. Rules, edges and emphasis are carried by `--ds-rule-hairline`,
`--ds-rule-boundary`, ink weight and the record ramp — never by a tint.

## 6. Dark mode

The Astro marketing site page and component CSS (`web/src/`) has **no `prefers-color-scheme: dark`
media query**. Dark zone is a layout concept — specific sections use `--ds-hero-bg` as a design
property, not in response to user OS preference. Every component's zone is fixed at design time,
not toggled by user setting. Exception: `web/public/favicon.svg` does include a
`@media (prefers-color-scheme: dark)` rule to adjust the favicon fill in dark OS mode — this is
a standalone SVG asset and does not affect page or component CSS.

Dark mode exists only in the **Starlight docs-site** (`docs-site/src/styles/starlight.css`,
toggled by the Starlight theme switcher) — and that sheet is dark-**first**: the dark palette
is declared on bare `:root`, and `:root[data-theme='light']` overrides it. There is no
`[data-theme='dark']` selector. The docs palette is also self-contained per ADR-0085:
`starlight.css` carries no `@import` and does not read `web/src/styles/tokens.css`. It
declares its own `--doc-*` tokens and re-derives the `--ds-*` names that the shared
`primitives/` components consume, so no `--prim-*` token reaches the docs surface.

Docs dark-theme resolved values (token → hex), read from `starlight.css`:

| Role | Token reference | Hex |
| --- | --- | --- |
| Docs surface background | `var(--doc-ground)` | `#0c111c` |
| Sidebar / elevated surface | `var(--doc-surface)` | `#111726` |
| Accent — fills, large marks | `var(--doc-accent)` | `#4f7df0` |
| Link color — text-safe on dark (8.68:1) | `var(--doc-accent-strong)` | `#8ab0f9` |
| Inline code background | `var(--doc-tint)` | `rgba(138,176,249,0.12)` |

## 7. Card icon parity decision

**Decision: intentional asymmetry — no change required.**

Two sections use visually similar card layouts with different information architectures:

| Section | Component | Numeric badge? | Reason |
| --- | --- | --- | --- |
| TheModel | `.actor` items with `.actor__n` | Yes — 01 / 02 / 03 / 04 | Sequential telling of one work lifecycle; order is semantically meaningful |
| PackCatalogue | `.work-card` items | No | Unordered outcome entries; a badge would imply false ranking |
| `/packs/` index | `.pack-card` | No | Unordered catalogue entries |
| `/catalogue/` | `.outcome-record`, `.role-record`, `.pack-record` | No | Unordered catalogue entries |

The `.actor__n` ordinal in TheModel uses `color: --ds-on-surface-muted` and
`font-family: --ds-font-mono` at `font-size: --ds-type-h3`, at `--ds-weight-semibold` with
tabular lining numerals. 600 rather than 800 because mono ships two weights (see
`fonts.css`); an 800 would resolve to 600 and the declaration would describe nothing. The
former accent color is withdrawn: the ordinal is ink, not chroma. No badge or icon addition is in scope for this spec — this record
closes the question so it is not re-litigated in future PRs.

## 8. Starlight CSS audit

**Context:** the docs site migrated from MkDocs / Material for MkDocs to Starlight. The
previously planned audit of Material-injected raw-hex deviations (`.md-header`, `.md-tabs`,
etc.) no longer applies — those component classes do not exist in the current codebase.

The Starlight CSS (`docs-site/src/styles/starlight.css`) is a self-contained token sheet per
ADR-0085: it imports nothing, declares its own `--doc-*` palette, and maps Starlight's slot
variables (`--sl-*`) onto that palette. A compatibility layer at the foot of the file
re-derives the `--ds-*` names that the shared `src/components/primitives/` components consume
in scoped styles — those names are re-derivations onto the doc palette, not imports of
`web/`'s values. It is predominantly token-compliant. One known deviation:

| Location | Raw value | Note |
| --- | --- | --- |
| `--sl-color-text-invert`, light-theme assignment (`starlight.css:124`) | `#ffffff` | Used by Starlight's built-in UI for inverted text. The dark-theme assignment of the same slot uses `var(--doc-ground)`, so this is the only raw literal left in the slot mapping |

The `.site-footer__brand { color }` literal previously recorded here is resolved: it now reads
`color: var(--doc-heading)`. Updating the remaining `--sl-color-text-invert` literal to a
`--doc-*` token is out of scope for this spec — it is documented as a known current
deviation, not a necessary architectural exception.

The zone-violation lint (`tools/lint_zone_violations.py`) scans `web/src/` only.
`docs-site/src/styles/starlight.css` is intentionally outside its scope — the two `#ffffff`
deviations documented above are known current deviations that could be token references, not
violations that should be suppressed.

## 9. Annotation margin

The register's load-bearing layout move: a claim carries its receipt beside it. The layout half
lives in `Section.astro`; the content half is `Receipt.astro` (§4). The reasoning is in
`docs/design/direction/tech-site-amendment-palette.md` — §2 ("The derived language — the
register") commits to the margin, and §3 ("One goal added — Checked in public") is the goal it
serves. Not restated here.

### How a band opts in

1. The band passes `annotated` to `Section.astro`, which adds `.section__inner--annotated`.
2. A row inside it opts in by carrying the class `annotation-row`. Rows that do not opt in are
   untouched, so `annotated` costs a band nothing until a receipt exists for it.
3. Inside an annotation row, any `.receipt` is placed in the margin column.

A row may declare its own content tracks through `--annotation-content-columns`; the margin is
appended as the **last** track, so the receipt's placement is identical for every row. At narrow
widths a row may say which content column its receipt should line up under via
`--annotation-receipt-column` (default: span the whole row).

### Geometry

| Token | Value | Role |
| --- | --- | --- |
| `--ds-annotation-col-min` | `20rem` (320px = 40 × `--ds-rule-pitch`, padding included) | Narrowest the receipt column may be before it fights the text measure |
| `--ds-annotation-gap`     | `var(--ds-space-7)` (48px = 6 × `--ds-rule-pitch`) | Content-to-margin gutter |

At `min-width: 1100px` the row becomes
`var(--annotation-content-columns, minmax(0, 1fr)) minmax(var(--ds-annotation-col-min), 1fr)`
and the receipt takes `grid-column: -2 / -1; grid-row: 1`. The gutter is applied as
`padding-inline-start` on the receipt rather than a row `column-gap`, because a row-wide gap
would also widen the gaps between the row's own content columns and pull them out of step with
the un-annotated rows beside them.

**Why 1100px, and why it is a literal.** A media query cannot read a custom property, so the
breakpoint is written out in `Section.astro` and `--ds-annotation-col-min` records what decides
it: 1100px is the first width at which a 64ch measure and that column both fit inside
`--ds-content-max`. That is well above the usual tablet boundary, on purpose — below it the
content and the margin would fight for space.

### The non-negotiable rule

**At narrow widths the receipt reflows beneath its claim. It is never hidden.**

Below the breakpoint the margin simply does not exist and the receipt falls into its natural
DOM position — in flow, directly beneath its claim, at full size. `display: none`,
`visibility: hidden`, `content-visibility`, `aria-hidden`, `<details>`, a checkbox toggle, and
any other tap-to-reveal are **forbidden on a receipt at every width**. Muted *presentation* is
correct; muted *availability* is the anti-pattern. A receipt that disappears on a phone fails
the reflow item in the amendment's floor check and defeats the goal outright. Tufte CSS, the
most-copied sidenote recipe on the web, hides its notes on mobile by default; that is the single
most likely way to build this wrong.

Two further rules hold the margin together:

- **DOM order first.** The receipt is authored as the sibling immediately after the claim it
  annotates. Everything in the stylesheet is visual placement only — `grid-column` moves a box,
  not a node — so reading order and focus order are already correct and WCAG 1.3.2 is satisfied
  with no extra attributes. Nothing may reorder the DOM to get a visual result.
- **CSS grid only.** No floats, no absolute positioning, no JavaScript. A floated or
  absolutely-positioned note is out of flow, which is what makes other sidenote recipes overlap
  or clip at some width.

**Guard test:** `web/src/test/annotation-margin.test.ts` holds this open. It asserts, per
annotated band, that the receipt renders from the generated projection rather than a literal,
that every field name is paired with its own value, that the receipt is the DOM sibling
immediately after its claim, that it carries no attribute removing it from the accessibility
tree, and that it sits behind no disclosure or toggle. It also walks every stylesheet under
`web/src` to confirm none withholds a receipt at any width, and checks that every receipt the
generator produces is shown.

### What is annotated today

| Band | Receipt key | Claim it evidences |
| --- | --- | --- |
| TheModel (`section--surface`) | `reviewers` | The third actor — reviewers who did not write the code |
| AdapterMatrix (`section--surface`) | `adapters` | The adapter capability table |
| PackCatalogue (`section--surface`) | `catalogue` | The outcome router |

The other three actors are deliberately left unannotated; the guard test pins that too,
so an added receipt cannot silently skip a band and an unannotated actor cannot be quietly
annotated without updating the record.

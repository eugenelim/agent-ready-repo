# Design System Foundations — agent-ready-repo platform

Derived from `site/aesthetic-direction.md` (Option B — Alternating Conviction).  
Follows the three-tier architecture: **Primitive → Semantic → Component**.  
Implementation target: Astro marketing site CSS + MkDocs `extra.css` override.

> **Superseded in part — read the current token file with this document.**
> This file was a values mirror of `web/src/styles/tokens.css`. The palette it
> mirrors was withdrawn on 2026-09-18 by
> `docs/design/direction/tech-site-amendment-palette.md` (`status: active`),
> which replaced the dark/neutral/amber ramps with the **register** language: a
> green-black machine zone (`--prim-ink-*`), a pale green-grey record zone
> (`--prim-record-*`), and a single vermilion clearance mark
> (`--prim-stamp-*`) that is defined and deliberately unused.
>
> **Current authorities, in order:**
>
> - `web/src/styles/tokens.css` — the implementation authority for every value.
> - `web/src/design-system.md` — the living reference that describes the current
>   system, including the annotation margin, which postdates this file entirely.
> - `docs/design/direction/tech-site-amendment-palette.md` — why the change was
>   made. The reasoning is not paraphrased here.
>
> Claims in this file that the amendment falsified are marked inline below as
> **[Corrected]**. The original wording is kept so the shipped record stays
> honest; it is not authoritative where a correction follows it.
>
> **Governance.** Only `spec.md` and `plan.md` in this directory carry a
> `- **Status:**` field, and the convention's freeze mechanism works exclusively
> through that field. This companion carries no Status field, so the mechanism
> does not reach it — the same check recorded for `aesthetic-direction.md` in
> `docs/design/direction/tech-site-amendment.md`. This file therefore follows
> the convention already applied to `aesthetic-direction.md`: a supersession
> banner plus inline `[Corrected]` markers, and no rewriting of the original.

---

## Tier 1 — Primitive scale

```css
/* ── Color primitives ─────────────────────────────────────────────────────── */
:root {
  /* Dark zone */
  --prim-dark-950: #0b0e12;  /* hero canvas — neutral-cool near-black */
  --prim-dark-900: #111520;  /* dark card / elevated on hero */
  --prim-dark-800: #1a2035;  /* dark elevated overlay on hero */
  --prim-dark-700: #232b40;  /* dark border-visible surface */

  /* Neutral (light zone) */
  --prim-neutral-50:  #fafaf9;  /* content surface — warm near-white */
  --prim-neutral-100: #f0efed;  /* alt surface — card background */
  --prim-neutral-200: #e0ddd9;  /* border on light */
  --prim-neutral-300: #c4c0bb;  /* muted border */
  --prim-neutral-400: #9c9891;  /* placeholder, disabled */
  --prim-neutral-600: #6b6760;  /* secondary text */
  --prim-neutral-800: #2e2c28;  /* primary text */
  --prim-neutral-900: #1c1b18;  /* heading text */

  /* Amber-gold — the single chromatic accent */
  --prim-amber-50:  #fff8e8;
  --prim-amber-100: #fdecc9;
  --prim-amber-200: #fad49a;
  --prim-amber-300: #f5bc6a;   /* light decorative glow */
  --prim-amber-400: #e8952b;   /* primary accent — CTA, icon, stat */
  --prim-amber-500: #c8780a;   /* darker variant */
  --prim-amber-700: #8b5e0a;   /* text-safe on light (≥4.5:1 on neutral-50) */
  --prim-amber-900: #4a3005;   /* deep, for dark-on-amber text */

  /* Alpha tokens */
  --prim-white-06:  rgba(255, 255, 255, 0.06);
  --prim-white-10:  rgba(255, 255, 255, 0.10);
  --prim-white-20:  rgba(255, 255, 255, 0.20);
  --prim-white-60:  rgba(255, 255, 255, 0.60);
  --prim-white-80:  rgba(255, 255, 255, 0.80);
  --prim-black-06:  rgba(0, 0, 0, 0.06);
  --prim-black-12:  rgba(0, 0, 0, 0.12);
  --prim-amber-10:  rgba(232, 149, 43, 0.10);
  --prim-amber-15:  rgba(232, 149, 43, 0.15);
  --prim-amber-20:  rgba(232, 149, 43, 0.20);
}
```

---

> **[Corrected] — every colour primitive above.** The dark, neutral and amber
> ramps no longer exist in `tokens.css`. The current primitives are:
>
> | Withdrawn | Current | Hex |
> | --- | --- | --- |
> | `--prim-dark-950` `#0b0e12` | `--prim-ink-950` | `#0e1311` |
> | `--prim-dark-900` `#111520` | `--prim-ink-900` | `#151b18` |
> | `--prim-dark-800` `#1a2035` | `--prim-ink-800` | `#1d2521` |
> | `--prim-dark-700` `#232b40` | `--prim-ink-700` | `#2a332e` |
> | `--prim-neutral-50` `#fafaf9` | `--prim-record-50` | `#f1f3ef` |
> | `--prim-neutral-100` `#f0efed` | `--prim-record-100` | `#e7eae5` |
> | `--prim-neutral-200` `#e0ddd9` | `--prim-record-200` | `#d3d8cf` |
> | `--prim-neutral-300` `#c4c0bb` | `--prim-record-300` | `#b4bcb0` |
> | — (new) | `--prim-record-350` | `#a4ad9f` |
> | `--prim-neutral-400` `#9c9891` | `--prim-record-400` | `#8f978c` |
> | — (new) | `--prim-record-500` | `#7a8773` |
> | `--prim-neutral-600` `#6b6760` | `--prim-record-600` | `#5e645c` |
> | `--prim-neutral-800` `#2e2c28` | `--prim-record-800` | `#2b302c` |
> | `--prim-neutral-900` `#1c1b18` | `--prim-record-900` | `#161a17` |
> | the eight `--prim-amber-*` steps (whole ramp withdrawn) | `--prim-stamp-500` | `#e2593a` |
> | — | `--prim-stamp-700` | `#b23a22` |
>
> The amber alpha tokens went with the ramp: `--prim-amber-10/15/20` are now
> `--prim-stamp-10` `rgba(226, 89, 58, 0.10)`, `--prim-stamp-15`
> `rgba(226, 89, 58, 0.15)` and `--prim-stamp-20` `rgba(226, 89, 58, 0.20)`. The
> white and black alpha tokens are unchanged.
>
> `--prim-stamp-*` is the **clearance mark** — the only chroma, and it means a
> human cleared something. It is defined and has no consumer in `web/src`; that
> absence is the invariant, not a gap. The functional state primitives
> (`--prim-green-*`, `--prim-red-*`, `--prim-orange-*`, `--prim-blue-*`) are
> retuned off stock Tailwind and were never part of this file's mirror; they are
> listed in `web/src/design-system.md` §1.

---

## Tier 2 — Semantic layer

One-way dependency: semantic tokens reference primitives only. Component CSS references semantics only — never primitives directly.

```css
/* ── Semantic tokens ──────────────────────────────────────────────────────── */
:root {
  /* ── Hero / dark zone ───────────────────────────────────────────── */
  --ds-hero-bg:          var(--prim-dark-950);
  --ds-hero-surface:     var(--prim-dark-900);   /* card on dark */
  --ds-hero-elevated:    var(--prim-dark-800);   /* elevated card on dark */
  --ds-hero-fg:          #ffffff;                /* primary text on dark */
  --ds-hero-fg-2:        var(--prim-white-80);   /* secondary text on dark */
  --ds-hero-fg-muted:    var(--prim-white-60);   /* muted / caption on dark */
  --ds-hero-border:      var(--prim-white-06);   /* hairline divider on dark */
  --ds-hero-border-card: var(--prim-white-10);   /* card border on dark */

  /* ── Content / light zone ───────────────────────────────────────── */
  --ds-surface:          var(--prim-neutral-50);
  --ds-surface-alt:      var(--prim-neutral-100); /* card background */
  --ds-on-surface:       var(--prim-neutral-900); /* heading text */
  --ds-on-surface-2:     var(--prim-neutral-800); /* body text */
  --ds-on-surface-muted: var(--prim-neutral-600); /* captions, metadata */
  --ds-border:           var(--prim-neutral-200); /* card, section border */
  --ds-border-subtle:    var(--prim-black-06);    /* hairline, lowest weight */

  /* ── Accent — amber-gold, single chromatic ──────────────────────── */
  --ds-accent:            var(--prim-amber-400);  /* icon, CTA fill on dark, stat */
  --ds-accent-deep:       var(--prim-amber-700);  /* text-safe on light (4.5:1+) */
  --ds-accent-subtle:     var(--prim-amber-10);   /* low-opacity fill on light */
  --ds-accent-subtle-dk:  var(--prim-amber-15);   /* low-opacity fill on dark */
  --ds-accent-glow:       var(--prim-amber-20);   /* ambient glow, gate pulses */

  /* ── CTA buttons ────────────────────────────────────────────────── */
  /* Primary on dark hero: amber fill, near-black text */
  --ds-cta-primary-bg:    var(--prim-amber-400);
  --ds-cta-primary-fg:    var(--prim-dark-950);
  --ds-cta-primary-bg-hover: var(--prim-amber-300);

  /* Primary on light section: amber fill, near-black text */
  /* (same tokens work — amber has sufficient contrast both ways) */

  /* Ghost on dark hero: transparent fill, white border + text */
  --ds-cta-ghost-border:  var(--prim-white-20);
  --ds-cta-ghost-fg:      var(--prim-white-80);
  --ds-cta-ghost-bg-hover: var(--prim-white-10);

  /* Ghost on light: amber border, deep-amber text */
  --ds-cta-ghost-light-border: var(--prim-amber-400);
  --ds-cta-ghost-light-fg:     var(--prim-amber-700);

  /* ── Type scale ─────────────────────────────────────────────────── */
  /* Display — hero headline, alternating section headlines */
  --ds-type-display:  clamp(2.75rem, 5.5vw, 4rem);      /* ~44–64px */
  --ds-type-h2:       clamp(1.875rem, 3.5vw, 2.5rem);   /* ~30–40px */
  --ds-type-h3:       clamp(1.25rem, 2vw, 1.5rem);      /* ~20–24px */
  --ds-type-body-lg:  1.125rem;                          /* lead / intro */
  --ds-type-body:     1rem;                              /* body */
  --ds-type-sm:       0.875rem;                          /* captions, metadata */
  --ds-type-xs:       0.75rem;                           /* labels, badges */
  --ds-type-mono-sm:  0.8125rem;                         /* inline code, skill names */

  /* Weight */
  --ds-weight-regular: 400;
  --ds-weight-medium:  500;
  --ds-weight-semibold: 600;
  --ds-weight-bold:    700;
  --ds-weight-heavy:   800;

  /* Tracking */
  --ds-track-display:  -0.03em;   /* negative — required at display sizes */
  --ds-track-heading:  -0.02em;   /* slightly negative at h2/h3 */
  --ds-track-label:     0.08em;   /* uppercase monospace labels */
  --ds-track-normal:    0em;      /* body — never deviate */

  /* Leading */
  --ds-lead-display: 1.1;   /* tight for display size */
  --ds-lead-heading: 1.25;  /* slightly open for h2/h3 */
  --ds-lead-body:    1.65;  /* comfortable reading */
  --ds-lead-mono:    1.5;   /* code and terminal */

  /* ── Spacing — 4px base, 8-step scale ──────────────────────────── */
  --ds-space-1:  4px;
  --ds-space-2:  8px;
  --ds-space-3:  12px;
  --ds-space-4:  16px;
  --ds-space-5:  24px;
  --ds-space-6:  32px;
  --ds-space-7:  48px;
  --ds-space-8:  64px;
  --ds-space-9:  96px;
  --ds-space-10: 128px;

  /* Section rhythm — responsive */
  --ds-section-gap:    clamp(5rem, 10vw, 8rem);   /* between major sections */
  --ds-section-pad-y:  clamp(4rem, 8vw, 6rem);    /* internal section padding */
  --ds-content-max:    1140px;                     /* max content width */
  --ds-content-pad-x:  clamp(1.25rem, 5vw, 2.5rem); /* horizontal margin */

  /* ── Radius ─────────────────────────────────────────────────────── */
  --ds-radius-sm:   4px;   /* inline code, badges, chips */
  --ds-radius-md:   8px;   /* cards, inputs */
  --ds-radius-lg:   12px;  /* modals, large cards */
  --ds-radius-pill: 9999px; /* CTA buttons */

  /* ── Shadow — border-not-shadow philosophy ──────────────────────── */
  /* Cards: no shadow. Use border only. Shadow = overlay elevation only. */
  --ds-shadow-overlay: 0 20px 60px rgba(0, 0, 0, 0.25);  /* modals, dropdowns */
  --ds-shadow-none:    none;

  /* ── Motion ─────────────────────────────────────────────────────── */
  --ds-dur-quick:    120ms;
  --ds-dur-moderate: 200ms;
  --ds-dur-gentle:   300ms;
  --ds-ease-std:     cubic-bezier(0.4, 0, 0.2, 1);
  --ds-ease-out:     cubic-bezier(0, 0, 0.2, 1);

  /* ── Z-index scale ──────────────────────────────────────────────── */
  --ds-z-base:    0;
  --ds-z-raised:  10;
  --ds-z-overlay: 100;
  --ds-z-modal:   200;
  --ds-z-toast:   300;
}
```

---

> **[Corrected] — the semantic block above, in five places.**
>
> 1. **Zone tokens re-point.** `--ds-hero-*` now reads the `--prim-ink-*` ramp
>    and `--ds-surface*` / `--ds-on-surface*` the `--prim-record-*` ramp. The
>    token names and roles are unchanged.
> 2. **The accent layer has no consumer.** `--ds-accent`, `--ds-accent-deep`,
>    `--ds-accent-subtle`, `--ds-accent-subtle-dk` and `--ds-accent-glow` still
>    exist, now aliased to the stamp, but nothing in `web/src` reads them. They
>    are kept only as the names the design-system document and the browser gate
>    cite. Pointing a component at one reintroduces the defect the withdrawal
>    removed.
> 3. **The CTA tokens changed meaning.** The primary CTA is the record itself,
>    not chroma: `--ds-cta-primary-bg` → `--prim-record-50`,
>    `--ds-cta-primary-fg` → `--prim-ink-950`, `--ds-cta-primary-bg-hover` →
>    `--prim-record-200`. The light ghost CTA takes the boundary rule and heading
>    ink: `--ds-cta-ghost-light-border` → `--prim-record-500`,
>    `--ds-cta-ghost-light-fg` → `--prim-record-900`. The claim that "the same
>    tokens work" on a light section no longer holds, because there is no amber
>    fill to reuse.
> 4. **New roles exist that this file predates.** `--ds-rule-hairline`
>    (`--prim-record-350`), `--ds-rule-boundary` (`--prim-record-500`),
>    `--ds-field-label` (`--prim-record-600`), `--ds-clearance`
>    (`--prim-stamp-700`), `--ds-clearance-dk` (`--prim-stamp-500`),
>    `--ds-focus-ring` (`--ds-on-surface` on light, re-pointed to
>    `--ds-hero-fg` on dark carriers), and the annotation-margin geometry
>    `--ds-annotation-col-min` (`20rem`) and `--ds-annotation-gap`
>    (`var(--ds-space-7)`).
> 5. **Spacing, rhythm and radius changed.** A `--ds-rule-pitch: 8px` vertical
>    rhythm was added and every vertical measure is an integer multiple of it.
>    `--ds-space-3` is `8px`, not `12px`. `--ds-space-1` stays `4px` as an
>    explicit half-pitch for inline use only, never a vertical measure.
>    `--ds-section-pad-y` is no longer `clamp(4rem, 8vw, 6rem)` — it is stepped
>    per breakpoint (`4rem` base, `4.5rem` ≥768px, `5rem` ≥1024px, `5.5rem`
>    ≥1280px, `6rem` ≥1440px) so every value lands on the pitch. Radius
>    collapsed to `--ds-radius-sm: 2px`, `--ds-radius-md: 6px`,
>    `--ds-radius-lg: 10px`, and **`--ds-radius-pill` is deleted**: a register
>    has corners, not capsules. Every former pill consumer takes
>    `--ds-radius-md`.
>
> Tracking, leading, the type scale, the weight scale, shadow, motion and
> z-index are unchanged in value. One meaning changed:
> **`--ds-track-label` (`0.08em`) no longer means uppercase.** Homepage field
> labels are sentence-case with their own lighter local tracking; `/catalogue/`
> is the last consumer of the token.

---

## Tier 3 — Component notes (not values)

Component CSS references semantic tokens only. Notes on key components:

### Hero section
- Background: `--ds-hero-bg` with a subtle radial glow from `--ds-accent-glow` anchored at center-top (15–20% opacity). This is the "one non-neutral move."
- Optional grid texture: 1px lines at 4% opacity, 28px repeat — same as current `extra.css`. Keep or drop; the glow alone is sufficient.
- Headline: `--ds-type-display`, `--ds-weight-heavy`, `--ds-track-display`, color `--ds-hero-fg`.
- Subhead: `--ds-type-body-lg`, `--ds-weight-regular`, color `--ds-hero-fg-2`.

### Stat strip (below hero CTA)
- Three or four items, monospace (`JetBrains Mono`), tabular-nums.
- Number: `--ds-type-h2` size, `--ds-weight-heavy`, color `--ds-accent`.
- Label: `--ds-type-xs`, uppercase, `--ds-track-label`, color `--ds-hero-fg-muted`.
- Separator: vertical `1px solid --ds-hero-border`.

### Cards (light sections)
- Background: `--ds-surface-alt`.
- Border: `1px solid --ds-border` always visible (not on-hover only — border-not-shadow).
- On hover: border transitions to `--ds-accent` at `--ds-dur-moderate`.
- `translate(-2px)` on hover — subtle lift only.
- Radius: `--ds-radius-md`.
- No box-shadow on cards. `--ds-shadow-overlay` reserved for modals/dropdowns.

### Skill name / command chips
- Background: `--ds-accent-subtle`.
- Text: `--ds-accent-deep` (text-safe on light, 4.5:1+).
- Font: `JetBrains Mono`, `--ds-type-mono-sm`, `--ds-track-label` (subtle uppercase).
- Radius: `--ds-radius-sm`.

### Section bands (light content)
- Background: `--ds-surface` or `--ds-surface-alt` for alternation.
- Padding: `--ds-section-pad-y` top and bottom.
- Hard-cut at band boundaries — no gradients between dark and light bands.

### CTA buttons
- Primary: `--ds-cta-primary-bg` fill, `--ds-cta-primary-fg` text, `--ds-radius-pill`.
- Ghost on dark: transparent fill, `--ds-cta-ghost-border` border, `--ds-cta-ghost-fg` text.
- Both: `padding: 0.7rem 1.6rem`, `--ds-weight-semibold`, `--ds-type-sm` or `--ds-type-body`.
- Focus ring: `outline: 2px solid --ds-accent; outline-offset: 3px` (both surfaces).

### Focus rings (all interactive elements)
- `outline: 2px solid var(--ds-accent); outline-offset: 3px`.
- On dark surfaces: same — amber-gold has sufficient luminance ratio against `--ds-hero-bg`.

---

> **[Corrected] — the component notes above, wherever they name the accent.**
>
> - **Hero.** The radial `--ds-accent-glow` glow is withdrawn. The canvas carries
>   a ruled grid only; there is no "one non-neutral move" on the hero.
> - **Stat strip.** The label is sentence case with a local `letter-spacing:
>   0.02em`, not uppercase with `--ds-track-label`. The number is
>   `--ds-hero-fg`, not `--ds-accent`. Tabular lining numerals still hold.
> - **Cards.** The hover border no longer transitions to `--ds-accent`. Card
>   edges are carried by `--ds-border` and, where a record edge is meant,
>   `--ds-rule-boundary` — for example `HumanGates`' `.gate-card` left border.
>   Border-not-shadow still holds.
> - **Skill name / command chips.** `--ds-accent-subtle` and `--ds-accent-deep`
>   have no consumer. Chips are set in the record ramp with `--ds-field-label`
>   and ink weight.
> - **CTA buttons.** `--ds-radius-pill` is deleted; CTAs take
>   `--ds-radius-md` (`6px`).
> - **Focus rings.** The ring is not the accent. `--ds-focus-ring` resolves to
>   `--ds-on-surface` on light and is re-pointed to `--ds-hero-fg` on the
>   dark-zone carriers enumerated at the foot of `tokens.css`. The ratios are
>   re-measured in the browser gate against the current palette, not asserted
>   in a document.
>
> **Not in this file at all: the annotation margin.** It postdates this record.
> `Section.astro`'s `annotated` prop, the `.annotation-row` grid, the
> `Receipt.astro` primitive, the 1100px collapse, and the rule that a receipt
> reflows beneath its claim and is never hidden are documented in
> `web/src/design-system.md` §9 and held open by the guard test
> `web/src/test/annotation-margin.test.ts`.

---

## Typeface decisions

| Role | Font | Notes |
|---|---|---|
| Display + headings + body | **Inter** (already in MkDocs) | 700–800 at display, 400 at body |
| Code, skills, commands, chips | **JetBrains Mono** (already in MkDocs) | Uppercase + wide tracking for labels |
| No additional typefaces | — | Adding a third face breaks the identity |

The existing MkDocs `font:` config (`text: Inter`, `code: JetBrains Mono`) is correct. No change needed.

---

> **[Corrected] — the "Uppercase + wide tracking for labels" note.** Mono is a
> field face, not a decorative label face: it sets record fields, and homepage
> field labels are sentence-case. The two families and the "no third face" rule
> stand. The MkDocs `font:` config referenced here no longer exists — the docs
> surface is Starlight, and it is out of this amendment's scope by owner
> decision.

---

## Contrast verification (WCAG AA — amber-gold)

| Use | Foreground | Background | Ratio | Passes |
|---|---|---|---|---|
| Stat number (large) | `#e8952b` | `#0b0e12` | ~6.2:1 | AA large ✓ |
| CTA text | `#0b0e12` | `#e8952b` | ~6.2:1 | AA ✓ |
| Skill chip text | `#8b5e0a` | `#fafaf9` | ~6.0:1 | AA ✓ |
| Icon on light | `#e8952b` | `#fafaf9` | ~3.2:1 | AA large / UI ✓ |
| Body text (never use) | `#e8952b` | `#fafaf9` | ~3.2:1 | ✗ fails body |
| Body text (light bg) | `#1c1b18` | `#fafaf9` | ~16:1 | AA ✓ |
| Body text (dark bg) | `#ffffff` | `#0b0e12` | ~18:1 | AA ✓ |

**Rule:** `--ds-accent` (`#e8952b`) is never used as body-text color on light backgrounds. Use `--ds-accent-deep` (`#8b5e0a`) when accent-colored text must appear at body size.

---

> **[Corrected] — the whole table and the rule below it.** Every row measures a
> withdrawn colour, so none of these ratios describes the shipped surface, and
> the rule about `--ds-accent` at body size guards a token nothing reads. The
> current measured ratios live where they are measured: `tokens.css` records the
> record-ramp ratios at the primitive definitions (`--prim-record-350` 2.08:1 on
> `#f1f3ef` / 1.91:1 on `#e7eae5`; `--prim-record-500` 3.39:1 / 3.12:1;
> `--prim-record-600` 5.45:1 / 5.01:1) and the state `fg` ratios on
> `--prim-record-50` (green-700 4.75:1, red-700 5.75:1, orange-700 4.55:1,
> blue-700 5.82:1). Focus-ring and control-edge ratios are re-measured in the
> browser gate, not asserted here.

---

## MkDocs alignment notes

To bring `/docs/` visually in line with the marketing site, update `site/docs/stylesheets/extra.css`:

1. **Replace indigo accent** (`#5e6ad2` / `--md-accent-fg-color`) with amber: `#e8952b` on dark, `#8b5e0a` on light for text links.
2. **Update dark mode canvas** (`[data-md-color-scheme="slate"]`) to `--ds-hero-bg` (`#0b0e12`) — matches the marketing dark zone exactly.
3. **Update light mode surface** to `--ds-surface` (`#fafaf9`) — replaces Material's default `#ffffff`.
4. **Header** stays dark zone (`#0b0e12`) — already correct in current `extra.css`.
5. **Card hover accent** changes from `#5e6ad2` to `#e8952b`.
6. **Inline code chip accent** changes from `rgba(94,106,210,0.07)` / `#3a4ab8` to `rgba(232,149,43,0.10)` / `#8b5e0a`.

These are 6 targeted find-replace operations in `extra.css`. The structural CSS (hero layout, full-bleed, section rhythm) is unchanged.

---

> **[Corrected] — this whole section is inoperative.** The docs surface migrated
> from MkDocs / Material to Starlight, so `site/docs/stylesheets/extra.css` and
> every `--md-*` slot named below are gone, and the amber values the six
> find-replace steps would write are withdrawn. The docs surface is also
> explicitly out of the palette amendment's scope by owner decision: `docs-site/`
> keeps its own palette and does not read `web/src/styles/tokens.css`
> (ADR-0085). No action survives from this section.


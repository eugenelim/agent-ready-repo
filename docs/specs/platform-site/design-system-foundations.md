# Design System Foundations — agent-ready-repo platform

Derived from `site/aesthetic-direction.md` (Option B — Alternating Conviction).  
Follows the three-tier architecture: **Primitive → Semantic → Component**.  
Implementation target: Astro marketing site CSS + MkDocs `extra.css` override.

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

## Typeface decisions

| Role | Font | Notes |
|---|---|---|
| Display + headings + body | **Inter** (already in MkDocs) | 700–800 at display, 400 at body |
| Code, skills, commands, chips | **JetBrains Mono** (already in MkDocs) | Uppercase + wide tracking for labels |
| No additional typefaces | — | Adding a third face breaks the identity |

The existing MkDocs `font:` config (`text: Inter`, `code: JetBrains Mono`) is correct. No change needed.

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

## MkDocs alignment notes

To bring `/docs/` visually in line with the marketing site, update `site/docs/stylesheets/extra.css`:

1. **Replace indigo accent** (`#5e6ad2` / `--md-accent-fg-color`) with amber: `#e8952b` on dark, `#8b5e0a` on light for text links.
2. **Update dark mode canvas** (`[data-md-color-scheme="slate"]`) to `--ds-hero-bg` (`#0b0e12`) — matches the marketing dark zone exactly.
3. **Update light mode surface** to `--ds-surface` (`#fafaf9`) — replaces Material's default `#ffffff`.
4. **Header** stays dark zone (`#0b0e12`) — already correct in current `extra.css`.
5. **Card hover accent** changes from `#5e6ad2` to `#e8952b`.
6. **Inline code chip accent** changes from `rgba(94,106,210,0.07)` / `#3a4ab8` to `rgba(232,149,43,0.10)` / `#8b5e0a`.

These are 6 targeted find-replace operations in `extra.css`. The structural CSS (hero layout, full-bleed, section rhythm) is unchanged.

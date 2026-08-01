# Spec: site-design-system-spec

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [plan.md](plan.md)
- **Constrained by:** [design-system-foundations.md](../platform-site/design-system-foundations.md), [platform-site/spec.md](../platform-site/spec.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed (documentation + tooling)

Mode: light (no risk trigger — internal docs tooling, no structural CSS change; no RFC needed)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The platform site's design system is authoritatively implemented in
`web/src/styles/tokens.css` and narrated in
`docs/specs/platform-site/design-system-foundations.md`. No single
machine-readable, human-browsable document in the `web/` source tree
consolidates the complete token vocabulary, component vocabulary, zone
rules, dark-mode equivalents, and known third-party deviations.

This spec delivers two artefacts:

1. **`web/src/design-system.md`** — a Markdown document in the `web/`
   tree that is the single reference for every designer or developer
   working on the platform site. It covers: color tokens (names, roles,
   zone assignments), typography scale, spacing rhythm, component
   vocabulary (BEM classes + token usage per component), zone rules, dark
   mode equivalents (Starlight docs-site `[data-theme='dark']` only), the card icon
   parity decision, and an audit of Starlight CSS deviations.

2. **`tools/lint_zone_violations.py`** — a stdlib-only Python lint script
   that scans `web/src/` for raw color values (hex literals or `rgba()`
   calls) used as CSS property values outside the token-definition
   `:root {}` block, and exits non-zero on any violation.

Success: a developer opening `web/src/design-system.md` finds the
complete, canonical token reference for the Astro site; the lint exits 0
on the current clean codebase; and the card icon parity question has a
documented resolution decision.

## Acceptance Criteria

- [x] **AC1.** `web/src/design-system.md` documents all color tokens from
  `web/src/styles/tokens.css`: Tier 1 primitive names with hex values and
  roles (dark zone, neutral/light zone, amber-gold accent, alpha tokens),
  Tier 2 semantic names with their primitive targets and zone assignments
  (hero/dark zone vs. content/light zone vs. accent layer vs. CTA layer),
  and the layering rule (component CSS references semantic tokens only —
  never primitives directly).
- [x] **AC2.** `web/src/design-system.md` documents the typography scale:
  font families (`--ds-font-sans`, `--ds-font-mono`), all eight size steps
  (`--ds-type-display` through `--ds-type-mono-sm`) with pixel-range
  equivalents, all five weight steps, all four tracking values, and all
  four leading values — each with its intended usage context.
- [x] **AC3.** `web/src/design-system.md` documents the spacing rhythm: the
  4px base grid, all ten `--ds-space-*` steps with pixel values, and the
  four responsive layout tokens (`--ds-section-gap`, `--ds-section-pad-y`,
  `--ds-content-max`, `--ds-content-pad-x`). It also documents radius (4
  steps), shadow (overlay-only philosophy), motion (3 durations + 2 easing
  curves), and z-index (5 steps).
- [x] **AC4.** `web/src/design-system.md` documents the component
  vocabulary for the marketing-homepage and catalogue/pack components. Scope:
  Hero section, StatStrip, ThreeLoops loop items, HumanGates gate cards,
  AdapterMatrix table, InstallTerminal + CSS-only tabs, PackCatalogue
  loop-cards + pack-cards, BuildYourOrg, Section band wrapper (surface /
  surface-alt / dark tones), SiteNav, SiteFooter, PackCard (`/packs/`
  index), catalogue `cat-card` (`/catalogue/`), copy button. Journey pages,
  plugin pages, and 404 are out of scope. Each listed component is
  documented with its zone assignment, BEM class names, and its primary
  semantic tokens (zone-defining color, typography, and motion tokens — per-component
  spacing values are covered by §3 and are not repeated per component). Spot-check
  greps per component (e.g. `grep "loop__n"
  web/src/design-system.md` for ThreeLoops, `grep "cat-card"` for
  catalogue card) must each return a match.
- [x] **AC5.** `web/src/design-system.md` states that the Astro marketing
  site page and component CSS (`web/src/`) has no `prefers-color-scheme: dark`
  media query; dark zone is a layout property (specific sections use
  `--ds-hero-bg`), not a user-preference mode. The document notes that
  `web/public/favicon.svg` does include such a query for the favicon fill, but
  this is a standalone SVG asset outside the component CSS scope. Dark mode equivalents exist only in the Starlight
  docs-site layer (`docs-site/src/styles/starlight.css` via
  `[data-theme='dark']`). The Starlight CSS imports `tokens.css` at build
  time and expresses dark-mode overrides via `--prim-*` / `--ds-*` tokens
  rather than raw hex. The document lists the resolved dark-mode values:
  surface (`var(--prim-dark-950)` → `#0b0e12`), accent (`var(--ds-accent)`
  → `#e8952b`), link color (`var(--prim-amber-300)` → `#f5bc6a`), inline
  code background (`var(--ds-accent-subtle-dk)` →
  `rgba(232,149,43,0.15)`).
- [x] **AC6.** `web/src/design-system.md` documents the card icon parity
  decision: ThreeLoops section (Section 4) items carry ordered numeric
  sequence badges (`.loop__n`: 01 / 02 / 03) because they represent named
  steps in a sequential "how it works" narrative; PackCatalogue section
  (Section 8) `.loop-card` items and all catalogue/pack cards (`cat-card`,
  `pack-card`) are unordered catalogue entries and intentionally carry no
  numeric badge. The visual asymmetry is by design — different content
  types with different information architectures. No badge or icon
  additions are in scope for this spec; this AC records the decision so the
  question is closed.
- [x] **AC7.** `web/src/design-system.md` audits the Starlight CSS
  (`docs-site/src/styles/starlight.css`): the file imports `tokens.css`
  at build time and is predominantly token-compliant. The document lists
  the two known raw-hex deviations and their closest `--ds-*` equivalents:
  `#ffffff` in `--sl-color-text-invert` (Starlight's light-mode inverted
  text slot, same resolved value as `--ds-hero-fg: #ffffff` but different
  semantic role) and `#ffffff` in `.site-footer__brand { color }` (bootstrap
  context for the Starlight footer). Both values could technically reference
  `--ds-hero-fg` (as demonstrated by `--sl-color-accent: var(--ds-accent)` at
  `starlight.css` line 23) but were not updated — they are current out-of-scope
  deviations, not necessary architectural exceptions. The document notes that
  fixing these is out of scope for this spec.
- [x] **AC8.** `tools/lint_zone_violations.py` exists and scans
  `web/src/**/*.{astro,css}` for raw color assignments (bare hex literals
  `#rrggbb` or `rgba()` calls used as CSS property values) that appear
  outside a `:root {}` token-definition block. The script excludes:
  (a) comment lines — `/* … */` (CSS) and line-leading `//` (i.e. lines matching `^\s*//`; JS/TS comments in `.astro` frontmatter are always line-leading, so a line-leading test is sufficient and avoids adding per-file fence-state tracking);
  (b) SVG attribute lines (`fill=`, `stroke=`, `xmlns=`, `viewBox=` etc.);
  (c) the `:root {}` token-definition block in `tokens.css`. The exclusion
  assumes flat, single-line-brace `:root` blocks (the current `tokens.css` shape — two
  single-line `{` openings, no nested braces). The scanner operates line-by-line and
  handles both multi-line declarations (property name and value on separate lines, with
  state tracked through the terminating semicolon) and inline single-line rules like
  `.foo { color: #fff; }` (detected by scanning the portion after `{`). Astro frontmatter
  is scanned as-is; a frontmatter object property that resembles a CSS property could
  false-positive, but `web/src/` frontmatter patterns do not match this shape. Exits 0 = clean,
  exits 1 = violations found, printing `file:line: <value>` for each hit.
- [x] **AC9.** `python tools/lint_zone_violations.py web/src/` exits 0 on
  the current codebase. Note: this AC is validated by running the lint itself, not by
  a preliminary grep — the lint's comment-exclusion logic (including `//` comments in Astro
  frontmatter) determines the outcome.
- [x] **AC10.** `docs/specs/README.md` is updated to include this spec in
  the active list.

## Boundaries

### Always do

- Keep `web/src/design-system.md` as documentation of *existing* tokens —
  derive all values from `web/src/styles/tokens.css` as the implementation
  authority.
- Scope the lint to `web/src/` only; use stdlib Python with no new
  dependency.
- Record the card icon parity decision as-is (asymmetry is intentional);
  do not add any layout element.

### Never do

- Change any existing CSS — this spec documents first; CSS changes are a
  separate PR.
- Add icons, badges, or any visual element to catalogue cards or loop cards.
- Extend the lint to `docs-site/src/styles/starlight.css` — Starlight is
  intentionally outside the lint's scope; the two `#ffffff` deviations there
  are known current deviations (documented in §8 of design-system.md), not
  violations to suppress.
- Introduce a new dependency beyond stdlib Python for the lint script.
- Rename or reorganise existing tokens, even to fix the two Starlight
  deviation values.

### Ask first

- Any fix to the two known Starlight deviation values (`#ffffff` in
  `--sl-color-text-invert` and `.site-footer__brand`).
- Any decision to add `prefers-color-scheme: dark` support to the Astro
  marketing site.

## Testing Strategy

Goal-based throughout — no new compilation step, no production test file.

- **AC1–AC7 (`web/src/design-system.md` content):** Manual read-through.
  Verify each section against `web/src/styles/tokens.css` as the source of
  truth. Representative spot-check: `grep
  "ds-type-display\|ds-space-1\|ds-accent-subtle-dk"
  web/src/design-system.md` returns matches.
- **AC8 (lint script exists and runs):** `python
  tools/lint_zone_violations.py web/src/` runs without import error or
  crash. Introduce a synthetic violation in a scratch file, confirm exit 1
  and a `file:line:` report; remove the scratch file.
- **AC9 (lint exits 0 on current codebase):** `python
  tools/lint_zone_violations.py web/src/ && echo OK` exits 0.
- **AC10 (README updated):** `grep site-design-system-spec
  docs/specs/README.md` returns a match.

## Assumptions

- Technical: The implementation authority for all `--ds-*` and `--prim-*`
  token values is `web/src/styles/tokens.css`; `docs/specs/platform-site/
  design-system-foundations.md` is the upstream narrative spec. (Verified.)
- Technical: The Astro component CSS is currently fully token-compliant — no
  raw hex or `rgba()` values appear as CSS property assignments outside
  `tokens.css`. (Verified: grep returned only comment-line matches.)
- Technical: Dark mode equivalents exist only in the Starlight docs-site layer
  (`docs-site/src/styles/starlight.css`); the Astro marketing site's "dark zone"
  is a layout concept and carries no `prefers-color-scheme` media query. The repo
  migrated from MkDocs/Material to Starlight — the spec's original AC5/AC7
  references to `site/docs/stylesheets/extra.css` and `.md-*` component classes
  have been updated accordingly. (Verified.)
- Technical: "Loop cards have icons" refers to ThreeLoops `.loop__n` badges;
  "catalogue cards" refers to PackCatalogue and `cat-card` items which carry
  no badge. The asymmetry is intentional. (Verified.)
- Technical: The two Starlight deviation values (`#ffffff` in
  `--sl-color-text-invert` and `.site-footer__brand`) are current out-of-scope
  deviations — both could technically reference `--ds-hero-fg` but were not
  updated as part of this spec. (Verified.)
- Process: No RFC is needed — the backlog entry explicitly states "no RFC
  needed — internal docs tooling; normal PR."

## Tasks

1. **Inventory existing CSS tokens** — Read `web/src/styles/tokens.css`
   top-to-bottom; read every `.astro` file and extract BEM class names and
   their token usage.
2. **Write `web/src/design-system.md`** — Author the full token reference
   covering AC1–AC7.
3. **Write `tools/lint_zone_violations.py`** — Stdlib-only Python state
   machine that walks `web/src/`, skips comment lines and SVG attribute
   lines, skips the `:root {}` block in `tokens.css`, and flags bare hex
   or `rgba()` values in CSS property positions. Exits 0 = clean, 1 =
   violations.
4. **Verify lint exits 0** — Run the lint against the current codebase.
5. **Update `docs/specs/README.md`** — Add this spec to the active list.

## Declined

- Fixing the two Starlight deviation values (`#ffffff`) — out of scope for this
  spec; both could technically reference `--ds-hero-fg` (same resolved value) but
  were not updated here.
- Auditing Material/MkDocs component families — MkDocs replaced by Starlight;
  `.md-*` component classes no longer exist in the codebase. Note: the
  `site-shell` spec (its plan.md §18–21 and spec.md §27–30) was authored
  when this spec deferred four Material deviation fixes to it; that deferral
  is now superseded — MkDocs is gone, so there is nothing left to implement.
  The site-shell spec is now historical context only.
- Adding `prefers-color-scheme: dark` to the Astro marketing site — out of scope.
- Adding icons or badges to catalogue cards.
- Linting `docs-site/src/styles/starlight.css` — Starlight is intentionally outside this lint's
  scope; the two `#ffffff` deviations there are known current deviations, not suppressible
  false positives.
- Scanning HTML `style` attributes in Astro markup (`<div style="color: #fff">`) — would
  require HTML attribute parsing across multiple lines; the line-by-line CSS scanner design
  does not cover this. `web/src/` components use CSS custom properties via class names, not
  inline style attributes, so no violations exist there in practice.
- Failing closed on directory-enumeration `PermissionError` from `Path.rglob()` — the lint
  exits 2 on `OSError` reading a file; rglob enumeration errors are not surfaced by the
  stdlib. Acceptable for a developer-owned source tree where all paths are readable.

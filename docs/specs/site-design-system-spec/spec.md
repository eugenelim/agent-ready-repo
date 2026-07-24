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
   mode equivalents (MkDocs only), the card icon parity decision, and an
   audit of Material-injected component deviations.

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
  documented with its zone assignment, BEM class names, and the semantic
  tokens it uses. Spot-check greps per component (e.g. `grep "loop__n"
  web/src/design-system.md` for ThreeLoops, `grep "cat-card"` for
  catalogue card) must each return a match.
- [x] **AC5.** `web/src/design-system.md` states that the Astro marketing
  site has no `prefers-color-scheme: dark` media query; dark zone is a
  layout property (specific sections use `--ds-hero-bg`), not a
  user-preference mode. Dark mode equivalents exist only in the MkDocs
  layer (`site/docs/stylesheets/extra.css` via `[data-md-color-scheme=
  "slate"]`). The document lists the dark-mode token values defined there:
  surface (`#0b0e12`), code background (`#111520` — `var(--prim-dark-900)`, overriding Material's default `#141516`), accent (`#e8952b`),
  link color (`#f5bc6a`).
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
- [x] **AC7.** `web/src/design-system.md` audits Material-injected
  component deviations: the MkDocs `extra.css` overrides Material for
  MkDocs using raw hex values (by necessity — `--ds-*` custom properties
  are defined in the Astro build layer and are not available to the MkDocs
  build). The document lists each Material component family overridden
  (`.md-header`, `.md-tabs`, `.md-button`, `.grid.cards`, `.md-typeset
  code` / `pre`, `.md-typeset table`, `.md-banner`, `.platform-back-link`)
  and flags the four known value deviations from the token spec: `#f8fafc`
  (primary text on dark, Material context) vs `--ds-hero-fg: #ffffff`;
  `#141516` (dark code background) vs `--prim-dark-900: #111520`; `#1a202c`
  (table header text) vs `--prim-neutral-900: #1c1b18`; `#e2e8f0` (table
  border) which has no primitive-scale equivalent.
- [x] **AC8.** `tools/lint_zone_violations.py` exists and scans
  `web/src/**/*.{astro,css}` for raw color assignments (bare hex literals
  `#rrggbb` or `rgba()` calls used as CSS property values) that appear
  outside a `:root {}` token-definition block. The script excludes:
  (a) comment lines — `/* … */` (CSS) and line-leading `//` (i.e. lines matching `^\s*//`; JS/TS comments in `.astro` frontmatter are always line-leading, so a line-leading test is sufficient and avoids adding per-file fence-state tracking);
  (b) SVG attribute lines (`fill=`, `stroke=`, `xmlns=`, `viewBox=` etc.);
  (c) the `:root {}` token-definition block in `tokens.css`. The exclusion
  assumes flat, single-line-brace `:root` blocks (the current `tokens.css` shape — two
  single-line `{` openings, no nested braces). Exits 0 = clean, exits 1 = violations found,
  printing `file:line: <value>` for each hit.
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
- Extend the lint to `site/docs/stylesheets/extra.css` — Material overrides
  require raw hex values by design; linting them produces only false
  positives.
- Introduce a new dependency beyond stdlib Python for the lint script.
- Rename or reorganise existing tokens, even to fix the four Material
  deviation values.

### Ask first

- Any fix to the four known Material deviation values (`#f8fafc`,
  `#141516`, `#1a202c`, `#e2e8f0`).
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
- Technical: Dark mode exists only in the MkDocs layer; the Astro marketing
  site's "dark zone" is a layout concept and carries no `prefers-color-scheme`
  media query. (Verified.)
- Technical: "Loop cards have icons" refers to ThreeLoops `.loop__n` badges;
  "catalogue cards" refers to PackCatalogue and `cat-card` items which carry
  no badge. The asymmetry is intentional. (Verified.)
- Technical: The four Material deviation values in `extra.css` are known
  side-effects of Material for MkDocs requiring raw CSS values. (Verified.)
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

- Fixing the four Material deviation values — out of scope; a follow-on PR.
- Adding `prefers-color-scheme: dark` to the Astro marketing site — out of scope.
- Adding icons or badges to catalogue cards.
- Linting `site/docs/stylesheets/extra.css` — Material overrides require raw values.

# Spec: docs-site-design-refresh

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0061 (web/ top-level directory), platform-site spec (design-system foundations), [`creative-direction.md`](creative-direction.md)
- **Brief:** user direction in-session (2026-08-05): adopt the navigation / font / section-layout design language of an external reference docs site (supplied in-session; deliberately not named in-tree) on our Starlight tech docs; keep Astro; pick a color theme conveying engineering capability and enterprise professionalism; split per-site agent context files.
- **Contract:** none
- **Shape:** build

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it.

## Objective

A reader of the tech docs site (`docs-site/`, served at `/agent-ready-repo/docs/`)
gets a page whose typography, navigation, and section layout carry the design
language of the grounded reference — an optical-size display serif over a
working sans, eyebrow-labeled sidebar groups, hairline rules as the only
chrome, generous whitespace — expressed in a cool, single-accent enterprise
palette instead of the reference's warm terracotta/paper. Today the site
renders in system-font fallbacks (the CSS declares `Inter Variable` and
`JetBrains Mono` but `docs-site/package.json` installs no font package) over
near-default Starlight with amber accents — the "broken" styling this spec
replaces. The direction is named and ranked in
[`creative-direction.md`](creative-direction.md); this spec and its plan
derive the values.

## Boundaries

### Always do

- Keep Astro + Starlight — restyle via `customCss`, config, and the two
  existing component overrides (`Banner`, `Footer`); do not fork Starlight
  internals.
- Self-host all runtime assets via **exact-pinned** npm packages (repo
  precedent from `web/`): fonts via Fontsource, and mermaid bundled instead
  of the current CDN script. No runtime CDN calls remain.
- Hold the WCAG AA floor: text pairs ≥ 4.5:1 **against the ground they
  actually sit on** (main ground, sidebar ground, chip/tint fills, code
  ground) in both themes; `:focus-visible` indicator ≥ 3:1 non-text contrast
  (WCAG 1.4.11) at ≥ 2px; `prefers-reduced-motion` honored.
- Keep Starlight's functional affordances — search (including the pagefind
  results overlay), theme toggle, skip links, mobile drawer, on-page ToC —
  restyled, never removed.
- Record the new dependencies and the docs-palette divergence in a new
  `docs-site/AGENTS.md` before they land (repo AGENTS.md § Check before
  acting).

### Ask first

- Any change to the marketing site's (`web/`) rendered appearance — its
  palette remains amber/dark-hero; only its `AGENTS.md` is touched here.
- Any change to sidebar IA / nav structure (owned by the queued
  `catalogue-wave6-technical-docs-ia` item) — this spec restyles the existing
  structure only.

### Never do

- Add a CSS framework (Tailwind et al.) — banned by the platform-site spec.
- Edit `guides/**` or generated content under `docs-site/src/content/`.
- Touch `tools/build-site.py` or the `pages.yml` build-order steps.
  (`docs.yml` — the AGENTS.md lint workflow — gains two `paths:` entries so
  AC8's line caps are CI-enforced; that is the only workflow edit.)
- Use the display serif at body or UI sizes (creative-direction arbitration:
  clarity beats gravitas).

## Testing Strategy

No compressible invariant — this is build config + CSS + prose. Verification
is **goal-based** (builds, greps against built output, numeric contrast
script) plus **visual/manual QA** (screenshots of the real built site at
desktop and 375 px, light and dark), per the work-loop verification-mode
doctrine. Contrast pairs are computed numerically (script in plan) and the
measured table in the plan is the record.

## Acceptance Criteria

- [x] **AC1 (fonts, exact pins).** `docs-site` self-hosts three families via
  exact-pinned Fontsource packages — `@fontsource-variable/source-serif-4@5.3.0`
  (display serif), `@fontsource-variable/inter@5.3.0`,
  `@fontsource/jetbrains-mono@5.3.0` — wired through Starlight `customCss`;
  the built CSS contains their `@font-face` rules; the installed
  Source Serif 4 build demonstrably exposes the `opsz` axis (checked against
  the package's `@font-face` declarations); rendered pages use all three
  families. Install-script audit (lockfile-wide, covering mermaid's
  transitive tree too): no entry in `docs-site/package-lock.json` carries
  `"hasInstallScript": true` beyond the **versioned** keys already vetted in
  `package.json` `allowScripts` (currently `esbuild@0.28.1`,
  `fsevents@2.3.3`) — a different version of either package carrying an
  install script fails the audit. These pins are the
  canonical version record; the plan references them rather than restating.
- [x] **AC2 (header).** The header is restyled to the reference language:
  light ground with a hairline bottom rule in light mode (dark equivalent in
  dark mode), wordmark set in the display serif; search and theme toggle
  remain functional, and the pagefind search modal/results overlay is
  restyled to the new palette (not left at default styling).
- [x] **AC3 (sidebar).** Sidebar group labels render as accent eyebrows
  (uppercase, letter-spaced, small); links are medium-weight rows with
  rounded hover/active treatment; the active item carries an accent-tinted
  background — matching the reference's sidebar grammar.
- [x] **AC4 (prose).** Content typography carries the reference language:
  h1/h2 in the display serif with optical sizing active, h2 with a hairline
  bottom rule, h3 in the sans at semibold, body line-height ≥ 1.7, inline
  code as tinted chips, code blocks dark-on-light with rounded corners,
  styled tables (2px head rule, 1px row rules) and accent-bordered
  blockquotes.
- [x] **AC5 (palette).** Both light and dark themes are fully mapped to a
  cool neutral ground with a single cobalt-family accent; every text/ground
  pair used for body, sidebar, eyebrows, chips, and code text is ≥ 4.5:1
  **measured against its actual ground**, recorded in the plan's measured
  table. The theme default remains Starlight's system-following `auto`
  (decision: respecting the OS preference is the enterprise-polish behavior;
  "light-first" in the direction doc means light is the primary derivation
  target, with dark re-derived — not a forced default).
- [x] **AC6 (footer + banner + chrome colors + primitive compatibility).**
  The hard-coded dark-hero palette in `starlight.css` (`header.header`,
  `.site-footer*` rules) is replaced by the new language (hairline rules,
  faint small text meeting AA); the `Footer.astro` prev/next block and
  `Banner.astro` are styled consistently. The `tokens.css` import is
  dropped, and a **compatibility block** in `starlight.css` re-derives the
  `--ds-*`/`--prim-*` names consumed by the primitive components under
  `docs-site/src/components/primitives/` (not edited) onto the new doc
  tokens, so they stay styled *and* re-palette. **State-token carve-out:**
  the semantic state tokens (`--ds-state-{success,danger,warn,info,neutral}-*`)
  keep hue-distinct green/red/orange/blue/gray values — retuned for the
  cool grounds in both themes, never collapsed into the cobalt accent —
  with each fg-on-bg pair recorded in the plan's measured contrast table
  (visual QA cannot exercise state chips; the numeric record is the
  evidence). Verified by extracting every `var(--ds-*`/`var(--prim-*` name
  consumed in `docs-site/src` and checking each has a docs-local
  definition (the extraction, not a hand count, is the contract). No amber
  `--ds-accent` value survives.
- [x] **AC7 (responsive + a11y floor).** No horizontal body scroll at
  375 px on the checked pages; `prefers-reduced-motion` disables the
  transitions this spec adds; `:focus-visible` meets the ≥ 3:1 / ≥ 2px bar
  in both themes.
- [x] **AC8 (per-site agent context).** `docs-site/AGENTS.md` exists (with
  `CLAUDE.md` symlink) recording the dependency table, the docs-palette
  divergence from `--ds-*`, and the canonical build-order fact;
  `web/AGENTS.md` is slimmed to marketing-site scope and **references** the
  canonical build-order fact in `docs-site/AGENTS.md` rather than restating
  it (shared facts live in exactly one place). Both files ≤ 150 lines;
  `.github/workflows/docs.yml` `paths:` gains `docs-site/**/AGENTS.md` and
  `web/**/AGENTS.md` so the cap is CI-enforced for both.
- [x] **AC9 (mermaid self-hosted).** The runtime CDN `<script>` for mermaid
  is removed; `mermaid@11.16.1` (exact pin) is bundled as a docs-site
  dependency and lazily imported client-side with
  `{ startOnLoad: false, securityLevel: 'strict' }`, rendering the existing
  `.mermaid-diagram[data-mermaid]` placeholders; diagrams still render on
  guide pages that use them. Theming decision: diagrams **re-render on
  theme toggle** (observe `data-theme` on the root element; mermaid theme
  `neutral` in light, `dark` in dark) so the surface is fully mapped in
  both modes — the raw source stays available in `data-mermaid`.
- [x] **AC10 (gates + QA evidence).** `python tools/build-site.py`, the
  `web` build, and the `docs-site` build all pass; screenshots of the docs
  home, one guide page, and one reference page (light + dark, desktop +
  375 px) are captured during QA and the observed results recorded in the
  PR.

## Assumptions

- The user's in-session direction constitutes the scope decision (they named
  the reference, the palette register, the mermaid concern, and the
  AGENTS.md split explicitly); aesthetic value choices within that register
  are delegated ("pick a good color theme").
- `web/` and `docs-site/` may diverge chromatically: docs adopt the new
  enterprise palette while the marketing site keeps amber/dark-hero.
  Re-skinning `web/` is surfaced as a follow-on decision in the PR.
- **Deferred (slugs recorded in `[backlog].open` at spec stage; T5
  re-verifies their presence at ship time):** SCA coverage for
  `docs-site/package-lock.json` (no `npm audit`/Dependabot wiring exists
  repo-wide; adding scanner infra is out of scope) — deferral slug
  `docs-site-npm-sca-gap`. Print-specific styling beyond Starlight's
  defaults — deferral slug `docs-site-print-styles`.

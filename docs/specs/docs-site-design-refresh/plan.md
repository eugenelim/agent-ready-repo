# Plan: docs-site-design-refresh

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** implementation strategy; allowed to change as we learn.

## Approach

Everything lands inside `docs-site/` plus the two `AGENTS.md` files and two
`paths:` lines in `.github/workflows/docs.yml`. The shape: install and wire
the fonts first (they are the load-bearing fix — the site currently renders
in system fallbacks), then rewrite `src/styles/starlight.css` as a
self-contained token sheet + Starlight override layer expressing the
reference's design language in the enterprise palette (including the
`header.header` / `.site-footer*` rules that currently hard-code the
dark-hero palette), then bundle mermaid and align the custom components and
Expressive Code, then split the per-site `AGENTS.md`, then run the visual-QA
sweep against the real built site.

The riskiest part is styling against Starlight internals we don't own. Per
the EXECUTE contract-grounding gate, the selector/variable contract was
verified against the installed `@astrojs/starlight@0.41.4` source (grounded
2026-08-05): `:root` carries dark-mode values with light overrides under
`[data-theme='light']`; key slots `--sl-color-*`, `--sl-font`,
`--sl-content-width` (45rem default), `--sl-nav-height`; component classes
`.site-title`, `header.header`, `.sidebar-content` with
`details > summary .group-label .large` groups and `a[aria-current="page"]`
links, `.sl-markdown-content`, `.starlight-aside*`, `.right-sidebar`
(`#starlight__on-this-page`), `.pagination-links` (unused — our Footer
renders its own `.sl-prev-next__*`), pagefind UI under `.pagefind-ui`.
Custom CSS loads unlayered, so it wins over Starlight's `@layer` styles.

`starlight.css` stops importing the `tokens.css` copied from `web/` — the
docs palette is deliberately self-contained so the two sites can diverge
(recorded in `docs-site/AGENTS.md`). The primitive components under
`docs-site/src/components/primitives/` consume `--ds-*`/`--prim-*`
references in scoped styles; they are **not edited** — a compatibility
block in the new `starlight.css` re-derives exactly the token names they
consume (per spec AC6's extraction contract — no hand counts), keeping
them styled and re-paletted, with the semantic state tokens carved out as
hue-distinct per AC6. `tools/build-site.py` still copies the file; removing that
copy step is deferred (touching the tool is out of scope per the spec's
Never-do).

## Assumption trio

- **Files touched:** `docs-site/package.json`, `docs-site/package-lock.json`,
  `docs-site/astro.config.ts`, `docs-site/src/styles/starlight.css`,
  `docs-site/src/components/Footer.astro`, `docs-site/src/components/Banner.astro`,
  `docs-site/AGENTS.md` (new), `docs-site/CLAUDE.md` (new symlink),
  `web/AGENTS.md`, `.github/workflows/docs.yml` (two `paths:` lines only),
  `workspace.toml` (two deferral slugs), this spec dir.
- **"Done" demonstrated by:** all three builds green; grep of built CSS for
  the three `@font-face` families; recorded screenshots (docs home, a
  how-to page, a reference page × light/dark × desktop/375 px); measured
  contrast table below; mermaid renders from the bundle with the CDN script
  gone.
- **Not changing:** `web/` rendered output, sidebar IA, `guides/**` content,
  `tools/build-site.py`, `pages.yml`, packs.

## Declined temptations

- Re-skinning `web/` to the new palette — separate decision, surfaced in PR.
- Forking Starlight components (Header/Sidebar/PageFrame overrides) — CSS +
  config reach every AC; component forks rot against upstream.
- Restructuring the sidebar IA — owned by `catalogue-wave6-technical-docs-ia`.
- Adding Tailwind to match the reference's implementation — banned; the
  language ports to plain CSS.
- Adding Dependabot/`npm audit` CI infra to close the SCA gap properly —
  new scanner infrastructure; recorded as an explicit deferral instead.
- Removing the `tokens.css` copy step from `tools/build-site.py` — works
  today; deferred.

## Design (LLD) — token derivation

Playing the `design-system` role for this surface, from the four named goals.
Two-tier: `--doc-*` primitives → `--sl-*` (Starlight semantic slots).

**Type.** Display serif: **Source Serif 4 Variable** (`opsz` + `wght` axes) —
optical sizing like the reference's serif but a crisper, more restrained cut
(enterprise register; grounds: creative-direction goals 2+3). Body/UI:
**Inter Variable** (matches `web/`). Code: **JetBrains Mono** 400/500/600/700
(matches `web/`). Versions: exact pins as named canonically in spec AC1/AC9
(not restated here). Fontsource caveat: the default `index.css` of a
variable package carries the `wght` axis only — the `opsz`-carrying
stylesheet (e.g. `…/opsz.css`; exact path verified against the installed
package in T1) must be the wired import for the serif.

**Light theme (default derivation target).** Measured 2026-08-05 with the
WCAG relative-luminance formula (script below).

| Role | Value | Measured contrast |
| --- | --- | --- |
| ground | `#f7f8fa` | — |
| ground-deep (chips, tints) | `#eceff2` | — |
| ink (headings) | `#111827` | 16.69 on ground |
| ink-soft (body) | `#2b3444` | 11.78 on ground |
| ink-muted (captions, sidebar idle) | `#4b5565` | 7.09 on ground |
| ink-faint (footer small print) | `#67707f` | 4.70 on ground |
| rule (hairlines) | `#dfe3e9` | decorative |
| accent (icons, large text ≥ 24px) | `#2563eb` | 4.86 on ground |
| accent-deep (links, eyebrows, chip text) | `#1d4ed8` | 6.31 on ground; 5.81 on ground-deep |
| accent-tint | `rgba(37, 99, 235, 0.08)` | fill only |
| code-block ground | `#0d1424` | — |
| code-block text | `#c9d6ee` | 12.55 on code ground |

**Semantic state tokens (AC6 carve-out — hue-distinct, never cobalt).**
Measured fg-on-bg (light): success `#15803d` on `#dcfce7` = 4.57; danger
`#b91c1c` on `#fee2e2` = 5.30; warn `#c2410c` on `#ffedd5` = 4.52; info
`#1d4ed8` on `#dbeafe` = 5.49; neutral `#2b3444` on `#eceff2` = 10.85.
Measured fg-on-bg (dark): success `#86dfa8` on `#122a1c` = 9.56; danger
`#f4a3a3` on `#341418` = 8.43; warn `#f0b27f` on `#33200f` = 8.40; info
`#8ab0f9` on `#131f3a` = 7.52; neutral `#c3ccdb` on `#1a2130` = 9.95.
Borders take the mid value of each hue family (decorative, no AA claim).

Eyebrows and chip text use `accent-deep` (never `accent`) so they clear AA
on both ground and ground-deep. The sidebar shares the main ground (the
reference's grammar — a hairline `border-inline-end`, not a tinted panel),
so sidebar text pairs measure against `#f7f8fa`.

**Dark theme.** Measured same date.

| Role | Value | Measured contrast |
| --- | --- | --- |
| ground | `#0c111c` | — |
| surface (search modal, cards) | `#111726` | — |
| text | `#c3ccdb` | 11.67 on ground |
| text-muted | `#8b95a7` | 6.25 on ground |
| rule | `rgba(255,255,255,0.09)` | decorative |
| accent (links/active/eyebrows) | `#8ab0f9` | 8.68 on ground |
| accent-tint | `rgba(138, 176, 249, 0.12)` | fill only |

Verification script (rerun in T5 against the final CSS values):
`python3` one-liner computing WCAG 2.x relative luminance + contrast ratio
for every pair above; any pair < 4.5 fails the gate.

**Layout grammar (from the reference):** eyebrow labels 11px/500/0.18em
uppercase in accent-deep; sidebar rows 13.5px/500 with 6px-radius hover
pills; h2 hairline underline; content measure kept near Starlight's 45rem;
hairline borders, no shadows; motion 150ms color transitions only, inside
`@media (prefers-reduced-motion: no-preference)`; `:focus-visible` 2px
solid `accent-deep` (light) / `accent` (dark), offset 2px — both ≥ 3:1
against their grounds.

## Tasks

### T1 — fonts + wiring

Depends on: none. Add the three Fontsource
  packages at the exact pins named in spec AC1; wire via Starlight
  `customCss` entries before `starlight.css`, using the serif's
  `opsz`-carrying stylesheet (verify exact path in the installed package —
  the default `index.css` is `wght`-only). Verify installed family names
  from the package `@font-face` CSS.
  `Tests:` no stub (goal-based). Done when: docs-site build passes, built
  CSS contains `@font-face` for all three families, `opsz` present in the
  serif's `@font-face` axes, and the lockfile-wide install-script audit
  passes: no `"hasInstallScript": true` in `docs-site/package-lock.json`
  beyond the `allowScripts`-vetted exceptions (esbuild, fsevents).
### T2 — starlight.css rewrite

Depends on: T1. Self-contained
  `--doc-*` token sheet (tables above) mapped onto the grounded `--sl-*`
  slots; header, sidebar, on-page ToC, prose (`.sl-markdown-content`),
  asides, pagefind search modal + results overlay, mobile drawer, and the
  existing `header.header`/`.site-footer*`/`.sl-prev-next__*` rules
  rewritten per the layout grammar; drop the `tokens.css` import and add
  the primitive-component **compatibility block** (re-derive the consumed
  `--ds-*`/`--prim-*` names onto cobalt/doc tokens); theme default stays
  `auto`.
  `Tests:` no stub (visual QA + goal-based). Done when: dev-server
  screenshots match the design language in both themes, and every
  `var(--ds-*` / `var(--prim-*` name consumed anywhere in `docs-site/src`
  has a docs-local definition (extraction script), with no amber accent
  value surviving.
### T3 — mermaid bundle + components + code blocks

Depends on: T2.
  Add mermaid at the exact pin named in spec AC9; replace the CDN head
  script with a bundled lazy `import('mermaid')` client script
  (`startOnLoad: false`, `securityLevel: 'strict'`) rendering
  `.mermaid-diagram[data-mermaid]`, re-rendering on root `data-theme`
  change (`neutral` light / `dark` dark, per AC9's theming decision);
  restyle `Footer.astro` prev/next + brand block and `Banner.astro`; set
  Expressive Code to a dark theme with rounded frames.
  `Tests:` no stub (visual QA + goal-based). Done when: a guide page with a
  mermaid block renders the diagram from the bundle (no jsdelivr request in
  the page source), the diagram re-themes on toggle, footer/banner/code
  blocks match in both themes.
### T4 — per-site AGENTS.md + lint wiring

Depends on: T1 (final
  dependency table), T3 (mermaid pin recorded). New `docs-site/AGENTS.md`
  (+ `CLAUDE.md` symlink): dependency table (fonts + mermaid), palette-
  divergence rationale, canonical build-order fact, dev/QA commands, SCA
  deferral note. Slim `web/AGENTS.md` to marketing-only; it references the
  canonical build-order fact instead of restating it. Add
  `docs-site/**/AGENTS.md` and `web/**/AGENTS.md` to `docs.yml` `paths:`.
  `Tests:` no stub (goal-based). Done when: both files ≤ 150 lines;
  `python tools/lint-agents-md.py` passes; `git grep` shows the build-order
  fact stated once and referenced once.
### T5 — QA sweep

Depends on: T2, T3, T4. Build all three steps;
  screenshot matrix (3 pages × 2 themes × 2 widths); rerun the numeric
  contrast script against final CSS values and correct the LLD tables if
  any pair moved; 375 px horizontal-scroll check; reduced-motion +
  focus-visible check; re-verify the two deferral slugs
  (`docs-site-npm-sca-gap`, `docs-site-print-styles`) are present in
  `workspace.toml [backlog].open` (recorded at spec stage).
  `Tests:` no stub (manual QA). Done when: all AC7/AC10 evidence recorded
  and both slugs grep-present in `[backlog].open`.

Single wave; sequential by the `Depends on:` lines.

## Construction tests

Covered per-task (`Done when:` lines). No unit-test surface — no logic.

## Changelog

- 2026-08-05: drafted.
- 2026-08-05 (round 3): semantic state tokens carved out of the cobalt
  derivation (hue-distinct, both themes, measured pairs added — round-3
  Blocker); brittle hand counts dropped in favor of the extraction
  contract; deferral slugs recorded in `[backlog].open` at spec stage with
  T5 re-verification; install-script allowlist comparison pinned to
  versioned `allowScripts` keys.
- 2026-08-05 (round 2): primitive-component compatibility block added (8
  components / 142 `--ds-*` refs would have been orphaned by the import
  drop — round-2 Blocker); `opsz` stylesheet path caveat pinned into
  T1/LLD; mermaid re-themes on toggle (decision recorded in AC9);
  install-script audit widened to lockfile-wide `hasInstallScript`
  (security round-2) and mechanisms aligned; version pins de-duplicated to
  spec AC1/AC9 as canonical.
- 2026-08-05: revised after pre-EXECUTE adversarial + security review —
  exact pins for all deps incl. serif; mermaid CDN → bundled dependency
  (new AC9); footer/banner colors repointed at `starlight.css` rules;
  pagefind overlay in scope; `ink-faint` corrected `#6b7484`→`#67707f`
  (4.43 → 4.70); contrast tables replaced with measured values; per-task
  `Depends on:`; `docs.yml` paths edit authorized; SCA + print-styles
  recorded as explicit deferrals; precedent names anonymized in the
  direction doc; theme-default decision pinned (`auto`).

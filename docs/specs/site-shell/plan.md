# Plan: site-shell

- **Spec:** [spec.md](spec.md)
- **Status:** Done

## Approach

Four coordinated changes that must ship together:

1. **Build pipeline** — `build-site.py` copies `web/src/styles/tokens.css` to
   `site/docs/stylesheets/tokens.css`. `mkdocs.yml` adds it to `extra_css`
   before `extra.css`. The copy runs as part of `site-sync` so no separate step
   is needed in CI.

2. **Token-driven `extra.css`** — Full rewrite replacing every standalone hex/rgba
   literal with a `var(--ds-*)` or `var(--prim-*)` reference. Adds the visual-seam
   fixes: button pill shape, card radius token, typography tokens, dark-mode token
   ladder. Implements the four Material deviation fixes deferred by
   `site-design-system-spec`: `#f8fafc → var(--ds-hero-fg)`,
   `#141516 → var(--prim-dark-900)`, `#1a202c → var(--ds-on-surface)`,
   `#e2e8f0 → var(--ds-border)`.

3. **Footer override** — `site/overrides/partials/footer.html` replaces
   Material's copyright block with a brand strip matching Astro's SiteFooter.
   Keeps Material's prev/next navigation (users rely on it).

4. **`.gitignore`** — Adds `site/docs/stylesheets/tokens.css` to prevent
   committing the generated artifact.

Declined: new top-level `tokens/` directory (RFC required); MkDocs font migration
(imperceptible visual difference, build complexity not worth it); any Astro changes.

## Tasks

### T1: Build pipeline — token copy + mkdocs.yml

**Depends on:** none

**Done when:**
- `make site-sync` runs without error
- `site/docs/stylesheets/tokens.css` exists and matches `web/src/styles/tokens.css`
- `make site-build` exits 0

**Approach:**
- `tools/build-site.py`: add `copy_tokens()` call after the changelog step; uses
  `shutil.copy2(REPO_ROOT / 'web/src/styles/tokens.css', SITE_DOCS / 'stylesheets/tokens.css')`
- Add `site/docs/stylesheets/tokens.css` to the `generated` list so it appears in `.siteignore`
- `site/mkdocs.yml`: add `- stylesheets/tokens.css` as the FIRST entry under `extra_css`
  (must precede `stylesheets/extra.css`)
- `site/mkdocs.yml`: add `copyright:` line for use in the footer template

---

### T2: Token-driven `extra.css`

**Depends on:** T1 (tokens.css must exist and be loaded before extra.css can reference it)

**Done when:**
- `grep -E '#[0-9a-fA-F]{3,6}' site/docs/stylesheets/extra.css` returns zero matches
- `make site-build` exits 0
- Dark header, amber accent, pill buttons, token-driven card styles all visible
  in `mkdocs serve`

**Approach:**
- Full rewrite of `site/docs/stylesheets/extra.css`:
  - `:root` mapping block: bind `--md-*` variables to `--ds-*` tokens
  - `[data-md-color-scheme="slate"]`: bind dark mode to `--prim-dark-*` / `--prim-amber-*`
  - `.md-header` / `.md-tabs`: replace `#0b0e12` with `var(--ds-hero-bg)`
  - `.md-button--primary`: add `border-radius: var(--ds-radius-pill)`;
    replace color literals with CTA tokens
  - `.grid.cards`: replace all literals with `--ds-surface-alt`, `--ds-radius-md`,
    `--ds-border-subtle`, `--ds-accent`, `--ds-dur-quick`
  - `.md-typeset code/pre`: reference `--ds-font-mono`, `--ds-radius-sm`,
    `--ds-type-mono-sm`, `--ds-lead-mono`
  - `.md-typeset table th`: reference `--ds-surface-alt`, `--ds-on-surface`,
    `--ds-weight-semibold`, `--ds-border`
  - `.md-nav__title`: reference `--ds-weight-bold`
  - `.md-banner`: reference `--ds-hero-bg`, `--ds-type-sm`
  - `.platform-back-link`: reference `--ds-font-mono`, `--ds-type-mono-sm`,
    `--ds-accent`, `--ds-track-label`
  - `.hero-section`: replace color literals with `--ds-*`; replace spacing
    literals with `--ds-space-*`; add `.site-footer` CSS block

---

### T3: Footer override

**Depends on:** T2 (footer CSS must exist in extra.css)

**Done when:**
- `make site-build` exits 0
- `grep 'site-footer__brand' build/docs/index.html` returns a match
- Footer renders dark zone background + brand name + three links + copyright

**Approach:**
- Create `site/overrides/partials/footer.html`
- Block 1: Material's prev/next navigation (copied from Material template)
- Block 2: `.site-footer` div with brand, links, copyright using Jinja2 variables

---

### T4: `.gitignore`

**Depends on:** T1

**Done when:** `git ls-files site/docs/stylesheets/tokens.css` returns empty
(file is not tracked)

**Approach:**
- Append `site/docs/stylesheets/tokens.css` to `.gitignore`

## Changelog

- 2026-07-23: initial plan; all tasks authored

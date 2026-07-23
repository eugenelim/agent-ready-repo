# Spec: site-shell

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [plan.md](plan.md)
- **Constrained by:** [design-system-foundations.md](../platform-site/design-system-foundations.md), [platform-site/spec.md](../platform-site/spec.md), [site-design-system-spec/spec.md](../site-design-system-spec/spec.md)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** frontend (CSS + MkDocs template overrides + build tooling)

Mode: full (risk triggers: structural build-pipeline change; multi-feature dependent tasks; user-visible docs surface change)

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Close the visual seam between the Astro marketing site and the MkDocs
documentation site by: (1) extracting the shared CSS token system into a
pipeline-generated shared file, (2) having both renderers consume it so values
cannot drift, (3) building MkDocs template overrides (footer, page chrome) that
match Astro's shell, and (4) aligning component-level styles (buttons, code
blocks, callouts, cards, dark mode, mobile nav) so the two surfaces feel like
one product.

This PR is the "follow-on CSS spec" explicitly deferred by
`site-design-system-spec` § Declined — it implements the four known Material
deviation fixes (`#f8fafc`, `#141516`, `#1a202c`, `#e2e8f0`) and replaces all
raw hex/rgba values in `extra.css` with `var(--ds-*)` / `var(--prim-*)` references.

## Boundaries

### Always do

- Keep `web/src/styles/tokens.css` as the canonical source of truth; propagate
  changes to MkDocs via a `build-site.py` copy step, not a separate file.
- Use `var(--ds-*)` and `var(--prim-*)` references in `extra.css` for every
  rule that touches color, spacing, radius, or motion — no standalone hex or
  rgba literals except computed alpha composites with no token equivalent,
  each annotated with a comment.
- Keep Material's prev/next page navigation in the footer override (users rely
  on it).
- Maintain `make site-build --strict` passing with zero warnings.

### Never do

- Create a new top-level `tokens/` directory (requires RFC per AGENTS.md).
- Migrate MkDocs to Astro/Starlight — not required for this PR.
- Add JavaScript to MkDocs pages.
- Change `web/src/styles/tokens.css` or any Astro component (out of scope).

### Ask first

- Any change to the MkDocs `nav:` structure.
- Any change to the GitHub Actions deploy workflow.

## Testing Strategy

Goal-based + visual/manual QA throughout.

- **T1 (build pipeline):** `make site-sync` completes; `site/docs/stylesheets/tokens.css`
  exists; `make site-build` exits 0.
- **T2 (token-driven extra.css):** `grep -E '#[0-9a-fA-F]{3,6}' site/docs/stylesheets/extra.css`
  returns zero matches (all hex values replaced by `var(--ds-*)` / `var(--prim-*)`).
  `grep -E 'rgba\(' site/docs/stylesheets/extra.css` returns only computed alpha
  composites with no token equivalent (each annotated with a comment).
- **T3 (footer):** `grep 'site-footer__brand' build/docs/index.html` returns a match;
  footer renders with dark zone background and brand name.
- **Gate:** `make site-build` exits 0 after all changes.

## Acceptance Criteria

- [x] AC1. `tools/build-site.py` copies `web/src/styles/tokens.css` →
  `site/docs/stylesheets/tokens.css` as part of `site-sync`; the file is
  listed in `.siteignore`.
- [x] AC2. `site/mkdocs.yml` lists `stylesheets/tokens.css` before
  `stylesheets/extra.css` in `extra_css`; MkDocs loads both.
- [x] AC3. `site/docs/stylesheets/tokens.css` is added to `.gitignore`
  (generated artifact, not source).
- [x] AC4. `site/docs/stylesheets/extra.css` contains zero standalone hex
  literals (`#rrggbb`) outside comment blocks; all color/spacing/radius/motion
  values in rule blocks reference `var(--ds-*)` or `var(--prim-*)`.
- [x] AC5. MkDocs Material `--md-accent-fg-color`, `--md-typeset-a-color`,
  `--md-default-bg-color`, and `--md-primary-fg-color` are bound to `--ds-*`
  tokens in the `:root` mapping block of `extra.css`.
- [x] AC6. `.md-header` and `.md-tabs` backgrounds reference `var(--ds-hero-bg)`,
  not hardcoded `#0b0e12`.
- [x] AC7. `.md-button--primary` has `border-radius: var(--ds-radius-pill)` and
  all color properties reference `var(--ds-cta-primary-bg)` / `var(--ds-cta-primary-fg)`.
- [x] AC8. `.grid.cards` card styles reference `var(--ds-surface-alt)`,
  `var(--ds-radius-md)`, `var(--ds-border-subtle)`, `var(--ds-accent)`, and
  `var(--ds-dur-quick)` — no hardcoded values.
- [x] AC9. `site/overrides/partials/footer.html` exists and renders: (a) Material's
  prev/next page navigation when enabled, and (b) a brand strip matching Astro's
  SiteFooter (brand name in mono, links: Platform / GitHub / PyPI, copyright line).
- [x] AC10. `make site-build` exits 0 with `--strict` flag (zero MkDocs warnings).
- [x] AC11. `build/docs/index.html` contains `class="site-footer__brand"`.
- [x] AC12. `build/docs/stylesheets/tokens.css` exists (tokens copied into build output).

## Assumptions

- Technical: `web/src/styles/tokens.css` exists and is the committed source of truth
  for `--prim-*` and `--ds-*` tokens (confirmed by reading).
- Technical: `make site-build` runs `python tools/build-site.py` then
  `mkdocs build --config-file site/mkdocs.yml --strict` (confirmed from Makefile).
- Technical: MkDocs `extra_css` loads files in order; tokens loaded before
  `extra.css` makes `var(--ds-*)` available to all rules in `extra.css`.
- Technical: No new Python dependency required — the copy step is `shutil.copy2`.
- Technical: MkDocs Material `partials/footer.html` override must include the
  prev/next navigation template itself (Material does not merge partial overrides).

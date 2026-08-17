# Docs tap-target audit

- **Status:** Planned
- **Owner:** eugenelim
- **Programme:** `tech-site-completion`
- **Producing task:** `site-browser-quality-gate/T0`
- **Decision authority:**
  `docs/product/briefs/tech-site-completion.md` decision 10

## Purpose

Classify the documentation site's interactive targets before target-size fixes
or CI exceptions are authored. This is an evidence record, not an instruction
to change the site. A demonstrated non-exempt failure may enter the browser
gate or a narrowly scoped remediation spec; a legitimate exception remains
visible and owned.

## Classification contract

Use WCAG 2.2 Success Criterion 2.5.8, Target Size (Minimum). A target passes
when its size or spacing meets that criterion. A smaller target is exempt only
when the accepted criterion class applies: inline content, an equivalent
control, user-agent/framework presentation not modified by the site,
or essential presentation. Record the exact geometry and context; do not infer
failure from a source selector alone.

Reference:
[W3C WCAG 2.2, SC 2.5.8](https://www.w3.org/TR/WCAG22/#target-size-minimum).

## Audit matrix

Audit these emitted routes at 360, 375, 390, 414, and 1440 CSS-pixel widths in
both light and dark themes:

- `/docs/`
- `/docs/guides/core/how-to/start-a-project/`

Resolve both paths through the configured deployment base. Inspect at least
the site orientation/header controls, search, theme control, sidebar or mobile
drawer, breadcrumbs where present, in-content links, pagination, table-scroll
regions, and footer links.

## Evidence record

No measurements have been performed in the shaping session because no browser
runtime is exposed. T0 replaces the placeholder rows below with observed
evidence; it does not claim a pass from source inspection.

| Route | Width | Theme | Target / context | Target box | Spacing evidence | Classification | Exception / failure owner |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| pending | — | — | pending execution | — | — | unclassified | eugenelim |

## Exception register

| ID | Exact selector or content context | WCAG exception class | Rationale | Owner | Revisit trigger |
| --- | --- | --- | --- | --- | --- |
| pending | pending execution | — | No exception accepted during shaping | eugenelim | T0 execution |

## Acceptance bar

The audit moves to **Accepted** only when:

- every matrix case has observed measurements;
- every candidate target is classified;
- each non-exempt failure has a stable identifier and owner;
- each exception is exact, criterion-grounded, and narrowly scoped;
- the record names any physical-device discrepancy; and
- no site source was changed as part of classification.

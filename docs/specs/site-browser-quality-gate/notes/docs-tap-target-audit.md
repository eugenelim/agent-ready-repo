# Docs tap-target audit

- **Status:** Planned — browser evidence unavailable
- **Owner:** eugenelim
- **Programme:** `tech-site-completion`
- **Producing task:** `site-browser-quality-gate/T0`
- **Decision authority:**
  `docs/product/briefs/tech-site-completion.md` decision 10

## Purpose

Classify the documentation site's interactive targets before target-size fixes
or CI exemptions are authored. This is an evidence record, not an instruction
to change the site. A demonstrated non-exempt failure returns to its owning
behavior spec or a narrowly scoped remediation spec; a legitimate exception
remains visible, exact, criterion-grounded, and owned.

## Evidence availability

No browser-control runtime was exposed during shaping. Installed browser code,
configuration, or CSS was not treated as geometry evidence. Therefore this
artifact records zero measured passes, zero demonstrated failures, and zero
accepted exceptions. T0 must replace this evidence state with measurements
from an actually exposed runtime before the audit can become Accepted.

## Classification contract

Use WCAG 2.2 Success Criterion 2.5.8, Target Size (Minimum). Record each
candidate as one of:

- conforming;
- demonstrated non-exempt failure;
- inline-content exception;
- user-agent/framework-controlled exception;
- equivalent-control exception; or
- essential exception.

Framework ownership identifies an implementation owner; it is not itself an
exception. Record exact geometry and spacing in emitted output. Never infer a
classification from a source selector or CSS declaration.

Reference:
[W3C WCAG 2.2, SC 2.5.8](https://www.w3.org/TR/WCAG22/#target-size-minimum).

## Audit matrix

Audit these emitted routes at 360, 375, 390, 414, and 1440 CSS-pixel widths in
both light and dark themes:

- `/docs/`
- `/docs/guides/core/how-to/start-a-project/`

Resolve both paths through the configured deployment base.

## Candidate inventory

For every matrix case, measure and classify each candidate that is present:

| Surface/context | Candidate target | Initial behavior owner |
| --- | --- | --- |
| Product-orientation band | Product destination links; mobile Product disclosure and disclosed links | `site-shared-chrome` |
| Starlight header | Site title, search, theme control, repository link | pinned Starlight/docs renderer |
| Starlight compact navigation | Docs menu trigger, drawer close, sidebar links | pinned Starlight/docs renderer |
| Docs wayfinding | Breadcrumb links, table-of-contents links | pinned Starlight/docs renderer |
| Main content | In-content links, heading anchors, inline code links | owning guide/docs content |
| Interactive content | Mermaid or tab controls where present | owning docs component/framework |
| Pagination | Previous and next guide links | pinned Starlight/docs renderer |
| Docs footer | Product, Docs, and Project destination links | `site-shared-chrome` |

The inventory is a minimum, not a selector allowlist. Any additional
interactive target visible in a matrix case receives its own measured row.

## Required evidence rows

One row represents one candidate in one route/width/theme context.

| Route | Width | Theme | Selector or content context | Target box (w×h) | Spacing | WCAG classification | Rationale | Owner | Exact remediation if required |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- |
| _pending browser execution_ | — | — | — | — | — | unclassified | No runtime was exposed during shaping. | eugenelim | Measure before deciding. |

## Final shaping classification and exemption table

| Classification | Accepted rows | Evidence state |
| --- | ---: | --- |
| Measured conforming | 0 | Unmeasured |
| Demonstrated non-exempt failure | 0 | Unmeasured |
| Inline-content exception | 0 | None accepted |
| User-agent/framework-controlled exception | 0 | None accepted |
| Equivalent-control exception | 0 | None accepted |
| Essential exception | 0 | None accepted |

## Exception register

No exception is accepted during shaping. T0 may add a row only after measuring
the exact target and recording all fields below. Broad selectors and
framework-ownership-only rationales are prohibited.

| ID | Route / width / theme | Exact selector or content context | Geometry / spacing | WCAG exception class | Rationale | Owner | Revisit trigger |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Defect register

No target-size defect is demonstrated during shaping. If T0 observes one, add
an exact row with route, width, theme, context, measurement, intended behavior,
owning spec, smallest remediation boundary, red construction test,
post-remediation browser proof, and whether the now-decided work is mechanical
or remains judgment-led.

## Acceptance bar

The audit moves to **Accepted** only when:

- every matrix case has observed measurements;
- every candidate target is classified;
- each non-exempt failure has a stable identifier, owner, intended behavior,
  and exact remediation boundary;
- each exception is exact, criterion-grounded, and narrowly scoped;
- serious/critical axe, overflow beyond 1px, missing focus, broken keyboard,
  and unstable framework-control observations are cross-recorded with the
  browser gate;
- the record names any physical-device discrepancy; and
- no site source was changed as part of classification.

# Representative print audit

- **Status:** Planned — browser evidence unavailable
- **Owner:** eugenelim
- **Programme:** `tech-site-completion`
- **Producing task:** `site-browser-quality-gate/T4`
- **Allowed final disposition:** `close-stale` or `shape`

## Decision rule

Prefer `close-stale`: accept browser/framework defaults when content remains
legible and navigation-only chrome does not corrupt the printed result. Choose
`shape` only for an observed failure, and then record the smallest route and
selector boundary required. Do not propose a general print stylesheet from
source inspection or visual preference.

No browser runtime was exposed during shaping, so no printed page was observed
and neither final disposition is claimed yet.

## Representative routes

| Page role | Emitted route |
| --- | --- |
| Marketing landing | `/` |
| Docs landing | `/docs/` |
| Ordinary guide | `/docs/guides/core/how-to/start-a-project/` |
| Code-heavy guide | `/docs/guides/catalogue-curation/tutorials/your-first-skill/` |
| Aside-heavy guide | `/docs/guides/atlassian/tutorials/review-your-team-backlog/` |
| Long-table page | `/docs/guides/converters/reference/converter-skills/` |

Resolve every path through the configured deployment base.

## Evidence contract

For each route, record:

- browser, version, paper size, orientation, scale, margins, and print settings;
- whether marketing, product-orientation, Starlight, sidebar, table of contents,
  pagination, and footer navigation are absent or non-disruptive;
- legibility and continuity of body text, headings, links, code, asides, and
  tables where present;
- clipping, overlap, content outside the printable area, orphaned headings,
  unusable page breaks, and unexpected blank pages;
- whether link URLs or decorative treatments preserve or harm reading; and
- the final disposition and owner.

## Audit record

| Route | Browser / paper settings | Navigation result | Content result | Code / aside / table result | Clipping / overlap / breaks | Observed failure and smallest rule boundary | Disposition | Owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| _pending browser execution_ | — | — | — | — | — | — | pending | eugenelim |

## Acceptance bar

- `close-stale` requires all six rows to show acceptable defaults with no
  demonstrated contract failure.
- `shape` requires at least one exact failing row, the smallest necessary print
  rule, construction proof that reproduces the failure, emitted print/browser
  evidence after remediation, and an independently shippable owning spec.
- Mixed evidence cannot be generalized: acceptable routes keep defaults, and
  rules target only the demonstrated failing boundary.

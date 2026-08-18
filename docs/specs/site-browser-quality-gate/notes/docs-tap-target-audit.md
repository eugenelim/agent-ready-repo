# Docs tap-target audit

- **Status:** Accepted — measured 2026-08-18
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

Measured 2026-08-18 with Google Chrome for Testing 151.0.7922.34, driven through
Playwright's Chromium build. Both approved routes at all five widths in both
themes — 20 cases — with the theme set through Starlight's own
`localStorage['starlight-theme']` key *before* navigation and read back from
`html[data-theme]`, and every measurement taken after `networkidle`.

414 undersized observations resolve to **44 distinct candidates**. Every one
satisfies an SC 2.5.8 exception; there are **zero demonstrated non-exempt
failures** and therefore no remediation in this audit.

### Two measurement traps, corrected — both produced plausible false failures

Recorded because the corrected method is the load-bearing part of this evidence,
and because a later reader re-measuring naively will get the wrong answer.

1. **Ancestor adjacency.** Measuring each target against every other reported
   `centre-to-nearest = 0` for any nested link — against its own container. Every
   nested link looked like a spacing failure. Excluded via
   `e.contains(o) || o.contains(e)`.

2. **Unpainted overlay targets.** Three breadcrumb links reported a gap of 0
   against a 412×35 `<a>` containing "Prerequisites" — the mobile
   table-of-contents list, whose links still report a box while the panel is not
   painted. That invented a failure against something a finger cannot reach.
   Settled by hit testing rather than geometry: `document.elementFromPoint` at
   each breadcrumb's own centre returns the breadcrumb itself at 360, 414 and
   1440. The target set for SC 2.5.8 is therefore "elements that receive a tap at
   their own centre", and with that set the breadcrumb gaps are 33.2 / 38.5 /
   49–61.5px. The overlay is absent at 1440, which is why the artifact appeared
   only at 360–414.

This is what the spec's "never infer a classification from a source selector or
CSS declaration" means in practice: both artifacts were *measured*, and both were
wrong, because they measured the wrong frame.

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

One row per distinct candidate. `Width` lists every approved width the candidate
was observed at; geometry is given as a range when it varies across them.
`Spacing` is the distance from the candidate's centre to the nearest **other
painted** target.

| Route | Widths | Themes | Selector or content context | Target box (w×h) | Spacing | WCAG classification | Rationale | Owner | Exact remediation if required |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'How to orient at the start of a sessio' in main, `display:inline` | 283.2×20 | 22–987.1 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Your first workspace session' in main, `display:inline` | 218.6×20 | 22–50 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'decide' in main, `display:inline` | 51.3×20 | 34.7–106 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'research' in main, `display:inline` | 66.4×20 | 42.3–75 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'shape' in main, `display:inline` | 46×20 | 50–64.9 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'design the system' in main, `display:inline` | 138×20 | 0–18 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'start with core' in main, `display:inline` | 118.4×20 | 22 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'system' in main, `display:inline` | 54.3×20 | 0 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Get started' in main, `display:inline` | 84.2×20 | 22–50 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Compare install routes' in main, `display:inline` | 169.8×20 | 0–22 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Browse every pack' in main, `display:inline` | 144.5×20 | 0–22 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Preview an install or upgrade' in main, `display:inline` | 219.1×20 | 18–22 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'upgrade safely' in main, `display:inline` | 112.2×20 | 18–22 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Create the first valid catalogue' in main, `display:inline` | 231.9×20 | 22 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'The three supervised loops' in main, `display:inline` | 206.8×20 | 22–78 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'The file-safety contract' in main, `display:inline` | 178×20 | 22–50 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'agentbundle CLI reference' in main, `display:inline` | 207.5×20 | 22–50 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Complete pack reference' in main, `display:inline` | 191.4×20 | 22–50 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'The two-room model' in main, `display:inline` | 158.9×20 | 22–50 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'workspace.toml schema reference' in main, `display:inline` | 261.7×20 | 22–50 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 375, 390, 414, 1440 | dark+light | `<a>` 'author contracts' in main, `display:inline` | 124.4×20 | 0–18 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 375, 390, 414, 1440 | dark+light | `<a>` 'stop at the production gate' in main, `display:inline` | 204.1×20 | 0–18 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 375, 390, 414, 1440 | dark+light | `<a>` 'Author against the portable standards' in main, `display:inline` | 285.6×20 | 22 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `start-a-project` | 390, 414, 1440 | dark+light | `<a>` 'How to plan and execute non-trivial wo' in main, `display:inline` | 310.3×20 | 22–154.1 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390 | dark+light | `<a>` 'start with evidence' in main, `display:inline` | 143.8×20 | 18 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 390, 414 | dark+light | `<a>` 'produce a reviewable infrastructure pl' in main, `display:inline` | 306.1×20 | 18 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 414, 1440 | dark+light | `<a>` 'design the experience' in main, `display:inline` | 167.9×20 | 0–18 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 414, 1440 | dark+light | `<a>` 'adapter support' in main, `display:inline` | 121.1×20 | 22 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 1440 | dark+light | `<a>` 'initialize an organization-owned catal' in main, `display:inline` | 319.4×20 | 22 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 1440 | dark+light | `<a>` 'install a curated profile' in main, `display:inline` | 172.3×20 | 22 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 1440 | dark+light | `<a>` 'Add this catalogue as a plugin marketp' in main, `display:inline` | 325.4×20 | 54 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 1440 | dark+light | `<a>` 'Understand packs, profiles, adapters, ' in main, `display:inline` | 513.5×20 | 22 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/` | 1440 | dark+light | `<a>` 'Implement the provider-neutral verify ' in main, `display:inline` | 515.1×20 | 22 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | owning guide/docs content | none — conforms by exception |
| `/docs/ + start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Platform' in nav[Site footer], `display:inline` | 51.4×16 | 49.7 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | `site-shared-chrome` (footer destinations) | none — conforms by exception |
| `/docs/ + start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'GitHub' in nav[Site footer], `display:inline` | 42.4×16 | 45.2 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | `site-shared-chrome` (footer destinations) | none — conforms by exception |
| `/docs/ + start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'PyPI' in nav[Site footer], `display:inline` | 27.5×16 | 37.7 | inline-content exception | in a sentence; height equals the line-height of the non-target text around it | `site-shared-chrome` (footer destinations) | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Decide what to build' in main, `display:block` | 264.7–318.7×21.6 | 120.8–140.8 | spacing exception | a 24px circle on its centre clears every other target by 120.8–140.8px | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Provision and release safely' in main, `display:block` | 264.7–318.7×21.6 | 140.8–148.8 | spacing exception | a 24px circle on its centre clears every other target by 140.8–148.8px | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Document what ships' in main, `display:block` | 264.7–318.7×21.6 | 140.8–194.4 | spacing exception | a 24px circle on its centre clears every other target by 140.8–194.4px | owning guide/docs content | none — conforms by exception |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Build and govern a catalogue' in main, `display:block` | 264.7–318.7×21.6 | 140.8–172.8 | spacing exception | a 24px circle on its centre clears every other target by 140.8–172.8px | owning guide/docs content | none — conforms by exception |
| `/docs/` | 375, 390, 414, 1440 | dark+light | `<a>` 'Design the product and system' in main, `display:block` | 279.7–318.7×21.6 | 120.8–140.8 | spacing exception | a 24px circle on its centre clears every other target by 120.8–140.8px | owning guide/docs content | none — conforms by exception |
| `start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Docs' in nav[Breadcrumb], `display:block` | 29×18 | 33.2 | spacing exception | a 24px circle on its centre clears every other target by 33.2px | pinned Starlight (breadcrumbs) | none — conforms by exception |
| `start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Guides' in nav[Breadcrumb], `display:block` | 39.6×18 | 38.5 | spacing exception | a 24px circle on its centre clears every other target by 38.5px | pinned Starlight (breadcrumbs) | none — conforms by exception |
| `start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'The Build Loop (core)' in nav[Breadcrumb], `display:block` | 122.5×18 | 49–61.5 | spacing exception | a 24px circle on its centre clears every other target by 49–61.5px | pinned Starlight (breadcrumbs) | none — conforms by exception |

## Final shaping classification and exemption table

| Classification | Accepted rows | Evidence state |
| --- | ---: | --- |
| Measured conforming (≥24×24) | — | Not enumerated: only undersized candidates are rows here |
| Inline-content exception | 36 | Measured 2026-08-18 |
| Spacing exception (24px circle clear) | 8 | Measured 2026-08-18 |
| Demonstrated non-exempt failure | 0 | Measured 2026-08-18 |
| User-agent/framework-controlled exception | 0 | None needed |
| Equivalent-control exception | 0 | None needed |
| Essential exception | 0 | None needed |

No row is classified as a framework-controlled exception, and that is deliberate:
the brief's decision 10 and this spec's Never-do bar framework ownership from
being an exception by itself. The three breadcrumb rows are Starlight-owned, and
they are accepted on their **measured spacing**, with ownership recorded only to
say who would fix them if they ever failed.

## Cross-recorded axe observations

The acceptance bar requires serious/critical axe, overflow, focus, keyboard and
unstable-framework-control observations to be cross-recorded with the browser
gate. Measured across the full approved 60-case matrix on 2026-08-18:

| Observation | Count | Disposition |
| --- | ---: | --- |
| serious or critical axe findings | **0** | threshold met (AC5) |
| document horizontal overflow beyond 1px | **0** | threshold met (AC4); measured 0px on all 60 cases |
| missing focus indication | 0 | none observed |
| broken keyboard path | 0 | none observed |
| unresolved same-document fragment | 0 | none observed |
| page or console errors | 0 | none observed |

### One accepted lower-severity result

`landmark-unique` — **moderate** — 8 occurrences: `/docs/guides/core/how-to/start-a-project/`
at 360, 375, 390 and 414 in both themes. Two `role="region"` landmarks on one page
without distinguishing accessible names.

- **Exact cause, traced to source rather than inferred.**
  `@expressive-code/core` ships an inline runtime module (`tabindex-js-module`)
  that, for each `.expressive-code pre > code` parent, sets `tabindex="0"` and
  `role="region"` when the element scrolls and removes both when it does not. It
  sets no accessible name. It runs through a ResizeObserver with a 250ms debounce
  inside `requestIdleCallback` — which is also why measurement requires a settle,
  and why axe run at `load` reports these same elements as a *serious*
  `scrollable-region-focusable` failure that does not exist.
- **Owner:** `@expressive-code/core`, via the pinned docs renderer.
- **Why accepted:** severity is moderate, and the approved ceiling is zero
  serious/critical. Accepted on severity plus this exact recorded cause — **not**
  on framework ownership, which the brief's decision 10 and this spec's Never-do
  bar from being an exception by itself. Ownership here records who would fix it.
- **Available remediation, if a future reader wants it closed:** a docs-local
  build-time pass adding `aria-label` to `<pre>` inside `.expressive-code`. A name
  persists because Expressive Code only toggles `role`/`tabindex`, and an
  `aria-label` on a non-scrolling `<pre>` carries no role, so assistive tech
  ignores it.
- **Not a gap in earlier work.** The shipped `rehype-scrollable-tables` plugin
  wraps TABLES only and already names each region after its nearest preceding
  heading, precisely to avoid this rule. Code blocks were never in its scope.

## Exception register

No TARGET-SIZE exception is accepted: all 44 undersized candidates satisfy either
the inline-content or the spacing exception on measured geometry, which are
criterion conformance rather than exceptions granted. The one accepted
lower-severity result is the `landmark-unique` axe observation recorded above.
Broad selectors and framework-ownership-only rationales remain prohibited.

| ID | Route / width / theme | Exact selector or content context | Geometry / spacing | WCAG exception class | Rationale | Owner | Revisit trigger |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Defect register

**No target-size defect is demonstrated.** 414 undersized observations across 20
matrix cases resolve to 44 distinct candidates, every one conforming through an
SC 2.5.8 exception on measured geometry. Nothing returns to an owning spec and no
remediation spec is warranted from this audit.

Two candidate groups belong to surfaces another spec will change, and are recorded
so a later reader does not read this audit as covering them after that change:
the three docs-footer destination links (`Platform`, `GitHub`, `PyPI`) are replaced
by `site-shared-chrome`'s approved three-group footer, and the product-orientation
band that spec introduces does not exist yet. Both need re-measuring when that
slice lands.

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

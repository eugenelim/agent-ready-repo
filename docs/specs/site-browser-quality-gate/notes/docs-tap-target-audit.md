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

Undersized observations across those 20 cases resolve to **56 distinct
candidates**. Every one conforms through an SC 2.5.8 exception; there are **zero
demonstrated non-exempt failures** and therefore no remediation in this audit.
This is the count's home; § Final shaping classification decomposes it per class
(29 + 15 + 12) and repeats the total only as a sum of the cells directly above it,
so the two cannot drift apart unnoticed.

### The target set, defined once

Four rules decide whether an element is a tap target here. Each was added because
its absence produced a wrong answer, and all four are needed together:

1. non-zero box;
2. not `display:none` / `visibility:hidden`;
3. resting `opacity > 0` — otherwise it is **hover-revealed** and classified as its
   own group rather than dropped; and
4. it receives a tap at its own centre (`document.elementFromPoint`) **after being
   scrolled into view**.

Adjacency for the spacing clause is measured against the set satisfying all four,
for both groups: what a finger can collide with is the same set whether or not the
target itself is hover-revealed.

### Three measurement traps, corrected — each produced plausible false results

Recorded because the corrected method is the load-bearing part of this evidence,
and the naive method is what a later reader reaches for first.

1. **Ancestor adjacency.** Measuring each target against every other reported
   centre-to-nearest 0 for any nested link — against its own container. Every
   nested link looked like a spacing failure. Excluded via
   `e.contains(o) || o.contains(e)`.

2. **Unpainted overlay targets.** Three breadcrumb links reported a gap of 0
   against a 412×35 `<a>` in the mobile table-of-contents list, whose links report
   a box while the panel is not painted — a failure against something a finger
   cannot reach. Rule 4 closes it: with the hit-tested set the breadcrumb gaps are
   33.2 / 38.5 / 49–61.5px. The overlay is absent at 1440, which is why the
   artifact appeared only at 360–414.

3. **Hover-revealed targets silently dropped.** An earlier pass filtered
   `opacity === 0` out of the candidate set entirely, which removed **12**
   Starlight heading-anchor links — 23.98 × 34.8, i.e. under the 24px minimum, and
   named in this audit's own candidate inventory under "heading anchors". They
   receive a tap once scrolled into view, so they are real targets and AC7 requires
   them classified. An exclusion rule that is not written down is not a rule;
   rule 3 above now states it and the group is classified below.

Trap 2 excludes *painted-but-unreachable*; trap 3 admits *unpainted-but-reachable*.
The two cut in opposite directions, which is why the target set is stated as one
definition rather than as a filter chain.

A fourth error was a classification bug rather than a measurement one: treating any
`<li>` as running text applied the Inline clause to the three docs-footer
destination links, whose list items carry no text beyond the link. "In running
text" now requires the host element to carry text beyond the link itself, and those
three are classified on their measured clearance instead.

## Classification contract

Use WCAG 2.2 Success Criterion 2.5.8, Target Size (Minimum). Record each
candidate as one of:

- conforming;
- demonstrated non-exempt failure;
- **spacing exception**;
- inline-content exception;
- user-agent/framework-controlled exception;
- equivalent-control exception; or
- essential exception.

The list is complete against the criterion: SC 2.5.8 defines exactly five
exceptions — Spacing, Equivalent, Inline, User agent control, Essential. An earlier
revision of this contract, and of the spec's AC7, omitted Spacing, which left 27 of
the measured candidates (§ Evidence availability) classified against a class
neither document admitted.

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

Grouped by exception class, with the rationale stated once per group: one row per
candidate repeating one sentence is a wall a re-verifier will skip. Per-candidate columns
carry what actually varies — context, widths, geometry and measured clearance.
`Widths` lists every approved width the candidate was observed at; geometry and
clearance are ranges when they vary.

### Spacing exception, hover-revealed — 12 candidates

Starlight heading-anchor links, `opacity: 0` until hover or focus. Recorded
rather than excluded: they receive a tap once scrolled into view, so they are
real targets. 23.98px wide is 0.02px under the 24px minimum — a sub-pixel
shortfall from Starlight's own sizing — and every one clears its nearest
neighbour by ≥ 50px, so SC 2.5.8's Spacing clause applies comfortably.

| Route | Widths | Themes | Context | Target box (w×h) | Centre-to-nearest | Owner |
| --- | --- | --- | --- | --- | ---: | --- |
| `/docs/` | 360, 375, 390, 414 | dark+light | `<a class=sl-anchor-link>` 'Section titled “Choose what you ' | 23.98×34.8 | 92.2 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414 | dark+light | `<a class=sl-anchor-link>` 'Section titled “Choose by role”' | 23.98×34.8 | 78.3–78.4 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414 | dark+light | `<a class=sl-anchor-link>` 'Section titled “Use a catalogue”' | 23.98×34.8 | 64.9–92.9 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414 | dark+light | `<a class=sl-anchor-link>` 'Section titled “Build and operat' | 23.98×34.8 | 151.8 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414 | dark+light | `<a class=sl-anchor-link>` 'Section titled “Understand and r' | 23.98×34.8 | 50–64.9 | owning guide/docs content |
| `start-a-project` | 360, 375, 390, 414 | dark+light | `<a class=sl-anchor-link>` 'Section titled “Prerequisites”' | 23.98×34.8 | 64.9 | owning guide/docs content |
| `start-a-project` | 360, 375, 390, 414 | dark+light | `<a class=sl-anchor-link>` 'Section titled “Step 1 — Confirm' | 23.98×34.8 | 167.7 | owning guide/docs content |
| `start-a-project` | 360, 375, 390, 414 | dark+light | `<a class=sl-anchor-link>` 'Section titled “Step 2 — Run wor' | 23.98×34.8 | 412.5 | owning guide/docs content |
| `start-a-project` | 360, 375, 390, 414 | dark+light | `<a class=sl-anchor-link>` 'Section titled “Step 3 — Identif' | 23.98×34.8 | 99.7–134.5 | owning guide/docs content |
| `start-a-project` | 360, 375, 390, 414 | dark+light | `<a class=sl-anchor-link>` 'Section titled “Step 4 — Pick a ' | 23.98×34.8 | 475.4–566.2 | owning guide/docs content |
| `start-a-project` | 360, 375, 390, 414 | dark+light | `<a class=sl-anchor-link>` 'Section titled “Step 5 — Start w' | 23.98×34.8 | 90–118 | owning guide/docs content |
| `start-a-project` | 360, 375, 390, 414 | dark+light | `<a class=sl-anchor-link>` 'Section titled “Related”' | 23.98×34.8 | 50 | owning guide/docs content |

### Inline-content exception — 29 candidates

Rationale, stated once for the group: each is `display:inline` inside a
paragraph or list item that carries text beyond the link, so its height is the
line-height of the surrounding non-target text. SC 2.5.8, Inline.

| Route | Widths | Themes | Context | Target box (w×h) | Centre-to-nearest | Owner |
| --- | --- | --- | --- | --- | ---: | --- |
| `start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'How to orient at the start of a ' | 283.2×20 | 22–1009.5 | owning guide/docs content |
| `start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Your first workspace session' | 218.61×20 | 22–50 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'decide' | 51.27×20 | 34.7–106 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'research' | 66.36×20 | 42.3–75 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'shape' | 46.02×20 | 50–64.9 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'design the system' | 138.05×20 | 0–18 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'start with core' | 118.44×20 | 22 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'system' | 54.31×20 | 0 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Get started' | 84.22×20 | 22–50 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Compare install routes' | 169.81×20 | 0–22 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Browse every pack' | 144.55×20 | 0–22 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Preview an install or upgrade' | 219.08×20 | 18–22 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'upgrade safely' | 112.16×20 | 18–22 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'The three supervised loops' | 206.78×20 | 22–78 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'The file-safety contract' | 178.03×20 | 22–50 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'agentbundle CLI reference' | 207.55×20 | 22–50 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Complete pack reference' | 191.44×20 | 22–50 | owning guide/docs content |
| `start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'The two-room model' | 158.92×20 | 22–50 | owning guide/docs content |
| `start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'workspace.toml schema reference' | 261.73×20 | 22–50 | owning guide/docs content |
| `/docs/` | 375, 390, 414, 1440 | dark+light | `<a>` 'author contracts' | 124.36×20 | 0–18 | owning guide/docs content |
| `/docs/` | 375, 390, 414, 1440 | dark+light | `<a>` 'stop at the production gate' | 204.06×20 | 0–18 | owning guide/docs content |
| `start-a-project` | 390, 414, 1440 | dark+light | `<a>` 'How to plan and execute non-triv' | 310.31×20 | 22–154.1 | owning guide/docs content |
| `/docs/` | 360, 375, 390 | dark+light | `<a>` 'start with evidence' | 143.84×20 | 18 | owning guide/docs content |
| `/docs/` | 390, 414 | dark+light | `<a>` 'produce a reviewable infrastruct' | 306.08×20 | 18 | owning guide/docs content |
| `/docs/` | 414, 1440 | dark+light | `<a>` 'design the experience' | 167.88×20 | 0–18 | owning guide/docs content |
| `/docs/` | 414, 1440 | dark+light | `<a>` 'adapter support' | 121.09×20 | 22 | owning guide/docs content |
| `/docs/` | 1440 | dark+light | `<a>` 'initialize an organization-owned' | 319.36×20 | 22 | owning guide/docs content |
| `/docs/` | 1440 | dark+light | `<a>` 'install a curated profile' | 172.27×20 | 22 | owning guide/docs content |
| `/docs/` | 1440 | dark+light | `<a>` 'Add this catalogue as a plugin m' | 325.38×20 | 54 | owning guide/docs content |

### Spacing exception — 15 candidates

Rationale, stated once for the group: not in running text, so the Inline clause does
not apply — accepted on measured clearance instead.

SC 2.5.8's Spacing clause has **two forms, with different thresholds**, and an
earlier revision of this paragraph stated only the first and applied its number to
both:

- **circle vs. a full-size neighbour's box** — the 24px-diameter circle centred on
  the undersized target must not intersect that box, i.e. **centre-to-box ≥ 12px**;
- **circle vs. another undersized target's circle** — the two circles must not
  intersect, which needs **centre-to-centre ≥ 24px**, not 12.

The `Centre-to-nearest` column holds the **centre-to-box** distance to the nearest
other tappable target. The conclusion survives the correction with room to spare:
the smallest value recorded anywhere in this audit is 22px centre-to-box, which
implies ≥30px centre-to-centre, and the hover-revealed group's minimum is 50px. So
every row clears the binding form whichever applies — but the rule as previously
written would have accepted two undersized targets 13px apart, which fails the
criterion.

| Route | Widths | Themes | Context | Target box (w×h) | Centre-to-nearest | Owner |
| --- | --- | --- | --- | --- | ---: | --- |
| `both` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Platform' | 51.41×16 | 49.7 | `site-shared-chrome` |
| `both` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'GitHub' | 42.42×16 | 45.2 | `site-shared-chrome` |
| `both` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'PyPI' | 27.47×16 | 37.7 | `site-shared-chrome` |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a class=astro-vodiqeol>` 'Decide what to build' | 264.69–318.69×21.59 | 120.8–140.8 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a class=astro-vodiqeol>` 'Provision and release safely' | 264.69–318.69×21.59 | 140.8–148.8 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a class=astro-vodiqeol>` 'Document what ships' | 264.69–318.69×21.59 | 140.8–194.4 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a class=astro-vodiqeol>` 'Build and govern a catalogue' | 264.69–318.69×21.59 | 140.8–172.8 | owning guide/docs content |
| `/docs/` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Create the first valid catalogue' | 231.94×20 | 22 | owning guide/docs content |
| `start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Docs' | 29.05×18 | 33.2 | pinned Starlight |
| `start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'Guides' | 39.64×18 | 38.5 | pinned Starlight |
| `start-a-project` | 360, 375, 390, 414, 1440 | dark+light | `<a>` 'The Build Loop (core)' | 122.45×18 | 49–61.5 | pinned Starlight |
| `/docs/` | 375, 390, 414, 1440 | dark+light | `<a class=astro-vodiqeol>` 'Design the product and system' | 279.69–318.69×21.59 | 120.8–140.8 | owning guide/docs content |
| `/docs/` | 375, 390, 414, 1440 | dark+light | `<a>` 'Author against the portable stan' | 285.56×20 | 22 | owning guide/docs content |
| `/docs/` | 1440 | dark+light | `<a>` 'Understand packs, profiles, adap' | 513.48×20 | 22 | owning guide/docs content |
| `/docs/` | 1440 | dark+light | `<a>` 'Implement the provider-neutral v' | 515.14×20 | 22 | owning guide/docs content |

## Final shaping classification and exemption table

| Classification | Accepted rows | Evidence state |
| --- | ---: | --- |
| Inline-content exception (SC 2.5.8, Inline) | 29 | Measured 2026-08-18 |
| Spacing exception (SC 2.5.8, Spacing) | 15 | Measured 2026-08-18 |
| Spacing exception, hover-revealed | 12 | Measured 2026-08-18 |
| Demonstrated non-exempt failure | 0 | Measured 2026-08-18 |
| User-agent/framework-controlled exception | 0 | None needed |
| Equivalent-control exception | 0 | None needed |
| Essential exception | 0 | None needed |
| **Total classified** | 56 | |

Measured targets at or above 24×24 are not enumerated: only undersized candidates
need a classification, and listing the conforming majority would bury the rows that
carry the argument.

The total sits directly beneath its own addends (29 + 15 + 12), which is the reason
it is restated here at all: a sum a reader can check against the four cells above it
cannot quietly disagree with them. Free-floating restatements elsewhere in this file
can, and did — an earlier revision left a superseded total standing beside its
replacement — so every other mention now refers to § Evidence availability instead
of repeating the number.

No row is classified as a framework-controlled exception, and that is deliberate:
the brief's decision 10 and this spec's Never-do bar framework ownership from being
an exception by itself. The Starlight-owned rows — breadcrumbs and heading
anchors — are accepted on **measured clearance**, with ownership recorded only to
say who would fix them if they ever failed.

## Cross-recorded browser observations

The acceptance bar requires serious/critical axe, overflow, focus, keyboard and
unstable-framework-control observations to be cross-recorded with the browser gate.
Measured across the full approved 60-case matrix on 2026-08-18:

| Observation | Count | Disposition |
| --- | ---: | --- |
| serious or critical axe findings | **0** | threshold met (AC5) |
| document horizontal overflow beyond 1px | **0** | threshold met (AC4); 0px on all 60 |
| missing focus indication | 0 | none observed |
| broken keyboard path | 0 | none observed |
| unresolved same-document fragment | 0 | none observed |
| page or console errors | 0 | none observed |

### One accepted lower-severity result

`landmark-unique` — **moderate** — 8 occurrences:
`/docs/guides/core/how-to/start-a-project/` at 360, 375, 390 and 414 in both themes.
Two `role="region"` landmarks on one page without distinguishing accessible names.

- **Exact cause, traced to source rather than inferred.**
  `@expressive-code/core` ships an inline runtime module (`tabindex-js-module`)
  that, for each `.expressive-code pre > code` parent, sets `tabindex="0"` and
  `role="region"` when the element scrolls and removes both when it does not. It
  sets no accessible name. It runs through a `ResizeObserver` with a 250ms debounce
  inside `requestIdleCallback` — which is also why the gate must settle before
  measuring, and why axe run at `load` reports these same elements as a *serious*
  `scrollable-region-focusable` failure that does not exist.
- **Owner:** `@expressive-code/core`, via the pinned docs renderer.
- **Why accepted:** severity is moderate and the approved ceiling is zero
  serious/critical. Accepted on severity plus this exact recorded cause — **not** on
  framework ownership, which the brief's decision 10 and this spec's Never-do bar
  from being an exception by itself. Ownership records who would fix it.
- **Runtime signal:** the gate now attaches every non-serious axe finding to the
  test result, so this list is checkable against a run rather than being a snapshot
  that rots when the docs renderer moves.
- **Available remediation if a future reader wants it closed:** a docs-local
  build-time pass adding `aria-label` to `<pre>` inside `.expressive-code`. A name
  persists because Expressive Code only toggles `role`/`tabindex`, and an
  `aria-label` on a non-scrolling `<pre>` carries no role, so assistive tech ignores
  it.
- **Not a gap in earlier work.** The shipped `rehype-scrollable-tables` plugin wraps
  TABLES only and already names each region after its nearest preceding heading,
  precisely to avoid this rule. Code blocks were never in its scope.

### One framework observation, recorded not fixed

Starlight's compact Docs menu button opens on `Enter` but leaves
`aria-expanded="false"`. Measured at 360: after `Enter` the theme control becomes
visible — so the menu genuinely opened — while the attribute does not change.

axe reports nothing for it, so it is not a serious or critical finding and does not
affect AC5's ceiling. It is recorded because the browser gate asserts the
*observable* state (the control becoming reachable) rather than the attribute, and a
later reader who assumes `aria-expanded` is trustworthy here will write a test that
fails on a menu that works. Owner: pinned Starlight. Not fixed: this spec's Never-do
bars replacing a Starlight-native control, and the brief bars treating
framework-owned behaviour as a defect without a demonstrated user outcome.

## Exception register

No TARGET-SIZE exception is accepted. Every undersized candidate (count in
§ Evidence availability — stated once there, deliberately not restated here) satisfies
SC 2.5.8's own Inline or Spacing clause on measured geometry, which is criterion
conformance rather than an exception granted against it. The one accepted
lower-severity result is the `landmark-unique` axe observation recorded above, which
is not a target-size exception. Broad selectors and framework-ownership-only
rationales remain prohibited.

**Empty, deliberately.** Nothing is exempted here, so there is no row — the table
shape is omitted rather than left as a bare header that reads as unfilled.

## Defect register

**No target-size defect is demonstrated.** Every distinct candidate conforms through
SC 2.5.8's Inline or Spacing clause on measured geometry — see § Evidence
availability for the count and § Final shaping classification for the split. Nothing
returns to an owning spec and no remediation spec is warranted from this audit.

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
- the record names any physical-device discrepancy — **none is known, and that is
  not the same as none existing**: the device pass is Blocked, recorded with its
  owner in `docs/product/release-checklist.md` § site-browser-quality-gate, so
  discrepancies are unmeasured rather than absent; and
- no site source was changed as part of classification.

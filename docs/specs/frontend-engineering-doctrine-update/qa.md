# Frontend Engineering Doctrine QA

- **Date:** 2026-08-09
- **Task:** T7 — rendered adopter journeys clear the experience and repository gates
- **Status:** **clean pass** — the sole severity-3 defect (`F1`, journey 375 px
  horizontal overflow) was remediated by Codex and re-verified resolved in this
  session; no severity-3-or-higher finding remains (see
  [Experience review](#experience-review-fresh-context)). A subsequent
  **claim-narrowing copy edit** ("prove it is ready to ship" →
  "produce the frontend evidence for release review") was rebuilt and
  re-inspected — old wording gone from generated + built outputs, new wording
  present and visible at 375/768/1280 px with no page-level overflow, and
  `make site-build`, the scoped build check, and the subsequent full
  SAST/SCA-enabled `make build-check` all exit 0 (see
  [Post-copy-change re-verification](#post-copy-change-re-verification-2026-08-09)).

## Post-copy-change re-verification (2026-08-09)

After the experience gate cleared, Codex applied a **claim-narrowing copy
edit** to the frontend-engineering "shortest path" line: the marketing claim
**"prove it is ready to ship"** was replaced with the evidence-scoped
**"produce the frontend evidence for release review."** This session rebuilt
the static site from the working tree and re-inspected the rendered surfaces to
confirm the narrowed wording propagated through the generator, the built HTML,
and the served DOM — and that the old phrase survives nowhere.

Edit locus (Codex's source edits; not touched by this session):

- `guides/frontend-engineering/README.md` (canonical source; new phrase present)
- `web/src/content/packs/frontend-engineering.md` (pack page source; new phrase present)
- `docs-site/src/content/docs/guides/frontend-engineering/index.md` is a
  **generated projection** of the `guides/` source (git-ignored). Before
  `make site-build` it still carried the old phrase; the generator overwrote it
  from source during this rebuild.

### Build and gate exit results (this session)

| # | Command | Exit | Result |
|---|---|---:|---|
| 1 | `nvm use 26.4.0` | — | `Now using node v26.4.0 (npm v11.17.0)`. |
| 2 | `make site-build` | 0 | generator (12 pack journeys synced, 183 navigable guide pages) → `npm run build --prefix web` (**46** pages into `build/`) → `npm run build --prefix docs-site` (**217** pages into `build/docs/`, pagefind index over 217 HTML files). |
| 3 | `npm run preview --prefix web -- --host 127.0.0.1` | 0 | Served `build/` at `http://127.0.0.1:4321/agent-ready-repo`; both target routes returned HTTP `200`. Stopped cleanly after inspection. |
| 4 | `SKIP_SAST=1 make build-check` | 0 | All drift/lint/policy gates passed. **SAST/SCA leg intentionally skipped** via the task-authorized `SKIP_SAST=1`; the banner prints `INCOMPLETE — the SAST/SCA leg was SKIPPED`. A subsequent full build check closed that evidence gap; see below. The `lint-pack-descriptions` "801 chars … run away" line is again the lint's **own self-test fixture** (literal `[pack]` placeholder); the real repo scan printed `no pack description has run away`. |

### Final guide validation evidence (Codex, 2026-08-09)

After the claim-narrowing sources and generated outputs were current, Codex ran
the two guide-specific AC11 gates directly against the final working tree:

| Command | Exit | Result |
|---|---:|---|
| `python3 tools/validate_guides.py` | 0 | `validate-guides: OK (0 errors, 163 warnings)`. The warnings are the repository's existing frontmatter-migration advisories; neither new guide reports an error. |
| `python3 tools/check-guide-index.py` | 0 | `check-guide-index: OK — all 20 active packs present in guide index`. |

### Full SAST/SCA build-check evidence (user terminal, 2026-08-09)

After the final eval and backlog-comment review fixes, the user ran the complete
repository gate without `SKIP_SAST` and supplied its terminal transcript:

| Command | Exit | Result |
|---|---:|---|
| `make build-check` | 0 | The full gate reached and passed its final SAST/SCA leg: Bandit reported no failing finding; the audit-requirements self-test passed; `pip-audit` reported no unhandled known vulnerability (the documented Semgrep-tooling allowlist ignored three accepted transitive findings); Semgrep reported no blocking finding; and the custom Semgrep-rule self-test passed 5/5. |

### Phrase propagation — string evidence

- **Old phrase `"prove it is ready to ship"` — 0 hits** across generated content
  and built output. Swept `docs-site/src/content`, `build/`, `web/src/content`,
  `guides/`, and `packs/` (excluding `node_modules`); `OLD_PHRASE_HITS=0`. The
  stale projection that previously held it (`docs-site/.../index.md`) was
  overwritten from source by the generator.
- **New phrase `"produce the frontend evidence for release review"` — present**
  in each of the three required outputs:

  | File | New phrase |
  |---|---|
  | `docs-site/src/content/docs/guides/frontend-engineering/index.md` (generated) | present |
  | `build/packs/frontend-engineering/index.html` (built) | present |
  | `build/docs/guides/frontend-engineering/index.html` (built) | present |

### Rendered-DOM re-inspection at 375 / 768 / 1280 px

Headless Chromium (Playwright `1.62.0`, cached Chromium) loaded each route at
each width against the local `astro preview` build, measured
`document.documentElement.scrollWidth` vs `clientWidth` and `window` max scroll,
and read `document.body.innerText` to confirm the narrowed wording is visible in
the rendered DOM (not just the source).

| Route | Width | HTTP | scrollWidth | clientWidth | maxScrollX | Page-level H-overflow | New wording visible | Old wording |
|---|---:|---:|---:|---:|---:|---|:--:|:--:|
| pack (`/packs/frontend-engineering/`) | 375 | 200 | 375 | 375 | 0 | none | ✓ | absent |
| pack | 768 | 200 | 768 | 768 | 0 | none | ✓ | absent |
| pack | 1280 | 200 | 1280 | 1280 | 0 | none | ✓ | absent |
| FE guide index (`/docs/guides/frontend-engineering/`) | 375 | 200 | 375 | 375 | 0 | none | ✓ | absent |
| FE guide index | 768 | 200 | 768 | 768 | 0 | none | ✓ | absent |
| FE guide index | 1280 | 200 | 1280 | 1280 | 0 | none | ✓ | absent |

- All six route×width cells: **HTTP 200**, `scrollWidth == clientWidth`,
  `maxScrollX == 0` → **no page-level horizontal overflow**; the narrowed
  wording is present in rendered `body.innerText`; the old wording is absent.
- FE guide index @375 — a full-`main` sweep found a `<code>` / `div.ec-line`
  block whose `getBoundingClientRect().right = 585` exceeds the 375 px viewport,
  but the page itself stays `375 / 375` with `maxScrollX 0`: Expressive Code /
  Starlight contains that code block in its own internal scroll region, so it
  scrolls inside its container rather than widening the page body. This matches
  the Starlight wide-content containment already recorded under
  [Code blocks and wide tables](#code-blocks-and-wide-tables-internal-scroll-vs-page-widening);
  it is internal scroll, not a page-level overflow regression.

### Session boundary (this re-verification)

Local static-build reader session on Node `v26.4.0`; `node_modules` already
present (no `npm ci`, no manifest or lockfile edits, nothing installed
globally). **No adopter-facing source file was staged, committed, reset, or
edited by this session — only this `qa.md` was written.** The copy edits
themselves were Codex's; this session only rebuilt and re-inspected. Post-run
`git status --short` shows **14 entries**, unchanged from session start (the
`docs/specs/frontend-engineering-doctrine-update/` untracked directory, which
holds this `qa.md`, counts as one entry; generated `build/` and `node_modules/`
are git-ignored). Nothing was staged or committed.

## Post-fix re-verification (2026-08-09)

After the initial pass reported `F1`, Codex remediated it and this session
rebuilt and re-inspected the surfaces from the working tree. The remediation
**replaced the opening `You say / Agent does / You get / Decision` table with a
list-based structure** on the journey template, so the route now renders **zero
`main table` elements** — the wide-table overflow can no longer occur. The
build and re-inspection used the same sequence as the initial pass:

- `make site-build` (generator → `web` build → `docs-site` build) — exit `0`;
  46 `web` pages + 217 `docs-site` pages built, pagefind index emitted.
- `npm run preview --prefix web -- --host 127.0.0.1` — served `build/` at
  `http://127.0.0.1:4321/agent-ready-repo`; all four target routes returned
  HTTP `200`.
- Headless Chromium (Playwright `1.62.1`, bundled Chromium) re-measured the
  four routes at 375 / 768 / 1280 px.
- Node `v26.4.0`; `node_modules` already present (no `npm ci`, no manifest or
  lockfile edits). No adopter-facing source file was staged, committed, reset,
  or edited — only this `qa.md` was written. Post-run `git status --short` is
  byte-identical to session start (13 entries); `build/` and `node_modules/`
  are git-ignored.

## Session boundary

This is a **local static-build reader session**. The four surfaces were built
from the working tree with the repository-prescribed generator/build sequence,
served locally with `astro preview` at `http://127.0.0.1:4321/agent-ready-repo`,
and inspected with headless Chromium (Playwright, bundled `@playwright/test`
Chromium) at 375 px, 768 px, and 1280 px. Evidence below is rendered-DOM
measurement from that local static build.

- Runtime: Node `v26.4.0` (satisfies both site packages' `engines.node >=24.0.0`).
- Dependencies were absent and were installed with `npm ci` (no manifest or
  lockfile edits, nothing installed globally).
- The prior session's blockers — Node v22, absent `node_modules`, and a
  `build-site.py` permission error — did **not** recur in this environment.
- No adopter-facing source file was staged, committed, reset, or edited. Only
  this `qa.md` was written. Post-run `git status --short` is byte-identical to
  the session-start status (13 entries); generated `build/` and `node_modules/`
  are git-ignored.

### Explicitly not exercised

- **Actual `frontend-engineering` skill execution** — no create/retrofit/audit/
  verify run was performed; only the published static surfaces were read.
- **Field Core Web Vitals collection** — no field/lab CWV measurement (LCP/INP/
  CLS) was taken; the reference page's *targets* were read as published copy.
- **Remote deployment** — GitHub Pages / production deploy was not exercised;
  all routes were served locally.
- **Live cross-theme sweep and pagefind search overlay** — theme toggle and
  search were present and focusable but not exhaustively exercised in both
  themes for every route.

## Commands and exit results

| # | Command | Exit | Result |
|---|---|---:|---|
| 1 | `npm ci --prefix web` | 0 | Installed; `web/node_modules/.bin/astro` present. |
| 2 | `npm ci --prefix docs-site` | 0 | Installed; `docs-site/node_modules/.bin/astro` present. |
| 3 | `python tools/build-site.py` | 0 | `build-site: done.` — 12 pack journeys synced (incl. `frontend-engineering`), 183 navigable guide pages, sidebar + mirrors generated. No permission error. |
| 4 | `npm run build --prefix web` | 0 | 46 pages built into `build/`; `sitemap-index.xml` emitted. |
| 5 | `npm run build --prefix docs-site` | 0 | 217 pages built into `build/docs/`; pagefind index built. |
| 6 | `npm run preview --prefix web -- --host 127.0.0.1` | 0 | Served `build/` at `http://127.0.0.1:4321/agent-ready-repo`; all four target routes returned HTTP `200` (incl. the `/docs/...` guide routes served from `build/docs/`). Shut down cleanly. |
| 7 | `SKIP_SAST=1 make build-check` | 0 | All drift/lint/policy gates passed. **SAST/SCA leg intentionally skipped** via the task-authorized `SKIP_SAST=1`; the make banner prints `INCOMPLETE — the SAST/SCA leg was SKIPPED`. The later full `make build-check` recorded above also passed. The `lint-pack-descriptions` "801 chars … run away" line is the lint's **own self-test fixture** (literal `[pack]` placeholder; `test-lint-pack-descriptions: all cases passed`); the real repo scan printed `no pack description has run away`. The `frontend-engineering` `pack.toml` description measures 226 chars. |

Build order followed `docs-site/AGENTS.md` § Build exactly: generator → `web`
(cleans and writes `build/`) → `docs-site` (writes `build/docs/`).

## Routes exercised

| Surface | Route (under `/agent-ready-repo`) | HTTP |
|---|---|---:|
| FE pack page | `/packs/frontend-engineering/` | 200 |
| FE journey | `/journeys/frontend-engineering/` | 200 |
| Page/screen-contract how-to | `/docs/guides/frontend-engineering/how-to/page-screen-contract/` | 200 |
| Performance reference | `/docs/guides/frontend-engineering/reference/performance-targets/` | 200 |

## Per-viewport observations and DOM evidence

Each identifier below is a durable `dom:<route>-<width>-<aspect>` anchor,
recording route, viewport, selector/aspect, and measured result.

### Horizontal overflow — `document.documentElement.scrollWidth` vs `clientWidth`

| Evidence ID | Route | Width | scrollWidth | clientWidth | Page-level horizontal overflow |
|---|---|---:|---:|---:|---|
| `dom:pack-375-overflow` | pack | 375 | 375 | 375 | none |
| `dom:pack-768-overflow` | pack | 768 | 768 | 768 | none |
| `dom:pack-1280-overflow` | pack | 1280 | 1280 | 1280 | none |
| `dom:journey-375-overflow` | journey | 375 | 375 | 375 | none (post-fix; pre-fix was **404** / **present — 29 px**) |
| `dom:journey-768-overflow` | journey | 768 | 768 | 768 | none |
| `dom:journey-1280-overflow` | journey | 1280 | 1280 | 1280 | none |
| `dom:howto-375-overflow` | how-to | 375 | 375 | 375 | none |
| `dom:howto-768-overflow` | how-to | 768 | 768 | 768 | none |
| `dom:howto-1280-overflow` | how-to | 1280 | 1280 | 1280 | none |
| `dom:reference-375-overflow` | reference | 375 | 375 | 375 | none |
| `dom:reference-768-overflow` | reference | 768 | 768 | 768 | none |
| `dom:reference-1280-overflow` | reference | 1280 | 1280 | 1280 | none |

- `dom:journey-375-overflow-culprit` (**pre-fix diagnosis**) — journey @375,
  selector `main table` (the opening `| You say | Agent does | You get |
  Decision |` 4-column table under **The journey**). Measured
  `getBoundingClientRect().width = 384 px`, `right = 404 px` against a 375 px
  viewport; computed `overflow-x: visible` (the table was **not** wrapped in a
  scroll container), so it widened the page body instead of scrolling
  internally. Corroborated by `dom:journey-375-body-scroll`:
  `window.scrollTo(scrollWidth, y)` drove `window.scrollX` to `29` with
  `maxScrollX = 29`, i.e. the whole page body rubber-banded 29 px sideways.
- `dom:journey-375-overflow-resolved` (**post-fix**) — the remediation replaced
  that opening table with a list-based structure. At 375 px the journey now
  reports `document.documentElement.scrollWidth = 375`, `clientWidth = 375`,
  `maxScrollX = 0`, and **`main table` count = 0**. A full-`main` sweep found
  **no element** whose `getBoundingClientRect().right` exceeds the 375 px
  viewport (`wideElements = []`). The four job entries **Create, Retrofit,
  Audit, Verify** now render as genuine `<li>` list items (the first four
  `main li` nodes: `Create: …`, `Retrofit: …`, `Audit: …`, `Verify: …`), and
  each per-step contract (`You provide / Agent does / You do / You decide /
  Output / State`) renders as list items rather than table rows. No page-level
  horizontal scrolling remains. Smoke-checked at 768 px (768/768, `maxScrollX
  0`, 0 tables) and 1280 px (1280/1280, `maxScrollX 0`, 0 tables) — both clean.
- Scope check `dom:journey-375-template-scope` — pre-fix, the same template
  rendered the `core` and `experience-design` journeys' widest table at 335 px
  (fits, no overflow) and `product-documentation` with no table. So the defect
  was **not** template-wide; it was triggered by this pack's opening-table cell
  copy exceeding the viewport, on a journey template that did not wrap wide
  markdown tables in a scroll container. The remediation removed the wide table
  from this journey's content rather than adding a template-level scroll
  wrapper, so the latent template gap (a future wide journey table would still
  need containment) persists but is no longer tripped here (tracked by `F2`'s
  sibling concern; not blocking).

### Reader-visible layout outcome

- `dom:pack-375-layout` / `dom:pack-768-layout` / `dom:pack-1280-layout` — pack
  page renders the `web` amber system: dark top nav, light hero with the pack
  name, `USER` scope chip, `9 skills`, tagline, then job sections. Single-column
  at 375/768; content column with generous margin at 1280. No clipping, no
  overlap.
- `dom:journey-*-layout` — journey renders the amber hero (`Install this pack →`
  filled amber CTA, `Read the reference ↗` amber-outlined CTA), the contract
  block, the six numbered journey steps, human gates, and skills. Clean at
  375/768/1280 post-fix — the opening contract now renders as lists (no
  `main table`), and the body no longer scrolls horizontally at 375 px.
- `dom:howto-*-layout` / `dom:reference-*-layout` — docs surfaces render the
  `docs-site` enterprise cobalt palette: cool neutral ground, Source Serif 4
  display headings, cobalt eyebrow/accent, tinted inline-code chips,
  accent-bordered blockquote. Sidebar/ToC collapse behind a `Menu` control at
  375/768; three-column at 1280. No overflow at any width; the large 12-field
  and surface-type tables are contained (Starlight wraps tables in a scrollable
  region — see code-block/table note below).

### Navigation behavior

- `dom:pack-nav` / `dom:journey-nav` — `web` marketing `nav.nav`. At 375/768 the
  full link row collapses behind a `<summary>` labelled **"Toggle navigation
  menu"** (CSS `<details>`, zero-JS); at 1280 the inline links
  `How it works · Catalogue · Journeys · Docs ↗` plus the `Install →` CTA are all
  present and focusable.
- `dom:howto-nav` / `dom:reference-nav` — Starlight `header.header` with a
  `Menu` toggle at 375/768 that opens the sidebar drawer; at 1280 the sidebar,
  `GitHub` link, and `Dark/Light/Auto` theme `<select>` are inline. `Search ⌘K`
  present at all widths.

### Keyboard focus — visibility and order (first 8 tab stops per route/width)

- `dom:pack-focus` / `dom:journey-focus` — every captured stop showed a visible
  indicator: computed `outline-style: solid`, `outline-width: 2px`. Order is
  sensible: `Skip to content` → wordmark → (mobile) `Toggle navigation menu` →
  in-content CTAs (`Install this pack →`, `Read the reference ↗`) → disclosure
  `<summary>` gate rows → `Copy` on the install snippet. 8/8 stops visible at
  each width.
- `dom:howto-focus` / `dom:reference-focus` — 8/8 stops visible; several carry
  both `outline` and a `box-shadow` ring. Order: `Skip to content` → wordmark →
  `Search ⌘K` → (mobile) `Menu` / (desktop) `GitHub` + theme `<select>` →
  `On this page` ToC → `← Platform` back-link → in-content links. Focus order
  follows DOM/reading order; no focus trap observed across the 8 stops.

### Code blocks and wide tables (internal scroll vs page widening)

- `dom:pack-codeblocks` / `dom:journey-codeblocks` — the only fenced blocks on
  these two routes are the `agentbundle install …` snippets. Measured
  `right-edge ≤ viewport` at every width (e.g. @375 `right = 323 ≤ 375`; @1280
  `right = 805 ≤ 1280`); `scrollWidth == clientWidth` (content fits, no scroll
  needed) and `widens-page = false` in all cases. No wide fenced code block
  exists on the four target routes to force internal horizontal scrolling, so
  that specific behavior was not triggered here; no block widened the page.
- `dom:howto-tables` / `dom:reference-tables` — the how-to's 12-field contract
  tables and the reference's 7-category asset-budget and 5-row surface-type
  tables are the widest content. At 375 px none caused page-level overflow
  (`dom:howto-375-overflow` / `dom:reference-375-overflow` both 375/375):
  Starlight contains wide tables in a scrollable region (e.g. the reference's
  widest table @375 measures `scrollWidth 466 > clientWidth 343`, scrolling
  internally without widening the page). This containment is what the `web`
  journey template still lacks at the template level; the `F1` remediation
  sidestepped that gap by removing the wide table from this journey's content
  rather than adding a scroll wrapper.

### Link destinations — pack → journey → guide

- `dom:pack-links` — pack body links resolve to
  `…/journeys/frontend-engineering/` ("Follow the frontend engineering journey"
  and "Explore the Frontend Engineering journey") and `…/docs/guides/
  frontend-engineering/` ("Read the full reference ↗"). Frontmatter `journeyUrl`
  and `docsUrl` present.
- `dom:journey-links` — journey body links resolve to
  `…/packs/frontend-engineering/` ("Install this pack →"), `…/docs/guides/
  frontend-engineering/` ("Read the reference ↗"), and the related journeys
  `…/journeys/experience-design/` and `…/journeys/product-documentation/`.
- `dom:howto-links` — how-to in-page section anchors resolve within
  `…/how-to/page-screen-contract/#…`.
- `dom:transition-chain` — followed live: pack → `…/journeys/frontend-engineering/`
  returned **200**; journey → `…/docs/guides/frontend-engineering/` returned
  **200**. The pack ⇄ journey ⇄ guide loop is navigable end-to-end.

### Cold-reader five-second assessment (pack page)

- `dom:pack-heading-order` — `main` heading sequence is:
  `H1 Frontend Engineering` → `H2 Create` → `H2 Retrofit` → `H2 Audit` →
  `H2 Verify` → `H2 Journey` → `H2 Skill inventory` → … The four jobs
  (**Create, Retrofit, Audit, Verify**) each lead with an "Expected output" and
  appear **before** the skill inventory. The intro paragraph states the pack
  "routes the work by job before it shows the skill inventory." A cold reader
  can answer *what the pack is* (implementation layer for product web
  surfaces), *who it serves* (product teams/agents building HTML/CSS/JS
  surfaces), and *which job to choose* within the first scroll, ahead of the
  inventory. Satisfies AC3/AC9 as rendered.

## Experience review (fresh context)

Read as (a) an evaluating lead scanning the pack/journey and (b) a task-focused
adopting engineer using the two guides, against the two grounded directions:
`docs/specs/platform-site/spec.md` (amber/dark-hero `web` system, WCAG 2.2 AA,
no horizontal body scroll at 375 px) and
`docs/specs/docs-site-design-refresh/spec.md` (cool cobalt enterprise palette,
optical-size display serif, hairline chrome, eyebrow sidebar, AA floor).

Severity scale: 4 = critical, 3 = major (blocking), 2 = minor, 1 = cosmetic.
Per the task and spec AC12, success is not declared while any severity-3-or-higher
finding is open. `F1` was reported for Codex to apply, applied, and re-verified
resolved in this session (no source was fixed by this session).

| ID | Sev | Route | Finding | Status |
|---|:--:|---|---|---|
| `F1` | **3** | journey @375 | The opening `You say / Agent does / You get / Decision` table (`main table`, 384 px wide, `overflow-x: visible`, not in a scroll wrapper) caused 29 px of page-level horizontal body scroll at 375 px (`dom:journey-375-overflow`, `dom:journey-375-overflow-culprit`, `dom:journey-375-body-scroll`). This violated the explicit "no horizontal body scroll at 375 px" contract stated in `web/AGENTS.md`, `docs-site/AGENTS.md`, and the platform-site WCAG 2.2 AA posture, on a primary adopter surface at the smallest supported viewport. | **Resolved** — Codex replaced the opening table with a list-based structure. Re-inspected post-fix (`dom:journey-375-overflow-resolved`): journey @375 now `scrollWidth 375 / clientWidth 375 / maxScrollX 0`, **0 `main table` elements**, no element overflowing the viewport, Create/Retrofit/Audit/Verify present as `<li>` items; clean at 768/1280 too. Contract now satisfied. |

No other severity-3-or-higher findings. Lower-severity observations:

- `F2` (sev 1, journey/pack) — `web` fenced-code `<pre>` computes
  `overflow-x: visible` rather than the `auto` that `web/AGENTS.md` describes;
  harmless on these routes because the install snippets fit, but a long code
  line would widen the page. Not exercised by these four routes; noted for
  awareness, not blocking.

Aesthetic-fit verdict: the pack and journey render coherently in the amber
platform-site system; the two guides render coherently in the docs-site cobalt
enterprise system (display serif headings, eyebrow ToC, cobalt accent, tinted
code chips, hairline rules). Palette separation between `web` and `docs-site` is
intact and intentional. Both themes' tokens appeared mapped; focus indicators
meet the ≥2 px / visible bar on every captured stop. The one blocking issue,
`F1`, is now **resolved and re-verified**; no severity-3-or-higher finding
remains open. **Experience-review verdict: SHIP** — the rendered experience
clears the grounded directions at all three viewports, subject to the explicit
limitations recorded above (no live skill execution, no field CWV, no remote
deploy, no exhaustive cross-theme/search sweep).

## Disposition

- Repository gates: `make site-build` (generator → `web` build → `docs-site`
  build), the scoped `SKIP_SAST=1 make build-check`, and the final full
  SAST/SCA-enabled `make build-check` all exit 0.
- Rendered experience: **clear** — the sole severity-3 finding `F1` (journey
  375 px horizontal overflow) has been remediated by Codex and re-verified
  resolved (`dom:journey-375-overflow-resolved`: 375/375, `maxScrollX 0`, 0
  `main table`). Per AC12 and the task instruction, T7 is now a clean pass at
  the experience gate; no severity-3-or-higher finding is open.
- Limitations preserved: the re-verification remains a **local static-build
  reader session** — no live `frontend-engineering` skill execution, no field
  Core Web Vitals collection, no remote/GitHub-Pages deploy, and no exhaustive
  cross-theme or pagefind-search sweep (see [Explicitly not
  exercised](#explicitly-not-exercised)).
- Handoff: `F1` is resolved; the non-blocking `F2` (`web` fenced-code `<pre>`
  computes `overflow-x: visible`) and the latent template-level wide-table
  containment gap remain open for follow-up but do not block T7. This session
  made no source edits — only this `qa.md` was written.

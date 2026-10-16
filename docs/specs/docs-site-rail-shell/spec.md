# Spec: docs-site-rail-shell

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`docs/design/direction/docs-site.md`](../../design/direction/docs-site.md), [`docs/design/journeys/team-orientation-future-state.md`](../../design/journeys/team-orientation-future-state.md) Stage 4
- **Brief:** none
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`, `What
> Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working
> material.

## Outcome

A reader of the technical docs site (`docs-site/`) sees one top bar with four
tabs — Docs, CLI, Author, Catalogue System — and a sidebar that holds only the
current tab. In the Docs tab, the guides hang from five operating-model stage
lines: Set up a repository, Decide what to build, Shape it, Build it, Ship it.
The page title names its stage. The site wears the Rail line look recorded in
`docs/design/direction/docs-site.md`. The docs home is a short Intro that
installs the toolkit with `agentbundle` or as a Claude plugin.

## What Changes

- **Top bar.** `Header.astro` renders the site title, the tab links, and on the
  right search, the GitHub link, and a theme toggle. The product orientation
  band and the phone Product disclosure are gone from docs pages.
- **Tabs and sidebar.** The Starlight sidebar config's top level is the tab set.
  `Sidebar.astro` renders the current tab only, with stage groups drawn as
  coloured lines; on phones the tabs repeat at the top of the menu.
- **Stage chip.** `PageTitle.astro` shows the stage name above the title of a
  page that sits in a stage group, in place of the breadcrumb.
- **Pagination.** Previous and next stay inside the current tab.
- **Theme toggle.** A single icon button replaces Starlight's theme dropdown.
- **Look.** `rail.css` re-points the docs tokens to the Rail line palette and
  restyles type, prose, code, tables, asides, tabs, cards, and the on-this-page
  list.
- **Intro.** `index.mdx` replaces the task hub with the Intro page.

Guide content, guide URLs, the guide merge into job pages, the Packs, CLI and
Catalogue System page content, the pack-page template, and the Changelog page
are outside this spec. Sidebar entries link to today's guide pages.

About 190 guide pages that the old pack-grouped sidebar listed are in no tab.
Each still builds at its URL, shows the Docs tab with nothing current, and has
no previous or next link. Readers reach them through search, the guides index
at `/docs/guides/`, each pack page's guide links, and in-body links, until the
guide-merge follow-ons fold them into job pages.

A page that sets `prev` or `next` in its frontmatter keeps Starlight's
pagination instead of the tab-scoped one.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Visual direction | The look changes | `docs/design/direction/docs-site.md` (status `selected`) | creative-direction | Owner approval recorded in the record | Record selected; superseded record points to it |
| Journey | Stage 4 navigation changes | `docs/design/journeys/team-orientation-future-state.md` Stage 4 amendment | approve-journey | Amendment entry dated 2026-10-15 | Entry present |
| Superseded contracts | Shipped specs pin the old shell | `site-shared-chrome`, `docs-site-design-refresh`, `docs-wayfinding-cluster`, `documentation-entry-navigation` spec notes | this spec | Each carries a "superseded in part" note naming the AC | Notes present |
| Maintainer guidance | Two `docs-site/AGENTS.md` traps describe the removed Product disclosure | `docs-site/AGENTS.md` | this spec | Trap text matches the shell | Text updated |
| Release history | Not applicable: the docs site is not a versioned artifact, and `docs/product/changelog.md` records released artifacts only | none | — | — | — |

## Agent Rules

### Always do

- Derive tabs, stage groups, and pagination from the one Starlight sidebar
  array, so header, sidebar, title, and paging cannot disagree.
- Keep every text colour, including each stage hue, at or above 4.5:1 on both
  the page ground and the subtle surface in both themes.

### Ask first

- Changing any published guide URL.
- Adding a dependency.

### Never do

- Colour a link, button, focus ring, or background with a stage hue.
- Add a print stylesheet rule outside `Footer.astro`.

## Testing Strategy

- **Goal-based check** — built-HTML assertions in `web/src/test/rendered-output.test.ts`
  for the top bar, tabs, sidebar scope, stage chip, pagination, and Intro.
- **Goal-based check** — `tools/check-docs-contrast.py` measures the Rail line
  pairs, stage hues included.
- **Visual / manual QA** — the browser gate (`npm run test:e2e:gate --prefix web`)
  plus recorded screenshots of Intro and one stage page at 1440 px in both
  themes and at 390 px.

## Acceptance Criteria

- [x] **AC1 — One top bar.** Given any docs page, the page has exactly one
  `nav[aria-label="Documentation sections"]` inside the header with links
  labelled Docs, CLI, Author, Catalogue System in that order, exactly one
  carrying `aria-current="true"`; the header holds the search control, a GitHub
  link, and the theme toggle; no page contains `nav[aria-label="Product orientation"]`
  or `nav[aria-label="Product navigation"]`.
- [x] **AC2 — Theme toggle.** Given a docs page in light theme, when the reader
  activates the theme toggle, `html[data-theme]` becomes `dark`,
  `localStorage['starlight-theme']` is `dark`, the button's accessible name
  becomes "Switch to light theme", and a reload keeps the dark theme. The phone
  menu carries the same control.
- [x] **AC3 — Sidebar holds the current tab.** Given a page listed in a tab, its
  rendered sidebar links are exactly that tab's links in config order, and the
  page's own link carries `aria-current="page"`. A page listed in no tab
  renders the Docs tab. On a 390 px viewport the open menu shows the four tab
  links.
- [x] **AC4 — Docs tab structure.** The Docs tab renders Intro, an Operating
  model group with no `data-stage` holding Overview and Detailed model, Packs,
  then groups with `data-stage` `setup`, `decide`, `shape`, `build`,
  `ship` in that order, then a collapsed Pack listing group whose links are
  every `packs/<slug>/` page in label order.
- [x] **AC5 — Stage chip.** Given a page in a stage group, the title block shows
  one `.rail-chip` whose text is the stage name and whose `data-stage` matches
  the group, and no breadcrumb. Every other titled non-home page shows one
  breadcrumb and no chip.
- [x] **AC6 — Pagination stays in the tab.** For every page listed in a tab,
  `a[rel="prev"]` and `a[rel="next"]` point at its neighbours in that tab's
  link order, and are absent at the tab's ends. A page listed in no tab has no
  pagination links.
- [x] **AC7 — Intro.** The docs home has the title "Intro", an Install section
  with tabs labelled `agentbundle` and `Claude plugin` that show
  `agentbundle install --pack core` and `claude plugin install`, a "Make your
  first request" section, and link cards to the Operating model and Packs. It
  has no `.docs-hub__primary` or `.docs-hub__supporting` element.
- [x] **AC8 — Contrast.** `tools/check-docs-contrast.py` exits 0 and its output
  includes every Rail line text pair — ink, text, muted, and the five stage
  hues — on ground and subtle in both themes.
- [x] **AC9 — Quality floor.** The browser gate passes: zero serious or critical
  axe findings on the gated docs pages in both themes, no horizontal overflow
  at 375 px, keyboard focus visible on the tabs, toggle, and sidebar links.

## Follow-ons

- Merge guides into job pages (one PR per stage group), Packs, CLI, and
  Catalogue System content, the pack-page template, and the Changelog removal.

## Assumptions

- The site title keeps linking to the docs Intro; product destinations stay in
  the footer.

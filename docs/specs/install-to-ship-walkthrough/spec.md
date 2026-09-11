# Spec: install-to-ship-walkthrough

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [`documentation-entry-navigation`](../documentation-entry-navigation/spec.md) (Shipped; AC10 makes `guides/README.md` the portable hub, AC14 forbids a new top-level route or design-system expansion)
- **Brief:** docs/product/briefs/sdlc-guide-uplift-and-learning-paths.md
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: full. The change touches the marketing landing page, the documentation
home, the getting-started page, and the portable guide hub — four public entry
surfaces owned by a Shipped spec.

## Objective

A newcomer who lands on either public entry point — the marketing landing page
at `/` or the documentation home at `/agent-ready-repo/docs/` — finds one named
route, **the install-to-ship walkthrough**, and follows it from installing the
catalogue to a governed, reported release without first choosing a pack or
reading a menu of files. The walkthrough lives on the existing guide hub at
`/agent-ready-repo/docs/guides/`. It presents the ordered paths that already
exist there as one continuous line of five stages: each stage names what the
reader must already have, what they get, and carries a link to the stage that
follows, so the reader is never left at the end of a stage deciding where to go.
The catalogue-extension path stays on the hub as a branch a reader can take
later, outside the walkthrough. The route survives site generation, so what a
reader clicks in the deployed site is the route this repository authored.

The walkthrough is a reading route over content that already exists. It renames
and connects; it adds no new page, no new URL, and no new workflow.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — the walkthrough *is* the user-facing promise this slice makes | `guides/README.md` | `author-product-docs` workflow; docs maintainers | The named walkthrough section with its five ordered stages, their prerequisite and first-value lines, and their next-stage links | AC1–AC7 hold |
| Current product truth (documentation entry) | Applicable — the documentation home advertises what a reader can do | `docs-site/src/content/docs/index.mdx` | `docs-site/` maintainers, under `docs-site/AGENTS.md` | A named link to the walkthrough above the outcome grid | AC9 holds |
| Current product truth (funnel continuity) | Applicable — the docs hero action sends readers to getting-started, which ends without a route into the lifecycle | `docs-site/src/content/docs/getting-started/index.mdx` | `docs-site/` maintainers, under `docs-site/AGENTS.md` | A named link to the walkthrough in the `## Continue` list | AC10 holds |
| Current product truth (marketing entry) | Applicable — the landing page shows an install command and then stops | `web/src/components/marketing/InstallTerminal.astro` | `web/` maintainers, under `web/AGENTS.md` | A named link to the walkthrough in the section's closing note | AC8 holds |
| Interface compatibility | Applicable — published URLs are an external contract | `notes/route-baseline.txt` in this spec directory, holding the accepted-base route set | `web/` maintainers, as part of the site build contract | The recorded route set, and the post-change comparison in `notes/verification-ledger.md` | AC12 holds |
| Operations | Applicable in the narrow sense that execution observations need a home outside the pinned pair | `notes/verification-ledger.md` | `work-loop`, during execution | Build, comparison, and gate results produced during execution | The ledger records each gate's command and result |
| Decision rationale | **Not applicable** — no decision is made here that the Shipped `documentation-entry-navigation` spec did not already settle. This slice applies its AC10 hub and stays inside its AC14 no-new-route boundary. | — | — | — | — |
| Release history | **Not applicable** — `docs/CONVENTIONS.md` § 5b makes a changelog entry owed "in the same PR that bumps a released artifact's version" and states that "repository tooling that ships in no release needs no entry". This slice bumps no version and ships no released artifact. | — | — | — | — |
| Architecture | **Not applicable** — no component, boundary, or data flow changes. | — | — | — | — |
| Maintainer procedure | **Not applicable** — no new authoring or release step is introduced. | — | — | — | — |
| Reusable learning | **Not applicable** — the one durable lesson (which suites a `tools/` or web test actually runs under) is already owned by the executable surfaces that encode it: the file list at `Makefile:584` and `.github/workflows/pages.yml`. `docs/CONVENTIONS.md` § *Durable outputs own lasting truth* forbids using this spec/plan pair as a substitute for a living owner, and creating a prose document restating a Makefile would be exactly that. | — | — | — | — |

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Reuse the ordered-path content already in `guides/README.md`. Reframe and
  connect it; do not rewrite the guidance it points at.
- Link to the walkthrough by its named heading from every entry point, so a
  reader lands on the route rather than the top of the hub page.

### Ask first

- Adding a tenth marketing section component, or any change to the landing
  page's section order in `web/src/pages/index.astro`.
- Changing a published URL, or changing a heading anchor that any authored page
  in this repository links to. Anchors that only Starlight's own on-this-page
  navigation and heading permalink reference are generated from the heading and
  move with it; they are not inbound links for this rule.
- Promoting the paths to their own pages, as
  `docs/design/screens/team-orientation/path-page.md` proposes. That is a
  separate programme with its own route decisions.

### Never do

- Add a new top-level route or a new page under `docs-site/src/content/docs/`.
  The Shipped `documentation-entry-navigation` AC14 forbids it.
- Add a key to `contracts/guide.schema.json`. It sets
  `additionalProperties: false`, and this slice needs no frontmatter key.
- Change any skill's behavior, trigger phrasing, or `SKILL.md`.
- Edit generated content under `docs-site/src/content/docs/guides/` or
  `docs-site/src/content/docs/packs/`. Those trees are produced by
  `tools/build-site.py` from `guides/**` and `packs/**`.
- Deliver any part of brief slices S2 through S5: the `desk-research` handover
  link, the product-strategy or harvestable affordance passes, and the tutorial
  input demonstrations are out of scope.
- Freeze a count of guides, packs, or paths into a criterion or a test. The
  corpus moves; a count assertion decays into a false failure.

## Testing Strategy

Every criterion here describes what the published site shows a reader, so every
standing check is a **goal-based check over emitted HTML**. Reading authored
source instead would admit content a reader never sees — a walkthrough written
inside an HTML comment satisfies a source regex and renders nothing.

- **Walkthrough structure (AC1–AC7, AC14):** the emitted guide hub page carries the
  named heading, the five stage headings in order, the eight activity names,
  each stage's prerequisite and first value, each stage's successor link, and
  the catalogue-extension path outside the walkthrough.
- **Entry links (AC8–AC10):** each emitted entry page carries one anchor whose
  text and target are asserted together. Two separate assertions — a right
  target somewhere and the right words somewhere — pass on a page where they
  belong to different elements.
- **Emitted anchor (AC11):** exercised as an integration check across the
  generation step and both site builds, since only the consuming renderer
  establishes the heading id.
- **Route preservation (AC12):** set membership against the recorded
  accepted-base route set. A count comparison is not sufficient: a build that
  drops one route and adds another preserves the count.
- **Link integrity (AC13):** every internal link emitted on the three entry
  surfaces resolves to a page the site also emits.

**What these checks do not establish.** AC4 and AC5 constrain the *shape* of a
stage's prerequisite and first value — a prerequisite must name earlier stages
or `none`, and first values must be present and distinct — but no mechanical
check can judge whether a first value is the *right* description of what the
stage produces. That judgement belongs to the documentation review the
`author-product-docs` workflow owns, on the guide diff. The criteria catch a
stage that loses its lines or duplicates another's; they do not catch prose that
is well-formed and wrong.

These checks also read the emitted document, so they prove an anchor exists with
the right text and target — not that it is visible after CSS, nor that a pointer
actually lands on it. The repository's browser
gate visits the marketing routes, the docs home, and one nested guide; it does
not visit the guide hub or the getting-started page, and its marketing route set
is another spec's ratified constant. Extending it is out of this slice's scope,
so CSS-level concealment of a walkthrough link is a gap this spec accepts rather
than one it covers. The browser gate still runs and must stay green.

No behavior in this slice has a compressible invariant, so no criterion is
TDD-mode. No new screen or component is designed, so no criterion is
visual/manual QA; the one marketing edit is a link inside an existing section.

## Acceptance Criteria

- [x] **AC1 — the route has a name.** `guides/README.md` contains a heading
      whose text is `The install-to-ship walkthrough`.
- [x] **AC2 — the walkthrough has five stages in this order.** The walkthrough's
      stages, in document order, are: adopt the catalogue, shape what to build,
      build it, decide together, ship and report. **A stage is a heading labelled
      `P<n>` with a bare number** — see the 2026-09-11 amendment. A heading
      labelled `P<n>b` is an alternative route, not a stage, and is excluded from
      AC2's count, AC4's prerequisite chain, AC5's first-value uniqueness and
      AC6's successor chain.
- [x] **AC3 — the walkthrough covers the whole lifecycle.** Each of these eight
      activities is named in at least one walkthrough stage: installation,
      shaping, architecture, Core intake, build, governance, release, reporting.
- [x] **AC4 — every stage states what a reader needs first.** Each walkthrough
      stage states its prerequisite as either `none` or one or more earlier
      stages of the walkthrough.
- [x] **AC5 — every stage states what it produces.** Each walkthrough stage
      states a non-empty first value, and no two stages state the same one.
- [x] **AC6 — every stage but the last links to its successor.** Each
      walkthrough stage except the fifth carries a link whose text names the
      stage that follows it and whose target is that stage.
- [x] **AC7 — catalogue extension is a branch, not a stage.** The
      catalogue-extension path appears on the guide hub outside the walkthrough
      section.
- [x] **AC8 — the marketing landing page enters the walkthrough.** The rendered
      marketing landing page at `/` presents an anchor whose text names the
      install-to-ship walkthrough and whose target is the walkthrough heading on
      the published guide hub.
- [x] **AC9 — the documentation home enters the walkthrough.** The rendered
      documentation home at `/agent-ready-repo/docs/` presents an anchor whose
      text names the install-to-ship walkthrough and whose target is the
      walkthrough heading on the published guide hub.
- [x] **AC10 — the getting-started page continues into the walkthrough.** The
      rendered page at `/agent-ready-repo/docs/getting-started/` presents an
      anchor whose text names the install-to-ship walkthrough and whose target
      is the walkthrough heading on the published guide hub.
- [x] **AC11 — the walkthrough heading is addressable in the published site.**
      The emitted guide hub page carries an element whose `id` is
      `the-install-to-ship-walkthrough`.
- [x] **AC12 — no published route is lost.** The set of internal routes the site
      emits contains every route recorded in
      [`notes/route-baseline.txt`](notes/route-baseline.txt).
- [x] **AC13 — every internal link on the three entry surfaces resolves.** Every
      internal link emitted on the marketing landing page, the documentation
      home, and the guide hub targets a page the site also emits.
- [x] **AC14 — the catalogue-extension branch stays walkable.** The
      catalogue-extension section links to each of: why catalogue curation, your
      first skill, build an org stack pack, and create a catalogue.

## Follow-ons

- eugenelim: `docs/product/briefs/sdlc-guide-uplift-and-learning-paths.md`
  candidate slices S2–S5 — the `desk-research` handover link, the two affordance
  passes, and the tutorial input demonstrations remain unconfirmed slices of the
  same brief.
- eugenelim: `docs/design/screens/team-orientation/path-page.md` — the
  six-path-pages pattern is a designed but unbuilt future state that would add
  routes; it needs its own route decision before any of it is built.

## Assumptions

- Technical: `guides/README.md` is published at `/agent-ready-repo/docs/guides/`
  because `tools/build-site.py` renames `README.md` to `index.md` to preserve
  the directory-index URL (source: `tools/build-site.py:1235-1241`).
- Technical: under `docs-site/src/content/docs/`, only `index.mdx` and the
  `getting-started/` files are tracked; `guides/`, `packs/`, `changelog.md`, and
  `contributing.md` are build outputs ignored by `.gitignore:91-96` (source:
  `git ls-files docs-site/src/content/docs`, which lists only the tracked four).
- Technical: neither `web/src/pages/index.astro` nor
  `docs-site/src/content/docs/index.mdx` links to the guide hub at
  `/docs/guides/` today, which is why the walkthrough is unreachable from either
  entry point (source: `grep -rn "docs/guides/" web/src/ docs-site/src/`). Deep
  links to individual guide pages exist elsewhere on the marketing site and are
  not affected by this slice.
- Technical: `contracts/guide.schema.json` sets `additionalProperties: false`
  and already carries optional `journey` and `order` keys, so a prose-and-links
  walkthrough needs no schema change (source: parsed
  `contracts/guide.schema.json`; properties are `aliases, journey, kind, order,
  pack, slug, status, summary, title`).
- Technical: Starlight emits a stable id derived from each authored heading's
  text — the observed pair is `## Follow a path` → `id="follow-a-path"` (source:
  2026-09-08 spike build recorded in
  [`notes/verification-ledger.md`](notes/verification-ledger.md)). AC11's exact
  id is therefore an expectation, not a derivation: no general slug rule is
  claimed here, because the observed ids for the punctuated stage headings do
  not follow the obvious one. An emitted id other than the required one is a
  criterion failure, not a target to adjust to.
- Technical: no authored page in this repository links to `#follow-a-path`. The
  emitted page's references to it are Starlight's own on-this-page navigation
  and heading permalink, which are generated from the heading and move with a
  rename (source: repository-wide `grep` for `follow-a-path`, whose only
  non-spec match is an action name in
  `docs/design/journeys/docs-guides-champion-current-state.md:136`).
- Technical: `tools/test_documentation_entry_links.py` runs under `make test`
  via the file list at `Makefile:584`; `web/src/test/rendered-output.test.ts`
  runs only under `npm test --prefix web`, invoked in CI by
  `.github/workflows/pages.yml:192` and by no `make` target (source: those
  files).
- Technical: `tools/test_documentation_entry_links.py` lists
  `web/src/pages/index.astro` but not `InstallTerminal.astro` in its
  `MARKETING_SOURCES`; the component is read only by its homepage-anchor
  discovery (source: that module's `DOC_SOURCES` and `MARKETING_SOURCES`
  tuples).
- Process: a changelog entry is owed only "in the same PR that bumps a released
  artifact's version", and "repository tooling that ships in no release needs no
  entry" (source: `docs/CONVENTIONS.md` § 5b).
- Process: from plan approval, `spec.md` and `plan.md` are pinned in substance
  and "an observation produced by execution belongs in the sibling
  `notes/verification-ledger.md`" (source: `docs/CONVENTIONS.md` § *A spec
  directory freezes as a unit, when the spec ships*).
- Process: `docs/specs/documentation-entry-navigation/spec.md` is `Shipped` and
  owns all four entry surfaces; its AC14 forbids a new top-level route or
  design-system expansion, and its AC10 already established `guides/README.md`
  as the portable hub (source: that spec's header and AC list).
- Product: the route is named "the install-to-ship walkthrough" (source: user
  confirmation 2026-09-08).
- Product: the marketing entry point is a link inside the existing
  `InstallTerminal` section rather than a new landing-page section (source: user
  confirmation 2026-09-08).
- Product: the walkthrough's main line is the install-to-ship sequence; the
  catalogue-extension path stays reachable on the hub but is not a stage,
  because the brief's outcome names installation through reporting and stops
  there (source: user confirmation 2026-09-08 confirming S1 only, and the
  brief's stated outcome).
- Product: AC10 adds a third entry surface that the brief's S1 row does not name.
  The owner admits it as an extension to S1 because the documentation home's own
  hero action sends readers to getting-started, so without it that funnel
  dead-ends (source: user confirmation 2026-09-08).

## Amendment 2026-09-11 — "stage" is defined, so an alternative route can sit inside the section

**What prompted it.** Slice S6 of `sdlc-guide-uplift-and-learning-paths` added
`P2b`, a wider alternative to `P2`, placed directly after it so a reader sees
both options at the moment they choose a shaping route. An independent design
review endorsed that placement: `P2b` "is now discoverable exactly when P2 is
evaluated."

**What broke, and why it was the contract's fault rather than the content's.**
This spec's test implemented "stage" as *every `h3` inside the walkthrough
section*. `P2b` is an `h3` there, so AC2 counted six stages and AC6 tried to make
`P2` link to `P2b` as its successor. Both failed.

The first repair moved `P2b` out of the section to satisfy the test. That was
wrong. **A Shipped spec records what was true at delivery; it does not bind the
product's future shape.** When a shipped criterion blocks a change that is right,
the criterion gets amended — with its owner's consent, which this has — rather
than the content contorted to fit a snapshot. Reshaping the page to preserve an
implementation detail of a test is how a historical record turns into an
accidental design constraint.

**What changed.** Nothing about the walkthrough's five stages, their order, their
prerequisites, their first values, or their successor chain. Only the *definition*
of what counts as a stage, which was previously implicit in a selector: a stage is
`P<n>` with a bare number. `P<n>b` is an alternative route.

**The guard is not weakened.** Before, any `h3` added to the section failed AC2 —
including a legitimate alternative. Now a sixth *numbered* stage still fails it,
which is the case the criterion exists to catch, while a labelled alternative does
not. Verified by mutation: adding `### P6 · ...` inside the walkthrough section
still fails AC2.

**Ownership.** `P2b`'s content belongs to S6 and its walkability to S7. This
amendment only defines the term this spec already used.

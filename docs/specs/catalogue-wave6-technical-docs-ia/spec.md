# Spec: Catalogue Wave 6 — technical documentation information architecture

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0076 D9 and OQ4](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md)
- **Discovery:** intent:catalogue-wave6-technical-docs-ia
- **Contract:** none — this spec reads `contracts/pack.schema.json` and `contracts/skill.schema.json` and changes neither.
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `OQ4 resolution`, `Durable Outputs`,
> `Follow-ons` and `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

**Mode:** full. It restructures the docs-site's top-level navigation, a tab set
ratified at `approve-journey`, and adds a generator that projects two published
contracts into reference pages.

## Outcome

A catalogue author or evaluator opens one docs-site tab, Build a Catalogue, and
walks the ten RFC-0076 D9 routes from creating a catalogue to packaging and
publishing it, with field references for `pack.toml` and `SKILL.md` frontmatter
that state only what the schemas state. Success is that every route lands on its
authoritative page, the docs home offers "Use the catalogue" and "Build or
evaluate a catalogue" as separate choices, and no existing docs URL moves.

## What Changes

- Tabs — the Author and Catalogue System tabs are replaced by one Build a Catalogue tab; the bar reads Docs, CLI, Packs, Build a Catalogue (`docs-site/astro.config.ts`, with the new tab's tree in `docs-site/src/build-a-catalogue-nav.json`).
- Route tree — the tab's ten top-level entries are the D9 routes in D9 order; every page the two retired tabs listed moves under one of them.
- Fragment links — a sidebar link carrying a `#fragment` keeps it exact, and takes no position in previous/next paging because its page already has one (`docs-site/src/routeData.ts`).
- Field references — `tools/build-site.py` generates `/docs/reference/pack-toml/` from `contracts/pack.schema.json` and `/docs/reference/skill-frontmatter/` from `contracts/skill.schema.json` (`tools/schema_field_reference.py`); both are gitignored build output.
- Docs home — `docs-site/src/content/docs/index.mdx` gains the two route choices above its install steps.
- Journey — the prime journey records the new tab set and the docs-home route choices as a ratified amendment (`docs/design/journeys/team-orientation-future-state.md`).
- RFC-0076 OQ4 — resolved in [OQ4 resolution](#oq4-resolution-rfc-0076) below.

## OQ4 resolution (RFC-0076)

RFC-0076 OQ4 asks which `pack.schema.json` fields the schema annotations describe
well enough to generate reference pages, and which need manual narrative.

**The cut is by fact, not by field.** Every field gets a generated row. A fact is
generated when the schema states it with a keyword in AC-0010's set, which is
the one home of that list, or as a `description`, copied verbatim (AC-0011).
Everything else is narrative: what a field means, why
to set it, how it interacts with other fields, what the installer does with it,
and examples.

**What that leaves to narrative, measured at `d714ab829`.** `pack.schema.json` carries a
`description` on 4 fields (`pack.metadata`, `pack.evals`, `pack.recipes`,
`pack.runtime-dependencies`), so every other field's meaning is narrative. Its
three conditional rules — on `pack`, `pack.install` (twice) — are cross-field
semantics the generator names but does not render. `skill.schema.json` carries a
`description` on 5 of its 6 fields; `license` has none. The narrative owners are
[catalogue authoring standards § 2 Pack manifest](../../../guides/_shared/reference/catalogue-authoring-standards.md#2-pack-manifest)
and [§ 5 Skill frontmatter and body](../../../guides/_shared/reference/catalogue-authoring-standards.md#5-skill-frontmatter-and-body),
which each generated page links.

**Why descriptions are not added here.** Both schemas are published contracts,
byte-copied into `packages/agentbundle/agentbundle/_data/`. Adding annotations
changes that contract and needs an AgentBundle release. A later change that
adds a `description` gains generated text with no change to the generator.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing navigation | the tab set, route tree and docs home change | `docs-site/astro.config.ts`, `docs-site/src/build-a-catalogue-nav.json`, `docs-site/src/content/docs/index.mdx` | implementer | built pages and `web/src/test/rendered-output.test.ts` | AC-0001 to AC-0008 and AC-0017 checked |
| Generated reference | two field reference pages are new | `tools/schema_field_reference.py`, called from `tools/build-site.py`; output under `docs-site/src/content/docs/reference/` (gitignored) | implementer | `tools/test_schema_field_reference.py`; built pages | AC-0009 to AC-0016 checked |
| Current product truth (journey) | Stage 4 navigation was ratified with five tabs | `docs/design/journeys/team-orientation-future-state.md` new amendment; `docs/design/README.md` gate row | lifecycle owner ratifies at `approve-journey` | amendment names the four tabs, the two docs-home route choices and the owner's ratification date | ratification recorded before merge |
| Design direction | it names the retired tabs | `docs/design/direction/docs-site.md` tab mentions | implementer | lines name the four tabs | no retired tab name remains as current |
| Maintainer guidance | the site boundary and tab comment name what is generated | `docs-site/AGENTS.md` § Site boundary; `docs-site/src/components/rail.ts` header comment | implementer | both name the generated reference pages or the four tabs | text matches the tree |
| Decision rationale | OQ4 resolves here | this spec's OQ4 section; RFC-0076 acceptance checklist OQ4 line checked with a link here | implementer | RFC checklist item checked | link resolves |
| Product intent | the intent projects to this spec | intent `Decomposition` section and `- **Decomposed:**` line; `workspace.toml` `["ini-007".work]` | lifecycle owner | intent names this spec; workspace lists it | `workspace-status` shows it canonical |

No AgentBundle package file and no `guides/` source changes, so no release and no
scaffold sync apply.

## Agent Rules

### Always do

- Read route labels for AC-0002 from the RFC-0076 D9 tree, never from a copy.
- Keep generated reference pages out of Git; they exist only after `tools/build-site.py` runs.
- Build with `make site-build` and inspect the rendered pages before claiming a rendered criterion.
- Pass `encoding="utf-8"` to every text read and write.

### Ask first

- Changing any guide's content, URL or slug.
- Changing the Docs, CLI or Packs tab entries.
- Adding a `description` or any other keyword to a schema under `contracts/`.

### Never do

- Add a dependency, an npm package or a new top-level repository directory.
- Change `tools/build-site.py`'s guide mirror, guide rewriting or generated guide sidebar.
- Write prose about a field into a generated page that the schema does not state.
- Hand-maintain a list of schema fields anywhere.

## Testing Strategy

- **Tab set, page placement, fragment hrefs and paging — goal-based, exercised by an integration test over the built site (AC-0001, AC-0003, AC-0004, AC-0006, AC-0017)** — the rendered sidebar is what a reader sees, and `web/src/test/rendered-output.test.ts` already reads built HTML.
- **D9 route labels — TDD (AC-0002)** — a pytest suite compares the nav source with the RFC's D9 tree, both parsed natively.
- **Link closure — goal-based (AC-0005)** — `tools/check-rendered-site-links.py` already resolves every internal page and fragment target in the build.
- **Unchanged routes — goal-based (AC-0007)** — the sorted list of built `index.html` paths is compared with a build of the merge base.
- **Docs home — goal-based, integration test over the built site (AC-0008)** — the rendered cards and their hrefs are observable in built HTML.
- **Field reference content — TDD (AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015)** — the generator is a pure function from a schema to text; fixture schemas pin each keyword, and the real schemas pin coverage.
- **Narrow layout — visual / manual QA (AC-0016)** — a browser at 375 px measures page scroll width on both generated pages; record the measured widths.
- **Author walkthrough — visual / manual QA** — on the built site, follow the ten routes in order from the docs home and record where each lands.

## Acceptance Criteria

- [ ] **AC-0001.** On every built docs page, the header's "Documentation sections" navigation shows exactly the tabs Docs, CLI, Packs, Build a Catalogue, in that order.
- [ ] **AC-0002.** The Build a Catalogue tab's top-level entry labels equal the ten labels in the RFC-0076 D9 tree, in D9 order.
- [ ] **AC-0003.** Each page the Author and Catalogue System tabs link in `docs-site/astro.config.ts` at the branch's merge base with `origin/main` is linked from the Build a Catalogue tab's sidebar.
- [ ] **AC-0004.** No page linked from the Build a Catalogue tab's sidebar is linked from the Docs, CLI or Packs tab's sidebar.
- [ ] **AC-0005.** `tools/check-rendered-site-links.py --build-dir build` reports no missing page or fragment, including every Build a Catalogue sidebar link.
- [ ] **AC-0006.** On every built page in the Build a Catalogue tab, the sidebar href of each entry carrying a `#fragment` ends with that fragment, with no `/` after it.
- [ ] **AC-0007.** The set of built `build/docs/**/index.html` paths equals the set built from the branch's merge base with `origin/main`, plus exactly `reference/pack-toml/index.html` and `reference/skill-frontmatter/index.html`.
- [ ] **AC-0008.** The built docs home shows a "Use the catalogue" choice linking to its own `#install` section and a "Build or evaluate a catalogue" choice linking to `guides/_shared/how-to/create-a-catalogue/`, both before the "Install" heading.
- [ ] **AC-0009.** For each of `contracts/pack.schema.json` and `contracts/skill.schema.json`, its generated page has exactly one row per field path, where field paths are every `properties` key reached from the root through object `properties` and array `items`, after resolving local `$ref`.
- [ ] **AC-0010.** Each row states the field's `type` value, plus for an array the `type` its `items` schema gives, with an empty Type cell when the node has no `type`; whether its parent's `required` lists it; and every `enum`, `const`, `pattern`, `default`, `minimum`, `maximum`, `minLength`, `maxLength`, `minItems`, `maxItems`, `maxProperties`, `uniqueItems` and `additionalProperties` value the schema gives at that path, on that field's `items` schema, or under its `propertyNames`.
- [ ] **AC-0011.** A row's description cell is the schema's `description` at that path, verbatim, when one exists, and is empty otherwise.
- [ ] **AC-0012.** Each row whose schema node carries `if`, `allOf`, `anyOf` or `not` contains the marker `Conditional rules: see the narrative reference`, and no row contains text derived from those keywords' contents.
- [ ] **AC-0013.** Any schema node given as `oneOf` — a field, a value schema, an `items` schema, or an alternative of another `oneOf` — is rendered, after local `$ref` resolution, as a list of alternatives in schema order in which an alternative that is itself a `oneOf` contributes its own alternatives in its place, an alternative's `items` alternatives stay grouped inside that alternative, and each alternative carries its type and the AC-0010 values it gives.
- [ ] **AC-0014.** Each generated page names its source schema path and links to its narrative owner: `catalogue-authoring-standards#2-pack-manifest` for `pack.toml`, `catalogue-authoring-standards#5-skill-frontmatter-and-body` for `SKILL.md` frontmatter.
- [ ] **AC-0015.** Generating both pages twice from the same schemas produces byte-identical output.
- [ ] **AC-0016.** At a 375 px viewport, neither generated reference page's document scrolls horizontally.
- [ ] **AC-0017.** On every built page linked from the Build a Catalogue tab, the previous and next links are that page's neighbours in the tab's sidebar order with every `#fragment` entry skipped, and no previous or next href carries a fragment.

## Follow-ons

- eugenelim: [intent validation hook](../../product/intents/catalogue-wave6-technical-docs-ia.md#de-risking-verdict) — paired task-based navigation tests with 5 catalogue authors and evaluators.

## Assumptions

- Product: no author or evaluator has used the ten-route path yet — whether the grouping beats the old tabs is ungrounded until the follow-on runs.

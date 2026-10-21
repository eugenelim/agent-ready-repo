# Plan: Catalogue Wave 6 — technical documentation information architecture

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** RFC-0076 D9; `docs-site/AGENTS.md` (build order, rail tab rule, prime journey); analogous production paths `tools/build-site.py` `generate_sidebar_config` and `build_pack_index` (build-time projection into gitignored docs-site content) and `tools/build-site.py`'s importlib load of `tools/changelog.py` (sibling-module seam); their tests `tools/test_build_site_sidebar.py` and `web/src/test/rendered-output.test.ts`. Deviation: the Build a Catalogue tree lives in a JSON file `astro.config.ts` imports, rather than inline TypeScript, so a Python test can parse it natively.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/<feature>/notes/verification-ledger.md` (or the adopter's
> equivalent). A genuine artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval: approval hashes the whole plan.

## Approach

The generator lands first, because the new tab links its two pages and
Starlight refuses a sidebar slug with no page. The tab and its contract test
land second, then the docs home and the rendered tests, then the companion
documents. The riskiest part is fragment links: a spike on the base build
showed Starlight appends `/` after a `#fragment` in sidebar and pagination
hrefs (`…/#11-optional-pack-integrations/`), which the rendered link checker
reports as a missing fragment. The fix sits in the route middleware, which
already rewrites pagination, so both surfaces read one corrected href.

Review shape: one PR, MIXED but small, one commit per task. Each task leaves
the repository green.

## Constraints

- RFC-0076 D9 fixes the ten route labels and their order, the two home routes, and leaves the central guide rendering and pack-guide routes unchanged.
- `tools/AGENTS.md`: new `tools/` files are pure-stdlib Python.
- `docs-site/AGENTS.md`: `web/` builds before `docs-site/`; `rail.ts` keys stage colour by Docs-tab group label, so no Docs-tab label changes.
- `web/AGENTS.md`: full Playwright runs rewrite tracked snapshots; stage files explicitly.
- `tools/test_build_site_sidebar.py::test_promoted_guides_are_reachable_from_get_started` greps `astro.config.ts` for `slug: '<promoted>'`; the promoted guides in `site.toml` are not among the 21 moved pages, which T2 confirms before moving anything.

## Construction tests

**Rule for every acceptance test:** it must fail when the mechanism it checks is bypassed — the D9 test fails when one label is renamed in the JSON; the fragment assertion fails when the middleware fix is removed; the generator tests fail when one keyword is dropped from the renderer.

**Integration tests:** `web/src/test/rendered-output.test.ts` over a full `make site-build` (T3).

**Manual verification:** T5 — base-versus-new page set, link check, 375 px measurement, and the ten-route walkthrough from the docs home.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| User-facing navigation | T2, T3 | nav JSON, `astro.config.ts`, `index.mdx` | rendered-output suite green on a full build |
| Generated reference | T1 | `tools/schema_field_reference.py` | `tools/test_schema_field_reference.py` green; two built pages |
| Current product truth (journey) | T4 | journey amendment, `docs/design/README.md` row | owner ratification date recorded |
| Design direction | T4 | `docs/design/direction/docs-site.md` | no retired tab named as current |
| Maintainer guidance | T4 | `docs-site/AGENTS.md`, `rail.ts` comment | text matches the tree |
| Decision rationale | T4 | RFC-0076 OQ4 checklist line | link resolves |
| Product intent | T4 | intent Decomposition, `workspace.toml` | `workspace-status` canonical |

## Design (LLD)

### Component / module decomposition

- `tools/schema_field_reference.py` (new, stdlib): `field_rows(schema: dict) -> list[FieldRow]` walks the schema; `render_page(schema: dict, *, title: str, source: str, narrative_href: str, narrative_label: str) -> str` returns Markdown with frontmatter; `generate(out_dir: Path, *, dry_run: bool = False) -> list[Path]` writes both pages. `PAGES` names the two schemas, their output slugs (`reference/pack-toml`, `reference/skill-frontmatter`), titles (`pack.toml fields`, `SKILL.md frontmatter fields`) and narrative links.
- `tools/build-site.py` loads it by `importlib` exactly as it loads `tools/changelog.py`, and calls `generate(SITE_DOCS / "reference", dry_run=args.dry_run)` once in the full pass after mirroring guides. `.gitignore` and `docs-site/.gitignore` gain `docs-site/src/content/docs/reference/`. `--clean` also removes that directory.
- `docs-site/src/build-a-catalogue-nav.json` holds the tab group `{label: "Build a Catalogue", items: [...]}` in Starlight's sidebar shape; `astro.config.ts` imports it and replaces the Author and Catalogue System groups with it.
- `docs-site/src/routeData.ts` gains one pass over the resolved sidebar before pagination: for a link whose href contains `#` and ends in `/` after it, drop that `/`. Its `links()` walk then skips every link whose href carries `#`, so paging runs over page entries only. Why skip rather than keep: a fragment entry points into a page the tab already lists, and `findIndex(isCurrent)` places that page at its own entry, so a fragment entry in the paging order would send "next" from Ledger and guard to the route-2 page and its "next" back to route 3. With the skip, Ledger and guard pages to Design a profile, and Catalogue CI contract pages to Host on Artifactory.

Owned by: T1, T2.

### Behavior & rules

The Build a Catalogue tree. Labels in quotes are sidebar labels; `#` marks a fragment link. Every moved page keeps its URL.

1. "Create a catalogue" → `guides/_shared/how-to/create-a-catalogue`
2. "Catalogue authoring standards" → `guides/_shared/reference/catalogue-authoring-standards`
3. "Author a pack" (group) → "Build a pack" `guides/_shared/how-to/build-an-org-stack-pack`; "Pack config API" `guides/_shared/reference/pack-config-api`
4. "Author a skill" (group) → "Write a skill" `guides/_shared/how-to/author-a-skill`; "Author a subagent" `guides/catalogue-curation/tutorials/your-first-subagent`; "Import and curate skills" `guides/catalogue-curation/how-to/survey-a-repo`; "Add credentials to a skill" `guides/credential-brokers/how-to/add-a-credentialed-skill`; sub-group "Reference" → "Skill authoring standards" `guides/_shared/reference/skill-authoring-standards`, "Skill script conventions" `guides/_shared/reference/skill-script-conventions`, "Skill UX patterns" `guides/_shared/reference/skill-ux-patterns`, "Credentialed skill walkthrough" `guides/credential-brokers/reference/credentialed-skill-walkthrough`, "Ledger and guard" `guides/catalogue-curation/reference/ledger-and-guard`
5. "Optional pack integrations" → `guides/_shared/reference/catalogue-authoring-standards/#11-optional-pack-integrations`
6. "Author a profile" → `guides/_shared/how-to/design-a-profile`
7. "Journey format" (group) → "Journey format reference" `guides/_shared/reference/pack-journey-format`; "Write a pack journey" `guides/_shared/how-to/pack-journey-authoring`
8. "Contract and schema reference" (group) → "pack.toml fields" `reference/pack-toml`; "SKILL.md frontmatter fields" `reference/skill-frontmatter`; "catalogue.toml format" `guides/_reference/catalogue-format`
9. "Verify and test" → `guides/_shared/reference/catalogue-ci-contract`
10. "Package and publish" (group) → "Package a release" `guides/_shared/reference/catalogue-ci-contract/#agentbundle-catalogue-package`; "Host on Artifactory" `guides/_shared/how-to/create-a-self-hosted-catalogue`; "Artifactory distribution" `guides/_shared/reference/artifactory-catalogue-distribution`; "Set enterprise defaults" `guides/_shared/how-to/configure-catalogue-enterprise-distribution`; "Roll out across an enterprise" `guides/_shared/how-to/roll-out-agent-ready-repo-across-an-enterprise`

The 21 pages AC-0003 names are the slug targets the base `astro.config.ts` Author and Catalogue System groups list: the 12 Author entries and 9 Catalogue System entries. All 21 appear above as non-fragment entries; `pack-journey-format` and the two generated pages are additions.

Field reference rows:

- A row per field path, depth-first in schema key order; an array of objects contributes `path[]` as the prefix of its item fields. A local `$ref` (`#/$defs/...`) is resolved before reading keywords.
- Columns: Field, Type, Required, Rules, Description. Type is the `type` value; `array of <item type>` for an array whose `items` states a type, `array of [<alternatives>]` when `items` is a `oneOf`, and plain `array` when `items` states neither; `one of: <alternatives>` for `oneOf`; empty when the node states no type. `field_rows` holds each `oneOf` as a list of `Alternative(type, rules, items)` records, where `items` is the item alternatives of an array alternative or `None`, built per AC-0013. Rendering writes each alternative as its type, then its rules in parentheses with values in code spans, then for an array ` of [<item alternatives>]`, alternatives joined by `; ` — so the `compatibility` value reads ``one of: string (maxLength: `1024`); boolean; integer (minimum: …, maximum: …); array (maxItems: `256`) of [string (maxLength: `1024`); boolean; integer (…)]``. The text format is design; the T1 assertions read the records. Keywords on the `items` schema other than `properties` and `required` appear in Rules prefixed `items`, so an array of closed objects reads `items: no undeclared keys`; `propertyNames` keywords appear prefixed `keys`. Required is `yes` or `no` from the parent's `required`. Rules lists the AC-0010 keywords as `keyword: value`, values in code spans; `additionalProperties: false` reads `no undeclared keys`; a schema-valued `additionalProperties` reads `each value: <type summary>`. A row whose node carries `if`, `allOf`, `anyOf` or `not` adds the AC-0012 marker. Description is the schema `description` or empty.
- Table cells escape `|` as `\|` and wrap values in code spans; the spike rendered `^0\.([2-9]|[1-9][0-9])|^[1-9]` intact this way.
- The page opens with one sentence naming the source schema path and one linking the narrative owner, then the table. No other prose.

Owned by: T1, T2.

### State & control flow

Docs home: a `## Choose your route` section after the two opening paragraphs and before `## Install`, holding a `CardGrid` of two `LinkCard`s — "Use the catalogue" → `#install`, describing installing packs and making a first request; "Build or evaluate a catalogue" → `/agent-ready-repo/docs/guides/_shared/how-to/create-a-catalogue/`, describing authoring, verifying and publishing with the contracts behind it. The rest of the page is unchanged.

Owned by: T3.

### Quality attributes (NFRs)

AC-0016: the field tables are the widest content. `rehype-scrollable-tables` already wraps every table in a scroll container, so the table scrolls inside its frame and the document does not; T5 measures `document.documentElement.scrollWidth` against the viewport.

Owned by: T1, T5.

## Tasks

### T1 — Field reference pages are generated from the two schemas

- **Depends on:** none
- **Touches:** `tools/schema_field_reference.py`, `tools/test_schema_field_reference.py`, `tools/build-site.py`, `.gitignore`, `docs-site/.gitignore`
- **Verification mode:** TDD
- **Tests:** `tools/test_schema_field_reference.py`, pytest, loads the module by `importlib` like `tools/test_build_site_sidebar.py` loads `build-site.py`.
  - AC-0009: an independent walker in the test collects field paths from each real schema; the rendered page's first-column paths equal that list, with no duplicates. A fixture with a nested object, an array of objects and a `$ref` pins the walk.
  - AC-0010: one fixture schema carries every listed keyword once; each value appears in its row's Rules cell. In the real schemas, the `schema` row's Type cell is empty, `pack.seeds` shows its items `pattern`, `pack.install.allowed-scopes` its items `enum`, and `compatibility` its `propertyNames` `maxLength: 1024`; `pack.categories` reads `array of string`, `pack.install.allowed-scopes` reads `array`, and `pack.maintainers` shows `items: no undeclared keys`.
  - AC-0011: in the real pack schema, the `pack.metadata` row's Description cell equals the schema text, and the `pack.name` row's cell is empty.
  - AC-0012: the real pack schema's `pack` and `pack.install` rows carry the marker; a fixture whose `if` contains a sentinel string never shows it.
  - AC-0013: for the skill schema's `compatibility` row, the value-schema `Alternative` records equal, by `(type, rules, items)`: `string {maxLength: 1024}`, `boolean`, `integer {minimum: -9007199254740991, maximum: 9007199254740991}`, then `array {maxItems: 256}` whose `items` are those same three records. Dropping the nested `compatibilityScalar` alternatives, or merging the array's items into the outer list, fails the comparison. A fixture pair yields unequal records and unequal rendered cells: `oneOf[string, array with items oneOf[integer, boolean]]` against `oneOf[string, array with items oneOf[integer], boolean]`, so `boolean` is the array's last item alternative in one and the outer alternative right after the array in the other — the placement a flat renderer writes identically.
  - AC-0014: each page contains its source path and its narrative href.
  - AC-0015: two `render_page` calls over the same input are equal, and `generate` into two temporary directories writes byte-identical files.
  - Stub (scratch red before the module exists):
    ```python
    import importlib.util, json
    from pathlib import Path
    ROOT = Path(__file__).resolve().parent.parent
    _spec = importlib.util.spec_from_file_location("schema_field_reference", ROOT / "tools" / "schema_field_reference.py")
    sfr = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(sfr)

    def test_pack_rows_cover_every_field_path():
        schema = json.loads((ROOT / "contracts" / "pack.schema.json").read_text(encoding="utf-8"))
        assert [r.path for r in sfr.field_rows(schema)] == _walk(schema)  # _walk: test-local walker
    ```
- **Done when:** the suite is green, `python3 tools/build-site.py` writes both pages, and `git status` shows neither.

### T2 — The Build a Catalogue tab carries the ten D9 routes

- **Depends on:** T1
- **Touches:** `docs-site/src/build-a-catalogue-nav.json`, `docs-site/astro.config.ts`, `docs-site/src/routeData.ts`, `tools/test_build_a_catalogue_nav.py`
- **Verification mode:** TDD for the labels; goal-based for the rest
- **Tests:** `tools/test_build_a_catalogue_nav.py`, pytest.
  - AC-0002: parse the fenced tree under `### D9` in the RFC — each `├──`/`└──` line's label is the text before the first run of two spaces or `(` — and compare with the JSON's top-level `label`s.
  - Every JSON `slug` resolves to a guide source through `build-site.py`'s `_guide_site_url`, or to a `PAGES` entry of the generator.
- **Done when:** the suite is green and `tools/test_build_site_sidebar.py` stays green.

### T3 — The docs home offers two routes and the rendered suite pins the new tabs

- **Depends on:** T2
- **Touches:** `docs-site/src/content/docs/index.mdx`, `web/src/test/rendered-output.test.ts`, `web/src/test/e2e/site-quality-gate.spec.ts`
- **Verification mode:** goal-based, integration test over the built site
- **Tests:** in `rendered-output.test.ts`, after `make site-build`:
  - AC-0001: the four existing tab-order assertions read Docs, CLI, Packs, Build a Catalogue; `current(AUTHOR_PAGE)` is `Build a Catalogue`. The e2e tab-order assertion moves the same way.
  - AC-0003: a constant lists the 21 URLs the Author and Catalogue System groups link at `d714ab829`; each is a sidebar href on `AUTHOR_PAGE`. T5 confirms the constant still equals that set in the merge base's `astro.config.ts`.
  - AC-0004: the `AUTHOR_PAGE` sidebar hrefs share none with the sidebars of `NESTED_GUIDE` (Docs), `CLI_PAGE` (CLI) and `packs/index.html` (Packs).
  - AC-0006: for every non-fragment sidebar href on `AUTHOR_PAGE`, open that built page; its "Optional pack integrations" and "Package a release" hrefs end exactly `#11-optional-pack-integrations` and `#agentbundle-catalogue-package`.
  - AC-0017: the existing docs-site-rail-shell AC6 test (`rendered-output.test.ts` ~553-574, walks `AUTHOR_PAGE`'s sidebar) computes expected neighbours from the sidebar links with fragment entries removed, and skips fragment entries as subjects; it also asserts that no `rel=prev`/`rel=next` href on those pages contains `#`. Its Docs-tab behaviour is unchanged, since the Docs tab has no fragment entry.
  - AC-0008: the home's `.sl-link-card` hrefs include `#install` and `…/guides/_shared/how-to/create-a-catalogue/`, and both cards precede the `Install` `h2` in document order.
  - The existing AC3 sidebar assertions hold for the Build a Catalogue tab: one current link, no link shared with the Docs tab.
- **Done when:** `npm test --prefix web` is green against a fresh full build.

### T4 — Companion records match the new tab set

- **Depends on:** none
- **Touches:** `docs/design/journeys/team-orientation-future-state.md`, `docs/design/README.md`, `docs/design/direction/docs-site.md`, `docs-site/AGENTS.md`, `docs-site/src/components/rail.ts`, `docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md`, `docs/product/intents/catalogue-wave6-technical-docs-ia.md`, `workspace.toml`
- **Verification mode:** goal-based
- **Tests:** no stub (goal-based). `git grep -n "Author, Catalogue System\|Docs, CLI, Author"` over `docs/design` and `docs-site` returns only dated history; `python3 .claude/skills/work-loop/scripts/lint-graph-pointers.py --root . --base-ref origin/main` and `python3 tools/check_closure_terminality_parity.py --root .` exit 0.
- **Done when:** both commands exit 0, the RFC diff is the one OQ4 line, and the journey amendment covers the four tabs and the two docs-home route choices and carries the owner's ratification date.

### T5 — The built site passes the rendered checks and the walkthrough

- **Depends on:** T1, T2, T3
- **Touches:** `docs/specs/catalogue-wave6-technical-docs-ia/notes/verification.md`
- **Verification mode:** visual / manual QA
- **Tests:** no stub (manual QA).
  - AC-0005: `make site-link-check` exits 0.
  - AC-0003: the slugs in the Author and Catalogue System groups of `git show $(git merge-base HEAD origin/main):docs-site/astro.config.ts` equal the T3 constant.
  - AC-0007: `git worktree add` a temporary checkout of `git merge-base HEAD origin/main`, run `make bootstrap-sites` then `make site-build` there, and diff its sorted `find build/docs -name index.html` list with this branch's; the diff shows exactly the two added pages. The worktree is removed afterwards.
  - AC-0016: Playwright Chromium at 375 × 812 records `scrollWidth` and `innerWidth` on both generated pages.
  - Walkthrough: from the docs home, follow "Build or evaluate a catalogue", then each of the ten routes in order, and record the landing URL and heading for each.
- **Done when:** `notes/verification.md` records each result above with its command and observed output.

## Changelog

- 2026-10-21 — drafted.
- 2026-10-21 — spec approved by eugenelim, with the Stage 4 journey amendment (four tabs; two docs-home route choices) ratified at `approve-journey`.
- 2026-10-21 — plan approved by eugenelim.

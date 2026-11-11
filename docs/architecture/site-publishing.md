# Site publishing

The repository publishes one GitHub Pages site built from two Astro projects.
`web/` is the marketing site at `/`. `docs-site/` is the technical
documentation site at `/docs/`.

Neither project owns its content: the pack
READMEs, `guides/`, the product changelog, and the contract schemas do, and
`tools/build-site.py` projects them into the build inputs. Two gates stand
between a content change and a deployment: `pages.yml` runs the builds,
rendered-output checks, and a browser gate before it uploads, and a deployment
job runs only on `main`. [Binder publishing](binder-publishing/README.md) is a
separate design and is `STATUS: PLANNED`; it does not describe this site.

Allowed dependency edges follow [ARCHITECTURE.md § 3](../../ARCHITECTURE.md):
site builders read authored content and contracts, and nothing authored depends
on a build output.

## 1. Authored content is projected, never edited in place

`tools/build-site.py` is the only writer of generated site inputs.[^1] Edit the
source, not the projection.

| Source | Projection | Notes |
| --- | --- | --- |
| `packs/*/README.md` | `docs-site/src/content/docs/packs/<pack>.md` | Links rewritten; `packs/index.md` is generated |
| `guides/**` | `docs-site/src/content/docs/guides/**` | `README.md` becomes `index.md`; Starlight frontmatter injected; guide-only fields stripped |
| `docs/product/changelog.md`, `CONTRIBUTING.md` | `changelog.md`, `contributing.md` | Links rewritten |
| `contracts/pack.schema.json`, `contracts/skill.schema.json` | `docs-site/src/content/docs/reference/` | Field references |
| `contracts/catalogue-spec.toml`, `docs-site/spec-src/catalogue/overview.md` | `docs-site/src/content/docs/spec/` | Catalogue specification pages |
| Pack journeys | `web/src/content/journeys/` | `build-site.py --journeys-only` |
| Released changelog highlights | `web/src/lib/now-highlights.generated.json` | Feeds `/now/` |
| Shared chrome, receipts | `*.generated.json` renderer inputs | Gitignored |

The `*.generated.json` inputs are gitignored. The `predev`, `prebuild`, `preastro` and `pretest` hooks in `web/`, and the same three plus `pretest:plugins` in
`docs-site/`, run `build-site.py --renderer-inputs` to regenerate
them, so those scripts need `python3` as well as Node.[^2] The sidebar derives
from `site.toml` (`[[groups]]` for packs, `[[guide_groups]]` for guides,
`promoted_guides` for hand-linked entries) and `guide-nav-baseline.toml`, a
frozen label source that outranks a page's own title until its entry is removed.
`project_guide_sidebar` orders each kind bucket by the resolved label, so
adopting a curated title reorders its bucket.[^3]

### 1.1 Guide links resolve at build time and fall back to GitHub

`_rewrite_guide` resolves each relative Markdown link in a guide against the
tree. A target inside `guides/` that exists becomes a base-qualified site URL. A
target that does not exist inside `guides/`, or that lies elsewhere in the
repository, becomes a GitHub blob URL.

An unresolved in-tree guide link
therefore becomes an external link, and `tools/check-rendered-site-links.py`,
which audits internal links only, never sees it.[^4] No gate detects that
fallback. The detector is registered as
[`emitted-guide-link-fallback-detector`](../product/intents/emitted-guide-link-fallback-detector.md).

## 2. Two sites build in a fixed order

`web/` builds first, because `astro build` cleans the repository `build/`
directory and `docs-site/` then writes `build/docs/`. Reversing the order
deletes the documentation site.[^5]

`make site-build` runs `site-sync` (`build-site.py`), then both builds. `make
site-link-check` adds the rendered-link audit. `make bootstrap-sites` installs
both npm projects, and `make web-browser-gate` runs the browser gate on a leased
preview port.[^6] None of these targets is a prerequisite of `make ci`
([verification topology § 3.2](verification-graph.md)).

## 3. `pages.yml` gates the artifact before it deploys

`pages.yml` runs a `build` job and, on `main` only, a `deploy` job. The build
job runs these steps in order, and a failure at any step prevents the upload:[^7]

1. Install `web/` and `docs-site/` dependencies under one `setup-node` (Node 24).
2. Install Playwright Chromium.
3. Validate the frozen product changelog baseline with `tools/changelog.py render`.
4. Project marketing renderer inputs (`build-site.py --journeys-only`).
5. Build the marketing site.
6. Assert the Claude plugin route is offered only for user-capable packs
   (`tools/check-site-plugin-offers.py`, reading rendered HTML).
7. Run the docs-site plugin unit tests.
8. Aggregate content and build the docs site.
9. Assert release anchors match the emitted changelog.
10. Audit rendered internal links (`tools/check-rendered-site-links.py`).
11. Compare built release members with the deployed release index
    (`tools/check-deployed-release-parity.py`). The check fetches the live index
    and skips only on a `workflow_dispatch` whose ref is not `main`.
12. Assert rendered-output invariants with `npm test --prefix web`, run with a
    6 GiB Node heap because the whole-site scans parse every page.
13. Run the deterministic browser gate, `npm run test:e2e:gate --prefix web`: an
    explicit allowlist of four Playwright specs (`site-quality-gate`,
    `quality-assertions`, `docs-rail`, `press-state`). `tools/test_browser_gate_subset.py`
    asserts the allowlist in both directions.
14. Upload the Pages artifact. Failure artifacts upload only on failure.

The workflow triggers on `push` to `main` and on `pull_request`, filtered by
path, and on `workflow_dispatch`. The `build` job is not a required status
context, and its `paths:` filter means it cannot simply become one. A concurrency
group keyed by event isolates pull requests; the `deploy` job uses the bare group
`pages` with `cancel-in-progress: false` so a writer is never killed mid-write.

That group serializes deployments but does not order them: an older commit can
publish last after two close merges. Both gaps are registered in
[`required-check-and-deploy-ordering`](../product/intents/required-check-and-deploy-ordering.md).
`tools/test-pages-workflow.py` and `tools/test-pages-concurrency.py` pin the
workflow's shape; both run under `make test`.

## 4. Marketing and documentation sites divide the reader journey

`web/` serves the first three stages of the prime journey (evaluate, prove on
real work, win buy-in), and `docs-site/` serves stages four and five.[^8] Both
resolve internal links relative to the deployment subpath, and Markdown content
uses relative cross-site links because origin-root paths fail under that
subpath.

| Surface | Route source | Notes |
| --- | --- | --- |
| `web/src/pages/index.astro` | Home | Pack and journey data from `web/src/content/` |
| `web/src/pages/packs/`, `catalogue/`, `plugins/`, `journeys/` | Pack, catalogue, plugin, and journey views | Per-pack pages from `web/src/content/packs/` (23 records) |
| `web/src/pages/now/` | Released highlights | Index, pagination, archive, per-release permalink, Atom feed; all from one parsed changelog model |
| `docs-site/src/content/docs/` | Guides, pack pages, reference, spec, changelog | Starlight, with `docs-site/src/plugins/` rehype plugins |

## 5. Gaps registered against this subsystem

| Gap | Intent |
| --- | --- |
| Unresolved in-tree guide link ships as an external 404 | [`emitted-guide-link-fallback-detector`](../product/intents/emitted-guide-link-fallback-detector.md) |
| A curated guide title reorders its sidebar bucket | [`guide-sidebar-label-ordering`](../product/intents/guide-sidebar-label-ordering.md) |
| `agent-skill-engineering` has no guide and is exempt from the guide index | [`agent-skill-engineering-guide-slice`](../product/intents/agent-skill-engineering-guide-slice.md) |
| Orphaned end-to-end specs | [`test-runner-boundary-completion`](../product/intents/test-runner-boundary-completion.md) |
| Pages deploy lacks commit ordering; `build` is not a required context | [`required-check-and-deploy-ordering`](../product/intents/required-check-and-deploy-ordering.md) |
| Binder publishing has no build specification | [`binder-publishing-build-spec`](../product/intents/binder-publishing-build-spec.md) |

## Governing records

- [RFC-0061](../rfc/0061-web-top-level-directory.md): the `web/` directory.
- [ADR-0085](../adr/0085-docs-rendering-is-site-local.md): docs rendering is site-local.
- [ADR-0109](../adr/0109-starlight-replaces-mkdocs-for-reference-docs.md): Starlight renders reference docs.

[^1]: Module docstring and `main` in `tools/build-site.py`.

[^2]: `web/AGENTS.md` and `docs-site/AGENTS.md`; `predev`, `prebuild`, `preastro`, `pretest`, and `pretest:plugins` scripts in `web/package.json` and `docs-site/package.json`.

[^3]: `site.toml`; `guide-nav-baseline.toml`; `project_guide_sidebar` and `_guide_label` in `tools/build-site.py`.

[^4]: `_rewrite_guide` in `tools/build-site.py`; `LinkParser` and `AuditError` in `tools/check-rendered-site-links.py`.

[^5]: `web/AGENTS.md` build-order rule; the comment above the first build in `.github/workflows/pages.yml`.

[^6]: `site-sync`, `site-build`, `site-link-check`, `bootstrap-sites`, and `web-browser-gate` targets in the `Makefile`.

[^7]: Step names and order in the `build` job of `.github/workflows/pages.yml`; `tools/check-deployed-release-parity.py` docstring; `tools/test_browser_gate_subset.py`.

[^8]: `web/AGENTS.md` and `docs-site/AGENTS.md`, which anchor on `docs/design/journeys/team-orientation-future-state.md`.

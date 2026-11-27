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

Guide metadata exemptions are structural, not a reason to invent a reader
outcome for an import shim. `validate_guides.py` owns the exact root-relative
allowlist, including the one-line `CLAUDE.md` import. Mirroring is unconditional
and sidebar eligibility is separate. An exempt file gaining frontmatter would
also skip slug/alias registration, so the exception is not general metadata
coverage. Curated sidebar labels sort by `casefold()` and slug; the proposal to
stabilize their order was withdrawn, not left as an implementation obligation.

The catalogue outcome labels in `guides/README.md` follow
`web/src/lib/catalogue-navigation.ts`, as `test_catalogue_navigation.py` binds
them. That test establishes the label authority; a source header describing a
narrower scope does not reverse it. The task-first documentation home routes to
workflows independently of that outcome taxonomy.

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

### 2.1 A config-only change once left cached output unchanged

During the Mermaid rollout recorded on 2026-08-23, a remark-plugin config change
left the emitted HTML unchanged. The Markdown had not changed, and the build
reused cached renders from `docs-site/.astro` and `node_modules/.astro`. The
delivery's output checks were repeated with cold caches before their results
were accepted.[^10] This is a dated verification observation; cache behavior
on the current Astro version was not remeasured in this retirement review.

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

A source-content edit can change emitted HTML without moving a route. A route
count alone cannot prove route stability: a rename keeps the count. Check source
path additions, deletions and renames against the projector's routing rules when
that distinction matters.

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

### CLI navigation and moved URLs

The CLI tab in `docs-site/astro.config.ts` lists four tasks: Install
agentbundle, Install packs for your agent, Configure agentbundle, and Upgrade
packs. Its Reference group links to Command reference, Adapter support, and
File safety. The authored task pages live in `guides/_shared/how-to/`.

Moved guide URLs live in the absorbing page's `aliases` frontmatter, which
`tools/build-site.py` projects as redirect stubs. The separate
`/getting-started/install/` route redirects to Install agentbundle through
`docs-site/astro.config.ts`. These two mechanisms preserve the former install,
configure, preview, profile, and user-scope entry routes.[^9]

The README helps evaluators choose a route; CONTRIBUTING owns contributor
entry, and the authoring hub owns author instructions. They need different
densities, so a generated README/shared-copy system was deliberately rejected.
Links connect those roles without creating parallel rule owners. Current
`guides/AGENTS.md` owns job-page writing; retired guidebook-step and old four-tab
shell scope are migration history, not instructions for new guides.

Guide aliases use explicit meta-refresh stubs rather than assuming an unverified
Starlight `redirect:` frontmatter feature. Sidebar generation was a separate
phase and is now present; its old deferral is not unpaid work. Early alias
staging warnings are not proof that current published links resolve.

### Renderer contracts and evidence limits

ADR-0085 keeps components, palettes and framework controls local to each
renderer. Shared destination kind owns internal/external behavior; hostname
comparison does not. Component source interfaces and the current design tree
own the present UI. Earlier plans' shared-color and blanket CSS-only choices
are historical: marketing's current install component contains script, while
its mobile navigation uses native disclosure. Retiring those plans does not
reassert their old MkDocs pipeline or claim new browser QA.

Breakpoint-edge captures target rules leaking across a breakpoint. One sample
per band leaves every other width unobserved; a scrollbar can also change the
attained layout viewport, so its width must be read back. Height/scroll pairs
are grouped by exact width and height, not band. The old height-only prose guard
was a finite string-deletion pin, not a semantic proof that all such claims had
gone. The retained
[channel contract](../specs/rendered-page-channel-axis/spec.md) owns the full
capture rules.

The deterministic browser gate is distinct from optional screenshots. Framework
ownership does not excuse an accessibility defect. Print evidence has separate
owner decisions: the page-break check closed on regenerated evidence, while the
chrome-paint inventory was retired as won't-do. The
[print audit](../specs/site-browser-quality-gate/notes/print-audit.md)
and tap-target audit retain those results; no unchecked task is declared done.

Source-derived callout checks deliberately ended conversion-ledger-to-live-tree
coupling. Per-type counts cannot detect a same-type swap or replaced body, and
indented/lazy/nested blockquotes can differ between the small counter and remark.
Three accepted counter cases had no live occurrence when evaluated; the
aside-nested-body case was fixed, not waived. The historical quotation-versus-
advice ledger records human judgment and is not a perpetual claim about current
prose. Its archival release/handoff tripwire is intentionally not a required
runner; mechanical authoring-standard and ledger-integrity checks remain gated.

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

[^9]: `docs-site/astro.config.ts`: `redirects` and the CLI sidebar group;
    `guides/_shared/how-to/install-agentbundle.md`, `install-packs.md`,
    `configure-agentbundle.md`, and `upgrade-packs.md`; guide alias projection
    in `tools/build-site.py`.

[^10]: Historical plan evidence at commit
    `58a22840a114a6e962d7a0cf84fd8c6f80aad777`, blob
    `95248de76903dfe346dbba9b369a2c0c404061e2`, Changelog entry dated
    2026-08-23. These Git object references remain usable after the delivery
    directory is removed.

## Build-contract migration and evidence limits

After the retired token-copy generator is removed, an old untracked
`docs-site/src/styles/tokens.css` must also be removed from a pre-existing
worktree: that stale file once made verification pass for the wrong reason.
The docs plugin tests require `npm ci --prefix docs-site`. Their Node execution
checks behavior; the build-contract delivery accepted missing `node:test` type
declarations and no docs-site CI typecheck. An editor or `astro check` complaint
is not evidence that those runtime assertions failed. Unit HAST fixtures still
need the emitted-page assertions because they can drift from real Starlight
output. The retained guide-image projection note owns the separate missing-image
work.

Docs-site overrides deliberately remain unlayered so they outrank Starlight's
layered styles. Print overrides keep that origin; adding a layer would lower
priority even when a selector has greater specificity. This is the CSS ownership
premise retained from the design refresh, not a claim of a new browser probe.

## Marketing press-state decisions

Press paints the actionable element, never a descendant label. It lands without
an ease-in; release can still ease under the base rule. Browser checks are needed
because inherited transitions can escape a static selector parser. The historical
2026-09-23 repair also reconciled rendered controls with the derived set and checked
that each press left the URL unchanged, after navigation had corrupted a measurement.

The chosen ground-shift idiom retains a dark-band exception and raises ink only
where the text contrast floor requires it, on both hovered and unhovered paths.
The warn-panel correction added a pressed foreground measured at 6.59:1; the paper
ground moved from record-200 to record-250 because record-200 duplicated existing
hover grounds. These are dated design measurements, not a new browser run.
Tight inline fill was accepted to retain the left alignment and single idiom;
adding horizontal padding or a second text-only idiom was declined. The loop-card
bar's recorded 2.33:1 against pressed ground versus 3.26:1 at rest was left as a
separate contrast question, not repaired by this change. Hover retuning and removal
of the unused PackCard stayed separate follow-ons.

## Link-repair causal limit

Authored link repairs must survive regeneration; editing only generated pages is
not durable. The historical marketing/docs incident attributed at most 11 of 37
reverted files to projection, disproved the stale-base explanation, and left the
other 26 unexplained. A projection guard therefore cannot be claimed to prevent
the whole recurrence. That repair deferred a committed checker and the frozen
phase-4b instruction repair; the current rendered-link checks and fallback-detector
owner must be assessed on their actual coverage. Site remounting and hard-coded
schema routing were declined as wider coupling, not established as necessary fixes.

## Visual inspection judgment boundary

Capture and judgment remain separable: images need state records, including scroll
position, before they can support a finding. At-rest top clipping is blocking;
an image without state cannot establish that case. Severity is derived from the
structured finding-class mapping, not chosen by the judge. A screenshot-difference
baseline was declined because a deliberate redesign is not itself a failure.

Keep five outcomes distinct from a completed inspection: no browser capability
(named skip), missing capture state (unusable and no finding), navigation failure,
capture failure and judgment failure. One unverified bucket would hide a recording
defect as an environment problem. The original delivery did not change the cost of
a skip at `accept-frontend-evidence`, and it did not claim screenshot-diff regression
coverage. The retained visual-inspection spec is a literal supersession-test input;
its ledger remains the measured procedure and guide-walk evidence, not fresh QA.

## Documentation migration scope

The Phase 4 pack rollout moved outcome-led entry points and journey sources;
it did not prove that every guide had frontmatter. Its missing-frontmatter warning
count was a historical inventory, and today's validator owns required fields.
Atomic-pack journey pages were retained to avoid breaking published `journeyUrl`
links until their replacement source existed. It also avoided rewriting already
outcome-led READMEs merely to match one pack's layout. A later migration must check
current links and sources rather than treating that staged rollout as authority
to delete pages or ignore present validator errors.

## Plugin discovery page choices

Derive install URLs from pack identity instead of maintaining per-content-file URL
fields. A linked card cannot contain a second interactive copy control; the plugin
listing uses its own install block rather than nesting controls inside the card's
anchor. Custom-protocol deep links were declined because an OS handler is an
additional product dependency. Existing layout and token reuse does not establish
client installation success; the distribution route owns that evidence.

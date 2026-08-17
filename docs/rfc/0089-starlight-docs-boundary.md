# RFC-0089: Starlight docs boundary

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-17
- **Date closed:** 2026-08-17
- **Decision weight:** heavy (ratifies a permanent top-level project and
  partially supersedes accepted ADR-0055; requires bounded de-risk evidence and
  explicit Approver sign-off)
- **Related:** [ADR-0055](../adr/0055-starlight-replaces-mkdocs-for-reference-docs.md),
  [RFC-0061](0061-web-top-level-directory.md),
  [`starlight-migration`](../specs/starlight-migration/spec.md),
  [`docs-site-design-refresh`](../specs/docs-site-design-refresh/spec.md),
  [`tech-site-completion`](../product/briefs/tech-site-completion.md)

## Reviewer brief

- **Decision:** Whether to ratify `docs-site/` as the permanent Starlight
  technical-docs project beside the already authorized `web/` marketing
  project.
- **Recommended outcome:** Accept.
- **Change if accepted:**
  - Record the current sibling-project ownership boundary.
  - Preserve renderer-specific visual and framework contracts.
  - Record the ordered, single-artifact build and combined verification seam.
- **Affected surface:** repository governance, `web/`, `docs-site/`,
  `guides/`, site generation, Pages deployment, and emitted-site checks.
- **Stakes:** The decision is easy to amend in documentation but costly to
  ignore once more tooling depends on an unnamed structural boundary.
- **Review focus:** Whether “standalone project” is clearly distinguished from
  “independent deployment,” and whether the RFC accidentally authorizes a
  redesign.
- **Not in scope:** Site implementation, new routes, palette alignment,
  dependency changes, content rewrites, or separate deployments.

## The ask

- **Recommendation (bottom line up front):** Ratify `docs-site/` as the
  permanent standalone Astro and Starlight project for technical
  documentation, sibling to the existing `web/` Astro marketing project. Keep
  their renderers independent but publish their output as one ordered,
  verified artifact.
- **Why now (situation–complication–question):** ADR-0055 selected Starlight and
  the migration has shipped. RFC-0061 authorized `web/`, but the permanent
  `docs-site/` top-level directory still lacks the equivalent structural
  record required by repository governance. The question is whether to ratify
  the shipped boundary as-is or reopen the site architecture.
- **Decisions requested:**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | What does `docs-site/` own? | The standalone Starlight technical-docs project; `web/` remains the separate marketing project | Names the existing renderer boundary without implying that one project contains the other | This review | Confirm the sibling-project boundary |
| D2 | What may the renderers share? | Ratify the later shipped docs refresh: share information architecture and generated content contracts, but not CSS, component implementations, palettes, or framework-native controls | The docs refresh deliberately replaced the migration's amber-token contract with a self-contained cobalt docs palette | This review | Confirm renderer autonomy and the explicit palette supersession |
| D3 | How are the projects built and deployed? | Generate shared content, build `web/` first, build `docs-site/` second, run combined emitted checks, and deploy one artifact | The marketing build cleans the artifact root; docs then writes beneath it | This review | Confirm the load-bearing order and single artifact |
| D4 | What does acceptance authorize? | Retrospective ratification of the shipped structural and palette boundaries, plus the follow-on governance records; no runtime implementation or redesign | Runtime changes belong to independently reviewed specs | This review | Confirm the governance-only scope and reject redesign or runtime implementation here |

## Problem & goals

### Diagnosis

The repository has two site renderers with distinct ownership. `web/` renders
the marketing home, catalogue, pack, journey, and work pages. `docs-site/`
renders the Starlight technical-documentation experience under the configured
`/docs/` path. Published adopter guides remain canonical under `guides/` and
are projected into Starlight by `tools/build-site.py`.

The implementation is already shipped, but its governance record is
asymmetric. RFC-0061 explicitly authorized the `web/` top-level directory.
ADR-0055 chose Starlight over the previous documentation renderer, but it did
not authorize the resulting permanent top-level project. Repository rules
require an RFC before a new top-level directory becomes permanent. Leaving the
gap open makes future work reconstruct whether `docs-site/` is temporary,
whether it contains the marketing site, and whether the two projects are meant
to converge.

The frozen migration record also preserves a decision that is no longer
current: ADR-0055's token-sharing rationale and the shipped migration spec's
amber-palette criteria describe the site at migration time. The later shipped
`docs-site-design-refresh` spec removed that import, established a
self-contained cobalt docs palette, and recorded the divergence in living
`docs-site/AGENTS.md`. D2 resolves that evidence-backed contradiction without
rewriting either frozen body.

### Goals

- Give `docs-site/` the missing structural authorization.
- State the ownership of `web/`, `docs-site/`, and `guides/` without ambiguity.
- Preserve the independent renderer and palette contracts already in force.
- Record the load-bearing build order and one-artifact deployment boundary.
- Give future site specs a stable governance constraint without repeating
  migration history.

### Non-goals

- Reconsidering Astro, Starlight, the project split, routes, or the completed
  migration mechanics; D2 reconciles only the later palette/token reversal.
- Moving marketing pages into `docs-site/` or technical docs into `web/`.
- Sharing CSS, components, color tokens, or a runtime package between sites.
- Aligning the docs palette with the marketing palette.
- Adding, removing, renaming, or moving routes or navigation destinations.
- Changing content, site chrome (headers, navigation, footers, and other
  surrounding interface), tests, workflows, dependencies, or deployment in
  this RFC.
- Creating a separate docs deployment, repository, domain, or artifact.

## Proposal

### Sibling project boundary

The repository keeps two sibling Astro projects:

| Project or source | Owns | Published outcome |
| --- | --- | --- |
| `web/` | Marketing shell, catalogue, pack, journey, and work renderers | The configured site root |
| `docs-site/` | Starlight configuration, docs components, docs styles, search/theme/sidebar integration, and documentation rendering | The configured `/docs/` subtree |
| `guides/` | Canonical adopter-facing guide content | Generated pages inside the docs subtree |
| `tools/build-site.py` | Deterministic projection of pack, journey, guide, and navigation inputs | Renderer inputs; it does not become a third renderer |

“Standalone” describes project and renderer ownership. It does not mean an
independent deployment. Neither Astro project imports the other's components
or styles, and neither owns the other's routes.

### Renderer autonomy

The marketing renderer keeps its platform design system. The documentation
renderer keeps its docs-specific palette and the pinned Starlight contracts
for title, search, theme control, sidebar, pagination, and supported override
seams. Shared product identity is expressed through approved information
architecture, destination vocabulary, and generated content data rather than
shared CSS or runtime components.

D2 deliberately supersedes only the palette/token-sharing part of ADR-0055
and the corresponding amber/token assertions in the frozen
`starlight-migration` spec. ADR-0055 remains authoritative for Starlight,
the sibling project boundary, the Node/Astro toolchain, and build order. On
RFC acceptance, a focused follow-on ADR records the renderer-local palette
decision; the earlier ADR and frozen spec then receive Status-only partial-
supersession pointers under `docs/CONVENTIONS.md`: metadata links naming the
superseding ADR and exact affected scope while leaving the frozen bodies
unchanged.

This boundary permits a future spec to project shared navigation data into two
renderer-local implementations. It does not permit that spec to align colors,
replace Starlight-native controls, or introduce a cross-renderer component
package.

### Ordered combined build

The current deployed contract is:

1. Project the journey inputs required by the marketing build.
2. Build `web/` into the artifact root. This render runs first because its
   Astro build cleans that root.
3. Aggregate the complete docs content required by Starlight.
4. Build `docs-site/` into the docs subtree of the same artifact.
5. Run the current combined rendered-link checker and rendered-output
   assertions against the completed artifact.
6. Upload and deploy the single Pages artifact.

A workflow or local command may package those steps differently, but it must
preserve their observable order and combined verification boundary. A site
cannot pass deployment merely because its source compiles in isolation.

Contrast, deterministic browser accessibility, the registered seven-test
construction group (the seven existing Python site-test modules enumerated by
the [`site-ci-contract-closure`](../specs/site-ci-contract-closure/spec.md)
spec), and additional route evidence are approved completion work, not claims
about current CI. They join the pre-upload combined gate only when that spec
and the
[`site-browser-quality-gate`](../specs/site-browser-quality-gate/spec.md)
ship.

### Existing-state treatment

Acceptance requires no runtime or directory migration. The projects,
configured output paths, palette implementation, and deployment shape already
exist. Governance completion does require the focused follow-on ADR and
Status-only partial-supersession pointers described under D2. Follow-on specs
may correct stale guidance, strengthen tests, or adapt chrome within this
RFC's boundaries, but they do not redesign the boundary.

## Options considered

The option axis is the degree of structural separation: leave the current
boundary unratified, ratify it, reduce separation by consolidation, or increase
separation through independent delivery. These choices exhaust the meaningful
governance outcomes for the shipped two-project state.

| Option | Trade-offs against the goals | Disposition |
| --- | --- | --- |
| Leave the current state unratified | No immediate file change, but every future session must infer whether `docs-site/` is temporary and the top-level-directory rule remains unsatisfied | Rejected: cost of delay is continuing governance ambiguity |
| Ratify sibling projects with one ordered artifact | Matches shipped behavior, preserves both reading modes, and requires no migration; retains two Node workspaces and their sequencing constraint | **Recommended** |
| Consolidate technical docs into `web/` | Creates one Astro project boundary, but reopens the shipped migration, risks replacing Starlight-native behavior, and couples visual systems without a user outcome | Rejected: contradicts settled decisions and expands scope |
| Split docs into an independent deployment or repository | Removes artifact-order coupling, but duplicates deployment governance, changes route/release contracts, and introduces coordination cost without demonstrated need | Rejected: increases operational surface without improving the accepted experience |

Starlight's documented project structure treats a Starlight site as an Astro
project with its own content and configuration. Astro exposes `base` and
`outDir` as project configuration, which supports the current nested output
without requiring renderer consolidation. GitHub Pages custom workflows deploy
an uploaded artifact, so a single artifact assembled from two ordered builds is
a supported delivery shape.

## Risks & what would make this wrong

### Pre-mortem

- **“Standalone” is read as “deploy separately.”** The proposal distinguishes
  project ownership from artifact ownership, and D3 makes one deployment
  explicit.
- **Renderer autonomy becomes an excuse for vocabulary drift.** Shared
  information architecture may be projected as data; only implementation and
  visual tokens remain renderer-local.
- **The build order changes silently.** Follow-on construction tests must fail
  when docs renders before the artifact-cleaning marketing render or when the
  current combined checks are omitted. Additional approved checks become part
  of that contract only when their owning specs ship.
- **Framework internals drift under the pinned version.** The docs project keeps
  its documented Starlight touchpoints and must reverify them on any later
  upgrade; this RFC does not authorize an upgrade.

### Key assumptions

- The marketing build continues to clean the shared artifact root. If it stops,
  the order may become simplifiable, but combined emitted verification remains
  necessary.
- Starlight continues to own docs search, theme, sidebar, and pagination. A
  future accepted framework migration would supersede this renderer boundary.
- One deployment remains the route and release contract. A demonstrated need
  for independent release cadence or ownership would justify reopening D3.
- Shared information architecture can remain renderer-neutral data. If a
  second concrete consumer proves that data projection cannot preserve
  behavior, the boundary should be revisited rather than bypassed.

### Drawbacks

The repository retains two Node workspaces, two renderer configurations, and
some unavoidable duplication in accessible chrome implementation. The build is
sequential because one project owns the artifact root cleanup. Contributors
must understand both a project boundary and a combined deployment boundary.
Those costs are accepted because consolidation would trade explicit build
coupling for deeper framework and design coupling.

## Evidence & prior art

### De-risk result

The load-bearing local routing and rendering contracts were exercised before
this draft:

```text
python3 -m pytest -p no:cacheprovider \
  tools/test_build_site_routing.py \
  tools/test_build_site_link_rewrites.py \
  tools/test_check_rendered_site_links.py -q

37 passed in 11.64s
```

This proves the current routing, rewrite, and combined link-check contracts are
coherent. It does not prove browser presentation or physical-device behavior;
those remain follow-on verification work.

The Approver confirmed D2-D4, then clarified and confirmed D1, before this
draft was written. That confirmation establishes the proposal direction; it
does not substitute for explicit acceptance of this heavy RFC after its
adversarial and cold-reader gates complete.

### Repository precedent

- [ADR-0055](../adr/0055-starlight-replaces-mkdocs-for-reference-docs.md)
  selects Starlight for technical documentation and records the project/build
  boundary; its palette/token rationale is the narrow part D2 supersedes.
- [RFC-0061](0061-web-top-level-directory.md) authorizes the sibling marketing
  project and establishes the precedent for explicit top-level site approval.
- The shipped [`starlight-migration`](../specs/starlight-migration/spec.md)
  records the migration-time amber/token acceptance contract as frozen
  history.
- The shipped
  [`docs-site-design-refresh`](../specs/docs-site-design-refresh/spec.md)
  removed the token import and established the current self-contained cobalt
  palette in acceptance criteria 5 and 6.
- [`docs-site/AGENTS.md`](../../docs-site/AGENTS.md) owns the current palette,
  pinned framework touchpoints, and canonical build-order guidance.
- [`.github/workflows/pages.yml`](../../.github/workflows/pages.yml) implements
  the current ordered single-artifact deployment.

### External prior art

- [Starlight project structure](https://starlight.astro.build/guides/project-structure/)
  documents a Starlight site as an Astro project with project-local content and
  configuration.
- [Astro configuration](https://docs.astro.build/en/reference/configuration-reference/)
  documents the `base` and `outDir` boundaries used to place a project beneath
  a deployment base and into a selected output directory.
- [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
  documents uploading a prepared artifact and deploying it in a later job,
  consistent with assembling both renderers before deployment.

## Open questions

None. D1-D4 reflect stakeholder-confirmed pre-draft direction from 2026-08-17;
formal governance ratification occurs only if this RFC is accepted.

## Follow-on artifacts

- ADR: [ADR-0085](../adr/0085-docs-rendering-is-site-local.md) records that
  docs palette and renderer implementation are site-local and supersedes the
  token-sharing part of ADR-0055.
- Spec: [`site-contract-provenance-cleanup`](../specs/site-contract-provenance-cleanup/spec.md)
  applies Status-only partial-supersession pointers to ADR-0055 and the frozen
  `starlight-migration` spec after that ADR exists.
- Spec: [`docs-site-build-contract-hardening`](../specs/docs-site-build-contract-hardening/spec.md)
- Spec: [`site-ci-contract-closure`](../specs/site-ci-contract-closure/spec.md)
  adds the seven existing site-test modules and docs contrast checker to
  required CI after the current build boundary.
- Related independent specs:
  [`site-shared-chrome`](../specs/site-shared-chrome/spec.md) and
  [`site-browser-quality-gate`](../specs/site-browser-quality-gate/spec.md)

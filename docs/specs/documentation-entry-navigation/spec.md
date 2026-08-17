# Spec: documentation-entry-navigation

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** [RFC-0076 D9–D10](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md), [`docs-site-design-refresh`](../docs-site-design-refresh/spec.md), [`platform-site`](../platform-site/spec.md)
- **Supersedes:** [`catalogue-wave8-readme-contributing`](../catalogue-wave8-readme-contributing/spec.md)
- **Precedes:** ini-007 Wave 6–7; this spec delivers their current-route editorial and navigation foundation while preserving their Wave 4/index-dependent work
- **Brief:** none
- **Discovery:** [`notes/information-architecture.md`](notes/information-architecture.md)
- **Contract:** none
- **Shape:** cross-surface documentation and navigation retrofit

> **Spec contract:** this document defines what “done” means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

Mode: full. The change restructures public entry points across the repository,
marketing site, and technical documentation site.

## Objective

Turn the repository README into a concise hub-and-spoke router while preserving
the information adopters need in canonical public destinations.

The catalogue is the product. Packs are its composable units, profiles are
curated starting sets, `agentbundle` distributes them, and this repository is a
self-hosted example of the model. The supervised `core` build loop is the
flagship and strongest standalone reason to adopt, but no entry surface may
imply that software implementation is the catalogue's only use.

A product manager must be able to recognize the strategy, research, and product
shaping path. A platform, infrastructure, or SRE team must be able to recognize
the architecture, contract, infrastructure-as-code, and release path. Engineers,
designers, researchers, catalogue operators, and coding agents must retain
predictable routes into the same inventory.

The public surfaces have one job each:

| Surface | Job |
| --- | --- |
| Marketing site | Create recognition through outcomes, proof, and the self-hosted catalogue story |
| Catalogue | Help readers choose from the complete pack inventory |
| Technical docs | Help adopters install, use, operate, and build catalogues |
| `guides/` | Hold canonical adopter-facing tutorials, how-tos, reference, and explanation |
| GitHub README | Identify the product and route readers to the right public or contributor surface |
| Contributor pages | Explain source ownership, contracts, architecture, and repository procedure |

## Approved assumptions

- **Product:** the catalogue and its self-hosting system are the product;
  `core` is the differentiated flagship product rather than the catalogue
  taxonomy. Public copy leads with its verifiable mechanics and then reveals
  catalogue breadth without an unsupported comparative superlative.
- **Audience:** role and arrival pathway are orthogonal. Public discovery leads
  with recognizable work, then reveals pack names and installation details.
- **Content:** a fact is authored once. Other surfaces summarize and link; they
  do not grow parallel handbooks or hand-maintained complete inventories.
- **Navigation:** the first implementation uses current routes and anchors. It
  does not add `/evaluate/`, a separate role-page hierarchy, or new top-level
  directories. The `/evaluate/` route, neutral-index consumption, generated
  field reference, and pack-integration relationship view remain owned by
  ini-007 Waves 6–7 after Wave 4 ships.
- **Guides:** `guides/` remains portable public source mirrored into the docs
  site. Physically adding the full tree to packaged catalogue archives is a
  separate `agentbundle` backlog item, not an implied part of this change.
- **Scope:** content removed from the README must be strengthened at its
  canonical destination in this same change. Marketing, technical docs,
  adopter guides, contributor docs, and internal navigation are in scope where
  the migration requires them.
- **Approval:** the user approved this direction and expanded scope on
  2026-08-12.

## Content migration contract

No README section is removed on the strength of a link alone. The destination
must contain the information an adopter needs to continue.

| README content being reduced | Canonical destination | Destination requirement |
| --- | --- | --- |
| Product argument and testimonial | Marketing home | State the supervised operating-model problem and sell the flagship through its verifiable mechanics without relying on the testimonial |
| Detailed discovery/build/release explanation | [`guides/_shared/explanation/the-three-loops.md`](../../../guides/_shared/explanation/the-three-loops.md) and the marketing “How it works” section | Name each loop, its output, handoff, and human gate |
| Curated pack table and pack descriptions | Marketing catalogue and generated technical pack index | Preserve the complete current inventory and expose outcome-first discovery before pack metadata |
| Role routing | Marketing catalogue, docs landing, and `guides/README.md` | Product management and infrastructure routes must be explicit; other primary roles remain findable |
| Install alternatives, adapter details, profiles, upgrades, and dry-run | Technical getting-started and shared install/reference guides | Preserve one clear first install plus routes to alternative installs, adapter support, profiles, preview, and upgrade |
| Catalogue composition and self-hosting | Marketing “Build your organisation” section, docs landing, and pack-catalogue explanation | Explain packs, profiles, adapters, ownership, `catalogue init`, and the no-fork starting path |
| Files-you-own and ecosystem mechanics | Pack-catalogue and file-safety explanations plus architecture links | Preserve editability, adapter projection, non-clobbering composition, and credential-safety routes without duplicating package internals in the README |
| Contribution procedures | `CONTRIBUTING.md`, `packs/README.md`, and contracts | Remove the obsolete requirement to update a README pack table; retain portable authoring and contract routes |

## Boundaries

### Always do

- Keep the root README at or below 90 lines.
- Keep the flagship build-loop quickstart visible without presenting it as the
  complete catalogue; sell its spec, gate, cold-review, stasis, and human-decision
  mechanics as product strengths rather than describing it as a disposable demo.
- Preserve one-click routes from the README to marketing discovery, technical
  getting started, the complete catalogue, catalogue authoring, and contributing.
- Put product-manager and infrastructure/platform outcomes in first-screen or
  first-section discovery on the marketing catalogue, technical docs landing,
  and guide hub.
- Keep the complete pack grid data-driven from the existing content collection.
- Verify every new internal link target exists.
- Preserve the existing visual system, responsive behavior, focus behavior,
  reduced-motion behavior, and page routes.
- Update the old Wave 8 spec and workspace routing so this spec owns the
  current-route work while the Wave 4/index-dependent remainder stays visible
  under Waves 6–7.

### Ask first

- Adding a new top-level route or directory.
- Changing the guide tree's catalogue-package distribution behavior.
- Editing `packs/README.md`, `profiles/README.md`, or their projected authoring
  scaffold copies; those changes carry an `agentbundle` release implication.
- Introducing search/filter JavaScript, a new dependency, a schema change, or a
  design-token/styling-system change.
- Rewriting individual pack READMEs, pack journeys, or the complete guide corpus.

### Never do

- Delete public information without satisfying the destination requirement in
  the migration contract.
- Hand-maintain a complete pack inventory in the root README, guide root, docs
  landing, or marketing homepage.
- Edit generated guide navigation, generated pack pages, projected adapter
  outputs, or generated site content directly.
- Claim the full `guides/` tree ships in a packaged catalogue archive.
- Restore adopt-by-forking language; `agentbundle catalogue init` is the clean
  starting route.
- Turn install scope, adapter support, skill count, or pack names into the
  first-level discovery taxonomy.

## Acceptance Criteria

- [x] **AC1 — README is a router.** `README.md` is at most 90 lines and contains:
  one product definition; one compact flagship case; one supported quickstart;
  routes to outcome discovery, technical getting started, complete catalogue,
  catalogue authoring, architecture/contracts, contributing, security, and
  license; and a short composable/self-hosted catalogue explanation.
- [x] **AC2 — README duplication is removed.** `README.md` contains no
  testimonial, full three-loop walkthrough, pack table, multi-route CLI manual,
  adapter matrix, profiles tutorial, package ecosystem tour, or instruction to
  fork the repository to adopt it.
- [x] **AC3 — README cuts have complete destinations.** Every row in the content
  migration contract is checked after implementation. The named destination
  contains the required substance and its route from the README or an immediate
  hub resolves.
- [x] **AC4 — marketing broadens immediately after the hook.** The marketing
  homepage leads with supervised build work as the differentiated flagship, then presents
  outcome paths for deciding what to build, designing a product/system, building
  and reviewing software, provisioning and releasing safely, working with team
  systems/evidence, documenting what ships, and building/governing a catalogue.
- [x] **AC5 — marketing navigation matches reader intent.** Primary navigation
  includes “Use cases,” Catalogue, Docs, and a supervised-loop CTA.
  Journeys remain reachable from pack and loop context but are not a primary
  navigation category.
- [x] **AC6 — self-hosting is first-class and current.** The marketing closer
  and docs landing explain how an organization initializes, adapts, validates,
  and distributes its own catalogue. Neither tells readers to fork this repo.
- [x] **AC7 — catalogue discovery precedes inventory.** `/catalogue/` presents
  outcome and role routes before the complete data-driven pack grid. Product
  manager/strategist and infrastructure/platform/SRE routes are explicit. The
  grid retains every pack supplied by the existing content collection and keeps
  install metadata at the detail layer.
- [x] **AC8 — docs landing separates use from build.** The technical docs home
  provides: outcome-first task routes; role shortcuts; a “use a catalogue” path;
  a “build and operate a catalogue” path; getting-started and reference routes;
  and no hand-maintained complete pack table.
- [x] **AC9 — getting started supports more than engineers.** The technical
  getting-started page retains the flagship loop and adds recognizable starting
  paths for product work and infrastructure/release work, with appropriate pack
  or profile commands and human-boundary language.
- [x] **AC10 — guide root is a portable hub.** `guides/README.md` routes by
  outcome, includes role shortcuts, explains shared versus pack-specific
  guidance, links the complete generated catalogue, and points once to the
  guide-authoring contract. It links every active pack home without a prose
  catalogue duplicated from every pack and has no long embedded authoring
  manual. `tools/check-guide-index.py` verifies link coverage without requiring
  an “All packs” section or a particular presentation.
- [x] **AC11 — removed deep explanations remain public.** The shared three-loop,
  pack-catalogue, install-route, adapter-support, profile-install, preview, and
  upgrade pages are reachable from the docs landing, getting-started page, or
  guide hub as appropriate.
- [x] **AC12 — contributor navigation converges.** `CONTRIBUTING.md` points to
  the portable catalogue authoring standards, documents optional
  `[[pack.integrations]]` navigation, adds catalogue authoring to the authority
  table, and replaces the obsolete “update the README Packs table” instruction
  with the real data/guide/site registration sources. It routes contributors
  through the public technical docs and explains the evidence → decision → spec
  → implementation → adopter-doc chain without duplicating the source-of-truth
  hierarchy.
- [x] **AC13 — ownership is explicit without losing future work.** The old Wave
  8 spec is Archived with a `Superseded by` link. ini-007 points Wave 9's former
  Wave 8 dependency to this spec. Waves 6 and 7 remain queued, but their comments
  name only the work this spec does not deliver: neutral-index and generated
  reference consumption, the deep “Build a Catalogue” sidebar/reference
  structure, `/evaluate/`, and pack-integration relationship presentation.
- [x] **AC14 — no route or design-system expansion.** No new top-level route,
  dependency, token, schema, pack payload, generated output, or packaging
  behavior is introduced.
- [x] **AC15 — feasible verification passes.** Static construction checks,
  guide validation/index checks, site routing tests, formatting/lint checks that
  do not require generated writes, and `git diff --check` pass. Build and
  tempfile-dependent gates are reported as environment-blocked rather than
  represented as passed.

## Testing strategy

- **Structure:** line-count and negative-content checks on `README.md`; heading,
  label, and route checks on the two site entry points and guide hub.
- **Inventory:** construction check that the marketing catalogue still maps the
  full `astro:content` pack collection rather than a hard-coded subset.
- **Links:** extract changed Markdown links and site route/anchor targets; verify
  local targets and existing public route sources.
- **Guides:** run `tools/validate_guides.py` and `tools/check-guide-index.py` if
  they complete without creating temporary output.
- **Sites:** run read-only routing/construction tests. Site sync/build commands
  are blocked in this workspace because generated-output directories are not
  writable; record that limitation and provide only the smallest final manual
  verification set.
- **Review:** adversarial review checks spec-to-content drift and missing
  audience paths; quality review checks maintainability, duplicated ownership,
  link durability, and test shape.

## Completion signal

A cold reader can answer, within two navigation actions:

1. What is this product?
2. What can it do for my role or outcome?
3. Which pack or profile should I start with?
4. How do I install and verify it?
5. How does my organization own and self-host the system?
6. Where do I contribute to the catalogue implementation?

The README is no longer required to answer all six itself.

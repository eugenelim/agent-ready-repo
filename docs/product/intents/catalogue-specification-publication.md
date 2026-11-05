# Publish a versioned agentbundle catalogue specification

- **Slug:** `catalogue-specification-publication`
- **Status:** Fulfilled
- **Accepted:** 2026-10-21 by eugenelim, lifecycle owner. Basis: explicit owner direction to accept; RFC-0109 governs the intent, and intent-mode review of this revision produced no malformed findings.
- **Fulfilled:** 2026-11-04 eugenelim, lifecycle owner: the one delivery brief, [`catalogue-specification-publication-delivery`](../briefs/catalogue-specification-publication-delivery.md), is Shipped and maps the four slice specs, all Shipped, per close-work's closure check (`all-descendants-terminal`, terminus `brief`). Evidence reviewed: `contracts/catalogue-spec.toml` holds 10 member, 9 bundled and 2 vendored rows and one `[[release]]` `0.1` dated 2026-10-23 with adapter contract `0.18`; `contracts/catalogue-manifest.schema.json` and the frozen `contracts/releases/catalogue/0.1/` snapshot exist; `check_contract_parity.py`, `check_spec_version.py` and `check_release_gate.py` pass, the last confirming the deployed index serves release `0.1`; [`docs/architecture/catalogue/specification.md`](../../architecture/catalogue/specification.md) records the delivered shape. The capability-placement question stays open and does not gate closure.
- **Nonmaterial correction 2026-11-04 by eugenelim, lifecycle owner.** The Decomposition section names the four shipped slice specs and the Sidebar placement question links its recorded settlement. Both are evidence-link corrections: no opportunity, outcome, boundary, owner, assumption, or projection changed, so the prior review evidence stands.
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Shaping-reviewed:** 2026-10-21
- **Decomposed:** 2026-11-04 brief
- **Governed by:** [RFC-0109](../../rfc/0109-catalogue-specification-publication.md)

## Outcome

- **Input (steerable):** The share of contracts an adopter needs to build their own catalogue that have a published, versioned specification page and a schema served at a stable site URL.
- **Outcome (lagging):** An adopter can set up and validate their own agentbundle catalogue from the published specification alone, without reading this repository's `contracts/` folder or telling catalogue contracts apart from work-loop and delivery contracts.
- **Guardrail:** The published specification never drifts from the contracts the `agentbundle` CLI enforces. `contracts/` stays the one authored source, and the CLI's bundled copies stay byte-identical.

## Opportunity

Every platform an adopter builds on publishes its specification on its website, with a version and a stable address. Here, the catalogue contracts are files in a mixed folder that an adopter must find, sort, and pin by Git revision.

- **Functional job:** Find the exact set of formats and schemas a catalogue must satisfy, at a named version, and point tools and CI at them.
- **Emotional job:** Trust that the specification is complete and current, and that following it produces a catalogue the CLI accepts.
- **Social job:** Show reviewers and other implementers a public, versioned standard rather than a path inside someone else's repository.
- **Struggling moment:** An adopter opening `contracts/` sees 61 schemas. Catalogue authoring, work-loop records, delivery-engine records, and CLI output all sit side by side, nothing marks which ones a catalogue needs, and no schema resolves at a real URL.

## Boundary

This intent owns publishing the catalogue specification: which contracts belong to it, its version, its human-readable pages, and the stable URLs its schemas are served at. It does not own the meaning of any contract; each contract's owning spec keeps that.

[RFC-0109](../../rfc/0109-catalogue-specification-publication.md) governs this intent. It records its amendments in [RFC-0003](../../rfc/0003-spec-and-cli.md) § Amendments and in [RFC-0076](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md) § Errata, and decides:

- **Membership (D1):** 10 members, declared in one manifest, `contracts/catalogue-spec.toml`. That manifest also drives the CLI's `_data/` copies and `public-contracts.txt`. Host projections, engine settings, and other records are not members.
- **Home (D2):** a `/docs/spec/catalogue/` section of the docs site. The marketing site links to it and carries no schema pages.
- **URLs and versions (D3):** an immutable `<MAJOR.MINOR>/` path per release on the existing site host, starting at `0.1`. Each member's `$id` equals its served URL. `latest/` and `draft/` are aliases, not identities.
- **Files on disk (D4):** contracts stay where they are, and the manifest does the separating.
- **Archive manifest (D5):** a new member, `contracts/catalogue-manifest.schema.json`.
- **Pages (D6):** a generated field table per member, plus short narrative pages that link to fields and never define them.
- **Drift (D7):** four CI checks, including a gate at CLI release time.

Work-loop, delivery, and workspace contracts stay unpublished here. [`catalogue-wave7-marketing-evaluator`](catalogue-wave7-marketing-evaluator.md) owns the evaluator page that links into this specification. [`catalogue-wave6-technical-docs-ia`](catalogue-wave6-technical-docs-ia.md) owns the Build a Catalogue guide route.

## Current evidence — 2026-10-21

- `contracts/` holds 61 schemas outside `vendor/`:
  - 13 at the top level, mostly catalogue authoring.
  - 18 under `jsonschema/`, mostly work-loop, workspace, and work-intake records, plus `agentbundle-show` output.
  - 30 under `delivery/`, all delivery-engine records.
- Of those schemas, 32 use an `$id` on the reserved `agent-ready-repo.invalid` host and 16 use `agent-ready-repo.example`. The rest have a bare filename or no `$id`. The core catalogue schemas (`pack`, `catalogue`, `profile`, `skill`, `skill-manifest`, `catalogue-index`) use bare filenames. No schema resolves at a real address.
- RFC-0109 was accepted on 2026-10-21 and merged in PR #1592 (`99dafc6ef`).
- The site is served at `https://eugenelim.github.io/agent-ready-repo`. Neither `web/` nor `docs-site/` publishes a contract page; links to contracts fall back to GitHub file views.
- [`contracts/README.md`](../../../contracts/README.md) calls these files "the published interface this catalogue exposes". It lists every contract in one table with no domain grouping.
- The CLI bundles 18 contracts listed in `packages/agentbundle/agentbundle/_data/public-contracts.txt`. That list is the closest thing to a catalogue set today, and it still includes the work-loop `knowledge-captured-observation` schema.
- Only `adapter.toml` carries a contract version (`0.18`), as [RFC-0003](../../rfc/0003-spec-and-cli.md) § Spec versioning defines. The catalogue set as a whole has no version.
- `catalogue-manifest.json`, the release archive manifest that adopters verify, has no schema in `contracts/`. Its shape is documented only in [`catalogue-archive.md`](../../guides/reference/catalogue-archive.md).

## Assumptions

- RFC-0109 D1's membership rule draws a set an adopter can work from: what a catalogue author writes, what `agentbundle` gives adopters to consume, and the adapter contract.
- The CLI's bundled copies and `agentbundle catalogue contracts` serve the same versioned set the site publishes, because one manifest drives both.
- Real `$id` URLs can be adopted without breaking existing adopters' validation, because current IDs resolve nowhere and tools resolve them locally.
- **Knowledge surface:** the in-repository contracts, CLI data directory, RFC-0003, RFC-0076, site configuration, and product-intent corpus and RFC-0109 with its desk-research survey, at revision `99dafc6efb608f4856cc7ec311ec554959f271bf`. No external knowledge surface was used.

## Riskiest assumption

**An adopter can build and validate a working catalogue from a published, versioned catalogue specification without reading repository internals.** If the published set leaves out something the CLI enforces, adopters fall back to `contracts/` and the outcome fails. RFC-0109 is accepted, so de-risking against its slices is the next shaping step.

## Non-goals

- Publishing work-loop, delivery, workspace, or work-intake contracts.
- Changing what any contract means.
- Moving the specification to a sibling repository or neutral organisation (RFC-0109 non-goal).
- Building the evaluator page or the Build a Catalogue guide route.

## Open questions

- **Capability placement:** this intent serves both the *judge* and *learn* clauses of [CAP-0006](CAP-0006-catalogue-trust-and-adoption.md), which already have owners. Following CAP-0006's own rule, it stays unparented until the owner places it. Decider: the owner.
- **Sidebar placement:** RFC-0109 OQ1 owns whether the spec section gets its own docs sidebar tab or sits inside Build a Catalogue. Evidence: [`catalogue-spec-site`](../../specs/catalogue-spec-site/spec.md) records the placement under the RFC-0109 Errata.

## Decomposition

Four specs, one per slice RFC-0109 D8 names, mapped by the retrospective delivery brief [`catalogue-specification-publication-delivery`](../briefs/catalogue-specification-publication-delivery.md). The brief exists because the delivery resolver maps a single-spec intent to exactly one spec and reports four as a projection mismatch:

- **S1** — [`catalogue-spec-manifest`](../../specs/catalogue-spec-manifest/spec.md): the membership manifest and bundled-only contract loading.
- **S2** — [`catalogue-manifest-schema`](../../specs/catalogue-manifest-schema/spec.md): the schema for the release archive manifest.
- **S3** — [`catalogue-spec-site`](../../specs/catalogue-spec-site/spec.md): the `draft/` site section.
- **S4** — [`catalogue-spec-release`](../../specs/catalogue-spec-release/spec.md): the one-way release 0.1.

## Source

- Mode: chat-only
- Locator: conversation/catalogue-specification-publication
- Revision: 2026-10-21
- Authority: transferred-to-repository

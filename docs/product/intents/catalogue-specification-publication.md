# Publish a versioned agentbundle catalogue specification

- **Slug:** `catalogue-specification-publication`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **Shaping-reviewed:** 2026-10-21

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

This intent cannot be decided under current governance:

- [RFC-0003](../../rfc/0003-spec-and-cli.md) makes the GitHub file path the canonical spec home for v0.x.
- RFC-0076 D9 assigns the contract reference to the docs site, and D10 keeps schemas off the marketing site. See [RFC-0076](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md).

An RFC that amends both sets the publication home, the URL scheme, and whether files move on disk. This intent is shaped against that RFC and is not de-risked until it is accepted.

Work-loop, delivery, and workspace contracts stay unpublished here. [`catalogue-wave7-marketing-evaluator`](catalogue-wave7-marketing-evaluator.md) owns the evaluator page that links into this specification. [`catalogue-wave6-technical-docs-ia`](catalogue-wave6-technical-docs-ia.md) owns the Build a Catalogue guide route.

## Current evidence — 2026-10-21

- `contracts/` holds 61 schemas outside `vendor/`:
  - 13 at the top level, mostly catalogue authoring.
  - 18 under `jsonschema/`, mostly work-loop, workspace, and work-intake records, plus `agentbundle-show` output.
  - 30 under `delivery/`, all delivery-engine records.
- Of those schemas, 32 use an `$id` on the reserved `agent-ready-repo.invalid` host and 16 use `agent-ready-repo.example`. The rest have a bare filename or no `$id`. The core catalogue schemas (`pack`, `catalogue`, `profile`, `skill`, `skill-manifest`, `catalogue-index`) use bare filenames. No schema resolves at a real address.
- The site is served at `https://eugenelim.github.io/agent-ready-repo`. Neither `web/` nor `docs-site/` publishes a contract page; links to contracts fall back to GitHub file views.
- [`contracts/README.md`](../../../contracts/README.md) calls these files "the published interface this catalogue exposes". It lists every contract in one table with no domain grouping.
- The CLI bundles 18 contracts listed in `packages/agentbundle/agentbundle/_data/public-contracts.txt`. That list is the closest thing to a catalogue set today, and it still includes the work-loop `knowledge-captured-observation` schema.
- Only `adapter.toml` carries a contract version (`0.18`), as [RFC-0003](../../rfc/0003-spec-and-cli.md) § Spec versioning defines. The catalogue set as a whole has no version.
- `catalogue-manifest.json`, the release archive manifest that adopters verify, has no schema in `contracts/`. Its shape is documented only in [`catalogue-archive.md`](../../guides/reference/catalogue-archive.md).

## Assumptions

- The catalogue set can be drawn by audience: pack, catalogue, profile, skill, skill manifest, catalogue index, adapter, and release archive manifest, with the RFC settling the edge cases such as marketplace, plugin-manifest, distribution-route, and OKF contracts.
- The CLI's bundled copies and `agentbundle catalogue contracts` can serve the same versioned set the site publishes, so one list defines the specification.
- Real `$id` URLs can be adopted without breaking existing adopters' validation, because current IDs resolve nowhere and tools resolve them locally.
- **Knowledge surface:** the in-repository contracts, CLI data directory, RFC-0003, RFC-0076, site configuration, and product-intent corpus at revision `3cc898b991df987b8ef8e515c6457a9ae8e5b501`. No external knowledge surface was used.

## Riskiest assumption

**An adopter can build and validate a working catalogue from a published, versioned catalogue specification without reading repository internals.** If the published set leaves out something the CLI enforces, adopters fall back to `contracts/` and the outcome fails. De-risking runs after the governing RFC is accepted.

## Non-goals

- Publishing work-loop, delivery, workspace, or work-intake contracts.
- Changing what any contract means.
- Moving the specification to a sibling repository or neutral organisation, which RFC-0003 reserves for v1.0.
- Building the evaluator page or the Build a Catalogue guide route.

## Open questions

- **Governing RFC:** the RFC must amend RFC-0003's spec home and RFC-0076 D9 and D10. It sets the site location, URL and version scheme, and whether contracts move on disk. Decider: the owner, through `new-rfc`.
- **Capability placement:** this intent serves both the *judge* and *learn* clauses of [CAP-0006](CAP-0006-catalogue-trust-and-adoption.md), which already have owners. Following CAP-0006's own rule, it stays unparented until the owner places it. Decider: the owner.
- **Archive manifest schema:** whether the specification adds a schema for `catalogue-manifest.json` or publishes its prose contract. Decider: the RFC.

## Decomposition

None yet.

## Source

- Mode: chat-only
- Locator: conversation/catalogue-specification-publication
- Revision: 2026-10-21
- Authority: transferred-to-repository

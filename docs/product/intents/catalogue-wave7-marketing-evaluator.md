# Catalogue marketing evaluator surface

- **Slug:** `catalogue-wave7-marketing-evaluator`
- **Status:** Accepted
- **Accepted:** 2026-10-21 by eugenelim, lifecycle owner. Basis: explicit owner direction to accept; the recorded de-risking verdict is re-sequenced behind RFC-0109 slice S4, and intent-mode review of this revision produced no malformed findings.
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **De-risked:** 2026-10-21
- **Shaping-reviewed:** 2026-10-21
- **Decomposed:** no
- **Parent intent:** capability:catalogue-trust-and-adoption
- **Governed by:** [RFC-0076 D10](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md), as amended by [RFC-0109](../../rfc/0109-catalogue-specification-publication.md)

## Outcome

- **Input (steerable):** The share of the nine RFC-0076 D10 claims on `/evaluate/` that link straight to a shipped public evidence page, and the share of facts on the catalogue and pack pages that come from `catalogue-index.json` rather than hand-written page data.
- **Outcome (lagging):** A platform lead who is deciding whether their organisation should build and own a catalogue on agentbundle can make that call from the marketing site and follow each claim to its proof without asking a maintainer.
- **Guardrail:** No claim says more than its evidence proves. For example, a unit digest proves that an archive agrees with its own manifest, not who published it. Pack pages show no fact the neutral index does not carry. The existing `/catalogue/` and `/packs/<pack>/` routes, plugin install offers, and scope parity keep working, and the visual system is not redesigned.

## Opportunity

A platform lead who meets the marketing site today sees a list of packs and their skills, but nothing that answers the questions they must settle before committing an organisation: can we own the source, can we check it, can we release it safely, and what does it run on.

- **Functional job:** Judge whether the catalogue model fits the organisation — open formats, versioned contracts, checks that run the same way every time, human approval points, source ownership, multi-tool projection, release integrity, and optional composition — and find the proof for each.
- **Emotional job:** Feel that the decision rests on facts that can be checked, not on marketing that may be out of date.
- **Social job:** Hand a budget holder or security reviewer a page where every claim links to the contract, command, or guide that enforces it.
- **Struggling moment:** The facts exist, but they are spread across technical guides, release references, and a `contracts/` folder that mixes catalogue, work-loop, and delivery schemas with no published specification. The marketing pages show none of version, adapters, or composition, and no page is written for someone evaluating the catalogue as a platform.

## Boundary

This intent owns three things on the marketing site in `web/`: a new `/evaluate/` page, index-backed facts on the catalogue and pack pages, and a relationship view of optional pack integrations using the RFC-0076 D6 labels. It links to evidence and does not restate contracts.

The versioned catalogue specification that `/evaluate/` links to belongs to [`catalogue-specification-publication`](catalogue-specification-publication.md). This page explains and links; it does not publish contracts itself. [RFC-0109](../../rfc/0109-catalogue-specification-publication.md) D2 places that specification at `/docs/spec/catalogue/` on the docs site, and the marketing site stays free of schema pages.

Other owners keep the rest. The Build a Catalogue documentation route belongs to [`catalogue-wave6-technical-docs-ia`](catalogue-wave6-technical-docs-ia.md). Release-integrity behaviour belongs to [`catalogue-wave5-release-integrity`](catalogue-wave5-release-integrity.md). Finding packs by query belongs to [`catalogue-search-verb`](catalogue-search-verb.md). The marketing home page and its adoption-champion journey belong to [`team-orientation-future-state`](../../design/journeys/team-orientation-future-state.md). Any new pack `lifecycle` field is a contract change outside this intent.

## Current evidence — 2026-10-21

### What shipped and what D10 now reads as

- Wave 5 shipped on 2026-10-21 in PR #1587 (merge `d714ab829`, agentbundle 0.53.0). It adds per-pack and per-profile SHA-256 digests to `catalogue-manifest.json`, refuses with exit 2 to package an existing release unless `--force` is passed, and adds `catalogue package --compare <prior archive>` with table or `--format json` output. See [the Wave 5 spec](../../specs/catalogue-wave5-release-integrity/spec.md).
- These release facts are published in [`catalogue-ci-contract.md`](../../../guides/_shared/reference/catalogue-ci-contract.md). [`catalogue-archive.md`](../../guides/reference/catalogue-archive.md) states that a unit digest shows agreement with the archive's own `files[]` and does not show who published it.
- RFC-0076 § Errata now records that D10's "Wave 8, after D8 ships" is stale, because D8 shipped as Wave 5. It also records RFC-0109's D10 amendment: the "Versioned contracts" and "Links to technical evidence" claims link to the published specification instead of the `contracts/` folder. D10 also says optional composition waits for D6; D6 shipped in [Wave 2](../../specs/catalogue-wave2-pack-integrations/spec.md).

### What the neutral index carries

- The neutral index shipped in [Wave 4](../../specs/catalogue-wave4-semantic-contracts-index/spec.md): `agentbundle catalogue index` writes `catalogue-index.json` against [`catalogue-index.schema.json`](../../../contracts/catalogue-index.schema.json).
- Running the index over this repository at revision `3cc898b9` gives 23 packs and 3 profiles. All 23 packs carry `version`, `scope`, `adapters`, `description`, and `digest`.
- Documentation links are on 15 of 23 packs. They come only from `JOURNEY.md` `docsUrl`, so 8 packs have none in the index.
- Optional integrations appear on 5 packs as 16 edges, and inverse integrations on 6 packs. Their kinds are `input`, `augment`, `review`, and `handoff`, which map to the D6 labels Accepts input from, Works with, Optional reviewers, and Hands off to.
- No `lifecycle` field exists in `pack.toml`, `pack.schema.json`, or the index schema. The Wave 4 spec deferred it to a later contract wave.
- The index's `catalogue` object has a name and description but no version.

### What the marketing site does today

- [`web/src/pages/catalogue/index.astro`](../../../web/src/pages/catalogue/index.astro) and [`web/src/pages/packs/[pack].astro`](../../../web/src/pages/packs/[pack].astro) read the Astro `packs` collection. That collection is 23 hand-written files in `web/src/content/packs/`, one per pack.
- Each file carries name, scope, `pluginInstallable`, tagline, skills, install command, `docsUrl`, and an optional `journeyUrl`. [`tools/lint-site-scope-parity.py`](../../../tools/lint-site-scope-parity.py) keeps `pluginInstallable` honest against `pack.toml`.
- Nothing in `web/` or `tools/` reads `catalogue-index.json`. The pages show no pack version, adapters, or integrations.
- `web/` has no `/evaluate/` route, and no page in `web/src` mentions evaluation.
- The site's standing journey, [`team-orientation-future-state`](../../design/journeys/team-orientation-future-state.md), names the adoption champion as its one reader. [`web/AGENTS.md`](../../../web/AGENTS.md) asks that a new reader be reconciled with that map.

### Dependencies and sequencing

- `/evaluate/` depends on [`catalogue-specification-publication`](catalogue-specification-publication.md) for the specification pages its open-formats and versioned-contracts claims link to. [RFC-0109](../../rfc/0109-catalogue-specification-publication.md), accepted on 2026-10-21 and merged in PR #1592 (`99dafc6ef`), governs it. Its slice S4, the one-way 0.1 release, is what unblocks Wave 7's specification links (RFC-0109 D8). Until then only the `draft/` pages from slice S3 exist, and a draft `$id` is not a promise.
- `/evaluate/` also links into the Build a Catalogue route that [`catalogue-wave6-technical-docs-ia`](catalogue-wave6-technical-docs-ia.md) owns. That intent's Status and Decomposed lines own its state. On `main` at `3cc898b9` there is no Wave 6 spec and no open Wave 6 PR; the owner reports Wave 6 delivery running in parallel.
- `workspace.toml` registers [`catalogue-wave9-migration-closeout`](catalogue-wave9-migration-closeout.md) as needing this intent. Wave 7 is therefore on the critical path for closing RFC-0076.

## Assumptions

- Every `/evaluate/` claim can link to a published page. Claims about formats and contracts link to the versioned catalogue specification; the rest link to published guides. Wave 6's Build a Catalogue route becomes the preferred entry link when it ships.
- Pack-page facts can come from a `catalogue-index.json` generated during the site build, while install-route facts such as `pluginInstallable` and the install command stay with their current owners.
- A platform lead reads claim-then-proof copy: one plain sentence per claim, followed by a link to the contract, command, or guide that proves it.
- **Knowledge surface:** the in-repository RFC, shipped Wave 2, 4, and 5 specs, published guides, contracts, `web/` source, the approved journey map, and an index generated from this repository, all at revision `3cc898b991df987b8ef8e515c6457a9ae8e5b501`; RFC-0109 and the RFC-0076 errata at `99dafc6efb608f4856cc7ec311ec554959f271bf`. No external knowledge surface was used.

## Riskiest assumption

**A platform lead can reach an informed build-or-adopt decision from one claim-then-proof page plus index-backed pack facts, and published evidence — the versioned catalogue specification and published guides — backs every claim without overstating it.** If any claim has no published proof, the page breaks the parent capability's guardrail. If the proof exists but platform leads still cannot decide, the page is only a list of links.

## De-risking verdict

- **Reversibility:** two-way door. Marketing pages and their build input can change without migrating user data or breaking a wire contract.
- **Prototype approach:** `validate-first`, overriding the two-way-door default. Whether every claim has proof is a precondition that a desk probe can settle before any prototype is built.
- **What would have to be true:** Each of the nine D10 claims has a shipped, publicly reachable evidence page today, and platform leads use those links to make the call.
- **Kill condition (predeclared 2026-10-21 by the owner):** Kill or re-sequence the bet if any of the nine D10 claims has no shipped public destination — a docs-site page built from `guides/**` or `packs/**`, a file under `contracts/`, or the PyPI package page — or rests only on repository-internal material such as an RFC, spec, or `docs/guides/` page.
- **Probe:** Map each D10 claim to a public destination at revision `3cc898b991df987b8ef8e515c6457a9ae8e5b501`.
- **Result:** All nine claims have a public destination. The kill condition did not fire.
  1. Open file-based formats: [`catalogue-format.md`](../../../guides/_shared/reference/catalogue-format.md), [`skill-authoring-standards.md`](../../../guides/_shared/reference/skill-authoring-standards.md), and `contracts/pack.schema.json`, `skill.schema.json`, and `profile.schema.json`.
  2. Versioned contracts: [`contracts/README.md`](../../../contracts/README.md) and [`contracts/REGISTRY.md`](../../../contracts/REGISTRY.md).
  3. Deterministic verification and packaging: [`catalogue-ci-contract.md`](../../../guides/_shared/reference/catalogue-ci-contract.md), which states the archive is deterministic for the same source content.
  4. Human gates: the repo-governance [`new-rfc`](../../../guides/repo-governance/how-to/new-rfc.md) and [`new-adr`](../../../guides/repo-governance/how-to/new-adr.md) guides and [the core pack explanation](../../../guides/core/explanation/core-pack.md).
  5. Source ownership: [`create-a-catalogue.md`](../../../guides/_shared/how-to/create-a-catalogue.md), "Publish your own packs and profiles".
  6. Adapter projection: [`adapter-support.md`](../../../guides/_shared/reference/adapter-support.md) and `contracts/adapter.toml`.
  7. Release integrity: [`catalogue-ci-contract.md`](../../../guides/_shared/reference/catalogue-ci-contract.md), covering `--force` and `--compare`.
  8. Optional composition: § 11 of [`catalogue-authoring-standards.md`](../../../guides/_shared/reference/catalogue-authoring-standards.md) and [`pack-catalogue.md`](../../../guides/_shared/explanation/pack-catalogue.md).
  9. Technical evidence: the docs site, `contracts/` in the public repository, and the PyPI destination declared in [`site.toml`](../../../site.toml).
- **Owner reframe (2026-10-21):** The predeclared line accepted a raw file under `contracts/` as public proof. The owner rejects that: a platform publishes its specification on its website, and `contracts/` mixes catalogue, work-loop, and delivery schemas with no version or stable URL. Without that destination kind, claim 1 (open formats) and claim 2 (versioned contracts) have no published specification page, and claim 9 loses its contracts link.
- **Verdict:** **Re-sequenced.** The line as written did not fire, but the owner's reframe removes the destination two claims rested on. Wave 7 waits for [`catalogue-specification-publication`](catalogue-specification-publication.md) through RFC-0109 slice S4, and is de-risked again against the published specification once that exists. Whether platform leads make the decision from the page remains `to-validate`.
- **Adversarial validation hook:** Stop the page if a claim can only be proved by following a link into maintainer-only material. Before release, open every `/evaluate/` link on the deployed site from a signed-out browser, and treat the first link that lands on an RFC, spec, `docs/guides/` page, or a 404 as a stop condition.

```yaml
validation_hook:
  assumption: A platform lead can decide whether their organisation should build and own a catalogue on agentbundle from one claim-then-proof /evaluate/ page and index-backed pack facts.
  kill_condition: Fewer than 4 of 5 platform leads, after five minutes on a prototype /evaluate/ page, can state whether their organisation could own a catalogue on agentbundle and name the evidence link that supports their answer.
  activity: Run five-minute task sessions with platform leads on a low-fidelity /evaluate/ prototype, asking each for a build-or-adopt call and the link behind it, and record the answer, the link chosen, and any claim they doubted.
```

## What the decision requires

- Add a marketing-site `/evaluate/` page covering open file-based formats, versioned contracts, deterministic verification and packaging, human gates, source ownership, adapter projection, release integrity, optional composition, and links to technical evidence (RFC-0076 D10). Format and contract claims link to the published catalogue specification, not to repository files.
- Update catalogue and pack pages to use neutral-index facts for version, scope, adapters, optional integrations, and documentation links (RFC-0076 D10). `lifecycle` is deferred by owner decision on 2026-10-21 because no contract carries it.
- Render pack composition as a legible relationship view using the user-facing labels from D6 (RFC-0076 D10).

## Non-goals

- Turning the marketing site into raw schema documentation or broadly redesigning its visual system (RFC-0076 D10).
- Adding a `lifecycle` field to `pack.toml`, `pack.schema.json`, or the index schema.
- Changing the marketing home page or its adoption-champion journey stages.
- Building the Build a Catalogue documentation route, release-integrity behaviour, or the search verb.
- Publishing the catalogue specification or changing contract `$id` URLs, which [`catalogue-specification-publication`](catalogue-specification-publication.md) owns.

## Open questions

- **Lifecycle:** D10 asks for a lifecycle fact that no contract carries. A separate contract change would add it to `pack.schema.json` and the index together, as the Wave 4 spec suggests. Decider: the owner.
- **Journey reconciliation:** `/evaluate/` adds a platform-lead reader beside the journey map's adoption champion. Either the map gains an amendment through `approve-journey`, or `/evaluate/` gets its own journey. Decider: the owner, before the spec freezes the page's reader.
- **Documentation links:** The index has documentation links for 15 of 23 packs, while the site's own page data has one for every pack. The spec decides whether to close the gap with `JOURNEY.md` `docsUrl` entries or to keep the site value as a declared fallback.
- **Catalogue version:** The index carries pack versions but no catalogue version. The spec decides whether D10's "version" means pack version only.

## Decomposition

None yet. After acceptance, this feature intent projects to one marketing-site specification. The specification owns the page content model, the index build input, and the relationship view.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md
- Revision: 99dafc6efb608f4856cc7ec311ec554959f271bf

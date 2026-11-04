# Brief: publish the versioned catalogue specification

- **Slug:** `catalogue-specification-publication-delivery`
- **Received:** 2026-11-04
- **Owner:** eugenelim
- **Status:** Shipped
- **Cut-closed:** 2026-11-04 All four slices confirmed Shipped; see § Spec map.
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/catalogue-specification-publication.md`](../intents/catalogue-specification-publication.md). **Retrospective brief.** The four slice specs shipped between 2026-10-21 and 2026-10-23 under RFC-0109 D8 without a brief, so the delivery resolver mapped one intent to four specs and refused closure with `delivery-projection-mismatch`. The owner authored this brief on 2026-11-04 to record that mapping and validate the delivered work against the intent. It records no slice decision that was not already made in the specs and RFC-0109.
- **Parent intent:** intent:catalogue-specification-publication

## Outcome

An adopter can set up and validate their own agentbundle catalogue from the published specification alone. The specification is the ten members named in `contracts/catalogue-spec.toml`, served per release at a stable URL, and four checks keep the published bytes equal to the bytes the CLI enforces.

## Scope / Non-goals

In scope, as RFC-0109 D8 cut it:

- S1: the membership manifest and bundled-only contract loading.
- S2: the schema for the release archive manifest.
- S3: the specification section of the docs site at `draft/`.
- S4: the one-way release `0.1`.

Non-goals:

- Publishing work-loop, delivery, workspace, or work-intake contracts.
- Changing what any contract means.
- The evaluator page and the Build a Catalogue guide route, which belong to other intents.

## Constraints / Appetite

[RFC-0109](../../rfc/0109-catalogue-specification-publication.md) fixes the shape: one manifest, an immutable `<MAJOR.MINOR>/` path per release, and `contracts/` as the only authored source. The slices ran in the order S1, S2, S3, S4 and each depends on the one before.

## Assumptions / Risks

- **Validated 2026-11-04.** `contracts/catalogue-spec.toml` holds 10 `member`, 9 `bundled`, and 2 `vendored` rows and one `[[release]]` for version `0.1`, dated 2026-10-23, paired with adapter contract `0.18`.
- **Validated 2026-11-04.** `contracts/catalogue-manifest.schema.json` exists, and the frozen snapshot sits under `contracts/releases/catalogue/0.1/`.
- **Validated 2026-11-04.** `check_contract_parity.py`, `check_spec_version.py`, and `check_release_gate.py` pass against the tree. The release-gate check reports that the deployed index serves release `0.1`.
- **Risk carried by the intent, not closed here.** The intent's capability placement is still open: it serves two clauses of CAP-0006 and stays unparented until the owner places it. That affects navigation, not delivery.

## Delivery slices

1. **S1, `catalogue-spec-manifest`.** The membership manifest, the generated inventory files, and bundled-only contract loading.
2. **S2, `catalogue-manifest-schema`.** The schema for `catalogue-manifest.json`.
3. **S3, `catalogue-spec-site`.** The generated site section at `draft/` with field tables and narrative pages.
4. **S4, `catalogue-spec-release`.** Release `0.1`: the frozen snapshot, real `$id` URLs, and the release-time drift gates.

## Spec map

The Status column is derived from each spec; it is not hand-edited.

| Spec | Status |
| --- | --- |
| `catalogue-spec-manifest` | <auto> |
| `catalogue-manifest-schema` | <auto> |
| `catalogue-spec-site` | <auto> |
| `catalogue-spec-release` | <auto> |

## Governance references (optional)

- [RFC-0109](../../rfc/0109-catalogue-specification-publication.md) — decides membership, home, URLs and versions, the archive manifest schema, pages, drift checks, and the slice order.
- [RFC-0003](../../rfc/0003-spec-and-cli.md) § Amendments and [RFC-0076](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md) § Errata — where RFC-0109 records its amendments.

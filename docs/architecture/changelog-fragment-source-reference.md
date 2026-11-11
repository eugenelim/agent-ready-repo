# Per-update changelog sources: reference

This page holds the contracts, verification and build mapping for
[per-update changelog sources](changelog-fragment-source.md). Rationale lives
in [ADR-0123](../adr/0123-product-changelog-per-update-sources-and-generated-views.md)
and [ADR-0143](../adr/0143-released-changelog-records-move-into-monthly-bundles.md).

## 1. Contracts

| Contract | Rule | Enforced by |
| --- | --- | --- |
| Identity and path | A lowercase UUIDv4 appears in the filename stem and the envelope `id`; for a bundled record the identity is the `id` and the part's month | `new` creates it; the validator rejects mismatches and duplicates across both forms |
| Envelope | The file opens with `+++`, holds TOML fields `schema`, `id`, `anchor`, `date` and one or more `packages` records (`name`, `version`), and closes with a second `+++` | Standard-library `tomllib` plus explicit field and type checks |
| Body | Established changelog section names only; each fragment has a non-empty `Highlights`; release-level headings and duplicate sections are rejected | Parser |
| Order | `date` descending, then `id` ascending; same-date order has no editorial meaning | Canonical sort before rendering |
| Anchor | The package-and-date slug, a hyphen, and the fragment UUID as 32 lowercase hex digits; the renderer emits `<a id="<anchor>"></a>` before the update heading | `new` composes it; the validator recomputes it from `packages`, `date` and `id` |
| Published identity | `packages`, `date` and `id` of a merged fragment are immutable, so `/now/<anchor>/` and the Atom `<id>` never move; a bundled record leaves publication only through a listed retraction | Merge-base comparison keyed by `id`, reading changed entries as raw bytes |
| Bundle record | A part is a sequence of `+++ record +++` separator lines, each followed by one fragment's exact UTF-8, LF-only bytes, in canonical order; parts are append-only | Container parser; `compact` and `retract` are the only writers |
| Retraction | `[[retraction]]` entries with `id` and `category` (`credential`, `personal-data`, `legal`, `other`); append-only | `retract` |
| Projection schema | `now-highlights.generated.json` stays at `schemaVersion` 1, and fragment groups carry the same fields as history groups | Five importers throw on any other version |
| Baseline | Existing release sections and anchor-producing headings stay at `docs/product/changelog.md` | Migration notice and a historical-section digest test |
| Determinism | Repeated and shuffled builds are byte-identical; no clock, network, model or Git-history input | No volatile fields; canonical sort |

## 2. Verification

| Attribute | Check |
| --- | --- |
| Mergeability | A synthetic merge-group commit from representative branches has no changelog-path conflict when fragment ids differ |
| Content integrity | Every fragment and Highlights item appears exactly once, byte for byte, in `/now/` data |
| Historical compatibility | Release sections, model payloads and anchors are identical at the original path and in generated views |
| Determinism | Five shuffled enumerations produce byte-identical output |
| Git cleanliness | Regeneration from a clean checkout leaves no tracked diff; outputs stay under `build/` |
| Build performance | Three interleaved arms (today's corpus, a monolith with ten times the entries, the same corpus as fragments); the fragment arm's median over the monolith arm's stays under 10%, and page count per arm is recorded |
| Diagnosability | Every diagnostic class has a fixture and names a source path and field |
| Dependency posture | An offline build and a static dependency check prove no model or network input |

The performance method and its measurements are in the
[spec notes](../specs/product-changelog-fragments/notes/).

## 3. Build mapping

| Element | Owner | Verification |
| --- | --- | --- |
| Fragment store | `docs/product/changelog.d/<id>.md` | Contract fixtures; changed-path merge replay |
| Bundle store | `docs/product/changelog.months/YYYY-MM-NN.bundle` | Container, identity, compaction and retraction fixtures |
| Retraction list | `docs/product/changelog-retractions.toml` | Schema, append-only and reappearance fixtures |
| Baseline | `docs/product/changelog.md` | Digest, inbound-link and full-corpus tests |
| Model and assembler | `tools/changelog.py` | Parser, ordering, identity, golden-output and offline tests |
| Site changelog and `/now/` adapter | `tools/build-site.py`; `web/src/pages/now/` and `web/src/components/now/NowHighlights.astro` | Routing tests; per-fragment Highlights correspondence; every `/now/` anchor resolves in the emitted changelog |
| Release validators | `tools/check-core-release.py`, `tools/repo/check_release_impact.py` | Fragment-to-release match; added and changed fragment path tests |
| Publish filter | `.github/workflows/pages.yml` | Path-trigger test |
| Author guidance | `docs/product/AGENTS.md`, `packs/AGENTS.local.md`, the baseline header, the fragment template | Guidance search and lint |

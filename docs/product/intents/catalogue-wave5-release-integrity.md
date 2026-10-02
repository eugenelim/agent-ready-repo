# Catalogue release integrity

- **Slug:** `catalogue-wave5-release-integrity`
- **Status:** Accepted
- **Accepted:** 2026-10-02 by eugenelim, lifecycle owner. Basis: explicit owner direction to refresh, de-risk, and apply the needed reviews; the recorded de-risking verdict survived, and intent-mode review of this revision produced no malformed findings.
- **Level:** feature
- **Owner:** eugenelim
- **Scale:** app
- **Maturity:** brownfield
- **De-risked:** 2026-10-02
- **Shaping-reviewed:** 2026-10-02
- **Decomposed:** no
- **Parent intent:** capability:catalogue-trust-and-adoption
- **Governed by:** [RFC-0076 D8](../../rfc/0076-catalogue-contracts-composition-semantics-discovery.md)

## Outcome

- **Input (steerable):** The share of release comparisons in which a publisher or adopter can identify changed packs and profiles from package-produced evidence without inspecting raw catalogue files.
- **Outcome (lagging):** Publishers and adopters can identify which packs or profiles changed, verify what arrived, and prevent an existing catalogue version from being silently replaced.
- **Guardrail:** Release packaging stays deterministic and preserves the shipped per-file manifest, archive sidecar, staged self-verification, and default overwrite refusal. Generated outputs do not affect content identity, and first-party publication never uses an override.

## Opportunity

The package command already records per-file digests, emits an archive digest sidecar, verifies the staged archive, and refuses an existing output path. It does not yet give a release consumer pack- and profile-level identity or a direct comparison with a prior archive.

- **Functional job:** Package a catalogue release, see which distributable units changed from the prior release, and prove that the received archive matches what was published.
- **Emotional job:** Be confident that a version label still names the same release and that a changed pack cannot hide inside a large file-level diff.
- **Social job:** Show reviewers and adopters release evidence produced by the packaging contract instead of an informal explanation of what changed.
- **Struggling moment:** The current manifest can prove individual archive files and the archive sidecar can prove the whole download, but neither answers which pack or profile changed between releases.

## Boundary

This intent owns release-archive integrity: unit-level content identity inside `catalogue-manifest.json`, comparison with one prior catalogue archive, and the archive-version mutation refusal defined by RFC-0076 D8. It extends the existing package snapshot and verification path rather than creating a second release identity source.

Marketplace pack identity belongs to [CAP-0007 catalogue publication](CAP-0007-catalogue-publication.md). Catalogue acquisition, sync, installation, registry history, multi-version resolution, and the content semantics of individual packs and profiles remain with their existing owners.

## Current evidence — 2026-10-02

- [`package_catalogue`](../../../packages/agentbundle/agentbundle/catalogue_tooling/package.py) writes schema-2 `catalogue-manifest.json` with sorted per-file SHA-256 values, writes an archive SHA-256 sidecar, and self-verifies the staged archive before atomic placement.
- Packaging already refuses when the target release archive exists, but the CLI exposes no package `--force` or `--compare` option.
- Manifest pack entries contain name and version, while profile entries contain names. Neither carries the normalized content-tree digest required by RFC-0076 D8.
- [`catalogue-wave4-semantic-contracts-index`](../../specs/catalogue-wave4-semantic-contracts-index/spec.md) is shipped, so the neutral-index prerequisite is complete.

## Assumptions

- The archive-level mutation boundary in RFC-0076 remains the baseline scope to refine.
- A comparison against one prior archive is enough to explain a release without adding registry history or multi-version resolution.
- **Knowledge surface:** the in-repository RFC, package implementation, CLI contract, shipped Wave 4 spec, tests, and product-intent corpus at revision `2f33168e489345e386977012d553f26b26cdaa8f`.

## Riskiest assumption

**Publishers and adopters will use pack- and profile-level differences to make or explain release decisions, and those differences can be derived from the package command's existing normalized content snapshot without creating a conflicting identity model.** If either the decision value or the single-snapshot derivation fails, the feature's stated outcome does not hold.

## De-risking verdict

- **Reversibility:** one-way door. The manifest and CLI become published release contracts, so changing their identity rules after adoption would be costly.
- **Prototype approach:** `validate-first`.
- **What would have to be true:** Publishers and adopters need to explain a release at pack or profile granularity, and that identity can be derived from the same normalized snapshot that packaging already verifies.
- **Kill condition (predeclared 2026-10-02):** Kill the bet if the current public package artifacts can already answer all three release questions without re-reading raw catalogue files: whether the archive matches, whether the version is protected from replacement, and which packs or profiles changed from the prior release. Also kill it if unit digests cannot be derived from the package command's existing bounded content snapshot.
- **Probe:** Read the current package CLI, manifest generator, archive-placement path, release guides, and package tests at revision `2f33168e489345e386977012d553f26b26cdaa8f`.
- **Result:** The sidecar answers archive identity and the existing-path refusal protects a version, but neither the manifest nor the CLI identifies changed packs or profiles across releases. The package command already holds one confined `file_bytes` snapshot before manifest and archive generation, so the unit digests need no second source walk. The kill condition did not fire.
- **Verdict:** **Survived, desk-grounded.** The missing consumer answer and one-snapshot feasibility both hold. Real publisher and adopter behavior remains `to-validate` before treating the comparison shape as proven.
- **Adversarial validation hook:** Kill the release path if a clean adopter checkout cannot exercise it end to end without maintainer-only workspace state or unpublished Wave 4 assumptions. Rehearse the published package artifact and CLI in a temporary adopter tree with no source-workspace fallback, and treat the first missing contract, path, or command as a stop condition.

```yaml
validation_hook:
  assumption: Publishers and adopters use pack- and profile-level release differences to make publish, review, or adoption decisions.
  kill_condition: Fewer than 3 of 5 target users use the unit-level difference to make or explain a release decision when comparing two realistic archives.
  activity: Give catalogue publishers and adopters two realistic release archives, ask them to decide whether to publish or adopt the candidate, and observe which evidence changes or explains their decision.
```

## What the decision requires

- Add a SHA-256 digest for every pack and profile to `catalogue-manifest.json`, calculated from the sorted, normalized file list of the normalized content tree and excluding generated outputs (RFC-0076 D8).
- Refuse, with exit 2, to package a version whose catalogue archive already exists unless `--force` is passed; first-party CI must not use `--force` in the publish pipeline (RFC-0076 D8).
- Add `--compare <archive>` to `agentbundle catalogue package` for added, removed, and changed packs with version and digest changes, in default human output and `--format json` (RFC-0076 D8).

## Non-goals

- The refusal applies to packaged catalogue `.tar.gz` archives, not local development re-builds (RFC-0076 D8).

## Open questions the RFC left

- Wave 5 determines whether pack-level archives, if any, also fall within the mutation-refusal scope (RFC-0076 OQ3).

## Decomposition

None yet. This feature intent projects to one release-integrity specification after acceptance; the specification owns the detailed manifest, CLI, comparison, and refusal contracts.

## Source

- Mode: repo-origin
- Locator: docs/rfc/0076-catalogue-contracts-composition-semantics-discovery.md
- Revision: 2f33168e489345e386977012d553f26b26cdaa8f

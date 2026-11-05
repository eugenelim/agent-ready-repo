# Include the guide corpus in catalogue archives

- **Slug:** `catalogue-archive-guide-corpus`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [spec/documentation-entry-navigation](../../specs/documentation-entry-navigation/spec.md)

## Outcome

Source-flavor catalogue archives include the adopter guide corpus under a decided archive layout and prove the package and install contract.

## Opportunity

Current source-flavor archives include `guides/_shared` but omit pack-specific adopter guides. The owning shipped spec explicitly leaves physically adding the full tree to packaged catalogue archives as separate `agentbundle` work.

## What this absorbs

### catalogue-package-guides

Decide the archive layout, include the guide corpus, and add package/install contract coverage. The protected tree `packages/agentbundle/**` is touched, so the landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. This requirement applies at commit time.

Unblocks when: the archive layout and package/install contract coverage are accepted through the authorized protected-tree change path.

## Current state — checked 2026-11-05

Packaging a source-flavor archive of this repository (`package_source_flavour`) wrote 2,955 entries, 52 of them under `guides/_shared`, none under `guides/<pack>`. The repository holds 237 guide files, so 185 pack guides are left out. `_SOURCE_INCLUDE_SHARED_GUIDES` in `catalogue_tooling/package.py` is the only guide allowlist.

An adjacent defect sits in the same command: `agentbundle catalogue package --flavor source` requires `--channel` and also refuses it, so a source package builds only with `--channel ""`. The first slice fixes this where it touches the command.

## Assumptions

- Layout decision, recommended: mirror the repository layout, so `guides/<pack>/**` is packed for each pack that is in the archive and existing relative links keep working.
- **Riskiest assumption:** packing `guides/<pack>/**` leaves existing relative links resolving and does not break the wave 5 unit-digest goldens. Test it agent-only: pack a fixture catalogue, unpack it, check every guide link resolves, and run the release-integrity goldens before and after.

## Non-goals

- Changing the runtime-flavor archive or the release-integrity digest scheme.
- Writing or restructuring the guides themselves.
- Any change outside the source-flavor packaging path and its manifest.

## De-risk result

- **Date:** 2026-11-05.
- **Ran:** packed a source archive of this repository with `package_source_flavour`, extracted it under `.context/`, copied in `guides/<pack>/**` for the 21 guide directories whose packs are in the archive, and checked every relative Markdown link in the pack guides; read `unit_digest`.
- **Observed:** the archive holds 25 pack directories and covers all 21 guide directories. With pack guides added, 50 of 739 links in pack guides do not resolve: 33 are site-absolute links (they fail in the repository too), 15 point at `docs/` and 1 at `.github/` (both exist in the repository and not in the archive), and 1 is another file. The already-shipped `guides/_shared` guides have 11 unresolved links of 231 in the archive. `unit_digest` covers only files under each unit's own path, so adding `guides/` does not move any pack unit digest.
- **Verdict:** partly holds, so not stamped. Digests are not at risk. Links resolve except 16 that leave the archive, so the spec must decide how to treat them, and the 33 site-absolute links are an existing defect to leave out of scope.

## Readiness

- **Route:** new-spec, one session. It changes `packages/agentbundle/**`. The protected-tree gate (`tools/lint-catalogue-curation-guard.py`) checks only that the commit message carries an `Engine-Change-RFC:` trailer; recent commits cite an accepted record or write `n/a` with the reason, so no new RFC is needed.
- **First slice:** include `guides/<pack>/**` for every packed pack, add the guides to the archive manifest, and make `--channel` optional for the source flavor.
- **Agent-only proof:** a test packs a fixture catalogue and asserts the guide set equals the packed packs' guides; an install test unpacks the archive and checks that relative guide links resolve, with the 16 links to `docs/` and `.github/` handled by a decision the spec records (rewrite, drop, or allow-list); the archive stays byte-identical across two runs. Before the change, run the wave 5 release-integrity goldens, because the unit digests move.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

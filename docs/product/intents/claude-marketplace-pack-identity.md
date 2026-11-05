# Identify each Claude marketplace pack by content

- **Slug:** `claude-marketplace-pack-identity`
- **Status:** Accepted
- **De-risked:** 2026-11-05
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Parent intent:** capability:catalogue-publication
- **Governed by:** [spec/claude-plugin-route-scope](../../specs/claude-plugin-route-scope/spec.md)

## Outcome

Each Claude marketplace pack has an independently identifiable and recoverable content digest compatible with the upstream marketplace schema.

## Opportunity

Mutable `claude-plugins-dist` references have no per-pack content hash, so installs cannot be independently identified or recovered after delist.

## What this absorbs

### plugin-marketplace-content-hash

Extend the marketplace contract with a per-pack digest after resolving upstream-schema compatibility. `docs/specs/claude-plugin-route-scope/spec.md` names “a per-pack content hash”; generated marketplace entries still use `ref: "claude-plugins-dist"`, and no per-pack marketplace digest was found. The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC at commit time.

## Upstream schema check — 2026-11-05

The current Claude Code marketplace reference (`code.claude.com/docs/en/plugins/marketplace-reference`) settles the compatibility question:

- `github`, `url` and `git-subdir` plugin sources take `ref` and a full 40-character lowercase `sha`; when both are set, Claude Code checks out `sha`, so installation survives a deleted or moved branch while the commit stays reachable.
- The `archive` source takes a `sha256` of the zip and refuses a mismatch. No git source carries a content digest.
- An entry accepts a free-form `metadata` object that Claude Code never reads, so a content digest placed there raises no warning. Unknown entry keys are ignored at load and reported as a warning by `claude plugin validate`.

This repository's `contracts/marketplace-entry.schema.json` sets `additionalProperties: false` on the entry and the source, so a digest field needs a schema change here whichever channel is used.

## Assumptions

- The digest reuses the per-unit digest that release integrity already computes (`unit_digest` in `catalogue_tooling/archive.py`, and the `digest` field of each pack in `catalogue-index.json`). That keeps one digest scheme over pack content and leaves the release-archive digest untouched, which is the seam with `catalogue-trust-and-adoption`.
- **Riskiest assumption:** the existing unit digest is a stable identity for a built plugin tree, so the same files always give the same digest. Test it agent-only: build twice, compare each entry digest with the unit digest of the built files, and assert the schema accepts `metadata` while still rejecting other unknown keys.

## Non-goals

- Release-archive digests, which `catalogue-wave5-release-integrity` owns.
- Pinning `sha` to the published-branch commit, left open because that hash exists only after the push.
- Verification of the digest by Claude Code at install, which the upstream schema does not offer.

## De-risk result

- **Date:** 2026-11-05.
- **Ran:** `agentbundle catalogue build --root . --output <dir>` twice into separate directories under `.context/`, then compared every file hash and computed `unit_digest` (from `catalogue_tooling/archive.py`) for each plugin tree.
- **Observed:** both builds hold 3,434 files with identical hashes (0 differences). `claude-plugins/` holds 16 plugin trees, each with the same unit digest in both builds, and they match the 16 entries of the built `marketplace.json` one for one by name and `source.path`. The current entry schema rejects an added `metadata` key (`additionalProperties: false`), which confirms the schema change the slice needs.
- **Verdict:** supported. The unit digest is a stable identity for a built plugin tree. The schema half (accept `metadata`, still reject other keys) is the slice's own work.

## Readiness

- **Route:** brief. It is slice P4 of [`catalogue-publication-delivery`](../briefs/catalogue-publication-delivery.md). The protected-tree gate (`tools/lint-catalogue-curation-guard.py`) checks only that an `Engine-Change-RFC:` trailer is present, and recent commits cite an accepted record or write `n/a` with the reason, so none of these changes needs a new RFC.
- **Recommended contract:** put the pack content digest in the entry's `metadata` object, add `metadata` to the entry schema, and compute it with the existing unit digest over the built plugin files. It can be computed before publish and does not depend on the commit hash. Pinning `sha` to the `claude-plugins-dist` commit stays open, because the commit hash exists only after the push, which would make the entry in `main` change after every publish.
- **Not before:** slice P1 (schema edits) and slice P2 (the publisher gate), because both touch the same files.
- **Agent-only proof:** a build test that the digest in each entry equals the unit digest of that pack's built files; a schema fixture that accepts `metadata` and still rejects other unknown keys; `claude plugin validate` stays warning-free where the CLI is installed.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

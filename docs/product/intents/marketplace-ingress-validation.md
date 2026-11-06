# Marketplace ingress accepts valid repository references

- **Slug:** `marketplace-ingress-validation`
- **Status:** Accepted
- **De-risked:** 2026-11-05
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Parent intent:** capability:catalogue-publication
- **Governed by:** [spec/marketplace-generator-single-source Assumptions](../../specs/marketplace-generator-single-source/spec.md)

## Outcome

Marketplace ingress rejects invalid Git references and empty configured branch values before a fork can resolve an install route to upstream.

## Opportunity

`marketplace-entry.schema.json` admits arbitrary `ref` and `sha` strings on the `archive.py` and `verify.py --root` ingress path, while an empty `claude-plugin-branch` passes schema validation and lets `build_catalogue` retain the upstream `claude-plugins-dist` constant.

## What this absorbs

### marketplace-ref-not-git-ref-validated

- `contracts/marketplace-entry.schema.json` declares `"ref": { "type": "string" }`; the adjacent `sha` property is likewise only a string.
- Validate `ref` and `sha` as Git references on the `archive.py` and `verify.py --root` ingress path.
- **BLOCKER:** The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. This applies at commit time.

### catalogue-branch-empty-falls-back-to-upstream-constant

- An empty `claude-plugin-branch` passes schema validation. In `packages/agentbundle/agentbundle/catalogue_tooling/build.py`, `if config and config.build.claude_plugin_branch:` means it does not replace `_DIST_BRANCH`.
- With unchanged upstream `pack.links.repository` values, a fork's install route therefore resolves upstream. An omitted key is rejected; an absent `catalogue.toml` separately uses hardcoded defaults.
- Require a non-empty configured branch value so it cannot fall back to the upstream `claude-plugins-dist` constant.
- **BLOCKER:** The fix changes protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. This applies at commit time.

## Assumptions

- None.
- **Riskiest assumption:** a Git-reference pattern in the schema rejects invalid references without rejecting a valid one a real catalogue uses. Test it agent-only with fixtures of valid and invalid references, including slashes, tags and 40-character hashes, and by validating this repository's own marketplace entries against the stricter schema.

## Current state — checked 2026-11-05

Both gaps reproduce. A marketplace entry with `ref` set to `bad ref ~^:` and one with an empty `ref` both pass `contracts/marketplace-entry.schema.json`, where `ref` and `sha` are bare strings. A `catalogue.toml` with `claude-plugin-branch = ""` loads with the empty value, and `build.py` line 106 skips the override because an empty string is false, so the upstream `claude-plugins-dist` constant stays. The entry schema also forbids extra keys at the entry and source levels.

## Non-goals

- Pinning `sha` to a published commit, or adding a per-pack digest, which belong to `claude-marketplace-pack-identity`.
- Changing the publish workflow or who may publish, which belongs to `plugin-publish-trust-boundary`.
- Validating anything beyond Git references and the configured branch.

## De-risk result

- **Date:** 2026-11-05.
- **Ran:** (1) read the 16 entries of this repository's `.claude-plugin/marketplace.json`; (2) used `git check-ref-format --branch` as the oracle on 6 valid and 11 invalid references; (3) compared a candidate pattern (no control or space characters, none of `~ ^ : ? * [ \`, no `..`, `@{` or `//`, no leading `/` or `-`, no trailing `/` or `.`, no component starting with `.` or ending `.lock`) with the oracle on 3,012 strings; (4) checked that a 40-character lowercase hex pattern accepts a full hash and rejects uppercase and short values.
- **Observed:** all 16 real entries use the single ref `claude-plugins-dist` and none carries a `sha`. The oracle accepts all 6 valid references and rejects 10 of the 11 invalid ones (it also rejects the eleventh, a leading `-`, under `--branch`). The candidate pattern disagreed with the oracle on 20 of 3,012 strings, all of them the single string `@`, which git accepts and the pattern refuses; refusing it is the safe direction.
- **Verdict:** supported. A pattern rejects the invalid references without rejecting any reference a real catalogue uses. The slice's own test should keep the oracle comparison as a fixture.

## Readiness

- **Route:** brief. It is slice P1 of [`catalogue-publication-delivery`](../briefs/catalogue-publication-delivery.md), merged with `marketplace-config-single-authority` because both edit `catalogue_tooling/build.py` and `config.py`. The protected-tree gate (`tools/lint-catalogue-curation-guard.py`) checks only that an `Engine-Change-RFC:` trailer is present, and recent commits cite an accepted record or write `n/a` with the reason, so none of these changes needs a new RFC.
- **First slice:** a Git reference pattern for `ref` (the rules `git check-ref-format` applies), a 40-character lowercase hex pattern for `sha`, and a loader error for an empty `claude-plugin-branch`.
- **Agent-only proof:** schema fixtures for valid and invalid references; a config test that an empty branch is refused; `tools/test_marketplace_envelope_parity.py` still passes (61 tests pass today).
- **Answered:** a private-only publisher still needs this, because the empty-branch fallback runs for every builder.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

# Marketplace ingress accepts valid repository references

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/marketplace-generator-single-source Assumptions](../../specs/marketplace-generator-single-source/spec.md)

## Outcome

Marketplace ingress rejects invalid Git references and empty configured branch values before a fork can resolve an install route to upstream.

## Opportunity

`marketplace-entry.schema.json` admits arbitrary `ref` and `sha` strings on the `archive.py` and `verify.py --root` ingress path, while an empty `claude-plugin-branch` passes schema validation and lets `build_catalogue` retain the upstream `claude-plugins-dist` constant.

## What this absorbs

### marketplace-ref-not-git-ref-validated

- `contracts/marketplace-entry.schema.json:90` declares `"ref": { "type": "string" }`; the adjacent `sha` property is likewise only a string.
- Validate `ref` and `sha` as Git references on the `archive.py` and `verify.py --root` ingress path.
- **BLOCKER:** The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. This applies at commit time.

### catalogue-branch-empty-falls-back-to-upstream-constant

- An empty `claude-plugin-branch` passes schema validation. At `packages/agentbundle/agentbundle/catalogue_tooling/build.py:106`, `if config and config.build.claude_plugin_branch:` means it does not replace `_DIST_BRANCH`.
- With unchanged upstream `pack.links.repository` values, a fork's install route therefore resolves upstream. An omitted key is rejected; an absent `catalogue.toml` separately uses hardcoded defaults.
- Require a non-empty configured branch value so it cannot fall back to the upstream `claude-plugins-dist` constant.
- **BLOCKER:** The fix changes protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. This applies at commit time.

## Assumptions

- None.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

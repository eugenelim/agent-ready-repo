# Include the guide corpus in catalogue archives

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/documentation-entry-navigation](../../specs/documentation-entry-navigation/spec.md)

## Outcome

Source-flavor catalogue archives include the adopter guide corpus under a decided archive layout and prove the package and install contract.

## Opportunity

Current source-flavor archives include `guides/_shared` but omit pack-specific adopter guides. The owning shipped spec explicitly leaves physically adding the full tree to packaged catalogue archives as separate `agentbundle` work.

## What this absorbs

### catalogue-package-guides

Decide the archive layout, include the guide corpus, and add package/install contract coverage. The protected tree `packages/agentbundle/**` is touched, so the landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. This requirement applies at commit time.

Unblocks when: the archive layout and package/install contract coverage are accepted through the authorized protected-tree change path.

## Assumptions

- No additional assumptions.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

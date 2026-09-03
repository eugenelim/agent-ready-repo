# Make catalogue.toml the marketplace configuration authority

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/marketplace-generator-single-source](../../specs/marketplace-generator-single-source/spec.md)

## Outcome

Maintainers can set the marketplace branch and description in `catalogue.toml`, and every public render path uses those values after the `toml_emit.py` main-scaffold default has been decided.

## Opportunity

The public render surfaces do not load catalogue configuration, `_aggregate_marketplace` keeps an independent description default, and the existing parity layers retain known dynamic-rebind and publisher resolved-value gaps.

## What this absorbs

### marketplace-envelope-config-authority

`catalogue.toml` must be authoritative for marketplace branch and description across `render_pack_files` and `render_packs_to_dir`, including `packages/agentbundle/agentbundle/render.py:131` (`def render_packs_to_dir(`). Decide whether `toml_emit.py`'s main-scaffold default may change. The public render surfaces do not load the catalogue configuration. The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC at commit time.

### marketplace-description-fourth-statement-in-self-host

`packages/agentbundle/agentbundle/build/self_host.py:698` (`description: str = (`) shows that `_aggregate_marketplace` still carries an independent literal marketplace-description default, a fourth statement. Removing it needs an `Engine-Change-RFC:` trailer and a version bump. `tools/lint-catalogue-curation-guard.py` refuses a protected `packages/agentbundle/` change without that trailer, and `AGENTS.local.md` requires a `pyproject` version bump for an engine change. A configuration-drift fix must not become an engine release. The parity gate anchors the literal and catches divergence, but not the duplication. Unblocks when an engine-scoped RFC is open to cite in the trailer.

### marketplace-envelope-post-import-rebind-unbounded

Neither parity layer bounds a post-import rebind of `_DIST_BRANCH` or `_MARKETPLACE_DESCRIPTION`. `tools/test_marketplace_envelope_parity.py:120` records: `#: Dynamic rebinds layer 2 cannot model. A tripwire over the two anchor modules, so`; the resolved-value layer cannot model dynamic rebinds. The needed instrument is a runtime assertion inside the build or a Semgrep rule, not more static reading. Unblocks when SAST rule authoring is in scope; `sast-cwe-delta-review` is adjacent.

### marketplace-publisher-branch-layer-2-only

The publisher's `BRANCH` push target is covered by the parity gate's literal layer only, not its resolved-value layer. `tools/test_marketplace_envelope_parity.py:33` says: `That residual is \`marketplace-publisher-branch-layer-2-only\`.` The fix changes the publisher's import surface, which is publish-path code the prior PR deliberately did not touch. Unblocks when the publisher's import surface is next touched.

## Assumptions

- The shipped authority deliberately made `catalogue.toml` a required restatement rather than the resolution authority; this Draft intent carries the recorded follow-on to decide and implement a different authority model.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

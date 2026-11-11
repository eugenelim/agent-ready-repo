# Make catalogue.toml the marketplace configuration authority

- **Slug:** `marketplace-config-single-authority`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Parent intent:** capability:catalogue-publication
- **Governed by:** [spec/marketplace-generator-single-source](../../specs/marketplace-generator-single-source/spec.md)

## Outcome

Maintainers can set the marketplace branch and description in `catalogue.toml`, and every public render path uses those values after the `toml_emit.py` main-scaffold default has been decided.

## Opportunity

The public render surfaces do not load catalogue configuration, `_aggregate_marketplace` keeps an independent description default, and the existing parity layers retain known dynamic-rebind and publisher resolved-value gaps.

## What this absorbs

### marketplace-envelope-config-authority

`catalogue.toml` must be authoritative for marketplace branch and description across `render_pack_files` and `render_packs_to_dir`, including `render_packs_to_dir` in `packages/agentbundle/agentbundle/render.py`. Decide whether `toml_emit.py`'s main-scaffold default may change. The public render surfaces do not load the catalogue configuration. The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC at commit time.

### marketplace-description-fourth-statement-in-self-host

The `description` default of `_aggregate_marketplace` in `packages/agentbundle/agentbundle/build/self_host.py` shows that it still carries an independent literal marketplace-description default, a fourth statement. Removing it needs an `Engine-Change-RFC:` trailer and a version bump. `tools/lint-catalogue-curation-guard.py` refuses a protected `packages/agentbundle/` change without that trailer, and `AGENTS.local.md` requires a `pyproject` version bump for an engine change. A configuration-drift fix must not become an engine release. The parity gate anchors the literal and catches divergence, but not the duplication. Unblocks when an engine-scoped RFC is open to cite in the trailer.

### marketplace-envelope-post-import-rebind-unbounded

Neither parity layer bounds a post-import rebind of `_DIST_BRANCH` or `_MARKETPLACE_DESCRIPTION`. `tools/test_marketplace_envelope_parity.py` records: `#: Dynamic rebinds layer 2 cannot model. A tripwire over the two anchor modules, so`; the resolved-value layer cannot model dynamic rebinds. The needed instrument is a runtime assertion inside the build or a Semgrep rule, not more static reading. Unblocks when SAST rule authoring is in scope; `sast-cwe-delta-review` is adjacent.

### marketplace-publisher-branch-layer-2-only

The publisher's `BRANCH` push target is covered by the parity gate's literal layer only, not its resolved-value layer. `tools/test_marketplace_envelope_parity.py` says: `That residual is \`marketplace-publisher-branch-layer-2-only\`.` The fix changes the publisher's import surface, which is publish-path code the prior PR deliberately did not touch. Unblocks when the publisher's import surface is next touched.

## Assumptions

- The shipped authority deliberately made `catalogue.toml` a required restatement rather than the resolution authority; this Draft intent carries the recorded follow-on to decide and implement a different authority model.
- **Riskiest assumption:** loading `catalogue.toml` in the render paths changes no value for a catalogue that sets nothing. Test it agent-only: run `tools/test_marketplace_envelope_parity.py` (61 tests pass today) and compare the generated marketplace output for this repository before and after the change.

## Current state — checked 2026-11-05

`_aggregate_marketplace` in `build/self_host.py` still carries its own literal description default, and `toml_emit.py` still scaffolds `claude-plugin-branch = "main"`. `catalogue_tooling/build.py` overrides the two module constants only inside `build_catalogue`, and only when the configured value is non-empty. `tools/test_marketplace_envelope_parity.py` passes (61 tests).

## Non-goals

- Changing the `toml_emit.py` scaffold default branch (`main`).
- The post-import rebind bound, which needs a Semgrep rule or runtime assertion and is deferred to its own rule-authoring work.
- Changing the publisher's import surface for its `BRANCH` parity layer, taken only when that surface is next touched.

## De-risk result

- **Date:** 2026-11-05.
- **Ran:** read `build/main.py`, `catalogue_tooling/build.py`, `config.py`, `toml_emit.py` and this repository's `catalogue.toml`; ran `tools/test_marketplace_envelope_parity.py`.
- **Observed:** the parity test passes (61 tests). The builder's defaults are `_DIST_BRANCH = "claude-plugins-dist"` and a description literal. The loader's default for a missing key is `main`, the schema rejects an omitted key, and the scaffold writes `main`. So a catalogue with no `catalogue.toml` keeps the builder defaults, but a scaffolded catalogue that sets `main` would change from `claude-plugins-dist` to `main` on any render path that starts loading the file.
- **Verdict:** partly holds, so not stamped. Loading `catalogue.toml` changes no value only for a catalogue without the file; for a scaffolded one it flips the emitted ref to a value this repository has documented as wrong for its builder. The slice must decide the scaffold default first, and its proof compares generated marketplace output for a no-config catalogue and a scaffolded one, before and after.

## Readiness

- **Route:** brief. It is slice P1 of [`catalogue-publication-delivery`](../briefs/catalogue-publication-delivery.md), merged with `marketplace-ingress-validation`. The protected-tree gate (`tools/lint-catalogue-curation-guard.py`) checks only that an `Engine-Change-RFC:` trailer is present, and recent commits cite an accepted record or write `n/a` with the reason, so none of these changes needs a new RFC.
- **Open decision, recommended answer changed by the de-risk run:** the `toml_emit.py` scaffold writes `claude-plugin-branch = "main"` while the builder's `_DIST_BRANCH` is `claude-plugins-dist`, and this repository's `catalogue.toml` records that `main` is a value "no build published from". Recommended: the scaffold emits `claude-plugins-dist`, and the spec records the choice. Existing scaffolded catalogues that kept `main` are changed only when they next render through the new path, and the spec states that.
- **First slice:** load `catalogue.toml` in `render_pack_files` and `render_packs_to_dir`, and delete the independent description literal in `_aggregate_marketplace`.
- **Agent-only proof:** the parity test, extended to read the value that the render paths resolve from `catalogue.toml`.
- **Split off, not blocking:** the post-import rebind bound needs a Semgrep rule or a runtime assertion, which is separate rule-authoring work. The publisher `BRANCH` resolved-value layer waits until the publisher's import surface is next touched, which slice P2 or P4 of the brief may do.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

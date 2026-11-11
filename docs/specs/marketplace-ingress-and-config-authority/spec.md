# Spec: marketplace ingress and configuration authority

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0072, ADR-0079
- **Brief:** brief:catalogue-publication-delivery
- **Discovery:** none
- **Depends on:** none
- **Contract:** contracts/marketplace-entry.schema.json
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author
> corrects them in place as the work teaches, without an amendment and without
> a review round.

## Outcome

A catalogue maintainer who sets the marketplace branch and description in `catalogue.toml` gets exactly those values in every marketplace file the build emits, and malformed Git references or an empty branch are refused before any install route is resolved. An organisation's fork can no longer fall back to the upstream `claude-plugins-dist` constant by leaving a value empty.

## What Changes

- Marketplace entry `ref` and `sha` are validated as Git references — `contracts/marketplace-entry.schema.json` and its byte-identical `packages/agentbundle/agentbundle/_data/` copy.
- An empty `claude-plugin-branch` is refused when `catalogue.toml` loads — `packages/agentbundle/agentbundle/catalogue_tooling/config.py`.
- The public render paths resolve branch and description from `catalogue.toml` when it exists — `packages/agentbundle/agentbundle/render.py`, `build/main.py` and `catalogue_tooling/build.py`.
- `_aggregate_marketplace` stops carrying an independent description literal — `packages/agentbundle/agentbundle/build/self_host.py`.
- The scaffold writes the branch the builder uses — `packages/agentbundle/agentbundle/catalogue_tooling/toml_emit.py`.
- The envelope parity gate reads the values the render paths resolve — `tools/test_marketplace_envelope_parity.py`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable: the entry schema is a bundled contract and the loader refuses a value it accepted | `contracts/marketplace-entry.schema.json` and its `_data/` twin | eugenelim | `tools/catalogue/check_contract_parity.py` green | The twin is byte-identical |
| Release history | Applicable: `packages/agentbundle/**` changes | `packages/agentbundle/CHANGELOG.md`, following [`cut-a-package-release`](../../guides/how-to/cut-a-package-release.md) | eugenelim | A changelog entry for the change | The entry names the refused inputs |
| Decision rationale | Not applicable: ADR-0072 already fixes the advertised ref and the parity-gate control | ADR-0072 | none | none | No new decision record |

## Agent Rules

### Always do

- Carry an `Engine-Change-RFC:` trailer on the landing commit, citing ADR-0072 or writing `n/a` with the reason; `tools/lint-catalogue-curation-guard.py` checks that the trailer is present.
- Keep `contracts/marketplace-entry.schema.json` and its `_data/` twin byte-identical.
- Run `tools/test_marketplace_envelope_parity.py` before and after every change to a value it anchors.

### Ask first

- Edit `contracts/catalogue.schema.json`. It is a member of the published catalogue specification, so an edit follows RFC-0109 versioning.
- Change the signature of a public function in `agentbundle.render`.

### Never do

- Never add a new top-level dependency or module boundary.
- Never weaken a parity-gate layer to make a change pass.
- Never accept an empty branch by substituting a default.

## Testing Strategy

- **Reference validation:** TDD. A fixture set of valid and invalid references is checked against the schema and against `git check-ref-format --branch` as the oracle.
- **Empty branch refusal:** TDD, a loader test on a `catalogue.toml` fixture.
- **Render authority:** goal-based, exercised by an integration test that builds a fixture catalogue with and without `catalogue.toml` and compares the emitted marketplace file.
- **Parity and contract twins:** goal-based, `tools/test_marketplace_envelope_parity.py` and `tools/catalogue/check_contract_parity.py`.

## Acceptance Criteria

- [ ] A marketplace entry whose `source.ref` is empty, contains a character `git check-ref-format` forbids, or breaks its component rules is rejected by the schema, over a fixture set of at least 10 invalid and 6 valid references; the schema and the oracle agree on every fixture except the single string `@`, which the schema may refuse.
- [ ] A marketplace entry whose `source.sha` is not 40 lowercase hexadecimal characters is rejected, and a 40-character lowercase value is accepted.
- [ ] Loading a `catalogue.toml` whose `claude-plugin-branch` is empty raises a configuration error that names the key.
- [ ] Building a fixture catalogue whose `catalogue.toml` sets a branch and a description emits those exact values in the marketplace file from `render_packs_to_dir`, and the same build without `catalogue.toml` emits the builder defaults.
- [ ] `_aggregate_marketplace` has no description literal of its own, and `tools/test_marketplace_envelope_parity.py` fails if one is reintroduced.
- [ ] The branch that `agentbundle catalogue init` writes into a new `catalogue.toml` equals the branch the builder uses when no `catalogue.toml` exists.
- [ ] `tools/test_marketplace_envelope_parity.py` passes, and `tools/catalogue/check_contract_parity.py` and `check_spec_version.py` pass.

## Follow-ons

- eugenelim: a Semgrep rule or runtime assertion for a post-import rebind of the branch and description constants, parked as deferred scope in the brief.
- eugenelim: the publisher `BRANCH` resolved-value parity layer, taken when the publisher's imports are next touched.

## Assumptions

- Defaulted: Technical: an empty branch is refused in the loader and `contracts/catalogue.schema.json` is left unchanged — default: no catalogue specification release is needed; if wrong: a `minLength` edit to a published member needs an RFC-0109 versioned release (settled by: eugenelim).
- Defaulted: Product: the scaffold writes `claude-plugins-dist`, the builder's value, instead of `main` — default: this repository's `catalogue.toml` records that a build never published from `main`; if wrong: a scaffolded catalogue keeps `main` and the spec drops the scaffold criterion (settled by: eugenelim).
- Open: Technical: how a render path locates `catalogue.toml` without changing a public signature — default: the file beside the packs directory's parent when present, and the builder defaults when absent; if wrong: a new optional parameter, which is a public-interface change (settled by: eugenelim, before approval).

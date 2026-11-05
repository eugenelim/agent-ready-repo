# Brief: an organisation publishes into its catalogue through a reviewable, validated gate

- **Slug:** `catalogue-publication-delivery`
- **Received:** 2026-11-05
- **Owner:** eugenelim
- **Status:** Ready
- **Ready confirmed:** 2026-11-05 by eugenelim, lifecycle owner. Bound to the file as reviewed `Clean` by an independent delivery-brief review at commit `97221f5bb`; the later edits were wording corrections, recorded as nonmaterial by the lifecycle owner. Slice membership and status are the Spec map's; this line does not restate them.
- **Source / provenance:** Mode `repo-origin`; locator [`docs/product/intents/CAP-0007-catalogue-publication.md`](../intents/CAP-0007-catalogue-publication.md), cut into slices on 2026-11-05 from reproduced gaps in the code.
- **Parent intent:** capability:catalogue-publication

## Outcome

Marketplace input is validated before it can resolve an install route, one configuration authority drives every render path, publishing waits for a passing build and shows an approver what will ship, and each published pack carries a content digest a consumer can recover independently.

## Success metrics

- A marketplace entry with an invalid or empty `ref`, or a `catalogue.toml` with an empty `claude-plugin-branch`, is refused with a named error.
- `tools/test_marketplace_envelope_parity.py` still passes and reads the values the render paths resolve from `catalogue.toml`.
- `tools/lint-claude-plugin-publish-control.py` fails a workflow that publishes without a successful-build gate.
- Each marketplace entry carries a digest equal to the unit digest of that pack's built files.

## Scope / Non-goals

**In scope:**

- The four children of the capability: ingress validation, configuration authority, the publish trust boundary, and pack identity.

**Non-goals:**

- Release-archive digests (owned by `catalogue-wave5-release-integrity`), pinning `sha` to the published-branch commit (that hash exists only after the push, so the entry in `main` would change after every publish), the post-import rebind Semgrep rule, and any change to who holds repository settings.

## Proposed slices

Every slice is checked by an agent with no live service, credential, or human reviewer. Changes under `packages/agentbundle/**` carry an `Engine-Change-RFC:` trailer; the gate checks only that it is present, and recent commits cite an accepted record or write `n/a` with the reason.

| # | Slice | Agent-only verification | Depends on | Gating |
| --- | --- | --- | --- | --- |
| P1 | Ingress and configuration authority in one change (the two child intents share `build.py`, `config.py` and the entry schema, and the parity test covers both): Git reference patterns for `ref` and `sha`, a refused empty `claude-plugin-branch`, `catalogue.toml` loaded by `render_pack_files` and `render_packs_to_dir`, and the second description literal removed from `_aggregate_marketplace`. | Schema fixtures for valid and invalid references; config test for an empty branch; generated marketplace output compared before and after for a catalogue without `catalogue.toml` and for a scaffolded one; the envelope parity test; `tools/catalogue/check_contract_parity.py` and `check_spec_version.py` | none | Decisions recorded in the spec: the `toml_emit.py` scaffold default (recommended `claude-plugins-dist`, the builder's value; the scaffold writes `main` today); refuse the empty branch in the loader, or also add `minLength` to `catalogue.schema.json`. Only `catalogue.schema.json` is a member of the published catalogue specification (`contracts/catalogue-spec.toml`, frozen copy under `contracts/releases/catalogue/0.1/`), so an edit to it follows RFC-0109's versioning. `marketplace-entry.schema.json` has role `bundled` with no frozen copy, so an edit to it needs only a byte-identical `_data/` copy, which `check_contract_parity.py` checks |
| P2 | Publishing runs only after a successful build, using `workflow_run` with `conclusion == success`, and the lint asserts it. It edits the lint that the stale evidence feeds, so it lands after the evidence recapture below. | The lint's own tests with a passing and a failing fixture workflow; a check that the publish job builds the commit that passed | none | P2's spec drafts the amendment note on the AC35 constraint in `claude-plugin-hook-parity`; the owner's evidence recapture (decided 2026-11-05, due before 2026-11-10) must land first, because the lint fails after 2026-11-10 17:24 UTC |
| P3 | A separate non-gated workflow that writes an approver preview: packs changed against the published branch, plugins added or removed, and hook entries that will register. It never feeds the publish job. | A preview generator test over fixture before and after trees; a lint check that the publish job has no dependency on it | P2 | none |
| P4 | A per-pack content digest in each entry's `metadata` object, using the existing unit digest, with `metadata` added to the entry schema. | Build test: the entry digest equals the unit digest of the built files; schema fixtures | P1, P2 | Recorded upstream-schema result (see Assumptions). Depends on P1 because both edit `marketplace-entry.schema.json`, and on P2 because both edit the publisher and its lint; `metadata` is a change to a bundled contract, needing only the byte-identical `_data/` copy |

### Blocking prerequisite, owner action

- Recapture the publish-control evidence and run the ordinary-actor rejection canary (`tools/capture-publish-control-evidence.py`, which needs the publisher App key). It gates P2; the date is in P2's Gating cell.

### Deferred scope, owned by the maintainers, not part of P1 to P4

- A Semgrep rule or runtime assertion for a post-import rebind of the branch and description constants. It needs a decision that rule authoring is in scope; `sast-cwe-delta-review` is adjacent.
- The publisher `BRANCH` resolved-value parity layer, taken when P2 or P4 next touches the publisher's imports.

## Constraints / Appetite

Four to five sessions. P1 and P2 can run in parallel.

## Assumptions / Risks

- Upstream check, 2026-11-05: Claude Code's marketplace reference accepts `ref` and a 40-character `sha` on git sources, a `sha256` on `archive` sources, a free-form entry `metadata` object, and warns on unknown entry keys. A digest in `metadata` raises no warning.
- Riskiest assumption: the publish job can build from a `workflow_run` event. A `workflow_run` job starts on the default branch, so P2 verifies it checks out the built commit.

## Ready gaps (Draft only)

None.

## Spec map

| Spec | Status |
| --- | --- |

## Provenance

- Parent intent: see the preamble; capability [`CAP-0007-catalogue-publication.md`](../intents/CAP-0007-catalogue-publication.md).
- Children: [`marketplace-ingress-validation`](../intents/marketplace-ingress-validation.md), [`marketplace-config-single-authority`](../intents/marketplace-config-single-authority.md), [`plugin-publish-trust-boundary`](../intents/plugin-publish-trust-boundary.md), [`claude-marketplace-pack-identity`](../intents/claude-marketplace-pack-identity.md).

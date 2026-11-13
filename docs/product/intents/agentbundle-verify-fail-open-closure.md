# Agentbundle verify fail-open closure

- **Slug:** `agentbundle-verify-fail-open-closure`
- **Status:** Fulfilled
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Fulfilled:** 2026-11-12 eugenelim: closed validator-import and missing-field skips using CAT-V-003 and CAT-V-005 with zero new codes; 86 targeted tests pass, including real zipapp resource failures.
- **Shaping-reviewed:** 2026-11-05
- **De-risked:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [spec/agentbundle-engine-stragglers AC12](../../specs/agentbundle-engine-stragglers/spec.md)

## Outcome

`agentbundle catalogue verify` reports bounded diagnostics whenever pack-schema validation or version-parity inputs cannot be validated.

## Opportunity

Two verifier paths previously reported clean when they could not validate required metadata. Both now emit errors using existing diagnostic codes.

## What this absorbs

### pre-existing-pack-schema-validator-fail-open

`_step_pack_schema` in `packages/agentbundle/agentbundle/catalogue_tooling/verify.py` now emits a bounded `CAT-V-003` error when the validator import fails. Existing unit tests already cover missing, malformed, and undecodable bundled schemas. Real zipapp tests now cover healthy, missing, malformed, and undecodable resources through the archive reader. The relocated-package integration test remains separate evidence. Wheel behavior remains unverified; this slice uses the authorized offline zipapp fallback.

### verify-parity-silent-skip-codes

`_step_version_parity` now emits `CAT-V-005` for each missing name or version in either input, naming both the input and field. Matching inputs stay clean; mismatch and malformed-input handling remain intact. Tests cover each missing field, both fields missing, matching inputs, and mismatches. Zero new diagnostic codes are introduced.

## Non-goals

- The separate documented `ImportError` fail-soft in the plugin-manifest engine-module check of `verify.py`: it is intentional and stays.
- New verifier steps, and any change to other `CAT-V` codes.

## Assumptions

- **Riskiest assumption:** a missing-field parity skip can be closed with a message on the existing `CAT-V-005`, and an import failure can be forced in a test. Both were reproduced 2026-11-05 by making `agentbundle.build.validate` unimportable and by building a pack whose `plugin.json` lacks a version; the same two fixtures become the failing tests.

- `CAT-V-003` remains the bounded code for pack-schema validation failure, and `CAT-V-005` for version-parity input failure; missing names or versions reuse `CAT-V-005`, with zero new diagnostic codes.

## Readiness

- **Route:** direct-light, one session. The change closes two silent skips and adds tests, with zero new diagnostic codes.
- **Reproduced 2026-11-05:** with `agentbundle.build.validate` made unimportable, `_step_pack_schema` returns `[]` (clean). With a `plugin.json` that lacks `version`, or lacks both fields, `_step_version_parity` returns `[]`.
- **Design answer:** emit `CAT-V-003` for the import branch, matching the bundled-schema failure branch. For a missing name or version, reuse `CAT-V-005` with a message naming the input and missing field. This settles the earlier contradictory one-new-code wording: zero new codes are required. Leave the separate `ImportError` fail-soft in the plugin-manifest engine-module check alone: it is documented as intentional.
- **Authority:** earlier commits to `verify.py` cite RFC-0076 and RFC-0109 in the `Engine-Change-RFC:` trailer.
- **Agent-only proof:** 86 tests pass across the verify unit, bundled-contract error, relocated-package, external portability, and zipapp suites. Integration still owns the six-file engine release edits and the `Engine-Change-RFC:` trailer naming accepted authority.

## De-risk result

- **Date:** 2026-11-05.
- **Ran:** with `agentbundle.build.validate` made unimportable, `_step_pack_schema` was called; then `_step_version_parity` was called on a temporary pack whose `plugin.json` has `{"name":"p1"}` and then `{}`. `CAT-V-005` is already used five times in `verify.py`.
- **Observed:** the import-failure case returned `[]`; the missing-version case returned `[]`; the missing-both case returned `[]`. All three read as clean.
- **Verdict:** supports the assumption. Both gaps reproduce with small fixtures and the existing `CAT-V-005` code can carry the missing-field message. The same fixtures become the failing tests.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

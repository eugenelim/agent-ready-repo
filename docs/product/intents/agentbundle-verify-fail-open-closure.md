# Agentbundle verify fail-open closure

- **Slug:** `agentbundle-verify-fail-open-closure`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **De-risked:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim
- **Governed by:** [spec/agentbundle-engine-stragglers AC12](../../specs/agentbundle-engine-stragglers/spec.md)

## Outcome

`agentbundle catalogue verify` reports bounded diagnostics whenever pack-schema validation or version-parity inputs cannot be validated.

## Opportunity

Two verifier paths report clean or continue when their inputs cannot be examined, which hides a failure in validation intended to protect published pack metadata.

## What this absorbs

### pre-existing-pack-schema-validator-fail-open

`_step_pack_schema` in `packages/agentbundle/agentbundle/catalogue_tooling/verify.py` returns an empty diagnostic list when `from agentbundle.build.validate import validate` raises `ImportError`, so the step reports clean without validating. A bundled-schema load failure (`OSError` or `ValueError` from `_load_bundled_json("pack.schema.json")`) already emits a bounded `CAT-V-003` error. Emit the same bounded `CAT-V-003` error for the import branch and cover wheel and zipapp resource failures. The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. Unblocks when the bounded failure diagnostic and resource-failure coverage land; the trailer applies at commit time.

### verify-parity-silent-skip-codes

`_step_version_parity` in the same file still skips a comparison silently when `pack.toml` or `plugin.json` lacks a name or version: the checks `if pt_name and pj_name and pt_name != pj_name` and `if pt_version and pj_version and pt_version != pj_version` let a missing field bypass comparison. Unreadable or malformed parity inputs already emit `CAT-V-005` and move to the next pack. Define bounded diagnostic codes for the missing-field skip and close it with the import branch above. The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. Unblocks when both skip paths emit the defined bounded diagnostics; the trailer applies at commit time.

## Non-goals

- The separate documented `ImportError` fail-soft in the engine-module check (near line 1269 of `verify.py`): it is intentional and stays.
- New verifier steps, and any change to other `CAT-V` codes.

## Assumptions

- **Riskiest assumption:** a missing-field parity skip can be closed with a message on the existing `CAT-V-005`, and an import failure can be forced in a test. Both were reproduced 2026-11-05 by making `agentbundle.build.validate` unimportable and by building a pack whose `plugin.json` lacks a version; the same two fixtures become the failing tests.

- `CAT-V-003` remains the bounded code for pack-schema validation failure, and `CAT-V-005` for version-parity input failure; the parity code for a missing name or version will be defined by the AC12 implementation.

## Readiness

- **Route:** direct-light, one session. The change is two diagnostics and their tests, with no new interface beyond one diagnostic code.
- **Reproduced 2026-11-05:** with `agentbundle.build.validate` made unimportable, `_step_pack_schema` returns `[]` (clean). With a `plugin.json` that lacks `version`, or lacks both fields, `_step_version_parity` returns `[]`.
- **Design answer:** emit `CAT-V-003` for the import branch, matching the bundled-schema failure branch. For a missing name or version, the spec's AC12 note says a new code is needed; the smallest answer is `CAT-V-005` with a message naming the missing field, and a distinct code only if review asks for one. Leave the separate `ImportError` fail-soft near line 1269 alone: it is documented as intentional.
- **Authority:** earlier commits to `verify.py` cite RFC-0076 and RFC-0109 in the `Engine-Change-RFC:` trailer.
- **Agent-only proof:** the two reproductions above become failing tests, then pass.

## De-risk result

- **Date:** 2026-11-05.
- **Ran:** with `agentbundle.build.validate` made unimportable, `_step_pack_schema` was called; then `_step_version_parity` was called on a temporary pack whose `plugin.json` has `{"name":"p1"}` and then `{}`. `CAT-V-005` is already used five times in `verify.py`.
- **Observed:** the import-failure case returned `[]`; the missing-version case returned `[]`; the missing-both case returned `[]`. All three read as clean.
- **Verdict:** supports the assumption. Both gaps reproduce with small fixtures and the existing `CAT-V-005` code can carry the missing-field message. The same fixtures become the failing tests.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

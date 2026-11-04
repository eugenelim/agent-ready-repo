# Agentbundle verify fail-open closure

- **Slug:** `agentbundle-verify-fail-open-closure`
- **Status:** Draft
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

## Assumptions

- `CAT-V-003` remains the bounded code for pack-schema validation failure, and `CAT-V-005` for version-parity input failure; the parity code for a missing name or version will be defined by the AC12 implementation.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

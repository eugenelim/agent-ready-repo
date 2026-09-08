# Agentbundle verify fail-open closure

- **Status:** Draft
- **Level:** feature
- **Authority:** [spec/agentbundle-engine-stragglers AC12](../../specs/agentbundle-engine-stragglers/spec.md)

## Outcome

`agentbundle catalogue verify` reports bounded diagnostics whenever pack-schema validation or version-parity inputs cannot be validated.

## Opportunity

Two verifier paths report clean or continue after invalid inputs, which hides a failure in validation intended to protect published pack metadata.

## What this absorbs

### pre-existing-pack-schema-validator-fail-open

Current `_step_pack_schema` reports clean when the validator import or bundled schema load fails. At `packages/agentbundle/agentbundle/catalogue_tooling/verify.py:182`, `except (OSError, ValueError):` leads to an empty diagnostic list; the validator-import branch also returns empty on `ImportError`. Emit a bounded `CAT-V-003` error and cover wheel and zipapp resource failures. The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. Unblocks when the bounded failure diagnostic and resource-failure coverage land; the trailer applies at commit time.

### verify-parity-silent-skip-codes

Current version parity silently skips missing name/version fields and parse exceptions, although other steps usually catch malformed input. At `packages/agentbundle/agentbundle/catalogue_tooling/verify.py:367`, `if pt_name and pj_name and pt_name != pj_name:` permits missing fields to bypass comparison; malformed parity inputs enter an exception path that emits `CAT-V-005` but continues. Define bounded diagnostic codes and close both skip paths together. The fix touches protected `packages/agentbundle/**`; its landing commit needs an `Engine-Change-RFC:` trailer naming a real RFC. Unblocks when both skip paths emit the defined bounded diagnostics; the trailer applies at commit time.

## Assumptions

- `CAT-V-003` remains the bounded code for bundled-schema load failure; the parity codes will be defined by the AC12 implementation.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

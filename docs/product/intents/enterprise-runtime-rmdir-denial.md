# Verify cleanup-sensitive tests in a supported runtime

- **Status:** Draft
- **Level:** feature

## Outcome

Cleanup-sensitive tests and rendered-site gates can run in CI or a managed profile that permits temporary-directory cleanup without weakening production confinement behavior.

## Opportunity

The managed enterprise runtime denies Python `os.rmdir` under approved `/private/tmp` roots, causing cleanup failures after behavior assertions run.

## What this absorbs

### pre-existing-enterprise-python-rmdir

Pre-flight on 2026-08-24 found that the managed enterprise runtime denies Python `os.rmdir`, including under approved `/private/tmp` roots and after an escalated test invocation. The result reproduces byte-for-byte at `HEAD` in `test_symlink_escape_stops_before_any_callback`, `test_t2_positive_dispatch_and_reconciliation_surface`, `test_t2_active_and_shipped_specs_validate_sibling_plan`, all 15 cases in `packs/core/tests/skills/receive-brief/test_lint_brief_coverage.py`, `tools/test_check_guide_index.py::test_underscore_prefixed_pack_is_not_active`, and the two verify-catalogue pipeline cases in `packages/agentbundle/tests/unit/test_catalogue_wave2_validation.py`. Each failure occurs in temporary-fixture cleanup or reset after the behavior assertion has run.

`docs/specs/local-pytest-process-optimization/spec.md:189` records that a standalone attempt again exited 2 in the same first process with widespread `PermissionError: os.rmdir` failures. Current reproduction is `pytest packages/agentbundle/tests/unit/test_catalogue_wave2_validation.py -q`: 29 tests ran, 27 passed, and 2 cleanup failures occurred at `os.rmdir` in temporary render trees.

Run these cleanup-sensitive cases in CI or a managed profile that permits Python to remove empty temporary directories. Do not weaken production confinement behavior or translate the policy denial into a pass. The denial also prevents in-place self-host/catalogue verification cleanup, and Vite cannot rename its workspace cache directory. Locally use clean-root projection parity and source/link suites; leave destructive cleanup and rendered-site gates to CI or a supported profile. Unblocks when that supported verification environment is available.

## Assumptions

- A supported verification environment must permit Python cleanup of empty temporary directories while preserving the production confinement contract.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

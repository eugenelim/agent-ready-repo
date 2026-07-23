# Spec: workspace-toml-adopter-seeding

Mode: light (no risk trigger fired)

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Constrained by:** RFC-0069 (workspace.toml adopter seeding)
- **Related:** RFC-0002 (EXCLUDED_PATTERNS / Manual semantics), RFC-0001 (seed delivery contract)

## Objective

Add `workspace.toml` as a minimal, schema-commented core-pack seed so adopters
receive a parseable coordination file on `agentbundle install`, closing the gap
where the installed CONVENTIONS.md references `workspace.toml [backlog].open`
but the file is never created on install.

## Acceptance Criteria

- [x] AC1 `packs/core/seeds/workspace.toml` exists and contains the `[backlog]`
  section header as a literal string.
- [x] AC2 `REQUIRED_PLACEHOLDERS` in `tools/lint-catalogue-seeds.py` contains
  `"workspace.toml": ("[backlog]",)` and `lint-catalogue-seeds.py --root .`
  exits 0.
- [x] AC3 `EXCLUDED_PATTERNS` in `self_host.py` contains `"workspace.toml"` so
  `make build-self` does not overwrite the repo's curated coordination file.
- [x] AC4 The golden snapshot `core.paths.txt` lists `workspace.toml`.
- [x] AC5 `test_install_seed_delivery.py` asserts `workspace.toml` is delivered.
- [x] AC6 `test_self_host_check.py` asserts `workspace.toml` is excluded via
  `_is_excluded` and a `_project_seeds` round-trip confirms a curated on-disk
  `workspace.toml` survives reprojection byte-identical.
- [x] AC7 Core pack version bumped to `0.13.6` and a `[Unreleased]` changelog
  entry added.

## Task list

1. Create `packs/core/seeds/workspace.toml` (minimal template: schema comments +
   `[backlog]` section).
2. Add `"workspace.toml": ("[backlog]",)` to `REQUIRED_PLACEHOLDERS` in
   `tools/lint-catalogue-seeds.py`.
3. Add `"workspace.toml"` to `EXCLUDED_PATTERNS` in `self_host.py` near the
   `"docs/CHARTER.md"` entry.
4. Bump core pack version to `0.13.6` and add `[Unreleased]` changelog entry.
5. Regenerate golden snapshot (`UPDATE_GOLDEN=1`).
6. Add/update tests: seed delivery assertion + EXCLUDED_PATTERNS assertion.
7. Run gates (lint-catalogue-seeds, pre-pr, build-check locally).

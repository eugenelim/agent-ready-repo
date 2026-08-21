# Manual QA — distribution route contract

Date: 2026-08-21

## Twice-built catalogue output

The normal `agentbundle.build build` entry point ran twice from the repository
pack source into separate approved `/private/tmp` roots with bytecode writes
disabled and the package source on `PYTHONPATH`.

- Both runs exited 0 and named the same seven repo-only Claude-route exclusions.
- Each output root contained exactly `apm/` and `claude-plugins/`.
- The APM tree contained 991 regular-file/symlink entries; the Claude tree
  contained 693.
- Lossless inventories (relative path, type, regular-file mode and bytes, or
  symlink target) compared equal across the two runs: `twice-identical=True`.
- The checked-in representative route oracle passed all four golden tests both
  before and after migration, including byte/mode/link mutation sensitivity and
  the safe relative-link witness on both routes.

## Automated gates

- Focused distribution-route, adapter-contract, and marketplace tests: passed.
- Entire `packages/agentbundle/tests/build_pipeline/` suite: passed.
- Final targeted route/render/integration regression set: passed, including
  route-aware render selection, aggregate permission refusal, admitted-pack
  preflight ordering, actionable recipe diagnostics, and unsafe link refusal.
- Full `packages/agentbundle/tests/` suite: all tests completed; three unrelated
  tests failed only because the managed permission profile denies reads of all
  `.pem` files. Two failures were pip/ensurepip certificate-bundle reads and one
  deliberately created a `.pem` fixture. No product assertion failed.
- `tools/catalogue/check_contract_parity.py`: passed with 16 byte-identical
  public contracts.
- `make lint-ruff`: passed.
- `make build-self FORCE=1`: passed; `FORCE=1` bypassed only the expected dirty
  worktree refusal for this uncommitted implementation session.
- `SKIP_SAST=1 make build-check`: exited 0 and passed every offline build,
  drift, lint, construction-test, and parity stage. Per the command's own
  warning, this is not a full SAST/SCA pass because the plan-authorized local
  shortcut skipped that final scanner leg.
- Final adversarial, quality, and security re-reviews: all reported
  `Clean — ready to commit.`

## Scope audit

`git diff --name-only` showed no `packs/**/pack.toml`, plugin manifest, new
distribution output directory, or publisher-workflow change. AgentBundle alone
moved from 0.38.6 to 0.39.0. Direct-install adapter tests remain in the full
package run; the route golden proves package-output compatibility.

## Project knowledge disposition

No reusable project observation was admitted at the spec-approved or
plan-locked semantic gates: the work used only durable RFC/ADR/spec contracts
and implementation-local test evidence. Named no-capture; no knowledge diff.

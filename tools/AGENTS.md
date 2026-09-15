# Tools instructions

Applies to `tools/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

- New additions to `tools/` must be pure-stdlib Python `.py` files. Existing
  `.sh` files stay; this rule applies forward.
- Path triggers in `.github/workflows/docs.yml` must invoke matching scripts as
  `python3 <script>`.
- The repo-only hook implementation and wiring guide is
  [`tools/hooks/README.md`](hooks/README.md). Keep this pointer out of shipped
  pack content because adopters do not receive the maintainer guide.
- A hyphenated `tools/test-lint-*.py` is a standalone entry point, not a pytest
  surface. pytest collects `test_*.py`, so the hyphen makes it uncollectable even
  when named explicitly, and a gate list assembled from pytest runs omits it in
  silence. Run it directly after changing what it governs. Underscored
  `tools/test_*.py` files are ordinary pytest suites.
- `tools/lint-catalogue-curation-guard.py` skips its path gate when it has no
  diff base, so it passes locally and can still fail in CI. Verify it with
  `--base origin/main`. It protects `packages/agentbundle/` and
  `packs/credential-brokers/`: a commit touching either needs an
  `Engine-Change-RFC:` trailer, conventionally `n/a — <justification>` when no
  RFC governs the change.
- Adding a step to `.github/workflows/build-check.yml` requires a matching
  `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py`, naming either the make
  target that covers it locally or why none can.

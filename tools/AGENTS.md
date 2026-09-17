# Tools instructions

Applies to `tools/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

- New additions to `tools/` must be pure-stdlib Python `.py` files. Existing
  `.sh` files stay; this rule applies forward.
- Path triggers in `.github/workflows/docs.yml` must invoke matching scripts as
  `python3 <script>`.
- The repo-only hook implementation and wiring guide is
  [`tools/hooks/README.md`](hooks/README.md). Keep this pointer out of shipped
  pack content because adopters do not receive the maintainer guide.
- A hyphenated `tools/test-lint-*.py` is a standalone entry point. A directory
  sweep collects none of them: the default `python_files` glob is `test_*.py`,
  the hyphen fails it, and `pyproject.toml` sets no override — so a gate list
  assembled from `pytest tools/` omits them in silence. Naming one explicitly
  does collect whatever `test_*` functions it defines, so the two routes
  disagree; do not read a green sweep as covering them. Some of these files
  also define no `test_*` function at all and collect zero nodes either way
  (`tools/test-lint-ci-parity.py` runs its 143 cases from `main()`). Run them
  directly after changing what they govern. Underscored `tools/test_*.py` files
  are ordinary pytest suites.
- A new single-rule lint belongs on the shared drivers, not in a fresh copy of
  the plumbing: `tools/lint_harness.py` owns the file walk, the report and the
  exit status, and `tools/selftest_harness.py` owns the self-test loader and
  case runners. Each rule keeps its own predicate, messages and rationale.
- `tools/lint-catalogue-curation-guard.py` skips its path gate when it has no
  diff base, so it passes locally and can still fail in CI. Verify it with
  `--base origin/main`. It protects `packages/agentbundle/` and
  `packs/credential-brokers/`: a commit touching either needs an
  `Engine-Change-RFC:` trailer, conventionally `n/a — <justification>` when no
  RFC governs the change.
- Adding a step to `.github/workflows/build-check.yml` requires a matching
  `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py`, naming either the make
  target that covers it locally or why none can.

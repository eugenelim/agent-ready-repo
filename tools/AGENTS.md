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
- `tools/lint-ci-parity.py` holds two rosters, one per direction, and the step
  roster carries two axes. Editing any of these surfaces obliges its entry:
  - **Adding a step to `.github/workflows/build-check.yml`** requires a
    `STEP_DISPOSITION` entry naming either the make target that covers it
    locally or why none can.
  - **Declaring that step's phase and dependencies** requires the same
    `STEP_DISPOSITION` entry to name either `PROVISIONING(id=...)` or
    `CHECK(needs=(...), evidence=...)` on its phase-and-dependency axis.
  - **Adding or moving a line in the Makefile's `run-test-suite` define**
    requires a `SUITE_DISPOSITION` entry per target on that line, naming the
    pull-request check that gates the suite (`PR_GATED`), the condition under
    which one does (`PR_GATED_IF`), or why none does (`NO_PR_GATE`). Spell a
    path in the workflow exactly as the define spells it: both directions
    compare written paths, so a parent directory matches neither and reports a
    real gate as absent.
  Neither roster's reasons are machine-checked for truth, only for presence —
  that is a human-review control, and the module docstring says so.

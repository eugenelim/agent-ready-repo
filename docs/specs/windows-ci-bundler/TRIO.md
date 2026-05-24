# windows-ci-bundler — TRIO

Step 1 of a five-step Windows-support action plan. Adds a `windows-latest`
job to `.github/workflows/build-check.yml` so the Phase-3 bash→Python port
(PR #71) is verified on real Windows in CI and can't silently regress.

## Files I'll touch

- `.github/workflows/build-check.yml` — add a second top-level job
  `build-check-windows` running the Python-portable subset.

That's the entire diff surface. No source, no tests, no docs beyond this scratch.

## "Done when"

- YAML parses (`python -c "import yaml; yaml.safe_load(...)"`).
- `make build-check` locally still green (Linux job behaviour unchanged).
- `python tools/hooks/pre-pr.py` locally green (no drift in repo state).
- CI gives us a fresh windows-latest job slot on the PR. The actual
  Windows-green validation happens on the PR's CI run, not locally —
  we're on macOS.

## What I am NOT changing

- The existing Linux `build-check` job — preserved byte-for-byte.
- Any hook source, any linter, any test file.
- The `rg`-based scrubs (source-attribution scrub, Rail-C marker scrub),
  the `evals.json` carry-over disposition step, or the `sudo apt-get`
  ripgrep install — all stay Linux-only. Porting them is explicitly
  out of scope (subsequent steps in the user's five-step plan).

## Declined patterns

- *Tempted to convert the existing job into an `os` matrix.* Declining —
  adds `if: runner.os == 'Linux'` gating on every existing step. Option B
  (a second top-level job) is the explicit, no-conditional shape and
  preserves the Linux job byte-for-byte. Less clever, more obvious.
- *Tempted to port the `rg` scrubs to Python so they run on Windows too.*
  Declining — scope creep; the user has explicitly named four other PRs
  in the action plan and asked that they stay separate. The `rg` scrubs
  are AC2/AC3 from the converters spec and belong to a focused port PR.
- *Tempted to add a `python -m pytest packages/agentbundle/` umbrella run
  on Windows.* Declining — slower, includes Linux-only fixture suites
  (e.g. `test_install_*` that shell `bash`-only test scripts). The prompt
  names the two specific test files to run; honour that.
- *Tempted to add a `pip cache` action / setup-python `cache: pip` flag.*
  Declining — premature optimisation; no second caller for this pattern
  yet, and Windows runners install fast enough on a single-PR cadence.
- *Tempted to add a `name:` decoration on every step.* Declining — keeps
  the diff smaller; the existing Linux job's step names are aspirational
  not mandatory and step `run:` text is self-documenting.

## Why prefer (B) — second top-level job — over (A) matrix?

The Linux job is the green gate today. Any matrix-conversion that goes
wrong (a forgotten `if:`, a renamed env var, a Windows-only failure mode
leaking into the Linux path) risks regressing the existing build. Two
top-level jobs are independently scheduled, independently visible, and
share no YAML except the trigger block. That isolation is the value.

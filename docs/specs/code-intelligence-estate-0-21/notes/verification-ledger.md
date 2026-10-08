# Verification ledger — code-intelligence-estate-0-21

Observations from execution. The binary under test is `wicked-estate 0.21.0`,
built on 2026-10-07 with `cargo install wicked-estate --version 0.21.0 --locked --root /tmp/we021`.
No `wicked-estate` was on the maintainer's `PATH`, and none was installed there.

## Base

- The branch was fast-forwarded onto `46e064fc6` (#1517, golden composition example) before PLAN finished.
  That release took pack version 0.1.4, so this change releases 0.1.5. #1517's preflight sample files under
  `evals/files/` were added to T2.

## T1 — suites on the 0.21.0 surface

- With the 0.21.0 binary first on `PATH`: 12 failed, 142 passed. The 12 are exactly the T1 Done-when list.
- `make lint-ruff lint-mypy`: pass. `tools/test-lint-pack-test-boundary.py`: 158 cases passed.

## T2 — prose teaches 0.21.0

- The implementer's own run had the binary off `PATH` (44 live tests skipped). The controller re-ran with the
  binary first on `PATH`: 3 failed, 151 passed. The 3 are the T3-owned eval and version tests.
- Guide commands: `scanner='pin'` exit 0; `scanner='retired'` exit 0.
- Controller corrections after reading the diff: removed history-tense "now" from `gaps.md` (two sentences) and
  `README.md`; the README limits bullet names all three MCP-only domains.

## T3 — evals, release, projection

- The controller applied T3; an implementer then verified it against its Done-when and changed nothing. Eval 6's
  third assertion says rows "omit per-dependent depth", not the plan's "no per-row depth or confidence" wording,
  because that wording trips the eval-6 check's negation guard; the meaning is the same.
- On the committed head `f00bd8162`: `agentbundle catalogue self-host --root . --write` left `git status --porcelain`
  empty; `agentbundle catalogue verify --root .` ok.
- With the binary first on `PATH`: pack suites plus `tools/test_check_output_readability.py` 190 passed in 14.8 s.
  `tests/roster/test_verification_ledger_contract.py -k core_release_heading` 1 passed; the changelog projection
  tests 3 passed.

## End to end

In a scratch git repository holding a two-file fixture indexed with 0.21.0:

- `estate_preflight.py --check` printed `status: ready`, `version: 0.21.0`, exit 0.
- `wicked-estate lineage --symbol <entry id>` listed `handle` at depth 1 and `helper` at depth 2 within depth 8,
  with a `confidence:` line.
- `wicked-estate traverse helper --direction dependents` printed the walk with per-node depths.
- `wicked-estate rank --seeds <entry id> --limit 3` printed three rows and `STALENESS: 0 commits since last index`.

## Reusable learning

No capture. The one trap worth keeping — a seeded `rank` is a graph-wide bias, not a filter — is now in the pack's
own references.

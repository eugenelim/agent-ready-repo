# Verification ledger — code-intelligence-estate-0-18

Observations from execution. The binary under test is `wicked-estate 0.18.0`,
built with `cargo install wicked-estate --version 0.18.0 --locked --root <scratch>`
on 2026-10-02. The installed `wicked-estate` on the maintainer's `PATH` (0.16.7)
was not replaced.

## T1 — suites on the 0.18.0 surface

- With the 0.18.0 binary first on `PATH`, `python3 -m pytest packs/code-intelligence/tests -q`
  gave 10 failed, 105 passed in 44 s. The 10 failures are exactly the T1 Done-when list.
- Deviation from the task row, corrected by the controller: the implementer planted one
  stale sentence per pattern group (6). The plan's Design asks for one per pattern. The
  controller added sentences so all 26 patterns are exercised, plus an assertion that
  fails when a pattern has no stale sample. The planted-sample tests pass.
- `python3 tools/test-lint-pack-test-boundary.py`: pass, 154 cases.
- `make lint-ruff lint-mypy`: pass.

## T2 — prose teaches 0.18.0

- With the 0.18.0 binary first on `PATH`: pack suites 2 failed, 113 passed. The two
  failures are the T3-owned eval and version tests.
- Guide commands: `scanner='pin'` exit 0; `scanner='retired'` exit 0.
- `tools/test_check_output_readability.py`: 36 passed. `make lint-ruff lint-mypy`: pass.
- Controller corrections after reading the implementer's diff:
  - `capability-map.md` stated MCP `TraverseGraph` `max_nodes` max 5000. Upstream's
    v0.18.0 conformance schema says max 1000 (5000 is `Path`). Corrected to 1000.
  - Removed history-tense wording ("now returns", "was added in 0.18.0", "is now
    reported") and the guide's "What changed in 0.18" section; the changelog owns history.
  - README "Honest about limits" listed a reported depth cut as a limit; replaced it
    with a real remaining gap (lineage and rules discovery are MCP-only).
  - `gaps.md` §12 Completeness verdict set to Direct, since all three limits are now
    reported; a stray backtick fixed.
  - `capability-surface.md` gained a "What the CLI reports about completeness" section;
    its maturity row no longer implies `path` was exercised on a real index.
- Bundled fix (implementer): `tools/test_check_output_readability.py` expected 22
  publishable packs; `packs/*/pack.toml` resolves 25 directories, 23 non-underscore,
  and the test fails on `HEAD` with 23. The count is now 23.

## Manual QA — the real artifact end to end

In a scratch git repository holding the three-file fixture, with the updated
`estate_preflight.py`:

- 0.18.0 first on `PATH`, no index: `status: index-absent`, exit 3, remediation names `wicked-estate index <repo>`.
- After `wicked-estate index .`: `status: ready`, `version: 0.18.0`, exit 0.
- The maintainer's installed 0.16.7: `status: version-below`, `required: 0.18`,
  remediation `cargo install wicked-estate --version 0.18.0 --locked`, exit 4.
- `wicked-estate path entry helper`: "2 hop(s) from 'entry' to 'helper':" then
  `entry (caller.py:3) -> handle (core.py:4)  [Calls] confidence 0.63 (import-map-resolver)` and
  `handle (core.py:4) -> helper (core.py:1)  [Calls] confidence 0.65 (scoped-name-resolver)`.
- `wicked-estate blast-radius helper --depth 1`: coverage line ends
  "CUT AT depth=1 — more dependents exist beyond 1 hops, re-run with a larger --depth".

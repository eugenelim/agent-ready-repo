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

## Review round 1 fixes (owner authorized all 11 findings, 2026-10-03)

Evidence for the two findings the adjudicator could not settle:

- `wicked-estate path nope helper --json` (0.18.0, fixture) returns
  `{"depth_bounded":false,"found":false,"from":"nope","hops":[],"node_bounded":false,"to":"helper","unresolved":"from"}`
  and exits 0 — the same flags as a searched absence. The contract suite now asserts
  `found`, `depth_bounded` and `node_bounded` are all false in that case.
- Upstream v0.18.0 `crates/wicked-estate-retrieve/src/lib.rs`, `Path::invoke`, returns
  `{hops, found, depth_bounded, node_bounded, unresolved}` with no `from`/`to`; endpoints
  carry `{symbol, name, kind, file, line, line_1based}`. No `Path` response schema ships.
- `wicked-estate path caller.py helper` (0.18.0, fixture) returns three hops, the first
  `caller.py (caller.py:1) -> entry (caller.py:3)  [Contains] confidence 1.00 (tree-sitter)`:
  `path` follows non-call edges.
- Upstream v0.18.0 MCP `BlastRadius` input schema has only `depth` and `symbol`; the CLI
  `path` arm hardcodes its node budget. No surface offers a node-budget control.

Mutation check: setting `PINNED_VERSION = "0.18.1"` turns
`test_required_pin_equals_preflight_pinned_version` red (1 failed); restoring it turns it green.

## Final run on the fixed head

- Binary first on `PATH`: `wicked-estate 0.18.0 — usage:`.
- `python3 -m pytest packs/code-intelligence/tests tools/test_check_output_readability.py -q`: 152 passed.
- Guide commands: `scanner='pin'` exit 0; `scanner='retired'` exit 0.
- `make lint-ruff lint-mypy`: pass. `tools/test-lint-pack-test-boundary.py`: 154 passed.
  `tools/validate_guides.py`: OK.

## Review round 2 fixes

- The direct-versus-transitive rule now reads identically in `evidence.md`, `gaps.md`,
  `capability-map.md`, `investigation-patterns.md` and `agents/impact-analyst.md`: the
  difference is the complete transitive set only when the full run reports no cut
  (`truncated_dependents` 0, `depth_horizon_reached: false`, `node_cap_reached: false`)
  and the `--depth 1` run reports `truncated_dependents` 0; otherwise a floor.
- `gaps.md` §11 heading and summary row scope the schema-derived label to MCP only.
- Gates after the fix: pack suites + readability 152 passed (0.18.0 first on `PATH`);
  guide commands exit 0 and 0; `make lint-ruff lint-mypy` pass.

## Review round 3 fixes

- The direct-versus-transitive rule now lives once, in `references/evidence.md`
  § Direct and transitive dependents, with three cases: both runs uncut (complete
  split), only the full run cut (floor within `searched_depth`), the `--depth 1` run
  truncated (no split). `gaps.md`, `capability-map.md`, `investigation-patterns.md` and
  `agents/impact-analyst.md` point to it instead of restating it.
- `example-prompts.md` states `node_cap_reached` false and an untruncated `--depth 1`
  run before giving the 12 / 35 split.
- Gates: 152 passed (0.18.0 first on `PATH`); guide commands exit 0 and 0; lint pass.

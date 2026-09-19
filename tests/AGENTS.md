# AGENTS.md — `tests/`

Applies to `tests/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

`packages/AGENTS.md` owns the table of which assertion belongs in which tree.
This file owns what living here obliges you to do, and why the boundary is not
merely a convention.

## A repository-level assertion cannot live in a package test tree

`packages/agentbundle/tests/` is packaged into the `agentbundle` sdist and re-run
against an extracted workspace holding only the package — no `contracts/`, no
`packs/`, no `docs/`, no `catalogue.toml`. A test there that reads a repository
path passes locally and fails the sdist artifact gate, which is what
`gate-export-boundary`, `build-and-smoke` and `make build-check` are reporting
when they raise `FileNotFoundError` on a path that plainly exists.

Put the repository-level half in `tests/roster/`, anchored at
`Path(__file__).resolve().parents[2]`. Leave the package-level behaviour in the
package suite, exercised against fixtures rather than the real tree.

The same boundary applies downward: a test under `packs/<pack>/tests/` may not
read above its own pack, and `tools/test-lint-pack-test-boundary.py` enforces it.
Check the reach before relocating one — a test whose paths all sit inside the
pack is pack-local and should re-anchor at the pack instead of moving.

## Roster steps are named and placed by hand

`gate-main` collects every roster module through one bulk
`python -m pytest tests/ -q` step (`.github/workflows/build-check.yml`), so a new
file does run on a pull request — but that step reports the failure as its own.
Adding `tests/roster/test_x.py` obliges three further edits, each guarded
separately:

1. a step in `.github/workflows/build-check.yml` naming the file, placed **above**
   that bulk step. The job is fail-fast with no step-level `if:`, so a named step
   below the bulk step never runs and attributes nothing;
2. a matching `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py`.
   `LOCAL("test-after-build-check")` is the right value for roster, because that
   target's `run-test-suite` includes `pytest tests/ -q`;
3. an entry in `.workspace-prune-protected.toml` when the test names a
   `docs/specs/<slug>` path as a literal.

Moving a test out of a suite also orphans the imports only it used. Run
`ruff check .` afterwards: the repository lint targets do not cover it.

## Essential commands

```bash
python3 -m pytest tests/roster/ -q       # ~15 min, and targeted runs never reach it
python3 -m pytest tests/conformance/ -q
python3 tools/test-lint-pack-test-boundary.py
```

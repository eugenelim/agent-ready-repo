# AGENTS.md — `packages/`

Applies to `packages/`. Inherits the root `AGENTS.md`. Scope-specific deltas only.

## Version bump rule

Non-cosmetic package changes update both `version.py` and `pyproject.toml`.
CLI-surface changes may require release; see
[`AGENTS.local.md`](AGENTS.local.md#release-coupling).

## Cross-package traps

- Text reads and writes must pass `encoding="utf-8"`.
- Use list-form subprocess calls only: never `shell=True` or shell out to
  `grep`, `sed`, or `make` from portable package code.
- Tests isolating a user root must set `AGENTBUNDLE_USER_ROOT` with `HOME`:
  Windows `expanduser()` ignores monkeypatched environment variables.
- Projection-layout, orphan-scanner, and adapter-resolution tests parametrize over
  every shipped adapter from `agentbundle/_data/adapter.toml`; document exceptions.
- Use `build_pipeline`, not `build`, for build-pipeline tests: pytest skips any
  directory named `build` by default.

## Test conventions

| Assertion owner | Test home |
| --- | --- |
| Engine distribution | `packages/agentbundle/tests/{unit,integration,build_pipeline}/` |
| Catalogue rule | `tests/conformance/` |
| Catalogue roster | `tests/roster/` |
| Pack behavior | `packs/<pack>/tests/` |
| Repository tool | beside its `tools/` script |

## Deeper pointers

Package release process lives in
[`docs/guides/explanation/release-coupling.md`](../docs/guides/explanation/release-coupling.md).

---
**Status:** In Progress
**Mode:** Full (multi-feature, dependent tasks, new tooling)
---

# Spec: ruff + mypy linting (tools + CI)

## Objective

Wire ruff (style + correctness) and mypy (type checking) into the project's
Python toolchain. Every Python file in scope passes both tools on every CI run.
Findings are fixed, not suppressed, unless the code is intentionally doing
something the linter cannot understand (documented with `noqa`/`type: ignore`
and a rationale).

## Scope

**In:** All Python under `packages/`, `tools/`, `packs/`, `.agents/`, `docs/specs/`.
**Out:** `.agentbundle/` (projected build outputs), `build/`, `__pycache__`.

**mypy scope:** `packages/agentbundle/agentbundle` and `packages/credbroker/credbroker`
only — the typed library code. Tools/ and skill scripts are untyped; mypy is not
run on them.

## Findings baseline (2026-07-27)

### ruff (`--select E,W,F,I,UP,B,SIM,C4,PIE,T20,RET,ARG,PTH`, line-length=88)

| Rule | Count | Fixable | Category |
|------|------:|--------|----------|
| E501 line-too-long | 1734 | manual | style |
| T201 print | 939 | manual | style (CLI intentional) |
| ARG001 unused-function-argument | 301 | manual | correctness (fixtures) |
| I001 unsorted-imports | 283 | auto | style |
| UP006 non-pep585-annotation | 226 | auto | modernization |
| UP037 quoted-annotation | 194 | auto | modernization |
| UP032 f-string | 162 | auto | modernization |
| UP045 non-pep604-annotation | 130 | auto | modernization |
| F401 unused-import | 121 | auto | correctness |
| ARG005 unused-lambda-argument | 97 | manual | correctness |
| UP035 deprecated-import | 88 | auto(-) | modernization |
| C408 unnecessary-collection-call | 52 | manual | quality |
| SIM105 suppressible-exception | 47 | manual | quality |
| PTH118 os-path-join | 43 | manual | modernization |
| PTH102 os-mkdir | 36 | manual | modernization |
| B904 raise-without-from | 30 | manual | correctness |
| E702 semicolon | 27 | manual | style |
| PIE810 multiple-starts-endswith | 26 | manual | quality |
| PTH105/PTH108/PTH101/PTH211 | ~60 | manual | modernization |
| F821 undefined-name | 12 | manual | correctness |
| **Total** | **4867** | **1231 auto** | |

**With line-length=99:** E501 drops to 387 (from 1734). Net total: ~3520.

### mypy (`--ignore-missing-imports --no-strict-optional`, packages only)

- 262 errors in 26 files (141 source files checked)
- Main categories: `attr-defined` on mixin test patterns (~200), `union-attr` on reconfigure (~8), misc (~54)

## Acceptance Criteria

- [x] Root `pyproject.toml` exists with `[tool.ruff]` (line-length=99) and `[tool.mypy]` config
- [ ] `tools/lint-ruff.py` wrapper exists and exits 0 on clean, 1 on violations
- [ ] `tools/lint-mypy.py` wrapper exists and exits 0 on clean, 1 on violations
- [ ] `ruff check .` exits 0 (all violations fixed or config-suppressed with rationale)
- [ ] `mypy packages/agentbundle/agentbundle packages/credbroker/credbroker` exits 0
- [ ] Both wired into `.github/workflows/build-check.yml` (or a new `lint.yml`)
- [ ] No existing tests broken by the fixes

## Config decisions (rationale)

- **line-length=99** — drops E501 from 1734→387 without changing behavior; the existing codebase uses ~90-99 char lines throughout.
- **T201 excluded for CLI areas** — `tools/`, `**scripts/**`, skill scripts use print as output; per-file-ignore rather than `noqa` per line.
- **ARG001/ARG002 excluded for test files** — pytest fixture pattern: `def test_x(tmp_path)` where `tmp_path` is used for side-effect setup only.
- **ARG005 excluded globally** — lambda `_x:` patterns are intentional ignores.
- **mypy scope = packages only** — tools/ and skill scripts are untyped prose-execution scripts; typing them is a separate initiative.
- **UP035 excluded** — `typing_extensions` imports are version-guarded; unsafe-fix only.

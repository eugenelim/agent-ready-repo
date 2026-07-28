# Plan: ruff + mypy linting

## Tasks

### T1 — Root pyproject.toml + tool wrapper scripts
**Mode:** Goal-based
**Done when:** `python tools/lint-ruff.py` and `python tools/lint-mypy.py` run without crash; config file exists.

- Create root `pyproject.toml` with `[tool.ruff]` and `[tool.mypy]` sections
- Create `tools/lint-ruff.py` (wrapper: runs `ruff check .`, returns exit code)
- Create `tools/lint-mypy.py` (wrapper: runs mypy on packages, returns exit code)

**Depends on:** none

### T2 — ruff auto-fix pass
**Mode:** Goal-based
**Done when:** `ruff check --fix .` exits cleanly; all I001/UP*/F401/C4* auto-fixed.

- Run `ruff check --fix --unsafe-fixes .` scoped to auto-fixable rules
- Verify gate: `ruff check . --select I,UP,F401,C420,PTH201,F541,PIE` exits 0

**Depends on:** T1

### T3 — ruff manual fixes: correctness rules
**Mode:** Goal-based
**Done when:** `ruff check --select B,F821,F841,E702,SIM105,PIE810 .` exits 0

Fix in order:
- B904 (30): add `from err` to `raise ... from` in except clauses
- F821 (12): undefined names — investigate each; may be dynamic attributes needing `# type: ignore`
- F841 (18): unused variables — delete or rename to `_`
- E702 (27): split semicolon-separated statements
- SIM105 (47): replace `try/except/pass` with `contextlib.suppress()`
- PIE810 (26): combine multiple `startswith`/`endswith` into tuple form

**Depends on:** T2

### T4 — ruff manual fixes: PTH (pathlib modernization)
**Mode:** Goal-based
**Done when:** `ruff check --select PTH .` exits 0

Fix in order: PTH118 os.path.join, PTH102 os.mkdir, PTH105 os.replace,
PTH108 os.unlink, PTH101 os.chmod, PTH211 os.symlink, PTH112 os.path.isdir,
PTH208 os.listdir, PTH123 builtins.open, PTH111 os.path.expanduser

**Depends on:** T2

### T5 — ruff manual fixes: remaining quality rules
**Mode:** Goal-based
**Done when:** `ruff check --select C4,SIM,RET,B905,B007,C401,SIM1,SIM10 .` exits 0

- C408 (52): `dict()`, `list()`, `tuple()` → literals
- SIM108 (8): ternary if-else
- SIM102 (7): nested if → single if
- SIM117 (22): nested with → single with (auto-fix available)
- RET504 (8): unnecessary assignment before return
- B905 (8): zip without strict
- B007 (7): unused loop variable
- C401 (7): generator→set literal

**Depends on:** T2

### T6 — ruff remaining E501 (long lines at line-length=99)
**Mode:** Goal-based
**Done when:** `ruff check --select E501 .` exits 0

~387 long lines remain after setting line-length=99. Fix by wrapping.
Use per-file `# noqa: E501` ONLY for lines that cannot be wrapped
(e.g., URLs in comments, SQL-like strings — document each).

**Depends on:** T2

### T7 — mypy fixes: packages
**Mode:** Goal-based
**Done when:** `mypy packages/agentbundle/agentbundle packages/credbroker/credbroker --ignore-missing-imports --no-strict-optional` exits 0

Fix in priority order:
- `union-attr` on reconfigure (~8): cast to `TextIOWrapper` or `# type: ignore[union-attr]`
- `attr-defined` on mixin test patterns (~200): add Protocol stub or `# type: ignore[attr-defined]` on mixin call sites
- remaining misc errors (~54): investigate each

**Depends on:** T1

### T8 — Wire into CI
**Mode:** Goal-based
**Done when:** `build-check.yml` (or `lint.yml`) includes ruff and mypy steps; CI passes

Add to `.github/workflows/build-check.yml` (or new `lint.yml`):
```yaml
- name: ruff lint
  run: python3 tools/lint-ruff.py

- name: mypy type-check (packages)
  run: python3 tools/lint-mypy.py
```

**Depends on:** T1, T2, T3, T4, T5, T6, T7

## Declined patterns

- **Tempted to run mypy on all 588 Python files** — declining. Untyped scripts produce noise without correctness value; scope to packages only.
- **Tempted to enable strict mypy** — declining. 588 files with no annotations would require a full annotation pass as a separate initiative.
- **Tempted to suppress all T201 with `noqa`** — declining. Per-file-ignores in config is cleaner and documents the intent (these are CLI tools).
- **Tempted to raise line-length to 120 to eliminate all E501** — declining. 99 is the community standard; 120 would hide genuinely long lines.
- **Tempted to add UP035 (deprecated-import) fixes** — declining. Requires unsafe-fix and may break 3.10-compat import guards; separate task.

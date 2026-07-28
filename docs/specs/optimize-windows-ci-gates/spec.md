# Spec: optimize-windows-ci-gates

**Mode:** light (no risk trigger fired)
**Status:** Shipped

## Objective

Reduce `build-check-windows.yml` wall-clock time by removing platform-independent static-analysis steps (ruff/mypy) that duplicate the authoritative Linux job, and adding scoped pip caching. The T4 test step (`test_credential_brokers_pack_install.py`) is retained: adversarial review confirmed that only 3 of ~15 assertions self-skip on Windows; the path-sensitive integration assertions (user-scope install, consumer import resolution) run on Windows and represent the sole Windows CI coverage for that contract.

## Acceptance Criteria

- [x] AC1 — `Install ruff + mypy`, `ruff lint`, and `mypy type-check` steps are absent from `build-check-windows.yml`
- [x] AC2 — `actions/setup-python@v5` in `build-check-windows.yml` includes `cache: 'pip'` with `cache-dependency-path` scoped to `tools/requirements.txt`, `packages/agentbundle/pyproject.toml`, and `packages/credbroker/pyproject.toml`
- [x] AC3 — The workflow YAML is syntactically valid (passes `yaml.safe_load`)
- [x] AC4 — No implementation or config files other than `build-check-windows.yml` are modified (spec dir excepted)
- [x] AC5 — The T4 pytest step (`pytest user-scope floor delivery / test_credential_brokers_pack_install.py`) is present and unchanged

## Tasks

1. Edit `.github/workflows/build-check-windows.yml`: remove three ruff/mypy steps, add `cache: 'pip'` with scoped `cache-dependency-path`
2. Validate YAML syntax
3. Commit and open PR

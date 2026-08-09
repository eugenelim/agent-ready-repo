# Spec: ci-windows-sso-concurrency-test-fix

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim

Mode: light (no risk trigger fired)

## Objective

Fix the Windows CI failure introduced by commit `ca183de0` in the credbroker
SSO store concurrency test suite.

Two root-cause fixes:

1. **`test_filesystem_refusing_locks_is_a_fault` parametrize** —
   `test_sso_profile_lock.py` line 193 accesses `errno.ENOLCK`, `errno.EOPNOTSUPP`,
   and `errno.ENOSYS` directly in a `@pytest.mark.parametrize` list. On any
   platform where one of these constants is absent this is an `AttributeError` at
   pytest collection time, causing the entire module to fail to collect. The
   production code (`_LOCK_UNSUPPORTED_ERRNOS` in `sso-broker.py`) already guards
   with `getattr(errno, "EOPNOTSUPP", None)` — the test must mirror that pattern.

2. **`__version__` consistency** — commit `ca183de0` bumped `pyproject.toml` to
   `0.6.0` but left `__init__.py` at `0.5.0`. The hardcoded assertion in
   `test_version_matches_pyproject` keeps the test passing today, but the
   inconsistency will cause `pip install credbroker==0.6.0` to install a package
   whose `__version__` attribute reports `0.5.0`. Fix the version string and its
   three copies (package source + two user-libs projections) together.

## Acceptance Criteria

- [x] **AC1.** `test_filesystem_refusing_locks_is_a_fault` is parametrized with
      `getattr`-guarded errno values, not bare attribute accesses, so the module
      collects cleanly on every supported platform.
- [x] **AC2.** `__version__` in `packages/credbroker/credbroker/__init__.py`
      matches the `version` field in `packages/credbroker/pyproject.toml`
      (`"0.6.0"`), and the two user-libs projections remain byte-identical to
      the package source.
- [x] **AC3.** `test_version_matches_pyproject` asserts `"0.6.0"`.
      (deferred: credbroker-version-test-dynamic — the test still hardcodes the
      literal rather than reading `pyproject.toml`; a future bump reintroduces
      the same drift risk without a dynamic check)
- [x] **AC4.** All tests in `packages/credbroker/` pass (`pytest -q`).

## Tasks

1. Fix `test_sso_profile_lock.py` parametrize to use `getattr` guard.
2. Update `__version__` in `__init__.py` from `"0.5.0"` to `"0.6.0"`.
3. Update `test_version_matches_pyproject` assertion from `"0.5.0"` to `"0.6.0"`.
4. Sync user-libs projections to be byte-identical to the updated `__init__.py`.
5. Run GATES and verify.

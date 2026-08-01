# Spec: atlassian-sso-cookie-selector-integration-test

- **Status:** Shipped
- **Owner:** eugenelim
- **Constrained by:** `atlassian-sso-cookie` (parent spec, Shipped; AC13 asserted the selector; tests for each component exist; the wiring is the gap)
- **Brief:** none
- **Contract:** none
- **Shape:** quality

Mode: light (named selector extraction + three tests; no new module boundary, no security-surface change, no public interface exposed)

> **Spec contract:** this document defines what "done" means. The implementing PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Close the coverage gap on the `_run()` / `main_async()` auth selector branch in `jira.py` and `crawl_space.py`. The three selector cases — config absent → token path; `auth_default = "sso-cookie"` + valid config → cookie path; malformed config → `EXIT_USER_ACTION` — are each unit-tested at the component level (`test_sso_config.py`, `test_sso_client.py`), but the wiring itself is untested. Driving `_run()` or `main_async()` from a test requires importing a module designed for `python <script>` invocation: its bootstrap block (`if __package__ in (None, "") and __spec__ is None:`) sets `__package__` only under script invocation, causing the relative imports (`from ._client import …`) to fail when pytest imports the file normally.

The fix is a targeted extraction: add a directly-testable `_select_auth_path(config_path=None)` function to `_sso_config.py` in both atlassian skills (jira and confluence-crawler), have `_run()` and `main_async()` delegate to it, and add three integration tests covering the three selector outcomes. Because `_sso_config.py` uses only absolute imports, it is already importable from tests. No new module boundary, no wait for a CLI import-safe seam.

## Acceptance Criteria

- [x] **AC1.** `_select_auth_path(config_path: Path | None = None) -> tuple[str, SsoConfig | None]` exists in `_sso_config.py` in **both** jira/ and confluence-crawler/ `scripts/`. The function:
  - Returns `("token", None)` when `load_sso_config(config_path)` returns `None` (config absent or `auth_default = "creds"`).
  - Returns `("sso-cookie", sso_config)` when `load_sso_config(config_path)` returns an `SsoConfig` (valid `auth_default = "sso-cookie"` config).
  - Propagates any exception from `load_sso_config()` without catching it — callers map this to `EXIT_USER_ACTION`.
  - Is underscore-prefixed (internal helper, not part of any public surface).
- [x] **AC2.** `_run()` in `jira/scripts/jira.py` calls `_select_auth_path()` (imported from `._sso_config`) instead of calling `load_sso_config()` inline. The surrounding `try/except Exception → EXIT_USER_ACTION` block remains. The `if sso_config is not None:` branch (the current condition) is replaced by branching on the returned tuple: the `"sso-cookie"` path calls `JiraClient.from_sso_cookies(sso_config)`; the `"token"` path calls `load_credentials()` + `JiraClient(credentials, ...)`. Behavior is identical to today's code.
- [x] **AC3.** `main_async()` in `confluence-crawler/scripts/crawl_space.py` applies the same delegation — calls `_select_auth_path()` instead of inline `load_sso_config()`, with equivalent surrounding structure.
- [x] **AC4.** A new `test_auth_selector.py` file exists in **both** skills' `scripts/` directories (byte-identical per the parity constraint). The file opens with `pytest.importorskip("credbroker")` and then `from credbroker import SsoConfigError` (mirroring `test_sso_config.py:18-19`). It contains three tests:
  - **absent → token**: `_select_auth_path(tmp_path / "no-such.toml")` returns `("token", None)`.
  - **valid sso-cookie → sso-cookie**: `_select_auth_path(path_to_valid_fixture)` returns `("sso-cookie", <SsoConfig instance>)`.
  - **malformed → raises**: `_select_auth_path(path_to_malformed_fixture)` raises `SsoConfigError`.
- [x] **AC5.** `tools/test-lint-sso-config.py`'s `_DUPLICATED` list is extended to include `"test_auth_selector.py"`, and the parity check passes (both copies byte-identical).
- [x] **AC6.** All existing sso-cookie tests still pass: `test_sso_config.py`, `test_sso_client.py`, `test_setup_sso.py`, `test_exit_codes.py` in both skills; `tools/test-lint-sso-config.py` passes (parity + schema-parity + upstream-file lint).
- [x] **AC7.** The `_ALLOWED_SSO_KEYS` set in `_sso_config.py` is unchanged (no schema drift; adding `_select_auth_path` must not cause the `lint._ALLOWED_SSO_KEYS != loader._ALLOWED_SSO_KEYS` parity check to fail).

## Boundaries

### Always do

- Edit `_sso_config.py` in **both** skills simultaneously and keep them byte-identical — the parity gate enforces this; a one-sided edit fails the self-test.
- When `_select_auth_path()` raises an exception, propagate it unchanged — never catch it inside the function. The caller's existing `except Exception → EXIT_USER_ACTION` is the mapping point.
- Keep `_select_auth_path` underscore-prefixed (internal helper) and out of any `__all__` or public surface.
- Run `python tools/test-lint-sso-config.py` before declaring done — it verifies parity, schema-set equality between the lint and the loader, and the upstream reference files.

### Never do

- Never widen the function signature to accept the client factory (e.g., `_from_sso_cookies=`) or make it async.
- Never change `_ALLOWED_SSO_KEYS` or `_REQUIRED_SSO_KEYS`.
- Never modify `sso-broker.py` or any credbroker internals.
- Never expose `_select_auth_path` through `credbroker`'s `__all__` or any package public surface.

### Ask first

- Adding `_select_auth_path` to the byte-equality list for any skill beyond jira and confluence-crawler.
- Any change to the function's return type or exception contract.

## Testing Strategy

All three acceptance criteria resolve to running Python tests — no goal-based prose checks, no manual QA.

- **AC4 (the three new test cases)**: run `pytest test_auth_selector.py` in each skill's `scripts/` directory. Each test is deterministic and network-free.
- **AC6 (regression)**: run the full per-skill test suites for both jira and confluence-crawler.
- **AC5, AC7 (parity + schema-set)**: `python tools/test-lint-sso-config.py` — already part of the repo's gate.

## Assumptions

- Technical: `_sso_config.py` in both jira/ and confluence-crawler/ uses only absolute imports at module level and defers `from credbroker import …` to inside the `load_sso_config()` function body — this is what makes it importable from tests without the bootstrap block.
- Technical: `tools/test-lint-sso-config.py` pins the four duplicated files in `_DUPLICATED = ("_sso_config.py", "setup_sso.py", "test_sso_config.py", "test_setup_sso.py")` and checks byte-equality between jira/ and confluence-crawler/ scripts/ for each. Adding `"test_auth_selector.py"` to this list is AC5.
- Technical: The parity gate also checks `lint._ALLOWED_SSO_KEYS == loader._ALLOWED_SSO_KEYS`. The new `_select_auth_path()` function does not modify `_ALLOWED_SSO_KEYS`.
- Technical: `test_sso_config.py` already imports `_sso_config` as a module (for `_sso_config._DEFAULT_CONFIG_PATH`), so a test that does `from _sso_config import _select_auth_path` will work in the same test environment.
- Process: This is light-mode work-loop. The function introduces no new security logic, no new entry point for untrusted data, and no change to how cookies or credentials are resolved.

## Tasks

1. **Add `_select_auth_path()` to `_sso_config.py` (both skills, byte-identical).** The function wraps `load_sso_config(config_path)`, returning the typed two-tuple or propagating any exception. Add it immediately after `load_sso_config()` in the file.

2. **Update `_run()` in `jira/scripts/jira.py`.** Replace the `from ._sso_config import load_sso_config` import with `from ._sso_config import _select_auth_path` (remove `load_sso_config` from the import to avoid an unused-import ruff F401 error). Replace the inline `load_sso_config()` call with `_select_auth_path()`, destructure the returned `(path, sso_config)` tuple, and branch on `path`.

3. **Update `main_async()` in `confluence-crawler/scripts/crawl_space.py`.** Same structural change as Task 2 — replace the import and the call site. Ensure `load_sso_config` is removed from the import line.

4. **Add `test_auth_selector.py` to both skills' `scripts/` directories (byte-identical).** Three test functions: `test_select_auth_path_absent_is_token`, `test_select_auth_path_valid_sso_cookie`, `test_select_auth_path_malformed_raises`.

5. **Update `tools/test-lint-sso-config.py`.** Add `"test_auth_selector.py"` to `_DUPLICATED`. No other changes.

6. **Run gates.** `python tools/test-lint-sso-config.py`, `pytest` over both skill suites, `make build-check`.

## Declined

- **Import-safe seam for `jira.py` / `crawl_space.py`.** Making those CLI entrypoints importable from pytest would require restructuring the bootstrap block — that is the follow-on "wait until CLI entrypoints gain an import-safe seam" branch. Out of scope here.
- **`--sso-config <path>` CLI argument.** Adds a CLI surface out of scope for a quality follow-on test extraction.
- **Extracting the full selector + client factory wiring.** Would require the helper to import from `_client.py`, bringing in the full credential/HTTP stack — a structural refactoring, not a light-mode fix.

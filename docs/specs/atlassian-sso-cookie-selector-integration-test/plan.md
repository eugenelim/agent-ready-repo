# Plan: atlassian-sso-cookie-selector-integration-test

**Mode:** light (AC5 is the only remaining task; one line in one file)

## Assumption trio

- **Files I'll touch:** `tools/test-lint-sso-config.py` (line 90: `_DUPLICATED` tuple)
- **Tests demonstrate "done":** `python tools/test-lint-sso-config.py` exits 0 — the parity check then verifies both `test_auth_selector.py` copies are byte-identical. `SKIP_SAST=1 make build-check` passes.
- **Not changing:** `_sso_config.py`, skill scripts (`jira.py`, `crawl_space.py`), `test_auth_selector.py`, or any other file. ACs 1–4 are already in origin/main.

## Declined temptations

- Add `test_exit_codes.py` to `_DUPLICATED` while I'm in the file — not in spec, out of scope.
- Refactor `_parity_failures()` — no second caller, no spec authorization.

## Task list

1. **Add `"test_auth_selector.py"` to `_DUPLICATED` in `tools/test-lint-sso-config.py`.** (AC5)
   - Mode: goal-based check
   - Tests: `python tools/test-lint-sso-config.py` exits 0 (Done when)

## Gates

```
python tools/test-lint-sso-config.py
SKIP_SAST=1 make build-check
```

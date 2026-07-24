# Plan: PackState Source Provenance

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Changes across three files, with a new canonicalization helper. First, `PackState.source` becomes `str | None = None` and `_parse_adapter_row` drops the `"agent-ready-repo"` fallback on read — this makes the state file authoritative and unknown provenance visibly `None` rather than a misleading literal. Second, `canonicalize_source` is introduced as a single shared function that normalizes local paths to absolute form and remote URIs to lowercase-scheme/netloc form, and maps both `None` and the legacy literal to `None`. Third, the install write site replaces its hard-coded `"agent-ready-repo"` with `canonicalize_source(catalogue_uri)`, and the upgrade whole-pack branch gains a new source write (upgrade currently preserves whatever source the row had — this spec adds the write). All existing tests must pass unchanged — the only observable behaviour change is that new installs and upgrades record real provenance.

## Constraints

- RFC-0072 D3: same-name/different-source conflict semantics require a stable canonicalization function; this spec defines it.
- RFC-0072 Key assumptions: no schema version bump; `str | None = None` is backward-compatible.
- ADR-0036: source resolution chain is the source of the `catalogue_uri` value this spec records.
- RFC-0031 Principle 3: stdlib-only, no new runtime dependency.
- Security: never persist credentials, bearer tokens, or URL user-info; redact in errors.

## Construction tests

**Integration tests:** One integration test verifies that after a full `agentbundle install` against a local fixture, the written state row has a non-`None`, non-`"agent-ready-repo"` source equal to `canonicalize_source(fixture_path)`. This spans T1–T3 and is the canonical AC12 verification.

**Manual verification:** none beyond the integration test above.

## Design (LLD)

### Design decisions

- `canonicalize_source` lives in `config.py` alongside `PackState` rather than `source_defaults.py` — it operates on already-resolved values, not on the resolution chain itself. `source_defaults.py` resolves *which* source to use; `canonicalize_source` normalizes the value for storage. Traces to: AC5, AC8, AC9. **Duplication risk:** `source_defaults.py:172-174` and `:94-101` already own the `file://` non-localhost-netloc check and the scheme-discrimination ladder; `canonicalize_source` re-implements the same logic. **Intentional divergence on `file://` decoding:** `source_defaults.py:175` uses `url2pathname(unquote(path))` which double-decodes; this spec uses `url2pathname(path)` only (single decode) — the correct behavior. The `test_canonicalize_file_url_literal_percent` discriminator test will catch any regression back to double-decode; `source_defaults.py:175` is flagged for a follow-up fix. Alternative considered: move `canonicalize_source` to `source_defaults.py` (no circular import cost since `source_defaults` doesn't import `config`); rejected here because `PackState`-coupled callers (install, upgrade) already import `config`, avoiding a second import. Revisit if a third caller in a different module appears.
- `dump_state` omits the `source` key when `None` (not `source = ""`). An absent key round-trips to `None` via the updated `_parse_adapter_row`, preserving backward compatibility. Traces to: AC4, AC15.
- Legacy literal `"agent-ready-repo"` is treated as unknown by `canonicalize_source` (returns `None`) but preserved on write (if it's in an existing row, `dump_state` still emits it). This means reading a legacy file and writing it back is a no-op — no silent migration. Traces to: AC3, AC7, AC15.

### Data & schema

`PackState.source: str | None = None` — change from `str = "agent-ready-repo"`. TOML representation: key absent when `None`, `source = "<value>"` when non-`None`. No schema version bump. Traces to: AC1, AC4.

### Interfaces & contracts

`canonicalize_source(value: str | None) -> str | None` — public function in `agentbundle.config`. Called by install, upgrade, and (in future specs) conflict-check and status paths. Traces to: AC5–AC10.

### Behavior & rules

Canonicalization rules:
1. `None` → `None`
2. `"agent-ready-repo"` (exact case-sensitive match) → `None`
3. `""` or blank → `None`
4. Windows drive path (`_WIN_DRIVE_RE`) or schemeless (no `urlsplit` scheme) → local path branch: `try: return str(Path(value).resolve()) except OSError: return None`
5. `file://` scheme → local path branch: parse via `urlsplit`; reject non-empty/non-localhost netloc (return `None` for remote `file://` URIs like `file://remote-host/…`); convert path component using `Path(url2pathname(parsed.path)).resolve()` — `url2pathname` already unquotes percent-encoding on its own (it *is* `unquote` on POSIX); wrapping in an extra `unquote()` double-decodes and corrupts paths with literal `%` characters (e.g. `%25` → `%` correctly with single decode, but `%20` with double-decode); return `str(resolved_path)`. Note: `source_defaults.py:175` uses `url2pathname(unquote(...))` — a double-decode bug; this spec intentionally diverges; flag `source_defaults.py:175` for a follow-up fix.
6. Remote URL with user-info in netloc (any `@` in netloc, including bare `user@` without a password) → `None` (reject, never record credentials)
7. Remote URL with a query string or URI fragment containing a credential-style string → `None` (reject, never record credentials in state TOML). Query: check each query key (from `key=value` parse) for substring match against `token`, `key`, `secret`, `password`, `auth` (case-insensitive). Fragment: scan the **full fragment string** as a single case-insensitive substring match against the same terms — no splitting; `"access_token=SECRET"` matches because the fragment string contains `"token"`. This whole-string scan avoids ambiguous fragment tokenization. Legitimate fragments such as `#sha256=<64hex>` contain none of the credential substrings and pass safely.
8. Remote URL (no user-info, no credential query params, no credential fragment tokens) → scheme lowercased + `://` + netloc lowercased (netloc = hostname + optional `:port`; user-info already rejected so lowercasing the whole netloc is safe; port is preserved) + normalized path (strip trailing slash on non-empty path); query and fragment preserved only when no credential params match rule 7

Traces to: AC6–AC10, AC9b.

### Failure, edge cases & resilience

- Temporary extraction paths (e.g. `/tmp/agentbundle-XXXX/`) are valid local paths. The spec does not exclude them at the canonicalization layer — the install path must pass the logical catalogue URI (before `resolve_catalogue()` resolves it to a temp dir), not the resolved directory. Implementation must capture `catalogue_uri` before calling `resolve_catalogue()`.
- `Path.resolve()` may raise `OSError` on exotic inputs; catch and return `None`.
- `urlsplit` on a value with a `+` in the scheme (e.g. `catalogue+https://`) returns a non-empty scheme that includes the `+`. The remote URL branch (rule 8) handles `catalogue+https://` correctly — the compound scheme is lowercased as a string. An explicit test (`test_canonicalize_catalogue_https_scheme`) in T2 confirms this, which `spec/https-catalogue-channels` AC8 depends on.

## Tasks

### T1: Update `PackState.source` field, `_parse_adapter_row`, and `dump_state`

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/config.py`

**Tests (TDD — all tests below require red stubs materialized at EXECUTE PLAN):**
- `test_pack_state_source_default_is_none`: construct `PackState(installed_version="1.0")` with no `source` argument; assert `ps.source is None`. Verifies AC1.
- `test_parse_adapter_row_absent_source_key`: parse a TOML row with no `source` key; assert `packstate.source is None`. Verifies AC2.
- `test_parse_adapter_row_legacy_literal_preserved`: parse a TOML row with `source = "agent-ready-repo"`; assert `packstate.source == "agent-ready-repo"`. Verifies AC3.
- `test_parse_adapter_row_real_source_preserved`: parse a TOML row with `source = "git+https://example.test/repo"`; assert `packstate.source == "git+https://example.test/repo"`. Verifies AC3.
- `test_dump_state_none_source_omits_key`: serialize a `PackState` with `source=None`; assert `"source"` does not appear in the serialized TOML for that row. Verifies AC4.
- `test_dump_state_legacy_literal_emits_key`: serialize a `PackState` with `source="agent-ready-repo"`; assert `source = "agent-ready-repo"` appears in the TOML. Verifies AC4.
- `test_dump_and_parse_round_trip_none`: dump then parse a state with `source=None`; assert round-trip value is `None`. Verifies AC4 + AC2.
- `test_dump_and_parse_round_trip_legacy`: dump then parse a state with `source="agent-ready-repo"`; assert round-trip is `"agent-ready-repo"`. Verifies AC4 + AC3.

**Approach:**
- `config.py:118`: change `source: str = "agent-ready-repo"` → `source: str | None = None`
- `config.py:395`: change `body.get("source", "agent-ready-repo")` → `body.get("source")`
- `dump_state`: in the per-row serialization block, emit `source = …` only when `ps.source is not None`. Locate the existing `source` emit line in `dump_state` and wrap it in an `if ps.source is not None:` guard.

**Done when:** all eight tests above pass; `mypy` (or equivalent) reports no type errors for the changed fields.

---

### T2: Implement `canonicalize_source`

**Depends on:** T1

**Touches:** `packages/agentbundle/agentbundle/config.py`

**Tests (TDD — all tests below require red stubs materialized at EXECUTE PLAN):**
- `test_canonicalize_none` → `None`. Verifies AC6.
- `test_canonicalize_legacy_literal` → `None`. Verifies AC7.
- `test_canonicalize_local_abs_path`: pass `"/tmp/catalogue"` → absolute normalized path. Verifies AC8.
- `test_canonicalize_local_rel_path`: pass `"./catalogue"` → absolute path (resolved relative to cwd at call time). Verifies AC8.
- `test_canonicalize_windows_drive_path` (parametrize with `"C:\\repo"` and `"C:/repo"`) → absolute-normalized. Verifies AC8.
- `test_canonicalize_git_https`: `"git+https://EXAMPLE.TEST/repo"` → `"git+https://example.test/repo"` (scheme+host lowercased). Verifies AC9.
- `test_canonicalize_trailing_slash_normalized`: `"git+https://example.test/repo/"` → `"git+https://example.test/repo"` (trailing slash on non-empty path removed). Verifies AC9.
- `test_canonicalize_host_port_preserved`: `"git+https://example.test:8443/repo"` → `"git+https://example.test:8443/repo"` (port preserved in lowercased netloc). Verifies AC9.
- `test_canonicalize_catalogue_https_scheme`: `"catalogue+https://EXAMPLE.TEST/channels/stable.json"` → `"catalogue+https://example.test/channels/stable.json"` (compound scheme treated as remote URL via rule 8). Verifies AC9 and confirms the scheme canonicalize_source is expected to handle by spec/https-catalogue-channels AC8.
- `test_canonicalize_fragment_preserved`: `"archive+https://example.test/r.tar.gz#sha256=" + "a" * 64` → same URL with fragment intact and scheme/host lowercased (fragment passes rule 7 — `"sha256"` contains no credential substring). Verifies rule 8 fragment-preservation relied on by spec/https-catalogue-channels AC8b.
- `test_canonicalize_fragment_credential_rejected`: `"git+https://example.test/repo#access_token=SECRET"` → `None` (fragment contains `"token"` substring; rejected by rule 7 fragment scan). Verifies AC10, AC9b.
- `test_canonicalize_file_url_remote_netloc`: `"file://remote-host/tmp/x"` → `None` (non-localhost netloc rejected). Verifies rule 5 return value.
- `test_canonicalize_user_info_rejected`: `"git+https://user:pass@example.test/repo"` → `None`. Verifies AC9, AC10.
- `test_canonicalize_user_info_only_user_rejected`: `"git+https://user@example.test/repo"` → `None`. Verifies AC10.
- `test_canonicalize_bare_at_netloc_rejected`: `"git+https://@example.test/repo"` → `None` (bare `@` with empty username rejected via `"@" in parsed.netloc`; `parsed.username` would be `""` which is falsy — the `@`-check catches it). Verifies AC10, rule 6.
- `test_canonicalize_query_private_token_rejected`: `"git+https://example.test/repo?private_token=SECRET"` → `None` (substring match on `"token"` in `"private_token"`). Verifies AC9b, rule 7 substring semantics.
- `test_canonicalize_benign_query_preserved`: `"git+https://example.test/repo?ref=main"` → `"git+https://example.test/repo?ref=main"` (benign query param preserved; `"ref"` matches none of the credential substrings). Verifies rule 8 query preservation.
- `test_canonicalize_query_token_rejected`: `"git+https://example.test/repo?access_token=SECRET"` → `None`. Verifies AC9b, AC10.
- `test_canonicalize_query_api_key_rejected`: `"git+https://example.test/repo?api_key=SECRET"` → `None`. Verifies AC9b.
- `test_canonicalize_file_url_local`: `"file:///tmp/catalogue"` → absolute-normalized path. Verifies AC8.
- `test_canonicalize_file_url_percent_encoded`: `"file:///tmp/a%20b"` → absolute path with space (single decode via `url2pathname`). Verifies rule 5 single-decode.
- `test_canonicalize_file_url_literal_percent` (discriminator): `"file:///tmp/a%2520b"` → absolute path containing literal `%20` (not a space) — distinguishes single-decode (correct: `%2520` → `%20`) from double-decode (wrong: `%2520` → ` `). Verifies rule 5 no-double-decode requirement.
- `test_canonicalize_file_url_windows` (Windows-only or parametrized skip on non-Windows): `"file:///C:/repo"` → `"C:\\repo"` or normalized Windows path (via `url2pathname`). Verifies rule 5 `url2pathname` requirement.
- `test_canonicalize_empty_string` → `None`. Verifies robustness.
- `test_canonicalize_os_error_returns_none`: pass an exotic path that raises `OSError` on `resolve()`; assert returns `None`. Verifies AC8 edge case.

**Approach:**
- Add `canonicalize_source(value: str | None) -> str | None` to `config.py`, placed after the `PackState` dataclass and before `dump_state`.
- Implementation order:
  1. `if value is None: return None`
  2. `if value == "agent-ready-repo": return None`
  3. `if value == "" or not value.strip(): return None`
  4. Check Windows drive path regex (`_WIN_DRIVE_RE` from `source_defaults.py`) OR schemeless (no `urlsplit` scheme) → local path branch: `try: return str(Path(value).resolve()) except OSError: return None`
  5. Parse with `urlsplit(value)`. If `parsed.scheme == "file"` → local path branch: reject non-empty/non-localhost `parsed.netloc` (return `None`); `try: return str(Path(url2pathname(parsed.path)).resolve()) except OSError: return None`. Use `url2pathname` from `urllib.request` (or `urllib.parse.unquote` on POSIX where they are equivalent — do NOT wrap in an extra `unquote()` as that double-decodes and corrupts paths with literal `%`). (Must handle `file://` here — before step 6 — because `file://` has a truthy scheme but is a local path, not a remote URL.)
  6. If `"@" in parsed.netloc` → `return None` (reject user-info in remote URLs — covers bare `user@` where `parsed.username` is an empty string and thus falsy).
  7. Normalize: lowercase `parsed.scheme` and `parsed.netloc` (netloc = hostname + optional `:port`; user-info already rejected so lowercasing the whole netloc is safe and preserves the port); reconstruct URI with `SplitResult`; strip trailing slash from path if non-empty.
  8. Return normalized URI string.
- Import `_WIN_DRIVE_RE` from `source_defaults` OR define a local copy in `config.py` to avoid a circular import. Check for circular import risk first; if present, duplicate the small regex constant.

**Done when:** all T2 tests above pass; function is importable from `agentbundle.config`.

---

### T3: Fix `install.py` write path

**Depends on:** T1, T2

**Touches:** `packages/agentbundle/agentbundle/commands/install.py`

**Tests:**
- `test_install_records_local_catalogue_source` (integration): run the install handler against a local fixture catalogue; read the written state; assert `state.row(pack_name, adapter).source == canonicalize_source(fixture_path_str)` where `fixture_path_str` is the logical URI, not the resolved temp dir. Verifies AC11, AC12.
- `test_install_records_git_https_source` (integration): run the install handler with a `git+https://example.test/repo` catalogue URI (mocked `resolve_catalogue`); assert written source equals `canonicalize_source("git+https://example.test/repo")`. Verifies AC13.
- `test_install_never_writes_agent_ready_repo` (regression): scan all integration fixture test runs; assert no state row has `source == "agent-ready-repo"`. Verifies AC11.
- `test_profile_install_records_logical_uri` (integration): run a profile install against a local fixture; assert every installed pack row's source is a non-temp canonical path/URI, not a `/tmp/agentbundle-XXXX/` path. Verifies AC14b.

**Approach:**
- At `install.py:1025`: replace `source="agent-ready-repo"` with `source=canonicalize_source(catalogue_uri)`.
- `catalogue_uri` is the value passed to `resolve_catalogue()` at line ~209 and remains in scope.
- Import `canonicalize_source` from `agentbundle.config` (it's already imported for `PackState` and related).
- Profile-install path (`install.py` around line 4195): the profile orchestrator sets `ns.catalogue = str(catalogue_dir)` (the resolved directory path, not the original URI). Trace the call chain: capture the original `catalogue_uri` *before* calling `resolve_catalogue()` and thread it to the per-pack `run()` calls. Do not use `str(catalogue_dir)` as the source. This may require adding a `_source_uri` attribute to the per-pack namespace so the inner `run()` can write `canonicalize_source(_source_uri)` instead of `canonicalize_source(catalogue_uri)` (which would be the resolved dir string).

**Done when:** integration tests above pass; `grep -r '"agent-ready-repo"' packages/agentbundle/agentbundle/commands/install.py` returns zero lines.

---

### T4: Add source write to `upgrade.py`

**Depends on:** T1, T2

**Touches:** `packages/agentbundle/agentbundle/commands/upgrade.py`

**Tests:**
- `test_upgrade_migrates_legacy_source` (integration): start with a state row where `source = "agent-ready-repo"` (legacy); run upgrade against a local fixture; assert the updated row's source equals `canonicalize_source(fixture_path_str)`. Verifies AC14.
- `test_upgrade_with_none_source_migrates` (integration): start with a state row where `source` key is absent (None); run upgrade; assert updated row source equals `canonicalize_source(catalogue_uri)`. Verifies AC14.
- `test_upgrade_preserves_concrete_source` (integration): start with a state row with a concrete canonical source; run upgrade with the same source; assert source is unchanged (or re-canonicalized to the same value). Verifies AC14.
- `test_upgrade_does_not_overwrite_concrete_with_none` (integration): start with a concrete canonical source row; run upgrade against a `canonicalize_source`-returning-`None` catalogue URI (edge case); assert existing source is preserved. Verifies AC14.

**Approach:**
- `upgrade.py` mutates `pack_state.installed_version` in place and re-serializes via `dump_state` — it does NOT hard-code `"agent-ready-repo"`. There is no existing source write to fix; this task adds one.
- `upgrade.py` has two upgrade branches: a **whole-pack branch** (updates `installed_version`) and a **per-primitive branch** (`is_per_primitive`, upgrades individual skills without touching `installed_version`). This spec adds the source write to the **whole-pack branch only** — AC14 is scoped accordingly; per-primitive source write is deferred.
- At the point in the whole-pack branch where `pack_state.installed_version` is updated, add: `canonical = canonicalize_source(catalogue_uri)` and then `if canonical is not None: pack_state.source = canonical` — this migrates legacy rows when a real source is known and preserves concrete existing sources when the catalogue URI is itself unknown (unusual but possible).
- Import `canonicalize_source` from `agentbundle.config`.
- Locate `catalogue_uri` in the upgrade flow — it is the resolved source string passed to `resolve_catalogue()`, analogous to the install path.

**Done when:** integration tests above pass; `upgrade.py` has an explicit source write alongside the `installed_version` update.

---

### T5: Run existing test suite; confirm no regression

**Depends on:** T1, T2, T3, T4

**Touches:** none (read-only verification)

**Tests:**
- Run full agentbundle test suite: `python -m pytest packages/agentbundle/ -x`.
- Goal-based: `git diff pyproject.toml` shows no new dependency entries; `grep -n "^import\|^from" packages/agentbundle/agentbundle/config.py` confirms `canonicalize_source` imports only stdlib modules. Verifies AC17.

**Approach:**
- Run the test suite.
- If failures arise: distinguish pre-existing failures (known-skip via `[backlog].open`) from regressions caused by this change. Any new failure is a blocker.
- Run the AC17 goal-based check.

**Done when:** pytest exits 0 (or all failures are pre-existing and documented in `[backlog].open`) and AC17 goal-based check passes. Verifies AC16, AC17.

## Rollout

Pure-logic change — no infrastructure, no new dependency, no deployment sequencing. Backward-compatible for existing state files. Ships as part of the broader ini-004 agentbundle release (minor version bump in `spec/agentbundle-enterprise-distribution-release`).

## Risks

- **Circular import:** `canonicalize_source` in `config.py` may need `_WIN_DRIVE_RE` from `source_defaults.py`; if `source_defaults.py` imports from `config.py`, duplicating the small regex constant avoids the cycle. Check before implementing T2.
- **Profile-install path:** the profile install handler at `install.py:~4195` sets `ns.catalogue = str(catalogue_dir)` (a resolved path, not the original URI). If this becomes the `catalogue_uri` for the inner per-pack install call, the recorded source would be a temporary directory. Must trace the call graph to ensure the logical URI is passed through, not the resolved directory.
- **Upgrade in-place mutation:** if `upgrade.py` mutates a row's `installed_version` without constructing a new `PackState`, the `source` update must be added as an explicit assignment, not assumed to happen.

## Changelog

- 2026-07-23: initial plan
- 2026-07-23: second adversarial review — fixed port preservation in rule 8 + netloc reconstruction (C2); added T2 tests for host:port, catalogue+https scheme, file:// remote netloc; scoped AC14/T4 to whole-pack upgrade branch only (C3); added TDD stub markers to T1/T2; clarified file:// rejection return value (Nit 8)
- 2026-07-23: third adversarial review — updated Approach to reflect three files + upgrade as new write (not replacement) (C1); replaced "eleven tests" with count-free Done when (C2); inserted explicit file:// local-branch step in implementation order before remote-URL step (Nit 3); fixed Objective to not label _parse_adapter_row read fallback a "write site" (Nit 4); added test_canonicalize_fragment_preserved for AC8b cross-spec dependency
- 2026-07-23: fourth adversarial review — fixed bare-@ netloc rejection to use "@" in netloc check (C1); added test_canonicalize_bare_at_netloc_rejected; added AC17 goal-based check to Testing Strategy + T5; fixed Objective dataclass-default wording (Nit 3)
- 2026-07-23: fifth adversarial review — tightened rule 7 to substring matching with explicit rationale; added test_canonicalize_query_private_token_rejected + test_canonicalize_benign_query_preserved
- 2026-07-23: sixth adversarial review — fixed file:// path conversion to use url2pathname+unquote (Blocker); added tests for percent-encoded and Windows file:// URLs; addressed code-duplication concern in Design decisions with url2pathname alignment note and alternative-considered rationale
- 2026-07-23: seventh adversarial review — fixed double-decode: changed to url2pathname(path) only (Concern); added test_canonicalize_file_url_literal_percent discriminator; noted intentional divergence from source_defaults.py:175 (double-decode bug flagged for follow-up)
- 2026-07-23: eighth adversarial review — extended rule 7 + rule 8 to scan URI fragment for credential substrings (AC10 gap); added test_canonicalize_fragment_credential_rejected; updated AC9b in spec to cover fragment credentials
- 2026-07-23: ninth adversarial review — propagated fragment credential rejection to Always do boundary + Testing Strategy in spec (Concern); clarified rule 7 fragment scanning as whole-string substring (not split-on-token) in plan (Nit)

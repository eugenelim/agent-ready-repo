# Plan: HTTPS Catalogue Channels

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Four coherent tasks. First, extend `_is_valid_source` with two new scheme branches — the minimal gate that lets the rest of the chain accept `catalogue+https://` and `archive+https://` strings. Second, implement the HTTPS fetcher module (`agentbundle/https_catalogue.py`) covering bearer-token injection, proxy support, channel descriptor fetch + schema validation, archive streaming + SHA-256 verification + safety limits + extraction safety. Third, wire the new fetcher into `resolve_catalogue` so it handles the two new schemes. Fourth, write the test suite using a local in-process HTTP server fixture — no external network calls.

## Constraints

- RFC-0072 D1: mutable channel descriptor → immutable archive + SHA-256.
- RFC-0031 Principle 3: stdlib-only, no new runtime dependency.
- Security: bearer token never persisted, printed, or forwarded across host redirects; no TLS-bypass; HTTPS-only artifact and redirect URLs.
- ADR-0036: the new schemes integrate into the existing source chain at the `_is_valid_source` gate and `resolve_catalogue` dispatch.
- spec/packstate-source-provenance must ship first: `canonicalize_source` (from that spec) is needed for AC8; `install.py:1025` source write (that spec's AC11) is what records the channel URI. This spec verifies AC8 via an integration test only after packstate-source-provenance is applied.
- Same-origin is defined as scheme + host + port (full origin, not just host). Traces to: AC9, AC21.

## Construction tests

**Integration tests:** one end-to-end test (local HTTP server fixture → channel descriptor JSON → archive tar.gz with a minimal pack → `resolve_catalogue` returns the temp extraction dir → `_locate_pack` finds the pack). This spans T1–T3.

**Manual verification:** none beyond the integration test.

## Design (LLD)

### Design decisions

- New module `agentbundle/https_catalogue.py` rather than extending `catalogue.py` — keeps `catalogue.py` thin (path resolution + git+https only); the HTTPS fetcher is a large, security-sensitive addition that deserves its own module. Traces to: AC6, AC30.
- Custom `urllib` opener with explicit `ProxyHandler` + redirect handler for bearer-token host-pinning. `urllib`'s default redirect handler forwards all headers including `Authorization` to the redirect target; the custom redirect handler **rejects** any redirect to a different origin (scheme + host + port) from the originally-requested URL — no request is ever sent to the cross-origin redirect target. Same-origin redirects are forwarded with `Authorization` intact. Traces to: AC21, AC21d, AC23.
- SHA-256 streamed in chunks during download; digest computed before extraction; `tarfile.open()` called on the verified temp file. Traces to: AC7, AC13.
- Safety limits as module-level named constants (easy to adjust per RFC-0072 note). Traces to: AC13–AC15, AC26, AC27.
- Archive extraction via a member-by-member `tarfile` iteration with per-member safety checks before `tarfile.extract()`; never `tarfile.extractall()` without a filter. Traces to: AC16–AC20.

### Interfaces & contracts

`fetch_catalogue_archive(source_uri: str, *, env: dict[str, str] | None = None) -> Path` — new function in `https_catalogue.py`. Returns the extraction temp directory path. Called by `resolve_catalogue` when the scheme is `catalogue+https` or `archive+https`. `env` defaults to `os.environ`; injectable for testing.

### Failure, edge cases & resilience

- Redirect to a different origin: reject it entirely (not just strip `Authorization`). This keeps the same-origin anchor for artifact validation pinned to the originally-requested channel URI and prevents open-redirect exploitation. Cross-origin redirects are rejected before being followed; same-origin redirects are allowed and `Authorization` is forwarded.
- `Content-Length` absent or dishonest: enforce size limits via a running byte counter during streaming, not via `Content-Length`.
- `minimum_agentbundle_version` check: use `agentbundle.__version__` as the running version source; compare using integer-tuple `(MAJOR, MINOR, PATCH)` splitting — never lexicographic string comparison (`"10.0.0" > "9.0.0"` must hold). Do not import `packaging` (not stdlib).
- Cleanup on failure: use `tempfile.TemporaryDirectory` as a context manager; re-raise after logging; caller receives `None` → error propagated.

## Tasks

### T1: Extend `_is_valid_source` for new schemes

**Depends on:** none

**Touches:** `packages/agentbundle/agentbundle/source_defaults.py`

**Tests:**
- `test_is_valid_source_catalogue_https` → `True`. Verifies AC1.
- `test_is_valid_source_catalogue_http` → `False`. Verifies AC2.
- `test_is_valid_source_archive_https_with_sha256` → `True`. Verifies AC3.
- `test_is_valid_source_archive_http` → `False`. Verifies AC4.
- `test_is_valid_source_catalogue_https_user_info` → `False`. Verifies AC5.
- `test_is_valid_source_archive_https_user_info` → `False` (user-info in archive+https:// URL). Verifies AC5b.
- `test_is_valid_source_archive_https_no_fragment` → `False`. Verifies AC25.
- `test_is_valid_source_archive_https_bad_fragment` (non-hex sha256) → `False`. Verifies AC25.
- Existing `_is_valid_source` tests pass unchanged. Verifies AC31.

**Approach:**
- In `_is_valid_source`, add two new branches before the existing `if urlsplit(value).scheme: return False` gate (currently at line 96):
  1. `if value.startswith("catalogue+https://")`: parse with `urlsplit`; reject if `netloc` contains `@` (user-info); accept.
  2. `if value.startswith("archive+https://")`: parse with `urlsplit`; reject if no `#sha256=` fragment matching 64 lowercase hex chars; reject if user-info; accept.
- Do NOT add `catalogue+http://` or `archive+http://` branches.

**Done when:** all scheme tests pass; existing tests unchanged.

---

### T2: Implement `https_catalogue.py` fetcher

**Depends on:** none (can start in parallel with T1)

**Touches:** `packages/agentbundle/agentbundle/https_catalogue.py` (new file)

**Tests (all use local in-process HTTP server fixture):**
- `test_fetch_channel_descriptor_ok`: local server serves a valid descriptor JSON; assert parsed fields match. Verifies AC6.
- `test_fetch_channel_descriptor_too_large`: local server serves 1 MiB + 1 byte; assert `CatalogueError` raised before JSON parse. Verifies AC26.
- `test_fetch_archive_sha256_match`: serve a minimal tar.gz with matching sha256; assert extraction succeeds and temp dir contains expected file. Verifies AC6.
- `test_fetch_archive_sha256_mismatch`: serve archive with wrong sha256 in descriptor; assert error names both digests; temp dir cleaned up. Verifies AC7.
- `test_fetch_archive_too_large_compressed`: serve an archive > 256 MiB (mock streaming counter); assert rejected before extraction. Verifies AC13.
- `test_fetch_archive_too_many_members`: synthetic tar.gz with 20 001 zero-byte members; assert rejected during extraction. Verifies AC14.
- `test_fetch_archive_too_large_expanded`: synthetic tar.gz where total expanded bytes > 1 GiB (mock); assert rejected. Verifies AC15.
- `test_extraction_path_traversal`: member path `../evil`; assert extraction aborted, temp cleaned. Verifies AC16.
- `test_extraction_absolute_path`: member path `/etc/passwd`; assert aborted. Verifies AC17.
- `test_extraction_symlink`: symlink member; assert aborted. Verifies AC18.
- `test_extraction_hard_link`: hard link member; assert aborted. Verifies AC19.
- `test_extraction_device_file`: char device member; assert aborted. Verifies AC20.
- `test_bearer_token_sent`: intercept request headers in local server; assert `Authorization: Bearer test-token` present. Verifies AC21.
- `test_bearer_token_cross_origin_redirect_rejected`: redirect to different host (different origin); assert `CatalogueError` is raised and no request is sent to the redirect target — the redirect is rejected before any outbound request, so the bearer token is never forwarded. Verifies AC21 (cross-origin clause) and AC21d.
- `test_cross_origin_redirect_rejected_descriptor`: local server A redirects the descriptor request to a local server B (different port = different origin); assert `CatalogueError` is raised before the redirect is followed. Verifies AC21d.
- `test_same_origin_anchor_is_originally_requested`: local server A redirects descriptor to A/other-path (same origin — ok); artifact URL is resolved against the **originally-requested** URI A/stable.json, not A/other-path; assert correct artifact URL computed. Verifies AC21d.
- `test_bearer_token_absent_from_errors`: trigger an error while token is set; assert error string does not contain token value. Verifies AC22.
- `test_proxy_env_honored`: monkeypatch `os.environ["HTTPS_PROXY"] = "http://proxy.example.test:3128"` (not via `env=` injection — `ProxyHandler()` reads proxies from `os.environ` via `getproxies()`, not from the `env=` parameter); build opener; assert the opener's proxy handlers resolve `https` to the configured proxy URL. Verifies AC23.
- `test_no_proxy_honored`: monkeypatch `os.environ["NO_PROXY"] = "example.test"`; assert the proxy is bypassed for that host. Verifies AC23.
- `test_cross_origin_artifact_rejected_different_host`: descriptor's `artifact` field is on a different host; assert error. Verifies AC9.
- `test_cross_origin_artifact_rejected_different_port`: descriptor's `artifact` field is same host but different port; assert error. Verifies AC9.
- `test_cross_origin_artifact_rejected_different_scheme`: descriptor's `artifact` field uses `http://` instead of `https://`; assert error (also covers AC10). Verifies AC9, AC10.
- `test_http_artifact_rejected`: descriptor `artifact` is HTTP, not HTTPS; assert error. Verifies AC10.
- `test_minimum_version_older_client_rejected`: descriptor has `minimum_agentbundle_version = "999.0.0"`; assert version error before archive download. Verifies AC11, AC35.
- `test_minimum_version_ten_vs_nine`: call `_check_client_version("10.0.0", running_version="9.9.9")`; assert version error (integer comparison — `9 < 10`, not lexicographic where `"9" > "1"`). Verifies AC35.
- `test_minimum_version_malformed`: descriptor has `minimum_agentbundle_version = "not-semver"`; assert clear error rather than crash. Verifies AC36.
- `test_minimum_version_absent_proceeds`: no `minimum_agentbundle_version` in descriptor; assert normal flow. Verifies AC12.
- `test_minimum_version_equal_proceeds`: `minimum_agentbundle_version` equals running version; assert proceeds. Verifies AC12.
- `test_missing_required_field_rejected`: descriptor missing `sha256` field; assert clear error naming the field. Verifies AC32.
- `test_wrong_schema_rejected`: descriptor with `schema: 2`; assert error. Verifies AC33.
- `test_wrong_kind_rejected`: descriptor with `kind: "not-agentbundle"`; assert error. Verifies AC33.
- `test_descriptor_sha256_non_hex_rejected`: descriptor's `sha256` is `"UPPERCASE"` or `"gg..."` (not 64 lowercase hex); assert rejected at parse time. Verifies AC25b.
- `test_redirect_to_http_rejected`: local server redirects to `http://` target; assert error. Verifies AC21b.
- `test_redirect_with_user_info_rejected`: local server redirects to URL with `user:pass@host`; assert error. Verifies AC21c.
- `test_stdlib_only` (goal-based): `python -c "import agentbundle.https_catalogue"` succeeds; grep confirms no `import packaging`, `import requests`, or similar non-stdlib imports. Verifies AC30, AC37.
- `test_timeout_is_finite`: mock a hanging server (no response); assert request times out (set very short timeout for test). Verifies AC27.
- `test_temp_dir_cleaned_on_digest_mismatch`: verify temp dir does not exist after mismatch failure. Verifies AC28.
- `test_temp_dir_cleaned_on_extraction_error`: verify temp dir cleaned after extraction rejection. Verifies AC28.
- `test_archive_https_direct`: `archive+https://` URL with correct fragment; assert extraction succeeds; no descriptor fetch. Verifies AC24.
- `test_no_real_endpoints_in_tests` (static lint): grep test files for non-`example.test` domain names; assert zero hits. Verifies AC29.

**Approach:**
- Module-level constants: `_MAX_DESCRIPTOR_BYTES = 1 * 1024 * 1024`, `_MAX_ARCHIVE_BYTES = 256 * 1024 * 1024`, `_MAX_MEMBERS = 20_000`, `_MAX_EXPANDED_BYTES = 1 * 1024 * 1024 * 1024`, `_HTTP_TIMEOUT = 30`.
- `_build_opener(token: str | None, *, env=None) -> urllib.request.OpenerDirector`: builds opener with `ProxyHandler()` (no args — reads `HTTPS_PROXY`/`NO_PROXY`/etc. from environment automatically via `urllib.request.getproxies()`) + custom redirect handler + `HTTPSHandler`. No `HTTPHandler` (HTTP disabled). The custom redirect handler: (a) rejects any redirect to a different origin from the **originally-requested** URL — the originally-requested URL must be captured before `urlopen` and compared against the redirect `Location`; same-origin redirects are forwarded with all headers intact; (b) rejects HTTP redirect targets; (c) rejects redirect `Location` URLs containing user-info. The same-origin anchor for artifact URL validation (`_resolve_artifact_url`) uses the originally-requested channel descriptor URI — not the post-redirect final URL — so cross-origin redirects must be rejected rather than updated as the new anchor. Note: `ProxyHandler(env_dict)` takes a `{scheme: url}` mapping, NOT the raw `os.environ` dict — always use `ProxyHandler()` or `ProxyHandler(urllib.request.getproxies())` to read env correctly. Note: proxy tests must monkeypatch `os.environ` (not pass via `env=`), since `ProxyHandler()` reads from `os.environ`, not from the `env=` injectable.
- `_fetch_bytes_limited(url, opener, max_bytes, timeout) -> bytes`: streams response; running counter; raises `CatalogueError` if `max_bytes` exceeded.
- `_parse_descriptor(data: bytes) -> dict`: validates JSON, required fields, `schema == 1`, `kind == "agentbundle-catalogue"`, returns parsed dict.
- `_resolve_artifact_url(descriptor_url: str, artifact_field: str) -> str`: resolves relative or absolute artifact URL against descriptor URL; checks same origin (scheme+host+port all equal); checks HTTPS; rejects HTTP; rejects user-info in netloc.
- `_check_client_version(minimum: str | None, *, running_version: str | None = None)`: no-op if `minimum is None`; reads running version via `agentbundle.__version__` (module attribute lookup, not a `from agentbundle import __version__` copy — the latter can't be monkeypatched); the `running_version` kwarg overrides for testing (`_check_client_version("10.0.0", running_version="9.9.9")`); parses both as `(MAJOR, MINOR, PATCH)` integer tuples (never lexicographic); raises `CatalogueError` if the running version is older; raises `CatalogueError` (not crash) if either version string does not match `DIGIT.DIGIT.DIGIT`.
- `_stream_and_verify(url: str, expected_sha256: str, opener, timeout) -> Path`: streams to a temp file; computes SHA-256; raises on mismatch (names both); returns temp file path.
- `_safe_extract(archive_path: Path, dest: Path)`: iterates members; checks each for traversal, absolute path, symlink, hard link, device/FIFO; raises on any violation; tracks member count and expanded bytes; extracts clean members.
- `fetch_catalogue_archive(source_uri: str, *, env=None) -> Path`: top-level function called by `resolve_catalogue`. Parses scheme; dispatches to `catalogue+https` (descriptor fetch → artifact resolve → stream+verify → extract) or `archive+https` (direct stream+verify → extract).

**Done when:** all tests above pass; `fetch_catalogue_archive` importable from `agentbundle.https_catalogue`.

---

### T3: Wire fetcher into `resolve_catalogue`

**Depends on:** T1, T2

**Touches:** `packages/agentbundle/agentbundle/catalogue.py`

**Tests:**
- `test_resolve_catalogue_catalogue_https_dispatches` (integration with local server): call `resolve_catalogue("catalogue+https://localhost:PORT/stable.json")`; assert returns a `Path` to the extracted temp dir. Verifies AC6.
- `test_resolve_catalogue_archive_https_dispatches` (integration): similar for `archive+https://`. Verifies AC24.
- `test_resolve_catalogue_http_explicit_arg_rejected`: call `resolve_catalogue("catalogue+http://example.test/stable.json")`; assert `CatalogueError` is raised with a clear HTTPS-only message (not a local-path-not-found error). Verifies AC34.
- `test_install_via_catalogue_https_records_channel_uri` (integration — requires packstate-source-provenance applied): run full `agentbundle install` against a local HTTPS server fixture; read the written state row; assert `state.row(pack_name, adapter).source == "catalogue+https://localhost:PORT/stable.json"` (or its canonicalized form). Verifies AC8.
- `test_install_via_archive_https_records_archive_uri` (integration — requires packstate-source-provenance applied): run full `agentbundle install` with an `archive+https://` source URI including `#sha256=<64hex>` fragment; read the written state row; assert `state.row(pack_name, adapter).source == canonicalize_source(archive_uri)` with the `#sha256=` fragment intact. Verifies AC8b.
- Existing `resolve_catalogue` tests pass unchanged. Verifies AC31.

**Approach:**
- In `resolve_catalogue`, before the existing `git+https://` branch:
  1. Add an explicit reject branch for `value.startswith("catalogue+http://") or value.startswith("archive+http://")` → raise `CatalogueError("HTTPS-only: catalogue+http:// and archive+http:// are not supported; use catalogue+https:// or archive+https://")`. This prevents the layer-1 bypass (explicit arg skips `_is_valid_source`) from silently treating an HTTP catalogue URL as a local path.
  2. Add the dispatch branch for `value.startswith("catalogue+https://") or value.startswith("archive+https://")` → call `fetch_catalogue_archive(value)` from `agentbundle.https_catalogue` and return the result.
- Import `fetch_catalogue_archive` lazily inside the branch (avoids import at top of `catalogue.py` if that causes issues).
- The AC8 and AC8b integration tests both require packstate-source-provenance to be applied first; mark both with `@pytest.mark.requires_packstate_provenance` or a skip condition if the source write at `install.py:1025` is still the legacy literal.

**Done when:** integration tests pass; `resolve_catalogue` routes new schemes correctly.

---

### T4: Full test suite + no-external-network assertion

**Depends on:** T1, T2, T3

**Touches:** none (verification only)

**Tests:**
- `python -m pytest packages/agentbundle/ -x` passes.
- Static check: no test file in the agentbundle package imports `socket` for outgoing connections or contains real domain names other than `example.test` / `localhost`. Verifies AC29, AC31.

**Approach:**
- Run full test suite.
- Grep for suspicious external domains in test files: `grep -r 'github\.com\|artifactory\.' packages/agentbundle/tests/` should return zero hits (other than fixture comments explaining the pattern).

**Done when:** pytest exits 0; grep returns zero hits on real domains in test assertions.

## Rollout

Additive — new schemes, no behavior change for existing sources. Ships as part of ini-004. No infrastructure change; no state schema change.

## Risks

- **`urllib` opener and redirects:** the default opener forwards all request headers to redirect targets. The custom redirect handler must reject cross-origin redirects entirely (not just strip `Authorization`) — this keeps the same-origin anchor for artifact URL validation pinned to the originally-requested channel URI and prevents open-redirect exploitation. The originally-requested URI must be captured before `urlopen` and threaded through the redirect handler. Implement and test this carefully; it's the main security-sensitive path.
- **`tarfile` extraction safety:** Python < 3.12 does not have the `filter=` argument for `extractall`. Use member-by-member iteration with per-member checks on all Python 3.11 targets.
- **Semver comparison without `packaging`:** a hand-rolled `MAJOR.MINOR.PATCH` tuple comparison is simpler than it looks — but it fails on pre-release suffixes (`1.0.0-alpha`). Document the limitation: only semver `MAJOR.MINOR.PATCH` is supported for `minimum_agentbundle_version`.
- **`Content-Length` spoofing:** enforce byte counter during streaming regardless of header. Already in design — must be verified in tests.

## Changelog

- 2026-07-23: initial plan
- 2026-07-23: second adversarial review — fixed Blocker: cross-origin redirect rejection in redirect handler + same-origin anchor pinned to originally-requested URI (AC21d); added AC5b + T1 test for archive+https:// user-info rejection (C4); fixed proxy test to use monkeypatch os.environ (C5); reordered AC26-31 before AC32-37 in spec (Nit 6); added running-version parse assumption (Nit 7); removed "registered" from same-origin definition (Nit 8)
- 2026-07-23: third adversarial review — added T3 integration test test_install_via_archive_https_records_archive_uri for AC8b (Blocker); added fragment-preservation Assumption entry in spec citing packstate rule 8 + test_canonicalize_fragment_preserved (Concern 2)
- 2026-07-23: fourth adversarial review — extended skip-guard note to cover both AC8 and AC8b integration tests (Nit)
- 2026-07-23: fifth adversarial review — removed stale "strip Authorization" language from design decisions (line 35), _build_opener approach (step b), and test_bearer_token_not_forwarded_cross_host (rewritten to assert CatalogueError); updated AC21 to reference reject-by-AC21d, not strip-on-forward
- 2026-07-23: sixth adversarial review — fixed Resilience section to say integer-tuple not lexicographic; removed importlib.metadata duplicate version source (Concern + Nit)
- 2026-07-23: seventh adversarial review — added running_version kwarg to _check_client_version (module-attr not from-import, injectable for tests); updated test_minimum_version_ten_vs_nine to pass running_version="9.9.9" explicitly
- 2026-07-23: eighth adversarial review — fixed AC11 inverted wording ("older than" → "newer than") so it correctly names the client-too-old failure case

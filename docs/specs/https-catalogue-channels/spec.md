# Spec: HTTPS Catalogue Channels

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0072 (D1, D5, D6), ADR-0036 (source resolution chain), RFC-0031 (stdlib-only, no new runtime dep), spec/packstate-source-provenance (canonicalize_source function used for AC8)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

agentbundle currently resolves catalogues only from local directories or `git+https://` GitHub archives. Enterprise environments behind an internal Artifactory or other HTTPS artifact server have no supported path. This spec adds two new source URL schemes — `catalogue+https://` (mutable channel descriptor → immutable archive + SHA-256) and `archive+https://` (direct pinned archive URL) — to the agentbundle source resolution chain. The resolver fetches, verifies, and extracts archives using Python 3.11 stdlib only, enforcing named safety limits on descriptor size, archive size, member count, and expanded bytes, and rejecting path traversal, symlinks, hard links, and special files. Bearer-token auth is supplied via environment variable, never persisted or printed. The logical channel URI (not the temporary extraction path) is recorded as the installed source.

## Boundaries

### Always do

- Enforce all six named safety limits (descriptor 1 MiB, archive 256 MiB, members 20 000, expanded 1 GiB, finite HTTP timeout) even when `Content-Length` is absent or reports a lower value.
- Verify SHA-256 during streaming download; fail before extraction on mismatch — name expected and received digests in the error.
- Clean up temporary directories on any failure path (success may keep them until the outer install completes; failure must always clean up).
- Reject cross-origin artifact URLs — the artifact URL must resolve to the same origin (scheme + host + port) as the **originally-requested** channel descriptor URL (not the post-redirect final URL).
- Reject HTTP (non-TLS) artifact and channel URLs — HTTPS only.
- Reject URL user-info credentials in both channel and artifact URLs.
- Use `AGENTBUNDLE_HTTP_BEARER_TOKEN` as the sole bearer-token source; never persist, print, log, or include in exception repr or `__str__`.
- Reject path traversal (`..`), absolute paths, symlinks, hard links, device files, and FIFOs during archive extraction.
- Honor `HTTPS_PROXY` and `NO_PROXY` via the standard `urllib` proxy handler; the custom opener must explicitly preserve proxy support alongside bearer-token injection and redirect control.
- Check `minimum_agentbundle_version` (when present in channel descriptor) against the running version before downloading the archive; fail with a clear version error if the client is older.
- Record the logical channel URI (e.g. `catalogue+https://…/channels/stable.json`) as the installed source, not the temporary extraction path.
- Use `example.test` placeholders in all tests and documentation — no real org endpoints.

### Ask first

- Relaxing or removing any of the six named safety limits.
- Adding a new archive format beyond `.tar.gz`.
- Adding a `--no-verify` or `--skip-integrity-check` flag.
- Caching channel descriptors or archives across invocations.
- Supporting `archive+https://` with a hash algorithm other than SHA-256.
- Adding certificate-disable or certificate-override options.

### Never do

- Follow a redirect during the channel descriptor or archive fetch to a different origin (scheme + host + port) from the originally-requested URL — cross-origin redirects collapse the same-origin anchor for artifact validation and forward the bearer token to an untrusted host.
- Accept HTTP (non-TLS) URLs for channel descriptors or artifacts.
- Forward the bearer token to a different host under any redirect.
- Persist the bearer token to disk, state, logs, or error messages.
- Allow `ignore-TLS-errors` or any TLS-bypass option.
- Add a new runtime dependency — Python 3.11 stdlib (`urllib`, `tarfile`, `hashlib`, `tempfile`) only.
- Use a temporary extraction path as the canonical source identity.
- Accept cross-origin artifact URLs (the `artifact` field must resolve to the same host as the channel descriptor URL).
- Extract archives without first verifying the SHA-256 digest.
- Silently fall back to an alternate source when integrity verification fails.

## Testing Strategy

- **TDD** for all validation rules (channel descriptor schema, URL safety checks, cross-origin check, user-info rejection, safety limits). Each rule has a unit test with a minimal fixture triggering the rejection.
- **TDD** for SHA-256 streaming verification: test digest match (happy path) and mismatch (fail before extraction, clean up temp dir, name both digests in error).
- **TDD** for extraction safety: each rejected path pattern (traversal, absolute, symlink, hard link, special file) has a test with a synthetic `tarfile` fixture that triggers the rejection.
- **TDD** for `minimum_agentbundle_version`: test client-older-than-minimum (fail before archive download) and client-equal-or-newer (proceed).
- **Goal-based check** for `_is_valid_source` extension: `_is_valid_source("catalogue+https://example.test/…")` returns `True`; `_is_valid_source("catalogue+http://…")` returns `False`; `_is_valid_source("archive+https://example.test/…#sha256=<64hex>")` returns `True`.
- **Goal-based check** for no external network calls in tests: all tests use a local in-process HTTP server fixture (e.g. `http.server.HTTPServer` in a thread) — no external network calls permitted in the test suite.
- **TDD** for proxy support: assert the custom opener includes a `ProxyHandler`; test with a mock proxy environment variable set.
- **Goal-based check** for bearer token redaction: in all error messages raised by the HTTPS fetcher, assert the literal `AGENTBUNDLE_HTTP_BEARER_TOKEN` value does not appear.

## Acceptance Criteria

- [ ] AC1: `_is_valid_source("catalogue+https://example.test/path/stable.json")` returns `True`.
- [ ] AC2: `_is_valid_source("catalogue+http://example.test/path/stable.json")` returns `False` (HTTP rejected).
- [ ] AC3: `_is_valid_source("archive+https://example.test/path/release.tar.gz#sha256=" + "a" * 64)` returns `True`.
- [ ] AC4: `_is_valid_source("archive+http://example.test/…")` returns `False`.
- [ ] AC5: `_is_valid_source("catalogue+https://user:pass@example.test/…")` returns `False` (user-info rejected).
- [ ] AC5b: `_is_valid_source("archive+https://user:pass@example.test/path/r.tar.gz#sha256=" + "a" * 64)` returns `False` (user-info rejected in archive+https:// URLs).
- [ ] AC6: A `catalogue+https://` install fetches the channel descriptor JSON, validates schema v1 fields (`schema=1`, `kind="agentbundle-catalogue"`, `bundle`, `channel`, `release`, `artifact`, `sha256` all required), resolves the artifact URL, streams and SHA-256-verifies the archive before extraction, extracts to a temp directory, and returns the temp directory path for the normal pack-locate flow.
- [ ] AC7: SHA-256 mismatch fails before any extraction; the error names both expected and received digests; the temp directory is cleaned up.
- [ ] AC8: The installed `PackState.source` after a `catalogue+https://` install equals `canonicalize_source(channel_descriptor_url)` — the channel URI, not the temp dir path. (Verification requires `spec/packstate-source-provenance` AC11 to be in place; AC8 is verified by an integration test that installs via a local HTTPS server fixture and reads the written state row.)
- [ ] AC8b: After an `archive+https://` install, `PackState.source` equals `canonicalize_source(archive_uri)` — the full `archive+https://` URL with the `#sha256=<64hex>` fragment preserved (the fragment is part of the canonical identity; it distinguishes this archive from a different version at the same URL).
- [ ] AC9: A cross-origin `artifact` URL (different scheme, host, or port from the channel descriptor URL) is refused with a clear error before any download.
- [ ] AC10: An HTTP (non-TLS) `artifact` URL is refused even when the channel descriptor itself is HTTPS.
- [ ] AC11: `minimum_agentbundle_version` present in the descriptor and **newer** than the running version fails before archive download with a version error naming both versions (the client is too old to satisfy the minimum requirement).
- [ ] AC12: `minimum_agentbundle_version` absent or equal-to-or-older than the running version proceeds normally.
- [ ] AC13: An archive exceeding 256 MiB (compressed) is rejected during streaming, before extraction; temp dir cleaned up.
- [ ] AC14: An archive with more than 20 000 members is rejected during extraction; temp dir cleaned up.
- [ ] AC15: Total expanded bytes exceeding 1 GiB is rejected during extraction; temp dir cleaned up.
- [ ] AC16: A `tar.gz` member with a path containing `..` is rejected; extraction aborted; temp dir cleaned up.
- [ ] AC17: A `tar.gz` member with an absolute path (starting with `/`) is rejected; extraction aborted; temp dir cleaned up.
- [ ] AC18: A `tar.gz` member that is a symlink is rejected; extraction aborted; temp dir cleaned up.
- [ ] AC19: A `tar.gz` member that is a hard link is rejected; extraction aborted; temp dir cleaned up.
- [ ] AC20: A `tar.gz` member that is a device file or FIFO is rejected; extraction aborted; temp dir cleaned up.
- [ ] AC21: `AGENTBUNDLE_HTTP_BEARER_TOKEN` is sent as `Authorization: Bearer <token>` on requests to the channel descriptor and archive URLs; a cross-origin redirect is rejected before any request is sent to the redirect target (per AC21d), so the token is never forwarded to a different origin by construction — not by stripping the header on forward.
- [ ] AC21b: A redirect to an HTTP (non-TLS) URL is rejected regardless of whether the bearer token is set.
- [ ] AC21c: A redirect `Location` URL containing user-info credentials is rejected.
- [ ] AC21d: A redirect during the channel descriptor or archive fetch to a different origin (scheme, host, or port different from the **originally-requested** URL) is rejected before the redirect is followed — the custom redirect handler enforces this, ensuring the same-origin anchor for artifact URL validation cannot be undermined by an open-redirect exploit on a trusted host.
- [ ] AC22: `AGENTBUNDLE_HTTP_BEARER_TOKEN` does not appear in any exception message, error string, or log line emitted by the HTTPS fetcher.
- [ ] AC23: `HTTPS_PROXY` and `NO_PROXY` environment variables are honored; the custom opener includes a `ProxyHandler`.
- [ ] AC24: An `archive+https://` URL with a valid `#sha256=<64 lowercase hex>` fragment is fetched, SHA-256-verified, extracted, and the pack located — no channel descriptor fetch.
- [ ] AC25: An `archive+https://` URL without a `#sha256=` fragment, or with a fragment that is not exactly 64 lowercase hexadecimal characters, is rejected at validation time (not at download time).
- [ ] AC25b: A channel descriptor `sha256` field value that is not exactly 64 lowercase hexadecimal characters is rejected at descriptor-parse time with a clear error.
- [ ] AC26: Channel descriptor fetch respects the 1 MiB size limit; a descriptor exceeding this limit is rejected before JSON parsing.
- [ ] AC27: HTTP timeout is finite and documented as a named constant; requests that exceed it fail with a clear timeout error.
- [ ] AC28: Temp directory is cleaned up on all failure paths (digest mismatch, extraction error, schema error, timeout, OS error).
- [ ] AC29: No real org endpoints appear in any test or documentation file delivered by this spec; all examples use `example.test` placeholders.
- [ ] AC30: No new runtime dependency is introduced; implementation uses Python 3.11 stdlib only (`urllib`, `tarfile`, `hashlib`, `tempfile`, `json`, `ssl`, `http`).
- [ ] AC31: All existing agentbundle tests pass after the change with no modification to the tests themselves.
- [ ] AC32: A channel descriptor missing any required field (`schema`, `kind`, `bundle`, `channel`, `release`, `artifact`, `sha256`) is rejected with a clear error naming the missing field.
- [ ] AC33: A channel descriptor with `schema != 1` or `kind != "agentbundle-catalogue"` is rejected with a clear error.
- [ ] AC34: `resolve_catalogue` rejects `catalogue+http://` and `archive+http://` explicit args (layer-1 bypass of `_is_valid_source`) with a clear HTTPS-only error rather than treating them as local paths.
- [ ] AC35: `minimum_agentbundle_version` is compared using integer-tuple `(MAJOR, MINOR, PATCH)` comparison, not lexicographic string comparison; a value of `10.0.0` is correctly seen as newer than `9.0.0`.
- [ ] AC36: A malformed (non-numeric) `minimum_agentbundle_version` value in the descriptor is rejected with a clear error rather than crashing.
- [ ] AC37: `AC30` (stdlib-only) is verified by a goal-based check confirming `https_catalogue.py` imports no non-stdlib module and `pyproject.toml` dependencies are unchanged.

## Assumptions

- Technical: Python 3.11 stdlib is sufficient — `urllib.request`, `tarfile`, `hashlib`, `tempfile`, `json`, `ssl`. (source: RFC-0072 § Key assumptions; RFC-0031 Principle 3)
- Technical: `_is_valid_source` at `source_defaults.py:76` is the single targeted extension point for scheme validation; the fix is a new `startswith` branch before the existing `urlsplit` scheme gate at line 96. (source: RFC-0072 § Evidence & prior art; code inspection)
- Technical: `resolve_catalogue` in `catalogue.py` is the fetch entry point; the new `catalogue+https://` and `archive+https://` handlers extend it. (source: code inspection — `resolve_catalogue` is called at `install.py:209` with the source URI)
- Technical: `urlsplit("catalogue+https://…").scheme` returns `"catalogue+https"` (non-empty), so the existing scheme gate at `_is_valid_source:96` would reject it without the new branch. (source: RFC-0072 § Evidence & prior art spike result)
- Technical: SHA-256 streaming is feasible with `hashlib.sha256()` updated in chunks during `urllib` streaming download. (source: standard Python practice; no confirmation needed)
- Process: RFC-0072 D1 accepted — mutable channel descriptor → immutable archive + SHA-256 is the approved pattern. (source: RFC-0072 status: Accepted)
- Product: No credential storage in agentbundle — bearer token lives only in env var for the duration of the process. (source: RFC-0072 D1; user confirmation 2026-07-23)
- Technical: The spec/packstate-source-provenance `canonicalize_source` function handles the `catalogue+https://` scheme as a remote URL via its rule 8 (lowercase scheme+netloc + normalize path). Confirmed by explicit test `test_canonicalize_catalogue_https_scheme` in packstate-source-provenance T2. (source: spec/packstate-source-provenance AC9, plan.md T2)
- Technical: `canonicalize_source` preserves the URI fragment (including `#sha256=…`) for `archive+https://` URLs — rule 8 preserves query and fragment when no credential params are present. Confirmed by explicit test `test_canonicalize_fragment_preserved` in packstate-source-provenance T2. This is the guarantor of AC8b's stated rationale that distinct pinned archives at the same URL produce distinct source identities. (source: spec/packstate-source-provenance plan.md rule 8, T2)
- Technical: `agentbundle.__version__` is assumed to be a clean `MAJOR.MINOR.PATCH` string (no pre-release suffixes). Dev installs with pre-release version strings may cause `_check_client_version`'s running-version parse to raise a clear error; this is documented behavior, not a crash. (source: design decision — scope `minimum_agentbundle_version` to clean semver only)

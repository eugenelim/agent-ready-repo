# credbroker changelog

All notable changes to the `credbroker` Python package.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
the package targets pre-1.0 semver as documented in `docs/CONVENTIONS.md`
— a minor bump on a 0.x release MAY be breaking.

## [0.5.0] — 2026-08-06

### Added

- **SSO session recapture.** `refresh_sso_session(profile)` re-establishes an
  expired session without a human; `register_sso_session(...)` performs a first
  capture. `refresh_sso_session` takes **only a profile** — the signature is
  structurally incapable of forwarding a sign-in destination, so an automated
  caller cannot choose where the browser goes. `register_sso_session` is the
  sole function that accepts one, and always drives the engine's ephemeral
  capture mode.

- **`validate_sso_profile(profile)`** — the shared grammar guard for the name
  that becomes a filename and a keychain entry:
  `^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$` under `re.fullmatch`, excluding Windows
  reserved device names.

- **`derive_sso_destination(base_url, *, strategies=())`** — ask a resource
  server where it sends users to sign in, via RFC 9728 protected resource
  metadata, then OIDC discovery / RFC 8414, then an opt-in named vendor probe.
  Returns an **origin** — `scheme://host:port`, the port always explicit and an
  IPv6 host bracketed (`https://idp.example:443`) — or `None`. Normalise your
  own configured destination the same way before comparing; a server is free to
  spell the default port either way. `None` is a real outcome, since SAML-only
  SPs expose no discovery. Bounded: https-only at every hop, redirects not
  followed, 5 s socket timeout under a 15 s budget, a 64 KiB body cap, strict
  TLS, and no auth headers.

- **Four exception types** so a caller can tell an expired session from a broker
  failure: `SsoProfileNotRegisteredError` (subclasses
  `SsoSessionUnavailableError`, so existing handlers keep working),
  `SsoInteractionRequiredError`, `SsoRecaptureFailedError`,
  `SsoBrokerUnavailableError`.

### Changed

- **`load_sso_cookies` no longer passes the whole environment to the engine, and
  no longer runs unbounded.** It composes the child environment from an
  allowlist — so a spawned process cannot inherit an unrelated `*_API_TOKEN` —
  and applies a 30-second wall-clock bound with a whole-process-tree kill.

- **Potentially breaking:** a timeout, a spawn failure, or an engine-internal
  error now raises `SsoBrokerUnavailableError` rather than
  `SsoSessionUnavailableError`. Code that retries or re-registers on the latter
  no longer does so for a slow keychain. Catch `SsoError` for the previous
  blanket behaviour.

- `load_sso_cookies` validates the profile against the grammar before spawning,
  so every entry point that reaches the engine is guarded.

## [0.4.0] — 2026-07-27

### Changed

- **Ruff + mypy CI gates.** `credbroker` is now covered by the repo-wide
  `ruff check` and `mypy` gates added to `build-check.yml` and
  `build-check-windows.yml`. No behaviour changes; all internal code now
  satisfies `mypy --strict` import checking.

### Fixed

- **`_vault.py`: explicit `binascii` import.** The exception handler in
  `_vault.py` previously caught `base64.binascii.Error` — a private
  cross-module reference that worked in practice but is not part of any
  stable interface. Changed to `import binascii` at the top of the module
  and `binascii.Error` in the handler, which is the documented form.
- **`_vault.py`: pathlib migration.** `os.replace()` and `os.unlink()` calls
  replaced with `Path.replace()` / `Path.unlink()` to eliminate `os`-module
  usage where `pathlib` already owns the path object.

## [0.3.0] — 2026-07-27

### Fixed

- **`sso-broker` Windows console hardening.** The companion `sso-broker.py`
  script now reconfigures stdout and stderr to UTF-8 inside its
  file-path-invocation bootstrap gate. On a Windows cp1252 console, the
  previous code raised `UnicodeEncodeError` when the script emitted em-dash
  messages before the Python import guard ran. The fix mirrors the pattern
  applied to the other credentialed CLIs (figma, confluence-crawler,
  confluence-publisher, jira, jira-align) in agentbundle 0.20.1.

## [0.2.0] — 2026-06-16

### Added

- **SSO web-session cookie family (RFC-0035)** — a second consumer-resolution
  family alongside the token `creds` family. `load_sso_cookies(profile)` resolves
  a captured SSO web session to an on-disk `0600` cookie-jar **path** (path-not-
  value handoff) by subprocess-invoking the unchanged `sso-broker` engine; it
  fails closed (`SsoSessionUnavailableError` / `SsoBrokerNotInstalledError`) and
  never silently falls back to the token path.
- **SSO confinement primitives** — `filter_jar_to_domains`,
  `domain_in_cookie_domains`, `require_host_in_cookie_domains`,
  `validate_https_url`, and `validate_root_relative_endpoint`: the reusable
  https-only / root-relative / cookie-domain guards the engine does not perform,
  with a label-boundary suffix match (`evil-corp.example.com` is rejected against
  `corp.example.com`). The base import graph stays stdlib-only.

## [0.1.1] — 2026-06-12

### Changed

- **README rewritten for adoption** — badges, a corrected attribute-access
  usage example (`creds.API_TOKEN`), an explicit per-OS resolution model
  (macOS Keychain / Windows Credential Manager / dotfile floor elsewhere),
  and absolute documentation links that render on the PyPI project page.

## [0.1.0] — 2026-06-10

Initial public release (RFC-0023): in-process three-tier credential
resolver (environment variable → OS keyring → `0600` dotfile floor), with
an optional encrypted-at-rest vault under the `[crypto]` extra.

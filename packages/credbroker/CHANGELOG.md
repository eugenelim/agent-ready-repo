# credbroker changelog

All notable changes to the `credbroker` Python package.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
the package targets pre-1.0 semver as documented in `docs/CONVENTIONS.md`
— a minor bump on a 0.x release MAY be breaking.

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

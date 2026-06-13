# credbroker changelog

All notable changes to the `credbroker` Python package.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
the package targets pre-1.0 semver as documented in `docs/CONVENTIONS.md`
— a minor bump on a 0.x release MAY be breaking.

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

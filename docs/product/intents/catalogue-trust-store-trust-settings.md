# Catalogue trust-store Never Trust enforcement

- **Slug:** `catalogue-trust-store-trust-settings`
- **Level:** feature
- **Status:** Accepted
- **Owner:** eugenelim


## Outcome

The macOS corporate trust fallback excludes certificates that an administrator has explicitly marked Never Trust before augmenting the default TLS context.

## Boundary

- Preserve RFC-0086 fallback timing, add-without-replace behavior, administrator-keychain scope, diagnostics, and user opt-out.
- Do not read the user-writable login keychain or change Windows and Linux trust-store behavior.
- Do not add a dependency or silently accept certificates when trust-setting evaluation is unavailable.

## Owner

- AgentBundle maintainers.

## Resolved questions — recommended answers, checked 2026-11-05

- **Interface:** read the administrator trust settings with `security trust-settings-export -d <file>` and parse the plist with the standard library. The export keys each certificate by the upper-case SHA-1 of its DER bytes, and an entry carrying a `trustSettings` result of Deny (`kSecTrustSettingsResultDeny`) is an explicit Never Trust. Checked on a macOS 26.5.1 host: the export ran without a prompt, wrote a version 1 plist, and all 8 of its keys matched the SHA-1 of a certificate in `/Library/Keychains/System.keychain`. That host has no Deny entry, so the Deny shape is tested from fixture plists, not live.
- **When trust settings cannot be read:** skip the macOS fallback and emit one distinct, redacted diagnostic. Do not fail the catalogue request. Skipping returns to the behaviour before RFC-0086, which never trusts more than the default store, so it fails closed. `AGENTBUNDLE_NO_SYSTEM_TRUST` stays as the user opt-out.

## Projection

- Shape a dedicated full-mode delivery spec constrained by RFC-0086, with security review and tests for explicit distrust, unavailable trust settings, duplicate certificates, and redacted diagnostics.

## Opportunity

The current macOS fallback imports every certificate from the administrator keychain even when an administrator has explicitly revoked trust for one of them.

## Assumptions

- RFC-0086 is the existing Engine-Change-RFC authority and its Windows filtering behavior is the comparison shape, not an instruction to add Windows interop.

## Readiness

- **Route:** new-spec, full mode with security review, constrained by RFC-0086. The change is in `packages/agentbundle/agentbundle/system_trust.py`, whose `system_anchor_pem` docstring still records the gap, and it runs the existing `_RUNNER` test seam. The protected-tree gate (`tools/lint-catalogue-curation-guard.py`) checks only that the commit message carries an `Engine-Change-RFC:` trailer. Recent commits cite an accepted RFC or write `n/a` with the governing record and reason, so no new RFC is needed for this change.
- **First slice, one session:** export the administrator trust settings through `_RUNNER`, parse them with `plistlib`, drop each certificate whose SHA-1 has a Deny result before the PEM is returned, and skip the fallback with a redacted diagnostic when the export or parse fails.
- **Agent-only proof:** checked-in fixture plists for explicit Deny, allow with constraints, a duplicate certificate, a malformed plist, and an empty list; assert that the diagnostic names no certificate subject.
- **Manual follow-up, not blocking:** one real-Mac pass using the existing `docs/specs/catalogue-corporate-trust-store/notes/manual-qa.md`, with a certificate the administrator has marked Never Trust.
- **Size:** S to M.

## Source

- Mode: repo-origin
- Locator: docs/specs/catalogue-corporate-trust-store/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

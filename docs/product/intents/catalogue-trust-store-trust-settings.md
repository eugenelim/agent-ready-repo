# Catalogue trust-store Never Trust enforcement

- **Status:** Accepted


## Outcome

The macOS corporate trust fallback excludes certificates that an administrator has explicitly marked Never Trust before augmenting the default TLS context.

## Boundary

- Preserve RFC-0086 fallback timing, add-without-replace behavior, administrator-keychain scope, diagnostics, and user opt-out.
- Do not read the user-writable login keychain or change Windows and Linux trust-store behavior.
- Do not add a dependency or silently accept certificates when trust-setting evaluation is unavailable.

## Owner

- AgentBundle maintainers.

## Unresolved questions

- Which supported macOS trust-settings interface provides a bounded, stable, and testable mapping between exported certificates and explicit Never Trust decisions?
- Should inability to evaluate administrator trust settings skip the macOS fallback or fail the catalogue request with a distinct diagnostic?

## Projection

- Shape a dedicated full-mode delivery spec constrained by RFC-0086, with security review and tests for explicit distrust, unavailable trust settings, duplicate certificates, and redacted diagnostics.

## Opportunity

The current macOS fallback imports every certificate from the administrator keychain even when an administrator has explicitly revoked trust for one of them.

## Assumptions

- RFC-0086 is the existing Engine-Change-RFC authority and its Windows filtering behavior is the comparison shape, not an instruction to add Windows interop.


## Source

- Mode: repo-origin
- Locator: docs/specs/catalogue-corporate-trust-store/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

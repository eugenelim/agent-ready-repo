# Credential-pack defaults are safely projected

- **Status:** Draft
- **Level:** feature

## Outcome

Credential-pack catalogue defaults reach standard-library-only skill scripts through an installer projection without becoming trusted sign-in or automatic-refresh authority.

## Boundary

- The catalogue pack-defaults cascade, installer projection to a per-pack defaults file, provenance and precedence, and credential-pack consumption of non-sensitive defaults.
- Sign-in destinations, authentication defaults, headed automatic refresh, broker-written state, and unrelated catalogue configuration remain outside this intent.

## Owner

- AgentBundle distribution and credential-pack maintainers; no individual owner is recorded.

## Unresolved questions

- Accept an RFC-0074 addendum authorizing the projection and its trust boundary.
- Record an ADR extending ADR-0059 with the projected file location, precedence, provenance, and update behavior.

## Projection

- An RFC-0074 addendum and ADR-0059 extension followed by one focused implementation specification for installer projection and credential-pack consumption.

## Opportunity

This intent absorbs pack-config-catalogue-sso-defaults. RFC-0074 shipped the catalogue cascade, but its baked AgentBundle layer is unreachable from standard-library-only skill scripts and no safe installer projection exists.

## Assumptions

- The projected defaults file remains catalogue-derived untrusted configuration even when the installer writes it.
- The file cannot supply a sign-in destination or authentication default, and automatic refresh remains pinned to broker-written state.


## Source

- Mode: repo-origin
- Locator: docs/specs/jira-check-sso-auto-login/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

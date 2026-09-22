# Credential-pack defaults are safely projected

- **Slug:** `credential-pack-defaults-projection`
- **Status:** Draft
- **Level:** feature
- **Owner:** eugenelim

## Outcome

Credential-pack catalogue defaults reach standard-library-only skill scripts through an installer projection without becoming trusted sign-in or automatic-refresh authority.

## Boundary

- The catalogue pack-defaults cascade, installer projection to a per-pack defaults file, provenance and precedence, and credential-pack consumption of non-sensitive defaults.
- Sign-in destinations, authentication defaults, headed automatic refresh, broker-written state, and unrelated catalogue configuration remain outside this intent.

## Owner

- AgentBundle distribution and credential-pack maintainers; no individual owner is recorded.

## Unresolved questions

- Accept an RFC-0101 addendum authorizing the projection and its trust boundary.
- Record an ADR extending ADR-0059 with the projected file location, precedence, provenance, and update behavior.

## Projection

- An RFC-0101 addendum and ADR-0059 extension followed by one focused implementation specification for installer projection and credential-pack consumption.

## Opportunity

This intent absorbs pack-config-catalogue-sso-defaults. RFC-0101 shipped the catalogue cascade, but its baked AgentBundle layer is unreachable from standard-library-only skill scripts and no safe installer projection exists.

A second consumer now needs the same projection: [`catalogue-level-telemetry-endpoint-default`](catalogue-level-telemetry-endpoint-default.md) wants an enterprise operator to bake a telemetry endpoint once so users of that catalogue export with no configuration step. Its readers are standard-library-only for a stronger reason than convenience — the sender's contract forbids any runtime dependency beyond the standard library, and the hook that invokes it is stdlib-only by repository convention. Two independent consumers blocked on one missing hop is the argument for solving the projection generally rather than per pack, and it means the trust boundary this intent draws has to hold for a non-credential value too: an endpoint is a data destination, not a sign-in destination, so it sits outside the sensitive class this intent refuses to project while still needing the same delivery path.

## Assumptions

- The projected defaults file remains catalogue-derived untrusted configuration even when the installer writes it.
- The file cannot supply a sign-in destination or authentication default, and automatic refresh remains pinned to broker-written state.


## Source

- Mode: repo-origin
- Locator: docs/specs/jira-check-sso-auto-login/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

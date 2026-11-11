# Credential-pack defaults are safely projected

- **Slug:** `credential-pack-defaults-projection`
- **Status:** Accepted
- **Accepted:** 2026-11-05 by eugenelim, lifecycle owner. A fresh independent intent-mode shaping review on 2026-11-05 returned zero MALFORMED tokens.
- **Shaping-reviewed:** 2026-11-05
- **Level:** feature
- **Owner:** eugenelim

## Outcome

Credential-pack catalogue defaults reach standard-library-only skill scripts through an installer projection without becoming trusted sign-in or automatic-refresh authority.

## Boundary

- The catalogue pack-defaults cascade, installer projection to a per-pack defaults file, provenance and precedence, and credential-pack consumption of non-sensitive defaults.
- Sign-in destinations, authentication defaults, headed automatic refresh, broker-written state, and unrelated catalogue configuration remain outside this intent.

## Owner

- eugenelim, with AgentBundle distribution and credential-pack maintainers.

## Unresolved questions

- Accept RFC-0112, which authorizes the projection and its trust boundary.
- Record an ADR extending ADR-0059 with the projected file location, precedence, provenance, and update behavior.

## Projection

- RFC-0112 and an ADR-0059 extension, followed by one focused implementation specification for installer projection and credential-pack consumption.

## Opportunity

This intent absorbs pack-config-catalogue-sso-defaults. RFC-0101 shipped the catalogue cascade, but its baked AgentBundle layer is unreachable from standard-library-only skill scripts and no safe installer projection exists.

A second consumer now needs the same projection: [`catalogue-level-telemetry-endpoint-default`](FEAT-0017-catalogue-level-telemetry-endpoint-default.md) wants an enterprise operator to bake a telemetry endpoint once so users of that catalogue export with no configuration step. Its readers are standard-library-only for a stronger reason than convenience — the sender's contract forbids any runtime dependency beyond the standard library, and the hook that invokes it is stdlib-only by repository convention. Two independent consumers blocked on one missing hop is the argument for solving the projection generally rather than per pack, and it means the trust boundary this intent draws has to hold for a non-credential value too: an endpoint is a data destination, not a sign-in destination, so it sits outside the sensitive class this intent refuses to project while still needing the same delivery path.

## Assumptions

- The projected defaults file remains catalogue-derived untrusted configuration even when the installer writes it.
- The file cannot supply a sign-in destination or authentication default, and automatic refresh remains pinned to broker-written state.


## Source

- Mode: repo-origin
- Locator: docs/specs/jira-check-sso-auto-login/spec.md
- Revision: 79b23d2944ef2e4e534ae26331c4393aacd7360a
- Authority: repo-origin

## Current truth

Verified 2026-11-05: no installer projection exists. Decided by the owner on 2026-11-05: project generically, for an allowlist of non-sensitive keys only. The telemetry endpoint of FEAT-0017 is the driving consumer. Sign-in destinations and authentication defaults stay refused.

## Readiness

- **Route:** governance first, then one new-spec. This is one implementation slice, so no brief.
- **First step:** RFC-0112 is drafted (Draft). The owner accepting it is the only human gate; the ADR-0059 extension follows acceptance.
- **Then:** one spec for installer projection and consumption.
- **Agent-only proof:** a fixture catalogue that tries to supply `login_url` is refused; an allowlisted telemetry endpoint reaches a stdlib-only reader.
- **Manual dependency:** none.

## Riskiest assumption

**Riskiest assumption:** a stdlib-only reader can consume an installer-written defaults file without that file becoming trusted authority. Tested agent-only with a fixture catalogue that supplies `login_url` and an authentication default (both must be refused) and an allowlisted telemetry endpoint (must reach the reader).

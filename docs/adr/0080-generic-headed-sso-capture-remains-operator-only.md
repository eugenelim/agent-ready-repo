# ADR-0080: Generic headed SSO capture remains operator-only

- **Status:** Accepted
- **Date:** 2026-08-11
- **Decision-makers:** eugenelim
- **Consulted:** security-reviewer, adversarial-reviewer
- **Supersedes:** none
- **Related:** [RFC-0084](../rfc/0084-sso-destination-trust-boundary.md),
  [ADR-0026](0026-sso-consumer-resolution-in-credbroker.md),
  [credential architecture](../architecture/credentials.md), and the
  [`jira-check-sso-auto-login` spec](../specs/jira-check-sso-auto-login/spec.md)

## Decision summary

- **Decision:** The baseline credential-brokers installation will not
  implement or claim a same-principal destination enforcer. Generic headed
  SSO-cookie capture remains operator-only, and automatic refresh remains
  headless.
- **Because:** Every component the supported installation can deploy is owned
  by or bypassable by the same operating-system account as agent-controlled
  code.
- **Applies to:** Generic SSO-cookie capture through `credbroker`,
  `sso-broker.py`, and projected skill scripts.
- **Tradeoff accepted:** Interactive capture retains a known destination-
  poisoning exposure to hostile same-principal code.
- **Revisit if:** A concrete consumer supports remotely bound authorization,
  or the supported deployment can install a component under independent
  authority.

## Context

The supported installation consists of a user-scoped `credbroker` Python
package or vendored fallback, `sso-broker.py`, and projected skill scripts.
Moving destination validation into another Python package, virtual
environment, signed file, or in-process verifier would not change who owns,
modifies, or bypasses the enforcement path.

The current generic SSO-cookie workflow does not use a system-browser callback.
An operator explicitly starts registration, the broker runs its existing
visible capture flow, and later agent-triggered use consumes stored state
headlessly. Automatic refresh must fail when human interaction is required
rather than displaying a login page.

A future OAuth, OpenID Connect, or device-authorization mode could use an
external browser and a remotely bound response. That would return
protocol-specific credentials for a concrete supported consumer, not generic
SAML session cookies, and is not authorized by this decision.

## Decision

The credential-brokers baseline provides no destination security boundary
against hostile code running under the agent principal.

Within supported catalogue workflows:

1. Interactive capture is reachable only through an operator-typed
   registration action.
2. Automatic refresh is always headless and never falls back to visible login.
3. Existing HTTPS, origin, derivation, and success-condition checks remain
   defense in depth for mistakes and ordinary misconfiguration.
4. Those checks must not be described as protection against hostile
   same-principal destination poisoning.
5. No second user-scoped Python package or verifier will be built as a
   destination enforcer.

A destination-protected mode requires a new proposal backed by either:

- a remote authorization protocol that independently binds user approval for
  a concrete consumer; or
- a supported installation class whose code, policy, and invocation contract
  are protected by another authority.

## Decision drivers

- Do not claim a security boundary the supported installation cannot provide.
- Preserve generic SSO-cookie compatibility.
- Prevent automatic workflows from soliciting credentials.
- Avoid maintaining an additional package that changes packaging without
  changing authority.
- Keep future protocol-backed authentication possible without pretending it
  solves generic cookie capture.

## Consequences

**Positive:**

- Automatic agent workflows cannot legitimately open a headed login page.
- The architecture accurately describes the same-principal limitation.
- Four unimplementable destination-boundary backlog entries are closed without
  producing duplicate implementations.
- Other credential privacy, reliability, audit, packaging, and validation work
  continues independently.

**Negative:**

- Generic interactive capture remains vulnerable if hostile same-principal
  code poisons the destination and the operator does not detect it.
- The current deployment has no engineering path to eliminate that exposure.
- A future secure protocol mode would cover only consumers that support it and
  may introduce another credential family.

**Revisit if:** A concrete consumer supports remotely bound authorization, or
the supported deployment can install a component under independent authority.

## Confirmation

- **Mode:** reviewer-checked
- **Signal:** automatic refresh remains headless; headed capture remains
  operator-typed; architecture and product specifications describe destination
  validation only as defense in depth; no open workspace item claims a
  same-principal destination enforcer
- **Owner:** credential-brokers maintainers

## Alternatives considered

- **Another Python package or virtual environment.** Rejected because it remains
  owned and bypassable by the agent principal.
- **A root-owned or signed policy with the current verifier.** Rejected because
  a user-writable or bypassable verifier cannot enforce that policy.
- **A browser extension, privileged helper, or local service.** Technically
  viable, but outside the supported installation envelope.
- **Implement protocol-backed authorization now.** Rejected without a concrete
  consumer, issuer contract, client registration, credential type, and
  migration path.
- **Remove generic headed capture.** Rejected because explicit operator capture
  remains a useful compatibility workflow when its limitation is understood.

## References

- [RFC-0084](../rfc/0084-sso-destination-trust-boundary.md)
- [Credential architecture](../architecture/credentials.md)
- [RFC 8252: OAuth 2.0 for Native Apps](https://www.rfc-editor.org/rfc/rfc8252.html)
- [RFC 8628: OAuth 2.0 Device Authorization Grant](https://www.rfc-editor.org/rfc/rfc8628.html)

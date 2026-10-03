# ADR-0001: Alpha record for navigation tests

- **Status:** Accepted (superseded in part by ADR-0020 for D3)
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** ADR-0020 D3
- **Related:** ADR-0002, RFC-0050, ADR-0001, ADR-9999
- **Related** (additional context): ADR-0003
  - ADR-0010
- **Related** — see also RFC-0060

> This blockquote contains ADR-0020 and ADR-0030.
> Both must NOT count as contextual references: the Related field
> terminated at the blank line above this blockquote.

## Context

Alpha record covers: qualified status, checked partial supersession
(Superseded in part: ADR-0020 D3), all three Related field forms, a
self-reference (ADR-0001 excluded), an unresolved reference (ADR-9999
is not admitted), indented nested bullets, and a blank-line-then-blockquote
that must not count.

## Decision

- **D1:** Components use the shared configuration store at startup.
- **D2:** The configuration store is refreshed every thirty seconds.
- **D3:** Legacy services may cache configuration for up to five minutes.

## Consequences

D3 is superseded in part by ADR-0020, which narrows the caching window.

# Design system foundations for experience design

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0071 D3a](../../rfc/0071-digital-experience-doctrine.md)

## Outcome

Experience-design practitioners can take an approved token taxonomy into a working design-system foundation, with a clear compatibility posture for the tools that consume it.

## Opportunity

The current design-system method stops at deriving a taxonomy, while projects still need a distinct, installable practice for establishing and reviewing the foundation that applies those tokens.

## Assumptions

- The settled XD skill boundaries will distinguish taxonomy naming from foundation implementation.

## What the decision requires

- Add `design-system-foundations` as a distinct `experience-design` skill: it takes a token taxonomy and establishes a working token foundation for a specific project (RFC-0071 D3a).
- Its lightweight mode covers semantic color roles, typography, spacing, radius, focus, key statuses, responsive rules, and core components (RFC-0071 Area D).
- Its full mode covers a DTCG 2025.10-compatible token source, light and dark themes, semantic aliases, full component anatomy, and generated platform outputs (RFC-0071 Area D).
- Keep taxonomy derivation and foundation implementation as separate jobs with distinct triggers, outputs, and reviewers (RFC-0071 D3a).

## Non-goals

- Generated Figma variables, iOS Swift UI tokens, and Android Material tokens are deferred until an adopter need surfaces (RFC-0071 Follow-on work).

## Open questions the RFC left

- The full-mode spec must set the DTCG 2025.10 compatibility posture and fallback for tooling that cannot export that format (RFC-0071 OQ1).

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f

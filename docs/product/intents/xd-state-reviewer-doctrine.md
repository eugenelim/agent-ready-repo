# Experience state and reviewer doctrine

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0071 § Implementation sequence — M3d](../../rfc/0071-digital-experience-doctrine.md)

## Outcome

Teams can assess an experience across its required states and use an experience reviewer that examines cold-read comprehension, task completion, and contract conformance.

## Opportunity

The current experience-reviewer and quality floor do not cover the needed state set or provide the three complementary review passes required for a reliable experience evaluation.

## Assumptions

- Information-architecture object and state guidance will provide the reviewer’s shared surface model.

## What the decision requires

- Extend `quality-floor.md` from 8 to 18 states (RFC-0071 Area D / M3d).
- Restructure `design-review` (`experience-reviewer`) into cold-read, task-completion, and contract-review passes (RFC-0071 Area D).
- Use blocker, concern, and suggestion severity tiers, and require rendered evidence when a rendered surface exists (RFC-0071 Area D).
- Deliver M3d after M3c in the accepted implementation sequence (RFC-0071 § Implementation sequence).

## Source

- Mode: repo-origin
- Locator: docs/rfc/0071-digital-experience-doctrine.md
- Revision: a03b9d3f8df15a9b88cdabda5c10f21c662bfd0f

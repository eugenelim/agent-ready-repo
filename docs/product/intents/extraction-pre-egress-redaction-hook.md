# Extraction pre-egress redaction hook

- **Status:** Draft
- **Level:** feature
- **Authority:** [RFC-0058 D5 / Open-Q3](../../rfc/0058-capability-tiered-document-extraction.md)

## Outcome

Adopters with a concrete in-skill redaction need have a separately reviewed path to consider optional pre-egress redaction or PII scrubbing.

## Opportunity

RFC-0058 Decision 5 keeps pre-egress redaction out of Tier-3: documents are sent to the managed vendor unmodified, and adopters gate at their own classification layer, while optional in-skill redaction remains an open design question.

## What this absorbs

### extraction-tier3-pre-egress-redaction-hook

This is the `spec/extraction-higher-tiers` follow-on for RFC-0058 D5 / Open-Q3. If an adopter need surfaces, open a new slice with a fresh security review because an optional pre-egress redaction/PII-scrubbing hook changes the egress-boundary `security-reviewer` gates. Tier-3 continues to send documents to the managed vendor unmodified. Unblocks when a concrete adopter need for in-skill redaction surfaces.

## Assumptions

- A concrete adopter need and a fresh egress-boundary security review are required before this optional hook can be scoped.

## Source

- Mode: repo-origin
- Locator: workspace.toml
- Revision: 581dd8b7aefba04f566e4ea9a3213da8c6afb55d

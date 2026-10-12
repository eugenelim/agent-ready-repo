# Brief: Repair parent

- **Slug:** `repair-parent`
- **Received:** 2026-01-01
- **Owner:** placeholder-owner
- **Status:** Draft
- **Parent intent:** intent:good-slug
- **Parent intent:** bad-value-no-prefix

## Outcome

Brief with a mix of one accepted Parent intent: value (intent:good-slug) and one malformed value
(bare slug without kind: prefix). After the merge by slug, exactly one accepted value remains:
intent:good-slug resolves, and bad-value-no-prefix is a separate unparseable edge per AC-0064.

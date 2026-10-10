# Brief: Malformed parent

- **Slug:** `malformed-parent`
- **Received:** 2026-01-01
- **Owner:** placeholder-owner
- **Status:** Draft
- **Parent intent:** bare-slug-no-prefix

## Outcome

Brief with a malformed Parent intent: value (no kind: prefix, just a bare slug-like string).
The resolver's line rule requires kind:slug format; this is delivery-reference-malformed.
The navigator refuses it as unparseable per AC-0064.

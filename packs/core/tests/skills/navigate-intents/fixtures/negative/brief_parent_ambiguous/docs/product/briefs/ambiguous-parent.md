# Brief: Ambiguous parent

- **Slug:** `ambiguous-parent`
- **Received:** 2026-01-01
- **Owner:** placeholder-owner
- **Status:** Draft
- **Parent intent:** intent:ambig-a
- **Parent intent:** intent:ambig-b

## Outcome

Brief with two Parent intent: values naming different slugs (ambig-a and ambig-b).
After slug deduplication, two distinct slugs remain, so the resolver emits
delivery-relation-ambiguous for this field. The navigator returns multiple_values per AC-0064.

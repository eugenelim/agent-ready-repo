# Spec: synthetic lowercase acceptance heading

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->

Hand-authored fixture. `canonical_contract`'s `_AC_HEADING_RE` is deliberately
case-insensitive because `lint-spec-status.py` matches `Acceptance Criteria`
exactly, so its own AC extraction returns nothing for a spec spelled with a
lowercase `c`. Inheriting that bug would break normalization for exactly those
specs. No spec in the live tree spells it this way, so the case cannot be
captured — only authored.

## Objective

Pin the lowercase-heading normalization path.

## acceptance criteria

- [x] The checked box above this line is normalized (bookkeeping).
- [ ] The unchecked box is normalized too.

## Boundaries

### Never do

- [ ] This checkbox sits OUTSIDE the AC section and must NOT be normalized —
      it is a `Never do` item, which is the scope the pin exists to protect.

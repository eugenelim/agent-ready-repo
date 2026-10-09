# Backtick suffix normalization test

- **Slug:** `backtick-suffix`
- **Status:** Draft
- **Kind:** `outcome` (rung notation)
- **Owner:** placeholder-owner
- **Parent intent:** none

## Outcome

Intent with Kind: `outcome` (rung notation). AC-0004 says sentinels must be cut
before backticks are stripped, so the correct node id is outcome:backtick-suffix,
not intent:backtick-suffix (which the old bug produced).

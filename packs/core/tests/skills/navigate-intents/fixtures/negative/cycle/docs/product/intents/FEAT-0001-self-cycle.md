# Feature: Self cycle

- **Slug:** `self-cycle`
- **Status:** Draft
- **Level:** feature
- **Owner:** placeholder-owner
- **Parent intent:** intent:self-cycle

## Outcome

Intent whose Parent intent: points to itself. Results in a cycle refused edge (1-member cycle).
The refused edge leaves self-cycle (it is the only member and therefore the lowest-sorting slug).

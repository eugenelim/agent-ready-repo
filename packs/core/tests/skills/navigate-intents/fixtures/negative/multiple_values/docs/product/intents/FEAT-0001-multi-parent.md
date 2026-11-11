# Feature: Multi parent

- **Slug:** `multi-parent`
- **Status:** Draft
- **Level:** feature
- **Owner:** placeholder-owner
- **Parent intent:** capability:parent-a
- **Parent intent:** capability:parent-b

## Outcome

Intent with two distinct Parent intent: values in the preamble. Results in a multiple_values
refused edge (AC-0003). Both parent candidates have different slugs, so they cannot merge.

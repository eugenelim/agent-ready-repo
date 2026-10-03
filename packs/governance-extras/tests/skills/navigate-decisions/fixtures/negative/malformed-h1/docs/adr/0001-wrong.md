# ADR-0002: Wrong ordinal in H1

- **Status:** Accepted
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none

## Context

The H1 says "ADR-0002" but the basename is "0001-wrong.md" (ordinal 0001).
This mismatch makes the record malformed. The navigator must fail the whole
operation rather than silently dropping this file or assigning a wrong id.

## Decision

- **D1:** The H1 ordinal must match the basename ordinal exactly.

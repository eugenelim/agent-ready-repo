# ADR-0001: Alpha duplicate ordinal

- **Status:** Accepted
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none

## Context

This is the first of two files with basename ordinal 0001. Together with
0001-beta.md (which also parses as ADR-0001) it creates a duplicate
kind+ordinal identity, which must fail the whole operation.

## Decision

- **D1:** Ordinals must be unique within their kind (ADR or RFC).

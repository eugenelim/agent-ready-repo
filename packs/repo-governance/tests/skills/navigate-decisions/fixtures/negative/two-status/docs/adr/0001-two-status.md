# ADR-0001: Two status fields in header

- **Status:** Accepted
- **Status:** Draft
- **Supersedes:** none
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none

## Context

This record has two "**Status:**" fields in the header region.
The navigator must reject this as malformed and fail the whole operation.
The spec permits at most one Status field in the header region.

## Decision

- **D1:** At most one Status field is permitted in the header region.

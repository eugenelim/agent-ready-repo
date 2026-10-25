# ADR-0001: Missing supersession endpoint test

- **Status:** Accepted
- **Supersedes:** ADR-9999
- **Supersedes in part:** none
- **Superseded by:** none
- **Superseded in part:** none

## Context

This record claims "Supersedes: ADR-9999". ADR-9999 does not exist in
the corpus, so the endpoint is missing. The entry must remain as unresolved
evidence (relationship with resolution_state=unresolved) rather than forming
a checked edge or failing the whole operation. Missing endpoints are unresolved
evidence, not a parse failure.

## Decision

- **D1:** Supersession entries with missing endpoints are unresolved evidence.

---
title: "authn-session"
type: "Reference"
status: "Active"
license: "Apache-2.0 OR MIT"
compatibility: "repo-original"
boundaries:
  - filesystem_read_untrusted
---
# authn-session

Use when the change touches login, logout, password handling, MFA, session
creation or expiry, or token issuance and verification.

## Spec-stage

Require session lifecycle criteria: rotation, idle and absolute timeout,
invalidations, throttling, and MFA strength where the asset warrants it.

## Implementation checks

- `reason` Rotate sessions on login and privilege elevation.
- `reason` Verify JWT algorithms and keys from trusted configuration.
- `reason` Generate and store tokens with CSPRNG and hashing where applicable.
- `reason` Rate-limit sensitive authentication endpoints.
- `reason` Confirm logout and expiry invalidate server-side state.
- `hybrid` Treat hardcoded credentials as scanner-found but reviewer-judged.

## Established-helper bypass

Resolve the sanctioned auth/session library and flag hand-rolled password
hashing, token parsing, or session storage.

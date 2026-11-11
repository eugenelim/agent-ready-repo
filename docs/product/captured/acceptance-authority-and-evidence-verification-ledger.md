# Acceptance authority and evidence verification ledger

- **Status:** Closed
- **Resolution:** fixed
- **Kind:** defect
- **Detail:** docs/specs/acceptance-authority-and-evidence/notes/verification-ledger.md

## Summary

Clean the caller-supplied operation and correlation IDs at the effect broker (request_effect) so an odd value is never stored or escapes unaudited; pin the evidence-store task_projection_revision, authority identity, and nested-value schema checks with tests that fail when each is removed; and take any later in-class finding routed here by the security stop rule or the owner's 2026-10-07 review cap

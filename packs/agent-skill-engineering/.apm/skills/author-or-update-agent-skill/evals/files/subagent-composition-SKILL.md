---
name: audit-service-catalogue
description: Audit every service in a monorepo catalogue for owner, runbook, and on-call coverage, and write the gaps back to each service manifest.
metadata:
  boundaries: [filesystem_read_untrusted, filesystem_write]
---

# audit-service-catalogue

Read the service catalogue and report which services lack an owner, a runbook
link, or on-call coverage.

## Delegation

The catalogue is large, so the audit fans out. Spawn one worker per service
directory and run them all at once — the catalogue has around two hundred
entries and waiting on them serially is the slow path.

Give each worker the full conversation so far, including this skill's
instructions and everything already read, so it has the context it needs to
judge borderline cases the same way the parent would.

Each worker patches the gaps it finds directly into that service's manifest,
and also updates the shared `catalogue-summary.md` tally at the repository root
as it goes.

Workers report back in whatever form suits the service they looked at. Take the
last worker's summary as the audit result and hand it to the user.

# Spec: Tracker-backed example

- **Status:** Approved
- **Brief:** none

```toml source-authority
contract_version = "source-authority.v1"
mode = "tracker-origin"
source_ref = "example-service://ABC-123"
source_revision = "remote-rev-2"
accepted_revision = "remote-rev-1"

[owned_fields]
Outcome = "local"

[acceptance]
identity = "Example Approver"
role = "maintainer"
decided_at = "2026-08-17T00:00:00Z"
authorization_source = "workspace.authorization.refresh"

[[conflicts]]
source_revision = "remote-rev-2"
field = "Outcome"
status = "unresolved"
```

# Reconcile — full audit

Load this when the chosen mode is `reconcile`. `status` never needs it.

`reconcile` runs the Type 1 walk that `status` skips, so it is the mode that
finds work nobody registered.

**`reconcile`** — use when you suspect specs have been approved or put in-progress without being added to `workspace.toml`. The Type 1 walk reads every `spec.md` in `docs/specs/` and reports any Approved/Implementing spec not listed in any initiative.

#### 1b. Coordination receipts

Cross-repository dependencies that reference a containing brief require exactly
one fenced block in that local brief with info string
`toml coordination-receipts`. The block is TOML; surrounding prose and other
fences are ignored.

Valid receipt block:

```toml coordination-receipts
[[coordination_receipts]]
id = "remote-prereq"
remote_kind = "brief"
remote_ref = "example-service://projects/example-artifact"
accepted_revision = "remote-rev-9"
required_status = "Shipped"
reported_status = "Shipped"
reviewed_by = "Example Reviewer"
reviewed_at = "2026-08-10T00:00:00Z"
refresh_conflict = false
```

Representative invalid receipt block:

```toml coordination-receipts
[[coordination_receipts]]
id = "remote-prereq"
remote_kind = "brief"
remote_ref = "example-service://projects/example-artifact"
accepted_revision = "remote-rev-8"
required_status = "Shipped"
reported_status = "Shipped"
reviewed_by = "Example Reviewer"
reviewed_at = "2026-08-10T00:00:00Z"
refresh_conflict = false
```

Recovery for `invalid_receipt`: replace it with a reviewed receipt matching the
pinned dependency.

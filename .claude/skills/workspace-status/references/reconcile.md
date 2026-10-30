# Reconcile — full audit

Load this when the chosen mode is `reconcile`. `status` never needs it.

`reconcile` is the full audit of stale and premature entries. Its Type 1 audit
reports nothing for specs, because a spec needs no workspace entry.

**`reconcile`** — use when you suspect queue or active entries have gone stale, or shipped entries have drifted from their specs.

#### 1b. Coordination receipts

Cross-repository dependencies that reference a containing brief require exactly
one fenced block in that local brief with info string
`toml coordination-receipts`. The block is TOML; surrounding prose and other
fences are ignored.

The waiting item names the brief in its `Depends on:` header line, as
`brief:<slug>`. A `Dependency receipts:` line beside it holds a coordination
receipt, as `<reference> coordination <remote_kind> <receipt_id> <accepted_revision>`.
That receipt must match the block below. Registry `needs` stays `[]`.

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

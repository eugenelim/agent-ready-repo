---
title: workspace.toml schema reference
summary: Exact target entries, lifecycle collections, compatibility forms, and validation limits for the workspace index.
pack: core
kind: reference
---

`workspace.toml` is the repository coordination index. It points to canonical
artifacts, records lifecycle membership, stores minimal source provenance, and
names hard dependencies. It is not a requirements document.

Use this reference when you need to answer: “How should this artifact be
represented in `workspace.toml`, and is the entry safe to dispatch?” The result
is either a valid five-field target entry in one lifecycle collection or a
non-dispatchable compatibility or reconciliation finding.

## Contract at a Glance

Input: A repository-relative canonical artifact path, its artifact kind,
minimal source provenance, a display summary, and any hard dependencies.

Output: A target entry that validates against the published workspace-entry
schema, or a fail-closed finding that names the unsafe or legacy condition.

Reads: Consumers read `workspace.toml` and the referenced canonical artifacts
needed to confirm lifecycle, provenance, plans, dependencies, and confinement.

Writes: Writers update lifecycle membership only after they have created or
updated the canonical artifact. Requirements and acceptance decisions stay in
that artifact, never in the workspace index.

Human decision: A person chooses the canonical artifact route, approves
requirement-bearing artifacts, and decides how to migrate a legacy entry.

Repositories that enable tracker refresh also carry a global
`[authorization.refresh]` role policy outside initiative entries. See
[Refresh tracked work safely](../../_shared/how-to/use-work-intake.md) for
the exact required keys and confirmation boundaries. The policy contains roles
only; artifact authority, approver identities, decisions, conflicts, and
receipts remain in the canonical artifact.

Comments, `summary`, list order, tracker object type, and profile hints are
display context only. They must not decide routing, reconciliation, dependency
satisfaction, dispatch, or which processor runs.

Section headers use TOML quoted dotted keys when an initiative id contains a
hyphen:

```toml
["ini-001"]
name = "Workspace routing"
status = "active"
milestone = "M1"
```

## Target Entry

Every target-state lifecycle entry is an inline table with exactly five
semantic fields:

```toml
{ path = "docs/specs/self-service-reset/spec.md", kind = "spec", source = { mode = "repo-origin" }, summary = "Let a user reset access without support", needs = [] }
```

| Field | Type | Meaning |
| --- | --- | --- |
| `path` | string | Repository-relative canonical artifact path. |
| `kind` | string | `intent`, `research`, `design`, `brief`, `spec`, or `defect`. |
| `source` | table | Minimal provenance used for display and reconciliation. |
| `summary` | string | Non-empty display text. Non-semantic. |
| `needs` | array | Typed hard dependencies. Empty when unblocked by other artifacts. |

Unknown fields fail the target contract. Requirements, acceptance criteria,
field ownership maps, source-decision history, credentials, and raw source
payloads do not belong in `workspace.toml`.

### Limits

| Value | Limit |
| --- | ---: |
| `path` and dependency paths | 1–1,000 characters |
| `summary` | 1–500 characters |
| `needs` | 0–50 records |
| `source.ref` | 1–1,000 characters when present |
| `source.revision` | 1–200 characters when present |
| `source.coordination` | 1–300 characters when present |
| Tracker profile `id` | 1–200 characters |
| Tracker profile `version` | 1–100 characters |

## Paths

`path` and local dependency paths are repository-relative POSIX-style paths.
They must not be empty, absolute, contain backslashes, or contain a `..`
segment.

The lexical check is not enough before reading or dispatching. Consumers must
resolve the repository root and target path after symlinks, then verify the
resolved target remains under the resolved root. A symlink that points outside
the repository fails closed even if its text path looks valid.

## Source

`source.mode` is required and is either `repo-origin` or `tracker-origin`.

```toml
source = { mode = "repo-origin", parent = "docs/product/briefs/account-recovery.md" }
```

```toml
source = { mode = "tracker-origin", ref = "example-service://tickets/WORK-123", revision = "tracker-rev-42", tracker_profile = { id = "example-service/default", version = "2026-08" } }
```

Tracker-origin entries require both `ref` and `revision`. Optional fields are:

| Field | Meaning |
| --- | --- |
| `parent` | Local parent artifact such as a brief or intent. |
| `coordination` | Cross-repository coordination reference. |
| `tracker_profile` | Optional profile hint with `id` and `version`. |

`ref` is durable provenance, not a credential carrier. Userinfo (`@`), query
strings, and fragments fail the contract; store a sanitized opaque source
identifier instead.

Tracker profile and object vocabulary are hints. They cannot determine
artifact kind, lifecycle membership, or processor.

## Dependencies

`needs` is an array of typed hard dependencies. A local dependency names the
required artifact kind and canonical local path:

```toml
needs = [
  { type = "local", kind = "design", path = "docs/product/design/workspace-routing.md" },
]
```

A cross-repository dependency is satisfied only by a reviewed local receipt in
the containing brief. The dependency pins the local brief path, receipt id, and
accepted revision:

```toml
needs = [
  { type = "cross-repo", kind = "brief", path = "docs/product/briefs/account-recovery.md", containing_brief = "docs/product/briefs/account-recovery.md", receipt_id = "remote-prereq", accepted_revision = "remote-rev-9" },
]
```

When a cross-repository dependency names a containing brief, that local brief
must contain exactly one fenced block whose info string is exactly
`toml coordination-receipts`. The block is parsed as TOML; surrounding prose and
other fenced blocks are inert.

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

The invalid example fails because its `accepted_revision` does not match the
dependency's pinned revision. Recovery: replace it with a reviewed receipt
matching the pinned dependency; the finding code is `invalid_receipt`.

Priority, affinity, rationale, and suggested order are not dependencies.

## Lifecycle Membership

Membership is lifecycle state. A target entry appears in exactly one lifecycle
collection.

| Collection | Valid artifacts | Meaning |
| --- | --- | --- |
| `[backlog].open` | Draft artifacts and open defect contexts | Visible, not dispatchable. |
| `[backlog].closed` | Retained captures and closed defect contexts | Closed defect resolution is `fixed`, `declined`, or `superseded`. |
| `["ini-NNN".shaping_queue].backlog` | `intent`, `research`, `design` | Waiting for shaping, research, or design processing. |
| `["ini-NNN".shaping_queue].active` | `intent`, `research`, `design` | Currently being processed outside implementation work. |
| `["ini-NNN".brief_queue].draft` | `brief` | Draft brief. |
| `["ini-NNN".brief_queue].ready` | `brief` | Passed the Ready gate and has no Implementing child. May have zero child specs. |
| `["ini-NNN".brief_queue].executing` | `brief` | Has at least one Implementing child spec. |
| `["ini-NNN".brief_queue].shipped` | `brief` | Explicitly closed; materialized children are Shipped. |
| `["ini-NNN".work].queue` | `spec` | Approved spec with an existing sibling plan, waiting to be claimed. |
| `["ini-NNN".work].active` | `spec` | Implementing spec claimed by the build loop. |
| `["ini-NNN".work].shipped` | `spec` | Shipped spec retained for dependency and history. |

An initiative table is active only when `status = "active"`. Paused and closed
initiatives are visible but non-dispatchable.

```toml
[backlog]
open = [
  { path = "docs/product/intents/workspace-routing.md", kind = "intent", source = { mode = "repo-origin" }, summary = "Define deterministic workspace routing", needs = [] },
]
closed = []

["ini-001"]
name = "Workspace routing"
status = "active"
milestone = "M1"

["ini-001".brief_queue]
draft = []
ready = [
  { path = "docs/product/briefs/account-recovery.md", kind = "brief", source = { mode = "tracker-origin", ref = "example-service://projects/PROJ-123", revision = "tracker-rev-42" }, summary = "Make account recovery self-service", needs = [] },
]
executing = []
shipped = []

["ini-001".work]
queue = [
  { path = "docs/specs/self-service-reset/spec.md", kind = "spec", source = { mode = "tracker-origin", ref = "example-service://projects/PROJ-123", revision = "tracker-rev-42", parent = "docs/product/briefs/account-recovery.md" }, summary = "Let a user reset access without support", needs = [] },
]
active = []
shipped = []

["ini-001".shaping_queue]
backlog = []
active = []
```

## Ready Briefs

A Ready brief with zero child specs is valid and useful planning state. It is
visible in `workspace-status`, but it is not dispatchable. Implementation begins
only when a selected slice has a spec, its sibling plan, Approved status, and a
target entry in `work.queue`.

## Canonical Findings

Every refusal is visible as a stable code with a safe next action.

| Code | Why blocked | Safe action |
| --- | --- | --- |
| `invalid_workspace` | TOML parse failure or invalid lifecycle collection shape. | Correct workspace.toml, then rerun reconciliation. |
| `invalid_entry` | Malformed target record, unknown field or kind, or failed schema conditional. | Rewrite the entry to the accepted target contract. |
| `legacy_entry` | Supported compatibility form; visible but never dispatchable. | Materialize and register a canonical target entry. |
| `unsupported_legacy` | Legacy-like form outside accepted compatibility fixtures. | Route the item manually; do not infer a target entry. |
| `invalid_artifact_path` | Unsafe, noncanonical, or out-of-repository artifact-like path. | Replace it with a confined canonical repository-relative path. |
| `missing_artifact` | Registered canonical artifact does not exist. | Create and review the canonical artifact before dispatch. |
| `unreadable_artifact` | A confined artifact cannot be read safely. | Restore readable repository state, then rerun reconciliation. |
| `missing_plan` | A spec has no sibling `plan.md`. | Create and approve the plan before dispatch. |
| `unapproved_spec` | Queue spec is not `Approved`. | Complete the spec approval gate. |
| `unregistered_work` | Supplied or active spec has no unique matching workspace membership. | Register or reconcile the canonical entry explicitly. |
| `duplicate_membership` | One artifact occurs more than once across lifecycle memberships. | Remove the duplicate after choosing the authoritative membership. |
| `impossible_transition` | Artifact status and lifecycle membership cannot coexist. | Correct the artifact or membership through a reviewed transition. |
| `provenance_mismatch` | Workspace source metadata disagrees with canonical artifact metadata. | Resolve provenance in the canonical artifact and mirror it deliberately. |
| `refresh_conflict` | Tracker-origin refresh conflict remains unresolved. | Resolve the conflict through the artifact's authority workflow. |
| `invalid_source_authority` | Tracker-origin source authority is missing, duplicated, malformed, or violates its closed contract. | Correct the closed source-authority block, then rerun reconciliation. |
| `unsatisfied_dependency` | A known dependency lacks its kind-specific terminal state. | Complete or explicitly revise the dependency. |
| `missing_dependency` | A dependency target cannot be resolved locally. | Materialize or correct the dependency target. |
| `dependency_cycle` | The hard-dependency graph contains a cycle. | Break the cycle through an explicit plan change. |
| `invalid_receipt` | Cross-repository receipt is incomplete, mismatched, or conflicted. | Replace it with a reviewed receipt matching the pinned dependency. |
| `inactive_initiative` | Work belongs to a paused or closed initiative. | Reactivate the initiative explicitly or move the work through governance. |
| `configuration_mismatch` | Versioned schema, adapter/profile, or routing identity is missing or inconsistent. | Install or select a consistent versioned configuration, then rerun. |

## Minimal Intent

The shared intent artifact contains:

- `Status`
- `Level`
- `Outcome`
- `Opportunity`
- `Assumptions`
- `Source`

The default path is `docs/product/intents/<slug>.md`. A repository may relocate
the parent through its configured core layout, but the resolved output must stay
inside the repository so it can be indexed by `workspace.toml`.

## Defects

A defect context captures already-intended behavior that is not currently true.
It requires expected behavior, observed behavior, reproduction evidence or an
error signature, source provenance, and a durable citation establishing the
intended behavior. Closed defect contexts record exactly one resolution:
`fixed`, `declined`, or `superseded`.

Defects stay in the repository-level backlog. They are routed to the bug-fix
workflow, not directly to implementation queue dispatch.

## Legacy Compatibility

During the compatibility window, readers may recognize these legacy shapes:

| Collection | Legacy shape |
| --- | --- |
| Work arrays | Bare `spec/<slug>` strings only. |
| Shaping arrays | Bare shaping slugs, or `{ slug, type, needs }` objects where `type` is `shape`, `research`, `strategy`, `signal`, or `design`. |
| Brief queue arrays | Brief path strings such as `docs/product/briefs/<slug>.md`. |
| `[backlog].open` | Comment-rich inline objects with `slug` plus legacy fields such as `needs`, `source`, `summary`, or `type`. |

The same shape in the wrong collection is invalid. A legacy entry is tagged as
legacy, visible, and non-dispatchable. A missing artifact or plan stays
non-dispatchable, and readers do not reconstruct requirements from comments.
Migration requires a human to choose the canonical artifact route and write a
target entry.

## Compaction

Shipped entries may be removed from the active index only when no live `needs`
edge references them, no open parent references them, and closure evidence is
durable in the canonical artifacts. Compaction removes only the index entry. It
never deletes the canonical artifact or its Git history.

## Encoding

Examples use TOML strings as raw UTF-8. Do not encode Unicode scalar values as
JSON surrogate escapes in TOML examples. JSON fixture loading rejects
non-standard `NaN` and infinity constants, and JSON emission must refuse
non-finite values.

## See Also

- [The two-room model](../explanation/two-room-model.md)
- [How to orient at the start of a session](../how-to/orient-at-session-start.md)

---
title: Start, remember, inspect, or refresh repository work
summary: Use one content-based front door for new work, deferred work, workspace status, and reviewed tracker refresh.
pack: core
kind: how-to
---

# Start, remember, inspect, or refresh repository work

Use work intake when you know what you want to accomplish but should not have
to choose an internal skill or workspace collection first. Start with ordinary
language:

```text
Start work on export-retention controls. Keep the existing API route compatible.
```

The agent validates the request, selects one artifact from its content, writes
that artifact before registering it, and names the next processor. Ambiguous
or incoherent input remains non-dispatchable until you answer the smallest
missing question.

## Start work

Describe the outcome, constraints, evidence, and any source reference you
already have. Intake distinguishes these common shapes:

| What the content supports | Result |
| --- | --- |
| A minimal opportunity | Draft intent; stop for shaping |
| One independently shippable behavior | Spec route through `new-spec` |
| One coherent outcome needing several specs | Draft brief through `author-brief` |
| A cross-repository outcome | One linked local brief per repository |
| Unrelated items or an incoherent view | Separate units, view-only, or one clarification |
| A regression with durable expected-behavior evidence | Defect context through `bug-fix` |

Tracker object type, list size, comments, labels, and hierarchy do not select
the route. A claimed defect without durable expected-behavior evidence remains
unresolved or follows the spec path.

Core-only intake uses no network. A tracker adapter acquires a bounded source
record through its exact configured profile, treats its content as untrusted,
and passes the same normalized fields to the core route.

## Remember work for later

Say:

```text
Remember that export retries need idempotent replay. Do not implement it now.
```

The agent creates the smallest safe Draft artifact, registers a
non-dispatchable entry, and stops. Use `work-intake` in new prompts.
`capture-work` remains a forwarding compatibility alias and produces the same
result plus a deprecation notice.

## Inspect or triage the workspace

Say:

```text
Show workspace status and triage anything that is not safe to dispatch.
```

Work intake delegates to `workspace-status` and returns its lifecycle,
findings, and next actions unchanged. This path is read-only. It does not
classify a new artifact or repair a finding automatically.

Canonical entries, accepted legacy forms, duplicates, missing artifacts or
plans, authority problems, and refresh conflicts remain visible. When status
reports `legacy_entry`, follow [Migrate a legacy workspace entry safely](../../core/how-to/migrate-capture-work.md);
migration is a separate workspace-status repair surface, not ordinary intake.

## Refresh tracked requirements

Use refresh only when a canonical repository artifact already exists and is
registered as tracker-origin. Ask for the comparison before any write:

```text
Refresh docs/specs/export-retention/spec.md from its registered tracker source.
Show every changed field and do not write back yet.
```

The artifact must carry one valid source-authority record and an exact profile
version with a configured processor. The repository must also declare its
closed role policy:

```toml
[authorization.refresh]
contract_version = "refresh-authorization-policy.v1"
draft_approver_roles = ["maintainer"]
accepted_approver_roles = ["maintainer"]
remote_mutation_approver_roles = ["maintainer"]
```

Replace the example role with repository-authorized roles. The policy stores
roles, not identities or tracker-supplied evidence; missing, unknown, or empty
role sets fail closed.

The canonical artifact carries provenance and ownership in one closed fence:

```toml source-authority
contract_version = "source-authority.v1"
mode = "tracker-origin"
source_ref = "tracker://item/EX-123"
source_revision = "rev-7"

[owned_fields]
```

Before the first refresh, assign every profile-mapped field in `owned_fields`
to `source` or `local`. An empty or incomplete ownership map refuses rather
than guessing. The ordinary prose source section is not a substitute for this
record.

Tracker text can supply candidate field values. It cannot choose the profile,
destination, lifecycle, decisions, confirmation, or write payload.

### Review the field delta

For a Draft artifact, approved source-owned fields may change while local-owned
fields remain locked. Accepted intents, Ready briefs, and Approved specs need
an authorized `keep-local`, `accept-source`, or `revise-both` decision for each
changed local field.

Implementing specs and Executing briefs refuse requirement refresh. Shipped
requirements are locked. Failed acquisition or comparison advances no source
revision.

After review, state the local decisions explicitly:

```text
Keep the local Outcome, accept the source Constraint, and record Scope as
revise-both.
```

The artifact authority record and the small workspace revision mirror advance
through one fingerprint-guarded write. A stale fingerprint, invalid authority,
missing processor, or profile mismatch leaves both at their prior values.

### Confirm coordination write-back separately

A local field decision never authorizes a tracker mutation. Request one
coordination action and inspect its exact target and payload:

```text
Add the reviewed pull-request link to the linked tracker item. Show the exact
target and payload, then wait for confirmation.
```

Each supported comment, trace link, pull-request link, display-status change,
or closure uses its own fresh confirmation. A pending local receipt is written
before the remote call. Failures are not retried automatically.

| Profile | Reviewed local refresh | Confirmed coordination actions |
| --- | --- | --- |
| Jira token | Yes | Display status, comment, closure |
| Jira SSO cookie | Yes, read acquisition only | None; non-GET/HEAD is refused |
| Jira Align | Yes | None |
| Linear | Yes | Trace link, pull-request link, display status, comment, closure |
| GitHub | Yes | Trace link, pull-request link, display-status label, comment, closure |

## Verify and continue

Run `workspace-status`. Confirm the artifact path, lifecycle membership,
processor, authority mode, compared and accepted revisions, conflict state,
and next action.

Then continue with the named processor, resolve the one reported gap, or stop
with the Draft recorded for later. Use [Work-intake routing and lifecycle](../reference/work-intake-routing-and-lifecycle.md)
for exact routes and [Tracker vocabulary](../reference/tracker-vocabulary.md)
for profile terminology.

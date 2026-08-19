---
title: Refresh tracked work safely
summary: Compare a registered tracker-origin artifact with its source, review each field, and confirm any coordination write-back separately.
pack: core
kind: how-to
---

# Refresh tracked work safely

Use refresh when a canonical repository artifact already exists and its Jira,
Jira Align, Linear, or GitHub source has changed. Start with a request such as:

```text
Refresh docs/specs/export-retention/spec.md from its registered tracker source.
Show me every changed field and do not write back yet.
```

You receive a field-level comparison. The tracker remains unchanged, and no
local requirement changes until an authorized approver chooses what to keep,
accept, or revise.

## Before you start

The artifact must be registered in `workspace.toml`, use `tracker-origin`
authority, and contain one valid `source-authority` record. Its exact profile
version must have a configured refresh processor. The repository-owned
`workspace.toml` must also declare the closed refresh authorization policy:

```toml source-authority
[authorization.refresh]
contract_version = "refresh-authorization-policy.v1"
draft_approver_roles = ["maintainer"]
accepted_approver_roles = ["maintainer"]
remote_mutation_approver_roles = ["maintainer"]
```

Replace the example role with the repository's actual authorized roles. Each
array must contain one or more unique, non-empty role names: Draft decisions
use `draft_approver_roles`, Accepted/Ready/Approved decisions use
`accepted_approver_roles`, and every separately confirmed tracker mutation uses
`remote_mutation_approver_roles`. Unknown or missing policy keys fail closed;
the table stores roles only, never identities or tracker-supplied evidence.

`workspace-status` shows the origin mode, profile, compared and accepted
revisions, conflict state, and known availability without copying the authority
record into workspace state.

Tracker content is untrusted. It can supply candidate field values, but it
cannot choose the processor, lifecycle, destination, command, approval, or
write payload.

A tracker-origin artifact carries its provenance in one closed authority fence;
the ordinary prose source section is not a substitute:

```toml
contract_version = "source-authority.v1"
mode = "tracker-origin"
source_ref = "tracker://item/EX-123"
source_revision = "rev-7"

[owned_fields]
```

## Review the comparison

Ask for the delta without a write:

```text
Compare the latest source revision with the accepted artifact. Keep local
fields unchanged and show the decision needed for each difference.
```

For a Draft artifact, refresh can update approved source-owned fields; local
fields remain unchanged. For an Accepted intent, Ready brief, or Approved
spec, each changed local requirement needs an authorized `keep-local`,
`accept-source`, or `revise-both` decision. The decision records the approver,
role, time, and authorization source.

An Implementing spec or Executing brief refuses requirement refresh. Shipped
requirements are also locked. A failed acquisition or comparison advances no
revision.

## Apply the reviewed local update

After reviewing the complete delta, state the decisions explicitly:

```text
Keep the local Outcome, accept the source Constraint, and record the Scope
difference as revise-both.
```

The artifact authority record and the small `workspace.toml` revision mirror
advance through one guarded local operation. A stale fingerprint, missing
processor, profile-version mismatch, unresolved ambiguity, or write failure
leaves both files at their pre-refresh values.

## Confirm coordination write-back separately

A local refresh decision never authorizes a tracker mutation. Ask for one
coordination action, inspect its exact target and payload, then confirm it:

```text
Add the reviewed pull-request link to the linked tracker item. Show the exact
target and payload, then wait for my confirmation.
```

Each comment, trace link, pull-request link, display-status change, or closure
uses its own fresh confirmation. The confirmation is bound to the approver,
artifact, source revision, profile, destination, action, target, and payload
digest. A pending local receipt is recorded before the command or request. A
failed mutation is not retried automatically; retrying requires a new
confirmation.

## Know the active profile limits

| Profile | Reviewed local refresh | Coordination write-back |
| --- | --- | --- |
| Linear | Yes | Trace link, pull-request link, display status, comment, closure |
| GitHub | Yes | Trace link, pull-request link, display-status label, comment, closure |
| Jira with token credentials | Yes | Display status, comment, closure |
| Jira with SSO cookies | Yes, read acquisition only | Refused before any non-GET/HEAD request |
| Jira Align | Yes | None; unsupported actions fail before payload or transport |

Capabilities come from the exact versioned profile. Missing actions do not
fall back to a raw API or generic update command.

## Next request

Run `workspace-status` to confirm the compared revision and any unresolved
conflict. If one remote action failed, inspect its receipt and request a new
confirmation for that action only.

## See also

- [Choose a tracker integration](choose-a-tracker-integration.md)
- [Tracker vocabulary](../reference/tracker-vocabulary.md)
- [Work-intake routing and lifecycle](../../core/reference/work-intake-routing-and-lifecycle.md)

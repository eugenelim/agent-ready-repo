---
title: Work-intake routing and lifecycle reference
summary: Look up intake routes, authority modes, dispatch rules, refresh results, and migration boundaries across supported profiles.
pack: _shared
kind: reference
---

# Work-intake routing and lifecycle reference

Use this reference after asking, “Intake this request as repository work.” It
defines the fields the route returns and the conditions that make a result
dispatchable. The rules are the same for repo-origin input and for the Jira,
Jira Align, Linear, and GitHub profiles.

## Intent index

| You want to | Result |
| --- | --- |
| Start or do work | One content-based artifact route and processor |
| Remember work | A Draft artifact and non-dispatchable membership |
| Inspect or triage status | The `workspace-status` result, unchanged and read-only |
| Refresh tracked requirements | A profile-bound comparison governed by lifecycle and source authority |
| Plan a legacy-entry migration | A read-only migration result for a reviewed selection |

## Normalized route record

Every routing evaluation projects the actual adapter, validator, router,
refresh, and migration-planner outputs into these evaluation-only fields:

| Field | Meaning |
| --- | --- |
| `case_id` | Stable fixture case |
| `profile_id`, `profile_version` | Exact source profile, or `core` for repo-local cases |
| `artifact_kind`, `artifact_path` | Selected canonical artifact |
| `lifecycle_membership` | Target workspace collection or read-only passthrough |
| `processor` | Owning next processor, or `none` |
| `authority_mode` | `repo-origin`, `tracker-origin`, or `read-only` |
| `dispatchable` | Whether the named processor may continue now |
| `result_code` | Stable route, refresh, or migration outcome |
| `next_action` | One safe follow-up |

This projection is test support, not a published runtime schema. Runtime
`Route`, refresh-result, and migration-result contracts remain independently
owned.

## Start routes

| Content and evidence | Artifact | Initial membership | Processor | Dispatchable |
| --- | --- | --- | --- | --- |
| Minimal opportunity | intent | shaping backlog or repository backlog | `none` | No |
| One independently shippable behavior | spec | `work.queue` only after approval and sibling plan | `new-spec` | Yes after gates |
| One coherent outcome needing several specs | brief | `brief_queue.draft` | `author-brief` | Yes for drafting; not for implementation |
| Cross-repository outcome | one linked local brief per repository | `brief_queue.draft` | `author-brief` | Yes for each local slice |
| Unrelated collection or incoherent view | separate units, view-only result, or Draft with named gaps | none or non-dispatchable Draft | `none` | No |
| Regression with durable expected-behavior evidence | defect context | `backlog.open` | `bug-fix` | Yes after context exists |
| Claimed defect without that evidence | Draft with a named evidence gap | non-dispatchable | `none` | No |

A title, item count, tracker object type, hierarchy position, label, workspace
comment, or previous collection cannot override these routes.

## Remember and status

Remember materializes the smallest safe Draft artifact, registers it after the
artifact exists, and stops. `capture-work` is only a compatibility alias for
this behavior.

Status delegates to `workspace-status`. It performs no intake classification
and no mutation. Canonical, legacy, duplicate, invalid, and refresh findings
remain visible with their stable next actions.

## Authority modes

Repo-origin: the repository artifact owns requirements. A tracker projection
cannot import requirement changes into it.

Tracker-origin: the artifact's closed source-authority record divides mapped
fields into source-owned and local-owned values. The exact configured profile
acquires and compares the source revision.

Read-only: status, triage, and planning may return findings or proposed
operations but cannot write.

## Refresh lifecycle

| Lifecycle | Requirement result | Next action |
| --- | --- | --- |
| Draft | `ready`; approved source-owned changes may be reviewed | Review the field delta |
| Accepted, Ready, Approved | `ready`; each changed local field needs an authorized decision | Keep local, accept source, or revise both |
| Implementing | `implementing_requirements_locked` | Preserve local requirements |
| Executing | `executing_requirements_locked` | Preserve local requirements |
| Shipped | `shipped_requirements_locked` | Keep requirements locked; request coordination separately if supported |

Local refresh and remote coordination are separate effects. Every remote
comment, trace link, pull-request link, display-status change, or closure needs
one fresh confirmation bound to the exact target and payload. Unsupported
actions never fall back to generic tracker access.

## Migration boundary

`repair-plan --migration-selection <path>` is read-only and refuses
`--plan-file`. It returns `planned`, `artifact_missing`, a manual-routing
result, or a redacted refusal. The evaluation route is non-dispatchable and
its next action is to review the migration plan.

`repair-apply` and `repair-rollback` are workspace-status repair effects, not
tracker routes. They require the repository's `[authorization.migration]`
policy plus one fresh, single-use, current-session confirmation for the exact
operation. See [Migrate a legacy workspace entry](../../core/how-to/migrate-capture-work.md).

## Read and write limits

Core-only routing uses no network. Tracker adapters enforce their declared
page, item, byte, timeout, retry, backoff, destination, and capability limits.
Artifact and workspace paths must remain repository-confined. Registration
occurs only after artifact creation; processor dispatch occurs only after both
are durable and reconciled.

## See also

- [Use work intake](../how-to/use-work-intake.md)
- [Tracker vocabulary](tracker-vocabulary.md)
- [How work records divide responsibility](../explanation/work-artifact-responsibilities.md)
- [workspace.toml schema reference](../../core/reference/workspace-toml-schema.md)

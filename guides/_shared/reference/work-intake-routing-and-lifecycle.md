---
title: Work-intake routing and lifecycle reference
summary: Look up intake routes, authority modes, dispatch rules, refresh results, and what remains of the old registry across supported profiles.
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
| Inspect or triage status | The `work-loop` `dispatch.py` listing, or `navigate-intents` `outstanding` for work under an intent; both read-only |
| Refresh tracked requirements | A profile-bound comparison governed by lifecycle and source authority |

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
| Minimal opportunity | intent | none | `none` | No |
| One independently shippable behavior | spec | none (ready once approved with a sibling plan) | `new-spec` | Yes after gates |
| One coherent outcome needing several specs | brief | none (its `Status: Draft`) | `author-delivery-brief create` | Yes for drafting; not for implementation |
| Cross-repository outcome | one linked local brief per repository | none | `author-delivery-brief create` | Yes for each local slice |
| Unrelated collection or incoherent view | separate units, view-only result, or Draft with named gaps | none or non-dispatchable Draft | `none` | No |
| Regression with durable expected-behavior evidence | captured-item file under `docs/product/captured/` | none | `bug-fix` | Yes after context exists |
| Claimed defect without that evidence | Draft with a named evidence gap | non-dispatchable | `none` | No |

A title, item count, tracker object type, hierarchy position, label, workspace
comment, or previous collection cannot override these routes.

## Remember and status

Remember materializes the smallest safe Draft artifact and stops. A repo-origin
intent or brief is its file alone and gets no registry entry. A spec is its file alone too; a tracker-origin brief or spec carries its tracker profile in its own record. A
remembered defect, design, or research item is written as its own file under
`docs/product/captured/` and gets no registry entry. Closing it is an edit to
that file alone.

Status delegates to `work-loop`'s `dispatch.py` (what is ready, active, or
blocked; add `--captured` for captured items) and to `navigate-intents`
`outstanding` (work placed under an intent). Neither performs intake
classification or mutation, and findings remain visible with their stable next
actions.

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

Refresh reads its approver roles from the `[authorization.refresh]` table of
`.work-intake.toml` at the repository root, and binds that file's digest when
it writes locally. A repository whose table is still in `workspace.toml` gets
`invalid_refresh_policy` until the `refresh-policy-move` repair moves it.

## Leftover registry entries

A repository that still has `workspace.toml` entries from an older version keeps
the file. `workspace-status` only plans and applies the repair that drops
them; nothing else reads those entries as lifecycle. Dispatch refuses an entry
written in the legacy form with `unmigrated_workspace` until you edit it by
hand. See [Upgrade from a workspace.toml registry](../../core/how-to/upgrade-from-a-workspace-registry.md).

## Read and write limits

Core-only routing uses no network. Tracker adapters enforce their declared
page, item, byte, timeout, retry, backoff, destination, and capability limits.
Artifact paths must remain repository-confined. A route is one artifact write
and nothing registers; processor dispatch occurs only after that file is
durable. A defect start or a remembered defect, design, or research item
writes only its captured-item file.

## See also

- [Use work intake](../how-to/use-work-intake.md)
- [Tracker vocabulary](tracker-vocabulary.md)
- [How work records divide responsibility](../explanation/work-artifact-responsibilities.md)
- [Upgrade from a workspace.toml registry](../../core/how-to/upgrade-from-a-workspace-registry.md) (repair leftover entries)

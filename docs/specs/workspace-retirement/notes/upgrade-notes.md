---
title: Upgrade from a workspace.toml registry
summary: Move what your workspace.toml registry records onto your intents, briefs, specs and captured items with one repair run, and learn what no longer works after core 4.0.10.
pack: core
kind: how-to
---

# Upgrade from a workspace.toml registry

You can move what your `workspace.toml` registry records about your work onto the work items themselves. After that, `work-loop` decides what is ready from each item's own headers, and the registry is no longer a place you edit. This needs the `core` pack at 4.0.10 or later: install it with `agentbundle install --pack core`, or upgrade an installed one with `agentbundle upgrade --pack core`.

This is the publication draft for the brief's slice 9. It replaces the earlier draft at `docs/specs/pre-cutover-closure/notes/upgrade-notes.md`, whose hash that spec's ledger binds. Publishing it is the owner's step and has not happened.

## What you will see

While `workspace.toml` still holds an entry, `work-loop`'s dispatch refuses. It prints the decision `refuse`, empty `ready`, `active` and `blocked` lists, and one finding with the code `unmigrated_workspace` and the path `workspace.toml`. The finding's next action reads: run `workspace-status` `repair-plan`, then `repair-apply`, to move the remaining entries onto their artifacts, and rewrite or remove by hand any entry the repair leaves. The refusal writes nothing, whatever the items' headers say.

## Plan the repair

Ask your agent, in a session in the repository, to plan the repair:

```text
Run the workspace-status repair-plan and show me the plan.
```

The agent runs `workspace-status`'s `repair-plan`. It writes `.workspace-repair-plan.json` and lists each automatic operation and each manual item. Nothing else changes. `repair-plan` needs only the Python standard library.

## Apply the plan

Read the plan, then ask your agent to apply that exact plan:

```text
Apply the workspace repair plan.
```

The agent runs `repair-apply --yes`, the only writer. It needs `tomlkit`: if that is missing, `repair-apply` exits 2 with the reason `tomlkit_unavailable`, and the agent asks before installing it. A manual item keeps its entry and names the reason. Fix it by hand and plan again.

The plan holds these operations. Each is applied only when the plan lists it for your repository:

| Operation | What it does |
| --- | --- |
| `needs-to-header` | Moves a legacy `needs` string onto the waiting item's `Depends on:` header. |
| `needs-drop-cooled` | Drops the `needs` of a cooled entry, which contributes no edge. |
| `captured-to-file` | Writes a captured item into its own file with a `Status:` line. |
| `captured-entry-drop` | Drops a captured-item membership or slug-only legacy entry whose captured-item file it can read. |
| `intent-brief-drop` | Removes the entry for a repo-origin intent or brief. |
| `spec-entry-drop` | Removes the entry for a repo-origin spec. |
| `tracker-entry-drop` | Moves a tracker-origin entry's profile into the artifact's own `source-authority` record. |
| `refresh-policy-move` | Moves an `[authorization.refresh]` table into `.work-intake.toml`. |
| `queue-to-shipped`, `queue-remove` | Retire a queue entry: `queue-to-shipped` when its spec is Shipped, `queue-remove` otherwise. |

## What is not carried over

The repair moves only what a tracked file records. These behaviors are not carried over, and nothing replaces them:

- `<initiative>`, `<initiative>.name`, `<initiative>.status`, `<initiative>.milestone` and `<initiative>.parent`: an initiative is no longer a work item, so nothing moves its name, status, milestone or parent onto an item.
- `entry position`: the order of a registry list means nothing. A start with no named spec lists the ready specs and asks. Record a priority with the optional `Priority:` header.
- `behavior outside tracked files`: anything that lived only outside tracked files is not moved.
- the per-entry refresh status `origin_mode`, `profile` and `refresh` for tracker work: refresh itself reports whether it can run.
- `the MCP canonical reconciliation object`: the `workspace_status()` tool's `canonical` field is now the output of the packaged `dispatch.py`.

The decisions behind these removals are the entries in the [RFC-0106 errata](../../../rfc/0106-stop-registering-derivable-work.md#errata) dated 2026-10-25, 2026-10-26, 2026-10-27, 2026-10-29, 2026-10-30, 2026-10-31 and 2026-11-02. The [retirement record](../retirement-record.md#disposition) lists each one.

## What stops working

After `core` 4.0.10 these no longer exist:

- `workspace-status` keeps only `repair-plan` and `repair-apply`. Its `status`, `reconcile`, `explain`, `selected-membership`, `prune`, `retirement-candidates` and `repair-rollback` subcommands are retired. Ask `work-loop`'s dispatch what is ready, and `navigate-intents` what work exists.
- The migration tooling and the `[authorization.migration]` table it read are removed. An operation left unfinished in `.workspace-migrations.json` can no longer be rolled back after the upgrade. Finish or abandon it before you upgrade; this note is the only warning.
- The `next_queue` and `next_shape` suggestions are removed.
- The MCP `workspace_status()` tool returns items with no `ini_slug`, an empty `shaping`, and a two-part dispatched item `type:slug` whose branch is `<type>/<slug>`. A legacy `ini_slug/type:slug` value still derives its three-part branch.
- Registration stops for every item type, and no writer adds a `workspace.toml` entry. `close-work`'s closure packet carries no registry field.
- The `capture-work` skill and its forwarding alias are gone.

## What stays until the registry is deleted

The repair does not remove everything. Initiative tables stay in `workspace.toml`, and dispatch keeps refusing while the file holds an entry, as the finding says: rewrite or remove by hand any entry the repair leaves. The file and the repair stay supported until the maintainer certifies the retirement. This draft names no release that deletes the file, because none is decided.

## Which release changed what

Each row is the `core` version that shipped the change, read from the version in `packs/core/pack.toml` at that change's commit.

| Release | Change |
| --- | --- |
| 3.1.20 | Dependency edges move onto the waiting item's `Depends on:` header. |
| 3.1.22 | Captured items get their own files. |
| 3.1.23 | The optional `Priority:` header. |
| 3.1.24 | The first-in-list `next_queue` and `next_shape` suggestions are removed. |
| 3.1.26 | Captured items stop registering. |
| 3.1.29 | Repo-origin intents and briefs stop registering. |
| 3.1.35 | Dispatch decides from headers, with a replay against the registry. |
| 3.1.40 | Specs stop registering. |
| 4.0.0 | Full-mode `work-loop` runs through the execution supervisor. |
| 4.0.1 | Tracker-origin work stops registering. |
| 4.0.2 | `close-work` drops its registry field. |
| 4.0.5 | The last registry entries are dropped, and refresh policy moves to `.work-intake.toml`. |
| 4.0.10 | Dispatch reads headers only, and `workspace-status` keeps only the repair. |

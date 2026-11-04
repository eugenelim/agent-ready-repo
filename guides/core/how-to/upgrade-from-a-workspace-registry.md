---
title: Upgrade from a workspace.toml registry
summary: Move what your workspace.toml registry records onto your intents, briefs, specs and captured items with one repair run.
pack: core
kind: how-to
---

# Upgrade from a workspace.toml registry

Your work items now carry their own state. A spec's `Status:` line says where it is, its `Depends on:` line says what it waits for, and each captured item is a file under `docs/product/captured/`. This guide moves what an older `workspace.toml` registry records onto those items, in one repair run. It needs the `core` pack.

## Before you upgrade

Look for a `.workspace-migrations.json` file in your repository root. It exists only if you used the older migration tooling. If it records an operation that is still `pending`, or one you want to roll back, finish or roll it back with your current `core` release first. The new release cannot recover or roll back a recorded migration operation.

## Upgrade the core pack

Upgrade an installed pack with `agentbundle upgrade --pack core`. To install it fresh, use `agentbundle install --pack core`.

## Plan the repair

Ask your agent, in a session in the repository, to plan the repair:

```text
Run the workspace-status repair-plan and show me the plan.
```

The agent runs `workspace-status`'s `repair-plan`. It writes a plan file and lists each automatic operation and each manual item. Nothing changes yet.

## Apply the plan

Read the plan, then ask your agent to apply that exact plan:

```text
Apply the workspace repair plan.
```

The agent runs `repair-apply --yes`. In one run it:

- moves each dependency edge onto the waiting item's `Depends on:` header (`needs-to-header`), including the older string `needs` of a slug-only captured entry;
- writes each captured item that lives elsewhere into its own file under `docs/product/captured/`;
- copies each tracker profile into its artifact's `source-authority` record;
- moves the refresh role policy, the `[authorization.refresh]` table, into `.work-intake.toml` (`refresh-policy-move`);
- removes the intent, brief, spec, tracker and captured-item entries the registry no longer needs, including each captured entry whose file it can read (`captured-entry-drop`).

A manual item keeps its entry and names the reason. Fix it by hand, then plan again.

## Fix any entry the repair cannot read

An entry in an older form, such as a bare `spec/<slug>` string or a `{ slug = … }` table, gets no operation. Rewrite it by hand: give the spec or captured item the matching header, then remove the entry.

## Check the result

Ask your agent what is ready to work on. `work-loop`'s `dispatch.py` reads each artifact's own headers. While `workspace.toml` still holds any entry, it refuses with `unmigrated_workspace` and points you back to the repair. Plan and apply again until it answers.

After the repair, `workspace.toml` holds only what the repair does not move, such as initiative tables. Keep the file. A later `core` release removes what remains.

## Replace the retired commands

`workspace-status` now answers only `repair-plan` and `repair-apply`. These subcommands are retired and exit with `retired_subcommand`:

| Retired subcommand | Use instead |
| --- | --- |
| `status` | `work-loop`'s `dispatch.py` for what is ready, active or blocked; `navigate-intents` `outstanding` for work placed under an intent |
| `reconcile` | `work-loop`'s `dispatch.py`, whose findings name each problem |
| `explain` | `work-loop`'s `dispatch.py` |
| `selected-membership` | `work-loop`'s `dispatch.py` |
| `prune` | no replacement |
| `retirement-candidates` | no replacement |
| `repair-rollback` | no replacement |

The migration tooling is gone too. `repair-plan --migration-selection`, the migration form of `repair-apply`, the `[authorization.migration]` table and `.workspace-migrations.json` are no longer read.

## Update a control plane that reads workspace_status()

If a harness or control plane calls the `agentbundle` MCP tool `workspace_status()`, three things changed:

- Its `ready`, `active` and `blocked` items no longer carry `ini_slug`.
- `shaping` is always an empty list.
- Set `WORKSPACE_MCP_DISPATCHED_ITEM` as `type:slug`. The expected branch is then `type/slug`. The older three-part `ini_slug/type:slug` form still works.

## Check what is not carried over

The repair moves only what a tracked file records. These behaviors are not carried over, and nothing replaces them:

- `<initiative>`, `<initiative>.name`, `<initiative>.status`, `<initiative>.milestone` and `<initiative>.parent`: an initiative is no longer a work item, so nothing moves its name, status, milestone or parent onto an item.
- `entry position`: the order of a registry list means nothing. A start with no named spec lists the ready specs and asks; record a priority with the optional `Priority:` header.
- `behavior outside tracked files`: anything that lived only outside tracked files is not moved.
- the per-entry refresh status `origin_mode`, `profile` and `refresh` for tracker work: refresh itself reports whether it can run.

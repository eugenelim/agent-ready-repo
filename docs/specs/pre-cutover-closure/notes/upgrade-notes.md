---
title: Upgrade from a workspace.toml registry
summary: Move what your workspace.toml registry records onto your intents, briefs, specs and captured items with one repair run.
pack: core
kind: how-to
---

# Upgrade from a workspace.toml registry

You can move what your `workspace.toml` registry records about your work onto the work items themselves. This needs the `core` pack: install it with `agentbundle install --pack core`, or upgrade an installed one with `agentbundle upgrade --pack core`.

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

The agent runs `repair-apply --yes`. It moves each dependency edge onto the waiting item, each captured item into its own file, and each tracker profile into its artifact's record, then removes the intent, brief, spec and tracker entries the registry no longer needs. A manual item keeps its entry and names the reason; fix it by hand and plan again.

After the repair, `workspace.toml` is not empty. Anything the repair does not move stays in it, such as initiative tables, captured-item entries and older slug-only entries, and refresh and migration still read its `[authorization.refresh]` and `[authorization.migration]` policy tables. Keep the file; a later `core` release moves or removes the rest.

## Check what is not carried over

The repair moves only what a tracked file records. These behaviors are not carried over, and nothing replaces them:

- `<initiative>`, `<initiative>.name`, `<initiative>.status`, `<initiative>.milestone` and `<initiative>.parent`: an initiative is no longer a work item, so nothing moves its name, status, milestone or parent onto an item.
- `entry position`: the order of a registry list means nothing. A start with no named spec lists the ready specs and asks; record a priority with the optional `Priority:` header.
- `behavior outside tracked files`: anything that lived only outside tracked files is not moved.
- the per-entry refresh status `origin_mode`, `profile` and `refresh` for tracker work: refresh itself reports whether it can run.

The decisions behind these removals are the [RFC-0106 errata](../../../rfc/0106-stop-registering-derivable-work.md#errata) entries of 2026-10-25 and 2026-10-30, and the [retirement record](../../workspace-retirement/retirement-record.md#disposition) lists each one.

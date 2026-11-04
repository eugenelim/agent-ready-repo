---
title: Move from capture-work to work-intake
summary: Replace capture-work prompts with the current work-intake front door.
pack: core
kind: how-to
---

# Move from capture-work to work-intake

`capture-work` is no longer available. Use `work-intake` directly in prompts,
guides, and automations.

```text
Remember that export retries need idempotent replay. Do not start implementation.
```

The agent creates the smallest safe Draft artifact and stops. An intent, brief or spec is its file alone.

## Replace an existing prompt

Change:

```text
capture-work: export retries need idempotent replay
```

to:

```text
work-intake: remember that export retries need idempotent replay; stop without implementation
```

## Move a former registry entry

If your repo still has a `capture-work` entry in `workspace.toml`, the older registry is still in place. Follow
[Upgrade from a workspace.toml registry](upgrade-from-a-workspace-registry.md): the repair moves what it can onto the artifacts, and the page shows how to rewrite by hand an entry it cannot read.

## Verify the result

Ask what is ready, which runs `work-loop`'s `dispatch.py`; add `--captured` to list the captured items. The artifact carries the lifecycle state chosen by `work-intake`; remembered work remains Draft and non-dispatchable.
A remembered defect, design, or research item is its own file under
`docs/product/captured/`.

See [Use work intake](../../_shared/how-to/use-work-intake.md)
for the current workflow and [Work-intake routing and lifecycle](../reference/work-intake-routing-and-lifecycle.md)
for exact routes and boundaries.

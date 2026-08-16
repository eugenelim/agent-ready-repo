---
title: Migrate capture-work requests to work-intake
summary: Use the compatibility alias safely while moving saved prompts and guidance to Core's intake front door.
pack: core
kind: how-to
---

# Migrate capture-work requests to work-intake

`capture-work` remains available for compatibility, but it no longer owns
classification or storage. Replace it with the equivalent `work-intake`
request in prompts, guides, and automations.

```text
Remember that export retries need idempotent replay. Do not start implementation.
```

The agent records a Draft artifact and non-dispatchable workspace entry, then
stops. This is the same result whether the request reached `work-intake`
directly or through the alias.

## Replace an existing request

Change a prompt such as:

```text
capture-work: export retries need idempotent replay
```

to:

```text
work-intake: remember that export retries need idempotent replay; stop without implementation
```

The alias emits a deprecation notice, normalizes the request, and forwards it.
It does not write a legacy queue entry, run a separate `[build]` versus
`[shape]` classifier, or retain independent semantics.

## Verify the result

Run `workspace-status`. The new artifact should appear in the lifecycle state
chosen by `work-intake`; remembered work remains Draft and non-dispatchable.
The artifact must exist before its schema-valid workspace entry is registered.

See [Start or remember work without choosing a skill](start-or-remember-work.md)
for the main workflow and [Work-intake routing and lifecycle](../reference/work-intake-routing-and-lifecycle.md)
for exact routes and boundaries.

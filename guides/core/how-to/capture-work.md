---
title: Move from capture-work to work-intake
summary: Replace capture-work prompts and legacy workspace entries with the current work-intake front door.
pack: core
kind: how-to
---

# Move from capture-work to work-intake

`capture-work` is no longer available. Use `work-intake` directly in prompts,
guides, and automations.

```text
Remember that export retries need idempotent replay. Do not start implementation.
```

The agent creates the smallest safe Draft artifact, registers a
non-dispatchable entry, and stops.

## Replace an existing prompt

Change:

```text
capture-work: export retries need idempotent replay
```

to:

```text
work-intake: remember that export retries need idempotent replay; stop without implementation
```

## Rewrite a former legacy workspace entry

If `workspace-status` reports an `unsupported_legacy` finding for an entry in
`workspace.toml`, rewrite it in canonical form by hand. Ordinary reconciliation
no longer accepts legacy shapes; they are never dispatchable. Old shaping
entries (for example, `{slug = "...", type = "design"}`) still appear in the
information-only shaping lists (the lists the agent reads but that do not drive
dispatch) until you rewrite them too.

Write a target entry directly in the correct collection:

```toml
{path = "docs/specs/<slug>/spec.md", kind = "spec", source = {mode = "repo-origin"}, summary = "<current outcome>", needs = []}
```

Then remove the legacy record in the same edit — a canonical entry stays blocked
with a `duplicate_membership` finding while its old alias survives anywhere in
the workspace. Run `workspace-status` to confirm the entry reconciles as
expected. For the full set of accepted shapes and
collections, see the
[Target Entry](../reference/workspace-toml-schema.md#target-entry),
[Lifecycle Membership](../reference/workspace-toml-schema.md#lifecycle-membership),
and [Legacy Forms](../reference/workspace-toml-schema.md#legacy-forms) sections
of the schema reference.

## Verify the result

Run `workspace-status`. The artifact should appear in the lifecycle state
chosen by `work-intake`; remembered work remains Draft and non-dispatchable.
The artifact must exist before its schema-valid workspace entry is registered.

See [Use work intake](../../_shared/how-to/use-work-intake.md)
for the current workflow and [Work-intake routing and lifecycle](../reference/work-intake-routing-and-lifecycle.md)
for exact routes and boundaries.

If you have an operation already recorded in `.workspace-migrations.json`
(a prior interrupted apply or a completed apply that you want to roll back),
follow [Recover or roll back a migration operation](migrate-capture-work.md).

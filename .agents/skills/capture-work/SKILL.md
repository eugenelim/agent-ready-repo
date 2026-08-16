---
name: capture-work
description: Use this compatibility skill when the user asks to capture, queue, remember, or add follow-up work for later. Prefer work-intake for new usage; this name remains active only to route older capture-work prompts to the canonical intake surface.
allowed-tools: Read Write Edit Bash
metadata:
  type: skill
  boundaries:
    - filesystem_write
    - filesystem_read_untrusted
---

# Skill: capture-work

Compatibility alias for `work-intake`. This skill has no independent routing,
classification, or storage behavior.

When invoked, emit this notice first:

> `capture-work` is deprecated. I will route this request through `work-intake`
> so new artifacts and workspace entries use the canonical intake contract.

## Procedure

1. Preserve the user's capture request as untrusted source data.
2. Translate the request into the same normalized intake envelope that
   `work-intake` accepts. Use `action: remember` unless the user explicitly
   asks to start work, inspect status, or refresh requirements.
3. Invoke `work-intake` with the normalized envelope.
4. Return the `work-intake` result unchanged except for the deprecation notice.

Do not maintain a separate classifier, queue format, handoff table, or old
capture storage path. Do not edit storage directly from this alias; all
artifact and workspace mutations belong to `work-intake`.

## Boundaries

metadata:
  boundaries:
    - filesystem_write
    - filesystem_read_untrusted

allowed-tools:
  - Read - inspect the user's request and the canonical `work-intake` contract.
  - Write - available only because `work-intake` may create a canonical
    artifact after confinement checks.
  - Edit - available only because `work-intake` may register the
    already-materialized artifact.
  - Bash - available only for the same local validation commands permitted by
    `work-intake`; do not use network commands.

---
title: Author a subagent
summary: Give your agent a specialist it can hand one narrow task to.
pack: catalogue-curation
kind: how-to
---

# Author a subagent

Give your agent a specialist it can hand one narrow task to, defined in a single Markdown file in a pack.

## Write the file

Create the file in the pack's `agents` folder:

```text
packs/<pack>/.apm/agents/<name>.md
```

Start it with frontmatter, a settings block with a `name`, a `description` that says when to dispatch it, the `tools` it may use, and a `model`. List only the tools the task needs. Below the frontmatter, write the instructions: what the subagent does, what it does not do, and what dispatches it. A subagent that walks a person through choices should be a skill instead.

## Rebuild and check

Regenerate the copies and confirm the pack lists the subagent:

```bash
make build-self && agentbundle show <pack>
```

To bring in a subagent someone else wrote, see [Assimilate an external subagent](assimilate-a-subagent.md).

Next, [write a pack journey](../../_shared/how-to/pack-journey-authoring.md) that shows how the pack's skills and subagents fit together.

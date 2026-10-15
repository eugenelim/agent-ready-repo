---
title: "Author a skill"
summary: "Teach your agent a repeating task, as a skill it loads only when a request matches."
pack: _shared
kind: how-to
---

# Author a skill

Teach your agent a task you repeat, as a skill it loads only when a request matches. Add one after you have done the same multi-step task three times, never speculatively.

## Create the skill

Add a `SKILL.md` file in a folder under your pack:

```text
packs/<pack>/.apm/skills/<name>/SKILL.md
```

The file opens with frontmatter, a settings block. Give it a kebab-case `name` and a one-line `description` that starts with "Use when" and names the trigger, because your agent reads the description to decide when to load the skill. Below it, write the steps your agent should follow.

## Rebuild and lint

Edit the source under `packs/`, never the copy under `.claude/skills/`, then regenerate the copies and lint:

```bash
make build-self && agentbundle catalogue lint --root .
```

The linter checks the frontmatter and the projected copy, and tells you what to fix.

## Test that it activates

List prompts that should and should not trigger the skill in `evals/eval_queries.json`, then run them:

```bash
agentbundle pack evals run --pack <name>
```

A miss means the `description` should name its trigger more precisely.

Next, [author a subagent](../../catalogue-curation/tutorials/your-first-subagent.md). Every rule on body structure, scripts, dependencies, and evals is in [Skill authoring standards](../reference/skill-authoring-standards.md).

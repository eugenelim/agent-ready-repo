# How to start working on a project

You have been given access to a repo that uses `workspace.toml`. This guide walks you through confirming the setup, getting oriented, and picking up your first piece of work.

For the greenfield case — starting a brand-new project from scratch — see [From idea to a walking skeleton](../tutorials/start-a-new-project.md). For an end-to-end walkthrough of a complete workspace session, see [Your first workspace session](../tutorials/your-first-workspace.md).

## Prerequisites

- Access to the repo (cloned locally or in a Conductor workspace).
- The `core` pack installed. Check with:

  ```bash
  ls .claude/skills/workspace-status/
  ```

  If the directory is absent, install the pack:

  ```bash
  pip install agentbundle
  agentbundle install --pack core git+https://github.com/<org>/<repo>
  ```

  Then start a fresh agent session so it picks up the installed skills.

## Step 1 — Confirm `workspace.toml` exists

At the repo root:

```bash
ls workspace.toml
```

If it exists, proceed to Step 2. If it is absent, run `workspace-status` — the skill offers to initialize it and walks you through setting up the first initiative.

## Step 2 — Run `workspace-status`

```
workspace-status
```

Read the output carefully. You should see:

- The active initiative name and current milestone.
- Items in the build queue (ready to start or blocked with a reason).
- Items in the shape room (if any shaping work is active).
- Any active-context signals.

For a detailed guide to reading this output, see [How to orient at the start of a session](orient-at-session-start.md).

## Step 3 — Identify the active initiative and milestone

The initiative names what the team is working toward. The milestone names the current phase. Before picking up any work, confirm:

- Which initiative is active.
- Which milestone you are in.
- Whether the spec you are about to start belongs to this milestone.

If you are unsure whether a spec is in scope for the current milestone, read the milestone notes (usually in `docs/product/` or referenced in `workspace.toml` comments) before starting.

## Step 4 — Pick a ready item

From the `workspace-status` output, pick an item from the **Ready to start** section. The output shows the command to start it:

```
work-loop docs/specs/<slug>/
```

If the Ready section is empty and everything is blocked, read the blocked section to understand the dependency. Surface the blocker if you need help resolving it.

## Step 5 — Start `work-loop`

Invoke the work-loop skill on the spec you picked:

```
use the work-loop skill to implement docs/specs/<slug>/
```

The skill reads the spec, orients to the plan, and begins the plan → execute → gates → review loop. For the full how-to, see [How to plan and execute non-trivial work](plan-and-execute-non-trivial-work.md).

## Related

- [How to orient at the start of a session](orient-at-session-start.md) — detailed orientation guide
- [How to plan and execute non-trivial work](plan-and-execute-non-trivial-work.md) — the `work-loop` guide
- [The two-room model](../explanation/two-room-model.md) — why the queue has two rooms
- [workspace.toml schema reference](../reference/workspace-toml-schema.md) — every field explained
- [Your first workspace session](../tutorials/your-first-workspace.md) — an end-to-end walkthrough

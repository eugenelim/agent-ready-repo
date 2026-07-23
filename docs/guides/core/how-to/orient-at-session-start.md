# How to orient at the start of a session

**Use this when:** You are starting an agent session on a repo that uses `workspace.toml` and need to read queue state before picking work.
**Prerequisites:** `core` pack installed and a terminal or agent session open in the repo root; see Prerequisites below.
**Result:** Active initiative, milestone, and next ready action identified — you know which spec to start or which shaping skill to run.

You are starting an agent session on a repo that uses `workspace.toml`. This guide walks you through running `workspace-status` to read the queue state, identifying your active initiative, and picking your next action before starting any work.

For *why* the shaping and build queues are separated, see [The two-room model](../explanation/two-room-model.md). For the authoritative description of every `workspace.toml` field, see [workspace.toml schema reference](../reference/workspace-toml-schema.md).

## Prerequisites

- The `core` pack installed in the target repo.
- A terminal or agent session open in the repo root.

## Step 1 — Run `workspace-status`

Invoke the `workspace-status` skill at the start of every session:

```
workspace-status
```

The skill reads `workspace.toml` and produces an orientation output. If `workspace.toml` is absent, the skill offers to initialize it.

**You should see:** a block with the active initiative name, current milestone, and the state of both the shape room and the build room.

## Step 2 — Read the initiative and milestone

At the top of the output, confirm:

- Which initiative is active (the `["ini-NNN"].name` value, e.g. "Platform Core").
- Which milestone is current (e.g. "M1 · Workspace Foundation").

This is the strategic context for the session. If you are about to work on a spec, confirm it belongs to this initiative before picking it up.

## Step 3 — Read the active-context signals

The output includes an **Active context** block listing any `signal`-type entries in the shape room. Signals are ongoing monitoring items — they have no discrete end state and don't require action, but they set the context for what you build.

Read them if present; no action is required.

## Step 4 — Read the ready-to-start and blocked sections

The output lists build-room items by readiness:

- **Ready to start** — unblocked specs in the build queue. Each comes with the command to start it (`work-loop docs/specs/<slug>/`).
- **Blocked** — specs in the queue whose `needs` dependencies aren't yet satisfied, with the blocking item named.

Pick one ready-to-start item. If nothing is ready, read the blocked section to understand what would unblock the queue.

## Step 5 — Read the shaping queue

If the output includes a shaping section, read it:

- **Active shaping** — items currently in the shape room, each with the recommended skill to run.
- **Shape room backlog** — items waiting to be picked up for shaping.

If your session goal is shaping work, pick an active shaping item and run the suggested skill.

## Step 6 — Pick your next action

You now have enough context to start. The common cases:

| Queue state | Next action |
|-------------|------------|
| A build item is ready | `work-loop docs/specs/<slug>/` |
| A shaping item is active | Run the suggested shaping skill |
| You've noticed something new mid-session | `capture-work` — see [How to capture and triage a work item](capture-work.md) |
| Nothing is ready; everything is blocked | Surface the blocking dependency — resolve it or capture a follow-on |

## Related

- [The two-room model](../explanation/two-room-model.md) — why the queue has two rooms
- [How to capture and triage a work item](capture-work.md) — when you notice something new during the session
- [How to start working on a project](start-a-project.md) — if this is your first session on the repo
- [workspace.toml schema reference](../reference/workspace-toml-schema.md) — every field explained
- [Your first workspace session](../tutorials/your-first-workspace.md) — an end-to-end walkthrough

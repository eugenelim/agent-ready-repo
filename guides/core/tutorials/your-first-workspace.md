---
title: Your first workspace session
summary: Complete a workspace session from orientation through durable follow-up intake.
pack: core
kind: tutorial
---

# Your first workspace session

**What you'll build:** A complete workspace session — oriented with `workspace-status`, a spec progressed through `work-loop`, a separable follow-on remembered mid-session with `work-intake`, and a clean queue handed off for the next session.
**Prerequisites:** A repo with `workspace.toml` at the root and the `core` pack installed; see [How to start working on a project](../how-to/start-a-project.md) for the install step.
**Time:** About 30 minutes.

:::note
At the end of this tutorial you'll have run a complete workspace session: oriented using `workspace-status`, picked a spec from the build queue, invoked `work-loop`, remembered a separable follow-on mid-session using `work-intake`, and left the queue in a clean state for the next session.
:::

We use one concrete workspace throughout: the **Acme Platform** repo — a backend platform with one active initiative, two specs in its build queue, and one shaping item being framed as strategy. The session goal is to orient, pick a spec, and begin building.

## Before you begin

You need:

- A repo with `workspace.toml` at the root.
- The `core` pack installed. If you haven't installed it yet, see [How to start working on a project](../how-to/start-a-project.md) for the install step.
- A fresh agent session (restart your Claude Code or Conductor session if you've been working on something else — a fresh context gives you a complete orientation).

## Step 1 — Orient: run `workspace-status`

Start every session by invoking `workspace-status`:

```
workspace-status
```

For the Acme Platform, you should see output like this:

```
Initiative: Platform Core
Milestone: M1 · Workspace Foundation

Active context — signals
  [shape] infra-cost-monitoring (signal) — ongoing cost context

Shape room
  [shape] auth-strategy (strategy) — run frame-situation

Build queue — Ready to start
  [build] spec/workspace-core — work-loop docs/specs/workspace-core/
  [build] spec/capture-work-v2 — work-loop docs/specs/capture-work-v2/

Build queue — Blocked
  [build] spec/workspace-status-phase2 — needs: work:spec/workspace-core
```

Read each section before doing anything:

- **Active context** — `infra-cost-monitoring` is a signal. It gives ongoing cost context for architectural decisions; no action is needed today.
- **Shape room** — `auth-strategy` needs strategic framing before it can become a spec. It is not ready to build yet.
- **Ready to start** — two specs are unblocked and ready. Each shows the command to start it.
- **Blocked** — `workspace-status-phase2` is waiting for `workspace-core` to ship first.

:::note
If your output uses different slugs, that is expected — the section structure is what matters.
:::

## Step 2 — Pick a spec and read it briefly

You'll build `workspace-core` — the first ready item. It also unblocks `workspace-status-phase2` when it ships.

Before running `work-loop`, skim the spec:

```bash
cat docs/specs/workspace-core/spec.md
```

Confirm:
- The **Objective** tells you what it does and why.
- The **Acceptance Criteria** are specific and checkable.
- **Status** is not `Shipped` (if it is already shipped, pick a different spec).

Understanding the goal before the loop starts saves time if review finds scope creep.

## Step 3 — Invoke `work-loop`

Start the loop:

```
use the work-loop skill to implement docs/specs/workspace-core/
```

The skill reads `spec.md` and `plan.md`, orients to the task wave, and enters PLAN. It tells you:

- Which files it will touch.
- What tests will demonstrate "done" for each task.
- What it is *not* changing — the declined-pattern register.

**You should see:** a PLAN block with the task wave, the verification modes, and the declined patterns named. The loop then proceeds to EXECUTE task by task.

Let the loop run. After each wave, it runs gates (lint, typecheck, tests). When all gates pass, it routes to adversarial review.

## Step 4 — Mid-session: notice a separable follow-on

While `work-loop` is executing, review finds an improvement that does not
belong in the accepted outcome:

```
Follow-on: make retry backoff configurable for service owners.
```

The owner confirms that the current spec can ship without this behavior. If it
were still required, the spec would remain `Implementing`. Because it is
separable, capture it as its own artifact instead of leaving an open acceptance
criterion behind.

## Step 5 — Capture the follow-on

Invoke `work-intake` without stopping the loop:

```
work-intake: remember the configurable retry backoff follow-on from this spec;
stop without implementation
```

The skill classifies it as a minimal intent and records Draft,
non-dispatchable membership with a source reference:

```
artifact    docs/product/intents/configurable-retry-backoff.md
membership  draft · non-dispatchable
processor   none
source      spec/workspace-core follow-on
```

Confirm. The skill writes the Draft intent first, then registers a schema-valid
entry containing `path`, `kind`, `source`, `summary`, and `needs`.

**You should see:** the new intent artifact and its non-dispatchable workspace
entry. The artifact, not a TOML comment or chat transcript, is the requirements
authority. The workspace entry keeps a short current/next summary and hard
dependencies only. Because the item is not independently shippable yet, no
processor is dispatched.

For more on how intake routes items, see [Start or remember work without choosing a skill](../how-to/start-or-remember-work.md).

## Step 6 — Let `work-loop` finish

Return to the loop. It completes its remaining tasks, runs gates, and routes to adversarial review. Review findings come back as Blockers / Concerns / Nits; the loop fixes and re-reviews until the reviewer reports `Clean — ready to commit.`

**You should see:** `Clean — ready to commit.` from the adversarial reviewer, followed by commit and PR instructions.

## Step 7 — Ship and close the session

Follow the loop's commit and PR instructions. When the PR merges:

1. The spec's **Status** updates to `Shipped` in `spec.md`.
2. Move the entry in `workspace.toml` from `["ini-001".work].queue` to `["ini-001".work].shipped`.
3. Run `workspace-status` to confirm the queue state.

**You should see:** `workspace-core` no longer in the Ready section, and `workspace-status-phase2` now unblocked — ready to start.

## What you learned

In this session you:

- Oriented using `workspace-status` and read both the shape room and the build room.
- Read a spec briefly before starting `work-loop`.
- Ran a complete `work-loop` cycle — PLAN, EXECUTE, GATES, REVIEW, DECIDE.
- Remembered a follow-on mid-session with `work-intake`, producing a Draft, non-dispatchable artifact with source provenance.
- Ended with a clean queue: one item shipped, one backlog entry added, one build-queue item unblocked.

## Next steps

- To orient faster at future session starts: [How to orient at the start of a session](../how-to/orient-at-session-start.md).
- To understand the two-room model behind the queue: [The two-room model](../explanation/two-room-model.md).
- To remember future items mid-session: [Start or remember work without choosing a skill](../how-to/start-or-remember-work.md).
- To start the next spec: run `workspace-status`, then `work-loop docs/specs/<next-slug>/`.

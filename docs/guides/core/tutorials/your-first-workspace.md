# Your first workspace session

> At the end of this tutorial you'll have run a complete workspace session: oriented using `workspace-status`, picked a spec from the build queue, invoked `work-loop`, captured a deferred item mid-session using `capture-work`, and left the queue in a clean state for the next session.

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

> If your output uses different slugs, that is expected — the section structure is what matters.

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

## Step 4 — Mid-session: notice a deferred item

While `work-loop` is executing, you read through the spec and notice this acceptance criterion:

```
- [ ] AC7: retry backoff is configurable (deferred: configurable-retry-backoff)
```

AC7 was cut from this PR — it is deferred with slug `configurable-retry-backoff`. This needs to be captured in `workspace.toml` so it doesn't get lost.

## Step 5 — Capture the deferred item

Invoke `capture-work` without stopping the loop:

```
capture-work: the workspace-core spec deferred configurable retry backoff — AC7 with slug configurable-retry-backoff
```

The skill classifies it as a repo-level deferred item and routes it to `[backlog].open` with a source reference:

```
[build] — deferred acceptance criterion; routes to [backlog].open.
Proposed: append to [backlog].open:
  # spec/workspace-core AC7: retry backoff should be configurable
  {slug = "configurable-retry-backoff", source = "spec/workspace-core AC7"}
Confirm? (y/n)
```

Confirm. The skill writes the entry with its provenance comment.

**You should see:** a new entry in `[backlog].open` with slug `configurable-retry-backoff`. Deferred AC items go to `[backlog].open` (not the initiative's `[work].queue`) because they carry a `source` reference back to the spec that deferred them.

For more on how `capture-work` classifies items, see [How to capture and triage a work item](../how-to/capture-work.md).

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
- Captured a deferred item mid-session with `capture-work`, routing it to `[backlog].open` with a `source` reference back to the spec that deferred it.
- Ended with a clean queue: one item shipped, one backlog entry added, one build-queue item unblocked.

## Next steps

- To orient faster at future session starts: [How to orient at the start of a session](../how-to/orient-at-session-start.md).
- To understand the two-room model behind the queue: [The two-room model](../explanation/two-room-model.md).
- To capture future items mid-session: [How to capture and triage a work item](../how-to/capture-work.md).
- To start the next spec: run `workspace-status`, then `work-loop docs/specs/<next-slug>/`.

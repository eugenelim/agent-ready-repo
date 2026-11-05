---
title: Your first workspace session
summary: Complete a workspace session from orientation through durable follow-up intake.
pack: core
kind: tutorial
---

# Your first workspace session

**What you'll build:** A complete workspace session — oriented by asking what is ready, a spec progressed through `work-loop`, a separable follow-on remembered mid-session with `work-intake`, and a clean state handed off for the next session.
**Prerequisites:** A repo with the `core` pack installed; see [How to start working on a project](../how-to/start-a-project.md) for the install step.
**Time:** About 30 minutes.

:::note
At the end of this tutorial you'll have run a complete workspace session: asked what is ready, picked a spec, invoked `work-loop`, remembered a separable follow-on mid-session using `work-intake`, and left the repo in a clean state for the next session.
:::

We use one concrete workspace throughout: the **Acme Platform** repo — a backend platform with two Approved specs, one of them waiting on the other through a `Depends on:` header, and one captured strategy item. The session goal is to orient, pick a spec, and begin building.

```text
What is ready to work on in this repo?
```

## Before you begin

You need:

- A repo with the `core` pack installed. If you haven't installed it yet, see [How to start working on a project](../how-to/start-a-project.md) for the install step. No `workspace.toml` is needed.
- A fresh agent session (restart your agent session if you've been working on something else — a fresh context gives you a complete orientation).

## Orient: ask what is ready

Start every session by asking what is ready. Your agent runs `work-loop`'s `dispatch.py`, which reads each spec's `Status:` and `Depends on:` headers and writes nothing:

```bash
python '<skill-dir>/scripts/dispatch.py' --root . --captured
```

For the Acme Platform, the answer reads like this:

```
Ready
  docs/specs/workspace-core/spec.md          Approved
  docs/specs/capture-work-v2/spec.md         Approved

Blocked
  docs/specs/status-phase2/spec.md Approved — Depends on: spec/workspace-core

Captured
  auth-strategy (strategy) — run frame-situation
  infra-cost-monitoring (signal) — ongoing cost context

Decision: ask — two specs are ready
```

Read each part before doing anything:

- **Ready** — two specs are unblocked. Each starts with `work-loop docs/specs/<slug>/`.
- **Blocked** — `status-phase2` carries `Depends on: spec/workspace-core`, so it waits for `workspace-core` to ship first.
- **Captured** — `auth-strategy` needs strategic framing before it can become a spec. `infra-cost-monitoring` is a signal: ongoing cost context, no action needed today.
- **Decision** — with two ready specs, dispatch asks you to choose and never picks for you.

**The agent asks:**

```text
Which ready item do you want to start?
```

**You answer:**

```text
Start workspace-core, the first ready build item for the current milestone.
```

:::note
If your output uses different slugs, that is expected — the sections are what matter.
:::

## Pick a spec and read it briefly

You'll build `workspace-core` — the first ready item. It also unblocks `status-phase2` when it ships.

Before running `work-loop`, skim the spec:

```bash
cat docs/specs/workspace-core/spec.md
```

Confirm:
- The **Objective** tells you what it does and why.
- The **Acceptance Criteria** are specific and checkable.
- **Status** is not `Shipped` (if it is already shipped, pick a different spec).

Understanding the goal before the loop starts saves time if review finds scope creep.

## Invoke `work-loop`

Start the loop:

```
use the work-loop skill to implement docs/specs/workspace-core/
```

The skill reads `spec.md` and `plan.md`, orients to the task wave, and enters PLAN. It tells you:

- Which files it will touch.
- What tests will demonstrate "done" for each task.
- What it is *not* changing.
- Any declined architectural addition that materially affects scope or design.

**You should see:** a PLAN block with the task wave, verification modes, and review shape. A declined architectural addition appears only when it materially affects scope or design. The loop then proceeds to EXECUTE task by task.

Let the loop run. After each wave, it runs gates (lint, typecheck, tests). When all gates pass, it routes to adversarial review.

## Mid-session: notice a separable follow-on

While `work-loop` is executing, review finds an improvement that does not
belong in the accepted outcome:

```
Follow-on: make retry backoff configurable for service owners.
```

The owner confirms that the current spec can ship without this behavior. If it
were still required, the spec would remain `Implementing`. Because it is
separable, capture it as its own artifact instead of leaving an open acceptance
criterion behind.

## Capture the follow-on

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

Confirm. The skill writes the Draft intent as its own file, because a repo-origin intent is its file alone.

**You should see:** the new intent artifact. The artifact, not a TOML comment or
chat transcript, is the requirements authority. Because the item is not independently shippable yet, no
processor is dispatched.

For more on how intake routes items, see [Start a software change](../how-to/start-or-remember-work.md).

## Let `work-loop` finish

Return to the loop. It completes its remaining tasks, runs gates, and routes to adversarial review. Review findings come back as Blockers / Concerns / Nits; the loop fixes and re-reviews until the reviewer reports `Clean — ready to commit.`

**You should see:** `Clean — ready to commit.` from the adversarial reviewer, followed by commit and PR instructions.

## Ship and close the session

Follow the loop's commit and PR instructions. When the PR merges:

1. The spec's **Status** updates to `Shipped` in `spec.md`.
2. Nothing else needs moving: a spec's `Status:` is the whole record.
3. Ask what is ready again, which runs `dispatch.py`, to confirm the state.

**You should see:** `workspace-core` shown as shipped, and `status-phase2` now unblocked — ready to start.

Shipping is not closeout. Before the delivery contract itself is disposed of, ask
`close-work` for a mutation-free preview of what the spec and plan still hold that
no other document does — see
[Close work without losing lasting context](../how-to/close-and-disposition-work.md).

## What you learned

In this session you:

- Oriented by asking what is ready, answered by `dispatch.py`, and read both the shape room and the build room.
- Read a spec briefly before starting `work-loop`.
- Ran a complete `work-loop` cycle — PLAN, EXECUTE, GATES, REVIEW, DECIDE.
- Remembered a follow-on mid-session with `work-intake`, producing a Draft, non-dispatchable artifact with source provenance.
- Ended clean: one spec shipped, one follow-on captured, one blocked spec unblocked.

## What you have now

You have a completed workspace session: the shipped spec, a separately captured
follow-on at `docs/product/intents/configurable-retry-backoff.md`, and an
updated state that identifies the next ready item. Start the next session by
asking what is ready.

## Next steps

- To orient faster at future session starts: [How to orient at the start of a session](../how-to/orient-at-session-start.md).
- To understand the two-room model behind the two kinds of work: [The two-room model](../explanation/two-room-model.md).
- To remember future items mid-session: [Use work intake](../../_shared/how-to/use-work-intake.md).
- To close a finished delivery without losing its lasting context: [Close work without losing lasting context](../how-to/close-and-disposition-work.md).
- To start the next spec: ask what is ready (`dispatch.py`), then `work-loop docs/specs/<next-slug>/`.

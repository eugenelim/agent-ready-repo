---
title: How to plan and execute non-trivial work
summary: Turn an approved spec into a locked plan, checked implementation, independent review, and merge-ready change.
pack: core
kind: how-to
---

# How to plan and execute non-trivial work

Take a feature, refactor, or multi-file change to a merge-ready pull request with the `new-spec` and `work-loop` skills. You need [the `core` pack installed](../../_shared/how-to/install-packs.md) and set up with [adapt-to-project](adapt-to-project.md), and a directory where you can edit, commit, and run your lint, type, and test commands. A spec is a short document that says what done means; [the core pack explained](../explanation/core-pack.md) gives the why.

## Pick your entry point

Choose the skill by where the work stands:

| Situation | Skill to invoke |
| --- | --- |
| New feature or significant change, no spec yet | `new-spec`, then `work-loop` |
| Spec already exists in `docs/specs/<feature>/` | `work-loop` (it reads the spec) |
| Multi-file bug fix | `bug-fix`; see [how to fix a bug](bug-fix.md) |
| One-line edit, typo, single config tweak | Skip the loop; the overhead is not worth it |

When unsure whether a change is trivial, default to the loop. Name the skill in your request: naming it guarantees it fires, where a natural phrasing usually does but not always.

## Write the spec

Ask for the spec by naming the skill:

```text
use the new-spec skill to design webhook retries with exponential backoff for the payment-events stream
```

The agent writes `docs/specs/<feature>/spec.md` and `plan.md`, lists its assumptions as Verified, Unverified, and Defaulted, and waits for you to confirm the Unverified ones. The shaping reviewer reads the draft cold for scope and observability, and the adversarial reviewer reads it for construction risk; security and quality reviewers stay later code-review lenses. Approve the spec before any code is written. Stopping here is fine: the spec and plan are durable.

## Build it

Point the agent at the approved spec:

```text
use the work-loop skill to implement docs/specs/webhook-retries
```

Naming `work-loop` fires its full discipline: gates, adversarial review, and the iteration cap. The agent builds task by task, runs lint, type checks, and tests, and sends the diff to an independent reviewer. It stops for your decision where it needs one, and the merge is yours.

## Stop when the loop tells you to

When gates are green and review is clean, ship. If the work is not done and either cue below fires, the task is bigger than you planned. Re-plan rather than widening scope silently:

- **The retry cap fires.** `work-supervisor.py status --check` exits 3, or a `retry-cap` decision opens. The loop stopped converging; stop and re-plan or split the task.
- **The diff shrinks but findings do not.** You are fixing symptoms; go back to the plan.

## What you have now

After the spec, you have an approved spec and plan in `docs/specs/<feature>/` and nothing implemented. After the loop, you have the change built against that spec: every gate green, reviewers clean, findings resolved or explicitly dispositioned, the spec `Shipped`, the plan `Done`, and a merge-ready pull request.

Skip this workflow for one-line edits, throwaway spikes, and work you cannot yet describe. [The reference](../reference/plan-and-execute-details.md) has worked examples, the full stop cues, step details, variations, pitfalls, and the checks before a pull request.

Next, [close the work out](close-and-disposition-work.md).

---
title: How to plan and execute non-trivial work
summary: Turn an approved spec into a locked plan, checked implementation, independent review, and merge-ready change.
pack: core
kind: how-to
---

# How to plan and execute non-trivial work

Take a feature, refactor, or multi-file change from an idea to a merge-ready pull request, using the `new-spec` and `work-loop` skills. You need the `core` pack installed and a working directory where you can edit, commit, and run your lint, type, and test commands. The skills write a spec, a short document that says what done means, and a plan, then build and review against them.

## Pick your entry point

Choose the skill by where the work stands:

| Situation | Skill to invoke |
| --- | --- |
| New feature or significant change, no spec yet | `new-spec`, then `work-loop` |
| Spec already exists in `docs/specs/<feature>/` | `work-loop` (it reads the spec) |
| Multi-file bug fix | `bug-fix`; see [how to fix a bug](bug-fix.md) |
| One-line edit, typo, single config tweak | Skip the loop; the overhead is not worth it |

When you are unsure whether a change is trivial, default to the loop. Name the skill in your request: naming it guarantees it fires, where a natural phrasing like "let's spec this out" usually does but not always.

## Write the spec

Ask for the spec by naming the skill:

```text
use the new-spec skill to design webhook retries with exponential backoff for the payment-events stream
```

The agent writes `docs/specs/<feature>/spec.md` and `plan.md`, lists what it assumed as Verified, Unverified, and Defaulted, and waits for you to confirm the Unverified items. The shaping reviewer then reads the draft cold for scope and observability, and the adversarial reviewer reads it for construction risk. Security and quality reviewers stay later code-review lenses. Read the spec and approve it before any code is written; stopping here is a fine exit, because the spec and plan are durable.

## Build it

Point the agent at the approved spec:

```text
use the work-loop skill to implement docs/specs/webhook-retries
```

The agent plans each task, builds task by task, runs lint, type checks, and tests, and sends the diff to an independent reviewer, fixing what the reviewer finds. It stops for your decision where it needs one. The merge is yours.

## Stop when the loop tells you to

Three cues mean the task is bigger than planned:

- **Gates green and review clean:** ship.
- **The retry cap fires:** the loop stopped converging. Stop and re-plan or split the task; do not push past it.
- **The diff shrinks but findings do not:** you are fixing symptoms. Go back to the plan.

Re-plan rather than widening scope silently.

## What you have now

If you stopped after the spec, you have an approved spec and plan at `docs/specs/<feature>/` and nothing implemented. If you ran the loop through, you have the change implemented against that spec with every gate green and the reviewers clean, the spec marked `Shipped`, and a merge-ready pull request.

Skip this workflow for genuine one-line edits, throwaway spikes, and investigation before you know what to build. [The reference](../reference/plan-and-execute-details.md) lists what each step does, the variations, the common pitfalls, and the checks that run before a pull request opens.

Next, [close the work out](close-and-disposition-work.md).

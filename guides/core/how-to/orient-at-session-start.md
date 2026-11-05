---
title: How to orient at the start of a session
summary: Read what is ready, active and blocked, and choose the next action.
pack: core
kind: how-to
---

# How to orient at the start of a session

**Use this when:** You are starting an agent session on a repo and need to know which work is ready, in flight or blocked before picking something.
**Prerequisites:** `core` pack installed and a terminal or agent session open in the repo root; see Prerequisites below.
**Result:** The ready, active and blocked specs, any captured items, and the next action identified.

This guide covers session orientation. It uses `work-loop`'s `dispatch.py`, which reads each spec's own `Status:` header, its `Depends on:` line and its sibling plan, and writes nothing.

For **intent status, hierarchy, and outstanding work** — which intents are not yet terminal, what the parent of an intent is, or what briefs and specs are open — use `navigate-intents` instead: [How to navigate intents, briefs, and specs](navigate-intents.md).

```text
What is ready to work on in this repo?
```

For *why* shaping work and build work are told apart, see [The two-room model](../explanation/two-room-model.md).

## Prerequisites

- The `core` pack installed in the target repo.
- A terminal or agent session open in the repo root.

## Ask what is ready

At the start of every session, ask your agent what is ready. It runs `work-loop`'s `dispatch.py` and reads its JSON output:

```bash
python '<skill-dir>/scripts/dispatch.py' --root . --captured
```

No `workspace.toml` is needed. The `ready`, `active` and `blocked` lists name each spec with its `status` and any findings. The `decision` object says what to do next: `start`, `resume`, `ask`, `none` or `refuse`.

**You should see:** the decision for this session and the specs behind it.

## Read the ready and blocked lists

- **Ready** — Approved specs whose plan exists and whose `Depends on:` targets are satisfied. Start one with `work-loop docs/specs/<slug>/`.
- **Active** — specs whose `Status:` is `Implementing`. Resume one rather than starting another.
- **Blocked** — specs that are neither, with a finding that names the reason, such as an unmet `Depends on:` target.

When several specs qualify, `decision.action` is `ask` and `decision.candidates` lists them. Pick one yourself; dispatch never does. If nothing is ready, read the blocked findings to see what would unblock work.

## Read the captured items

`--captured` adds a `captured` key that lists the items under `docs/product/captured/`. A captured item with a shaping type names the skill that picks it up; a `signal` item is monitoring context and needs no action. Read them if present.

## Read the work placed under an intent

Dispatch answers only for specs. To see which briefs and specs are open under an intent, use `navigate-intents` `outstanding`: [How to navigate intents, briefs, and specs](navigate-intents.md).

## If dispatch refuses

If `workspace.toml` still holds registry entries from an older release, dispatch refuses with `unmigrated_workspace` and its `next_action` points to the repair. Follow [Upgrade from a workspace.toml registry](upgrade-from-a-workspace-registry.md), then ask again.

## Pick your next action

| Dispatch answer | Next action |
|-----------------|-------------|
| `start` or a ready spec | `work-loop docs/specs/<slug>/` |
| `resume` or an active spec | Resume it with `work-loop` |
| `ask` | Pick one of `decision.candidates` |
| `none`, everything blocked | Resolve the blocking dependency or capture a follow-on |
| You've noticed something new mid-session | `work-intake` — see [Use work intake](../../_shared/how-to/use-work-intake.md) |
| A tracker-origin artifact has a newer source revision | Ask `work-intake` to refresh it and review the field delta |
| `unmigrated_workspace` | Run the repair in [Upgrade from a workspace.toml registry](upgrade-from-a-workspace-registry.md) |

## What you have now

You know what is ready, active and blocked, and have a safe next action for this session. Start the selected ready spec, or resolve a named blocker before choosing another task.

## Related

- [The two-room model](../explanation/two-room-model.md) — how shape and build work differ
- [Use work intake](../../_shared/how-to/use-work-intake.md) — when you notice something new during the session
- [How to start working on a project](start-a-project.md) — if this is your first session on the repo
- [Your first workspace session](../tutorials/your-first-workspace.md) — an end-to-end walkthrough
- [Upgrade from a workspace.toml registry](upgrade-from-a-workspace-registry.md) — repair an older registry onto the headers

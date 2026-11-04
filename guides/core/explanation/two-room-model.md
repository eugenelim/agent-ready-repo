---
title: "The two-room model: shaping vs. building"
summary: Why shaping work and build work use distinct lifecycle rooms.
pack: core
kind: explanation
---

# The two-room model: shaping vs. building

Most knowledge work has two distinct modes that don't mix well. In the first, you *discover* what to build — you research, frame, and structure an idea until it is sharp enough to become a spec. In the second, you *build* — you implement, verify, and ship. This repo separates those two modes into two rooms: the **shape room** and the **build room**.

This page explains the distinction, what goes in each room, and how items move between them. For how to orient to both rooms at session start, see [How to orient at the start of a session](../how-to/orient-at-session-start.md). For the current intake route, see [Start a software change](../how-to/start-or-remember-work.md).

## The shape room

The shape room holds work that is not yet ready to implement. The canonical question is: *do we know exactly what to build?* If the answer is no — the idea needs research, framing, or strategic validation before a spec can be written — the item belongs in the shape room.

Shape work is told apart by its artifact type and that artifact's `Status:`: an intent or brief that is still being framed, or a captured item under `docs/product/captured/`. A captured item's `Type:` routes it to the right shaping skill:

| Type | What it means | Skill |
|------|--------------|-------|
| `shape` | Needs product-engineering shaping | `intent frame` |
| `research` | Needs desk research before a spec can be written | `desk-research-project-start` |
| `strategy` | Needs market or product strategy work | `frame-situation` |
| `signal` | Ongoing monitoring context — has no discrete end state | (informational only — no action) |
| `design` | Needs experience-design work | `experience-status` |

Shaping work ends when the item is shaped enough to write a spec. At that point, a spec is authored via `new-spec`. A `signal` item never graduates — it stays as ongoing context.

## The build room

The build room holds work that is ready to implement — a spec exists, the contract is clear, and `work-loop` can carry it. The canonical question is: *does a spec exist and is the contract clear?* If yes, the item belongs in the build room.

The build room is the specs under `docs/specs/`. Each spec's own headers say where it stands:

| Header | What it means |
|--------|--------------|
| `Status: Approved` | Ready to start, once its plan exists and its dependencies are met |
| `Status: Implementing` | Being built |
| `Status: Shipped` | Implemented — set when the PR merges |
| `Depends on:` | The items it waits for |

Readiness comes from `work-loop`'s `dispatch.py`, which reads those headers. Nothing is registered anywhere else.

## Why the separation matters

Mixing shaping and building in one queue causes two kinds of harm:

1. **False readiness** — an item looks ready to build but turns out to need research or framing mid-implementation. The session has to stop, do discovery work, and restart — paying the cost of a context-switch mid-build.
2. **Blocked builds** — a build queue full of items-that-are-really-shape-work blocks the real build items. Nothing ships because nothing is actually ready.

Separating the rooms makes the distinction explicit at capture time, before work starts, rather than at implementation time, when the surprise is most expensive.

## How items move between rooms

The path is one-way:

1. A new item arrives — a user surfaces it mid-session, a spec reveals a follow-on, or a review finds a gap. `work-intake` materializes the right canonical artifact; its `Status:` is its lifecycle state. Work that is not independently shippable remains a non-dispatchable Draft.
2. Shape items are worked until a spec can be written. The spec lands in `docs/specs/<slug>/`.
3. The spec is ready for the build room once its `Status:` and sibling plan say so, and its `Depends on:` targets are met.
4. `work-loop` builds the spec. On PR merge, its `Status:` becomes `Shipped`.

A `signal` item never follows this path — it stays as persistent context.

## How `dispatch.py` surfaces both rooms

Asking what is ready at session start runs `work-loop`'s `dispatch.py`:

- **Build room** — `ready`, `active` and `blocked` specs, and a `decision` saying whether to start, resume, ask or stop.
- **Shape room** — `dispatch.py --captured` adds the captured items, each with its type. Work placed under an intent shows in `navigate-intents` `outstanding`.
- **Signals** appear as context without a suggested action.

Read that output to understand the state of both rooms before picking up any work.

## See also

- [How to orient at the start of a session](../how-to/orient-at-session-start.md) — read both rooms at session start
- [Start a software change](../how-to/start-or-remember-work.md) — route a new item into durable artifact and lifecycle state
- [Upgrade from a workspace.toml registry](../how-to/upgrade-from-a-workspace-registry.md) — repair a repo that still has an older registry

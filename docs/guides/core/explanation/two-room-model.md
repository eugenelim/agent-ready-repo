# The two-room model: shaping vs. building

Most knowledge work has two distinct modes that don't mix well. In the first, you *discover* what to build — you research, frame, and structure an idea until it is sharp enough to become a spec. In the second, you *build* — you implement, verify, and ship. This repo separates those two modes into two rooms: the **shape room** and the **build room**.

This page explains the distinction, what goes in each room, and how items move between them. For how to orient to both rooms at session start, see [How to orient at the start of a session](../how-to/orient-at-session-start.md). For how to route a new item to the right room, see [How to capture and triage a work item](../how-to/capture-work.md).

## The shape room

The shape room holds work that is not yet ready to implement. The canonical question is: *do we know exactly what to build?* If the answer is no — the idea needs research, framing, or strategic validation before a spec can be written — the item belongs in the shape room.

In `workspace.toml`, the shape room is the `["ini-NNN".shaping_queue]` section:

- **`active`** — items currently being shaped in this initiative, plus `signal`-type entries that live here permanently as ongoing monitoring context.
- **`backlog`** — items waiting to be picked up for shaping.

Each entry carries a `type` field that routes it to the right shaping skill:

| Type | What it means | Skill |
|------|--------------|-------|
| `shape` | Needs product-engineering shaping (default when `type` omitted) | `frame-intent` |
| `research` | Needs desk research before a spec can be written | `desk-research-project-start` |
| `strategy` | Needs market or product strategy work | `frame-situation` |
| `signal` | Ongoing monitoring context — has no discrete end state | (informational only — no action) |
| `design` | Needs experience-design work | `experience-status` |

Shaping work ends when the item is shaped enough to write a spec. At that point, a spec is authored via `new-spec` and the spec's path moves to the build room. A `signal` item never graduates — it stays in the shape room as ongoing context.

## The build room

The build room holds work that is ready to implement — a spec exists, the contract is clear, and `work-loop` can carry it. The canonical question is: *does a spec exist and is the contract clear?* If yes, the item belongs in the build room.

In `workspace.toml`, the build room is the `["ini-NNN".work]` section with three lists:

| List | What it means |
|------|--------------|
| `queue` | Ready to start, or waiting on a `needs` dependency |
| `active` | Currently being built in this session |
| `shipped` | Implemented — moved here on PR merge |

Items move through the lists by list membership: an entry in `queue` is ready, in `active` is in-flight, in `shipped` is done. There is no per-entry status field — list position is the lifecycle.

## Why the separation matters

Mixing shaping and building in one queue causes two kinds of harm:

1. **False readiness** — an item looks ready to build but turns out to need research or framing mid-implementation. The session has to stop, do discovery work, and restart — paying the cost of a context-switch mid-build.
2. **Blocked builds** — a build queue full of items-that-are-really-shape-work blocks the real build items. Nothing ships because nothing is actually ready.

Separating the rooms makes the distinction explicit at capture time, before work starts, rather than at implementation time, when the surprise is most expensive.

## How items move between rooms

The path is one-way:

1. A new item arrives — a user surfaces it mid-session, a spec reveals a follow-on, a review finds a gap. The `capture-work` skill classifies it as `[build]` or `[shape]` and writes it to the right room.
2. Shape items are worked until a spec can be written. The spec lands in `docs/specs/<slug>/`.
3. The spec's path enters the build room's `queue`.
4. `work-loop` builds the spec. On PR merge, the entry moves to `shipped`.

A `signal` item never follows this path — it stays in the shape room as persistent context.

## How `workspace-status` surfaces both rooms

Running `workspace-status` at session start surfaces both rooms in a single orientation pass:

- The **shape room** appears as shaping items in `active`, each with a suggested skill command.
- The **build room** appears as ready-to-start items (unblocked, not in `shipped`) and active items.
- **Signals** appear as active context without a suggested action — they inform decisions without requiring one.

Read the orientation output to understand the full state of both rooms before picking up any work.

## See also

- [How to orient at the start of a session](../how-to/orient-at-session-start.md) — read both rooms at session start
- [How to capture and triage a work item](../how-to/capture-work.md) — route a new item to the right room
- [workspace.toml schema reference](../reference/workspace-toml-schema.md) — authoritative field and section descriptions

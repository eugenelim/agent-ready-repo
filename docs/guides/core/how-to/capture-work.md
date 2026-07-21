# How to capture and triage a work item

Mid-session, you notice something that should be tracked: a follow-on from a spec, a bug, an idea, or an item a spec marked as deferred. This guide walks through using `capture-work` to classify the item and write it to the right room in `workspace.toml`.

For *why* items route to either the shape room or the build room, see [The two-room model](../explanation/two-room-model.md). For the `workspace.toml` sections that `capture-work` writes to, see [workspace.toml schema reference](../reference/workspace-toml-schema.md).

## When to use this guide

Use `capture-work` any time you surface a new item during a session:

- A spec's `(deferred: <slug>)` marker identifies something cut from the current PR.
- You notice a bug or gap that is out of scope for the current spec.
- A review finding surfaces a follow-on that should not block the current PR.
- You have an idea worth tracking but not yet ready to build.

`capture-work` handles classification — you describe the item in plain language and the skill routes it.

## Step 1 — Invoke `capture-work`

At any point during a session:

```
capture-work
```

The skill prompts you to describe the item. You can also describe it inline:

```
capture-work: the retry logic should handle transient network failures
```

## Step 2 — Describe the item in plain language

State what the item is and why it matters. Do not pre-classify it — the skill does the routing. Examples:

- "The payment-retry spec deferred idempotent replay. It should be a follow-on spec."
- "The API timeout is hardcoded; it should be configurable."
- "We need to track competitor pricing weekly — it is context for the roadmap."

The skill uses your description to classify the item as `[build]` (ready to implement) or `[shape]` (needs research, framing, or strategy first), and picks a subtype if it is a shape item.

## Step 3 — Review the proposed routing

The skill surfaces its classification:

- **`[build]`** — the item is shaped enough to go directly to the build room as a spec path in `["ini-NNN".work].queue`.
- **`[shape] (subtype)`** — the item needs shaping first; it goes to the shape room. Subtypes and their skills:
  - `shape` → `frame-intent`
  - `research` → `desk-research-project-start`
  - `strategy` → `frame-situation`
  - `signal` → stays in `[shaping_queue].active` as ongoing monitoring context (no skill action)
  - `design` → `experience-status`

The skill shows you the proposed routing and the target list before writing anything.

## Step 4 — Confirm or redirect

Read the proposed routing. If the classification matches what you intended, confirm.

If the item is misclassified — for example, routed to the shape room when it is clearly a build item — tell the skill how to reclassify before it writes.

## Step 5 — Verify the entry in `workspace.toml`

After confirmation, the skill writes the entry to `workspace.toml`. Verify:

- For a **build item** scoped to the active initiative: the path appears in `["ini-NNN".work].queue`.
- For a **deferred acceptance criterion** (a `(deferred: <slug>)` marker from a spec): the entry appears in `[backlog].open` with `source = "spec/<name> ACn"` — even when an initiative is active. Deferred items carry provenance back to the spec that cut them.
- For a **repo-level build item** not scaled to an initiative (too small or too cross-cutting to own a spec in `[work].queue`): the entry appears in `[backlog].open` without a `source`.
- For a **shape item**: the entry appears in `["ini-NNN".shaping_queue].backlog` (or `[backlog].open` with a `type` field). Exception: `signal`-subtype items land in `.active`, not `.backlog` — they are persistent monitoring context, not a queue entry waiting to be worked.

The entry is written with a `# comment` above it describing the item for future sessions.

## Step 6 — Handle the shaping hand-off (shape items only)

After writing a shape item, the skill checks whether the matching shaping skill is installed and offers to start shaping immediately. If you want to continue current work and shape later, decline — the entry is in `workspace.toml` and will surface in the next `workspace-status` run.

## Related

- [The two-room model](../explanation/two-room-model.md) — why items route to two different rooms
- [How to orient at the start of a session](orient-at-session-start.md) — where all captured items appear after a session
- [workspace.toml schema reference](../reference/workspace-toml-schema.md) — the sections `capture-work` writes to

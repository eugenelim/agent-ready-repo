---
name: queue-add
description: Use this skill when a session has surfaced a list of future work — follow-ons, review recommendations, audit remediation items, deferred scope — and you want to capture it into workspace.toml so a later session can pick it up cold. Triggers on "add these to the queue", "capture these as queue items", "queue these up", "add this to the backlog" + a bulleted or numbered list in context. Do NOT use to turn unstructured external input into a product brief (use author-brief), to decompose a brief into specs (use receive-brief), or to orient at session start (use workspace-status).
---

# Skill: queue-add

Bridge work surfaced in the current session into `workspace.toml` so it is not
lost when the session ends. Given a bulleted or numbered list, `queue-add`
derives spec paths, infers real dependencies, prioritizes and groups the items,
and appends them to the right queue — each entry carrying a comment rich enough
that a cold-start session can write the full spec without revisiting this one.

`queue-add` writes `workspace.toml` only. It never creates spec files, and it
never invents a dependency. The user reviews the complete proposed change before
anything is written.

## When to invoke

- A session produced a list of "things we should do later" — deferrals,
  follow-ons, recommendations, remediation items — and you want them queued.
- The items are concrete enough to name, even if not yet fully shaped.

If the input is unstructured external prose that needs shaping into a product
brief, use `author-brief`. If it is an already-written brief to decompose into
specs, use `receive-brief`. If you just want to see what is already queued, use
`workspace-status`.

## The two homes this skill writes to

`queue-add` appends only to the two destinations it owns. For anything else it
*suggests* the right home and defers the write to the owning skill.

1. **An active initiative's `[work].queue`** — well-shaped, ready work scoped to
   an active initiative. If more than one initiative is `active`, ask which one;
   never guess.
2. **The repo-level `[backlog].open`** — well-shaped, ready work that is not
   initiative-scale. This is the home for the common ad-hoc case (e.g. items
   from an audit that belong to no active initiative). A **deferred acceptance
   criterion** of an existing spec also appends here, carrying a
   `source = "spec/<name> ACn"` key. `[backlog]` is a top-level, repo-durable
   section; if it does not exist yet, create it.

## Procedure

### 1. Ingest

Take the bulleted or numbered list from context, or from what the user pastes.
Do not reject partial or messy input.

### 2. Derive slugs

For each item, propose a kebab-case `spec/<slug>` derived from the item text.
Check for collisions: if a spec directory with that slug already exists, or the
slug is already present in a `queue`, `active`, or `[backlog].open` list, stop
and ask before proceeding — never overwrite.

### 3. Infer dependencies

Read the list for **explicit** sequencing language ("after X", "depends on Y",
"once Z ships", "then"). Add a `needs` edge only where the language is explicit,
using queue-prefix notation (`"work:spec/<slug>"`, `"backlog:<slug>"`). Items
the list does not sequence are independent — give them no `needs`.

**Never encode a priority *preference* as a `needs`.** A `needs` is a hard "cannot
start until" dependency. A preference about what to do first is queue order plus
a comment, not a dependency — a spurious `needs` would falsely serialize work
that could otherwise run in parallel.

### 4. Route

Decide the destination per item or batch:

- Scoped to exactly one active initiative → that initiative's `[work].queue`.
- Scoped to more than one active initiative → ask which one.
- Well-shaped and ready but not initiative-scale → repo-level `[backlog].open`.
- Fits neither cleanly → run the **escalation rubric** below and *suggest* the
  right home rather than writing.

### 5. Prioritize

Two axes, never conflated:

- **Sequence** (`needs`) — hard dependency, from step 3.
- **Priority** — among items that are all ready, which to prefer first. This is
  advisory: it is expressed as **queue order plus a one-line rationale in the
  comment**, never as a schema field and never as a `needs`.

When two or more items are mutually independent and their order is a real call,
elicit priority from the user. Offer a ranking rubric as a prompt (for example
RICE, value-vs-effort, or the user's own decision matrix) — do not impose one,
and do not write a numeric score. Skip elicitation when dependencies already
determine the order or only one item is added.

### 6. Group

Pick the grouping shape by how tightly the items are coupled:

- **Independent batch** (default) — separable items land as flat entries under a
  single labeled comment header (e.g. `# Session audit YYYY-MM-DD — remediation
  batch`). Each stays its own entry so it can be picked up, sequenced, or
  parallelized alone. Annotate any parallel-safe set in the comment as advisory
  guidance ("items 2–4 are parallel-safe; do 1 first").
- **Atomic bundle** — when two or more items **must ship together** because
  splitting them leaves a broken intermediate state (the load-bearing case: a
  shared hard gate, where doing one without the other breaks a check), record
  them as a **single queue entry** whose comment enumerates the coupled parts
  *and* the coupling hazard. This is stronger than `needs`: `needs` orders two
  separately shippable items; an atomic bundle says there is no valid state
  between them. The tell is coupling language ("must ship together", "can't
  split", "would break if separate"). Confirm the bundling with the user.
- **Shaped work unit** — when the batch coheres as one outcome with a plausible
  appetite and an initiative fits, *suggest* `author-brief` instead of flat
  entries; the brief becomes the group container.

### 7. Compose comments

Each appended entry carries a comment block sufficient for a cold-start session
to write the full spec: **the problem, the fix, the affected file or skill, and
any key decisions already taken.** One-liners are not enough — write what a fresh
session would otherwise have to reconstruct.

### 8. Confirm

Present the complete proposed change — entries, comments, order, inferred
`needs`, and any escalation suggestions — and wait for the user to approve before
writing.

### 9. Write

Edit `workspace.toml` with a **comment-preserving** write — targeted text
insertion, or `tomlkit`. Never a full `tomllib` + `tomli_w` round-trip: it strips
every comment in the file, and the comments are the whole point.

- Append entries to the resolved `[work].queue` or `[backlog].open`.
- If routing to `[backlog]` and the section does not exist, create it as a
  top-level `[backlog]` table with an `open` list and the standard header
  comment.
- Stage the file.

Degrade gracefully: if `workspace.toml` is absent, unparseable, or has no
matching queue, do not throw. Emit a diagnostic naming the derived entries and
how to add them by hand, and stop.

### 10. Hand off

Tell the user the items are queued and that `workspace-status` will surface them
at the next session start.

## Escalation rubric

When an item does not cleanly fit `[work].queue` or `[backlog]`, suggest the
right home. The spine is one question: *is it shaped enough to become a spec
now, and at what scale?*

| Item shape | Suggest |
| --- | --- |
| Cluster of related features, one outcome + appetite, under an initiative | `author-brief` (brief queue) |
| Needs shaping, research, or strategy before it is a spec | a `shaping_queue` entry of the matching type |
| Big future feature, not yet shaped or scheduled | a row in `roadmap-intents.md` |
| Cross-cutting design question to work through | a row in `rfc-candidates.md` |
| Cross-cutting proposal needing a decision | `new-rfc` |
| Sustained, multi-quarter effort | standing up a new initiative (never auto-create) |

## Anti-patterns to refuse

- **Creating spec files.** This skill writes `workspace.toml` only.
- **Inventing a dependency.** Add `needs` only from explicit sequencing language.
- **Encoding a priority preference as a `needs`.** Preference is order + comment.
- **Writing a numeric priority or a new schema field.** Priority is order +
  comment; the schema is not extended.
- **A full `tomllib` round-trip** that strips the file's comments.
- **One-liner comments** that a cold-start session cannot act on.
- **Overwriting** an existing spec directory or queue entry — prompt on collision.
- **Guessing the initiative** when more than one is active — ask.
- **Force-fitting** an item into an ill-matching initiative, or auto-creating an
  initiative or brief — suggest instead.
- **Blocking on a missing `workspace.toml`.** Degrade to the named diagnostic.

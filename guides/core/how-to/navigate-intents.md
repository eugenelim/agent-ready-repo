---
title: How to navigate intents, briefs, and specs
summary: Query the intent graph to find outstanding work, trace parents, and walk the hierarchy without opening files one by one, or export it as one offline HTML page.
pack: core
kind: how-to
---

# How to navigate intents, briefs, and specs

Find outstanding work, trace where an intent sits, and share the whole graph as one offline page, without opening files one by one. An intent is a short file that states an outcome you want and why; briefs and specs sit beneath intents. You need the `core` pack and an agent session open in the repository root.

## Find outstanding work

Ask for the open work under one intent:

```text
Show me the outstanding work under capability:work-item-capture-and-disposition.
```

The agent runs the navigator's `outstanding` query and prints each open item under its parent:

```text
(no parent)
  capability:work-item-capture-and-disposition · capability · Accepted
    opportunity:duplicate-coverage-check · feature · opportunity · Accepted
      spec:duplicate-coverage-offer · Draft
    opportunity:governance-item-record-routing · feature · opportunity · Accepted
      spec:governance-item-record-routing · Draft
```

This output is trimmed. The capability prints under `(no parent)` because it has no parent intent of its own.

## Trace where an intent sits

Ask for the parents and the work placed under one intent:

```text
Show me the parents of intent:my-slug and the briefs and specs placed under it.
```

The agent runs the `ancestors` and `record` queries and returns the chain up to a root, the intent's recorded fields, and the briefs and specs placed under it.

## Count live intents

Ask for the overall picture:

```text
How many live intents do we have, by level?
```

The agent runs the `summary` query and returns counts by level and kind, plus the briefs, specs, outstanding items, and refused links. A live intent is an intent file without a `Tombstone:` field.

## Export an offline view

Ask for one page you can open without a terminal:

```text
Export the intent graph as an offline HTML page.
```

The agent runs `export` and prints the path of one HTML file in your system's temporary directory. Open it in a browser; it needs no network. The export never writes inside your repository.

### Show what is ready to work on

To mark what `work-loop` says is ready, ask the agent to pipe the argless dispatch output into the export. It runs:

```bash
python3 '<work-loop-skill-dir>/scripts/dispatch.py' --root <repo-root> \
  | python3 <skill-dir>/scripts/navigate_intents.py export --root <repo-root> --readiness -
```

Use the same `<repo-root>` on both sides, and pipe only argless `dispatch.py --root` output. The export never runs `dispatch.py`; it reads only what you pipe in. [Readiness input](../reference/navigate-intents-queries.md#readiness-input) lists what the page shows and when readiness cannot be checked.

## What this job does not do

The navigator only reads. For what is ready to start, ask `work-loop` to run `dispatch.py` ([Orient at the start of a session](orient-at-session-start.md) shows how). For workspace repair, use `workspace-status`. This skill never reads `workspace.toml`.

Next, [look up every operation, option, and refusal code](../reference/navigate-intents-queries.md).

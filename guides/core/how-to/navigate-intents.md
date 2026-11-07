---
title: How to navigate intents, briefs, and specs
summary: Query the intent graph to find outstanding work, trace parents, and walk the hierarchy without opening files one by one, or export it as one offline HTML page.
pack: core
kind: how-to
---

# How to navigate intents, briefs, and specs

Find outstanding work, walk the intent hierarchy, trace where an intent sits, and share the graph as one offline page, using the `navigate-intents` skill. An intent is a short file that states an outcome you want and why; briefs and specs sit beneath intents. You need the `core` pack and an agent session in the repository root.

## Find outstanding work

Ask for the open work under one intent:

```text
Show me the outstanding work under capability:work-item-capture-and-disposition.
```

The agent runs the skill's `outstanding` query, with `--operation outstanding --format text --from capability:work-item-capture-and-disposition`, and prints each open item under its parent:

```text
(no parent)
  capability:work-item-capture-and-disposition · capability · Accepted
    opportunity:duplicate-coverage-check · feature · opportunity · Accepted
      spec:duplicate-coverage-offer · Draft
    opportunity:governance-item-record-routing · feature · opportunity · Accepted
      spec:governance-item-record-routing · Draft
```

This output is trimmed. The capability prints under `(no parent)` because it has no parent intent of its own.

## Walk the hierarchy

Ask for the tree under one intent:

```text
Show me the intent tree under capability:work-item-capture-and-disposition, one level deep.
```

The agent runs the `tree` query with `--depth 1` and prints each intent with its level, kind, and status.

## Trace where an intent sits

Ask for the parents and the work placed under one intent:

```text
Show me the parents of intent:my-slug and the briefs and specs placed under it.
```

The agent runs the `ancestors` and `record` queries and returns the chain up to a root, then the intent's recorded fields, its children, and the briefs and specs placed under it with their delivery links.

## Summarize the graph

Ask for the overall picture:

```text
Summarize the intent graph: how many live intents are there at each level?
```

The agent runs `summary` and returns counts of live intents by level and kind, briefs and specs, outstanding items, refused edges by state, and parentless intents. A live intent is an intent file without a `Tombstone:` field.

## Export an offline view

Ask for one page you can open without a terminal:

```text
Export the intent graph as an offline HTML page.
```

The agent runs `export` and prints the path of one HTML file in your system's temporary directory. Open it in a browser; it needs no network. The export never writes inside your repository.

### Show what is ready to work on

To mark what `work-loop` says is ready, ask the agent to pipe the argless dispatch output into the export. It runs the command below, where `<skill-dir>` is the installed `navigate-intents` skill folder, `<work-loop-skill-dir>` is the installed `work-loop` skill folder, and `<repo-root>` is your repository root:

```bash
python3 '<work-loop-skill-dir>/scripts/dispatch.py' --root <repo-root> \
  | python3 <skill-dir>/scripts/navigate_intents.py export --root <repo-root> --readiness -
```

Use the same `<repo-root>` on both sides, and pipe only argless `dispatch.py --root` output. The export never runs `dispatch.py`; it reads only what you pipe in. [Readiness input](../reference/navigate-intents-queries.md#readiness-input) lists what the page shows and when readiness cannot be checked.

## What this job does not do

The skill only reads. For what is ready to start, ask `work-loop` to run `dispatch.py` ([Orient at the start of a session](orient-at-session-start.md) shows how). For workspace repair, use `workspace-status`. The skill never reads `workspace.toml`.

Next, [look up every operation, option, and refusal code](../reference/navigate-intents-queries.md).

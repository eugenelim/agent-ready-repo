---
title: How to navigate intents, briefs, and specs
summary: Query the intent graph to find outstanding work, trace parents, and walk the hierarchy without opening files one by one.
pack: core
kind: how-to
---

# How to navigate intents, briefs, and specs

**Use this when:** You want to see outstanding work, walk the intent hierarchy, trace the parent of an intent, or get a count of live intents by level.
**Prerequisites:** `core` pack installed; a terminal or agent session open in the repo root.
**Result:** A list of outstanding artifacts placed under their parent, a tree of intents, or a focused view of one intent's record and delivery links.

Ask the agent to look up intents:

```text
Show me the outstanding work under capability:work-item-capture-and-disposition.
```

or run the bundled query script directly from the skill directory:

```bash
python3 <skill-dir>/scripts/navigate_intents.py query \
  --root <repo-root> \
  --operation outstanding \
  --format text \
  --from capability:work-item-capture-and-disposition
```

```text
capability:work-item-capture-and-disposition · capability · Accepted
  opportunity:duplicate-coverage-check · feature · opportunity · Accepted
    spec:duplicate-coverage-offer · Draft
  opportunity:governance-item-record-routing · feature · opportunity · Accepted
    spec:governance-item-record-routing · Draft
```

For queue order and workspace repair, use `workspace-status` instead. This skill never reads `workspace.toml`.

## Query operations

The skill exposes six operations, each described below.

### summary

Returns counts of live intents by level and kind, of briefs and specs, of outstanding items, of refused edges by state, and of parentless intents. Use it for a quick view of the repository's intent landscape before diving into a specific node.

```bash
python3 scripts/navigate_intents.py query --root <repo> --operation summary
```

### record

Returns all recorded fields for one intent: its node id, path, `Level:`, `Kind:`, and exact `Status:`; its resolved or refused parent edge; its child intents; the briefs and specs placed under it; and its delivery-resolver relations.

```bash
python3 scripts/navigate_intents.py query --root <repo> \
  --operation record --id capability:my-slug
```

### tree

Prints the full intent forest as an indented tree. Each line shows the node id, level, optional kind, and recorded status. Add `--depth <n>` to limit how deep the traversal goes; without it you get the whole forest.

```bash
python3 scripts/navigate_intents.py query --root <repo> \
  --operation tree --format text --depth 1
```

```text
capability:work-item-capture-and-disposition · capability · Accepted
  opportunity:duplicate-coverage-check · feature · opportunity · Accepted
```

### ancestors

Returns the ordered chain of resolved parents from a given intent to its root, nearest first. Useful for tracing where an intent sits in the hierarchy.

```bash
python3 scripts/navigate_intents.py query --root <repo> \
  --operation ancestors --id capability:my-slug
```

### search

Filters live intents by level, kind, exact status, parentless status, or a text match on slug or first heading. Pass selectors as a JSON array; an unknown key returns an error instead of silently ignoring it.

```bash
python3 scripts/navigate_intents.py query --root <repo> \
  --operation search \
  --selectors '[{"level": "capability"}, {"exact_status": "Accepted"}]'
```

### outstanding

Returns every intent, brief, and spec whose recorded `Status:` is not terminal, placed under its parent intent. Items with no resolved parent appear at the end in a `(no parent)` group. This operation refuses to return a partial list: if any file the derivation reads fails validation, the whole operation fails.

```bash
# All outstanding work:
python3 scripts/navigate_intents.py query --root <repo> --operation outstanding

# Outstanding work under one intent only:
python3 scripts/navigate_intents.py query --root <repo> \
  --operation outstanding --from capability:my-slug \
  --format text
```

## Tree format

`--format text` prints one line per artifact at its depth in the tree. Two spaces indent each level:

```text
capability:work-item-capture-and-disposition · capability · Accepted
  opportunity:duplicate-coverage-check · feature · opportunity · Accepted
    spec:duplicate-coverage-offer · Draft
```

Each intent line reads: `node-id · level · kind (when present) · status`. A refused parent edge prints one level deeper as `! refused <state>`.

`--format json` (the default) returns a structured JSON envelope with a `schema` field, the echoed query, provenance counts, and the operation's result fields.

## Identities

`record`, `tree`, `ancestors`, and `outstanding --from` accept an identity in three forms:

| Form | Example |
|------|---------|
| Node id | `capability:my-slug`, `intent:my-slug`, `outcome:my-slug` |
| Bare intent slug | `my-slug` |
| Filename ordinal | `FEAT-0029` |

An identity that matches no live intent returns `not_found`. An ordinal that matches more than one file returns `ambiguous_identity`.

## Read-only boundary

This skill never writes to the repository. Every answer is derived from preamble headers at the moment it is asked; nothing is cached or stored. Symlinks, hard links, special files, and paths outside the repository root are refused before any content is read. The `boundary` field in every JSON response states this explicitly.

Results are candidate context derived at query time, not authoritative policy. The `provenance.generated_at` field is the only non-deterministic value; results are otherwise byte-identical across runs once it is removed.

## Related

- [Orient at the start of a session](orient-at-session-start.md) — read queue state and pick a next action with `workspace-status`

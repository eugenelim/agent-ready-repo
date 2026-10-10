---
title: How to navigate intents, briefs, and specs
summary: Query the intent graph to find outstanding work, trace parents, and walk the hierarchy without opening files one by one.
pack: core
kind: how-to
---

# How to navigate intents, briefs, and specs

**Use this when:** You want to see outstanding work, walk the intent hierarchy, trace the parent of an intent, or get a count of live intents (intent files without a `Tombstone:` field) by level.
**Prerequisites:** `core` pack installed; a terminal or agent session open in the repo root.
**Result:** A list of outstanding artifacts placed under their parent, a tree of intents, or a focused view of one intent's record and delivery links.

`<skill-dir>` is the installed skill directory — for example, `.agents/skills/navigate-intents` for most adapters, or `.claude/skills/navigate-intents` for Claude Code. Replace `<repo-root>` with your repository root.

Ask the agent to look up intents:

```text
Show me the outstanding work under capability:work-item-capture-and-disposition.
```

or run the bundled query script directly:

```bash
python3 <skill-dir>/scripts/navigate_intents.py query \
  --root <repo-root> \
  --operation outstanding \
  --format text \
  --from capability:work-item-capture-and-disposition
```

```text
(no parent)
  capability:work-item-capture-and-disposition · capability · Accepted
    opportunity:duplicate-coverage-check · feature · opportunity · Accepted
      spec:duplicate-coverage-offer · Draft
    opportunity:governance-item-record-routing · feature · opportunity · Accepted
      spec:governance-item-record-routing · Draft
```

This output is trimmed. The capability prints under `(no parent)` because it has no parent intent of its own.

For queue order and workspace repair, use `workspace-status` instead. This skill never reads `workspace.toml`.

## Query operations

The skill exposes six operations, each described below.

### summary

Returns counts of live intents by level and kind, of briefs and specs, of outstanding items, of refused edges (parent or pointer links that could not be resolved) by state, and of parentless intents. Use it for a quick view of the intent graph (the network of intents, briefs, and specs linked by their pointer fields) before diving into a specific node.

```bash
python3 <skill-dir>/scripts/navigate_intents.py query \
  --root <repo-root> --operation summary
```

### record

Returns all recorded fields for one intent: its node id, path, `Level:`, `Kind:`, and exact `Status:`; its resolved or refused parent edge; its child intents; the briefs and specs placed under it; and the delivery resolver's (the component that matches briefs and specs to their covering intents) relations and diagnostics for it.

```bash
python3 <skill-dir>/scripts/navigate_intents.py query --root <repo-root> \
  --operation record --id capability:my-slug
```

### tree

Prints the full intent forest as an indented tree. Each line shows the node id, level, optional kind, and recorded status. Add `--depth <n>` to limit how deep the traversal goes; without it you get the whole forest.

```bash
python3 <skill-dir>/scripts/navigate_intents.py query --root <repo-root> \
  --operation tree --format text --depth 1
```

```text
capability:work-item-capture-and-disposition · capability · Accepted
  opportunity:duplicate-coverage-check · feature · opportunity · Accepted
```

To see one intent and its direct children:

```bash
python3 <skill-dir>/scripts/navigate_intents.py query --root <repo-root> \
  --operation tree --id capability:my-slug --depth 1 --format text
```

### ancestors

Returns the ordered chain of resolved parents from a given intent to its root, nearest first. Useful for tracing where an intent sits in the hierarchy.

```bash
python3 <skill-dir>/scripts/navigate_intents.py query --root <repo-root> \
  --operation ancestors --id capability:my-slug
```

### search

Filters live intents by level, kind, exact status, parentless status, or a text match. Pass selectors as a JSON object with one or more of the keys `level`, `kind`, `exact_status`, `parentless`, and `text`. The `text` selector matches the slug or the first `# ` heading, case-insensitively. An unknown key returns an error instead of silently ignoring it. If the result is too large, add selectors to narrow it.

```bash
python3 <skill-dir>/scripts/navigate_intents.py query --root <repo-root> \
  --operation search \
  --selectors '{"level": "capability", "exact_status": "Accepted"}'
```

### outstanding

`outstanding` returns every intent, brief, and spec in a non-terminal state. A terminal state (such as Fulfilled or Archived) means the work is done. An item is outstanding when its leading status word is not terminal.

Each item is placed under its parent intent. Items with no resolved parent appear at the end in a `(no parent)` group. Each item carries its ancestor chain up to a root. A terminal ancestor is included in the chain and marked `terminal`. Each spec placement names the pointer field (`Brief:` or `Discovery:`) and, where the delivery resolver found one, the relation type. A spec placed by both `Brief:` and `Discovery:` appears under both its parent brief and its parent intent.

In text output, a terminal ancestor that places an outstanding item prints as a context line ending `· (terminal ancestor)`. That line is not itself outstanding.

An empty result prints no text in text format, or empty arrays in JSON format. Exit code is 0 in both cases. This operation refuses a partial list: if any file the derivation reads fails validation, the whole operation fails.

```bash
# All outstanding work:
python3 <skill-dir>/scripts/navigate_intents.py query \
  --root <repo-root> --operation outstanding

# Outstanding work under one intent only:
python3 <skill-dir>/scripts/navigate_intents.py query --root <repo-root> \
  --operation outstanding --from capability:my-slug \
  --format text
```

## Text output

Only `tree` and `outstanding` support `--format text`. The other operations (`summary`, `record`, `ancestors`, `search`) always return JSON regardless of the flag.

`--format text` prints one line per artifact at its depth in the tree. Two spaces indent each level. This is `tree --id capability:work-item-capture-and-disposition --depth 1 --format text`, trimmed:

```text
capability:work-item-capture-and-disposition · capability · Accepted
  opportunity:duplicate-coverage-check · feature · opportunity · Accepted
  opportunity:governance-item-record-routing · feature · opportunity · Accepted
```

`tree` prints intents only. `outstanding` also prints the briefs and specs placed under them, as in the first example on this page.

Each intent line reads: `node-id · level · kind (when present) · status`. A brief or spec line reads: `node-id · status`. A refused parent edge prints one level deeper as `! refused <state>`.

`--format json` (the default) returns a structured JSON envelope with a `schema` field, the echoed query, provenance counts, and the operation's result fields.

## Identities

Use `--id` for `record`, `tree`, and `ancestors`; use `--from` for `outstanding`. Each accepts an identity in three forms:

| Form | Example |
|------|---------|
| Node id | `capability:my-slug`, `intent:my-slug`, `outcome:my-slug`, `opportunity:my-slug` |
| Bare intent slug | `my-slug` |
| Filename ordinal (the order code in the filename) | `FEAT-0029` |

The prefix of a node id is `outcome:` or `opportunity:` when `Kind:` names that rung. Otherwise it is `capability:` when `Level:` is `capability`, and `intent:` for everything else. An identity that matches no live intent returns `not_found`. An ordinal that matches more than one file returns `ambiguous_identity`.

## Refused edges

A refused edge is a parent or pointer link that could not be resolved. Each carries one of these states:

| State | What it means | Edit to clear it |
|-------|---------------|------------------|
| `dangling` | The pointer names a slug or path with no matching live intent. | Correct the slug, or create the target. |
| `retired_target` | The target has a `Tombstone:` field. | Update the pointer to the replacement in `Reissued as:`, or remove it. |
| `kind_mismatch` | The typed prefix (e.g. `outcome:`) does not match the target's actual node id. | Change the prefix to match the target. |
| `out_of_type` | The pointer names the wrong artifact type (e.g. a spec where an intent is expected). | Point to the correct file. |
| `multiple_values` | The pointer field appears more than once with conflicting values. | Keep exactly one value. |
| `cycle` | Following this parent edge would circle back to this intent. | Remove the pointer that closes the loop. |
| `unparseable` | The pointer uses an unrecognised form (e.g. an absolute path). | Rewrite it as a typed id, bare slug, or relative path. |

A refused edge leaves every other node and edge in the result; the rest of the tree is still shown.

## When a query is refused

A refused query returns `status: error` with exit code 1 and an `error` object containing `code`, `message`, `limits`, and `observed`. A command the argument parser rejects, such as an unknown or malformed flag, exits 2 with no JSON envelope.

**Large result:** `result_too_large` means the result exceeds the size limit. For `tree`, add or lower `--depth`. For `outstanding`, add `--from` to limit to one intent. The flag to use is named in `error.limits.bounded_route`. `search` and `ancestors` refuse with the exceeded limit but do not name a bounded route. Add selectors to narrow a `search`. An oversized `ancestors` chain has no narrowing flag.

**Broken file:** `unsafe_input`, `input_too_large`, `malformed_record`, and `duplicate_identity` name the file that must be repaired in `error.message`. An `unsafe_input` whose message is "the intent graph could not be derived" names no file: the navigator itself failed, so reinstall the skill.

**Delivery incomplete:** `delivery_incomplete` names no file. Read `error.observed.reason`. `resource_limit` means the delivery resolver hit the limit named in `error.observed.limit`; `unsafe` means it refused part of the corpus. Fix what the resolver reports, then run again.

**Missing helpers:** `resolver_unavailable` means the skill's bundled helpers are absent. Reinstall the skill.

**Wrong arguments:** `not_found`, `ambiguous_identity`, `invalid_selector`, `invalid_depth`, `invalid_query`, `missing_operation`, and `unknown_operation` mean the command arguments do not match any live intent or valid operation. Correct them and run again.

## Read-only boundary

This skill never writes to the repository. Every answer is derived from preamble headers (the `Status:`, `Level:`, and other fields at the top of each intent file) at the moment it is asked; nothing is cached or stored. Symlinks, hard links, special files, and paths outside the repository root are refused before any content is read. The `boundary` field in every JSON response states this explicitly.

Results are candidate context derived at query time, not authoritative policy. The `provenance.generated_at` field is the only non-deterministic value; results are otherwise byte-identical across runs once it is removed.

## Related

- [Orient at the start of a session](orient-at-session-start.md) — read queue state and pick a next action with `workspace-status`

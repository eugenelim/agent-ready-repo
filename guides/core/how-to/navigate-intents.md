---
title: How to navigate intents, briefs, and specs
summary: Query the intent graph to find outstanding work, trace parents, and walk the hierarchy without opening files one by one, or export it as one offline HTML page.
pack: core
kind: how-to
---

# How to navigate intents, briefs, and specs

**Use this when:** You want to see outstanding work, walk the intent hierarchy, trace the parent of an intent, get a count of live intents (intent files without a `Tombstone:` field) by level, or hand a reviewer an offline page of the whole graph.
**Prerequisites:** `core` pack installed; a terminal or agent session open in the repo root; Git 2.44 or later for commit-pinned source links in the HTML export (older Git still exports, and every GitHub link is marked "may be newer than this export").
**Result:** A list of outstanding artifacts placed under their parent, a tree of intents, a focused view of one intent's record and delivery links, or one HTML file that shows all of it offline.

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

For a page you can open offline or send to a reviewer, see [Export an offline view](#export-an-offline-view).

## Query operations

The skill exposes seven query operations, each described below. An eighth command, `export`, is described in [Export an offline view](#export-an-offline-view).

### summary

Returns counts of live intents by level and kind, of briefs and specs, of outstanding items, of refused edges (parent or pointer links that could not be resolved) by state, and of parentless intents. Use it for a quick view of the intent graph (the network of intents, briefs, and specs linked by their pointer fields) before diving into a specific node.

```bash
python3 <skill-dir>/scripts/navigate_intents.py query \
  --root <repo-root> --operation summary
```

### record

Returns all recorded fields for one intent: its node id, path, `Level:`, `Kind:`, and exact `Status:`; its resolved or refused parent edge; its child intents; the related intents it writes (`related_written_here`) and the intents that write it as related (`related_written_elsewhere`); the briefs and specs placed under it; and the delivery resolver's (the component that matches briefs and specs to their covering intents) relations and diagnostics for it.

```bash
python3 <skill-dir>/scripts/navigate_intents.py query --root <repo-root> \
  --operation record --id capability:my-slug
```

### tree

Prints the full intent forest as an indented tree. Each line shows the node id, level, optional kind, and recorded status. Each intent entry in the JSON also carries its two related lists, `related_written_here` and `related_written_elsewhere`. Add `--depth <n>` to limit how deep the traversal goes; without it you get the whole forest.

```bash
python3 <skill-dir>/scripts/navigate_intents.py query --root <repo-root> \
  --operation tree --format text --depth 1
```

```text
capability:work-item-capture-and-disposition · capability · Accepted
  opportunity:duplicate-coverage-check · feature · opportunity · Accepted
```

This output is trimmed.

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

### dependencies

Ask which intents an intent depends on, or which depend on it. Run `query --operation dependencies --id <identity> --direction prerequisites --depth 2 --format text`, or open the offline view, pick an intent and use its **Dependencies** part. Each line reads "A waits for B": A's `Depends on:` header names B.

```bash
python3 <skill-dir>/scripts/navigate_intents.py query \
  --root <repo-root> --operation dependencies \
  --id intent:alpha --direction both --depth 2 --format text
```

```text
dependencies of intent:alpha · direction both · depth 2
scope: Reads the Depends on: headers of live intents only. Workspace dependencies are not read, and nothing here decides whether work can start.
intents:
  intent:alpha
  intent:bravo
  intent:charlie
edges (waiting -> prerequisite):
  intent:alpha -> intent:bravo
  intent:bravo -> intent:charlie
diagnostics:
  intent:alpha · outside_scope · spec:some-spec
```

This output comes from a small example set of intents. `--direction` is `prerequisites` (the default), `dependents`, or `both`. `--depth` counts steps from the start and defaults to 1; `0` returns the start alone. `--id` takes the identities in [Identities](#identities).

The view reads `Depends on:` headers, accepting typed references (`intent:`, `capability:`, `outcome:`, `opportunity:` and a slug) and legacy repository paths to intent files. It does not include workspace-only dependencies or decide whether work may start. Check the listed problems before relying on a dependency chain. A problem is a value that is dangling, retired, a wrong kind, unparseable or outside the scope (such as a brief or spec), or a cycle among intents. Only `--format text` and JSON are offered; `result_too_large` means lower `--depth`.

## Export an offline view

`export` writes the whole intent graph to one HTML file that opens in any browser with no network. Use it to share the graph with a reviewer, or to browse it without a terminal. The `query` operations above only read; `export` also writes one file, always outside your repository.

```bash
python3 <skill-dir>/scripts/navigate_intents.py export --root <repo-root>
```

The command prints one JSON object. On success it carries `status: ok`, `path` (the file's absolute path), `bytes`, and `scope`; open `path` in a browser. Without `--destination` the file goes to your system's temporary directory, named `intent-graph-<UTC time as YYYYMMDDTHHMMSSZ>.html`.

| Flag | Meaning |
|------|---------|
| `--destination <dir>` | An existing directory outside the repository. |
| `--name <file>` | One name made of letters, digits, `.`, `_`, and `-`, ending in `.html`, at most 100 characters before the suffix. |
| `--from <identity>` | Only the subtree under one intent. Takes the same identities as `query --from`. The export also carries the dependency records of intents linked to that subtree, and names those outside it by id. |

### What the file contains

The page opens on six questions, each a link in the page's nav, grouped by the job you are doing. A link shows a short label; the question it answers is shown above that list's title, and a screen reader announces it as the link's description:

- **Work.**
  - **Next up** ("What can I work on next?"). Open work in a startable stage (Implementing spec, Approved spec, Executing brief, Ready brief), then Accepted intents with nothing beneath them. The page says that readiness is not checked in this snapshot, so an item can still be blocked for a reason the file does not show.
  - **Broken** ("What is broken?"). Pointers that did not resolve, dependency problems, and delivery problems.
- **Progress.**
  - **Capability progress** ("How far along is each capability?"). Every capability under its product strategy, with a bar and counts of the work beneath it: delivered, in progress, not started, and stopped (withdrawn or archived work, kept apart). It shows only what the records say; it never claims a capability is on track or at risk. A capability that sits on a parent loop is listed once, with no capability above it.
  - **Open by capability** ("What is still open under a capability?"). The capabilities, each with its open count. Picking one shows the open work beneath it.
- **Tidy.**
  - **No parent** ("What has no parent?"). Open intents, briefs and specs with no resolved parent, grouped by type.
- **Browse.**
  - **All intents** ("Browse all intents") shows every intent as a tree, sorted by name under each parent (or under each capability). **Show** narrows it to all, open or done work, keeping each match's parents visible as rows marked "context". **Group** switches between the full hierarchy and grouping under the nearest capability. **Expand all** and **Collapse all** open or close every branch. While a level, kind or status filter is set, the list is flat and sorted by name.

A search box in the header covers intents, briefs, and specs.

The **Dependencies** part of a detail panel lists "A waits for B" lines for the picked intent. **Show** chooses prerequisites, dependents, or both, and **Steps** chooses how far to follow them. Problems are listed below the lines and in "What is broken?". The part says it does not decide whether work can start, and the Key explains its marks.

Each row leads with the human name, shows its state as a word plus a shape inside a pale tinted label (so colour is never the only cue), and carries a context tag. A **Key** opens on demand to explain the marks.

Selecting a row opens a detail panel: the state line; a **Next step** that says in plain words what to do and why, with a ready-to-paste prompt where a skill can start the work (see [The hand-over prompt](#the-hand-over-prompt)); what is open beneath the item; what is broken; where it sits in the graph; a **Dependencies** part; a link to its source file; and collapsed record details with the header facts, including two "Depends on" groups. A broken entry shows as a tinted callout with its diagnostic text in monospace. The layout changes at narrow and wide widths, the page works from the keyboard, and light and dark follow your system. Hover and selection fade briefly, and the detail fades in as it changes; if your system asks for reduced motion, the page does not move at all.

#### The hand-over prompt

When the Next step points to a skill that can start the work, the panel shows a prompt block under the sentence. It is one fixed sentence that names the skill and holds only the item's file path, in backticks. Nothing written inside the record is added to it. The block has a **Copy prompt** button. Pressing it copies the prompt and the button reads "Copied" for a moment. Paste the prompt into your agent to start the skill on that file. The page never launches anything itself.

If your browser refuses the clipboard, the page selects the prompt and says "Copy didn't work here. Press Ctrl+C or ⌘C to copy the selected prompt." Press those keys to copy it by hand.

If a file's path is too long or uses characters a prompt cannot carry safely, the panel shows "No prompt shown: this file's path is too long or uses characters a prompt cannot carry safely. Start the skill yourself from Open the file." and no prompt. Some Next steps, such as a wait or a finished item, carry no prompt at all.

The file holds exactly the facts `query` returns over the same corpus: the summary, each intent's record, outstanding work, and every node and edge. It does not hold artifact bodies, your absolute repository path, or any part of the Git remote beyond host, owner, and repository name.

- **Source links** go to GitHub only when `origin` is a plain GitHub remote. A link marked "at commit ..." opens the file at the exported commit. A link marked "may be newer than this export" opens it on the GitHub default branch. Every link carries that mark when the exported commit is not on origin, when any intent file differs from it, or when Git is older than 2.44. An untracked or unpushed file may not exist there yet. Any other remote shows each source's path as plain text.
- **With `--from`**, the page names the scoped intent and shows only that subtree. The totals still count the whole corpus and the page says so. A scoped export also carries the dependency records of intents linked to that subtree and names those outside it by id.
- **When delivery mapping is unavailable** (the delivery resolver hit its limit), the page says so and gives the reason where it would list delivery relations.
- **Record text is inert.** The page never runs script from a record, never loads anything, and makes no network request when you open it. A header value that contains markup shows as plain text.

### Where the file may go

The export refuses to write inside the repository: not in the root, not in any Git repository that encloses it, and not in any work tree of that repository. If your home directory is itself a Git repository, pass a `--destination` outside it. The default temporary directory is unaffected.

One case is not covered. If you export from a linked worktree whose main checkout was created with `--separate-git-dir`, or moved with `core.worktree`, Git does not list that main checkout, so the export cannot tell you a destination inside it is wrong. Do not choose one.

The file is written complete or not at all, with mode `0600` (readable only by you), and an existing entry is never overwritten.

### When an export is refused

A refusal prints `status: error` with an `error` object (`code`, `message`, `limits`, `observed`), writes nothing, and exits 1. A command the argument parser rejects exits 2 with no JSON.

| Code | What it means | What to do |
|------|---------------|-----------|
| `invalid_destination` | The destination is missing, is not a directory, or lies inside the repository, or `--name` is not allowed. The message names the directory it lies under. When `git` is unavailable or cannot list the work trees of an enclosing repository, every destination is refused. | Choose an existing directory outside the repository, fix the name, or make `git` available. |
| `destination_exists` | An entry with that name is already there. | Choose another `--name`. |
| `publish_failed` | The directory changed while the file was written, the directory cannot be written (permissions, no free space, or a read-only file system), or the platform lacks the directory-relative file calls the export needs (Windows). `error.observed` names the `stage` and the `errno` name when the system gave one, and never a path. | Pick a writable directory with free space; for a changed directory, retry on a stable one; on Windows the export is not supported. |
| `export_too_large` | The page is larger than `error.limits.budget_bytes`. | Re-run with `--from`, the bounded route named in `error.limits.bounded_route`, on a smaller subtree. |

The corpus codes from [When a query is refused](#when-a-query-is-refused) apply too: `duplicate_identity`, `malformed_record`, `unsafe_input`, `input_too_large`, `resolver_unavailable`, `not_found`, and `ambiguous_identity`. `not_found` and `ambiguous_identity` come from `--from`. `invalid_query` means a command-line argument is not valid UTF-8; pass valid UTF-8 arguments.

## Related intents

An intent can name another intent it sits beside with a `Related intents:` line. The author writes the line on one side only, and the navigator shows the relation from both ends. `record` and `tree` list the edges the intent writes in `related_written_here`, and the edges that name it in `related_written_elsewhere`.

A related edge is never a parent, a child, a dependency, or an ordering. It does not move an intent in the tree, and it does not affect `outstanding`. A related value takes only typed ids: `intent:`, `capability:`, `outcome:`, or `opportunity:` followed by a slug of lowercase letters, digits, and single hyphens. A bare slug, a path, or a malformed slug is refused as `unparseable`; a `brief:` or `spec:` id is refused as `out_of_type`. A related value that cannot resolve shows as a refused edge with its state, and the rest of the result stays whole.

## Text output

Only `tree` and `outstanding` support `--format text`. The other operations (`summary`, `record`, `ancestors`, `search`) always return JSON regardless of the flag.

`--format text` prints one line per artifact at its depth in the tree. Two spaces indent each level. This is `tree --id capability:work-item-capture-and-disposition --depth 1 --format text`, trimmed:

```text
capability:work-item-capture-and-disposition · capability · Accepted
  opportunity:duplicate-coverage-check · feature · opportunity · Accepted
  opportunity:governance-item-record-routing · feature · opportunity · Accepted
```

`tree` prints intents only. `outstanding` also prints the briefs and specs placed under them, as in the first example on this page.

Each intent line reads: `node-id · level · kind (when present) · status`. A brief or spec line reads: `node-id · status`. A refused parent edge prints one level deeper as `! refused <state>`. Related edges print one level deeper too, before the intent's children. A related intent the line names prints as `~ related <id>`. A related value that cannot resolve prints as `! refused related <state>`. An intent that another intent names as related prints as `~ related from <id>`.

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
| `self_reference` | The `Related intents:` value names the intent itself. Only that field reports it. | Remove the item. |
| `cycle` | Following this parent edge would circle back to this intent. | Remove the pointer that closes the loop. |
| `unparseable` | The pointer uses an unrecognised form (e.g. an absolute path). | Rewrite it as a typed id, bare slug, or relative path. For `Related intents`, use one of the four intent prefixes and a lowercase slug, as in [Related intents](#related-intents). |

A refused edge leaves every other node and edge in the result; the rest of the tree is still shown.

## When a query is refused

A refused query returns `status: error` with exit code 1 and an `error` object containing `code`, `message`, `limits`, and `observed`. A command the argument parser rejects, such as an unknown or malformed flag, exits 2 with no JSON envelope.

**Large result:** `result_too_large` means the result exceeds the size limit. For `tree`, add or lower `--depth`. For `outstanding`, add `--from` to limit to one intent. The flag to use is named in `error.limits.bounded_route`. `search` and `ancestors` refuse with the exceeded limit but do not name a bounded route. Add selectors to narrow a `search`. An oversized `ancestors` chain has no narrowing flag.

**Broken file:** `unsafe_input`, `input_too_large`, and `malformed_record` name in `error.message` the file or directory that must be repaired. `duplicate_identity` names the clashing id or slug instead: search for the files that declare it and keep one. An `unsafe_input` whose message is "the intent graph could not be derived" names no file: the navigator itself failed, so reinstall the skill.

**Delivery incomplete:** `delivery_incomplete` names no file. Read `error.observed.reason`. `unsafe` means the delivery resolver refused a link, special file, or non-UTF-8 file among the specs, briefs, and intents it reads. It names none of them, so look for such a file, replace it with a regular UTF-8 file, then run again. `resource_limit` means the corpus is larger than the resolver's fixed limit named in `error.observed.limit`. No flag raises that limit. Only `outstanding` returns `delivery_incomplete`: `summary`, `record`, `tree`, `ancestors`, and `search` still answer for either reason.

**Missing helpers:** `resolver_unavailable` means a bundled helper is missing or broken. Reinstall the skill.

**Wrong arguments:** `not_found`, `ambiguous_identity`, `invalid_selector`, `invalid_depth`, `invalid_query`, `missing_operation`, and `unknown_operation` mean the command arguments do not match any live intent or valid operation. Correct them and run again.

## Read-only boundary

The `query` operations never write anything, and `export` never writes inside the repository. Every answer is derived from preamble headers (the `Status:`, `Level:`, and other fields at the top of each intent file) at the moment it is asked; `query` caches and stores nothing. Symlinks, hard links, special files, and paths outside the repository root are refused before any content is read. The `boundary` field in every `query` response states this explicitly. An `export` response carries no `boundary` field; it reports the one file it wrote.

Results are candidate context derived at query time, not authoritative policy. The `provenance.generated_at` field is the only non-deterministic value; results are otherwise byte-identical across runs once it is removed.

## Related

- [Orient at the start of a session](orient-at-session-start.md) — read queue state and pick a next action with `workspace-status`

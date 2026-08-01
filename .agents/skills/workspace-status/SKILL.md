---
name: workspace-status
description: Use this skill to orient at session start, check initiative queue state, or see what's ready to work on next. Reads workspace.toml and surfaces ready-to-start items, blocked items with reason, parallel candidates, and active signals. Triggers on "workspace status", "where am I", "orient me", "session start", "what's ready", "show the queue", "what's next", "what should I work on", "check workspace", or any cold-start orientation request. Offers to initialise workspace.toml if absent.
---

# Skill: workspace-status

Read the local `workspace.toml` and surface the current queue state across all active initiatives. Run this at every session start — it replaces reading multiple product docs by hand.

## Output rendering

Status list — Lead each row with a status glyph — ● running, ✓ done, ○ idle, ⚠ blocked — status first, one item per line, labels aligned.
Table — When presenting several items that share the same fields, render a Markdown table. Cap at ~5 columns; beyond that, switch to a per-item detail list. Right-align numeric columns.
Diagram / flow — For relationships or flow, emit a fenced ```mermaid block (it renders in chat and artifacts). If the surface is terminal-only, fall back to an ASCII box-and-arrow sketch.
Progress — Report progress inline as done/total (e.g. 3/8). Only draw a bar if you're animating in a terminal.

## When to invoke

Any time you need to orient: which initiative is active, what specs are ready to start, what is blocked and why, what signals the strategist has flagged. Also the right skill if workspace.toml does not yet exist and you want to initialise it.

## Procedure

### 1. Invoke the backend

Run the production backend via **argument vector** (the canonical and only safe invocation):

```
["<python>", "<skill-dir>/scripts/workspace_status.py", "--root", "<repo-root>"]
```

`<python>` is the Python 3.11+ interpreter available in your environment: `python3` on macOS/Linux; `python` on Windows. `<skill-dir>` is the directory where your installer placed this skill's files (i.e., the directory containing this SKILL.md). Passing the paths as **discrete arguments** prevents shell expansion of `$()`, backticks, `$VAR`, and other metacharacters — the values are never interpreted by a shell.

**Shell-string-only tools:** If your adapter cannot be configured to pass a discrete argument vector, use the shell-specific form below — or, for maximum portability, set the working directory to the repository root and pass `--root .`:

- **POSIX (bash/zsh):** `python3 '<skill-dir>/scripts/workspace_status.py' --root .`
- **PowerShell:** `python '<skill-dir>/scripts/workspace_status.py' --root .` (single-quoted strings are literal in PS; safe unless the path contains `'`)
- **cmd.exe:** argv form required — cmd.exe does not treat single quotes as quoting characters; paths with spaces cannot be quoted safely in a shell string.

Any path with special characters requires the argv form.

**Exit 1 — workspace.toml absent:** the JSON will contain `"workspace_present": false`. Offer to initialise — ask the user whether to create a blank file or bootstrap with their first initiative. A blank file emits the full schema-documented template:

```toml
# workspace.toml
#
# Declared-intent coordination artifact for this repo.
# Each initiative gets its own named section. Run `workspace-status` to surface
# ready items, blocked items, and active signals.
#
# Queue entries are strings (no deps) or inline objects {path/slug, needs}
# (with dependencies). `needs` uses queue-prefix notation:
#   "work:<path>"      — depends on a work queue entry
#   "shape:<slug>"     — depends on a shaping queue entry
#   "research:<slug>"  — depends on a research entry
#   "brief:<path>"     — depends on a brief queue entry
#   "backlog:<slug>"   — depends on a repo-level [backlog] item
# Cross-initiative deps prefix the initiative slug: "ini-002:work:spec/..."
#
# shaping_queue entry types: shape | research | strategy | signal | design
#   shape    → frame-intent (or frame-situation when PE pack is available)
#   research → desk-research-project-start (requires desk-research pack)
#   strategy → frame-situation (PE pack — M2); interim: frame-intent
#   signal   → no action; surfaces in "active context" section only
#   design   → experience-status (requires experience-design pack); fallback: journey-mapping
#
# The top-level [backlog] section (repo-durable open work not scoped to any
# active initiative) is distinct from a shaping_queue's `backlog` array.

["<initiative-slug>"]
name      = "<Initiative Name>"
status    = "active"      # active | paused | closed
milestone = "<milestone>"

["<initiative-slug>".work]
queue   = []  # ordered list of spec paths to build; earliest-first
active  = []  # currently in-progress
shipped = []  # completed

["<initiative-slug>".shaping_queue]
active  = []
backlog = []

[backlog]
open = []
```

**Exit 2 — unexpected error:** surface the stderr message and stop — do not proceed with partial data.

**Exit 0:** parse the JSON result. Key fields:

```
initiatives              — list of active initiatives (slug, name, status, milestone, brief_queue)
initiatives[].brief_queue — {executing, ready, draft} or null
work.ready     — list of ready-to-start build entries; each carries ini_slug and blocking_needs
work.blocked   — list of blocked build entries; each carries ini_slug and blocking_needs
work.active    — list of currently in-progress build entries; each carries ini_slug
work.shipped   — list of shipped build entries; each carries ini_slug
shaping.ready  — list of ready shaping entries (from active AND backlog); each carries ini_slug and blocking_needs
shaping.signals — list of active-context signal entries; each carries ini_slug
shaping.blocked — list of blocked shaping entries (backlog only); each carries ini_slug and blocking_needs
shaping.active_entries — list of all shaping_queue.active entries; each carries slug, ini_slug, and entry_type (signals included)
reconciliation.type1             — untracked live specs
reconciliation.type2             — stale queue/active entries
reconciliation.type3             — prematurely-shipped entries
reconciliation.type2_cleanup_ops — cleanup operations per Type 2 finding
diagnostics.spec_files_read      — number of spec.md files examined
```

### 2. Surface results

If the reconciliation block is non-empty (any type1/type2/type3 findings), output it first:

**Reconciliation:**

Let N = total count across all three finding types. When N > 0, output before the main sections; omit subsections with no entries; name the initiative for each stale/shipped entry (e.g. `[ini-002 work]`):

```
**Reconciliation** — N inconsistenc(y/ies) detected:

  Untracked live specs (Approved or Implementing, not in any initiative list):
  - `spec/<slug>` (Status: Approved) — add to [work].queue or run capture-work

  Stale queue/active entries (spec shows Shipped or Archived):
  - `spec/<slug>` in [ini-002 work].queue — Status: Shipped
  - `spec/<slug>` in [ini-002 work].active — Status: Archived

  Prematurely-shipped entries ([work].shipped, spec shows live status):
  - `spec/<slug>` in [ini-002 work].shipped — Status: Implementing
    Possible causes: (1) spec Status was not updated after shipping, or
    (2) the workspace.toml entry was moved before the work was done.
```

When Type 2 findings exist, build the cleanup offer using `reconciliation.type2_cleanup_ops`. For any Type 2 entry whose `list_name` is `active`, ask first: "Is `<path>` actively being worked on in this session?" — if the user says yes, **exclude all ops for that `(ini_slug, path)` pair** from the confirmed-operation set (both the active-list op and any queue-list op for the same path, to avoid partially applying a cleanup that leaves the path in both `active` and `shipped`). Build the _confirmed set_ (all ops except those excluded) before showing the offer. Then append:

```
Stale entries found — clean up now?
  Shipped entries move to [work].shipped (bare string, `needs` dropped).
  Archived entries are removed from [work].queue or [work].active.
  Reply Y to apply, or edit workspace.toml manually.
```

**Cleanup write — after Y confirmation (Type 2 only):**

Apply only the _confirmed set_ of operations (do not re-read `type2_cleanup_ops`). Each op describes:
- `ini_slug` — initiative to modify
- `source_list` — list to remove the entry from (`queue` or `active`)
- `target_list` — list to add it to (`shipped`) or `null` (Archived: remove only)
- `path` — the entry path
- `written_form` — TOML source literal for text insertion (Shipped only; e.g. `"spec/foo"` with surrounding quotes)

When appending to `[work].shipped`, deduplicate by `path`: skip the append if the path is already present (a path in both `queue` and `active` produces two ops; apply the source-list removal for each but append at most once).

Use a comment-preserving write — targeted text insertion or `tomlkit`; never a `tomllib` + `tomli_w` round-trip (strips comments).
- **Text insertion:** append `written_form` as-is (it is already a correctly-quoted TOML string literal, including surrounding `"` characters).
- **`tomlkit` structured API:** append `path` (the raw string value); `tomlkit` handles quoting automatically. Do not pass `written_form` to `tomlkit` — it would persist the surrounding quote characters as part of the path value.

**Main output sections:**

Format output in four sections (omit sections with no entries):

---

**Active initiatives:** (for each entry in `initiatives[]`)
`<ini-slug>` — `<name>` (milestone: `<milestone>`)
- **Brief queue** (from `initiatives[].brief_queue`; omit when `null`): Executing: `<executing>` (or "none") · Ready: N item(s) · Draft: N item(s)

**Active context — signals** _(ongoing; do not need action):_
- `<slug>` (`signal`) — no action needed; informs shaping decisions

**Ready to start:**
- `[build]` `<path>` — run `work-loop` on `docs/specs/<path>/`
- `[shape]` `<slug>` (`shape`) — run `frame-intent`
- `[shape]` `<slug>` (`research`) — run `desk-research-project-start`
- `[shape]` `<slug>` (`strategy`) — route through `frame-situation` (PE pack — M2); if not yet available, run `frame-intent` as interim
- `[shape]` `<slug>` (`design`) — run `experience-status` (requires experience-design pack); fallback: `journey-mapping`
- `[brief]` `<path>` (Ready) — run `receive-brief` on `docs/product/briefs/<path>.md`

**Parallel candidates:** _(all of the above with no inter-dependencies can start concurrently)_

**Blocked:**
- `<path>` — waiting on `<needs-entry>` (status: `<queued|in-progress>`)

  Resolve the status from JSON: for each entry in `blocking_needs`, strip the queue-prefix to get the slug/path, then branch on the prefix. **For same-initiative deps** (no `ini-NNN:` prefix), scope every lookup to the blocked entry's own `ini_slug`; only entries matching that `ini_slug` count. For cross-initiative deps, scope to the named initiative instead.
  - `work:` — scope to blocked entry's `ini_slug`: filter `work.active`, `work.ready`, `work.blocked` by `ini_slug == owning-ini`. Path in filtered `work.active` → `in-progress`; in filtered `work.ready` or `work.blocked` → `queued`; else → omit.
  - `shape:` — scope to `ini_slug` as above; use `shaping.active_entries` filtered to `ini_slug == owning-ini`: if a matching entry with `slug == dep_slug` is found → `in-progress` (signals included); else → omit.
  - `research:` — research deps block while the item is in `shaping_queue.backlog`; backlog items appear in `shaping.ready` or `shaping.blocked` — filter both by `ini_slug == owning-ini`: if dep slug found → `queued`; else → omit.
  - `brief:` — scope to the owning initiative's `brief_queue` only (filter `initiatives[]` by `slug == owning-ini`, since `initiatives[]` carries `slug` not `ini_slug`): if path in `brief_queue.draft` → `queued`; if in `brief_queue.executing` → `in-progress`; else → omit.
  - Cross-initiative prefix (e.g. `ini-002:work:spec/foo`) — strip the `ini-NNN:` prefix to get the named initiative; resolve the remainder as above using that initiative's `ini_slug`.
  - Not found by any path (dependency belongs to a paused initiative) → omit the status annotation.

**Closeout check:** For each initiative in `initiatives[]`, filter `work.ready`, `work.blocked`, `work.active`, and `work.shipped` by that initiative's `ini_slug`. Also check `reconciliation.type2` for any entry with that `ini_slug`. Gate closeout on all of: (1) filtered ready + blocked + active are empty, (2) no type2 findings for that initiative, (3) `initiatives[i].queue_empty` is `true` — a path in both `queue` and `shipped` is excluded from the classifier's ready/blocked output and may have no type2 finding, so the raw queue emptiness flag is the authoritative check, (4) filtered shipped is non-empty → surface: "`<ini-slug>`: all specs shipped — ready to close out? Run closeout to remove this section (git history preserves the record)."

**Findings:** Read `docs/product/findings/rfc-candidates.md` and `docs/product/findings/roadmap-intents.md` if they exist. Count non-header rows in each (a non-header row is any `|…|` line after the header separator row — the `|---|...|` line of dashes).

- **When either file has data rows:** output a `**Findings:**` section with both tables printed inline — paste each file's full markdown table (column header row + separator + data rows) under a sub-label (`RFC candidates:` / `Roadmap intents:`). If one file is absent or has no data rows, output its sub-label followed by `_(empty)_`.
- **When both are empty or absent:** emit a single line: `0 rfc candidates · 0 roadmap intents — both registers empty`

**Backlog:** when `[backlog].open` in `workspace.toml` is non-empty, render:

```
**Backlog** — N open item(s):
- `[shape]` `<slug>` — <first # comment line above the entry>
- `[build]` `<slug>` — <first # comment line above the entry>
  ...
```

Each entry is prefixed with its room: `[shape]` when the entry carries a `type` field (shaping work); `[build]` when it does not (build work). To extract the first comment line: read `workspace.toml` as text; for each entry in `[backlog].open`, find the nearest `# ` comment line immediately preceding `{slug = "<slug>"}`. Use the comment text (without the leading `# `) as the item's summary. If no comment line is present, omit the summary and render just the slug. Omit this section entirely when `[backlog].open` is empty or absent.

---

### 3. Skill prompts by type

When surfacing shaping_queue entries, append the right skill invocation based on what's installed:

| Entry type | Skill to suggest |
|-----------|-----------------|
| `shape` (default) | `frame-intent` (available now); `frame-situation` (M2, when available) |
| `research` | `desk-research-project-start` (requires desk-research pack) |
| `strategy` | route through `frame-situation` (PE pack — M2); if not yet available, run `frame-intent` as interim |
| `signal` | no action — surface in "active context" section only |
| `design` | `experience-status` (requires experience-design pack); if experience-design is not installed: `journey-mapping` |

If the required pack is not installed, surface: "requires `<pack-name>` pack — install to work this item."

### 4. Missing fields

`workspace.toml` evolves: older entries may lack a `type` field (treat as `shape`), a `milestone` field (omit from output), or a `parent` field (omit). Never fail on missing optional fields.

### 5. Next-actions

Using the JSON data from Step 1 — do not re-read `workspace.toml` or recompute the DAG:

**5a. Resolve choices**

From the JSON result:

- `active_spec` = first entry in `work.active` (if any)
- `next_queue` = first entry in `work.ready` (JSON field, already resolved; first in list order)
- `unblocked` = all entries in `work.ready`
- `next_shape` = first entry in `shaping.ready` whose `entry_type` is not `signal` AND for which `shaping.active_entries` contains an entry matching all of `slug`, `ini_slug`, and `entry_type` (a signal named `x` in active does not make a non-signal `x` in ready count as active); fall back to the first `shaping.ready` non-signal entry with no such full match (backlog-ready)

**Path resolution:** entries in `work.ready`, `work.active`, etc. carry a `path` field (e.g. `"spec/m1-workspace-core"`). Strip the `spec/` prefix to get the slug; use `docs/specs/<slug>/` for file-system commands.

**5b. ASCII dependency graph (when ≥2 unblocked work items)**

If `len(unblocked) ≥ 2`, render the following block _before_ the numbered choices:

```
Work queue — parallel opportunities:

  <slug-A>  [ready]
  <slug-B>  [ready]
  <slug-C>  [blocked by <dep-slug>]
```

- Right-pad the slug column to the longest slug for alignment. Use the bare path (with `spec/` prefix preserved) for both `[ready]` and `[blocked by]` rows — e.g. `spec/alpha [ready]` and `spec/gamma [blocked by spec/alpha]`.
- Entries in `work.ready`: annotate `[ready]`.
- Entries in `work.blocked`: annotate `[blocked by <dep-slug>]`, where `<dep-slug>` is the first entry in that item's `blocking_needs` with the queue-prefix domain stripped.

**5c. Harness detection and parallel-session offer (when graph rendered)**

When the graph was rendered, offer a parallel-session choice as the **first** numbered slot. Check whether `--bg` appears in `claude --help` output (if a shell/command tool is available):

- **`--bg` found:** emit a numbered choice listing `claude --bg "work-loop docs/specs/<slug>/"` for each parallel-ready root node.
- **`--bg` absent or no shell tool available:** emit a numbered choice with prose instructions for each parallel-ready root node (no automated spawn).

**5d. Numbered choices**

Emit the following choices in order. Omit any whose source is empty; renumber sequentially. The parallel-session offer from 5c (when present) occupies the first slot and the remaining choices follow.

- **Active spec:** `work-loop docs/specs/<slug>/` — continue active spec. Present when `active_spec` is non-empty.
- **Next queue item:** `work-loop docs/specs/<slug>/` — next unblocked queue item. Present when `next_queue` is non-empty.
- **First shaping item:** skill command per Step 3 routing table for the entry's type. Present when `next_shape` is non-empty. If the required pack is not installed, emit `requires \`<pack-name>\` pack — install to work this item` instead of the skill command.
- **Start new work (always — final choice):** `new-spec` · `new-rfc` · `new-adr` · `capture-work`

## See also

- `references/agentbundle-layout.md` — the `[product]` table: configurable `projects/` and `shaping/` paths used by product-facing skills

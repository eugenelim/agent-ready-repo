---
name: workspace-status
description: Use this skill to orient at session start, check initiative queue state, or see what's ready to work on next. Reads workspace.toml and surfaces ready-to-start items, blocked items with reason, parallel candidates, and active signals. Triggers on "workspace status", "where am I", "orient me", "session start", "what's ready", "show the queue", "what's next", "what should I work on", "check workspace", or any cold-start orientation request. Offers to initialise workspace.toml if absent.
---

# Skill: workspace-status

Read the local `workspace.toml` and surface the current queue state across all active initiatives. Run this at every session start — it replaces reading multiple product docs by hand.

## When to invoke

Any time you need to orient: which initiative is active, what specs are ready to start, what is blocked and why, what signals the strategist has flagged. Also the right skill if workspace.toml does not yet exist and you want to initialise it.

## Procedure

### 1. Read workspace.toml

Open `workspace.toml` from the repo root. Parse it as TOML (`tomllib.loads()` in Python 3.11+ / `tomli.loads()` backport for earlier).

**If absent:** offer to initialise — ask the user whether to create a blank file or bootstrap with their first initiative. A blank file contains only the one-line comment:

```toml
# workspace.toml — add ["<initiative-slug>"] sections to declare initiatives
```

**If present and unparseable:** surface the TOML parse error and stop — do not proceed with partial data.

### 2. Resolve the DAG

For each initiative's `[work]` and `[shaping_queue]`:

- A queue entry is **ready** when all its `needs` entries are satisfied (see below).
- A queue entry is **blocked** when one or more `needs` entries are not yet satisfied.
- An entry with no `needs` field is unconditionally ready (unless already in `active` or `shipped`).

**Needs resolution:**

`needs` is a string or list of strings using queue-prefix notation:

| Prefix | Resolves against |
|--------|-----------------|
| `work:<path>` | `[work].shipped` (or `[work].active` counts as in-progress) |
| `shape:<slug>` | `[shaping_queue].active` or treated as shipped if not present |
| `research:<slug>` | `[shaping_queue]` entries of `type = "research"` — ready when that entry is not in the backlog |
| `brief:<path>` | `[brief_queue].ready` or `executing` |
| `<ini-slug>:work:<path>` | Cross-initiative: `["<ini-slug>".work].shipped` |

An entry is satisfied when its referenced item is in the appropriate shipped/done list. When `needs` is a list, ALL entries must be satisfied.

### 3. Surface results

Format output in four sections (omit sections with no entries):

---

**Active initiatives:** `<ini-slug>` — `<name>` (milestone: `<milestone>`)

**Active context — signals** _(ongoing; do not need action):_
- `<slug>` (`signal`) — no action needed; informs shaping decisions

**Ready to start:**
- `[work]` `<path>` — run `work-loop` on `docs/specs/<path>/`
- `[shaping_queue]` `<slug>` (`shape`) — run `frame-intent`
- `[shaping_queue]` `<slug>` (`research`) — run `desk-research-project-start`
- `[shaping_queue]` `<slug>` (`strategy`) — route through `frame-situation` (PE pack — M2); if not yet available, run `frame-intent` as interim
- `[shaping_queue]` `<slug>` (`design`) — run `experience-status` (requires experience-design pack); fallback: `journey-mapping`
- `[brief_queue]` `<path>` (Ready) — run `receive-brief` on `docs/product/briefs/<path>.md`

**Parallel candidates:** _(all of the above with no inter-dependencies can start concurrently)_

**Blocked:**
- `<path>` — waiting on `<needs-entry>` (status: `<queued|in-progress>`)

**Brief queue:**
- Executing: `<path>` (or "none")
- Ready: `<count>` item(s)
- Draft: `<count>` item(s)

**Closeout check:** if `[work].queue` is empty and `[work].active` is empty and `[work].shipped` is non-empty → surface: "`<ini-slug>`: all specs shipped — ready to close out? Run closeout to remove this section (git history preserves the record)."

**Findings:** count non-header rows in `docs/product/findings/rfc-candidates.md` and `docs/product/findings/roadmap-intents.md` if the files exist. Surface as a single count line:

```
N rfc candidates · M roadmap intents
```

Omit the line entirely when both counts are zero or the files are absent.

---

### 4. Skill prompts by type

When surfacing shaping_queue entries, append the right skill invocation based on what's installed:

| Entry type | Skill to suggest |
|-----------|-----------------|
| `shape` (default) | `frame-intent` (available now); `frame-situation` (M2, when available) |
| `research` | `desk-research-project-start` (requires desk-research pack) |
| `strategy` | route through `frame-situation` (PE pack — M2); if not yet available, run `frame-intent` as interim |
| `signal` | no action — surface in "active context" section only |
| `design` | `experience-status` (requires experience-design pack); if experience-design is not installed: `journey-mapping` |

If the required pack is not installed, surface: "requires `<pack-name>` pack — install to work this item."

### 5. Missing fields

`workspace.toml` evolves: older entries may lack a `type` field (treat as `shape`), a `milestone` field (omit from output), or a `parent` field (omit). Never fail on missing optional fields.

### 6. Next-actions

Using Step 2 DAG state only — do not re-read `workspace.toml`:

**6a. Resolve choices**

From the state already computed in Step 2:

- `active_spec` = first entry in `[work].active` (if any)
- `next_queue` = first entry in `[work].queue` whose `needs` are all satisfied (queue order); if an entry is an inline object, use its `path` field
- `unblocked` = all entries in `[work].queue` whose `needs` are all satisfied
- `next_shape` = first entry in `[shaping_queue].active` whose `type` is not `signal` (if any); else first entry in `[shaping_queue]` that is ready (unblocked, not in `active` or `shipped`) and whose `type` is not `signal`

**Path resolution:** workspace.toml paths carry a `spec/` prefix (e.g. `"spec/m1-workspace-core"`). Strip it before building file-system paths — the slug is the part after `spec/`, and the command uses `docs/specs/<slug>/`.

**6b. ASCII dependency graph (when ≥2 unblocked work items)**

If `len(unblocked) ≥ 2`, render the following block _before_ the numbered choices:

```
Work queue — parallel opportunities:

  <slug-A>  [ready]
  <slug-B>  [ready]
  <slug-C>  [blocked by <dep-slug>]
```

- Right-pad the slug column to the longest slug for alignment. Use the bare path (with `spec/` prefix preserved) for both `[ready]` and `[blocked by]` rows — e.g. `spec/alpha [ready]` and `spec/gamma [blocked by spec/alpha]`.
- Unblocked entries: annotate `[ready]`.
- Blocked entries: annotate `[blocked by <dep-slug>]`, where `<dep-slug>` is the path with the queue-prefix domain stripped (e.g. `needs = "work:spec/alpha"` → `spec/alpha`).

**6c. Harness detection and parallel-session offer (when graph rendered)**

When the graph was rendered, offer a parallel-session choice as the **first** numbered slot. Check whether `--bg` appears in `claude --help` output (via the Bash tool if available):

- **`--bg` found:** emit a numbered choice listing `claude --bg "work-loop docs/specs/<slug>/"` for each parallel-ready root node.
- **`--bg` absent or Bash tool unavailable:** emit a numbered choice with prose instructions for each parallel-ready root node (no automated spawn).

**6d. Numbered choices**

Emit the following choices in order. Omit any whose source is empty; renumber sequentially. The parallel-session offer from 6c (when present) occupies the first slot and the remaining choices follow.

- **Active spec:** `work-loop docs/specs/<slug>/` — continue active spec. Present when `active_spec` is non-empty.
- **Next queue item:** `work-loop docs/specs/<slug>/` — next unblocked queue item. Present when `next_queue` is non-empty.
- **First shaping item:** skill command per Step 4 routing table for the entry's type. Present when `next_shape` is non-empty. If the required pack is not installed, emit `requires \`<pack-name>\` pack — install to work this item` instead of the skill command.
- **Start new work (always — final choice):** `new-spec` · `new-rfc` · `new-adr` · `queue-add`

## See also

- `references/agentbundle-layout.md` — the `[product]` table: configurable `projects/` and `shaping/` paths used by product-facing skills

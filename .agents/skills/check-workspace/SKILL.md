---
name: check-workspace
description: Use this skill to orient at session start, check initiative queue state, or see what's ready to work on next. Reads workspace.toml and surfaces ready-to-start items, blocked items with reason, parallel candidates, and active signals. Triggers on "check workspace", "what should I work on", "orient me", "session start", "what's ready", "show the queue", "workspace status", "what's next", or any cold-start orientation request. Offers to initialise workspace.toml if absent.
---

# Skill: check-workspace

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
- `[shaping_queue]` `<slug>` (`research`) — run `research-project-start`
- `[shaping_queue]` `<slug>` (`strategy`) — run product-strategy pack skill (requires product-strategy pack)
- `[brief_queue]` `<path>` (Ready) — run `receive-brief` on `docs/product/briefs/<path>.md`

**Parallel candidates:** _(all of the above with no inter-dependencies can start concurrently)_

**Blocked:**
- `<path>` — waiting on `<needs-entry>` (status: `<queued|in-progress>`)

**Brief queue:**
- Executing: `<path>` (or "none")
- Ready: `<count>` item(s)
- Draft: `<count>` item(s)

**Closeout check:** if `[work].queue` is empty and `[work].active` is empty and `[work].shipped` is non-empty → surface: "`<ini-slug>`: all specs shipped — ready to close out? Run closeout to remove this section (git history preserves the record)."

---

### 4. Skill prompts by type

When surfacing shaping_queue entries, append the right skill invocation based on what's installed:

| Entry type | Skill to suggest |
|-----------|-----------------|
| `shape` (default) | `frame-intent` (available now); `frame-situation` (M2, when available) |
| `research` | `research-project-start` (requires desk-research pack) |
| `strategy` | product-strategy pack skill (requires product-strategy pack — M4) |
| `signal` | no action — surface in "active context" section only |

If the required pack is not installed, surface: "requires `<pack-name>` pack — install to work this item."

### 5. Missing fields

`workspace.toml` evolves: older entries may lack a `type` field (treat as `shape`), a `milestone` field (omit from output), or a `parent` field (omit). Never fail on missing optional fields.

## See also

- `references/agentbundle-layout.md` — the `[product]` table: configurable `projects/` and `shaping/` paths used by product-facing skills

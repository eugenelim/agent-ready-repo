# workspace.toml — Dependency model reference

`workspace.toml` uses an inline dependency notation on queue entries to
declare coordination constraints between work items. This document explains
the notation in full. The authoritative source for D7 (dependency model) and
D9 (shaping-type prefixes) is
[RFC-0064](../rfc/0064-ini-001-ai-native-ecosystem.md); this doc is the
quick reference. See `workspace.toml` in the repo root for a lived example.

---

## Entry format

A queue entry is either a bare string (no dependencies) or an inline TOML
object with `path` and `needs` keys (with dependencies):

```toml
# String — no dependencies; can start immediately
"spec/my-feature"

# Inline object — has dependencies; blocked until needs resolves
{path = "spec/my-feature", needs = "work:spec/prerequisite"}

# Multiple dependencies — needs is a list of strings
{path = "spec/my-feature", needs = ["work:spec/a", "brief:docs/product/briefs/b.md"]}
```

`needs` is a string or a list of strings. Each string uses a prefix to
identify the queue type and target.

---

## Cross-queue prefix forms (for `[work]` queue entries)

These prefixes are used in `["ini-NNN".work].queue` entries to express
dependencies on items in different queues (RFC-0064 D7):

| Prefix | Meaning | Example |
| --- | --- | --- |
| `work:<path>` | depends on a work-queue entry at the given spec path | `"work:spec/m1-workspace-core"` |
| `shape:<slug>` | depends on a shaping-queue entry (an upstream PE artifact) | `"shape:capability-map-ini-002"` |
| `brief:<path>` | depends on a brief-queue entry at the given brief path | `"brief:docs/product/briefs/platform-core.md"` |

---

## Shaping-type prefix forms (for `[shaping_queue]` cross-type deps)

These prefixes are used within `["ini-NNN".shaping_queue]` entries to
express dependencies across shaping subtypes (RFC-0064 D9):

| Prefix | Meaning | Example |
| --- | --- | --- |
| `research:<slug>` | depends on a research entry (desk-research pack output) | `"research:adopter-persona"` |
| `strategy:<slug>` | depends on a strategy/shaping entry at the given slug | `"strategy:ini-002-initiative-brief"` |

---

## Cross-initiative prefix

To express a dependency on a work entry owned by a *different* initiative,
prefix the initiative slug before the queue type:

```
"ini-NNN:work:<path>"
```

Example — a feature in ini-003 depends on workspace-core from ini-002:

```toml
# In ["ini-003".work].queue:
{path = "spec/ini-003-feature",
 needs = "ini-002:work:spec/m1-workspace-core"}
```

The initiative slug matches the TOML section key (`["ini-002"]`) in
`workspace.toml`.

---

## Display surface

**`workspace-status`** is the skill that reads `workspace.toml`, resolves the
declared dependency DAG, and surfaces:

- Items whose `needs` are all in `shipped` → **ready to start**
- Items with at least one `needs` not yet shipped → **blocked** (with reason)
- Items with no `needs` or all satisfied — and that are in parallel with the
  current `active` item → **parallel candidates**

Agents read the `workspace-status` output to decide what to work on next.
They do not enforce the DAG themselves; `workspace-status` is the sole
resolution surface.

---

## Deferred: `work-loop` DAG enforcement

`work-loop` enforcement of the dependency DAG (blocking EXECUTE when an
entry's `needs` are not yet shipped) is deferred to a **post-M1 milestone**
per RFC-0064 D7. Until that milestone ships:

- `workspace-status` surfaces ready/blocked/parallel status — agents read it.
- `work-loop` does **not** automatically block when a `needs` dep is unmet.
- Teams rely on `workspace-status` output and human judgment to sequence work.

This reference doc does not create a false expectation: the deferred
enforcement means the `needs` field today is a *declared intent*, not a
runtime guard.

---

*See also:* [RFC-0064](../rfc/0064-ini-001-ai-native-ecosystem.md) §D7
(dependency model) and §D9 (shaping-type prefixes) for the full design
rationale. `workspace.toml` in the repo root is the lived example.

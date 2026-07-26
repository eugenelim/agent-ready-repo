# workspace.toml schema reference

> Authoritative description of every `workspace.toml` section, its fields, the `needs` queue-prefix notation, and the shaping-entry `type` vocabulary. For why the workspace model separates shaping from building, see [The two-room model](../explanation/two-room-model.md). For how to read this file at session start, see [How to orient at the start of a session](../how-to/orient-at-session-start.md).

`workspace.toml` lives at the repo root. It is the declared-intent coordination artifact: `workspace-status` reads it at session start to orient, `capture-work` writes to it when a new item is triaged, and `new-rfc` prompts to update it when an RFC is accepted. The file uses TOML's [quoted dotted-key form](https://toml.io/en/v1.0.0#keys) for section headers — **the quotes are required** when the key contains a hyphen (e.g. `["ini-NNN".shaping_queue]`, not `[ini-NNN.shaping_queue]`).

## Section: `["ini-NNN"]`

Top-level initiative metadata. `NNN` is a three-digit sequential number (zero-padded).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Human-readable initiative name, e.g. `"Platform Core"` |
| `status` | string | yes | `"active"` or `"inactive"` — only `"active"` initiatives appear in `workspace-status` output |
| `milestone` | string | no | Current milestone label, e.g. `"M1 · Workspace Foundation"` |
| `parent` | string | no | Parent initiative identifier, e.g. `"INI-001"` |

```toml
["ini-002"]
name = "Platform Core"
status = "active"
milestone = "M1 · Workspace Foundation"
```

Multiple `["ini-NNN"]` sections may coexist. Skills read all sections where `status = "active"`.

## Section: `["ini-NNN".shaping_queue]`

The **shape room** — items being discovered, researched, or framed before they are ready to implement. See [The two-room model](../explanation/two-room-model.md) for the conceptual explanation.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `active` | array | yes | Items currently being shaped, plus `signal`-type entries that live here permanently as ongoing monitoring context |
| `backlog` | array | yes | Items waiting to be picked up for shaping |

### Shaping entry format

Each entry is either a bare string (slug) or an inline object:

```toml
# Bare string — slug only; type defaults to "shape"
"my-research-topic"

# Inline object with explicit type
{slug = "my-research-item", type = "research"}

# Inline object with a dependency
{slug = "my-strategy-item", type = "strategy", needs = "shape:my-research-item"}
```

### `type` vocabulary

Defined in `packs/core/.apm/skills/capture-work/SKILL.md`. The `type` field is shaping-only — build entries do not carry it.

| Value | What it means | Skill |
|-------|--------------|-------|
| `shape` | Needs product-engineering shaping (default when `type` omitted) | `frame-intent` |
| `research` | Needs desk research before a spec can be written | `desk-research-project-start` |
| `strategy` | Needs market or product strategy work | `frame-situation` |
| `signal` | Ongoing monitoring context — no discrete end state; stays in the shape room permanently | (informational only — no action) |
| `design` | Needs experience-design work | `experience-status` |

A `signal` entry never graduates to the build room. All other types exit the shape room when a spec is authored via `new-spec`.

## Section: `["ini-NNN".brief_queue]`

Briefs in progress. A brief is a multi-feature product handoff that decomposes into multiple specs via `receive-brief`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `executing` | string | yes | Path to the brief currently executing, or `""` if none |
| `ready` | array | yes | Paths to briefs that have passed the definition-of-ready gate |
| `draft` | array | yes | Paths to briefs currently being authored |

```toml
["ini-002".brief_queue]
executing = "docs/product/briefs/my-brief.md"
ready = []
draft = []
```

## Section: `["ini-NNN".work]`

The **build room** — specs in the implementation queue.

Items move through three lists by list membership. Lifecycle direction is one-way: `queue` → `active` → `shipped`. There is no per-entry status field — a path's lifecycle stage is determined by which list it is in.

| List | What it means |
|------|--------------|
| `queue` | Ready to start, or waiting on a `needs` dependency |
| `active` | Currently being built in this session |
| `shipped` | Implemented — moved here on PR merge |

### Build entry format

```toml
# Bare string — no dependencies
"spec/my-feature"

# Inline object — with a single dependency
{path = "spec/my-feature", needs = "work:spec/other-feature"}

# Inline object — with multiple dependencies (all must be satisfied)
{path = "spec/my-feature", needs = ["work:spec/a", "work:spec/b"]}
```

### `needs` queue-prefix notation

The `needs` field names a dependency by prefix and path. An item is unblocked when all its `needs` are satisfied.

| Prefix | Resolves to |
|--------|------------|
| `work:<path>` | `["ini-NNN".work].shipped` — satisfied when the path appears there |
| `shape:<slug>` | `["ini-NNN".shaping_queue].active` — satisfied when the slug is no longer in `active` (the item has graduated from active shaping) |
| `research:<slug>` | Shaping entries of `type = "research"` — satisfied when not in `backlog` |
| `brief:<path>` | `["ini-NNN".brief_queue].ready` or `executing` — satisfied when path appears in either |
| `<ini-slug>:work:<path>` | Cross-initiative: `["<ini-slug>".work].shipped` |

When `needs` is a list, **all** entries must be satisfied for the item to be unblocked.

## Section: `[backlog]`

Repo-level open work not scoped to any active initiative. Distinct from `["ini-NNN".shaping_queue].backlog`, which is per-initiative.

```toml
[backlog]
open = [
  # My backlog item description
  {slug = "my-backlog-item"},
  # Another item, blocked on the first
  {slug = "my-blocked-item", needs = "backlog:my-backlog-item"},
]
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `slug` | string | yes | Unique identifier — must match any `(deferred: <slug>)` marker in specs |
| `needs` | string or array | no | Same prefix notation as the build room `needs` field |
| `type` | string | no | When present, marks a shaping item (same vocabulary as shaping entries); absent means a ready build item |
| `source` | string | no | Provenance, e.g. `"spec/foo AC3"` |

The comment immediately above each entry (starting with `# `) is used by `workspace-status` as the item's one-line summary. Write it as a cold-start-sufficient description: what the item is, what skill or spec is relevant, and what would unblock it if blocked.

## See also

- [The two-room model](../explanation/two-room-model.md) — why shaping and building are separated
- [How to orient at the start of a session](../how-to/orient-at-session-start.md) — how to read this file at session start
- [How to capture and triage a work item](../how-to/capture-work.md) — how `capture-work` writes to this file

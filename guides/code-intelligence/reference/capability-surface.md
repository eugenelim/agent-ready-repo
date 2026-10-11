---
title: Command and capability reference
summary: Which tool-neutral intent maps to which Wicked Estate command, what each returns, which surface was executed versus read from schemas, and the capabilities that do not exist.
pack: code-intelligence
kind: reference
---

# Command and capability reference

This page is the adopter-facing summary. The authoritative mapping ships inside
the pack, because it is what the agent reads:

- `references/capability-map.md` — every intent, its exact command, and what
  that command returns.
- `references/gaps.md` — a fourteen-point assessment against a general
  code-intelligence contract.
- `references/evidence.md` — how provenance, confidence and completeness are
  carried into an answer.
- `references/investigation-patterns.md` — the five patterns and their stop
  conditions.
- `references/example-prompts.md` — worked examples across debugging, feature
  impact, architecture, refactoring and modernization.

## Two surfaces

Wicked Estate ships a command-line tool and an MCP server. The pack drives the
**CLI** by default, for two reasons: the server advertises 30 tool schemas that
stay resident in the agent's context for a whole session, and the CLI is the
larger surface — 42 names, several with no MCP equivalent.

| Surface | Maturity | Why |
| --- | --- | --- |
| CLI | **validated** | Exercised end to end against a real index; tests pin the returned shapes of `resolve`, `blast-radius` (with `--depth` and `confidence` summary), `path`, `lineage`, `traverse`, `rank` (with `--seeds`), `rules-inventory` (top-level keys; per-engine entry fields are source-read), `rules-recall`, and other verbs on a small fixture |
| MCP | **contract-complete** | Mapped from upstream's registered tools and conformance schemas. Never executed by this pack |

The memory, knowledge, and proposal domains are **MCP-only**. Register the server
only if you need them, and prefer `--readonly`. The richer MCP response shapes
(`summary.top_by_pagerank` on `BlastRadius`, `Communities` summaries,
`ContextBundle`) are also MCP-only.

## Intent to command, in brief

| Intent | Command |
| --- | --- |
| Resolve a name to a stable ID | `wicked-estate resolve <name> --json` |
| Fetch source | `wicked-estate source --symbols <id> --json` |
| What depends on this | `wicked-estate blast-radius <name> [--depth N] --json` |
| What this depends on (forward) | `wicked-estate lineage <symbol> --json` (a name or a symbol id) |
| Walk by direction and edge kind | `wicked-estate traverse <symbol> [--direction ...] [--edge-kinds ...] --json` |
| Route from A to B | `wicked-estate path <from> <to> [--max-depth N] --json` |
| Bounded neighbourhood | `wicked-estate graph-view --focus <name>` |
| Load-bearing symbols | `wicked-estate rank [--seeds ...] [--limit N] --json` |
| Rules inventory | `wicked-estate rules-inventory --json` |
| Rules recall | `wicked-estate rules-recall [--severity ...] --json` |
| Subsystems | `wicked-estate clusters --json` |
| Task context | `wicked-estate context <name> --budget <chars> --json` |
| Graph size and freshness | `wicked-estate stats --json` (indexed commit, index time, commits behind) |

**Traps worth knowing:** `lineage` accepts a name or a symbol id, but an unknown
or ambiguous name exits non-zero with nothing on stdout, so `resolve` first when
a name may be shared. The CLI parses arguments strictly: a malformed value, a
surplus operand, a repeated flag, or a `--db` with no path exits 1 with nothing
on stdout, which is a command error and not an empty answer. Most read commands
refuse a `--db` path that does not exist or is empty with `no graph at <db>`
and create nothing; `clusters`, `context`, `semantic`, `semantics`, `drift`, `cross-graph` and `correspond` instead turn it into an empty graph and return an
empty result. Before running one, check that `stats --json --db <path>` shows a
non-zero `nodes` count for every database it will read. `semantic` and
`clusters --weight semantic` also return an empty result when the index has no
embeddings, with the reason only on stderr, and until `tfstate` has
imported live state, `drift` lists every declared resource as undeployed, which
is not drift. `rank --seeds`
biases a graph-wide ranking — seeded output includes symbols the seeds cannot
reach. To rank a dependent set, keep only the rows whose `symbol` is in your set
and report missing members as unranked.

## What the CLI reports about completeness

- **`blast-radius --json`** returns `unresolved`, `truncated_dependents`,
  `searched_depth`, `depth_horizon_reached`, `node_cap_reached`, and a
  `confidence {min, avg, edge_count}` summary. A true `depth_horizon_reached`
  means more dependents lie beyond the depth searched; raise `--depth`
  (default 12, maximum 24). A true `node_cap_reached` means the node budget cut
  the walk, and no flag raises it. Each `blast-radius` row carries a per-row
  `depth` (1 is a direct dependent) and no per-row confidence.
- **`path --json`** returns `found`, `depth_bounded`, `node_bounded` and
  `unresolved`. `found: false` means no route exists only when `unresolved` is
  null and both bound flags are false. A misspelled name sets `unresolved` and
  still exits 0. With a bound flag true, a route may lie beyond the search.
  `path` follows every dependency edge kind, so read each hop's `kind`. Endpoint
  `line` counts from 0; use `line_1based`.
- Commands served by the same retrieval tools as the MCP server (`lineage`,
  `traverse`, `rank`, `rules-inventory`, `rules-recall`) write `STALENESS:` to
  stderr under `--json`; in text mode they print it on stdout after the result
  (source-read from `tool_bridge.rs`; pinned on `lineage --json`). They print
  `N commit(s)` for each root that is behind, `unknown` for each root whose
  freshness could not be determined, and a single `0 commits` line when every
  root was checked and none is behind (source-read from `main.rs`). `CLAMPED:`, the line printed when a
  limit such as `--depth` above 24 is lowered to its ceiling, follows the same
  channels. `blast-radius` and `path` suppress `STALENESS:` under `--json`, and
  text `stats` stays silent when freshness is unknown, so check freshness with
  `wicked-estate stats --json`: the graph is current only when
  `staleness.commits_behind` is 0 and `staleness.unknown` is empty. `query`,
  `clusters` and `context` print commits-behind lines on stdout before their
  JSON, even under `--json`.

## What does not exist on the CLI

- **A ranked-dependents summary on blast-radius.** MCP `BlastRadius` adds
  `summary.top_by_pagerank`, which the CLI lacks. Its rows carry a per-row
  `depth`, and `--depth 1` still returns only direct dependents; see
  `evidence.md` for the split.
- **Memory, knowledge, and proposal domains.** These have no CLI verb.

## Commands that write

Read-only work needs none of these, and the pack asks before any of them:
`index`, `scip`, `evidence`, `tfstate`, `import-telemetry`, `annotate`, `semantics`,
`compact`, `watch`, `supports retract`, and `clusters --annotate`.

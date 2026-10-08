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
larger surface — 40 names, several with no MCP equivalent.

| Surface | Maturity | Why |
| --- | --- | --- |
| CLI | **validated** | Exercised end to end against a real index; tests pin the returned shapes of `resolve`, `blast-radius` (with `--depth` and `confidence` summary), `path`, `lineage`, `traverse`, `rank` (with `--seeds`), `rules-inventory`, `rules-recall`, and other verbs on a small fixture |
| MCP | **contract-complete** | Mapped from upstream's registered tools and conformance schemas. Never executed by this pack |

The memory, knowledge, and proposal domains are **MCP-only**. Register the server
only if you need them, and prefer `--readonly`. The richer MCP response shapes
(per-dependent `depth` and `summary.top_by_pagerank` on `BlastRadius`,
`Communities` summaries, `ContextBundle`) are also MCP-only.

## Intent to command, in brief

| Intent | Command |
| --- | --- |
| Resolve a name to a stable ID | `wicked-estate resolve <name> --json` |
| Fetch source | `wicked-estate source --symbols <id> --json` |
| What depends on this | `wicked-estate blast-radius <name> [--depth N] --json` |
| What this depends on (forward) | `wicked-estate lineage --symbol <id> --json` (resolve first) |
| Walk by direction and edge kind | `wicked-estate traverse <symbol> [--direction ...] [--edge-kinds ...] --json` |
| Route from A to B | `wicked-estate path <from> <to> [--max-depth N] --json` |
| Bounded neighbourhood | `wicked-estate graph-view --focus <name>` |
| Load-bearing symbols | `wicked-estate rank [--seeds ...] [--limit N] --json` |
| Rules inventory | `wicked-estate rules-inventory --json` |
| Rules recall | `wicked-estate rules-recall [--severity ...] --json` |
| Subsystems | `wicked-estate clusters --json` |
| Task context | `wicked-estate context <name> --budget <chars> --json` |
| Graph size and freshness | `wicked-estate stats` |

**Trap worth knowing:** `lineage` takes an exact SymbolId only — a name returns
an empty result with exit 0, not an error. Always `resolve` first.

## What the CLI reports about completeness

- **`blast-radius --json`** returns `unresolved`, `truncated_dependents`,
  `searched_depth`, `depth_horizon_reached`, `node_cap_reached`, and a
  `confidence {min, avg, edge_count}` summary. A true `depth_horizon_reached`
  means more dependents lie beyond the depth searched; raise `--depth`
  (default 12, maximum 24). A true `node_cap_reached` means the node budget cut
  the walk, and no flag raises it. `blast-radius` rows carry no per-row confidence.
- **`path --json`** returns `found`, `depth_bounded`, `node_bounded` and
  `unresolved`. `found: false` means no route exists only when `unresolved` is
  null and both bound flags are false. A misspelled name sets `unresolved` and
  still exits 0. With a bound flag true, a route may lie beyond the search.
  `path` follows every dependency edge kind, so read each hop's `kind`. Endpoint
  `line` counts from 0; use `line_1based`.
- **Bridged commands** (`traverse`, `rank`, `rules-inventory`, `rules-recall`)
  write `STALENESS:` to stderr even under `--json`. `blast-radius` and `path`
  suppress it under `--json`; use bare `wicked-estate stats` to check freshness
  before those.

## What does not exist on the CLI

- **Per-dependent depth on blast-radius rows.** MCP `BlastRadius` stamps each
  dependent with its `depth`; the CLI form does not. Use `--depth 1` to get only
  direct dependents, and see `evidence.md` for how to split direct from transitive.
- **A structured graph revision field.** Recoverable from a staleness warning
  plus `stats`, not queryable.
- **Memory, knowledge, and proposal domains.** These have no CLI verb.

## Commands that write

Read-only work needs none of these, and the pack asks before any of them:
`index`, `scip`, `tfstate`, `import-telemetry`, `annotate`, `semantics`,
`compact`, `watch`, `supports retract`, and `clusters --annotate`.

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
larger surface — 35 subcommand names, several with no MCP equivalent.

| Surface | Maturity | Why |
| --- | --- | --- |
| CLI | **validated** | Exercised end to end against a real index; tests pin the returned shapes of `resolve`, `blast-radius` (with `--depth`), `path`, and other verbs on a small fixture, and check the rest for acceptance |
| MCP | **contract-complete** | Mapped from upstream's registered tools and conformance schemas. Never executed by this pack |

Four capabilities are **MCP-only**: `Lineage`, `RulesInventory`,
`rules.recall`, and the memory and knowledge domains. Register the server only
if you need them, and prefer `--readonly`.

## Intent to command, in brief

| Intent | Command |
| --- | --- |
| Resolve a name to a stable ID | `wicked-estate resolve <name> --json` |
| Fetch source | `wicked-estate source --symbols <id> --json` |
| What depends on this | `wicked-estate blast-radius <name> [--depth N] --json` |
| Route from A to B | `wicked-estate path <from> <to> [--max-depth N] --json` |
| Bounded neighbourhood | `wicked-estate graph-view --focus <name>` |
| Load-bearing symbols | `wicked-estate rank` |
| Subsystems | `wicked-estate clusters --json` |
| Task context | `wicked-estate context <name> --budget <chars> --json` |
| Graph size and freshness | `wicked-estate stats` |

**One trap worth knowing:** `source`'s selectors (`--symbols`, `--cluster`,
`--file`) and `--signatures-only` are **silently ignored without `--json`**.
The text path re-runs a name search instead, so an ambiguous name returns every
match while appearing pinned to one. Always pass `--json` with a selector.

## What the CLI reports about completeness

- **`blast-radius --json`** returns `unresolved`, `truncated_dependents`,
  `searched_depth`, `depth_horizon_reached` and `node_cap_reached`. A true
  `depth_horizon_reached` means more dependents lie beyond the depth searched;
  raise `--depth` (default 12, maximum 24). A true `node_cap_reached` means the
  node budget cut the walk, and no flag raises it.
- **`path --json`** returns `found`, `depth_bounded`, `node_bounded` and
  `unresolved`. `found: false` means no route exists only when `unresolved` is
  null and both bound flags are false. A misspelled name sets `unresolved` and
  still exits 0. With a bound flag true, a route may lie beyond the search.
  `path` follows every dependency edge kind, so read each hop's `kind`. Endpoint
  `line` counts from 0; use `line_1based`.

## What does not exist

- **Per-edge confidence or provenance on blast-radius rows**, although every
  edge carries them in the model. Use `wicked-estate path A B --json` for
  per-hop evidence on a specific route.
- **Ranked dependents on the CLI.** `rank` is a global top-25 with no seed and
  no input set; MCP `BlastRadius` has `summary.top_by_pagerank`.
- **A structured graph revision field.** Recoverable from a staleness warning
  plus `stats`, not queryable.

## Commands that write

Read-only work needs none of these, and the pack asks before any of them:
`index`, `scip`, `tfstate`, `import-telemetry`, `annotate`, `semantics`,
`compact`, `watch`, and `clusters --annotate`.

# Capability map — tool-neutral intent to Wicked Estate surface

Every row names a command or tool that exists in Wicked Estate 0.21 and says
what it actually returns. Nothing here is aspirational. If an intent has no row,
the capability does not exist — see [`gaps.md`](gaps.md).

**Maturity differs by surface, and so does the evidence behind these rows.**

| Surface | Maturity | Evidence |
| --- | --- | --- |
| CLI | **validated** | Exercised end-to-end against a real index. Tests pin the returned shapes for `resolve`, `blast-radius` (incl. `--depth` and `confidence` summary), `path`, `nodes`, `rank` (incl. `--seeds` and `--json`), `lineage`, `traverse`, `rules-inventory`, `rules-recall`, `source`, `graph-view`, `annotations`, `stale-annotations`, `context`, and `stats`; every other verb is checked for acceptance, not for its return shape. |
| MCP | **contract-complete** | Read from upstream's registered tool names and conformance schemas. **Never executed here** |

Where a row describes MCP behaviour, it states what upstream documents, not
what this pack has observed. Prefer the CLI where both can answer.

Two CLI facts here are also not observed, and are marked where they appear:
the dispatch-arm count below, and the row count in the `nodes` warning. Both
were read from upstream's source and a one-off manual index respectively.

Two surfaces ship, and they are not the same size.

- **The CLI** (`wicked-estate`) accepts 40 names across 35 dispatch arms and 4
  bridged commands — `rank` and `hotspots` are one arm with two names, and the
  4 bridged commands (`traverse`, `rank`, `rules-inventory`, `rules-recall`) share
  tool-bridge infrastructure. Both counts are source-read from upstream's dispatch
  table and `tool_bridge.rs`.
  It is the default provider for this skill: it costs no resident context, and
  it covers several capabilities the MCP server does not expose at all.
- **The MCP server** (`wicked-estate-mcp`) advertises 30 tools without an
  embedding backend and 31 with one (`SemanticSearch`), across an estate domain,
  a memory domain, a knowledge domain, and a proposal queue. Registering it puts
  all tool schemas in the agent's context for the whole session, so this pack
  treats it as opt-in for the MCP-only set: the memory, knowledge, and proposal
  domains, plus the richer MCP response shapes (per-dependent `depth` and
  `summary.top_by_pagerank` on `BlastRadius`, `Communities` summaries, `ContextBundle`).

Throughout: `--db` is optional. The CLI resolves the graph as explicit `--db`,
then `WICKED_ESTATE_DB`, then `.wicked-estate/graph.db`.

---

## Core retrieval

| Intent | CLI | Returns |
| --- | --- | --- |
| Resolve a name to a stable ID | `wicked-estate resolve <name> [--file F] [--kind K] --json` | `[{symbol_id, name, kind, file, line}]`. Use this first — names are not unique. |
| Search for a symbol | `wicked-estate query <name>` | Human-readable match list: kind, name, `file:line`. **No `--json`.** Use `resolve --json` when you need to parse. |
| Inventory nodes by kind or annotation | `wicked-estate nodes [--kind K] [--annotated-with K[=V]] --json` | Per node: `symbol_id`, `name`, `kind`, `file`, `line`, `signature`, `annotation_summary {count, by_type, has_advisory}`, and up to 20 `annotations[]`. **There is no symbol filter** — `--kind` and `--annotated-with` are the only narrowing options, and an unfiltered call returns the whole graph (61,182 rows on one manual index of this repository, 2026-09-30). Never use this to look up one symbol. `nodes --symbol` is not a valid flag and exits non-zero. |
| Add requirement and rule fields | `wicked-estate nodes --json --semantics` | Adds `requirement`, `requirement_validated`, `rule_confidence`, and distinct `out_edges[]` per node. This is a **whole-graph export** that costs an extra semantics read and edge fetch *per node*; scope it with `--kind` or accept the cost deliberately. |
| Fetch source | `wicked-estate source <name> --json` | The exact source slice for matching symbols, with `file:line` provenance. |
| Fetch source in bulk | `wicked-estate source --symbols <ids> [--file <path>] [--cluster <id>] [--json]` | `{nodes[], summary}` for the selected set. Text mode honours `--symbols`; `--cluster`, `--file`, and `--signatures-only` are also honoured in text mode (source-read). `--max-total-chars N` and `--max-node-chars N` require `--json` — without it, the command exits non-zero. Precedence is `--symbols` > `--cluster` > `--file` > `<name>` in both modes (source-read). Output is the indexed revision's text, never confirmation of a call site; `--file` takes a path from your own search or the prompt, not from a provider location field. |
| Semantic search | `wicked-estate semantic "<query>"` | Embedding-ranked symbol matches. **Requires the index to have been built with `--embeddings`**; otherwise unavailable. |

MCP equivalents: `SearchEntity` (name search, ranked, `limit` ≤ 100),
`RetrieveEntity` (one symbol by ID: name, kind, language, `file:line`, signature,
doc comment), `FetchContent` (source slice; returns `found=false` rather than an
error when content was not stored at index time), and `SemanticSearch` — which
the server advertises **only** when an embedding backend is available.

---

## Graph relationships

| Intent | CLI | Returns |
| --- | --- | --- |
| Blast radius / who depends on this | `wicked-estate blast-radius <name> [--depth N] [--json]` | JSON: `{target, dependents[], unresolved, truncated_dependents, searched_depth, depth_horizon_reached, node_cap_reached, confidence}` where `confidence {min, avg, edge_count}` summarises the edges that admitted the rows. Default depth 12, max 24. Text adds an `evidence:` line. Structural `contains` and `defines` edges are excluded from the confidence evidence (source-read from `main.rs`); the traversal itself walks all edge kinds. Read [Completeness](#completeness-fields) below before quoting it. |
| Route from one symbol to another | `wicked-estate path <from> <to> [--max-depth N] --json` | `{from, to, hops[], found, depth_bounded, node_bounded, unresolved}`. Each hop: `{source, target, kind, confidence, provenance, resolved_by}`. Each endpoint: `{symbol, name, kind, file, line, line_1based}` — `line` is 0-based; use `line_1based`. Follows every dependency edge kind; read each hop's `kind`. `found:false` is proven absence only when `unresolved` is null and both bound flags are false. An unknown name sets `unresolved: "from"` or `"to"` and still exits 0. With `depth_bounded:true`, raise `--max-depth` (max 16); with `node_bounded:true`, report the answer as bounded — no flag raises the node budget. |
| Bounded neighbourhood | `wicked-estate graph-view [--focus <name>] [--limit N] [--include-tests] [--include-trivial] [--ignore <pat>]` | A filtered subgraph. `--limit N` controls rows; each edge carries `kind`, `confidence`, `provenance`, `resolved_by`. Upstream does not commit to the JSON shape of `graph-view` output. |
| Walk the graph by direction and edge kind | `wicked-estate traverse <symbol> [--depth N] [--direction dependencies\|dependents\|both] [--edge-kinds a,b] [--max-nodes N] [--json]` | JSON: `{nodes, edges, depths, truncated, searched_depth, depth_horizon_reached, node_cap_reached}`; each edge carries `kind`, `confidence`, `provenance`, `resolved_by`. Over-ceiling `--depth` or `--max-nodes` is clamped with `CLAMPED:` written to stderr. A `--direction` value outside the closed set exits 1. |
| Entry points | `wicked-estate entrypoints --json` | Symbols with no callers or importers. |
| Leaves | `wicked-estate leaves --json` | Symbols that call and import nothing. |
| Unreferenced symbols | `wicked-estate dead-code --json` | Symbols with no edges at all. Absence of an edge is not proof of absence of use — see [`gaps.md`](gaps.md). |
| Cross-repository search | `wicked-estate cross-graph <name> --db a.db --db b.db` | Federated search and blast radius across separately indexed repositories. |
| Full graph export | `wicked-estate export [--format ndjson\|json] [--nodes-only] [--edges-only]` | The whole graph. Use only when a bounded query genuinely cannot answer the question. |

MCP `BlastRadius` returns richer output than the CLI form. Each dependent carries
`depth`, so direct and transitive separate cleanly. The response also carries a
`confidence {min, avg, edge_count}` envelope, a `summary` with `by_kind`,
`top_files`, and `top_by_pagerank` — a ranked-dependents view the CLI does not
offer — and `depth_horizon_reached`, `node_cap_reached`, `searched_depth`.

MCP `TraverseGraph` covers the same intent; the JSON structures are equivalent.
`wicked-estate traverse` supports `--max-nodes` and reports per-node depth in
the `depths` field; it writes `CLAMPED:` to stderr when depth or max-nodes is
clamped (source-read from `tool_bridge.rs`).

MCP `Path` is the equivalent of `wicked-estate path`. It takes `from`, `to`,
`depth` (1–16, default 8), and `max_nodes` (1–5000, default 1000) — inputs
schema-derived. It returns `{hops, found, depth_bounded, node_bounded,
unresolved}`, without the CLI's `from` and `to`, with per-hop `{source, target,
kind, confidence, provenance, resolved_by}` — response shape source-read, since
no response schema ships. Not executed here.

> **Edge direction.** Wicked Estate's invariant is `source = dependent`,
> `target = dependency`. Blast radius is reverse reachability; lineage is
> forward reachability.

---

## Forward dependencies and lineage

| Intent | CLI | Returns |
| --- | --- | --- |
| Transitive dependencies of a symbol | `wicked-estate lineage --symbol <SYMBOL_ID> [--depth N] [--json]` | `{content, diagnostics}` where `content` holds `dependencies[] {symbol, name, kind, file, line, depth}`, `total`, `truncated`, `confidence`, and three cut fields. Default depth 8; `line` is 0-based. Takes an exact SymbolId only — a name returns an empty result with exit 0. Always `resolve` first. |
| Value lineage (TypeScript) | `wicked-estate lineage --symbol <SYMBOL_ID> --relation flows_to [--json]` | Adds `flows[]` rows per hop. Each row carries `producer`, `consumer`, `confidence`, `provenance`, `resolved_by`; when present also `flow_semantics` (`value_preserving` / `may_influence`) and `flow_evidence` (`syntax` / `call_derived` / `convention`). Additional fields may appear; the list is not exhaustive (source-read from `wicked-estate-retrieve` 0.21.0 `flow_hop_row`). TypeScript only. |

`lineage --json` places diagnostics in the `diagnostics` array: always a
placeholder entry, and a real `STALENESS: commits_behind=N` entry when the
graph is behind HEAD (source-read). A depth above 24 or an unsupported
`--relation` exits 1.

MCP `Lineage` covers the same intent. The richer MCP response shapes — per-dependent `depth` and `summary.top_by_pagerank` on `BlastRadius`, `Communities`
summaries, `ContextBundle` — are MCP-only.

---

## Ranking, clustering, and context

| Intent | CLI | Returns |
| --- | --- | --- |
| Hotspots / load-bearing symbols | `wicked-estate rank [--seeds s1,s2,...] [--limit N] [--json]` | JSON: `{hotspots[], total, truncated}` where each hotspot carries `{symbol, name, kind, file, line, line_1based, score}`. `--seeds` personalises PageRank over the **whole graph** — seeded output includes symbols the seeds cannot reach, so it biases rather than filters. An ambiguous seed name exits 1. Default 20 rows, ceiling 200, and a 25,000-character budget (all source-read). To rank a dependent set: `rank --seeds <dependent ids> --limit 200 --json`, then keep only rows whose `symbol` is in your set; report set members absent from the output as unranked (cut by the limit or budget). A seed id containing a comma cannot be seeded (source-read, `tool_bridge.rs`); leave it out and report it as unranked. |
| Architectural communities | `wicked-estate clusters [<min-size>] [--json] [--resolution <γ>] [--hierarchical] [--package-bias <f>]` | Louvain communities over `Calls` + `Imports`. `--json` is a **list of lists of symbol IDs** — no member counts, no ranking, no dominant-file rollup. MCP `Communities` returns those summaries; the CLI does not. `γ > 1.0` yields smaller, tighter clusters. The list index is the `<id>` that `source --cluster` takes. |
| Semantic clustering | `wicked-estate clusters --weight semantic [--k <n> \| --eps <d> --min-pts <n>]` | Embedding-based clustering. Requires an `--embeddings` index. |
| Bounded task context | `wicked-estate context <name> --budget <chars> --json` | Neighbours of up to 20 full-text seed matches, scored by **fixed edge weights, not PageRank**, packed into the character budget. Each row is `{file, kind, line, name}` — note there is no `symbol_id`. |

MCP equivalents: `RankHotspots` (adds `seeds[]` for personalized, subsystem-local
PageRank — same bias-not-filter semantics as the CLI `--seeds`), `Communities`
(`limit`, `min_size`, `resolution`, each summarized with top-PageRank members and
dominant files — `Communities` summaries are MCP-only), and `ContextBundle`
(resolves a seed by `symbol` **or** `query`, ranks neighbours by personalized
PageRank, and packs them as elided stubs within a `budget` capped at 24,000
characters — MCP-only shape).

`ContextBundle` is the closer match to "assemble task context" because it
accepts a free-text seed and returns elided stubs. `context` is the CLI
equivalent and is sufficient for most work.

---

## Rules and requirements

| Intent | CLI | Returns |
| --- | --- | --- |
| Inventory rules-engine nodes | `wicked-estate rules-inventory [--json]` | `{engines, total, rule_nodes: {total, in_rule_sets, ungrouped}}` (pinned by live key assertions). `engines` has one entry per `RuleSet` node; per-engine fields `{symbol, name, kind, file, invoked_by}` are source-read from `wicked-estate-retrieve` `RulesInventory` (the fixture has no RuleSet). `rule_nodes` counts `Rule` nodes (not listed). An unknown flag exits 1. |
| Recall conformance rules | `wicked-estate rules-recall [--severity \| --rule-type \| --language \| --layer \| --framework \| --scope \| --projects \| --limit] [--json]` | Faceted, severity-ordered rules. Filters: `framework`, `language`, `layer`, `rule_type` (`pattern` \| `policy`), `scope`, `severity` (`info` \| `warn` \| `error` \| `critical`), `limit`, `projects` (array of strings — a project-scoped rule is returned only when its project is listed; omit/empty for global rules only). Results within a severity are ordered by weight then id. An unknown flag exits 1. |
| Symbols satisfying a requirement | `wicked-estate by-requirement <requirement>` | Symbols annotated as satisfying that requirement, with `file:line`. Not listed in `--help`; it is in the CLI's dispatch table. |
| Requirement linkage per symbol | `wicked-estate nodes --json --semantics` | Adds `requirement` and `requirement_validated` to each node. |
| Trace code to a rules engine | `wicked-estate traverse <symbol> --edge-kinds invoked_by [--json]` | Walk from code symbols to the rules engine along `invoked_by` edges. Combine with `rules-inventory` to map the full rule graph. |

MCP equivalents for rules: `RulesInventory` and `rules.recall` match the CLI
commands. MCP `TraverseGraph` with `edge_kinds: ["governs"]` gives ruleset →
rule structure; `["evaluates"]` gives rule → condition.

Requirement linkage is **populated by a write** — `wicked-estate semantics
<symbol> --requirement <id> [--validated true|false --validated-by <actor>]`.
An estate nobody has annotated returns nothing here, and that is an empty
result, not a contradiction. Do not run the write to make the read succeed.

---

## Provenance, confidence, and freshness

| Intent | CLI | Returns |
| --- | --- | --- |
| Read the evidence envelope | `wicked-estate annotations <name> [--type T] --json` | An **array** of `{symbol, annotations[]}` — one entry per name match. Only the `--symbol <id>` form returns a single object. Each annotation carries `key`, `value`, `type`, `confidence`, `provenance`, `author`, `ts`, and `advisory`. There is **no `last_verified` field in the JSON**; `ts` is the timestamp you get. |
| Find stale evidence | `wicked-estate stale-annotations <cutoff-unix-seconds> --json` | An array of `{symbol, annotation}` pairs older than the cutoff. The cutoff is **Unix seconds** — a date string is rejected with a usage error. Never-verified rows are always stale. |
| Graph identity and size | `wicked-estate stats` | Node and edge counts by kind, a **graph-wide `unresolved` total**, database size, git provenance when indexed from a checkout, and the per-repository registry in a multi-repo graph. |
| Symbol fingerprint | `wicked-estate fingerprint <name>` | A stable hex fingerprint for the symbol, for detecting change across revisions. |
| What changed since a revision | `wicked-estate changed-since <sha> --json` | Symbols in files changed since that git SHA. |
| Index freshness | `wicked-estate stats` or bridged commands (`traverse`, `rank`, `rules-inventory`, `rules-recall`) | `STALENESS: N commit(s) in '<label>' since last index`. Under `--json`, bridged commands write this to stderr; in text mode, diagnostics go to stdout (source-read from `tool_bridge.rs`; pinned on `rank --json`). `blast-radius` and `path` suppress `STALENESS:` under `--json` so machine output stays one document; use bare `wicked-estate stats` to check freshness before those. `lineage --json` carries staleness in its `diagnostics` array (source-read). |
| Clamped output | `wicked-estate traverse`, `rank`, and other bridged commands | When `--depth` or `--max-nodes` exceeds the ceiling, the command clamps and writes `CLAMPED: <param>=<asked> is above this tool's ceiling; used <param>=<ceiling>` to stderr, even under `--json`. The value after `used` is the one applied. |

---

## Completeness fields

Four limits decide whether an answer is a total or a floor. The CLI and the MCP
server **use different field names for the same ideas** — do not read one set
from the other.

| Limit | CLI field | MCP field | Means |
| --- | --- | --- | --- |
| Unbound call sites | `unresolved` | `unresolved_callers` | References the resolver could not bind. Potential missing dependents. |
| Output cut | `truncated_dependents` (rows dropped) | `truncated` (boolean) plus `total` | The list is a prefix. |
| Traversal depth cap | `searched_depth`, `depth_horizon_reached`, `node_cap_reached` | `depth_horizon_reached`, `node_cap_reached`, `searched_depth` | Use `blast-radius <name> --depth N` (default 12, max 24) to control reach. |
| Index freshness | `STALENESS:` line — `stats` and bridged commands; suppressed by `blast-radius`/`path` under `--json` | not surfaced | The graph describes an older revision. |
| Source-bundle cut | `summary.truncated_count` with `requested` / `returned` | n/a | `source --json` reports how many of the selected symbols it actually returned within `budget`. A large `--cluster` easily exceeds it. |

**The depth cut is reported.** `blast-radius --json` returns `searched_depth`,
`depth_horizon_reached`, and `node_cap_reached`. When `depth_horizon_reached` is
true, the text output prints a `CUT AT depth=N` line; raise `--depth` (max 24) to
go further. Use `blast-radius <name> --depth 1` to get only direct dependents. Whether the difference against the full run is the transitive set depends on conditions stated in [`evidence.md` § Direct and transitive dependents](evidence.md#direct-and-transitive-dependents).
A true `node_cap_reached` means the node budget cut the walk; no CLI flag raises
it. `path` hops carry `confidence`, `provenance`, and `resolved_by` per hop;
`blast-radius` rows carry no per-row confidence — the summary `confidence` object
covers the full traversal, not individual rows.

MCP `BlastRadius` takes an explicit `depth` (default 8, max 24) and returns a
per-dependent `depth`, plus `depth_horizon_reached`, `node_cap_reached`, and
`searched_depth`, so the horizon is fully visible there. MCP `TraverseGraph`
truncates at `max_nodes` (default 200, max 1000) and reports depth per node, so
a result at the cap is also a floor.

---

## Infrastructure and cross-estate

| Intent | CLI | Returns |
| --- | --- | --- |
| Index live Terraform state | `wicked-estate tfstate <file>` | Writes. Indexes live infrastructure state into the graph. |
| IaC versus live drift | `wicked-estate drift` | Differences between declared infrastructure and live resources. |
| Match symbols across two graphs | `wicked-estate correspond --db-a A.db --db-b B.db [--kind K] [--top N] [--min-score F] [--explain] [--json]` | Scored candidate pairs between two separately indexed repositories. Lexical BM25 only unless both graphs carry embeddings, in which case it fuses lexical and vector ranking. |

`correspond` is the only comparison primitive Wicked Estate ships. It matches
symbols between two graphs; it does not diff two revisions of one graph.

---

## Memory, knowledge, and proposals — MCP only

Eighteen tools across three domains, none with a CLI verb. This pack does not
build a workflow on them, and deliberately ships no separate skill for them:
they are optional, they are unavailable in the default CLI-only setup, and a
skill that only fires when an optional server is registered triggers unreliably.

- **Memory (7):** `memory.capture`, `memory.recall`, `memory.reflect`,
  `memory.erase`, `memory.learn`, `memory.coverage`, `memory.list`.
  `memory.learn` is the one most relevant here — it stores a non-obvious fact
  about the codebase linked by name to the symbols it concerns.
- **Knowledge (7):** `knowledge.ingest`, `knowledge.write`, `knowledge.relate`,
  `knowledge.recall`, `knowledge.coverage`, `knowledge.relate_code`,
  `knowledge.recall_about_code`. `knowledge.recall_about_code` surfaces
  documentation linked to a code symbol with no lexical overlap needed.
- **Proposal queue (4):** `proposal.submit`, `proposal.list`, `proposal.approve`,
  `proposal.reject`.

Ten of these mutate state. Running `wicked-estate-mcp --readonly` drops the
write tools from the advertised set, leaving 20 read tools (21 with SemanticSearch).
Prefer it.

---

## Registering the MCP server, if you need it

Register for the memory, knowledge, and proposal domains, which have no CLI verb,
or when the richer MCP response shapes are needed (per-dependent `depth` and
`summary.top_by_pagerank` on `BlastRadius`, `Communities` summaries, `ContextBundle`):

```bash
claude mcp add wicked-estate -s project -- \
  wicked-estate-mcp --readonly --db "$PWD/.wicked-estate/graph.db"
```

The server also publishes six bundled skills as `skill://` MCP resources and one
prompt named `expedition`. Those are Wicked Estate's own authored guidance, not
part of this pack.

---

## Commands that write

Read-only work never needs these. Ask before running any of them.

`index`, `scip`, `tfstate`, `import-telemetry`, `annotate`, `semantics`,
`compact`, `watch`, `subscribe` (polls a change log; harmless but stateful),
`supports retract` (removes edge support), and `clusters --annotate`,
which writes a `community` annotation onto every member symbol.

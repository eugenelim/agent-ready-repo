# Capability map — tool-neutral intent to Wicked Estate surface

Every row names a command or tool that exists in Wicked Estate 0.16 and says
what it actually returns. Nothing here is aspirational. If an intent has no row,
the capability does not exist — see [`gaps.md`](gaps.md).

Two surfaces ship, and they are not the same size.

- **The CLI** (`wicked-estate`) accepts 34 subcommand names across 33 dispatch
  arms (`rank` and `hotspots` are one arm with two names). It is the default
  provider for this skill: it costs no resident context, and it covers several
  capabilities the MCP server does not expose at all.
- **The MCP server** (`wicked-estate-mcp`) advertises 29 tools across an estate
  domain, a memory domain, a knowledge domain, and a proposal queue. Registering
  it puts all 29 tool schemas in the agent's context for the whole session, so
  this pack treats it as opt-in for the four capability areas with no CLI verb.

Throughout: `--db` is optional. The CLI resolves the graph as explicit `--db`,
then `WICKED_ESTATE_DB`, then `.wicked-estate/graph.db`.

---

## Core retrieval

| Intent | CLI | Returns |
| --- | --- | --- |
| Resolve a name to a stable ID | `wicked-estate resolve <name> [--file F] [--kind K] --json` | `[{symbol_id, name, kind, file, line}]`. Use this first — names are not unique. |
| Search for a symbol | `wicked-estate query <name>` | Human-readable match list: kind, name, `file:line`. **No `--json`.** Use `resolve --json` when you need to parse. |
| Inventory nodes by kind or annotation | `wicked-estate nodes [--kind K] [--annotated-with K[=V]] --json` | Per node: `symbol_id`, `name`, `kind`, `file`, `line`, `signature`, `annotation_summary {count, by_type, has_advisory}`, and up to 20 `annotations[]`. **There is no symbol filter** — `--kind` and `--annotated-with` are the only narrowing options, and an unfiltered call returns the whole graph (61,182 rows on a mid-size repository). Never use this to look up one symbol. |
| Add requirement and rule fields | `wicked-estate nodes --json --semantics` | Adds `requirement`, `requirement_validated`, `rule_confidence`, and distinct `out_edges[]` per node. This is a **whole-graph export** that costs an extra semantics read and edge fetch *per node*; scope it with `--kind` or accept the cost deliberately. |
| Fetch source | `wicked-estate source <name> --json` | The exact source slice for matching symbols, with `file:line` provenance. |
| Fetch source in bulk | `wicked-estate source --symbols <ids> \| --file <path> \| --cluster <id>` | Same, for a symbol set. Precedence is `--symbols` > `--cluster` > `--file` > `<name>`. Bound it with `--signatures-only`, `--max-total-chars N`, `--max-node-chars N`. |
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
| Blast radius / who depends on this | `wicked-estate blast-radius <name> --json` | `{target, dependents[], unresolved, truncated_dependents}`. Read [Completeness](#completeness-fields) below before quoting it. |
| Bounded neighbourhood | `wicked-estate graph-view [--focus <name>] [--limit N] [--include-tests] [--include-trivial] [--ignore <pat>]` | A filtered subgraph around the focus symbol. Trivial nodes and tests are excluded unless asked for. |
| Entry points | `wicked-estate entrypoints --json` | Symbols with no callers or importers. |
| Leaves | `wicked-estate leaves --json` | Symbols that call and import nothing. |
| Unreferenced symbols | `wicked-estate dead-code --json` | Symbols with no edges at all. Absence of an edge is not proof of absence of use — see [`gaps.md`](gaps.md). |
| Cross-repository search | `wicked-estate cross-graph <name> --db a.db --db b.db` | Federated search and blast radius across separately indexed repositories. |
| Full graph export | `wicked-estate export [--format ndjson\|json] [--nodes-only] [--edges-only]` | The whole graph. Use only when a bounded query genuinely cannot answer the question. |

MCP equivalents: `TraverseGraph` is the closest thing to a general walk and has
no CLI counterpart with the same shape — it takes `symbol`, `depth` (≤ 16),
`direction` (`dependencies` / `dependents` / `both`), `edge_kinds[]`, and
`max_nodes` (≤ 1000), and returns nodes, edges, and depths.

MCP `BlastRadius` returns **considerably more than the CLI form**, and it is
worth registering the server when impact work is the session's main job. Each
dependent carries `depth`, so direct and transitive separate cleanly. The
response also carries a `confidence {min, avg, edge_count}` envelope over the
traversal edges, and a `summary` with `by_kind`, `top_files`, and
`top_by_pagerank` — the last being the only way to rank dependents by
importance, since the CLI's `rank` cannot take a supplied set.

> **Edge direction.** Wicked Estate's invariant is `source = dependent`,
> `target = dependency`. Blast radius is reverse reachability; lineage is
> forward reachability.

---

## Forward dependencies and lineage

| Intent | Surface | Returns |
| --- | --- | --- |
| Transitive dependencies of a symbol | **MCP only** — `Lineage` | Forward reachability over `Calls` + `Imports`, to `depth` ≤ 24. The complement of `BlastRadius`. |

The CLI has **no lineage subcommand at all.** The nearest CLI approximation
is `graph-view --focus <name>`, which returns a bounded neighbourhood rather
than transitive forward reachability, and `leaves` for terminal symbols. Say
which one you used; they are not interchangeable.

---

## Ranking, clustering, and context

| Intent | CLI | Returns |
| --- | --- | --- |
| Hotspots / load-bearing symbols | `wicked-estate rank` | The global top 25 symbols by PageRank over `Calls` + `Imports`, as text. **Fixed at 25, ignores `--json`, and takes no seed or filter** — so it cannot rank a supplied set such as a blast radius. |
| Architectural communities | `wicked-estate clusters [<min-size>] [--json] [--resolution <γ>] [--hierarchical] [--package-bias <f>]` | Louvain communities over `Calls` + `Imports`. `γ > 1.0` yields smaller, tighter clusters. |
| Semantic clustering | `wicked-estate clusters --weight semantic [--k <n> \| --eps <d> --min-pts <n>]` | Embedding-based clustering. Requires an `--embeddings` index. |
| Bounded task context | `wicked-estate context <name> --budget <chars> --json` | Neighbours of up to 20 full-text seed matches, scored by **fixed edge weights, not PageRank**, packed into the character budget. Each row is `{file, kind, line, name}` — note there is no `symbol_id`. |

MCP equivalents: `RankHotspots` (adds `seeds[]` for personalized, subsystem-local
PageRank — the CLI `rank` has no seed bias), `Communities` (`limit`, `min_size`,
`resolution`, each summarized with top-PageRank members and dominant files), and
`ContextBundle` (resolves a seed by `symbol` **or** `query`, ranks neighbours by
personalized PageRank, and packs them as elided stubs within a `budget` capped at
24,000 characters).

`ContextBundle` is the closer match to "assemble task context" because it
accepts a free-text seed and returns elided stubs. `context` is the CLI
equivalent and is sufficient for most work.

---

## Rules and requirements

| Intent | Surface | Returns |
| --- | --- | --- |
| Inventory rules-engine nodes | **MCP only** — `RulesInventory` | `[{name, kind, file, invoked_by: [code_files]}]` for every `RuleSet` and `Rule` node, and the code that invokes them. Takes no parameters. |
| Recall conformance rules | **MCP only** — `rules.recall` | Faceted, severity-ordered rules. Filters: `framework`, `language`, `layer`, `rule_type` (`pattern` \| `policy`), `scope`, `severity` (`info` \| `warn` \| `error` \| `critical`), `limit`. Read-only by design; there is deliberately no write counterpart. |
| Symbols satisfying a requirement | `wicked-estate by-requirement <requirement>` | Symbols annotated as satisfying that requirement, with `file:line`. Not listed in `--help`; it is in the CLI's dispatch table. |
| Requirement linkage per symbol | `wicked-estate nodes --json --semantics` | Adds `requirement` and `requirement_validated` to each node. |
| Trace code to a rules engine | **MCP only** — `TraverseGraph` with `edge_kinds` | `["invoked_by"]` traces code → rules; `["governs"]` gives ruleset → rule structure; `["evaluates"]` gives rule → condition. |

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
| Graph identity and size | `wicked-estate stats` | Node and edge counts by kind, plus git provenance when the repository was indexed from a checkout, plus the per-repository registry in a multi-repo graph. |
| Symbol fingerprint | `wicked-estate fingerprint <name>` | A stable hex fingerprint for the symbol, for detecting change across revisions. |
| What changed since a revision | `wicked-estate changed-since <sha> --json` | Symbols in files changed since that git SHA. |
| Index freshness | `wicked-estate stats`, or any non-`--json` read | `STALENESS: N commit(s) in '<label>' since last index`. **Only five subcommands print it** — `query`, `blast-radius`, `stats`, `clusters`, `context` — and `blast-radius` suppresses it under `--json` so machine output stays one document. The `--json` calls this skill teaches therefore never show it: get freshness from a bare `wicked-estate stats`. |

---

## Completeness fields

Four limits decide whether an answer is a total or a floor. The CLI and the MCP
server **use different field names for the same ideas** — do not read one set
from the other.

| Limit | CLI field | MCP field | Means |
| --- | --- | --- | --- |
| Unbound call sites | `unresolved` | `unresolved_callers` | References the resolver could not bind. Potential missing dependents. |
| Output cut | `truncated_dependents` (rows dropped) | `truncated` (boolean) plus `total` | The list is a prefix. |
| Traversal depth cap | **none — unreported** | `depth` per dependent, `depth` request parameter | See below. |
| Index freshness | `STALENESS:` line, five commands only | not surfaced | The graph describes an older revision. |

**The unreported one matters most.** The CLI hardcodes its blast-radius
traversal to **depth 12**. Dependents further away are dropped, and they are
counted in neither `unresolved` (which counts unbound references to the target
name) nor `truncated_dependents` (a character-budget cut). So a CLI blast radius
has a silent horizon, and nothing in the output tells you whether you hit it.
MCP `BlastRadius` takes an explicit `depth` (default 8, max 24) and returns a
per-dependent `depth`, so the horizon is at least visible there.

MCP `TraverseGraph` truncates at `max_nodes` (default 200) and reports depth per
node, so a result at the cap is also a floor.

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

## Memory and knowledge — MCP only

Fourteen tools across two domains, none with a CLI verb. This pack does not
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
write tools from the advertised set, leaving 19 read tools. Prefer it.

---

## Registering the MCP server, if you need it

Only when the session needs `Lineage`, rules, memory, or knowledge:

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
and `clusters --annotate`, which writes a `community` annotation onto every
member symbol.

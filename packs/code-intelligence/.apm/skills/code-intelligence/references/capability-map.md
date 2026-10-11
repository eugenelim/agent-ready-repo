# Capability map — tool-neutral intent to Wicked Estate surface

Every row names a command or tool that exists in Wicked Estate 0.26 and says
what it actually returns. Nothing here is aspirational. If an intent has no row,
the capability does not exist — see [`gaps.md`](gaps.md).

**Maturity differs by surface, and so does the evidence behind these rows.**

| Surface | Maturity | Evidence |
| --- | --- | --- |
| CLI | **validated** | Exercised end-to-end against a real index. Tests pin the returned shapes for `resolve`, `blast-radius` (incl. `--depth` and `confidence` summary), `path`, `nodes`, `rank` (incl. `--seeds` and `--json`), `lineage`, `traverse`, `rules-inventory`, `rules-recall`, `source`, `graph-view`, `annotations`, `stale-annotations`, `context`, and `stats`; every other verb is checked for acceptance, not for its return shape. |
| MCP | **contract-complete** | Read from upstream's registered tool names and conformance schemas. **Never executed here** |

Where a row describes MCP behaviour, it states what upstream documents, not
what this pack has observed. Prefer the CLI where both can answer.

Some CLI facts here are also not observed, and are marked where they appear.
The dispatch counts below and the value-lineage coverage and hops were read
from upstream's source (source-read). The row count in the `nodes` warning
comes from a one-off manual index. Provenance labels are executed (the CLI,
run on 0.26.0), schema-derived (MCP rows), and source-read (read from the 0.26.0
sources).

`wicked-estate` parses its arguments strictly. A malformed value, a surplus or
missing operand, a repeated flag, or a `--db` with no path exits 1 with nothing
on stdout and usage on stderr (executed). Most read commands refuse a `--db`
path that does not exist or is empty with `no graph at <db>` and create
nothing. Read an exit 1 or a `no graph at <db>` refusal as a command error,
never as an empty answer. `clusters`, `context`, `semantic`, `semantics`, `drift`, `cross-graph` and `correspond` instead turn a missing or empty database path
into an empty graph and exit 0 with an empty result (source-read from
`main.rs`). Their empty result is a real answer only once `stats --json --db
<path>` reports a non-zero `nodes` count for every database the command read.

Two surfaces ship, and they are not the same size.

- **The CLI** (`wicked-estate`) accepts 42 names: 35 bespoke dispatch arms, 5
  bridged commands (`lineage`, `traverse`, `rank`, `rules-inventory`,
  `rules-recall`) that share tool-bridge infrastructure, the `hotspots` alias
  for `rank`, and `version`, which is matched before dispatch. Every count is
  source-read from upstream's dispatch table and `tool_bridge.rs`.
  It is the default provider for this skill: it costs no resident context, and
  it covers several capabilities the MCP server does not expose at all.
- **The MCP server** (`wicked-estate-mcp`) advertises 30 tools without an
  embedding backend and 31 with one (`SemanticSearch`), across an estate domain,
  a memory domain, a knowledge domain, and a proposal queue. Registering it puts
  all tool schemas in the agent's context for the whole session, so this pack
  treats it as opt-in for the MCP-only set: the memory, knowledge, and proposal
  domains, plus the richer MCP response shapes (`summary.top_by_pagerank` on
  `BlastRadius`, `Communities` summaries, `ContextBundle`).

Throughout: `--db` is optional. The CLI resolves the graph as explicit `--db`,
then `WICKED_ESTATE_DB`, then `.wicked-estate/graph.db`.

---

## Core retrieval

| Intent | CLI | Returns |
| --- | --- | --- |
| Resolve a name to a stable ID | `wicked-estate resolve <name> [--file F] [--kind K] [--include-values] --json` | `[{symbol_id, name, kind, file, line}]`. Use this first — names are not unique. Plain `resolve` returns structural symbols only; `--include-values` adds value slots such as parameters and locals, the seeds a value-lineage query needs (source-read). |
| Search for a symbol | `wicked-estate query <name> [--json]` | Human-readable match list: kind, name, `file:line`. `--json` returns the same rows as `resolve --json`: `[{symbol_id, name, kind, file, line}]` (executed). On a stale graph, commits-behind `STALENESS:` lines precede the JSON on stdout (source-read from `main.rs`). Structural symbols only. |
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
| Blast radius / who depends on this | `wicked-estate blast-radius <name> [--depth N] [--json]` | JSON: `{target, dependents[], unresolved, truncated_dependents, searched_depth, depth_horizon_reached, node_cap_reached, confidence}`. Each dependent row is `{id, name, kind, file, line, depth}`, and the per-row `depth` is 1 for a direct dependent (executed). `confidence {min, avg, edge_count}` summarises the edges that admitted the rows. Default depth 12, max 24. Text adds an `evidence:` line. Structural `contains` and `defines` edges are excluded from the confidence evidence (source-read from `main.rs`); the traversal itself walks all edge kinds. Read [Completeness](#completeness-fields) below before quoting it. |
| Route from one symbol to another | `wicked-estate path <from> <to> [--max-depth N] --json` | `{from, to, hops[], found, depth_bounded, node_bounded, unresolved}`. Each hop: `{source, target, kind, confidence, provenance, resolved_by}`. Each endpoint: `{symbol, name, kind, file, line, line_1based}` — `line` is 0-based; use `line_1based`. Follows every dependency edge kind; read each hop's `kind`. `found:false` is proven absence only when `unresolved` is null and both bound flags are false. An unknown name sets `unresolved: "from"` or `"to"` and still exits 0. With `depth_bounded:true`, raise `--max-depth` (max 16); with `node_bounded:true`, report the answer as bounded — no flag raises the node budget. |
| Bounded neighbourhood | `wicked-estate graph-view [--focus <name>] [--limit N] [--include-tests] [--include-trivial] [--ignore <pat>]` | A filtered subgraph. `--limit N` controls rows; each edge carries `kind`, `confidence`, `provenance`, `resolved_by`. Upstream does not commit to the JSON shape of `graph-view` output. |
| Walk the graph by direction and edge kind | `wicked-estate traverse <symbol> [--depth N] [--direction dependencies\|dependents\|both] [--edge-kinds a,b] [--max-nodes N] [--json]` | JSON: `{nodes, edges, depths, truncated, searched_depth, depth_horizon_reached, node_cap_reached}`; each edge carries `kind`, `confidence`, `provenance`, `resolved_by`. Over-ceiling `--depth` or `--max-nodes` is clamped with `CLAMPED:` written to stderr. A `--direction` value outside the closed set exits 1. |
| Entry points | `wicked-estate entrypoints --json` | Symbols with no callers or importers. |
| Leaves | `wicked-estate leaves --json` | Symbols that call and import nothing. |
| Unreferenced symbols | `wicked-estate dead-code --json` | Symbols with no edges at all. Absence of an edge is not proof of absence of use — see [`gaps.md`](gaps.md). |
| Cross-repository search | `wicked-estate cross-graph <name> --db a.db --db b.db` | Federated search and blast radius across separately indexed repositories. |
| Full graph export | `wicked-estate export [--format ndjson\|json] [--nodes-only] [--edges-only]` | The whole graph. Use only when a bounded query genuinely cannot answer the question. |

MCP `BlastRadius` returns richer output than the CLI form in one respect. Both
surfaces stamp each dependent with `depth`, so direct and transitive separate
cleanly. The MCP response also carries a `summary` with `by_kind`, `top_files`,
and `top_by_pagerank` — a ranked-dependents view the CLI does not offer. Both
carry a `confidence {min, avg, edge_count}` summary and `depth_horizon_reached`,
`node_cap_reached`, `searched_depth`.

MCP `TraverseGraph` covers the same intent; the JSON structures are equivalent.
`wicked-estate traverse` supports `--max-nodes` and reports per-node depth in
the `depths` field. Under `--json` it writes `CLAMPED:` to stderr when depth or
max-nodes is clamped; in text mode the line prints on stdout after the result
(source-read from `tool_bridge.rs`).

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
| Transitive dependencies of a symbol | `wicked-estate lineage <symbol> [--depth N] [--json]` | `<symbol>` is a name or an exact symbol id; `--symbol` is not a flag and exits 1. `--json` prints the result object directly: `{dependencies[] {symbol, name, kind, file, line, depth}, total, truncated, confidence, relation, searched_depth, depth_horizon_reached, node_cap_reached}`. `relation` echoes `dependency`. Default depth 8; `line` is 0-based. An unknown or ambiguous name exits non-zero with nothing on stdout, so `resolve` first when a name may be shared (executed). |
| Value lineage (TypeScript, TSX, JavaScript) | `wicked-estate lineage <symbol> --relation flows_to [--json]` | Adds `flows[]` rows per hop and echoes `relation` as `flows_to`. Each row carries `producer`, `consumer`, `confidence`, `provenance`, `resolved_by`; when present also `flow_semantics` (`value_preserving` / `may_influence`) and `flow_evidence` (`syntax` / `call_derived` / `convention` / `compiler`). Seed it with a parameter or local found by `resolve <name> --include-values --json`. Coverage is `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, and `.cjs` (source-read); callbacks, `await` and `.then`, destructuring, loops, local object properties, and closure returns add hops, almost all `may_influence`. Any `--relation` other than `flows_to` exits 1 (executed). The `flows[]` fields and the new hop kinds are source-read from the 0.26.0 sources; the Python fixture produces no value flow. |

A `--depth` above 24 is clamped to 24, and `CLAMPED:` goes to stderr under
`--json` and to stdout after the result in text mode (executed under `--json`).
`lineage` is a bridged command, so `STALENESS:` follows the same channel rule:
stderr under `--json`, stdout after the result in text mode (executed under
`--json`; text mode source-read from `tool_bridge.rs`).

MCP `Lineage` covers the same intent and echoes `relation` (schema-derived). The
richer MCP response shapes — `summary.top_by_pagerank` on `BlastRadius`,
`Communities` summaries, `ContextBundle` — are MCP-only.

---

## Ranking, clustering, and context

| Intent | CLI | Returns |
| --- | --- | --- |
| Hotspots / load-bearing symbols | `wicked-estate rank [--seeds s1,s2,...] [--limit N] [--json]` | JSON: `{hotspots[], total, truncated}` where each hotspot carries `{symbol, name, kind, file, line, line_1based, score}`. `--seeds` personalises PageRank over the **whole graph** — seeded output includes symbols the seeds cannot reach, so it biases rather than filters. An ambiguous seed name exits 1. Default 20 rows, ceiling 200, and a 25,000-character budget (all source-read). To rank a dependent set: `rank --seeds <dependent ids> --limit 200 --json`, then keep only rows whose `symbol` is in your set; report set members absent from the output as unranked (cut by the limit or budget). A seed id containing a comma cannot be seeded (source-read, `tool_bridge.rs`); leave it out and report it as unranked. |
| Architectural communities | `wicked-estate clusters [<min-size>] [--json] [--resolution <γ>] [--hierarchical] [--package-bias <f>]` | Louvain communities over `Calls` + `Imports`. `--json` is a **list of lists of symbol IDs** — no member counts, no ranking, no dominant-file rollup. On a stale graph, commits-behind `STALENESS:` lines precede the JSON on stdout (source-read from `main.rs`). MCP `Communities` returns those summaries; the CLI does not. `γ > 1.0` yields smaller, tighter clusters. The list index is the `<id>` that `source --cluster` takes. |
| Semantic clustering | `wicked-estate clusters --weight semantic [--k <n> \| --eps <d> --min-pts <n>]` | Embedding-based clustering. Requires an `--embeddings` index. |
| Bounded task context | `wicked-estate context <name> --budget <chars> --json` | Neighbours of up to 20 full-text seed matches, scored by **fixed edge weights, not PageRank**, packed into the character budget. Each row is `{file, kind, line, name}` — note there is no `symbol_id`. On a stale graph, commits-behind `STALENESS:` lines precede the JSON on stdout (source-read from `main.rs`). |

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
| Recall conformance rules | `wicked-estate rules-recall [--severity \| --rule-type \| --steering-type \| --language \| --layer \| --framework \| --scope \| --projects \| --limit] [--json]` | Faceted, severity-ordered rules. Filters: `framework`, `language`, `layer`, `rule_type` (`pattern` \| `policy`), `steering_type` (`architecture` \| `development` \| `security` \| `testing` \| `operations` \| `compliance` \| `design-ux`; exact match, and a rule with no steering type counts as `architecture`; source-read from `tool_bridge.rs`), `scope`, `severity` (`info` \| `warn` \| `error` \| `critical`), `limit`, `projects` (array of strings — a project-scoped rule is returned only when its project is listed; omit/empty for global rules only). Results within a severity are ordered by weight then id. An unknown flag exits 1. |
| Symbols satisfying a requirement | `wicked-estate by-requirement <requirement>` | Symbols annotated as satisfying that requirement, with `file:line`. `--help` lists every dispatched command (source-read). |
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
| Read the evidence envelope | `wicked-estate annotations <name> [--type T] --json` | An **array** of `{symbol, annotations[]}` — one entry per name match. Only the `--symbol <id>` form returns a single object. Each annotation carries `key`, `value`, `type`, `confidence`, `provenance`, `author`, `ts`, `advisory`, `source_type`, `extraction_method`, and `last_verified` (executed). |
| Find stale evidence | `wicked-estate stale-annotations <cutoff> --json` | An array of `{symbol, annotation}` pairs older than the cutoff. Give exactly one cutoff: Unix seconds, a `YYYY-MM-DD` date, or `--older-than <N>{s,m,h,d,w}`; two cutoffs exit non-zero. Never-verified rows are always stale. |
| Read resolution provenance | `wicked-estate path`, `traverse`, `graph-view` edge fields | Each edge carries `provenance` and `resolved_by`. `compiler` is a resolution tier and a provenance value. A SCIP import adds reference support and never call edges (source-read). |
| Graph identity and size | `wicked-estate stats [--json]` | Node and edge counts by kind, a **graph-wide `unresolved` total**, database size, and the per-repository registry in a multi-repo graph. `--json` adds `provenance {commit, branch, remote, dirty, indexed_root, indexed_at, indexed_version, …}` and `staleness {checked, commits_behind, unknown[]}`. `commit` is null outside a git checkout. A graph indexed with `--repo` leaves `commit`, `branch`, `dirty`, `id_scheme` and `indexed_version` null in `provenance` and reports them per repository under `repos[]`, with each repository's `commits_behind`; `commits_behind` is null when no indexed root could be checked, and `unknown` names those roots (source-read from `main.rs`). |
| Symbol fingerprint | `wicked-estate fingerprint <name>` | A stable hex fingerprint for the symbol, for detecting change across revisions. |
| What changed since a revision | `wicked-estate changed-since <sha> --json` | Symbols in files changed since that git SHA. |
| Index freshness | `wicked-estate stats --json`, or the `STALENESS:` line from bridged commands (`lineage`, `traverse`, `rank`, `rules-inventory`, `rules-recall`) | `stats --json` prints one JSON document carrying freshness as `staleness.commits_behind`; stderr may carry a `VERSION MISMATCH:` or `SYMBOL-ID SCHEME MISMATCH:` warning, which calls for re-indexing (source-read from `main.rs`). Bridged commands print a `STALENESS:` line for each stale or unknown root, or a single `0 commits` line when every root was checked and none is behind: `N commit(s) since last index` (stale), `0 commits since last index` (current for every checked root), `unknown for <root> — freshness could not be determined`, or `unknown — <db> records no indexed root to check`. An `unknown` line is not a revision gap (source-read from `main.rs`). Under `--json` the line goes to stderr and stdout stays one JSON document (executed on `lineage --json`); in text mode it follows the result on stdout (source-read from `tool_bridge.rs`). `path`, `blast-radius` and text `stats` print only commits-behind lines, so their silence does not prove the graph is current (source-read from `main.rs`); `blast-radius` and `path` also suppress the line under `--json`. `query`, `clusters` and `context` print commits-behind lines on stdout before the JSON even under `--json` (source-read from `main.rs`). |
| Clamped output | `wicked-estate lineage --depth`, `traverse --depth` / `--max-nodes`, `rank --limit`, `rules-recall --limit` | When one of those flags exceeds its ceiling, the command clamps and writes `CLAMPED: <param>=<asked> is above this tool's ceiling; used <param>=<ceiling>` to stderr under `--json` and to stdout after the result in text mode. The value after `used` is the one applied. |

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
| Index freshness | `stats --json` `staleness.commits_behind`; the `STALENESS:` line from bridged commands (stderr under `--json`, stdout after the result in text mode); suppressed by `blast-radius`/`path` under `--json` | not surfaced | A positive count means the graph describes an older revision. The graph is current only when the count is 0 and `staleness.unknown` is empty; a root listed there has unknown freshness. |
| Source-bundle cut | `summary.truncated_count` with `requested` / `returned` | n/a | `source --json` reports how many of the selected symbols it actually returned within `budget`. A large `--cluster` easily exceeds it. |

**The depth cut is reported.** `blast-radius --json` returns `searched_depth`,
`depth_horizon_reached`, and `node_cap_reached`. When `depth_horizon_reached` is
true, the text output prints a `CUT AT depth=N` line; raise `--depth` (max 24) to
go further. Read the per-row `depth` to separate direct dependents (`depth` 1) from transitive ones in one call; `blast-radius <name> --depth 1` still returns direct dependents only. Whether the difference against the full run is the transitive set depends on conditions stated in [`evidence.md` § Direct and transitive dependents](evidence.md#direct-and-transitive-dependents).
A true `node_cap_reached` means the node budget cut the walk; no CLI flag raises
it. `path` hops carry `confidence`, `provenance`, and `resolved_by` per hop;
`blast-radius` rows carry no per-row confidence — the summary `confidence` object
covers the full traversal, not individual rows.

MCP `BlastRadius` takes an explicit `depth` (default 8, max 24) and returns a
per-dependent `depth` like the CLI, plus `depth_horizon_reached`, `node_cap_reached`, and
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
or when the richer MCP response shapes are needed (`summary.top_by_pagerank` on
`BlastRadius`, `Communities` summaries, `ContextBundle`):

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

`index`, `scip` (adds reference support, never call edges), `evidence` (ingests
a compiler-evidence envelope, such as Angular input and output bindings),
`tfstate`, `import-telemetry`, `annotate`, `semantics`, `compact`, `watch`, `subscribe` (polls a change log; harmless but stateful),
`supports retract` (removes edge support), and `clusters --annotate`,
which writes a `community` annotation onto every member symbol.

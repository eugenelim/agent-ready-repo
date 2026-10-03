# Gaps against a general code-intelligence contract

Fourteen capabilities a general code-intelligence provider could offer,
assessed against what Wicked Estate 0.18 actually exposes. This exists so the
skill can say "that is not available" with a reason instead of improvising.

**Three provenances, and the difference matters.** The rule below classifies
every claim in this document; a few rows repeat their provenance inline where
it would otherwise be easy to misread, but the rule governs whether or not a
row says so. References to "capability N" below mean the numbered capability
sections, not the findings list near the end.

1. **Executed.** Run against a real repository with Wicked Estate **0.16.7** —
   65,807 nodes, 104,113 edges, 4,625 files — and the output read. Those counts
   are attributed to 0.16.7; executed rows for 0.17/0.18 additions were run on a
   small fixture with 0.18.0. Most CLI rows are this.
2. **Schema-derived.** Read from upstream's registered tool names and frozen
   conformance schemas. **Every MCP row is this. The MCP server has never been
   run here.**
3. **Source-read.** A property no run could show, because the CLI does not
   emit it or the fixture could not reach it. On the CLI side this covers the
   path edge direction and ambiguity resolution (capability 6); the model-level
   statements that every edge carries confidence, provenance and `resolved_by`
   (capabilities 10 and 11); and the behaviour of `semantic` and of `correspond`'s
   vector fusion (capabilities 2 and 9), both of which need an `--embeddings`
   index the fixture does not build.

Where a row's provenance is not obvious from this rule, it says so inline.

A schema-derived claim is weaker than an executed one, and this document
credits MCP with capabilities the CLI lacks. Treat those as upstream's
documented intent. The warning is not hypothetical. Three CLI claims taken from upstream's help
text and docs were wrong when finally run: `source`'s selectors, `rank`'s row
count, and the `annotations` payload shape. Upstream prose about the CLI is a
fourth, weakest origin — it is not listed below because no surviving claim
rests on it; every one that did has been executed or removed.

Each point carries one of five verdicts:

| Verdict | Meaning |
| --- | --- |
| **Direct** | A single command or tool does it. |
| **Composition** | Available by combining two or more existing calls. |
| **Partial** | Something adjacent exists but does not fully satisfy the intent. |
| **Absent** | Not available today by any route. |
| **Unclear** | The surface suggests it but current documentation does not settle it. |

Nothing here is a request to change Wicked Estate. It is a map of where the
skill must stop.

---

## 1. Resolve — **Direct**

`wicked-estate resolve <name> --json` returns `{symbol_id, name, kind, file,
line}` per candidate, with `--file` and `--kind` disambiguators. Names are not
unique and the tool is honest about returning several.

## 2. Search — **Direct**

`wicked-estate query <name>` for lexical search; MCP `SearchEntity` for the same
ranked and capped at 100.

*Caveat worth stating:* `query` has no `--json`, so parse `resolve --json`
instead. Semantic search exists — `wicked-estate semantic`, MCP
`SemanticSearch` — but only when the index was built with `--embeddings`, and
the MCP server advertises the tool only when an embedding backend is present.
Treat semantic search as conditionally available.

## 3. Retrieve — **Direct**

`wicked-estate nodes --json` returns per-symbol metadata with an annotation
summary; `--semantics` adds requirement and rule fields. MCP `RetrieveEntity`
fetches one symbol by stable ID including its doc comment.

## 4. Source / content — **Direct**

`wicked-estate source` with single, `--symbols`, `--file`, or `--cluster`
selectors and character bounds. MCP `FetchContent` for one symbol.

*Caveat, and it is a trap:* `source` has **two code paths**. The text path
requires a positional `<name>` and silently ignores `--symbols`, `--cluster`,
`--file`, and `--signatures-only`. Only the `--json` path honours them.
`--symbols` with no positional errors with `usage: wicked-estate source
<name>`; `--symbols` *with* a positional is accepted and then ignored, so an
ambiguous name returns every match while appearing to have been pinned to one.
Always pass `--json` with a selector.

*Caveat:* content is only available when it was stored at index time.
`FetchContent` returns `found=false` rather than erroring in that case, which is
easy to misread as "the symbol does not exist". It means "no stored content".

## 5. Traverse — **Partial on CLI, Direct on MCP (schema-derived)**

MCP `TraverseGraph` is a genuine bounded walk: direction, depth to 16,
`edge_kinds` filtering, node cap, and per-node depth in the response.

The CLI has no equivalent. `graph-view --focus` returns a filtered
neighbourhood, which answers many traversal questions but does not let you
select edge kinds or read depth per node. If traversal semantics matter to the
answer, either register the MCP server or state which approximation you used.

## 6. Paths — **Direct**

`wicked-estate path <from> <to> [--max-depth N] [--json]` follows dependency
edges of every kind — calls, imports, containment and the rest (source-read) —
and returns the shortest route. Read each hop's `kind`: a `Contains` or
`Imports` hop is not a call. With an ambiguous
`<from>`, it returns one shortest route across all candidates (source-read).
`--max-depth` takes 1–16, defaults to 12, and values above 16 are accepted and
clamped to 16 (source-read).

`--json` returns `{from, to, hops[], found, depth_bounded, node_bounded,
unresolved}`. Each hop carries `{source, target, kind, confidence, provenance,
resolved_by}`. Each endpoint carries `{symbol, name, kind, file, line,
line_1based}` — `line` is 0-based here; use `line_1based` to match the 1-based
`line` that `resolve` and `blast-radius` report.

`found: true` means a route exists. `found: false` is proven absence only when
`unresolved` is null and both `depth_bounded` and `node_bounded` are false: the
whole reachable set was searched. Otherwise it proves nothing:

- `unresolved: "from"` or `"to"` means that name matched no symbol. The command
  still exits 0 and both bound flags read false, so check this field first.
- `depth_bounded: true` means a route may lie deeper; raise `--max-depth` (max 16).
- `node_bounded: true` means the search hit the CLI's fixed node budget. No flag
  raises it, so report the answer as bounded.

MCP `Path` is the equivalent; its response omits `from` and `to`. Inputs are
schema-derived and the response shape is source-read — not executed here.

Text output prints a `STALENESS:` line; `--json` suppresses it.

## 7. Impact — **Direct**

`wicked-estate blast-radius --json` and MCP `BlastRadius`, both reporting an
unresolved count. This is the capability Wicked Estate is strongest at, and the
only one that reports its own incompleteness numerically.

The two surfaces differ substantially, and the MCP form is the richer one:

| | CLI `blast-radius [--depth N] --json` (executed) | MCP `BlastRadius` (schema-derived) |
| --- | --- | --- |
| Per-dependent depth | no | **yes** |
| Confidence envelope | no | **yes** — `{min, avg, edge_count}` |
| Ranked dependents | no | **yes** — `summary.top_by_pagerank` |
| Traversal depth | `--depth` parameter, default 12, max 24 | `depth` parameter, default 8, max 24 |
| Depth cut reported | `searched_depth`, `depth_horizon_reached`, `node_cap_reached` | `depth_horizon_reached`, `node_cap_reached`, `searched_depth` |
| Unbound references | `unresolved` | `unresolved_callers` |
| Output cut | `truncated_dependents` | `truncated` + `total` |

*Note:* use `blast-radius <name> --depth 1 --json` to get direct dependents
only; the difference against the full run is the complete transitive set only when the full run reports no cut — `truncated_dependents` 0, `depth_horizon_reached: false` and `node_cap_reached: false` — and the `--depth 1` run reports `truncated_dependents` 0. Otherwise it is a floor within `searched_depth`. When
`depth_horizon_reached` is true, the text output prints `CUT AT depth=N`;
raise `--depth` (max 24) to go further. `blast-radius` rows carry no per-hop
confidence or provenance — use `wicked-estate path` when you need those.

*Caveat, MCP only:* the MCP column is schema-derived. The richer response is
what upstream documents; nothing here has observed it.

## 8. Context — **Direct**

`wicked-estate context <name> --budget <chars> --json` and MCP `ContextBundle`.
`ContextBundle` additionally resolves a seed from free text and returns elided
stubs, so it is the better fit for filling an agent's window; the CLI form is
sufficient for most work and costs no resident context.

## 9. Compare — **Partial**

`wicked-estate correspond --db-a A.db --db-b B.db` scores candidate symbol
matches between two separately indexed graphs, lexically by default and
lexical-plus-vector when both carry embeddings.

What is missing is a **revision** comparison: there is no "diff this graph
against that one" that reports added, removed, and changed symbols.
`changed-since <sha>` gives symbols in files changed since a git SHA, and
`fingerprint <name>` gives a per-symbol stable hash, so a limited comparison is
constructible by composition. A general graph diff is not available.

## 10. Provenance and evidence — **Partial on blast-radius, Direct on path**

Every edge carries `provenance` and `resolved_by` in the model. Annotations
carry `provenance` and `author`, readable via `annotations --json` and
auditable via `stale-annotations`.

`wicked-estate path --json` hops carry `confidence`, `provenance`, and
`resolved_by` per hop — so for a specific route, the full edge evidence is
available on the CLI. `blast-radius --json` gives `{id, name, kind, file, line}`
per dependent — no confidence, no provenance per row. So for impact work,
provenance **exists in the model** but is not printed per dependent on the CLI.

A second, smaller correction: the annotation JSON carries `ts`, not
`last_verified`. The human-readable `stale-annotations` text mentions a
verification date; the machine payload does not.

## 11. Confidence — **Partial on CLI `blast-radius`; Direct on CLI `path`; Direct on MCP (schema-derived)**

Confidence is on every edge by construction and on every annotation as a field.
`nodes --json --semantics` exposes `rule_confidence` per node.

**On MCP this reaches the read path.** `BlastRadius` returns a
`confidence {min, avg, edge_count}` envelope over the traversal edges, so you
can tell a high-confidence impact set from a speculative one.

**On CLI `blast-radius` it does not.** You cannot look at a `blast-radius --json`
result and see which dependents came from high-confidence edges. That is the
gap. `path --json` does carry `confidence` on every hop, so for one specific
route the CLI shows it. The correct response on the CLI is to verify load-bearing
edges against source rather than to invent a confidence figure.

## 12. Completeness — **Direct**

All three limits are reported, and reporting any is unusual.

Reported: `unresolved` / `unresolved_callers`, `truncated_dependents` /
`truncated`, and `searched_depth` / `depth_horizon_reached` / `node_cap_reached`
on `blast-radius --json` (executed). Use `blast-radius <name> --depth N` (default
12, max 24) to control reach; when `depth_horizon_reached` is true, the text
output prints `CUT AT depth=N`. A true `node_cap_reached` means the traversal hit
its node budget; no CLI flag raises it, so report the list as a floor.
`max_nodes` truncation on MCP `TraverseGraph`.
`stats` for overall graph size.

`wicked-estate path --json` reports its own limits the same way: see
§6 Paths for when `found: false` is a proven absence.

*Caveat:* `dead-code` returns symbols with no edges at all, and the count is
larger than intuition suggests — **42,509 of 65,807 nodes (65%)** on this
catalogue. Absence of an edge is not proof of absence of use: dynamic dispatch,
reflection, and entry-by-framework all produce edgeless symbols that are very
much alive. Never recommend a deletion on `dead-code` output alone.

## 13. Snapshot / revision identity — **Partial**

The `STALENESS: N commit(s) since last index` line tells you the graph is behind
and by how much. `stats` reports git provenance when the repository was indexed
from a checkout. `fingerprint` and `changed-since` support per-symbol and
per-revision change detection.

What is missing is a single call returning "this graph was built from commit
`<sha>` at `<time>`" as structured data. You can establish the revision, but by
reading a warning line and a stats block rather than by querying a field.

## 14. Capability discovery — **Partial**

Over MCP, `tools/list` is genuine runtime capability discovery: the advertised
set varies by what is actually available. `SemanticSearch` appears only with an
embedding backend; `--readonly` drops the ten write tools, leaving 20 (21 with
`SemanticSearch`).

Over the CLI, discovery is `wicked-estate --help`, which is a static usage
block — and there is **no `--version` flag at all**; `--version` falls through
to the same 68-line usage banner, which happens to start with the version
string.

Three dispatched commands do not appear in that banner: `graph-view`,
`by-requirement`, and `semantics`. The help text is therefore not a complete
inventory of what the binary accepts. Verify a verb by running it rather than
by assuming `--help` is exhaustive.

---

## Summary

| # | Capability | Verdict |
| --- | --- | --- |
| 1 | Resolve | Direct |
| 2 | Search | Direct (semantic is conditional) |
| 3 | Retrieve | Direct |
| 4 | Source / content | Direct |
| 5 | Traverse | Partial on CLI, Direct on MCP (schema-derived) |
| 6 | Paths | Direct on CLI; Direct on MCP (schema-derived) |
| 7 | Impact | Direct |
| 8 | Context | Direct |
| 9 | Compare | Partial |
| 10 | Provenance / evidence | Partial on blast-radius (in the model, not per row); Direct on path hops |
| 11 | Confidence | Partial on CLI blast-radius; Direct on CLI path hops; Direct on MCP (schema-derived) |
| 12 | Completeness | Direct — unresolved, truncation and depth cut all reported |
| 13 | Snapshot / revision identity | Partial |
| 14 | Capability discovery | Partial |

---

## Gaps found while building this pack

Recorded for the reader's benefit. No change to Wicked Estate is proposed or
required, and this pack works within all of them.

1. **The CLI is a much thinner surface than MCP for impact work.** MCP
   `BlastRadius` returns per-dependent depth, a confidence envelope, and
   PageRank-ranked dependents; the CLI form returns none of the three. The gap
   is not in Wicked Estate's model, it is in what the CLI exposes.
2. **Nothing ranks a supplied set of symbols on the CLI.** `rank` is a global
   top-25 with no seed, no filter, and no `--json`, so "which of these 47
   dependents matter most" has no CLI answer.
3. **Lineage is MCP-only.** Forward transitive reachability has no CLI verb,
   despite being the documented complement of `blast-radius`, which does.
4. **Rules discovery is MCP-only.** `RulesInventory` and `rules.recall` have no
   CLI equivalent, so a CLI-only adopter cannot inventory business rules.
5. **`nodes` has no symbol filter.** The only metadata-inventory verb narrows
   by `--kind` or `--annotated-with` and otherwise returns the whole graph, so
   it cannot serve single-symbol lookup.
6. **Freshness is invisible on the machine path.** `STALENESS:` prints from
   only six subcommands and is suppressed under `--json`, so an agent working
   in JSON never sees it.
7. **`query` has no `--json`.** The most obvious search verb is the one that
   cannot be parsed; `resolve --json` has to stand in.
8. **No `--version` flag and no structured revision field.** `--version`
   prints the full usage banner, and graph revision is recoverable only from a
   warning line plus a stats block.
9. **`--help` is not a complete command inventory.** `graph-view`,
   `by-requirement`, and `semantics` are dispatched but undocumented there.
10. **`source`'s selectors silently no-op without `--json`.** The help text
    documents a precedence (`--symbols` > `--cluster` > `--file` > `<name>`)
    that only holds on the JSON path. On the text path the selectors are
    ignored rather than rejected, so the command returns a plausible wrong
    answer instead of an error — the worst available failure mode for an agent
    that cannot see it went wrong.

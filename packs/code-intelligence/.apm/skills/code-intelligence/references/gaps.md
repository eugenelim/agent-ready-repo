# Gaps against a general code-intelligence contract

Fourteen capabilities a general code-intelligence provider could offer,
assessed against what Wicked Estate 0.16 actually exposes. This exists so the
skill can say "that is not available" with a reason instead of improvising.

Verdicts were checked by running Wicked Estate 0.16.7 against a real
repository — 65,807 nodes, 104,113 edges, 4,625 files — and reading the actual
output, not by reading source alone. Where a claim below names a field or a
count, it was observed.

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

## 5. Traverse — **Partial on CLI, Direct on MCP**

MCP `TraverseGraph` is a genuine bounded walk: direction, depth to 16,
`edge_kinds` filtering, node cap, and per-node depth in the response.

The CLI has no equivalent. `graph-view --focus` returns a filtered
neighbourhood, which answers many traversal questions but does not let you
select edge kinds or read depth per node. If traversal semantics matter to the
answer, either register the MCP server or state which approximation you used.

## 6. Paths — **Absent**

Nothing returns the path between two symbols. There is no "how does A reach B"
primitive on either surface.

You can approximate by traversing from A and checking whether B appears, but
that tells you reachability, not the route. Do not present a reconstructed
route as one the tool produced.

## 7. Impact — **Direct**

`wicked-estate blast-radius --json` and MCP `BlastRadius`, both reporting an
unresolved count. This is the capability Wicked Estate is strongest at, and the
only one that reports its own incompleteness numerically.

The two surfaces differ substantially, and the MCP form is the richer one:

| | CLI `blast-radius --json` | MCP `BlastRadius` |
| --- | --- | --- |
| Per-dependent depth | no | **yes** |
| Confidence envelope | no | **yes** — `{min, avg, edge_count}` |
| Ranked dependents | no | **yes** — `summary.top_by_pagerank` |
| Traversal depth | hardcoded 12, unreported | `depth` parameter, default 8, max 24 |
| Unbound references | `unresolved` | `unresolved_callers` |
| Output cut | `truncated_dependents` | `truncated` + `total` |

*Caveat, CLI only:* the result is a flat list with no depth, so direct and
transitive impact cannot be separated from the CLI alone.

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

## 10. Provenance and evidence — **Partial**

Every edge carries `provenance` and `resolved_by` in the model. Annotations
carry `provenance` and `author`, readable via `annotations --json` and
auditable via `stale-annotations`.

*Caveat, and it is a real one:* the CLI read commands do not print edge
provenance per row. `blast-radius --json` gives `{id, name, kind, file, line}`
per dependent — no confidence, no provenance. So provenance **exists in the
model** and is **absent from the CLI output you will normally be reading**.

A second, smaller correction: the annotation JSON carries `ts`, not
`last_verified`. The human-readable `stale-annotations` text mentions a
verification date; the machine payload does not.

## 11. Confidence — **Partial on CLI, Direct on MCP**

Confidence is on every edge by construction and on every annotation as a field.
`nodes --json --semantics` exposes `rule_confidence` per node.

**On MCP this reaches the read path.** `BlastRadius` returns a
`confidence {min, avg, edge_count}` envelope over the traversal edges, so you
can tell a high-confidence impact set from a speculative one.

**On the CLI it does not.** You cannot look at a `blast-radius --json` result
and see which dependents came from high-confidence edges. That is the gap, and
it is CLI-specific. The correct response on the CLI is to verify load-bearing
edges against source rather than to invent a confidence figure.

## 12. Completeness — **Partial**

Two of three limits are reported, and reporting any is unusual.

Reported: `unresolved` / `unresolved_callers`, and `truncated_dependents` /
`truncated`. `max_nodes` truncation on MCP `TraverseGraph`. `stats` for overall
graph size.

**Unreported:** the CLI hardcodes blast-radius traversal to depth 12, and
dependents beyond that are counted in neither reported field. A CLI blast
radius therefore has a silent horizon. MCP `BlastRadius` makes depth an explicit
parameter and stamps each dependent with its own, so the horizon is visible
there.

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
embedding backend; `--readonly` drops the ten write tools, leaving 19.

Over the CLI, discovery is `wicked-estate --help`, which is a static usage
block — and there is **no `--version` flag at all**; `--version` falls through
to the same 65-line usage banner, which happens to start with the version
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
| 5 | Traverse | Partial on CLI, Direct on MCP |
| 6 | Paths | **Absent** |
| 7 | Impact | Direct |
| 8 | Context | Direct |
| 9 | Compare | Partial |
| 10 | Provenance / evidence | Partial — in the model, absent from CLI output |
| 11 | Confidence | Partial on CLI, Direct on MCP |
| 12 | Completeness | Partial — depth cap unreported |
| 13 | Snapshot / revision identity | Partial |
| 14 | Capability discovery | Partial |

---

## Gaps found while building this pack

Recorded for the reader's benefit. No change to Wicked Estate is proposed or
required, and this pack works within all of them.

1. **No path query.** The most conspicuous absence. "How does the HTTP handler
   reach the database write" is a question agents ask constantly, and only
   reachability can be answered.
2. **The CLI is a much thinner surface than MCP for impact work.** MCP
   `BlastRadius` returns per-dependent depth, a confidence envelope, and
   PageRank-ranked dependents; the CLI form returns none of the three. The gap
   is not in Wicked Estate's model, it is in what the CLI exposes.
3. **The CLI blast radius has a silent depth-12 horizon.** It is reported by
   neither completeness field, so a truncated-by-reach answer is
   indistinguishable from a complete one.
4. **Nothing ranks a supplied set of symbols on the CLI.** `rank` is a global
   top-25 with no seed, no filter, and no `--json`, so "which of these 47
   dependents matter most" has no CLI answer.
5. **Lineage is MCP-only.** Forward transitive reachability has no CLI verb,
   despite being the documented complement of `blast-radius`, which does.
6. **Rules discovery is MCP-only.** `RulesInventory` and `rules.recall` have no
   CLI equivalent, so a CLI-only adopter cannot inventory business rules.
7. **`nodes` has no symbol filter.** The only metadata-inventory verb narrows
   by `--kind` or `--annotated-with` and otherwise returns the whole graph, so
   it cannot serve single-symbol lookup.
8. **Freshness is invisible on the machine path.** `STALENESS:` prints from
   only five subcommands and is suppressed under `--json`, so an agent working
   in JSON never sees it.
9. **`query` has no `--json`.** The most obvious search verb is the one that
   cannot be parsed; `resolve --json` has to stand in.
10. **No `--version` flag and no structured revision field.** `--version`
    prints the full usage banner, and graph revision is recoverable only from a
    warning line plus a stats block.
11. **`--help` is not a complete command inventory.** `graph-view`,
    `by-requirement`, and `semantics` are dispatched but undocumented there.
12. **`source`'s selectors silently no-op without `--json`.** The help text
    documents a precedence (`--symbols` > `--cluster` > `--file` > `<name>`)
    that only holds on the JSON path. On the text path the selectors are
    ignored rather than rejected, so the command returns a plausible wrong
    answer instead of an error — the worst available failure mode for an agent
    that cannot see it went wrong.

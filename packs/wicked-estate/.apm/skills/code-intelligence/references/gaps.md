# Gaps against a general code-intelligence contract

Fourteen capabilities a general code-intelligence provider could offer,
assessed against what Wicked Estate 0.16 actually exposes. This exists so the
skill can say "that is not available" with a reason instead of improvising.

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

`wicked-estate blast-radius --json` and MCP `BlastRadius`, both reporting the
unresolved count. This is the capability Wicked Estate is strongest at, and the
only one that reports its own incompleteness numerically.

*Caveat:* the result is a flat list. Depth attribution — direct versus
transitive — requires MCP `TraverseGraph`, because the blast-radius response
does not carry it.

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

## 10. Provenance and evidence — **Direct**

Every edge carries `provenance` and `resolved_by`. Annotations carry
`provenance`, `author`, and `last_verified`, readable via `annotations --json`
and auditable for staleness via `stale-annotations`.

*Caveat, and it is a real one:* edge-level provenance is a property of the
stored edge, and the read commands do not print it per row. `blast-radius
--json` gives `{id, name, kind, file, line}` per dependent — no confidence, no
provenance. So provenance **exists in the model** and is **not surfaced on the
common impact path**. Treat per-edge provenance as available in principle and
unavailable in the output you will normally be reading.

## 11. Confidence — **Partial**

Confidence is on every edge by construction and on every annotation as a field.
`nodes --json --semantics` exposes `rule_confidence` per node.

But, as with provenance: the routine read paths do not print per-edge
confidence. You cannot look at a `blast-radius` result and see which dependents
came from high-confidence edges. That is the gap. The correct response is to
verify load-bearing edges against source rather than to invent a confidence
figure.

## 12. Completeness — **Direct, and better than most**

`unresolved` and `truncated_dependents` on `blast-radius --json`; `max_nodes`
truncation on MCP `TraverseGraph`; `stats` for overall graph size. Wicked Estate
reports what it could not resolve, which is unusual and worth using.

*Caveat:* `dead-code` returns symbols with no edges at all. Absence of an edge
is not proof of absence of use — dynamic dispatch, reflection, and
entry-by-framework all produce edgeless symbols that are very much alive. Never
recommend a deletion on `dead-code` output alone.

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
block. Two commands the CLI dispatches — `graph-view` and `by-requirement` — do
not appear in it, so the help text is not a complete inventory of what the
binary accepts. Verify a verb by running it rather than by assuming `--help` is
exhaustive.

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
| 10 | Provenance / evidence | Direct in model, not on the common read path |
| 11 | Confidence | Partial |
| 12 | Completeness | Direct |
| 13 | Snapshot / revision identity | Partial |
| 14 | Capability discovery | Partial |

---

## Gaps found while building this pack

Recorded for the reader's benefit. No change to Wicked Estate is proposed or
required, and this pack works within all of them.

1. **No path query.** The most conspicuous absence. "How does the HTTP handler
   reach the database write" is a question agents ask constantly, and only
   reachability can be answered.
2. **Per-edge confidence and provenance are not surfaced on read paths.** The
   model's most distinctive property — no bare edges — is largely invisible in
   `blast-radius` and `graph-view` output. An agent cannot weigh a dependent by
   how the edge was resolved.
3. **`blast-radius` returns no depth.** Direct and transitive impact cannot be
   separated from the CLI alone, which is the single most common follow-up
   question after asking for a blast radius.
4. **Lineage is MCP-only.** Forward transitive reachability has no CLI verb,
   despite being the documented complement of `blast-radius`, which does.
5. **Rules discovery is MCP-only.** `RulesInventory` and `rules.recall` have no
   CLI equivalent, so a CLI-only adopter cannot inventory business rules.
6. **`query` has no `--json`.** The most obvious search verb is the one that
   cannot be parsed; `resolve --json` has to stand in.
7. **No structured graph revision field.** Revision identity is recoverable but
   only from a warning line plus a stats block.
8. **`--help` is not a complete command inventory.** `graph-view` and
   `by-requirement` are dispatched but undocumented there.

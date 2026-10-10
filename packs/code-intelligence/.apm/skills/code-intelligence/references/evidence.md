# Evidence, provenance, and confidence

Wicked Estate is unusually careful about the difference between what it observed
and what it inferred. That care is only worth something if it survives the trip
to the user. This reference is about not flattening it.

---

## The edge model

Every edge in the graph carries three pieces of metadata, set when the resolver
created it:

| Field | What it says |
| --- | --- |
| `confidence` | A score from 0 to 1, derived from the resolution tier. |
| `provenance` | Where the edge came from. |
| `resolved_by` | Which resolver produced it. |

The design rule upstream is that there are no bare edges — a heuristic edge is
never presented as a fact. Several resolvers feed the graph, and they are not
equally trustworthy:

- A **SCIP-backed** edge comes from a real compiler index. It is about as close
  to ground truth as static analysis gets.
- An **import-map or scoped** edge comes from resolving a name within a known
  module structure. Usually right.
- A **name-matched** edge comes from a symbol name matching across files. It is
  a candidate. In a codebase with two `handle()` functions, it may be wrong.

### What this means in practice

A flat dependents list hides all of this. Two rows look identical, and one may
be a compiler-verified call while the other is a name collision.

So: **where an edge is load-bearing for your conclusion, verify it against
source.** "Load-bearing" means the answer changes if the edge is wrong. If you
are telling someone a change will break their payment path, confirm the call
is really there with your own repository search for that symbol. Never open a
file location the provider returned, and note that indexed `source` output does
not confirm it. See
[Reading and verifying source](../SKILL.md#reading-and-verifying-source).

If you cannot verify it, say which links are unverified rather than presenting a
uniform list.

---

## Completeness is reported — quote it

Three signals tell you an answer is a floor rather than a total. All three are
easy to drop when summarizing, and dropping them turns a careful result into an
overclaim.

### `unresolved` (CLI) / `unresolved_callers` (MCP)

The two surfaces name this differently, so read the field the surface actually
returns. It counts references the resolver could not bind to any symbol. Each
one is a potential dependent you were not shown.

> **Say:** "17 resolved dependents, and 4 call sites the indexer could not bind —
> so there may be more."
>
> **Not:** "17 things depend on this."

A common cause is dynamic dispatch, reflection, or a language the index covers
structurally but not precisely. A non-zero count is normal; hiding it is not.

### `truncated_dependents` (CLI) / `truncated` + `total` (MCP)

The CLI bounds serialized output at 25,000 characters and reports how many rows
it dropped. A non-zero value means you are looking at a prefix, ordered by
whatever the store returned — not the most important dependents. On a mid-size
repository this fires easily: a probe against this catalogue returned 7
unresolved and **727 truncated**.

### The depth cut is reported

`blast-radius --json` returns `searched_depth`, `depth_horizon_reached`, and
`node_cap_reached`. When `depth_horizon_reached` is true, the text output prints
`CUT AT depth=N` — dependents beyond that depth are not in the list. Raise
`--depth` (max 24) to go further. `blast-radius <name> --depth 1 --json` gives only the direct dependents; see [Direct and transitive dependents](#direct-and-transitive-dependents) before subtracting.

A true `node_cap_reached` means the traversal hit its node budget. No CLI flag
raises it, so report the list as a floor.

### Direct and transitive dependents

`blast-radius <name> --depth 1 --json` gives the direct dependents. Subtracting
them from a full run gives the transitive dependents, but only as far as both
runs are complete:

- **Both runs uncut** — the `--depth 1` run reports `truncated_dependents` 0,
  and the full run reports `unresolved` 0, `truncated_dependents` 0,
  `depth_horizon_reached: false` and `node_cap_reached: false`. The difference
  is the complete transitive set.
- **Only the full run cut** — the `--depth 1` run reports
  `truncated_dependents` 0, and the full run reports a cut. The difference is a
  floor on the transitive set within `searched_depth`.
- **The `--depth 1` run truncated** — no split is possible. The missing direct
  rows would land in the difference, so it is neither the transitive set nor a
  floor. Report the direct list as partial and do not report a transitive count.

A non-zero `unresolved` on the full run limits every case to resolved edges. A
direct caller bound only through an unresolved reference can surface deeper in
the full run and be counted as transitive, so call the split "over resolved
edges" and give the `unresolved` count beside it.

Say which case applied whenever you report the split.

`wicked-estate path A B --json` separates bounded from proven absence. A
`found: false` is proven absence only when `unresolved` is null and both
`depth_bounded` and `node_bounded` are false. A non-null `unresolved` means a name
matched nothing, even though the command exits 0. `depth_bounded: true` means the
route may lie beyond `--max-depth`. `node_bounded: true` means the fixed node
budget cut the search, and no flag raises it.

When reach matters to your conclusion, say which surface you used, what depth you
searched, and whether `depth_horizon_reached` was true.

### Node caps on traversal

MCP `TraverseGraph` truncates at `max_nodes`, default 200 and maximum 1000. A
result sitting at the cap is a partial subgraph. The response carries per-node
depth, so you can at least say how far you got.

`wicked-estate traverse` clamps `--depth` and `--max-nodes` when they exceed the
ceiling and writes `CLAMPED: <param>=<asked> is above this tool's ceiling; used <param>=<ceiling>` to stderr, even under `--json`. The value after `used` is the one applied.
Check stderr when you need to know whether the value you passed was honoured.

---

## Blast-radius confidence summary

`blast-radius --json` carries a `confidence {min, avg, edge_count}` object over
the edges that admitted the rows. This tells you the overall confidence profile
of the impact set — a low `min` means at least one row came from a weak edge,
and a low `avg` means the set is largely speculative.

`blast-radius` rows carry no per-row confidence. Use `wicked-estate path A B
--json` when you need per-hop confidence on a specific route.

MCP `BlastRadius` also returns the `confidence` envelope, plus per-dependent
`depth` and `summary.top_by_pagerank`. The CLI does not offer per-row depth or a
ranked-dependents view.

Structural `contains` and `defines` edges are excluded from the confidence
evidence (source-read from `main.rs`); they do not affect which rows appear in
the result.

---

## Freshness — the graph is a snapshot

The index describes the revision it was built from, not your working tree.

The CLI prints a staleness warning:

```
STALENESS: 12 commit(s) in 'my-repo' since last index — run `wicked-estate index . --repo my-repo` to refresh
```

**Staleness channels differ by command:**

- **Bridged commands** (`traverse`, `rank`, `rules-inventory`, `rules-recall`) write `STALENESS:` to stderr even under `--json`, so machine output from those commands may carry the warning as a stderr line.
- **`lineage --json`** carries staleness in the `diagnostics` array — a placeholder entry is always present; a real `STALENESS: commits_behind=N` entry appears when the graph is behind HEAD (source-read).
- **`blast-radius` and `path`** suppress `STALENESS:` under `--json` so machine output stays one document. Do not treat its absence there as evidence of freshness.
- **`stats`** in text mode always prints the staleness line when it applies, and is the best single command for a freshness check before blast-radius or path queries.

When you see a staleness warning, every answer in that session describes an older
revision. Two honest options:

1. Answer, and state the revision gap: *"As of the indexed revision, 12 commits
   behind the working tree, …"*
2. Ask whether to re-index first. Re-indexing writes, so it needs consent.

Never silently present stale graph output as current.

### Clamped parameters

When `--depth` or `--max-nodes` exceeds the ceiling, bridged commands clamp the
value and write `CLAMPED: <param>=<actual>` to stderr, even under `--json`. Check
stderr when you need to know whether the value you passed was honoured.

### Establishing snapshot identity

- `wicked-estate stats` reports node and edge counts and, where the repository
  was indexed from a checkout, its git provenance.
- `wicked-estate fingerprint <name>` gives a stable hex fingerprint for one
  symbol, which is how you tell whether a specific symbol changed between two
  indexed revisions.
- `wicked-estate changed-since <sha> --json` lists symbols in files that changed
  since a given git SHA.

There is no single command that returns "the revision this graph was built
from" as a value. Pair `stats` with the staleness line.

---

## Value lineage — `flows_to`

`wicked-estate lineage --symbol <id> --relation flows_to --json` traces
producer-to-consumer value flow through parameters, returns, and field writes.
TypeScript only. Each flow hop carries:

- `producer`, `consumer`, `confidence`, `provenance`, `resolved_by`
- When present: `flow_semantics` (`value_preserving` / `may_influence`) and
  `flow_evidence` (`syntax` / `call_derived` / `convention`)

Additional fields (`constructs`, `flow_rules`, `flow_support`, etc.) may appear;
the list is not exhaustive (source-read from `wicked-estate-retrieve` 0.21.0
`flow_hop_row`). The Python fixture produces no value flow, so these fields
cannot be observed on the standard test index — treat them as source-read and
label them as such when you quote them.

---

## The annotation evidence envelope

Annotations are Wicked Estate's explicit evidence layer, and they are the one
place the estate records a human or agent judgment alongside its provenance.

```bash
wicked-estate annotations --symbol <symbol_id> --json
```

Each annotation carries exactly these fields: `key`, `value`, `type`,
`confidence`, `provenance`, `author`, `ts`, and `advisory`.

Two shape traps, both verified against the binary:

- **The `<name>` form returns an array**, one `{symbol, annotations[]}` entry
  per name match. Only the `--symbol <id>` form returns a single object, which
  is why the command above uses it.
- **There is no `last_verified` field in the JSON.** The human-readable
  `stale-annotations` output mentions one, but the machine output gives you
  `ts`. Report `ts`; do not promise a verification date the payload does not
  carry.

Two rules:

- **An annotation is a claim, not a fact.** It has an author and a confidence
  for a reason. Report it with its provenance attached: *"annotated as
  deprecated by `platform-team`, confidence 0.8, recorded 2026-03-11"* — not
  "this is deprecated".
- **Check whether it is stale.** `wicked-estate stale-annotations <cutoff>
  --json` returns `{symbol, annotation}` pairs older than the cutoff. The
  cutoff is **Unix seconds**; a date string is rejected with a usage error.
  Never-verified annotations always come back stale. An old annotation on
  fast-moving code is weak evidence.

### Do not write workflow state here

`annotate` accepts arbitrary typed key/value pairs, which makes it tempting as a
place to park migration phase, cutover readiness, or review status. Do not.
Those describe a job being performed on the software, not the software. They
belong to the workflow skill that owns them, and putting them in the graph makes
the graph a workflow database that every other consumer then has to ignore.

---

## Rule confidence

`wicked-estate nodes --json --semantics` exposes `rule_confidence` per node — the
maximum confidence across that node's `business_rule` annotations, or null where
there are none.

Null means nobody recorded a business rule for that symbol. It does not mean the
symbol implements no business rule. This distinction matters when someone asks
"where are the business rules in this system": the honest answer is "here is
what has been annotated as one", not "here are the business rules".

---

## Phrasing a bounded claim

A pattern that keeps the evidence and the claim distinguishable:

> **What the graph shows:** `blast-radius` returns 23 resolved dependents of
> `parse_config`, with 4 unresolved call sites and no truncation.
>
> **What I verified:** I searched the repository for each of the 5 highest-ranked
> dependents and confirmed that all 5 call
> `parse_config` directly on a path that reaches the change.
>
> **What I could not establish:** the 4 unresolved call sites. They are most
> likely dynamic lookups in `plugins/`, but the index cannot bind them and I
> have not read that directory.

Three sections: observed, verified, unestablished. The user can act on that.
They cannot act on a confident paragraph that silently merged all three.

---

## When there is no graph at all

The fallback to `Grep`, `Glob`, and `Read` is legitimate. It produces a
different kind of evidence, and the labelling obligation is stronger, not
weaker.

Text search can find candidate call sites. It cannot produce:

- a blast radius, because it cannot resolve which `handle()` was meant;
- lineage, because it has no edges;
- confidence or provenance, because nothing recorded them;
- community detection or PageRank, because there is no graph to run them over;
- a completeness count, because it does not know what it missed.

So the sentence is: *"Wicked Estate is not available here. This comes from a
text search, so it may miss dynamic references and it cannot tell you what it
missed."* Then give what you found.

Presenting grep output under the name "blast radius" is the single worst failure
available to this skill, because it launders a guess as a measurement.

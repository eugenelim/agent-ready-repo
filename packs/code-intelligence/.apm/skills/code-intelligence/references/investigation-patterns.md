# Investigation patterns

Five reusable shapes. Pick the one that matches the question, not the one that
matches the tool you remember. Each names its stop condition, because the
dominant failure here is walking the graph long after the question was answered.

Commands assume the default graph at `.wicked-estate/graph.db`.

---

## 1. Understand an entity

**Question shape:** "What is `OrderService` and how does it work?"

1. **Locate the canonical entity.**

   ```bash
   wicked-estate resolve OrderService --json
   ```

   Several hits means the name is ambiguous. Narrow with `--file` or `--kind`,
   or ask which one the user means. Do not silently take the first.

2. **Retrieve metadata.** `resolve --json` already gave you kind, file, and
   line. For the signature, go straight to the symbol:

   ```bash
   wicked-estate source --symbols <symbol_id> --json --signatures-only
   ```

   Do **not** reach for `wicked-estate nodes` here. It has no symbol filter —
   only `--kind` and `--annotated-with` — so it returns the whole graph, and
   `--semantics` adds a per-node semantics read and edge fetch on top of that.
   It is an inventory command, not a lookup.

   For annotations on this one symbol:

   ```bash
   wicked-estate annotations --symbol <symbol_id> --json
   ```

3. **Inspect the source.** Never describe behaviour you have not read:

   ```bash
   wicked-estate source OrderService --json
   ```

   `--json` is not optional here. The text path ignores every selector and
   falls back to a name search, so dropping it silently returns the wrong
   symbol when the name is ambiguous.

   For a large type, start with `--signatures-only` and pull full bodies only
   for the members that matter.

4. **Inspect incoming relationships.** Who uses it, and how heavily:

   ```bash
   wicked-estate blast-radius OrderService --json
   ```

5. **Inspect outgoing relationships.** What it depends on:

   ```bash
   wicked-estate graph-view --focus OrderService --limit 40
   ```

   For true transitive forward reachability you need MCP `Lineage`; if it is not
   registered, say that this is a bounded neighbourhood rather than a full
   dependency closure.

6. **Find the supporting material, where the question warrants it.** Tests and
   configuration via `wicked-estate source --file <path> --json` on
   neighbouring files;
   requirements via `wicked-estate by-requirement`; rules via MCP
   `RulesInventory`.

**Stop when** you can state what the entity is for, what it depends on, and who
depends on it. A full transitive walk is almost never needed to answer "how does
this work".

---

## 2. Analyze change impact

**Question shape:** "What breaks if I change `parse_config`?"

1. **Resolve the subject.** As above. Impact analysis on the wrong overload is
   worse than no analysis.

2. **Obtain the blast radius.**

   ```bash
   wicked-estate blast-radius parse_config --json
   ```

3. **Read the completeness fields before reading the list.** `unresolved` counts
   references that could not be bound, and `truncated_dependents` counts rows
   dropped at the 25,000-character bound. Both mean your list is a floor. Also
   read `depth_horizon_reached`: when true, the text prints `CUT AT depth=N`
   and you can raise `--depth` (max 24) to go further.

   Freshness is not in this output — `blast-radius` suppresses its `STALENESS:`
   line under `--json`. Run a bare `wicked-estate stats` to learn whether the
   graph is behind the working tree.

4. **Separate direct from transitive.** The flat `dependents` array does not
   distinguish them. Get depth by running:

   ```bash
   wicked-estate blast-radius parse_config --depth 1 --json
   ```

   That gives the direct dependents. The difference against the full blast
   radius is the complete transitive set only when the full run reports no cut — `truncated_dependents` 0, `depth_horizon_reached: false` and `node_cap_reached: false` — and the `--depth 1` run reports `truncated_dependents` 0. Otherwise it is a floor within `searched_depth`.

   - MCP available: `TraverseGraph` with `direction: "dependents"` and
     `depth: 1` gives the direct set with per-node depth in the response.

5. **Inspect the important paths, not the whole list.** A hundred-row list
   pasted back is not impact analysis. Five paths read properly is.

   Choosing *which* five is where the CLI runs out. `wicked-estate rank` is a
   global top-25 by PageRank; it takes no seed and no input set, so it cannot
   rank your dependents. Two honest routes:

   - **MCP registered:** `BlastRadius` returns `summary.top_by_pagerank`, which
     ranks the dependents it found. This is the only ranked-dependents result
     available anywhere in the surface.
   - **CLI only:** select by judgement from `{file, kind, name}` — public
     entry points, anything in a hot directory, anything whose name suggests it
     touches the changing behaviour — and **say the selection was yours, not a
     ranking**. Then read them:

     ```bash
     wicked-estate source --symbols <id1>,<id2> --json
     ```

6. **Validate the conclusions against source.** For every dependent you call
   out as breaking, confirm from its source that it actually uses the part you
   are changing.

**Stop when** direct and transitive impact are separated, the completeness
caveat is stated, and each claimed breakage is grounded in source.

---

## 3. Investigate behavior

**Question shape:** "Why does the retry loop fire twice?" or "How does A reach B?"

1. **Locate the relevant implementation.** Start from the observable symptom.
   `wicked-estate query` for a name you already know; `wicked-estate semantic`
   when you only have a description **and** the index carries embeddings.

2. **When the question is a specific route, use path.** For "how does A reach B",
   run `wicked-estate path A B --json` and read only the hop files. Read each
   hop's `kind`: a `Contains` or `Imports` hop is not a call. Check `unresolved`
   first — a misspelled name exits 0. A `found: false` is proven absence only
   when `unresolved` is null and both bound flags are false. With
   `depth_bounded: true`, raise `--max-depth`; with `node_bounded: true`, report
   the answer as bounded, because no flag raises the node budget.

3. **Follow what the behaviour actually flows through.** Calls via
   `graph-view --focus`; configuration via `source --file <path> --json`; rules via MCP
   `RulesInventory` and `TraverseGraph` with `edge_kinds: ["invoked_by"]`.

4. **Gather evidence incrementally.** One hop, read, decide whether the next hop
   is warranted. Pulling a large subgraph and then reasoning over it produces
   confident answers from unread code.

5. **Keep heuristic edges out of the causal chain.** A name-resolved edge is a
   candidate, not a call. Where an edge is load-bearing for the explanation,
   open the source and confirm the call is really there.

**Stop when** the evidence explains the behaviour, or when you can name
precisely which link you could not establish. The second outcome is a real
result; report it rather than closing the gap with a guess.

---

## 4. Analyze architecture

**Question shape:** "How is this system organized?"

1. **Find the load-bearing symbols.**

   ```bash
   wicked-estate rank
   ```

2. **Find the natural subsystems.**

   ```bash
   wicked-estate clusters --json
   ```

   Raise `--resolution` above 1.0 for smaller, tighter clusters when the default
   returns a few giant ones.

3. **Find the edges of the system.**

   ```bash
   wicked-estate entrypoints --json
   wicked-estate leaves --json
   ```

4. **Read representative source per cluster.**

   ```bash
   wicked-estate source --cluster <id> --json --signatures-only
   ```

5. **Separate structure from interpretation.** This is the discipline that
   matters in this pattern.

   > **Observed:** cluster 3 holds 41 symbols across `billing/` and `invoicing/`,
   > with the highest-PageRank member being `InvoiceBuilder`.
   >
   > **Interpretation:** these two directories are probably one billing domain
   > that was split by folder rather than by responsibility.

   The first is what the graph reported. The second is your reading of it, and
   it may be wrong. Label them differently and never merge them into one
   sentence.

**Stop when** the cluster and hotspot structure is described and your reading of
it is clearly marked as a reading.

---

## 5. Assemble task context

**Question shape:** "Give me what I need to work on the checkout flow."

1. **Use the purpose-built capability.**

   ```bash
   wicked-estate context CheckoutController --budget 8000 --json
   ```

   Where MCP is registered, `ContextBundle` is the closer fit — it resolves the
   seed from free text as well as from an ID, and returns elided stubs rather
   than full slices.

2. **Keep it bounded.** A budget is not a formality. Raise it deliberately when
   the returned set is visibly too thin, not by default.

3. **Explain why each item is in the bundle.** The CLI `context` scores
   neighbours of up to 20 full-text seed matches with fixed edge weights — it
   is proximity, not PageRank, and only MCP `ContextBundle` uses personalized
   PageRank. Either way the user cannot see the scoring. One clause per item —
   "`PaymentGateway`, because `CheckoutController` calls it directly on the
   success path" — turns a list into context.

4. **Name what you left out.** If the budget cut the bundle, say so and say what
   kind of thing was dropped.

**Stop when** the bundle is within budget and every item has a reason attached.

---

## Choosing between patterns

| The user says | Pattern |
| --- | --- |
| "what is", "how does X work", "explain" | 1 — Understand an entity |
| "what breaks", "what depends on", "safe to change" | 2 — Analyze change impact |
| "why does", "where does this come from", "trace" | 3 — Investigate behavior |
| "how is this organized", "map this", "what are the modules" | 4 — Analyze architecture |
| "give me context", "what do I need to read" | 5 — Assemble task context |

Two patterns often run in sequence — understanding an entity before analyzing
its change impact is the common pair. Run them in order rather than merging
them, so the stop condition of the first still applies.

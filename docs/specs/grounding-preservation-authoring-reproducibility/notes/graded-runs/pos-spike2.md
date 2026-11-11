I wrote a Draft spec and plan for synthetic value nodes in `docs/specs/synthetic-value-nodes/`. Reading the supplied files shows that a test proving only that a value node can be created would miss the main risks. The spec adds 11 preservation criteria (P1–P11) next to the creation test (F1). The work followed the `new-spec` skill and its `shared-substrate-preservation.md` reference.

## What the files show must be preserved

- **Ranking is the real break.** `rank` counts every node by `parent_file`. Value nodes must carry a `parent_file` so the existing cleanup removes them, so they raise their file's rank. A probe confirmed it: two value nodes in file 2 moved `rank(2)` from 2 to 4. The plan's design is for `rank` to skip value nodes (P7).
- **Cleanup needs a parent file.** A value node with `parent_file=None` survives `remove_file_nodes`; the probe confirmed it (P9).
- **Ids must be fresh.** Reusing an id overwrites an existing node and lists the id twice in `name_index`; the probe confirmed it (P1).
- **Already safe paths still get criteria.** `resolve_call` (P2) and default `search` (P3) already filter out value nodes. Values appear only when `include_values=True` (P4).
- **Full and incremental builds must agree.** On the base files the two build paths already differ in insertion order and leave empty `name_index` lists. So P5 and P6 compare the graphs in a way that ignores order and empty lists.
- **Invalidation is bounded.** `invalidated_files` must return the same sets as before (P8). The code that builds the dependency map it reads is not in the supplied files.
- **The Rust surface is protected.** Code outside the module must still build `Resolution` with a struct literal and take it apart field by field (P10). `unresolved` and `consume` must return the same five results as before (P11).
- **Serialization has no reader.** A search of the supplied files found no serializer.

## Checks run

- The grounding inquiry ran in discovery phase. It found no `AGENTS.md`, manifest, test runner or git history. Phrase pins and gates were reported as "input unavailable".
- One probe ran on the unchanged files with nothing written. It produced the confirmations above.

## Gates not met

- **Spec review and adversarial review: blocked.** Subagents were not allowed, so the receipt is `BLOCKED: spec shaping review — independent route unavailable` and the spec stays Draft. The adversarial review was skipped for the same reason.
- **The Rust check cannot run yet.** No Cargo manifest exists, so P10 and P11 have no way to compile. This blocks review until an owner names a build entry.

## What I would have asked a human

1. Should `rank` ignore value nodes? The spec assumes yes; a "no" changes P3 and P7.
2. What creates synthetic values, and does each belong to exactly one file?
3. How should the Rust file be built?
4. Is there a serializer outside the supplied files?
5. Is Shape `data` right? I picked it.
6. Who owns and approves the spec and its Agent Rules?

---

## docs/specs/synthetic-value-nodes/spec.md

```markdown
# Spec: Synthetic value nodes

- **Status:** Draft
- **Owner:** unassigned (no owner named in the repository)
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none — the only public interface in view is the Rust `Resolution` surface in `evals/files/shared-graph-public.rs`, which this spec preserves and does not change
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

Maintainers of the repository graph can add synthetic value nodes (graph nodes of kind `"value"` that no source declaration produced) to a graph and find them through an explicit `include_values=True` search. Every existing reader of the graph returns exactly what it returned on the base revision, except that value nodes appear in search results only when explicitly requested.

## What Changes

- A creation path for synthetic value nodes, each owned by one file — `evals/files/shared-graph-model.py` or the module the plan's discovery step selects.
- Value nodes take part in containment cleanup like declarations do — `evals/files/shared-graph-builders.py`, `evals/files/shared-graph-lifecycle.py`.
- `rank` stops counting value nodes toward a node's rank — `evals/files/shared-graph-consumers.py`.
- The model's module docstring stops describing the graph as "before synthetic value nodes are added" — `evals/files/shared-graph-model.py`.
- A stdlib `unittest` suite holds the base-revision expectations and the feature test — `evals/files/`.
- A compile check exercises the Rust `Resolution` surface from outside its module — location per the plan's discovery step.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applicable: the model module's docstring is the only architecture statement for the graph, and it says the graph has no synthetic value nodes | `evals/files/shared-graph-model.py` module docstring | Implementer of T3 | Diff of the docstring | The docstring describes value nodes as members of the graph that belong to one file |
| Interface compatibility | Applicable: `Resolution` has public fields that external code constructs and destructures | Compatibility check from T2; its location is a required decision (see Assumptions) | Implementer of T2 | The check compiles and passes on the base revision and after T3 | The check exists in the repository and is green |

No other role applies: the repository has no user documentation, decision records, operations guides, maintainer procedures, or changelog for these files.

## Agent Rules

### Always do

- Take every expected value in a preservation test from a run against the base revision, before any feature code exists.
- Give each synthetic value node the id of the file it belongs to as its `parent_file`.
- Run the whole preservation suite, not only the feature test, before calling a task done.

### Ask first

- Changing the allowed delta of any preservation criterion below.
- Adding, removing, or renaming a field of `Resolution`, or changing what `consume` or `unresolved` return.
- Letting a value node add or remove an entry in the dependency map that `invalidated_files` reads.

### Never do

- Add a third-party dependency; the suite uses the Python standard library only.
- Add a new top-level directory or a new module boundary for value nodes.
- Edit a recorded base-revision expectation to match new output.
- Make `resolve_call` or default `search` return a node of kind `"value"`.

## Testing Strategy

- **Value creation (F1):** TDD, because creation has a direct observable in `graph.nodes` and `graph.name_index`.
- **Preservation (P1–P9):** TDD with characterization tests, because each existing reader has a deterministic output on a fixed fixture, and the base revision supplies the expected side.
- **Full and incremental build agreement (P5):** TDD, exercised as an integration test across `build_full`, `apply_incremental`, and the creation path together.
- **Rust compatibility (P10, P11):** goal-based check, because compiling external construction and destructuring code is the observable; P11 also runs the compiled check.

## Acceptance Criteria

Each preservation criterion names the old behavior, its allowed delta, and its oracle. The fixture is the one the plan defines: at least two files, a name shared by declarations in both files, and value nodes owned by each file, one of which shares a name with a declared function. A sustained review finding that the behavior a preservation criterion names has moved contradicts that criterion and leaves it unchecked.

### Feature

- [ ] **F1.** When a synthetic value node is created for file `F` with name `n`, `graph.nodes` holds a node with a fresh id, kind `"value"`, name `n`, and `parent_file` `F`, and `graph.name_index[n]` contains that id once. Red: the node is missing, or its id is absent from `name_index[n]`.

### Preservation

- [ ] **P1 — direct readers and writers.** Old behavior: every node present before value creation keeps its id, name, kind, and `parent_file`, and each `name_index` list keeps every pre-existing id as many times as before. Allowed delta: value ids are appended to the `name_index` list for the value's name. Oracle: the pre-existing node map and index counts recorded on the base revision. Red: a value node reuses an existing node id. Green: a value node with a fresh id that shares a declared function's name.

- [ ] **P2 — selection and resolution.** Old behavior: `resolve_call(graph, name)` returns the same node ids in the same order as on the base revision for every name in the fixture, including a name a value node shares. Allowed delta: none. Oracle: base-revision `resolve_call` output for each fixture name. Red: a value node appears in the result.

- [ ] **P3 — default search.** Old behavior: `search(graph)` and `search(graph, query)` without `include_values` return the same node ids in the same order as on the base revision, for no query and for a query that matches a value node's name. Allowed delta: none. Oracle: base-revision `search` output for each fixture query. Red: a value node appears, or two non-value nodes swap places.

- [ ] **P4 — explicit value search.** Old behavior: with `include_values=True`, the non-value nodes in the result keep the relative order that default `search` gives on the base revision. Allowed delta: value nodes appear in the result, and only on this path. Oracle: the result with value nodes removed equals the base-revision default `search` output for the same query. Red: a created value node is missing from the result, or a non-value node moves.

- [ ] **P5 — full and incremental construction agree.** Old behavior: `build_full` over the final file set and `apply_incremental` from an earlier file set to that same final set produce the same graph. Allowed delta: none. Oracle: the two graphs compared under the plan's normalized comparison, with value nodes present in both. Red: a value node from a replaced file version survives only on the incremental path.

- [ ] **P6 — each build matches the base revision.** Old behavior: the non-value part of the graph from `build_full`, and from `apply_incremental`, equals what the base revision builds from the same inputs. Allowed delta: value nodes are added. Oracle: the base-revision graph for the same inputs, compared under the plan's normalized comparison after removing value nodes. Red: a declaration node is missing, duplicated in `name_index`, or changed.

- [ ] **P7 — ranking.** Old behavior: `rank(graph, node_id)` returns its base-revision value for every pre-existing node id. Allowed delta: none. Oracle: base-revision `rank` output for each fixture node id. Red: value nodes owned by file `F` raise the rank of the node whose id is `F`.

- [ ] **P8 — invalidation.** Old behavior: `invalidated_files(dependencies, file_id)` returns the same set as on the base revision for every fixture file id, using the dependency map in effect after value nodes are created. Allowed delta: none. Oracle: base-revision `invalidated_files` output over the fixture dependency map. Red: value creation adds a dependency edge, so a file that did not call the changed file is invalidated.

- [ ] **P9 — lifecycle and cleanup.** Old behavior: after `remove_file_nodes`, `replace_file`, or `apply_incremental` runs for file `F`, no node that `F`'s previous version owned remains in `graph.nodes` or in any `name_index` list, and nodes owned by other files are unchanged. Allowed delta: none. Oracle: base-revision cleanup output for declarations, with each value node treated as owned by its file. Red: a value node with no `parent_file` survives the removal of its file.

- [ ] **P10 — public construction and destructuring.** Old behavior: code outside the module that builds `Resolution { target, confidence }` with a struct literal and destructures it with `let Resolution { target, confidence } = r;` compiles. Allowed delta: none. Oracle: the T2 compile check, written and passing on the base revision. Red: `Resolution` gains, loses, or renames a public field.

- [ ] **P11 — public results.** Old behavior: `unresolved()` returns `target: None` and `confidence: 0`, and `consume` returns the base-revision value for each of `(None, 0)`, `(None, 1)`, `(Some(1), 0)`, and `(Some(1), 1)`. Allowed delta: none. Oracle: the T2 check's expected values, recorded on the base revision. Red: any of those five results differs.

## Follow-ons

none

## Assumptions

- Product: what produces synthetic values, and from which inputs, is not in the supplied files — it decides where the creation path lives and whether F1's inputs are complete (settled by: feature owner).
- Product: P7 keeps `rank` unchanged, so value nodes add no rank to their file — if the owner wants value nodes to count, P3 and P7 change (settled by: feature owner).
- Technical: the producer of the dependency map that `invalidated_files` reads is not in the supplied files — P8 still bounds that map's output on the fixture.
- Technical: no serializer, dump, or persistence reader appears in the supplied files — if one exists elsewhere, serialization needs its own preservation criterion (settled by: repository owner).
- Technical: the producer of `Resolution` values is not in the supplied files, so whether a `Resolution` can name a value node's id is unknown — P10 and P11 still bound the public surface (settled by: repository owner).
- Technical: no Cargo manifest or Rust build entry exists in the supplied files — P10 and P11 cannot be run until one is named; this blocks review while it stands (settled by: repository owner).
- Process: no owner, approver, or contribution guide exists in the repository — nobody is named to approve this spec or sign off on Agent Rules (settled by: repository owner).
```

## docs/specs/synthetic-value-nodes/plan.md

```markdown
# Plan: Synthetic value nodes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** no architecture or convention source exists (no `AGENTS.md`, manifest, test suite, runner, or git history in the repository). The module the feature touches is the five files under `evals/files/`. No analogous production implementation or test exists to follow. Named deviation: tests use stdlib `unittest` because no test convention exists.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/synthetic-value-nodes/notes/verification-ledger.md`. A genuine
> artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material that an implementer corrects in place only
> before approval.

## Approach

Record the base revision's behavior first, then add the feature against it. T1 writes characterization tests over a fixed fixture and records every expected value from a run on the unchanged files. T2 does the same for the Rust `Resolution` surface. T3 adds the creation path, containment, and the `rank` change, and must turn F1 green while every T1 and T2 expectation stays green unedited. The riskiest part is `rank`: value nodes must carry a `parent_file` for cleanup (P9), and `rank` counts every node by `parent_file`, so containment alone moves P7.

## Constraints

- No ADR or RFC governs these files.
- Python 3.10 or later: the files use `int | None` in dataclass fields, which is evaluated at class creation.
- The file names contain hyphens, so tests load them with `importlib.util.spec_from_file_location` rather than `import`.

## Construction tests

**Integration tests:** the P5 agreement test in T3 drives `build_full`, `apply_incremental`, and the creation path together.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current architecture / `evals/files/shared-graph-model.py` docstring | T3 | Docstring diff | Docstring describes value nodes as file-owned graph members |
| Interface compatibility / T2 compile check | T2 | Check green on base and after T3 | Check is in the repository and green; its location decision is recorded |

## Design (LLD)

### Consumer map

This map is task-local working material; deleting or rebuilding it changes no criterion.

| Class | Consumer evidence | Criterion or gap |
| --- | --- | --- |
| Direct readers and writers | `shared-graph-model.py:19-25` (`add_node`, `remove_node`); `shared-graph-lifecycle.py:4-6` (`attach_to_file`) | F1, P1 |
| Selection and resolution | `shared-graph-consumers.py:4-6` (`resolve_call`, kind filter `{"function", "method"}`) | P2 |
| Default search or presentation | `shared-graph-consumers.py:9-15` (`search`, `include_values` filter) | P3, P4 |
| Ranking and traversal | `shared-graph-consumers.py:18-19` (`rank`, no kind filter) | P7 |
| Full and alternate construction | `shared-graph-builders.py:4-8` (`build_full`), `:11-15` (`apply_incremental`) | P5, P6 |
| Invalidation and update | `shared-graph-builders.py:18-19` (`invalidated_files`); dependency-map producer not in view | P8; unseen producer in spec Assumptions |
| Lifecycle and cleanup | `shared-graph-builders.py:22-24` (`remove_file_nodes`); `shared-graph-lifecycle.py:9-12` (`replace_file`) | P9 |
| Serialization | Unreachable in view: a search of `evals/files/*` for `serial`, `dump`, `json`, `pickle`, `asdict`, `to_dict`, `write`, `save` found no reader | none; out-of-view serializer is a spec Assumption |
| Supported public compatibility | `shared-graph-public.rs:1-13` (`Resolution` public fields, struct literal in `unresolved`, exhaustive destructuring in `consume`) | P10, P11; build entry is a spec Assumption |

### Design decisions

Traces to: F1, P1, P5, P7, P9. Owned by: T3.

- **Value nodes are contained by their file.** Each value node's `parent_file` is its owning file's id, so `remove_file_nodes` and `replace_file` clean it up with no new path. Rejected: `parent_file = None`, which a probe showed survives `remove_file_nodes`. Rests on: every synthetic value belongs to exactly one file.
- **`rank` counts only non-value nodes.** This keeps P7 with containment in place. Rejected: storing values outside `graph.nodes`, which would hide them from `search(include_values=True)`. Rests on: the owner confirms value nodes add no rank (spec Assumptions).
- **Value ids are fresh.** A value id never equals an existing node id. A probe showed `add_node` with a reused id overwrites the node and duplicates the id in `name_index`. The allocation means is `implementation-discovered`; constraint: no collision with any id in `graph.nodes`; verification: P1's red case.
- **Creation seam.** `implementation-discovered`. Discovery predicate: the function or module that knows a value's owning file. Constraint: it adds nodes through `Graph.add_node` or `attach_to_file`. Required outcome: F1. Kill condition: if no seam can learn the owning file, stop and raise the spec's first Product assumption.

### Behavior & rules

Traces to: P5, P6. Owned by: T1.

**Normalized graph comparison.** Two graphs are equal when their `node_id → (name, kind, parent_file)` maps are equal and their `name → multiset of ids` maps are equal after dropping empty lists. The comparison ignores order because a base-revision probe showed `build_full` and `apply_incremental` already differ in `nodes` insertion order and in `name_index` list order. It drops empty lists because `remove_node` leaves an empty list behind when it removes a name's last id.

**Fixture rule.** Every declaration in the fixture carries its file's id as `parent_file`. A base-revision probe showed that a declaration with `parent_file = None` is never removed by `apply_incremental`, so it is re-added and its id is duplicated in `name_index`. That base quirk is outside this feature and would break P5 on the base revision.

### Data & schema

Traces to: F1. Owned by: T3. `Node` keeps its four fields. A value node is a `Node` with `kind = "value"`; `search` already reserves that literal.

## Tasks

### T1: Base-revision characterization suite records P1–P9 expectations and passes on the unchanged files

**Depends on:** none

**Touches:** `evals/files/test_shared_graph.py`

**Tests:**
- One test per preservation criterion P1–P9 in `evals/files/test_shared_graph.py`, each loading the five Python modules through `importlib`. TDD mode; the boundary is the public function each criterion names.
- The fixture follows the Fixture rule in Design: two files, the name `run` declared in both, a `helper` declared in both with different kinds, and a dependency map in which file 2 depends on file 1.
- Expected values are literals captured from a run on the unchanged files and written into the test file.
- The P5 and P6 tests use the normalized comparison from Design. The P5 test first checks that the base revision's two build paths agree on the fixture with no value nodes.
- Until T3 lands, the "with value nodes" side of each test adds file-owned value nodes through `Graph.add_node` with `kind="value"` and a fresh id. Expected on the base revision: the P7 test is red, because `rank` counts value nodes; every other preservation test is green.

**Done when:** `python3 -I -m unittest discover -s evals/files -p 'test_*.py'` shows every T1 test green except the P7 test, which is red for the reason the Tests bullet names.

### T2: Rust `Resolution` compatibility check compiles and passes on the base revision

**Depends on:** none

**Tests:**
- An external-crate-style test that builds `Resolution { target, confidence }` with a struct literal and destructures it with `let Resolution { target, confidence } = r;` (P10). Goal-based.
- The same test asserts the five results P11 names, with expected values recorded on the base revision.

**Approach:**
- Discovery predicate: a Cargo manifest or other Rust build entry that compiles `shared-graph-public.rs`. Kill condition: none exists, so stop and raise the spec's Rust build assumption rather than adding a manifest.

**Done when:** the compile check passes on the base revision through the build entry the owner names.

### T3: Synthetic value creation turns F1 green with every T1 and T2 expectation unchanged

**Depends on:** T1, T2

**Touches:** `evals/files/shared-graph-model.py`, `evals/files/shared-graph-consumers.py`, `evals/files/test_shared_graph.py`

**Tests:**
- F1's feature test in `evals/files/test_shared_graph.py`, driving the creation seam from Design. TDD.
- The T1 tests switch their "with value nodes" side from direct `Graph.add_node` calls to the creation seam. Their recorded expectations stay byte-identical.
- The P5 integration test builds file set A, applies an incremental update to file set B, and compares with `build_full` over B, with value nodes owned by both files in both sets.
- The T2 check stays green.
- The model module's docstring is refreshed per the Durable-output map. Goal-based.

**Done when:** the T1 `unittest` command shows every test green, the T2 check is green, and no recorded expectation differs from its T1 value.

## Rollout

Pure logic in fixture files; no flag, infrastructure, external system, or deployment order applies.

## Risks

- Another caller of `rank` outside the supplied files may depend on counting every node; changing `rank` would move it.
- If the creation seam has no access to the owning file, the containment decision fails and the plan needs a controlled amendment.

## Changelog
```

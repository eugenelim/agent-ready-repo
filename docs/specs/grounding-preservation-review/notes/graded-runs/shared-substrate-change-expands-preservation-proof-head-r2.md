# Deliverable: synthetic-value-nodes spec and plan

The spec and plan are drafted at `docs/specs/synthetic-value-nodes/spec.md` and `docs/specs/synthetic-value-nodes/plan.md` in the working directory. The spec is `Draft` and the plan is `Drafting`; neither is approved.

The proposed feature test proves only that a value can be created (now AC-0001). Adding a node kind to the shared graph reaches every generic reader, so the shared-substrate preservation rule fired. It fired because `rank`, `remove_file_nodes`, `add_node`/`remove_node`, the name index, and the three build paths read the graph with no kind filter. Only `resolve_call` (kind filter) and `search` (`include_values` opt-in) already exclude values. The spec therefore adds 12 preservation criteria (AC-0002 to AC-0013) across 8 reachable behavior classes, plus one named gap (invalidation). The consumer map is in the plan's `## Design (LLD)`.

## Pre-approval probe: what breaks today

The unmodified files were run with value nodes added (throwaway, nothing written):

- Three values owned by `a.py` raise its `rank` from 1 to 4. Default search then lists `b.py` before `a.py`, even though the values themselves stay hidden.
- A value with no owner survives removal of every file.
- A value that reuses id 10 silently replaces the function `run`. After file removal, `name_index["run"]` holds id 10 with no node 10, so `resolve_call("run")` would raise `KeyError`.
- `resolve_call` stays correct because of its kind filter.

## Assumption checkpoint

```
ASSUMPTIONS I'M MAKING:

## Verified
- Technical: the substrate is Graph.nodes + Graph.name_index of Node(node_id, name, kind, parent_file) (evals/files/shared-graph-model.py:6-25)
- Technical: search already hides kind "value" unless include_values=True (evals/files/shared-graph-consumers.py:9-12)
- Technical: resolve_call keeps only kind function/method (evals/files/shared-graph-consumers.py:4-6)
- Technical: rank counts nodes by parent_file with no kind filter (evals/files/shared-graph-consumers.py:18-19; probe above: file order flips)
- Technical: containment (parent_file) is the update and deletion boundary (evals/files/shared-graph-lifecycle.py:1; shared-graph-builders.py:22-24)
- Technical: no serializer exists (grep -rniE "json|pickle|serial|dump|asdict|to_dict|repr|write|save" evals/files: no match)
- Technical: Resolution is a pub struct with all-pub fields, built by struct literal and destructured exhaustively (evals/files/shared-graph-public.rs:1-13)
- Process: no AGENTS.md, architecture doc, manifest, runner, or test exists (repository-grounding discovery: scoped rules none found; gates unavailable, no runner file)

## Unverified
- Technical: nothing in the supplied files produces the `dependencies` map that invalidated_files reads, so whether values change invalidation is ungrounded (searched: grep "dependencies" finds only builders.py:18-19)
- Technical: Rust compiler availability for the compatibility oracle; no Cargo.toml or build file exists (not probed: outside the permitted directories)
- Technical: Python runtime is undeclared; the code's `int | None` syntax needs 3.10 or later (no manifest found)
- Product: a value belongs to exactly one source file and comes from that file's parse (no local source)
- Process: who owns and approves the spec and its Never-do rules (no contribution guidance found)
```

The procedure says to wait for human sign-off here. This run cannot ask, so these assumptions were used to continue:

- One value belongs to one file.
- The Agent Rules entries are proposed for the owner to confirm.
- Python 3.10 or later and the standard library are the runtime and test harness.

The items that are still open are listed in the spec's `## Assumptions`.

## Review and gate status

- `lint-contract-item-alignment.py`: pass, 0 findings. It ran with `--no-since` because there is no git history, so the reworded-criterion rule had no input. It checks only ID and cross-reference alignment. It does not check plan content or whether a criterion can be reached.
- Shaping review (step 6): not run. The evaluation keeps all work inside two directories, and an isolated reviewer could not be held to them. Review is also blocked by the invalidation named gap. The spec stays `Draft`.
- Adversarial review (step 7): not run, for the same reason.
- Before approval: settle the dependency-map gap and the Rust compiler question, confirm value ownership, then run both reviews.
- Keep each fact in one canonical home, and keep the spec body in present tense. Drift between the spec and the code is a bug, fixed in the same PR.

---

# Spec: synthetic-value-nodes

- **Status:** Draft
- **Owner:** <github-handle>
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

Maintainers of the repository graph get synthetic value nodes: nodes of kind
`"value"`, each owned by one source file, that a reader sees only when it asks
for values. Success is that every existing graph reader (call resolution,
default search and its order, ranking, full and incremental builds, updates,
file removal, and the public Rust resolution surface) returns exactly what it
returned before values existed.

## What Changes

- The graph can hold nodes of kind `"value"` owned by one file — `evals/files/shared-graph-model.py`.
- Creating a value whose id is already taken is refused instead of silently replacing the existing node — the value creation path.
- `rank` does not count values toward a file's rank — `evals/files/shared-graph-consumers.py`.
- The three construction paths carry a file's values with its declarations — `evals/files/shared-graph-builders.py` and `evals/files/shared-graph-lifecycle.py`.
- A preservation suite compares every existing reader against outputs captured from the unmodified files — a new test module beside the substrate.
- The public Rust surface in `evals/files/shared-graph-public.rs` does not change; a compile fixture proves it still constructs and destructures as before.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applies: values are file-owned and excluded from rank, which changes the containment rule the lifecycle module states | Module docstrings of `evals/files/shared-graph-lifecycle.py` and `evals/files/shared-graph-consumers.py` (the established in-repository convention; no architecture document exists) | Implementer of T3 and T4 | Docstrings state that values are contained by their file and that `rank` counts declarations only | close-work reads both docstrings and finds them consistent with AC-0007 and AC-0010 |
| Interface compatibility | Applies: `Resolution`, `unresolved`, and `consume` are `pub` | The compile fixture named in plan T5 | Implementer of T5 | AC-0012 and AC-0013 checks green | close-work runs the compile fixture once |
| User promise, product truth, decision rationale, operations, maintainer procedure, release history, reusable learning | Absent: the supplied repository has no user documentation, ADR corpus, runbook, contribution guide, or changelog, and this change creates none | none | none | none | none |

Retention class: repository-durable, at `docs/specs/synthetic-value-nodes/`.
Locator fingerprint: recorded at approval. Required readers: the approver, the
implementer, and every reviewer. Post-closeout evidence owner: the preservation
suite and its committed base golden.

## Agent Rules

### Always do

- Capture the base golden from the unmodified substrate files before any feature code lands, and commit it with the preservation suite.
- Give every synthetic value the kind `"value"` exactly and exactly one owning file.
- Run the whole preservation suite after any change to the model, builders, lifecycle, or consumer modules.

### Ask first

- Any change to a field, constructor, or function signature on the public Rust surface (`Resolution`, `unresolved`, `consume`).
- Making a value a call-resolution candidate, or visible in search without `include_values=True`.
- Adding, changing, or removing any entry of a dependency map because of a value.
- Changing how existing declarations are added, replaced, or numbered.

### Never do

- Never regenerate or edit the base golden from the implementation under test.
- Never add a third-party dependency; the suite uses the Python standard library and the Rust compiler only.
- Never add a module or top-level directory beyond the one preservation test module and the compile fixture.
- Never prove compatibility by asserting that `shared-graph-public.rs` is byte-identical; exercise its construction and destructuring instead.

## Testing Strategy

"Base" in every criterion means the output of the substrate files as they stand
when this spec is approved, run over the shared fixture and captured before any
feature code lands. A base comparison takes its expected side from that
capture, never from the code under test.

- **TDD, unit level on the model (AC-0001, AC-0002, AC-0011).** Each is an invariant of one graph operation with a named red input, so a failing unit test can be written first.
- **Characterization against the base golden (AC-0003, AC-0004, AC-0005, AC-0006, AC-0007).** Each keeps an existing reader's output; only a comparison with outputs captured before the change can fail when that output moves.
- **TDD, integration across builders and lifecycle (AC-0008, AC-0009, AC-0010).** Each compares two construction or cleanup routes over the same fixture, so the oracle is the other route rather than a stored value.
- **Goal-based compile and run check (AC-0012, AC-0013).** Compatibility of a public Rust surface is decided by whether downstream-style code compiles and behaves, which one compiler invocation shows.

## Acceptance Criteria

Each preservation criterion names the behavior it keeps, its allowed delta, and
its oracle. A sustained review finding against a preservation criterion
contradicts it and reopens the criterion.

- [ ] **AC-0001.** When a synthetic value is created for a file, the graph holds a node with that id and name, kind `"value"`, and that file as its owner. Red: the node is missing, has another kind, or has no owner.
- [ ] **AC-0002.** If a synthetic value is created with an id that any node in the graph already holds, creation raises an error and the graph's nodes and name index equal their state before the call. Green: a value with an unused id is created. Red: the existing node is replaced, as the unmodified `add_node` does.
- [ ] **AC-0003.** Keeps: the name index. Allowed delta: a value's id appears under its own name, after the ids already there. Oracle: for every name, the name index with value ids removed equals base in membership and order.
- [ ] **AC-0004.** Keeps: call resolution. Allowed delta: none. Oracle: for every callee name in the fixture, including a name a value shares with a function, `resolve_call` returns the same node ids in the same order as base.
- [ ] **AC-0005.** Keeps: default search. Allowed delta: none. Oracle: for every query in the fixture's query set, including no query, `search(graph, query)` returns the same node ids in the same order as base. Red: three values owned by one file reorder two file nodes, as the pre-approval probe showed.
- [ ] **AC-0006.** Keeps: opt-in search for base nodes. Allowed delta: values appear only when `include_values=True`, and only those whose name matches the query. Oracle: for every query in the query set, the `include_values=True` result with values removed equals the base default result in order, and the removed values are exactly the fixture values matching the query.
- [ ] **AC-0007.** Keeps: ranking. Allowed delta: none. Oracle: for every pre-existing node id, `rank` returns its base value while values are present.
- [ ] **AC-0008.** For the fixture's final file contents, `build_full`, `apply_incremental` from the fixture's earlier contents, and `replace_file` from the same earlier contents each produce a graph with the same set of (id, name, kind, owner) nodes, values included.
- [ ] **AC-0009.** After a file is re-applied with contents that drop one of its values, through either `apply_incremental` or `replace_file`, the dropped value is absent from the graph's nodes and from every name-index list.
- [ ] **AC-0010.** After `remove_file_nodes(graph, f)` for each fixture file `f`, the graph's (id, name, kind, owner) node set equals that of a full build of the fixture without `f`. Red: a value survives its file's removal.
- [ ] **AC-0011.** After every step of the fixture's create, update, and remove sequence, every id in every name-index list is a key of the graph's nodes. Red: a dangling id, which the unmodified code leaves after an id collision followed by file removal.
- [ ] **AC-0012.** Keeps: Rust construction and destructuring. Allowed delta: none. Oracle: a downstream fixture that builds `Resolution { target, confidence }` with a struct literal and destructures it with the exhaustive pattern `let Resolution { target, confidence } = r;` compiles against `shared-graph-public.rs`.
- [ ] **AC-0013.** Keeps: `consume` behavior. Allowed delta: none. Oracle: `consume(unresolved())` is false, `consume(Resolution { target: Some(1), confidence: 1 })` is true, `consume(Resolution { target: Some(1), confidence: 0 })` is false, and `consume(Resolution { target: None, confidence: 1 })` is false.

## Follow-ons

none

## Assumptions

- Technical (named gap): no producer of the `dependencies` map that `invalidated_files` reads exists in the supplied files — whether a value adds or changes a dependency edge, and so whether invalidation is preserved, is ungrounded. This gap blocks review while it stands.
- Technical: whether a Rust compiler is available where the suite runs; the supplied files carry no `Cargo.toml` or build file — without one, AC-0012 and AC-0013 have no running oracle (settled by: a `rustc --version` probe in the build environment, before approval).
- Product: a value is owned by exactly one source file and is created from that file's parse — if a value can span files or have no file, AC-0001, AC-0008, AC-0009, and AC-0010 change and a new lifecycle rule is needed (settled by: the spec owner).
- Process: the supplied repository names no owner, approver, or review route for specs or for the `Never do` rules — the `Owner` header and the approval entries stay open (settled by: the repository maintainer).

---

# Plan: synthetic-value-nodes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** no `AGENTS.md`, architecture document, manifest, runner, or test exists in the supplied repository (repository-grounding discovery run: scoped rules none found, path refs none found, gates unavailable — no runner file). The substrate is `evals/files/shared-graph-model.py`; its readers and writers are the other four files under `evals/files/`. No analogous production implementation of a second node family exists; the closest precedent is the `include_values` opt-in already in `search` (`shared-graph-consumers.py:9-12`). Deviation: the suite and compile fixture introduce the repository's first tests.

## Approach

Capture first, change second. T1 freezes every existing reader's output over a
shared fixture while the substrate is untouched, so each preservation check
compares against base rather than against the new code. T2 adds value creation
to the model. T3 and T4 then make the readers and the construction paths
correct with values present, each judged against the T1 golden or against a
second construction route. T5 is independent and proves the Rust surface
still compiles and behaves. The riskiest part is `rank`: it counts containment,
and containment is also what cleans values up, so the two must be decoupled
without moving any existing rank.

## Constraints

- No ADR or RFC governs this repository; none is cited.
- Python standard library only (`unittest`, `json`, `importlib`); the substrate's `int | None` annotations need Python 3.10 or later.
- The substrate file names contain hyphens, so tests load them by path through `importlib.util.spec_from_file_location`, not by `import`.
- `add_node` keeps its unmodified overwrite behavior for declarations; only the value creation path refuses a taken id (Agent Rule: ask before changing how declarations are added).

## Construction tests

**Integration tests:** the full preservation suite (T1 golden comparisons plus T3 and T4 route comparisons) runs as one `python3 -m unittest` invocation after every task from T2 on.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current architecture — lifecycle and consumers module docstrings | T3, T4 | Docstring diff in the same commits as the rank and lifecycle changes | Both docstrings state file containment of values and declaration-only rank |
| Interface compatibility — Rust compile fixture | T5 | AC-0012 and AC-0013 green | One compile-and-run of the fixture at closeout |

## Design (LLD)

### Design decisions

Traces to: AC-0001, AC-0002, AC-0005, AC-0007, AC-0008, AC-0010.

- **Values are owned through `parent_file`.** The lifecycle module states that containment is the lifecycle boundary (`shared-graph-lifecycle.py:1`), and `remove_file_nodes` deletes by `parent_file` (`shared-graph-builders.py:22-24`), so file-owned values are cleaned up by the existing path. Rejected: owner-less values, which the probe below shows survive every file removal. Rests on: a value belongs to one file (spec Assumptions, Product).
- **`rank` counts declarations only.** `rank` counts nodes whose `parent_file` equals the ranked id (`shared-graph-consumers.py:18-19`), so contained values inflate a file's rank and reorder default search. Excluding kind `"value"` from that count leaves every base rank unchanged, because base graphs hold no values. Rests on: `rank` is the only reader that counts containment (consumer map below).
- **Id refusal lives in the value creation path, not in `add_node`.** Refusing in `add_node` would change base behavior for duplicate declarations. Means: `implementation-discovered`.
- **Values travel with a file's declarations.** `build_full` and `apply_incremental` add `parsed_file.declarations` without setting `parent_file`, while `replace_file` sets it through `attach_to_file`. Carrying values in the same declaration stream, with the owner set at creation, puts them on all three paths from one place. Means: `implementation-discovered`. Discovery predicate: locate the producer of `declarations`; none is in the supplied files. Kill condition: if values cannot reach all three paths from one producer, stop and ask before adding per-path code.
- **The golden is data, captured once.** T1 runs the unmodified modules over the fixture and writes a JSON golden committed with the suite; later tasks only read it.

Owned by: T1, T2, T3, T4.

### Data & schema

Traces to: AC-0001, AC-0003, AC-0011.

`Node` keeps its four fields; a value is a `Node` with `kind="value"` and `parent_file` set. `Graph.nodes` and `Graph.name_index` keep their types. The name index invariant (every listed id is a node key) is checked after each fixture step.

Fixture shape: two file nodes; one function and one method owned by them; a function named `run` and a value also named `run`; three values owned by one file, which is enough to flip the base order of the two file nodes; an earlier and a final content version of one file, where the final drops one value; a value creation attempt reusing a declaration's id.

Owned by: T1, T2.

### Interfaces & contracts

Traces to: AC-0012, AC-0013.

No Python signature changes. `Resolution`, `unresolved`, and `consume` in `shared-graph-public.rs` keep their fields and signatures. The compile fixture includes the public file as a module and holds the downstream-style uses; it is compiled with `rustc` directly because no Cargo manifest exists.

Owned by: T5.

### Consumer map

Built from the substrate definition outward: every function under `evals/files/` that reads or writes `Graph.nodes`, `Graph.name_index`, `Node.kind`, or `Node.parent_file`, plus the public surface.

| Class | Consumer evidence | Criterion or gap |
| --- | --- | --- |
| Direct readers and writers | `shared-graph-model.py:19-25` (`add_node`, `remove_node`) | AC-0001, AC-0002, AC-0003, AC-0011 |
| Selection and resolution | `shared-graph-consumers.py:4-6` (`resolve_call` reads `name_index`, filters kind) | AC-0004 |
| Default search or presentation | `shared-graph-consumers.py:9-15` (`search`, `include_values` filter) | AC-0005, AC-0006 |
| Ranking and traversal | `shared-graph-consumers.py:18-19` (`rank` counts by `parent_file`, no kind filter) | AC-0007 |
| Full and alternate construction | `shared-graph-builders.py:4-8` (`build_full`), `:11-15` (`apply_incremental`), `shared-graph-lifecycle.py:9-12` (`replace_file`) | AC-0008 |
| Invalidation and update | `shared-graph-builders.py:18-19` (`invalidated_files` reads a `dependencies` map whose producer is absent); update via `apply_incremental` and `replace_file` | AC-0009 for update; invalidation is the named gap in spec Assumptions |
| Lifecycle and cleanup | `shared-graph-builders.py:22-24` (`remove_file_nodes`), `shared-graph-lifecycle.py:4-6` (`attach_to_file`) | AC-0010, AC-0011 |
| Serialization | Unreachable: `grep -rniE "json\|pickle\|serial\|dump\|asdict\|to_dict\|repr\|write\|save" evals/files` returned no match | none — no reader |
| Supported public compatibility | `shared-graph-public.rs:1-13` (`pub` struct with all-public fields, struct-literal construction, exhaustive destructuring) | AC-0012, AC-0013 |

Disconfirming probe, run against the unmodified files before review (throwaway, nothing written):

```
base default search (id, rank):           (12,0) (10,0) (11,0) (1,1) (2,2)
three values owned by file 1:             (12,0) (10,0) (11,0) (2,2) (1,4)
resolve_call("run") with value "run":     [10]; name_index["run"] = [10, 20]
owner-less value after removing files:    nodes [1, 2, 30] — value 30 survives
value reusing id 10:                      node 10 becomes kind "value"; after
                                          remove_file_nodes(1), name_index["run"] = [10]
                                          with no node 10
```

It confirms the rank decision (file order flips), the ownership decision (owner-less values leak), AC-0002 (silent replacement), and AC-0011 (dangling index id). Call resolution is already safe because of its kind filter.

Owned by: T1, T3, T4, T5.

## Tasks

### T1: Base golden captured and characterization suite green on the unmodified substrate

**Depends on:** none

**Tests:**
- Characterization, goal-based: the suite loads the five substrate modules by path, builds the Data & schema fixture without values, and records name index, `resolve_call` per callee name, `search` per query with and without `include_values`, `rank` per node id, and the three construction routes' node sets into the golden; this is the expected side of AC-0003, AC-0004, AC-0005, AC-0006, and AC-0007.
- The golden comparison tests pass against the unmodified files, which proves the oracle reads base.

**Touches:** evals/files/test_synthetic_values.py, evals/files/synthetic_values_golden.json

**Done when:** the T1 tests pass with no substrate file changed, and the golden is committed.

### T2: Value creation and its model invariants

**Depends on:** T1

**Tests:**
- TDD unit: create a value for a file and read it back (AC-0001).
- TDD unit: create a value reusing a declaration's id and compare nodes and name index with their pre-call copies (AC-0002).
- TDD property over the fixture's create, update, and remove sequence: name-index ids are a subset of node keys after each step (AC-0011).

**Touches:** evals/files/shared-graph-model.py, evals/files/test_synthetic_values.py

**Done when:** the T2 tests pass and the T1 golden tests still pass.

### T3: Readers return base output with values present

**Depends on:** T2

**Tests:**
- Golden comparison with the three same-file values and the shared `run` name present: name index with value ids removed (AC-0003), `resolve_call` (AC-0004), default `search` (AC-0005), `include_values=True` search with values removed plus the removed set (AC-0006), and `rank` per pre-existing id (AC-0007).

**Touches:** evals/files/shared-graph-consumers.py, evals/files/test_synthetic_values.py

**Done when:** the T3 tests pass, the T1 and T2 tests still pass, and the consumers docstring states that `rank` counts declarations only.

### T4: Construction, update, and cleanup carry values

**Depends on:** T2

**Tests:**
- Integration: node sets from `build_full`, `apply_incremental`, and `replace_file` over earlier-then-final contents are equal (AC-0008).
- Integration: after each update route applies the final contents, the dropped value is absent from nodes and from every name-index list (AC-0009).
- Integration: `remove_file_nodes` per file against a full build without that file (AC-0010).

**Touches:** evals/files/shared-graph-builders.py, evals/files/shared-graph-lifecycle.py, evals/files/test_synthetic_values.py

**Done when:** the T4 tests pass, the T1 to T3 tests still pass, and the lifecycle docstring states that values are contained by their file.

### T5: Rust public surface compiles and behaves as before

**Depends on:** none

**Tests:**
- Goal-based: a compile fixture that constructs `Resolution { target, confidence }` and destructures it exhaustively builds with `rustc` against `shared-graph-public.rs` (AC-0012).
- Goal-based: the fixture's `main` asserts the four `consume` cases and exits 0 (AC-0013).

**Touches:** evals/files/compat_resolution.rs

**Done when:** the fixture compiles and its binary exits 0 with `shared-graph-public.rs` unchanged by this feature.

## Rollout

Pure in-repository logic with no flag, infrastructure, external system, migration, or persisted state; reverting the commits restores base behavior.

## Risks

- The `dependencies` producer is outside the supplied files, so a value could change invalidation without any test here going red (spec Assumptions named gap).
- If the declaration producer cannot carry values on all three construction paths, T4's kill condition stops the task and the design needs a decision.

## Changelog

none

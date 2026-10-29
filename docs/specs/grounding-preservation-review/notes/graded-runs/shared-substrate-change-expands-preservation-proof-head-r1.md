# Synthetic value nodes: draft spec, plan, and consumer map

The spec and plan are drafted at `Status: Draft` / `Drafting` in `docs/specs/synthetic-value-nodes/` of the working repository. The proposed feature test (a value can be created) covers only AC-0001. Twelve more criteria preserve the behavior of every generic reader the new node kind reaches.

## What must be preserved, and why

Adding nodes of kind `"value"` to `Graph.nodes` and `Graph.name_index` fires the shared-substrate rule, because generic readers see them without opting in. Only `search` and `resolve_call` filter by kind. The step-5a probe found one live break: values hidden from default search still change its order, because `rank` counts them. In the probe, default search went from `['go', 'run', 'a.py', 'b.py']` to `['go', 'run', 'b.py', 'a.py']` after two values were added to `a.py`. The probe also showed that an uncontained value survives file cleanup, and that re-adding an id duplicates it in `name_index`.

Eight of nine behavior classes are reachable and each has a criterion. Serialization is unreachable: a search of `evals/` for serializer terms found no match. The full consumer map is in the plan's `## Design (LLD)`.

## Assumption checkpoint

ASSUMPTIONS I'M MAKING:

## Verified
- Technical: the graph is a Python dataclass with `nodes` and `name_index`; `add_node` overwrites by id and appends to the index (`evals/files/shared-graph-model.py:19-21`)
- Technical: default search already hides `"value"` unless `include_values=True` (`evals/files/shared-graph-consumers.py:11-12`)
- Technical: `rank` counts values, so hidden values reorder default search (step-5a probe: order changed from a.py,b.py to b.py,a.py)
- Technical: containment by `parent_file` is the only cleanup boundary (`evals/files/shared-graph-builders.py:22-24`, `evals/files/shared-graph-lifecycle.py:1-12`)
- Technical: no serializer exists (`grep -rniE "json|pickle|serial|dump|to_dict|asdict|repr|export|load" evals/` returned no match)
- Technical: fixture modules load by path with `importlib` (step-5a probe ran all four)
- Process: no guidance, manifest, runner, or git history exists (repository-grounding discovery run: surfaces none, gates unavailable, git unavailable)

## Unverified
- Product: whether values carry dependency edges that should invalidate readers (no local source)
- Product: whether every value belongs to exactly one file (no local source)
- Product: whether values count toward `rank` when `include_values=True` (no local source)
- Technical: which runner compiles the Rust compatibility test (no `Cargo.toml` or build file found)
- Process: who approves the spec and signs off on Agent Rules (no contribution guide found)

The procedure says to wait for a human here. Per the task, I continued with these assumptions: values carry no dependency edges, every value has one containing file, and values never count toward `rank`. Each one is recorded as an open item in the spec's `## Assumptions`.

## Review and gate receipts

- `lint-contract-item-alignment.py`: pass, 0 findings, 1 spec. It proves IDs, task coverage, verification groups, and LLD owners line up. It does not prove the criteria are right, and its stale-assertion rule did not run because there is no git history.
- `BLOCKED: spec shaping review — independent route unavailable`. The evaluation confines work to two directories, and the Rust-runner named gap blocks review while it stands. The spec stays `Draft`.
- `adversarial-reviewer`: not run, for the same reason.

Left to do: the owner settles the three product assumptions and names a Rust runner. Then shaping and adversarial review run, followed by approval.

---

# Spec: synthetic-value-nodes

- **Status:** Draft
- **Owner:** <owner-handle>
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none — the public Rust `Resolution` surface in `evals/files/shared-graph-public.rs` is preserved, not changed (AC-0013)
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads. `Outcome`,
> `What Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working
> material.

## Outcome

Graph maintainers can add a synthetic value node, contained by a source file, to the repository graph fixture. Every existing generic reader of the graph — call resolution, default search, ranking, full and incremental builds, file replacement and cleanup, invalidation, and the public Rust `Resolution` surface — returns what it returned before values existed, and values reach a caller only through `search(..., include_values=True)`.

## What Changes

- A creation path for nodes of kind `"value"` that always carries a containing file — `evals/files/shared-graph-model.py` and `evals/files/shared-graph-lifecycle.py`.
- `rank` ignores value nodes, so hidden values cannot reorder default search — `evals/files/shared-graph-consumers.py`.
- Full builds, incremental builds, and file replacement create and remove a file's values together with its declarations — `evals/files/shared-graph-builders.py`, `evals/files/shared-graph-lifecycle.py`.
- A frozen base snapshot of the five fixture files and a differential test suite that compares the changed graph against it — new test files beside the fixture.
- A Rust compatibility test for `Resolution` — beside `evals/files/shared-graph-public.rs`, runner still to be named (see Assumptions).

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable: `Resolution`, `unresolved`, and `consume` are `pub` and destructured exhaustively by callers | The compatibility test from plan T6 | Spec owner | AC-0013 test green against the changed crate | Test exists and runs in a named runner |
| Current architecture | Not applicable: no architecture document exists in the supplied repository; containment as the lifecycle boundary is stated in `shared-graph-lifecycle.py`'s module docstring, which stays true | none | — | — | — |
| Release history | Not applicable: no changelog or version manifest exists in the supplied repository | none | — | — | — |
| User promise, product truth, operations, maintainer procedure, decision rationale, reusable learning | Not applicable: the fixture has no user docs, runbooks, contribution guide, or decision records | none | — | — | — |

Retention: repository-durable at `docs/specs/synthetic-value-nodes/` in the working repository; every reader is a maintainer of that repository.

## Agent Rules

### Always do

- Take the expected side of every preservation test from the frozen base snapshot, never from the code under test.
- Give every synthetic value a containing file, so file replacement and removal clean it up.
- Exercise each preserved reader on a graph that holds a value sharing a name with an existing function.

### Ask first

- Adding, removing, or renaming any field or `pub` item in `shared-graph-public.rs`.
- Giving values dependency edges or changing what `invalidated_files` returns.
- Changing `Graph.add_node` or `Graph.remove_node` behavior for non-value nodes.

### Never do

- Never add a third-party dependency; tests use the Python standard library and the Rust toolchain only.
- Never add a new module boundary or top-level directory beyond the test files named in the plan.
- Never claim preservation from "existing tests pass", from a file-unchanged check, or from a test that only creates a value.
- Never change the default of `include_values` in `search`.

## Testing Strategy

- **AC-0001, AC-0002, AC-0003, AC-0011 — TDD.** Value creation is logic with a compact invariant: one contained, indexed node per call, and no change to anything already present.
- **AC-0004, AC-0005, AC-0006, AC-0007, AC-0012 — TDD, differential against the base snapshot.** Each reader's old answer is the oracle, so the test runs the base and changed module on the same inputs and compares results.
- **AC-0008, AC-0009, AC-0010 — TDD, integration across builders and lifecycle.** These properties hold only across two modules together, so the test drives `build_full`, `apply_incremental`, `replace_file`, and `remove_file_nodes` on one graph.
- **AC-0013 — Goal-based check.** A compile-and-run test of the supported construction and destructuring surface proves compatibility.

## Acceptance Criteria

- [ ] **AC-0001.** Creating a synthetic value named `n` in file `F` yields exactly one node of kind `"value"` with `parent_file == F` in `graph.nodes`, and its id appears exactly once in `graph.name_index[n]`. Red: the node is missing, uncontained, or indexed twice. Green: a single creation on an empty graph.
- [ ] **AC-0002.** Creating a value whose node id is already present in `graph.nodes` raises an error and leaves `graph.nodes` and `graph.name_index` equal to their state before the call. Red: the existing node is overwritten (the base `add_node` behavior). Green: a fresh id succeeds.
- [ ] **AC-0003.** After values are created, each `graph.name_index` list equals its base-snapshot list for the same declarations, followed only by the ids of values with that name. Red: a declaration id is reordered, dropped, or duplicated. Green: a name shared by a function and a value lists the function id first.
- [ ] **AC-0004.** For every name in the fixture graph, including a name shared by a function and a value, `resolve_call` returns the same node ids in the same order as the base snapshot returns on the same graph without values. Allowed delta: none.
- [ ] **AC-0005.** `search(graph, query)` with `include_values` left at its default returns the same node-id sequence as the base snapshot on the same graph without values, for `query=None` and for a query that matches a value name. Allowed delta: none. Red: a value contained by file `a.py` moves `a.py` behind `b.py`.
- [ ] **AC-0006.** `search(graph, query, include_values=True)` returns the AC-0005 sequence with its relative order intact, plus every value whose name matches the query, and no other node. Allowed delta: values appear only when explicitly requested.
- [ ] **AC-0007.** For every non-value node, `rank(graph, node_id)` equals the base snapshot's `rank` on the same graph without values. Allowed delta: none.
- [ ] **AC-0008.** Applying `apply_incremental` for a changed file to `build_full(old files)` yields the same `nodes` and the same non-empty `name_index` entries as `build_full(new files)`, when old and new files both carry values. Allowed delta: none; empty `name_index` lists left by removal are excluded on both sides, as in the base snapshot.
- [ ] **AC-0009.** After `replace_file` or `remove_file_nodes` for file `F`, no value contained by `F` remains in `graph.nodes` or `graph.name_index`, and every value contained by another file is unchanged.
- [ ] **AC-0010.** Calling `replace_file` for the same parsed file twice yields the same `nodes` and `name_index` as calling it once. Red: a value id appears twice in a `name_index` list.
- [ ] **AC-0011.** Creating a value with no containing file raises an error and leaves the graph unchanged.
- [ ] **AC-0012.** `invalidated_files` returns the base snapshot's result for every dependency map in the fixture suite, and building a graph with values adds no entry to any dependency map. Allowed delta: none.
- [ ] **AC-0013.** A Rust test compiled against the changed `shared-graph-public.rs` constructs `Resolution { target: Some(1), confidence: 3 }`, destructures it exhaustively as `let Resolution { target, confidence } = r;`, and asserts that `unresolved()` destructures to `(None, 0)` and that `consume` returns true only for `Some` with `confidence > 0`. Red: a field is added, removed, or renamed. Allowed delta: none.

## Follow-ons

- <owner-handle>: work-intake item to be filed — decide whether readers of a value are invalidated when that value changes.

## Assumptions

- Product: values carry no dependency edges in this slice, so AC-0012 pins `invalidated_files` to base behavior — if values must invalidate their readers, AC-0012 becomes new behavior and the plan gains a task (settled by: spec owner, before approval).
- Product: every synthetic value belongs to exactly one source file — if graph-level values without a file are needed, AC-0011 inverts and cleanup needs a second lifecycle boundary (settled by: spec owner, before approval).
- Product: values never count toward a file's `rank`, even when `include_values=True` — if they should, AC-0006's order clause changes (settled by: spec owner, before approval).
- Technical: no Rust build manifest or runner exists in the supplied repository — AC-0013 has no oracle that can run. This named gap blocks review while it stands.
- Process: no `AGENTS.md`, contribution guide, or approval record exists in the supplied repository — who approves this spec, and who signs off on Agent Rules, is ungrounded (settled by: repository owner).

---

# Plan: synthetic-value-nodes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** no guidance, manifest, test, or runner exists in the supplied repository (repository-grounding discovery run: surfaces none, scoped rules none, gates unavailable, git unavailable). Anchors are the five fixture files under `evals/files/`. Shared-substrate preservation governs the search instead of the analogue count.

## Approach

Freeze the base fixture first, because no revision control exists to supply the old behavior later. Then add the value creation path, then repair the one generic reader the probe showed breaking (`rank`), then prove builds and lifecycle stay equivalent. The riskiest part is that values hidden from default search still change its order through `rank`; T3 carries that.

## Constraints

- No ADR, RFC, or repository guidance exists in the supplied files.
- Fixture files have hyphenated names, so tests load them by path with `importlib.util.spec_from_file_location`. The step-5a probe loaded all four Python modules this way.
- Python tests use the standard library `unittest` only.

## Construction tests

**Integration tests:** the T4 build/lifecycle suite spans `shared-graph-builders.py`, `shared-graph-lifecycle.py`, and `shared-graph-model.py`.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility — `Resolution` compatibility test | T6 | AC-0013 test green | Test runs in a named runner; blocked until the runner gap closes |

## Design (LLD)

### Data & schema

A value is a `Node` with `kind == "value"` and a non-`None` `parent_file`. No new field is added to `Node`. Traces to: AC-0001, AC-0011.

Owned by: T2

### Design decisions

- `rank` counts only non-value nodes. Rejected: filtering values out of `search` alone, because the step-5a probe shows hidden values still reorder results. Rests on: `rank` has no reader that expects values counted. Traces to: AC-0005, AC-0006, AC-0007. Owned by: T3.
- Values ride the existing containment boundary (`parent_file`) rather than a second cleanup path. Rests on: every value has one containing file. Traces to: AC-0009, AC-0010. Owned by: T4.
- The creation path refuses id collisions instead of changing `Graph.add_node`, so declaration nodes keep base overwrite semantics. Traces to: AC-0002. Owned by: T2.
- The base snapshot is a byte copy of the five fixture files, taken before any edit. Owned by: T1.

Owned by: T1, T2, T3, T4

### Consumer map

The predicate fires: values become members of `Graph.nodes` and `Graph.name_index`, which generic readers observe without opt-in. The explicit-filter exception does not apply, because only `search` (`shared-graph-consumers.py:11-12`) and `resolve_call` (`shared-graph-consumers.py:6`) filter by kind; `rank`, the builders, and the lifecycle paths do not.

| Class | Consumer evidence | Criterion or gap |
| --- | --- | --- |
| Direct readers and writers | `shared-graph-model.py:19-21` `add_node` overwrites an id and appends to `name_index`; `:23-25` `remove_node` | AC-0001, AC-0002, AC-0003, AC-0011 |
| Selection and resolution | `shared-graph-consumers.py:4-6` `resolve_call` reads `name_index`, keeps `function`/`method` | AC-0004 |
| Default search or presentation | `shared-graph-consumers.py:9-15` `search` hides `"value"` unless `include_values` | AC-0005, AC-0006 |
| Ranking and traversal | `shared-graph-consumers.py:18-19` `rank` counts every node whose `parent_file` equals the id, values included; used as `search`'s sort key at `:15` | AC-0007 (and AC-0005 observes the effect) |
| Full and alternate construction | `shared-graph-builders.py:4-8` `build_full`; `:11-15` `apply_incremental` | AC-0008 |
| Invalidation and update | `shared-graph-builders.py:18-19` `invalidated_files` reads a caller-to-targets map | AC-0012; value-dependency question in spec Assumptions |
| Lifecycle and cleanup | `shared-graph-builders.py:22-24` `remove_file_nodes` deletes by `parent_file`; `shared-graph-lifecycle.py:4-12` `attach_to_file`, `replace_file` | AC-0009, AC-0010 |
| Serialization | Unreachable: `grep -rniE "json\|pickle\|serial\|dump\|to_dict\|asdict\|repr\|export\|load" evals/` found no match | none needed |
| Supported public compatibility | `shared-graph-public.rs:1-4` `pub struct Resolution`; `:6-8` literal construction; `:11` exhaustive destructuring | AC-0013; runner gap in spec Assumptions |

Owned by: T1, T2, T3, T4, T5, T6

### Step-5a disconfirming probe

A throwaway stdin script loaded the fixture modules by path and built files `a.py` (id 1) and `b.py` (id 2) with functions `run` and `go`. Base default search returned `['go', 'run', 'a.py', 'b.py']`. After adding two values contained by `a.py`, default search returned `['go', 'run', 'b.py', 'a.py']`, although neither value appears. `resolve_call("run")` stayed `[10]`. A value with `parent_file=None` survived `remove_file_nodes(graph, 1)`, and re-adding id 50 produced `name_index["x"] == [50, 50]`. These results add T3 and the AC-0002, AC-0010, and AC-0011 refusals to the plan.

Owned by: T3

## Tasks

### T1: Base snapshot and differential harness are green on unchanged code

**Depends on:** none

**Tests:**
- Harness self-check: base-versus-head comparison of `resolve_call`, `search`, `rank`, and `invalidated_files` is green before any edit, and reds when the test perturbs one node's name. Supports AC-0004, AC-0005, AC-0007, AC-0012. Verification mode: TDD.

**Approach:**
- Copy the five fixture files into a test-only base directory before T2 starts; the harness loads base and head modules under distinct module names. This must come first because no revision control can recover the base later.

**Done when:** the T1 harness self-check is green on unchanged code and red on the perturbation.

### T2: Value creation is contained, indexed once, and refuses collisions

**Depends on:** T1

**Tests:**
- Unit tests for AC-0001, AC-0002, AC-0003, and AC-0011 on a graph holding a function and a value that share the name `run`. Verification mode: TDD.
- The creation call site is `implementation-discovered`. Discovery predicate: the smallest function in `shared-graph-model.py` or `shared-graph-lifecycle.py` that sets `parent_file` and calls `add_node`. Constraint: `Graph.add_node` keeps base behavior. Kill condition: a collision check needs a change to `add_node` itself, which is an Ask-first item.

**Done when:** the T2 unit tests are green.

### T3: Hidden values no longer move default search or rank

**Depends on:** T2

**Tests:**
- Differential tests for AC-0004, AC-0005, AC-0006, and AC-0007 through the T1 harness, using the step-5a two-file graph as the red case. Verification mode: TDD.

**Done when:** the T3 differential tests are green, and the AC-0005 test is red on T2's head before the `rank` change.

### T4: Full builds, incremental builds, and file replacement agree with values present

**Depends on:** T2

**Tests:**
- Integration tests for AC-0008, AC-0009, and AC-0010. The AC-0008 expected side is `build_full(new files)`; the test first confirms the base snapshot meets the same equivalence for declaration-only files, so a failure is attributable to values. Verification mode: TDD.

**Done when:** the T4 integration tests are green.

### T5: Invalidation keeps its base answers

**Depends on:** T1, T4

**Tests:**
- Differential test for AC-0012 over three dependency maps: empty, one caller, and two callers of one file; plus a check that a graph built with values leaves each map unchanged. Verification mode: TDD.

**Done when:** the T5 differential test is green.

### T6: Rust `Resolution` stays constructible and destructurable

**Depends on:** none

**Tests:**
- Compile-and-run test for AC-0013. The runner is `implementation-discovered`. Discovery predicate: the repository owner names a Cargo manifest or `rustc --test` invocation. Kill condition: no runner is named, so the task stays blocked and the spec gap stands. Verification mode: goal-based.

**Done when:** the T6 compatibility test is green in the named runner.

## Rollout

Pure fixture and test change. No flag, infrastructure, external system, or deployment order applies.

## Risks

- `rank`'s sort direction puts lower-ranked nodes first; a fix that changes the comparison instead of the count would pass T2 and red only in T3.
- The base snapshot is only trustworthy if T1 copies the files before any edit.

## Changelog

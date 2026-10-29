I drafted the spec and plan for synthetic value nodes in `/tmp/gpar-spike3/work/docs/specs/synthetic-value-nodes/`. Both stay at Draft/Drafting: the independent reviews could not run, and one approval blocker is open.

## What must be preserved, and what breaks

Creation alone is not enough to prove safety. I checked nine kinds of existing behavior; eight can be reached by the change, and serialization cannot (no reader of it exists in the files). Each reachable one gets a criterion with the old behavior, the allowed change, and an expected result recorded from the unedited files.

A read-only probe (in memory, no files written) found three hidden breaks:

- **Ranking:** `rank` counts every node owned by a file, values included. So even with values hidden from default `search`, file nodes change order: `[…,1,2]` became `[…,2,1]`. The plan makes `rank` skip values.
- **Cleanup:** a value with no owning file survives `remove_file_nodes`. Creation therefore requires an owning file.
- **Id reuse:** a value that reuses an existing id replaces that node. It also corrupts `name_index`, and `resolve_call` can then fail. Creation refuses ids already in use.

The probe also confirmed the plan's approach. With `rank` skipping values and creation going through `attach_to_file`:
- default search keeps its old order;
- `include_values=True` minus the values equals the default result;
- full and incremental builds agree.

The base incremental build already leaves empty and duplicate `name_index` entries. The spec records these as old behavior that this change must not fix.

## Checks and gates

- **Alignment lint:** `lint-contract-item-alignment.py` passed with 0 findings. Only its reworded-criterion rule did not run, because there is no git history.
- **Grounding run:** `repository-grounding` found no scoped rules, no runners and no git history.

## What I would have asked a human

- **Assumptions to confirm:**
  - Are values created on demand by a caller against a file (my choice), or built from parsed input during construction?
  - Do file ids and node ids share one id space?
  - Who owns the code outside the supplied files: the parser, whatever builds `dependencies`, and the callers?
- **Approval blocker:** AC-0012 (Rust compatibility) has no way to run yet. There is no Cargo manifest, and no `rustc` or `cargo` on this machine. The owner of the Rust file must name the build and toolchain.
- **Shaping review:** `BLOCKED: spec shaping review — independent route unavailable` (subagents were not allowed).
- **Adversarial review:** `adversarial-reviewer: no matching subagent installed; review skipped` (not dispatched by rule).
- **Owner:** no owner is named, so no approval is recorded.

---

## docs/specs/synthetic-value-nodes/spec.md

````markdown
# Spec: Synthetic value nodes

- **Status:** Draft
- **Owner:** <owner-handle> (no owner named yet)
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none — the only public interface in view is the Rust `Resolution` surface in `evals/files/shared-graph-public.rs`, which this spec keeps compatible and does not change (AC-0012)
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
> gates the text it cites.

## Outcome

Code that works with the repository graph can create a synthetic value node owned by a file, and it lives and dies with that file. Every existing reader of the graph — call resolution, default search, ranking, full and incremental builds, file cleanup, invalidation, and the Rust `Resolution` surface — returns exactly what it returned before any value existed, except that values appear in search when the caller passes `include_values=True`.

## What Changes

- A creation operation for synthetic value nodes (kind `"value"`, owned by one file) — `evals/files/shared-graph-lifecycle.py`
- Ranking stops counting value nodes as children of a file — `evals/files/shared-graph-consumers.py`
- The graph model's module docstring describes the model with value nodes present — `evals/files/shared-graph-model.py`
- A base-revision oracle and a preservation suite over every existing graph reader — test location is set in the plan

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth (in-code) | Applicable: the model docstring states the model is "before synthetic value nodes are added", which is false once this ships | `evals/files/shared-graph-model.py` module docstring | Implementer of T2 | Docstring describes value nodes and their file containment | The docstring no longer describes a pre-value model |
| Interface compatibility | Applicable: `Resolution` is `pub` with `pub` fields, and node ids are its `target` | Compatibility check owned by T5 | Owner of `shared-graph-public.rs` | AC-0012 check passes | The check ran on a real Rust toolchain and passed |
| Decision rationale, operations, maintainer procedure, release history, user-facing promise | Not applicable: the repository has no ADR, runbook, guide, changelog, or user documentation surface (search of the repository tree found only `evals/files/`) | none | — | — | — |

Retention: this spec and plan are repository-durable at `docs/specs/synthetic-value-nodes/`, readable by every reviewer and resuming session; the consumer map inside `plan.md` is working material.

## Agent Rules

### Always do

- Take every expected value in a preservation test from the base-revision oracle (plan T1), never from the code under test.
- Give every synthetic value node the kind `"value"` and an owning file id.
- Show each preservation test red against a seeded defect before relying on it as green evidence.

### Ask first

- Any change to `evals/files/shared-graph-public.rs`.
- Any change to `build_full`, `apply_incremental`, `remove_file_nodes`, `replace_file`, `invalidated_files`, or `resolve_call`.
- Letting a synthetic value exist without an owning file, or outlive that file.

### Never do

- Add a dependency outside the Python standard library, or add a new module to the graph code beyond the test suite and its oracle data.
- Change the default of `search(include_values=False)` or the kind filter in `resolve_call`.
- Repair pre-existing `name_index` residue (empty lists left by removal, duplicate ids) in this change; it is base behavior that the oracle records.

## Testing Strategy

- **TDD, unit level (AC-0001, AC-0002, AC-0003).** Creation is a small invariant over one graph: the new node's fields, the untouched existing entries, and the refusal case each have one red input.
- **TDD against a recorded base-revision oracle, unit and cross-path level (AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011).** Each existing reader runs on the same fixture before and after values are created, and the expected side comes from the unmodified fixture files, so a moved behavior fails as an inequality.
- **Goal-based compile-and-run check, integration level (AC-0012).** Compatibility of a public Rust type is proved by a consumer that constructs and destructures it compiling and behaving the same; no Python test can observe it.

## Acceptance Criteria

Each preservation criterion (AC-0004 to AC-0012) states the old behavior, its allowed delta, and its oracle. A sustained review finding that the stated behavior moved beyond its allowed delta contradicts that criterion and means it is not met.

The fixture graph is the one recorded by plan T1: at least two files, each with function, method, and file-kind declarations whose `parent_file` is their file id, and at least one function whose name a synthetic value also uses.

- [ ] **AC-0001.** When a synthetic value is created with a node id absent from `graph.nodes`, a name, and an owning file id, `graph.nodes` gains exactly that one node, with kind `"value"`, that name, and `parent_file` equal to the owning file id, and `graph.name_index[name]` ends with that node id.
- [ ] **AC-0002.** After a synthetic value is created, every node id present before creation maps to an equal node, and every `name_index` list present before creation is unchanged except for the new id appended to the value's own name. Red input: a creation request reusing the id of an existing function.
- [ ] **AC-0003.** If a synthetic value is requested with an id already in `graph.nodes`, or with no owning file, creation raises an error and `graph.nodes` and `graph.name_index` equal their state before the request; the AC-0001 input still succeeds.
- [ ] **AC-0004.** Old behavior: `resolve_call(graph, name)` returns only function and method nodes, in `name_index` order. Allowed delta: none. Oracle: for every name in the fixture, including a name shared with a synthetic value, the returned node ids equal the base-revision result, in the same order.
- [ ] **AC-0005.** Old behavior: `search(graph, query)` with `include_values` left at its default hides value nodes and orders results by `(rank, name)`. Allowed delta: none. Oracle: with synthetic values attached to fixture files, the returned node ids for `query=None` and for a query matching a value's name equal the base-revision result, in the same order. Red input: values attached to the lower-ranked file, which reorder file nodes when ranking counts them.
- [ ] **AC-0006.** Old behavior: values are visible to search only on request. Allowed delta: with `include_values=True`, value nodes matching the query appear in the result. Oracle: the `include_values=True` result with value nodes removed equals the AC-0005 default result in the same order, and contains every synthetic value whose name matches the query.
- [ ] **AC-0007.** Old behavior: `rank(graph, node_id)` counts the nodes whose `parent_file` is `node_id`. Allowed delta: none for every node id present in the base fixture. Oracle: after synthetic values are attached to fixture files, `rank` for each base-fixture node id equals its base-revision value.
- [ ] **AC-0008.** Old behavior: removing a file removes every node whose `parent_file` is that file, from both `graph.nodes` and every `name_index` list. Allowed delta: the removed set includes that file's synthetic values. Oracle: after `remove_file_nodes`, `replace_file`, and `apply_incremental` each run on a file that owns synthetic values, no id of those values remains in `graph.nodes` or any `name_index` list, and every node owned by another file, including its synthetic values, is unchanged.
- [ ] **AC-0009.** Old behavior: `build_full` and `apply_incremental` produce the base-revision `nodes` and `name_index` for the fixture inputs. Allowed delta: the synthetic values created on the graph and their ids in `name_index`. Oracle: for each path, the result with synthetic value nodes and their ids removed equals that path's base-revision result exactly, including empty `name_index` lists.
- [ ] **AC-0010.** Old behavior: a full build and an incremental update of the same final inputs agree. Allowed delta: none. Oracle: graph A is a full build of the original files plus synthetic values on two files, then `apply_incremental` of one of those files; graph B is a full build of the final files plus the synthetic values not owned by the updated file. A and B have equal `nodes`, and equal `name_index` when each is compared as a set of ids per name with empty lists dropped.
- [ ] **AC-0011.** Old behavior: `invalidated_files(dependencies, changed_file_id)` returns the callers whose targets include the changed file. Allowed delta: none. Oracle: for the T1 fixture `dependencies` mapping and each fixture file id, the result after synthetic values exist equals the base-revision result.
- [ ] **AC-0012.** Old behavior: external Rust code builds `Resolution` with the struct literal `Resolution { target, confidence }`, destructures it exhaustively with `let Resolution { target, confidence } = r;`, gets `target: None, confidence: 0` from `unresolved()`, and gets `consume` true only when `target` is `Some` and `confidence > 0`. Allowed delta: none. Oracle: a separate consumer crate doing exactly those four things compiles against the changed source and its four `consume` cases (`Some`/`None` × `0`/`1`) return the base results.

## Follow-ons

none

## Assumptions

- Product: are synthetic values created on demand by a caller against an owning file, or derived from parsed input during construction? This spec takes on-demand creation. Derived creation would change AC-0001's creation surface and the inputs AC-0010 compares (settled by: feature owner).
- Technical: the repository has no Cargo manifest, and the probe host has no `rustc` or `cargo`, so AC-0012's runner is unresolved. It changes the verification strategy, so it blocks approval (settled by: owner of `shared-graph-public.rs`, naming the crate build and toolchain).
- Technical: do file ids and node ids share one id space? `rank` compares `parent_file` with node ids, which implies they do. If they do not, a synthetic value id equal to a file id could gain a nonzero rank under `include_values=True`, which AC-0006 still bounds (settled by: graph owner).
- Technical: these producers and callers are outside the supplied files. The criteria still bound each consumer's output on base-revision inputs: the parser that yields `parsed_file.declarations`, the code that builds the `dependencies` mapping, callers of `search`, `resolve_call` and `rank`, and Rust code that produces `Resolution` values.
````

## docs/specs/synthetic-value-nodes/plan.md

````markdown
# Plan: Synthetic value nodes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** No `AGENTS.md`, architecture source, manifest, runner, or test suite exists (repository-grounding discovery run on `evals/files`: scoped rules none found; gates unavailable, no runner file). The analogous production path is `attach_to_file` and `replace_file` in `evals/files/shared-graph-lifecycle.py`, which already sets containment before `Graph.add_node`. No existing test or construction harness exists, which is the named deviation: T1 creates the oracle.

## Approach

The change is small in code and wide in what it can disturb. Creation reuses the file-containment path, so cleanup, rebuilds, and invalidation need no edit. Ranking is the one reader that breaks without an edit: it counts every node owned by a file, so hidden values still reorder default search. The riskiest part is the oracle, not the code. T1 records base-revision outputs from the unmodified files before any edit, and every preservation test compares against that record.

## Constraints

- No ADR or RFC governs this code.
- Python standard library only; the fixture uses `int | None` annotations, so Python 3.10 or later. The probe host runs Python 3.15.0.
- The fixture files have hyphenated names, so tests load them by path, not by package import.
- Writes stay inside the repository; the oracle is data, not executable code.

## Construction tests

**Integration tests:** AC-0010 crosses `build_full`, `apply_incremental`, and the creation operation; it lives in T4. AC-0012 crosses a crate boundary; it lives in T5.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current product truth — `shared-graph-model.py` docstring | T2 | Docstring diff | Docstring describes value nodes owned by a file |
| Interface compatibility — Rust `Resolution` | T5 | AC-0012 consumer check output | Check ran on a named toolchain and passed; blocked until the spec's runner question is settled |

## Design (LLD)

### Design decisions

- Synthetic values use kind `"value"`. `search` already hides that kind by default (`shared-graph-consumers.py`, `search`), so the default-search filter needs no edit. Rests on: no other kind name is expected by an out-of-view caller.
- Containment through `parent_file` is the lifecycle boundary, as the lifecycle module docstring states. Creation goes through `attach_to_file`, so `remove_file_nodes`, `replace_file`, and `apply_incremental` remove a file's values with no edit. Rejected: a separate value registry, which every cleanup path would have to learn. Rests on: every cleanup path selects by `parent_file`.
- `rank` excludes kind `"value"` from the children it counts. Rejected: giving values `parent_file=None`, which keeps rank stable but leaks values past file removal (probe below). Rests on: no out-of-view caller relies on values counting toward rank.
- Creation refuses an id already in `graph.nodes`. `Graph.add_node` overwrites the node but appends a second index entry, so a collision corrupts `name_index` and later makes `resolve_call` raise `KeyError` (probe below). Rejected: allocating ids inside creation, which would need knowledge of the file-id space that the spec leaves open.
- The creation operation's name and signature are `implementation-discovered`. Constraint: it lives in `shared-graph-lifecycle.py` beside `attach_to_file` and takes the graph, owning file id, node id, and name.

Owned by: T2, T3

Probe (step 5a, in memory, no files written; fixture: two files, functions sharing the name `load`, values attached to file 1):

- Unmodified `rank`: default `search()` order moves from `[10, 20, 11, 21, 22, 1, 2]` to `[10, 20, 11, 21, 22, 2, 1]`. `resolve_call("load")` stays `[10, 20]`.
- A value with `parent_file=None` survives `remove_file_nodes`.
- A value reusing id 10 replaces the function and leaves `name_index["load"] == [10, 20]` with node 10 gone after cleanup.
- Base `apply_incremental` leaves empty `name_index` lists that `build_full` never has; `nodes` still agree.
- With `rank` excluding values and creation via `attach_to_file`: default search order matches base, `include_values=True` minus values matches default, and full and incremental builds agree on `nodes` and on per-name id sets.

### Data & schema

- `Node` gains no field. A synthetic value is a `Node` with `kind="value"` and an int `parent_file`.
- Oracle data: a JSON file recording, for the T1 fixture, the base-revision output of `resolve_call` per name, `search` for each query, `rank` per node id, `build_full` and `apply_incremental` `nodes` and `name_index`, `remove_file_nodes` and `replace_file` results, and `invalidated_files` per file id. It records the SHA-256 of each unmodified fixture file it was produced from. Location is `implementation-discovered`; constraint: inside the repository, next to the suite.

Owned by: T1

### Interfaces & contracts

- `shared-graph-public.rs` is not edited. The compatibility seam is a separate consumer crate depending on it by path. Its manifest and toolchain are blocked on the spec's runner question.

Owned by: T5

### Consumer map

This map is working material; deleting or rebuilding it changes no criterion.

| Class | Consumer evidence | Criterion or gap |
| --- | --- | --- |
| Direct readers and writers | `shared-graph-model.py:19` `add_node`, `:23` `remove_node` | AC-0001, AC-0002, AC-0003 |
| Selection and resolution | `shared-graph-consumers.py:4` `resolve_call` | AC-0004 |
| Default search or presentation | `shared-graph-consumers.py:9` `search` | AC-0005, AC-0006 |
| Ranking and traversal | `shared-graph-consumers.py:18` `rank`; no edge traversal exists in the supplied files | AC-0007 |
| Full and alternate construction | `shared-graph-builders.py:4` `build_full`, `:11` `apply_incremental` | AC-0009, AC-0010 |
| Invalidation and update | `shared-graph-builders.py:18` `invalidated_files`; update via `:11` | AC-0011, AC-0008 |
| Lifecycle and cleanup | `shared-graph-builders.py:22` `remove_file_nodes`; `shared-graph-lifecycle.py:4` `attach_to_file`, `:9` `replace_file` | AC-0008 |
| Serialization | Unreachable: `grep -rnEi 'json\|pickle\|serial\|asdict\|to_dict\|dump\|repr\|export'` over the repository found no match | none needed |
| Supported public compatibility | `shared-graph-public.rs:1` `Resolution`, `:6` `unresolved`, `:10` `consume` | AC-0012 |

Owned by: T1, T2, T3, T4, T5

## Tasks

### T1: Base-revision oracle recorded from the unmodified files

**Depends on:** none

**Tests:**
- A generator script loads the four Python fixture files by path, builds the fixture graph, and writes the oracle data described in `## Design (LLD)` › Data & schema. It runs before any fixture file is edited. This is the expected side for AC-0004, AC-0005, AC-0007, AC-0008, AC-0009, AC-0010, and AC-0011.
- The suite refuses to use the oracle when a recorded fixture hash does not match the base copy it names, so an oracle regenerated from edited code cannot pass silently.
- Verification mode: goal-based.

**Approach:**
- Ordering: this task lands, with its hashes, before T2 or T3 touch any fixture file. Regenerating it later would take the expected side from the implementation.

**Done when:** the oracle file exists with one hash per fixture file, and those hashes match the files at the base revision.

### T2: Synthetic values are created inside their owning file

**Depends on:** T1

**Tests:**
- Unit, TDD: creation on the fixture graph checks the fields and index entry for AC-0001.
- Unit, TDD: a snapshot of `nodes` and `name_index` taken before creation is compared after it for AC-0002. Red against a seeded creation that calls `Graph.add_node` without an id check.
- Unit, TDD: the duplicate-id and missing-owner requests each raise, and the graph equals its snapshot, for AC-0003.
- Goal-based: the `shared-graph-model.py` module docstring no longer says the model predates synthetic value nodes (Durable Outputs, current product truth).

**Done when:** the T2 tests pass, and each was red before the creation operation existed.

### T3: Ranking ignores value nodes, so default search order is unchanged

**Depends on:** T1, T2

**Tests:**
- Unit, TDD: `rank` per base-fixture node id compared with the oracle after values are attached for AC-0007. Red on the unmodified `rank`, as the probe shows.
- Unit, TDD: `search` with `query=None` and `query="load"` compared with the oracle, in order, for AC-0005. Red on the unmodified `rank`.
- Unit: the `include_values=True` result with values removed is compared with the default result, and every matching value is present, for AC-0006. Red against a seeded `search` that ignores `include_values`.

**Done when:** the T3 tests pass, and the AC-0005 and AC-0007 tests were red on the unmodified `rank`.

### T4: Existing readers return their base results with values present

**Depends on:** T1, T2

**Tests:**
- Unit: `resolve_call` per fixture name compared with the oracle for AC-0004. Red against a seeded kind filter that admits `"value"`.
- Unit: after each of `remove_file_nodes`, `replace_file`, and `apply_incremental` on a file owning values, no value id remains, and other files' nodes are unchanged, for AC-0008. Red against values created with `parent_file=None`.
- Unit: each build path's output with values stripped compared with its oracle entry, exactly, for AC-0009. Red against a seeded `add_node` that also indexes under a second key.
- Integration: graphs A and B built as AC-0010 defines and compared under its normalization. Red against a seeded `apply_incremental` that skips `remove_file_nodes`.
- Unit: `invalidated_files` per fixture file id compared with the oracle for AC-0011. Red against a seeded dependency map that gains an edge when a value is created.

**Done when:** the T4 tests pass, and each was shown red against its named seeded defect.

### T5: The Rust `Resolution` surface stays compatible

**Depends on:** none (blocked on the spec's AC-0012 runner question)

**Tests:**
- Integration, goal-based: a consumer crate builds `Resolution` by struct literal, destructures it exhaustively, calls `unresolved()`, and runs the four `consume` cases, for AC-0012. Red against a seeded extra `pub` field on `Resolution`.

**Done when:** the consumer crate compiles and its four cases match the base results on the toolchain the owner names.

## Rollout

Pure library change with no flag, infrastructure, or migration. It is reversible by reverting the commit. T5 cannot run until the owner names the Rust build.

## Risks

- An out-of-view caller of `rank` may rely on values counting as children. AC-0007 bounds only base-fixture ids, so such a caller would surface as a later consumer and take the controlled amendment.
- The base `apply_incremental` leaves empty and duplicate `name_index` entries. AC-0009 records them as base behavior, so a well-meant cleanup in this change fails the suite.

## Changelog

none
````

## Summary

I drafted the spec and plan for synthetic value nodes in `docs/specs/synthetic-value-nodes/`. The spec stays at `Draft` and the plan at `Drafting`. The task's feature test only proves that a value can be created, so I treated the graph as shared: every generic reader of it can now see the new nodes. I mapped each reader in the supplied files and wrote 13 acceptance criteria. AC-0001 to AC-0003 cover creation. AC-0004 to AC-0013 each say what existing behavior must not change, how much change is allowed, and what test result would prove it moved.

**What must be preserved, found by reading the files and running in-memory probes (nothing written):**
- **Default search order breaks.** Search already hides value nodes unless `include_values=True` is passed. But `rank` counts every child node, values included, so it changes the order. In the probe, `alpha.py`'s rank went from 1 to 3 and the order changed from `go, run, stop, alpha.py, beta.py` to `go, run, stop, beta.py, alpha.py`. This is why T2 exists.
- **A reused node id silently overwrites a node.** `Graph.add_node` replaced the function `run` (id 10) with a value. AC-0003 refuses this.
- **A value with no owning file is never cleaned up.** With `parent_file=None`, it survived `remove_file_nodes` and made the full and incremental builds disagree. AC-0002 refuses this.
- **The two build paths already differ slightly today.** `remove_node` leaves empty lists in `name_index`, so the agreement check (AC-0009, AC-0010) drops empty entries and sorts ids before comparing.
- **Call resolution is already safe.** `resolve_call` only keeps functions and methods, so values never appear there (AC-0005).
- **Invalidation needs a guard.** AC-0011 requires that creating a value adds no dependency edge.
- **The Rust struct `Resolution` must keep working.** Its public fields are built and destructured exhaustively, so AC-0013 compiles and runs code that does both, rather than just checking the file is unchanged.
- **Serialization is not affected.** A grep found no serializer anywhere in `evals/`.

**Checks:**
- The repository-grounding probe found no `AGENTS.md`, runner, docs, or git history.
- The new-spec skill's contract-item alignment lint passed with 0 findings. Its reworded-criterion rule could not run, because the repository has no git history.

**Not done (subagents were not allowed):**
- Shaping review: `BLOCKED: spec shaping review — independent route unavailable`.
- Adversarial review: `adversarial-reviewer: no matching subagent installed; review skipped`.
- Human approval: not sought, so the spec stays at `Draft`.

**What I would have asked the owner before writing the body (open items in Assumptions):**
1. Are all value nodes synthetic? The plan uses `kind == "value"` as the only marker.
2. Which caller creates synthetic values, and from what source?
3. Which Rust build compiles `shared-graph-public.rs`? Neither `rustc` nor a `Cargo.toml` exists, so AC-0013 and T5 cannot pass until this is answered.
4. Is a standard-library `unittest` suite under `evals/tests/` acceptable? The repository has no test location, and pytest is not installed.

The new `docs/specs/` directory follows the skill's convention. Nobody has approved it for this repository yet.

---

## docs/specs/synthetic-value-nodes/spec.md

```markdown
# Spec: Synthetic value nodes

- **Status:** Draft
- **Owner:** <owner-handle>
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
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites.

## Outcome

Code that builds the repository graph in `evals/files/` can add a synthetic value node, owned by one file, to the graph.
Every existing generic reader of the graph returns exactly what it returned before for every non-value node, and value nodes appear only where a caller asks for them with `include_values=True`.

## What Changes

- A creation entry point for synthetic value nodes, owned by a file — `evals/files/shared-graph-lifecycle.py`.
- Ranking ignores value nodes when it counts a node's children — `evals/files/shared-graph-consumers.py`.
- Module docstrings describe the graph with value nodes in it — `evals/files/shared-graph-model.py`, `evals/files/shared-graph-consumers.py`.
- A differential test suite compares each generic reader against a frozen copy of the base modules — new test location under `evals/` (see Assumptions).
- A compile-and-run check of the public `Resolution` construction and destructuring surface — `evals/files/shared-graph-public.rs` stays as it is.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | Applicable: the model docstring says the graph is "before synthetic value nodes are added", which goes stale with this change | Module docstrings of `evals/files/shared-graph-model.py` and `evals/files/shared-graph-consumers.py` | Implementer | Docstring check in the T3 tests | Neither docstring describes value nodes as absent or future |
| Interface compatibility | Applicable: `Resolution` in `evals/files/shared-graph-public.rs` is a public struct whose fields downstream code builds and destructures exhaustively | The AC-0013 compatibility check, at the Rust build location the open question below settles | Implementer | AC-0013 check passing | AC-0013 check green on the named Rust build |
| User promise, architecture, decision rationale, operations, maintainer procedure, release history, reusable learning | Not applicable: the repository carries no docs, guides, ADRs, changelog, or runbooks for this fixture | none | — | — | — |

Record retention: this spec and its plan are repository-durable at `docs/specs/synthetic-value-nodes/`. Their readers are the implementer, every reviewer, and close-work. After closeout the test suite owns the evidence. The approval fingerprint (SHA-256 of both files) is recorded in the plan's Changelog when each is approved.

## Agent Rules

### Always do

- Take the expected side of every preservation check from the frozen base copy of the modules, never from the code under test.
- Use `kind == "value"` as the one marker of a value node, which is the marker the existing `search` filter already reads.
- Run the full differential suite after every change to `evals/files/`.

### Ask first

- Adding, removing, or renaming a field on `Node`, `Graph`, or `Resolution`.
- Changing how `remove_node` leaves empty name-index entries.
- Making a synthetic value add any entry to a dependency map.
- Choosing a test location or runner other than the standard-library `unittest` suite the plan names.

### Never do

- Change the public fields of `Resolution` or the signatures of `unresolved` or `consume`.
- Add a third-party dependency, or a new module under `evals/files/`.
- Make `search` return value nodes when `include_values` is not set.
- Create a synthetic value with no owning file, or over an existing node id.

## Testing Strategy

- **AC-0001, AC-0002, AC-0003 — TDD.** Creation has a small invariant (owned, unique id, refused otherwise) that red-green tests pin directly.
- **AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0011 — TDD, differential.** Each reader runs twice on one fixture graph that holds value nodes: once in the code under test, once in the frozen base copy on the same graph with value nodes stripped. The two results must match.
- **AC-0009, AC-0010, AC-0012 — goal-based check, exercised by an integration test.** These properties only show up when the build paths and the lifecycle path run together over a sequence of file revisions.
- **AC-0013 — goal-based check, exercised by a compile-and-run test.** Compatibility is proved by downstream-style code that builds and destructures the struct, not by a file being unchanged.

## Acceptance Criteria

Each preservation criterion below names the old behavior, its allowed delta, and its oracle. A sustained review finding that the behavior moved beyond the stated delta contradicts that criterion.

- [ ] **AC-0001.** When a synthetic value with a fresh node id and a name is created for file `F`, the graph's state equals its prior state plus one change: `nodes` gains that id, mapped to a node with that name, `kind == "value"`, and `parent_file == F`, and `name_index` gains that id at the end of the entry for that name.
- [ ] **AC-0002.** If a synthetic value is created with no owning file (`None`), creation raises an exception, and `nodes` and `name_index` are equal to their state before the call.
- [ ] **AC-0003.** If a synthetic value is created with a node id already in `nodes`, creation raises an exception, and `nodes` and `name_index` are equal to their state before the call. The fixture's colliding id belongs to a `function` node, and that node is still returned by `resolve_call` for its name afterwards.
- [ ] **AC-0004.** Direct writers keep their behavior. For a fixed sequence of `add_node` and `remove_node` calls over non-value nodes built with the four-field `Node` constructor, the resulting `nodes` and `name_index` equal the base copy's result exactly, empty name-index entries included. Delta: none.
- [ ] **AC-0005.** Resolution keeps its behavior. For every name in the fixture graph, including a name shared by a function and a value node, `resolve_call` returns the same node ids in the same order as the base copy on the graph with value nodes stripped. Delta: none.
- [ ] **AC-0006.** Default search keeps its results and order. For `query` set to `None`, to a substring that matches a value node's name, and to a substring that matches nothing, `search(graph, query)` returns the same node ids in the same order as the base copy on the graph with value nodes stripped. The fixture puts at least two value nodes under one file node. Delta: none.
- [ ] **AC-0007.** Value nodes appear only on request. For each query in AC-0006, the set of node ids that `search(graph, query, include_values=True)` returns equals the set from `search(graph, query)` plus every value node whose name contains the query, case-folded. Delta: this added set and nothing else.
- [ ] **AC-0008.** Ranking keeps its counts. For every non-value node in the fixture graph, `rank` returns the value the base copy returns on the graph with value nodes stripped. Delta: none.
- [ ] **AC-0009.** The build paths agree. For a fixture where file `F`'s synthetic values are added, renamed, and removed across revisions, three routes reach the same final revision: a full build of it, a full build of the first revision then the incremental update, and a full build of the first revision then the lifecycle file replacement. All three yield equal `nodes`. Their `name_index` mappings are also equal once empty entries are dropped and each entry's ids are sorted.
- [ ] **AC-0010.** Each build path keeps its behavior. On the AC-0009 inputs, each route's state with value nodes stripped equals the base copy's state for the same route on the same inputs with value nodes stripped. The comparison uses the AC-0009 normalization. Delta: none.
- [ ] **AC-0011.** Invalidation keeps its behavior. For every file id in the fixture dependency map, `invalidated_files` returns the same set as the base copy, and creating a synthetic value leaves that map equal to its prior state. Delta: none.
- [ ] **AC-0012.** Cleanup reaches value nodes. After file `F`'s nodes are removed, or `F` is replaced by a revision that declares no value nodes, no node with `kind == "value"` and `parent_file == F` remains. Every id listed in `name_index` is a key of `nodes`.
- [ ] **AC-0013.** The public `Resolution` surface stays compatible. A check compiled against `evals/files/shared-graph-public.rs` builds `Resolution { target, confidence }` as a literal and destructures it exhaustively with `let Resolution { target, confidence } = ...`. It asserts three results: `consume(unresolved())` is `false`, `consume(Resolution { target: Some(1), confidence: 1 })` is `true`, and `consume(Resolution { target: Some(1), confidence: 0 })` is `false`. Delta: none.

## Follow-ons

none

## Assumptions

- Product: whether every value node is synthetic, or other value nodes exist — if others exist, `kind == "value"` alone cannot mark a synthetic value, and AC-0001, AC-0006, and AC-0007 need a second marker (settled by: feature owner).
- Product: which caller creates synthetic values, and from what source — this bounds the creation entry point's inputs beyond owner, id, and name (settled by: feature owner).
- Technical: the producer of `parsed_file.declarations` is out of view. Bounded by AC-0009 and AC-0010, which take their oracle from the base copy on the same inputs.
- Technical: the producer of the dependency map that `invalidated_files` reads is out of view. Bounded by AC-0011.
- Technical: the repository has no Rust toolchain or Cargo manifest, so the AC-0013 check can be written but not run here. AC-0013 cannot be checked until this is settled (settled by: maintainer naming the Rust build that compiles `shared-graph-public.rs`).
- Process: the repository has no test runner or test directory. The plan proposes a standard-library `unittest` suite under `evals/tests/` (settled by: maintainer accepting or naming the location).
```

## docs/specs/synthetic-value-nodes/plan.md

```markdown
# Plan: Synthetic value nodes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** no architecture, convention, or `AGENTS.md` source exists in the repository. The anchors are the five fixture modules in `evals/files/`. The analogue for creation is `attach_to_file` in `shared-graph-lifecycle.py`. The analogue for an opt-in filter is the `include_values` filter in `search` in `shared-graph-consumers.py`. No tests, runner, or construction path exist; this is a named deviation, and T1 creates the test path.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/synthetic-value-nodes/notes/verification-ledger.md`. A genuine
> artifact error follows the controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material.

## Approach

Preservation tests land before any behavior change, so each one is seen green or red on the base code first. T1 freezes a copy of the base modules and builds the differential harness. T2 fixes the one reader a pre-review probe showed breaking: ranking counts value nodes, which reorders default search. T3 adds the creation entry point. T4 proves build-path agreement and cleanup with values present. T5 adds the Rust compatibility check and waits on the toolchain question. The riskiest part is T2, because `rank` feeds every search ordering.

## Constraints

- No ADR or RFC governs this fixture.
- Standard library only: `pytest` is not installed (`python3 -I -c "import pytest"` fails), so the suite uses `unittest` under Python 3.15.
- The fixture module names contain hyphens, so tests load them by file path through `importlib.util.spec_from_file_location`, never by `import`.
- No Rust toolchain is installed (`rustc` and `cargo` are absent), and no `Cargo.toml` exists.

## Construction tests

**Integration tests:** the AC-0009 to AC-0012 suite in T4 drives the builders and the lifecycle module together.
**Manual verification:** none.

Suite command, from the repository root: `python3 -I -m unittest discover -s evals/tests -t .`

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current product truth — module docstrings | T3 | Docstring check in T3 tests | Check green; docstrings read as current |
| Interface compatibility — `Resolution` check | T5 | Compiled check run | Check green on the Rust build named in the spec's Assumptions |

The consumer map below is delivery residue and has no durable owner. The base snapshot in `evals/tests/base/` is a test fixture owned by the suite.

## Design (LLD)

### Design decisions

- **A value node is a `Node` with `kind == "value"` and no new field.** `search` already filters on that kind, and adding a field to the dataclass changes its constructor, equality, and repr. Rests on: every value node is synthetic (open in the spec's Assumptions).
- **Creation goes through `attach_to_file`.** That is the containment path both cleanup routes use, so an owned value is removed with its file. Rests on: `remove_file_nodes` selects by `parent_file` alone (`shared-graph-builders.py`, `remove_file_nodes`).
- **Creation checks the id before writing.** `Graph.add_node` overwrites `nodes[node_id]` silently and appends a second index entry. The probe below shows a value over id 10 replacing the `run` function. Rests on: ids are the only collision key.
- **`rank` skips value nodes.** Excluding values from `search` results is not enough, because `rank` iterates over all of `graph.nodes`. Rests on: no caller wants value nodes counted as children.
- **The oracle is a frozen base copy, not git.** The repository is not a git checkout, so a base revision cannot be read with `git show`. T1 copies the four Python modules unchanged and records their SHA-256 digests. A test refuses to run if a digest differs.
- **Build-state comparison is normalized.** `remove_node` leaves empty lists in `name_index`, so incremental and full builds already differ there in the base code. AC-0009 and AC-0010 compare `nodes` exactly, then compare `name_index` with empty entries dropped and ids sorted. AC-0004 compares raw state, because there the base behavior itself is the subject.
- The creation function's name and its exception type are `implementation-discovered`. Constraint: it lives in `shared-graph-lifecycle.py` and calls `attach_to_file`. Required outcome: AC-0001 to AC-0003. Verification: T3 tests.

Owned by: T1, T2, T3, T4.

### Data & schema

No field, type, or persisted state changes. `Node` keeps its four fields; `Graph` keeps `nodes` and `name_index`. There is no serializer in the fixture (search below), so no stored format moves.

Owned by: T3.

### Consumer map

This map is working material: deleting or rebuilding it changes no criterion.

| Class | Consumer evidence | Criterion or gap |
| --- | --- | --- |
| Direct readers and writers | `shared-graph-model.py` `Graph.add_node`, `Graph.remove_node` | AC-0001, AC-0003, AC-0004 |
| Selection and resolution | `shared-graph-consumers.py` `resolve_call` (reads `name_index`, keeps `function` and `method`) | AC-0005 |
| Default search or presentation | `shared-graph-consumers.py` `search` (`include_values` filter) | AC-0006, AC-0007 |
| Ranking and traversal | `shared-graph-consumers.py` `rank` (counts every node whose `parent_file` equals the id) | AC-0008, and AC-0006 for its effect on order |
| Full and alternate construction | `shared-graph-builders.py` `build_full`, `apply_incremental`; `shared-graph-lifecycle.py` `replace_file` | AC-0009, AC-0010 |
| Invalidation and update | `shared-graph-builders.py` `invalidated_files`; update via `apply_incremental` and `replace_file` | AC-0011, AC-0009 |
| Lifecycle and cleanup | `shared-graph-builders.py` `remove_file_nodes`; `shared-graph-lifecycle.py` `attach_to_file`, `replace_file` | AC-0002, AC-0012 |
| Serialization | Unreachable: `grep -rniE "json\|pickle\|serial\|asdict\|dump\|to_dict\|repr" evals/` found no match | none needed |
| Supported public compatibility | `shared-graph-public.rs` `Resolution` (pub fields), `unresolved`, `consume` (exhaustive destructure) | AC-0013 |

Owned by: T1, T2, T3, T4, T5.

### Pre-review probe

A throwaway in-memory script, with nothing written, loaded the base modules. It built two file nodes (`alpha.py` id 1, `beta.py` id 2) and three functions (one under file 1, two under file 2). Then it attached two value nodes to file 1. Results:

- Default `search` order moved from `go, run, stop, alpha.py, beta.py` to `go, run, stop, beta.py, alpha.py`. That happened because `rank` of `alpha.py` rose from 1 to 3. This disconfirms "the existing `include_values` filter already protects default search", and it is why T2 exists.
- `resolve_call("run")` still returned only the function, so resolution is already safe.
- A value with `parent_file=None` survived `remove_file_nodes`. A value over id 10 replaced the `run` function. Both are why AC-0002 and AC-0003 refuse.
- Full and incremental builds agreed on owned values, and disagreed once an ownerless value was present.

Owned by: T2, T3.

## Tasks

### T1: Base snapshot and differential harness are in place and green on the base code

**Depends on:** none
**Touches:** evals/tests/base/*, evals/tests/harness.py, evals/tests/test_preservation_readers.py
**Verification mode:** TDD, differential
**Review shape:** WIDE (copied files plus one harness)

**Tests:**
- The harness refuses to run when any file in `evals/tests/base/` differs from its recorded SHA-256 digest, checked by a test that mutates a temporary copy.
- AC-0004: a fixed `add_node`/`remove_node` sequence; raw `nodes` and `name_index` compared against the base copy.
- AC-0005: a fixture where a value node shares the name `run` with a function; `resolve_call` over every name in the graph, compared against the base copy on the stripped graph.
- AC-0011: a dependency map with at least one file that has two callers and one with none; `invalidated_files` for every key and target id compared against the base copy, and the map compared before and after a value is attached with `attach_to_file`.

**Approach:** the snapshot is copied before any edit to `evals/files/`, which is the ordering decision every later oracle depends on.

**Done when:** the T1 tests pass with `evals/files/` unchanged, and the digest-mismatch test fails as designed when its copy is mutated.

### T2: Ranking ignores value nodes, so default search order holds

**Depends on:** T1
**Touches:** evals/files/shared-graph-consumers.py, evals/tests/test_preservation_search.py
**Verification mode:** TDD, differential
**Review shape:** DEEP

**Tests:**
- AC-0006: the probe graph above (two values under `alpha.py`), with `query` set to `None`, to `"lim"` (matching value `limit`), and to `"zzz"`. Ordered node ids compared against the base copy on the stripped graph. It is red on the base code before the change.
- AC-0007: the same three queries with `include_values=True`. The id set is compared with the default set plus the values whose case-folded name contains the query.
- AC-0008: `rank` for every non-value node, compared against the base copy on the stripped graph.

**Done when:** the T2 tests pass and were recorded red on the base code in the verification ledger before the change.

### T3: Synthetic values are created owned and unique, and docstrings are current

**Depends on:** T1
**Touches:** evals/files/shared-graph-lifecycle.py, evals/files/shared-graph-model.py, evals/files/shared-graph-consumers.py, evals/tests/test_creation.py
**Verification mode:** TDD
**Review shape:** DEEP

**Tests:**
- AC-0001: create value `limit` with id 100 for file 1; compare the deep-copied prior state plus the expected entries with the new state.
- AC-0002: create with owner `None`; assert an exception and equality with a deep copy of prior state.
- AC-0003: create with id 10, held by function `run`; assert an exception, equality with a deep copy of prior state, and `resolve_call("run")` returning id 10.
- Durable output: the module docstrings of `shared-graph-model.py` and `shared-graph-consumers.py` no longer contain "before synthetic value nodes are added", and each mentions value nodes.

**Done when:** the T3 tests pass, and the T1 and T2 suites stay green.

### T4: Build paths agree and cleanup reaches value nodes

**Depends on:** T1, T3
**Touches:** evals/tests/test_build_agreement.py
**Verification mode:** goal-based check, exercised by an integration test
**Review shape:** DEEP

**Tests:**
- AC-0009: revision 1 of file 2 declares value `cap`. Revision 2 renames it `cap2` and adds `floor`. Revision 3 removes both. Each revision's declarations carry `parent_file`. Then, for each step from one revision to the next, three routes run: `build_full` of the later revision, `build_full` of the earlier revision then `apply_incremental`, and `build_full` of the earlier revision then `replace_file` with `remove_file_nodes`. A value created through the T3 entry point after each build is applied identically on every route. The routes are compared with the normalization in Design.
- AC-0010: for each route and step, the stripped state is compared with the base copy's same route on the same inputs, stripped.
- AC-0012: after `remove_file_nodes(graph, 2)`, and after replacing file 2 with a revision that has no value declarations, no value node with `parent_file == 2` remains, and every id in `name_index` is a key of `nodes`.

**Done when:** the T4 tests pass, and the full suite command in Construction tests exits 0.

### T5: The public `Resolution` surface compiles and behaves as before

**Depends on:** none
**Touches:** implementation-discovered (Rust test location, settled by the spec's Rust toolchain question)
**Verification mode:** goal-based check, exercised by a compile-and-run test
**Review shape:** DEEP

**Tests:**
- AC-0013: a test crate or `rustc --test` file includes `shared-graph-public.rs` unchanged, builds the struct literal, destructures it exhaustively, and asserts the three `consume` results.

**Done when:** the AC-0013 check compiles and passes on the Rust build the maintainer names, recorded in the verification ledger. Until that build is named, this task is blocked.

## Rollout

Pure fixture and test change. No flag, infrastructure, external system, or deployment order applies. It is reverted by reverting the commit.

## Risks

- The base snapshot could be taken after an edit to `evals/files/`, which would make every differential oracle agree with the change. T1's ordering and digest check guard this.
- If the feature owner says non-synthetic value nodes exist, the marker decision falls, and AC-0001, AC-0006, and AC-0007 need a controlled amendment.
- T5 cannot finish in this environment, so the spec stays `Implementing` until the Rust build is named.

## Changelog

<!-- Approvals only. Each entry records the date, the approver's handle, and the SHA-256 of the approved file. -->
```

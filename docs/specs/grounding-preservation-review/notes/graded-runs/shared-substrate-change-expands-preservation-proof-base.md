# Synthetic value nodes: draft spec, plan, and consumer map

The spec and plan are drafted at `docs/specs/synthetic-value-nodes/spec.md` (Status: Draft) and `docs/specs/synthetic-value-nodes/plan.md` (Status: Drafting) in the working directory. Both are reproduced in full below.

## What must be preserved, and why the feature test is not enough

The proposed feature test proves only AC-0001: a value node can be created. A throwaway in-memory probe of the base modules shows that test passes while existing behavior breaks:

- **Ranking and default search move even though values stay hidden.** `search()` drops `kind == "value"`, but `rank()` counts every node whose `parent_file` matches, values included. Three values on file 2 raise `mod_b`'s rank from 1 to 4 and flip `mod_a`/`mod_b` in default search order.
- **An unowned value never gets cleaned up.** A value with `parent_file=None` survives `remove_file_nodes` for every file.
- **An id collision corrupts the index.** A value reusing id 10 silently replaces the `run` function, and `name_index["run"]` keeps a dangling 10 after file 1 is removed, so `resolve_call("run")` would raise `KeyError`.
- **`resolve_call` is already safe.** It filters to `function`/`method` and returns `[10, 20]` before and after.

Each of the nine behavior classes has a preservation criterion, a cited no-reader search, or a named gap. The consumer map is in the plan's `## Design (LLD)`:

- Direct readers and writers: AC-0002, AC-0003.
- Selection and resolution: AC-0004.
- Default search: AC-0005, with AC-0007 as the one allowed delta (values appear only when explicitly requested).
- Ranking: AC-0006.
- Full and incremental construction: AC-0008.
- Lifecycle and cleanup: AC-0009, AC-0010.
- Supported public compatibility: AC-0011. It exercises `Resolution` construction and destructuring; it does not check that the file is unchanged.
- Serialization: unreachable. The grep cited in the map found no serializer.
- Invalidation and update: **named gap.** The producer of the `dependencies` map is not in the supplied files. This gap blocks review.

## Assumption checkpoint (new-spec step 3)

Grounding inquiry: `explore-grounding.py --root . --phase discovery evals/files` found no scoped rules, no path refs, no `AGENTS.md` or other known surfaces, and no runner. Phrase pins and gates were unavailable, and git was unavailable.

```
ASSUMPTIONS I'M MAKING:

## Verified
- Technical: the graph substrate is `Graph.nodes` plus `Graph.name_index`, written only by `add_node`/`remove_node` (evals/files/shared-graph-model.py:19-25)
- Technical: default search already excludes `kind == "value"` behind `include_values` (evals/files/shared-graph-consumers.py:11-12)
- Technical: `rank` counts value nodes, so hidden values reorder default search (probe above: mod_b 1 -> 4, order flips)
- Technical: cleanup is keyed on `parent_file`; an unowned value survives every file removal (evals/files/shared-graph-builders.py:22-24; probe: True)
- Technical: `Resolution` is a public struct destructured exhaustively (evals/files/shared-graph-public.rs:1-4, :11)
- Technical: no serializer exists in the supplied files (grep for json|pickle|dump|serial|asdict|to_dict|repr|write|save|load|export: exit 1)
- Process: no AGENTS.md, ADR, RFC, or contribution guide exists (grounding inquiry: surfaces present none)

## Unverified
- Technical: producer of the `dependencies` map read by `invalidated_files` (not in supplied files; searched evals/files)
- Technical: a gate that compiles Rust (`rustc` not found; no runner file)
- Product: who calls `search(..., include_values=True)` and whether value nodes need a defined order among themselves
- Product: values never raise a file's rank (my assumption, which the rank decision rests on)
- Process: approver and review cadence (no workflow guidance in the supplied repository)
```

The task says not to wait for a human, so I proceeded on four assumptions:

- `rank` must ignore value nodes. This is the highest-stakes item, and AC-0005 and AC-0006 depend on it.
- Every value belongs to one file.
- Shape is `data`.
- Status stays Draft until the named gap is settled.

The remaining open items are in the spec's `## Assumptions`.

## Checks run

- `lint-contract-item-alignment.py --no-since`: 0 findings, 1 spec checked. The reworded-criterion rule had no input because no base revision exists.
- The lint proves that criterion identifiers, references, task coverage, and LLD ownership line up. It does not prove that the plan's mechanism is correct.

## What is left

The shaping review (step 6) and the spec-mode adversarial review (step 7) were not run. This draft is the pre-review deliverable, and the named `dependencies` gap blocks review while it stands. The next step is to settle that gap, then send both files to `shaping-reviewer` and `adversarial-reviewer`.

Keep one home per fact. When the implementation moves, update the spec in the same PR, and keep the body in present tense.

---

# Spec: synthetic value nodes

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
> `Acceptance Criteria` are what a completion gate reads. `Outcome`,
> `What Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working
> material.

## Outcome

Callers of the repository graph can hold synthetic value nodes (`kind == "value"`) in the same `Graph` as file declarations and can see them when they ask for them with `search(..., include_values=True)`.
Every caller that does not ask for values gets exactly the call resolution, search results, search order, rank, rebuild result, cleanup, and Rust `Resolution` API it gets from the base revision of `evals/files/`.

## What Changes

- A node of kind `"value"` is a supported member of `Graph.nodes` and `Graph.name_index` — `evals/files/shared-graph-model.py`.
- Adding a value node whose `node_id` is already in the graph is refused — `evals/files/shared-graph-model.py`.
- Every value node belongs to a file through `parent_file` — `evals/files/shared-graph-model.py`, `evals/files/shared-graph-lifecycle.py`.
- `rank` counts only non-value nodes, so hidden values cannot reorder default search — `evals/files/shared-graph-consumers.py`.
- A base-revision golden suite and a Rust compile-compatibility test guard the existing consumers — new test files beside `evals/files/` (paths settled in the plan).

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applies: `pub struct Resolution` in `shared-graph-public.rs` is a public construction and destructuring surface | The compile-compatibility test itself (AC-0011) | Implementer of T5 | AC-0011 test passes on the changed crate | `close-work` sees AC-0011 green on the final revision |
| Current architecture | Applies: "value nodes are hidden from rank and default search, and owned by a file" is a new graph invariant | Required decision: no architecture or guidance file exists in the supplied repository | Spec owner | Module docstring in `shared-graph-model.py` until a destination is chosen | Destination chosen, or the docstring accepted as the owner |
| User promise, product truth, operations, maintainer procedure, release history, decision rationale, reusable learning | Not applicable: the supplied repository has no user docs, runbooks, changelog, ADRs, or guides, and this change is internal to the graph fixture | none | — | — | none |

## Agent Rules

### Always do

- Take every preservation expected value from the base revision of `evals/files/` (the golden suite in plan T1), never from the code under change.
- Give every value node a `parent_file` that names an existing file.
- Keep each preservation criterion's allowed delta exactly as stated; a wider delta is a spec amendment.

### Ask first

- Any change to the rank, search order, or `resolve_call` result for a non-value node.
- Any change to the field set, field visibility, or attributes of `pub struct Resolution`, or to `unresolved()` or `consume()`.
- Any change to how `dependencies` is produced or read by `invalidated_files`.

### Never do

- Never edit a golden expected value so it matches new output.
- Never add a dependency, a package manifest, or a new module outside `evals/files/` and its test files.
- Never mark `Resolution` `#[non_exhaustive]` or add a field to it.
- Never let `resolve_call` return a value node.

## Testing Strategy

- **Value creation (AC-0001, AC-0002, AC-0003, AC-0010): TDD.** Each is a small invariant on `Graph` with an exact failing input.
- **Preservation of resolution, search, rank, rebuild, and cleanup (AC-0004, AC-0005, AC-0006, AC-0008, AC-0009): TDD against base-revision goldens.** The expected side comes from running the unmodified base modules over a shared fixture, so the implementation cannot grade itself.
- **Explicit value search (AC-0007): TDD.** It pins the one allowed delta against the same golden.
- **Public compatibility (AC-0011): goal-based, integration surface.** A separate crate-style test compiles against `Resolution`; a compile and a pass are the oracle.
- The proposed feature test (a value can be created) is AC-0001 only. It is not evidence for any preservation criterion.

## Acceptance Criteria

Each preservation criterion names the old behavior, the allowed delta, and its oracle. A sustained review finding that the stated behavior moves contradicts that criterion.

- [ ] **AC-0001.** Adding `Node(node_id, name, "value", parent_file=<existing file id>)` to a graph makes that id present in `graph.nodes` and listed in `search(graph, include_values=True)`. Red: the id is absent from either.
- [ ] **AC-0002.** Direct writers. Adding a value node whose `node_id` is already in `graph.nodes` raises an error and leaves `graph.nodes` and `graph.name_index` equal to their state before the call. Old behavior kept: adding a non-value node behaves as in the base revision. Allowed delta: the refusal applies to value nodes only. Oracle: a value add with `node_id` equal to an existing declaration's id; red if the declaration is replaced.
- [ ] **AC-0003.** Index consistency. After any sequence of value adds, `remove_file_nodes`, `apply_incremental`, and `replace_file` calls on the golden fixture, every id in every `graph.name_index` list is a key of `graph.nodes`. Old behavior kept: the base fixture already holds this. Allowed delta: none. Oracle: walk `name_index` after each step; red on any dangling id.
- [ ] **AC-0004.** Selection and resolution. For every callee name in the golden fixture, including a name shared by a value node, `resolve_call` returns the same node ids in the same order as the base revision. Allowed delta: none. Oracle: base-revision golden.
- [ ] **AC-0005.** Default search. On the golden fixture with value nodes added, `search(graph)` and `search(graph, q)` for every golden query `q` return the same node ids in the same order as the base revision on the fixture without values. Allowed delta: none. Oracle: base-revision golden.
- [ ] **AC-0006.** Ranking. On the golden fixture with value nodes added, `rank(graph, node_id)` for every non-value node equals the base-revision rank on the fixture without values. Allowed delta: none. Oracle: base-revision golden; the fixture attaches at least three values to one file so a counting change reorders that file.
- [ ] **AC-0007.** Explicit value search. `search(graph, include_values=True)` returns every non-value node in its AC-0005 relative order, plus every value node. Allowed delta: values appear only when explicitly requested. Oracle: base-revision golden for the non-value subsequence; red if a value is missing or the non-value order differs.
- [ ] **AC-0008.** Full and incremental construction. For the same final set of parsed files containing value nodes, `build_full` on an empty graph and `build_full` of the earlier files followed by `apply_incremental` of each changed file produce equal `{node_id: (name, kind, parent_file)}` maps and equal `name_index` lists up to order within each list. Old behavior kept: the two paths agree on the base fixture. Allowed delta: none. Oracle: both paths compared to each other and, for non-value nodes, to the base-revision golden.
- [ ] **AC-0009.** Lifecycle and cleanup. After `replace_file` or `apply_incremental` for file `F`, no value node from `F`'s previous version remains in `graph.nodes` or `graph.name_index`, and every value node of every other file is unchanged. Old behavior kept: declarations of `F` are removed and other files are untouched, as in the base revision. Allowed delta: none. Oracle: base-revision golden for declarations, plus a value-presence check.
- [ ] **AC-0010.** No orphan values. Adding a value node with `parent_file=None` raises an error and leaves the graph unchanged. Red: the add succeeds, which leaves a node that no file removal can clean up.
- [ ] **AC-0011.** Supported public compatibility. A test outside `shared-graph-public.rs` that builds `Resolution { target, confidence }` with a struct literal, destructures it with `let Resolution { target, confidence } = r;`, and asserts `consume(unresolved()) == false` and `consume(Resolution { target: Some(1), confidence: 1 }) == true` compiles and passes against the changed crate. Allowed delta: none. Oracle: the compiler and the two assertions; red if any field is added, removed, renamed, or made non-exhaustive.

## Follow-ons

none

## Assumptions

- Technical (named gap, blocks review): the producer of the `dependencies` map read by `invalidated_files` is not in the supplied files — whether value nodes add dependency edges, and so whether invalidation and update keep their base result, is ungrounded. No invalidation criterion can be written until the producer is found. (settled by: the repository owner pointing at the producer, or a search of the full repository)
- Technical: no Rust toolchain is on the authoring machine (`rustc` not found) — AC-0011 cannot run locally, and no CI file names a Rust gate. (settled by: the repository owner naming the gate that runs AC-0011)
- Product: who calls `search(..., include_values=True)` and what they need from value ranking is unknown — it would change AC-0007 if value nodes need a defined order among themselves. (settled by: the feature requester)
- Process: no `AGENTS.md`, contribution guide, ADR, or RFC exists in the supplied repository, so the approver and review cadence are unknown. (settled by: the repository owner)

---

# Plan: synthetic value nodes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** no architecture, convention, or `AGENTS.md` source exists in the supplied repository (grounding inquiry: scoped rules none found, gates unavailable, git unavailable). The substrate is `evals/files/shared-graph-model.py`; its generic consumers are `shared-graph-consumers.py`, `shared-graph-builders.py`, `shared-graph-lifecycle.py`, and the public surface `shared-graph-public.rs`. No tests or manifests exist, so no analogous test or construction path anchors the test layout.

## Approach

Capture the base revision's behavior first, then change the model. T1 runs the unmodified base modules over one fixture graph and freezes their outputs as goldens, so every later preservation test compares against the base rather than against the code under change. T2 makes value nodes a guarded member of `Graph`. T3 fixes the one consumer the probe showed breaking: `rank` counts hidden values. T4 proves rebuild and cleanup keep values consistent. T5 adds the Rust compile-compatibility test. The riskiest part is `rank`, because default search hides values yet still orders by a count that includes them.

## Constraints

- No ADR or RFC governs the supplied files.
- Python syntax in the files (`int | None`, `set[int]`) needs Python 3.10 or later; no manifest pins a version.
- No dependency may be added (spec Agent Rules); tests use the standard library only.

## Construction tests

**Integration tests:** the T1 golden suite, rerun unchanged after T2, T3, and T4, is the cross-task preservation check for AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility — AC-0011 test | T5 | AC-0011 test compiles and passes | AC-0011 green on the final revision, on the gate the owner names |
| Current architecture — value-node invariant | T2, T3 | Module docstring in `shared-graph-model.py` states: values are file-owned, ids are unique, `rank` and default search ignore them | Destination decision recorded, or docstring accepted |

## Design (LLD)

### Design decisions

- **Golden from base, not from head.** T1 imports the base modules before any edit and writes expected outputs as literal data in the test. Rests on: the supplied files are the base revision. Traces to AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009. Owned by T1.
- **`rank` ignores value nodes.** The alternative, excluding values from `parent_file` counting only in `search`, leaves `rank` wrong for any other caller. Rests on: no caller wants values to raise a file's rank (spec Assumptions, Product). Traces to AC-0005, AC-0006. Owned by T3.
- **Values are file-owned.** Requiring `parent_file` lets the existing `remove_file_nodes` clean them up with no new cleanup path. Rests on: every value belongs to exactly one file. Traces to AC-0009, AC-0010. Owned by T2, T4.
- **The refusal sits on the value add path only.** Declarations keep the base overwrite behavior, so no declaration caller changes. Traces to AC-0002. Owned by T2.
- Where the refusal lives (inside `Graph.add_node` or a separate `add_value` method) is `implementation-discovered`; either satisfies AC-0002 and AC-0010.

Owned by: T1, T2, T3, T4

### Data & schema

`Node.kind` gains the value `"value"`. No field is added to `Node`, `Graph`, or `Resolution`.

Owned by: T2

### Consumer map

This map is working material. Deleting it changes no criterion.

Owned by: T1, T2, T3, T4, T5

| Class | Consumer evidence | Criterion or gap |
| --- | --- | --- |
| Direct readers and writers | `shared-graph-model.py:19-21` `add_node` writes `nodes` and appends to `name_index` with no id check; `:23-25` `remove_node` pops both. Probe: a value with an existing id replaces the declaration and leaves a dangling id in `name_index["run"]` | AC-0002, AC-0003 |
| Selection and resolution | `shared-graph-consumers.py:4-6` `resolve_call` reads `name_index`, then keeps only `kind in {"function", "method"}`. Probe: result `[10, 20]` unchanged with a value named `run` | AC-0004 |
| Default search or presentation | `shared-graph-consumers.py:9-15` `search` drops `kind == "value"` unless `include_values=True`, then sorts by `rank` | AC-0005, AC-0007 |
| Ranking and traversal | `shared-graph-consumers.py:18-19` `rank` counts every node whose `parent_file == node_id`, values included. Probe: `mod_b` rank 1 → 4 with three values, and default search order flips `mod_b`/`mod_a` although no value is shown | AC-0006 (and AC-0005) |
| Full and alternate construction | `shared-graph-builders.py:4-8` `build_full` adds declarations only; `:11-15` `apply_incremental` removes then re-adds by file | AC-0008 |
| Invalidation and update | `shared-graph-builders.py:18-19` `invalidated_files` reads a `dependencies` map whose producer is not in the supplied files | Named gap (spec Assumptions, first item) |
| Lifecycle and cleanup | `shared-graph-builders.py:22-24` `remove_file_nodes` removes by `parent_file`; `shared-graph-lifecycle.py:4-12` `attach_to_file` and `replace_file` stamp `parent_file`. Probe: a value with `parent_file=None` survives removal of every file | AC-0009, AC-0010 |
| Serialization | Unreachable in the supplied files: `grep -nEi 'json\|pickle\|dump\|serial\|asdict\|to_dict\|repr\|write\|save\|load\|export' evals/files/*` matched nothing (exit 1) | none — unreachable, search cited |
| Supported public compatibility | `shared-graph-public.rs:1-4` `pub struct Resolution` with two `pub` fields; `:11` exhaustive destructuring `let Resolution { target, confidence } = result;` | AC-0011 |

### Disconfirming probe (step 5a)

A throwaway in-memory script loaded the five base modules and ran them; nothing was written. Results:

```
base search   [('Runner',0),('run',0),('run',0),('mod_b',1),('mod_a',2)]
after search  [('Runner',0),('run',0),('run',0),('mod_a',2),('mod_b',4)]   # 3 values on file 2
resolve run   [10, 20] before and after
orphan value (parent_file=None) survives removal of files 1 and 2: True
value with id 10 replaces the 'run' function; name_index['run'] keeps 10 after file 1 is removed
```

It confirmed that a creation-only test passes while default search order changes. That moved `rank` into the plan as T3.

Owned by: T3

## Tasks

### T1: Base-revision goldens exist for every reachable consumer class

**Depends on:** none

**Tests:**
- Goal-based. One fixture graph: two file nodes, declarations of kinds `function`, `method`, `class` across both files, one callee name shared across files, and a dependency map with at least one caller. The suite records, from the unmodified base modules, `resolve_call` per name, `search` with no query and with each golden query, `rank` per node, the `build_full` and `build_full`+`apply_incremental` graph states, the state after `replace_file`, and `invalidated_files` per file. Expected values are literal data in the test file.
- Test file location is `implementation-discovered`: no test directory exists. Discovery predicate: none exists, so the test sits beside `evals/files/`. Kill condition: a test directory or runner appears that names a different place.

**Done when:** the golden suite passes against the unmodified base modules, and its expected data contains no call into the modules under test.

### T2: Value nodes are a guarded graph member

**Depends on:** T1

**Tests:**
- TDD on `Graph`: AC-0001 with a value attached to file 2; AC-0002 with a value whose id equals a declaration's id, asserting `nodes` and `name_index` equal their snapshot; AC-0010 with `parent_file=None`.
- TDD: AC-0003 walks `name_index` after each step of add, `remove_file_nodes`, `apply_incremental`, `replace_file`.
- AC-0004: T1 `resolve_call` goldens rerun with a value named like an existing callee.

**Touches:** `evals/files/shared-graph-model.py`, the T1 test file

**Done when:** the T2 tests and the unchanged T1 suite pass.

### T3: Hidden values do not move rank or default search

**Depends on:** T2

**Tests:**
- TDD: the fixture plus three values on one file; AC-0005 and AC-0006 compare to T1 goldens. Red before the change is the probe's `mod_b` rank 4 and flipped order.
- TDD: AC-0007 checks the non-value subsequence of `search(include_values=True)` against the AC-0005 golden order and that every value id is present.

**Touches:** `evals/files/shared-graph-consumers.py`, the T1 test file

**Done when:** the T3 tests and the unchanged T1 suite pass.

### T4: Rebuild and cleanup keep values consistent

**Depends on:** T2

**Tests:**
- TDD: AC-0008 compares `build_full` on the final files with `build_full` on the earlier files followed by `apply_incremental`, both containing values; the non-value part also matches the T1 golden.
- TDD: AC-0009 runs `replace_file` and `apply_incremental` on a file that held values, then checks old values are gone from `nodes` and `name_index` and the other file's values are unchanged.

**Touches:** `evals/files/shared-graph-builders.py`, `evals/files/shared-graph-lifecycle.py`, the T1 test file

**Done when:** the T4 tests and the unchanged T1 suite pass.

### T5: `Resolution` keeps its construction and destructuring surface

**Depends on:** none

**Tests:**
- Goal-based, integration surface: a test outside `shared-graph-public.rs` performs the AC-0011 struct literal, destructuring, and two `consume` assertions.
- Gate is `implementation-discovered`: no Rust toolchain or runner exists in the supplied repository. Kill condition: the owner names no gate that compiles Rust, which leaves AC-0011 unprovable and returns the spec to review.

**Done when:** the AC-0011 test compiles and passes on the named gate.

## Rollout

Pure in-repository logic change. No flag, infrastructure, external system, or deployment order applies. Rollback is a revert.

## Risks

- A caller outside the supplied files may already depend on `rank` counting every node; the supplied files show none.
- The `dependencies` producer may emit edges for values, which would change `invalidated_files`; this stays a named gap until found.

## Changelog

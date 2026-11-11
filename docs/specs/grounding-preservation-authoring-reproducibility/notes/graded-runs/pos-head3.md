## Summary

I wrote a Draft spec and plan for synthetic value nodes under `docs/specs/synthetic-value-nodes/`. Before writing them I checked the supplied files for every existing behavior a new `value` kind could disturb. The feature test only proves a value can be created, so the spec adds preservation criteria. Each one compares the changed code with a frozen copy of today's five files.

**What the files showed (one throwaway in-memory probe, not committed; I deleted the `__pycache__` it left behind):**
- **`rank` reorders search:** `rank` counts every node whose `parent_file` matches. Three values owned by file 10 raised its rank from 1 to 4, and files 10 and 20 swapped places in default search, even though values are hidden there.
- **`add_node` silently overwrites:** adding a value with an existing id replaced function 11. It also left `name_index["alpha"] == [11, 32]`, pointing at a value with a different name.
- **Full and incremental builds diverge:** a value with no owning file survived `apply_incremental`, but `build_full` of the same final file did not produce it.
- **`resolve_call` is already safe:** its kind allowlist filters values out.
- **`search` is already safe:** its explicit `include_values` filter hides values unless asked.
- **Serialization is unreachable:** a grep for json, pickle, serialize, dump, to_dict, asdict and repr found nothing (exit 1).
- **Public surfaces:** `Resolution` in the Rust file is built as a struct literal and destructured exhaustively, so adding a field would break downstream callers. `Node` is built by position.

**What the contract covers:** 13 criteria, AC-0001 to AC-0013, across all nine behavior classes. These include full-versus-incremental build agreement and Rust and `Node` compatibility checks that exercise construction, not "file unchanged". The plan has five tasks and a consumer map with line numbers. Because there is no git history, task T1 freezes a base copy to serve as the oracle.

**Checks:** `lint-contract-item-alignment.py` passed with 0 findings. Rule 9 had no input because I ran it with `--no-since` (there is no git).

**Not done or still open:**
- **Reviews:** subagents were not allowed, so the receipt is `BLOCKED: spec shaping review — independent route unavailable`. I also did not run the adversarial review. The spec stays at `Draft`.
- **Questions I would have asked the owner** (I wrote the body using my best answer to each, and recorded them in the spec's Assumptions):
  1. Should values arrive through each file's `declarations`, or from a separate pass after building?
  2. Should `rank` skip values, or is a rank change for files that own values acceptable?
  3. Where can AC-0012 run? `rustc` is not installed and there is no `Cargo.toml`.
  4. Who approves the spec and its `Never do` list?
- **Location:** `docs/specs/` and `tests/` are new top-level directories in `/tmp/gpar-head-pos3/work`. The repository has no guidance on adding them.

---

## docs/specs/synthetic-value-nodes/spec.md

```markdown
# Spec: synthetic value nodes

- **Status:** Draft
- **Owner:** <github-handle>
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none — the Rust `Resolution` surface in `evals/files/shared-graph-public.rs` is a supported public surface this spec preserves, not one it defines or changes
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

Code that builds and reads the repository graph in `evals/files/` can hold synthetic value nodes (nodes of kind `value`) that belong to the file that produced them. Every existing graph reader returns exactly what it returned before values existed, and values show up only where a caller asks for them with `include_values=True`.

## What Changes

- A value node is created for a file and joins `Graph.nodes` and `Graph.name_index` — `evals/files/shared-graph-model.py`, `evals/files/shared-graph-lifecycle.py`.
- Adding a value node whose `node_id` is already in the graph is refused — `evals/files/shared-graph-model.py`.
- `rank` stops counting value nodes, so default search order stays as it was — `evals/files/shared-graph-consumers.py`.
- A preservation suite pins nine existing behavior classes against a frozen copy of the current files — new test location, chosen in plan task T1.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable: `Node`, `Graph`, and the Rust `Resolution` struct are constructed and read by callers outside the changed lines | The preservation suite named in plan task T1 | Implementer of T1–T5 | Suite green on the changed files, with the expected side taken from the frozen base copy | `close-work` sees every AC in this spec checked and the suite green |
| Current architecture | Not applicable: the repository has no architecture surface (no `AGENTS.md`, no `docs/architecture/`), and the ownership rule "a value belongs to its file" is readable from code and tests | none | — | — | — |
| User promise, operations, maintainer procedure, release history, reusable learning | Not applicable: the repository is a fixture with no user docs, runbooks, release notes, or learning store | none | — | — | — |

Retention class: repository-durable, at `docs/specs/synthetic-value-nodes/`. Required readers are the implementer and the spec reviewers. The post-closeout evidence owner is the preservation suite.

## Agent Rules

### Always do

- Take the expected side of every preservation check from the frozen base copy of the five files in `evals/files/`, never from the code under test.
- Keep a value node owned by exactly one file through `parent_file`.
- Keep every existing call form of `build_full`, `apply_incremental`, `invalidated_files`, `remove_file_nodes`, `attach_to_file`, `replace_file`, `resolve_call`, `search`, and `rank` working unchanged.

### Ask first

- Any change to `evals/files/shared-graph-public.rs`, including adding a field or variant to `Resolution`.
- Any change to what `Graph.add_node` or `Graph.remove_node` do for nodes whose kind is not `value`.
- Giving a value node a role in call resolution or in the `dependencies` map that `invalidated_files` reads.

### Never do

- Never add a third-party dependency; the suite uses the Python standard library (`unittest`).
- Never add a module or package boundary beyond the five files in `evals/files/` and the one test location chosen in T1.
- Never make a value node visible in `search` unless the caller passes `include_values=True`.
- Never weaken or regenerate the frozen base copy to make a preservation check pass.

## Testing Strategy

The oracle for every preservation criterion is the frozen base copy of `evals/files/` (plan T1). Each check runs the same inputs through the base copy and the changed files and compares the stated projection.

- **TDD — value creation and collision (AC-0001, AC-0002):** the invariant is small and local, so a red test comes first at the `Graph` boundary.
- **TDD with a base-revision oracle — writers, resolution, search, and ranking (AC-0003, AC-0004, AC-0005, AC-0006, AC-0007):** each compares the changed code with the base copy over one shared fixture graph, so a moved behavior turns the check red.
- **Integration with a base-revision oracle — construction, invalidation, and lifecycle (AC-0008, AC-0009, AC-0010, AC-0011):** these only prove out across the builder, lifecycle, and model files working together.
- **Goal-based compile check — public compatibility (AC-0012, AC-0013):** a downstream-style snippet must construct and destructure the supported surfaces; a compile or construction failure is the red signal.

## Acceptance Criteria

The shared fixture is the graph the plan names in T1: at least two files, each owning a `function` node and a `method` node, and at least one value node whose name equals an existing function's name. "Value-free graph" means the same fixture with every value node left out. Every comparison in AC-0003 to AC-0011 runs the same inputs through the base copy and through the changed files.

- [ ] **AC-0001.** Creating a value node for file `F` leaves a node in `graph.nodes` under its `node_id` with `kind == "value"` and `parent_file == F`, and that `node_id` appears once in `graph.name_index[name]`.
- [ ] **AC-0002.** Adding a value node whose `node_id` is already a key of `graph.nodes` raises `ValueError`, and `graph.nodes` and `graph.name_index` compare equal to their state before the call. Green case: a value node with a fresh `node_id` is added without error.
- [ ] **AC-0003.** For the fixture's sequence of `add_node` and `remove_node` calls on non-value nodes, interleaved with value additions on the changed side only, `graph.nodes` restricted to non-value nodes equals the base result, and each `name_index` list with value ids removed equals the base list in the same order, empty lists included. Allowed delta: value ids may appear in `name_index` lists.
- [ ] **AC-0004.** For every name in the fixture's `name_index`, `resolve_call(graph, name)` on the fixture returns the same `node_id` list, in the same order, as the base copy on the value-free graph. Allowed delta: none.
- [ ] **AC-0005.** For each query in `None`, `""`, a substring that matches both a value and a non-value node, and a name shared by a value and a function, `search(graph, query)` with the default `include_values=False` on the fixture returns the same `node_id` list, in the same order, as the base copy on the value-free graph. Allowed delta: none.
- [ ] **AC-0006.** For every non-value `node_id` in the fixture, `rank(graph, node_id)` equals the base copy's `rank` on the value-free graph, including for the file whose id is the `parent_file` of a value node. Allowed delta: none.
- [ ] **AC-0007.** For each query in AC-0005, `search(graph, query, include_values=True)` returns exactly the default result's nodes plus the value nodes whose names contain the query (case-folded), and the non-value nodes keep their default relative order. Allowed delta: value nodes appear only in this opt-in call.
- [ ] **AC-0008.** For the fixture's final file set with value nodes present, `build_full` from an empty graph and `apply_incremental` from the previous file contents produce equal `graph.nodes` mappings and equal `name_index` content, compared per name as sorted id lists with empty lists ignored.
- [ ] **AC-0009.** With value nodes removed, the graph that `build_full` produces and the graph that `apply_incremental` produces each equal the base copy's graph from the same value-free inputs, under the AC-0008 comparison. Allowed delta: none.
- [ ] **AC-0010.** For the fixture's `dependencies` map and every file id in it, including a file that owns value nodes, `invalidated_files(dependencies, file_id)` returns the same set as the base copy. Allowed delta: none.
- [ ] **AC-0011.** After `replace_file` or `apply_incremental` replaces file `F`, the value nodes in `graph.nodes` are exactly the value nodes of every other file plus those in `F`'s new declarations, and every id in every `name_index` list is a key of `graph.nodes`.
- [ ] **AC-0012.** A downstream Rust snippet that builds `Resolution { target: Some(7), confidence: 1 }` as a struct literal and destructures a `Resolution` with the exhaustive pattern `let Resolution { target, confidence } = r;` compiles against `evals/files/shared-graph-public.rs`, and `consume` returns `true` for that literal and `false` for `unresolved()`. Allowed delta: none.
- [ ] **AC-0013.** `Node(1, "f", "function")`, `Node(1, "f", "function", 2)`, and the keyword form `Node(node_id=1, name="f", kind="function", parent_file=2)` construct nodes whose four fields equal the base copy's for the same call, with `parent_file` defaulting to `None`, and `Graph()` starts with empty `nodes` and `name_index`. Allowed delta: none.

## Follow-ons

none

## Assumptions

- Technical: Who produces value nodes is not in the supplied files. The plan routes them through each file's `declarations` so both build paths and `replace_file` build them the same way. If values are instead made by a separate pass after building, AC-0008 needs that pass in both paths — this changes the mechanism and maybe AC-0008 (settled by: feature owner).
- Technical: `rank` counts nodes whose `parent_file` equals the ranked `node_id`, so a file-owned value raises its file's rank and reorders default search (probe: file rank went from 1 to 4 and two files swapped order). The plan makes `rank` skip value nodes. The other choice is to accept a rank delta for files that own values, which would rewrite AC-0005 and AC-0006 (settled by: feature owner).
- Technical: `rustc` is not installed here (`rustc --version`: command not found), and there is no `Cargo.toml`. AC-0012 has an oracle but no place to run it yet — this decides whether AC-0012 can be checked before merge (settled by: repository owner naming a Rust toolchain or CI job).
- Technical: bounded unseen producer — whatever parses files into `declarations` is out of view. AC-0008, AC-0009, and AC-0011 bound it by checking builder output on fixture declarations.
- Technical: bounded unseen producer — whatever fills the `dependencies` map is out of view. AC-0010 bounds it by checking `invalidated_files` on a fixture map.
- Technical: bounded unseen producer — how the Python graph feeds `Resolution` is out of view. AC-0012 bounds it at the Rust surface.
- Process: who approves this spec and its `Never do` list, and where review runs, is not recorded in the repository (no `AGENTS.md`, contribution guide, or prior spec) (settled by: repository owner).
```

## docs/specs/synthetic-value-nodes/plan.md

```markdown
# Plan: synthetic value nodes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** no architecture or convention source exists (no
  `AGENTS.md`, no `docs/architecture/`, no manifest, no test runner, no git
  history). The substrate is `evals/files/shared-graph-model.py`; its readers
  and writers are the other four files in `evals/files/`. No analogous
  production implementation or test exists, so the preservation suite is the
  first test in the repository.

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

Freeze the base first, then change the code. T1 copies the five files in
`evals/files/` into a read-only base directory and builds the shared fixture,
because the repository has no git history to diff against and every
preservation oracle needs a base side. T2 adds the value node and its collision
guard. T3 makes `rank` skip values. T4 and T5 add the integration and
compatibility checks. The riskiest part is `rank`: the probe in
[Design decisions](#design-decisions) shows that file-owned values change
default search order unless `rank` skips them.

## Constraints

- No ADR or RFC governs this repository.
- The files use hyphenated names (`shared-graph-model.py`), so tests load them
  by path with `importlib.util.spec_from_file_location`, not by `import`.
- The builder, consumer, and lifecycle files do not import the model; they
  take any object with `nodes`, `name_index`, `add_node`, and `remove_node`.
- Python is 3.15.0 (`python3 --version`); `pytest` is not installed, so the
  suite uses `unittest` (`python3 -m unittest`).
- `rustc` is not installed, so T5's Rust check cannot run here (spec
  `## Assumptions`).

## Construction tests

**Integration tests:** T4 owns the cross-file checks.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility — preservation suite | T1, T2, T3, T4, T5 | Suite green on the changed files against the frozen base copy | Every spec AC checked; suite green; base copy byte-equal to the T1 snapshot |

The consumer map and design decisions below are delivery residue. The lasting
fact ("a value belongs to its file and is hidden unless requested") is readable
from the code and the suite.

## Design (LLD)

### Design decisions

- **Values ride in each file's `declarations` with `kind == "value"`.** Both
  `build_full` and `apply_incremental` then add them, and `remove_file_nodes`
  and `replace_file` remove them with their file. Rejected: a separate pass
  after building, which `apply_incremental` would skip. Rests on: the unseen
  parser can emit values per file (spec `## Assumptions`). Traces to: AC-0001,
  AC-0008, AC-0011.
- **The value creator sets `parent_file` through `attach_to_file`.** Ownership
  is the lifecycle boundary in `shared-graph-lifecycle.py`, so a value must
  have an owner or incremental updates leave it behind. Probe: an unowned value
  survived `apply_incremental` while `build_full` of the same final file lacked
  it. Traces to: AC-0001, AC-0011.
- **`Graph.add_node` refuses a value whose `node_id` is present; other kinds
  keep overwriting.** Base `add_node` silently replaces the node and leaves the
  old id under the old name in `name_index`. Probe: adding value `11` replaced
  function `11` and left `name_index["alpha"] == [11, 32]` pointing at a value
  named `vcoll`. The guard is kind-scoped so AC-0003 holds for every other
  kind. Traces to: AC-0002, AC-0003.
- **`rank` skips nodes whose kind is `value`.** Base `rank` counts every node
  whose `parent_file` equals the ranked id. Probe: three values owned by file
  `10` raised its rank from 1 to 4 and swapped files `10` and `20` in default
  search. Rests on: the owner rejecting a rank delta (spec `## Assumptions`).
  Traces to: AC-0005, AC-0006.
- **Values stay out of `resolve_call` and `dependencies`.** `resolve_call`
  already keeps only `function` and `method` kinds; probe: `resolve_call("alpha")`
  returned `[11]` with a value also named `alpha`. Traces to: AC-0004, AC-0010.

Owned by: T2, T3.

### Data & schema

`Node` keeps its four fields and their order: `node_id`, `name`, `kind`,
`parent_file=None`. A value node is a `Node` with `kind="value"` and a
non-`None` `parent_file`; no new field is added. `Resolution` in
`shared-graph-public.rs` is not changed. Traces to: AC-0001, AC-0012, AC-0013.

Owned by: T2, T5.

### Interfaces & contracts — consumer map

This map is working material: deleting or rebuilding it changes no criterion.

| Class | Consumer evidence | Criterion or gap |
| --- | --- | --- |
| Direct readers and writers | `shared-graph-model.py:19-25` (`add_node`, `remove_node`) | AC-0001, AC-0002, AC-0003 |
| Selection and resolution | `shared-graph-consumers.py:4-6` (`resolve_call`, kind allowlist at line 6) | AC-0004 |
| Default search or presentation | `shared-graph-consumers.py:9-15` (`search`, value filter at lines 11-12) | AC-0005, AC-0007 |
| Ranking and traversal | `shared-graph-consumers.py:18-19` (`rank`, counts by `parent_file`, no kind filter) | AC-0006 |
| Full and alternate construction | `shared-graph-builders.py:4-8` (`build_full`), `:11-15` (`apply_incremental`) | AC-0008, AC-0009 |
| Invalidation and update | `shared-graph-builders.py:18-19` (`invalidated_files`) | AC-0010 |
| Lifecycle and cleanup | `shared-graph-builders.py:22-24` (`remove_file_nodes`), `shared-graph-lifecycle.py:4-12` (`attach_to_file`, `replace_file`) | AC-0011 |
| Serialization | Unreachable: `grep -rniE 'json\|pickle\|serial\|dump\|to_dict\|asdict\|repr' evals/files` found no match (exit 1) | none |
| Supported public compatibility | `shared-graph-public.rs:1-13` (`Resolution` literal at line 7, exhaustive destructure at line 11); `shared-graph-model.py:7-11` (`Node` dataclass) | AC-0012, AC-0013 |

The probes cited above were one throwaway in-memory script run against the
current files; it was not committed.

Owned by: T1, T4, T5.

## Tasks

### T1: Base copy frozen and shared fixture loads on both sides

**Depends on:** none

**Touches:** `tests/base/*`, `tests/fixture_graph.py`

**Tests:**
- A loader test loads all four Python files from both `tests/base/` and
  `evals/files/` by path and finds each function named in the consumer map.
  Mode: goal-based.
- A snapshot test records the SHA-256 of each file in `tests/base/` and fails
  if any changes. Mode: goal-based.
- The fixture builds the graph AC-0003 to AC-0011 use: two files, each owning
  a `function` and a `method`, value nodes owned by one file with one value
  named like an existing function, a previous and a final content for one file,
  and a `dependencies` map that names the file owning values. It also yields
  the value-free variant. Mode: goal-based.

**Approach:**
- Copy before T2 edits any file; a copy taken later would hold changed code.
  The test directory name is a proposal; the owner may pick another
  (spec `## Assumptions`, Process item).

**Done when:** `python3 -m unittest discover -s tests` passes the loader,
snapshot, and fixture tests.

### T2: Value nodes are file-owned and refuse id collisions

**Depends on:** T1

**Touches:** `evals/files/shared-graph-model.py`, `evals/files/shared-graph-lifecycle.py`, `tests/test_values.py`

**Tests:**
- AC-0001: create a value for file `F` through the lifecycle path and read it
  back from `nodes` and `name_index`. Mode: TDD.
- AC-0002: add a value with a taken id; assert `ValueError` and deep-equal
  `nodes` and `name_index` against a copy taken before the call; then add one
  with a fresh id. Mode: TDD.
- AC-0003: replay the fixture's add/remove sequence on base and changed
  graphs, values added on the changed side only, and compare the stated
  projections including `name_index` list order and empty lists. Mode: TDD,
  base oracle.
- AC-0013: construct each `Node` form on both sides and compare the four
  fields; check `Graph()` is empty. Mode: goal-based.

**Done when:** the T2 tests pass and the T1 snapshot test still passes.

### T3: Existing readers return base results with values present

**Depends on:** T2

**Touches:** `evals/files/shared-graph-consumers.py`, `tests/test_readers.py`

**Tests:**
- AC-0004: `resolve_call` for every fixture name, base on the value-free graph
  versus changed on the full fixture. Mode: TDD, base oracle.
- AC-0005: default `search` for each listed query, same comparison, ids and
  order. Mode: TDD, base oracle.
- AC-0006: `rank` for every non-value id, including the file that owns the
  values; this is the test that is red before the `rank` change. Mode: TDD,
  base oracle.
- AC-0007: `search(..., include_values=True)` for each query, checked as the
  default set plus matching values with non-value relative order kept. Mode:
  TDD, base oracle.

**Done when:** the T3 tests pass and the T1 snapshot test still passes.

### T4: Build paths agree and file replacement cleans up values

**Depends on:** T2

**Touches:** `tests/test_construction.py`

**Tests:**
- AC-0008: build the final file set with `build_full` and with
  `apply_incremental` from the previous contents; compare `nodes` and the
  per-name sorted, empty-dropped `name_index`. Mode: integration.
- AC-0009: drop value nodes from both graphs and compare each with the base
  copy's builds of the value-free inputs, same comparison. Mode: integration,
  base oracle.
- AC-0010: `invalidated_files` for every file id in the fixture map, base
  versus changed. Mode: integration, base oracle.
- AC-0011: run `replace_file` (passing `remove_file_nodes`) and, separately,
  `apply_incremental` on the file owning values; check the value set and that
  every `name_index` id is a key of `nodes`. Mode: integration.

**Done when:** the T4 tests pass and the T1 snapshot test still passes.

### T5: Public Rust surface still compiles for downstream callers

**Depends on:** T1

**Touches:** `tests/rust/compat.rs`

**Tests:**
- AC-0012: a snippet that includes `evals/files/shared-graph-public.rs`,
  builds the struct literal, destructures exhaustively, and asserts `consume`
  on both inputs, compiled and run with `rustc --test`. Mode: goal-based.
  Kill condition: no Rust toolchain can be named by the owner; then AC-0012
  stays open and the spec cannot reach `Shipped`.

**Done when:** `rustc --test tests/rust/compat.rs` builds and its test passes
on the toolchain the owner names.

## Rollout

Pure library and test change in a fixture repository: no flag, no
infrastructure, no external system, no deployment order. Rollback is reverting
the edits to `evals/files/`.

## Risks

- If the owner chooses a rank delta over the `rank` change, T3 and AC-0005 and
  AC-0006 change before approval.
- If value production is a separate post-build pass, T4's fixture and the first
  design decision change.
- T5 cannot run in this environment until a Rust toolchain is named.

## Changelog
```

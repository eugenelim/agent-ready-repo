I wrote a Draft spec and a Drafting plan for synthetic value nodes in `docs/specs/synthetic-value-nodes/`. Together they add 12 behavior-keeping criteria (AC-0004 to AC-0013, plus the two refusals AC-0002 and AC-0003) on top of the proposed test, which only proves a value can be created (AC-0001). The contract item lint passed with 0 findings. The spec is not ready for approval: the required shaping review and adversarial review were not run, because subagents were not allowed here.

## What the files showed must be preserved

I followed `new-spec` and its `shared-substrate-preservation.md` reference. That reference applies because a new node kind is visible to every generic reader of the graph. I ran throwaway probes against the fixture files from stdin, with no files written. They found three things that would break:

- **Ranking:** `search` already hides `kind == "value"`. But `rank` counts every node in a file, values included. Values in a file whose id is also a node id raise that node's rank, so default search changes order even though no value is shown. A probe on the planned fixture moved the order from `[21, 10, 11, 2, 1]` to `[21, 10, 11, 1, 2]`. This is the only production fix besides the new create operation.
- **Id collision:** `add_node` silently overwrites an existing node. A value created with function 10's id leaves `name_index["run"]` pointing at the value, so `resolve_call("run")` loses the function. The new create operation therefore refuses an id that is already used (AC-0002).
- **Orphans:** a value with `parent_file=None` survives every rebuild, because cleanup only removes nodes by containing file. Creation therefore requires a containing file (AC-0003).

These existing behaviors also each get a criterion that compares against base-revision results:

- **Resolution:** call resolution results (AC-0005).
- **Search:** default search stays the same (AC-0006), and values appear only when `include_values=True` is passed (AC-0007).
- **Rank:** rank values for non-value nodes (AC-0008).
- **Builds:** full and incremental builds agree (AC-0009). Empty `name_index` lists are dropped before comparing, because the base code already leaves them behind.
- **Cleanup:** replacing a file removes its own values (AC-0010) and leaves other files untouched (AC-0011). Both are checked through `apply_incremental` and `replace_file`.
- **Invalidation:** `invalidated_files` results stay the same (AC-0012).
- **Public Rust surface:** an outside consumer can still build and fully unpack `Resolution` (AC-0013).

I searched for serialization code and found none, so that category has no criterion. The search command is recorded in the plan's consumer map.

## Open questions I would have asked

- **Rust toolchain:** there is no Cargo manifest and no `rustc` on this machine. Without one, AC-0013 cannot be checked.
- **Test setup:** the repo declares no test runner or test folder. The plan assumes standard-library `unittest` under `evals/tests/`.
- **Producer of value nodes:** the code that puts value nodes into parsed files is not in the repo. The criteria that judge the builders cover it, so it is a bounded assumption, not a gap.
- **Dependency map source:** the code that builds the `dependencies` map is also not in the repo. AC-0012 covers it the same way.
- **Product:** may a value ever be a call target or show in default search? The spec says never.
- **Process:** nothing names an approver. Creating a new top-level `docs/specs/` folder also needs the owner's sign-off.

## Review status

- **Shaping review:** `BLOCKED: spec shaping review — independent route unavailable`. The spec stays at `Draft`.
- **Adversarial review:** not run, so no review of the spec has happened yet.
- **Contract item lint:** exit 0, 0 findings. Its reworded-criterion check did not run, because there is no git history.

## Files

### docs/specs/synthetic-value-nodes/spec.md

````markdown
# Spec: synthetic value nodes

- **Status:** Draft
- **Owner:** unassigned (repository owner to name)
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
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

Code that builds the repository graph can add a synthetic value node, a graph
node of kind `"value"` that no source declaration produced, owned by the file
it belongs to. Every existing reader of the graph — call resolution, default
search, ranking, full and incremental builds, invalidation, file replacement,
and the public `Resolution` surface — returns the same results it returned
before values existed, and values show up only where a caller asks for them.

## What Changes

- A creation operation for synthetic value nodes, which refuses an occupied
  node id and a value with no containing file — `evals/files/shared-graph-model.py`.
- `rank` stops counting value nodes, so values cannot reorder default search —
  `evals/files/shared-graph-consumers.py`.
- The model's module docstring describes value nodes and their containment
  instead of the pre-value state — `evals/files/shared-graph-model.py`.
- A preservation suite pins base-revision behavior of every existing graph
  reader and checks it again with values present — test location named in the
  plan.
- No change to `evals/files/shared-graph-builders.py`,
  `evals/files/shared-graph-lifecycle.py`, or `evals/files/shared-graph-public.rs`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current architecture | Applicable: the model's module docstring is the only prose describing the graph, and it states the pre-value state | `evals/files/shared-graph-model.py` module docstring | implementer (plan T2) | Docstring names value nodes, kind `"value"`, and the containing-file requirement | Docstring no longer says synthetic values are absent |
| Interface compatibility | Applicable as evidence only: the public Rust surface does not change | none — no file to update | implementer (plan T5) | AC-0013 result | AC-0013 checked |
| User promise, product truth, decision rationale, operations, maintainer procedure, release history, reusable learning | Not applicable: the repository has no docs, changelog, guides, or decision records (only `evals/files/` exists) | none | — | — | — |

## Agent Rules

### Always do

- Record every base-revision expectation table from the unmodified graph
  modules before editing any production file.
- Represent a synthetic value as a node whose `kind` is exactly `"value"`, the
  literal the existing `search` filter already excludes.
- Run each preservation oracle against its named mutation and keep the run as
  evidence; an oracle that passes its mutant is not evidence.

### Ask first

- Any edit to `evals/files/shared-graph-public.rs`, or to the signatures of
  `resolve_call`, `search`, `invalidated_files`, `remove_file_nodes`, or
  `replace_file`.
- Changing what `Graph.add_node` or `Graph.remove_node` do for existing node
  kinds.
- Choosing a test runner, a test directory, or a Rust crate manifest that the
  repository does not already have.

### Never do

- Never regenerate or edit a base-revision expectation table to match new
  output.
- Never add a field to `Node`, `Graph`, or `Resolution`.
- Never add a third-party dependency or a new production module; the change
  stays inside the existing graph files plus the test suite.

## Testing Strategy

- **TDD (AC-0001, AC-0002, AC-0003)** — creation and its two refusals are a
  compressible invariant over one writer, checked at the graph's public
  methods.
- **Behavior pin (AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013)** —
  each is an existing behavior, so its expected side is recorded from the base
  revision before any production edit, and the check then runs with synthetic
  values present. AC-0009 is exercised by an integration test across the two
  builders; AC-0013 by compiling and running a consumer outside the crate.

**Base revision** means the graph modules in `evals/files/` as they stand
before this delivery's first production edit. **Base tables** are the outputs
of those modules over the oracle fixture with every value node removed,
written into the test as literals.

**The oracle fixture** is a set of parsed files whose every declaration is
contained in its own file. It must include all of these, so each criterion can
fail:

- a value whose name equals a function's name, and a value whose name no
  non-value node has;
- a file whose id equals a node's id, holding enough values that base-revision
  `rank` over the graph with values present changes the order of default
  `search`;
- a changed file whose old version holds a value its new version drops, and an
  unchanged file that holds a value.

## Acceptance Criteria

- [ ] **AC-0001.** When a synthetic value is created with an unused node id, a
  name, and a containing file id, `graph.nodes[id]` is a node with that id,
  that name, kind `"value"`, and that `parent_file`, and `graph.name_index[name]`
  contains that id.
- [ ] **AC-0002.** If a synthetic value is created with a node id already in
  `graph.nodes`, creation raises `ValueError` and `graph.nodes` and
  `graph.name_index` equal their state before the call.
- [ ] **AC-0003.** If a synthetic value is created with `parent_file` of
  `None`, creation raises `ValueError` and `graph.nodes` and `graph.name_index`
  equal their state before the call.
- [ ] **AC-0004.** For the oracle fixture, both the full build and the
  incremental build with values present, after removing value nodes from
  `nodes` and value ids from `name_index`, equal the base table for the same
  build. Allowed delta: none.
- [ ] **AC-0005.** For every name in the oracle fixture, `resolve_call` on the
  graph with values present returns the same nodes, in the same order, as the
  base table; a name only a value has returns an empty list. Allowed delta:
  none.
- [ ] **AC-0006.** For each fixture query, including no query, `search` with
  its default `include_values=False` on the graph with values present returns
  the same nodes, in the same order, as the base table. Allowed delta: none.
- [ ] **AC-0007.** For each fixture query, `search(..., include_values=True)` on
  the graph with values present returns every value node matching the query
  exactly once, and its non-value nodes, taken in result order, equal the base
  table for that query. Allowed delta: values appear only when explicitly
  requested.
- [ ] **AC-0008.** For every non-value node id in the oracle fixture, `rank` on
  the graph with values present equals the base table. Allowed delta: none.
- [ ] **AC-0009.** Applying the incremental build to the full build of the
  fixture's initial files yields the same graph as the full build of its final
  files, where "the same" means equal sets of `(node_id, name, kind,
  parent_file)` and equal `name_index` after sorting each id list and dropping
  names whose list is empty. The comparison also reports two graphs that differ
  in one value node as different.
- [ ] **AC-0010.** After a file is replaced through `apply_incremental` or
  through `replace_file`, no node whose `parent_file` is that file remains in
  `graph.nodes` or `graph.name_index` unless the new parsed file declares it.
- [ ] **AC-0011.** After a file is replaced through `apply_incremental` or
  through `replace_file`, every node contained in any other file, values
  included, keeps its id, name, kind, and `parent_file`.
- [ ] **AC-0012.** For the fixture's dependency map and every file id in the
  fixture, `invalidated_files` returns the base-table set while values are
  present in the graph. Allowed delta: none.
- [ ] **AC-0013.** A Rust consumer outside the crate that builds a
  `Resolution` with a struct literal, destructures it with the exhaustive
  pattern `let Resolution { target, confidence } = r;`, and prints
  `consume(unresolved())`, `consume` of `{ target: Some(7), confidence: 1 }`, and
  `consume` of `{ target: Some(7), confidence: 0 }` compiles and prints
  `false true false`, which is what the base-revision `consume` and
  `unresolved` return for those inputs.

A sustained review finding against any preservation criterion (AC-0004 to
AC-0013) contradicts that criterion and is resolved by amending it, not by
weakening its oracle.

## Assumptions

- Technical: the producer that puts synthetic values into parsed files for real
  builds is out of view — bounded by AC-0004, AC-0009, AC-0010, and AC-0011,
  which judge the readable builders on base-revision inputs; not a gap.
- Technical: the producer of the `dependencies` map that `invalidated_files`
  reads is out of view — bounded by AC-0012; not a gap.
- Technical: the repository declares no Rust toolchain or crate manifest, and
  `rustc` is not installed where this spec was drafted — until one is named,
  AC-0013 cannot produce evidence and stays unchecked (settled by: repository
  owner).
- Technical: the repository declares no test runner or test directory — the
  plan assumes standard-library `unittest` under `evals/tests/` (settled by:
  repository owner).
- Product: whether a synthetic value may ever be a call-resolution target or
  appear in default search — this spec says never (AC-0005, AC-0006); a "yes"
  changes both criteria (settled by: product owner).
- Process: the repository has no contribution guidance naming who approves a
  spec or where specs live — this spec creates `docs/specs/` (settled by:
  repository owner).
````

### docs/specs/synthetic-value-nodes/plan.md

````markdown
# Plan: synthetic value nodes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** no architecture or convention source exists (no
  `AGENTS.md`, docs, manifest, or runner; repository-grounding discovery over
  `evals/files` found none). The analogous production path is
  `attach_to_file` in `evals/files/shared-graph-lifecycle.py`, which sets
  containment before `Graph.add_node`. No tests exist; the construction path is
  the builders in `evals/files/shared-graph-builders.py`. Named uncertainty:
  test runner, test location, and Rust toolchain are undeclared (spec
  Assumptions).

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
> before approval: approval hashes the whole plan.

## Approach

Pin first, then change. T1 records base tables from the unmodified modules, so
the expected side of every preservation oracle comes from the base revision and
never from the code under test. T2 adds the creation operation. T3 makes `rank`
ignore value nodes, the one existing reader the pre-review probe showed values
break. T4 runs the remaining preservation pins with values present and proves
each oracle against a mutation. T5 guards the Rust surface independently. The
riskiest part is ranking: values contained in a file whose id is also a node id
silently reorder default search even though `search` already hides values.

## Constraints

- No ADR or RFC governs this code.
- Python syntax in the modules (`int | None`, `set[int]`) needs Python 3.10 or
  later; standard library only.
- The module filenames contain hyphens, so tests load them by path with
  `importlib.util.spec_from_file_location`, not by `import`.
- The modules do not import each other: `replace_file` receives
  `remove_file_nodes` as an argument, and tests pass the builders' function in.

## Construction tests

**Integration tests:** the T4 equivalence check drives `build_full` and
`apply_incremental` together over the oracle fixture.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Current architecture / `shared-graph-model.py` docstring | T2 | Docstring diff | Docstring names kind `"value"` and the containing-file requirement |
| Interface compatibility / none | T5 | AC-0013 consumer build-and-run output | AC-0013 checked, or left open under the toolchain assumption |
| Delivery record / `docs/specs/synthetic-value-nodes/` | all | This spec and plan | Retention class repository-durable; approver and fingerprint recorded at approval |

## Design (LLD)

### Data & schema

A synthetic value is a plain `Node` with `kind="value"` and a non-`None`
`parent_file`; no field is added. Choice rests on: the existing `search` filter
keys on the literal `"value"`, so any other kind would leak into default
search. Containment is required because `remove_file_nodes` and `replace_file`
remove nodes only by `parent_file`; the probe showed a value with
`parent_file=None` survives an incremental rebuild forever.

Owned by: T2

### Interfaces & contracts

New writer: `Graph.add_synthetic_value(node_id: int, name: str, parent_file: int) -> Node`
in `evals/files/shared-graph-model.py`. It raises `ValueError` before any
mutation when `node_id in self.nodes` or `parent_file is None`, then delegates
to `add_node`. The refusal exists because `add_node` overwrites silently: the
probe overwrote declaration node 10 with a value, `name_index["run"]` kept
pointing at id 10, and `resolve_call("run")` then lost the function.
Values from a parsed file's `declarations` keep entering builds through
`add_node` unchanged; that producer is out of view (spec Assumptions).

The Rust `Resolution` surface is untouched. Its compatibility oracle is a
consumer crate compiled against `shared-graph-public.rs` built as a library
(`rustc --crate-type lib` plus `--extern`), so only `pub` items are visible.

Owned by: T2, T5

### Behavior & rules

`rank(graph, node_id)` counts nodes with `parent_file == node_id` and
`kind != "value"`. Probe evidence: with two values contained in file 2 and node
2 present, base `rank(2)` rose from 1 to 3 and default `search` order flipped
`mod_b`/`mod_a`. `resolve_call`, `search`, `invalidated_files`,
`remove_file_nodes`, `apply_incremental`, and `replace_file` need no change;
T4 proves it.

Equivalence normalisation (AC-0009) drops empty `name_index` lists because
`remove_node` leaves them behind at base too; the probe showed raw
`name_index` differs between full and incremental builds only by such a
`"v1": []` entry.

Owned by: T3, T4

### Consumer map

This map is working material; deleting or rebuilding it changes no criterion.

| Class | Consumer evidence | Criterion or gap |
| --- | --- | --- |
| Direct readers and writers | `shared-graph-model.py:19-25` `add_node`, `remove_node`, `name_index` | AC-0001, AC-0002, AC-0003, AC-0004 |
| Selection and resolution | `shared-graph-consumers.py:4-6` `resolve_call` | AC-0005 |
| Default search or presentation | `shared-graph-consumers.py:9-15` `search` | AC-0006, AC-0007 |
| Ranking and traversal | `shared-graph-consumers.py:18-19` `rank`, read by the sort at `:15` | AC-0008, AC-0006 |
| Full and alternate construction | `shared-graph-builders.py:4-15` `build_full`, `apply_incremental` | AC-0004, AC-0009 |
| Invalidation and update | `shared-graph-builders.py:18-19` `invalidated_files` | AC-0012 |
| Lifecycle and cleanup | `shared-graph-builders.py:22-24` `remove_file_nodes`; `shared-graph-lifecycle.py:4-12` `attach_to_file`, `replace_file` | AC-0003, AC-0010, AC-0011 |
| Serialization | Unreachable: `grep -nE "json\|pickle\|serial\|dump\|asdict\|repr\|to_dict\|import" evals/files/*` found only the `dataclasses` import at `shared-graph-model.py:3` | none |
| Supported public compatibility | `shared-graph-public.rs:1-13` `Resolution`, `unresolved`, `consume` | AC-0013 |

Owned by: T1

### Oracle fixture

Every declaration is contained in its own file. File 1: `mod_a` (id 1,
module), `run` (10, function), `stop` (11, function), value `run` (91). File 2
initial: `mod_b` (2, module), `run` (20, method), value `v_old` (90). File 2
final: `mod_b` (2), `go` (21, method), value `go` (92), value `limit` (93).
Dependency map: `{1: {2}, 3: {1, 2}, 2: set()}`. Queries: none, `"run"`,
`"go"`, `"mod"`, `"limit"`. Names for `resolve_call`: every name above.

Owned by: T1

## Tasks

### T1: Base tables recorded and green on the unmodified modules

**Depends on:** none

**Touches:** evals/tests/test_shared_graph_preservation.py

**Tests:**
- Behavior pin: literal base tables for AC-0004, AC-0005, AC-0006, AC-0007,
  AC-0008, AC-0009, AC-0012, produced by the base modules over the oracle
  fixture with values removed, pass on the base revision.
- Fixture sanity: base `rank` and base default `search` over the fixture *with*
  values differ from their tables, proving AC-0006 and AC-0008 can red.

**Done when:** `python3 -m unittest discover -s evals/tests` is green with no
production file edited.

### T2: Synthetic values can be created and bad creations are refused

**Depends on:** T1

**Touches:** evals/files/shared-graph-model.py, evals/tests/test_synthetic_value.py

**Tests:**
- TDD at `Graph.add_synthetic_value`: AC-0001 red first, then green.
- TDD: AC-0002 and AC-0003, each red under the mutation "delegate to
  `add_node` without the check", each comparing `nodes` and `name_index`
  snapshots taken before the call.

**Done when:** `python3 -m unittest discover -s evals/tests` is green and the
T1 tables are unchanged.

### T3: Values do not change rank or default search

**Depends on:** T1, T2

**Touches:** evals/files/shared-graph-consumers.py

**Tests:**
- Behavior pin: AC-0006, AC-0007, AC-0008 against the T1 tables with values
  present; red before the `rank` change (fixture sanity in T1), green after.
- Mutations: reverting the `rank` filter reds AC-0006 and AC-0008; removing the
  `include_values` filter reds AC-0006; filtering values out unconditionally
  reds AC-0007.

**Done when:** `python3 -m unittest discover -s evals/tests` is green and each
named mutant run is recorded red in the verification ledger.

### T4: Resolution, builds, lifecycle, and invalidation preserved with values

**Depends on:** T1

**Tests:**
- Conservation: AC-0004 and AC-0005 against T1 tables; mutants "drop the
  `name_index` append in `add_node`" and "add `"value"` to `resolve_call`'s
  kinds" each red.
- Equivalence (integration): AC-0009; mutant "skip `remove_file_nodes` in
  `apply_incremental`" reds it, and the comparator distinguishes two graphs
  differing by node 93.
- Lifecycle: AC-0010 and AC-0011 over both `apply_incremental` and
  `replace_file`; mutants "skip cleanup in `replace_file`" reds AC-0010 and
  "remove every value node regardless of file" reds AC-0011.
- Conservation: AC-0012; mutant "include `changed_file_id` in the result" reds
  it.

**Done when:** `python3 -m unittest discover -s evals/tests` is green and each
named mutant run is recorded red in the verification ledger.

### T5: Public `Resolution` surface still constructs and destructures

**Depends on:** none

**Tests:**
- Compatibility: AC-0013 consumer built against `shared-graph-public.rs` as an
  external library; mutant "rename field `confidence`" fails to compile.

**Done when:** the consumer compiles and prints `false true false`; if no Rust
toolchain is declared, the task stays blocked on the spec's toolchain
assumption and AC-0013 stays unchecked.

## Rollout

Pure logic change inside the repository; no flag, infrastructure, external
system, or deployment order. Rollback is reverting the commit.

## Risks

- The real producer of value nodes may assign ids that collide with
  declaration ids through `add_node`, which T2's refusal does not cover; the
  preservation pins only judge the fixture.
- Without a declared Rust toolchain, AC-0013 cannot close and the spec cannot
  ship.

## Changelog
````

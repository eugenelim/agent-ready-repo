## Summary

I wrote a Draft spec and a Drafting plan for synthetic value nodes in `/tmp/gpar-spike/work/docs/specs/synthetic-value-nodes/`. I followed `new-spec` and its `references/shared-substrate-preservation.md`. That reference applies because a new `value` node joins a graph that generic readers see without asking for it.

**What must be preserved.** I traced every reader in the five fixture files. Then I ran a throwaway in-memory probe on the unchanged fixture; nothing was written. The probe found three real breaks that a "can create a value" test would miss:
- **Ranking.** `rank` counts every node, values included. Two values owned by file 1 moved `rank(1)` from 2 to 4. That also changed the default `search` order from `[4,3,1,2]` to `[4,3,2,1]`, even though `search` hides values from its results.
- **Taken ids.** `add_node` with an id already in use silently replaces the existing node. The old name's index entry then points at the new node.
- **Unowned values.** A value with `parent_file=None` survives `remove_file_nodes`, so it would leak.

**Criteria.** The spec has 14 acceptance criteria:
- 3 cover the feature: create a value, refuse a taken id, refuse a value with no owning file.
- 1 covers the asked-for delta: `include_values` returns exactly the values whose names match the query.
- 10 are preservation criteria. They cover resolution, default search, search with values requested, rank, full build, incremental build, file cleanup, index integrity, invalidation, and the public Rust `Resolution` type.

Each preservation criterion states the old behavior, its allowed change, a test oracle, and what contradicts it. The oracle is a "golden" (expected output recorded by running the unchanged fixture on fixed inputs), captured in task T1 before any code edit.

**Consumer map.** It is in the plan, one row per behavior class. Serialization is marked unreachable, citing the repository search that found no serializer.

**Checks run.**
- Repository-grounding discovery: no governing files, runners, or git history found.
- `lint-contract-item-alignment.py`: 0 findings. The reworded-criterion rule could not run because there is no git history.

**Blocked and skipped steps.**
- Shaping review is `BLOCKED: spec shaping review — independent route unavailable`, because subagents were not allowed. The spec stays at `Draft`.
- adversarial-reviewer: review skipped, because subagents were not allowed.
- The plan's step-5a probe was run; its result is cited in the plan's Design decisions.

**Questions I would have asked a human (answered with my best judgment instead):**
1. Should a synthetic value be removed with its owning file and re-created by its creator, or should rebuilds re-create it? I assumed removed. This drives AC-0011 and must be settled before approval.
2. Should `Shape` be `data`? I chose `data`.
3. Highest-stakes confirmation: every synthetic value must have an owning file (AC-0003).
4. Who owns and approves this spec? The repository has no `AGENTS.md` or contribution guide.
5. Where should the Rust compile check (AC-0014) run? There is no Cargo manifest, and no `rustc` was found locally.

## Files written

### docs/specs/synthetic-value-nodes/spec.md

````markdown
# Spec: Synthetic value nodes

- **Status:** Draft
- **Owner:** unassigned
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
> `Assumptions` are working material: an author corrects them in place as the
> work teaches, without an amendment and without a review round.

## Outcome

Code that works with the repository graph fixture under `evals/files/` can add a
synthetic value node: a node of kind `value` that no parsed file declared but
that one file owns. Every existing reader of the graph returns what it returned
before values existed, except where this spec names the allowed change.

## What Changes

- A creation operation for synthetic value nodes — the graph model in
  `evals/files/shared-graph-model.py`.
- Refusal of a synthetic value whose node id is taken or that has no owning
  file — the same creation operation.
- `rank` stops counting value nodes — `evals/files/shared-graph-consumers.py`.
- Preservation tests whose expected values come from the graph fixture as it
  stands before this change — a test location the plan resolves.
- A compile-level compatibility check for the public `Resolution` type —
  against `evals/files/shared-graph-public.rs`, which itself does not change.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable: `Resolution` in `evals/files/shared-graph-public.rs` is public, and AC-0014 keeps it compatible | The compatibility check the plan's T4 adds | Spec owner | The check compiles and passes against the unchanged `Resolution` | The check exists in the repository and passes |
| Reusable learning | Applicable: the preservation goldens are the base-revision record every later graph change can reuse | The golden file the plan's T1 adds | Spec owner | Goldens captured before any production edit | Golden file is committed unchanged from its T1 capture |

No other role applies. The repository has no user documentation, architecture
surface, decision record, operations guide, or changelog for this fixture, so
there is no existing surface to refresh.

## Agent Rules

### Always do

- Take the expected side of every preservation test from goldens captured by
  running the unmodified fixture modules, before any production edit.
- Use the literal kind `value` for synthetic values, because `search` already
  filters on that literal.
- Give every synthetic value an owning file, so the existing file cleanup
  removes it.

### Ask first

- Changing the signature or the non-value behavior of `resolve_call`, `search`,
  `rank`, `build_full`, `apply_incremental`, `invalidated_files`,
  `remove_file_nodes`, `attach_to_file`, or `replace_file`.
- Making either build path create synthetic values.
- Adding a test runner, a package manifest, or a new top-level directory.

### Never do

- Never add a third-party dependency.
- Never add a new production module; the creation operation lives in the
  existing graph model file.
- Never change `evals/files/shared-graph-public.rs`.
- Never change how `add_node` treats a declaration whose node id already
  exists.
- Never edit a golden value to match the implementation under test.

## Testing Strategy

Every preservation criterion compares against a golden recorded from the
unmodified fixture on frozen inputs, so the expected side never comes from the
code under test.

- **TDD (AC-0001, AC-0002, AC-0003, AC-0007, AC-0008):** creation, refusal,
  and requested values are a compressible invariant over graph state. The rank
  rule is TDD because a probe of the unmodified code shows it goes red as soon
  as an owned value exists.
- **Goal-based golden comparison (AC-0004, AC-0005, AC-0006, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013):**
  each runs an existing reader on the frozen inputs with synthetic values
  present and compares to the golden. It is exercised as an integration test
  across the model, builders, consumers, and lifecycle files together.
- **Goal-based compile check (AC-0014):** downstream-style Rust code that builds
  and destructures `Resolution` compiles and its assertions pass.

## Acceptance Criteria

Each preservation criterion names the behavior it keeps, its allowed delta, its
oracle, and what contradicts it.

- [ ] **AC-0001.** When a synthetic value is created with an unused node id, a
  name, and an owning file id, the graph's `nodes` and `name_index` equal their
  prior contents plus exactly one node of kind `value` with that id, name, and
  `parent_file`, listed under its name in `name_index`.
- [ ] **AC-0002.** If a synthetic value is created with a node id already in
  `nodes`, then creation raises an error and `nodes` and `name_index` equal
  their prior contents.
- [ ] **AC-0003.** If a synthetic value is created with no owning file, then
  creation raises an error and `nodes` and `name_index` equal their prior
  contents.
- [ ] **AC-0004.** Keeps: `resolve_call` returns only `function` and `method`
  nodes for a name. Delta: none, including for a name a synthetic value
  shares. Oracle: for every name in the frozen inputs, the result with values
  present equals the golden. Contradicted by: any sustained finding that a
  value node or a changed node list reaches a `resolve_call` result.
- [ ] **AC-0005.** Keeps: default `search`, with and without a query, returns
  no value node and orders results by rank, then name. Delta: none. Oracle: the
  node-id sequence with values present equals the golden sequence for each
  frozen query. Contradicted by: any sustained finding that default search
  membership or order moves.
- [ ] **AC-0006.** Keeps: `search(include_values=True)` orders non-value nodes
  by rank, then name. Delta: value nodes may appear among them. Oracle: with
  values present, the result with value nodes removed equals the golden default
  node-id sequence for each frozen query. Contradicted by: any sustained
  finding that non-value order or membership moves when values are requested.
- [ ] **AC-0007.** When `search` is called with `include_values=True`, the
  value nodes in its result are exactly the synthetic values whose names
  contain the query, compared case-insensitively, or every synthetic value when
  there is no query.
- [ ] **AC-0008.** Keeps: `rank` of a node id counts the non-value nodes whose
  `parent_file` equals it. Delta: none for any non-value node id. Oracle: with
  values present, `rank` for every node id in the frozen inputs equals the
  golden. Contradicted by: any sustained finding that a value node changes a
  rank.
- [ ] **AC-0009.** Keeps: `build_full` adds exactly the parsed declarations.
  Delta: none. Oracle: `nodes` and `name_index` after `build_full` on the
  frozen inputs equal the golden. Contradicted by: any sustained finding that a
  full build creates or drops a node.
- [ ] **AC-0010.** Keeps: `apply_incremental` replaces a changed file's
  declarations. Delta: none for non-value nodes. Oracle: after synthetic values
  are created on two files and one file is updated incrementally, the
  non-value nodes and the `name_index` entries for non-value ids equal the
  golden incremental result. Contradicted by: any sustained finding that an
  incremental update changes a declaration node or its index entry.
- [ ] **AC-0011.** Keeps: removing a file's contents removes exactly the nodes
  it owns. Delta: the owned nodes now include synthetic values. Oracle: after
  `remove_file_nodes`, `replace_file`, or `apply_incremental` for file F, the
  remaining value nodes are exactly the synthetic values owned by files other
  than F. Contradicted by: any sustained finding that a value outlives its
  owning file's removal or that another file's value is lost.
- [ ] **AC-0012.** Keeps: `name_index` names only nodes that exist. Delta:
  none. Oracle: after creating synthetic values and then running any operation
  AC-0011 names, every id in every `name_index` list is a key of `nodes`, as it
  is in the golden. Contradicted by: any sustained finding that an index entry
  outlives its node.
- [ ] **AC-0013.** Keeps: `invalidated_files` returns the callers whose
  dependency targets include the changed file. Delta: none. Oracle: for each
  file id in the frozen dependency map, the result equals the golden.
  Contradicted by: any sustained finding that a synthetic value adds,
  removes, or alters an invalidated file.
- [ ] **AC-0014.** Keeps: downstream code can build `Resolution` with a struct
  literal of exactly `target` and `confidence`, destructure it exhaustively,
  and call `unresolved()` and `consume()`. Delta: none. Oracle: such code
  compiles and asserts that `unresolved()` is `target: None, confidence: 0` and
  that `consume` is true only for `target: Some(_)` with `confidence > 0`.
  Contradicted by: any sustained finding that the `Resolution` construction or
  destructuring surface moves.

## Follow-ons

none

## Assumptions

- Product: Should a synthetic value survive or be re-created when its owning
  file is rebuilt incrementally? This draft takes "no — it is removed with the
  file, and its creator re-creates it" — a different answer changes AC-0011 and
  the Ask-first rule on build paths (settled by: feature owner, before
  approval).
- Product: Which code creates synthetic values, and from what input, is not in
  the fixture. AC-0001 to AC-0012 still bound the graph's behavior for any
  creator (settled by: feature owner).
- Technical: The producer of the dependency map that `invalidated_files` reads
  is not in the fixture. AC-0013 still bounds the consumer on base inputs
  (settled by: feature owner).
- Technical: The code that turns a Python resolution into a Rust `Resolution`
  is not in the fixture. AC-0014 still bounds the public surface (settled by:
  feature owner).
- Technical: The repository has no Cargo manifest, and no Rust toolchain was
  found where this draft was written. Where the AC-0014 check runs is open
  (settled by: repository owner).
- Process: The repository has no `AGENTS.md`, contribution guide, or prior
  spec, so who approves this spec and its Agent Rules is open (settled by:
  repository owner).
````

### docs/specs/synthetic-value-nodes/plan.md

````markdown
# Plan: Synthetic value nodes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** No architecture or convention source exists: the
  repository has no `AGENTS.md`, manifest, test runner, or VCS history. The
  anchors are the five fixture files under `evals/files/`, read whole. No
  analogous production implementation or existing test exists, which is a
  named gap for test placement (see T1).

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`. After approval, `spec.md`
> and `plan.md` are pinned in substance, and execution observations go to
> `docs/specs/synthetic-value-nodes/notes/verification-ledger.md`.

## Approach

First capture goldens by running the unmodified fixture modules on frozen
inputs, so every preservation oracle comes from the base revision. Then add the
creation operation with its two refusals. Then add the preservation tests with
values present; the rank test goes red, and the fix is a kind filter in `rank`.
The Rust compatibility check is independent and runs last. The riskiest part is
the rank interaction, because default `search` hides values from its results
but still orders by a rank that counts them.

## Constraints

- No ADR or RFC governs this fixture.
- Python 3.10 or later is required by the fixture's `int | None` annotations;
  the local interpreter is 3.15.
- The fixture modules have hyphenated file names, so tests load them with
  `importlib.util.spec_from_file_location`, not `import`, and run under
  `python3 -I`.
- Tests use only the standard library (`unittest`), per the spec's Never-do
  rule on dependencies.
- Approval record: repository-durable at `docs/specs/synthetic-value-nodes/`,
  readable by every reviewer and resuming session; the owner is the spec owner.

## Construction tests

**Integration tests:** the T3 suite loads the model, builders, consumers, and
lifecycle files together and runs every golden comparison against one graph.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility — the `Resolution` compatibility check | T4 | The check compiles and passes | The check is in the repository and passes on the unchanged `.rs` file |
| Reusable learning — the base-revision golden file | T1 | Goldens written before any production edit | The golden file is unchanged since T1 |

The consumer map and the design decisions below are delivery residue: the
tests and the `rank` filter carry them once T3 lands.

## Design (LLD)

### Consumer map

This map is working material. Deleting or rebuilding it changes no criterion.

| Class | Consumer evidence | Criterion or gap |
| --- | --- | --- |
| Direct readers and writers | `Graph.add_node` and `Graph.remove_node` in `shared-graph-model.py` write `nodes` and `name_index` | AC-0001, AC-0002, AC-0003, AC-0012 |
| Selection and resolution | `resolve_call` in `shared-graph-consumers.py` reads `name_index`, filters `kind in {"function", "method"}` | AC-0004 |
| Default search or presentation | `search` in `shared-graph-consumers.py` drops `kind == "value"` unless `include_values` | AC-0005, AC-0006, AC-0007 |
| Ranking and traversal | `rank` in `shared-graph-consumers.py` counts every node whose `parent_file` equals a node id, with no kind filter | AC-0008 |
| Full and alternate construction | `build_full` and `apply_incremental` in `shared-graph-builders.py` | AC-0009, AC-0010 |
| Invalidation and update | `invalidated_files` in `shared-graph-builders.py` reads only the dependency map; `apply_incremental` is the update path | AC-0013, AC-0010 |
| Lifecycle and cleanup | `remove_file_nodes` in `shared-graph-builders.py`; `attach_to_file` and `replace_file` in `shared-graph-lifecycle.py` select by `parent_file` | AC-0011, AC-0012 |
| Serialization | Unreachable: a case-insensitive search of the repository for `json`, `pickle`, `serial`, `dump`, `to_dict`, `asdict`, `serde`, and `repr` found no match | none |
| Supported public compatibility | `Resolution`, `unresolved`, and `consume` in `shared-graph-public.rs`; `consume` destructures `Resolution` exhaustively | AC-0014 |

Owned by: T1, T3, T4

### Design decisions

- **`rank` excludes `kind == "value"` from its count.** A throwaway probe of the
  unmodified fixture added two values owned by file 1: `rank(1)` moved from 2
  to 4, and default search order moved from `[4, 3, 1, 2]` to `[4, 3, 2, 1]`.
  The rejected alternative is unowned values (`parent_file = None`): the same
  probe showed an unowned value survives `remove_file_nodes`, so it would leak.
  This rests on the assumption that no caller relies on `rank` counting values;
  no value exists before this change, so none can.
- **Creation refuses a taken node id instead of reusing `add_node` blindly.**
  The probe showed `add_node` with a taken id silently replaces the declaration
  and leaves the old name's `name_index` entry pointing at the new node. The
  refusal lives only in the synthetic path, so declaration behavior is
  unchanged.
- **Builders and lifecycle code do not change.** A value owned by a file is
  removed by the existing `parent_file` selection in `remove_file_nodes`, which
  `apply_incremental` and `replace_file` both reach. This rests on the
  spec's open question about rebuild semantics resolving to "removed with the
  file".

Owned by: T2, T3

### Data & schema

- A synthetic value is a `Node` with `kind="value"` and a non-`None`
  `parent_file`. `Node` gains no field.
- The creation operation lives in `shared-graph-model.py` beside
  `Graph.add_node`. Its exact name and whether it is a `Graph` method or a
  module function are `implementation-discovered`; the constraint is that it
  validates, then delegates to `add_node`.
- The error type for both refusals is `implementation-discovered`; tests
  assert that an exception is raised and that state is unchanged.

Owned by: T2

### Interfaces & contracts

- `shared-graph-public.rs` does not change. The T4 check uses `Resolution`
  the way a downstream crate would: a struct literal and an exhaustive `let`
  destructure. A file-unchanged check is not the oracle.
- How the check is compiled is `implementation-discovered`. Discovery
  predicate: a Rust toolchain is reachable and the `.rs` file can be compiled
  as a library the check links against. Kill condition: no toolchain is
  reachable in local or CI execution; stop and ask the repository owner
  rather than adding a manifest.

Owned by: T4

## Tasks

### T1: Base-revision goldens are captured before any production edit

**Depends on:** none

**Tests:**
- A capture script runs the unmodified fixture on the frozen inputs and writes
  the golden file. Frozen inputs: file 1 declares `1 alpha function` and
  `2 beta method`; file 2 declares `3 gamma class` and `4 beta function`; the
  incremental update replaces file 1 with only `1 alpha function`; the
  dependency map is `{10: {1}, 11: {2}, 12: {1, 2}}`.
- Goldens recorded: `resolve_call` for every declared name (AC-0004); default
  `search` node-id sequences for no query, `"beta"`, and `"a"` (AC-0005,
  AC-0006); `rank` for node ids 1–4 (AC-0008); `nodes` and `name_index` after
  `build_full` (AC-0009) and after `apply_incremental` (AC-0010); the
  index-integrity result after each removal path (AC-0012); and
  `invalidated_files` for file ids 1 and 2 (AC-0013).

**Approach:**
- Test location is `implementation-discovered`. Discovery predicate: a test
  directory any repository runner collects. None exists, so place tests under
  `evals/` beside the fixture and ask before creating any other directory.

**Done when:** the golden file exists, and re-running the capture against the
unmodified fixture reproduces it byte for byte.

### T2: Synthetic values can be created, and bad creations are refused

**Depends on:** T1

**Tests:**
- TDD, at the graph model: creating value `100 "beta"` owned by file 1 on the
  T1 full-build graph adds exactly that node and index entry (AC-0001).
- Creating a value with id 3 raises and leaves `nodes` and `name_index` equal
  to a deep copy taken before the call (AC-0002).
- Creating a value with no owning file raises and leaves the same state
  unchanged (AC-0003).

**Touches:** evals/files/shared-graph-model.py

**Done when:** the three T2 tests are green and the T1 capture still
reproduces its goldens.

### T3: Existing readers match the goldens with synthetic values present

**Depends on:** T1, T2

**Tests:**
- Integration, over one graph built from the T1 inputs plus values
  `100 "beta"` and `101 "v"` owned by file 1 and `102 "gamma"` owned by file 2.
  The name overlaps exercise the index and query paths.
- `resolve_call` matches the goldens (AC-0004).
- Default `search` matches the goldens (AC-0005).
- `search(include_values=True)` with value nodes removed matches the default
  goldens (AC-0006), and its value nodes equal the query-matching set (AC-0007).
- `rank` matches the goldens; this is red before the `rank` filter (AC-0008).
- `build_full` matches its golden (AC-0009).
- After `apply_incremental` of file 1, non-value state matches its golden
  (AC-0010).
- For each of `remove_file_nodes`, `replace_file`, and `apply_incremental` on
  file 1, from a fresh graph each time, the remaining values are exactly
  `{102}` (AC-0011), and every `name_index` id is a key of `nodes` (AC-0012).
- `invalidated_files` matches its goldens (AC-0013).

**Touches:** evals/files/shared-graph-consumers.py

**Done when:** every T3 test is green, the AC-0008 test was observed red before
the `rank` change, and the T1 capture still reproduces its goldens.

### T4: Downstream use of `Resolution` still compiles and behaves

**Depends on:** none

**Tests:**
- Goal-based compile check: Rust code outside `shared-graph-public.rs` builds
  `Resolution { target: Some(7), confidence: 3 }`, destructures it with
  `let Resolution { target, confidence } = r;`, asserts `unresolved()` is
  `target: None, confidence: 0`, and asserts `consume` over the four cases of
  `Some`/`None` and `0`/`>0` (AC-0014).

**Done when:** the check compiles and its assertions pass, with
`shared-graph-public.rs` unedited.

## Rollout

Pure fixture logic with no flag, infrastructure, external system, or
deployment order. Rollback is a revert.

## Risks

- A caller outside the fixture may rely on `rank` counting every node. No value
  exists today, so the filter changes nothing for current inputs, but an
  unseen caller with its own value nodes would see ranks change.
- With no test runner, T1–T4 run only when someone invokes them. Until a runner
  collects them, they do not guard later changes.

## Changelog
````

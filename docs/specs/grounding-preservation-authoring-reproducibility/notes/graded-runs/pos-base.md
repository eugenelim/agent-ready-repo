## Summary

I wrote a Draft spec and plan for synthetic value nodes in `docs/specs/synthetic-value-nodes/` under `/tmp/gpar-base-pos/work`. The skill's alignment lint passes with 0 findings. The skill's stale-assertion rule did not run because the directory has no git history. Neither file is ready for approval yet: the independent reviews could not run (see Reviews below).

**What must be preserved.** Synthetic values are added to a graph that other code reads without opting in. So I mapped every behavior class those readers cover against the five fixture files. 13 criteria resulted:

- **The proposed feature test:** AC-0001 proves only that a synthetic value can be created.
- **Creating nodes:** AC-0002 refuses an id the graph already holds. AC-0003 keeps the old ways of building a `Node` working.
- **Readers of the graph:** call resolution (AC-0004), default search (AC-0005), explicit value search (AC-0006) and ranking (AC-0007).
- **Builds and updates:** full and incremental builds agree (AC-0008). Updating a file removes its synthetic values (AC-0009) and keeps other files' values (AC-0010). Invalidation is unchanged (AC-0011).
- **Public Rust surface:** `Resolution` still builds and destructures from outside the crate (AC-0012). `consume` behaves the same (AC-0013).
- **Serialization:** no reader exists. The search for one found no match (grep exit 1).

**Main finding.** A probe of the supplied files, run in memory with no files written, showed a break the creation test misses. Attaching two values to `a.py` raised its `rank` from 1 to 3. That moved it after `b.py` in default `search`, even though search hides values. Declared values already count toward rank, so the plan adds a `synthetic` flag and makes ranking skip only synthetic nodes. The probe confirmed this brings back the original search order.

Two more risks from the probe are guarded:
- A value with no owning file survives an incremental update, so every synthetic value gets one.
- `add_node` silently overwrites a used id and leaves a stale `name_index` entry, so creation refuses a used id.

**What I checked.**
- The grounding script found no `AGENTS.md`, guidance files, gates, git history or manifests.
- Python 3.15 is available. pytest is not, so tests use `unittest`.
- `rustc` and `cargo` are absent.
- The probe wrote a `__pycache__` into `evals/files/`. I deleted it, and the plan runs tests with `-B` so this does not recur.

**Questions I would have asked; I went ahead with my best guess** (no human was available):
1. What triggers a synthetic value: a caller, or a rule applied to each parsed file? I assumed a caller adds it to a file. A rule would change both build paths and need an amendment.
2. Who uses synthetic values? I assumed nobody yet, so this spec covers creating and finding them only.
3. Which toolchain or CI job runs the Rust check? Until one is named, T4 is blocked.
4. Who approves the spec and its Agent Rules? The repository names nobody.
5. Is `evals/tests/` the right place for tests? No convention exists.

**Reviews.**
- `BLOCKED: spec shaping review — independent route unavailable`. Subagents were not allowed, so the spec stays at `Draft`.
- `adversarial-reviewer: no matching subagent dispatched (subagents disallowed); review skipped`.

## docs/specs/synthetic-value-nodes/spec.md

```markdown
# Spec: synthetic value nodes

- **Status:** Draft
- **Owner:** <owner-handle>
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none — the Rust `Resolution` surface in `evals/files/shared-graph-public.rs` is a supported public interface this spec preserves, not one it defines or changes
- **Shape:** data

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

Code that builds the repository graph can add a synthetic value node, a value
that no source file declares, to a file and find it through an explicit value
search. Every existing reader of the graph returns exactly what it returned
before for the declared nodes: call resolution, default search, ranking, full
and incremental builds, invalidation, file cleanup, and the public Rust
`Resolution` surface.

## What Changes

- A node can be marked synthetic, and existing ways of building a node still work unchanged — `evals/files/shared-graph-model.py`
- One creation entry point adds a synthetic value to a file and refuses an id the graph already holds — `evals/files/shared-graph-lifecycle.py`
- Ranking stops counting synthetic values as a file's children — `evals/files/shared-graph-consumers.py`
- A frozen copy of the five fixture files becomes the base-revision oracle, and differential tests compare against it — a new test directory under `evals/`

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | Applicable: the Rust `Resolution` struct is public and must stay constructible and destructurable | The compile-check consumer in the new test directory | Implementer of T4 | AC-0012 and AC-0013 checks green under a Rust toolchain | close-work confirms the compile check ran, or records the open toolchain question as unresolved |
| Current architecture | Applicable: "containment is the lifecycle boundary" is stated only in the docstring of `shared-graph-lifecycle.py`, and synthetic values must follow it | Docstrings of the changed functions in `evals/files/` | Implementer of T2 | The creation function's docstring states that a synthetic value is owned by its file and removed with it | close-work reads the docstring |

No other role applies. The repository has no user documentation, architecture
document, decision record, changelog, or contributor guide to update.

## Agent Rules

### Always do

- Take the expected side of every preservation check from the frozen base-revision copy, run on the same input, and never from the code under test.
- Give every synthetic value an owning file, so that removing the file removes the value.
- Keep declared nodes, including declared values with kind `value`, behaving exactly as in the base revision.

### Ask first

- Changing the fields, field order, or derives of the Rust `Resolution` struct, or the bodies of `unresolved` or `consume`.
- Making `build_full` or `apply_incremental` create synthetic values themselves, which depends on the open trigger question under Assumptions.
- Adding a test runner, a package manifest, or any third-party dependency.

### Never do

- Never add a new top-level directory or a new module file inside `evals/files/`; the change lives in the existing five fixture files plus one test directory under `evals/`.
- Never let a synthetic value replace an existing node, or remain in `nodes` or `name_index` after its file is removed or replaced.
- Never mark `Resolution` `#[non_exhaustive]` or add a field to it.
- Never prove preservation by checking that a file is unchanged, or by "existing tests pass"; the repository has no existing tests.

## Testing Strategy

- **TDD (AC-0001, AC-0002, AC-0003)** — creating, refusing, and constructing nodes are small logic with a clear invariant, so a red test comes first, at the Python unit level.
- **Goal-based differential check (AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011)** — each is an integration test that runs the frozen base-revision modules and the changed modules on the same fixture and compares the named output, because preservation is only visible as a comparison with the old behavior.
- **Goal-based compile check (AC-0012, AC-0013)** — a consumer crate built and run against the library, because Rust compatibility is decided by the compiler on the supported construction and destructuring surface, not by reading the source.

## Acceptance Criteria

"Base revision" means the five files under `evals/files/` whose SHA-256 digests
are listed in the plan's `## Constraints`. "Without synthetic values" means the
same fixture graph built with every synthetic-value creation step left out.

- [ ] **AC-0001.** When a synthetic value is created with an unused node id, a name, and an owning file id, the graph holds exactly one new node with that id, kind `value`, that name, `parent_file` equal to the owning file id, and marked synthetic, and `name_index[name]` contains that id.
- [ ] **AC-0002.** If a synthetic value is created with a node id the graph already holds, creation raises an error and `nodes` and `name_index` compare equal to their state before the call.
- [ ] **AC-0003.** A `Node` built in each base-revision form — positional or keyword, with and without `parent_file` — succeeds, is not marked synthetic, and has the same `node_id`, `name`, `kind`, and `parent_file` values as the base-revision `Node` built from the same arguments.
- [ ] **AC-0004.** For a fixture where a synthetic value shares its name with a declared function and a declared method, `resolve_call` on that name returns the same node ids, in the same order, as the base revision on the fixture without synthetic values.
- [ ] **AC-0005.** For a fixture where synthetic values are attached to a file that also has declared children, `search` with `include_values` left false returns the same node ids, in the same order, as the base revision on the fixture without synthetic values, both with no query and with a query matching a synthetic value's name.
- [ ] **AC-0006.** With `include_values=True`, `search` returns the base-revision result on the fixture without synthetic values plus exactly the synthetic values that match the query, and the declared nodes keep the same relative order as in the base-revision result.
- [ ] **AC-0007.** For every node id present in the fixture without synthetic values, `rank` returns the base-revision value after synthetic values are added, including a file whose children include a declared value.
- [ ] **AC-0008.** For declared input files that include a declared value, `build_full` over the final file set and `build_full` over the initial set followed by `apply_incremental` of the changed file produce the same node records and, for each name with a non-empty list, the same sorted id list in `name_index`, and both equal the base revision's output on the same input.
- [ ] **AC-0009.** For each update path — `apply_incremental` and `replace_file` — updating file F leaves no synthetic value whose owning file is F in `nodes` or in any `name_index` list.
- [ ] **AC-0010.** For each update path — `apply_incremental` and `replace_file` — updating file F leaves every synthetic value owned by another file present in `nodes` and `name_index` with unchanged field values.
- [ ] **AC-0011.** After synthetic values are created for a file, `invalidated_files` returns, for every file id in the fixture dependency map, the same set as the base revision.
- [ ] **AC-0012.** A consumer crate that builds `Resolution { target: None, confidence: 0 }` and `Resolution { target: Some(7), confidence: 3 }` as struct literals and destructures one with `let Resolution { target, confidence } = r;` compiles against the library.
- [ ] **AC-0013.** In that consumer, `consume(unresolved())` returns `false` and `consume(Resolution { target: Some(7), confidence: 3 })` returns `true`.

## Follow-ons

none

## Assumptions

- Product: what triggers a synthetic value — a caller adding it to a file, or a rule that derives it from each parsed file — is unanswered; a derivation rule would make both build paths create synthetic values and would add a criterion that full and incremental builds produce the same synthetic values (settled by: feature owner).
- Product: no consumer of synthetic values is named, so this spec covers creating and finding them, not using them in call resolution or as a `Resolution` target (settled by: feature owner).
- Technical: no Rust toolchain or Cargo manifest is present, so the AC-0012 and AC-0013 checks cannot run in this workspace (settled by: maintainer naming the toolchain or CI job that runs them).
- Process: the repository has no contribution guide, `AGENTS.md`, or decision records, so nobody is named to approve this spec or its Agent Rules (settled by: repository owner).
```

## docs/specs/synthetic-value-nodes/plan.md

```markdown
# Plan: synthetic value nodes

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting
- **Repository anchors:** no architecture, convention, or `AGENTS.md` source exists; the substrate definition is `evals/files/shared-graph-model.py`, and its generic readers and writers are the other four files under `evals/files/`; no tests, manifests, runners, or git history exist; deviation: the base-revision oracle is a frozen file copy, because there is no version control to diff against

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`. After approval, execution
> observations go to `docs/specs/synthetic-value-nodes/notes/verification-ledger.md`.

## Approach

Freeze the base revision first, so every later check has an oracle that the
change cannot move. Then add the model field and the creation entry point under
red tests. Then fix ranking, which is the one existing reader that a synthetic
value disturbs today. Last, add the Rust compile check. The riskiest part is
ranking: a synthetic value attached to a file raises that file's rank and
reorders default search, even though search hides the value itself.

## Constraints

- No ADR or RFC governs this repository.
- Tests use the Python standard library (`unittest`, `importlib`) because no test runner is installed and no manifest exists. Python 3.15 is the available interpreter; the fixture already needs 3.10 or later for `int | None` and `set[int]`.
- The fixture module names contain hyphens, so tests load each file by path with `importlib.util.spec_from_file_location`, and run with bytecode writing off (`python3 -I -B`), so no `__pycache__` lands in `evals/files/`.
- Base-revision identity, SHA-256 of each file at freeze time:
  - `shared-graph-builders.py` — `44789ddada567d8f11760857ab552cda7423c2adb46563ef9a446a3c0c647b08`
  - `shared-graph-consumers.py` — `ac3af2f8edd6aab3290a65f5176342965ed8a5109173e612003e7fe8303e5fb6`
  - `shared-graph-lifecycle.py` — `3602663715a23d13319b708dc93ce7ddc392b4c680fd5ac29450a4da53544d2d`
  - `shared-graph-model.py` — `8a9a9fcc3325bc524dd822ceeb288af59714c363e0619c5e4a169675b862ef6c`
  - `shared-graph-public.rs` — `8eab927cc1063928aa2a57b8787563d1c0ab3106de26eea1e99b65d3ce712ac6`

## Construction tests

**Integration tests:** the differential suite in T1 runs the baseline and the
changed modules on one shared fixture; T2–T3 add cases to it.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility / Rust compile-check consumer | T4 | Consumer crate builds and its assertions pass | Toolchain run recorded in the verification ledger, or the open toolchain question carried as unresolved |
| Current architecture / creation-function docstring | T2 | Docstring states file ownership and removal with the file | close-work reads the docstring |

## Design (LLD)

### Design decisions

- Synthetic values reuse kind `value`, so the existing `include_values` filter in `search` already hides them by default. A new kind would show them in default search. Rests on: `value` is the only kind that filter excludes.
- A separate `synthetic: bool = False` field, appended last on `Node`, tells synthetic values from declared ones. Ranking needs that split: declared values count toward a file's rank in the base revision, so excluding every `value` would change rank for declared input. Rests on: no base-revision caller passes a fifth positional argument to `Node`.
- The creation entry point sits beside `attach_to_file` and attaches through it, so the existing rule that containment is the lifecycle boundary covers synthetic values. `remove_file_nodes` already deletes by `parent_file`, so both update paths remove a file's synthetic values with no change. Rests on: every synthetic value has a non-`None` owning file.
- The entry point checks `node_id in graph.nodes` before attaching, because `Graph.add_node` overwrites silently and leaves a stale id in the old name's `name_index` list.
- `build_full`, `apply_incremental`, and `invalidated_files` are not changed. The trigger question in the spec's Assumptions decides whether that holds.

Owned by: T2, T3

### Data & schema

- `Node` gains `synthetic: bool = False` as its last field. Everything else in `Node` and `Graph` stays.
- `rank` counts a node as a child only when its `parent_file` matches and it is not synthetic.

Owned by: T2, T3

### Interfaces & contracts

- Python: one new function in `shared-graph-lifecycle.py`; its exact name and signature are `implementation-discovered`. Constraint: it takes the graph, owning file id, node id, and name, and raises on a used id. Verified by the AC-0001 and AC-0002 tests.
- Rust: `Resolution`, `unresolved`, and `consume` stay as they are. The compile check exercises struct-literal construction and exhaustive destructuring from outside the crate, which is the surface `#[non_exhaustive]` or a new field would break.

Owned by: T2, T4

### Consumer map

Built from the substrate definition and every read path in the five supplied
files. No code-intelligence provider was used.

| Class | Consumer evidence | Criterion or gap |
| --- | --- | --- |
| Direct readers and writers | `shared-graph-model.py` `Node`, `Graph.add_node`, `Graph.remove_node`; `shared-graph-lifecycle.py` `attach_to_file` | AC-0001, AC-0002, AC-0003 |
| Selection and resolution | `shared-graph-consumers.py` `resolve_call` reads `name_index` and filters to `function`/`method` | AC-0004 |
| Default search or presentation | `shared-graph-consumers.py` `search`, `include_values` filter | AC-0005, AC-0006 |
| Ranking and traversal | `shared-graph-consumers.py` `rank` counts nodes by `parent_file`, used as `search`'s first sort key | AC-0007 (and AC-0005 observes it through search order) |
| Full and alternate construction | `shared-graph-builders.py` `build_full`, `apply_incremental` | AC-0008 |
| Invalidation and update | `shared-graph-builders.py` `invalidated_files`, `apply_incremental`; `shared-graph-lifecycle.py` `replace_file` | AC-0009, AC-0010, AC-0011 |
| Lifecycle and cleanup | `shared-graph-builders.py` `remove_file_nodes`; `shared-graph-lifecycle.py` `replace_file` | AC-0009, AC-0010 |
| Serialization | Unreachable: `grep -rniE 'json\|pickle\|serial\|asdict\|to_dict\|dump\|repr' evals/` found no match (exit 1) | none needed |
| Supported public compatibility | `shared-graph-public.rs` `pub struct Resolution`, `unresolved`, `consume` | AC-0012, AC-0013 |

Owned by: T1, T4

### Disconfirming evidence

A side-effect-free in-memory probe over the supplied files showed:

- Attaching two synthetic values to file `a.py` moved it after `b.py` in default `search` output, because its rank rose from 1 to 3. This disproves "search hides values, so search is safe" and is why ranking changes.
- With a `synthetic` field and a rank that skips synthetic nodes, default search order matched the base result, and `include_values=True` kept the declared nodes' relative order.
- A value node with `parent_file=None` survived `apply_incremental` of its file. This is why every synthetic value has an owning file.
- `add_node` with a used id replaced a function and left its id in the old name's `name_index` list. This is why creation refuses a used id.
- On declared input, full and incremental builds matched once empty `name_index` lists were ignored. AC-0008 therefore compares non-empty lists only.

Owned by: T2, T3

### Fixture

One reference fixture serves every differential test. It has two file nodes,
a declared function and a declared method with one shared name, a declared value
under the file that receives synthetic values, synthetic values on both files
(one sharing the function's name), and a dependency map in which each file
depends on the other. Exact ids are `implementation-discovered`.

Owned by: T1

## Tasks

### T1: The base revision is frozen and the differential harness compares baseline and current modules on the reference fixture

**Depends on:** none

**Touches:** `evals/tests/baseline/*`, `evals/tests/harness.py`, `evals/tests/test_preservation.py`

**Tests:**
- A harness check recomputes the SHA-256 of each file in `evals/tests/baseline/` and fails if any differs from `## Constraints`. This keeps the oracle the base revision.
- The differential cases for AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, and AC-0011 are written against the reference fixture. Cases that need a synthetic value skip with a named reason until T2 lands. Cases that do not — AC-0008 on declared input — pass now.

**Approach:**
- Copy the five files before any edit to `evals/files/`. Every later task compares against this copy.

**Done when:** `python3 -I -B -m unittest discover -s evals/tests` reports the digest check and AC-0008 green, and every other case skipped with its reason.

### T2: Synthetic values can be created and are refused on a used id

**Depends on:** T1

**Touches:** `evals/files/shared-graph-model.py`, `evals/files/shared-graph-lifecycle.py`, `evals/tests/test_synthetic.py`

**Tests:**
- AC-0001: red first. Create a synthetic value through the new entry point. Assert the five node fields and that the id is in `name_index`.
- AC-0002: red first. Snapshot `nodes` and `name_index` by deep copy, call creation with a used id, and assert the error and equality with the snapshot.
- AC-0003: build `Node` in the four base-revision forms against both the baseline and the changed model. Compare the four shared fields, and assert `synthetic` is false.
- AC-0009 and AC-0010 un-skip in the differential suite. They pass with no change to either update path.

**Done when:** the T2 tests and the un-skipped AC-0009 and AC-0010 cases are green.

### T3: Synthetic values leave resolution, search, ranking, and invalidation unchanged

**Depends on:** T2

**Touches:** `evals/files/shared-graph-consumers.py`

**Tests:**
- AC-0005 and AC-0007 un-skip and go red before the rank change. The fixture's synthetic values sit on the file that has declared children.
- AC-0004, AC-0006, and AC-0011 un-skip and stay green through the change.
- AC-0008 stays green.

**Done when:** `python3 -I -B -m unittest discover -s evals/tests` reports every Python case green and none skipped.

### T4: The public Resolution surface still builds and behaves for an outside consumer

**Depends on:** none

**Touches:** `evals/tests/rust_consumer/*`

**Tests:**
- AC-0012: compile `evals/files/shared-graph-public.rs` as a library crate, then compile a consumer that uses it through `--extern` and has the two struct literals and the exhaustive `let Resolution { target, confidence } = r;`.
- AC-0013: the consumer's `main` asserts both `consume` results and exits 0.

**Done when:** the consumer builds and exits 0 under the toolchain the open Assumptions item names. Until then, the task is blocked, and the ledger records that.

## Rollout

Pure fixture-and-test change: no flag, infrastructure, external system, or
deployment order. Rollback is reverting the edits to `evals/files/` and removing
`evals/tests/`.

## Risks

- If the owner answers the trigger question with a per-file derivation rule, `build_full` and `apply_incremental` change, and the spec needs an amendment for a full-versus-incremental synthetic-value criterion.
- `evals/tests/` is a new directory chosen without a repository convention; the owner may want another location.

## Changelog

none
```

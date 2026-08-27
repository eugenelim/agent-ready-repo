# Plan: Local pytest process optimization

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `AGENTS.md`; `tools/AGENTS.md`;
  `docs/CONVENTIONS.md`; `ARCHITECTURE.md`;
  `docs/architecture/overview.md`; ADR-0071, ADR-0094, ADR-0096;
  `Makefile`; `pyproject.toml`; `tools/repo/build_gate_chain.py`;
  `tools/test_build_gate_chain.py`;
  `tools/test_local_ci_shared_test_deduplication.py`; and the source-resolution
  guard and regression history in `tools/test_import_time_path_leaks.py` and
  commit `687a8ed62`. The closest analogous mechanisms are the existing
  explicit Make pytest rosters and `_pytest_step_cwd`; the named uncertainty is
  that the repository declares no pytest dependency version range, so the plan
  uses documented public hooks and verifies the currently resolved pytest
  9.0.3 without inventing a historical compatibility promise.

> **Plan contract:** this is the implementation strategy. It remains mutable
> while Drafting. After human approval and cohort scheduling, substantive edits
> require returning to the plan gate rather than silently changing course.

## Approach

Implement two independently reversible waves. Wave A adds a narrow,
pure-standard-library pytest plugin that is inert unless explicitly loaded and
given a minimum count; exactly four current owners pass that count to their real
pytest execution, eliminating four ordinary collection-only launches without
moving a test. Wave B replaces five separately proven tool invocations with one
explicit five-path pytest command. It does not merge `tests/`, the
workspace-status pair, either existing batch, any other singleton, or any pack
suite. Construction tests precede each production edit and derive membership
and topology from the real Make/build-chain sources. Focused characterization,
mutation controls, resource measurement, full public gates, and two independent
review roles close the work.

The riskiest part is not the floor hook; it is shared-interpreter state that can
make a test pass only after another module has altered import resolution. For
that reason, process minimization stops at the sole class with isolated,
reordered, repeated, source-resolution, and failure-shaped evidence.

## Assumption trio and declined additions

- **Files expected to change:** `Makefile`, `tools/pytest_collection_floor.py`,
  `tools/repo/build_gate_chain.py`, `tools/test_build_gate_chain.py`,
  `tools/test_local_ci_shared_test_deduplication.py`, this spec and plan,
  `docs/specs/README.md`, and `workspace.toml`.
- **Tests that demonstrate done:** focused plugin/build-chain tests; real-Make
  construction and mutation tests; isolated/grouped exact collection and
  reordered execution; path-leak mutation control; Opportunity-1, CI parity,
  Make recursion/interpreter, editable-install, worktree/lease, and participant
  regressions; then one `make test` and one `SKIP_SAST=1 make ci`.
- **Not changing:** test/gate membership except approved new construction nodes
  inside already-owned files; pack process boundaries; Opportunity-1 ownership;
  workflows; SAST/SCA; coordination; production modules under test; the
  import-time path guard; shipped/frozen spec bodies; or existing node IDs.
- **Declined general runner:** a repository-wide executor or manifest would add
  a second authority for a bounded Make roster and is unnecessary.
- **Declined wrapper:** an outer Python entrypoint changes launcher and process
  semantics and would save no child over an opt-in plugin.
- **Declined broad consolidation:** `pytest tools/ tests/` recreates the exact
  historically dangerous source-resolution direction.
- **Declined import-child removal:** the specialized full-roster sanitized
  collector is not equivalent to the reduced local roster.
- **Declined pytest version policy:** no current repository range exists; this
  initiative does not create dependency governance to justify the hook.

No task approaches 2,000 reviewable behavior/test lines. The work is DEEP but
small: two dependency-ordered, independently reversible behavior waves, then
verification. There is no ungrounded domain claim. The resolve-vs-surface record
opens with all implementation choices resolved by repository evidence; the
only surfaced decision is the required human spec/plan approval.

## Baseline authority and command plans

### Orientation

- Current branch: `eugenelim/pytest-sessions-floor`.
- Checked-out and investigation-baseline commit:
  `f871fe506053ea17dd1702ccea37c802b78de557`.
- Local `origin/main` matched that commit at orientation, then moved externally
  during plan review to `fdacdb66c481c92035e5626a32e4f43579d78180` while
  `HEAD` remained unchanged. The user-authorized read-only profile skips the
  work-loop freshness command because that command force-fetches and writes a
  remote-tracking ref. On 2026-08-26 the owner explicitly approved completing
  this initiative on the investigated `f871fe5` checkout and resynchronizing
  later; no plan evidence is represented as characterizing `fdacdb66`.
- Worktree state before intake: clean. Current pre-implementation changes are
  only `workspace.toml`, the active entry in `docs/specs/README.md`, and this
  new spec directory.
- Ownership search: no active spec owns pytest process consolidation or
  one-pass collection floors. Backlog and deleted/historical references are
  evidence only. Opportunity 1 is shipped and explicitly excludes this work.

### Expanded public routes

The command plans come from the real `Makefile` and build-chain step list:

```text
make test
  -> coordination_lease.py with-lease
  -> recursive make test-unleased
  -> lint-editable-install
  -> run-test-suite with the workspace-status pair argument present

test-after-build-check
  -> requires build-check
  -> coordination_lease.py with-lease
  -> recursive make test-after-build-check-unleased
  -> lint-editable-install
  -> run-test-suite with three Opportunity-1 file exclusions and no
     workspace-status pair argument

make ci
  -> build-check + lint-ruff + lint-mypy + test-after-build-check
  -> the approved dependency graph and build-check ownership remain unchanged
```

`run-test-suite` also contains package, pack, npm, and direct-Python commands.
They remain in their current order and are not Opportunity-2 candidates. The
one-process-per-pack/skill lines remain byte-identical except for the two desk
floor arguments described below.

### Root/tool roster definitions

`B1` is the existing first explicit tool batch:

```text
tools/test_build_gate_chain.py
tools/test_journey_editorial_decisions.py
tools/test_catalogue_tooling_rewire.py
tools/test_catalogue_tooling_docs.py
tools/test_validate_guides.py
tools/test_check_guide_index.py
tools/test_catalogue_navigation.py
tools/test_documentation_entry_links.py
tools/test_build_site_link_rewrites.py
tools/test_check_rendered_site_links.py
tools/test_build_site_routing.py
tools/test_check_docs_contrast.py
tools/test_build_site_inventory.py
tools/test_build_site_projection.py
tools/test_build_site_sidebar.py
tools/test_browser_gate_subset.py
tools/test_local_ci_shared_test_deduplication.py
```

`B2` is the existing final explicit tool batch:

```text
tools/test_lint_agents_md_diataxis_block.py
tools/test_lint_agents_md_legacy_block.py
tools/test_lint_agents_md_risk_block.py
tools/test_lint_agents_md_frontmatter_scope.py
tools/test_catalogue_curation_guard.py
tools/test_contract_parity.py
tools/test_marketplace_envelope_parity.py
tools/test_guide_authoring_standard.py
tools/test_release_check.py
tools/test_check_release_impact.py
tools/test_scaffold_projection.py
tools/test_conformance_portability.py
tools/test_lint_guides_no_repo_only_refs.py
tools/test_okf_pre_pr.py
```

All rows below use repo-root cwd, root `pyproject.toml`, `-q`, exported Make
source-package `PYTHONPATH`, and the root plugin set unless the row says
otherwise. There is no root or `tools/` conftest. `Opp-1` means the process is
profile-controlled by the shipped ownership contract.

| Standalone / composed ordinal | Current pytest target(s) | Count and disposition | Nested behavior | Isolation rationale and candidate class |
| --- | --- | --- | --- | --- |
| 1 / 1 | `tests/` | 714; 2 `skipif` | Test-owned subprocesses | Historical source-resolution defect; bounded execution exceeded five minutes. Retain as highest-risk class. |
| 2 / 2 | `B1` (17 explicit files) | 323 | Build-chain/site subprocesses | Known-compatible current batch; cleanup-denied failures prevent merger proof. Retain. |
| 3 / omitted | `tools/test_workspace_status.py tools/test_workspace_status_cli.py` | 244 | CLI subprocesses | Opp-1 special owner; standalone only. Retain unchanged. |
| 4 / 3 | `tools/test_worktree_hygiene.py` | 41 | Git/worktree mutation | Clean-worktree/fs lifecycle; managed cleanup denial makes merger ambiguous. Retain. |
| 5 / 4 | `tools/test_worktree_lease_interlock.py` | 8; 1 `skipif` | Multiprocess/locks | Lease interlock and cleanup. Retain. |
| 6 / 5 | `tools/test_worktree_import_resolution.py` | 15 | Child imports | Requires clean interpreter/source resolution; cleanup failures. Retain. |
| 7 / 6 | `tools/test_editable_install_guard.py` | 22 | Import metadata/children | Editable-install and clean-interpreter expectations; cleanup failures. Retain. |
| 8 / 7 | `tools/test_import_time_path_leaks.py` | 4 | One specialized broad collect child per test case path | Proven member of new five-file class; specialized child remains. |
| 9 / 8 | `tools/test_managed_child.py` | 16; 14 `skipif` | Managed child processes | Proven member of new class; child cleanup checks pass. |
| 10 / 9 | `tools/test_coordination_lease.py` | 21 | Lease children | Proven member of new class; fixtures restore state. |
| 11 / 10 | `tools/test_branch_added_paths.py` | 7 | Git/path probes | Proven member of new class; no persistent state observed. |
| 12 / 11 | `tools/test_run_slot.py` | 12 | Locks/processes | Reverse candidate order produced real coordination contention. Retain singleton. |
| 13 / 12 | `tools/test_with_lease_cli.py` | 19 | CLI/lock children | Bounded candidate run did not complete. Retain singleton. |
| 14 / 13 | `tools/test_playwright_evidence_lifecycle.py` | 15 | Child/process lifecycle | `os.rmdir` cleanup failures and teardown errors. Retain singleton. |
| 15 / 14 | `tools/test_worktree_lifecycle_hooks.py` | 12 | Git/worktree lifecycle | Temporary-directory and hook mutation risk. Retain singleton. |
| 16 / 15 | `tools/test_frontend_runtime.py` | 33; 1 `skipif` | Runtime/signal/child behavior | Bounded probe did not finish. Retain singleton. |
| 17 / 16 | `tools/test_bootstrap.py` | 10 | Fake command subprocesses | Proven member of new five-file class. |
| 18 / 17 | `tools/test_check_artifact_contents.py` | 80; 3 `skipif` | PEP 517 build children | Build cleanup denied after assertions. Retain singleton. |
| 19 / 18 | `B2` (14 explicit files) | 146; 2 `skipif` | Direct scripts/build helpers | Known-compatible current batch; temporary-directory globals make wider merger ambiguous. Retain. |

The isolated collection union is 1,742 unique pre-existing node IDs in
standalone and 1,498 in composed. All 19 collections returned zero; no xfail
marker appeared in the collected metadata. Skip markers are listed above.
Execution failures caused by the managed `os.rmdir` denial are environment
evidence, not compatibility evidence; affected boundaries remain unchanged.

### Current and future collection-floor processes

The thresholds and baseline counts below are an execution view derived from
[`spec.md`'s Exact optimization contract](spec.md#exact-optimization-contract),
which is the canonical approval source for the values.

| Suite / owner | Current probe then execution | Floor / actual | Cwd, environment, config | Characterized failure behavior | Future one-pass command |
| --- | --- | ---: | --- | --- | --- |
| `packs/desk-research/tests/skills/desk-research/` / Make | Shell command substitutes `pytest ... -q --collect-only`, counts `::` with `grep`, then separately runs `pytest <suite> -q` | 9 / 15 | Repo cwd; Make exports; root config; no local conftest; cacheprovider unchanged | Low/zero/interrupt becomes shell exit 1; partial collection at or above floor reaches the second run and fails natively; bodies run only in second process | `$(PYTHON) -m pytest packs/desk-research/tests/skills/desk-research/ -q -p tools.pytest_collection_floor --minimum-collected=9 --collection-floor-suite=packs/desk-research/tests/skills/desk-research/` |
| `packs/desk-research/tests/skills/desk-research-project-start/` / Make | Same two-pass shell shape | 7 / 8 | Same root context; no local conftest | Same | `$(PYTHON) -m pytest packs/desk-research/tests/skills/desk-research-project-start/ -q -p tools.pytest_collection_floor --minimum-collected=7 --collection-floor-suite=packs/desk-research/tests/skills/desk-research-project-start/` |
| `assimilate-primitive` / build chain | `_pytest_step_cwd` captures `pytest -q -p no:cacheprovider --collect-only`, ignores probe rc, counts stdout `::`, then starts real pytest | 30 / 30 | Cwd is suite directory; `_source_packages_env()`; root config; suite conftest inserts its `.apm/.../scripts`; list argv | Low/zero/interrupt becomes build-chain exit 1 when count low; partial collection at/above floor reaches second run; captured native diagnostics can be suppressed | `[sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "tools.pytest_collection_floor", "--minimum-collected=30", "--collection-floor-suite=packs/catalogue-curation/tests/skills/assimilate-primitive"]` with exact existing cwd/env | 
| `assimilate-repo` / build chain | Same two-pass Python shape | 7 / 7 | Cwd is suite directory; same env/config; its own `.apm/.../scripts` conftest path | Same | `[sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "tools.pytest_collection_floor", "--minimum-collected=7", "--collection-floor-suite=packs/catalogue-curation/tests/skills/assimilate-repo"]` with exact existing cwd/env |

Collection errors, partial collection, zero tests, low counts, test failures,
skips, and interrupts were characterized. Skipped tests count as collected
items. The replacement intentionally improves fail-closed diagnostics: native
collection errors/interrupts dominate instead of being converted into a parsed
low-count message, while an actual low count fails in `pytest_collection_modifyitems`
before test execution.

Process accounting is separate:

The before/after values are likewise derived from the canonical spec table;
this table separates categories so the final measurement cannot collapse them
into a single headline.

| Category | Baseline | Planned |
| --- | ---: | ---: |
| Standalone root/tool outer pytest launches | 19 | 15 |
| Composed root/tool outer pytest launches | 18 | 14 |
| Ordinary collection-only floor launches | 4 | 0 |
| Real floor-bearing test launches | 4 | 4 |
| Specialized import-path child collections | 1 per owning guard invocation | unchanged |
| Other test-owned nested Python children | not exhaustively counted | semantic behavior unchanged; no removal claimed |

## Collection-floor design choice

| Option | Import/cwd and failure findings | Scope/cost | Decision |
| --- | --- | --- | --- |
| A — explicit opt-in pytest plugin | `-p tools.pytest_collection_floor` loads from repo root and deep suite cwd under the existing root config without a `sys.path` insertion. `pytest_collection_modifyitems` sees real items; returning when `session.testsfailed` preserves collection errors, and raising the session's failure type before runtest prevents bodies. Ordinary runs are unaffected when the plugin/options are absent. | One pure-stdlib tools module; public hook; no parent process or persistent state. | **Selected.** Narrowest mechanism common to all four invocations. |
| B — narrow Python wrapper around `pytest.main()` | Changes `python -m pytest` launcher semantics, the parent/child process shape, initial `sys.path`, signal handling, streams, and plugin discovery; deep-cwd parity needs extra bootstrap logic. | Adds a parent or turns the build chain into an in-process host; tends toward a runner. | Rejected. |
| C — opt-in conftest hook | A root conftest broadens every root session; four conftests duplicate policy; importing a shared helper from deep cwd adds source-resolution coupling. | Either pervasive or drifting. | Rejected. |

The plugin imports only the standard library, satisfying `tools/AGENTS.md`; it
does not import pytest at module import time. `pytest_addoption` defines
`--minimum-collected` and `--collection-floor-suite`. The public
`pytest_collection_modifyitems(session, config, items)` hook returns when no
floor is supplied or `session.testsfailed` is non-zero. Otherwise it compares
`len(items)`, emits `suite: collected N test(s), expected at least M`, and raises
`session.Failed` when low. This preserves exit 2 for collection errors and
interrupts and exit 1 for a genuine floor or test failure. The repository has
no declared pytest version range; tests therefore pin public-hook usage and the
current resolver's 9.0.3 behavior rather than claiming untested old versions.

Explicit Make commands are preferable to a manifest or runner. The two desk
lines gain literal plugin/floor arguments, and the five safe tool paths become
one visibly enumerated pytest command. Build-chain argv remains Python-owned
because cwd and Windows behavior already live there. No discovery or profile
selector is introduced.

## Compatibility matrix

The investigation inspected module-level `sys.path`, `sys.meta_path`, bare and
ambiguous imports, watched `sys.modules`, caches/registries, environment and cwd
mutation, logging/warnings/signals/atexit/locale/timezone, temporary globals,
asyncio policy and loops, multiprocessing method, monkeypatching, filesystem and
Git mutation, lease/run-slot state, process/thread cleanup, unittest class
state, session fixtures, plugin registration, and import-time production
behavior. The table records state that can survive a pytest file boundary;
pytest-managed fixture mutation is treated as restored only where reordered
execution proves it.

| Class | Import/path/modules | Environment/process globals | Filesystem/Git/children | Evidence | Disposition |
| --- | --- | --- | --- | --- | --- |
| `tests/` | Highest risk: historical earlier collector changed packaged-source resolution and cached worktree modules | Broad suite; bounded run timed out | Broad temp and subprocess surface | Exact isolated collection only; prior defect commit and current guard | Separate |
| `B1` | Imports build chain and site tooling; no new leak found | Many module caches and subprocess doubles | Cleanup-sensitive site/build tests | Current internal batch established; execution has cleanup-denied failures | Retain batch; no merger |
| Workspace-status pair | Registry/module injections are locally managed | CLI environment and class state | Many CLI temp roots/children | Shipped Opp-1 characterization | Separate profile owner |
| Worktree/fs singletons | Import resolution and editable-install tests explicitly need a clean interpreter | Leases, locks, cwd/env, process state | Git/worktrees/temp dirs; cleanup denied | Focused HEAD run once | Separate |
| New safe five-file class | Watched package paths and resolution identical before/after, forward/reverse | No surviving env/cwd/logging/signal/thread state observed; managed-child cleanup passes | Lease/path/bootstrap child behavior passes in both orders | Each file alone; exact 58-node union; forward/reverse; three alternating rounds; mutation guard; benchmark | **Merge** |
| `test_run_slot.py` | No path issue observed | Coordination admission state | Lock/process contention | Alone green; reverse candidate failed a real concurrency admission assertion | Separate |
| Remaining lifecycle/runtime singletons | Import risk varies | Signals, children, background/runtime state | Temp/worktree/build cleanup or bounded noncompletion | Incomplete or cleanup-denied characterization | Separate |
| `B2` | No known path leak, but wide module surface | Direct-script globals and subprocess doubles | TemporaryDirectory-heavy | Current internal batch only | Retain batch; no merger |

The approved five-file class is exactly:

```text
tools/test_import_time_path_leaks.py
tools/test_managed_child.py
tools/test_coordination_lease.py
tools/test_branch_added_paths.py
tools/test_bootstrap.py
```

This list is a command-oriented rendering of the canonical class in
[`spec.md`](spec.md#exact-optimization-contract), not an independent membership
authority.

Its pre-change commands are five separate `$(PYTHON) -m pytest <file> -q`
lines. Its post-change command is:

```text
$(PYTHON) -m pytest \
  tools/test_import_time_path_leaks.py \
  tools/test_managed_child.py \
  tools/test_coordination_lease.py \
  tools/test_branch_added_paths.py \
  tools/test_bootstrap.py -q
```

The exact isolated/forward/reverse collection has 58 unique nodes with SHA-256
`efa4ae209fbba434d71b9c090415ed0c77d6f14674094f410a992def9082bdc3`.
Both watched package paths occur once before and after collection, and
`agentbundle` and `credbroker` resolve to this worktree's package `__init__.py`
files in every order. A temporary import-time mutator made the existing guard
fail and attribute the path movement from one entry to two; the control was
removed afterward.

One non-package `sys.path` delta is expected and bounded:
`tools/test_branch_added_paths.py` inserts the repository root at module import.
A focused collection probe established the exact consequence. Relative to the
same four-file group without that module, the five-file group gains one
additional repo-root entry and one additional `tools/` entry (pytest prepends
`tools/` again when the next explicit module is collected after the root insert).
The `packages/agentbundle` and `packages/credbroker` entries, their multiplicity,
and loaded-module resolution do not move. T2 allows only this exact pair in both
approved orders and its negative controls prove any watched package-path or
resolution delta still fails; it does not treat an arbitrary `sys.path` change
as clean or edit the existing test mutation merely to enable consolidation.

Three comparable rounds produced:

| Shape | Wall seconds | Median wall | Median child CPU (user + sys) | Median peak RSS |
| --- | --- | ---: | ---: | ---: |
| Five isolated processes | 40.500, 38.943, 40.402 | 40.402 | 18.184 s | 99,483,648 bytes |
| One grouped process, alternating order | 28.998, 29.641, 29.701 | 29.641 | 13.662 s | 99,401,728 bytes |

The candidate is 26.6% faster by focused median wall time, 24.9% lower by
median child CPU, and shows no peak-RSS increase. A candidate is materially
regressive under the canonical rule in
[`spec.md`](spec.md#exact-optimization-contract). Crossing that rule stops for
renewed human approval.

## Final isolation classes

The standalone route has these 15 root/tool pytest processes; composed has the
same list except class 3, for 14:

1. `tests/` — historical source-resolution boundary and incomplete bounded run.
2. `B1` — existing compatible batch; no wider clean evidence.
3. Workspace-status pair — standalone-only Opportunity-1 owner.
4. `tools/test_worktree_hygiene.py` — worktree/fs isolation.
5. `tools/test_worktree_lease_interlock.py` — lock/process interlock.
6. `tools/test_worktree_import_resolution.py` — clean-interpreter resolution.
7. `tools/test_editable_install_guard.py` — installed/source resolution.
8. The explicit five-file compatible class above — the only new merger.
9. `tools/test_run_slot.py` — reversed-order failure.
10. `tools/test_with_lease_cli.py` — bounded noncompletion.
11. `tools/test_playwright_evidence_lifecycle.py` — lifecycle/cleanup state.
12. `tools/test_worktree_lifecycle_hooks.py` — Git/hook lifecycle state.
13. `tools/test_frontend_runtime.py` — runtime/signal/child noncompletion.
14. `tools/test_check_artifact_contents.py` — PEP 517 child/cleanup state.
15. `B2` — existing compatible batch; no wider clean evidence.

`tools/test_import_time_path_leaks.py` stops being an outer singleton but keeps
its own nested child unchanged. That child still collects the broader intended
`tools` and `tests` surface, strips inherited `PYTHONPATH` and `PYTEST_ADDOPTS`,
uses named carriers, continues through collection errors for attribution, and
holds its independent floor of 1,200. No nested-child reduction is claimed.

## Constraints

- ADR-0071 owns the pack/skill test-boundary rule; those commands do not move.
- ADR-0094 owns source imports and editable-install protection; the new plugin
  performs no path insertion.
- ADR-0096 and the shipped Opportunity-1 spec own the composed five-file graph;
  the workspace pair stays the literal third macro argument in standalone and
  absent in composed.
- `tools/AGENTS.md` requires a new tools module to be pure standard library.
- No workflow, ADR, shipped spec body, SAST/SCA, coordination, or production
  subject is modified.
- Managed `os.rmdir` denial is a documented environment limitation. It does not
  license weakening tests, retry loops, or interpreting cleanup-red candidates
  as compatible.

## Construction tests

**Integration tests:**

- Real-source parsing and mutation-shaped copies prove exact Make roster,
  process grouping, floors, Opp-1 ownership, pack boundaries, recursive and
  parallel ordering, and absence of the four old probes.
- Focused subprocess fixtures prove the plugin's floor/native-failure contract
  and build-chain argv/cwd/env/fail-fast behavior.
- Actual isolated/grouped collection and execution prove the 58-node class in
  both approved orders; controlled import mutation proves the historical guard.
- One final public standalone gate and one final composed non-SAST gate.

**Manual verification:** none. The outputs are command plans, exit statuses,
node inventories, and resource readings, all mechanically observable.

## Design (LLD)

### Design decisions

- `tools.pytest_collection_floor` is an opt-in plugin, not a global conftest or
  runner. It uses pytest's real item list and is inactive unless both explicitly
  loaded and passed a floor. Traces to AC6-AC11 and AC20.
- The Makefile gains only literal arguments on two existing skill lines and one
  explicit five-path grouped command. It gains no manifest, discovery, profile,
  or duplicated recipe. Traces to AC1-AC6, AC16, AC20.
- `_pytest_step_cwd` remains a subprocess owner. Its `floor` parameter appends
  plugin arguments to the real child instead of launching a probe; cwd/env and
  list argv stay unchanged. Traces to AC6-AC11.
- Source/path characterization remains external construction evidence. The
  specialized import-time child remains the independent regression oracle.
  Traces to AC12-AC15.

### State and control flow

```text
Desk Make suite
  -> one python -m pytest child
  -> explicitly load tools.pytest_collection_floor
  -> collect real items
     -> native collection error/interrupt: native pytest failure
     -> actual < floor: diagnostic + session failure before runtest
     -> actual >= floor: ordinary pytest runtest and exit semantics

Catalogue build-chain suite
  -> _pytest_step_cwd constructs one list argv with existing cwd/env/flags
  -> same plugin collection decision
  -> _run_chain stops on the child's non-zero status

Root/tool route
  -> explicit processes 1-7
  -> one explicit five-file process
  -> explicit processes 9-15
  -> no background execution or cross-process state
```

### Failure, edge cases, and resilience

- `session.testsfailed` prevents a floor exception from masking a native
  collection error. Interrupted collection does not reach a false low-count
  success.
- A low floor raises before runtest; a sentinel body proves it never ran.
- A normal test failure passes through unchanged after the floor succeeds.
- Missing or duplicated Make paths fail construction tests derived from the
  real source. A broad `tools/` target is forbidden.
- A reversed-order failure rejects the merger even if forward order is green;
  this rule retained `test_run_slot.py`.
- If post-change resource measurement crosses a material threshold, Wave B is
  rolled back independently while Wave A remains.

### Quality attributes

- **Correctness:** exact non-empty node unions, real pytest hooks, native error
  precedence, and explicit profile ownership.
- **Performance:** four collection-only launches and four root/tool launches
  disappear; the only merged class has lower measured wall/CPU and no RSS rise.
- **Maintainability:** all membership remains visible in `Makefile`; plugin
  semantics are focused in one pure-stdlib module and pinned by subprocess tests.
- **Portability:** no shell in the build-chain path; no new path syntax or
  platform API; rootdir and deep cwd are characterized.

## Human approval transaction (pre-EXECUTE gate)

The spec and plan stay `Draft` / `Drafting` and no implementation or test-file
stub is written until the owner explicitly approves this checkpoint. On an
unambiguous approval, the controller:

1. changes the spec to `Approved` and fires `spec-approved`;
2. changes the plan to `Approved` and fires `plan-approved`;
3. immediately records the approved baseline with `loop-cohort approve-plan`;
4. schedules T1-T3, fires `plan-locked`, and changes lifecycle tokens to
   `Implementing` / `Executing` before the first test edit.

A rejection or scope adjustment returns both artifacts to drafting and repeats
pre-EXECUTE review. The plan checkpoint explicitly approves only the four floor
routes, the five-file tool group, and new construction nodes inside the two
already-owned test files. It does not approve any Ask-first item outside that
list.

## Tasks

### T1: Four floor-bearing suites enforce their minimum in one real pytest process

**Depends on:** none

**Touches:** `tools/test_build_gate_chain.py`,
`tools/test_local_ci_shared_test_deduplication.py`,
`tools/pytest_collection_floor.py`, `tools/repo/build_gate_chain.py`, `Makefile`

**Mode:** TDD — subprocess contract and real-source construction tests precede
the plugin, build-chain, and Make edits.

**Tests:**

- Add focused plugin subprocess cases for exactly/above/below/zero collection,
  collection import error, partial collection, interrupted collection, unmet
  floor body sentinel, real test failure, explicit diagnostic, ordinary opt-out,
  public-hook/current-pytest behavior, stdout/stderr diagnostic channels, and no
  cache/bytecode files. Verify red because the plugin module/options do not
  exist. (AC6-AC10, AC20, AC22)
- Update build-chain fakes first to require one child for each floor-bearing
  suite, exact thresholds, cwd, `_source_packages_env()`, list argv, `-q`,
  `-p no:cacheprovider`, Windows path handling, and fail-fast on low collection,
  collection error, and test failure. Verify red against the current two-child
  implementation. (AC6-AC11)
- Pin stream inheritance before changing either owner: the two desk Make
  commands contain no shell redirection or capture, and each real
  `_pytest_step_cwd` child passes neither `capture_output` nor `stdout`/`stderr`
  overrides. Separate mutation-shaped controls must each make the construction
  test red for: desk stdout redirection, desk stderr redirection, a desk stdout
  pipe, a desk stderr pipe, build-chain `capture_output=True`, build-chain
  `stdout=subprocess.PIPE`, build-chain `stderr=subprocess.PIPE`, and either
  channel changed to `subprocess.DEVNULL`. The low-floor diagnostic remains on
  stderr and ordinary pytest stdout remains visible. (AC9-AC11, AC14, AC19)
- Extend real-Make construction tests first to require the two plugin arguments
  on real desk runs, the two exact thresholds, preserved pack lines/order, and
  absence of all four `--collect-only` probes. Mutation-shaped Make/build-chain
  copies must make each assertion red. (AC5-AC11, AC14)
- `stub: true` — user approval forbids touching implementation-owned test files
  during PLAN, so these compilable pytest shapes are materialized verbatim as
  the first EXECUTE edit and then run red:

```python
# STUB: AC7-AC9 — an unmet floor fails before a body runs
def test_collection_floor_fails_before_test_execution(tmp_path):
    result = run_floor_pytest(tmp_path, collected=1, minimum=2, body_sentinel=True)
    assert result.returncode == 1
    assert "collected 1 test(s), expected at least 2" in result.stderr
    assert not result.body_sentinel.exists()


# STUB: AC6, AC10-AC11 — a floor-bearing build step owns exactly one child
def test_floor_bearing_build_step_runs_one_windows_clean_pytest_child():
    calls = collect_assimilate_primitive_subprocess_calls()
    assert len(calls) == 1
    assert calls[0].argv == EXPECTED_ONE_PASS_ARGV
    assert calls[0].cwd == EXPECTED_SUITE_CWD
    assert calls[0].env == expected_source_packages_env()
    assert calls[0].shell is False
```

**Approach:**

- Add the pure-stdlib plugin with documented options and
  `pytest_collection_modifyitems`; avoid a pytest import and any `sys.path`
  mutation.
- Replace `_pytest_step_cwd`'s captured probe branch with arguments appended to
  its existing real `subprocess.run`. Preserve return codes, label attribution,
  cwd, env, list argv, flags, and inherited stdout/stderr; do not carry the
  probe's capture settings onto the real child.
- Remove only the two Make shell probes and append the plugin/options to the two
  existing real desk commands.
- Refactor only after the focused red cases turn green; do not generalize into
  a runner or change unrelated pytest calls.

**Red-green-refactor evidence:** record the missing-option/current-two-child
red outcomes, the focused one-pass greens, and the final minimal diff with the
same tests held fixed.

**Done when:** all focused plugin, build-chain, Make construction, mutation,
deep-cwd, and Windows-shape tests pass; each suite's real plan contains one
pytest process and its exact floor; Wave A can stand alone with all 19/18
root/tool processes unchanged.

### T2: The five proven-compatible tool files share one explicit pytest process

**Depends on:** T1

**Touches:** `tools/test_local_ci_shared_test_deduplication.py`, `Makefile`

**Mode:** TDD — topology, membership, profile, and failure-injection tests
precede the single Make grouping edit.

**Tests:**

- Extend construction tests first to derive all explicit root/tool groups from
  the real macro and assert each approved pre-existing path appears exactly once
  in standalone, composed differs only by the Opp-1 workspace pair, no broad
  `tools/` exists, and process counts are 15/14. Removal, duplication, stale
  exclusion, and ambient-profile mutations must fail. Verify red against 19/18.
  (AC1-AC5, AC14, AC16-AC17, AC20)
- Pin the five-member class, all retained classes, unchanged pack process lines,
  and exact Opportunity-1 recursive/parallel ownership. A grouped failing test
  must fail its route with normal pytest attribution. (AC2-AC5, AC14, AC16,
  AC19)
- Re-run isolated and grouped non-empty collection, forward and reverse
  execution, three alternating focused rounds, watched path/resolution checks,
  and the controlled import-time mutator. Compare skip/xfail disposition and
  exact node union without a permanent giant snapshot. (AC4, AC12-AC15)
- Add a test-only, explicitly loaded characterization plugin used only by the
  focused candidate command. It snapshots cwd, selected environment keys,
  `sys.path`/`sys.meta_path`, watched `sys.modules` resolution, logging handlers,
  warning filters, catchable signal handlers, locale/timezone, asyncio policy,
  live non-daemon threads, `multiprocessing.active_children()`, and a designated
  temporary filesystem root at session start; it compares after collection and
  at each file boundary. The actual five-file class must finish with no
  unexplained delta: the sole `sys.path` allowlist is the exact repo-root plus
  consequent `tools/` pair characterized above, while package entries and
  resolution remain identical. (AC4, AC12-AC14)
- Prove that characterization is non-vacuous with temporary synthetic mutator
  modules, one channel at a time: environment, cwd, logging, warnings, a
  catchable signal, locale, timezone, asyncio policy, non-daemon thread,
  multiprocessing child, and designated filesystem entry. The timezone case
  changes `TZ` and calls `time.tzset()` where the platform exposes it; the
  environment half remains covered on Windows where `tzset` is absent. Each
  control must produce a named failure in the following file boundary. Existing import-path mutation separately
  covers `sys.path`, `sys.meta_path`, watched module resolution, and collector
  attribution. A child/process control uses bounded cleanup after the expected
  red result so the test itself leaves no orphan. (AC14, AC20, AC22)
- Inspect the five files for `atexit` registration, locale/timezone mutation,
  subprocess monkeypatching, module caches/registries, and filesystem writes
  outside pytest-managed or explicitly designated temporary roots. Where a
  public runtime snapshot is not available (`atexit`), pin absence by AST/source
  construction checks and a mutation-shaped source copy that adds the forbidden
  registration and must fail. (AC4, AC14)
- `stub: true` — materialize this compilable shape as the first T2 edit after
  approval; it is red while the Makefile still contains five processes:

```python
# STUB: AC1-AC5, AC16-AC17 — real root/tool topology is explicit and exact
def test_real_make_root_tool_groups_match_the_approved_profiles():
    standalone = collect_real_root_tool_pytest_groups("test-unleased")
    composed = collect_real_root_tool_pytest_groups("test-after-build-check-unleased")
    assert standalone.count == 15
    assert composed.count == 14
    assert standalone.node_paths == EXPECTED_STANDALONE_PATHS
    assert composed.node_paths == EXPECTED_STANDALONE_PATHS - WORKSPACE_STATUS_PAIR
    assert standalone.group_for(PROVEN_COMPATIBLE_FILES) == PROVEN_COMPATIBLE_FILES
    assert all(path_occurrences(path, standalone) == 1 for path in EXPECTED_STANDALONE_PATHS)
```

**Approach:**

- Replace only the five current singleton command lines with the explicit
  multi-line command in the compatibility section, at the location of the first
  member. Add a concise Make comment naming reordered/source-resolution evidence
  and the retained nested path guard.
- Keep all other root/tool and all pack commands in their current order. Keep
  `$(3)` unchanged so Opportunity 1 remains lexical and inspectable.
- If any post-edit order, mutation, or material-resource check fails, restore
  the five lines and retain all of Wave A.

**Red-green-refactor evidence:** record the 19/18 construction red, the 15/14
green, exact 58-node equivalence, both order outcomes, mutation-control red,
and post-change resource medians before any formatting-only cleanup.

**Done when:** the real Make profiles are 15/14 explicit root/tool processes,
all pre-existing nodes remain exactly once in their applicable route, the safe
class passes every approved characterization, and no retained boundary moved.

### T3: Public gates, measurements, documentation, and independent review converge

**Depends on:** T2

**Touches:** `docs/specs/local-pytest-process-optimization/spec.md`,
`docs/specs/local-pytest-process-optimization/plan.md`, `docs/specs/README.md`,
`workspace.toml`

**Mode:** goal-based check — `no stub (mode)`; this task records final evidence
and lifecycle state without adding runtime behavior.

**Tests:**

- Run participant and regression suites for build-chain, Opportunity 1,
  real-Make recursion/parallel construction, CI parity, Python interpreter
  selection, editable-install, worktree/lease behavior touched by the group,
  import-time path leaks, workspace ownership, and all five grouped files.
- Run relevant `make lint-ruff` and `make lint-mypy` gates.
- Run exactly one final `make test` and one final `SKIP_SAST=1 make ci`, record
  the existing incomplete-SAST verdict and any enterprise cleanup limitation
  without changing a gate. Run a full direct build-chain invocation only if
  focused tests and composed CI cannot establish changed behavior.
- Repeat the baseline method and report standalone/composed outer launches,
  floor probes and real processes, directly measured nested children,
  specialized children retained, node equivalence, median focused wall/CPU/RSS,
  full-run wall time, and uncertainty.
- Run adversarial review to adjudicated `Clean — ready to commit.`, then
  quality-engineer review to the same verdict; resolve all sustained in-scope
  findings through normal GATES/review re-entry.
- Finish with `git status --short`, `git diff --check`, and a residue scan for
  bytecode, pytest cache files, benchmark output, and generated artifacts.
  Empty directory shells that enterprise policy makes undeletable are reported
  precisely and are not mistaken for cache files.

**Approach:**

- Update AC checkboxes and lifecycle metadata only from recorded evidence.
- Keep the resolve-vs-surface disposition record with every reviewer finding
  applied, refuted by adjudication, or surfaced; no silent deferrals.
- Do not edit any implementation strategy after plan locking. A discovered
  strategy error returns to the human plan gate.

**Done when:** every applicable AC is checked, both reviewer roles are clean,
public gate outcomes and measurements are recorded honestly, protected files
are byte-unchanged, and the repository contains no task-created residue files.

## Rollout and rollback

This is a local orchestration change with no deployment, migration, flag, or
external dependency. Wave A and Wave B are separately reversible:

- **Wave A rollback:** restore the four probe-plus-run owners and remove the
  plugin/build-chain one-pass wiring. Wave B, if independently green, does not
  depend on the plugin.
- **Wave B rollback:** restore the five explicit singleton lines. Wave A remains
  valuable and valid.
- **Whole initiative rollback:** restore both command shapes and delete only the
  new plugin/tests/docs introduced here; no persisted runtime state exists.

An implementation discovery that requires test membership, workflow changes,
production-code compatibility edits, a general runner, an ADR, path-guard
redesign, or material performance acceptance stops at the human boundary.

## Final gate strategy

Use the least expensive evidence first: focused red tests, minimal Wave A,
focused greens, Wave B construction reds, minimal grouping, order/mutation and
resource checks, relevant lint/type gates, then Opportunity-1 regressions. Run
the two expensive public gates once at the end. Do not weaken terminal verdicts
or rerun cleanup-denied cases. The final report distinguishes test failures
from environment failures and never claims concurrency reduction; these
processes remain sequential within a normal gate.

## Files that must remain byte-unchanged

- `.github/workflows/**`
- `pyproject.toml`
- every pack/skill test file and conftest, and every pack process boundary
- `docs/specs/local-ci-shared-test-deduplication/spec.md` and its shipped plan
- `docs/adr/**`
- `tools/test_import_time_path_leaks.py`
- production subjects exercised by the safe class, including coordination,
  run-slot, worktree, frontend-runtime, and bootstrap implementations
- SAST/SCA and coordination policy files

## Rejected broader optimizations

- Global pack consolidation, pack namespace redesign, broad in-process
  build-gate conversion, pytest-xdist/background execution, bytecode caching,
  machine scheduling, daemons/process pools, and language rewrites are excluded.
- `tests/` joining a tool group is rejected for this initiative: exact
  collection alone cannot overcome the historical masked-failure defect and the
  bounded execution did not provide clean repeated evidence.
- The workspace-status pair stays separate because merging it would make the
  shipped composed exclusion harder to inspect and prove without saving a
  composed process.
- `test_run_slot.py` stays separate because a reversed real candidate run
  failed; a green forward order is insufficient.
- Every other singleton stays separate because cleanup denial, noncompletion,
  or uncharacterized durable state prevents a proof. A singleton is a valid
  final class.
- The import-time child stays because its broader surface and sanitized carrier
  contract have no exact simple replacement.

## Risks

- A plugin exception could mask a collection error. The design checks native
  collection failure state first, and tests distinguish error exit 2 from low
  floor exit 1.
- Plugin loading from deep cwd could alter rootdir or imports. Exact rootdir,
  config, cwd, environment, and resolution are asserted before migration.
- A grouped file could retain state that appears only under another order. Both
  orders, alternating repetitions, watched globals, and mutation controls are
  mandatory; any ambiguity restores the boundary.
- Process consolidation can increase resident memory. The explicit threshold
  protects against trading startup wins for material memory growth.
- Managed cleanup denial limits local execution assurance for retained classes
  and possibly final gates. It is reported as an environment limitation and is
  never repaired by changing tests.
- Adding construction nodes changes the total post-change node count. They live
  only in two already-owned files, are explicitly approved at this checkpoint,
  and do not change any pre-existing node identity or gate membership.

## Changelog

- 2026-08-26: Initial Drafting plan from the checked-out command topology,
  four-floor characterization, root/tool compatibility matrix, source-path
  mutation control, and focused resource measurements.
- 2026-08-26: Recorded the externally advanced local `origin/main` ref and the
  owner's explicit approval to complete on the unchanged, characterized
  `f871fe5` checkout before resynchronizing; scope and implementation strategy
  are unchanged.

# Plan: Header-derived dispatch and its replay

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - RFC-0106 D1 and D3; RFC-0105 D3; ADR-0110; RFC-0096 § 7; RFC-0055; ADR-0074.
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`:
    - `run_canonical_reconciliation(workspace, root, cooled)` (line 4734), the entry point the header registry is fed to;
    - `extract_spec_status`, the status reader;
    - `_cooling_module_path`, the confined sibling loader `dispatch.py` mirrors.
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`:
    - `_cooling_selection` and `_canonical_projection`, which resolve the cooled set and project the canonical lists;
    - `_explain_selector_targets`, which owns the selector forms.
  - `packs/core/.apm/skills/work-loop/SKILL.md` lines 168–195 at `95a8cc985`: the dispatch rules the base decision follows.
  - `packs/core/.apm/skills/close-work/scripts/cooling.py` (`_REQUIRED`, `validate_payload`, `enrol`) and `contracts/jsonschema/delivery-lifecycle-record.schema.json`.
  - `packs/core/tests/skills/workspace-status/test_depends_on_headers_equivalence.py`: the frozen-outcome and worktree-record pattern, and the cases this replay reuses.
  - `tools/compare-registry.py`: the run-once tool shape `tools/replay-dispatch.py` follows.

## Approach

The work has three parts: build, prove, then record. T2 adds the record field on its own, because it touches `close-work` and a published schema and is independent of dispatch. T3 builds `dispatch.py` over the unchanged engine. T4 and T5 run the replay over the case corpus and this repository. T6 writes the records, but only after the owner has approved each errata wording and the live difference list. The riskiest part is T4: if a dependency case does not reproduce, spec registration stays.

## Constraints

- Standard library only in every changed skill script (ADR-0074).
- No file under `packs/core/.apm/skills/workspace-status/` changes. `dispatch.py` reaches the engine only by a confined path load, with `sys.dont_write_bytecode` set first, so the load leaves no `__pycache__` behind.
- `make build-self` reprojects skills into `.claude/skills/` and `.agents/skills/`, and `cooling.py` into `packages/agentbundle/agentbundle/_data/`. Projections are never hand-edited.
- A commit that changes `packages/agentbundle/**` carries `Engine-Change-RFC: 0106`.
- `core` takes one patch bump in `pack.toml` and `.claude-plugin/plugin.json`, and its eval harness gains a case (`packs/AGENTS.md`). Shipped pack text cites no internal record.
- An accepted RFC changes only through § Errata (RFC-0055).
- Pack tests load a skill module under a unique name that includes pack and skill. They never put `scripts/` on `sys.path`.
- Every added file that names `workspace.toml`, `workspace-status` or `workspace_status` needs an inventory row.
- The brief stays `Executing` with this spec as an `Implementing` child. This spec's `Status:` and its `workspace.toml` entry move together, because spec registration still runs. During a controlled amendment the spec may sit at `Draft` while its entry stays in `work.active`, until re-approval returns it to `Implementing`.
- Base outcomes come from `git worktree add <tmp> 95a8cc985`. The worktree is removed afterwards.

## Construction tests

- **Live replay (T5):** `tools/replay-dispatch.py --root <worktree> --base-engine <worktree>/packs/core/.apm/skills/workspace-status/scripts/workspace_status.py` writes the four lists, the registry SHA-256, the lifecycle record count, and each differing spec with its differing fields. The author assigns each difference to a case and class by hand in the ledger, and the owner approves the list there.
- **Manual verification:** the owner's approvals in T5 and T6 are Ask-first gates, recorded in the ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Dispatch result and decision | T3 | `dispatch.py` and its docstring | AC-0001 to AC-0012 pass |
| Lifecycle record `parent` | T2 | the schema, `cooling.py`, `docs/lifecycle/README.md`, `close-work` SKILL.md | AC-0013, AC-0014, AC-0015 and AC-0025 pass |
| `workspace-status` unchanged | T2, T3 | no diff under the skill directory | AC-0016 and AC-0017 pass |
| Equivalence evidence and authority | T4, T6 | the replay suite, its fixture, the § Equivalence rows, the RFC-0106 errata | AC-0018, AC-0020, AC-0021 and AC-0022 pass |
| Live replay and approvals | T5, T6 | `notes/verification-ledger.md` | AC-0019 and AC-0022 pass |
| Inventory | T6 | `inventory.toml` rows | AC-0023 passes |
| Release history | T7 | changelog fragment and `core` bump | changelog and version gates pass |
| Delivery membership | T1 | Spec map row and `workspace.toml` entry | AC-0024 passes |

## Design (LLD)

### Interfaces & contracts

Owned by: T3

`dispatch.py --root <root> [--start <spec> | --resume <spec>]`. A selector takes the forms `_explain_selector_targets` accepts. Output is one JSON object with `schema_version` `1`. Exit codes:
- `0`: a result was printed, whatever the decision;
- `2`: a usage error, an invalid selector, a root that is not a real directory, or an unavailable engine.

Standard output and standard error are reconfigured to UTF-8 before the first print. Findings keep the engine's keys, so the readiness bridge can re-point to this output in the stop's release without a new finding table.

### Component / module decomposition

Owned by: T3

- `dispatch.py` holds five things: the confined engine load, the `workspace.toml` read, header-registry synthesis, the ready/active/blocked projection, and the decision and output.
- The projection is `dispatch.py`'s own. It applies `_canonical_projection`'s three predicates to `run_canonical_reconciliation`'s evaluations, because that function re-reads `workspace.toml` from disk and cannot take an in-memory registry. In the stop's release it becomes the projection `work-loop` dispatches from. The replay checks it against the base projection.
- Status, metadata, readability, dependency settlement, cycles, child scope and cooling are all the engine's. They come from calling `run_canonical_reconciliation` and the same cooled-set resolution `workspace-status reconcile` uses. The exact public or private seam for that resolution is `implementation-discovered`. Its kill condition: if reaching it needs an engine edit, stop and return to the owner.
- The engine itself loads `close-work`'s `cooling.py` as it does today.

### Behavior & rules

Owned by: T3

- **Why the header registry.** Feeding the unchanged engine a registry built from headers alone keeps every rule in one owner. The differences that remain come only from what the registry used to supply, and the replay is the measure of those. A probe on 2026-10-28 fed such a registry to the base engine over this repository:
  - it gave 0 ready and 3 active specs, against canonical's 0 and 2;
  - the third active spec is the unregistered `plan-evolution-experiments`;
  - its only blocked items were 45 `work.shipped` evaluations, which AC-0003 leaves out.
  - A second probe on 2026-10-29 used this plan's registry, which keeps every entry except the 237 repo-origin spec entries with empty `needs`. It gave the same 0 ready and 3 active specs, with no finding on any `work.queue` or `work.active` evaluation.
- **Why start from the real registry.** The header registry is exactly the registry the registration stop leaves behind: every entry except repo-origin spec entries with empty `needs`. So tracker-origin entries keep their initiative and its status, unmigrated `needs` and captured-item entries are refused per entry as today, and nothing needs a special case. The replay then measures the stop's real end state.
- **Added initiative and summaries.** The added memberships need a valid initiative slug and a `summary` on each entry to pass the engine's schema checks. `dispatch.py` takes the highest `ini-NNN` slug, from `ini-999` down, that matches the engine's `^ini-\d{3}$` and that no kept initiative uses, and uses the spec's title as the summary. Neither reaches the output. If every slug is taken, AC-0010 refuses the run.
- **Status and parent** come from `_metadata_from_root`, the same reader `evaluate_dispatch` compares against. So an added membership never earns `provenance_mismatch` or `impossible_transition` from its own headers.
- **Cooled specs.** These come from the lifecycle records the engine's cooled-set resolution returns, never from a spec body. A named start or resume of one is refused from the record alone.
- **The `workspace.toml` read.** The file is read once through work-loop's co-located `file_safety.read_confined_regular_file`, and when it is absent nothing is read. `docs/specs/` is checked with the same module's `validate_confined_directory` and listed once, with a listing error giving the Spec file term's single `docs/specs` finding, and each entry is checked on its own with that function, so one bad entry never refuses the others. `dispatch.py` loads that module as a sibling under AC-0012's rule.
- **The engine load** mirrors `_cooling_module_path` and `_load_cooling_module`: the layout predicate, resolve-and-confine, a unique module name, and fail-closed on any load error.

### Data & schema

Owned by: T2

- **Where `parent` goes.** It joins the schema's `properties` and `cooling.py`'s optional keys beside `exception`.
- **Unchanged parts.** The `required` list and `contract_version` do not change. `x-spec` is not extended, because a roster test pins its exact list.
- **How `enrol` derives it.** `enrol` reads the spec's preamble through `close-work`'s confined reader before it writes, so a cooled body is never read after cooling.

### Design decisions

Owned by: T3, T4

- **No skill dispatch changes here.** `work-loop` switches to `dispatch.py`, and the bridge re-points, in the registration stop's release. Each contract that names registry dispatch or registry writes is amended in the release that changes it (RFC-0106 D1).
- **No rule moves in this spec.** Slice 9 moves what `dispatch.py` still needs when it shrinks `workspace-status` to the repair. `work-loop` already depends on `workspace-status` for dispatch, so this adds no new dependency.
- **The base decision** lives in the replay suite. It transcribes SKILL.md lines 168–195 at `95a8cc985`, every branch included:
  - **Named start.** It passes only when the path has a matching `canonical.ready` evaluation and no matching `canonical.blocked` or `canonical.findings` entry. Otherwise it refuses with the matching finding, or with `unregistered_work` when no canonical evaluation exists.
  - **Named resume.** The same rule against `canonical.active`.
  - **Argless start or resume.** One active spec is resumed, and several active specs are listed with a question. With no active spec, the first `canonical.ready` item is started unless a matching `canonical.blocked` or `canonical.findings` entry blocks it, in which case the decision is a refusal with that finding. No item at all gives `none`.
- **Expected classes.** The replay confirms or refutes each of these:
  - The unregistered Approved and Implementing specs are removals under RFC-0106 D1.
  - Several ready specs is a removal under RFC-0106 D3.
  - These each need an errata entry, because their fact's home is the header:
    - `impossible_transition`, `duplicate_membership`, `configuration_mismatch` and `provenance_mismatch` on a repo-origin entry the header registry drops;
    - the inactive initiative;
    - the bare `**Status:**` spec;
    - the registry-settled dependencies.
  - The three tracker-origin cases, both unmigrated-content cases, and the `unsupported_legacy` and aliasing legacy cases are expected to reproduce, because their entries are kept and the aliased spec gets no added membership.
  - The other dependency cases, and the cooled child with a declared parent, are expected to reproduce. The cooled child whose record predates `parent` is expected to be stricter, because it fails closed.

## Tasks

### T1: Delivery membership and the ledger

**Depends on:** none

**Mode:** goal-based

**Tests:**
- Criteria: AC-0024.
- After approval, one commit does three things: adds `header-derived-dispatch` to the brief's Spec map, moves this spec's `Status:` to `Implementing`, and adds its `workspace.toml` entry to `work.active`.
- `notes/verification-ledger.md` is created with sections for the live replay and the owner's approvals.

**Done when:** `lint-brief-coverage.py` and the inventory check pass.

### T2: The lifecycle record's `parent`

**Depends on:** T1

**Mode:** TDD

**Tests:**
- Criteria: AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0025.
- A new `packs/core/tests/skills/close-work/test_cooling_parent.py` checks each `parent` value against `validate_payload`: absent, `none`, a brief path, `brief:<slug>`, a nested path, `..`, upper case, a non-string, and an oversized value. It reads nothing above the pack.
- The same file checks `enrol` over:
  - planted spec files with each `Brief:` form;
  - a `Brief:` naming a missing brief file, and one naming a brief file whose name AC-0013's pattern refuses;
  - a missing, unreadable and symbolic-link spec file;
  - a non-spec locator.
- A new `tests/roster/test_cooling_parent_schema.py` validates the same values against the JSON Schema with the declared `jsonschema` tool dependency. It asserts that `validate_payload` and the schema agree on each value. The test gains its `build-check.yml` step and `STEP_DISPOSITION` entry (`tests/AGENTS.md`).
- The same file round-trips a record carrying `parent` through every function AC-0025 lists, and compares the `parent` value and `canonical_bytes` before and after each.
- `test_ac23_pinned_files_are_byte_unchanged` re-pins the two digests under a dated comment naming this spec, after the owner's OK, which is recorded in the ledger. The rest of both cooling roster suites is unchanged.

**Done when:** the new suite and both roster suites pass, and `git diff --exit-code 95a8cc985 -- packs/core/.apm/skills/workspace-status/` is clean.

### T3: `dispatch.py`

**Depends on:** T2

**Mode:** TDD

**Tests:**
- Criteria: AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012.
- A new `packs/core/tests/skills/work-loop/test_dispatch.py` loads `dispatch.py` under a unique name, from a planted skills tree that also holds the engine. It plants:
  - one spec for each status word, a bare `**Status:**` spec, a symbolic-link `spec.md`, a FIFO `spec.md`, a spec directory that resolves outside `docs/specs/`, a symbolic-link directory aliasing another spec, and `docs/specs/README.md`;
  - an unreadable plan, and an out-of-root plan symbolic link;
  - a dependency of each kind;
  - a cooled spec with each `parent` form, named by `--start` and `--resume`;
  - zero, one and several ready and active specs, with directory names chosen so that discovery order differs from sorted order;
  - a `workspace.toml` with spec entries in shuffled collections, compared byte for byte against the same tree without the file;
  - a `workspace.toml` that is malformed, a symbolic link, or unreadable;
  - kept entries of each kind: tracker-origin under an active and an inactive initiative, a non-empty `needs`, an unmigrated captured item, and legacy `spec/<slug>` and `{slug = ...}` entries aliasing a spec;
  - a kept initiative already named `ini-999`;
  - an unreadable regular `spec.md`, named and unnamed by a kept entry;
  - an engine path that is missing, one that is a symbolic link out of the skills tree, an engine whose import raises, one lacking `run_canonical_reconciliation`, and a `dispatch.py` outside a `scripts` directory under `skills`;
  - a `docs/specs/` symbolic link leaving the root, a dangling `docs/specs/` link, an absent `docs/specs/`, an unlistable `docs/specs/`, a symbolic-link child `docs/specs/linked` beside a valid sibling that still dispatches, and a symbolic-link `docs/specs/README.md` that gives no finding;
  - a missing work-loop `file_safety`, and one lacking `read_confined_regular_file`;
  - a `workspace.toml` over 8 MiB, one with two links, and spec entries whose `needs` is missing, `""` or `{}`, each kept;
  - a named start and resume of a spec a legacy entry aliases, and of one a non-array `needs` entry names, asserting `unsupported_legacy` and `invalid_entry`.
- A spy on file opens asserts no cooled body is read. A snapshot of `(path, bytes, mtime_ns)` for every path under the root asserts AC-0007.

```python
# stub: true
def test_several_ready_specs_ask_and_never_pick(tmp_path):
    repo = _plant(tmp_path, ready=["b-spec", "a-spec"])
    decision = run(repo)["decision"]
    assert decision["action"] == "ask"
    assert decision["candidates"] == ["docs/specs/a-spec/spec.md", "docs/specs/b-spec/spec.md"]
```

**Done when:** the new suite passes and `make lint-ruff lint-mypy` passes.

### T4: The case replay

**Depends on:** T3

**Mode:** TDD with frozen fixtures

**Tests:**
- Criteria: AC-0018.
- `test_header_derived_dispatch_replay.py` loads `test_depends_on_headers_equivalence.py`'s `CASES` by path under a unique name, and adds the further cases AC-0018 lists.
- With `HEADER_DISPATCH_BASE=<worktree>` and `HEADER_DISPATCH_RECORD=1`, the suite runs the worktree's `workspace_status.py reconcile` per case and records `expected.json` once. Without them, it compares.
- The classification table is keyed by `(case, spec path, field)`.

**Done when:** the suite passes, and every `accepted removal` entry that needs an errata entry is on T6's list for the owner.

### T5: The live replay

**Depends on:** T3

**Mode:** manual QA

**Tests:**
- Criteria: AC-0019.
- `tools/replay-dispatch.py` exits `0` when it has written its lists, and `2` on a usage error or an unreadable root. It never classifies.
- `tools/test_replay_dispatch.py` covers both exit codes over planted trees. It joins the Makefile `tools/` suite line beside `tools/test_compare_registry.py`, with the same `NO_PR_GATE` disposition in `tools/lint-ci-parity.py`.
- The run's output, the by-hand classification, and the owner's approval go into the ledger.

**Done when:** the ledger holds the run, every difference is classified, and the owner has approved the list.

### T6: Errata, equivalence rows and inventory

**Depends on:** T4, T5

**Mode:** goal-based

**Tests:**
- Criteria: AC-0020, AC-0021, AC-0022, AC-0023.
- Each errata entry is shown to the owner. Its case, the approval and the approval date go into the ledger before the commit that adds the entry.
- The `workspace-retirement` roster check and `tests/roster/test_workspace_retirement_inventory.py` pass.

**Done when:** both checks pass, and every slice-8 row's authority resolves.

### T7: Closeout

**Depends on:** T2, T3, T4, T5, T6

**Mode:** goal-based

**Tests:**
- `core`'s patch bump and changelog fragment pass the version and changelog gates.
- A `core` eval case covers enrolment writing `parent`.
- `make build-self` leaves no diff, and `make lint-ruff lint-mypy` passes.
- The PR dispatches `test-roster.yml` and `test-corpus.yml`.

**Done when:** every spec criterion is checked, the adversarial review is clean, and the PR is open.

## Rollout

One `core` patch release, with two effects:
- `close-work`'s `enrol` starts filling `parent` on a spec's lifecycle record, which also meets ADR-0110's first revisit trigger. ADR-0110 is amended in the registration stop's release, when dispatch reads the field.
- `dispatch.py` ships with no caller.

Older records stay valid, and rollback is a revert.

## Risks

- **A dependency case does not reproduce.** Spec registration then stays, and the owner decides the next step.
- **An errata entry could be written just to make the replay pass.** Each removal is an Ask-first owner decision, and the replay names every one.
- **The private seam for cooled-set resolution can change.** `dispatch.py` and the engine ship in one pack, and T3's suite reds on a change.

## Changelog

- Drafted 2026-10-28.
- Approved 2026-10-29 by eugenelim with the spec.
- Spec re-approved 2026-10-29 by eugenelim after the pre-EXECUTE reviews.
- Plan re-approved 2026-10-29 by eugenelim with the spec.
- Spec re-approved 2026-10-29 by eugenelim after the AC-0021 controlled amendment.
- Plan re-approved 2026-10-29 by eugenelim after the AC-0021 controlled amendment.

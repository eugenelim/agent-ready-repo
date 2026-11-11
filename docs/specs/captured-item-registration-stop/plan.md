# Plan: Captured items stop being registered

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - RFC-0106 D1 and D3; RFC-0105 D3; ADR-0053 D9; RFC-0063 D9; RFC-0083 § 6 and § 8; RFC-0055; ADR-0074.
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`: `parse_captured_item`, `read_captured_item`, `_dependency_is_satisfied`, `_resolve_header_item`, and `_dependency_terminal_satisfied`.
  - `packs/core/tests/skills/workspace-status/test_captured_item_files_reader.py` and `test_captured_item_files_equivalence.py`: the planted-file style and the `_write_repo` and `observe` helpers.
  - `packs/core/.apm/skills/work-intake/scripts/intake_router.py`: `route_intake` and `_START_ROUTES`; `scripts/intake_transaction.py`: `run_intake_transaction`.
  - `tests/roster/test_captured_item_files_instructions.py`: the closed-file-list instruction check this spec's roster check follows.
  - `docs/specs/workspace-retirement/`: the record and inventory this slice amends.

## Approach

Record first. T1 runs the registry comparison and writes it to the ledger before any writer text changes, because FEAT-0034's validation hook keeps registration if it fails. The engine change follows in T2: the grammar rule and the dependency rule for an unregistered captured item, so the files writers create from T3 on already have a working closed state. T3 changes the router and the eval matrices that pin it. T4 changes the writer, guide, and promise text. T5 commits the four errata entries only after the owner approves each wording. T6 amends the `workspace-retirement` spec, then writes the equivalence rows and the inventory edits. T7 closes out. The riskiest part is T4's breadth: about twenty files across six packs, the guides, and the web content, each of which also describes intent, brief, or spec registration that must stay unchanged.

## Constraints

- Standard library only in every changed skill script (ADR-0074).
- `make build-self` reprojects the engine into `packages/agentbundle/agentbundle/_data/` and each skill into `.claude/skills/` and `.agents/skills/`. Projections are never hand-edited.
- A commit that changes `packages/agentbundle/**` carries `Engine-Change-RFC: 0106`, as the build-check curation guard enforces.
- `core`, `product-strategy`, `product-engineering`, `atlassian`, `github`, and `linear` each take one patch bump in `pack.toml` and `.claude-plugin/plugin.json`, and each changed skill's eval harness gains or updates a case (`packs/AGENTS.md`).
- Shipped pack text states its rules directly and cites no internal record (`packs/AGENTS.md`). The ADR and RFC errata stay in `docs/`.
- None of the five non-core packs has a scoped `AGENTS.md`; `packs/AGENTS.md` and the root file govern them. T4 rechecks for one before editing.
- `guides/` pages follow `guides/AGENTS.md`'s job-page rules and keep `title` equal to the H1.
- A `docs/specs/<slug>` literal in a new roster test is added to `.workspace-prune-protected.toml`.
- Every file this change adds or edits that mentions `workspace.toml`, `workspace-status`, or `workspace_status` outside an inventoried skill or spec directory needs an inventory row; this spec's directory gets one `docs/specs/captured-item-registration-stop/*` `contract` row at owner 3.

## Construction tests

- **Live comparison (T7):** the engine from a `git worktree` of `dd4f7038c` under `.context/` and the head engine each run `status` over the implementing head's tree. A scratch script compares the AC-0019 fields, and the result goes into `notes/verification-ledger.md`.
- **Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| File grammar and closed state | T2, T3, T4 | the engine rule and transaction; `work-intake` SKILL.md and the schema guide | AC-0001, AC-0011, and AC-0020 pass |
| Contracts that required registration | T5 | ADR-0053, RFC-0063, and RFC-0083 errata entries | AC-0015 passes |
| Equivalence evidence and authority | T5, T6 | RFC-0106 errata entry; § Equivalence rows | AC-0016 and the amended `workspace-retirement` check pass |
| Inventory | T6 | `inventory.toml` edits | AC-0017 passes |
| User documentation | T4 | the pages the spec's user-documentation row lists | AC-0011 and AC-0014 pass; review for the generic route text |
| Cross-pack contract | T3, T4 | skill, reference, example, eval, and promise edits | AC-0010, AC-0012, and AC-0014 pass |
| Comparison record | T1 | `notes/verification-ledger.md` | AC-0018 passes |
| Release history | T7 | a changelog fragment and six version bumps | the changelog and version gates pass |
| Delivery membership | T7 | the Spec map row and the `workspace.toml` entry | `lint-brief-coverage.py` passes |

## Design (LLD)

### Data & schema

Owned by: T2

The grammar changes one rule. In `parse_captured_item`, `Resolution:` is required exactly when `Status:` is `Closed`, for every kind, where it was required only for a closed defect. Its value set stays `fixed`, `declined`, and `superseded`. The rule reaches registered records too, because `_captured_record_metadata` reads them through the same parser. Every file in this repository is `Open`, so none changes validity. In the equivalence suite, the `closed-record-in-shaping-backlog` and `closed-record-in-shaping-active` cases plant a registered `Closed` design record with no `Resolution:`; each gains `Resolution: fixed` so it keeps pinning `impossible_transition`. The `captured-to-file` repair copies a `Closed` source's `Resolution:` and refuses a planned record that does not read back as valid, so with no repair code change a `backlog.closed` design source with no `Resolution:` becomes a manual finding, and one carrying `Resolution: fixed` now migrates where it was refused.

### Behavior & rules

Owned by: T2

`_resolve_header_item` already decides, before satisfaction runs, an unregistered captured path that is spelled other than canonically, is unreadable, or has no captured `Kind:`. It passes a missing or unconfined path through with an empty kind, and `_dependency_is_satisfied` then gives `missing_dependency` or settles it by a completion receipt. All of these stay as at `dd4f7038c` (AC-0005). `_dependency_is_satisfied` gains one branch, taken only when no membership names the dependency path, the path spells a captured-item file canonically, the file is not cooled, and the resolved kind is non-empty, so a missing or unconfined path never reaches it. It reads the file once through `read_captured_item`. A valid, `Closed`, `Resolution: fixed` file satisfies. A valid file in any other state gives `unsatisfied_dependency`. An invalid or unreadable file gives the finding `read_captured_item` returns. The branch sits after the existing unmigrated-membership and structural-block checks and before the defect branch, so the defect branch and the probe below it run only for a registered item or a path outside the captured-item directory. Every membership-based rule and the cooled-file branch keep their current order and outcome, which AC-0007's frozen fixtures check.

Today's outcome for the unregistered case was probed at `dd4f7038c` with the equivalence suite's `_write_repo` and `observe` helpers: a `Closed`, `Resolution: fixed` defect, an `Open` defect, and a `Closed` design or intent each gave `unsatisfied_dependency` on the item path, and a `Closed` design carrying `Resolution: fixed` gave `invalid_captured_item`.

### Interfaces & contracts

Owned by: T3

`route_intake` keeps its signature. The `remember` branch returns membership `none` and mutation `materialize-draft-non-dispatchable` when `artifact_kind` is `defect`, `design`, or `research`; every other kind keeps `backlog.open` and `materialize-draft-and-register-non-dispatchable`. `_START_ROUTES["defect"]` becomes membership `none` with processor `bug-fix` and mutation `materialize-and-dispatch`. The evaluator that turns a route into the matrices' `dispatchable`, `result_code`, and `next_action` fields is found by searching for the matrix's `contract_version` string and the `lifecycle_membership` key under `tools/` and `packs/core/tests/`. If that evaluator derives dispatchability from membership alone and cannot express a dispatchable defect with membership `none`, T3 stops and asks the owner rather than adding a membership value. The defect case's `artifact` in each matrix moves from `docs/product/defects/login-timeout.md` to `docs/product/captured/login-timeout.md`.

`run_intake_transaction`'s `register_workspace_entry` becomes optional, defaulting to `None`. With `None`, the transaction takes the lock, materializes, releases, and dispatches, with no registration stage and no registration rollback. Every existing caller passes it, so their behavior is unchanged.

### Design decisions

Owned by: T4

- `work-intake` SKILL.md § Terse workspace capture and the schema guide's captured-item section state the closed-state grammar, with `Resolution:` on every `Closed` item, and the rule that closing a registered item deletes its entry. SKILL.md § 5 states that a route whose mutation does not register writes no entry and calls the transaction with no registration step.
- Text that describes the generic remember or start route, in `guides/core/how-to/capture-work.md`, `guides/_shared/how-to/use-work-intake.md`, both `work-intake-routing-and-lifecycle.md` references, and `packs/core/DESIGN.md`, keeps its intent, brief, and spec registration and says that a defect, design, or research item is written as its own file with no entry.
- An existing registered captured item stays registered until the brief's slice 9. Closing it deletes its entry in the same change as its file's `Status:` edit, so no closed item sits in `backlog.open`, and the deletion keeps deferral anchors behaving as today's move to `backlog.closed` does.
- `run-okr-cascade` drops its initiative-resolution step, because the step only chose which shaping queue to append to.
- `frame-situation` and `diverge-solutions` keep suggesting a captured item, now as the file alone, and keep directing the user to `work-intake` to write it.

## Tasks

### T1: The registry comparison is recorded with no failing row

**Depends on:** none

**Mode:** goal-based

**Tests:**
- Criteria: AC-0018.
- `python3 tools/compare-registry.py --root .` runs on this spec's branch before T3 and T4. Its full output, exit code, commit, and `git merge-base HEAD origin/main` go into `notes/verification-ledger.md`.

**Done when:** the ledger holds the run and its exit code is `0`. A non-zero exit stops the plan for the owner.

### T2: The grammar and the closed state

**Depends on:** T1

**Mode:** TDD

**Tests:**
- Criteria: AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007.
- A new `packs/core/tests/skills/workspace-status/test_captured_item_registration_stop.py` loads the engine under a unique module name and plants one file per case with the equivalence suite's repository shape: a waiter whose `Depends on:` names an unregistered file that is `Closed` `fixed`, `declined`, or `superseded`, for each of the four kinds; `Open`; invalid; a symlink; and cooled. A spy on reads asserts the cooled file is never opened.
- The same file asserts AC-0006 by running `status` over a repository holding one valid unregistered file per kind, with and without `Type:`, in each status.
- `test_captured_item_files_reader.py`'s `test_resolution_on_closed_non_defect_is_invalid` and `test_closed_non_defect_needs_no_resolution` are inverted to AC-0001's rule. A case for `Open` with a `Resolution:` line for each non-defect kind is a regression pin, since that case is already invalid at `dd4f7038c`.
- The equivalence suite's two `closed-record-in-shaping-*` cases gain `Resolution: fixed` and keep their `impossible_transition` result.
- `test_captured_item_files_repair.py` gains two cases: a design note `Closed` in `backlog.closed` with no `Resolution:` gives the planned-record manual finding, and one carrying `Resolution: fixed` migrates.
- AC-0005's cases run against the engine at `dd4f7038c` once and are pinned as literals: a variant spelling, a symlink, an unreadable file, a file with no captured `Kind:`, and a missing file with and without a completion receipt.
- AC-0006's missing-target and cycle cases are pins of the accepted removal: they pass at `dd4f7038c` too.
- AC-0007 is checked by `git diff --exit-code dd4f7038c --` on the three fixture files and by the suites that read them passing.

```python
# stub: true
def test_unregistered_closed_fixed_design_satisfies(tmp_path):
    path = "docs/product/captured/loose.md"
    case = Case("p", {path: _note("design", "Closed", "fixed")}, (), depends_on=path)
    _write_repo(tmp_path, case)
    assert observe(tmp_path) == {"findings": [], "dispatchable": {WAITER: True}}
```

**Done when:** the new suite, the reader, repair, and equivalence suites, and the dependency-header suites pass, and the packaged engine copy matches the source after `make build-self`.

### T3: The router and its eval matrices

**Depends on:** T2

**Mode:** TDD

**Tests:**
- Criteria: AC-0008, AC-0009, AC-0010, AC-0020.
- `packs/core/tests/skills/work-intake/test_intake_transaction.py` gains a no-registration case over a fixture repository: the artifact is written, the processor is dispatched, the lock file is gone afterwards, and `workspace.toml` bytes are unchanged; the existing cases pass unchanged.
- `packs/core/tests/skills/work-intake/` gains a router test asserting the two changed routes and, for every other case in the core routing matrix, the `Route` the router returned at `dd4f7038c`, captured once into the test as literals.
- The core routing matrix's defect case, and the defect case of each of the four tracker intake matrices, change only `lifecycle_membership`, `mutation`, `artifact` wherever the case carries it (in `routing_signals` and in `expected_route`), and any field the evaluator derives from them. The existing matrix comparison suites in `packs/core/tests/pack/test_work_intake_surface.py`, `tests/roster/test_shaping_intake_handoff_matrix.py`, and each tracker pack's eval tests pass.

**Done when:** the router test and every matrix comparison suite pass.

### T4: Writers, suggesters, guides, and promise pages

**Depends on:** T2

**Mode:** goal-based

**Tests:**
- Criteria: AC-0011, AC-0012, AC-0014.
- A new `tests/roster/test_captured_item_registration_stop.py` asserts AC-0011's closed list, line rules, and phrases, AC-0012's names, and AC-0014's phrases over its list. Its spec-path literal goes into `.workspace-prune-protected.toml`.
- `tests/roster/test_captured_item_files_instructions.py` still passes.
- `tests/roster/test_captured_item_registration_stop.py` gets a named step in `.github/workflows/build-check.yml` above the bulk tests step, and a `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py`, as `tests/AGENTS.md` § Roster steps requires.
- Each changed skill's `evals/evals.json` case that names registration of a captured item follows the new text; `run-okr-cascade`, `frame-situation`, `diverge-solutions`, `work-intake`, and `work-loop` eval suites pass.
- Any anchor-hash test over a changed `SKILL.md` section, such as `tools/test_workspace_status.py`, is updated in the same commit as the text.

**Done when:** the new roster test, the captured-item instruction test, each changed skill's eval suite, `tools/lint-ci-parity.py`, and the inventory test pass.

### T5: The errata entries, with owner-approved wording

**Depends on:** T1

**Mode:** manual QA

**Tests:**
- Criteria: AC-0015, and the RFC-0106 entry AC-0016's intended-change and accepted-removal rows cite.
- Each entry's wording is shown to the owner and committed only as approved. The ADR-0053, RFC-0063, and RFC-0083 entries each name the passages AC-0015 lists for them, and replace D9's shaping-queue entry with a `Kind: intent`, `Type: strategy` file under `docs/product/captured/` and no registration where D9 applies. The RFC-0106 entry authorises `the closed captured item of another kind` as an intended change and `the unregistered captured item's own dependencies` as an accepted removal.
- `tests/roster/test_captured_item_registration_stop.py` asserts AC-0015's names in each ADR and RFC entry.

**Done when:** each of the four entries carries the owner's approval in the ledger, and the roster assertion passes.

### T6: The retirement record and the inventory

**Depends on:** T2, T4, T5

**Mode:** goal-based

**Tests:**
- Criteria: AC-0016, AC-0017.
- The `workspace-retirement` spec is amended through the controlled-amendment path, with fresh owner approval: its closed list of intended-change cases adds `the closed captured item of another kind`, its real-record and build-step criteria reopen, and its plan gains a task naming this change.
- `retirement-record.md` § Equivalence gains AC-0016's four rows, each naming this spec's test files as Evidence.
- `inventory.toml` re-owns or removes each owner-3 row: a row whose consumer this stop disposes gets its new class and consumer text or is removed when its file no longer mentions the registry; a row this stop does not dispose, such as the initiative and transition suggestions of `lean-canvas`, `map-capabilities`, and `place-bet` and the tracker refresh coordinator, moves to the slice that disposes it. `docs/specs/captured-item-files/*` keeps owner 3, and this spec's directory row is added.
- `tests/roster/test_workspace_retirement_inventory.py` passes.

**Done when:** the inventory test passes against this repository and the amended `workspace-retirement` spec carries the owner's re-approval.

### T7: Closeout

**Depends on:** T3, T4, T6

**Mode:** goal-based

**Tests:**
- Criteria: AC-0019.
- The live comparison in Construction tests passes and is recorded in the ledger.
- `docs/specs/captured-item-files/spec.md`'s status line reads `Shipped (superseded in part by …)`, naming AC-0001's `Resolution:` bullet, and `lint-spec-status.py --root .` passes.
- The brief's Spec map gains `captured-item-registration-stop`; this spec's `workspace.toml` entry moves with its `Status:`; `lint-brief-coverage.py` passes.
- A changelog fragment from `tools/changelog.py new` names the stop and the closed-state rule; each of the six packs takes its patch bump; the changelog and version gates pass.

**Done when:** every listed gate passes and the ledger holds the live comparison.

## Rollout

- **Delivery:** one pull request, merged by the owner.
- **Reversal:** revert the pull request. No registry entry or captured-item file changes, so reverting needs no migration.

## Risks

- **Writer text also covers intent, brief, and spec registration.** An edit that drops a captured-item sentence can drop a neighbouring rule slices 7 and 8 still need. T4's review reads each changed paragraph whole.
- **The tracker evaluator may tie dispatchability to membership.** T3's discovery stop covers it.
- **The deletion-on-close rule is instruction-only.** Nothing mechanical deletes the entry, so a maintainer who closes a registered item and forgets gets the existing `impossible_transition` finding, which names the entry.

## Changelog

- 2026-10-27: spec approved by eugenelim
- 2026-10-27: plan approved by eugenelim

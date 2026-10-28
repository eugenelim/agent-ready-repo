# Plan: Intents and briefs stop being registered

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - RFC-0106 D1; RFC-0105 D3; RFC-0064; RFC-0083 § 6 and § 8; ADR-0119 D4; ADR-0134 D4; ADR-0110; RFC-0055; ADR-0074.
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`: `_VALID_OPERATION_TYPES`, the `needs-to-header` and `captured-to-file` plan and apply sections, and the legacy-migration apply path.
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`: `_brief_child_spec_states`, `_brief_child_scope_is_valid`, `_dependency_is_satisfied`, `_dependency_metadata_safety_finding`, `_structural_findings`, `_legacy_canonical_alias`, and `migration_candidate_routes`.
  - `packs/core/.apm/skills/work-intake/scripts/intake_router.py` (`_START_ROUTES`, `_UNREGISTERED_KINDS`, the remember and ready-brief branches), `intent_rename_request.py` (`_count_registry_matches` and the `source-unregistered` refusal), and `intent_rename.py` (`_registry_state`, `_workspace_transition`, `_merge_backward_workspace`, and the stage check that refuses `registry-ambiguous`).
  - `packs/core/tests/skills/workspace-status/test_depends_on_headers_repair.py` and `test_captured_item_registration_stop.py`: the planted-repository style this plan's tests follow.
  - `tests/roster/test_captured_item_registration_stop.py`: the closed-file-list instruction check this spec's roster check follows.
  - `docs/specs/workspace-retirement/`: the record and inventory this slice amends.

## Approach

Record first. T1 runs the registry comparison and writes it to the ledger before any writer text or entry changes, because FEAT-0034's validation hook keeps registration if it fails. T2 makes the engine safe for an unregistered intent or brief before anything removes one: the cooled-child rule and the child-state check on an unregistered brief, without which removing entries would open work that is blocked today. T3 adds the repair step. T4 changes the router and the rename. T5 changes the instruction text. T6 commits the governance wording only after the owner approves each. T7 runs the repair on this repository, with the owner's sight of the plan file. T8 amends the `workspace-retirement` spec and writes the equivalence rows and inventory edits. T9 closes out. The riskiest part is T4's rename change: the transaction has forward, rollback, and recovery paths that each assume one registry entry.

## Constraints

- Standard library only in every changed skill script (ADR-0074), apart from `tomlkit`, which `repair-apply` already uses under its declaration in `packs/core/AGENTS.md`.
- `make build-self` reprojects the engine and `workspace_status.py` into `packages/agentbundle/agentbundle/_data/` and each skill into `.claude/skills/` and `.agents/skills/`. Projections are never hand-edited.
- A commit that changes `packages/agentbundle/**` carries `Engine-Change-RFC: 0106`, as the build-check curation guard enforces.
- `core` takes one patch bump in `pack.toml` and `.claude-plugin/plugin.json`, and each changed skill's eval harness gains or updates a case (`packs/AGENTS.md`). No other pack's content changes; `web/src/content/packs/` is site content, not pack content.
- Shipped pack text states its rules directly and cites no internal record (`packs/AGENTS.md`). The errata and amendments stay in `docs/`.
- An ADR's prose is frozen after acceptance; only its connection fields and `## Errata` change (`new-adr`). An accepted RFC changes through § Errata (RFC-0055). An intent records a change as a dated owner amendment paragraph; the owner decided on 2026-10-27 that these three need no re-acceptance review.
- `guides/` pages follow `guides/AGENTS.md`'s job-page rules and keep `title` equal to the H1.
- A `docs/specs/<slug>` literal in a new roster test is added to `.workspace-prune-protected.toml`.
- Every file this change adds or edits that mentions `workspace.toml`, `workspace-status`, or `workspace_status` outside an inventoried skill or spec directory needs an inventory row; this spec's directory gets one `docs/specs/intent-brief-registration-stop/*` `contract` row at owner 7.
- The brief's Spec map row and this spec's `workspace.toml` entry are added together, and the brief stays `Executing` with this spec as an `Implementing` child.

## Construction tests

- **Live comparison (T9):** a scratch script builds the restored registry from the head `workspace.toml` and the entries the T7 apply removed, recorded in the ledger with their initiative, collection, and index, and writes it under `.context/` with its SHA-256 in the ledger. The engine from a `git worktree` of `ff33d0dcc` runs `status` over a copy of the head tree carrying that registry, and the head engine runs `status` over the head tree. The script lists every spec membership whose spec result differs; the author states each difference's cause, and the owner approves the list in the ledger.
- **Manual verification:** the owner judges AC-0032's difference list. The owner's approvals in T6 and T7 are Ask-first gates, recorded in the ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Registry entries and the repair | T3, T5 | the repair step; `mutate.md`, SKILL.md, and the schema guide | AC-0001 to AC-0006, AC-0023, and AC-0024 pass; review for the wording |
| Contracts that required registration | T6 | six errata entries and three intent amendments | AC-0025 and AC-0026 pass |
| Equivalence evidence and authority | T2, T6, T8 | engine tests; RFC-0106 errata entry; § Equivalence rows and re-owned Disposition rows | AC-0027, AC-0034, and the amended `workspace-retirement` check pass |
| Delivery plan | T6 | the brief's amended slice 7 and slice 9 text | the owner's approval in the ledger |
| Inventory | T8 | `inventory.toml` edits | AC-0028 passes |
| User documentation, architecture, and maintainer guidance | T5 | the pages AC-0024 lists | AC-0024 passes; review for the wording |
| Comparison and repair record | T1, T7 | `notes/verification-ledger.md` | AC-0029 and AC-0031 pass |
| Release history | T9 | a changelog fragment and `core`'s version bump | the changelog and version gates pass |
| Delivery membership | T1, T9 | the Spec map row and the `workspace.toml` entry | `lint-brief-coverage.py` passes |

## Design (LLD)

### Data & schema

Owned by: T3

`intent-brief-drop` joins `_VALID_OPERATION_TYPES`. An operation carries `entry_locator` (the initiative key, empty for a top-level collection; the collection label, as the engine's `_collection_label` writes it; and the index), `path`, `kind`, and the `registry_fingerprint` the other steps use. The label alone is not unique, because `brief_queue` occurs under five initiatives here, so the initiative key the membership iterator already yields is part of the locator. A canonical entry qualifies when its `source.mode` is `repo-origin` and it is `kind = "intent"` with a path under `docs/product/intents/` or `kind = "brief"` with a path under `docs/product/briefs/`; every captured item's entry, migrated in the same run or not, keeps its entry until slice 9. Legacy entries are not dropped: the legacy-migration repair keeps its routes, and an entry it migrates is a canonical entry the next `repair-plan` drops. The apply runs operation types in a fixed order, `needs-to-header` and `needs-drop-cooled` before `intent-brief-drop`, so a drop sees the `needs` its own run cleared, and one whose needs operation was refused keeps its entry and its edges. Before any operation of the apply changes the document, each drop locator is checked against the registry read under the lock, including that the entry there is a repo-origin intent or brief entry, as `_repair_entry_eligibility` already re-checks queue operations, and bound to its entry object; after the other operations run, each bound entry is removed by identity, so a queue operation that shifts an array cannot misdirect a drop. Removal uses the comment-preserving writer `repair-apply` already uses. On this repository the plan holds 118 operations: 95 intent and 23 brief entries, all repo-origin and none with `needs` (counted at `ff33d0dcc`).

### Behavior & rules

Owned by: T2

- **Cooled child scope.** `_brief_child_spec_states` builds `brief_membership_paths` from brief memberships, and a cooled child's declared parent that misses that set goes to `scope_unknown`, which refuses every `kind = "brief"` dependency in the repository (ADR-0110 D4 and D5). The resolving set widens to brief files. The declared value is first passed through `_resolved_provenance_parent(..., require_local_brief=True)`, the string-only step that already strips whitespace, maps an empty or `none` value to no parent, and rewrites `brief:<slug>`; the result must be byte-identical to `docs/product/briefs/` joined with one name `os.listdir` returns for that directory whose `lstat` shows a regular file, so a nested, `.`, `..`, or trailing-slash value never matches. Before listing, the term's own rule is checked, which is stricter than `_confined_briefs_path` (that helper resolves links and admits a linked briefs directory inside the repository): `docs/product/briefs/`, `docs/product/`, and `docs/` are each `lstat`-ed as a real, non-link directory and resolve beneath the resolved root; any failure, or any `OSError` from listing or `lstat`, lists no brief file, so the scope stays unknown. Nothing is resolved through the filesystem, so a case variant on a case-insensitive volume and a symbolic link both stay unknown, which keeps the fail-closed reason the function's comment gives. A cooled brief keeps its file, because `_cooled_locators` keeps only paths that exist, so no lifecycle-record lookup is needed. No body is opened, keeping ADR-0110 D9. A registered brief gives the same attribution at `ff33d0dcc`; T2's registered case pins it.
- **The child-state check on an unregistered brief.** Today any structural finding on a registered brief puts its path in `structurally_blocked_paths`, and every dependency on it is refused as "dependency has findings". For an unregistered target only `_dependency_metadata_safety_finding` runs. The child-state rule reads only the brief's `Status:` and its child specs, so `_dependency_is_satisfied` gains it for an unregistered brief target, after the safety check: `_brief_child_scope_is_valid` over the collection the brief's `Status:` maps to and `brief_child_states`, with `briefs_with_cooled_children` as the unevaluable flag. A break refuses the dependency with `unsatisfied_dependency` and the detail "dependency has findings", the result a registered target gives. The source-authority check runs only for a tracker-origin entry, so a repo-origin target never had it and gains nothing.
- **Accepted removals and the intended changes.** Three behaviours go, each with its own RFC-0106 errata case. The structural findings other than the child-state rule compare an entry against its artifact or the registry: duplicate membership, the collection and kind rules, the lifecycle rule, `provenance_mismatch`, the entry's own `source.parent`, and the inactive initiative. With no entry they have no input, and they are `the entry-derived findings of an intent or brief target`. `_dependency_cycles` builds its graph over memberships only, so a cycle through an unregistered intent or brief is not found, and a waiter blocked only by that cycle, on the cycle or waiting on a member of it, is released; that is `the waiter's dependency cycle through an unregistered intent or brief`. A target's own `Depends on:` findings sit on the target's own evaluation; with no entry they are not computed, which is `the unregistered intent or brief's own dependencies`. Because the child-state check reads only the brief file, it also reaches a brief that never had an entry, which today settles by its `Status:` alone; that is the intended change `the child-state check on a brief that never had an entry`. For the same reason a cooled child that declares a brief that never had an entry is now attributed to it, where at `ff33d0dcc` it made every brief dependency refuse; that is the intended change `the cooled child of a brief that never had an entry`. An unknown cooled scope refuses every brief dependency in the repository, so resolving one through a brief file can release waiters on other briefs as well, which is the reproduction AC-0007 pins, matching what a registered brief gives today.

### Interfaces & contracts

Owned by: T4

- **Router.** The start and remember branches, and the ready-brief branch, test `signals.authority_mode == "repo-origin"` for an `intent` or `brief` kind. A repo-origin start returns membership `none` with mutation `materialize-and-dispatch`, a repo-origin remember returns `none` with `materialize-draft-non-dispatchable`, and a repo-origin ready-brief returns `none` with `none`; processors are unchanged. A tracker-origin signal takes today's route. The evaluator that derives the matrices' `dispatchable`, `result_code`, and `next_action` already handles membership `none` for the slice-3 defect route; if it does not handle these cases, T4 stops and asks.
- **Rename.** `intent_rename_request.py`'s `source-unregistered` branch is removed; a count above `1` keeps `registry-ambiguous`, and the request-time `registry-unparseable` and `path-dirty` checks stay. The rename's mode is fixed by its base-commit `workspace.toml` (read with `_git_file`, as `_backward_workspace_candidate` already does) and governs every later read:
  - **Registered** — an entry names the source at the base commit. Every live read uses today's `_registry_state` unchanged, so a later removal of that entry still reads `alien` and refuses, as at `ff33d0dcc`.
  - **Cited** — no entry names the source, and the source path occurs. Live reads classify by occurrences: `before` when the source occurs and the successor does not, `after` for the reverse; anything else, including any live entry naming either path, is `alien`. Every `_registry_state` decision for the rename uses this classification, including those inside `_workspace_transition`, `_merge_backward_workspace`, and `_stage_budget_refused` on the pinned, derived, and changed images; their byte replacement and span merge are otherwise unchanged, giving AC-0018. Registered mode keeps today's decision at each of those sites.
  - **Successor only** — no entry names the source and only the successor path occurs: refused with `registry-ambiguous` at the pre-write gate, before the stage exists (AC-0019).
  - **No-registry** — neither path occurs. No live read of `workspace.toml` happens after the pre-write check. The skipped sites are the `run_intent_rename` gate before `_write_stage`, which becomes the pre-write check (an occurrence of either path refuses with `registry-ambiguous` before the stage exists); `_validate_targets`; `_validate_terminal_bytes`; `_discard_unsealed_before`; `_stage_budget_refused`; the registry calls in `_apply_forward` and `_apply_back`; the back-recovery candidate read in `recover_intent_rename`; and `_normalise_old_claim`. A no-registry rename never enters the registry critical section ADR-0134 D5 guards, so its recovery does not consult the shared lock and is not refused by a lock another tool holds.
  The marker-only and partial-record path in `_resume_terminal_cleanup` re-derives from `HEAD`, not a sealed base, and takes the mode `HEAD`'s `workspace.toml` gives, a successor-only `HEAD` reading as cited; there the mode governs only metadata disposal, which touches no live file. A dirty `workspace.toml` at request time still refuses `path-dirty`, as at `ff33d0dcc`. A citation added to `workspace.toml` after the pre-write check keeps the old path, the same as a citation added after any rename finishes; ADR-0134 rejected holding the lock across the transaction.

### Design decisions

Owned by: T5

- `work-intake` SKILL.md states that a repo-origin intent, a repo-origin brief, and a captured item are each their own file with no entry; that a tracker-origin intent or brief is registered as today, because refresh checks its tracker profile through the entry; and that a spec is registered. Its rename section says the rename repoints any `workspace.toml` text that names the old path and needs no entry.
- `author-delivery-brief` create writes the Draft brief, and for a tracker-origin brief adds its Draft entry. Continue writes `Status: Ready`, and for a tracker-origin brief moves its entry. Before it edits a repo-origin brief that still holds an entry, it sends the user to the `workspace-status` `intent-brief-drop` repair; `close-work`, `work-intake`, and `intake-intent` say the same for an intent or brief they change.
- `close-work`'s brief closeout writes the brief's terminal `Status:`, and for a tracker-origin brief moves its entry in the same confirmed effect.
- The two routing references, the architecture page, and the maintainer reference say a repo-origin brief's lifecycle is its `Status:` alone, and drop the Ready-to-Executing move that no skill performs.
- `cooled_child_scope_unknown` is defined in `workspace-status` SKILL.md and the schema guide as a `source.parent` that is absent or names neither a brief file nor a brief entry, and its repair is to declare the brief's path or an empty value.
- The schema guide keeps its collection tables, because spec, tracker-origin, and legacy entries still use them, and adds that new repo-origin intents and briefs get no entry and that `intent-brief-drop` removes existing ones.
- `role-journeys.md` and `your-first-skill.md` describe a Ready brief by its `Status:`, not by a queue.

## Tasks

### T1: The registry comparison is recorded with no failing row

**Depends on:** none

**Mode:** goal-based

**Tests:**
- Criteria: AC-0029.
- `python3 tools/compare-registry.py --root .` runs on this spec's branch before T2 to T7. Its full output, exit code, commit, and `git merge-base HEAD origin/main` go into `notes/verification-ledger.md`.
- The brief's Spec map gains `intent-brief-registration-stop`, and this spec's `workspace.toml` entry is added in `work.active` with its `Status:` moved to `Implementing`, in the same commit.

**Done when:** the ledger holds the run and its exit code is `0`. A non-zero exit stops the plan for the owner.

### T2: The engine is safe for an unregistered intent or brief

**Depends on:** T1

**Mode:** TDD; goal-based for AC-0009

**Tests:**
- Criteria: AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012.
- A new `packs/core/tests/skills/workspace-status/test_intent_brief_registration_stop.py` loads the engine under a unique module name and plants, with the depends-on-headers repository shape, a cooled spec membership declaring a parent brief that: has a file and no entry; is cooled, pruned, and named by its record's locator; has neither; differs from the listed name only in case; is a symbolic link to a real brief or to a cooled one; is a cooled path outside `docs/product/briefs/`; is written `brief:<slug>`; is nested, has a `.` or `..` segment, or ends in `/`; names a listed brief while `docs/product/briefs/` or `docs/product/` is a symbolic link; names a brief while the briefs directory is missing or unreadable; and is registered. A spy on file opens asserts no brief body is read.
- The same file plants: a waiter on an unregistered brief whose `Status:` is `Ready` with an `Implementing` child spec, one whose `Status:` is `Executing` with no executing child, and one that keeps the rule; a waiter on an unregistered brief with an invalid own parent, which gets the safety finding first; a waiter on an unregistered intent in each status, with AC-0011's settlement captured once from the engine at `ff33d0dcc` as literals; a spec-intent-spec cycle; and, for AC-0007, a cooled child of an unregistered brief file beside a waiter on that brief, a waiter on another brief, and a cooled brief that keeps its satisfied result.
- The same file runs `status` over a repository with intents and briefs in every status, a tracker-origin brief entry, and no repo-origin intent or brief entry, each unregistered one with a `Depends on:` naming a missing target or forming a cycle, and asserts AC-0012. 
- AC-0009's fixtures are checked by `git diff --exit-code ff33d0dcc --` and by `test_depends_on_headers_equivalence.py` and `test_captured_item_files_equivalence.py` passing.

```python
# stub: true
def test_waiter_on_unregistered_brief_with_bad_child_scope_is_blocked(tmp_path):
    repo = _plant(tmp_path, brief_status="Ready", child_status="Implementing", brief_entry=False)
    assert observe(repo)["dispatchable"][WAITER] is False
```

**Done when:** the new suite and the depends-on-headers and cooled-brief suites pass, and the packaged engine matches the source after `make build-self`.

### T3: The `intent-brief-drop` repair step

**Depends on:** T2

**Mode:** TDD

**Tests:**
- Criteria: AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006.
- `test_intent_brief_registration_stop.py` gains plan and apply cases over a fixture `workspace.toml` holding a repo-origin intent in `backlog.open` and `shaping_queue.backlog`, two repo-origin briefs in one `brief_queue.executing` list, the same collection name under two initiatives, a mis-collected repo-origin intent in `work.queue` behind a spec a queue operation removes, a tracker-origin brief, an entry with typed `needs`, a cooled entry with `needs`, a captured-item entry of `kind = "intent"` the same plan migrates (kept), a captured membership of `kind = "intent"` already under `docs/product/captured/` (kept), comment lines between entries, and a spec entry. The apply case compares the parsed registry with the one an apply without the drops produces, and the comment lines; the refusal cases plant a `needs-to-header` that is refused, a plan file whose locator is stale under a recomputed `plan_id`, and edited plan files with recomputed `plan_id` whose drop names a spec entry, a tracker-origin entry, the captured `kind = "intent"` entry the same plan moves (named by its path before the move), or the captured `kind = "intent"` entry already under `docs/product/captured/`, each refused with its entry kept.
- `test_depends_on_headers_repair.py`, `test_captured_item_files_repair.py`, and the legacy-migration cases in `tools/test_workspace_status.py` pass unchanged.

**Done when:** the new cases, the repair suites, and `tools/test_workspace_status.py` pass.

### T4: The router and the rename

**Depends on:** T1

**Mode:** TDD

**Tests:**
- Criteria: AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020.
- `packs/core/tests/skills/work-intake/test_registration_stop_routes.py` gains the changed routes and, for every other case of the core routing matrix and for a tracker-origin start, remember, and ready-brief signal of each kind, the `Route` returned at `ff33d0dcc`, captured once as literals.
- The four core matrix cases change only `lifecycle_membership`, `mutation`, and fields the evaluator derives from them; `packs/core/tests/pack/test_work_intake_surface.py`, `tests/roster/test_shaping_intake_handoff_matrix.py`, and each tracker pack's eval tests pass, and `git diff --exit-code ff33d0dcc --` holds for the four tracker matrices.
- `test_intent_rename_request.py` and `test_intent_rename_transaction.py` gain an unregistered source with no `workspace.toml` occurrence, one cited by a spec entry's `source.parent`, and one whose successor path already occurs. `test_intent_rename_recovery.py` gains a kill-and-recover and a rollback case for the first two. For the no-registry rename it also gains: an occurrence of the source path injected after the dirty checks and before the pre-write check, through a substitution of the pre-write read in the test (the base holds no occurrence), refused with `registry-ambiguous` and leaving no `.intent-rename-*` stage; an in-run edit adding the source path at the `before-commit` checkpoint, after which the commit is terminal and `workspace.toml` keeps that edit byte for byte; sealed partials killed at a named forward checkpoint, after which edits add the successor path, then both paths, and forward recovery and rollback each reach a terminal state without reading or writing the live `workspace.toml`; and the same recovery while another tool holds `.workspace-repair.lock`. For the other modes: a registered rename whose entry is removed between a sealed partial and recovery, while another occurrence of the path remains, refuses as at `ff33d0dcc`; and a cited rename that gains an entry naming the successor after its forward step, with the source no longer occurring, refuses with `registry-alien`.
- The cases that assert `source-unregistered` (`test_intent_rename_request.py` near lines 258, 666, 1089, and 1125, and the parametrized case in `test_intent_rename_transaction.py` near line 507) change to the outcome AC-0016 or AC-0019 sets. The line-1125 case keeps its property as a direct assertion that `_count_registry_matches` counts its decoy shapes as zero. Every other existing case passes unchanged.

**Done when:** each named suite passes.

### T5: Writer instructions, guides, and pack pages

**Depends on:** T3, T4

**Mode:** goal-based

**Tests:**
- Criteria: AC-0021, AC-0022, AC-0023, AC-0024.
- A new `tests/roster/test_intent_brief_registration_stop.py` asserts the four criteria's file lists and phrases, and that each AC-0021 file holds `tracker-origin` and `intent-brief-drop`; a companion check over the files at `ff33d0dcc` asserts every listed phrase is present there. Its spec-path literal goes into `.workspace-prune-protected.toml`, it gets a named step in `.github/workflows/build-check.yml` above the bulk tests step, and a `STEP_DISPOSITION` entry in `tools/lint-ci-parity.py`, as `tests/AGENTS.md` § Roster steps requires.
- `tests/roster/test_captured_item_registration_stop.py` and `tests/roster/test_captured_item_files_instructions.py` still pass.
- Each changed skill's `evals/evals.json` case that names intent or brief registration follows the new text; the `work-intake`, `author-delivery-brief`, `close-work`, `intake-intent`, and `workspace-status` eval suites pass.
- Any anchor-hash test over a changed `SKILL.md` section is updated in the same commit as the text.

**Done when:** the new roster test, the instruction tests, each changed skill's eval suite, `tools/lint-ci-parity.py`, and the inventory test pass.

### T6: The errata and amendments, with owner-approved wording

**Depends on:** T1

**Mode:** goal-based

**Tests:**
- Criteria: AC-0025, AC-0026, and the RFC-0106 entry AC-0027's accepted-removal rows cite.
- The brief's slice 7 text is amended to stop repo-origin intent and brief registration, and its slice 9 text to end tracker-origin registration once the tracker profile has a home on the artifact; the owner approves the wording.
- Each wording, the brief's included, is shown to the owner and committed only as approved, and the approval is recorded in the ledger. ADR-0119's `Superseded in part:` line names RFC-0106 D1 for D4's lifecycle clause, and its entry says D4's other point is unaffected. ADR-0110's entry adds the brief file to what a declared value resolves to. The RFC-0106 entry authorises the three accepted removals and the two intended changes and records that tracker-origin intents and briefs keep registration until the tracker profile has an artifact home.
- `tests/roster/test_intent_brief_registration_stop.py` asserts AC-0025's and AC-0026's names.

**Done when:** each of the ten wordings carries the owner's approval in the ledger, and the roster assertion passes.

### T7: The repair runs on this repository

**Depends on:** T2, T3, T5, T6

**Mode:** goal-based

**Tests:**
- Criteria: AC-0030, AC-0031.
- `repair-plan` output is shown to the owner whole; on approval, `repair-apply --yes` runs, and both outputs and the operation counts go into the ledger, with the SHA-256 of the `workspace.toml` it read and a copy of that file kept under `.context/` for T9. A second `repair-plan` holds no `intent-brief-drop` operation.
- `tests/roster/test_workspace_initiative_provenance.py`, `tests/roster/test_workspace_status_projection.py`, and every other suite that reads the live `workspace.toml` pass; a suite that pins an intent or brief entry is updated in the same commit.

**Done when:** the ledger holds both runs and the live-registry suites pass.

### T8: The retirement record and the inventory

**Depends on:** T2, T5, T6, T7

**Mode:** goal-based

**Tests:**
- Criteria: AC-0027, AC-0028, AC-0034.
- The `workspace-retirement` spec is amended through the controlled-amendment path, with fresh owner approval: its slice list names slice 7 among those adding Equivalence rows, AC-0018 and AC-0022 reopen, and its plan gains a task naming this change, and its closed list of intended-change cases admits `the child-state check on a brief that never had an entry` and `the cooled child of a brief that never had an entry`.
- `retirement-record.md` § Equivalence gains AC-0027's eight rows, each naming this spec's test files or ledger as Evidence; the child-state row names `test_intent_brief_registration_stop.py`'s dispatch cases.
- Each § Disposition row with Owner `7` is re-owned: a collection that still holds tracker-origin entries, and `entry.summary`, to `9`, with Home text naming the tracker-origin limit.
- `inventory.toml` re-owns or removes each owner-7 row: a row whose file no longer mentions the registry is removed; one whose remaining mention is about spec registration moves to 8; one whose remaining mention is about tracker-origin registration or the registry's definition moves to 9. Rows this change touches outside owner 7, such as `author-delivery-brief/*` and `close-work/*`, get consumer text that names only tracker-origin brief moves. This spec's directory row is added.
- `tests/roster/test_workspace_retirement_inventory.py` passes.

**Done when:** the inventory test passes and the amended `workspace-retirement` spec carries the owner's re-approval.

### T9: Closeout

**Depends on:** T4, T5, T7, T8

**Mode:** manual QA for AC-0032; goal-based for the gates

**Tests:**
- Criteria: AC-0032.
- The live comparison in Construction tests is recorded in the ledger, and the owner approves its difference list.
- A changelog fragment from `tools/changelog.py new` names the stop and the repair step; `core` takes its patch bump; the changelog and version gates pass.
- `lint-spec-status.py --root .` and `lint-brief-coverage.py` pass.

**Done when:** every listed gate passes and the ledger holds the live comparison.

## Rollout

- **Delivery:** one pull request, merged by the owner.
- **Reversal:** revert the pull request. The removed entries come back with the revert, because the repair's only write is to `workspace.toml` in the same pull request.

## Risks

- **Rename recovery spans three modes.** A rename interrupted under the old code and recovered under the new one is a registered-mode rename, so it keeps today's decisions. T4's recovery cases cover each mode, including the cited and no-registry modes this slice adds.
- **A live-registry test may pin an intent or brief entry.** T7 runs every suite that reads `workspace.toml` before closeout.
- **Writer text also covers spec and tracker-origin registration.** An edit that drops a repo-origin sentence can drop a neighbouring rule that stays. T5's review reads each changed paragraph whole.

## Changelog

- 2026-10-27: spec approved by eugenelim
- 2026-10-27: plan approved by eugenelim
- 2026-10-28: spec re-approved by eugenelim after the controlled amendment keeping captured items out of the drop
- 2026-10-28: plan re-approved by eugenelim

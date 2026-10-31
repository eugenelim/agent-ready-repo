# Plan: Pre-cutover compatibility closure

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - RFC-0105 D3; RFC-0106 D1 and § Errata (2026-10-25 and 2026-10-30 entries); ADR-0074.
  - `packs/core/.apm/skills/close-work/scripts/closure_index.py`: `WorkspaceLookup` (line 222), `_build_eligible_packet` (line 786, the lookup assigned at line 818), `EligiblePacket` (line 1455, the field at line 1518), `check_ancestor_closure` (line 1861, the seam at line 1877 and its pass-through at line 1977).
  - `packs/core/tests/skills/close-work/test_closure_packet.py`: `_call_eligible` (line 134), the two criterion-0031 tests (lines 457 and 478), six callers passing `workspace_lookup=None` (lines 659 to 747).
  - `tests/roster/test_workspace_retirement_inventory.py`: `_slice_numbers` (line 207), the owner rule (lines 303 to 320), the nine-slice fixture brief `_BRIEF` (line 748), `_BASE_ROWS` (line 770, whose readiness row has owner `8`), `test_clean_base_fixture_passes` (line 836), `test_ac0003_owner_not_a_slice` (line 894), `test_ac0009_wrong_consumer_text` (line 1144, another owner-`8` row).
  - `docs/specs/tracker-origin-registration-stop/`: the precedent for the roster check, the ledger, the § Compatibility closure entry and the brief edit.
  - `guides/core/how-to/capture-work.md`: the adopter how-to shape the draft follows.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open.
> Execution observations belong in `notes/verification-ledger.md`.

## Approach

Three independent strands, then the records and the release. The packet strand removes the field and seam and is proved by the close-work suites. The inventory strand changes only row metadata, then amends `workspace-retirement` with the owner rule and teaches its check to enforce it. The notes strand writes the draft and stops for the owner's wording. The closure entry, the brief edit and the release come last, because each cites the other strands' results. The riskiest part is the owner rule: the shared base fixtures carry owner-`8` rows, so they move to owner `9` in the same change, and the rule must not double-report the owner-`10` fixture.

## Constraints

- RFC-0105 D3 gate 4: closure evidence lives in the one retirement record.
- RFC-0106 § Errata: the draft cites the 2026-10-25 and 2026-10-30 entries and restates no decision.
- ADR-0074: `closure_index.py` stays standard-library only.
- `packs/AGENTS.md`: a pack-content change bumps `pack.toml` and `plugin.json` and updates the pack's eval harness; shipped pack content cites no internal record.
- `tests/AGENTS.md` § Roster steps: a new roster test gets a named `build-check.yml` step above the bulk step, a `LOCAL("test-after-build-check")` entry in `tools/lint-ci-parity.py`'s `_LOCAL_STEP_DISPOSITION` and its step name in `_GATE_MAIN_CHECKS` (the two tables `STEP_DISPOSITION` is built from), and a `.workspace-prune-protected.toml` line for each `docs/specs/<slug>` literal it holds.
- The inventory check runs on every pull request, so every file that holds a registry token gets its row in the task that adds it; this spec's directory row lands with the spec.
- `close_work.py` is the only close-work file packaged under `packages/agentbundle/agentbundle/_data/`, so this change needs no `Engine-Change-RFC:` trailer.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Closure packet | T1 | `packs/core/tests/skills/close-work/`; the ledger's AST comparison | AC-0001, AC-0002, AC-0003, AC-0004, AC-0020 checked |
| Closure-eligibility `Status:` line | T2 | the roster check | AC-0005 checked |
| Upgrade notes draft | T4 | the roster check; ledger approval | AC-0012, AC-0013, AC-0014, AC-0015, AC-0016 checked |
| Retirement evidence | T3, T5 | the inventory check; the roster check | AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0017 checked |
| Brief | T5 | `lint-brief-coverage.py` | AC-0018 checked |
| Verification record | T1, T3, T4, T5 | the ledger | AC-0016, AC-0020 checked |
| Release history | T6 | `tools/check-core-release.py`; the changelog checks | AC-0019 checked |

## Design (LLD)

### Design decisions

- **Historical, not re-owned, for finished spec directories.** A Shipped slice 2 to 8 spec has no remaining work and the inventory check admits `historical` for a terminal spec directory, as `header-derived-dispatch/*` already is. `FEAT-0002` is `Fulfilled`, which is terminal. Rests on: every historical-row target stays terminal. A throwaway probe on 2026-10-30 applied this split to a copy of the base inventory and ran `check_inventory` on it: 0 violations, 0 rows owned by slices 2 to 8.

Owned by: T3

- **Re-owned rows name their after-cutover item.** Each re-owned row's `consumer` keeps its description and appends the brief item that ends it: `docs/product/workspace-toml-deps.md`, ADR-0103, ADR-0148 and CAP-0004 wait on moving operative references; `tools/compare-registry.py`, its suite and `test_workspace_mcp_depends_on.py` go with `workspace.toml`; `test_priority_field_never_read.py` and `test_depends_on_headers_instructions.py` change when `workspace-status` shrinks to the repair. This is review-checked working text, not a criterion.

Owned by: T3

- **The owner rule is a new criterion, 0029 of `workspace-retirement`.** It reads the same slice set as that spec's criterion 0003 and fires only for an owner that set contains, so the owner-`10` fixture still reports criterion 0003 alone. Amending criterion 0003 instead would reopen a shipped criterion's wording.

Owned by: T3

- **The draft lives in this spec's `notes/`.** `guides/` publishes on write and `docs/guides/` is maintainer material; the draft carries `guides/` frontmatter, and publishing moves it under `guides/core/how-to/` and re-points its two relative links. Its exact `guide` row precedes this spec's directory row because the first matching row governs.

Owned by: T3, T4


### Behavior & rules

- `EligiblePacket` keeps every other field's position and default; `check_ancestor_closure` keeps every other keyword's position. `_build_eligible_packet` loses its `workspace_lookup` parameter. Traces to: AC-0001, AC-0002.

Owned by: T1

- The roster check is `tests/roster/test_pre_cutover_closure.py`: it imports nothing from the skill, reads files by path, and parses frontmatter with `yaml` and the schema with `jsonschema`, both in `tools/requirements.txt`. Traces to: AC-0005, AC-0006, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018.

Owned by: T2, T4, T5


## Tasks

### T1: The packet carries no registry field

- **Depends on:** none
- **Verification mode:** TDD
- **Touches:** `packs/core/.apm/skills/close-work/scripts/closure_index.py`, `packs/core/tests/skills/close-work/test_closure_packet.py`, `.claude/skills/close-work/**`, `.agents/skills/close-work/**`, `docs/specs/pre-cutover-closure/notes/verification-ledger.md`
- **Tests:** for AC-0001, AC-0002, AC-0003: a field-set test and a signature test in `test_closure_packet.py`, each with the base names frozen as literals, and a token scan of the module; for AC-0004 and AC-0020: the two criterion-0031 tests removed, `workspace_lookup` dropped from `_call_eligible` and its six callers, the suite run, and a throwaway `ast` comparison of each close-work test file with `git show f9bbf6ea1:<path>`, its output recorded in the ledger.
- **Done when:** the three new tests red at the base and pass after, `packs/core/tests/skills/close-work/` passes, and the ledger holds the comparison.

### T2: The roster check, the closure-eligibility record and the eval case

- **Depends on:** T1
- **Verification mode:** goal-based
- **Touches:** `tests/roster/test_pre_cutover_closure.py`, `docs/specs/workspace-retirement/inventory.toml`, `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`, `.workspace-prune-protected.toml`, `docs/specs/closure-eligibility-check/spec.md`, `packs/core/.apm/skills/close-work/evals/evals.json`, `.claude/skills/close-work/**`, `.agents/skills/close-work/**`
- **Tests:** for AC-0005, AC-0006: the roster check reads the `Status:` line and the eval file; its `fixture` row (owner `9`) in the inventory; `tools/lint-ci-parity.py`, the prune-protection construction test and the inventory check.
- **Done when:** each passes and the eval harness's schema suite passes.

### T3: The inventory and the owner rule

- **Depends on:** none
- **Verification mode:** TDD
- **Touches:** `docs/specs/workspace-retirement/inventory.toml`, `docs/specs/workspace-retirement/spec.md`, `docs/specs/workspace-retirement/plan.md`, `tests/roster/test_workspace_retirement_inventory.py`, `docs/specs/pre-cutover-closure/notes/verification-ledger.md`
- **Tests:** for AC-0007, AC-0008, AC-0009, AC-0010, AC-0011: a criterion-0029 fixture case (a row owned by `8`, reporting only criterion 0029) and its control (a row owned by `9`); `_BASE_ROWS`' readiness row and `test_ac0009_wrong_consumer_text`'s row moved to owner `9`, so `test_clean_base_fixture_passes` stays empty; `test_ac0003_owner_not_a_slice` unchanged; the check over this repository.
- **Approach:** amend `workspace-retirement` first — criterion 0029 added, its four lists of enforced rules extended to name it — the Testing Strategy list (line 75), the enforced-rules sentence (line 96), and the lists in its criteria 0022 (line 121) and 0018 (line 128) — criteria 0018 and 0022 un-checked, task T11 added, and the owner's re-approval written on its `Approved:` line with the ledger holding both files' SHA-256 — then the check and its fixtures, then the rows, so the check reds on the base inventory before the rows move.
- **Done when:** the owner has approved the amendment and `tests/roster/test_workspace_retirement_inventory.py` passes.

### T4: The upgrade notes draft

- **Depends on:** T2
- **Verification mode:** goal-based
- **Touches:** `docs/specs/pre-cutover-closure/notes/upgrade-notes.md`, `docs/specs/workspace-retirement/inventory.toml`, `docs/specs/pre-cutover-closure/notes/verification-ledger.md`, `tests/roster/test_pre_cutover_closure.py`
- **Tests:** for AC-0012, AC-0013, AC-0014, AC-0015, AC-0016: the roster check's frontmatter, command-order, fact, link-resolution and approval cases; the draft's `guide` row (owner `9`) placed before this spec's directory row; the inventory check.
- **Done when:** the owner has approved the draft and the checks pass.

### T5: The closure entry and the brief

- **Depends on:** T1, T3, T4
- **Verification mode:** goal-based
- **Touches:** `docs/specs/workspace-retirement/retirement-record.md`, `docs/product/briefs/workspace-registry-retirement-delivery.md`, `docs/specs/pre-cutover-closure/notes/verification-ledger.md`, `tests/roster/test_pre_cutover_closure.py`
- **Tests:** for AC-0017, AC-0018 and AC-0016's remaining approvals: the roster check's record case; `lint-brief-coverage.py`; the inventory check.
- **Done when:** the owner has approved both texts and the checks pass.

### T6: Release

- **Depends on:** T1, T2, T3, T4, T5
- **Verification mode:** goal-based
- **Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/*`, `.claude-plugin/marketplace.json`, `docs/specs/workspace-retirement/inventory.toml`
- **Tests:** for AC-0019: `python3 tools/check-core-release.py --base "$(git merge-base HEAD origin/main)"` after `git fetch origin`; the changelog-fragment checks; a `historical` row for the fragment only if it holds a registry token; `make lint-ruff lint-mypy`; the dispatched `test-roster.yml` run.
- **Done when:** each passes.

## Rollout

- **Delivery:** one `core` patch release. A caller passing `_workspace_lookup` gets a `TypeError`; no shipped caller does.
- **Reversal:** revert the release; no data moves.

## Risks

- A historical row's target that later leaves a terminal status fails the inventory check, naming the row.
- The owner rule reds every shared-fixture test until `_BASE_ROWS` moves to owner `9`; T3 moves both in one change.

## Changelog

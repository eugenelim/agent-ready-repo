# Plan: The last registry entries leave, and refresh gets its own policy file

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - RFC-0106 D1 and § Errata; RFC-0105 D3; RFC-0083; RFC-0055; ADR-0074.
  - `packs/core/.apm/skills/work-intake/scripts/refresh.py`: `parse_refresh_authorization_policy` (line 1021), the `local_receipts` record shape (lines 671-694 and 867), and every `workspace.toml` read and digest binding (lines 1235, 1504, 1609, 1698, 1718, 2005). Packaged copy: `packages/agentbundle/agentbundle/_data/work_intake_refresh.py`.
  - `contracts/jsonschema/source-authority.schema.json`: the `local_receipts` item (line 130).
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`: `_VALID_OPERATION_TYPES` (line 214), `_apply_operations` (line 1296), and the `tracker-entry-drop` section (line 3730), the precedent both new steps copy. The captured-item reader is the engine's `read_captured_item` (`workspace_status_engine.py` line 3523), read only.
  - `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`: `backlog_open_slugs` (line 477), `open_file_resolves` (line 975), `open_spec_resolves` (line 1005), and their caller (line 1120).
  - Suites: `tests/roster/test_work_intake_refresh_coordinator.py`; `packs/core/tests/skills/workspace-status/test_tracker_entry_drop.py`; `packs/core/tests/skills/work-loop/test_lint_spec_status_deferred.py`.
  - `docs/specs/tracker-origin-registration-stop/` and `docs/specs/pre-cutover-closure/`: the precedent for a repair step, the errata, the ledger and the closure entry.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open.
> Execution observations belong in `notes/verification-ledger.md`.

## Approach

Refresh moves first, because it is self-contained and its contract change is the published one. The two repair steps follow, then the anchor re-point, which must land before this repository's run removes the slug-only entries the lint reads today. The run on this repository comes after all three, with the owner confirming the plan file. The errata and the text changes land before the run, which needs the errata's authority; the ledger's run approval, the closure entry and the release come after it, because each cites the run. The riskiest part is the run: it removes every remaining captured and slug-only entry, and its dispatch comparison is the evidence that the three errata removals change nothing here. A throwaway probe on 2026-10-31 emptied every `[backlog]` collection of a copy of this repository's `workspace.toml` and ran `dispatch.py`: `ready`, `active`, `blocked` and `decision` were identical, and `findings` fell from 70 to 48.

## Constraints

- RFC-0106 § Errata: the three removals need one owner-approved entry before the run.
- `packs/AGENTS.md`: a pack-content change bumps `pack.toml` and `plugin.json` and updates the pack's eval harness; shipped pack content cites no internal record.
- The supervisor refuses any worker change under `docs/specs/last-registry-entries/` or to a cited record, which includes `docs/rfc/0106-stop-registering-derivable-work.md`; the ledger, approvals and the owner-approved errata entry are controller commits between attempts.
- The supervisor pins the installed `work-loop` skill at `start`; T4's change to `lint-spec-status.py` reaches the installed copy only through the supervisor's `regenerate` request.
- `tests/AGENTS.md` § Roster steps: a new roster test gets a named `build-check.yml` step, entries in `tools/lint-ci-parity.py`'s `_LOCAL_STEP_DISPOSITION` and `_GATE_MAIN_CHECKS`, and a `.workspace-prune-protected.toml` line for each `docs/specs/<slug>` literal.
- Before the PR: squash the branch and drop `docs/specs/last-registry-entries/delivery/`, keeping the run history on an evidence branch, as 9A and 9C did.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** T6, the run on this repository.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Source-authority record and lock | T1 | refresh coordinator, processor and schema suites | AC-0008, AC-0009, AC-0021 checked |
| Policy file and repair | T1, T2, T3 | refresh and repair suites | AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007 checked |
| Deferral anchors | T4 | the lint's suites | AC-0010 checked |
| Run on this repository | T6 | the ledger | AC-0011 checked |
| User documentation, decision rationale, records, brief | T5, T7 | the roster check; inventory check; `lint-brief-coverage.py` | AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018 checked |
| Release history | T8 | `tools/check-core-release.py`; changelog checks | AC-0020 checked |

## Design (LLD)

### Design decisions

- **The policy file holds only the refresh table.** It is parsed with `tomllib` and must hold exactly `authorization.refresh`; any other key refuses, so the file cannot become a second registry. Rests on: no other skill needs repository policy before 9E.

Owned by: T1

- **Refresh binds the policy file in place of `workspace.toml`.** Every place that read and compared `workspace.toml` bytes reads and compares the policy file through the same confined read, and a receipt stores its digest as `policy_digest`. Old receipts keep `workspace_digest` and stay readable; refresh never writes it again.

Owned by: T1

- **`captured-entry-drop` plans against the state `captured-to-file` leaves.** An entry the same plan backs with a new captured file gets its drop in that plan, carrying the record bytes that `captured-to-file` operation writes as its expected file; apply runs it after the `captured-to-file` write and checks the file against those bytes, so one apply leaves nothing for the next plan.

Owned by: T3

- **Both repair steps copy the `tracker-entry-drop` shape.** Plan derives operations and manual items from the registry and tree; apply re-derives each under the writer lock and removes entries in the existing single atomic, comment-preserving `workspace.toml` write. `refresh-policy-move` writes the policy file through the confined atomic file write the `needs-to-header` step uses, before the `workspace.toml` write; if that write fails, the next plan sees an equal policy file and only removes the table.

Owned by: T2, T3

- **Anchors read captured-item files.** `backlog_open_slugs` is replaced by a check that `docs/product/captured/<slug>.md` is a readable captured file, whatever its `Status:` (owner decision, 2026-10-31: a marker pins the record permanently, as it pinned the backlog entry), run lazily beside `open_file_resolves`; the lint no longer opens `workspace.toml`.

Owned by: T4

## Tasks

### T1: Refresh reads `.work-intake.toml`

- **Depends on:** none
- **Verification mode:** TDD
- **Touches:** `packs/core/.apm/skills/work-intake/scripts/refresh.py`, `packages/agentbundle/agentbundle/_data/work_intake_refresh.py`, `contracts/jsonschema/source-authority.schema.json`, `tests/roster/test_work_intake_refresh_coordinator.py`, `tests/roster/test_github_refresh_processor.py`, `tests/roster/test_jira_refresh_processor.py`, `tests/roster/test_jira_align_refresh_processor.py`, `tests/roster/test_linear_refresh_processor.py`, `tests/roster/test_tracker_origin_registration_stop.py`, `tests/roster/test_two_sided_prune_closure_invariant.py`, `.claude/skills/work-intake/**`, `.agents/skills/work-intake/**`
- **Tests:** for AC-0006, AC-0007, AC-0008, AC-0009, AC-0021: coordinator and remote receipt-store cases over a planted repository with a policy file and no `workspace.toml`, an absent and an invalid policy file, and a policy-file change and a `workspace.toml` change in each window; parser and schema cases for the four receipt shapes; the lock pin in `test_two_sided_prune_closure_invariant.py` observes the lock around the policy-file binding. Every suite that plants `[authorization.refresh]` in `workspace.toml` plants the policy file instead and keeps its other assertions.
- **Done when:** the refresh coordinator, the four processor suites, `test_tracker_origin_registration_stop.py`, `test_two_sided_prune_closure_invariant.py`, the work-intake suites and the schema suite pass.

### T2: The `refresh-policy-move` repair

- **Depends on:** T1, T3
- **Verification mode:** TDD
- **Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`, `packs/core/tests/skills/workspace-status/test_refresh_policy_move.py`, `.claude/skills/workspace-status/**`, `.agents/skills/workspace-status/**`
- **Tests:** for AC-0004, AC-0005: a new suite with one planted case each for move, absent table, invalid table, equal existing file, differing existing file, unparseable existing file, a parseable `.work-intake.toml` with an extra key (never overwritten), and an apply after a failed policy-file write.
- **Done when:** the new suite and `packs/core/tests/skills/workspace-status/` pass.

### T3: The `captured-entry-drop` repair

- **Depends on:** none
- **Verification mode:** TDD
- **Touches:** `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`, `packs/core/tests/skills/workspace-status/test_captured_entry_drop.py`, `.claude/skills/workspace-status/**`, `.agents/skills/workspace-status/**`
- **Tests:** for AC-0001, AC-0002, AC-0003, AC-0005: a new suite with one planted entry per matched and unmatched case (readable file, missing file, unreadable or linked file, slug-only in `[backlog]` and in a shaping queue, with and without its file), a plan that also holds `captured-to-file` operations, the lock-time refusals, and a check that no captured file's bytes change.
- **Done when:** the new suite and `packs/core/tests/skills/workspace-status/` pass.

### T4: Deferral anchors read captured-item files

- **Depends on:** none
- **Verification mode:** TDD
- **Touches:** `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`, `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md`, `packs/core/.apm/agents/adversarial-reviewer.md`, `docs/architecture/loop-contract.md`, `docs/architecture/work-intake-and-artifact-routing.md`, `.claude/skills/work-loop/**`, `.agents/skills/work-loop/**`, `.claude/skills/new-spec/**`, `.agents/skills/new-spec/**`, `.claude/agents/**`, `.codex/agents/**`, `packs/core/tests/skills/work-loop/test_lint_spec_status.py`, `packs/core/tests/skills/work-loop/test_lint_spec_status_deferred.py`
- **Tests:** for AC-0010: an anchor resolving through an open and a `Closed` captured file, refused through a `[backlog].open` entry with no file, the unresolved message naming the file path, the existing open-intent, brief and spec cases unchanged; the cases in `test_lint_spec_status.py` that planted `[backlog].open` plant captured files; the lint over this repository.
- **Done when:** the lint's suites pass and the supervisor's `regenerate` request has rebuilt the installed `work-loop` and `new-spec` copies.

### T5: Governance and text before the run

- **Depends on:** T1, T2, T3, T4
- **Verification mode:** goal-based
- **Touches:** the `work-intake` and `workspace-status` files AC-0014 lists and the guides it lists, `.claude/skills/work-intake/**`, `.agents/skills/work-intake/**`, `.claude/skills/workspace-status/**`, `.agents/skills/workspace-status/**`, `docs/specs/workspace-retirement/retirement-record.md`, `docs/specs/workspace-retirement/inventory.toml`, `docs/product/briefs/workspace-registry-retirement-delivery.md`, `tests/roster/test_last_registry_entries.py`, `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`, `.workspace-prune-protected.toml`
- **Tests:** for AC-0012, AC-0013, AC-0014, AC-0015, AC-0018: a new roster check over the closed file and phrase lists and the errata entry; the inventory and record check; `lint-brief-coverage.py`; `tools/lint-ci-parity.py`.
- **Done when:** the owner has approved the errata and brief text, the controller has committed the errata entry between attempts, and the checks pass.

### T6: Run the repair on this repository

- **Depends on:** T5
- **Verification mode:** manual QA
- **Touches:** `workspace.toml`, `docs/product/captured/credential-broker-contract-manual-qa.md`, `tests/roster/test_credential_broker_contract_docs.py`, `tests/roster/test_agent_skill_engineering_consumer_integrations.py`, `tools/test_guide_typed_asides.py`
- **Tests:** for AC-0011: the plan, the owner's confirmation with the plan file's SHA-256, the apply output, and `dispatch.py` output before and after; before the run the six-row QA matrix is copied, owner-approved, into `docs/product/captured/credential-broker-contract-manual-qa.md`; the two roster tests that asserted removed slug-only entries assert their captured files instead, the credential-broker test still asserting all six rows, and `tools/test_guide_typed_asides.py` passes with the emptied collections; after the test re-point lands, the `PINNED` comment block above the removed entry (`workspace.toml` lines 1490-1503) is removed in an edit separate from the repair write that touches no entry or table.
- **Done when:** the next `repair-plan` holds no `captured-entry-drop` operation, the dispatch comparison shows identical `ready`, `active`, `blocked` and `decision`, and the three suites pass.

### T7: Records after the run

- **Depends on:** T6
- **Verification mode:** goal-based
- **Touches:** `docs/specs/workspace-retirement/retirement-record.md`, `tests/roster/test_last_registry_entries.py`
- **Tests:** for AC-0016, AC-0017: the roster check's closure-entry and approval cases.
- **Done when:** the owner has approved the closure entry and the checks pass.

### T8: Release

- **Depends on:** T1, T2, T3, T4, T5, T6, T7
- **Verification mode:** goal-based
- **Touches:** `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.d/*`, `.claude-plugin/marketplace.json`, `packs/core/.apm/skills/workspace-status/evals/evals.json`, `packs/core/.apm/skills/work-intake/evals/evals.json`
- **Tests:** for AC-0020: one `workspace-status` eval case each for `captured-entry-drop` and `refresh-policy-move`, and one `work-intake` eval case for refresh reading `.work-intake.toml`, with the eval schema suites; `tools/check-core-release.py --base "$(git merge-base HEAD origin/main)"` after `git fetch origin`; the changelog checks; `make lint-ruff lint-mypy`; the dispatched `test-roster.yml` and `test-corpus.yml` runs.
- **Done when:** each passes.

## Rollout

- **Delivery:** one `core` release. An adopter's refresh refuses `invalid_refresh_policy` until they run `repair-plan` and `repair-apply --yes`.
- **Reversal:** revert the release; removed entries and the moved table are in the plan file and in git history.

## Risks

- An adopter's captured membership the reader refuses stays as a manual item, and dispatch still reads it until 9E.
- A repository that edits `.work-intake.toml` while a refresh is open refuses that refresh, as a `workspace.toml` edit did before.

## Changelog

- 2026-10-31: spec approved by eugenelim at `b920263b4`, after three spec-mode shaping and adversarial review rounds, with the round-3 repairs accepted unreviewed and the `workspace-status` projection globs added to T2 and T3 at approval.
- 2026-10-31: plan approved by eugenelim at `b920263b4`.

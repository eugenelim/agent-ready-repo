# Plan: Tracker-origin work stops being registered

- **Spec:** [`spec.md`](spec.md)
- **Status:** Executing <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - RFC-0106 D1 and § Errata; RFC-0105 D3; RFC-0083 and § Errata; RFC-0055; ADR-0074.
  - `packs/core/.apm/skills/work-intake/scripts/refresh.py`: `_TOP_AUTHORITY_KEYS` (line 461), `parse_source_authority` (line 534), `render_source_authority` (line 790), `coordinate_local_refresh` (line 1851, the `matching_entry` block from line 1919 to the profile checks ending line 2032), `guarded_write_pair` (line 1337). Packaged copy: `packages/agentbundle/agentbundle/_data/work_intake_refresh.py`.
  - `contracts/jsonschema/source-authority.schema.json`: closed top-level keys.
  - `packs/core/.apm/skills/intake-intent/scripts/intent_renderer.py`: `_render_tracker_source_authority` (line 273).
  - `packs/core/.apm/skills/work-intake/scripts/intake_router.py`: `_is_unregistered` (line 130), `route_intake`, and `invoke_refresh` (line 330), the refresh front door; `intake_guard.py`: `workspace_source_record` (line 72); `intake_transaction.py`: `run_intake_transaction`'s optional registration stage.
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`: `_VALID_OPERATION_TYPES` (line 214), `_apply_operations` (line 1286), and the `intent-brief-drop` section (line 3327), the precedent the new step copies. Engine: `_SOURCE_FIELDS` and the entry `tracker_profile` bounds (lines 79, 795-834), read only.
  - `packs/core/.apm/skills/work-loop/scripts/dispatch.py` and its suites: unchanged; they must stay green.
  - `docs/specs/spec-registration-stop/` and `docs/specs/intent-brief-registration-stop/`: the precedent for the repair step, the roster text check, the ledger and the governance shape.

## Approach

The record comes first, because every later surface reads or writes it: T1 adds the profile table to the schema, the parser and renderer, and the intent renderer. T2 moves refresh onto the record. With refresh no longer needing an entry, T3 stops the router's registration and T4 adds the repair that moves existing entries. T5 rewrites instruction and guide text. T6 commits governance wording only after the owner approves each entry. T7 runs the repair here, which is a no-op because this repository holds no tracker-origin entry. T8 writes the records, and T9 cuts the release.

## Constraints

- Standard library only in every changed skill script (ADR-0074), apart from `tomlkit`, which `repair-apply` already uses under its declaration in `packs/core/AGENTS.md`.
- No file under `packs/core/.apm/skills/work-loop/` or its projections changes. Open PR #1651 rewrites that skill.
- `make build-self` reprojects the engine and refresh into `packages/agentbundle/agentbundle/_data/` and each skill into `.claude/skills/` and `.agents/skills/`. Projections are never hand-edited.
- A commit that changes `packages/agentbundle/**` carries `Engine-Change-RFC: 0106`.
- `core`, `atlassian`, `github` and `linear` each take one patch bump in `pack.toml` and `.claude-plugin/plugin.json`, at the next free patch above fetched `origin/main` at merge time, and each changed skill's eval harness gains or updates a case.
- Shipped pack text states its rules directly and cites no internal record.
- An accepted RFC changes through § Errata (RFC-0055). A brief changes through `author-delivery-brief`.
- The new roster text check gets a named `build-check.yml` step above the bulk `tests/` step and a `tools/lint-ci-parity.py` `STEP_DISPOSITION` entry, as `tests/AGENTS.md` requires; the owner approved that workflow edit on 2026-10-30 after open PR #1651 merged. Its `docs/specs/tracker-origin-registration-stop` literal needs one line in `.workspace-prune-protected.toml`, which the owner approved with the spec on 2026-10-30.
- Every file this change adds or edits that names `workspace.toml`, `workspace-status` or `workspace_status` outside an inventoried directory needs an inventory row.
- This repository holds no tracker-origin entry and this spec gets no `workspace.toml` entry. The brief stays `Executing`.

## Construction tests

- **Dispatch identity (T4, T12):** `dispatch.py --root <tree>` stdout before and after `repair-apply --yes` on each planted repair tree, compared as AC-0015 states, including its Archived-tree exception. A throwaway probe on 2026-10-30 showed byte-identical output for an Approved tracker-origin spec with and without its `work.queue` entry: `dispatch.py` judges a spec from its headers either way.
- **Manual verification:** the owner's approvals in T6 and T7 are Ask-first gates, recorded in the ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| The source-authority record | T1, T2, T10 | the schema, parser, renderers, `work-intake` SKILL.md § Refresh | AC-0001 to AC-0008, AC-0025, AC-0026 and AC-0029 pass; T10 restores the paired write |
| Registry entries and the repair | T3, T4, T5 | the router, the repair step, `mutate.md`, SKILL.md, the schema guide | AC-0009 to AC-0017, AC-0027, AC-0028 and AC-0030 pass |
| User documentation and architecture | T5 | the pages AC-0018 lists | AC-0018 passes; review for the wording |
| Decision rationale | T6 | two errata entries and the ledger approval rows | AC-0019 and AC-0020 pass |
| Retirement evidence and inventory | T8 | record rows, closure entry, inventory rows | AC-0021 and AC-0022 pass |
| Delivery membership and remainder | T6, T8 | the Spec map row and slice 9 text | AC-0023 passes |
| Verification record | T6, T7 | `notes/verification-ledger.md` | AC-0020 and AC-0024 pass |
| Release history | T9 | changelog fragment and four version bumps | changelog and version gates pass |

## Design (LLD)

### Data & schema

Owned by: T1, T4

- The record's `tracker_profile` is a TOML table, rendered after `source_revision` and `accepted_revision` and before `[owned_fields]`, as `[tracker_profile]` with `id` and `version`. The schema adds it as an optional property with `additionalProperties: false`, both keys required, and the same length bounds as the entry field, so the record stays `source-authority.v1`: an older parser refuses a record that carries it, and every shipped parser moves in the same release.
- `tracker-entry-drop` joins `_VALID_OPERATION_TYPES`. It carries the `entry_locator` shape `intent-brief-drop` uses (initiative key, collection label, index), the entry's `path` and `kind`, the `registry_fingerprint`, the artifact's SHA-256 as read at plan time, and `profile` (the table to write) or `null`.
- A tracker-origin entry that is not matched becomes one item in the plan's existing manual list, with the reason the spec's matched-entry definition names. A held entry becomes the manual item `spec-entry-drop` already uses for its held entries, reusing that step's declared-parent and record-lookup helpers.
- The planner checks the matched-entry conditions in the spec's listed order and reports the first that fails. `needs-present` and `other-write-pending` make an entry wait for the `needs-to-header` step: the plan that migrates its `needs` leaves it unplanned, and the next plan, run after that apply, plans its drop. This keeps the artifact-byte check at apply time exact.

### Behavior & rules

Owned by: T1, T2, T4, T5, T10

- Refresh reads the profile from the parsed record. `coordinate_local_refresh` drops the `matching_entry` lookup, the entry parser call and the entry revision substitution. It moves the profile and kind binding from the entry to the artifact: the current record's profile table must equal the comparison's profile, and the artifact's first-line kind must equal the comparison's kind. It adds two checks: the proposed workspace bytes equal the current bytes, and the proposed record's profile equals the current record's. The workspace digest and policy checks before evaluation, and the digest in the receipt binding, stay. `guarded_write_pair` keeps its base interface and two-file semantics; the coordinator passes it the current `workspace.toml` bytes, so it rewrites `workspace.toml` with those bytes under the guard (its replace-failure and rollback paths stay live) and the file's bytes are unchanged afterwards; its digest re-check under the guard stays.
- `invoke_refresh` gains a `repository_root` parameter. Before resolving the processor it reads the artifact through the skill's confined regular-file read, parses its record, and returns `refresh-unavailable` with next action `add-record-tracker-profile` when the table is absent, or with `repair-refresh-request-profile` when the signals' profile differs from it. It reads no `workspace.toml`.
- `run_intake_transaction` gains an optional `tracker_source` argument (locator, revision, profile). When it is set, the stage that ran `register_workspace_entry` instead appends the AC-0025 record to the target through `write_confined_regular_file`, under the same lock, then re-reads it through `read_confined_regular_file` and parses it, so a link, non-regular file or identity change at the target is a refusal; any refusal, a second record, or a value mismatch takes the existing `_recover_partial_state` path with `failed_stage="source_authority_write"`. The agent passes values as Python arguments, never through a shell string. `register_workspace_entry` stays for callers that pass it, and `work-intake` SKILL.md § 5 stops telling anyone to pass it.
- `intake_transaction.py` loads `refresh.py` from its own skill directory by file path, the way `intent_rename_request.py` loads `intake_transaction`.
- `author-delivery-brief` and `new-spec` keep an existing block byte for byte when they fill the artifact.
- The coordinator's kind check strips one leading front-matter block (a `---` line through the next `---` line) before reading the first `# ` line.
- A held entry uses the same declared-parent resolver `spec-entry-drop` uses, called on the tracker-origin entry; the planner reuses that step's record lookup and manual-item shape.
- `candidate_queue_keys`, the seam `_build_repair_plan_json` already uses to skip queue moves for repo-origin drop candidates (`workspace_status.py:1136`), also takes each matched tracker-origin entry.
- `repair-apply` writes the artifact through the same confined, atomic file write the `needs-to-header` step uses, before the `workspace.toml` write, inside the writer lock. It inserts the table by re-rendering the parsed record with `refresh.py`'s renderer and replacing the block, then re-parses the result. If the `workspace.toml` write then fails, the artifact keeps the added table: its record then holds a table equal to the entry's, which the next plan treats as matched, so the next apply only removes the entry.

### Interfaces & contracts

Owned by: T1, T2

- `SourceAuthority` gains `tracker_profile: dict[str, str] | None`. `RefreshComparison.profile_id` and `profile_version` keep their meaning and are checked against it at the front door and at commit.
- `refresh.py` gains one function that renders a first record from a tracker-origin source (AC-0025); the intake transaction is its only caller. `workspace-status` loads `refresh.py` from the packaged engine data or the sibling `work-intake` skill the way it already loads `cooling.py`, rather than importing across skills.
- `RefreshResult` codes are unchanged; no finding code is added.

### Design decisions

Owned by: T2, T4

- The profile lives in the record rather than a header line, so a tracker fact has one home on the file and is parsed by the one closed-key parser that already guards refresh.
- Refresh keeps reading `[authorization.refresh]` and binding the `workspace.toml` digest. Their home is the deletion slice's, and the brief names it.
- The engine's per-entry refresh status (`origin_mode`, `profile`, `refresh`) goes with the entry. Refresh itself reports availability; RFC-0106's errata entry names this as a behavior not carried over.

### Dependencies & integration

Owned by: T3

- No new dependency. The `atlassian`, `github` and `linear` packs change only their routing matrices.

## Tasks

### T1: The profile table on the record

- **Depends on:** none
- **Verification mode:** TDD
- **Tests:** for AC-0001, AC-0002, AC-0003, AC-0025, AC-0029: the transaction cases in `packs/core/tests/skills/work-intake/test_intake_transaction.py` (a committed tracker-origin brief and spec, a materializer that writes its own record, a materializer that leaves a symlink at the target, a refused source); the schema cases in the source-authority schema suite in `tests/roster/test_work_intake_refresh_coordinator.py`; parse, render and refusal cases in the same suite; a tracker-origin and a repo-origin render in `packs/core/tests/skills/intake-intent/test_intake_intent.py`.
- **Done when:** those cases pass and the intake-intent template conformance suite passes.

### T2: Refresh reads the profile from the record

- **Depends on:** T1
- **Verification mode:** TDD
- **Tests:** for AC-0004, AC-0005, AC-0006, AC-0007, AC-0026 and AC-0008: coordinator cases over a planted repository with no entry, including a missing table, an `id` mismatch, a `version` mismatch and a kind mismatch; the existing entry-contract cases (`…rejects_workspace_entry_contract_violations`, `…invalid_current_workspace_entry…`) are replaced by these refusals, and every other case runs unchanged; front-door cases in `packs/core/tests/pack/test_work_intake_surface.py` and `packs/core/tests/skills/work-intake/test_registration_stop_routes.py`.
- **Done when:** `tests/roster/test_work_intake_refresh_coordinator.py`, `packs/core/tests/pack/` and `packs/core/tests/skills/work-intake/` pass.

### T3: The router stops registering tracker-origin work

- **Depends on:** T2
- **Verification mode:** TDD
- **Tests:** for AC-0009, AC-0016: `test_tracker_origin_routes_match_the_pre_change_route` in `packs/core/tests/skills/work-intake/test_registration_stop_routes.py` becomes a comparison with the repo-origin route; the five matrices' comparison suites.
- **Done when:** both suites and the four packs' matrix suites pass.

### T4: The `tracker-entry-drop` repair

- **Depends on:** T1
- **Verification mode:** TDD
- **Tests:** for AC-0010, AC-0030, AC-0011, AC-0027, AC-0012, AC-0013, AC-0014 and AC-0015: a new suite `packs/core/tests/skills/workspace-status/test_tracker_entry_drop.py`, one planted entry per matched and unmatched case, the lock-time refusals, the dispatch-identity digests, and a refresh call on a migrated artifact; the four existing repair suites unchanged.
- **Done when:** the new suite and `packs/core/tests/skills/workspace-status/` pass.

### T5: Writer and guide text

- **Depends on:** T2, T3, T4
- **Verification mode:** goal-based
- **Tests:** for AC-0017, AC-0028, AC-0018: a new `tests/roster/test_tracker_origin_registration_stop.py` with one parametrized case per file and phrase, each absent phrase checked present at the base; `packs/core/tests/skills/author-delivery-brief/test_project_knowledge_handoff.py`, whose `text.index` anchor on the removed tracker-origin step moves to the rewritten step.
- **Done when:** both pass and each changed skill's eval harness has its case.

### T6: Governance wording and the brief

- **Depends on:** T5
- **Verification mode:** goal-based
- **Tests:** for AC-0019, AC-0020, AC-0023: the roster check reads each errata entry, the brief's slice 9 text, and the ledger's approval rows; `lint-brief-coverage.py`.
- **Done when:** the owner has approved each text and the checks pass.

### T7: Run the repair on this repository

- **Depends on:** T4
- **Verification mode:** manual QA
- **Tests:** for AC-0024: the ledger's `repair-plan` output and its two counts.
- **Done when:** both counts are `0`.

### T8: The retirement record and inventory

- **Depends on:** T6, T7
- **Verification mode:** goal-based
- **Tests:** for AC-0021, AC-0022: `tests/roster/test_workspace_retirement_inventory.py` and the roster check's record rows.
- **Done when:** both pass.

### T9: Release

- **Depends on:** T1, T2, T3, T4, T5, T6, T7, T8, T10, T11, T12, T13, T14, T15
- **Verification mode:** goal-based
- **Tests:** for the release-history durable output: `python3 tools/check-core-release.py --base origin/main`; `python3 tools/lint-catalogue-curation-guard.py --root . --base origin/main` exiting `0` on the pull-request branch, which is one squashed commit carrying `Engine-Change-RFC: 0106` and the `Spec:` trailer, because the supervisor's own commits carry no trailer (owner decision, 2026-10-30; the full supervisor history is pushed as a separate evidence branch); the changelog-fragment checks, `make lint-ruff lint-mypy`, and the dispatched `test-roster.yml`, `test-corpus.yml` and `pack-javascript.yml` runs.
- **Done when:** each passes.

### T10: Restore the paired write's base interface

- **Depends on:** T2, T4
- **Verification mode:** behavior pin
- **Tests:** for AC-0008: the base file's `guarded_write_pair` cases (`…rolls_back_workspace_replace_failure`, `…redacts_rollback_failure`, `…respects_shared_workspace_lock`, `…rechecks_both_fingerprints_immediately_before_replace`, `…preserves_existing_file_modes`, `…rejects_symlink_escape`, `…rejects_stale_fingerprint_and_traversal`) restored to `tests/roster/test_work_intake_refresh_coordinator.py` byte for byte and passing; the coordinator suite and `tests/roster/test_two_sided_prune_closure_invariant.py` passing; `tests/roster/test_workspace_status_progressive_disclosure.py`'s `workspace_status.py` digest updated to the T4 bytes, with a dated note naming this spec added to that file's re-pin comment; the T2-added `test_guarded_pair_write_reports_artifact_replace_failure`, `test_guarded_pair_write_respects_shared_workspace_lock` and `test_guarded_write_rechecks_the_workspace_fingerprint_immediately_before_replace` removed in favour of their restored base counterparts.
- **Done when:** those suites pass and `make build-self` leaves no diff.

### T11: Review repairs

- **Depends on:** T1, T2, T4, T5, T10
- **Verification mode:** TDD
- **Tests:** for AC-0004, AC-0008, AC-0009, AC-0011, AC-0013, AC-0014, AC-0015, AC-0025, AC-0028 and AC-0029, from the implementation review's supported findings (records under `.context/reviews/tracker-origin-registration-stop-impl-r1/`):
  - `invoke_refresh` reads and parses the record before any signal-profile check, returns `add-record-tracker-profile` for a record with no profile table whatever profile the signals carry, resolves the processor from the record's table, and checks only a signal or request profile that is present against it; a front-door case whose signals carry no profile.
  - `render_first_source_authority` refuses, with no output, every locator in the named sensitive classes (control characters, an absolute or personal local path, a `.` or `..` segment, a backslash, an email or secret pattern, userinfo, a query or fragment), and accepts every other locator byte for byte, so the intake transaction ends at `source_authority_write` with no dispatch; one refusal case per class in `test_intake_transaction.py`.
  - `test_tracker_entry_drop.py`: the before-and-after `dispatch.py` comparison on every planted tree AC-0015 names; an `invoke_refresh` call on each migrated artifact resolving the entry's former profile; one planted case each for the apply refusals `entry_held`, `cooling_state_unavailable`, `record_not_writable` and `artifact_write_failed`, set up after planning, asserting the entry and the artifact unchanged; the plan-time `cooling-state-unavailable` manual item; exactly one manual item per planted unmatched entry.
  - `work-intake` SKILL.md: § 7 describes the two-file guarded write and keeps the `local_write_inconsistent` operator-repair instruction; the source-record paragraph no longer names the deleted `intake_guard.py` helper. Checked by new cases in `tests/roster/test_tracker_origin_registration_stop.py`, each red on the current text: § 7 holds `local_write_inconsistent` and no longer holds `replaces the artifact only`; the file holds no `intake_guard.py` source-record instruction.
  - `workspace-status` `references/mutate.md`: every tracker-origin entry is evaluated whatever its collection; the manual reasons include `cooling-state-unavailable`; `artifact_write_failed` is in the apply reason list. Checked by new cases in the same roster file, each red on the current text: the file no longer holds ``in a `work.` or `backlog.` collection`` and holds `cooling-state-unavailable` and `artifact_write_failed`.
  - The `test_registration_stop_routes.py` `_UNCHANGED` comment and test name, and the coordinator dependency-pin test name and fixture knob, say what they check now, with assertions unchanged.
- **Done when:** those suites, the roster checks and `make lint-ruff lint-mypy` pass, and `make build-self` leaves no diff.

### T12: The Archived-tree dispatch difference

- **Depends on:** T11
- **Verification mode:** TDD
- **Tests:** for AC-0015: `test_dispatch_output_is_identical_across_apply_on_an_archived_tracker_spec` in `packs/core/tests/skills/workspace-status/test_tracker_entry_drop.py` is renamed `test_dispatch_output_differs_only_by_the_archived_spec_blocked_item`, loses its `xfail`, asserts that the before output's `blocked` list holds the Archived spec's item with an `unapproved_spec` finding, and asserts that the two outputs, parsed as JSON, are equal once that one item is removed from the before output's `blocked` list, with nothing else removed.
- **Done when:** the suite passes.

### T13: Second review repairs

- **Depends on:** T11, T12
- **Verification mode:** TDD
- **Tests:** for AC-0005, AC-0025 and AC-0029, from the second implementation review's supported findings (records under `.context/reviews/tracker-origin-registration-stop-impl-r2/`):
  - `render_first_source_authority` drops the canonical-form equality refusal and refuses only the named sensitive classes; its secret check matches a credential keyword followed by `:` or `=` at any word boundary, as the removed registration helper did. `test_intake_transaction.py` gains one committing case per adapter locator shape (`jira://EX-101`, `jira://boards/7`, `jira-align://…`, `gh://items/101`, `linear://items/…`, a no-host `tracker:TEAM-42`), each with `source_ref` equal to the locator, and refusal cases for `https://t.example/i/1,api_key=SECRET` and `PROJ-1 token=abc`.
  - `invoke_refresh` returns `refresh-unavailable` with zero effects, before any resolve or acquire, when `request.profile_id` or `request.profile_version` differs from the record's profile, whatever the signals carry; `invalid-refresh-request` stays for path, kind and mode mismatches. A front-door case with no-profile signals and a mismatched request profile pins it.
  - `work-intake` SKILL.md's locator paragraph names exactly the refused classes.
- **Done when:** those suites, the roster checks and `make lint-ruff lint-mypy` pass, and `make build-self` leaves no diff.

### T14: Third review repairs

- **Depends on:** T13
- **Verification mode:** TDD
- **Tests:** for AC-0005, AC-0025 and AC-0029, from the third implementation review's supported findings (records under `.context/reviews/tracker-origin-registration-stop-impl-r3/`):
  - `_require_minimal_locator` refuses a locator with leading or trailing whitespace (Unicode included), any `@` (as the normalized-intake `safeLocator` pattern does), and a scheme-bearing locator with an empty host whose path is absolute; refusal cases in `test_intake_transaction.py` for `' /Users/name/notes.md'`, `' file:///home/name/x'`, `'\xa0/Users/name/x'`, `'user:pw@jira/x'`, `'https:///Users/name/x'`, and one case each that only the `file:` branch and only the `@` rule refuses; every adapter locator shape still commits.
  - The no-profile-signal mismatch case in `test_registration_stop_routes.py` covers both `profile_id` and `profile_version`.
  - `render_first_source_authority`'s docstring names the refused classes, and the work-intake SKILL.md locator paragraph says the classes are checked on the locator text as written, including `@`.
- **Done when:** those suites, the roster checks and `make lint-ruff lint-mypy` pass, and `make build-self` leaves no diff.

### T15: The locator allowlist

- **Depends on:** T14
- **Verification mode:** TDD
- **Tests:** for AC-0025 and AC-0029, from the fourth implementation review's supported findings (records under `.context/reviews/tracker-origin-registration-stop-impl-r4/`) and the owner's 2026-10-30 choice of an allowlist:
  - `_require_minimal_locator` accepts only an ASCII locator of the shape `scheme://host[/path]` or `scheme:ID`, built from letters, digits and `-._:/`, then still refuses a `file:` scheme, a `.` or `..` segment and a secret keyword followed by `:` or `=`; the unreachable userinfo check goes. Every adapter locator shape (`jira://EX-101`, `jira://boards/7`, `jira-align://epics/7`, `gh://items/101`, `linear://issues/ABC-1`, `tracker:TEAM-42`) still commits; refusal cases in `test_intake_transaction.py` for `https:/Users/name/x`, `jira:/home/name/x`, `https:Users/name/x`, a byte-order-mark prefix, a zero-width-space prefix, a bidi override, `~/notes`, `~name/x` and a percent-encoded locator, alongside the existing cases.
  - The work-intake SKILL.md locator paragraph and the `_require_minimal_locator` docstring state the accepted shape and the remaining refusals.
- **Done when:** those suites, the roster checks and `make lint-ruff lint-mypy` pass, and `make build-self` leaves no diff.

## Rollout

- **Delivery:** one patch release each of `core`, `atlassian`, `github` and `linear`. An adopter's tracker-origin artifact refuses refresh, naming the repair, until they run `repair-plan` and `repair-apply`.
- **Reversal:** revert the release; the removed entries are in the plan file and in git history.

## Risks

- An adopter's tracker-origin entry that the repair cannot match stays as a manual item; refresh on its artifact refuses until the owner fixes the record or the entry.
- Refresh still binds `workspace.toml`'s digest, so any unrelated registry edit between comparison and commit refuses the refresh, as at the base.

## Changelog

- 2026-10-30: spec approved by eugenelim at `f273a7659` (rebased `d9d91adf0`); `## Terminal Intent` added with the owner's approval before `start`.
- 2026-10-30: plan approved by eugenelim at `f273a7659` (rebased `d9d91adf0`).
- 2026-10-30: spec and plan re-approved by eugenelim after the AC-0008 controlled amendment and task T10.
- 2026-10-30: spec and plan re-approved by eugenelim after the `cooling-state-unavailable` amendment and task T11.
- 2026-10-30: spec and plan re-approved by eugenelim after the AC-0015 Archived-tree amendment and task T12.

# Plan: Tracker-origin work stops being registered

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - RFC-0106 D1 and § Errata; RFC-0105 D3; RFC-0083 and § Errata; RFC-0055; ADR-0074.
  - `packs/core/.apm/skills/work-intake/scripts/refresh.py`: `_TOP_AUTHORITY_KEYS` (line 461), `parse_source_authority` (line 534), `render_source_authority` (line 790), `coordinate_local_refresh` (line 1851, the `matching_entry` block from line 1919 to the profile checks ending line 2032), `guarded_write_pair` (line 1337). Packaged copy: `packages/agentbundle/agentbundle/_data/work_intake_refresh.py`.
  - `contracts/jsonschema/source-authority.schema.json`: closed top-level keys.
  - `packs/core/.apm/skills/intake-intent/scripts/intent_renderer.py`: `_render_tracker_source_authority` (line 273).
  - `packs/core/.apm/skills/work-intake/scripts/intake_router.py`: `_is_unregistered` (line 130) and `route_intake`; `intake_guard.py`: `workspace_source_record` (line 72).
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
- The new roster text check runs in the dispatched `test-roster.yml` and gets no `build-check.yml` step, so that this change edits no CI workflow. Its `docs/specs/tracker-origin-registration-stop` literal needs one line in `.workspace-prune-protected.toml`, which is an Ask-first edit.
- Every file this change adds or edits that names `workspace.toml`, `workspace-status` or `workspace_status` outside an inventoried directory needs an inventory row.
- This repository holds no tracker-origin entry and this spec gets no `workspace.toml` entry. The brief stays `Executing`.

## Construction tests

- **Dispatch identity (T4):** `dispatch.py --root <tree>` stdout digests before and after `repair-apply --yes` on each planted repair tree. A throwaway probe on 2026-10-30 showed byte-identical output for an Approved tracker-origin spec with and without its `work.queue` entry: `dispatch.py` judges a spec from its headers either way.
- **Manual verification:** the owner's approvals in T6 and T7 are Ask-first gates, recorded in the ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| The source-authority record | T1, T2 | the schema, parser, renderers, `work-intake` SKILL.md § Refresh | AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007 and AC-0008 pass |
| Registry entries and the repair | T3, T4, T5 | the router, the repair step, `mutate.md`, SKILL.md, the schema guide | AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016 and AC-0017 pass |
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
- A tracker-origin entry that is not matched becomes one item in the plan's existing manual list, with a reason string naming the failed condition: `artifact-missing`, `record-missing-or-invalid`, `mode-mismatch`, `ref-mismatch`, `profile-mismatch`, or `entry-profile-missing`.

### Behavior & rules

Owned by: T2, T4

- Refresh reads the profile from the parsed record. `coordinate_local_refresh` drops the `matching_entry` lookup, the entry parser call, the entry revision substitution and the entry profile comparisons, and adds two checks: the proposed workspace bytes equal the current bytes, and the proposed record's profile equals the current record's. The workspace digest and policy checks before evaluation, and the digest in the receipt binding, stay. `guarded_write_pair` writes the artifact and leaves `workspace.toml` as it is; its digest re-check under the guard stays.
- The front door that resolves the processor registration compares the request's profile with the record's before acquisition; an absent table is `refresh-unavailable` with the repair named in the next action.
- `repair-apply` writes the artifact through the same confined, atomic file write the `needs-to-header` step uses, before the `workspace.toml` write, inside the writer lock. If the `workspace.toml` write then fails, it restores the artifact's planned bytes; the plan names this order so a failed apply leaves at most a record that already holds an equal table, which the next plan treats as matched.

### Interfaces & contracts

Owned by: T1, T2

- `SourceAuthority` gains `tracker_profile: dict[str, str] | None`. `RefreshComparison.profile_id` and `profile_version` keep their meaning and are cross-checked against it.
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
- **Tests:** for AC-0001, AC-0002, AC-0003: the schema cases in the source-authority schema suite in `tests/roster/test_work_intake_refresh_coordinator.py`; parse, render and refusal cases in the same suite; a tracker-origin and a repo-origin render in `packs/core/tests/skills/intake-intent/test_intake_intent.py`.
- **Done when:** those cases pass and the intake-intent template conformance suite passes.

### T2: Refresh reads the profile from the record

- **Depends on:** T1
- **Verification mode:** TDD
- **Tests:** for AC-0004, AC-0005, AC-0006, AC-0007 and AC-0008: coordinator cases over a planted repository with no entry; the existing entry-contract cases (`…rejects_workspace_entry_contract_violations`, `…invalid_current_workspace_entry…`) are replaced by the AC-0007 refusals, and every other case runs unchanged.
- **Done when:** `tests/roster/test_work_intake_refresh_coordinator.py` and `packs/core/tests/skills/work-intake/` pass.

### T3: The router stops registering tracker-origin work

- **Depends on:** T2
- **Verification mode:** TDD
- **Tests:** for AC-0009, AC-0016: `test_tracker_origin_routes_match_the_pre_change_route` in `packs/core/tests/skills/work-intake/test_registration_stop_routes.py` becomes a comparison with the repo-origin route; the five matrices' comparison suites.
- **Done when:** both suites and the four packs' matrix suites pass.

### T4: The `tracker-entry-drop` repair

- **Depends on:** T1
- **Verification mode:** TDD
- **Tests:** for AC-0010, AC-0011, AC-0012, AC-0013, AC-0014 and AC-0015: a new suite `packs/core/tests/skills/workspace-status/test_tracker_entry_drop.py`, one planted entry per matched and unmatched case, the lock-time refusals, the dispatch-identity digests, and a refresh call on a migrated artifact; the four existing repair suites unchanged.
- **Done when:** the new suite and `packs/core/tests/skills/workspace-status/` pass.

### T5: Writer and guide text

- **Depends on:** T2, T3, T4
- **Verification mode:** goal-based
- **Tests:** for AC-0017, AC-0018: a new `tests/roster/test_tracker_origin_registration_stop.py` with one parametrized case per file and phrase, each phrase checked present at the base.
- **Done when:** the roster check passes and each changed skill's eval harness has its case.

### T6: Governance wording and the brief

- **Depends on:** T5
- **Verification mode:** goal-based
- **Tests:** for AC-0019, AC-0020, AC-0023: the roster check reads each errata entry, the brief's slice 9 text, and the ledger's approval rows; `lint-brief-coverage.py`.
- **Done when:** the owner has approved each text and the checks pass.

### T7: Run the repair on this repository

- **Depends on:** T4
- **Verification mode:** manual QA
- **Tests:** for AC-0024: the ledger's `repair-plan` output, its two counts, and the two `workspace.toml` digests.
- **Done when:** both counts are `0` and the digests are equal.

### T8: The retirement record and inventory

- **Depends on:** T6, T7
- **Verification mode:** goal-based
- **Tests:** for AC-0021, AC-0022: `tests/roster/test_workspace_retirement_inventory.py` and the roster check's record rows.
- **Done when:** both pass.

### T9: Release

- **Depends on:** T1, T2, T3, T4, T5, T6, T7, T8
- **Verification mode:** goal-based
- **Tests:** for the release-history durable output: `python3 tools/check-core-release.py --base origin/main`, the changelog-fragment checks, `make lint-ruff lint-mypy`, and the dispatched `test-roster.yml`, `test-corpus.yml` and `pack-javascript.yml` runs.
- **Done when:** each passes.

## Rollout

- **Delivery:** one patch release each of `core`, `atlassian`, `github` and `linear`. An adopter's tracker-origin artifact refuses refresh, naming the repair, until they run `repair-plan` and `repair-apply`.
- **Reversal:** revert the release; the removed entries are in the plan file and in git history.

## Risks

- An adopter's tracker-origin entry that the repair cannot match stays as a manual item; refresh on its artifact refuses until the owner fixes the record or the entry.
- Refresh still binds `workspace.toml`'s digest, so any unrelated registry edit between comparison and commit refuses the refresh, as at the base.

## Changelog

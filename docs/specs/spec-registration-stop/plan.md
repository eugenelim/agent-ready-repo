# Plan: Specs stop being registered

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - RFC-0106 D1 and D3; RFC-0105 D3 and its 2026-10-12 erratum; RFC-0108 D3; RFC-0064 D4; ADR-0110; ADR-0076; RFC-0055; ADR-0074.
  - `packs/core/.apm/skills/work-loop/scripts/dispatch.py` and its suites `packs/core/tests/skills/work-loop/test_dispatch.py` and `test_header_derived_dispatch_replay.py`: the dispatch this spec switches to, unchanged.
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_status.py`: `_VALID_OPERATION_TYPES` (line 213), `_canonical_explain` (line 665), `_apply_operations` (line 1280, the `queue-to-shipped` and `queue-remove` arms), and the `intent-brief-drop` section (line 3308), the precedent both new steps copy.
  - `packs/core/.apm/skills/workspace-status/scripts/workspace_status_engine.py`: `_FINDING_NEXT_ACTIONS` (line 101), `_resolved_provenance_parent` (line 2330), `_load_cooling_module` (line 2161).
  - `packs/core/.apm/skills/close-work/scripts/cooling.py`: `load_record` and the record's `parent`, read only; the repair never writes a record.
  - `packs/core/.apm/skills/navigate-intents/scripts/intent_readiness.py`: `check`, `_walk`, `start`, `project`, `_KNOWN_FINDINGS`.
  - `packs/core/.apm/skills/work-intake/scripts/intake_router.py`: `_is_unregistered` and `route_intake`.
  - `packs/core/.apm/skills/work-loop/scripts/lint-spec-status.py`: invariant (iv).
  - `docs/specs/intent-brief-registration-stop/`: the slice-7 precedent for the repair, the roster text check, the ledger, and the governance shape.

## Approach

Record first. T1 runs the comparison and the replay and writes both to the ledger before any writer, router, repair or registry change other than this spec's own entry, because FEAT-0034's validation hook keeps registration if either fails. T2 to T7 then change one surface each and leave the repository working: the finding table, the repair, the router, the bridge, `work-loop`'s dispatch text, and the lint. T8 changes the instruction and guide text. T9 commits governance wording only after the owner approves each. T11 runs the repair on this repository after every writer has stopped and the lint resolves open spec anchors, with the owner's sight of the plan file. T10 then writes the records whose evidence T11 produced. T12 cuts the release.

## Constraints

- Standard library only in every changed skill script (ADR-0074), apart from `tomlkit`, which `repair-apply` already uses under its declaration in `packs/core/AGENTS.md`.
- `workspace-status` reads a lifecycle record only through the engine's existing confined cooling loader, and writes none; `cooling.py` and `close_work.py` do not change.
- `make build-self` reprojects the engine into `packages/agentbundle/agentbundle/_data/` and each skill into `.claude/skills/` and `.agents/skills/`. Projections are never hand-edited.
- A commit that changes `packages/agentbundle/**` carries `Engine-Change-RFC: 0106`.
- `core` and `repo-governance` each take one patch bump in `pack.toml` and `.claude-plugin/plugin.json`, at the next free patch above fetched `origin/main` at merge time, and each changed skill's eval harness gains or updates a case. No `atlassian`, `github` or `linear` file changes.
- Shipped pack text states its rules directly and cites no internal record. Errata and amendments stay in `docs/`.
- An ADR's prose is frozen; only its connection fields and `## Errata` change. An accepted RFC changes through § Errata (RFC-0055). An intent records a change as a dated owner amendment paragraph. A brief changes through `author-delivery-brief`.
- A new roster test gets a `build-check.yml` step and a `tools/lint-ci-parity.py` `STEP_DISPOSITION` entry; a `docs/specs/<slug>` literal in it goes into `.workspace-prune-protected.toml`; parametrize ids are stable strings.
- Every file this change adds or edits that names `workspace.toml`, `workspace-status` or `workspace_status` outside an inventoried directory needs an inventory row.
- This spec's `Status:` and its `workspace.toml` entry move together until T11's repair removes the entry; the brief stays `Executing`.

## Construction tests

- **Corpus for the bridge (T5):** the suite builds each case tree of `test_header_derived_dispatch_replay.py` through that module's builder, loaded by unique name, runs `dispatch.py --root <tree>`, and feeds its stdout to `intent_readiness.member` with a `path_to_id` built from the tree's spec files; it asserts AC-0011 per case and prints the accepted and refused counts.
- **Before-and-after dispatch (T11):** the two `dispatch.py` stdout digests, taken just before and just after `repair-apply`. The comparison is exact because a drop candidate with empty `needs` is never a kept entry, so `dispatch.py` already ignores every entry the apply removes.
- **Manual verification:** the owner's approvals in T1, T9 and T11 are Ask-first gates, recorded in the ledger.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| How `work-loop` dispatches | T6 | Step 0 text and eval cases | AC-0001 and AC-0002 pass |
| Spec entries and the repair | T2, T3, T4, T8 | the router, the repair step, `mutate.md`, SKILL.md, the schema guide | AC-0003 to AC-0005, AC-0012 to AC-0020, AC-0023 pass |
| Readiness bridge input | T5, T8 | `intent_readiness.py`, its SKILL.md and guide | AC-0006 to AC-0011 and AC-0025 pass |
| Contracts that required registration | T9 | six errata entries, two amendments, the AGENTS.md sentence, the brief edit, the ledger approval rows | AC-0027 to AC-0031 pass |
| Equivalence evidence and authority | T9, T10 | § Equivalence rows, re-owned § Disposition rows | AC-0032 and AC-0033 pass |
| Inventory | T10 | `inventory.toml` edits | AC-0034 passes |
| User documentation and deferral guidance | T8 | the pages AC-0024 and AC-0026 list | AC-0024 and AC-0026 pass; review for the wording |
| Comparison, replay and repair record | T1, T11 | `notes/verification-ledger.md` | AC-0035, AC-0037, AC-0038 pass |
| Release history | T12 | changelog fragment and two version bumps | changelog and version gates pass |
| Delivery membership | T1 | the Spec map row | AC-0036 passes |

## Design (LLD)

### Data & schema

Owned by: T3

- `spec-entry-drop` joins `_VALID_OPERATION_TYPES`. It carries the `entry_locator` shape `intent-brief-drop` uses (initiative key, collection label, index), the entry's `path` and `kind`, and the `registry_fingerprint`.
- A held entry becomes one item in the plan's existing manual list, with a reason string, the entry `path`, the record path, and the `parent` value; it is not a finding.
- The declared parent reads the raw `source.parent` key first. An absent key, or a value the normalizer and brief-file rule reject, gives no declared parent, so the entry drops and its record stays without `parent`: `dispatch.py`, which reads a cooled spec's parent from its record, keeps child scope unknown and fails closed (ADR-0110), exactly as it does with the entry present.

### Behavior & rules

Owned by: T3

- **Plan.** Drop candidates come from the same membership iterator `intent-brief-drop` uses, filtered to `work.` and `backlog.` collections, so a table the engine does not parse is never a candidate and keeps the finding it has today. A spec entry whose `needs` a needs operation of the same plan empties is a candidate in that plan.
- **Apply order.** `needs-to-header` and `needs-drop-cooled`, then queue operations, then `spec-entry-drop` and `intent-brief-drop`, all in one `workspace.toml` write.
- **Lock-time hold re-check.** For a cooled candidate, apply re-reads its record through the engine's cooling loader; if the record still lacks `parent` while the entry declares one, the drop is refused.
- **Queue operations.** `queue-to-shipped` and `queue-remove` skip a drop candidate: `spec-entry-drop` removes it in the same run, and a held entry keeps its collection until a later run drops it, because moving a cooled spec's entry would read its status from the cooled body.

### Interfaces & contracts

Owned by: T5

- `check` replaces the status walk with a walk of `dispatch.py`'s keys: top-level `schema_version`, `ready`, `active`, `blocked`, `findings`, `decision`; items `path`, `slug`, `status`, `findings`; findings `code`, `path`, `dispatchable`, `next_action`; decision `action`, `path`, `candidates`, `findings`. Duplicate keys, non-finite numbers, lone surrogates and oversize `next_action` keep today's refusals.
- `start` reads `decision` instead of `checked.ready[0]`; `held` stays as today for the decision path. The page's argless wording follows the rule, so `ask` with several ready specs marks nothing.
- `no_workspace` leaves `REASONS`; the page text for it goes.

Owned by: T4

- `_is_unregistered` treats `spec` like `intent` and `brief`: unregistered when `authority_mode` is `repo-origin`.

Owned by: T2

- `_canonical_explain`'s fallback returns `{"selector_status": "not_found", "findings": []}`.

### Design decisions

Owned by: T8

- `workspace-status` SKILL.md keeps its triggers and sends "what's ready" for specs to `work-loop`'s `dispatch.py`; its status JSON is unchanged.
- `work-loop` Step 0 still shows the initiative and milestone when `workspace.toml` exists, but dispatch never depends on the file.
- Frozen Shipped spec directories are not edited; T10 reclassifies their inventory rows.

### Dependencies & integration

Owned by: T10

- The 17 owner-8 Shipped spec-directory rows become `historical`, owner `none`, consumer text naming the stop; every other owner-8 row outside this spec's directory becomes owner `9` with consumer text naming what remains (tracker-origin entries, the engine `dispatch.py` loads), or is removed when its last registry mention goes.
- § Disposition's owner-8 rows move to owner `9` with Home text naming the tracker-origin spec entries that stay; `spec registration as brief coverage evidence` keeps owner `8` with Home `nothing`.

## Tasks

### T1: Record the comparison and the replay

- **Depends on:** none
- **Verification mode:** goal-based
- **Tests:** for AC-0035, AC-0036:
  - The ledger holds `compare-registry.py` output, exit `0`, commit and merge base; and the `replay-dispatch.py` output over a `git worktree` of that merge base, each difference assigned to its slice-8 class or the owner's approval.
  - The brief's Spec map holds `spec-registration-stop`, this spec's `workspace.toml` entry and inventory row exist, and `lint-brief-coverage.py` passes.
- **Done when:** both runs are in the ledger with no failing or unassigned row, and the coverage lint passes.

### T2: Remove `unregistered_work` and reword the cooled-child next action

- **Depends on:** T1
- **Verification mode:** TDD
- **Tests:** for AC-0003, AC-0004, AC-0005, AC-0039, AC-0041:
  - A planted unregistered spec's `explain` output, in `tools/test_workspace_status_cli.py`, whose current `unregistered_work` assertions move to the new payload.
  - A search test over the AC-0003 trees.
  - The bridge's pinned-table parity test, with the owner-approved sentence, and eval case 11 rewritten.
  - A planted Approved spec with no entry: `reconcile`'s `reconciliation.type1` and `repair-plan`'s manual list, in the `workspace-status` suites that assert `type1-untracked` today, which move to the empty result.
- **Done when:** the tests above pass and `make build-self` leaves the packaged engine equal to the source.

### T3: The repair step

- **Depends on:** T1
- **Verification mode:** TDD
- **Tests:** for AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0042:
  - A new `packs/core/tests/skills/workspace-status/test_spec_registration_stop_repair.py` in the planted-repository style of `test_depends_on_headers_repair.py`: one planted entry per rule, including a candidate whose `needs` the same plan empties, an entry outside a canonical collection, an entry with no `needs` key, cooled entries whose `source.parent` is absent, `none`, empty, a brief file and invalid, a record that already has `parent`, each lock-time refusal, a declared parent that is a brief file outside the record's pattern, a held entry in `work.queue`, a digest of `docs/lifecycle/` before and after, the two-run sequence with a record gaining `parent` between runs, and `dispatch.py` stdout digests around each apply.
  - The existing legacy-migration and `intent-brief-drop` suites run unchanged.
- **Done when:** the tests above pass and `mutate.md` describes the step and the held entry.

### T4: The router and its matrix

- **Depends on:** T1
- **Verification mode:** TDD
- **Tests:** for AC-0012, AC-0013: `route_intake` cases for repo-origin spec start and remember and their tracker-origin twins; the two new matrix cases through the existing matrix comparison suites; the four tracker matrices' digests against the base.
- **Done when:** the tests above pass.

### T5: Re-point the readiness bridge

- **Depends on:** T2
- **Verification mode:** TDD
- **Tests:** for AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0040: the existing `packs/core/tests/skills/navigate-intents/` readiness suites rewritten to `dispatch.py`'s shape, keeping every carried case; one planted refusal per AC-0007 bullet, including a `decision` that names a blocked spec; a `workspace-status status` payload refused as `wrong_schema`; the four marks, and `refuse` giving `bad_workspace`; the marker-string case; and the corpus test the Construction tests section describes.
- **Done when:** the tests above pass.

### T6: `work-loop` dispatches from `dispatch.py`

- **Depends on:** T1
- **Verification mode:** goal-based
- **Tests:** for AC-0001, AC-0002: the roster check's `work-loop` SKILL.md rows, and its check that `evals.json` parses and holds the nine cases AC-0002 names with their outcomes in `expected_output` and `assertions`.
- **Done when:** the roster rows pass.

### T7: Deferral anchors through open spec files

- **Depends on:** T1
- **Verification mode:** TDD
- **Tests:** for AC-0021: planted cases in the `lint-spec-status` suite: an open spec resolves; a Shipped, an Archived, a symbolic-link spec file and a symbolic-link spec directory do not; each base case keeps its result.
- **Done when:** the tests above pass and the lint passes on this repository.

### T8: Writer, deferral and guide text

- **Depends on:** T3, T4, T5, T7
- **Verification mode:** goal-based
- **Tests:** for AC-0022, AC-0023, AC-0024, AC-0025, AC-0026: a new `tests/roster/test_spec_registration_stop.py` holding the closed file-and-phrase lists of AC-0001, AC-0005, AC-0023 to AC-0026 and AC-0029 to AC-0030, with each banned phrase's presence at the base asserted from `git show dfa3fe067:<path>`; the AC-0022 fixture digests.
- **Done when:** the roster test passes, including its build-check step and parity entry.

### T9: Governance wording

- **Depends on:** T1
- **Verification mode:** goal-based
- **Tests:** for AC-0027, AC-0028, AC-0029, AC-0030, AC-0031: the roster test's governance rows, and its ledger rows comparing each approval timestamp with `git log --format=%aI` of the commit that adds the text.
- **Done when:** each entry is committed with approved wording and its row passes.

### T11: Run the repair on this repository

- **Depends on:** T2, T3, T4, T6, T7, T8
- **Verification mode:** manual QA with a byte comparison
- **Tests:** for AC-0036, AC-0037, AC-0038: the ledger's plan and apply output, operation and held counts, the owner's sight of the plan file, and the two before-and-after digest pairs.
- **Done when:** the registry holds no repo-origin spec entry in a canonical collection and both digest pairs are equal.

### T10: The retirement record and inventory

- **Depends on:** T9, T11
- **Verification mode:** goal-based
- **Tests:** for AC-0032, AC-0033, AC-0034: `tests/roster/test_workspace_retirement_inventory.py` and the roster test's owner-8 rows.
- **Done when:** both pass.

### T12: Release

- **Depends on:** T2, T3, T4, T5, T6, T7, T8, T9, T10, T11
- **Verification mode:** goal-based
- **Tests:** for the release-history durable output: `python3 tools/check-core-release.py --base origin/main`, the changelog-fragment checks, `make lint-ruff lint-mypy`, and the dispatched `test-roster.yml` and `test-corpus.yml` runs.
- **Done when:** all pass on the branch.

## Rollout

- **Delivery:** one `core` and one `repo-governance` patch release. An adopter's registry keeps working unchanged until they run `repair-plan` and `repair-apply`; `dispatch.py` already ignores the entries the repair removes, so the order does not matter for dispatch.
- **Reversal:** revert the release; the removed entries are in the ledger's plan file and in git history.

## Risks

- A tracker-origin spec entry stays, and its writers stay, until slice 9. A reader that assumes no spec entries remain would miss them; `dispatch.py` judges them as kept entries.
- An adopter with a cooled spec whose entry declares a parent its record lacks keeps that entry until they add one `parent` line to the record, and an entry whose `needs` the needs repair leaves as a manual item keeps its entry until that is resolved; the plan names both.

## Changelog

- Drafted 2026-10-29.

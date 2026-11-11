# Spec: Adopter upgrade notes, and every operative reference off the registry

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-11-03 by eugenelim, spec and plan at SHA-256 `9fd87850b451b92c6b2b00a7250a0d108dcd5918d0d465ed901f22be0d80dc51` and `9a081738284606afef4f7dc9cbcb208972268566db5818f12b65bcf329170d23`, after three spec-mode shaping and adversarial review rounds (each adjudicated; the round-3 repairs accepted unreviewed) and three spec-stage security rounds ending clean (adjudicated); records under `.context/reviews/registry-upgrade-notes/`. Amended 2026-11-04 under controlled amendment at run-gates: AC-0020 names two excused sets (tests failing at both the base and the head on the same machine, and the five work-loop-copy checks while the run pins that skill, bounded by in-run checks) and AC-0017 names the agentbundle CHANGELOG, README-pypi and marketplace entries; task T12 added; two amendment review rounds (adjudicated; round 2 Nit-only, deferred); re-approved 2026-11-04 by eugenelim at SHA-256 `6a714dd0bd114184d65e0c93e11c30f8f4b13fd77507e0a85d8dd91877c724a0` and `537f71451e5255e7ae33cfbbfce812b4d4af699ae12f43b5d810375199b6973b`; records `amend*` under the same directory.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0105 (D3, gate 4: seeds and operative references are removed before the registry is deleted; the one retirement record), RFC-0106 (§ Errata, each removal's authority), RFC-0069 (the `workspace.toml` adopter seed this spec removes), ADR-0074 (standard-library skill scripts)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Depends on:** spec:repair-only-workspace-status
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites.

## Outcome

An adopter upgrading `core` finds one published guide that walks them from a `workspace.toml` registry to the headers-only model, and no guide, page, seed, manifest or skill in any pack still tells them to register work or to run a retired `workspace-status` subcommand. Success is that a fresh `core` install writes no `workspace.toml`, an intent rename completes without one, and every remaining mention of `workspace-status` in an operative surface is about the repair.

## What Changes

- **Upgrade notes.** A new how-to, `guides/core/how-to/upgrade-from-a-workspace-registry.md`, carries the approved draft forward and adds:
  - `.work-intake.toml` and the `refresh-policy-move` repair;
  - the `needs-to-header` and `captured-entry-drop` repair steps;
  - the retired `workspace-status` subcommands and migration tooling, and finishing a recorded migration operation before the upgrade;
  - the MCP `workspace_status()` fields;
  - dispatch's `unmigrated_workspace` refusal and the hand edit for a legacy-form entry.

  It links no repository-only record. The `pre-cutover-closure` draft stays byte-for-byte as that spec's approved record.
- **Seed and its tooling.**
  - `packs/core/seeds/workspace.toml` is deleted.
  - `workspace.toml` leaves `agentbundle`'s self-host excluded-pattern list and its catalogue lint's seed-placeholder table; the self-host regression test that pinned the pattern goes with it.
  - The sentence naming `workspace.toml` as a lifecycle index goes from `packs/core/seeds/docs/specs/README.md` and `docs/specs/README.md`.
- **Manifests.**
  - `packs/core/pack.toml`'s first-value `verification` and `recovery` name `work-loop`'s dispatch, and `packs/core/README.md`'s Verify line matches.
  - `packs/repo-governance/pack.toml`'s follow-on integration names `work-intake` alone.
- **Intent rename.** `work-intake`'s `intent_rename.py` and `intent_rename_request.py` treat a `workspace.toml` absent from the reference commit and the working tree as a registry the rename does not touch, and still refuse a registry that is a link, unreadable, invalid, or present on only one side. `work-intake`'s evals gain one rename case without `workspace.toml`; the rename guide says so.
- **Core pack text.**
  - `README.md`, `JOURNEY.md`, `DESIGN.md` and `docs/index.md`.
  - The SKILL.md and references of `work-loop`, `work-intake`, `close-work` and `workspace-status` (including `references/mutate.md`), and the evals of those skills, `intake-intent` and `author-delivery-brief`.
- **Other packs' text.**
  - repo-governance: `DESIGN.md` and `new-rfc`.
  - product-strategy: `DESIGN.md`, `JOURNEY.md` and `run-okr-cascade`'s cross-pack routing.
  - experience-design: `experience-status`.
  - desk-research: `desk-research-project-status`.
  - atlassian: `jira-team-status`'s description.
  - linear: `JOURNEY.md`.
  - product-engineering: `place-bet`, `map-capabilities`, `lean-canvas` and their examples, `diverge-solutions`' worked example, and `intent`'s layout reference.
- **Code strings.** The findings' next actions that say "rerun reconciliation" name `dispatch.py` in `work-loop`'s readiness module, `navigate-intents`' pinned copy, `agentbundle`'s packaged copy and `workspace_mcp.py`, and name `repair-plan` in `workspace-status`'s engine, CLI and finding table. Their fixtures and pins follow.
- **Guides and pages.**
  - Deleted: `guides/core/how-to/migrate-capture-work.md` and `guides/core/reference/workspace-toml-schema.md`. Their links point to the upgrade notes.
  - Rewritten around dispatch: `orient-at-session-start`, `two-room-model` and the `your-first-workspace` tutorial.
  - Edited where they state the registry model: every other guide under `guides/`, and `web/src/content/packs/*.md`. The generated `web/src/content/journeys/*.md` are rebuilt from the edited `packs/*/JOURNEY.md`.
- **Docs and root files.**
  - `docs/architecture/`, `docs/guides/reference/work-intake-maintenance.md` and the eight `docs/product/journeys/` pages.
  - `docs/product/README.md`, `docs/product/workspace-toml-deps.md`, `docs/product/initiatives/_template.md` and `docs/backlog.md`.
  - `ARCHITECTURE.md`, `CONTRIBUTING.md`, `llms.txt`, `.github/dependabot.yml` and `packages/agentbundle/README.md`.
- **Tests that pin moved text.** Each shipped test that reads a page this change deletes, or pins a sentence this change rewrites, is re-pointed to the text's new home or loses the assertion when the text it pinned is retired. The ledger lists each such change. This includes twelve roster modules and `tools/test_workspace_status.py`, which read the deleted schema page, and `web/src/test/rendered-output.test.ts`'s next-action pin on `start-or-remember-work`.
- **Roster registration.** The new roster module gets its `build-check.yml` step, its `tools/lint-ci-parity.py` entry and its `.workspace-prune-protected.toml` lines (owner decision, 2026-11-03).
- **Records.**
  - The inventory: this spec's row, the upgrade page's row, the draft's row as `historical`, no rows for deleted files, and each edited row's consumer text.
  - One § Compatibility closure bullet in the retirement record.
  - The brief's Spec map and after-cutover item.
  - This spec's ledger.
- **Release.** Each touched pack and `agentbundle` at its next patch, as `core` 4.0.10 shipped its removals (owner decision, 2026-11-03); one changelog fragment; the `agentbundle` `CHANGELOG.md` and `README-pypi.md` entries; and the marketplace versions.
- **Unchanged:**
  - every `repair-plan`, `repair-apply`, dispatch and MCP result other than the next-action text;
  - every intent-rename result when `workspace.toml` exists;
  - the repository's own `workspace.toml`, RFC-0064 and the inventory check, which 9G changes;
  - every file in the Records set the Acceptance Criteria define, apart from the edits AC-0013, AC-0014, AC-0015, AC-0016 and AC-0017 require.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User documentation: the upgrade path | Applicable: adopters move off the registry by hand | `guides/core/how-to/upgrade-from-a-workspace-registry.md`, linked from `guides/core/README.md` | eugenelim, Approver | AC-0001, AC-0002, AC-0003, AC-0004 pass | The ledger's SHA-256 equals the page at head |
| User promise: install and first value | Applicable: install seeds the registry and the first-value check runs a retired command | `packs/core/seeds/`; `packs/core/pack.toml`; `packs/core/README.md`; `packs/repo-governance/pack.toml` | Platform Core maintainer | AC-0005, AC-0023, AC-0006, AC-0007 pass | A fresh install writes no `workspace.toml` |
| User documentation and skill text | Applicable: guides, pages and skills route to retired behavior | the files What Changes lists | Platform Core maintainer | AC-0008, AC-0009, AC-0010, AC-0011, AC-0019 pass | The roster check passes |
| Interface compatibility: finding next actions | Applicable: dispatch, the MCP tool and the repair print them | `work-loop`'s finding table, its pinned copies, `workspace_mcp.py` and `workspace-status`'s tables | Platform Core maintainer | AC-0012, AC-0024, AC-0025 pass | No next action says "rerun reconciliation" |
| Interface compatibility: intent rename without a registry | Applicable: the registry's deletion would otherwise stop renames | `work-intake`'s rename scripts; `guides/product-engineering/how-to/rename-an-intent.md` | Platform Core maintainer | AC-0018, AC-0021, AC-0022 pass | A rename completes with `workspace.toml` absent |
| Retirement evidence | Applicable: RFC-0105 D3 gate 4 | `retirement-record.md` § Compatibility closure; `inventory.toml` | Platform Core maintainer | AC-0013, AC-0014 pass | The bullet names this spec, the seed removal and the rename |
| Delivery membership | Applicable: closes the after-cutover item | `docs/product/briefs/workspace-registry-retirement-delivery.md` | eugenelim, brief owner | AC-0015 passes | The brief names `registry-upgrade-notes` |
| Verification record | Applicable: owner approvals and moved pins | `docs/specs/registry-upgrade-notes/notes/verification-ledger.md` | Platform Core maintainer | AC-0016, AC-0020 pass | The ledger holds each approval and each moved pin |
| Release history | Applicable: eight packs and `agentbundle` change | one `docs/product/changelog.d/` fragment; each pack's `pack.toml` and `.claude-plugin/plugin.json`; `agentbundle`'s `version.py` and `pyproject.toml` | Platform Core maintainer | AC-0017 passes | The fragment names every package |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.
A syscall, flag, helper name, or exact write order is mechanism that belongs in
the plan's `## Design (LLD)`, not here.

### Always do

- State only what the shipped code does today; read the skill or script before writing a sentence about it.
- Add, re-scope or remove a file's inventory row in the same change that adds, edits or deletes the file.
- When rewording a negative eval assertion, keep the guard it carries.
- When a shipped test pins text this change retires or moves, re-point the pin to the text's new home, or drop it only when the behavior it pinned is retired; record each in the ledger.
- Follow the owning rules for what this change touches: `packs/AGENTS.md` (versions, evals, portable guidance, self-host), `tools/AGENTS.md` (the `Engine-Change-RFC` trailer), `tests/AGENTS.md` (roster steps) and `web/AGENTS.md` (generated journey pages).

### Ask first

- The upgrade notes' wording, the § Compatibility closure bullet and the brief text. The owner approves each before it is committed.
- Deleting a file the plan does not name, or editing a file outside the surfaces What Changes names.
- Any edit to a file in the Records set, apart from the edits AC-0013, AC-0014, AC-0015, AC-0016 and AC-0017 require.

### Never do

- Change a `repair-plan`, `repair-apply`, dispatch or MCP result other than the next-action strings AC-0012 names, or an intent-rename result other than what AC-0018 and AC-0021 require.
- Edit the repository root `workspace.toml`, the inventory check or the `pre-cutover-closure` draft, or edit `.workspace-prune-protected.toml` beyond the lines the new roster module needs.
- Tell adopters to delete `workspace.toml`.
- Add a dependency, a skill, a guide kind, or a top-level directory.

## Testing Strategy

- **Upgrade notes (AC-0001, AC-0002, AC-0003, AC-0004): goal-based.** A roster check reads the page: frontmatter against `contracts/guide.schema.json`, the repo-only-reference lint, the named tokens, and the order of the migration warning and the install step. Owner approval is the wording check.
- **Seed and install (AC-0005, AC-0023): TDD.** An install of `core` into an empty planted repository is the oracle; the catalogue lint and self-host check run over the repository.
- **Manifests (AC-0006, AC-0007): goal-based.** The roster check parses both `pack.toml` files and the README.
- **Operative text (AC-0008, AC-0009, AC-0010, AC-0011, AC-0019): goal-based.** The roster check scans the operative set by mention unit, and resolves the links of the pages it names.
- **Next actions (AC-0012, AC-0024, AC-0025): TDD.** The dispatch, readiness-bridge, MCP and `workspace-status` suites, with only next-action expectations changed.
- **Intent rename (AC-0018, AC-0021, AC-0022): TDD.** The rename suites gain planted repositories without `workspace.toml`, with a link, an unreadable or invalid file, and each one-sided state; their existing assertions stay, and the work-intake eval case covers the agent path.
- **Moved pins (AC-0020): goal-based.** Every test in the four test trees runs; a run of the same tests at the base names the ones the machine already fails; and a comparison script against the base produces the ledger's list of moved pins.
- **Records and release (AC-0013, AC-0014, AC-0015, AC-0016, AC-0017): goal-based.** The inventory and record checks, `lint-brief-coverage.py`, `tools/check-core-release.py`, the changelog checks and the ledger rows.

## Acceptance Criteria

**Terms**

- **Base.** Commit `3b1d0279d`.
- **Upgrade page.** `guides/core/how-to/upgrade-from-a-workspace-registry.md`.
- **Operative set.** Every tracked file matching one of these, apart from the upgrade page:
  - `guides/**/*.md`, `web/src/content/packs/**`;
  - `packs/*/README.md`, `packs/*/DESIGN.md`, `packs/*/JOURNEY.md`, `packs/*/docs/**`, `packs/*/seeds/**`, and every `.md` and `.json` file under `packs/*/.apm/`;
  - `docs/architecture/**/*.md`, `docs/guides/**`, `docs/product/journeys/**`, `docs/product/README.md`, `docs/product/workspace-toml-deps.md`, `docs/product/initiatives/_template.md`, `docs/backlog.md`, `docs/specs/README.md`;
  - `ARCHITECTURE.md`, `CONTRIBUTING.md`, `llms.txt`, `packages/agentbundle/README.md`, `.github/dependabot.yml`.
- **Records.** Files under `docs/specs/` other than `docs/specs/README.md`, `docs/rfc/`, `docs/adr/`, `docs/lifecycle/`, `docs/knowledge/`, `docs/design/`, `docs/product/intents/`, `docs/product/briefs/`, `docs/product/captured/`, `docs/product/research/`, `docs/product/findings/`, `docs/product/shaping/`, `docs/product/design/` and `docs/product/changelog.d/`; `docs/product/roadmap.md`, `docs/product/changelog.md`, `docs/product/initiatives/ini-*`; and every file named `CHANGELOG*`.
- **Repair skill.** `packs/core/.apm/skills/workspace-status/`, which describes the legacy collections the repair reads.
- **Retired command tokens.** `workspace-status status`, `workspace-status reconcile`, `workspace-status explain`, `selected-membership`, `retirement-candidates`, `repair-rollback`, `--migration-selection`, `prune --select`, `[authorization.migration]`, `.workspace-migrations.json`, `workspace.toml transition`, `rerun reconciliation`.
- **Registry-model tokens.** `shaping_queue`, `[work].queue`, `brief_queue`, `workspace entry`, `workspace membership`.
- **Normalized text.** A file's text with each run of whitespace collapsed to one space; for a JSON file, each string value normalized separately.
- **Mention unit.** In a Markdown file: one table row, one list item with its continuation lines, one paragraph, or one line of a fenced block or of frontmatter; a heading is not a unit. In a JSON file: one string value. In any other file: one line.
- **Word match.** Whole word and case-insensitive; `delet` and `regist` match as word prefixes, and a word ending `n't` counts as `not`.
- **Absent registry.** At a commit: `git ls-tree <commit> -- workspace.toml` succeeds and lists nothing. In the working tree: no directory entry named `workspace.toml` at the repository root, with links not followed, and a `git ls-files -- workspace.toml` that succeeds and lists nothing. A failed or timed-out Git query never establishes absence.
- **Reference commit.** The commit a rename pins; for the rename request, `HEAD`.

**Upgrade notes**

- [x] **AC-0001.** The upgrade page's frontmatter validates against `contracts/guide.schema.json` with `pack: core` and `kind: how-to`, its H1 equals its `title`, and `tools/lint-guides-no-repo-only-refs.py` passes over it. `guides/core/README.md` links it.
- [x] **AC-0002.** The upgrade page's normalized text names each of these in backticks:
  - `repair-plan`, `repair-apply --yes`, `needs-to-header`, `captured-entry-drop`, `refresh-policy-move`, `.work-intake.toml`, `[authorization.refresh]`, `unmigrated_workspace`, `dispatch.py`;
  - `status`, `reconcile`, `explain`, `selected-membership`, `prune`, `retirement-candidates`, `repair-rollback`, `[authorization.migration]`, `.workspace-migrations.json`;
  - `workspace_status()`, `ini_slug`, `shaping`, `WORKSPACE_MCP_DISPATCHED_ITEM`;
  - each behavior the draft lists as not carried over.
- [x] **AC-0003.** In the upgrade page, the first occurrence of `.workspace-migrations.json` precedes the first occurrence of `agentbundle upgrade`. No mention unit of the page contains both `workspace.toml` and a word match for `delet`, unless it also contains a word match for one of `no`, `not`, `never` or `keep`.
- [x] **AC-0004.** `docs/specs/pre-cutover-closure/notes/upgrade-notes.md` has SHA-256 `417412d4adb63ce114802cc8beffa82f1ae303b8a4d4c0dd9971e03fc8500a58`, its value at the base, and `tests/roster/test_pre_cutover_closure.py` passes unchanged.

**Seed and manifests**

- [x] **AC-0005.** `packs/core/seeds/workspace.toml` does not exist, and installing `core` into an empty repository writes no `workspace.toml`.
- [x] **AC-0023.** No entry of `agentbundle`'s self-host excluded-pattern list, and no key of its seed-placeholder table, is `workspace.toml`; `agentbundle catalogue lint --root . --deep` and the self-host check pass.
- [x] **AC-0006.** `packs/core/pack.toml`'s `[pack.first-value]` `verification` and `recovery` each name `dispatch.py` and neither names `workspace-status`; `packs/core/README.md`'s normalized text contains the normalized `verification` text.
- [x] **AC-0007.** `packs/repo-governance/pack.toml` contains no `workspace-status`.

**Operative text**

- [x] **AC-0008.** No retired command token appears in the normalized text of any file in the operative set, and no registry-model token appears in that of any file in the operative set outside the repair skill. `rerun reconciliation` appears in no `.py` file under `packs/*/.apm/` or `packages/agentbundle/agentbundle/`.
- [x] **AC-0009.** Outside the repair skill's `evals/`, every mention unit in the operative set that contains `workspace-status` also contains `repair`, apart from a JSON string value that holds no whitespace and a frontmatter line whose key is `name`.
- [x] **AC-0019.** No mention unit in the operative set contains both `workspace.toml` and a word match for `regist`, unless it also contains `repair` or a word match for one of `no`, `not`, `never`, `nothing`, `none` or `without`.
- [x] **AC-0010.** `guides/core/how-to/migrate-capture-work.md` and `guides/core/reference/workspace-toml-schema.md` do not exist, and no tracked file outside the Records set, apart from `tests/roster/test_registry_upgrade_notes.py`, contains `migrate-capture-work.md` or `workspace-toml-schema.md`. Each relative Markdown link in the upgrade page and the three rewritten guides, with any `#fragment` removed, resolves to a tracked file or to a directory holding one.
- [x] **AC-0011.** `guides/core/how-to/orient-at-session-start.md`, `guides/core/explanation/two-room-model.md`, `guides/core/tutorials/your-first-workspace.md` and `packs/core/JOURNEY.md` each name `dispatch.py`, and `tools/build-site.py --journeys-only` leaves `web/src/content/journeys/` unchanged.

**Next actions and rename**

- [x] **AC-0012.** No finding next action contains `reconciliation` in `work-loop`'s finding table, `navigate-intents`' pinned table, `agentbundle`'s packaged readiness module, `agentbundle`'s `workspace_mcp.py`, or `workspace-status`'s engine, CLI and SKILL.md. 
- [x] **AC-0024.** Each next action that differs from the base names `dispatch.py` in `work-loop`'s table, `navigate-intents`' table, the packaged readiness module and `workspace_mcp.py`, and names `repair-plan` in `workspace-status`'s engine, CLI and SKILL.md.
- [x] **AC-0025.** The tests under `packs/core/tests/skills/work-loop/`, `packs/core/tests/skills/navigate-intents/` and `packs/core/tests/skills/workspace-status/`, and `packages/agentbundle/tests/test_workspace_mcp_*.py`, pass. Their only differences from the base are next-action strings in expectations and fixtures, and the pin moves the ledger lists under AC-0020.
- [x] **AC-0018.** With the registry absent at the reference commit and in the working tree, each of these returns the same status and refusal code, and leaves the same tracked tree apart from `workspace.toml`, as in a repository whose `workspace.toml` is tracked, clean and names neither path; none of them creates `workspace.toml`:
  - the rename request, whose resolved fields other than `repository_root` also match;
  - a forward rename;
  - recovery of a staged rename in each direction;
  - terminal-cleanup recovery of an empty stage or of a stage holding a torn cleanup marker, run after a commit removed `workspace.toml`, which removes only that stage's own files and writes nothing else.
- [x] **AC-0021.** Each of these refuses and writes nothing:
  - a `workspace.toml` that is a link (resolving or dangling), not a regular file, unreadable, or not valid TOML: the request refuses `registry-unparseable`;
  - a registry absent at the reference commit but present and untracked in the working tree, parsing and naming neither path: the request refuses `path-dirty`;
  - a registry tracked at the reference commit but absent from the working tree: the request refuses `path-dirty`;
  - a registry held only in the Git index, absent from the reference commit and the working tree: the request refuses `path-dirty`;
  - a rename, or recovery of a staged rename, whose tree lookup of `workspace.toml` at its pinned commit fails or finds an entry that is not a regular file.
- [x] **AC-0022.** Every rename suite test at the base passes with its assertions unchanged, and `work-intake`'s evals hold one case whose prompt renames an intent in a repository without `workspace.toml` and whose assertions require that the rename completes and creates no `workspace.toml`.

**Records and release**

- [x] **AC-0013.** `inventory.toml` holds a `docs/specs/registry-upgrade-notes/*` `contract` row at owner `9`, a row for the upgrade page, the draft's row at class `historical` and owner `none`, and no row for a file this spec deletes; the inventory check passes.
- [x] **AC-0014.** `retirement-record.md` § Compatibility closure holds one bullet that links `../registry-upgrade-notes/spec.md` and names the upgrade page, the seed removal and the rename's absence handling, and the record check passes.
- [x] **AC-0015.** The brief's Spec map lists `registry-upgrade-notes`, its after-cutover item for the upgrade notes names it, and `lint-brief-coverage.py` passes.
- [x] **AC-0016.** `notes/verification-ledger.md` records eugenelim's approval of the upgrade page, the closure bullet and the brief text, each with a SHA-256 equal to that file's SHA-256 at the committed head.
- [x] **AC-0020.** Every test under `tests/roster/`, `packs/*/tests/` and `web/src/test/`, and every `tools/test*` suite, passes, apart from two named sets:
  - a test that fails or errors both at the base and at the head on the same machine; the ledger lists the failing test identifiers of each run, with its command and counts, and the excused set is the tests on both lists;
  - while the run pins the installed `work-loop` skill: `test_ac11_work_loop_projections_are_byte_identical_to_the_source`, both `TestProjectedCopiesByteIdentical` tests in `test_t9a_conformance_rollup.py`, `test_self_host_skill_projections_match_their_canonical_sources` (which compares every skill projection of four packs) and `test_archive_carries_the_map_unchanged` (which packages the tree, so it refuses a stale projection before it checks `contracts/renames/pack-renames.toml`). For this set, `test_registry_upgrade_notes.py` checks during the run that every `.claude/skills/` and `.agents/skills/` copy other than `work-loop` matches its pack source file for file, and that `contracts/renames/pack-renames.toml` is byte-identical to the base.

  The ledger holds the output of one comparison against the base of every test file in those trees, taken after the last task that edits a test file, with its command, listing each file that differs and each line removed or changed in it, module-level tables and fixtures included. Each listed file carries an annotation naming the file or files its changed pins read.
- [x] **AC-0017.** Each pack this change touches carries, in `pack.toml` and `.claude-plugin/plugin.json`, the next patch above its version on freshly fetched `origin/main`, and `tools/check-core-release.py --base` passes. `agentbundle`'s `version.py` and `pyproject.toml` carry the next patch above freshly fetched `origin/main`. One `docs/product/changelog.d/` fragment names every such package at its new version and names the upgrade page. `agentbundle`'s `CHANGELOG.md` and `README-pypi.md` each lead with an entry for its new version, and `.claude-plugin/marketplace.json` carries each touched pack's new version wherever it lists that pack.

## Terminal Intent

`code` — publish the upgrade notes, remove the `workspace.toml` seed and its tooling, let intent renames run without `workspace.toml`, move every operative reference off the registry, and release the touched packs and `agentbundle`.

## Follow-ons

- eugenelim: 9G — delete the repository's `workspace.toml` and the suites that read it, change the inventory check's fact set, retire `.workspace-prune-protected.toml`, amend RFC-0064, complete the closure checklist and record the certification.

## Assumptions

- Product: `tools/work_intake_routing_evaluation.py` and the routing matrix still name the status route's next action `inspect-workspace-status`, an identifier the router no longer follows; renaming it changes an evaluation contract outside this spec (owner to decide whether it becomes a follow-on).
- Product: adopters with an unfinished `.workspace-migrations.json` operation, or with a legacy-form entry, are invisible from here; the upgrade page is their only notice.

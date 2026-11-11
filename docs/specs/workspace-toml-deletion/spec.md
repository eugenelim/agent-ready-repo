# Spec: Closing the workspace retirement and deleting workspace.toml

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-11-03 by eugenelim, spec (sha256 `df3dec6e444d262a584d8a5f47f38145ce2e09d9a340d95667e7ff15dda4d357`) and plan (sha256 `8a41b8e11ef277a2e0b9d886e79bf0272265b5aaad4916de0dec06600e05000c`), after five spec-mode shaping and adversarial review rounds and a spec-stage security pass, each adjudicated; the round-5 repairs were accepted without a further round; records under `.context/reviews/workspace-toml-deletion/`. Amended 2026-11-04 before `start`, approved by eugenelim: `Permitted surfaces` adds `tests/roster/test_registry_upgrade_notes.py`'s ledger check, which 9F's head-bound AC-0016 pin forces, and `Depends on:` names 9F's spec.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0105 (D3, the four retirement gates, gate 4's order "remove operative references and seeds, pass activation and corpus gates, and only then delete the old skill and registry contract", and the Approver's certification "in that specification and the retiring change"; § Errata, the entry this spec adds that moves the old skill's deletion to the RFC-0067 release), RFC-0106 (§ Errata, the no-seam removals), RFC-0055 (errata entries on an Accepted RFC), RFC-0067 (the later retirement of the `workspace-status` name)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Depends on:** spec:registry-upgrade-notes
- **Contract:** none — the inventory and record shapes are contracted by the `workspace-retirement` spec, which this spec amends.
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy`,
> `Acceptance Criteria` and `Closeout` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites.

## Outcome

The Platform Core maintainer can certify RFC-0105 D3's four retirement gates from one checklist in the retirement record, where each item names its evidence. This repository then has no `workspace.toml`, no prune-protection list, and no suite or tool that needs either. Success is that the inventory check refuses a Shipped retirement spec in three cases: a checklist item is `open`; the certification is missing or not signed in the Approver's role; or `workspace.toml` is still tracked. Adopters keep the `workspace-status` repair, so the repair and dispatch's `unmigrated_workspace` refusal still ship.

## What Changes

The work lands as one pull request in three stages, all after slice 9F has merged to `main`, because 9F also makes intent renames work with no `workspace.toml`. Before the supervisor run starts, on a branch from that `main`, the controller commits RFC-0105's erratum with the approved spec and plan. The run then builds the code, test and inventory work straight through. After the run, the controller records the gate runs and the certification, ships the specs, and closes the brief.

- **Old-skill deferral (before the run).** RFC-0105 § Errata gains an entry, in the owner's wording. It moves gate 4's "delete the old skill" to the release that retires the `workspace-status` name under RFC-0067. It also says that the repair, dispatch's refusal and `contracts/jsonschema/workspace-entry.schema.json` ship with the skill until then, and are not part of the registry contract this spec retires.
- **Prune-protection list (run).** `.workspace-prune-protected.toml` is deleted, along with item 3 of `tests/AGENTS.md` § Roster steps and the file's inventory row. Nothing reads the file: its last reader, `tests/roster/test_two_sided_prune_closure_invariant.py`, was removed with `prune` in `repair-only-workspace-status`.
- **Retirement spec amendment (run).** `docs/specs/workspace-retirement/spec.md` and its plan gain the closure-checklist, certification and ship-time criteria (criteria 0030 to 0033). Criterion 0011's registry key paths become a frozen list, so the inventory check stops parsing `workspace.toml`. Criterion 0003 gains the owner `rfc-0067`. `tests/roster/test_workspace_retirement_inventory.py` enforces each rule.
- **Closure checklist (run, drafted).** `retirement-record.md` § Compatibility closure gains a checklist table: one row per gate item, each `met` with evidence or `open`. The closeout sets every row to `met`.
- **Deletion (run).** The root `workspace.toml` is deleted, and the repository's readers of it change to work without it. These are the reader suites and the comment in `.github/workflows/build-check.yml`. `tools/measure-changelog-conflicts.py` keeps the path, because it measures history. The `Makefile` comment stays, because another suite byte-pins that file, and so does the `gemini_command_toml.py` docstring, because a package edit needs an engine-change trailer; both rows are owned by `rfc-0067`. 9F removed `llms.txt`'s link.
- **Inventory re-ownership (run).** Each row still owned by slice 9 becomes one of three things:
  - a `historical` row with owner `none`, where criterion 0008 allows it;
  - a row owned by `rfc-0067`, for a surface that lives while the repair ships;
  - no row at all, where the file no longer mentions the registry.

  The rows for the brief, this spec's directory and FEAT-0034 settle at closeout, once their targets close.
- **Registry contract (run).** RFC-0064 § Errata gains a current-state row and an audit-trail entry, in the owner's wording. Together they retire what remains of its registry definition. RFC-0064 is a record this spec changes, not one it is constrained by.
- **Closeout (after the run).** The controller records the corpus, roster and activation runs on the tested commit, sets the checklist to `met`, and records the owner's certification in `retirement-record.md` § Certification, the pull request's description and its commit message. `workspace-retirement` and this spec move to `Shipped`. `close-work` closes the brief (with `Cut-closed:`) and routes FEAT-0034 per its lifecycle.
- **Unchanged:**
  - every file under `packs/`, including the `workspace-status` repair, `dispatch.py`'s `unmigrated_workspace` refusal, the packaged `_data/` copies and the `tomlkit` pin;
  - `contracts/jsonschema/workspace-entry.schema.json`;
  - every seed, guide, manifest and operative reference slice 9F moves. These include the `workspace.toml` seed, its `self_host.py` and `catalogue_tooling/lint.py` lines, and `packs/core/seeds/docs/specs/README.md`;
  - the intent-rename scripts and their tests, which 9F makes work with no `workspace.toml`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale: gate 4 closure and the certification | Applicable: RFC-0105 D3 names this record | `docs/specs/workspace-retirement/retirement-record.md` § Compatibility closure and § Certification | eugenelim, RFC-0105 Approver | AC-0003, AC-0004, AC-0006; criterion 0033 over this repository once `workspace-retirement` is Shipped | Every checklist row is `met` and the certification is the owner's text |
| Decision rationale: the old skill's deletion deferred | Applicable: RFC-0105 D3 gate 4 names it | `docs/rfc/0105-artifact-derived-navigation-and-workspace-retirement.md` § Errata | eugenelim, RFC-0105 Approver | AC-0012 | The owner approved the wording |
| Decision rationale: the registry contract retired | Applicable: RFC-0064 still defines the registry | `docs/rfc/0064-ini-001-ai-native-ecosystem.md` § Errata | eugenelim, RFC-0064 Approver | AC-0008 | The owner approved the wording |
| Current product truth: which surfaces still mention the registry | Applicable: the repair outlives the file | `docs/specs/workspace-retirement/inventory.toml` | Platform Core maintainer | AC-0007; criterion 0032 once `workspace-retirement` is Shipped | No row carries a slice number |
| Maintainer procedure: roster admission | Applicable: `tests/AGENTS.md` obliges the retired list | `tests/AGENTS.md` § Roster steps | Platform Core maintainer | AC-0001 | The rule lists two edits |
| Delivery membership and closure | Applicable: this is the brief's last slice | `docs/product/briefs/workspace-registry-retirement-delivery.md`; `docs/product/intents/FEAT-0034-workspace-registry-retirement.md` | `close-work`, eugenelim as brief owner | § Closeout; `lint-brief-coverage.py` | The brief is `Shipped` with `Cut-closed:` |
| Verification record | Applicable: approvals, hashes and gate runs | `docs/specs/workspace-toml-deletion/notes/verification-ledger.md`, written at closeout | Platform Core maintainer | § Closeout | Each approval names the SHA-256 of each file approved |
| Release history | Not applicable: no file under `packs/` changes, so no pack version moves | — | — | — | — |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.
A syscall, flag, helper name, or exact write order is mechanism that belongs in
the plan's `## Design (LLD)`, not here.

### Always do

- Run `tests/roster/test_workspace_retirement_inventory.py` after each task, and keep it passing.
- Add or drop a file's inventory row in the same task that adds the file or drops its last registry mention.
- Start the run on a branch created from `origin/main` fetched after 9F's merge, and merge nothing from `main` into it while the run is open.
- Compute every file hash and commit ID before quoting it to a reviewer or the owner.

### Ask first

- The certification text, both errata wordings, the `workspace-retirement` amendment, and the checklist rows. The owner writes or approves each before it is committed, and the closeout ledger records each approval with the file's SHA-256.
- Dispatching `pack-evals.yml`, because it calls a paid model API.
- Any edit to a file outside the permitted surfaces.

### Never do

- Run the supervisor's `start`, or commit anything for this spec beyond its approved spec and plan, before 9F's pull request has merged to `main`.
- Write or paraphrase the certification or either errata entry on the owner's behalf.
- Edit any file under `packs/`, any seed, guide or manifest slice 9F owns, or `contracts/jsonschema/workspace-entry.schema.json`.
- Edit a file only to drop its registry mention so that its row can go, outside the permitted surfaces.
- Add a dependency, a skill, a roster module, an inventory class, a disposition category, or a top-level directory.

## Testing Strategy

- **Inventory check rules (AC-0002, AC-0003, AC-0004, AC-0005, AC-0006): TDD.** Each new rule reds on a planted-violation fixture before it exists, and the frozen fact set reds a fixture record missing one frozen key. The check is a function over a fixture repository, and the existing harness builds one per test. For AC-0002, a test also compares the frozen list with the key paths parsed from `workspace.toml` at commit `3b1d0279d`, read with `git show`.
- **Prune list retired (AC-0001, AC-0015): goal-based.** A `git ls-files` and `git grep` over the head commit, and a read of `tests/AGENTS.md` § Roster steps at that commit for the two-edits sentence and its two numbered items.
- **Deletion, readers and ownership (AC-0007, AC-0016): goal-based.** The named suites and the inventory check pass at the run's final commit, where the file is absent, and a parse of `inventory.toml` lists each row's owner.
- **Errata (AC-0008, AC-0012): goal-based.** A read of each RFC's § Errata.
- **Closeout: goal-based, outside the run.** Criteria 0032 and 0033, enforced by the inventory check on the pull request once `workspace-retirement` is Shipped; `lint-spec-status.py`; `lint-brief-coverage.py`; `git diff --name-only`, `gh pr view` and `git log` against § Closeout.

## Acceptance Criteria

**Terms**

- **Registry token.** Any of `workspace.toml`, `workspace-status`, `workspace_status`.
- **Reader suites.** `tests/roster/test_agent_skill_engineering_consumer_integrations.py`, `tests/roster/test_close_work_extraction_and_immediate_disposition.py`, `tests/roster/test_intent_brief_registration_stop.py`, `tests/roster/test_repo_governance_rename_completeness.py`, `tests/roster/test_thirty_day_cooling_and_retirement.py`, `tests/roster/test_workspace_status_projection.py`, `tools/test_guide_typed_asides.py`, `tools/test_workspace_status_cli.py`.
- **Closeout rows.** The inventory rows whose `pattern` is `docs/product/briefs/workspace-registry-retirement-delivery.md`, `docs/product/intents/FEAT-0034-workspace-registry-retirement.md` or `docs/specs/workspace-toml-deletion/*`.
- **Permitted surfaces.** The record paths § Closeout names, and any path an amendment adds to them, the reader suites, `tests/roster/test_workspace_retirement_inventory.py`, `tests/roster/test_registry_upgrade_notes.py` (its ledger check for `retirement-record.md` and the brief, bound to 9F's merge commit, and its spec-directory row assertion), `tests/roster/test_repair_only_workspace_status.py` (its spec-directory row assertion), `tools/test_local_ci_shared_test_deduplication.py`, `.workspace-prune-protected.toml`, `tests/AGENTS.md`, `workspace.toml`, `tools/measure-changelog-conflicts.py`, `Makefile`, `.github/workflows/build-check.yml`, `.github/dependabot.yml`, `packages/agentbundle/agentbundle/build/projections/gemini_command_toml.py`, `llms.txt`, `docs/rfc/0105-artifact-derived-navigation-and-workspace-retirement.md`, `docs/rfc/0064-ini-001-ai-native-ecosystem.md`.
- **Gates.** RFC-0105 D3's four: `consumer inventory`, `state disposition`, `behavioral equivalence`, `compatibility closure`.

**Inventory check and records**

- [x] **AC-0001.** `git ls-files` lists no `.workspace-prune-protected.toml`, and `git grep` finds `.workspace-prune-protected.toml` in no tracked file outside `docs/specs/` and `docs/product/research/`.
- [x] **AC-0015.** `tests/AGENTS.md` § Roster steps says adding a roster test obliges two further edits, and lists exactly two numbered items.
- [x] **AC-0002.** `workspace-retirement`'s criterion 0011 defines the registry's key paths as a frozen list in its spec. The inventory check reads no `workspace.toml`, and a test shows the frozen list equals the key paths of `workspace.toml` at commit `3b1d0279d`.
- [x] **AC-0003.** `workspace-retirement`'s spec holds criterion 0030, and the check reports a violation under it, and no other, for a fixture breaking each clause, a row naming one tracked and one untracked path included. Criterion 0030 says:
  - § Compatibility closure holds a Markdown table with the columns Gate, Item, State, Evidence;
  - every Gate is one of the four gates, and each gate has at least one row;
  - every State is `met` or `open`;
  - every `met` row's Evidence is a `https://github.com/` Actions run URL, or names one or more paths, each resolved from the repository root and each listed by `git ls-files`.
- [x] **AC-0004.** `workspace-retirement`'s spec holds criterion 0031: once code-span marks are removed, each of these phrases is a substring of some `compatibility closure` row's Item text: `legacy entries`, `operative references and seeds`, `activation gate`, `corpus gate`, `registry contract retired`, `old skill deferred` and `workspace.toml deleted`. The Evidence of the row whose Item holds `old skill deferred` names `docs/rfc/0105-artifact-derived-navigation-and-workspace-retirement.md`. The check reports criterion 0031 for a fixture missing one item.
- [x] **AC-0005.** `workspace-retirement`'s criterion 0003 admits the owner `rfc-0067` on any class other than `historical` and `record`. Its spec holds criterion 0032: while its own `Status:` is `Shipped`, no row's owner is a slice number. The check reports criterion 0032 for a Shipped fixture with a row owned by 9, and nothing for a Draft one.
- [x] **AC-0006.** `workspace-retirement`'s spec holds criterion 0033, which applies while its `Status:` is `Shipped`, and the check reports criterion 0033 for a Shipped fixture breaking each clause. Criterion 0033 says:
  - every checklist row is `met`;
  - the first line of the certification text has the form `- **Certified:** <YYYY-MM-DD> by <signer>`, where `<signer>` contains the `- **Approver:**` value of `docs/rfc/0105-artifact-derived-navigation-and-workspace-retirement.md`;
  - at least one non-blank line follows that line;
  - `git ls-files` lists no `workspace.toml`.

  The certification text is the body of `retirement-record.md` § Certification, from the line after its heading to the end of the file, with surrounding blank lines trimmed.
- [x] **AC-0012.** RFC-0105 § Errata holds a dated entry that moves gate 4's deletion of the old skill, `workspace-status`, to the release that retires its name under RFC-0067. It also places the repair, dispatch's `unmigrated_workspace` refusal and `contracts/jsonschema/workspace-entry.schema.json` outside the registry contract this spec retires.

**Deletion**

- [x] **AC-0007.** `git ls-files` lists no `workspace.toml`, and these pass: the reader suites, `tools/test_local_ci_shared_test_deduplication.py`, `tools/measure-changelog-conflicts.py --help`, and `tests/roster/test_workspace_retirement_inventory.py`.
- [x] **AC-0016.** No inventory row other than the closeout rows has a slice number as its owner.
- [x] **AC-0008.** RFC-0064's § Errata current-state table holds a row naming D2, D4, D7, D9, the `workspace.toml` schema section and the repo-level backlog section as retired, linking RFC-0105 D3. § History / audit trail holds a dated entry for it.

## Terminal Intent

`code` — retire the prune-protection list, record the old skill's deferral, teach the inventory check its closing rules, delete `workspace.toml`, and retire RFC-0064's registry definition, so that the closeout can certify the four retirement gates.

## Closeout

The controller does this after the supervisor run is terminal and before the pull request merges. It is not a supervisor task, because the supervisor refuses a worker's change to this spec's directory. These obligations are enforced as follows: the inventory check enforces criteria 0032 and 0033 on the pull request once `workspace-retirement` is Shipped; `lint-spec-status.py` and `lint-brief-coverage.py` run in CI; and the controller checks the rest before asking for merge. A change to this section takes an amendment, like any contract section.

- **Tested commit.** The run's final product commit, kept reachable by pushing it as `evidence/workspace-toml-deletion`.
- **Record paths.** `docs/specs/workspace-retirement/retirement-record.md`, `docs/specs/workspace-retirement/spec.md`, `docs/specs/workspace-retirement/plan.md`, `docs/specs/workspace-retirement/inventory.toml`, `docs/specs/workspace-toml-deletion/spec.md`, `docs/specs/workspace-toml-deletion/plan.md`, `docs/specs/workspace-toml-deletion/notes/verification-ledger.md`, `docs/product/briefs/workspace-registry-retirement-delivery.md`, `docs/product/intents/FEAT-0034-workspace-registry-retirement.md`, `docs/product/intents/CAP-0003-workspace-coordination-reorganization.md`.
- **Gate runs.** Green `test-corpus.yml` and `test-roster.yml` runs on the tested commit. For the activation gate, a `pack-evals.yml` run for `core` on it, whose per-skill trigger-rate summary the owner reads and records as passed, or the owner's named alternative recorded the same way; the run's own conclusion does not count, because its eval step is report-only. The ledger records each run URL with the tested commit's ID and the owner's pass record, and the checklist's `corpus gate` and `activation gate` rows cite them.
- **Tree.** The files the pull request changes against its base are the files the tested commit changes against the base it was built on, without those under `docs/specs/workspace-toml-deletion/delivery/`, plus record paths. If the pull request's base moves past that base before merge, the pull request head becomes the tested commit and the gate runs are repeated on it.
- **Close-work effects.** A `close-work` write to a record path is accepted. Any other write it proposes, such as a durable-output destination or a cooling enrolment, is put to the owner. If the owner accepts it, an amendment adds its path to the record paths before it is written; otherwise it is declined, and the closure record says where that fact lives.
- **Status.** `workspace-retirement` and this spec are `Shipped` with every criterion checked. The closeout rows are `historical` with owner `none`, or owned by `rfc-0067` where criterion 0008 refuses `historical`. The brief is `Shipped` with a `Cut-closed:` record, and its Spec map lists `workspace-toml-deletion`. FEAT-0034 carries the status `close-work`'s closure gives it.
- **Certification.** The pull request's description, read with `gh pr view --json body`, and its single commit's message each contain the certification text byte for byte.
- **Approvals.** The ledger records the owner's approval of the certification text, both errata wordings, the `workspace-retirement` amendment and the checklist rows, each with the SHA-256 of the file approved.

## Follow-ons

- eugenelim: the release that retires the `workspace-status` name under RFC-0067 owns every `rfc-0067` inventory row. It also decides when the repair, dispatch's `unmigrated_workspace` refusal and the entry schema stop shipping.

## Assumptions

- **Activation gate evidence.** RFC-0105 D3 names an activation gate but does not define it. The plan reads it as `pack-evals.yml`, the report-only skill-activation eval, which calls a paid model API. If the owner names other evidence, § Closeout's alternative applies. Who settles it: eugenelim, before the closeout's gate runs.
- **9F's slug.** `Depends on:` names 9F's spec, currently `registry-upgrade-notes`, and is written at the plan's C0 step once 9F has merged. Who settles the slug: the 9F session, at its spec approval.

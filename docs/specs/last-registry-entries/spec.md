# Spec: The last registry entries leave, and refresh gets its own policy file

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0105 (D3, the retirement gates and the one retirement record), RFC-0106 (D1, a registration's readers go when its replacement ships; § Errata, each removal's authority), RFC-0083 (refresh and the source-authority record), RFC-0055 (errata entries on an Accepted RFC), ADR-0074 (standard-library skill scripts)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Depends on:** spec:pre-cutover-closure
- **Contract:** `contracts/jsonschema/source-authority.schema.json`
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

An adopter upgrading `core` moves the last work entries out of `workspace.toml` and its refresh role policy into `.work-intake.toml` with one repair run, and refresh then reads and binds only that policy file. Success is that, after the repair, `workspace.toml` holds no captured-item or slug-only entry, refresh and its remote write-back work with `workspace.toml` absent, and every deferral anchor and dispatch decision that held before still holds, apart from the three removals the RFC-0106 errata names.

## What Changes

- **Repair: `captured-entry-drop`.** A `workspace-status` step removes each captured-item membership whose file it can read and each slug-only legacy entry whose captured-item file exists, including entries a `captured-to-file` operation of the same plan just backed with a file; anything else is a manual item.
- **Repair: `refresh-policy-move`.** A `workspace-status` step copies `[authorization.refresh]` into `.work-intake.toml` and removes it from `workspace.toml`.
- **Refresh.** `work-intake`'s `scripts/refresh.py` (and its packaged copy) reads the role policy from `.work-intake.toml` and binds that file's digest on the local commit and the remote write-back alike, writes `policy_digest` in new local receipts, still takes the shared repair lock, and no longer reads `workspace.toml`. The GitHub, Jira, Jira Align and Linear refresh processor suites plant the policy file.
- **Contract.** `contracts/jsonschema/source-authority.schema.json`: a local receipt carries exactly one of `workspace_digest` and `policy_digest`.
- **Deferral anchors.** `work-loop`'s `scripts/lint-spec-status.py` resolves a `(deferred: <slug>)` marker against a captured-item file, whatever its status, in place of `[backlog].open`; `work-loop`'s SKILL.md, `new-spec`'s `references/spec-and-plan-contract.md` and the `adversarial-reviewer` agent say so.
- **Text.** `work-intake`'s SKILL.md § Refresh and `references/lifecycle-index.md`, `workspace-status`'s SKILL.md and `references/mutate.md`, and the guides that name `[authorization.refresh]` say where the policy lives and name both repair steps.
- **Governance and records.** One RFC-0106 errata entry; § Equivalence rows and a § Compatibility closure entry in the retirement record; the inventory; the brief's Spec map and after-cutover list; this spec's ledger.
- **This repository.** One repair run removes its remaining captured and slug-only entries; the roster tests that read those entries in `workspace.toml` read the captured-item files instead.
- **Release.** `core` at the next version `tools/check-core-release.py` accepts, with a changelog fragment.
- **Unchanged:**
  - `dispatch.py`, which still reads `workspace.toml` and loads the `workspace-status` engine;
  - `[authorization.migration]`, legacy migration recovery and rollback, and the `workspace-status` orientation run;
  - every refresh authority, lifecycle, approver, field and receipt check other than the policy source and the digest it binds;
  - every Shipped spec's body, and the upgrade-notes draft, which 9F corrects when it publishes it.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility: the source-authority record | Applicable: adopters' tools parse local receipts | `contracts/jsonschema/source-authority.schema.json`; `work-intake` SKILL.md § Refresh | Platform Core maintainer | AC-0008, AC-0009 pass | Schema and parser accept the same receipts |
| Interface compatibility: the refresh policy file, the repair and the anchor rule | Applicable: adopters write the policy, run the repair and defer criteria | `.work-intake.toml` shape in `work-intake` SKILL.md and `references/lifecycle-index.md`; `workspace-status` SKILL.md and `references/mutate.md`; the anchor rule in `work-loop` SKILL.md, `new-spec`'s contract reference and the `adversarial-reviewer` agent | Platform Core maintainer | AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0010, AC-0014, AC-0021 pass | Each names the current source |
| User documentation | Applicable: adopters configure refresh by hand | the guides AC-0014 lists | eugenelim, Approver | AC-0014 passes | No listed page says refresh reads `workspace.toml` |
| Decision rationale | Applicable: three dispatch behaviors are removed | RFC-0106 § Errata | eugenelim, Approver | AC-0013 passes | The entry carries owner-approved wording |
| Retirement evidence | Applicable: RFC-0105 D3 gates 3 and 4 | `retirement-record.md` § Equivalence and § Compatibility closure; `inventory.toml` | Platform Core maintainer | AC-0012, AC-0015, AC-0017 pass | The closure entry names this spec and the run |
| Delivery membership and remainder | Applicable: the after-cutover list is re-cut | `docs/product/briefs/workspace-registry-retirement-delivery.md` | eugenelim, brief owner | AC-0018 passes | The brief names 9D's items and the remainder |
| Verification record | Applicable: approvals and the run on this repository | `docs/specs/last-registry-entries/notes/verification-ledger.md` | Platform Core maintainer | AC-0011, AC-0016 pass | The ledger holds each approval and the run |
| Release history | Applicable: `core` content changes | one `docs/product/changelog.d/` fragment; `packs/core/pack.toml` and `.claude-plugin/plugin.json` | Platform Core maintainer | AC-0020 passes | The fragment names both repair steps and `.work-intake.toml` |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.
A syscall, flag, helper name, or exact write order is mechanism that belongs in
the plan's `## Design (LLD)`, not here.

### Always do

- Regenerate the projected and packaged copies with `make build-self`, bump `core` once, and carry `Engine-Change-RFC: 0106` on every commit that edits a file under `packages/agentbundle/`.
- Run the `work-intake` refresh suites, the `workspace-status` repair suites and `packs/core/tests/skills/work-loop/` after each task, and keep them passing.
- Add a file's inventory row in the same change that adds the file.

### Ask first

- The errata entry's wording, the brief's after-cutover text, the § Compatibility closure entry and the upgrade-notes draft. The owner approves each before it is committed.
- The repair run on this repository: the owner confirms the exact `repair-plan` file before `repair-apply --yes`.
- Any edit to a file outside the surfaces What Changes names.

### Never do

- Edit `packs/core/.apm/skills/work-loop/scripts/dispatch.py` or change dispatch's decision rules.
- Remove or weaken a refresh check other than the policy source and the digest it binds.
- Remove, move or rewrite a `workspace.toml` entry or table by hand; the repair alone removes them.
- Write, move or delete a captured-item file from either repair step.
- Add a dependency, a skill, a skill-script module, a finding code outside the repair's manual reasons, or a top-level directory; `.work-intake.toml` is a file.

## Testing Strategy

- **Repair steps (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005): TDD.** Each rule is a `repair-plan` or `repair-apply` result over a planted `workspace.toml` and tree, one planted entry or table per case.
- **Refresh and the contract (AC-0006, AC-0007, AC-0008, AC-0009, AC-0021): TDD.** Coordinator and remote receipt-store calls over a planted repository, the four tracker processor suites, and the schema suite with one planted receipt per case.
- **Deferral anchors (AC-0010): TDD.** The lint's anchor pass over planted specs and captured-item files.
- **This repository (AC-0011): manual QA.** One repair run and a dispatch comparison, recorded in the ledger.
- **Records and governance (AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018): goal-based.** The inventory and record check, `lint-brief-coverage.py`, and a roster check over closed lists of files and phrases.
- **Release (AC-0020): goal-based.** `tools/check-core-release.py` and the changelog checks.

## Acceptance Criteria

**Terms**

- **Base.** Commit `74f4b7248`.
- **Captured membership.** A canonical `workspace.toml` membership whose `path` is under `docs/product/captured/`.
- **Slug-only entry.** An element of a `[backlog]` collection or of an initiative's `shaping_queue.backlog` or `shaping_queue.active` that is a table with a `slug` and no `path`.
- **Readable captured file.** A regular, singly linked file inside the repository that the captured-item reader at the base accepts.
- **Policy file.** `.work-intake.toml` at the repository root, holding exactly one table, `[authorization.refresh]`, with the keys and `contract_version` refresh accepts at the base.

**Repair**

- [ ] **AC-0001.** `repair-plan` holds one `captured-entry-drop` operation for each captured membership whose `path` is a readable captured file, and for each slug-only entry for which `docs/product/captured/<slug>.md` is a readable captured file.
- [ ] **AC-0002.** Every other captured membership and slug-only entry gets no `captured-entry-drop` operation, becomes one manual item naming its locator and reason, and keeps its entry.
- [ ] **AC-0003.** `repair-apply --yes` removes exactly the entries of the `captured-entry-drop` operations whose check under the writer lock still holds, in one atomic `workspace.toml` write that keeps every byte outside the entries and tables the operations applied in that write remove, writes no file under `docs/product/captured/`, and refuses an operation whose entry or captured file changed since the plan, keeping that entry.
- [ ] **AC-0004.** When `workspace.toml` has an `[authorization.refresh]` table that refresh accepts, `repair-plan` holds one `refresh-policy-move` operation if no policy file exists, and `repair-apply --yes` creates the policy file, whose parsed table equals the moved one, and removes the table; if a policy file whose parsed table equals it exists, the operation only removes the table. An existing policy file that does not parse or whose table differs, and a table refresh does not accept, each become one manual item, and nothing moves.
- [ ] **AC-0005.** After `repair-apply --yes` applies every planned operation, including `captured-to-file` operations in the same plan, the next `repair-plan` holds no `captured-entry-drop` and no `refresh-policy-move` operation.

**Refresh and the contract**

- [ ] **AC-0006.** Refresh takes its role policy only from the policy file, refuses `invalid_refresh_policy` when the file is absent or invalid, and completes a local refresh, opens the remote receipt store, reloads its confirmations, consumes a confirmation and writes a remote-action receipt with no `workspace.toml` present.
- [ ] **AC-0007.** A refresh whose policy file changes between comparison and commit, or between opening the remote receipt store and consuming a confirmation or writing a receipt, refuses and writes nothing; a change to `workspace.toml` in either window does not refuse.
- [ ] **AC-0021.** Refresh's local commit and remote receipt write each hold the shared `.workspace-repair.lock` the repair takes, so a `refresh-policy-move` apply and a refresh commit never interleave.
- [ ] **AC-0008.** A local receipt refresh writes carries `policy_digest`, the SHA-256 of the policy file it read, and no `workspace_digest`; the record parser accepts a local receipt with exactly one of the two keys and refuses one with both or neither.
- [ ] **AC-0009.** `contracts/jsonschema/source-authority.schema.json` accepts and refuses the same four local-receipt shapes AC-0008 names.

**Deferral anchors**

- [ ] **AC-0010.** `lint-spec-status.py` resolves a `(deferred: <slug>)` marker when `docs/product/captured/<slug>.md` is a readable captured file, whatever its `Status:`, or through an open intent, brief or spec file as at the base; it resolves none through `workspace.toml`, and its unresolved-anchor message names `docs/product/captured/<slug>.md` and not `workspace.toml`.

**This repository**

- [ ] **AC-0011.** The ledger holds the `repair-plan` and `repair-apply` output of one run on this repository, with its counts of `captured-entry-drop` operations, `refresh-policy-move` operations and manual items; and the `dispatch.py` output before and after the apply, whose `ready`, `active`, `blocked` and `decision` are identical.

**Records and governance**

- [ ] **AC-0012.** `retirement-record.md` § Equivalence holds one `accepted removal` row at slice `9` for each of `the registered captured item's kind`, `the defect settled by backlog.closed`, and `the registered captured item's own findings and edges`, each citing the RFC-0106 errata entry AC-0013 names; the record check passes.
- [ ] **AC-0013.** RFC-0106 § Errata holds one owner-approved entry dated in this delivery that names those three removals and `.work-intake.toml` as the refresh policy's home.
- [ ] **AC-0014.** None of `guides/_shared/how-to/use-work-intake.md`, `guides/_shared/reference/work-intake-routing-and-lifecycle.md`, `guides/core/reference/workspace-toml-schema.md`, `packs/core/.apm/skills/work-intake/SKILL.md` or `packs/core/.apm/skills/work-intake/references/lifecycle-index.md` places `[authorization.refresh]` in `workspace.toml`, and each names `.work-intake.toml`; `packs/core/.apm/skills/workspace-status/SKILL.md` and `references/mutate.md` each name `captured-entry-drop` and `refresh-policy-move`; and none of `packs/core/.apm/skills/work-loop/SKILL.md`, `packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md` or `packs/core/.apm/agents/adversarial-reviewer.md` says a deferral anchor resolves through `[backlog].open`, and each names the captured-item file.
- [ ] **AC-0015.** `docs/specs/workspace-retirement/inventory.toml` holds a `docs/specs/last-registry-entries/*` `contract` row at owner `9`, a row for each file this spec adds that holds a registry token outside an inventoried directory, and no row for a file this spec leaves holding none; the inventory check passes.
- [ ] **AC-0016.** `docs/specs/last-registry-entries/notes/verification-ledger.md` records eugenelim's approval of the errata entry, the brief text, the closure entry and the repair plan applied to this repository, each with the SHA-256 of the file approved; the errata approval precedes the run.
- [ ] **AC-0017.** `retirement-record.md` § Compatibility closure holds an entry that links `../last-registry-entries/spec.md` and names `captured-entry-drop`, `refresh-policy-move`, `.work-intake.toml` and the AC-0011 counts.
- [ ] **AC-0018.** The brief's Spec map lists `last-registry-entries`, its "After the cutover" list keeps each item's text at the base and names `last-registry-entries` beside the legacy-entry removal and the policy tables' home, and `lint-brief-coverage.py` passes.

**Release**

- [ ] **AC-0020.** `tools/check-core-release.py --base` the merge base with freshly fetched `origin/main` passes, and one `docs/product/changelog.d/` fragment for `core` at the new version names `captured-entry-drop`, `refresh-policy-move` and `.work-intake.toml`.

## Terminal Intent

`code` — remove the last registry entries with the repair, move the refresh policy to `.work-intake.toml`, and release `core`.

## Follow-ons

- eugenelim: 9F corrects the upgrade-notes draft for the policy file and both repair steps, with PCC-ADV-05, when it publishes it.
- eugenelim: the brief's remaining after-cutover items — headers-only dispatch and a repair-only `workspace-status` with `[authorization.migration]` retired (9E), publishing the upgrade notes and moving references (9F), and the closure checklist, certification and deletion (9G).

## Assumptions

- Product: adopters' captured memberships that the reader refuses are invisible from here — whether many become manual items in practice is ungrounded, and the manual item is the only notice.

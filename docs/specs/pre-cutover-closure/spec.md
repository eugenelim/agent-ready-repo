# Spec: Pre-cutover compatibility closure

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-30 by eugenelim, spec and plan at `3ace13ecb`, after three spec-mode shaping and adversarial review rounds, each adjudicated, with the round-3 repair accepted unreviewed and AC-0020 kept at the deletion pass; records under `.context/reviews/87a629cd-91c6-435b-b8a2-edac5914679e/`.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0105 (D3, gate 4 and the one retirement record), RFC-0106 (D1, a registration's readers and writers go when its replacement ships; § Errata, the removals the upgrade notes list), ADR-0074 (standard-library skill scripts)
- **Brief:** brief:workspace-registry-retirement-delivery
- **Discovery:** none
- **Depends on:** spec:tracker-origin-registration-stop
- **Contract:** none — the inventory's shape is contracted by the `workspace-retirement` spec, which this spec amends.
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

A maintainer finishing the `workspace.toml` retirement finds no registry field left in `close-work`, no inventory row owned by a delivery slice that has finished, and a reviewed draft of the adopter upgrade notes ready to publish. Success is that `close-work`'s closure packet carries no registry field, every numbered inventory row is owned by slice 9 and the inventory check enforces that, and the draft tells an adopter to run the repair in a session and names each removed behavior the retirement record and RFC-0106's errata authorise.

## What Changes

- **Closure packet.** `close-work`'s `scripts/closure_index.py` loses the `workspace_registration` packet field, the `WorkspaceLookup` type and the `_workspace_lookup` seam on `check_ancestor_closure`; the two tests that filled the field go, the other packet tests stop passing the seam, and the `.claude/` and `.agents/` projections follow.
- **Closure-eligibility record.** The Shipped `closure-eligibility-check` spec's `Status:` line names this spec as superseding its criterion 0031.
- **Eval.** `close-work`'s `evals/evals.json` gains a case for a packet that names no registry entry.
- **Inventory.** In `docs/specs/workspace-retirement/inventory.toml`, the 19 rows owned by slices 2 to 8 become 10 `historical` rows with owner `none` (the nine slice 2 to 8 spec directories and `FEAT-0002`) and 9 rows owned by slice 9. This spec adds three rows — its directory, the draft and its roster check — and a fourth for the changelog fragment only if the fragment holds a registry token.
- **Retirement spec amendment.** `workspace-retirement`'s spec gains criterion 0029, that a numbered owner is the brief's last slice, and its plan gains a task; its inventory check (`tests/roster/test_workspace_retirement_inventory.py`) enforces the rule, and its base fixtures move to owner 9.
- **Roster check.** `tests/roster/test_pre_cutover_closure.py`, with its named step in `.github/workflows/build-check.yml`, its `tools/lint-ci-parity.py` entry and its `.workspace-prune-protected.toml` line.
- **Upgrade notes draft.** `docs/specs/pre-cutover-closure/notes/upgrade-notes.md`, unpublished, in the `guides/` how-to shape.
- **Records.** The retirement record's § Compatibility closure, the brief's Spec map and slice 9 text, and this spec's ledger.
- **Release.** `core`'s `pack.toml` and `.claude-plugin/plugin.json` at the next patch version, the regenerated `.claude-plugin/marketplace.json`, and one changelog fragment.
- **Unchanged:**
  - `work-loop`, `dispatch.py`, `workspace-status` and every file under their skill directories;
  - every packet field other than `workspace_registration`, and every closure verdict;
  - every page under `guides/`;
  - every other file an inventory row governs.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility: the closure packet | Applicable: adopters' callers of `check_ancestor_closure` see the field and seam go | `packs/core/.apm/skills/close-work/scripts/closure_index.py` | Platform Core maintainer | AC-0001, AC-0002, AC-0003, AC-0004 and AC-0020 pass | The packet and the call signature match AC-0001 and AC-0002 |
| Decision rationale | Applicable: a Shipped spec's criterion 0031 stops holding | `docs/specs/closure-eligibility-check/spec.md` `Status:` line | Platform Core maintainer | AC-0005 passes | The line names this spec and criterion 0031 |
| User documentation: the upgrade | Applicable: adopters upgrade by running the repair | `docs/specs/pre-cutover-closure/notes/upgrade-notes.md`, a draft; publishing it is the brief's after-cutover item | eugenelim, Approver | AC-0012, AC-0013, AC-0014, AC-0015 and AC-0016 pass | The owner has approved the wording |
| Retirement evidence | Applicable: RFC-0105 D3 gate 4 | `docs/specs/workspace-retirement/retirement-record.md` § Compatibility closure; `inventory.toml`; the `workspace-retirement` spec and plan | Platform Core maintainer | AC-0007, AC-0008, AC-0009, AC-0010, AC-0011 and AC-0017 pass | The closure entry names this spec |
| Delivery membership and remainder | Applicable: the brief's coverage map and slice 9 cut | `docs/product/briefs/workspace-registry-retirement-delivery.md` | eugenelim, brief owner | AC-0018 passes | The brief names this spec for its three items |
| Verification record | Applicable: approvals and the test comparison | `docs/specs/pre-cutover-closure/notes/verification-ledger.md` | Platform Core maintainer | AC-0016 and AC-0020 pass | The ledger holds each approval and the comparison |
| Release history | Applicable: `core` content changes | one `docs/product/changelog.d/` fragment; `packs/core/pack.toml` and `.claude-plugin/plugin.json` | Platform Core maintainer | AC-0019 passes | The fragment names the retired field |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.
A syscall, flag, helper name, or exact write order is mechanism that belongs in
the plan's `## Design (LLD)`, not here.

### Always do

- Regenerate the projected copies with `make build-self` after any `.apm/` edit, and bump `core` once.
- Run `packs/core/tests/skills/close-work/` and `tests/roster/test_workspace_retirement_inventory.py` after each task, and keep them passing.
- Change an existing inventory row only in its `class`, `owner` or `consumer`; its `pattern` and its place in the file stay.
- Add a file's inventory row in the same task that adds the file.

### Ask first

- The upgrade notes' wording, the brief's slice 9 and Spec map text, the § Compatibility closure entry, and the `workspace-retirement` spec and plan amendment. The owner approves each before it is committed.
- Any edit to a file outside the surfaces What Changes names.

### Never do

- Edit a file under `packs/core/.apm/skills/work-loop/`, `packs/core/.apm/skills/workspace-status/`, `guides/`, or any of their projections.
- Edit a file only to drop its registry mention so that its row can go.
- Change a `close-work` packet field other than `workspace_registration`, or any closure verdict or refusal.
- Add a dependency, a skill, a skill-script module, a finding code, an inventory class, or a top-level directory.
- Add, move or remove a `workspace.toml` entry.

## Testing Strategy

- **Closure packet (AC-0001, AC-0002, AC-0003): TDD.** Each reds against the base `closure_index.py`: the field set, the signature and the token scan are function calls over the module.
- **Close-work regression (AC-0004, AC-0020): goal-based.** AC-0004 is the regression oracle and passes at the base by design; AC-0020 is an AST comparison of the close-work tests with the base, run once and recorded in the ledger.
- **Closure-eligibility record and eval (AC-0005, AC-0006): goal-based.** The roster check reads the `Status:` line and the eval file.
- **Inventory and the owner rule (AC-0007, AC-0008, AC-0009, AC-0010, AC-0011): TDD and goal-based.** The new rule reds on a fixture row owned by slice 8; the inventory check over this repository is the goal check.
- **Upgrade notes (AC-0012, AC-0013, AC-0014, AC-0015, AC-0016): goal-based.** The roster check parses the draft's frontmatter against `contracts/guide.schema.json`, reads its closed list of facts and links, and reads the ledger's approval rows.
- **Records and release (AC-0017, AC-0018, AC-0019): goal-based.** The roster check reads the closure entry; `lint-brief-coverage.py`, `tools/check-core-release.py` and the changelog checks.

## Acceptance Criteria

**Terms**

- **Base.** Commit `f9bbf6ea1`.
- **Module.** `packs/core/.apm/skills/close-work/scripts/closure_index.py`.
- **Re-owned rows.** The inventory rows whose `pattern` is `docs/adr/0103-the-completion-receipt-carries-a-delivery-outcome-not-a-disposition.md`, `docs/adr/0148-completion-receipt-rides-on-the-waiting-items-header.md`, `docs/product/intents/CAP-0004-external-tracker-projection.md`, `docs/product/workspace-toml-deps.md`, `packages/agentbundle/tests/test_workspace_mcp_depends_on.py`, `tests/roster/test_priority_field_never_read.py`, `tests/roster/test_depends_on_headers_instructions.py`, `tools/compare-registry.py` or `tools/test_compare_registry.py`.
- **Historical rows.** The inventory rows whose `pattern` is `docs/product/intents/FEAT-0002-intent-graph-navigation.md` or `docs/specs/<dir>/*` for `<dir>` one of `depends-on-headers`, `captured-item-files`, `captured-item-registration-stop`, `spec-registration-stop`, `readiness-bridge-dispatch-input`, `intent-brief-registration-stop`, `next-item-suggestions-removal`, `priority-header-field`, `registry-comparison`.
- **Removed behaviors.** The record's seven `deliberate removal` facts — `<initiative>`, `<initiative>.name`, `<initiative>.status`, `<initiative>.milestone`, `<initiative>.parent`, `entry position`, `behavior outside tracked files` — and the per-entry refresh status (`origin_mode`, `profile`, `refresh`) that the RFC-0106 errata entry of 2026-10-30 removes.
- **Draft.** `docs/specs/pre-cutover-closure/notes/upgrade-notes.md`.
- **Registry token.** Any of `workspace.toml`, `workspace-status`, `workspace_status`.

**Closure packet**

- [ ] **AC-0001.** The names of `dataclasses.fields(EligiblePacket)` in the module are exactly `decision_date`, `decider`, `stated_outcome`, `ratified_decomposed`, `ratified_child_count`, `verification_basis`, `per_descendant_verdicts`, `stated_confidence`, `outcome_co_owner`, `disposition_row`, in that order.
- [ ] **AC-0002.** The parameter names of the module's `check_ancestor_closure` are exactly those at the base without `_workspace_lookup`, in the base order.
- [ ] **AC-0003.** The module's text holds none of `workspace.toml`, `workspace_registration`, `WorkspaceLookup`, `workspace_lookup`.
- [ ] **AC-0004.** `packs/core/tests/skills/close-work/` passes.
- [ ] **AC-0020.** The ledger holds an AST comparison of every module-level function under `packs/core/tests/skills/close-work/` with the base, showing that: every base function other than `test_ac0031_workspace_registration_named_in_packet` and `test_ac0031_no_registration_when_lookup_returns_none` exists in the same file with an identical body apart from removed `workspace_lookup=` keywords; `_call_eligible` differs only by the removed `workspace_lookup` parameter and `_workspace_lookup` keyword; and every added function is in `test_closure_packet.py` with a name starting `test_pre_cutover_`.
- [ ] **AC-0005.** The `- **Status:**` line of `docs/specs/closure-eligibility-check/spec.md` still begins `Shipped`, keeps its existing supersession note, and holds a link to `../pre-cutover-closure/spec.md` naming criterion `0031`.
- [ ] **AC-0006.** `packs/core/.apm/skills/close-work/evals/evals.json` holds one case whose assertions require that an eligible closure packet names no `workspace.toml` entry.

**Inventory**

- [ ] **AC-0007.** No row of `docs/specs/workspace-retirement/inventory.toml` has an `owner` from 2 to 8.
- [ ] **AC-0008.** Each historical row has `class = "historical"` and `owner = "none"`.
- [ ] **AC-0009.** Each re-owned row has `owner = 9` and its class at the base.
- [ ] **AC-0010.** The inventory holds a `docs/specs/pre-cutover-closure/*` row with `class = "contract"` and `owner = 9`; before it, a row whose `pattern` is the draft with `class = "guide"` and `owner = 9`; a row for each other file this spec adds that holds a registry token outside an inventoried skill or spec directory; and no row for a file this spec leaves holding no registry token. `tests/roster/test_workspace_retirement_inventory.py` passes on this repository.
- [ ] **AC-0011.** `docs/specs/workspace-retirement/spec.md` holds a criterion that a row whose `owner` is a slice number has the highest number the brief's `## Delivery slices` lists, and the inventory check reports a violation under that criterion's identifier, and no other, for an otherwise valid fixture row owned by slice 8 of a nine-slice brief.

**Upgrade notes**

- [ ] **AC-0012.** The draft opens with frontmatter that validates against `contracts/guide.schema.json` with `pack: core` and `kind: how-to`, and its first body heading is `# ` followed by the frontmatter `title`.
- [ ] **AC-0013.** The draft names the `workspace-status` `repair-plan` and `repair-apply --yes` commands, with `repair-plan` first, as the upgrade an adopter runs in an agent session.
- [ ] **AC-0014.** The draft names each removed behavior in backticks.
- [ ] **AC-0015.** The draft holds the Markdown link targets `../../../rfc/0106-stop-registering-derivable-work.md#errata` and `../../workspace-retirement/retirement-record.md#disposition`, each resolving from the draft's directory to a tracked file, and names the dates `2026-10-25` and `2026-10-30`.
- [ ] **AC-0016.** `docs/specs/pre-cutover-closure/notes/verification-ledger.md` records eugenelim's approval of the draft, of the § Compatibility closure entry, of the brief text, and of the `workspace-retirement` spec and plan amendment, each with the SHA-256 of each file approved.

**Records**

- [ ] **AC-0017.** `retirement-record.md` § Compatibility closure holds an entry that links `../pre-cutover-closure/spec.md` and names `workspace_registration`, the counts `10` historical and `9` re-owned rows, and the draft's path.
- [ ] **AC-0018.** The brief's Spec map lists `pre-cutover-closure`, each of the three remaining "Before the execution-supervisor cutover" items names `pre-cutover-closure`, and `lint-brief-coverage.py` passes on the brief.

**Release**

- [ ] **AC-0019.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` both carry the patch successor of `packs/core/pack.toml`'s version at the merge base with freshly fetched `origin/main`, and one `docs/product/changelog.d/` fragment for `core` at that version names `workspace_registration`; `tools/check-core-release.py --base` that merge base passes.

## Terminal Intent

`code` — retire `close-work`'s registry field, re-own the inventory, draft the upgrade notes, and release `core`.

## Follow-ons

- eugenelim: the brief's "After the cutover" list in `docs/product/briefs/workspace-registry-retirement-delivery.md` — publishing the draft (moving it under `guides/core/how-to/` and re-pointing its links), the engine rules `dispatch.py` needs, shrinking `workspace-status`, the legacy entries, the `[authorization.*]` tables' home, the closure checklist, the certification, and deleting `workspace.toml`.

## Assumptions

- Product: adopters with callers of `check_ancestor_closure` that pass `_workspace_lookup` are invisible from here — the leading underscore marks it a test seam, and a caller that passes it gets a `TypeError` after the release.

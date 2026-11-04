# Plan: Closing the workspace retirement and deleting workspace.toml

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:**
  - RFC-0105 D3 (line 112), gate 4 at line 121, and the certification sentence after the gate list; RFC-0064 § Errata (line 626), whose current-state table ends at row 13; RFC-0055.
  - `tests/roster/test_workspace_retirement_inventory.py`: `_LITERAL_FACTS` (line 435), `_REGISTRY_PATH` (line 447), `_registry_facts` (line 500), `_fact_set` (line 523, which parses the registry at line 536), `check_inventory` (line 274, the owner rule at lines 303 to 320), `check_record` (line 687), the fixture builder that writes a registry (line 1353).
  - `docs/specs/workspace-retirement/spec.md`: criteria 0003 (line 100), 0011, 0018 and 0022; the last two list the enforced rules, criteria 0001 to 0029.
  - `tests/AGENTS.md` § Roster steps, item 3 (line 44); `docs/specs/workspace-retirement/inventory.toml` line 61, the prune-protection list's row.
  - `packs/core/.apm/skills/work-loop/scripts/dispatch.py` `_read_workspace` (line 238): an absent `workspace.toml` reads as `None`, so dispatch needs no change; `workspace_status.py repair-plan` on a repository with no file reports `workspace_present: false` and exits 0.
  - RFC-0105 § Errata (line 278) and its line-163 rule that a D3 constraint changes only by amendment or erratum.
  - `docs/specs/pre-cutover-closure/`: the precedent for amending `workspace-retirement`, the ledger, and the record entry.
  - `.claude/skills/work-loop/scripts/_supervisor_loop.py` `_refuse_protected_change` (line 719): a worker change to this spec's directory or a cited record refuses `protected-path-changed`; `_supervisor_readiness.py` `criteria` (line 87): run-gates asks for every criterion in § Acceptance Criteria; `_loop_guards.py` `local_dep_ids` (line 911) keeps only `T<n>` dependencies. `origin/evidence/repair-only-workspace-status`: the precedent for an evidence branch.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, closeout, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open.
> Execution observations belong in `notes/verification-ledger.md`.

## Approach

The work runs in three stages, all after slice 9F has merged to `main`, split by RFC-0105 D3 gate 4's order and by what the supervisor admits. The supervisor pins its own scripts and the cited records at `start` and refuses every verb once either changes, so a merge from `main` mid-run would void the run; the run therefore starts on a branch from `origin/main` fetched after 9F's merge and takes nothing from `main` while open. Before `start`, the controller commits the RFC-0105 erratum (C0) with the approved spec and plan, because RFC-0105 is a cited record a worker may not change. The run then builds T1 to T6 straight through, and its final product commit is the tested commit. The closeout (C1 to C5) then writes only record paths. The riskiest step is freezing criterion 0011's fact set, and T2's test pins the frozen list to the registry at `3b1d0279d`.

## Constraints

- RFC-0105 D3 gate 4: deletion follows the removal of operative references and seeds and the activation and corpus gates. The deletion reaches `main` only when the pull request merges, after the closeout's gate runs on the tested commit. The certification is the Approver's, given in the spec and in the pull request.
- The supervisor admits no worker change to this spec's directory or to RFC-0105, and asks run-gates for every acceptance criterion. Ledger writes, the certification and the Shipped moves are therefore closeout steps, and the closeout obligations sit in the spec's § Closeout.
- The owner's no-seam decision (FEAT-0034, 2026-10-25): the repair keeps shipping, and so do the files it needs. No file under `packs/` changes. Slice 9F makes intent renames work with no `workspace.toml` (owner decision, 2026-11-03), and the second part relies on that.
- RFC-0055: an Accepted RFC changes only through its § Errata current-state table and audit trail.
- `tests/AGENTS.md` § Roster steps: no new roster module, so no `build-check.yml` or `tools/lint-ci-parity.py` edit.
- The inventory check runs on every pull request. Each task adds or drops the rows for the files it touches.

## Construction tests

**Integration tests:** none beyond per-task tests.
**Manual verification:** the owner reads the checklist, the errata wording and the certification text before each is committed.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Old-skill deferral erratum | C0 | the RFC-0105 § Errata entry | AC-0012 checked; ledger approval |
| Roster admission rule | T1 | `git grep` and the `tests/AGENTS.md` read | AC-0001 and AC-0015 checked |
| Inventory check and retirement spec amendment | T2 | the check's fixture tests; the frozen-list comparison test | AC-0002 to AC-0006 checked |
| Closure checklist | T3, C2 | the check's criteria 0030 and 0031 over this repository | criterion 0033 over this repository |
| Inventory | T4, T5, C3 | the check over this repository | AC-0007 and AC-0016 checked; criterion 0032 |
| RFC-0064 errata | T6 | the RFC-0064 § Errata row | AC-0008 checked; ledger approval |
| Certification, Shipped specs, brief closure | C3, C5 | criterion 0033; `lint-spec-status.py`; `lint-brief-coverage.py`; `close-work` | § Closeout |
| Verification record | C1, C4 | `notes/verification-ledger.md` | every approval carries a SHA-256 |

## Design (LLD)

### Design decisions

Owned by: T2, T4, T5, C3.


- **Frozen fact set.** Criterion 0011's registry key paths become the 19 paths the registry holds at `3b1d0279d`, written into the spec as a closed list and into the check as a literal tuple:
  - `<initiative>`, plus its `name`, `status`, `milestone` and `parent`;
  - `<initiative>.brief_queue` and its `draft`, `executing`, `ready` and `shipped`;
  - `<initiative>.shaping_queue` and its `active` and `backlog`;
  - `<initiative>.work` and its `active`, `queue` and `shipped`;
  - `backlog` and `backlog.open`.

  The schema facts still come from `contracts/jsonschema/workspace-entry.schema.json`, which stays.
- **The `rfc-0067` owner.** A live row that outlives slice 9 names the release that retires the `workspace-status` name. criterion 0029's highest-slice rule still governs numbered owners. criterion 0032 removes numbered owners once the retirement spec ships.
- **Dormant closing rules.** criterion 0032 and criterion 0033 apply only while `docs/specs/workspace-retirement/spec.md`'s `Status:` is `Shipped`. criterion 0030 and criterion 0031 apply at all times, so the drafted checklist is checked from T3 on.
- **Reader suites after deletion.** A suite that asserts the registry holds no entry of some kind treats an absent file as holding none. `test_workspace_status_projection.py`'s class over the real registry is removed, because its subject is gone. Synthetic-fixture tests stay. `tools/test_workspace_status_cli.py` finds the root by `AGENTS.md` and `packs/`. `test_agent_skill_engineering_consumer_integrations.py` drops `workspace.toml` from `BOUND_SURFACES`, because the file it binds is gone. A probe at `3b1d0279d` with the file removed found exactly these eight suites and the inventory check red, out of every test module that names `workspace.toml`. Two others, `view_browser_checks.py` and `atlassian_jira_epic_outcome_view_guarantees.py`, already collect no passing test at the base, and `tools/test_local_ci_shared_test_deduplication.py` reds only through the CLI suite's root finder.
- **Rows that settle only at closeout.** Three rows have live targets until the closeout closes them: the brief (`docs/product/briefs/workspace-registry-retirement-delivery.md`), this spec's directory, and FEAT-0034. T5 leaves them owned by 9. C3 makes them `historical` with owner `none` once each target is terminal under criterion 0008. If `close-work` leaves FEAT-0034 non-terminal, its row takes `rfc-0067`.
- **Measurement tool.** `tools/measure-changelog-conflicts.py` keeps `workspace.toml` in `WATCHED_PATHS`, because it measures history and the path stays meaningful in `git log`. Its row becomes `historical` if criterion 0008 admits that, or `rfc-0067` if not.

### Behavior & rules

Owned by: T2, T3.

- The check reads the retirement spec's own `Status:` from `docs/specs/workspace-retirement/spec.md` in the checked root. A fixture repository writes one.
- criterion 0033's Approver comes from RFC-0105's `- **Approver:**` line in the checked root, never from a literal.
- The checklist table sits under § Compatibility closure, after the existing dated entries. Criterion 0010 counts only `## ` headings, so a `### Checklist` subheading is allowed.

### Drafted checklist

Owned by: T3, C2.

| Gate | Item | State after T3 | Evidence |
| --- | --- | --- | --- |
| consumer inventory | every tracked file with a registry token has a governing row | met | `docs/specs/workspace-retirement/inventory.toml`; `tests/roster/test_workspace_retirement_inventory.py` |
| consumer inventory | no row is owned by a slice number | open | — |
| state disposition | every registry fact has a home and an owner | met | `docs/specs/workspace-retirement/retirement-record.md` |
| state disposition | every deliberate removal cites accepted authority | met | `docs/specs/workspace-retirement/retirement-record.md`; `docs/rfc/0106-stop-registering-derivable-work.md` |
| behavioral equivalence | every equivalence case is reproduced, an accepted removal or an intended change | met | `docs/specs/workspace-retirement/retirement-record.md` |
| behavioral equivalence | the headers-only dispatch replay found 0 differing outputs | met | `docs/specs/repair-only-workspace-status/notes/verification-ledger.md` |
| compatibility closure | legacy entries migrated or retired | met | `docs/specs/last-registry-entries/notes/verification-ledger.md` |
| compatibility closure | operative references and seeds removed | open | — (9F's spec, once merged) |
| compatibility closure | upgrade notes published | open | — (9F's guide page, once merged) |
| compatibility closure | prune-protection list retired | met | `tests/AGENTS.md` |
| compatibility closure | old skill deferred to the RFC-0067 release | met | `docs/rfc/0105-artifact-derived-navigation-and-workspace-retirement.md` |
| compatibility closure | registry contract retired in RFC-0064 | open | — |
| compatibility closure | activation gate passed | open | — |
| compatibility closure | corpus gate passed | open | — |
| compatibility closure | workspace.toml deleted | open | — |

## Tasks

### T1: Retire the prune-protection list

- **Depends on:** none
- **Verification mode:** goal-based
- **Touches:** `.workspace-prune-protected.toml`, `tests/AGENTS.md`, `docs/specs/workspace-retirement/inventory.toml`
- **Tests:** for AC-0001: `git ls-files .workspace-prune-protected.toml` is empty; `git grep -l workspace-prune-protected -- ':!docs/specs' ':!docs/product/research'` is empty; the inventory check passes with the line-61 row gone. For AC-0015: `tests/AGENTS.md` § Roster steps reads "obliges two further edits" and lists exactly two numbered items.
- **Done when:** each holds.

### T2: Amend the retirement spec and teach the check its closing rules

- **Depends on:** none
- **Verification mode:** TDD
- **Touches:** `docs/specs/workspace-retirement/spec.md`, `docs/specs/workspace-retirement/plan.md`, `tests/roster/test_workspace_retirement_inventory.py`
- **Tests:** for AC-0002: a fixture record missing one frozen key reds criterion 0011 without any registry file; a test that parses `git show 3b1d0279d:workspace.toml` and asserts `_registry_facts` of it equals the frozen tuple (build-check checks out with `fetch-depth: 0`). For AC-0003, AC-0004, AC-0005 and AC-0006: one planted fixture per clause of criteria 0030, 0031, 0032 and 0033, each reporting only its own identifier, plus a Draft-status control for the two dormant rules. `test_clean_base_fixture_passes` gains a valid checklist table and stays empty.
- **Approach:** the worker applies the `workspace-retirement` amendment text the owner approved before this task's attempt (criteria 0003 and 0011 reworded, criteria 0030 to 0033 added, criteria 0018 and 0022's rule lists extended and unchecked, a task added), then the check, so each new rule reds before it exists. The owner's re-approval is written onto that spec's `Approved:` line at C3.
- **Done when:** the check passes over this repository.

### T3: Draft the closure checklist

- **Depends on:** T1, T2
- **Verification mode:** goal-based
- **Touches:** `docs/specs/workspace-retirement/retirement-record.md`
- **Tests:** for AC-0003 and AC-0004 over this repository: the drafted table under § Compatibility closure, with the rows the owner approved, and criteria 0030 and 0031 pass on it. For AC-0012: the RFC-0105 § Errata entry committed at C0 holds what AC-0012 names, as the `old skill deferred` row's Evidence cites it.
- **Done when:** the check passes.

### T4: Delete workspace.toml and fix its readers

- **Depends on:** T3
- **Verification mode:** goal-based
- **Touches:** `workspace.toml`, the reader suites, `tools/measure-changelog-conflicts.py`, `Makefile`, `.github/workflows/build-check.yml`, `.github/dependabot.yml`, `packages/agentbundle/agentbundle/build/projections/gemini_command_toml.py`, `llms.txt` (only if 9F left its link), `tools/test_local_ci_shared_test_deduplication.py` (only if it still reds), `docs/specs/workspace-retirement/inventory.toml`
- **Tests:** for AC-0007: each reader suite passes with the file absent; `python3 tools/measure-changelog-conflicts.py --help` exits 0; `make lint-ruff lint-mypy`; the inventory check passes, with the rows for files that lost their last registry token removed.
- **Done when:** each passes.

### T5: Re-own the remaining rows

- **Depends on:** T4
- **Verification mode:** goal-based
- **Touches:** `docs/specs/workspace-retirement/inventory.toml`
- **Tests:** for AC-0016: every former slice-9 row other than the closeout rows is `historical` and `none` where criterion 0008 admits it, or keeps its class with owner `rfc-0067`. The check passes.
- **Done when:** it passes.

### T6: Retire RFC-0064's registry definition

- **Depends on:** T4
- **Verification mode:** goal-based
- **Touches:** `docs/rfc/0064-ini-001-ai-native-ecosystem.md`
- **Tests:** for AC-0008: current-state row 14 and its audit-trail entry, with the wording the owner approved before this task's attempt; the inventory check, whose criterion 0021 keeps RFC-0064 a `contract` row while it mentions the registry.
- **Done when:** both hold.

## Controller steps outside the run

These are not supervisor tasks. C0 runs before `start`; C1 to C5 run after `next` answers `terminal`, in order, and write only the record paths of the spec's § Closeout.

- **C0, before `start`, after 9F merges: the branch and the RFC-0105 erratum.** A branch from `origin/main` fetched after 9F's merge; the owner's erratum wording and the spec's `Depends on:` set to 9F's spec, committed with the approved spec and plan. Check: AC-0012 holds; `git merge-base --is-ancestor <9F merge commit> HEAD`.
- **C1: gate runs.** Push the run's final product commit as `evidence/workspace-toml-deletion`; that commit is the tested commit. `gh workflow run test-corpus.yml` and `test-roster.yml` with `--ref evidence/workspace-toml-deletion`, both green on it; `pack-evals.yml` with `packs: core` only after the owner agrees, then the owner reads its trigger-rate summary artifact and records pass or fail; or the owner's named alternative. Check: each run's `headSha` equals the tested commit, and the owner's pass record exists.
- **C2: the checklist.** Every row set to `met` with its path or run URL. Check: criteria 0030 and 0031 pass.
- **C3: certification and status.** The owner's re-approval of the `workspace-retirement` amendment on that spec's `Approved:` line; the owner's certification text in § Certification; `workspace-retirement` and this spec `Shipped` with every criterion checked; `close-work` run on the brief, each proposed write outside the record paths put to the owner as § Closeout says; then the closeout rows re-owned as `## Design (LLD)` says. Check: the inventory check passes, criteria 0032 and 0033 included; `lint-spec-status.py --root .`; `lint-brief-coverage.py --root .`.
- **C4: the ledger.** `notes/verification-ledger.md` with the tested commit, each run URL, the frozen-list comparison, and each owner approval with its file's SHA-256. Check: § Closeout's approvals bullet holds.
- **C5: the pull request.** Squash the branch to one commit on the base the run started from, with `delivery/` dropped, its message holding the certification text; open the pull request with the same text in its description. Check: the files `git diff --name-only <base> HEAD` lists are those `git diff --name-only <base> <tested commit>` lists, without `delivery/` files, plus record paths; if `main` moves and the pull request takes it in, C1's runs repeat on the new head; `gh pr view --json body` and `git log -1 --format=%B` each contain the certification text.

## Rollout

- **Delivery:** one pull request and no pack release, opened at C5 after 9F merges and the run is terminal.
- **Reversal:** revert the pull request to restore `workspace.toml`. Adopters are unaffected either way, because nothing under `packs/` changes.

## Risks

- 9F may drop a registry mention from a file whose row this branch also touches. Starting after 9F's merge means T4 and T5 see 9F's rows, and the inventory check names any row left behind.
- A row whose target is a live, non-terminal artifact cannot become `historical` (criterion 0008). It takes the `rfc-0067` owner instead.
- `main` moving during the closeout repeats C1's runs on the new head.

## Changelog

- 2026-11-03: spec approved by eugenelim (spec sha256 `df3dec6e444d262a584d8a5f47f38145ce2e09d9a340d95667e7ff15dda4d357`).
- 2026-11-03: plan approved by eugenelim (plan sha256 `8a41b8e11ef277a2e0b9d886e79bf0272265b5aaad4916de0dec06600e05000c`).

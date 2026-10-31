# Spec: Supervisor status in a checkout without the run's store

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Approved:** 2026-10-30 by eugenelim, spec at `01c13d980`, after four spec-stage rounds of shaping, adversarial and secure-design review, each adjudicated (round 4 adversarial only); the round-4 one-sentence repair to the Testing Strategy was accepted unreviewed. Records under `.context/reviews/12f339cc-9463-4289-b3d0-f1f07e3980f3/`.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0144 (the skill-shipped supervisor owns work-loop procedure), ADR-0074 (standard-library skill scripts)
- **Brief:** none
- **Discovery:** none
- **Depends on:** spec:execution-supervisor-attempt-security
- **Amends:** [execution-supervisor-attempt-security](../execution-supervisor-attempt-security/spec.md) — its pin-check criterion (number 0014), for the `status` verb only, on a run that has no store in the checkout. It also narrows the 2026-10-21 owner re-decision in that spec's verification ledger, which refuses every entry point on a run with committed approvals and no store: that refusal still holds for every verb but `status`.
- **Contract:** none
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy`,
> `Acceptance Criteria`, `Terminal Intent` and `Accepted Risk` are what a
> completion gate reads, and an amendment changes them. `Outcome`, `What
> Changes`, `Durable Outputs`, `Follow-ons` and `Assumptions` are working
> material: they orient a reader and an author corrects them in place as the
> work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because
> nothing gates the text it cites.

## Outcome

A maintainer, CI job, or adopter who checks out a branch or `main` holding a spec's committed `delivery/` records gets a `work-supervisor.py status --check` answer, and so a pre-PR hook result, decided by those committed records, with the output saying that no pin comparison was made. Success is that a fresh clone of a branch whose spec carries a terminal run's records passes `status --check` and the shipped pre-PR hook, while a changed installed supervisor during a live local run, a damaged local store, and every verb that advances a run still refuse `supervisor-changed`.

## What Changes

- **Pre-import check.** `work-supervisor.py`'s check before any sibling loads lets `status` through when the spec's run has no store directory in the checkout — `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py`.
- **Pin check after import.** The attempt store's pin check records whether it compared pins, and skips the comparison for `status` on a run with no store — `packs/core/.apm/skills/work-loop/scripts/_supervisor_attempt.py`.
- **Status output.** Every `status` view carries `verification`: `pinned` or `committed-records-only`.
- **Reference and architecture.** `work-loop`'s `references/supervisor.md` (§ Refusals, § Status, resume, and the retry cap, § What the supervisor writes) and `docs/architecture/work-loop-execution-supervisor.md` say what a checkout without the store verifies, and what to do with a finished run's store once a later release changes the installed supervisor.
- **Roster case.** `test_pre_pr_passes_when_no_spec_holds_approvals` leaves every spec's `delivery/` out of its sandbox, so it keeps testing a tree with no approvals — `tests/roster/test_core_pre_pr_hook.py`.
- **Captured defect.** `docs/product/captured/supervisor-common-config-residue.md` records the separate `attempt-residue: common:config` defect.
- **Release.** One `core` patch release and one changelog fragment.
- **Unchanged:** `start`, `next`, `report` and `resolve-effect` behaviour; the pinned file set; the store layout; the pre-PR hook; the security-event schema; and the body of every Shipped spec.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility: the `status` output and refusals | Applicable: controllers and hooks read `status --json` and its exit code | `packs/core/.apm/skills/work-loop/references/supervisor.md` | Platform Core maintainer | AC-0001 to AC-0006 pass; the reference states the `verification` field and the no-store rule | The reference's Refusals row for `supervisor-changed` and its Status section name the `status` exception |
| Current architecture | Applicable: the architecture page states what the run store guards | `docs/architecture/work-loop-execution-supervisor.md` | Platform Core maintainer | Review reads the page | The run-store row says a checkout without it verifies committed records only |
| Captured defect | Applicable: the owner chose to record the `common:config` residue defect | `docs/product/captured/supervisor-common-config-residue.md` | Platform Core maintainer | The file exists with `Kind: defect` and `Status: Open` | The file names the symptom and the code that treats `<common-dir>/config` as attempt state |
| Release history | Applicable: `core` pack content changes | one `docs/product/changelog.d/` fragment; `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` | Platform Core maintainer | AC-0008 passes | The fragment names the `status` change |
| Delivery records | Applicable: this spec runs through the supervisor | `docs/specs/supervisor-fresh-checkout-status/delivery/` | the supervisor | In the run, AC-0007's rebuilt-clone check; on the final head, the plan's finish evidence | The records are committed, and a plain fresh clone of the final head exits `0` on `status --check` and the shipped hook |

## Agent Rules

### Always do

- Keep every changed skill script standard-library only, and load no sibling before the pre-import check decides.
- Regenerate the projections with the repository's self-host command and bump `core` once. Inside the run, the installed `.claude/skills/work-loop/` is rebuilt only by the supervisor's `regenerate` request; no other step writes it.
- Run `packs/core/tests/skills/work-loop/test_supervisor_pinning.py` after each change to a supervisor script, and keep every case that passes at the base passing with its assertions unchanged; AC-0001 to AC-0006 are checked by added cases.

### Ask first

- Any change to what `start`, `next`, `report` or `resolve-effect` accept or refuse.
- Any change to `packs/core/.apm/hooks/pre-pr.py` or its repository copy, or to a `tests/roster/test_core_pre_pr_hook.py` case other than leaving the `delivery/` directories out of `test_pre_pr_passes_when_no_spec_holds_approvals`'s sandbox.

### Never do

- Edit anything under a spec's `.supervisor/` or `delivery/` by hand.
- Add a module, a dependency, a refusal code, or a verb; or change the pinned file set or the store layout.
- Write a security-event line, or any file, on the `committed-records-only` path.
- Edit the body of `docs/specs/execution-supervisor-attempt-security/` or its ledger.

## Testing Strategy

- **The no-store `status` path (AC-0001, AC-0002, AC-0003): TDD.** Each case runs the real CLI in a `git clone` of a supervisor-run test repository, which holds the committed records and no store; each reds at the base on the `supervisor-changed` refusal.
- **The `verification` field (AC-0006): TDD.** The `committed-records-only` cases run in the store-less clones above; the `pinned` cases run in a supervisor-run test repository that holds its store. At the base, the `committed-records-only` cases and the `pinned` case whose working-tree approvals name a run with no store red on the `supervisor-changed` refusal `the supervisor's pin record is missing`; every other `pinned` case reds because the `status` view has no `verification` key.
- **Refusals that stay (AC-0004, AC-0005): TDD.** Each planted tamper or verb runs the real CLI and asserts the refusal; the cases that pass at the base are pins, and the `status` cases that do not exist at the base are added.
- **The hook on this branch (AC-0007): goal-based and manual QA.** The no-approvals roster case runs on this branch, which carries this spec's `delivery/`. A fresh clone of the pushed branch rebuilds its own installed skill from the pack source and commits that only inside the clone, then runs the command and the hook; the commit id, commands and observed exit codes go in the ledger.
- **Release (AC-0008): goal-based.** The version and changelog gates.

## Acceptance Criteria

Terms used below.

- **Store directory.** The entry `<Git directory>/agentbundle-supervisor/<run id>/` of a checkout, whatever its kind, where `<Git directory>` is the one the `.git` entry names.
- **Working run.** The run id on the first line of the spec's `delivery/approvals.jsonl` in the working tree.
- **Committed run.** The run id on the first line of the spec's `delivery/approvals.jsonl` at `HEAD`.
- **No-store checkout.** A checkout with no store directory for the working run and none for the committed run. A store directory counts as absent only when looking it up reports that nothing exists at its path; any other lookup error refuses `supervisor-changed`.
- **Spec store.** A store directory whose `spec` record names the spec.
- **Pinned spec store.** A store directory whose pin record names the spec.

**The `status` verb in a no-store checkout**

- [ ] **AC-0001.** In a no-store checkout whose committed records and Git history derive the run terminal, `status <spec-dir> --check` exits `0` and prints a view with `"terminal": true` and `"verification": "committed-records-only"`.
- [ ] **AC-0002.** In a no-store checkout whose `HEAD` holds the spec's `delivery/` records in one commit with none of the run's supervisor commits reachable, `status <spec-dir> --check` exits `0` and prints a view with `"verification": "committed-records-only"` and an empty `refusal`.
- [ ] **AC-0003.** A `status` call in a no-store checkout leaves the checkout as it found it: no store directory, no `<spec-dir>/.supervisor/` entry and no `.loop-run/` entry is created, and `HEAD` and `git status --porcelain` are unchanged.

**Refusals that stay**

- [ ] **AC-0004.** In a no-store checkout, `start`, `next`, `report` and `resolve-effect` each exit `1` with refusal code `supervisor-changed` and detail `the supervisor's pin record is missing`, and leave `HEAD` unchanged.
- [ ] **AC-0005.** `status` exits `1` with refusal code `supervisor-changed`, whether or not the working run has a store directory, when: a spec store has no pin record and no orphan mark; the installed pinned files differ from a pinned spec store's pin record, and from the source digests that store's open `regenerate` request recorded; they differ from the pins of another run whose store holds an open attempt; or the committed run's store directory exists with no pin record.
- [ ] **AC-0006.** Every `status` view carries `verification`: `"pinned"` when the installed pinned files were compared, before any sibling script loaded, with the committed run's pin record, or with the source digests the committed run's open `regenerate` request recorded, and matched; and `"committed-records-only"` otherwise. A checkout whose working copy of `delivery/approvals.jsonl` is missing, or names another run that has no store directory, while the committed run's pins match, reports `"pinned"`.

**The hook and the release**

- [ ] **AC-0007.** On this spec's branch, with its `delivery/` records committed: `tests/roster/test_core_pre_pr_hook.py::test_pre_pr_passes_when_no_spec_holds_approvals` passes with every `docs/specs/*/delivery/` directory left out of its sandbox; and in a fresh `git clone` of the pushed branch at the commit T4 pushes, with the clone's installed work-loop skill rebuilt from `packs/core/.apm/skills/work-loop/` and committed there, `status docs/specs/supervisor-fresh-checkout-status --check` and the shipped `pre-pr.py` both exit `0`.
- [ ] **AC-0008.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the version one patch above the one `packs/core/pack.toml` carries at `git merge-base origin/main HEAD`, checked right after `git fetch origin` with that merge base equal to `origin/main`, and one `docs/product/changelog.d/` fragment names the `status` change.

## Terminal Intent

`code` — `status` verifies committed records in a checkout without the run's store and says so, and `core` is released.

## Accepted Risk

- In a no-store checkout, `status` loads the installed sibling scripts with no pin comparison, because no pin exists there to compare with. It runs the code the checkout holds, with the trust any script in that checkout has.
- A worker that deletes a live run's whole store directory makes that checkout's `status --check` answer from the committed records alone. It cannot advance the run: `next`, `report` and `resolve-effect` still refuse. Accepted by eugenelim on 2026-10-30.

## Follow-ons

none

## Assumptions

none

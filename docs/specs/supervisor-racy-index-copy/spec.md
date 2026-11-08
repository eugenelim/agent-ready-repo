# Spec: Supervisor racy-safe index copy

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0144, ADR-0154
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none — the change is internal to the supervisor's whole-tree scan; no record or CLI shape changes
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material: they orient a reader and an author corrects them in place
> as the work teaches, without an amendment and without a review round. A review
> finding against working material is advisory — it cannot block, because nothing
> gates the text it cites. Marking the tiers is the spec's job; honouring them
> when a finding is adjudicated is the reviewing surface's.

## Outcome

Maintainers running full-mode `work-loop` get a supervisor whose whole-tree scans see every change in the work tree, including a same-size rewrite made in the same second the work tree's index was last written. Success is that the scan seeded from the work tree's index names exactly the paths a scan from a `read-tree HEAD` index names in that case.

## What Changes

- The supervisor's private index copy takes the work tree index's access and modification times, at nanosecond precision, before any Git command reads or writes it, so Git's racy-clean check still applies to entries written in the index's own second — `work-loop/scripts/_supervisor_commit.py` (`_PrivateIndex`).
- A regression test reproduces the same-second, same-size rewrite — `packs/core/tests/skills/work-loop/test_supervisor_git.py`.
- Core ships the fix as a patch release.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Release history | A Core patch | `packs/core/pack.toml`, `.claude-plugin/plugin.json`, a changelog fragment | Core release maintainers | Version bump | One patch above `packs/core/pack.toml` at the merge base with freshly fetched `origin/main` |
| Verification record | Closeout evidence | `docs/specs/supervisor-racy-index-copy/notes/verification-ledger.md` | Spec owner | Ledger rows | Every criterion checked against a named test and run |

## Agent Rules

### Always do

- Run every `git` call through the hardened Git helper.
- Prove the defect with a test that fails before the fix and passes after it.

### Ask first

- Changing what the scan rehashes or when it falls back to a `read-tree HEAD` index.

### Never do

- Add a dependency, a module, or a configuration setting.
- Change any other supervisor behaviour in this change.

## Testing Strategy

- **Racy-clean scan (AC-0001):** TDD at the supervisor's `change_set` and `working_changes` boundary over a real Git repository with a tracked spec directory, so seeding takes the production path that rewrites the copy, with the rewrite made inside the index's own second and no Git command that refreshes the real index in between, because the defect only shows when Git trusts stat data the copy made look old.

## Acceptance Criteria

- [x] **AC-0001.** In a repository whose tracked spec directory makes the seeded scan rewrite its index copy, after a tracked file is rewritten to a same-size content within the second the work tree's index was last written, and a later second has begun, `change_set` and `working_changes` from the index-seeded scan both name that file.

## Closeout

Post-run duties, run by the controller after the supervisor's run is terminal; they are not acceptance criteria.

- Core is one patch above `packs/core/pack.toml` at the PR's merge base with freshly fetched `origin/main`, and `make build-self && make bootstrap-sites` leave no tracked change after the delivery commit.
- `notes/verification-ledger.md` records each criterion's test and run; the spec moves to `Shipped` and the plan to `Done`.

## Terminal Intent

`code` — ship the racy-safe index copy and its regression test as a Core patch release, then close the spec.

## Follow-ons

none

## Assumptions

none

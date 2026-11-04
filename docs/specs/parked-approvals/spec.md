# Spec: parked approvals

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0156, RFC-0099, ADR-0154
- **Brief:** none
- **Discovery:** none
- **Depends on:** none
- **Contract:** none — the `park` and `gates` outputs are supervisor CLI JSON, documented in the work-loop skill's supervisor reference; no `contracts/` schema changes
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

A human approving a full-mode work-loop spec or plan sees every waiting `spec-approved` and `plan-approved` gate in one listing, with the exact digests, the commit to read, and what each answer does, while the controller keeps working on independent specs. The supervisor admits `start` only for the digests that human approved, and a gate nobody answers stays unapproved forever.

## What Changes

- New supervisor verb `park <spec-dir> --gate spec-approved|plan-approved` — `packs/core/.apm/skills/work-loop/scripts/work-supervisor.py` and one new `_supervisor_gates.py` module beside it.
- New read-only supervisor verb `gates` — the same two files.
- The gate digest: the canonical contract digest over the artifact without its `## Changelog` section — `_supervisor_gates.py`, calling the existing canonicalizer in `_loop_guards.py`.
- `start` requires `--approved-spec-digest` and `--approved-plan-digest` and refuses a mismatch — `work-supervisor.py` and `_supervisor_admission.py`.
- Park records live in the checkout's local supervisor store, `<git-dir>/agentbundle-supervisor/gates/`.
- Controller procedure for parking, listing, answering, and working other specs while a gate waits — work-loop `SKILL.md` step 12, `references/supervisor.md`, `references/session-resumption.md`, `references/state-schema.md`.
- Eval cases for a parked gate — `packs/core/.apm/skills/work-loop/evals/evals.json`.
- Every existing `start` call site in the core pack tests passes the two digests — `packs/core/tests/skills/work-loop/`.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | The design choice and its alternatives | `docs/adr/0156-work-loop-approval-gates-park-instead-of-halting.md` | eugenelim | ADR committed `Accepted` before spec approval | Cited in `Constrained by:` |
| Maintainer procedure | Controllers follow the skill, not the code | work-loop `SKILL.md` step 12; `references/supervisor.md`; `references/session-resumption.md` | core pack maintainers | Content tests green | Guidance names `park`, `gates`, both `start` digest arguments, and the no-default rule |
| Current architecture | The supervisor's command surface table lists its verbs | `docs/architecture/work-loop-execution-supervisor.md` command-surface row | core pack maintainers | Row lists `park` and `gates` | Row matches the parser's verb set |
| Operations (state) | A new local record kind | `references/state-schema.md` local-store row | core pack maintainers | Row names `gates/` and its writer | Row present |
| Release history | Core changes content | `docs/product/changelog.d/<uuid>.md`; `packs/core/pack.toml`; `packs/core/.claude-plugin/plugin.json` | core pack maintainers | Release check green | Version is one patch above the merge base's |
| Reusable learning | none — no generalizable practice beyond the ADR is expected | — | — | — | — |

## Agent Rules

### Always do

- Compute every digest the supervisor shows or compares from the files themselves; never take a digest from a controller argument except the two `start` pins a human supplied.
- Fail closed: a missing, malformed, or unreadable park record, a Git read that fails, or an unparseable artifact refuses or lists the gate as not approvable; it never lists a gate as approved.
- Run every Git call through the supervisor's existing hardened Git helper, and every store write through the existing confined-mutation helper.
- Keep `start`'s existing refusals and its single approval-pair commit unchanged apart from the digest check.

### Ask first

- Any change to an existing `approval-record.v1` or `initial-plan-review.v1` field, or to the committed `delivery/approvals.jsonl` line shape.
- Any listing of gates from another worktree or from a remote.
- Any answer other than `approve`, `reject`, and no answer.

### Never do

- Never approve, or record as approved, a gate that no named human answered: no default, timeout, batch rule, flag, or record turns a parked gate into an approval.
- Never let `start` read a park record.
- Never write a commit, a ref, a `Status:` line, or a file in the working tree from `park` or `gates`.
- Never put controller-supplied free text into a park record or the `gates` listing.
- Never add a dependency, a new top-level directory, or a new `contracts/` schema.

## Testing Strategy

- **Gate digest (AC-0007, AC-0008, AC-0025): TDD, unit.** A pure function of the artifact text, so each normalization is one small case.
- **`park` and `gates` behaviour (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014): TDD, integration** through the supervisor CLI on a real Git repository built by the existing supervisor test harness, because each criterion is about what lands in Git and the store.
- **`start` digest binding and the no-default rule (AC-0015, AC-0016, AC-0017, AC-0018, AC-0019): TDD, integration** through the CLI, gated like the other supervisor integration suites, because the property is that no Git state changes.
- **Guidance and evals (AC-0020, AC-0021, AC-0022): goal-based**, a content test over the shipped skill files plus the eval harness's own schema check.
- **Release (AC-0023, AC-0024): goal-based**, the release and catalogue checks.

## Acceptance Criteria

### `park`

- [ ] **AC-0001.** Given a committed, clean spec directory whose spec is `Draft`, `park <spec-dir> --gate spec-approved` exits 0, prints JSON with `status` `parked`, `gate`, `spec_digest`, `plan_digest`, and `commit` equal to `HEAD`, and writes exactly one file under `<git-dir>/agentbundle-supervisor/gates/`.
- [ ] **AC-0002.** After any `park` run, `HEAD`, every ref, the index, and every working-tree file are byte-identical to before.
- [ ] **AC-0003.** `park` refuses with code `gate-uncommitted` and writes no record when `spec.md` or `plan.md` differs between the working tree, the index, and `HEAD`.
- [ ] **AC-0004.** `park --gate spec-approved` refuses with `gate-status-mismatch` unless the spec is `Draft`; `park --gate plan-approved` refuses with `gate-status-mismatch` unless the spec is `Approved` and the plan is `Drafting`.
- [ ] **AC-0005.** `park` refuses with `gate-already-admitted` when `<spec-dir>/delivery/approvals.jsonl` holds an approval pair at `HEAD`.
- [ ] **AC-0006.** A second `park` with the same gate and the same digests prints `status` `current` and leaves the record byte-identical; a `park` for the same spec with a different gate or different digests replaces the record, so the spec has one record.

### Gate digest

- [ ] **AC-0007.** The gate digest of an artifact is unchanged when only its `Status:` token changes, when lines are added to or removed from its `## Changelog` section, or when line endings or trailing whitespace change.
- [ ] **AC-0008.** The gate digest of an artifact changes when any byte outside its status token, its `## Changelog` section, line endings, trailing whitespace, and checkbox contents changes.
- [ ] **AC-0025.** An artifact whose `## Changelog` heading occurs more than once, is not its last level-two heading, or heads a section holding, outside HTML comments, any line other than a blank line or a `- ` list item has no gate digest: `park` refuses it with `gate-changelog-shape`, `start` refuses it with `approval-digest-mismatch`, and `gates` lists its entry as `stale`.

### `gates`

- [ ] **AC-0009.** `gates` prints one entry per park record with exactly the fields `spec_dir`, `gate`, `spec_digest`, `plan_digest`, `commit`, `read`, `answers`, and `state`, where `read` is the two commands `git show <commit>:<spec-dir>/spec.md` and `git show <commit>:<spec-dir>/plan.md`.
- [ ] **AC-0010.** Each entry's `answers` maps exactly `approve`, `reject`, and `no-answer` to the supervisor's fixed consequence text for that gate, and the `no-answer` text states that the gate stays unapproved.
- [ ] **AC-0011.** An entry's `state` is `stale` when the current gate digest of either working-tree artifact differs from the recorded one, and `pending` otherwise.
- [ ] **AC-0012.** `gates` omits a spec directory whose `delivery/approvals.jsonl` holds an approval pair at `HEAD`.
- [ ] **AC-0013.** A park record that is malformed, oversized, not a regular file, or names a spec directory outside the repository is listed with `state` `invalid` and no digests; it never makes `gates` exit non-zero for the other records, and it never lists as `pending`.
- [ ] **AC-0014.** After any `gates` run, the store, `HEAD`, every ref, the index, and every working-tree file are byte-identical to before.

### `start` binding

- [ ] **AC-0015.** `start` without `--approved-spec-digest` or without `--approved-plan-digest` exits 2 with a usage error and commits nothing.
- [ ] **AC-0016.** `start` with either digest different from the current gate digest of that artifact refuses with code `approval-digest-mismatch` and owner `owner`, exits 1, leaves `HEAD` unchanged, and adds no `approvals.jsonl` line.
- [ ] **AC-0017.** `start` with both digests equal to the current gate digests admits exactly as it did without the check: the same `status` values and one approval-pair commit.
- [ ] **AC-0018.** For the same arguments, `start`'s exit code and output are the same whether the spec's park record is present, absent, malformed, or rewritten to hold other digests.

### Never approved by default

- [ ] **AC-0019.** Given a parked gate and no human answer, running `park` again, `gates` any number of times, and `start` with digests taken from a stale entry or omitted leaves `approvals.jsonl` absent and both `Status:` lines unchanged.

### Guidance and evals

- [ ] **AC-0020.** The work-loop supervisor reference's verb table lists `park` and `gates`, and its `start` row names `--approved-spec-digest` and `--approved-plan-digest`.
- [ ] **AC-0021.** The work-loop `SKILL.md` approval step tells the controller to park each gate, to pass only the digests the human approved to `start`, to dispatch no implementation work for a parked spec, and never to treat a parked gate as approved.
- [ ] **AC-0022.** `evals.json` carries a case in which a gate is parked with no answer and another independent spec is ready, whose assertions require the controller to work the other spec, not run `start` for the parked one, and not report the gate approved.

### Release

- [ ] **AC-0023.** `packs/core/pack.toml` and `packs/core/.claude-plugin/plugin.json` carry the same version, one patch above `packs/core/pack.toml` at the merge base with freshly fetched `origin/main`, and a `docs/product/changelog.d/` fragment names the change.
- [ ] **AC-0024.** After self-host, `agentbundle catalogue lint --root . --deep` and `agentbundle catalogue verify --root .` exit 0 and the tree is clean.

## Terminal Intent

`code` — ship `park`, `gates`, the gate digest, the `start` digest binding, the guidance and eval cases, and the core release with its projections.

## Follow-ons

none

## Assumptions

none

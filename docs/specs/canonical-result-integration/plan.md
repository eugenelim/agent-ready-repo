# Plan: Canonical result integration

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0153 governs once Accepted; it supersedes ADR-0144 D9 and D11 in part.
  - **Commit builder:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_commit.py`
    (`GitPort.build_commit` moves `HEAD` by `update-ref HEAD new old`, with
    kill points `commit-built`, `head-moved`, `synced`; `record_made` and
    `made_commits` keep the run store's made-commit list).
  - **Derivation and decisions:** `_supervisor_loop.py` (`derive`, `decide`, `report`); `_supervisor_recovery.py` (the `confirm-replan` decision, the pattern `adopt-history` follows).
  - **Admission:** `_supervisor_admission.py` (`start`; run id at line 492).
  - **Subject:** `_supervisor_readiness.delivery_subject`.
  - **Attempt control state:** `_supervisor_attempt.py` (`git_state`, `_history`, issuance `head`, `retire_orphans`, pins); `_supervisor_git.py` runs `control_check` before every Git call.
  - **Tests:** `packs/core/tests/skills/work-loop/test_supervisor_crash_corpus.py`
    (kill at every kill point, rebase scenario), `test_supervisor_commit.py`,
    `test_supervisor_attempt.py`, `test_supervisor_pinning.py` (regenerate),
    `supervisor_harness.py`; CI in `.github/workflows/catalogue-tooling-ci-gates.yml`
    (POSIX supervisor integration) and `build-check-windows.yml`.

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an amendment only when it touches the spec's protected sections
> or its `Terminal Intent`. Tasks, tests, design, and approach change as
> in-envelope working-plan edits while no attempt is open. Execution
> observations belong in
> `docs/specs/canonical-result-integration/notes/verification-ledger.md`.

## Approach

ADR-0153 is accepted with this spec and plan, before `start`, so it is a
readable cited record from the first step and no task edits its decision
section. T1 ships the product ref in shadow: the two-ref transaction, ref
identity, recovery classification, owner adoption, attempt checks, and parity
evidence, with acceptance still reading `HEAD`. T1 also adds the product-ref
suites to the Windows CI job. It ships as its own Core release. T2 flips
`result_authority`, proves reversal through the `regenerate` route, and
refreshes the skill and architecture pages, in the next Core release. T3
closes the slice.

The riskiest part is T1's commit path: it replaces the single `update-ref` in
`build_commit` on every step. The crash corpus already kills at every kill
point, so extending it to the new writes is the main proof.

## Constraints

- ADR-0153 D1–D6; ADR-0144 D2 (standard library only, inside the skill), D7,
  D11 (worker attempts untrusted).
- ADR-0152: on hosts without descriptor walking, confined writes use the
  path-checked route; working-tree updates during repair go through Git.
- Every Git call goes through `_supervisor_git.py`'s hardened helper; no new
  `subprocess` call site.
- `packs/AGENTS.md`: shipped text cites no internal records; each `.apm/`
  change bumps Core to the next free version above the merge base with
  freshly fetched `origin/main`, checked right before push.
- Do not edit `work-loop/scripts/` while a `WORK_SUPERVISOR_INTEGRATION=1` run
  is live: the supervisor pins its own digests.

## Construction tests

**Integration tests:**

- **VI-0501 (AC-0007, AC-0017):** the crash corpus in
  `test_supervisor_crash_corpus.py` adds kill points for the pending record
  and each recovery write, records the product ref commit and tree in its
  summary, and asserts `HEAD` stays on its branch; every variant converges,
  and after each step the working-tree, `HEAD`, and product-ref manifests are
  equal. T1 owns
  it under `legacy-worktree`; T2 reruns it under `protected-product-ref`.

**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Decision rationale | before T1 (with approval) | ADR shape lint | ADR-0153 `Accepted`; ADR-0144 mirror |
| Current architecture | T2 | Architecture review in the ledger | Pages describe the product ref |
| Maintainer procedure | T1, T2 | Skill evals | Supervisor reference tables |
| Interface compatibility | T1 | Delivery contract tests | Existing records validate |
| Release history | T1, T2 | Version parity | Two changelog entries |
| Product coordination | T3 | Brief-coverage lint | Spec map row reports `Shipped` |

Design facts below are owned by `work-loop-result-integration.md` (the
transaction, classification, adoption, and parity rules) and
`work-loop-execution-supervisor.md` (kill points, refusals, the decision, the
policy key); the rest is delivery residue.

## Design (LLD)

### Design decisions

Owned by: T1, T2.

- **One chain, `HEAD` as projection.** Every supervisor step advances the
  product ref, so one commit chain carries both and AC-0002 is one equality.
  Rejected: a separate integration chain, which needs its own parentage and
  recovery.
- **The run store is the ref's trust anchor.** The run store records the
  product ref's name and its current value; before a step's transaction it
  also records the pending commit. The product ref is trusted only while it
  equals the recorded or pending value, which covers a missing, symbolic,
  rolled-back, planted, or foreign-written ref with one rule (AC-0005) and
  gives every refusal an exact restore command. The name is never read from a
  commit message. Rejected: trusting any made commit, which admits a rollback
  to an older made commit.
- **Exact source by compare-and-swap.** The transaction's expected old value
  for the product ref is the issuance `head` the attempt store records for a
  product result, and the recorded value otherwise. No three-tree apply; the
  Git floor stays 2.32. Two windows guard a moved ref: before the
  transaction's own Git call, `control_check` refuses it (AC-0015); between
  that check and the update, the compare-and-swap fails (AC-0003).
- **Two refs, one transaction, `HEAD` stays attached.** `git update-ref -z
  --stdin` with `start`, `update HEAD <new> <old>` (dereferenced, so the
  branch `HEAD` names moves), `option no-deref`, `update <product-ref> <new>
  <old>`, `prepare`, `commit`. A stale expected value on either ref refuses
  both. Probed 2026-10-30 on Git 2.56: a global `--no-deref` detaches `HEAD`;
  the per-command `option no-deref` keeps `HEAD` on its branch and replaces,
  never follows, a symbolic product ref. `start`/`prepare`/`commit` exist since
  Git 2.27. The files backend is not crash-atomic across refs, so AC-0008
  completes a commit that moved one ref.
- **Identity.** `start` draws a 16-hex token from `secrets`, records the name
  in the run store, and also writes it in a `Supervisor-Product-Ref` trailer
  on the approval commit for traceability only. The name is checked against
  `refs/agentbundle/delivery/run-[0-9a-f]{16}/[0-9a-f]{16}/product` before
  use. The ref lives in the common Git directory so `git gc` from any worktree
  keeps its commits; a probe on 2026-10-30 showed a `refs/worktree/` ref does
  not protect its objects from `gc` run in another worktree.
- **Authority selects the subject, not the writes.** Both authorities write and
  check the product ref identically; `result_authority` selects which tree the
  delivery subject reads. The policy is pinned at `start`, so authority is
  fixed for a run until `regenerate` re-pins it.
- **Adoption needs the owner.** Every piece of foreign history enters the
  product ref through one owner-authorized `reanchor` step; nothing
  re-anchors automatically, because a rewrite can keep trailers while
  changing content. Foreign history is measured against the product ref, so
  a `reanchor` ends it.

### Data & schema

Owned by: T1, T2.

- Run store (under the Git directory, per worktree and run): `product-ref`
  holding the ref name, the recorded commit, and the pending commit or none,
  written through the confined mutation port.
- Product ref: `refs/agentbundle/delivery/<run-id>/<token>/product` → the
  latest supervisor commit of the run.
- `approval` step: gains trailer `Supervisor-Product-Ref: <ref name>`.
- `reanchor` step: operation `reanchor`, trailers `Supervisor-Reanchor-From:
  <prior product ref commit>` and `Supervisor-Authority-Ref`, tree equal to the
  adopted `HEAD`'s, no `delivery/` append.
- `execution-request.v1`: `human-decision` `reason` gains `history-adoption`,
  carrying the `HEAD` commit id, the changed product path count and up to 20
  paths, and a spec-directory flag. `execution-result.v1`: decision gains
  `adopt-history` with `authority_ref` and `commit`.
- `supervisor-policy.json`: `"result_authority": "legacy-worktree"` (T1),
  `"protected-product-ref"` (T2).
- `delivery-subject.v1` under `protected-product-ref`: `lineage.provider`
  `protected-product-ref`, `projection_version` `1`, `result_ref` the product
  ref commit, manifest from its tree. Schema unchanged.

### Interfaces & contracts

Owned by: T1.

- New refusal codes, all owner `controller`: `integration-conflict`,
  `product-ref-diverged`, `projection-blocked`. Existing `invalid-policy`
  keeps owner `skill maintainer`; `load_policy` gains the `result_authority`
  check. Existing attempt codes are unchanged: `report` refuses
  `attempt-refused`, `next` answers `attempt-residue`.
- Refusal details list at most 20 paths, taken from the result's change set,
  as today's refusals do.
- Test seam for AC-0003: a hook between the transaction's control check and
  its `update-ref` call, installed like `set_kill_hook`; the test moves the
  ref there with plain `git update-ref`.

### State & control flow

Owned by: T1.

Every verb runs, under the run lock: the pin check, then the attempt guard
(`attempt-residue` or `attempt-refused` while an open attempt shows a
difference), then this classification, then `derive`. The first matching row
applies:

| State | Attempt open | Action |
| --- | --- | --- |
| No recorded product ref, no approval at `HEAD` | either | `start` records and creates it in the approval transaction |
| `extensions.refStorage` is not `files` | either | `start` refuses `unsupported-ref-storage` (AC-0022); later verbs refuse the same |
| No recorded product ref, approvals at `HEAD` | no | AC-0006: create at `HEAD` when it is the latest made commit, else `history-adoption` against the latest made commit |
| No recorded product ref, approvals at `HEAD` | yes | no ref change; the step that closes the attempt creates the ref at its commit |
| Ref missing, symbolic, or not the recorded or pending value | no | `product-ref-diverged` (AC-0005) |
| Same | yes | the attempt guard has already answered (AC-0015) |
| One ref at the pending commit, the other at the commit before | either | complete the move (AC-0008) and clear pending |
| `HEAD` = ref | either | continue |
| Ref descends from `HEAD` through made commits only | no | project forward (AC-0009, AC-0010) |
| `HEAD` carries foreign history | no | `history-adoption` (AC-0011) |
| Any other difference | yes | already refused by the attempt guard, which compares `HEAD` with issuance |
| Any other difference | no | `history-adoption` |

A step then runs: build the commit object in the private index →
`commit-built` → record pending → `pending-recorded` → transaction →
`refs-moved` (renamed from `head-moved`) → record value, clear pending →
`delivery/` working copies and index refresh → `synced`.

Forward projection (AC-0009) is `implementation-discovered` in its means. Its
predicate: for each path the skipped commits change, compare the working-tree
bytes and the index entry with `HEAD`'s and the ref's versions; refuse
`projection-blocked` if either matches neither; otherwise write the ref's
version through Git, update the index, then move `HEAD` by compare-and-swap.
`git read-tree -m -u` is ruled out: it refuses an entry whose working copy
already equals the target while the index is at `HEAD` (probed by
adversarial review on Git 2.56). Kill points `projection-updated` and
`repaired` bracket the ref move. Verification: VI-0514.

`git_state` reads this run's product ref by direct file reads, the loose ref
under the common Git directory and its `packed-refs` line, as it reads
`refs/replace` today, and digests the value; `control_check` compares that
value with the run store's recorded and pending values rather than with the
issuance digest, so the supervisor's own move is accepted and any other value
is refused. No Git call is made inside the check.

### Failure, edge cases & resilience

Owned by: T1.

- Crash before the transaction: the commit object is unreachable; the
  pending record names it, neither ref does, so the next call clears pending
  and rebuilds the same step.
- Crash after the transaction and before the record: both refs at pending;
  the next call records it and continues.
- Partial transaction: one ref at pending, AC-0008.
- Conflict: nothing moves; the attempt guard answers `attempt-residue` until
  the ref is restored, then clears and re-issues the request, and the
  worker's kept files are the re-issued attempt's result (AC-0004).

### Quality attributes (NFRs)

Owned by: T1.

- Observability: each new refusal reaches the controller through the verb's
  output and `run.json`'s `refusal`; `product-ref-diverged` also writes a
  denial line to `security-events.jsonl` and names the restore command;
  `reanchor` emits one `.loop-run/events.jsonl` line like every step.

## Tasks

### T1: The product ref ships in shadow, and every boundary converges

- **Depends on:** none (ADR-0153 Accepted before `start`)
- **Spec behavior:** AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0020, AC-0021, AC-0022; TDD, and goal-based for the corpus and CI.
- **Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_commit.py`, `_supervisor_loop.py`, `_supervisor_admission.py`, `_supervisor_attempt.py`, `_supervisor_recovery.py`, `_supervisor_readiness.py`, `work-supervisor.py`, `supervisor-policy.json`, `SKILL.md`, `references/supervisor.md`, `evals/evals.json`; `contracts/delivery/execution-request.v1.schema.json`, `execution-result.v1.schema.json`; `packs/core/tests/skills/work-loop/`; `.github/workflows/catalogue-tooling-ci-gates.yml`, `.github/workflows/build-check-windows.yml`; Core manifests and `docs/product/changelog.md`.
- **Verification mode:** TDD
- **Tests:**
  - **VI-0511 (AC-0001, AC-0002):** in a new `test_supervisor_product_ref.py`,
    after `start` and after each verb's step in a harness run, `git rev-parse`
    of the product ref equals `HEAD` and `git symbolic-ref HEAD` still names
    the starting branch; two worktrees admitted from one commit, and one run
    re-admitted after its store is retired, record different names.
  - **VI-0512 (AC-0003, AC-0004):** in `test_supervisor_product_ref.py`, the AC-0003 seam moves the product ref to
    a commit descending from the source commit; `report` refuses
    `integration-conflict`; both refs, the index, and `delivery/` bytes equal
    their pre-report values; `next` answers `attempt-residue`; after the test
    restores the ref, `next` re-issues the same request id and reporting it
    commits the kept bytes.
  - **VI-0513 (AC-0005, AC-0006, AC-0022):** in `test_supervisor_product_ref.py`, a deleted, symbolic, rolled-back (to an
    older made commit), and planted (a foreign commit with a forged
    `Supervisor-Product-Ref` trailer) product ref each refuse
    `product-ref-diverged` with a denial line and the recorded value; restoring
    the ref clears it. A trailer-free run pinned to the previous Core crosses
    by `regenerate` and gains its ref; the same run with a foreign commit on
    top, and the same run reset to an older made commit, each get
    `history-adoption`, and an `owner` answer lets each reach `terminal`; a
    `delivery/` change in that foreign commit refuses adoption. A repository
    with `extensions.refStorage=reftable` refuses `start` with
    `unsupported-ref-storage` and has no product ref.
  - **VI-0514 (AC-0008, AC-0009, AC-0010):** in `test_supervisor_product_ref.py`, `git reset --hard`, `--soft`, and
    `--mixed` two steps back each converge at the next `next` with the
    working tree equal to the ref's tree; a partial transaction (only one ref
    moved) completes, with the attempt open and with it closed; a reset plus
    an edit to a file those steps changed refuses `projection-blocked` and
    leaves the edit's bytes and the index.
  - **VI-0516 (AC-0011, AC-0012, AC-0013, AC-0014):** in `test_supervisor_product_ref.py`, the existing rebase
    scenario, an amend that keeps trailers and edits a product file, and a
    controller commit on top each issue `history-adoption` naming the changed
    paths and commit nothing; the amended edit is absent from the ref's tree;
    an `adopt-history` from `owner` naming `HEAD` commits one `reanchor`, the
    next `next` issues no second adoption, and the run reaches `terminal`; an
    answer naming another commit, or from `plan-reviewer`, refuses; a foreign
    commit appending a line to `delivery/review-decisions.jsonl` is refused
    adoption; after a manifest-changing `reanchor`, `run-gates` and review run
    again before readiness.
  - **VI-0517 (AC-0015, AC-0016):** in `test_supervisor_attempt.py`, during an
    open `implement-task` attempt, creating, moving, making symbolic, and
    deleting this run's product ref each make `report` refuse
    `attempt-refused` and `next` answer `attempt-residue` until restored; a
    `report` that commits with the attempt open, and a `refs-moved` kill
    inside it, are not refused; a second worktree's run advancing its own
    product ref during the attempt leaves it admissible.
  - **VI-0518 (AC-0020):** `start` with `result_authority` absent, or set to
    `other`, refuses `invalid-policy` with owner `skill maintainer`.
  - **VI-0501 (AC-0007, AC-0017)** passes under `legacy-worktree`.
  - **VI-0519 (AC-0021):** `catalogue-tooling-ci-gates.yml`'s supervisor
    integration job lists `test_supervisor_product_ref.py`;
    `build-check-windows.yml` gains a step running
    `test_supervisor_product_ref.py`, `test_supervisor_attempt.py`, and
    `test_supervisor_pinning.py` with `WORK_SUPERVISOR_INTEGRATION=1`; both
    jobs pass, and the clean-environment import fence passes.
- **Done when:** T1's `Tests` pass, the existing supervisor suites still pass,
  and security-reviewer, adversarial-reviewer, and quality-engineer return
  clean.

### T2: Acceptance reads the product ref, and reversal is proven

- **Depends on:** T1
- **Spec behavior:** AC-0017, AC-0018, AC-0019, AC-0021; goal-based.
- **Touches:** `_supervisor_readiness.py`, `supervisor-policy.json`, `SKILL.md`, `references/supervisor.md`, `evals/evals.json`; `packs/core/tests/skills/work-loop/`; `ARCHITECTURE.md` and the architecture pages the spec's Durable Outputs list; Core manifests and changelog.
- **Verification mode:** goal-based
- **Tests:**
  - **VI-0521 (AC-0018):** in `test_supervisor_product_ref.py`, under
    `protected-product-ref`, a harness run's subject has lineage
    `protected-product-ref` and `result_ref` equal to the product ref; a
    controller commit on `HEAD` leaves the subject unchanged until
    `adopt-history`, and changes it after.
  - **VI-0522 (AC-0019):** in the regenerate fixture of
    `test_supervisor_pinning.py`, a run pinned to one authority regenerates to
    the other after its first `implement` step, once each way, and reaches
    `terminal` with the uninterrupted run's final manifest; evidence from
    before the regeneration is re-established by `run-gates`.
  - **VI-0501 (AC-0007, AC-0017)** passes under `protected-product-ref`.
  - **VI-0519 (AC-0021)** passes with T2's suites.
- **Done when:** T2's `Tests` pass, the architecture review is recorded in the
  ledger, and security-reviewer, adversarial-reviewer, and quality-engineer
  return clean.

### T3: The slice closes

- **Depends on:** T2
- **Spec behavior:** none; closeout.
- **Touches:** `spec.md`, `plan.md`, `notes/verification-ledger.md`.
- **Verification mode:** goal-based
- **Tests:**
  - **VI-0531:** `lint-spec-status.py` and the brief-coverage lint pass with
    the spec `Shipped` and every criterion checked.
- **Done when:** VI-0531 passes.

## Rollout

- **Delivery:** ADR-0153 is accepted with the spec and plan. T1 ships in one
  Core release with `legacy-worktree`; T2 ships in the next with
  `protected-product-ref`. Each takes the next free version above the merge
  base with freshly fetched `origin/main`.
- **Reversal:** a Core patch that sets `result_authority` back to
  `legacy-worktree`. Runs started after it use `HEAD` for their subject, and a
  run in flight reaches it through `regenerate`; no product change is lost,
  because both refs carry the same commits. Reinstalling the prior Core
  release also works for new runs.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** T2 after T1 merges.

## Risks

- **Every step's path changes in T1.** Mitigation: the crash corpus kills at
  every kill point and now compares the product ref too.
- **Windows ref locking.** `update-ref --stdin` holds lock files that a
  Windows scanner can delay. Mitigation: VI-0519 runs the product-ref suites
  on the Windows job.

## Changelog

<!-- Approvals only. -->

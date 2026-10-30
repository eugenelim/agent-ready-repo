# Plan: Canonical result integration

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** ADR-0153 governs once Accepted; ADR-0144 D11 stands.
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

- **VI-0501 (AC-0006, AC-0015):** the crash corpus in
  `test_supervisor_crash_corpus.py` adds kill points for each recovery write
  and records the product ref commit and tree in its summary; every variant
  converges, and at each step the two subjects' manifests are equal. T1 owns
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
- **Exact source by compare-and-swap.** The transaction's expected old value
  for the product ref is the issuance `head` the attempt store records for a
  product result, and the observed tip otherwise. No three-tree apply; the Git
  floor stays 2.32. Two windows guard a moved ref: before the transaction's
  own Git call, `control_check` refuses it as control state (AC-0013); between
  that check and the update, the compare-and-swap fails (AC-0003).
- **Two refs, one transaction.** `git update-ref --stdin -z --no-deref` with
  `start`, `update HEAD`, `update <product-ref>` (each with new and old
  values), `prepare`, `commit`, so a symbolic product ref is never followed. A
  stale expected value on either ref refuses both (probed 2026-10-30 on Git
  2.56; `start`/`prepare`/`commit` exist since 2.27). The files backend is not
  crash-atomic across refs, so AC-0007 repairs a commit that moved one ref.
- **Identity.** `start` draws a 16-hex token from `secrets` and records the
  product ref name in a `Supervisor-Product-Ref` trailer on the approval
  commit. A run admitted before product refs existed gets its name from the
  one `reanchor` step its adoption commits (AC-0005), which carries the same
  trailer and no authority reference. Later verbs read the name from the run's
  latest supervisor commit carrying the trailer and check it against `refs/agentbundle/delivery/run-[0-9a-f]{16}/[0-9a-f]{16}/product`
  before use. The ref lives in the common Git directory so `git gc` from any
  worktree keeps its commits; a probe on 2026-10-30 showed a `refs/worktree/`
  ref does not protect its objects from `gc` run in another worktree.
- **Ownership by made commits.** A product ref is trusted only while it is a
  regular ref naming a made commit. That tells a sibling run's ref, a planted
  ref, and a foreign writer's value apart without a shared lock.
- **Authority selects the subject, not the writes.** Both authorities write and
  check the product ref identically; `result_authority` selects which tree the
  delivery subject reads. The policy is pinned at `start`, so authority is
  fixed for a run until `regenerate` re-pins it.
- **Adoption needs the owner.** Every piece of foreign history enters the
  product ref through one owner-authorized `reanchor` step; no automatic
  re-anchor exists, because a rewrite can keep trailers while changing
  content.

### Data & schema

Owned by: T1, T2.

- Product ref: `refs/agentbundle/delivery/<run-id>/<token>/product` → the
  latest supervisor commit of the run.
- `approval` step: gains trailer `Supervisor-Product-Ref: <ref name>`.
- `reanchor` step: operation `reanchor`, trailers `Supervisor-Reanchor-From:
  <prior product ref commit>` and `Supervisor-Authority-Ref`, tree equal to the
  adopted `HEAD`'s, no `delivery/` append.
- `execution-request.v1`: `human-decision` `reason` gains `history-adoption`,
  carrying the `HEAD` commit id. `execution-result.v1`: decision gains
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
  check.
- Refusal details list at most 20 paths, taken from the result's change set,
  as today's refusals do.
- Test seam for AC-0003: a hook between the transaction's control check and
  its `update-ref` call, installed like `set_kill_hook`; the test moves the
  ref there with plain `git update-ref`.

### State & control flow

Owned by: T1.

At every verb, under the run lock and before `derive`, the supervisor reads
`HEAD` (H) and the product ref (R) and takes the first matching row:

| State | Action |
| --- | --- |
| No R, no approval at H | `start` creates R in the approval transaction |
| No R, approvals at H | AC-0005 adoption, or `product-ref-diverged` |
| R symbolic or not a made commit | `product-ref-diverged` (AC-0009) |
| R = H | continue |
| H descends from R through made commits | move R (no files) |
| R descends from H through made commits | `git read-tree -m -u H R`, then move H; local modifications refuse `projection-blocked` |
| R descends from H through foreign history | `product-ref-diverged` |
| anything else, no attempt open | `history-adoption` decision |

A step then runs: build the commit object in the private index →
`commit-built` → transaction → `refs-moved` (renamed from `head-moved`) →
`delivery/` working copies and index refresh → `synced`. Repair adds
`projection-updated` after the read-tree and `repaired` after its ref move.

`_history` and `control_check` accept a product-ref change whose new value is
a made commit of this run, the same rule they apply to `HEAD`; `git_state`
digests only this run's product ref, by name, through Git.

### Failure, edge cases & resilience

Owned by: T1.

- Crash before the transaction: the commit object is unreachable and the next
  call rebuilds the same step.
- Crash after: the step is reachable from both refs and is skipped.
- Crash inside repair after `read-tree`: H still lags, the index and files
  already match R, and the repeated read-tree is a no-op before the ref move.
- Conflict: nothing moves, the attempt stays open, and the worker's files stay
  for the same result to be reported once R is restored.

### Quality attributes (NFRs)

Owned by: T1.

- Observability: each new refusal reaches the controller through the verb's
  output and `run.json`'s `refusal`; `product-ref-diverged` also writes a
  denial line to `security-events.jsonl`; `reanchor` emits one
  `.loop-run/events.jsonl` line like every step.

## Tasks

### T1: The product ref ships in shadow, and every boundary converges

- **Depends on:** none (ADR-0153 Accepted before `start`)
- **Spec behavior:** AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0018, AC-0019; TDD, and goal-based for the corpus and CI.
- **Touches:** `packs/core/.apm/skills/work-loop/scripts/_supervisor_commit.py`, `_supervisor_loop.py`, `_supervisor_admission.py`, `_supervisor_attempt.py`, `_supervisor_recovery.py`, `_supervisor_readiness.py`, `work-supervisor.py`, `supervisor-policy.json`, `SKILL.md`, `references/supervisor.md`, `evals/evals.json`; `contracts/delivery/execution-request.v1.schema.json`, `execution-result.v1.schema.json`; `packs/core/tests/skills/work-loop/`; `.github/workflows/build-check-windows.yml`; Core manifests and `docs/product/changelog.md`.
- **Verification mode:** TDD
- **Tests:**
  - **VI-0511 (AC-0001, AC-0002):** in a new `test_supervisor_product_ref.py`,
    after `start` and after each verb's step in a harness run, `git rev-parse`
    of the product ref equals `HEAD`; two worktrees admitted from one commit,
    and one run re-admitted after its store is retired, record different
    `Supervisor-Product-Ref` names.
  - **VI-0512 (AC-0003, AC-0004):** the AC-0003 seam moves the product ref to
    a commit descending from the source commit; `report` of an
    `implement-task` result refuses `integration-conflict`; both refs, the
    index, and `delivery/` bytes equal their pre-report values; the worker's
    files keep their bytes; `next` refuses until the test restores the ref;
    the same result then commits.
  - **VI-0513 (AC-0005):** a run whose commits were built with the product-ref
    trailer and ref removed gains the ref at its next `next`; the same run
    reset to an earlier made commit refuses `product-ref-diverged`.
  - **VI-0514 (AC-0007, AC-0008):** `git reset --hard HEAD~2` with no attempt
    open converges at the next `next` with the working tree equal to the
    product ref's tree; moving only the product ref back converges; the reset
    plus an edit to a file those steps changed refuses `projection-blocked`
    and leaves the edit's bytes.
  - **VI-0515 (AC-0009):** a symbolic product ref, a ref moved to a
    `git commit-tree` commit descending from `HEAD`, and a ref naming a
    non-made commit each refuse `product-ref-diverged` and write a denial line.
  - **VI-0516 (AC-0010, AC-0011, AC-0012):** the existing rebase scenario,
    an amend that keeps trailers and edits a product file, and a controller
    commit on top each issue `history-adoption` and commit nothing; the
    amended edit is absent from the product ref's tree; an `adopt-history`
    from `owner` naming `HEAD` commits one `reanchor` and the run then reaches
    `terminal`; an answer naming another commit, or from `plan-reviewer`,
    refuses; after a manifest-changing `reanchor`, `run-gates` and review run
    again before readiness.
  - **VI-0517 (AC-0013, AC-0014):** in `test_supervisor_attempt.py`, during an
    open `implement-task` attempt, creating, moving to a non-made commit,
    making symbolic, and deleting this run's product ref each refuse the
    result with `attempt-residue` until restored; a `report` that commits with
    the attempt open, and a `refs-moved` kill inside it, are not refused; a
    second worktree's run advancing its own product ref during the attempt
    leaves it admissible.
  - **VI-0518 (AC-0018):** `start` with `result_authority` absent, or set to
    `other`, refuses `invalid-policy` with owner `skill maintainer`.
  - **VI-0501 (AC-0006, AC-0015)** passes under `legacy-worktree`.
  - **VI-0519 (AC-0019):** the Windows CI job gains a step running
    `test_supervisor_product_ref.py` and `test_supervisor_attempt.py` with
    `WORK_SUPERVISOR_INTEGRATION=1`; it and the POSIX integration job pass,
    and the clean-environment import fence passes.
- **Done when:** T1's `Tests` pass, the existing supervisor suites still pass,
  and security-reviewer, adversarial-reviewer, and quality-engineer return
  clean.

### T2: Acceptance reads the product ref, and reversal is proven

- **Depends on:** T1
- **Spec behavior:** AC-0016, AC-0017, AC-0019; goal-based.
- **Touches:** `_supervisor_readiness.py`, `supervisor-policy.json`, `SKILL.md`, `references/supervisor.md`, `evals/evals.json`; `packs/core/tests/skills/work-loop/`; `ARCHITECTURE.md` and the architecture pages the spec's Durable Outputs list; Core manifests and changelog.
- **Verification mode:** goal-based
- **Tests:**
  - **VI-0521 (AC-0016):** under `protected-product-ref`, a harness run's
    subject has lineage `protected-product-ref` and `result_ref` equal to the
    product ref; a controller commit on `HEAD` leaves the subject unchanged
    until `adopt-history`, and changes it after.
  - **VI-0522 (AC-0017):** in the regenerate fixture of
    `test_supervisor_pinning.py`, a run pinned to one authority regenerates to
    the other after its first `implement` step, once each way, and reaches
    `terminal` with the uninterrupted run's final manifest; evidence from
    before the regeneration is re-established by `run-gates`.
  - **VI-0501 (AC-0006, AC-0015)** passes under `protected-product-ref`.
  - **VI-0519 (AC-0019)** passes with T2's suites.
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

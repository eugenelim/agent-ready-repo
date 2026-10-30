# Spec: Canonical result integration

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0144, ADR-0153, ADR-0151, ADR-0152, ADR-0150
- **Brief:** brief:acceptance-centered-work-loop
- **Discovery:** none
- **Depends on:** spec:execution-supervisor-cutover
- **Contract:** `contracts/delivery/delivery-subject.v1.schema.json` (consumed unchanged; a new `lineage.provider` value); `contracts/delivery/execution-request.v1.schema.json` and `execution-result.v1.schema.json` (extended additively: a `history-adoption` request reason and an `adopt-history` decision); `work-loop/supervisor-policy.json` (gains `result_authority`)
- **Shape:** service

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Protected semantic-policy contract.** `Contract`, `Scope and Non-goals`,
> `Durable Outputs`, `Agent Rules`, `Testing Strategy`, `Acceptance Criteria`,
> `Terminal Intent`, and `Accepted Risk` are approval-bound or explicitly
> review-authorized. A change follows its owning amendment, review, or risk
> decision. `Outcome`, `What Changes`, `Follow-ons`, and `Assumptions` are
> working material that may be corrected without changing accepted authority.

## Outcome

Maintainers running full-mode `work-loop` get a product result held in a protected Git ref that only the supervisor advances, by compare-and-swap, so a crash, a lost ref race, a reset, a rebase, a stray commit, or a worker's naive Git write either converges to the admitted product or stops the run until the owner's recorded decision admits it. Success is a synthetic run whose protected-ref and legacy `HEAD` subjects carry the same manifest at every step, and whose conflict, crash, divergence, adoption, and reversal fixtures all end with the uninterrupted run's product and no admitted change lost.

## What Changes

- Every supervisor step moves `HEAD` and the run's product ref together, in one compare-and-swap — `_supervisor_commit.py`.
- Each run's approval step names its own product ref, unique across worktrees and restarts — `_supervisor_admission.py`.
- Before deriving a request, the supervisor classifies how `HEAD` and the product ref relate and repairs, refuses, or asks the owner — `_supervisor_loop.py`.
- Attempt checks treat a change to this run's product ref that the supervisor did not make as a Git control-state change — `_supervisor_attempt.py`.
- A new `history-adoption` human decision lets the owner admit history the supervisor did not make — `_supervisor_loop.py`, the execution request and result schemas.
- `supervisor-policy.json` gains `result_authority`: the shadow release ships `legacy-worktree`, and the switch release ships `protected-product-ref`, under which the delivery subject reads the product ref.
- ADR-0153 supersedes ADR-0144 D9 for the result boundary, and the architecture pages describe the product ref as current.
- Core ships the shadow and the switch as two releases, and the Windows CI job runs the product-ref suites.

## Scope and Non-goals

This spec owns the sequential result boundary: the product ref, its
compare-and-swap, the conflict outcome, crash and partial-update repair,
divergence handling, owner adoption of foreign history, worker-forgery
detection, provider parity, the authority switch, and its reversal. ADR-0153
is Accepted before the first change that alters supervisor behavior merges,
and the switch release ships only after the shadow release.

It does not add a three-tree merge, parallel results, read or write sets,
sibling cancellation, `execution-result` source-tree fields, or the
`result-integration.v1` and `integration-conflict.v1` schemas; those belong to
Slice 7's parallel admission. It does not change which paths a result admits,
add path or byte caps, or add a Product addition profile. It does not prune
product refs after terminal, change light mode, remove `_subject_source.py`,
change what the delivery manifest hashes, or change how an installed-skill
change reaches a run in flight.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Decision rationale | Result authority moves only under an accepted record. | `docs/adr/0153-work-loop-product-result-is-a-protected-ref.md`; ADR-0144's `Superseded in part` mirror; the ADR index | Platform Core decision-maker | ADR shape lint | ADR-0153 is `Accepted` and ADR-0144 lists `D9` and `D11` as superseded in part by it. |
| Current architecture | The result boundary changes. | `ARCHITECTURE.md`; `docs/architecture/` `work-loop-result-integration.md`, `work-loop-authority-migration.md`, `work-loop-execution-supervisor.md`, `acceptance-centered-work-loop.md`, `work-loop-acceptance-evidence.md`, `work-loop-review-disposition.md`, `runtime-security-primitives.md` § 11 | Platform Core | Architecture review recorded in the ledger | Each page describes the product ref as the result boundary, and `work-loop-result-integration.md` separates what ships from what Slice 7 adds. |
| Maintainer procedure | The controller meets new refusals and a new human decision. | `work-loop/SKILL.md` and `work-loop/references/supervisor.md` | Core pack maintainers | Skill evals | The supervisor reference's refusal and human-decision tables name `integration-conflict`, `product-ref-diverged`, `projection-blocked`, `adoption-refused`, `unsupported-ref-storage`, and `history-adoption` with the controller's next action, including restoring a product ref to its recorded value. |
| Interface compatibility | The policy file gains a key; two delivery schemas gain values. | `work-loop/supervisor-policy.json`; `contracts/delivery/` | Core pack and `agentbundle` contract maintainers | Delivery contract tests | Every existing subject, request, and result record still validates. |
| Release history | Two releases change run behavior. | Core `pack.toml`, `plugin.json`, and `docs/product/changelog.md` | Core pack release maintainers | Version parity | Each release has an entry; the switch entry says which runs it reaches. |
| Product coordination | The slice closes. | The brief's Spec map | Platform Core | Brief-coverage lint | The map's `canonical-result-integration` row reports `Shipped`. |

## Agent Rules

### Always do

- Move the product ref only through the supervisor's hardened Git helper, and
  read confined files only through the shared confinement primitives.
- Prove each crash window, compare-and-swap race, and lost-work case with a
  test that runs.
- Get security-reviewer, adversarial-reviewer, and quality-engineer passes on
  every code task before merge.

### Ask first

- Raising the supervisor's minimum Git version.
- Choosing a Core version other than the next free one at merge time.

### Never do

- Add a module outside `work-loop/scripts/`, a dependency outside the standard
  library, or a parallel-result mechanism.
- Discard or overwrite a working-tree file that differs from both `HEAD` and
  the product ref.

## Testing Strategy

- **Integration boundary, conflict, and identity (AC-0001, AC-0002, AC-0003, AC-0004):**
  TDD at the supervisor's `start`, `next`, and `report` boundary over a real
  Git repository, because each is a compressible invariant on refs and trees.
- **Product-ref trust (AC-0005, AC-0006, AC-0022):** TDD at every verb over
  missing, symbolic, rolled-back, and planted refs, a reftable repository, and over a trailer-free run that
  crosses to this release by `regenerate`.
- **Crash and lag repair (AC-0007, AC-0008, AC-0009, AC-0010):** goal-based
  kill-point corpus, exercised as integration tests that kill the supervisor
  at each write and compare with the uninterrupted run, plus TDD over hard,
  soft, and mixed resets.
- **Divergence and adoption (AC-0011, AC-0012, AC-0013, AC-0014):** TDD at
  `next` and `report`, over rebased, amended, extra-commit, and
  forged-`delivery/` fixtures.
- **Worker forgery (AC-0015, AC-0016):** TDD on the attempt check, including
  a two-worktree fixture.
- **Parity, switch, and reversal (AC-0017, AC-0018, AC-0019, AC-0020):**
  goal-based synthetic full runs through the supervisor harness, crossing an
  authority change by the `regenerate` route, because parity and reversal are
  facts of whole runs.
- **Portability (AC-0021):** goal-based CI job checks.

## Acceptance Criteria

### Definitions

- **Product ref.** The run's ref, of the form
  `refs/agentbundle/delivery/<run-id>/<token>/product`, where `<token>` is
  fresh for each run admission.
- **Recorded value.** The product ref's name and the commit the run store
  last recorded for it; while a step is being committed, the store also
  records that step's pending commit.
- **Product manifest.** The sorted `(path, object id)` pairs of a commit's
  tree outside the spec directory.
- **Product result.** A `write-stub` or `implement-task` result `report`
  admits.
- **Source commit.** The commit the product ref named when the request for a
  product result was issued.
- **Made commit.** A commit this run's supervisor recorded as built, in its
  run store.
- **Anchor.** The product ref's recorded value or, for a run with no
  recorded product ref, its latest made commit.
- **Foreign history.** A commit reachable from `HEAD` and not from the anchor
  that is not a made commit.
- **Authority.** The `result_authority` value in the policy a run is pinned
  to: `legacy-worktree` or `protected-product-ref`.
- **Uninterrupted run.** The same synthetic run with no kill, race, reset,
  rebase, or adoption.

### Criteria

Integration boundary and identity

- [ ] **AC-0001.** After `start` admits a run, its product ref exists and
  names the commit of its `approval` step. Two runs admitted from the same
  spec and commit, in two worktrees or one after another, name different
  product refs.
- [ ] **AC-0002.** After every step a verb commits for a run with a recorded
  product ref, the product ref and `HEAD` name the same commit, and a `HEAD` that named a branch when the step began
  still names that branch.
- [ ] **AC-0003.** A product result whose source commit the product ref no
  longer names at the moment the supervisor moves it refuses with
  `integration-conflict`; neither ref, the index, nor any `delivery/` file
  changes.
- [ ] **AC-0004.** After an `integration-conflict`, every file the result
  changed keeps its bytes; `next` answers `attempt-residue` until the product
  ref names its recorded value again; the `next` after that re-issues the
  same request, and reporting its result commits those bytes.

Product-ref trust

- [ ] **AC-0005.** With no attempt open, when a recorded product ref is
  missing, symbolic, or names a commit other than its recorded value or the
  pending commit, every verb but `status` refuses with
  `product-ref-diverged`, owner `controller`, naming the ref and its recorded
  value, writes a denial line to the run's security log, and moves no ref.
  Restoring the ref to its recorded value clears the refusal. While an
  attempt is open, AC-0015's answer applies instead.
- [ ] **AC-0006.** A run with no recorded product ref, at every verb other
  than `status` with no attempt open, gains one naming its latest made commit
  when `HEAD` is that commit or that commit descends from `HEAD` through made
  commits only, after which AC-0009 and AC-0010 apply; otherwise `next`
  issues the AC-0011 decision and no ref is created. Steps committed while
  such a run's attempt is open create no ref.

Crash and lag repair

- [ ] **AC-0007.** A supervisor killed at any write of a step, of lag repair,
  or of adoption, and then resumed, ends with the same product ref tree,
  `HEAD` tree, `delivery/` bytes, and supervisor step list as the
  uninterrupted run, with no step committed twice. At every kill point the
  product ref names either the commit before that write or the commit after
  it.
- [ ] **AC-0008.** When one of `HEAD` and the product ref names a step's
  pending commit and the other names the commit before it, the next verb
  moves the lagging one to the pending commit.
- [ ] **AC-0009.** With no attempt open, when the product ref names its
  recorded value and descends from `HEAD` through made commits only, the next
  verb moves `HEAD` to it, and every tracked product file those commits
  changed then matches the product ref's tree, provided each such file's
  working-tree bytes and index entry match either `HEAD`'s or the product
  ref's version.
- [ ] **AC-0010.** When such a file matches neither version, the verb refuses
  with `projection-blocked`, owner `controller`, naming the file, and changes
  no ref, index entry, or file.

Divergence and adoption

- [ ] **AC-0011.** With no attempt open, when `HEAD` differs from the anchor
  in a way AC-0008 and AC-0009 do not repair, and AC-0005 does not refuse, `next`
  issues a `history-adoption`
  `human-decision` naming the `HEAD` commit, the count and at most 20 of the
  product paths adoption would change relative to the anchor, and whether it
  would change any file in the spec directory, and commits nothing.
- [ ] **AC-0012.** An `adopt-history` answer from an `owner` authority
  reference that names the current `HEAD` commit commits one `reanchor` step
  on `HEAD`, recording the anchor and the authority reference, and moves
  both refs to it, creating the product ref when none is recorded; the next `next` issues no
  `history-adoption` for that history. An answer naming any other commit, or
  with another authority role, refuses with `adoption-refused`, owner
  `controller`, and commits nothing.
- [ ] **AC-0013.** An `adopt-history` answer refuses with `adoption-refused`,
  owner `controller`, and commits nothing when
  the adopted history changes any `delivery/` file relative to the anchor.
- [ ] **AC-0014.** After a `reanchor` that changes the product manifest or a
  file in the spec directory, no evidence or review recorded before it counts
  toward readiness.

Worker forgery

- [ ] **AC-0015.** A worker attempt during which this run's product ref comes
  to name anything other than its recorded or pending value — created,
  moved, made symbolic, or deleted — has its result refused, `report` with
  `attempt-refused` and `next` with `attempt-residue`, until the ref is
  restored. The supervisor's own move while it commits that attempt's result
  is not refused.
- [ ] **AC-0016.** Another run's product-ref change in a sibling worktree
  during this run's attempt leaves the attempt admissible.

Parity, switch, and reversal

- [ ] **AC-0017.** In synthetic full `code` runs under each authority, after
  every committed step with no attempt open, and after every resumption in the
  AC-0007 corpus, the product manifest computed from the working tree's
  tracked files, the `HEAD` subject's manifest, and the product-ref subject's
  manifest are equal.
- [ ] **AC-0018.** Under `protected-product-ref`, the delivery subject carries
  lineage provider `protected-product-ref` and `result_ref` equal to the
  product ref commit, and foreign history on `HEAD` changes neither until an
  `adopt-history` answer admits it.
- [ ] **AC-0019.** A run regenerated from one authority to the other, in each
  direction, reaches `terminal` with the uninterrupted run's final product
  manifest, and evidence recorded under the earlier lineage does not count
  toward readiness under the later one.
- [ ] **AC-0020.** `start` refuses with `invalid-policy`, owner
  `skill maintainer`, when the installed policy's `result_authority` is
  missing or names neither authority.
- [ ] **AC-0022.** In a repository whose ref storage is not Git's files
  backend, `start` and every later verb but `status` refuse with
  `unsupported-ref-storage`, owner `owner`, and create no ref.

Portability

- [ ] **AC-0021.** `test_supervisor_product_ref.py`,
  `test_supervisor_attempt.py`, and `test_supervisor_pinning.py` pass on the
  POSIX supervisor-integration CI job and on the Windows CI job;
  `test_supervisor_crash_corpus.py` passes on the POSIX job; and the
  clean-environment import fence passes.

## Follow-ons

- Platform Core: brief `acceptance-centered-work-loop`, Slice 7 — three-tree
  apply, `result-integration.v1` and `integration-conflict.v1`, sibling
  cancellation, the Product addition profile, and result path and byte caps
  for parallel results.
- Platform Core: brief `acceptance-centered-work-loop`, Slice 8 — removing
  `_subject_source.py`, whose `legacy-worktree-snapshot` provider no caller
  uses, and pruning product refs at closeout.

## Terminal Intent

`code` — ship the shadow release, ship the switch, and close the slice.

## Accepted Risk

- A run keeps the authority it was pinned to at `start`. A Core release that
  changes `result_authority` reaches a run in flight only through the
  `regenerate` route, and that run then re-establishes its gates and reviews
  once because the subject's lineage changes; elsewhere it refuses
  `supervisor-changed`, as every installed-skill change does. The Platform
  Core decision-maker accepted this on 2026-10-30 because distribution is
  small.
- These controls catch a worker's naive Git writes. A deliberate worker
  running as the same operating-system user can write the run store that
  records made commits and so forge provenance; the run store stays the
  attempt-security trust root. The Platform Core decision-maker accepted this
  on 2026-10-30.
- An `adopt-history` answer's `owner` authority reference is recorded, not
  proven: the trusted controller supplies it, so adoption is as strong as the
  controller's relay of the owner's choice. The Platform Core decision-maker
  accepted this on 2026-10-30.

## Assumptions

none

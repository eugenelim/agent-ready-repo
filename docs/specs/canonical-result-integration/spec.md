# Spec: Canonical result integration

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0144, ADR-0153, ADR-0151, ADR-0152
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

Maintainers running full-mode `work-loop` get a product result held in a protected Git ref that only the supervisor advances, by compare-and-swap, so a crash, a lost ref race, a reset, a rebase, a stray commit, or a worker's naive Git write either converges to the admitted product or stops the run until a named human decides. Success is a synthetic run whose protected-ref and legacy `HEAD` subjects carry the same manifest at every step, and whose conflict, crash, divergence, adoption, and reversal fixtures all end with the uninterrupted run's product and no admitted change lost.

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
| Decision rationale | Result authority moves only under an accepted record. | `docs/adr/0153-work-loop-product-result-is-a-protected-ref.md`; ADR-0144's `Superseded in part` mirror; the ADR index | Platform Core decision-maker | ADR shape lint | ADR-0153 is `Accepted` and ADR-0144 lists `D9` as superseded in part by it. |
| Current architecture | The result boundary changes. | `ARCHITECTURE.md`; `docs/architecture/` `work-loop-result-integration.md`, `work-loop-authority-migration.md`, `work-loop-execution-supervisor.md`, `acceptance-centered-work-loop.md`, `work-loop-acceptance-evidence.md`, `work-loop-review-disposition.md`, `runtime-security-primitives.md` § 11 | Platform Core | Architecture review recorded in the ledger | Each page describes the product ref as the result boundary, and `work-loop-result-integration.md` separates what ships from what Slice 7 adds. |
| Maintainer procedure | The controller meets new refusals and a new human decision. | `work-loop/SKILL.md` and `work-loop/references/supervisor.md` | Core pack maintainers | Skill evals | The supervisor reference's refusal and human-decision tables name `integration-conflict`, `product-ref-diverged`, `projection-blocked`, and `history-adoption` with the controller's next action. |
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

- **Integration boundary, conflict, and identity (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005):**
  TDD at the supervisor's `start`, `next`, and `report` boundary over a real
  Git repository, because each is a compressible invariant on refs and trees.
- **Crash and lag repair (AC-0006, AC-0007, AC-0008):** goal-based kill-point
  corpus, exercised as integration tests that kill the supervisor at each
  write and compare with the uninterrupted run.
- **Divergence and adoption (AC-0009, AC-0010, AC-0011, AC-0012):** TDD at
  `next` and `report`, over reset, rebased, amended, and extra-commit
  fixtures.
- **Worker forgery (AC-0013, AC-0014):** TDD on the attempt check, including
  a two-worktree fixture.
- **Parity, switch, and reversal (AC-0015, AC-0016, AC-0017, AC-0018):**
  goal-based synthetic full runs through the supervisor harness, crossing an
  authority change by the `regenerate` route, because parity and reversal are
  facts of whole runs.
- **Portability (AC-0019):** goal-based CI job checks.

## Acceptance Criteria

### Definitions

- **Product ref.** The ref the run's first approval step names, of the form
  `refs/agentbundle/delivery/<run-id>/<token>/product`, where `<token>` is
  fresh for each run admission.
- **Product manifest.** The sorted `(path, object id)` pairs of a commit's
  tree outside the spec directory.
- **Product result.** A `write-stub` or `implement-task` result `report`
  admits.
- **Source commit.** The commit the product ref named when the request for a
  product result was issued.
- **Made commit.** A commit this run's supervisor recorded as built, in its
  run store.
- **Foreign history.** A commit reachable from `HEAD` or the product ref,
  after the run's approval commit, that is not a made commit.
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
- [ ] **AC-0002.** After every step a verb commits, the product ref and `HEAD`
  name the same commit, under both authorities.
- [ ] **AC-0003.** A product result whose source commit the product ref no
  longer names at the moment the supervisor moves it refuses with
  `integration-conflict`; neither ref, the index, nor any `delivery/` file
  changes.
- [ ] **AC-0004.** After an `integration-conflict`, every file the result
  changed keeps its bytes, every verb but `status` refuses until the product
  ref names the source commit again, and the same result reported then
  commits.
- [ ] **AC-0005.** A run admitted before product refs existed gains one at its
  first verb with no attempt open when `HEAD` carries every step its made
  commits record; otherwise every verb but `status` refuses
  `product-ref-diverged`.

Crash and lag repair

- [ ] **AC-0006.** A supervisor killed at any write of a step, of lag repair,
  of adoption, or of re-anchoring, and then resumed, ends with the same
  product ref tree, `HEAD` tree, `delivery/` bytes, and supervisor step list
  as the uninterrupted run, with no step committed twice. At every kill point
  the product ref names either the commit before that write or the commit
  after it.
- [ ] **AC-0007.** When one of `HEAD` and the product ref descends from the
  other only through made commits, the next verb moves the lagging one to the
  other, and every tracked product file those commits changed then matches
  the leading commit's tree.
- [ ] **AC-0008.** When that repair would change a working-tree file whose
  bytes match neither `HEAD` nor the product ref, the verb refuses with
  `projection-blocked`, owner `controller`, naming the file, and changes no
  ref or file.

Divergence and adoption

- [ ] **AC-0009.** When the product ref is symbolic, names a commit that is
  not a made commit, or descends from `HEAD` through foreign history, every
  verb but `status` refuses with `product-ref-diverged`, owner `controller`,
  records a denial in the run's security log, and moves no ref.
- [ ] **AC-0010.** With no attempt open, when `HEAD` carries foreign history
  — a reset onto older work plus a new commit, a rebase, an amend, or a commit
  on top of the product ref — and the product ref names a made commit, `next`
  issues a `history-adoption` `human-decision` naming the `HEAD` commit and
  commits nothing.
- [ ] **AC-0011.** An `adopt-history` answer from an `owner` authority
  reference that names the current `HEAD` commit commits one `reanchor` step
  on `HEAD` that records the prior product ref commit and the authority
  reference, and moves both refs to it. An answer naming any other commit, or
  lacking `owner` authority, refuses and commits nothing.
- [ ] **AC-0012.** After a `reanchor` that changes the product manifest, no
  evidence or review recorded before it counts toward readiness.

Worker forgery

- [ ] **AC-0013.** A worker attempt during which this run's product ref is
  created, moved to a commit that is not a made commit, made symbolic, or
  deleted has its result refused as a Git control-state change, and `next`
  answers `attempt-residue` until the ref is restored. The supervisor's own
  move of the ref while it commits that attempt's result is not refused.
- [ ] **AC-0014.** Another run's product-ref change in a sibling worktree
  during this run's attempt leaves the attempt admissible.

Parity, switch, and reversal

- [ ] **AC-0015.** In synthetic full `code` runs under each authority, at
  every committed step and after every resumption in the AC-0006 corpus and
  every adoption, the subject from `HEAD` and the subject from the product ref
  have equal product manifests, exclusions, spec identity, and evidence
  policy.
- [ ] **AC-0016.** Under `protected-product-ref`, the delivery subject carries
  lineage provider `protected-product-ref` and `result_ref` equal to the
  product ref commit, and foreign history on `HEAD` changes neither until an
  `adopt-history` answer admits it.
- [ ] **AC-0017.** A run regenerated from one authority to the other, in each
  direction, reaches `terminal` with the uninterrupted run's final product
  manifest, and evidence recorded under the earlier lineage does not count
  toward readiness under the later one.
- [ ] **AC-0018.** `start` refuses with `invalid-policy`, owner
  `skill maintainer`, when the installed policy's `result_authority` is
  missing or names neither authority.

Portability

- [ ] **AC-0019.** The suites that verify AC-0001 through AC-0016 pass on the
  POSIX supervisor-integration CI job and on the Windows CI job, and the
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

## Assumptions

none

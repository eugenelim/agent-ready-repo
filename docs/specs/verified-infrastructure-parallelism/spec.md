# Spec: Verified infrastructure parallelism

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0156, ADR-0154, ADR-0151, ADR-0144, ADR-0005, ADR-0061
- **Brief:** brief:acceptance-centered-work-loop
- **Discovery:** none
- **Depends on:** spec:canonical-result-integration
- **Contract:** `contracts/delivery/containment-attestation.v1.schema.json` (extended additively: an attempt binding, write roots, and a denial set); `contracts/delivery/access-attestation.v1.schema.json`, `result-integration.v1.schema.json`, and `integration-conflict.v1.schema.json` (new); `contracts/delivery/execution-request.v1.schema.json` (a `run-concurrent` request kind); `contracts/delivery/task-contract.v1.schema.json` (`reads` and `writes`); `work-loop/supervisor-policy.json` (gains `concurrency` and `reprojection_bound`)
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

Maintainers running full-mode `work-loop` get `implement-task` attempts that run at the same time only when an attestation the supervisor checks itself proves each attempt's isolation and every product read, and that otherwise run one after another exactly as they do today. Success is a corpus in which every missing condition serializes, every undeclared read is denied or joins the attested set, and every permutation of an admitted schedule ends with the sequential run's product tree and acceptance verdict, with Pi absent.

## What Changes

- Plan tasks may declare `Reads:` and `Writes:` sets; the projector records them in the task contract and its revision — `_supervisor_projector.py`, `task-contract.v1`.
- `supervisor-policy.json` gains `concurrency` (shipped `sequential`) and `reprojection_bound` — `work-loop/supervisor-policy.json`, `_supervisor_admission.py`.
- `start` pins an owner-approved launcher by sha256 and refuses a repository that configures a merge driver — `_supervisor_admission.py`, `_supervisor_git.py`.
- A new `run-concurrent` request kind: the supervisor spawns the pinned launcher once per admitted attempt, verifies its containment attestation before the worker starts, and collects its access attestation at the end over the launcher's own pipe — new `_supervisor_concurrency.py`, `_containment.py`.
- Admitted results integrate one at a time, in the sequential floor's order, through a pinned `git merge-tree --write-tree` onto the protected product ref; a meeting, conflict, or lost compare-and-swap records `integration-conflict.v1` and reprojects the task — new `_supervisor_integration.py`, `_supervisor_commit.py`.
- Each concurrent attempt has its own fresh tree, manifest, and residue record — `_supervisor_attempt.py`.
- `containment-attestation.v1` gains an attempt binding, write roots, and a denial set; `access-attestation.v1`, `result-integration.v1`, and `integration-conflict.v1` join `contracts/delivery/`.
- A test-only fixture launcher and the permutation and conflict corpus live in `packs/core/tests/skills/work-loop/`.
- The result-integration, execution-supervisor, runtime-security-primitives, and loop-parallelism architecture pages describe the concurrent path as built.
- **Known limit.** No shipped host can attest isolation or reads, and Core ships no attesting launcher. Every adopter therefore runs on the sequential floor. The concurrent path is proven only against the test-only fixture launcher until a verified containment adapter exists.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | New and extended delivery records | `contracts/delivery/` four schemas plus `execution-request.v1` and `task-contract.v1` | Core pack maintainers | Schema-parity and record-validation suites | Every record the corpus writes validates; every pre-existing record still validates |
| Current architecture | The result-integration design becomes as-built | `docs/architecture/work-loop-result-integration.md` §§ 1a–8, `work-loop-execution-supervisor.md`, `runtime-security-primitives.md` § 7, `loop-parallelism.md` | Core pack and `agentbundle` maintainers | Page diffs in the integration and corpus PRs | No `STATUS: PLANNED` remains for a built element; the known limit is stated on the result-integration page |
| Maintainer procedure | Plan authors declare read and write sets; operators read admission outcomes | `packs/core/.apm/skills/work-loop/references/supervisor.md`; the new-spec plan template's task grammar | Core pack maintainers | Reference and template diffs | The `Reads:` and `Writes:` grammar and the `status` admission fields are documented once |
| Product truth | The brief's slice moves | `docs/product/briefs/acceptance-centered-work-loop.md` spec map | Brief owner | Spec-map row | The row names this spec |
| Release history | Core changes ship as patch releases | `packs/core/pack.toml`, `plugin.json`, changelog fragment per Core PR | Core release maintainers | Version bump per Core PR | Each Core PR's version is one patch above `packs/core/pack.toml` at its merge base with freshly fetched `origin/main` |
| Verification record | Closeout evidence | `docs/specs/verified-infrastructure-parallelism/notes/verification-ledger.md` | Spec owner | Ledger rows per criterion | Every criterion is checked against a named test or run |

## Agent Rules

### Always do

- Verify every attestation from the launcher's own pipe, inside the supervisor process that spawned it.
- Run every `git` call, including the three-way apply and `check-attr`, through the hardened Git helper.
- Prove each refusal and each fall to the floor with a test that runs.
- Get security-reviewer, adversarial-reviewer, and quality-engineer passes on every code task before merge.

### Ask first

- Shipping any `concurrency` value other than `sequential` in `supervisor-policy.json`.
- Raising the Git floor of the sequential path above 2.32.
- Changing the launcher protocol, a binding field, or a schema after its contract PR merges.

### Never do

- Ship, install, or document an attesting launcher, or make the fixture launcher reachable outside the test corpus.
- Admit concurrency from `Depends on:`, `Touches:`, a declared write set alone, a task category, or a model's judgment.
- Trust an attestation, read set, or binding carried by `report`, the journal, the run store's worker-writable files, or an attempt tree.
- Add a dependency outside the standard library, a module outside `work-loop/scripts/`, or any import of a Pi or other runtime package.
- Run any request kind other than `implement-task` concurrently.

## Testing Strategy

- **Admission and the floor (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006):** TDD at `start`, `next`, and `status` over a real Git repository, one fixture per missing condition, because admission is a compressible predicate over a closed condition list.
- **Attestation verification (AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012):** TDD at the launcher boundary with the fixture launcher scripted to emit each defect, because each defect is one refusal with one oracle.
- **Read and write semantics (AC-0013, AC-0014, AC-0015):** TDD over the meet relation's table, then integration tests through `run-concurrent` with a scripted undeclared read in each mode.
- **Integration (AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025):** TDD at the integration boundary over real trees and refs, plus goal-based kill-point and race fixtures exercised as integration tests, because ordering and compare-and-swap are facts of whole runs.
- **Attempt isolation and blast radius (AC-0026, AC-0027, AC-0028, AC-0029, AC-0030):** integration tests over two- and three-attempt batches with injected refusal, failure, and cancellation.
- **Determinism (AC-0031, AC-0032):** goal-based permutation corpus that runs every completion order of each fixture schedule and compares with the sequential run, exercised end to end through the supervisor harness.
- **Contracts (AC-0033, AC-0034):** goal-based schema validation of every record the corpus writes, plus the existing parity suites.

## Acceptance Criteria

### Definitions

- **Floor.** The sequential execution mode every host supports: one attempt open at a time.
- **Concurrent mode.** `enforced-allowlist` or `complete-trace`, the value of the run's pinned `concurrency` policy.
- **Floor order.** The order in which the floor would issue the plan's tasks: repeatedly, the first task in plan order whose dependencies are complete.
- **Launcher.** The executable whose sha256 the run's approval record names and `start` pins. The supervisor spawns it once per concurrent attempt.
- **Fixture launcher.** The test-only launcher in `packs/core/tests/skills/work-loop/` that simulates an attesting host. It is a fixture, not a host.
- **Binding.** The run id, attempt id, grant id, a fresh 32-byte nonce, and the launcher's sha256 that the supervisor issues for one attempt.
- **Read.** A file read, a lookup of a path that does not exist, a directory listing, or a recursive walk.
- **Write.** A creation, modification, deletion, either end of a rename, or a mode or type change.
- **Meets.** A read or write meets a write exactly when one row holds: a missing-path lookup and a write creating that path; a listing of a directory and a write adding, removing, or renaming an entry directly in it; a walk of a root and any write under it; any other read or write and a write to the same path.
- **Declared sets.** The `Reads:` and `Writes:` entries of a task. An entry is a repository-relative path (a file), a path ending in `/` (a listing of that directory), or a path ending in `/**` (a walk of that root).
- **Verified containment attestation.** A `containment-attestation.v1` read from the launcher's stdout before the worker starts that validates against its schema; carries the issued binding exactly; has `read_enforcement` `allowlist` under `enforced-allowlist` or `trace` under `complete-trace`; has `network.allowed` false; has write roots equal to the attempt's tree; has roots no broader than the grant; and denies all six of `git-common-dir`, `shared-refs`, `run-store`, `delivery`, `sibling-trees`, and `sibling-ipc`.
- **Complete access attestation.** An `access-attestation.v1` read from the launcher's stdout after the worker ends that carries the issued binding, the sha256 of the `execution-result.v1` the supervisor computed for the attempt, and `complete` true.
- **Held result.** A finished concurrent result waiting for its turn in floor order. It is not an open attempt.

### Criteria

Admission and the floor

- [ ] **AC-0001.** Under the shipped `supervisor-policy.json`, `concurrency` is `sequential`, and a synthetic run issues no `run-concurrent` request and never has two attempts open.
- [ ] **AC-0002.** With `concurrency` set to a concurrent mode and a launcher pinned, a task whose conditions all hold is issued in a `run-concurrent` request; removing any one member of this closed condition set — the policy opt-in, a `Reads:` field, a `Writes:` field, the absence of a stub fence, completed dependencies, an unspent reprojection bound, Git 2.41 or later, a pinned launcher, or a verified containment attestation — issues that task only on the floor, and `start`, `next`, and `report` refuse nothing because of it.
- [ ] **AC-0003.** A floor attempt is issued only while no attempt is open, no attempt opens while it runs, and a held result does not prevent a floor attempt from being issued.
- [ ] **AC-0004.** Two tasks are never in the same `run-concurrent` request when a declared read or write of either meets a declared write of the other.
- [ ] **AC-0005.** A `Reads:` or `Writes:` entry that is absolute, contains `..`, contains a glob character other than a trailing `/**`, or names a path under `delivery/` or the spec directory leaves its task on the floor, and a change to either field changes the task's revision.
- [ ] **AC-0006.** `status` reports, for every task that ran or is open, whether it ran concurrently or on the floor and, for a floor task in a concurrent-mode run, the first missing condition from AC-0002's list.

Attestation verification

- [ ] **AC-0007.** `start` pins a launcher only when the run's approval record names its sha256; it copies the launcher into the run store, and a launcher whose bytes differ from the pinned sha256 at spawn sends that attempt to the floor and records a security event.
- [ ] **AC-0008.** The supervisor sends an attempt's release token only after verifying its containment attestation, and a result whose access attestation does not carry that release token is treated as having no complete access attestation (AC-0012).
- [ ] **AC-0009.** A containment attestation with any one of these defects sends its task to the floor without releasing the worker: a schema violation, a nonce issued to another attempt, a nonce from an earlier attempt of the same task, a run id of another run, a grant id not issued for the attempt, a launcher sha256 other than the pinned one, a mismatched `read_enforcement`, network allowed, write roots other than the attempt's tree, roots broader than the grant, or any of the six denials missing.
- [ ] **AC-0010.** A `report` for a `run-concurrent` request admits completion only; a report asserting an attestation, read set, write set, or binding refuses `result-fact-refused`.
- [ ] **AC-0011.** `start` refuses `launcher-fixture-refused` for a launcher whose bytes carry the fixture marker unless the in-process test seam enables it, and no file the Core pack installs or builds contains the fixture launcher.
- [ ] **AC-0012.** A result whose access attestation is missing, unbound, bound to a different `execution-result.v1` sha256, or not `complete` integrates only while the product ref names its source commit, and otherwise refuses `integration-conflict`.

Reads and writes

- [ ] **AC-0013.** The meet relation returns true exactly for the pairs in the Meets definition, over a table that covers every row and a non-meeting pair for each.
- [ ] **AC-0014.** Under `enforced-allowlist`, a worker's read outside its declared reads appears in the access attestation as denied and not in the attested read set.
- [ ] **AC-0015.** Under `complete-trace`, a worker's read outside its declared reads joins the attested read set, and the integration check of AC-0017 uses it.

Integration

- [ ] **AC-0016.** Admitted results integrate in floor order: the product ref's commits for a batch appear in floor order whatever order the attempts finish in, and a held result integrates only after every earlier task has integrated.
- [ ] **AC-0017.** A result whose attested read or write set meets a path changed on the product ref between its source commit and the observed tip refuses: the product ref, `HEAD`, the index, and every `delivery/` file are unchanged, an `integration-conflict.v1` is recorded, and the task is reprojected from the new tip.
- [ ] **AC-0018.** Two results changing the same line of one file produce a content conflict on the later one in floor order, with the outcome of AC-0017.
- [ ] **AC-0019.** The three-way apply uses the result's source commit as its merge base and reads attributes only from the empty tree, so a `merge=union` in the checked-out `.gitattributes` does not resolve a conflict.
- [ ] **AC-0020.** A non-default `merge` attribute on any changed path, from `info/attributes` or a configured `core.attributesFile`, refuses the result with the outcome of AC-0017.
- [ ] **AC-0021.** `start` refuses `unsupported-git-config` for a repository whose configuration defines any `merge.<name>.driver`.
- [ ] **AC-0022.** An apply whose tree changes a path outside the result's attested write set refuses with the outcome of AC-0017.
- [ ] **AC-0023.** A compare-and-swap lost to a concurrent ref move refuses with the outcome of AC-0017, and a kill at each integration write point leaves the product ref at its old or new commit and a rerun converges to the uninterrupted run's tree.
- [ ] **AC-0024.** Every `integration-conflict.v1` holds product paths only, at most 1,000 of them, and no file contents, and passes the `integration-diagnostic` content profile.
- [ ] **AC-0025.** Every successful concurrent integration records one `result-integration.v1` naming the source commit, observed tip, result commit, result tree, and the apply algorithm with the Git version that ran it.

Attempt isolation and blast radius

- [ ] **AC-0026.** Each concurrent attempt runs in a fresh directory that holds no `.git` entry and is never reused, and has its own manifest; a change to a trusted file, Git control state, or `delivery/` during the attempt refuses that attempt with `attempt-residue` whether or not siblings are open.
- [ ] **AC-0027.** A refused, conflicting, or failed attempt reprojects only itself and each running sibling whose declared sets meet its own; every other sibling's result integrates.
- [ ] **AC-0028.** A cancelled attempt's launcher process tree is ended and its end confirmed before the task is reprojected onto a fresh directory; an unconfirmed end sends the task to the floor; a cancelled attempt's result never integrates.
- [ ] **AC-0029.** A task reprojected `reprojection_bound` times (shipped value 2) runs its next attempt on the floor, and every reprojection appears in the journal and in `status`.
- [ ] **AC-0030.** A controller replan or stub-fence revision is admitted only while no attempt is open and no result is held.

Determinism and portability

- [ ] **AC-0031.** For each fixture schedule in the corpus, every permutation of attempt completion order ends with a product tree and an `acceptance-verdict.v1` byte-equal to the sequential run's over the same scripted attempt outputs.
- [ ] **AC-0032.** The corpus runs with no Pi executable resolvable on `PATH` and no Pi module importable, and it fails if either resolves.

Contracts

- [ ] **AC-0033.** Every `containment-attestation.v1`, `access-attestation.v1`, `result-integration.v1`, `integration-conflict.v1`, `execution-request.v1`, and `task-contract.v1` record the corpus writes validates against its schema in `contracts/delivery/`.
- [ ] **AC-0034.** Every `containment-attestation.v1` and `task-contract.v1` fixture that validated before this spec still validates.

## Follow-ons

none

## Assumptions

none

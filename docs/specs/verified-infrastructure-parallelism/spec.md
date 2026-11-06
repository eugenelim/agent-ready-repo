# Spec: Verified infrastructure parallelism

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0156, ADR-0160, ADR-0154, ADR-0151, ADR-0144, ADR-0005, ADR-0061
- **Brief:** brief:acceptance-centered-work-loop
- **Discovery:** none
- **Depends on:** spec:canonical-result-integration
- **Contract:** `contracts/delivery/containment-attestation.v1.schema.json` (extended additively: an attempt binding, a read allowlist, write roots, and a denial set); `contracts/delivery/access-attestation.v1.schema.json`, `launcher-message.v1.schema.json`, `result-integration.v1.schema.json`, and `integration-conflict.v1.schema.json` (new); `contracts/delivery/execution-request.v1.schema.json` (a `run-concurrent` request kind); `contracts/delivery/execution-result.v1.schema.json` (extended additively: a supervisor-written result tree and access-attestation sha256); `contracts/delivery/task-contract.v1.schema.json` (`reads` and `writes`); the `delivery/approvals.jsonl` approval line (gains `launcher_sha256`); `work-loop/supervisor-policy.json` (gains `concurrency`, `reprojection_bound`, `max_concurrent_attempts`, and `attempt_timeout_seconds`)
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

Maintainers running full-mode `work-loop` get `implement-task` attempts that may run at the same time only when an attestation the supervisor checks itself proves each attempt's isolation and every product read, and that otherwise run one after another exactly as they do today; no adopter reaches the concurrent path until a host can attest. Success is a corpus in which every missing condition serializes, every undeclared read is denied or joins the attested set, and every forced permutation of an admitted schedule ends with the sequential run's product tree and acceptance outcomes, with Pi absent.

## What Changes

- Plan tasks may declare `Reads:` and `Writes:` sets; the projector records them in the task contract and its revision — `_supervisor_projector.py`, `task-contract.v1`.
- `supervisor-policy.json` gains `concurrency` (shipped `sequential`), `reprojection_bound`, `max_concurrent_attempts`, and `attempt_timeout_seconds` — `work-loop/supervisor-policy.json`, `_supervisor_admission.py`.
- `start` pins a launcher whose sha256 the owner's own approval answer supplies, and refuses a repository that configures a merge driver — `_supervisor_admission.py`, `_supervisor_git.py`.
- A new `run-concurrent` request kind and blocking verb: the supervisor spawns the pinned launcher once per admitted attempt, verifies its containment attestation before releasing the worker, and reads its access attestation at the end over the launcher's own pipe — new `_supervisor_concurrency.py`, `_containment.py`.
- Each concurrent attempt runs in a fresh directory outside the Git directory, the run store, and the work tree, with its own manifest; the supervisor ingests the directory into Git objects itself once the launcher has ended — `_supervisor_attempt.py`, `_supervisor_concurrency.py`.
- Admitted results integrate one at a time, in the sequential floor's order, through a pinned `git merge-tree --write-tree` onto the protected product ref; a meeting, conflict, merge-configuration hazard, or lost compare-and-swap records `integration-conflict.v1` and reprojects the task — new `_supervisor_integration.py`, `_supervisor_commit.py`.
- `containment-attestation.v1` gains an attempt binding, a read allowlist, write roots, and a denial set; `access-attestation.v1`, `launcher-message.v1`, `result-integration.v1`, and `integration-conflict.v1` join `contracts/delivery/`.
- A test-only fixture launcher and the permutation and conflict corpus live in `packs/core/tests/skills/work-loop/`.
- The result-integration, execution-supervisor, runtime-security-primitives, and loop-parallelism architecture pages describe the concurrent path as built.
- Not in this spec: the Product addition profile for added paths stays planned on the result-integration page; ingestion admits exactly what the floor's change-set computation admits.
- **Known limit.** No shipped host can attest isolation or reads, and Core ships no attesting launcher. Every adopter therefore runs on the sequential floor. The concurrent path is proven only against the test-only fixture launcher until a verified containment adapter exists.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Interface compatibility | New and extended delivery records and the launcher protocol | `contracts/delivery/` five new or extended schemas plus `execution-request.v1` and `task-contract.v1` | Core pack maintainers | Schema-parity and record-validation suites | AC-0063 and AC-0064 hold |
| Current architecture | The result-integration design becomes as-built | `docs/architecture/work-loop-result-integration.md` §§ 1a–8, `work-loop-execution-supervisor.md`, `runtime-security-primitives.md` § 7 (launcher trust root, binding, release token, and the `run-concurrent` result-acceptance row), `loop-parallelism.md` | Core pack and `agentbundle` maintainers | Page diffs in the corpus task | No `STATUS: PLANNED` remains on an element this spec builds; the Product addition profile stays planned; the known limit is stated on the result-integration page |
| Result acceptance | `report` admits completion only for `run-concurrent`; this spec owns that row (AC-0021) | The Result acceptance table in `runtime-security-primitives.md` § 7, citing this spec for the row | Core pack maintainers | Table row | The § 7 table carries the `run-concurrent` row |
| Maintainer procedure | Plan authors declare read and write sets; operators read admission reasons | `packs/core/.apm/skills/work-loop/references/supervisor.md`; the new-spec plan template's task grammar | Core pack maintainers | Reference and template diffs | The `Reads:` and `Writes:` grammar and the `status` reason codes are documented once |
| Product truth | The brief's slice moves | `docs/product/briefs/acceptance-centered-work-loop.md` spec map | Brief owner | Spec-map row reporting status | The row reports `Shipped` at closeout |
| Release history | Core changes ship as patch releases | `packs/core/pack.toml`, `plugin.json`, changelog fragment per Core PR | Core release maintainers | Version bump per Core PR | Each Core PR's version is one patch above `packs/core/pack.toml` at its merge base with freshly fetched `origin/main` |
| Verification record | Closeout evidence | `docs/specs/verified-infrastructure-parallelism/notes/verification-ledger.md` | Spec owner | Ledger rows per criterion | Every criterion is checked against a named test or run |

## Agent Rules

### Always do

- Verify every attestation from the launcher's own pipe, inside the supervisor process that spawned it.
- Run every `git` call, including the three-way apply and `check-attr`, through the hardened Git helper.
- Read a worker-written attempt directory only through the blessed confinement helpers in `file_safety.py`, extending that module when ingestion needs a walk it lacks.
- Prove each refusal and each fall to the floor with a test that runs, and drive every timeout through an injectable clock or value, never a sleep.
- Get security-reviewer, adversarial-reviewer, and quality-engineer passes on every code task before merge.

### Ask first

- Shipping any `concurrency` value other than `sequential` in `supervisor-policy.json`.
- Raising the Git floor of the sequential path above 2.32.
- Changing the launcher protocol, a binding field, or a schema after its contract task merges.

### Never do

- Ship, install, or document an attesting launcher, or make the fixture launcher reachable outside the test corpus.
- Admit concurrency from `Depends on:`, `Touches:`, a declared write set alone, a task category, or a model's judgment.
- Trust an attestation, read set, or binding carried by `report`, the journal, an attempt directory, or any run-store file other than a held-result record the supervisor wrote and an attempt manifest covers.
- Persist, log, or pass to the launcher's children a release token.
- Add a dependency outside the standard library, a module outside `work-loop/scripts/`, or any import of a Pi or other runtime package.
- Run any request kind other than `implement-task` concurrently.

## Testing Strategy

- **Admission and the floor (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012):** TDD at `start`, `next`, and `status` over a real Git repository, one fixture per missing condition plus a non-meeting pair as the positive control, because admission is a compressible predicate over a closed condition list.
- **Launcher and attestation (AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0065, AC-0066, AC-0067, AC-0069):** TDD at the launcher boundary with the fixture launcher scripted to emit each defect, because each defect is one refusal with one oracle; the build-output check is a roster test, because pack tests may not read outside the pack.
- **Reads, writes, and paths (AC-0026, AC-0027, AC-0028):** TDD through `run-concurrent`, asserting the supervisor's response to scripted attestations, never the fixture's own output.
- **Ingestion and held results (AC-0029, AC-0030, AC-0031, AC-0032, AC-0033, AC-0070, AC-0071, AC-0073):** TDD at the ingestion boundary over link, special-file, oversized, late-write, and tamper fixtures.
- **Integration (AC-0034, AC-0035, AC-0036, AC-0037, AC-0038, AC-0039, AC-0040, AC-0041, AC-0042, AC-0043, AC-0044, AC-0045, AC-0046, AC-0047, AC-0048, AC-0072, AC-0074):** TDD at the integration boundary over real trees and refs; the apply-level conflict and attribute cases drive the apply step directly as defence in depth, because admission keeps meeting tasks apart; kill points and ref races are integration tests.
- **Isolation, blast radius, and plan changes (AC-0049, AC-0050, AC-0051, AC-0052, AC-0053, AC-0054, AC-0055, AC-0056, AC-0057, AC-0058, AC-0068):** integration tests over two- and three-attempt batches with injected refusal, failure, tamper, and cancellation.
- **Determinism (AC-0059, AC-0060, AC-0061, AC-0062):** goal-based permutation corpus, exercised end to end through the supervisor harness, with completion order forced by fixture coordination and observed in the journal.
- **Contracts (AC-0063, AC-0064):** goal-based schema validation in one roster suite that runs the corpus and collects its records, plus the existing parity suites.

## Acceptance Criteria

### Definitions

- **Floor.** The sequential execution mode every host supports: one attempt open at a time.
- **Concurrent mode.** `enforced-allowlist` or `complete-trace`, the value of the run's pinned `concurrency` policy.
- **Integrated.** A task's result is integrated once the product ref names a commit the supervisor made for it. A task is complete only once its result is integrated; a held result's task is not complete.
- **Floor order.** The order in which the floor would issue the plan's tasks: repeatedly, the first task in plan order whose dependencies are complete.
- **Launcher.** The executable whose sha256 the run's approval line names in `launcher_sha256` and `start` pins. The supervisor spawns it once per concurrent attempt.
- **Fixture launcher.** The test-only launcher in `packs/core/tests/skills/work-loop/` that simulates an attesting host. It is a fixture, not a host.
- **Binding.** The run id, attempt id, grant id, a fresh 32-byte nonce, and the launcher's sha256 that the supervisor issues for one attempt.
- **Release token.** 32 bytes from the operating system's secure random source that the supervisor sends one attempt's launcher after verifying its containment attestation.
- **Attempt directory.** A directory the supervisor creates empty for one attempt, outside the Git directory, the Git common directory, the run store, and the work tree, and never reuses.
- **Repository path.** A relative path with `/` separators and no empty, `.`, or `..` component, no NUL, control character, or backslash. Paths compare after Unicode NFC normalization, and case-insensitively when the repository's `core.ignoreCase` is true.
- **Read.** A file read, a lookup of a path that does not exist, a directory listing, or a recursive walk.
- **Write.** A creation, modification, deletion, either end of a rename, or a mode or type change of a path; a write also creates or removes each ancestor directory it brings into or out of existence.
- **Meets.** A read or write meets a write exactly when one row holds: a missing-path lookup and a write creating that path; a listing of a directory and a write adding, removing, or renaming an entry directly in it; a walk of a root and any write at or under it; any other read or write and a write to the same path. A declared write entry `root/**` writes every path at or under `root`.
- **Declared sets.** The `Reads:` and `Writes:` entries of a task, each a repository path. A `Reads:` entry is a file path, a path ending in `/` (a listing), or a path ending in `/**` (a walk). A `Writes:` entry is a file path or a path ending in `/**`.
- **Verified containment attestation.** A `containment-attestation.v1` that passes every check AC-0017 lists.
- **Complete access attestation.** An `access-attestation.v1` that passes every check AC-0020 lists.
- **Result identity.** The tree id the supervisor computes when it ingests the attempt directory after confirming the attempt's end, and the sha256 of the exact `access` line bytes, both recorded at that moment in the `execution-result.v1` the supervisor writes for the attempt.
- **Policy keys.** `concurrency` (`sequential` | `enforced-allowlist` | `complete-trace`, shipped `sequential`); `max_concurrent_attempts` (2 to 8, shipped 4); `reprojection_bound` (0 to 8, shipped 2); `attempt_timeout_seconds` (60 to 86,400, shipped 3600). A policy file with any value outside its range refuses `start`.
- **Held result.** A finished concurrent result, recorded by its result identity, waiting for its turn in floor order. It is not an open attempt.
- **Refusal outcome.** The product ref, `HEAD`, the index, and every `delivery/` file are unchanged; one `integration-conflict.v1` is recorded; and the task is reprojected from the new tip.

### Criteria

Admission and the floor

- [ ] **AC-0001.** Under the shipped `supervisor-policy.json`, `concurrency` is `sequential`, and a synthetic run issues no `run-concurrent` request and never has two attempts open.
- [ ] **AC-0002.** A task missing any one member of this closed set is never named in a `run-concurrent` request, is issued on the floor at its turn, and causes no refusal of `start`, `next`, or `report`: the policy opt-in, a `Reads:` field, a `Writes:` field, the absence of a stub fence, an unspent reprojection bound, a POSIX host, Git 2.41 or later, the absence of any `merge.*` key other than a `merge.<name>.driver` (which AC-0040 refuses) in repository configuration, and a launcher pin.
- [ ] **AC-0003.** Two tasks that hold every member of AC-0002's set, have complete dependencies, and whose declared sets do not meet are named in the same `run-concurrent` request.
- [ ] **AC-0004.** No two attempts are open at the same time when a declared read or write of either meets a declared write of the other.
- [ ] **AC-0005.** At most one `run-concurrent` request is open at a time.
- [ ] **AC-0006.** No `run-concurrent` request names more tasks than `max_concurrent_attempts` (Policy keys).
- [ ] **AC-0007.** A floor attempt is issued only while no attempt is open, and no attempt opens while it runs.
- [ ] **AC-0008.** A held result does not prevent a floor attempt from being issued.
- [ ] **AC-0009.** A task whose dependency has only a held result is not issued.
- [ ] **AC-0010.** A `Reads:` or `Writes:` entry that is not a repository path, that uses a glob character other than a trailing `/**`, that is a `Writes:` entry ending in `/`, or that names a path under `delivery/` or the spec directory leaves its task on the floor.
- [ ] **AC-0011.** A change to a task's `Reads:` or `Writes:` field changes its revision.
- [ ] **AC-0012.** `status` and the journal report, for every task that ran or is open, whether it ran concurrently or on the floor and, for each fall to the floor, failed attempt, exact-source-only integration, and refusal, one reason code from a closed set that names each AC-0002 member, each AC-0017 check, each AC-0020 check, each AC-0067 check, and each refusal reason; no launcher-supplied text appears in either.

Launcher and attestation

- [ ] **AC-0013.** `start` pins a launcher only when `launcher_sha256` in the run's approval line, taken from the owner's own approval answer, equals the sha256 of a launcher file outside the work tree; an approval line that names a `launcher_sha256` with no such file pins nothing and records a `security-event.v1`, and one that names none pins nothing; neither refuses `start`.
- [ ] **AC-0014.** A run's launcher pin does not change for the life of the run.
- [ ] **AC-0015.** The supervisor hashes the run's private launcher copy immediately before each spawn and again after reading the containment line, and a mismatch at either point sends the task to the floor without a release and records a `security-event.v1`.
- [ ] **AC-0016.** The launcher starts in an empty private working directory, with no inherited file descriptor other than its standard input, output, and error, and with an environment of exactly `PATH=/usr/bin:/bin`, `LANG=C.UTF-8`, and `HOME` and `TMPDIR` set to supervisor-created private directories, whatever the invoking environment holds.
- [ ] **AC-0017.** A containment attestation with any one of these defects sends its task to the floor without a release: no `containment` line within 60 seconds of spawn; a line over 4 MiB; a schema violation; a binding that differs in run id, attempt id, grant id, nonce, or launcher sha256 from the one issued; a `read_enforcement` other than `allowlist` under `enforced-allowlist` or `trace` under `complete-trace`; under `enforced-allowlist`, a read allowlist that differs from the declared `Reads:`; `network.allowed` true; write roots other than exactly the attempt directory; roots broader than the grant; or a missing denial of any of the Git common directory, the shared refs, the run store, the work tree and every other worktree of the repository, every sibling attempt directory, or inter-process channels to sibling attempts.
- [ ] **AC-0018.** Each AC-0067 defect, and each binding defect AC-0017 lists, records a `security-event.v1` naming the defect code.
- [ ] **AC-0019.** The release token appears in no request, argument, environment variable, run-store file, journal line, `status` output, security event, or diagnostic record.
- [ ] **AC-0020.** A result integrates only while the product ref names its source commit, and otherwise meets the refusal outcome, when its access attestation has any one of these defects: a `mode` that differs from the containment attestation's `read_enforcement`; under `allowlist`, an attested read outside the declared `Reads:`; a path that is not a repository path; more than 20,000 entries in any list; a change the supervisor computes from the attempt directory that is absent from the attested writes; or `complete` false.
- [ ] **AC-0021.** A `report` for a `run-concurrent` request that asserts an attestation, read set, write set, or binding refuses `result-fact-refused`.
- [ ] **AC-0022.** `start` refuses `launcher-fixture-refused` for a launcher whose bytes carry the fixture marker, whatever environment variable, command-line flag, policy key, or file is set, unless the test corpus enables its in-process seam.
- [ ] **AC-0072.** Results integrate in floor order whatever environment variable, command-line flag, policy key, or file is set, unless the test corpus enables the completion-order seam in process.
- [ ] **AC-0023.** No file the Core pack installs or `make build-self` writes contains the fixture launcher's marker.
- [ ] **AC-0024.** A second `run-concurrent` invocation for a request already run refuses `request-consumed` and spawns nothing.
- [ ] **AC-0067.** An attempt whose access line is over 4 MiB, violates the schema, carries a binding other than the one issued or a release token other than the one sent, or is followed by a second `access` line or any other line fails without integrating, and its task runs its next attempt on the floor.
- [ ] **AC-0069.** No release is sent before the launcher's process-group id and its leader's start time are durable in the run store.
- [ ] **AC-0068.** An attempt with no `access` line within `attempt_timeout_seconds` (Policy keys) is cancelled, with the outcome AC-0052, AC-0053, and AC-0054 state for a confirmed and an unconfirmed end.
- [ ] **AC-0025.** After a `run-concurrent` invocation dies, the next supervisor verb records as integrated each attempt of that invocation whose commit the product ref carries, keeps each attempt with a held-result record held, and for every other attempt ends its launcher process group, confirms the end within 10 seconds, closes it as cancelled, and issues its task on the floor.
- [ ] **AC-0065.** Recovery never signals a process group when a process other than the recorded leader (by process id and start time) holds the leader's process id, and treats that attempt's end as confirmed; when no process holds that id but the group still has members, recovery signals the group and confirms its end; when neither exists, the end is confirmed.
- [ ] **AC-0066.** An end recovery cannot confirm within 10 seconds leaves that attempt's directory as residue and issues its task on the floor.

Reads, writes, and paths

- [ ] **AC-0026.** Under `enforced-allowlist`, a read the access attestation lists as denied does not enter the attested read set, and the result integrates when nothing else meets.
- [ ] **AC-0027.** Under `complete-trace`, an undeclared traced read that meets a path changed on the product ref since the result's source commit gives the refusal outcome, and an undeclared traced read that meets nothing integrates.
- [ ] **AC-0028.** In a repository whose `core.ignoreCase` is true, an attested read and a changed path that differ only in letter case meet.

Ingestion and held results

- [ ] **AC-0029.** The supervisor ingests an attempt directory only after confirming that the launcher's process group has ended and reading an access attestation whose `processes_ended` is true; an attestation without it fails the attempt.
- [ ] **AC-0030.** Ingestion records a symbolic link as a link with its target text and never reads through it.
- [ ] **AC-0031.** An attempt directory holding any one of a FIFO, a socket, a device node, an entry Git refuses as `.git` with both `core.protectHFS` and `core.protectNTFS` on, a hard-linked file, more than 100,000 paths, or more than 10 GiB of file bytes fails its attempt, and the task is reprojected.
- [ ] **AC-0070.** A symbolic link in an attempt directory whose target, resolved from the link's product path through every link the attempt directory holds as the checked-out tree would resolve it, leaves the work tree, names a path in the Git directory, a `.git` entry, a trusted file, or `delivery/`, or needs more than 40 link hops, fails its attempt.
- [ ] **AC-0073.** The bytes ingested for each regular file come from one no-follow open whose identity and size match the listing, so a file or parent directory replaced by a link between listing and reading fails its attempt.
- [ ] **AC-0071.** Ingestion checks AC-0031's caps from file metadata before writing any object, so a refused attempt leaves the object store unchanged, and the supervisor's memory per ingested file stays under 64 MiB whatever the file's size.
- [ ] **AC-0032.** Ingestion admits exactly the paths the floor's change-set computation admits for the same files, under the same ignore rules.
- [ ] **AC-0033.** Integration reads a held result only through its result identity, so a change to its attempt directory after ingestion leaves the integrated tree unchanged, and a change to its held-result record during a floor attempt refuses that floor attempt with `attempt-residue`.

Integration

- [ ] **AC-0034.** Admitted results integrate in floor order whatever order their attempts finish in.
- [ ] **AC-0035.** A result whose attested read or write set meets a path changed on the product ref between its source commit and the observed tip meets the refusal outcome.
- [ ] **AC-0036.** At the apply step, two results changing the same line of one file give the later one the refusal outcome.
- [ ] **AC-0037.** At the apply step, a `merge=union` in the checked-out `.gitattributes` does not resolve a conflict.
- [ ] **AC-0038.** A non-default `merge` attribute from `info/attributes` on any changed path gives the refusal outcome.
- [ ] **AC-0039.** A `merge.*` key present in repository configuration at the apply, including `merge.default=union` over a same-line change, gives the refusal outcome.
- [ ] **AC-0040.** `start` refuses `unsupported-git-config` for a repository whose configuration defines any `merge.<name>.driver`.
- [ ] **AC-0074.** A symbolic link in the merged tree whose target, resolved through every link that tree holds, meets AC-0070's conditions gives the refusal outcome before the product ref moves.
- [ ] **AC-0041.** An apply whose tree differs from the observed tip at a path outside the result's changed paths gives the refusal outcome.
- [ ] **AC-0042.** A compare-and-swap lost to a ref move gives the refusal outcome.
- [ ] **AC-0043.** A ref move injected between the intervening-change check and the compare-and-swap gives the refusal outcome.
- [ ] **AC-0044.** A kill at each integration write point, from object creation through working-tree materialization, leaves the product ref at its old or new commit, and the run then converges, through the next supervisor verb, to the uninterrupted run's tree.
- [ ] **AC-0045.** The next supervisor verb after a kill between the compare-and-swap and the integration record recognises the landed operation from its commit and creates no commit, no conflict record, and no reprojection.
- [ ] **AC-0046.** After each integration and before any floor issue, the working tree and index match the product ref.
- [ ] **AC-0047.** Every `integration-conflict.v1` holds repository paths and no file contents, passes the `integration-diagnostic` content profile, and, when more paths conflict than that profile's path cap, lists the first cap-many in byte order with the total count and a truncation flag while the refusal outcome still holds.
- [ ] **AC-0048.** Every successful concurrent integration records one `result-integration.v1` naming the source commit, observed tip, result commit, result tree, access-line sha256, and the apply algorithm with the Git version that ran it.

Isolation, blast radius, and plan changes

- [ ] **AC-0049.** Each concurrent attempt runs in its own attempt directory.
- [ ] **AC-0050.** A change to a trusted file, Git control state, or `delivery/` during a concurrent attempt refuses that attempt with `attempt-residue` while a sibling attempt is open.
- [ ] **AC-0051.** A refused, conflicting, or failed attempt reprojects only itself and each running sibling whose declared sets meet its own, and every other sibling's result integrates.
- [ ] **AC-0052.** A cancelled attempt's launcher process group is ended and its end confirmed within 10 seconds before the task is reprojected onto a fresh attempt directory.
- [ ] **AC-0053.** A cancelled attempt whose end is not confirmed sends its task to the floor.
- [ ] **AC-0054.** A cancelled attempt's result never integrates.
- [ ] **AC-0055.** A task reprojected `reprojection_bound` times (Policy keys) runs its next attempt on the floor.
- [ ] **AC-0056.** Every reprojection appears in the journal and in `status`.
- [ ] **AC-0057.** A controller replan or stub-fence revision is admitted only while no attempt is open; it discards every held result, reprojects those tasks without counting toward the bound, and is admitted once the open attempts end.
- [ ] **AC-0058.** No `run-gates`, `review-role`, or evidence receipt is issued while an attempt is open or a result is held, and each names only a commit the product ref has held.

Determinism and portability

- [ ] **AC-0059.** Under each concurrent mode, every completion-order permutation of each corpus schedule — three independent attempts; a read-after-write that reprojects; a floor task between held results; and a conflict that reprojects — is forced by fixture coordination, observed in the journal, and ends with the same product tree id and per-criterion acceptance outcomes as the sequential run over the same scripted attempt outputs and run id.
- [ ] **AC-0060.** With the test-only seam that integrates in completion order enabled, the read-after-write schedule's comparison fails.
- [ ] **AC-0061.** The corpus holds at most six schedules of at most three concurrent attempts each.
- [ ] **AC-0062.** Every corpus subprocess runs in an environment the corpus builds, with an isolated interpreter and a `PATH` on which no `pi` executable resolves, and the corpus asserts both before the first run.

Contracts

- [ ] **AC-0063.** Every `containment-attestation.v1`, `access-attestation.v1`, `launcher-message.v1`, `execution-result.v1`, `result-integration.v1`, `integration-conflict.v1`, `execution-request.v1`, and `task-contract.v1` record the corpus writes validates against its schema, and the corpus writes at least one of each.
- [ ] **AC-0064.** Every `containment-attestation.v1` and `task-contract.v1` fixture under `tests/roster/` at the revision this spec is approved at still validates.

## Accepted Risk

The owner, eugenelim, accepted each entry below on 2026-11-05 at spec approval.

- The launcher pin covers the launcher file's bytes only. An interpreter its
  `#!` line names, and anything that interpreter loads, are outside the pin;
  AC-0016's fixed `PATH` limits which interpreter a `/usr/bin/env` line can
  reach to the system directories.
- A deliberate worker running as the same operating-system user, on the floor
  between two hashes, can replace the run store's launcher copy and restore it
  before the second hash. This is the same-user premise
  `runtime-security-primitives.md` § 7 already accepts for the run store.
- A process an attempt starts outside the launcher's process group is covered
  only by the launcher's `processes_ended` assertion (AC-0029); the supervisor
  cannot observe it.

## Follow-ons

none

## Assumptions

none

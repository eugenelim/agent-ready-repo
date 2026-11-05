# Plan: Verified infrastructure parallelism

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/work-loop-result-integration.md` and `runtime-security-primitives.md` § 7; ADR-0156; analogous implementations `_supervisor_commit.py` (`build_commit`, `update_refs`, `_diagnose`) and `_containment.py` (`validate_attestation_dict`, `check_attestation_within_grant`, `launch_untrusted`); tests `test_supervisor_product_ref.py`, `test_supervisor_crash_corpus.py`, `test_containment_broker.py` (`_FixtureHost`), `tests/roster/test_execution_supervisor_records.py`; deviation: no code launches a worker from the supervisor today, so the launcher boundary has no precedent beyond `launch_untrusted`

> **Plan contract:** this is the implementation strategy. After approval, a
> change needs an **amendment** only when it touches the spec's protected
> sections (contract, scope and non-goals, durable outputs, agent rules, testing
> strategy, acceptance criteria, accepted risk) or its `Terminal Intent`. A change
> to tasks, tests, stubs, design, or approach needs none: the controller makes it
> as an in-envelope working-plan change while no execution attempt is open, and
> the run continues with every finished task still finished. Execution
> observations belong in `docs/specs/<feature>/notes/verification-ledger.md` (or
> the adopter's equivalent). A genuine error in a protected section follows the
> controlled-amendment path.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads. `Design`, `Approach`, `Grounding` and `Risks` are working
> material the controller corrects in place, before or after approval, while no
> attempt is open.

## Approach

T1, T2, and T5 are one pull request each; T3 and T4 share one; every pull
request except T6's ships one Core patch release, four in all. T1 ships
the contracts, the plan fields, and the policy keys with `concurrency` shipped
`sequential`, so nothing changes at runtime. T2 ships admission, the pinned
launcher, and attestation verification, but caps every `run-concurrent` batch
at one attempt: the whole supervisor-launched path runs and is verified end to
end while results still integrate by exact source, so no result can land out
of order before T3 exists. T3 lifts the cap and ships ordered integration
through the three-way apply. T4 ships blast radius, cancellation, and the
reprojection bound. T5 ships the permutation and conflict corpus and turns the
architecture pages to as-built. T6 closes the spec.

The riskiest part is T3: one lock, one tip read, and a compare-and-swap that
must stay correct under every completion order. T2's batch cap is the seam that
keeps T2 shippable without it.

## Constraints

- ADR-0156 D1–D7. Its 2.38 Git floor is raised to 2.41 for the concurrent path
  only, because `--merge-base` arrived in Git 2.40 and `--attr-source` in 2.41;
  older Git runs on the floor (D2's fail-closed rule). Owner decision, 2026-11-05.
- ADR-0154 D1–D6 stand for every floor result and every result without a
  complete access attestation.
- ADR-0144 D2: standard library only, inside `work-loop/scripts/`.
- ADR-0151: replans and stub-fence revisions wait for no open attempt.
- ADR-0005 D2 (opt-in), D5, D6 (backstop), D7 stand.
- Every Git call goes through `_supervisor_git.py`; the launcher spawn is the
  only new process call site and lives in `_supervisor_concurrency.py`.
- `packs/AGENTS.md`: shipped text cites no internal records; each `.apm/`
  change bumps Core one patch above `packs/core/pack.toml` at the merge base
  with freshly fetched `origin/main`.
- Do not edit `work-loop/scripts/` while a `WORK_SUPERVISOR_INTEGRATION=1` run
  is live in the same worktree.

## Construction tests

**Integration tests:**

- **VIP-X01 (AC-0031, AC-0032):** `test_supervisor_concurrency_permutations.py`
  drives each fixture schedule through the supervisor harness once under
  `sequential` and once per completion permutation under each concurrent mode,
  with the fixture launcher's scripted outputs held fixed, and compares the
  final product tree id and the `acceptance-verdict.v1` bytes. It runs under a
  `PATH` and `sys.path` checked for Pi before the first run. Owned by T5.
- **VIP-X02 (AC-0033):** `tests/roster/test_execution_supervisor_records.py`
  gains the three new schemas in its registry and validates every record the
  corpus writes. Owned by T1, extended by T5.

**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility | T1 | Schema-parity and record suites | Existing fixtures validate unchanged |
| Current architecture | T5 | Page diffs | No `STATUS: PLANNED` on a built element |
| Maintainer procedure | T1, T5 | `references/supervisor.md` and plan-template diffs | Grammar documented once |
| Product truth | PR 2 | Brief spec-map row | Row present |
| Release history | T1–T5 | Version bumps | One changelog fragment per Core PR |
| Verification record | T6 | Ledger | Every AC row checked |

Design facts below are owned by `work-loop-result-integration.md` (ordering,
apply, conflict, and record semantics) and `runtime-security-primitives.md` § 7
(launcher trust root, binding, release token); the rest is delivery residue.

## Design (LLD)

### Design decisions

- **The supervisor spawns the launcher and owns its pipes** (owner decision 1,
  2026-11-05). Verification is a property of the channel: an attestation is
  read only from the stdout of a process the supervisor itself started from
  the pinned bytes. Rejected: an HMAC key from `credbroker` (whoever holds the
  key can mint, and the value still crosses a worker-reachable channel);
  asymmetric signatures (new dependency). Rests on: the pinned launcher is
  owner-approved, and a contained attempt cannot reach the run store copy.
- **`run-concurrent` is a request kind run by a blocking supervisor verb.**
  `next` emits it naming the admitted tasks; the controller runs
  `work-supervisor.py run-concurrent --request <id>`, which spawns, verifies,
  waits, and integrates, then exits; `report` admits completion only. Rests
  on: the supervisor CLI is not a daemon, so only a blocking verb can hold the
  pipes for an attempt's life.
- **Attempt trees are plain directories, not Git worktrees.** The supervisor
  exports the source tree into a fresh directory under the run store's
  `attempts-tree/<attempt-id>/` with a temporary index and
  `checkout-index --prefix`, and later hashes the directory back into objects
  itself. D1 denies the Git common directory to the attempt, which a linked
  worktree would need.
- **Write set at integration** is the union of the attested write set and the
  change set the supervisor computes from the attempt tree; the supervisor's
  own computation is never narrowed by an attestation.
- **Attributes.** The apply runs `git --attr-source=<empty tree> merge-tree
  --write-tree --merge-base=<source> <tip> <result>` with no `-X` options.
  `check-attr --source=<empty tree> merge` runs over every changed path with
  the same pins first; any value other than `unspecified` refuses, which
  catches `info/attributes` and `core.attributesFile`.

Traces to AC-0007 to AC-0012, AC-0017 to AC-0022.

Owned by: T2, T3

### Data & schema

- `containment-attestation.v1` gains optional `binding` (`run_id`,
  `attempt_id`, `grant_id`, `nonce`, `launcher_sha256`), `write_roots`, and
  `denied` (array of the six tokens). Optional in the schema, because the
  version has readers and no producers; required by admission.
- `access-attestation.v1`: `schema_version`, `binding`, `release_token`,
  `mode` (`allowlist` | `trace`), `execution_result_sha256`, `complete`,
  `reads` (`{path, kind: file | missing | listing | walk}`), `writes`
  (`{path, kind: write | delete | rename-from | rename-to | mode}`),
  `denied_reads`. Caps: 100,000 entries per array, as the result-integration
  page's path cap.
- `result-integration.v1` and `integration-conflict.v1` follow the
  result-integration page § 4 identity columns; the conflict record carries
  `reason` (`meets` | `content` | `merge-attribute` | `outside-write-set` |
  `stale-authority` | `cas-lost`) and paths only.
- `task-contract.v1` gains `reads` and `writes` arrays; `execution-request.v1`
  gains the `run-concurrent` kind with a `tasks` array.
- Policy: `concurrency` (`sequential` | `enforced-allowlist` |
  `complete-trace`), `reprojection_bound` (integer 0–8, shipped 2).
- Run store: `launcher` (the pinned copy), `attempts-tree/`, `held/`
  (held results), `integrations/` (records), `integration.lock`.

Owned by: T1 (schemas, fields, policy), T2 (store entries), T3 (records)

### Interfaces & contracts

**Launcher protocol** — newline-delimited JSON over the launcher's stdin and
stdout, stderr discarded beyond a bounded tail:

1. Supervisor → launcher: `{"type": "attempt", "binding": …, "grant": …,
   "tree": <abs path>, "request": <execution-request.v1>}`.
2. Launcher → supervisor: `{"type": "containment", "attestation": …}`.
3. Supervisor → launcher: `{"type": "release", "token": <32 random bytes,
   hex>}` after verification, or `{"type": "abort"}`.
4. Launcher → supervisor: `{"type": "access", "attestation": …}` once the
   worker has exited, then the launcher exits 0.

Any other line, an oversized line (64 KiB), a timeout, or a non-zero exit ends
the attempt without a complete access attestation. Test seam: the launcher
path, plus the module global that admits the fixture marker. Traces to AC-0007
to AC-0012.

Owned by: T2

### State & control flow

- **Admission** runs in `next` against the derived state: the floor-order
  queue, each task's conditions (AC-0002's list), and the meet relation over
  declared sets. A batch is the longest prefix-respecting set of admissible
  tasks that pairwise do not meet; T2 caps it at one.
- **Integration** runs under `integration.lock` (cross-process, `_statelock`)
  in floor order: read the tip once; check the result's sets against
  `diff --name-status -M source..tip` with both rename ends; `check-attr`;
  merge-tree; write-set check on the merged tree; commit; compare-and-swap
  `HEAD` and the product ref in one transaction from the observed tip; record
  `result-integration.v1`; release. A held result waits in `held/` until every
  earlier floor-order task has integrated.
- A floor task issues only while no attempt is open; a held result is not open.

Owned by: T2 (admission), T3 (integration)

### Failure, edge cases & resilience

- Any refusal before release falls the task to the floor and journals the
  first failed condition.
- Any integration refusal leaves both refs unchanged, writes
  `integration-conflict.v1`, increments the task's reprojection count, and
  reprojects from the new tip; at `reprojection_bound` the task goes to the
  floor.
- Cancellation sends `abort`, then ends the launcher's process group and waits
  for confirmation with a bounded timeout; an unconfirmed end falls the task
  to the floor and leaves its attempt tree in place as residue.
- Kill points: before objects, before the compare-and-swap, after it, before
  the record. Replay finds the record by operation key.

Owned by: T3, T4

## Tasks

### T1: Contracts, plan fields, and policy keys ship with the floor unchanged

**Depends on:** none

**Tests:**
- AC-0034: the existing containment-attestation and task-contract fixtures in
  `tests/roster/test_containment_attestation_parity.py` and the record suite
  still validate.
- AC-0033: VIP-X02's registry loads the three new schemas, and one valid and
  one invalid sample per schema pass and fail.
- AC-0005: projector tests in `test_supervisor_projector.py` parse `Reads:`
  and `Writes:`, reject each malformed entry form into a floor-only marker,
  and change the revision when either field changes.
- AC-0001: a harness run under the shipped policy issues no `run-concurrent`
  request.

**Done when:** the four named suites pass, `make lint-ruff lint-mypy` is
green, and Core is one patch above the merge base.

### T2: Admission, the pinned launcher, and attestation verification run with batches of one

**Depends on:** T1

**Tests:**
- AC-0002, AC-0006: `test_supervisor_concurrency_admission.py` removes each
  condition singly and checks the floor issue and the `status` reason.
- AC-0007, AC-0011: `start` pins only an approved launcher, refuses a changed
  one at spawn, and refuses the fixture marker without the seam; a build
  check asserts the fixture is absent from `make build-self` output.
- AC-0008, AC-0009, AC-0010, AC-0012: `test_supervisor_launcher.py` scripts
  the fixture launcher to emit each defect and each missing release token.
- AC-0013, AC-0014, AC-0015: the meet relation's table test, and a scripted
  undeclared read in each mode.
- AC-0021: `test_supervisor_git.py` refuses a `merge.<name>.driver` at `start`.
- AC-0026: a batch-of-one attempt runs in a fresh, `.git`-free directory with
  its own manifest, and a trusted-file change refuses it.

**Done when:** the named suites pass, the existing product-ref and crash
suites pass unchanged, and Core is one patch above the merge base.

### T3: Ordered integration through the pinned three-way apply

**Depends on:** T2

**Tests:**
- AC-0003, AC-0004, AC-0016: `test_supervisor_integration.py` runs two- and
  three-task batches whose fixture attempts finish in reverse order.
- AC-0017, AC-0018, AC-0022: read-after-write, same-line, and
  outside-write-set fixtures assert both refs, the index, and `delivery/`
  unchanged, and the conflict record's reason.
- AC-0019, AC-0020: a worktree `.gitattributes` `merge=union`, an
  `info/attributes` driver, and a `core.attributesFile` setting.
- AC-0023: the crash corpus gains the four integration kill points and a
  racing ref move.
- AC-0024, AC-0025: records validate and the conflict record passes the
  `integration-diagnostic` profile at 1,000 and refuses at 1,001 paths.

**Done when:** the named suites pass and Core is one patch above the merge
base.

### T4: Blast radius, cancellation, and the reprojection bound

**Depends on:** T3

**Tests:**
- AC-0027: a three-attempt batch where one fails and one sibling meets it.
- AC-0028: a fixture launcher that ignores `abort`, one whose process group
  outlives the timeout, and a late result after cancellation.
- AC-0029, AC-0030: a task that conflicts `reprojection_bound` times, and a
  replan requested while a result is held.

**Done when:** the named suites pass and Core is one patch above the merge
base.

### T5: The permutation and conflict corpus, and the as-built pages

**Depends on:** T4

**Tests:**
- AC-0031, AC-0032: VIP-X01.
- AC-0033: VIP-X02 over the corpus records.

**Done when:** both suites pass; `work-loop-result-integration.md`,
`work-loop-execution-supervisor.md`, `runtime-security-primitives.md` § 7,
`loop-parallelism.md`, `references/supervisor.md`, and the new-spec plan
template describe the concurrent path and the known limit; and Core is one
patch above the merge base.

### T6: The spec closes

**Depends on:** T5

**Tests:**
- Every AC has a ledger row naming its test and run.

**Done when:** `notes/verification-ledger.md` checks every AC, the spec is
`Shipped`, this plan is `Done`, and the brief's spec map reports it.

## Rollout

- **Delivery:** four Core patch releases (T1, T2, T3 with T4, T5). `concurrency` ships
  `sequential` in every one, so adopters see no behaviour change beyond
  AC-0021's merge-driver refusal, which arrives with T2.
- **Reversal:** reinstall the prior Core release; a run in flight finishes on
  the release that started it.
- **Deployment sequencing:** contracts (T1) before any producer (T2); the
  batch cap (T2) before integration (T3).

## Risks

- AC-0021 refuses `start` in an adopter repository that configures a merge
  driver, on every run, not only concurrent ones. ADR-0156 D5 decides this.
- T3 and T4 touch `_supervisor_commit.py` and `_supervisor_attempt.py`, which
  sibling tasks also edit; each merge serializes with them through the planner.

## Changelog

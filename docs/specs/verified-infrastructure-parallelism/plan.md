# Plan: Verified infrastructure parallelism

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `docs/architecture/work-loop-result-integration.md` and `runtime-security-primitives.md` § 7; ADR-0156; analogous implementations `_supervisor_commit.py` (`build_commit`, `update_refs`, `_diagnose`) and `_containment.py` (`validate_attestation_dict`, `check_attestation_within_grant`, `launch_untrusted`); tests `test_supervisor_product_ref.py`, `test_supervisor_crash_corpus.py`, `test_containment_broker.py` (`_FixtureHost`), `tests/roster/test_execution_supervisor_records.py`; deviations: no code launches a worker from the supervisor today, so the launcher boundary has no precedent beyond `launch_untrusted`; concurrent attempts use plain directories rather than ADR-0005 D7's worktree (ADR-0160 D1)

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

One supervisor run carries T1 to T5 on one branch; after it is terminal the
controller cuts the commits into a stack of four pull requests (T1, T2, T3 with
T4, T5), each one Core patch release. T1 ships the
contracts, the plan fields, and the policy keys with `concurrency` shipped
`sequential`, so nothing changes at runtime. T2 ships admission, the pinned
launcher, attestation verification, and ingestion, but caps every
`run-concurrent` batch at one attempt: the whole supervisor-launched path runs
and is verified end to end while results still integrate by exact source, so no
result can land out of order before T3 exists. T3 lifts the cap and ships
ordered integration through the three-way apply. T4 ships blast radius,
cancellation, the reprojection bound, and plan-change and evidence ordering. T5
ships the permutation and conflict corpus and turns the architecture pages to
as-built. The spec's Closeout section closes it.

The riskiest part is T3: one lock, one tip read, and a compare-and-swap that
must stay correct under every completion order. T2's batch cap is the seam that
keeps T2 shippable without it.

## Constraints

- ADR-0156 D1–D7. Its 2.38 Git floor is raised to 2.41 for the concurrent path
  only, because `--merge-base` arrived in Git 2.40 and `--attr-source` in 2.41;
  older Git runs on the floor. ADR-0160 D2.
- ADR-0154 D1–D6 stand for every floor result and every result without a
  complete access attestation.
- ADR-0144 D2: standard library only, inside `work-loop/scripts/`.
- ADR-0151: replans and stub-fence revisions wait for no open attempt.
- ADR-0005 D2 (opt-in), D5, D6 (backstop) stand; ADR-0160 D1 supersedes D7
  for concurrent attempts only.
- Every Git call goes through `_supervisor_git.py`; the launcher spawn is the
  only new process call site and lives in `_supervisor_concurrency.py`.
- `packs/AGENTS.md`: shipped text cites no internal records; each `.apm/`
  change bumps Core one patch above `packs/core/pack.toml` at the merge base
  with freshly fetched `origin/main`.
- Pack tests may not read outside the pack (`lint-pack-test-boundary`); the
  build-output check (AC-0023) and record validation over `contracts/` live in
  `tests/roster/`.
- Git-backed supervisor suites run on pull requests only when the Gate
  A-supervisor run line in `catalogue-tooling-ci-gates.yml` names them (with
  `WORK_SUPERVISOR_INTEGRATION=1`); elsewhere they skip. Every task that adds
  such a suite registers it there, and its evidence is the CI log showing the
  suite ran with zero skips (a Closeout duty per PR). `tests/roster/` runs
  through a recorded `test-roster.yml` dispatch on each PR's branch.
- Do not edit `work-loop/scripts/` while a `WORK_SUPERVISOR_INTEGRATION=1` run
  is live in the same worktree.

## Construction tests

**Integration tests:**

- **VIP-X01 (AC-0059, AC-0060, AC-0061, AC-0062):**
  `test_supervisor_concurrency_permutations.py` drives each schedule through
  the supervisor harness with a pinned run id, once under `sequential` and
  once per forced completion permutation under each concurrent mode. The
  fixture launcher blocks each attempt's `access` line on a per-attempt gate
  the test releases in the chosen order, and the test asserts the journal's
  observed order before comparing the product tree id and each criterion's
  outcome in `acceptance-verdict.v1`. Owned by T5.
- **VIP-X02 (AC-0063):** `tests/roster/test_concurrency_records.py` runs the
  corpus schedules through the harness into a temporary store, collects every
  record, validates each against `contracts/delivery/` through the registry
  pattern of `tests/roster/test_execution_supervisor_records.py`, and fails
  when any of the eight kinds is missing. It is registered on the Gate
  A-supervisor run line, because the harness skips without
  `WORK_SUPERVISOR_INTEGRATION=1`, and T5 adds `jsonschema` and `referencing`
  to that job's install step. Owned by T5.

**Manual verification:** none.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Interface compatibility | T1 | Schema-parity and record suites | AC-0063, AC-0064 |
| Current architecture | T5 | Page diffs | No `STATUS: PLANNED` on a built element |
| Result acceptance | T5 | § 7 table row | `run-concurrent` row citing this spec |
| Maintainer procedure | T1, T5 | `references/supervisor.md` and plan-template diffs | Grammar and reason codes documented once |
| Product truth | Closeout | Brief spec-map row | Row reports `Shipped` |
| Release history | T1–T5 | Version bumps | One changelog fragment per Core PR |
| Verification record | Closeout | Ledger | Every AC row checked |

Design facts below are owned by `work-loop-result-integration.md` (ordering,
apply, conflict, ingestion, and record semantics) and, from T5,
`runtime-security-primitives.md` § 7 (launcher trust root, binding, release
token); until T5 lands, this section is their only home.

## Design (LLD)

### Design decisions

- **The supervisor spawns the launcher and owns its pipes** (owner decision 1,
  2026-11-05). Verification is a property of the channel: an attestation is
  read only from the stdout of a process the supervisor itself started from
  the pinned bytes. Rejected: an HMAC key from `credbroker` (whoever holds the
  key can mint, and the value still crosses a worker-reachable channel);
  asymmetric signatures (new dependency). Rests on: the launcher digest comes
  from the owner's own answer, and a contained attempt cannot reach the run
  store copy. Residual: an uncontained floor worker acting deliberately as the
  same user can replace the copy; the spec's Accepted Risk records this and
  the interpreter limit. The second hash catches a naive replacement only.
- **`run-concurrent` is a request kind run by a blocking supervisor verb.**
  `next` emits it naming the admitted tasks; the controller runs
  `work-supervisor.py run-concurrent --request <id>`, which spawns, verifies,
  waits, ingests, and integrates, then exits; `report` admits completion only.
  The verb marks the request consumed in the run store before its first spawn
  and records each launcher's process-group id. Rests on: the supervisor CLI
  is not a daemon, so only a blocking verb can hold the pipes.
- **Attempt directories are plain directories outside Git and the run store.**
  `tempfile.mkdtemp(prefix="agentbundle-attempt-")` (mode 0700) under the
  system temporary directory, populated from the source tree with a temporary
  index and `checkout-index --prefix`. A linked worktree would need the Git
  common directory D1 denies.
- **ADR-0156 D3's fingerprint binding.** The launcher cannot know the
  result's digest, so the access line carries the binding and release token,
  and the supervisor writes the attempt's `execution-result.v1` itself,
  carrying the ingested tree id and the access line's sha256; that record is
  the result D3 binds the attestation to, and `result-integration.v1` cites
  both.
- **Ingestion** uses a link-recording walk in `_confined_entries.py`
  (`list_confined_entries`, no-follow, descriptor-relative, built on the
  blessed helpers' error types) that returns
  regular files with sizes and links with target text. It checks AC-0031's
  caps and AC-0070's link targets from that listing before any object
  exists, resolving each target through the listing's own links with a
  40-hop bound. It then opens each file no-follow and descriptor-relative,
  checks the descriptor's identity and size against the listing, and streams
  it in 1 MiB chunks into `hash-object -w --no-filters --stdin` through a
  streaming-stdin form the hardened helper gains, and builds the tree
  with `update-index --index-info` under `-c core.protectHFS=true -c
  core.protectNTFS=true`. It then applies the floor's ignore rules to the
  attempt directory itself, not the live work tree.
- **Held results** are a run-store record (tree id, access-line sha256,
  attested sets, source commit) plus a ref
  `refs/agentbundle/delivery/<run>/<token>/held/<attempt>` naming the tree.
  Both enter every later attempt manifest, so a floor worker's change to
  either is residue.
- **Merge hazards.** The apply runs `git --attr-source=<empty tree> merge-tree
  --write-tree --merge-base=<source> <tip> <result>` with no `-X` options.
  Before it, `check-attr --source=<empty tree> merge` over every changed path
  refuses any value other than `unspecified` (this catches `info/attributes`;
  the helper already forces `core.attributesFile=/dev/null`), and any
  `merge.*` key in local or worktree configuration refuses. Admission treats a
  `merge.*` key as a missing condition.
- **Replay.** Each integration commit carries a `Supervisor-Operation:`
  trailer with the attempt id; a rerun that finds it on the tip's first-parent
  chain since the source commit records the landing and moves on.

Owned by: T2, T3

### Data & schema

- `containment-attestation.v1` gains optional `binding` (`run_id`,
  `attempt_id`, `grant_id`, `nonce`, `launcher_sha256`), `read_allowlist`,
  `write_roots`, and `denied` (array of `git-common-dir`, `shared-refs`,
  `run-store`, `work-trees`, `sibling-trees`, `sibling-ipc`). Optional in the
  schema, because the version has readers and no producers; required by
  admission.
- `access-attestation.v1`: `schema_version`, `binding`, `release_token`,
  `mode`, `complete`, `processes_ended`, `reads` (`{path, kind: file | missing | listing |
  walk}`), `writes` (`{path, kind: write | delete | rename-from | rename-to |
  mode}`), `denied_reads`; at most 20,000 entries per list, which fits the
  4 MiB line cap.
- `launcher-message.v1`: one envelope with `type` (`attempt` | `containment` |
  `release` | `abort` | `access`) and the matching body.
- `result-integration.v1` and `integration-conflict.v1` follow the
  result-integration page § 4; the conflict record carries `reason`
  (`meets` | `content` | `merge-attribute` | `merge-config` |
  `outside-changed-paths` | `stale-authority` | `cas-lost` |
  `incomplete-attestation`), `paths`, `path_count`, and `truncated`.
- `task-contract.v1` gains `reads` and `writes`; `execution-request.v1` gains
  the `run-concurrent` kind with a `tasks` array; the approval line gains
  `launcher_sha256`.
- Policy: the four keys, ranges, and shipped values the spec's Policy keys
  definition states. Protocol constants: containment line 60 s,
  cancellation confirmation 10 s, line cap 4 MiB; each is a module constant a
  test overrides through the clock seam.
- Run store: `launcher/` (the pinned copy, alone in an 0700 directory),
  `held/`, `integrations/`, `consumed/`, `integration.lock`.

Owned by: T1, T2, T3

### Interfaces & contracts

**Launcher protocol** (`launcher-message.v1`), newline-delimited JSON:

1. Supervisor → launcher: `attempt` with the binding, grant, attempt
   directory, and the `execution-request.v1`.
2. Launcher → supervisor: `containment` with the attestation.
3. Supervisor → launcher: `release` with the token, or `abort`.
4. Launcher → supervisor: one `access` with the attestation once the worker
   has exited, then end of stream and exit 0.

A launcher whose standard input closes before a `release` arrives starts no
worker and exits; `launcher-message.v1`'s description states this rule.

stderr is drained and discarded. Test seams: the launcher path, the clock,
the module global that admits the fixture marker, and the module global that
integrates in completion order (AC-0060). Both globals are set only by
assignment in test code; no environment variable, flag, policy key, or file
reads them, and AC-0023's scan also asserts no installed file assigns them.

Owned by: T2

### State & control flow

- **Admission** runs in `next`: the floor-order queue, AC-0002's pre-issue
  conditions, complete dependencies, and pairwise non-meeting declared sets.
  A batch is the floor-order-first set of admissible, pairwise non-meeting
  tasks up to `max_concurrent_attempts`; T2 caps it at one.
- **Integration** runs under `integration.lock` (cross-process, `_statelock`)
  in floor order: read the tip once; check attested sets against
  the rename-aware `diff --name-status -M` from source to tip, with both rename
  ends and each path's ancestors; `merge.*` and `check-attr`; merge-tree;
  changed-path check and link re-check (AC-0074) on the merged tree; commit with the trailer;
  compare-and-swap `HEAD` and the product ref from the observed tip; record
  `result-integration.v1`; materialize the working tree and index; release.
- A floor task issues only while no attempt is open; a held result is not open
  and its task is not complete.
- **Held results after the verb exits.** Every verb that integrates (`report`
  for a floor result, `run-concurrent`, and `next` before it derives) takes
  `integration.lock` and then integrates every held result that is next in
  floor order, so floor and concurrent results share one lock and one order.
- **Recovery** runs first in every verb: for each attempt a dead
  `run-concurrent` recorded, a commit trailer on the product ref means landed,
  a held-result record means held, and anything else is ended, confirmed, and
  cancelled.

Owned by: T2, T3

### Failure, edge cases & resilience

- Any refusal before release falls the task to the floor and journals its
  reason code.
- Any integration refusal leaves both refs unchanged, writes
  `integration-conflict.v1`, increments the task's reprojection count, and
  reprojects from the new tip; at `reprojection_bound` the task goes to the
  floor.
- Cancellation sends `abort`, then signals the launcher's process group and
  waits up to 10 seconds for confirmation; an unconfirmed end falls the task to
  the floor and leaves the attempt directory as residue.
- A dead `run-concurrent` invocation leaves `consumed/` and the recorded
  process-group ids; the next verb ends and confirms each group before
  anything else.
- Kill points: before objects, before the compare-and-swap, after it, before
  the record, during materialization.

Owned by: T3, T4

## Tasks

### T1: Contracts, plan fields, and policy keys ship with the floor unchanged

**Depends on:** none

**Tests:**
- AC-0064: the parity and record suites' existing fixtures validate.
- The registry loads the new schemas, one valid and one invalid sample per
  schema pass and fail, and policy validation rejects each new key's
  out-of-range values (for example `max_concurrent_attempts` 1 and 9).
- AC-0010, AC-0011: `test_supervisor_projector.py` parses `Reads:` and
  `Writes:`, marks each malformed form floor-only, and changes the revision on
  either field.

**Done when:** each new git-backed suite is on the Gate A-supervisor run line
and passes locally under `WORK_SUPERVISOR_INTEGRATION=1` with zero skips, the roster suites pass locally, `make lint-ruff lint-mypy` is green, and
Core is one patch above the previous task's release (T1: above `packs/core/pack.toml` at the run's base).

### T2: Admission, the pinned launcher, attestation verification, and ingestion run with batches of one

**Depends on:** T1

**Tests:**
- AC-0001, AC-0002, AC-0005, AC-0007:
  `test_supervisor_concurrency_admission.py` removes each condition singly and
  checks the floor issue; the shipped-policy run asserts no
  `run-concurrent` request now that the kind exists.
- AC-0013, AC-0014, AC-0015, AC-0016, AC-0022, AC-0024, AC-0025, AC-0065,
  AC-0066, AC-0069: `test_supervisor_launcher.py` over approval, copy,
  swap-before-spawn, planted-environment, fixture-marker (with each candidate
  variable set), second-invocation, and killed-verb fixtures (a kill before
  the process-group record is durable sends no release), including a
  recorded process-group id reused by an unrelated process, a dead leader with
  a live group member, and an end that never confirms on the injected clock.
- AC-0017, AC-0018, AC-0019, AC-0020, AC-0021, AC-0026, AC-0067: the fixture
  launcher
  emits each defect; the release-token test searches every output channel for
  the raw bytes, lowercase and uppercase hex, and standard and URL-safe
  base64, with a planted leak in one channel as the positive control.
- AC-0023: `tests/roster/` scans the Core install and `make build-self`
  output for the marker.
- AC-0029, AC-0030, AC-0031, AC-0032, AC-0070, AC-0071, AC-0073:
  `test_supervisor_ingestion.py` over link, FIFO, socket, `.git` and its
  `.GIT`, HFS-ignorable, `git~1`, and trailing-dot aliases, hard link,
  absolute, relative, chained, and directory links into `.git` and trusted
  files, the link-then-`..` pair (`a/b/y -> ../../z`, `a/b/x ->
  y/../delivery/approvals.jsonl`) for `delivery/`, a trusted file, and an
  out-of-tree target, a 41-hop chain, a swap-to-link between listing and
  read (AC-0073), path-cap and byte-cap (asserting no new loose objects), a 1 GiB
  sparse file under a memory probe, late-write, and floor-equivalence
  fixtures.
- AC-0040, AC-0049: `test_supervisor_git.py` refuses a merge driver at
  `start`; the attempt directory is fresh, outside every denied location.
- Admission's meet relation is unit-tested over every Meets row, including
  ancestors and `root/**` writes.

**Done when:** each new git-backed suite is on the Gate A-supervisor run line
and passes locally under `WORK_SUPERVISOR_INTEGRATION=1` with zero skips, the existing
product-ref and crash suites pass unchanged, and Core is one patch above T1's release.

### T3: Ordered integration through the pinned three-way apply

**Depends on:** T2

**Tests:**
- AC-0003, AC-0004, AC-0006, AC-0008, AC-0009, AC-0034:
  `test_supervisor_integration.py` runs two- and three-task batches whose
  attempts finish in reverse order, with a meeting pair, a non-meeting pair,
  and three admissible tasks under `max_concurrent_attempts` 2.
- AC-0027, AC-0028, AC-0035: read-after-write in both modes and a case alias
  on an `ignoreCase` repository.
- AC-0036, AC-0037, AC-0038, AC-0039, AC-0041: the apply step directly, over
  same-line, worktree `merge=union`, `info/attributes`, `merge.default=union`,
  and outside-changed-path fixtures.
- AC-0074: a floor-integrated `p/q -> ..` followed by a concurrent
  `p/x -> q/delivery/approvals.jsonl` refuses at the merged-tree link check.
- AC-0033, AC-0050: a floor attempt rewrites a held record and a held tree; a
  trusted-file change while a sibling is open; a held result integrates through
  the floor result's `report` in floor order; and AC-0025's held branch,
  retested here against a real held result from a killed `run-concurrent`.
- AC-0072: with each candidate variable set and no seam, results land in
  floor order.
- AC-0042, AC-0043, AC-0044, AC-0045, AC-0046: the crash corpus gains the five
  integration kill points, a racing ref move, and a move between check and
  compare-and-swap.
- AC-0047, AC-0048: records validate, and a conflict over the profile's path
  cap is written truncated.

**Done when:** each new git-backed suite is on the Gate A-supervisor run line
and passes locally under `WORK_SUPERVISOR_INTEGRATION=1` with zero skips and Core is one patch above the previous task's release.

### T4: Blast radius, cancellation, the reprojection bound, and plan-change ordering

**Depends on:** T3

**Tests:**
- AC-0051: a three-attempt batch where one fails and one sibling meets it.
- AC-0052, AC-0053, AC-0054: fixture launchers that ignore `abort`, outlive
  the confirmation window on the injected clock, and return late.
- AC-0055, AC-0056: a task that conflicts `reprojection_bound` times.
- AC-0057: a replan refused while an attempt is open, then admitted, with held
  results discarded and reprojected.
- AC-0058: `next` issues no gate, review, or evidence while a result is held.
- AC-0012: the expected reason set is written in the test from the spec's
  list (each AC-0002 member, AC-0017 check, AC-0020 check, AC-0067 check, and
  refusal reason); the test fails when a code is missing from the production
  table, when a table code has no exercised emission in `status` and the
  journal, and on any launcher-supplied byte in either output.
- AC-0068: an attempt silent past `attempt_timeout_seconds` on the injected
  clock is aborted and never integrates; with a confirmed end it reprojects,
  and with an end that never confirms its task goes to the floor.

**Done when:** each new git-backed suite is on the Gate A-supervisor run line
and passes locally under `WORK_SUPERVISOR_INTEGRATION=1` with zero skips and this task adds no Core bump (it ships in T3's release).

### T5: The permutation and conflict corpus, and the as-built pages

**Depends on:** T4

**Tests:**
- AC-0059, AC-0060, AC-0061, AC-0062: VIP-X01.
- AC-0063: VIP-X02 over the corpus records.

**Done when:** both suites are on the Gate A-supervisor run line and pass
locally under `WORK_SUPERVISOR_INTEGRATION=1` with zero skips; the pages the spec's
Durable Outputs name describe the concurrent path and the known limit; and
Core is one patch above T3's release.

## Rollout

- **Delivery:** four Core patch releases (T1, T2, T3 with T4, T5).
  `concurrency` ships `sequential` in every one, so adopters see no behaviour
  change beyond AC-0040's merge-driver refusal, which arrives with T2.
- **Reversal:** reinstall the prior Core release; a run in flight finishes on
  the release that started it.
- **Deployment sequencing:** contracts (T1) before any producer (T2); the
  batch cap (T2) before integration (T3).

## Risks

- AC-0040 refuses `start` in an adopter repository that configures a merge
  driver, on every run, not only concurrent ones. ADR-0156 D5 decides this.
- T2–T4 touch `_supervisor_commit.py` and `_supervisor_attempt.py`, which
  sibling tasks also edit; each merge serializes with them through the planner.
- Process groups and descriptor-relative walking are POSIX facilities, so
  Windows hosts always run on the floor (AC-0002's POSIX member).

## Changelog

- 2026-11-06: spec approved by eugenelim
- 2026-11-06: plan approved by eugenelim
- 2026-11-06: amendment approved by eugenelim (scope)

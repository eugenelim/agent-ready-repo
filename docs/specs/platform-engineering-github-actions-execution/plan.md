# Plan: Platform engineering GitHub Actions release execution

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done
- **Repository anchors:** `packs/release-engineering/.apm/skills/release-loop/scripts/release_admission.py` (confined reads, strict JSON, `SafeParser`, UTF-8 stream setup, `verify` and `check-stage` to load by file path); `packs/release-engineering/.apm/skills/release-loop/scripts/release_handoff.py` (bounded YAML-subset reader to mirror, not extend); `packs/release-engineering/tests/skills/release-loop/test_release_admission.py` and `test_release_stage_check.py` (pack-qualified loading, temp-root fixtures, subprocess and socket prohibition seam); `packs/release-engineering/.apm/skills/release-loop/assets/image-only-ci-caller/` (candidate template and example CI workflow). Uncertainty: whether `github_release.py` loads `release_admission.py` by file path or keeps its own confinement helpers is implementation-discovered; no script goes on `sys.path`.

> **Plan contract:** Tests, Touches and Done when are completion fields.
> Design, Approach, Grounding and Risks are working material. Execution evidence
> belongs in `notes/verification-ledger.md`, not in this plan.

## Approach

One stdlib script carries every mechanical check so each control and refusal is testable without prose: the workflow reader and shared input handling first, then `readiness`, `bind`, and `reconcile` with `summary`. The example workflows and controls come next and are proved against `readiness` itself. Procedure prose, then offline journeys, then packaging. The live fixture runs last, on the finished templates, and are controller work because a sandboxed implementer has no network. Script tasks are TDD and DEEP; prose is content-pinned; journeys are integration; the live runs are manual QA with recorded run IDs.

## Constraints

- [ADR-0071](../../adr/0071-pack-runtime-export-boundary-and-test-placement.md) governs runtime exports, test placement and skill-local evals; [ADR-0101](../../adr/0101-pack-test-isolation-by-default-with-declared-compatibility-classes.md) governs isolated pytest processes.
- No dependency, no cross-pack import, no change to core, hooks, adopter workflow policy or the `pack.toml` dependency tables. `.apm/` content cites no internal records.
- The script runs no process and opens no network connection.
- No real cloud account number, role identifier, bucket name or the fixture's audit version ids in any committed file; synthetic `123456789012` and `example-*` names in tests and assets.
- Known CI registration traps: `pytest tests/roster/`, `tools/lint-pack-test-boundary.py`, a changelog fragment, version parity in `pack.toml` and `.claude-plugin/plugin.json`, roster pins on pack version, and main's sharded catalogue-test job list (`build-check.yml`, `tools/test-build-check-workflow.py`, `tools/fixtures/build-check-good.yml`, `tools/lint-ci-parity.py`).

## Construction tests

**Integration tests:** `test_github_release_journeys.py` builds an isolated root from the image-only caller fixture, runs collection, admission, synthetic pre-deploy reviews and stage checks through the real scripts, then `readiness`, `bind`, `reconcile` and `summary` over synthetic snapshot, context, approvals, observation and audit read-back files.

**Manual verification:** the live fixture runs of T9, recorded in the verification ledger with run IDs, step outcomes, refusal codes and placeholders for cloud identifiers.

## Durable-output map

| Durable output | Tasks | Implementation evidence | Closeout evidence |
| --- | --- | --- | --- |
| Script | T1 to T4 | Pack suite results | Spec contract and files resolve |
| Example workflows and controls | T5 | Readiness over the example, content pins | Assets resolve; no real identifiers |
| Reference, loop and lead procedure | T6 | Content pins | One reference owns the mapping |
| Offline journeys | T7 | Isolated-root runs | Ledger transcript |
| Guides, evals, version, history, CI registration | T8 | Link checks, parity, fragment, shard list | Destinations current |
| Live evidence | T9 | Run IDs and outcomes | Ledger entries |

## Design (LLD)

### Interfaces & contracts

Owned by: T1 to T4

Traces to AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018, AC-0019, AC-0020, AC-0021. `github_release.py` subcommands `readiness`, `bind` (with `--check`), `reconcile`, `summary`. Same shape as `release_admission.py`: `SafeParser`, UTF-8 setup before the first print, one JSON object on stdout, `main(argv)` returning 0, 1 or 2. `bind` and the `verify-admission` step reuse the admission script's `verify` by loading it from the same skill folder by file path.

### Data & schema

Owned by: T1 to T4

The controls file, settings snapshot, binding record, observation, ops, audit receipt and summary are internal JSON; the guide documents fields and codes without promising stability. The snapshot is a JSON object of raw API responses keyed by source; only listed fields are read.

### Workflow templates

Owned by: T5

The prepare workflow: `workflow_dispatch`, `permissions: contents: read, actions: read`, GitHub-hosted runner, checkout pinned by SHA, write the candidate from the release fixture template, collect and admit, upload one artifact. The deploy workflow: `workflow_dispatch` with `prepare_run_id`, `admission_sha256`, `pre_deploy_reviews`; one job that calls `./.github/workflows/release-deploy-job.yml` with those inputs and named secrets. The deploy-job workflow: `workflow_call`; one job with `environment`, `concurrency` (`cancel-in-progress: false`), `permissions: contents: read, actions: read, id-token: write`, `timeout-minutes`, GitHub-hosted runner; steps `capture` (run context, attempt, approvals, environment, prepare run, artifact listing and archive, all via `GITHUB_TOKEN`), `verify-admission`, `bind`, `credentials` (OIDC; role from a secret), `budget` (list every decision and ops version, observe effects, run `budget`), `audit` (write the decision record's bytes with a SHA-256 checksum, keep the receipt and head, list the decision prefix, capture live store and target settings), `recheck`, `mutate-deploy` (write the payload with its checksum, the marker and the expected owner), `observe`, `teardown` (guarded `if`), `summary` (guarded; read back by version id), `ops` final (guarded `always() && steps.audit.outcome == 'success'`; terminal outcome). Every input and API value reaches `run:` through `env`; no `run:` text holds `${{`.

### Cloud fixture setup

Owned by: T9

Outside every repository of this catalogue: a GitHub OIDC provider; a role whose trust is the customized subject for the fixture's environment and deploy-job workflow, with inline policies only, including read-only inspection of itself; a target bucket whose policy denies writes to every principal but the role and whose lifecycle expires objects within the window; an audit bucket with object lock in compliance mode, one-day default retention, no lifecycle rule on the decision or ops prefixes, and a bucket policy that denies writes under the prefixes to every principal but the role and denies every erasure action to everyone. The repository's OIDC subject template is set to `repo`, `context`, `job_workflow_ref`. Role ARN, account number and bucket names reach the fixture as environment secrets.

## Tasks

### T1: Script skeleton, shared input handling and the bounded workflow reader

**Depends on:** none

**Verification mode:** TDD. Review shape: DEEP, confined to input handling and the reader.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/github_release.py`, `packs/release-engineering/tests/skills/release-loop/test_github_release_inputs.py`

**Tests:**
- Confinement matrix for a file argument of every subcommand: absolute, drive letter, backslash, `.` and `..`, symlink, hard link, FIFO, oversized, swapped between open and read; no content or failed path echoed (AC-0017).
- Strict JSON matrix: duplicate keys, unknown fields in each closed shape, non-finite numbers, nesting past 32, over 1,048,576 bytes; the archive is hashed, never extracted (AC-0018).
- Subprocess and socket prohibition seam over every subcommand's cases (AC-0019); UTF-8, one JSON object, suppressed argv text, exit codes (AC-0021).
- Reader: accepted constructs parse to the expected structure; each refused construct gives `unparsed` (AC-0007).

**Done when:** `python3 -m pytest packs/release-engineering/tests/skills/release-loop/test_github_release_inputs.py -q` passes.

### T2: Readiness evaluates every control row

**Depends on:** T1

**Verification mode:** TDD. Review shape: DEEP, confined to `readiness`.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/github_release.py`, `packs/release-engineering/tests/skills/release-loop/test_github_release_readiness.py`

**Tests:**
- A synthetic fixture meeting every row is `ready` (AC-0001); one-change mutations for every code in every row (AC-0002, AC-0003, AC-0004, AC-0005, AC-0006), including both subject forms and the audit-erasure actions.
- Missing snapshot sources map to exactly the controls that read them; `unparsed` deploy workflows make the five workflow controls `unverified` (AC-0007).
- Waiver text and controls-named snapshot fields change nothing (AC-0009); directive text in snapshot and workflow changes nothing (AC-0020).

**Done when:** the suite passes and each code's case fails when its check is removed.

### T3: Bind ties the admission, prepare run, workflow, run and approval together

**Depends on:** T1

**Verification mode:** TDD. Review shape: DEEP, confined to `bind`.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/github_release.py`, `packs/release-engineering/tests/skills/release-loop/test_github_release_bind.py`

**Tests:**
- A valid binding equals its inputs (AC-0010); each refusal of AC-0011 and AC-0012 writes nothing; protection, approval-missing, unbound (other digest, prefix), self (triggering actor, agent) and rejected cases (AC-0013).
- An approval recorded for another run does not bind this run (AC-0023); directive text in an approval comment changes nothing except the digest token (AC-0020).

**Done when:** the suite passes and each refusal case fails when its check is removed.

### T4: Budget, recheck, reconcile and summary

**Depends on:** T3

**Verification mode:** TDD. Review shape: DEEP, confined to `budget`, `recheck`, `reconcile` and `summary`.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/github_release.py`, `packs/release-engineering/tests/skills/release-loop/test_github_release_reconcile.py`, `packs/release-engineering/tests/skills/release-loop/test_github_release_bind.py` (the binding's `effects` field), `packs/release-engineering/tests/skills/release-loop/test_github_release_inputs.py` (stub list)

**Tests:**
- `recheck` current and each refusal, including the window boundary for counted decisions, noncurrent versions, a truncated listing, a forged agent snapshot against a failing live snapshot, and a binding copied from another run (AC-0014, AC-0023, AC-0044).
- `budget` refusals and pass cases, before any write (AC-0043).
- `reconcile` outcomes including `run-not-terminal` and the execution limit (AC-0015).
- `summary` `audited` and each `audit-unconfirmed` cause, forged read-backs, summary fields and no approval field (AC-0016, AC-0022); directive text in observation, listing and ops changes nothing (AC-0020).

**Done when:** the suite passes and each refusal case fails when its check is removed.

### T5: Example workflows and controls pass readiness

**Depends on:** T2, T3, T4

**Verification mode:** TDD for the readiness-over-example pins; goal-based for asset content.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/assets/github-actions/` (`README.md`, `release-prepare.example.yml`, `release-deploy.example.yml`, `release-deploy-job.example.yml`, `controls.example.json`), `packs/release-engineering/tests/skills/release-loop/test_github_release_assets.py`

**Tests:**
- Both example workflows parse unchanged (AC-0008); the deploy workflow with the example controls and a synthetic snapshot meeting every snapshot row is `ready`, with step order, pins, input bound and `env`-only values (AC-0024).
- The prepare workflow holds no `id-token: write`, environment or mutation step and uploads one artifact (AC-0025); no twelve-digit account number, ARN or real bucket name in any asset, and the role and stores come from `secrets.` (AC-0026).

**Done when:** the suite passes and `readiness` over the example prints `ready`.

### T6: Reference, loop and lead procedure

**Depends on:** T5

**Verification mode:** goal-based content pins.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/references/github-actions.md`, `packs/release-engineering/.apm/skills/release-loop/SKILL.md`, `packs/release-engineering/.apm/agents/release-lead.md`, `packs/release-engineering/tests/skills/release-loop/test_github_release_procedure.py`

**Tests:**
- The reference owns the mapping and carries every capture command, setup step and statement of AC-0027.
- Loop routing and blocked-mutation rule (AC-0028); approval, re-run, agent and reconcile rules and audited-summary resume (AC-0029); lead steps and no-authority rule (AC-0030); sidecars, earlier-path runs, completion record (AC-0031).

**Done when:** the pins pass.

### T7: Offline journeys without core or Terraform

**Depends on:** T5, T6

**Verification mode:** integration.

**Touches:** `packs/release-engineering/tests/skills/release-loop/test_github_release_journeys.py`

**Tests:**
- Application-only happy path through final with cleanup `torn-down` (AC-0032).
- Each failure of AC-0033 stops before the next step.

**Done when:** the suite passes in an isolated root with no other pack present.

### T8: Guides, evals, version, history and CI registration

**Depends on:** T7

**Verification mode:** goal-based.

**Touches:** `packs/release-engineering/pack.toml`, `packs/release-engineering/.claude-plugin/plugin.json`, `packs/release-engineering/.apm/skills/release-loop/evals/evals.json`, `guides/release-engineering/how-to/run-a-release-with-github-actions.md`, `guides/release-engineering/reference/release-admission.md`, `guides/release-engineering/README.md`, the changelog fragment directory, `.github/workflows/build-check.yml`, `tools/test-build-check-workflow.py`, `tools/fixtures/build-check-good.yml`, `tools/lint-ci-parity.py`, generated projections and journey pages the self-host writes.

**Tests:**
- Version parity 0.4.0 with unchanged dependency tables and a validated fragment (AC-0039); eval cases for each listed behaviour (AC-0040); guide link check and content (AC-0041).
- `make build-self` zero diff, lint pair, precheck, `pytest tests/roster/`, boundary lint and the build-check shard list including the new suites (AC-0042).

**Done when:** every command in AC-0042 exits 0.

### T9: Live fixture runs

**Depends on:** T8

**Verification mode:** visual / manual QA against the real GitHub.com fixture repository and cloud sandbox. Controller-executed: the sandboxed implementer has no network.

**Touches:** `docs/specs/platform-engineering-github-actions-execution/notes/verification-ledger.md` (a controller commit between attempts, because the spec folder is worker-protected)

**Tests:**
- Happy path (AC-0034); zero-mutation runs (AC-0035); self-review, agent-token refusal, second-workflow credential refusal, second-principal write refusal and two queued dispatches (AC-0036); cancellation after mutation then reconcile (AC-0037); audit object immutability and ordering (AC-0038).

**Done when:** the ledger records every run id, outcome and code above with cloud identifiers as placeholders, and `git grep` finds no real account number or bucket name in the branch.

### T10: Budget and recheck refuse a listing with a missing page

**Depends on:** T9

**Verification mode:** TDD. Review shape: DEEP, confined to listing validation.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/github_release.py`, `packs/release-engineering/tests/skills/release-loop/test_github_release_reconcile.py`

**Tests:**
- A page stream whose continuation markers skip a page (a truncated page's `NextKeyMarker` and `NextVersionIdMarker` differ from the next page's `KeyMarker` and `VersionIdMarker`), a stream ending on a truncated page, and a missing first page each give `listing-incomplete` from `budget` and `recheck`; a contiguous multi-page stream and the job's combined single page pass (AC-0043, AC-0014).

**Done when:** the suite passes and the skipped-page case fails when the continuity check is removed.

### T11: Complete the live evidence

**Depends on:** T10

**Verification mode:** visual / manual QA against the fixture. Controller-executed.

**Touches:** `docs/specs/platform-engineering-github-actions-execution/notes/verification-ledger.md` (a controller commit between attempts)

**Tests:**
- The ledger names each live run's prepare run id (AC-0034).
- For each zero-mutation run, CloudTrail shows no deploy-role session for that run id, and the ledger lists its skipped steps (AC-0035).
- A run cancelled while a fixture-only pause holds the `observe` step after `mutate-object` succeeded is reconciled from its uploaded records and a fresh observation, with outcome and teardown state recorded (AC-0037).
- IAM policy simulation of the deploy role with the audit bucket policy denies deleting and altering a decision version, and a run's target write time from its uploaded observation is later than its decision version's write time (AC-0038).

**Done when:** the ledger records each item above with cloud identifiers as placeholders.

### T12: Summary accepts the specified inputs without controls

**Depends on:** T11

**Verification mode:** TDD. Review shape: bounded, confined to `summary`.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/github_release.py`, `packs/release-engineering/tests/skills/release-loop/test_github_release_reconcile.py`

**Tests:**
- `summary` with exactly the spec's inputs and no `--controls` returns `audited` for a matching read-back and head and each `audit-unconfirmed` cause of AC-0016; with `--controls`, a receipt key other than this binding's decision key returns `audit-unconfirmed` (AC-0016).

**Done when:** the suite passes.

### T13: Live re-runs with effect observations and a deploy-role erasure probe

**Depends on:** T12

**Verification mode:** visual / manual QA against the fixture. Controller-executed.

**Touches:** `docs/specs/platform-engineering-github-actions-execution/notes/verification-ledger.md` (a controller commit between attempts)

**Tests:**
- Each refusal case of AC-0035 is re-run, and the ledger records its step results and a post-run observation of every declared effect (AC-0035).
- A fixture-only step running as the deploy role tries to delete its own decision version and to shorten its retention, and both are refused; the version is then read back unchanged with its retention (AC-0038).

**Done when:** the ledger records each run, observation and refusal with cloud identifiers as placeholders.

### T14: Review repairs: reconcile job evidence, prerequisite guards, paged listings, role paths, guide paths

**Depends on:** T13

**Verification mode:** TDD for the script and template pins; goal-based for the guide.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/github_release.py`, `packs/release-engineering/.apm/skills/release-loop/assets/github-actions/release-deploy-job.example.yml`, `packs/release-engineering/.apm/skills/release-loop/references/github-actions.md`, `guides/release-engineering/reference/release-admission.md`, `packs/release-engineering/tests/skills/release-loop/test_github_release_reconcile.py`, `packs/release-engineering/tests/skills/release-loop/test_github_release_readiness.py`, `packs/release-engineering/tests/skills/release-loop/test_github_release_assets.py`

**Tests:**
- `reconcile` grants `retry-allowed` without terminal ops only when the jobs response is complete (`total_count` equals the jobs listed), every job belongs to the binding's run id and attempt, and the deploy job lists every declared `mutate-` step as not started; a jobs response for another run or attempt, a truncated response or one missing the mutate step gives `pause` (AC-0015).
- `readiness` reports `mutation-continues-on-error` when any prerequisite step (`verify-admission`, `bind`, `credentials`, `budget`, `audit`, `recheck`) or `mutate-` step sets `continue-on-error`, and `binding-order` when a `mutate-` step has an `if` that can run after a failed prerequisite (`always()`, `failure()`, `cancelled()`); the example passes (AC-0002, AC-0009).
- The example deploy-job saves the native S3 pages (each at most 1,000 entries, chained by markers) instead of one combined page, and `budget`, `recheck` and `reconcile` accept 2,500 versions across three pages (AC-0014, AC-0043).
- `recheck` accepts a role ARN with a path whose final name equals `cloud.role_name`, consistent with readiness (AC-0014).
- The reference guide's readiness command reads the snapshot file the capture recipe writes (AC-0041).

**Done when:** the suites pass and each new refusal fails when its check is removed.

### T15: Record the deploy-role overwrite probe and the updated-template runs

**Depends on:** T14

**Verification mode:** visual / manual QA against the fixture. Controller-executed.

**Touches:** `docs/specs/platform-engineering-github-actions-execution/notes/verification-ledger.md` (a controller commit between attempts)

**Tests:**
- The ledger records a deploy-role overwrite attempt on its own decision version, which only adds a new version, and a by-id read-back of the recorded version with unchanged bytes, checksum, lock mode and retention (AC-0038).
- The ledger records the live runs of the template after T14 (AC-0034).

**Done when:** the ledger records both with cloud identifiers as placeholders.

### T16: Review round 2 repairs: empty pages, required history streams, step conditions, secret-rendered controls

**Depends on:** T15

**Verification mode:** TDD for the script and template pins; goal-based for prose.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/github_release.py`, `packs/release-engineering/.apm/skills/release-loop/assets/github-actions/release-deploy-job.example.yml`, `packs/release-engineering/.apm/skills/release-loop/assets/github-actions/controls.example.json`, `packs/release-engineering/.apm/skills/release-loop/assets/github-actions/README.md`, `packs/release-engineering/.apm/skills/release-loop/references/github-actions.md`, `guides/release-engineering/reference/release-admission.md`, `packs/release-engineering/tests/skills/release-loop/test_github_release_reconcile.py`, `packs/release-engineering/tests/skills/release-loop/test_github_release_readiness.py`, `packs/release-engineering/tests/skills/release-loop/test_github_release_assets.py`, `packs/release-engineering/tests/skills/release-loop/test_github_release_journeys.py`

**Tests:**
- A native page without `Versions` or `DeleteMarkers` (an empty prefix) is read as empty, and a first execution with no history passes `budget` (AC-0043).
- `budget`, `recheck` and `reconcile` refuse `listing-incomplete` unless the listing holds a complete stream whose pages carry `Prefix` equal to the decision key prefix for the environment and another for the ops key prefix (AC-0014, AC-0043).
- `readiness` reports `binding-order` when a prerequisite step or a `mutate-` step has any `if` (AC-0002, AC-0009).
- The example deploy-job renders controls from a committed template whose bucket and role names are placeholders filled from the named environment secrets; the shipped controls example holds only placeholders; the capture recipe renders the same way (AC-0024, AC-0026, AC-0027).

**Done when:** the suites pass and each new refusal fails when its check is removed.

### T17: Review round 4 repairs: list-form triggers and allow-free captured bucket policies

**Depends on:** T16

**Verification mode:** TDD.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/github_release.py`, `packs/release-engineering/.apm/skills/release-loop/references/github-actions.md`, `packs/release-engineering/tests/skills/release-loop/test_github_release_readiness.py`

**Tests:**
- `on: [workflow_dispatch]` and `on: workflow_dispatch` are read as the same trigger set as the mapping form for the prepare and deploy workflows, and `[workflow_call]` for the deploy-job workflow; a list holding any other event is `untrusted-trigger` (AC-0002).
- A captured target or audit bucket policy holding any `Allow` statement makes `credentials` `missing` with `permissions-exceed-allowlist` and `isolation` `missing` with `role-reaches-beyond-effects`; the reference states that grants in other buckets' policies are outside what readiness can capture (AC-0005, AC-0027).

**Done when:** the suite passes and each new refusal fails when its check is removed.

### T18: Recheck binds the full role ARN

**Depends on:** T17

**Verification mode:** TDD.

**Touches:** `packs/release-engineering/.apm/skills/release-loop/scripts/github_release.py`, `packs/release-engineering/tests/skills/release-loop/test_github_release_reconcile.py`

**Tests:**
- `recheck` returns `cloud-identity-mismatch` when the expected role ARN, the live snapshot's role ARN and the caller's assumed-role identity do not all name the same account, IAM path and role name; a role with a path passes when all three agree (AC-0014).

**Done when:** the suite passes and the path-mismatch case fails when the check is removed.

## Risks

- GitHub's approval response has no timestamp or attempt; the digest comment is the binding and re-runs are refused.
- Approvals happen in the GitHub UI and need the owner present for T9.
- The controller host holds owner-level credentials; independence is proven for the agent app identity only and recorded as a residual.

## Changelog

- 2026-11-15: drafted.
- 2026-11-15: spec approved by eugenelim (scope)
- 2026-11-15: plan approved by eugenelim (build strategy)
- 2026-11-15: amendment drafted: the binding record carries each effect's admitted payload digest so `reconcile` can classify `applied` from its own inputs.
- 2026-11-15: amendment approved by eugenelim (scope)
- 2026-11-15: amendment approved by eugenelim (build strategy)
- 2026-11-16: replan after run-gates: T10 fixes listing continuity; T11 completes live evidence for AC-0034, AC-0035, AC-0037 and AC-0038.
- 2026-11-16: replan after the second run-gates: T12 makes summary's controls input optional; T13 re-runs the live refusal cases with observations and probes deploy-role erasure.
- 2026-11-16: replan after review round 1: T14 repairs the supported findings.
- 2026-11-21: replan: T15 records the deploy-role overwrite probe and the updated-template runs.
- 2026-11-21: replan after review round 2: T16 repairs the supported findings.
- 2026-11-21: amendment drafted: the candidate-binding row states that prerequisite and mutate- steps carry no continue-on-error and no if, as enforced.
- 2026-11-21: replan after review round 4: T17 repairs the supported findings.
- 2026-11-21: replan after run-gates: T18 binds the full role ARN in recheck.
- 2026-11-22: run terminal; status Shipped and Done.

# Structured review boundary verification ledger

## Preflight — 2026-10-07

- Branch: `feat/structured-review-boundary-slice2`, cut from shipped Slice 1
  squash commit `9d39eae8b`. Base freshness returned `ok` against `origin/main`.
- Workspace canonical preflight: `structured-review-boundary` is ready in
  `ini-002`, with no blocking needs or findings.
- Both prior state files were absent. Engine and cohort initialized in code
  mode with run ID `accb0133-8ca5-414a-a831-41a1bd9f35c4`.
- `spec-ready` entered `SPEC-PLAN-REVIEW`, transition sequence 1.
  `plan check-current` returned `plan_review_status: pending`, the expected
  pre-EXECUTE review signal. No old approval is inferred.
- [Slice 1 reconciliation](slice-1-reconciliation.md) covers append/replay,
  stable denial codes, writer profiles, shared validators, audit pairing, and
  the compatibility facade. Tasks were regenerated within the accepted scope.
- `git diff --check`: passed.
- `lint-spec-status.py --root .`: passed, one changed spec among 534; 181
  repository-wide warnings are reported separately from hard violations.
- No production code or tests have been written. New-test mutation proof is
  required during implementation and has not yet been earned.

## Scope and verification

The implementation touches only review-owned schemas, sibling work-loop
services and compatible callers, pack tests and evals, source guidance and its
generated projections, declared durable-output pages, paired Core version
files, release history, and Slice 2 lifecycle records. T1 resolves exact new
review module names before implementation.

The spec truth tables, VI-1001–VI-1019, mutation checks, synthetic producer,
compatibility crash/replay corpus, clean-environment runtime fence, targeted
pack suites, and repository gates demonstrate completion. Run the complete
work-loop suite in the background after implementation; run other large pack
suites per directory to avoid duplicate pytest basenames. External workflow
dispatches remain unauthorized.

Unchanged boundaries: Slice 1 schemas and public single-record APIs,
`file_safety.py`, `packages/agentbundle/`, legacy plan lock, task/cohort writer,
procedure authority, terminal intent, runtime provider, and Slices 3/4 behavior.
Review cutover and risk acceptance retain separate owner authority.

Expected review shape is DEEP. Dependency-ordered boundaries are T1 contracts,
T2 selection, T3 persistence/atomic batch support, T4 assessment/evidence bridge,
T5 disposition/closure, T6 compatibility, and T7 authorized policy cleanup and
durable outputs. Each task has its own verification; final integrated review
must also cover the complete synthetic-reviewer journey. Inspect the actual
behavior/test diff volume before the final handoff.

## Anchor-test sweep

The bounded sweep found the schema inventory at
`tests/roster/test_delivery_contract_bundle.py`, schema-validator parity at
`tests/roster/test_evidence_store_schema_parity.py`, and safety-registry matrix
agreement at `tests/roster/test_content_safety_boundary_matrix.py`.
Update the owning inventory or add review-owned coverage when new schemas and
boundaries land, without weakening existing Slice 1 checks.

The pack tests at `packs/core/tests/skills/work-loop/test_content_safety.py`
pin the Slice 1 writer registry. `test_compat_facade.py` pins one receipt/frame
per legacy transition. Those existing behaviors remain regression obligations.
The golden CLI fixtures also pin legacy engine output. Repeat the focused
anchor sweep for files selected by T1 and for every review repair.

## Resolve-versus-surface disposition record

This record tracks independently adjudicated findings and their repairs.
Persist and validate every raw report, independently adjudicate findings, and
record each sustained finding's disposition here before repair. Unacted Nits
retain citations; an indeterminate assessment or protected-policy decision
routes to the named owner. The owner requested no review-round cap.

### Adjudicator dispatch surface

The first secure-design raw report was persisted beneath the ignored session
review root and validated: 1,320 bytes,
`sha256:b51205d449c906a1b35fa9b5d0de5f7a2ebdf9ee4d655c300c91da5aae15b796`.
The strict raw classifier returned `findings`, one source finding, with a
`Not checked` footer. No source finding has been acted on or treated as sustained.

The installed Codex adjudicator projection declares `sandbox_mode = "read-only"`
and disabled web search. The active session, however, exposes workspace writes,
web/MCP tools, and recursive agent dispatch; the collaboration interface offers
no sandbox/tool restriction parameter or observable child permission profile.
The work-loop adjudication protocol requires inspection of the active managed
profile and says to stop before dispatch and ask the owner if additional
capabilities are exposed. Dispatch is therefore surfaced before any adjudicator
starts. Engine state remains `SPEC-PLAN-REVIEW`.

The first adversarial raw report was also persisted and validated: 756 bytes,
`sha256:0d142eb2c8f6c035a0b86b2c05038b3c454e054594e7866cf5ce976715ecb43f`.
Its strict classifier returned `findings`, one source finding, without a
footer. Both reports went through the paired independent adjudications below;
neither raw report was treated as a clean review or repair instruction.

### Pre-EXECUTE round 1 disposition

The owner authorized a session-only adjudicator dispatch exception on
2026-10-07: bounded read-only instructions apply despite the broader exposed
tool surface, and all runtime policy remains binding. Their dispatch
instructions prohibited mutation, project-code execution, web/MCP access, and
recursive delegation.

Both complete adjudications were persisted, validated, and strictly classified
as `findings`, with no indeterminate result:

- Security: 1,499 bytes, artifact digest
  `sha256:f9702ec8f9f42363ba27fe6efbc3c69a8e3b0c65712d65a0684335f290d1734e`;
  sustained finding fingerprint
  `e58870653264a8e01d606c462832eb563cae40a8784224aa7083bf48eaee071c`.
  Resolve through T5 authority-before-persistence, audit-before-effect,
  stable-refusal, and negative fixture coverage for every disposition kind.
- Adversarial: 1,310 bytes, artifact digest
  `sha256:24704a3e8ee27446541e6efb6422e0c2779a9deb838c6becab1a54c3d2d76f18`;
  sustained finding fingerprint
  `591f0442303c34fc3d5a1980e2f7a46b654f2749b7cd194f10aeb43199190c77`.
  Resolve through T7's explicit paired Core version files, eval harness,
  free-standing release entry, Highlights decision, and release checks.

`findings-remain` returned to `SPEC-PLAN-DRAFTING` at sequence 2. Repairs change
only the plan's implementation/verification surface; all protected spec text
is unchanged. The literal and semantic companion sweep covers T5's authority
and VI-1010/Done-when text and T7's Touches, VI-1016, and Done-when text.
Both reviewers must re-review the repaired plan before either human gate.

### Pre-EXECUTE round 2 result

Both reviewers re-reviewed the repaired plan with no remaining findings.
The adversarial raw artifact validated at 27 bytes with digest
`sha256:74b12980b87d0d6bc6a2bc7f5b51d18571074f7a3c4ec52969e3394d4c582e3c`;
the raw classifier accepted structural clean with no footer.

The security raw artifact validated at 350 bytes with digest
`sha256:337d6878e17dc6829c42072ee1121c45779ef92d9bd4185c80509d021bdf83d5`.
Its no-findings report retained the implementation/scanner limitations in its
`Not checked` footer, so it received independent adjudication rather than the
raw-clean fast path. The paired adjudication validated at 101 bytes with digest
`sha256:46806d6d2b96c4c499b20a768d19f66549cd3f8c3b9e0f6541fe73073819af10`;
strict inspection returned clean with no indeterminate result.

The owner separately authorized the round-2 local classifier, adjudication
inspection, and `reviewers-clean` transition after automatic approval review
required action-specific execution authorization. The human spec and plan
approvals remain separate gates; neither is inferred from tool authorization.

## Implementation admission

Fresh owner approvals were recorded separately on 2026-10-07. The engine
advanced through `spec-approved` (sequence 5), `plan-approved` (sequence 6), and
`plan-locked` (sequence 7) to `CODE-IMPLEMENTATION`. The cohort pinned approved
spec hash `83b4cecbe378…` and approved plan hash `fae9486d375d…`.
Lifecycle status changes do not amend the protected substance.

The scheduler persisted one wave containing T1–T7 despite the plan's declared
dependency chain. Sequential implementation in authored T1–T7 order respects
every dependency; no parallel write is admitted and no scheduled-plan text is
changed to work around this observation. Each task receives its own dispatch
receipt, and all tasks must finish before wave exit.

No reusable project-knowledge observation was admitted at either approval
gate; there is no journal or topic diff to persist.

## T1 execution hold

The sequential T1 implementer added the first construction test and recorded
contract discovery in `implementer-T1-0.md`. No review runtime implementation
or schema has been written. Automatic approval review rejected the targeted
pytest command for lack of action-specific execution authorization, so the
intended TDD red is not yet earned. This is an execution-policy hold, not a
plan error or a failing test. No task-completion receipt is recorded.

The owner approved the exact targeted pytest command, and the controller ran
it before implementation: exit 1, eight failures and ten setup errors in
1.77 seconds, caused by the intended missing review schemas/runtime module.
The test file compiled and collected; this earns the discovery-stage red.
Two pytest cache-write warnings reflect host filesystem restrictions and do
not explain the intended failures. The implementer resumes after the resolved
execution-policy hold, without changing the approved plan.

## T1 current verification hold

The six canonical schemas, review-owned runtime validators, contract inventory,
and conformance tests are authored. Controller inspection checked shared-schema
references, closed record dispatch, exact integer versions, typed enum guards,
UTF-8/content-safety checks, and subject/policy lineage selection. Container-kind
dispatch received a stable-denial guard and two regression fixtures.

The targeted green run was rejected from both implementer and controller
contexts. The controller's automatic review specifically requires fresh
action-specific approval after repository changes, despite the previously
approved identical command. No green or mutation result is claimed; T1 remains
incomplete and no dispatch-completion receipt has been recorded. Implementation
of T2–T7 is pending.

The owner authorized the exact T1 runner again, including repeated runs after
T1 fixes and mutation checks. The first green completed: 23 passed in
2.12 seconds, exit 0, with one host cache-write warning. Mutation proof and
focused malformed-input coverage remain pending. The process-list diagnostic
is unavailable (`sysmond` service missing); it is not needed for verification.

## T1 guard mutation proof

The expanded baseline passed: 42 tests in 2.29 seconds, exit 0, with one host
cache-write warning. Mutation batch 001 deliberately removed exact integer
version, typed enum, sorted-unique path, and closed dispatch-kind guards.
The same runner returned exit 1: 18 failed and 24 passed in 1.72 seconds.
Failures exercised boolean versions, container enums, ambiguous path identity,
and container record kinds; this is guard failure rather than fixture setup
failure. No claim is made that the other 24 tests killed this batch.

The controller restored the runtime bytes and verified SHA-256
`c4a971c348f1a747a449c50e32259619f4d6527ed966fb0759ea6ba8eface828`.
Remaining mutation checks and T1 task completion are pending.

The repository local gates passed on the current T1 diff: `make lint-ruff
lint-mypy`, with no Ruff findings and no Mypy issues across 155 source files.
These gates will run again when later implementation changes warrant it.

The pack-test boundary gate failed with four above-pack reads in the T1 schema
fixtures. Canonical schema conformance belongs in the existing repository
roster suite; runtime tests remain pack-local. The implementer is repairing
this ownership split without changing the boundary gate or copying schemas.

The repository delivery-contract bundle suite passed before the ownership
repair: 16 tests in 42.17 seconds, exit 0, with one host cache-write warning.
It must run again after the moved schema fixtures and report-status conditions
are added. Inspection found the report schema lacked the runtime status/findings
cardinality rule; T1 is aligning this rule in its owned schema and fixtures.

## T1 repaired baseline and individual guard checks

After moving repository schema coverage out of the pack tests, the runtime
suite passed 54 tests in 1.17 seconds and the roster schema suite passed
33 tests in 75.09 seconds. Each returned exit 0 with one host cache-write
warning. The pack-test boundary gate passed all eight cases, including
381 Python files checked for pack confinement.

The controller split batch 001 into individual mutations. Each run changed
only the stated property, ran the same runtime suite, and restored the source
by inverse edit. Results are stored individually beneath the ignored
`.context/t1-mutations/results/` path.

| Invariant and exact mutation | Catching test | Observed failure | Run time |
| --- | --- | --- | --- |
| Exact version type: use `isinstance(int)` instead of `type(...) is int` | Malformed report, subject, and non-report boolean-version fixtures | 5 failed, 49 passed | 1.16 s |
| Typed enums: remove the string type guard | Container-valued report, subject, and non-report enum fixtures | 9 failed, 45 passed | 1.14 s |
| Ordered unique paths: replace sorted-set comparison with string-list validation | Ambiguous subject identity, duplicate and unsorted path fixtures | 2 failed, 52 passed | 1.26 s |
| Typed record dispatch: remove the string-kind guard | Container record-kind fixtures | 2 failed, 52 passed | 2.19 s |
| Raw string scan: remove per-string shared safety scanning, retain whole-JSON scanning | Control-character producer fixture | 1 failed, 53 passed | 2.34 s |
| Field byte bound: raise 64 KiB to 128 KiB | Oversized producer fixture | 1 failed, 53 passed | 16.16 s |
| UTF-8 field validation: remove strict encoding from the nonempty-string guard | Invalid UTF-8 producer fixture | 1 failed, 53 passed | 2.95 s |

Each observed failure was the expected test assertion or stable-denial
regression, rather than collection or setup failure. The raw-string scan
mutation did not kill the executable-text fixture because whole-report
scanning also protects it; executable-text proof remains pending.

The runtime restoration hash matches its clean baseline:
`c4a971c348f1a747a449c50e32259619f4d6527ed966fb0759ea6ba8eface828`.
The report schema's new clean baseline is
`9457b0d22ccd6490743ee231190259f888cd602006a3b97920055af41f06dbaa`.

The next runtime mutations were caught individually: subject fingerprint
(1 failed, 1.22 s), subject policy (1 failed, 1.27 s), duplicate sequence
(1 failed, 2.05 s), forked previous-report linkage (1 failed, 2.58 s), missing
validator registry entry (1 failed, 0.87 s), wrong writer profile (1 failed,
0.92 s), and the obligation missing-field guard (1 failed, 1.40 s).
Each run had 53 passing tests and restored its source by inverse edit.
The obligation mutation proves that validator's stable missing-field denial;
it does not claim coverage of every record family's required-field guard.

Inspection of the duplicate fixture found that it also broke the previous-ID
chain. The controller changed only that fixture's previous ID to preserve a
linear chain while duplicating sequence 2. Its renewed green and mutation
proof are pending; the earlier result proves denial mapping only.

The revised duplicate fixture passed its clean baseline (54 tests, 0.75 s).
Removing only duplicate-sequence rejection then admitted `report-dup`:
`assert selected is None` failed (1 failed, 53 passed, 0.97 s). This isolates
duplicate admission from fork rejection.

Additional individual mutations removed the assessment unknown-field guard
(1 failed, 0.86 s), the subject projection-version requirement while preserving
provider and unknown-field checks (1 failed, 0.87 s), and the shared authority
shape scanner pattern (1 failed, 0.63 s). In each case the targeted assertion
`assert not ok` failed because the malformed record became accepted.
The scanner mutation was temporary proof against the real Slice 1 helper;
no shared-service change remains. Its restored SHA-256 is
`539e1e0b1cedaa88ec6cb3603c212d37b4ba4cf043d4fb6ebbb205c600a6f2fb`,
and `git diff` for that helper is empty.

An over-strict clean-status check killed the inert-prose positive oracle
(4 failed, 50 passed, 1.18 s; three secondary failures changed refusal codes).
Returning the lineage root instead of the final tip killed the safe-tip
positive oracle (1 failed, 53 passed, 1.42 s). Allowing major version 2 killed
the unknown-major fixture (1 failed, 0.84 s). Removing paired vector length
validation killed its isolated fixture (1 failed, 2.29 s).
All temporary changes were restored; the review runtime hash again matches
`c4a971c348f1a747a449c50e32259619f4d6527ed966fb0759ea6ba8eface828`.

The original seven report-schema missing-field fixtures were restored after
the boundary move dropped them. The focused schema baseline passed 26 tests
(14 deselected) in 1.37 s, exit 0. Schema mutations and final T1 gates remain
pending.

## T1 final mutation and gate evidence

All 36 individual mutation runs produced their expected catching-test failure.
The initial duplicate result proves denial mapping; its isolated repeat proves
admission rejection. Every new T1 test function has a catching mutation, but
remaining parametrized non-report cases still need their own guard proof.
Representative proofs are named rather than presented as every family's
coverage. The seven report
required-field fixtures were each checked with their own schema mutation.
The final malformed sequence fixture preserves all other required lineage
fields; admitting bool through `_positive_int` killed that fixture (1 failed,
53 passed, 1.33 s). No collection or setup error was used as mutation proof.

Schema checks caught removal of path uniqueness (1 failed, 2.17 s), admitting
unknown statuses (1 failed, 1.93 s), adding a false required workflow field
to the report (positive example failed, 2.13 s), removing status/findings
cardinality (both mismatch fixtures failed, 1.64 s), removing obligation kind
requiredness (1 failed, 1.57 s), and admitting unknown finding fields (1 failed,
1.46 s). Each run otherwise had 25 passing focused tests, except the two
cardinality failures which left 24 passing; 14 unrelated tests were deselected.

Removing each report requirement independently killed its corresponding
missing-field fixture: schema version (1.85 s), report ID (1.75 s), role
(1.55 s), subject (1.47 s), terminal status (1.55 s), lineage (1.91 s), and
findings (1.62 s). Each had one intended failure; terminal status also killed
the generic report-requiredness fixture. All schema bytes were restored and
their baseline hashes verified.

Restored gates passed: runtime 54 tests in 0.87 s, repository contract bundle
40 tests in 34.67 s, pack-test boundary eight cases across 381 files, and
`git diff --check`. Pytest emitted only host cache-write warnings.
Final Ruff found one missing blank-line separator in the relocated pack test.
The controller restored the separator and is rerunning lint/typecheck;
no behavior or assertion changed. Mypy excludes skill scripts by repository
policy, so the typed-package pass is not claimed as review-runtime type proof.

After the separator repair, `make lint-ruff lint-mypy` passed: Ruff clean and
Mypy no issues across 155 typed-package source files. The remaining T1 hold is
individual proof for parametrized non-report cases, not a failing baseline.

## T1 remaining-case execution hold

The malformed-report fixture now uses a clean report with empty findings.
Its malformed findings value is an empty string. These isolate terminal-status
membership and list-type guards from findings cardinality. The revised fixture
has not yet run; the preceding green baseline predates this fixture change.

Automatic approval review rejected the exact retry of
`python3 -m pytest packs/core/tests/skills/work-loop/test_review_contracts.py -q`
because it executes repository code and no action-specific approval marker was
present. The controller requested approval for that command and its repeats.
No workaround or alternate runner was used. The remaining 32 mutation cases
are pending; no mutation is currently applied and T1 has no dispatch receipt.

## T1 additional runtime mutation evidence

The owner approved the exact pack pytest command and repeats. The isolated
fixture baseline passed 54 tests in 0.52 s. All 18 remaining runtime mutations
then produced one intended failing case and 53 passing cases per run, bringing
the individual proof count to 54. Full outputs are retained in the ignored
`.context/t1-mutations/results/` directory.

The five malformed-report cases caught invalid admission independently:
empty report ID (1.08 s), empty role (1.15 s), malformed subject (0.97 s),
unknown terminal status (1.10 s), and non-list findings (0.90 s).
Missing subject fingerprint (0.88 s), assessment kind (0.78 s), and decision
maker (0.90 s) caught changes to the stable missing-field denial code;
removing finding actual-failure requiredness admitted the invalid record and
failed its rejection assertion (0.65 s).

Unknown-field mutations admitted their invalid subject (1.14 s), obligation
(1.97 s), report (0.96 s), finding (0.83 s), and disposition (1.27 s).
Incomplete-lineage mutations admitted their invalid obligation (0.91 s),
report (1.21 s), assessment (0.86 s), and disposition (0.71 s).
Each corresponding rejection assertion failed. No setup error counted as proof.

The restored pack suite passed 54 tests in 0.70 s. Runtime and shared
content-safety hashes match their earlier baselines. Automatic approval review
blocked the focused roster command because it differs from the specifically
approved pack command; approval for that command and repeats is pending.
The first temporary schema mutation was restored in `finally`; its inverse
also altered two context-line indentation bytes. The controller restored the
original bytes and confirmed the subject schema hash matches
`ad5958e85c6c0965d6e1f7158a647c8d5b1a74c002513f2c7ccb11e0cb4fbcb6`.
The 14 remaining schema checks have not run, and no mutation remains applied.

## T1 completed parameter-case proofs

The owner separately approved the focused roster command and its repeats.
All 14 remaining schema mutations produced one intended failing test, 25
passing tests, and 14 deselected tests. Requiredness checks covered subject
fingerprint (1.39 s), finding actual failure (1.65 s), assessment kind (1.41 s),
and disposition decision maker (1.32 s). Unknown-field checks covered subject
(2.02 s), obligation (1.90 s), report (1.45 s), assessment (1.73 s), and
disposition (2.02 s). Adding a false required workflow field killed the valid
example for each remaining family: subject (1.89 s), obligation (1.54 s),
finding (1.64 s), assessment (1.34 s), and disposition (1.46 s).

The disposition requiredness patch initially named an optional field as its
context and did not apply. The controller corrected the context before running
it; this patch failure was not counted as test evidence. Every applied mutant
was restored after its test process finished. The complete T1 proof count is
68 individual catching mutations, including the previously recorded 36.
Full records identify each invariant, failed test, output, and run time in the
ignored `.context/t1-mutations/results/` directory. No collection or setup error
is counted as a catching proof.

The restored focused schema baseline passed 26 tests, with 14 deselected, in
1.68 s. The restored pack baseline passed 54 tests in 0.70 s. `git diff --check`
passed. Runtime and all six schemas match their pre-mutation hashes; no
temporary validation change remains. Prior full contract bundle, pack boundary,
Ruff, and Mypy gates remain green. These results complete VI-1001–VI-1003.

## T1 dispatch accounting hold

Automatic approval review rejected the controller's `loop-cohort.py
dispatch-receipt` command for T1 because it executes repository code and writes
cohort state without an action-specific approval marker. The controller
requested approval for the exact command, task, wave, and run ID. The state
files were not edited by hand. T1 verification is complete; recording its
dispatch receipt remains pending.

The owner approved that exact command. The controller recorded the T1 receipt
in wave 0 for run `accb0133-8ca5-414a-a831-41a1bd9f35c4`; the tool exited 0.
The implementer's final T1 report is ready. T2 is dispatched sequentially with
its first test required before implementation and controller-owned execution.

## T2 first-test execution hold

The sequential T2 implementer discovered `_review_selection.py` as its new
pure service owner and wrote the first contract-surface test before any
selection logic. The controller required correction of its parameter-built
script loader to a literal path, as the pack-test boundary requires. The
implementer recorded that final VI-1004 still needs the actual engine caller
and independent plan/task provenance variation; the first test does not claim
that finished coverage.

Automatic approval review rejected the exact first-test pytest target because
it is a new target outside the T1 and roster approvals. The controller
requested approval for that exact target plus the whole T2 test file and
mutation repeats. No alternate runner or implementation logic was used to
bypass the red-test boundary. T2 remains paused before its first executed red.

The owner approved both T2 commands and repeats. The controller ran the exact
first target: exit 1, one setup error in 0.72 s, with the expected
`T2 selection module is not implemented: _review_selection.py` diagnostic.
The test collected; the absent discovered service is the reason for this red.
This is a discovery red, not an assertion-level mutation proof. T2 logic was
authorized to proceed after that observed result; all final tests still need
the implemented behavior and their own catching mutation checks.

## T2 first implemented baseline and controller inspection

The approved full T2 file passed 20 tests in 0.85 s. This initial baseline does
not complete VI-1004–VI-1005. The controller inspected the actual engine caller,
service, and tests and requested regressions before further logic changes.

Observed gaps include indeterminate reports treated as satisfied findings;
dispositions lacking current subject and replacement binding; arbitrary list
order selecting between conflicting assessments; malformed policy containers
escaping as raw lookup or type errors; noncanonical changed paths; and stale
obligation identity. The first parity case also varies provenance together
instead of independently. The requested regressions cover these classes and
the named stale, malformed, forked, unknown-major, and invalid-waiver cases.
The implementer is paused at another controller-proved red boundary.

The first regression run failed collection with an indentation error (exit 2,
0.45 s); it is not a behavioral red. After a test-only syntax repair, the
approved suite produced 17 intended assertion-level failures and 35 passes in
1.52 s, exit 1. The failures confirm indeterminate status, stale obligation,
ambiguous assessment, disposition binding/replacement, canonical-path, and
typed-policy parse gaps. The controller permitted class repairs only after
that result. The full red output is retained in ignored
`.context/t2-regression-red.json`.

The next T2 run produced two failures and 51 passes in 1.05 s. Its proposed
fixed-by positive fixture reused sequence 1 for two same-role reports, so the
lineage refusal was correct. Its incomplete-lineage fixture expected a local
denial instead of the delegated Slice 1 `denied-missing-required-field` code.
Both fixtures need correction. Controller inspection also found that the new
replacement helper required the same subject and did not prove the fresh
replacement-subject rule. T2 remains unfinished; new regressions and a class
repair are required before mutation proof and dispatch accounting.

The replacement/path regression run produced four failures and 54 passes in
1.24 s. Two drive-letter paths were wrongly admitted. The fixed-by positive
still evaluated the old subject, while the same-subject negative selected a
new clean lineage tip and wrongly expected review to remain blocked. A current
clean report must retain the accepted clean-row behavior. The controller
directed a smaller T2 mechanism: current supported failures close through
current verified accept-risk facts; T5 owns fixed-by links to replacement
subjects, and T2 evaluates the replacement subject's fresh report normally.
The corrected negative uses a still-current supported failure with a
self-replacement link. Test correction and class repair remain pending.

The corrected suite produced four failures and 54 passes in 1.65 s. The fresh
replacement-subject clean positive passes. The drive-letter cases and the
other-role replacement expose remaining implementation gaps. The same-subject
case instead lacks an assessment bound to its current report; that fixture
must be corrected before claiming its failure as proof of a closure defect.
The controller restarted the sequential implementer for this fixture repair,
the bounded T2 class repairs, and exact mutation metadata. T2 is not complete.

Automatic approval review rejected the post-repair T2 pytest repeat, stating
that the earlier repeat approval did not cover material source changes. The
controller requested action-specific approval for the corrected full suite,
mutation repeats, and restored baseline. No alternative runner was used.
Read-only inspection continues while that execution gate is pending.

The latest frozen source removes T2's fixed-by shortcut, binds the corrected
same-subject fixture assessment to the current report, and rejects drive and
URI paths. Inspection also removed redundant canonical-path guards and local
copies of unused delivery-subject shape rules: the shipped validator remains
the first check, followed by strict version and consumed identity checks.
These changes are not yet verified by an executed suite. No T2 receipt or
mutation proof is recorded.

After the owner approved the corrected suite and mutation repeats, the
controller's non-login shell selected Python 3.14 without pytest. The command
exited 1 with `No module named pytest`; no tests executed. Automatic approval
review then rejected the default-login-shell retry as a changed invocation.
The controller requested approval for the exact suite with `login: true`,
mutation repeats, and restored baseline. The frozen source and all 31 mutation
source chunks were inspected; reversible patches are prepared but none have
been applied. This environment hold does not count as a test failure or proof.

The owner approved the default-login-shell invocation. The corrected T2 suite
passed 58 tests in 0.91 s; only the host pytest-cache warning remains. Mutants
T2-MUT-001–022 each produced catching test failures and were restored before
the next run. Full output and exact apply/restore patches are retained beneath
ignored `.context/t2-mutations/`. Provenance mutations change only hash input,
keeping record shape valid. The delegated-validator mutation proves stable
denial-code preservation rather than admission of invalid input.

T2-MUT-023 removed the material flag, but 58 tests still passed in 1.01 s.
This survivor is not proof. The controller restored source and required a
supported nonmaterial finding fixture, plus exact malformed-policy denial
checks, before continuing. No T2 dispatch receipt has been recorded.

The implementer added that nonmaterial fixture and exact policy denial checks
without changing runtime source. Automatic approval review rejected the next
mutation run because the tests changed after the prior approval; the prepared
mutant was restored in the controller's `finally` block. The source hash is
again `5f8fe9fe105e0772ea4dfbd7cd02d71e0adbd548a44d31a520f26c7ef02881e7`.
The controller requested the strengthened 59-case suite, remaining mutations,
and restored baseline under the default login shell. Five more narrow mutants
are prepared for the remaining canonical-path, stable-denial, role-container,
identity-denial, and accept-risk positive cases. None have been applied.

On 2026-10-08, the owner approved the strengthened default-shell suite and
remaining mutations. The 59-case baseline passed in 1.21 s. T2-MUT-023 now
fails the supported nonmaterial case. All 38 distinct mutations are caught,
and [the T2 mutation ledger](t2-mutation-ledger.md) maps every current case to
its catching runs. The final restored baseline passes 59 tests in 0.85 s;
the source hash matches the frozen baseline, and `git diff --check` passes.

Automatic approval review rejected `make lint-ruff lint-mypy` and
`python3 tools/lint-pack-test-boundary.py`, requiring exact approval for
post-change repository tooling. The controller requested these default-shell
gates and the T2 dispatch receipt conditional on both passing. T2 remains
unaccounted in the cohort until those checks and that receipt complete.

The approved pack-boundary command passed eight checks across 382 Python
files. Ruff found one constant-attribute `getattr` in the T2 test; the
implementer replaced it with direct attribute access. It also removed the
orphan `_string_list` helper left by the earlier shared-validator cleanup.
Read-only function-body comparison confirms all remaining runtime functions
are byte-identical to the mutation-proved source. The cleaned runtime SHA-256
is `333d5f21f6583c0b530ced46d7b75c23b166fa1fdd789771159571ad7ccc2f6d`.
The diff check passes. Automatic approval review rejected post-cleanup lint
and test reruns; exact approval is requested before executing them. The
conditional T2 receipt remains authorized, but its gate precondition is unmet.

The owner approved final frozen-source reruns. Ruff is clean; mypy reports
no issues in 155 typed package files (these gates do not type-check the runtime
scripts). The cleaned T2 suite passes 59 tests in 1.24 s. The pack-boundary
and diff checks also pass. The approved T2 dispatch receipt completed with
exit 0 for wave 0 and run `accb0133-8ca5-414a-a831-41a1bd9f35c4`.
The implementer's final report is ready. VI-1004–VI-1005 are verified through
the actual engine callable and synthetic adapter; the public invocation is
unchanged. T3 is dispatched sequentially at its first-test-before-logic gate.

## T3 first-test execution hold

T3 resolved `_review_persistence.py` as the report service owner, with
`append_current_review_report` and `select_current_review_report` over the
real `EvidenceStore`. Before execution, the controller required literal
fixture script paths and a copied report subject so mutation of the submitted
report does not also mutate the expected subject. The repaired construction
test covers durable replay, whole-subject binding, and alias isolation.
No T3 runtime logic has been written.

Automatic approval review rejected the new command
`python3 -m pytest packs/core/tests/skills/work-loop/test_review_persistence.py -q`
because the exact repository-test target needs approval. The controller
requested its default-login-shell first run and implementation/mutation
repeats. The intended discovery red remains unearned; no alternate runner is
used, and T3 remains paused before logic.

The owner approved that exact default-shell suite. The first run collected
and exited 1 with one setup error in 0.82 s: the intended
`T3 review persistence module is not implemented: _review_persistence.py`.
This earns the implementation-discovered red, not a behavioral mutation proof.
The controller resumed the sequential implementer for T3 logic and its full
corpus. Every new test still requires a catching mutation before completion.

## T3 regression expansion

The first implemented report suite exited 1 with one failure and six passes
in 1.59 s. The failing whole-subject fixture had mismatched path/status
counts, so structural validation correctly refused it before identity
comparison. The fixture was corrected to preserve a valid subject shape.

The expanded suite exited 1 with 15 failures and ten passes in 1.90 s.
Confirmed runtime gaps include overlapping semantic-kind detection, legacy
typed identity and denial compatibility, atomic port-issued report sequencing,
legacy content-safety checks on replay, and malformed reader selectors.
The controller requested test-only corrections before runtime repair: privacy
and control fixtures must assert T1's actual denial codes, and the whole-report
size fixture must be structurally valid and demonstrably exceed one MiB.
Prevalidation must use an owned exception rather than inspect a supplied
store class's module globals.

The proposed supersession-authority regression was based on an incorrect
assumption. Shipped Slice 1's `append_supersession` requires the `append`
operation, not a separate `supersede` operation. T3 must preserve that
contract. The regression is being corrected to assert equivalent authority
and denial behavior rather than redefine the shipped grant requirements.

Automatic approval review rejected the existing Slice 1 evidence-store suite
again after the owner's approval, reporting that it did not recognize an
action-specific marker for execution of modified repository code. The exact
default-shell command and repair/mutation repeats are pending renewed
approval. No alternate runner was used.

The corrected T3 regression run exited 1 with 14 failures and 15 passes in
4.65 s. It earned reds for the owned prevalidation refusal, all review-family
admission, typed legacy identity and denial compatibility, locked port-issued
sequence and retry behavior, content safety on legacy replay, and malformed
reader selectors. One remaining authority-event expectation requires the
shipped distinction: the outer refusal is `denied-producer-authority`, while
the event reports `denied-missing-operation`. The controller authorized
repairs of these classes without changing Slice 1 grant requirements.
Pytest also warned that its disposable cache could not be written; tests
collected and ran normally, so this is not counted as a test failure.

The first repaired-source baseline exited 1 with four failures and 27 passes
in 4.78 s. Controller inspection found that the new semantic writer returned
the new transaction before updating in-memory indexes, and review-kind
detectors still confused primary identities with cross-record references.
One duplicate-report test also expected the wrong exception owner; delegated
store refusals remain `EvidenceStoreRefused`. These earned failures are being
repaired. The controller requested additional regressions for transaction
identity reuse and multiple reports for one role/subject in a single batch
before repairing those related classes. No T3 completion receipt is recorded.

The next baseline exited 1 with two failures and 31 passes in 5.07 s.
Both failures were exception-owner expectations: whole-subject prevalidation
uses `ReviewPersistenceRefused`, and the delegated duplicate-record refusal
uses `EvidenceStoreRefused`. The controller corrected those expectations.
Runtime repairs passed the other cases in that run; the current suite is not
yet claimed green.

Test-only additions now cover actual concurrent threads using separate open
stores, same-opaque-ID retries with different typed record bodies, and unsafe
transaction headers on replay. The latter is grounded in the existing
content-safety architecture's requirement that semantic transaction replay
use the registered Structured control profile. The changed-body retry fixture
also stores the alternate report under its own transaction before attempting
the conflicting retry, so it can expose the original false-idempotency class.
These tests have not run. Automatic approval review rejected the T3 command
because these additions materially changed the suite after prior approval.
Both exact T3 and Slice 1 commands, with repair and mutation repeats, await
fresh approval. `git diff --check` passes. No alternate execution path was used.

## T3 frozen baseline and mutation execution hold

The owner approved both exact pytest suites. T3 then exited 1 with one failure
and 35 passes in 5.29 s; the unsafe transaction-header replay fixture exposed
the missing registered profile check. The existing Slice 1 evidence-store
suite passed 110 tests in 3.30 s. The controller added the shared header
profile check and kept replay failures wrapped as `EvidenceStoreError`.
The repaired runs passed 36 T3 tests in 4.90 s and 110 Slice 1 tests in 3.77 s.

Mutation preparation strengthened two tests: input and returned-transaction
alias isolation now checks the live store and an idempotent retry, and torn
empty-log recovery checks that the suffix is actually removed. A baseline
attempt interrupted by the owner is not counted as evidence. The strengthened
suite subsequently passed all 36 tests in 4.60 s. Pytest's disposable-cache
write warning does not affect collection or execution.

The approved repository gates passed after four formatting/unused-variable
repairs. Ruff is clean. Mypy passes for 155 typed package files; that command
does not type-check these runtime scripts. The pack test-boundary linter
passes all eight checks across 383 Python files. `git diff --check` passes.

The frozen T3 runtime SHA-256 values are
`3949767ca2ec01be851acd55003e9367d3013daf290094af9bf26134480f5592`
for `_evidence_store.py` and
`993eb0c630b6d7ab0e27b83a82d40fe19af3f0494556bda4926b637a2d778e98`
for `_review_persistence.py`. The strengthened test SHA-256 is
`31bc6268e924e7041464132b7502b65e1dfbb90d262b0d385c237c40c26a0abc`.

Twenty-nine deliberate mutations are prepared with exact inverse patches.
They cover current subject/policy binding, provenance exclusion, fork refusal,
the closed registry, grant checks, typed identity, legacy denials, locked
sequence issuance, transaction retry/body association, registered replay
profiles, snapshots, complete-prefix recovery, audit pairing, and durability.
Where defense in depth protects one invariant, the mutation disables its
deciding guards together; error-owner and legacy-code checks are separately
labeled denial-mapping proof rather than unsafe-admission proof.

Automatic approval review rejected the first mutation execution because it
treated the latest owner approval as covering lint gates rather than the
changed pytest execution. The attempted whole-subject mutation was restored
in `finally`; all five service hashes match the frozen baseline. No runtime
mutation test was executed or counted. The exact default-shell mutation runs,
repair repeats, and restored-baseline repeats await fresh approval. T3 has
no completion receipt, and T4 has not started.

## T3 mutation progress and execution refusal

The owner approved the 29 prepared T3 mutation runs and restored-baseline
repeats. Twenty-six distinct mutations have now been caught by identified
runtime assertions in 27 runs. Their union covers all 36 current test cases.
The [T3 mutation ledger](t3-mutation-ledger.md) maps each case to its catching
mutation and records the three remaining checks without claiming completion.

Mutation 017's initial inverse matched an unrelated `pass`. The controller
restored both locations, verified the exact original service hashes, made
the inverse contextual, and repeated the mutation with a catching assertion
and verified restoration. Two patch-application failures for mutations 018
and 022 were corrected before their successful runs. No patch or execution
failure counts as mutation proof.

Automatic approval review rejected mutation 027's exact pytest execution,
citing unverified repository code and a trusted action-specific approval
marker. The controller inspected the test's literal script loaders, temporary
fixture writes, imports, shared fixtures, pytest configuration, and the exact
audit-pairing mutation. A provenance-grounded retry timed out in automatic
approval review. The single retry permitted by that timeout was rejected
because no fresh reapproval followed the concrete rejection.

Every applied mutation was restored. The evidence-store hash remains
`3949767ca2ec01be851acd55003e9367d3013daf290094af9bf26134480f5592`;
the other four checked services match their frozen baseline hashes.
Mutations 027–029 and the final restored baseline remain pending fresh
action-specific approval. The exact request has been presented to the owner.
T3 has no completion receipt; T4 has not started. No alternate execution
path or external action was attempted.

## T3 completed verification

Following the owner's concrete reapproval, the final three mutations were
caught. Audit-pairing removal failed the duplicate-report event assertion;
policy-binding removal failed the wrong-policy assertion; removal of the
confined append failed replay and multi-store durability assertions.
All five service hashes matched the baseline after each restoration.

T3 now has 29 distinct catching mutations across 30 runs, including the
verified repeat of mutation 017. Every one of the 36 new test cases is mapped
to at least one catching mutation in the durable mutation ledger. The final
restored baseline passed 36 tests in 4.55 seconds. No rejected or failed patch
attempt is counted as proof. T3's implementer returned Ready after updating
its task note. The final report is persisted verbatim in
`notes/implementer-T3-ready.md`.

Automatic approval review rejected the exact T3 `dispatch-receipt` command:
it recognized full-loop authorization in substance but required action-specific
approval for execution of the local script and cohort-state mutation.
The owner has been asked to approve that exact command. No state file was
edited and no alternate runner was used. T3's receipt remains unrecorded;
engine state remains CODE-IMPLEMENTATION and T4 has not started at this hold.

The owner approved the exact receipt command. It completed successfully and
recorded T3 in wave 0. The controller confirmed the receipt in cohort state;
no manual state change was made. T4 is dispatched sequentially in test-only
construction mode and must earn its first red before runtime implementation.

## T4 first-red construction stage

The sequential implementer added only `test_review_assessment.py` and its own
task note, then returned Blocked pending the controller's earned-red run.
Its report is persisted verbatim in `notes/implementer-T4-first-red.md`.
No T4 runtime service exists yet. The selected sibling seams are
`_review_assessment.py` and `_review_bridge.py`; they reuse T1 validators and
T3's atomic batch port without a second journal or runtime schema reads.

Controller inspection corrected the first draft before execution: the review
subject must use T1's closed shape, opinion fixtures must retain nonempty
reachability text, and assessment identities must support repeated outcomes
through distinct identities rather than an outcome-shaped identity.
Both construction fixtures now assert T1 schema validity and supply explicit
assessment identities and controlled falsifiability facts. Broader truth-table
and bridge lifecycle tests remain for the post-red stage.

Automatic approval review rejected the exact command
`python3 -m pytest packs/core/tests/skills/work-loop/test_review_assessment.py -q`.
It recognized implementation authorization in substance but required
action-specific reapproval for executing this new repository suite.
No test executed or earned red is claimed. The owner has been asked to approve
the exact suite and its repair, mutation, and restored-baseline runs.
Syntax compilation reported by the implementer is advisory, not runtime proof.
No alternate runner was used. T4 remains in the test-only stage.

## T4 discovery red

The owner approved the exact assessment suite. It exited 1 with two setup
errors in 1.00 second because `_review_assessment.py` does not yet exist.
This is the expected implementation-discovery red, not a runtime assertion
or mutation proof. The fixture schema assertions have not yet executed.

The implementer is authorized for the next bounded stage: add the pure
evaluator, expand its six-class truth-table tests and refusal cases, and add
the first bridge construction tests. Bridge and evidence-store runtime edits
remain withheld until the controller runs those construction tests.
The complete bridge delta must use the current store lock and replay path.
No new authority, record fields, second journal, or mutable task projection
is introduced. Final T4 mutation verification remains outstanding.

## T4 broadened construction stage

The implementer added the pure evaluator foundation and expanded its tests,
then added `test_review_bridge.py` without implementing that runtime service.
The returned report is persisted verbatim in
`notes/implementer-T4-broadened-red.md`. EvidenceStore is still at the verified
T3 baseline. No T4 behavior test or mutation proof is claimed yet.

The controller identified negative cases before repair: unrelated findings
cannot be assessed under another report, duplicates require current identity,
every cited path requires a current control, and independent authority must
record the judgment actually made rather than default to supported.
The widened tests precede those repairs.

Both exact suite commands were attempted independently and rejected by
automatic approval review. It requires fresh approval for the materially
expanded assessment suite and the newly added bridge suite. Neither executed.
The owner has been asked to approve both commands and their repair, mutation,
and restored-baseline repeats. No alternate runner was used.

While approval is pending, a test-only follow-up fixes the bridge proof shape:
persist the actual source report, reopen the store to prove replay, bind
receipt identity to the full canonical source tuple including acceptance
fingerprint, and use one closed authority-input shape throughout the corpus.
Bridge and EvidenceStore runtime edits remain withheld until earned reds.

The test-only correction pass is complete and frozen; its report is persisted
verbatim in `notes/implementer-T4-test-corrections.md`. The bridge suite now
requires a durable source report, actually reopens the store for replay proof,
and checks that receipt identity distinguishes acceptance fingerprints.
Assessment fixtures use one authority shape and current control facts for
each cited path. These corrected suites have not run.

The implementer's advisory syntax-compilation attempt was also rejected by
automatic approval review. It provides no verification evidence and was not
retried through another runner. Required controller pytest execution will
compile these files as part of normal collection; no separate syntax-command
approval is needed for the requested next step. The controller retains all
project runners. Bridge and EvidenceStore runtime remain unchanged.

## T4 earned runtime reds and bridge implementation

Following owner approval, the assessment suite exited 1 with nine failures
and 11 passes in 1.34 seconds. The bridge suite exited 1 with three setup
errors in 1.66 seconds because `_review_bridge.py` is absent. Its discovery
errors are not runtime assertion or mutation proof. Disposable-cache warnings
did not prevent collection or execution.

Assessment reds cover stale edge evidence misclassified as a refusal,
unsupported-stale records incorrectly rebound to a replacement subject,
missing per-path control input, unconsumed independent-judgment shape,
unrelated findings admitted under another report, malformed duplicate identity,
and unsupported control claims based only on an aggregate boolean.
An assessment remains bound to its source report's subject, even when that
source is stale relative to the current context; it cannot relabel an old
report's finding as a finding on a new subject.

The implementer is authorized to repair these classes, implement the bridge,
and integrate one shared semantic-transition check into the store's locked
append and replay paths. Bounded T3 fixture adjustments may preserve registry
coverage while adding the newly required current-source and complete-delta
facts. Existing Slice 1 APIs, grant rules, denial mappings, unrelated legacy
receipts, and plan/task/procedure authority remain unchanged.
Bridge replacement, invalidation, recovery, concurrency, retry, authority,
audit-pairing, and real acceptance-contradiction tests must accompany the
handoff. All project runners and mutation verification remain controller-owned;
the implementer is restricted to reads and edits, including no syntax runner.

## T4 runtime handoff and regression state

The implementer returned the first bridge/store runtime handoff, persisted
verbatim in `notes/implementer-T4-runtime.md`; it remains Blocked pending
controller verification. All four requested suite executions were rejected
by automatic approval review after runtime changes. The interrupted wait
left no admitted test process from those attempts; stored tool results show
four execution rejections. No test result is inferred from that interruption.

The owner then explicitly approved the evidence-store suite. It exited 1
with 110 setup errors in 6.73 seconds because four leftover lines caused an
indentation error in `_active_bridge_receipts_for_source`. The controller
removed those dead lines and repeated the exact suite: 110 passed in
3.25 seconds. This setup failure is not behavioral or mutation proof.

The controller requested fresh approval for the other three exact commands:
assessment, bridge, and persistence. Meanwhile, direct source inspection
identified incomplete transition classes before further runtime repair:
no-assessment batches bypass lifecycle checks; source report lookup does not
verify the current tip; receipt IDs do not prove the corresponding receipt
body; and projection must preserve report-plus-finding identity and exclude
invalidated sources. Required lifecycle recovery, concurrency, retry,
authority, and same-operation audit cases need T4-specific construction proof.

The implementer is expanding these tests only, with runtime frozen until
controller-earned reds. The bounded T3 registry fixture now persists its
actual source report before the assessment family; preservation of its
coverage and the complete-delta invariant will be verified by the pending
persistence run. S1's 110-test regression suite is green after the syntax fix;
T4's broad runtime suites, required gates, and mutation proof remain pending.

The final test-only expansion is complete and frozen. The implementer report
is persisted verbatim in `notes/implementer-T4-lifecycle-tests.md`. It adds
concrete VI-1009 cases for source invalidation and replay, report-tip changes,
new subjects, supported-to-indeterminate replacement, incomplete deltas,
stale open stores, retry authority and body identity, checksum-valid corrupt
frames, torn suffixes, paired audit events, and conflicting same-source
assessments. The pure assessment corpus also covers cross-report duplicates
and non-vacuous current control proof. No runtime repair followed this stage.

Despite the report's phrase 'approved suites', the current approval state is:
the evidence-store command was separately reapproved and passed; the other
three exact commands await owner reapproval after their concrete runtime-change
rejections. The controller does not infer execution approval from a task report.
No T4 completion receipt or mutation proof is claimed. `git diff --check`
passes; required runtime and repository gates remain outstanding.

## T4 approved lifecycle runs and class repair

The owner reapproved all three pending exact suite commands. Assessment
completed with 1 failed and 24 passed in 0.71 seconds; the earned failure
is current same-subject duplicate classification across reports or roles.
Bridge completed with 11 failed and 14 passed in 1.61 seconds. Persistence
completed with 36 passed in 4.05 seconds, preserving the T3 coverage after
the bounded source-report fixture update. These are baseline results, not
mutation proof or a T4 completion claim.

The bridge failures expose one lifecycle boundary class: current source
selection, complete assessment/receipt/supersession deltas, source retirement,
report-plus-finding projection identity, stable malformed-input refusal,
and exact retry composition after durable refresh. The implementer is
authorized to repair that class within the accepted T4 envelope, including
minimal typed-report persistence integration. Composition must occur under
the existing refreshed store lock; raw semantic retries retain exact ordered
record identities and checksum semantics. Caller-supplied validators and
authority callbacks remain excluded.

The controller also required stronger negative projection assertions and a
complete two-assessment fixture so those tests cannot pass through an
unrelated refusal. All runners, root inspection, restored-baseline verification,
and mutation proof remain controller-owned. T4 has no completion receipt.

The runtime repair handoff is persisted verbatim in
`notes/implementer-T4-class-repair.md`. All four exact repair reruns were
rejected by automatic approval review; stored tool results confirm no
execution was admitted despite the interrupted wait. The review requires
a fresh action-specific execution marker. The owner approval request names
the assessment, bridge, persistence, and evidence-store commands and includes
repair repeats and mutation/restoration checks.

Read-only controller inspection still finds composition outside the refreshed
store lock and blind committed-body substitution during bridge retry. The
implementer is adding concrete interleaving and typed-report replacement
tests before further repair. No new T4 test pass or mutation proof is claimed.

The test-only handoff is persisted verbatim in
`notes/implementer-T4-interleaving-tests.md`. Controller inspection refutes its
concurrency claim: the added thread performs the only append after the first
writer has finished. The implementer is correcting the test to overlap two
actual writes at a deterministic barrier and check both thread completions.
This correction precedes execution; runtime remains frozen.

The corrected test-only report is persisted verbatim in
`notes/implementer-T4-concurrency-correction.md`. Controller inspection confirms
two actual appends now overlap at a deterministic pre-commit barrier; both
thread completions and the complete durable winner's evidence delta are
asserted. Changed-body retry also asserts unchanged durable facts. Runtime is
still frozen. The report labels unrun gates 'fail'; their actual status is
not run, with no test evidence inferred. The final test file hash is
`44a1e32d10d96b06b1a2394e57a8c46d560377097aba2e65a08ed6602320d680`.

## Knowledge integrations

The exposed tool catalog contains no eligible capability with contract
`agent-skill-engineering-reference/v1`: `knowledge provider unavailable`.
No provider text was fetched or used as authority.

## T4 completed verification — 2026-10-09

The branch was rebased onto `origin/main` at `ca8af74f6` with owner approval
on 2026-10-08; the only conflict was `workspace.toml` queue membership. The
plan pin still checks current and base freshness returned `ok`.

On the rebased tree, the controller earned the reds before repair:
assessment 1 failed/24 passed; bridge 8 failed/19 passed. Persistence (36)
and evidence store (110) were green.

The repair moved all lifecycle composition inside `append_semantic_records`
under the refreshed store lock, using a closed `lifecycle` data keyword with
three kinds: assessment, typed report replacement, and subject invalidation.
Retries are checked against the request, not by substituting committed
records. The current-assessment view has one store-owned implementation.
Four stale fixtures were corrected with recorded justification; reports are
persisted verbatim in `implementer-T4-final-repair.md`,
`implementer-T4-defect-repair.md`, `implementer-T4-d6-repair.md`, and
`implementer-T4-ready.md`.

Controller source inspection then found six defects that the passing tests did
not catch, each repaired with a failing-first test:

- D1: Slice 1 single-record writers skipped the lifecycle checker. A probe
  cleared a bridge failure live and made the log unopenable. It now refuses,
  and the store reopens.
- D2: the invalidation context accepted any review subject.
- D3: an invalidation retry was not checked against the request.
- D4: an assessment retry was not checked against the request.
- D5: the projection accepted any supported assessment's receipts and partial
  sets.
- D6: an unrelated supersession could piggyback on a legitimate frame.

Independent mutation proof is in `t4-mutation-ledger.md`. Every guard has a
single-property catching mutation. The adjudicated exceptions:

- Two tests (`test_d2_durable_subject_after_source_report_admits`, typed
  report retry) assert success. Under their mutation the code refused inside
  the test body. That is a runtime failure of the named property, so the
  controller counts it as a catch.
- Four multi-violation tests are caught only by a compound mutation. They are
  retained as defense-in-depth; each of their guards is proven by its own
  isolated case.
- MUT-062 is not isolable, because one filter feeds both the unpaired-receipt
  rule and completeness. Both rules are proven separately.
- MUT-021 was a no-op, and the redundant guard was removed.

Final restored baseline: assessment 31, bridge 50, persistence 36, evidence
store 110, contracts 54, subject selection 59, compat facade 56, and content
safety 66 all passed. `make lint-ruff lint-mypy`,
`tools/lint-pack-test-boundary.py`, and `git diff --check` passed. Runtime
hashes: `_evidence_store.py` `10528d8f…`, `_review_bridge.py` `192a15fa…`,
`_review_persistence.py` `f3c559d5…`, and `_review_assessment.py` `91cf01f4…`.

## T5 implementation and controller verification — 2026-10-09

T5 adds `_review_disposition.py` with two entry points.
`append_finding_disposition` is the typed write port. `review_readiness` is
the pure readiness query. The `finding-disposition` store lifecycle checks
capability scope `review/disposition` and binds the decision maker to an
`approval-record.v1` before any effect. The approval binding requires all of:

- decision `approved`, scope `review-disposition`, and an approval ID equal to
  the disposition's authority reference;
- identity and role equal to the disposition's decision maker;
- the current policy fingerprint, and a subject equal to `base.manifest_ref`;
- no superseding approval.

Every post-allow refusal pairs with the allow operation ID. Implementer
reports are persisted verbatim: `implementer-T5-0.md` (the TDD red),
`implementer-T5-report-1.md`, `implementer-T5-report-2.md`, and
`implementer-T5-report-3.md`.

Controller verification found five defects; each was repaired:

- A change to T2's `_has_closing_disposition` trusted any supplied `fixed-by`
  and broke three T2 cases. The file was restored byte-exact (`333d5f21…`),
  and verified closure now lives only in readiness.
- Readiness duplicated a weaker copy of the closure rules. It now has one
  store-owned verifier, `disposition_closes`, which the write path and replay
  share.
- A raw `approval-record.v1` batch could revoke approvals. Approvals are now
  admitted only inside disposition frames, live and on replay.
- A "fast path" skipped every T4 check for frames without a disposition. It
  was removed: bridge 50/50 again, and the single-record probe still refuses.
- An unauthorized local commit `a48b86ffe` was made by the implementer. It
  is left in place, and history is normalized at closeout. Nothing was pushed.

**Replay content-safety adjudication.** T3 had extended replay so that
headers and legacy receipts and supersessions also passed content-safety. That
went beyond Slice 1, which only schema-validates them on replay, and it pushed
Slice 1's accepted 10 s cold-rehydration bound over its limit. The plan
requires existing recovery behavior to stay compatible, so legacy records
return to the Slice 1 behavior. Every review-owned and approval record is
still content-checked on replay. The three T3 tests that pinned the removed
extension were deleted.

**Readiness scope assumption.** Readiness is decided per subject. A
`fixed-by` closes the old subject's finding by naming a fresh, fully assessed
replacement-subject report. Findings are not carried forward across subjects.

Controller run on the final T5 tree:

| Suite | Passed |
| --- | ---: |
| Disposition | 52 |
| Assessment | 31 |
| Bridge | 50 |
| Persistence | 33 |
| Evidence store | 110 |
| Contracts | 54 |
| Subject selection | 59 |
| Compat facade | 56 |
| Content safety | 66 |
| Cold-rehydration benchmark | 1 (14.86 s wall clock) |
| Acceptance benchmark | 1 |
| Loop engine | 257 |
| Roster bundle | 40 |
| Roster parity | 22 |
| Roster matrix | 4 |

Lint, mypy, and the pack-test boundary check passed. T4's earlier mutation
proof is historical evidence for the T4 hashes; its regressions pass on the
final store.

### T5 first mutation proof — repair required

An independent proof (`t5-mutation-ledger.md`) ran 84 single-property
mutations on hashes `6014d514…`/`7a3f7c28…`. Only 37 of the 53 cases were
proven. The proof found three brief-required guards with no code: an approval
whose decision is not `approved`, a decision-maker role mismatch, and a
replacement report ID on a repair-request or accept-risk. A probe showed each
one is admitted and makes the review acceptance-eligible.

The other gaps are test shape. Every `fixed-by` negative points at an
unpersisted replacement, so rule 5 refuses each variant before the guard it
names. Several negatives assert only a `denied-` prefix. Most
`disposition_closes` and readiness re-checks are unreachable from the current
fixtures.

These are correctness and security defects of this change, so T5 is
reopened. It must add the guards, give each guard a single-input negative
against an admitted baseline, assert exact denial codes, and remove duplicate
port prechecks. The mutation proof then reruns. T5 has no receipt.

### T5 second mutation proof — runtime defects found

The second independent proof (`t5-mutation-ledger-2.md`) ran 95 mutations on
hashes `670d6190…`/`668b5689…` and proved 78 of 79 cases. Its probes found
four runtime defects of this change:

- **R1:** the approval subject and policy binding is skipped when the
  supplied review subject differs from the disposition's subject. A probe
  admitted an accept-risk under the wrong subject and policy, and the review
  became acceptance-eligible.
- **R2:** eligibility is enforced only in the port. A store-direct
  disposition with no assessment is admitted.
- **R3:** an unreferenced approval rides along in a disposition frame without
  authority checks, and it revoked an earlier accept-risk.
- **R4:** an assessment's subject fingerprint is not bound to its source
  report's subject.

It also listed 20 reachable but untested guards, one two-mechanism case, and
13 unreachable defence-in-depth copies, each with its reason. The
defence-in-depth copies are approval and rule-5 re-checks over immutable
admitted records, plus one dead lookup branch; they are accepted as
proportionate. R1–R4 and the 20 single-input tests are dispatched as one
repair round. T5 has no receipt.

## T5 completed verification — 2026-10-10

The R1–R4 repair moved every disposition rule into one store owner. That
owner is shared by the lifecycle write path, replay, and `disposition_closes`.

- **R1:** the approval subject and policy binding is unconditional.
- **R2:** eligibility is owned by the store.
- **R3:** only the referenced approval may ride in a disposition frame.
- **R4:** an assessment's subject must match its report's subject.

The report is persisted at `implementer-T5-ready.md`. The controller made two
follow-up corrections:

- Test 065 accepted either of two outcomes. It now asserts the exact replay
  refusal `denied-disposition-no-assessment`. Mutation check: disabling that
  refusal reds the test; restored to hash `7132491d…`.
- The now-dead `_validate_disposition_eligibility` was deleted from the port.

The second-pass probes that had admitted R1–R3 now refuse:

| Probe | Refusal |
| --- | --- |
| R1 wrong manifest and policy under another subject | `denied-disposition-subject-mismatch` |
| R2 store-direct disposition with no assessment | `denied-disposition-no-assessment` |
| R3 approval ride-along | `denied-approval-authority-required` |
| Raw approval and disposition pair | `denied-approval-authority-required` |

Independent mutation proof is in `t5-mutation-ledger.md` and
`t5-mutation-ledger-2.md`, plus the implementer's per-test self-check in
`implementer-T5-0.md`. Thirteen re-checks over immutable admitted records are
accepted as defence-in-depth, with the reasons in ledger 2.

Final runtime hashes: `_evidence_store.py` `7132491d…` and
`_review_disposition.py` `0e7d92ef…`.

Controller run on the final tree:

| Suite | Passed |
| --- | ---: |
| Disposition | 105 |
| Assessment | 31 |
| Bridge | 52 |
| Persistence | 33 |
| Evidence store | 110 |
| Contracts | 54 |
| Subject selection | 59 |
| Compat facade | 56 |
| Content safety | 66 |
| Cold-rehydration benchmark | 1 |
| Acceptance benchmark | 1 |
| Roster bundle | 40 |
| Roster parity | 22 |
| Roster matrix | 4 |

Lint, mypy, the pack-test boundary check, and `git diff --check` passed. The
single-record bypass probe still refuses, and the store reopens. The
implementer's run of the full work-loop suite reported 2761 passed and 6
skipped; the controller reruns it at closeout.

## T6 first implementation — controller review — 2026-10-10

The implementer's first T6 pass (`implementer-T6-report-1.md`, local commit
`ce758e8b1`) is returned for repair. The commit was not authorized. An audit
confirmed nothing was pushed, the shared stash stack was untouched, and git
config did not change. History will be normalized at closeout.

VI-1019 was weakened: the `agentbundle`-unavailability proof was removed, and
the file-open spy and the in-subprocess corpus run are absent. Source review
also found adapter defects that silently clear legacy findings:

- **C1:** structural-clean is accepted without the legacy grammar.
- **C2:** adjudicated findings get a forced `unsupported-opinion`, so
  sustained findings stop blocking.
- **C3:** legacy presence reads a history field that real entries do not
  carry, and there is no legacy/structured agreement check.
- **C4:** a crash between the report and assessment writes is never repaired.
- **C5:** grammar-invalid findings are persisted instead of mapping to
  `unable`.
- **C6:** the return fields are not the closed set, and temp files can fall
  back outside the store root.

All of these are dispatched to the implementer. T6 has no receipt.

### T6 mutation proof — repair required — 2026-10-10

An independent proof (`t6-mutation-ledger.md`) ran 76 mutations on the
repaired adapter (`_review_compat.py` `672f027b…`, `loop-engine.py`
`c2bf88cc…`) and proved 28 of 34 cases. Its baseline probes found six runtime
defects:

1. Direct-clean accepts the sentinel plus a newline or a `Not checked`
   footer. Legacy refuses both, and the result makes review eligible.
2. Replay idempotency keys only on the source event ID. A later replay can
   acknowledge a clean result that was never stored.
3. The legacy payload digest is never compared.
4. Schema-invalid or unknown-major adjudicated findings persist as
   indeterminate; the spec requires `unable` with nothing persisted.
5. The adjudication text gets no content-safety check. A late refusal leaves
   a report with no assessments.
6. `structured_present` is hard-coded.

It also found test defects:

- The contracts spy watches `packs/contracts/delivery/`, not the repository's
  `contracts/delivery/`.
- The authority-isolation test never calls the adapter, carries an
  always-true assertion, and skips instead of failing.
- The harness fail-proof tests do not depend on the runtime.
- Thirty guards are reachable but untested.

The controller had already replaced the vacuous package-check fail-proof with
a real one (run with `-S` only, so the stub is importable and the check must
fire). T6 is reopened and has no receipt.

### T6 repair round — controller completion

The implementer's ledger-repair round is persisted at
`implementer-T6-report-3.md`. The controller completed two items:

- **T1 proof.** The report called T6-MUT-164 uncaught. The controller
  injected a read of `<repo>/contracts/delivery/review-report.v1.schema.json`
  into `_review_compat.py`. `test_vi1019_self_containment` failed with the
  spy message naming that path. The file was restored by inverse edit, with
  its hash re-verified.
- **D3.** The adapter now calls loop-cohort's `_review_payload_digest` and
  compares it with the recorded digest. The check applies when the source is
  the latest recorded legacy review and the result is clean. Cohort state
  keeps only the latest digest, and findings digests cover adjudication
  fingerprints the adapter does not receive; those cases are matched by
  legacy event. Clean-state test fixtures now carry the independently
  computed legacy digest. Two new tests, an unrelated digest and a wrong-form
  digest, both red when the comparison is removed; restored to hash
  `d1bb92e8…`.

Controller run on this tree:

| Suite | Passed |
| --- | ---: |
| Compat | 65 |
| Disposition | 105 |
| Assessment | 31 |
| Bridge | 52 |
| Persistence | 33 |
| Evidence store | 110 |
| Contracts | 54 |
| Subject selection | 59 |
| Compat facade | 56 |
| Content safety | 66 |
| Both benchmarks | 1 each |
| Roster | 40, 22, and 4 |

Lint, mypy, the pack-test boundary check, and diff-check passed. A second
independent T6 mutation proof is running.

### T6 second mutation proof and controller restructure

The second proof (`t6-mutation-ledger-2.md`) proved 61 of 65 cases. It
confirmed four first-pass defects fixed and two partly fixed. It found new
defects:

- N1: the conflict return carried an extra key.
- N2: a partial write, then a raise.
- N3: escaped control characters were persisted.
- N4: a same-status, different-findings replay raised the wrong refusal.
- N5: a missing root raised instead of returning `unable`.

It also listed 18 reachable but untested guards.

The controller restructured `_review_compat.py` to validate everything, then
write. All of the following happen before the first write:

- the form gate;
- raw and adjudication content safety;
- the store-root check;
- the legacy grammar;
- schema validation of every finding (unknown major, missing field, wrong
  type, and duplicate ID → `unable`);
- full report validation;
- content safety over every decoded string value, because JSON
  re-serialization re-escapes control characters;
- building and validating every assessment.

A replay must match the stored report body and every stored assessment, or
it raises `ReviewCompatRefused("denied-compat-source-event-conflict")` with no
write. `legacy_state` is deep-copied, and `structured_present` is read from
the store on every path. The test that pinned missing-field →
`indeterminate`, against the spec row, now expects `unable` with nothing
persisted.

Re-running the second-pass probes now gives `unable` with nothing stored for
all of these: non-exact clean text, schema-invalid findings, a credential, an
escaped control character, a duplicate ID, a missing or non-directory root,
and missing criteria. Conflicting replays raise, and the caller's legacy
mapping stays unchanged. `test_review_compat.py`: 65 passed. A test-only
round now adds single-input tests for every remaining guard.

### T6 test round — controller additions

The test-only round is persisted at `implementer-T6-report-4.md` (76
tests). The controller added seven cases for behaviors that round skipped:

- a JSON-escaped control character in a finding field;
- a JSON-escaped control character in an authority ref;
- a duplicate finding ID;
- a wrong-type field;
- a missing store root and a store root that is a file, under direct-clean;
- a same-status replay with a changed finding.

Mutation results:

- Removing the decoded content-safety check reds the authority-ref case. The
  finding-field case is also refused by the report contract validator, so two
  mechanisms guard that input.
- Removing the duplicate-ID refusal reds its case.
- Removing the store-root directory check reds both root cases.
- Reducing the conflict test to a status comparison reds the same-status
  case.

The runtime was restored to hash `df6818a8…` each time.
`test_review_compat.py`: 83 passed.

## T6 completed verification — 2026-10-10

The final independent proof (`t6-mutation-ledger-3.md`, run on Sonnet) ran
103 single-property mutations on `_review_compat.py` `df6818a8…` and the
`loop-engine.py` caller `c2bf88cc…`. It proved 79 of 83 cases and found no
runtime defect. It confirmed defects N1–N5 fixed and pinned.

The four unproven cases have an unreachable shape:

- Two VI-1012 journeys prove AC-0001 through the published ports, without
  the adapter.
- Two VI-1019 fail-proofs prove the harness checks themselves.

The controller then added tests for three reachable groups:

- deterministic report and assessment transaction IDs;
- report-contract refusal (an empty role gives `unable` with nothing stored);
- identical-replay idempotency (no new transaction).

Mutating either transaction ID or the report contract reds the new tests.
The crash-repair skip is a two-mechanism guard: the store's identical-retry
rule also returns the committed transaction, with authority re-checked.

The remaining items are accepted with reasons:

- `review_policy` is unused by design, and is documented in the signature.
- The assessment-contract check is defence-in-depth behind the
  finding-contract checks.
- The extra-stored-assessment check is unreachable while the report body is
  equal.

The VI-1019 spy fail-proof now builds a fake repository under `tmp_path`
instead of reaching above `packs/core`; the pack-test boundary lint flagged
the earlier form.

Final controller run:

| Suite | Passed |
| --- | ---: |
| Compat | 85 |
| Disposition | 105 |
| Assessment | 31 |
| Bridge | 52 |
| Persistence | 33 |
| Evidence store | 110 |
| Contracts | 54 |
| Subject selection | 59 |
| Compat facade | 56 |
| Content safety | 66 |
| Both benchmarks | 1 each |
| Loop engine | 257 |
| Loop cohort | 257 |
| Roster | 40, 22, and 4 |

`make lint-ruff lint-mypy`, `tools/lint-pack-test-boundary.py`, and
`git diff --check` passed.

T6 evidence: VI-1012 synthetic reviewer, VI-1013 closed compatibility corpus
with crash and replay, VI-1018 authority isolation using the real
engine/cohort scripts, and VI-1019 clean-environment self-containment
(`-I -S`, package unavailability, file-open spy, and static import check).

## Controlled contract amendment — 2026-10-10

After T6, the owner chose to amend Slice 2 rather than perform the
review-authority cutover in this delivery. The decision and the evidence shown
with it are recorded at `owner-amendment-2026-10-10.md`.

The separated follow-on was materialized through `work-intake` →
`intake-intent` as Draft intent
`docs/product/intents/FEAT-0036-review-authority-cutover.md` (ordinal
allocated by `intent_ordinal.py`). It is registered non-dispatchable in the
`ini-002` shaping backlog, with a hard dependency on this spec.

`contract-amendment` fired from `CODE-IMPLEMENTATION` to `SPEC-PLAN-DRAFTING`
at sequence 8, amendment ID `c8e6f630…`. It was fired without
completed-evidence references because no task had a wave-advanced completion:
all seven tasks share wave 0. T1–T6 completion evidence remains in this
ledger and the per-task mutation ledgers.

The amendment changes these protected spec sections:

- Scope: the cutover is excluded and the current review path stays
  authoritative.
- Durable Outputs: the maintainer-procedure closeout now requires guidance
  that gains no reviewer-specific procedure, retires no authority, and matches
  its projections.
- Testing Strategy and AC-0010: bounded to the review-boundary runtime
  modules, the review-policy data shape, and the change to the canonical
  work-loop policy surface.
- AC-0013: review authority added to the unchanged set.
- Terminal Intent: the cutover is excluded.
- Follow-ons: FEAT-0036.

Working-material Outcome text was corrected to match. In the plan, the
authority constraint, the Durable-output map, and Rollout were updated. T7 was
rewritten as a durable-output refresh: VI-1017 removed, and VI-1014 rebound to
the amended AC-0010. T1–T6 task sections are byte-identical, checked by hash
before and after. The spec and plan are back at `Draft`/`Drafting`.
`spec-ready` fired to `SPEC-PLAN-REVIEW` at sequence 9.
`lint-spec-status.py --root .` passed. Round-3 adversarial and secure-design
reviews are dispatched.

### Amendment pre-EXECUTE review — rounds 3 and 4

Round 3, secure-design: the raw report was persisted (4,305 bytes,
`sha256:298f27e6…`). The strict raw classifier returned `invalid`
(`footer-bullet-malformed`), because rationale prose followed the `Not checked`
footer. It was not adjudicated and not treated as clean. The reviewer is
re-dispatched in round 4 with the strict output grammar.

Round 3, adversarial: the raw report was persisted (2,319 bytes,
`sha256:8411c5cc…`) and classified `findings` (2). The independent
adjudication was persisted (2,303 bytes, `sha256:ea4eeba7…`), and strict
inspection returned `findings`:

- **Sustained Blocker (fingerprint `8591f361…`):** AC-0013's new
  review-authority element had no named VI.
- **Refuted Concern:** architecture §10 places classifier retirement after
  parity and assigns future ownership; it does not promise the cutover in this
  slice.

`findings-remain` fired at sequence 10. The repair took the
`repair-the-artifact` rung:

- AC-0013's Testing Strategy entry now names legacy review-gate decisions.
- T7 adds VI-1020: the real engine and cohort review gate must give identical
  decisions with and without the compatibility adapter.
- VI-1020 is wired into T7's Done-when and the Durable-output map, and T7's
  behavior line now names review isolation.

The T6 section holding VI-1018 is unchanged, and T1–T6 hashes were verified.
`spec-ready` fired at sequence 11. Round 4 dispatched both reviewers.

### Amendment approvals and re-admission — 2026-10-10

| Review | Round | Result | Raw report | Adjudication |
| --- | --- | --- | --- | --- |
| Adversarial | 4 | One sustained minor: the plan dropped "review" from the closeout condition | `sha256:fe726431…` | `sha256:e8f46a36…` |
| Adversarial | 5 | Direct clean, byte-exact | 26 bytes, `sha256:49677814…` | none needed |
| Security | 4 | Adjudicated clean: all three findings refuted | `sha256:c888484f…` | `sha256:fa7424c9…` |

- **Round-4 adversarial:** `findings-remain` fired at sequence 12; the
  wording was repaired, and `spec-ready` fired at sequence 13.
- **Round-4 security refutations:** disposition authority-before-effect is
  already a T5 Done-when and VI-1010 obligation. Downstream `UntrustedData`
  handling is already the delivery-content-safety architecture invariant. The
  authority-by-implication bar is already AC-0013 plus Scope.
- **Engine and approvals:**
  1. `reviewers-clean` fired at sequence 14.
  2. The owner approved the amended spec. `Status: Approved`, plus the
     "2026-10-10: spec approved by owner" Changelog entry; `spec-approved` fired
     at sequence 15.
  3. The owner approved the amended plan. `Status: Approved`, plus the
     "2026-10-10: plan approved by owner" entry in the same edit;
     `plan-approved` fired at sequence 16.
- **Baseline:** `approve-plan` pinned spec `1cc08dba4e9a…` and plan
  `227b6286db81…`. `schedule` placed T1–T7 in one wave, and `plan-locked`
  fired at sequence 17, back to `CODE-IMPLEMENTATION`.
- **Statuses and receipts:** the spec is `Implementing` and the plan is
  `Executing`, and `plan check-current` is OK. Because the amendment cleared
  the schedule, the T1–T6 dispatch receipts were re-recorded from their
  completed evidence. T7 is dispatched to a sequential implementer.

## T7 completed verification — 2026-10-11

The T7 implementer report is persisted at `implementer-T7-report.md`. After
the owner approved the rebase, the branch was rebased onto `origin/main` at
`7798533dd`. Main had released Core 3.0.3, so the owner-approved version is
3.1.0, in both pack.toml and plugin.json. The changelog entry is
`## [core][3.1.0] — 2026-10-11`; it is free-standing, newest first, and
carries outcome-led Highlights.

The branch was squashed into one conventional commit carrying the `Spec:`
trailer. `make build-self` then ran on the clean tree, and the regenerated
`.agents` and `.claude` work-loop projections were folded into that commit.
`catalogue verify` is ok, and `catalogue lint --deep` reports 75 findings,
the same as main's baseline.

Controller mutation checks on the guarded files themselves:

- A reviewer-role literal in `_review_compat.py` reds the role-literal test.
- An extra reviewer-role mention in `references/reviewer-roster.md` reds the
  pinned skill-count test.
- Adding `prompt` to the closed policy shape initially survived: the test
  compared against a policy whose fingerprint did not match its subject, so
  every input was refused for that reason. It now has a positive control,
  covers six procedure fields, and asserts
  `denied-review-policy-unknown-field`. The same mutation now reds it, and
  `_review_selection.py` was restored to `333d5f21…`.

Each file was restored by inverse edit, with its hash re-checked.

Post-rebase controller run:

| Suite | Passed |
| --- | ---: |
| Boundary policy | 9 |
| Step-0 eval contract | 4 |
| Compat | 85 |
| Disposition | 105 |
| Bridge | 52 |
| Evidence store | 110 |
| Roster | 40, 22, and 4 |

`make lint-ruff lint-mypy`, the pack-test boundary check, and
`lint-spec-status` passed. The full work-loop suite is running.

### Version correction — 2026-10-11

The roster suite's mechanical bump check
(`test_two_sided_prune_closure_invariant.py::test_pack_delivery_contract_is_complete_and_version_increased`)
requires a patch bump when no primitive directory is added. This slice adds
modules inside the existing work-loop skill and no new primitive, so the
required version is 3.0.4, not 3.1.0. The owner approved 3.0.4 after this
evidence was shown. pack.toml, plugin.json, and the changelog heading
`## [core][3.0.4] — 2026-10-11` now agree, and the test file passes (47).

## GATES and review entry — 2026-10-11

On commit `1d4d0b7e1`, rebased on `origin/main` `7798533dd`:

| Suite | Result |
| --- | --- |
| Full work-loop | 2861 passed, 6 skipped, 70 subtests (16 min 7 s) |
| Core hooks | 21 passed |
| Core integration | 2 passed |
| Core pack | 416 passed |
| adapt-to-project | 29 passed |
| author-brief | 3 passed |
| author-delivery-brief | 171 passed |
| bug-fix | 5 passed |
| close-work | 341 passed |
| contract-acquisition | 1 passed |
| explain-diff | 45 passed |
| intake-intent | 50 passed |
| new-spec | 267 passed, 79 subtests |
| project-knowledge | 348 passed |
| receive-brief | 3 passed |
| repository-exploration | 47 passed |
| repository-grounding | 105 passed, 2 skipped |
| work-intake | 879 passed |
| workspace-status | 277 passed, 1 skipped |
| `tests/roster` | 2090 passed, 7 skipped, 56 subtests |

The roster count is after the 3.0.4 version correction: the version test
failed once, was fixed, and its file then passed (47).

Static gates also passed: `make lint-ruff lint-mypy`, the pack-test boundary
check, `git diff --check`, `lint-spec-status`, `catalogue verify`, and
`catalogue lint --deep` (75 findings, main's baseline).

`check --phase wave-exit` passed. `wave-complete` fired at sequence 18 and
`gates-clean` at sequence 19, entering `CODE-REVIEW`. The post-gates
adversarial review, round 1, is dispatched; the security and quality-engineer
reviews follow once the adversarial requirement is satisfied.

## Post-gates review — adversarial round 1

The raw report was persisted (3,021 bytes, `sha256:5c350480…`). The
independent adjudication was persisted (2,507 bytes, `sha256:1a6ff4a7…`), and
strict inspection returned `findings`, with fingerprints `f7465129…` and
`fc85bada…`. Both findings were sustained:

- **Concern:** the Compatibility corpus test never asserted that the
  indeterminate rows persist their result.
- **Nit:** the Obligation truth table's Row 5 does not name `indeterminate`.

`wave reopen` superseded 7 records, and `findings-remain` fired at sequence
20. The Concern was repaired with `repair-the-artifact`: the corpus test now
reads the store, and requires zero stored reports for `unable` rows and
exactly one report with the expected status for every other row. A mutation
that skips the indeterminate write reds both indeterminate rows; the adapter
was restored to its baseline hash.

The Nit is deferred with its citation (`spec.md:160`). Changing it needs a
protected-section amendment, the behavior is already tested, and Nits are
never auto-fixed. It will be recorded in the verdict as `deferred`.

The review repair took no implementer dispatch. The corpus-test assertion was
a controller fix of 30 lines or fewer, under the skill's FIX step 2. The
cohort accepts only `no-implementer-installed` and `human-directed` as decline
reasons, and neither is true. So all seven tasks were re-recorded with
`--receipt`, re-asserting their original sequential-implementer delivery.

## Post-gates review — adversarial round 2

The raw report was persisted (1,704 bytes, `sha256:ddfbf5a9…`). The
independent adjudication was persisted (2,032 bytes, `sha256:86d43b4b…`), and
strict inspection returned `findings`. One Blocker was sustained, fingerprint
`2404f0c2…`: the adapter admits `structural-clean` → clean, an input class
outside the closed Compatibility corpus. That violates AC-0011's rule that
no other class is admitted.

`wave reopen` superseded 7 records, and `findings-remain` fired at sequence
23. The repair takes the conforming alternative and amends no protected
text: `structural-clean` leaves the adapter's closed form set, so it is
refused by the out-of-corpus gate. The result is `unable`, nothing is
persisted, and nothing is acknowledged. A legacy structural-clean record is
therefore not reconciled by the Slice 2 adapter. The repair is dispatched to
a sequential implementer.

The repair is in place. `_CLOSED_FORMS` is now `{direct-clean, findings,
adjudicated}`, and `_classify_structural_clean` and its dispatch branch are
removed. One parametrized test proves that a structural-clean event, with
clean or findings text, is refused: `unable`, nothing stored, and not
acknowledged, even when the legacy digest matches.

Other test changes:

- The corpus content-safety row now uses an in-corpus form.
- The temp-dir tests now use the findings form.
- Two tests whose guards were removed or exactly duplicated were deleted:
  T4-031 is covered by the D1 byte-equality tests, and T4-194 by
  `test_d3_clean_digest_mismatch_is_divergent[wrong-form-digest]`.

The implementer used `git checkout` on its own owned file to undo a scratch
mutation. Everything had been committed beforehand, so only that file's
in-progress edits were reverted; they were re-applied. The controller
verified that only the two owned files and this ledger differ from `HEAD`.

Controller mutation check: re-admitting `structural-clean` reds
`test_c1_structural_clean_is_refused[clean-text]`; restored by inverse edit,
hash verified.

| Suite | Passed |
| --- | ---: |
| Compat | 83 |
| Boundary policy | 9 |
| Disposition | 105 |
| Evidence store | 110 |

Lint, mypy, the pack-test boundary check, and diff-check passed. The
implementer report is persisted at `implementer-T6-structural-clean.md`.

## Post-gates review — round 3 (adversarial, security, and quality engineer)

Adversarial round 3 returned a direct clean: 26 bytes, `sha256:49677814…`,
classified `clean`. The adversarial requirement is satisfied.

Security round 3:

- **Raw report:** 3,878 bytes, `sha256:1fdec6e4…`, with a `Not checked`
  footer.
- **Adjudication:** 3,125 bytes, `sha256:629cf88c…`. Strict inspection
  returned `invalid` (`indeterminate-present`).
- **Refuted:** S-1, the `mkdtemp` write in a fresh directory, is controlled
  elsewhere. S-2, the `disposition_closes` re-check gap, is enforced at write
  and on replay.
- **Indeterminate:** S-3 needs the owner's call on severity. The defect is
  confirmed: a lone surrogate in untrusted legacy text raises
  `UnicodeEncodeError` instead of returning `unable`.
- **Owner direction (2026-10-11):** treat S-3 as a Concern and fix it now.
  This is an owner choice, not a machine-checkable evidence retry, so it is
  recorded here, and the security reviewer re-runs after the fix.

Quality engineer round 3, including the whole-spec pass:

- **Raw report:** 3,948 bytes, `sha256:8676f8ef…`.
- **Adjudication:** 4,504 bytes, `sha256:d8d08376…`, classified `findings`.
- **Sustained (fingerprints `4bb8c723…` and `b9573b94…`):** F-1, no
  goal-based VI-1012 journey closes a supported material finding through
  accept-risk; and F-2, a duplicate role-literal check diverges from VI-1014's
  registry.
- **Refuted:** F-3, a copied `_normalize_state` helper, and F-4, comment
  placement.

`wave reopen` superseded 7 records, and `findings-remain` fired at sequence
26. S-3, F-1, and F-2 are dispatched to one sequential implementer.

### Round-3 repair verified

The implementer report is persisted at `implementer-review-r3-repair.md`. The
fixes:

- **S-3:** `UnicodeEncodeError` on untrusted raw or adjudication text now
  returns `unable`, with nothing stored.
- **F-1:** a goal-based VI-1012 journey closes a supported material finding
  through accept-risk using only published ports. The contradicting receipts
  stay active.
- **F-2:** the duplicate role-literal test is removed.

Mutation proof: removing the guard reds all three S-3 cases, and forcing
`disposition_closes` to False reds the F-1 journey. Both runtime files were
restored by inverse edit.

The implementer made one unauthorized local commit (`cfa9ac318`), and auto
mode flagged a git action. The controller audited the reflog: one commit
only, with no reset, checkout, stash, or push. The commit was folded into
the single feature commit, and a leftover history comment in the test file
was removed.

Controller run: compat 86, disposition 105, boundary policy 9, evidence
store 110. Lint, mypy, the pack-test boundary check, diff-check,
`make build-self`, and `catalogue verify` passed.

## Post-gates review — round 4 and closeout — 2026-10-11

| Review | Round 4 result |
| --- | --- |
| Adversarial | Direct clean |
| Quality engineer | Direct clean |
| Security | One concern, refuted as unreachable |

The security concern was that `decide_review_obligation` does not re-verify
approval authority. It is unreachable: the only production caller passes no
dispositions and re-verifies closure through `disposition_closes`. The raw
report hash is `1e5a18c1…` and the adjudication `e87ef08a…`, classified
`clean`. Every warranted reviewer is clean or adjudicated clean, and the one
Nit (`spec.md:160`) is deferred with its citation.

### Completion handoff

**Delivery:** `structured-review-boundary`, run
`accb0133-8ca5-414a-a831-41a1bd9f35c4`. Authority: the spec and plan
approved by the owner on 2026-10-10, after the owner-authorized amendment
(`owner-amendment-2026-10-10.md`).

**Implemented scope:** T1–T7. All 16 ACs are checked. The spec is `Shipped`
and the plan is `Done`. The workspace entry moved to `ini-002` shipped.

**Durable outputs:**

| Output | Destination | Evidence |
| --- | --- | --- |
| Interface compatibility | six review schemas under `contracts/delivery/`, registered in `contracts/README.md` and `REGISTRY.md` | roster bundle 40 |
| Current architecture | `work-loop-review-disposition.md` and `acceptance-centered-work-loop.md` | name the shipped modules, the compatibility state, and the FEAT-0036 cutover |
| Maintainer procedure | the canonical work-loop skill, unchanged apart from the new modules and their projections | VI-1014 pinned counts; `catalogue verify` ok |
| Release history | `docs/product/changelog.md` `## [core][3.0.4] — 2026-10-11`, with Highlights | pack.toml and plugin.json both 3.0.4 |

The Highlights verdict is yes: consumers can add a conforming reviewer
without changing work-loop code.

**Non-goals and follow-on:** FEAT-0036, the review-authority cutover, is a
Draft intent and is not queued.

**Unresolved:** none in scope. The human merge gate is pending.

**Pull request:** none opened and none offered; the owner prohibited a PR and
any external action for this session.

**Verdict record:** `review-verdict.md`, state `READY_WITH_RESIDUAL_RISK`.

## Landing — 2026-10-11

The owner authorized landing: update to main, dispatch remote CI, open the PR,
fix CI if it breaks, and squash-merge when green. Main had released its own
Core 3.0.4 (#1543), so this release is **3.0.5**, a patch above it. pack.toml,
plugin.json, the changelog entry `## [core][3.0.5] — 2026-10-11`, the
workspace shipped comment, and the verdict label now say 3.0.5. Earlier
sections above record 3.0.4 because that was the version when they were
written.

One mistake happened during the rebase. A chained `git add -A && git commit
--amend` ran while the rebase was stopped on conflicts. It rewrote a local
copy of main's tip, with the conflict markers staged into it. Nothing was
pushed. The rebase was aborted, which returned the branch to its own commit
`e6f865479`, and the rebase was redone step by step. The rebased commit's
parent is the real main tip, `36e524a41`.

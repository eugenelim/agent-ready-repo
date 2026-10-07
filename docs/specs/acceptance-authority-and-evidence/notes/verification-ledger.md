# Verification ledger: acceptance authority and evidence

Execution observations for the approved Slice 1 plan. This file is not
hash-pinned; it records how tasks are verified, not new obligations.

## Script-versus-schema parity (owner decision, 2026-10-01)

The canonical schemas in `contracts/delivery/` stay repository-only. Neither
`agentbundle` nor the Core pack ships them to adopters, and no work-loop script
reads them at runtime. Agents never write delivery records directly: trusted
work-loop scripts build every record from typed arguments, as `loop-engine`
already does for its state.

Every task that adds a module which builds or accepts a delivery record (T3a
through T7) therefore carries parity tests:

- each record the module emits validates against its canonical schema, using
  `jsonschema` at test time only; and
- the module's own validation refuses each schema-invalid case (an unknown
  authority-shaped field, a missing required field, an unknown
  `schema_version` major, an out-of-enum value) with a stable code.

The protected skill-copy set for AC-0013 is a constant in the scripts, with a
test pinning it to the work-loop projections `contracts/adapter.toml` declares
for the Core pack's surfaces. T9a's conformance run rolls these suites up as
the evidence for the Release history closeout: "Released pack versions contain
implementations that validate against the canonical contracts".

Shipping input schemas to the agent is deferred to the first slice that
accepts agent-written structured payloads.

## Benchmarks run inside the corpus (owner decision, 2026-10-01)

The AC-0018 harness takes 8.0 s for all 105 runs on a local M1 Max (p95 about
65 ms against the 2 s bound). The benchmarks are therefore ordinary pytest
tests in the work-loop pack suite, which `make test` already runs, so a
`test-corpus.yml` dispatch measures them on GitHub-hosted `ubuntu-latest` with
no workflow change. Each test asserts its bound, prints its measurement into
the job log, and writes results only under a temporary path. T9a records the
dispatched run's head commit SHA with the passing benchmark tests. The earlier
benchmark job, posture test, single-roster exception, and ADR draft were
dropped before commit.

T9a also confirms that `.github/workflows/test-corpus.yml` at the dispatched
run's head commit SHA is byte-identical to the default branch's copy. A
mismatch voids the benchmark evidence until the changed workflow passes the
CI security scanners. This replaces the round-12 scan-to-dispatch check and
carries a deferred round-13 security Nit.

T9a writes the dispatched run's ID, head commit SHA, the shard that ran the
work-loop pack suite, and the printed AC-0018 p95 and AC-0019 cold-rehydration
figures into this ledger, because the job log expires under the repository's
log-retention setting (deferred round-13 adversarial Nit).

Binding evidence: `test-corpus.yml` run 37339103075, head commit
`9fd5b5e6af1e43e15eba66e3f20f8730a88f10c0`, completed 2026-10-05 on
`ubuntu-latest`. All four shards passed. The workflow file at that commit is
byte-identical to the default branch's copy. Shard 2/4 ran the work-loop pack
suite:

- AC-0018: 1,000 criteria and 100,000 receipts, 5 warm-up runs and 100 timed
  runs. p95 was 101.2 ms and p50 97.7 ms, against the 2,000 ms bound.
- AC-0019: 1,000 criteria, 100,000 receipts, and 100,000 log frames rehydrated
  to 1,000 verdicts in 2.949 s, against the 10 s bound.

This replaces the earlier record of run 37096863910 at `d53bbc3af`. That run
concluded as a failure on shard 4/4, from the then-pending version bump and
workspace finding, and it predates the later evidence-store changes on the
rehydration path.

## T9a acceptance evidence map

Each criterion maps to the suites that exercise it. Pack-behaviour suites live
in `packs/core/tests/skills/work-loop/`; repository-level suites live in `tests/roster/`. Every runtime module's
records are also pinned to their canonical schemas by the roster parity suites
(`test_delivery_contract_bundle.py`, `test_security_primitives_schema_parity.py`,
`test_acceptance_schema_parity.py`, `test_delivery_subject_parity.py`,
`test_containment_attestation_parity.py`, `test_evidence_store_schema_parity.py`).
`test_t9a_conformance_rollup.py` proves the projected `.claude/` and `.agents/`
copies are byte-identical to the pack source and importable.

| AC | Evidence |
| --- | --- |
| AC-0001 | `test_policy_import.py::TestCanonicalizationCorpus` |
| AC-0002 | `test_policy_import.py::TestAtomicImport` |
| AC-0003 | `test_acceptance.py::TestEnvelopeProjection`; `test_policy_import.py::TestChangeClassification` |
| AC-0004 | `test_acceptance.py::TestChangeClassifier`; `test_policy_import.py::TestChangeClassification` |
| AC-0005 | `test_subject_projection.py::TestProviderParityAC0005` |
| AC-0006 | `test_subject_projection.py::TestSubjectAdmissionNegativesAC0006`, `::TestTraversalLimitsAC0006` |
| AC-0007 | `test_acceptance.py::TestVerdictEvaluation`; `test_compat_facade.py::TestAC0007DualEmitCorpus` |
| AC-0008 | `test_evidence_store.py::TestAllOrNoneVisibility`, `::TestChecksumAndReferenceCorruption`, `::TestIndexDeleteAndRebuild` |
| AC-0009 | `test_acceptance.py::TestFreshnessEvaluation`; `test_evidence_store.py::TestFreshnessAndContradiction` |
| AC-0010 | `test_security_primitives.py::TestCapabilityIntersection`, `::TestCapabilityGrantLifecycle`; `test_containment_broker.py::TestAttestationWithinGrant` |
| AC-0011 | `test_security_primitives.py::TestConfinedMutationHappyPath`, `::TestConfinedMutationAdversarial`; `test_compat_facade.py::TestAC0011Confinement` |
| AC-0012 | `test_process_safety.py` (all classes) |
| AC-0013 | `test_containment_broker.py::TestDeliveryControlPathGuard`, `::TestForgeryFixturesPerAdapter`, `::TestBrokerDeliveryControlRefusal`, `::TestProtectedRefForgery`, `::TestBrokerBypassForgery`, `::TestLaunchUntrusted`; `test_containment_attestation_parity.py` |
| AC-0014 | `test_content_safety.py`; `test_content_safety_boundary_matrix.py`; the content-profile refusals in `test_policy_import.py::TestAtomicImport` |
| AC-0015 | `test_content_safety.py` (no-payload and inert-data cases); credential-shaped correlation IDs redacted on denial in `test_containment_broker.py::TestBrokerAuditBoundary` and `test_process_safety.py::TestAuditSinkUnavailable` |
| AC-0016 | `test_compat_facade.py::TestAC0016ShadowOff`, `::TestAC0016ShadowOn`, `::TestAC0016FullTransitionSequence`; the engine and cohort suites in the full work-loop pack suite; the T9a real invocation below |
| AC-0017 | `test_policy_import.py::TestReverseReader`; `test_compat_facade.py::TestAC0017Governance` |
| AC-0018 | `test_acceptance_benchmark.py` (asserts p95 within 2 s); binding run: `test-corpus.yml` run 37339103075 at `9fd5b5e6a`, p95 101.2 ms |
| AC-0019 | `test_cold_rehydration_benchmark.py` (asserts within 10 s); binding run: `test-corpus.yml` run 37339103075 at `9fd5b5e6a`, 2.949 s |
| AC-0020 | `test_security_primitives.py::TestSecurityEventWriterAuthority`; `test_policy_import.py::TestWriterAuthorityRefusals`; `test_evidence_store.py::TestProducerCapabilityChecks`; `test_containment_broker.py::TestBrokerCapabilityFailures` |
| AC-0021 | `test_security_primitives.py::TestSecurityEvents`; `test_process_safety.py::TestAuditSinkUnavailable`, `::TestAuditEventOrder`; `test_evidence_store.py::TestAuditSinkBehavior`; `test_compat_facade.py::TestShadowAuditDurability`; `test_security_primitives.py::TestSingleAuditEmitter`; `test_containment_broker.py::TestBrokerAuditBoundary`; `test_audit_boundary_invariant.py` (all classes) |

The clean-environment fence (`test_t9a_clean_env_fence.py`) evidences the
Never-do rule that no `work-loop` runtime module imports outside the standard
library and its siblings, and that the projected scripts run where `agentbundle`
is not importable. The other Never-do rule, no change under
`packages/agentbundle/`, is a fact about this slice rather than a lasting
repository rule, so it is checked once here instead of by a permanent test:
`git diff --name-only origin/main -- packages/agentbundle` listed 0 files at
branch head `6616ba4f7` on base `c586b26cf` (2026-10-02). T9b re-runs it before
closeout.

## T9a real invocation

Recorded 2026-10-03 with the shipped scripts at `.claude/skills/work-loop/scripts/`
(byte-identical to the pack source), after the rewired shadow facade landed.
Each run used a throwaway spec in a fresh temporary Git repository. Commands
are shown with `<spec-dir>` for the absolute spec path. The spec, plan, and
cohort files were committed before `plan-locked`. Every command in both runs
exited 0.

```
python loop-engine.py init <spec-dir> --mode code --json
python loop-cohort.py init <spec-dir> --run-id <run-id>
python loop-engine.py transition <spec-dir> spec-ready
python loop-engine.py transition <spec-dir> reviewers-clean
python loop-engine.py transition <spec-dir> spec-approved
[write plan.md]
python loop-engine.py transition <spec-dir> plan-approved
python loop-cohort.py approve-plan <spec-dir> --expect-run-id <run-id>
python loop-cohort.py schedule <spec-dir> --expect-run-id <run-id>
[commit]
python loop-engine.py transition <spec-dir> plan-locked
```

### Run A: `WORK_LOOP_SHADOW_SERVICES=1`

Final legacy state: `CODE-IMPLEMENTATION` after `plan-locked`,
`transition_sequence` 5. The shadow folder `<spec-dir>/.shadow-acceptance/`
held:

- `shadow-evidence.log`: 5 evidence transactions, one per transition.
- `shadow-approval.json` and `shadow-initial-review.json`: the imported
  approval and initial plan review, checked against the cohort's approved spec
  and plan digests.
- `shadow-property.json`: the shadow acceptance property.
- `shadow-verdict.json`: derived verdict `supported` for criterion
  `shadow:legacy-plan-locked`, over 5 receipts.
- `shadow-security-events.jsonl`: 7 events, all `allowed`, with no divergence
  entry.
- `.gitignore`, which keeps the folder out of Git.

No `shadow-delivery-subject.json` was written. The engine rewrites its state
files at `plan-locked`, so the tree was no longer clean when the facade ran, and
subject projection refuses a dirty tree by design. That projection is optional
on the shadow path and does not feed the verdict.

### Run B: `WORK_LOOP_SHADOW_SERVICES` unset

The same commands, all exiting 0. Final legacy state: `CODE-IMPLEMENTATION`
after `plan-locked`, `transition_sequence` 5. No `.shadow-acceptance/` folder
was written.

### Comparison

The `engine-state.json` fields `schema_version`, `feature`, `mode`, `state`,
`last_event`, `last_event_context`, `transition_sequence`, and `gate_question`
were identical across both runs. Only `run_id` and `last_transition_at`
differed. The legacy engine made every decision in both runs; the shadow
services only wrote non-authoritative records beside it. The automated form of
this comparison, including stdout, stderr, cohort state, and the plan pin, is
`test_compat_facade.py::TestAC0016FullTransitionSequence::test_shadow_on_off_parity`.

## Pack eval harness

The `work-loop` skill is deliberately outside the Core pack's eval roster.
`packs/core/pack.toml` lines 49-50 record why: the skill is loaded broadly by
the plan, execute, and review discipline rather than by a narrow user prompt,
so no clean negative set can be written for it. The shadow services add no
prompt surface either; a maintainer opts in with `WORK_LOOP_SHADOW_SERVICES=1`.
Their behaviour is therefore covered by the pack and roster test suites listed
above, not by a new eval case.

## Shadow import has no envelope pin (owner decision, 2026-10-03)

The legacy approval pin in `state.json` holds only `approved_spec_hash` and
`approved_plan_hash`. It has never stored a reviewed-envelope fingerprint, so
the opt-in shadow facade has no current envelope to compare against. The owner
chose an explicit shadow-only exception. `import_policy` takes
`approved_envelope_fingerprint` as a required keyword with no default, so a
caller that skips the envelope comparison must say so by passing `None`. The
shadow facade passes `None` and states why at the call. Spec and plan digest
mismatches still refuse with zero records visible. The exception is safe only
because every shadow record is non-authoritative; any caller that grants
authority must supply a real envelope pin.

## Review retry cap override (owner decision, 2026-10-04)

The post-gates review hit its retry cap of five rounds with two sustained
findings. Both were on the same seam: broker and process events reached the
audit sink without the content-safety check, and their allow paths echoed sink
error text. Rounds three to six had each found the next uncovered call site on
that seam. The owner chose to override the cap for one more round, on the
condition that the fix close the whole class rather than the named sites. Every
shipped module now reaches a sink only through `emit_security_event`, which
returns a fixed message on any sink failure, and denials go through
`emit_denial_best_effort`, which redacts a refused correlation ID.
`test_security_primitives.py::TestSingleAuditEmitter` fails if any module
calls a sink directly.

A second override on 2026-10-04 followed round seven, which found that the
first sweep enforced the wrong rule: it checked that no module called a sink
directly, not that every refusal stored a redacted event. The owner chose to
fix the rule itself. `emit_security_event` now raises `SecurityEventRefused`
when the content-safety check refuses an event and plain
`AuditSinkUnavailable` when the sink fails. `emit_denial` retries only the
refused case, with the correlation ID redacted, and never retries a failing
sink. Writer-authority denials and all three untrusted-launch refusals now use
it. `test_audit_boundary_invariant.py` asserts one stored `denied` event for
each refusal at the four security boundaries.

A third override on 2026-10-04 followed the first post-gates security review,
which sustained 11 findings and refuted one: 2 Blockers, 6 Concerns, and 3 Nits,
including one downgraded from a Concern. They fall into four groups: untrusted
launch and grants, audit completeness after an allow event, the process
primitive, and file safety. The owner chose a single hardening wave covering all
11, each fix with a test that fails without it. A full re-review follows:
security first, then adversarial and quality-engineer. The refuted finding,
that confined-file stdin should share the bounded-bytes ceiling, stays refuted:
that mode keeps its own explicit per-call bound.

## Executable identity pinning (owner decision, 2026-10-04)

The process primitive verifies an executable through a no-follow, bounded,
regular-file descriptor before launch. The owner chose to pin by file identity
rather than run a private temp copy, because a relocated copy breaks binaries
that locate libraries or helpers relative to their own path. On Linux the
verified descriptor itself is executed through `/proc/self/fd`, so the kernel
runs the inode that was hashed. Elsewhere (macOS, other non-Linux POSIX hosts,
and Linux without a mounted `/proc/self/fd`) the original path runs after a
final no-follow check that its device and inode still match the verified file.
Accepted residual risk: on those hosts a window remains between that check and
exec. Exploiting it needs write access to the executable or to any directory
traversed to resolve its path, including symlink targets. The owner confirmed this wording on 2026-10-05. Running the
same inode does not pin its content; see "What the identity pin covers, on every host" under
Further process-primitive residuals below.

A fourth override on 2026-10-04 followed security review round 2, which found
no Blockers and upheld 5 Concerns and 1 Nit, and refuted 1 Nit. The owner chose
to fix all six in one wave. Each fix stays inside the current schemas; none adds
a `containment-attestation.v1` destinations field. CI run 37214031330 at
`8cdf5d88b` passed on every shard, which exercised the Linux `/proc/self/fd`
exec path that cannot run on macOS.

Security round 2 fixes, mutation-checked against the pre-fix code: the NUL,
post-allow error, and success-path group-kill tests in `test_process_safety.py`;
the attestation limit and destination tests and the child-grant trust,
expiry, and parent-chain tests; and the evidence-log lock symlink-swap and
inode-change tests plus the exclusive-create rollback test all fail without
their fixes. `TestAdvisoryLockConfinement::test_fifo_at_log_path_does_not_block`
also passes without the lock fix, because the store's earlier regular-file
check already refuses a FIFO log. It stays as a regression guard and is not
counted as evidence for the lock change.

A fifth override on 2026-10-04 followed security review round 3, which upheld
1 Concern and 3 Nits and found no Blockers. Across security rounds the counts
were 2 Blockers, 6 Concerns, 3 Nits; then 0, 5, 1; then 0, 1, 3. The fixes:
attestation `limits`, `network`, `children`, `roots`, and `principal_or_sandbox`
are now typed against the unchanged `containment-attestation.v1` schema, and any
exception in the attestation-versus-grant check refuses through the audited path.
Recovery records the evidence-log identity only when no-follow stats taken
before and after the read agree, and refuses to truncate otherwise. The
success-path group kill runs before the exited leader is reaped on hosts
with `os.waitid` and `WNOWAIT` (see the residual below). `cwd`,
`grant_id`, and `executable_identity` must be non-empty strings before any
filesystem call. Against the pre-fix code, 16 of the 17 new tests fail. The
exception is `network: {"allowed": "true"}`: the old code already refused it,
because the grant allows no network.

## Group kill on hosts without `waitid` (owner decision, 2026-10-04)

`os.waitid` with `WNOWAIT` can see that a process exited without reaping it.
On hosts that have it, the group kill that ends a launch signals the launch's
process group while the exited leader still reserves the group ID. The
primitive checks the leader's exit only after every pipe has closed, and every
exit after launch kills the group before any further work, so a refusal raised
before the tree settles kills the group before any reap. macOS
builds of Python 3.11 and 3.12 do not have it, and this repository supports
3.11. On those hosts a launch whose tree settled reaps the leader at exit
detection, and the group kill follows at once, whether the launch then
succeeds or is refused. The owner
accepted the remaining risk: another of the same user's process groups could
reuse the freed ID before the kill, or any user's group when the launcher runs
as root. The window runs from that reap to the kill. Pre-execute round 19
found the earlier wording described a refusal-path window the I/O rewrite
had closed. Round 20 found that redaction ran before the success-path kill,
so the kill now runs first; `test_refusal_after_settle_still_kills_the_group`
fails against the earlier order. Round 22 found that an interrupt
(`KeyboardInterrupt`, `SystemExit`) during the launch skipped the kill, so all
post-launch work, from the `Popen` call on, now runs under a guard that tries
to end the group, reap, and store a denial on an interrupt (best effort; see
the interrupt residual below);
`test_interrupt_during_io_kills_the_group` fails against the earlier code.
Round 23 found that this guard signalled the group a second time after a
refusal path had already reaped the leader. The group is now killed at most
once per launch, so it is never signalled after this code reaps the leader;
`test_refusal_signals_the_group_exactly_once` fails when the kill is
repeated. Round 24 found three narrower interrupt gaps; the kill flag is now
set after the kill, a launch stores at most one denial, and a late failure's
denial shares the allow event's operation ID
(`test_late_failure_denial_shares_the_allow_operation_id` fails against the
earlier code). The rest is the accepted "interrupts are best effort"
residual below. The owner confirmed this wording on 2026-10-05. The kill stays in place
there, because removing it would let a backgrounded child that remains in the
group outlive a successful launch.

A sixth override on 2026-10-04 followed security review round 4, which upheld
1 Concern and 3 Nits. All four came from validators that raised on an
unexpected type. The owner chose to close that whole class.
`validate_attestation_dict` and `validate_process_spec_dict` now never raise:
any exception refuses with a stable code. Every schema field is type-checked,
including booleans offered as integers, unhashable enum values, `limits: null`,
and `trace_coverage`. `test_validator_totality.py` runs every field of both
records through 15 wrong-type and edge values. It checks the validators and
both launch boundaries, and requires each refusal to be audited. All four of
its tests fail against the pre-fix code. Recovery on hosts without `fcntl`
now also refuses to replace a file whose identity differs from the one read.

A seventh override on 2026-10-04 followed security review round 5, which upheld
1 Concern and 2 Nits. The Concern was another exception path: a raising host or
issuer could leave `launch_untrusted` without an audit. The owner chose to guard
each launch boundary as a whole, not patch each call site.
`launch_untrusted` runs every pre-launch step inside one guard, so any exception
ends in an audited `denied-containment-check-failed` refusal.
`launch_safe_process` is now a guard around the launch steps: any exception
other than `ProcessDenied` becomes an audited `ProcessDenied`. Every stored
event's correlation and operation IDs are non-empty strings, with a fixed
placeholder otherwise. The durable shadow sinks refuse NaN, so the event log
stays valid JSON. A present-but-null `network`, `children`, `max_bytes`, or
`timeout_s` is now refused, so every attestation field really is type-checked.
`test_validator_totality.py` adds raising hosts and issuers and schema checks
on every stored event. Its new cases fail against the pre-fix code.

## Further process-primitive residuals (owner decision, 2026-10-05)

Pre-execute review rounds 14 to 26 of the contract amendment that records
these risks in the spec found three more residuals, and the owner accepted
all three on 2026-10-05.

- What the identity pin covers, on every host. The pin hashes the bytes read
  from a read-only descriptor, once, before launch. Linux with `/proc/self/fd`
  exec then runs that inode, and other hosts run a path whose device and inode
  still match; neither pins the content. So the pin does not protect the
  executable's bytes after the check, or anything it loads by path: the `#!`
  interpreter, the dynamic loader, shared libraries, and interpreter modules.
  A principal who can write the executable, a file it loads, or any directory
  searched to find either can make unchecked code run with the launch's
  arguments, environment, and grant.
  Rounds 14 to 16 found cases of this one at a time (a rewrite before exec, a
  `#!` script read after exec, a native binary rewritten while it runs on
  macOS, a library loaded by path), so the owner accepted it as one general
  statement on 2026-10-05. Closing even the first case on Linux would mean
  running a sealed in-memory copy, which breaks binaries that locate files
  through their own path, as the private temp copy did.
- A child that leaves the launch's process group, on every host. The tree kill
  signals the process group, so a descendant that calls `setsid` or `setpgid`
  survives it. The standard library has no portable way to track such a
  descendant. The primitive sees only its own end of each pipe. If stdout or
  stderr is still open, or stdin input is still waiting to be written into
  the pipe, at the launch timeout, the launch is refused as an audited timeout
  within a fixed bound. Input written into the pipe counts as delivered
  whether or not anything reads it.
  Otherwise the launch can succeed while the descendant keeps running,
  including one that keeps the read end of a stdin whose input was all
  delivered. Pre-execute rounds 19 and 20 found that case and its wording,
  and the owner confirmed this wording on 2026-10-05.

Pre-execute rounds 17 and 18 found that the primitive treated the leader's
exit as the whole tree finishing. A tree whose leader exited early, with a
descendant holding stdout, stderr, or stdin input still waiting to be written
into the pipe past the timeout, was
reported as success. A refusal could also hang while a blocked stdin write
held the pipe's lock, for as long as an escaped descendant lived. And a
descendant flooding past the output cap after the leader exited got a
truncated success. The owner chose to fix all three on 2026-10-05. One thread
now drives all three pipes with non-blocking I/O against the deadline. The
tree has finished only when this side of every pipe has closed (output at
EOF, stdin input delivered) and the leader has exited.
A capped capture is a truncated success only if the tree finishes within
0.2 s, and is refused otherwise. Every return path closes this side of the
pipes before a bounded reap. Five tests fail against the earlier code, one of
which forces the fallback used where `os.waitid` is missing:
`test_early_leader_exit_with_pipe_held_past_timeout_is_a_timeout`, both cases
of `test_stdin_holder_past_timeout_is_a_timeout_and_returns_promptly`,
`test_cap_flood_by_a_descendant_after_leader_exit_refuses`, and
`test_early_leader_exit_timeout_holds_without_waitid`. The owner confirmed the
resulting wording of this residual and the group-ID reuse residual on
2026-10-05.

- Interrupts are best effort, on every host. On a `KeyboardInterrupt` or
  `SystemExit` (which any process running as the launcher's user can cause by
  signalling it), the primitive tries to kill the group, reap the leader, and
  store one denial. Pure Python cannot make every moment interrupt-proof, so
  this is not guaranteed: an interrupt at any point during a launch can leave
  the allowed launch without its terminal audit event and, once the child has
  been forked, the tree running. Pre-execute rounds 24 to 26 found such gaps, and the owner accepted the rest as best
  effort on 2026-10-05 after the cheap ones were closed.

Rounds 14 and 15 also corrected the wording of the two 2026-10-04 residuals
above, and the owner confirmed both acceptances still hold.

## Shadow `.gitignore` is the audit store's bootstrap (owner decision, 2026-10-06)

Post-gates adversarial round 10 found that auditing the shadow folder's
`.gitignore` wrote the security-event log into the folder before the
`.gitignore` existed, so a refused or interrupted create left an un-ignored
file behind. The owner overrode the retry cap again and chose to exempt it.
The `.gitignore` is now created first and is not audited, and the
runtime-security-primitives page names it with the audit-log append as the
two unaudited writes. `test_refused_gitignore_leaves_no_unignored_shadow_file`
fails against the earlier code. The process primitive's module docstring now
states the narrowed process-group guarantees.

Post-gates round 11 asked whether this exemption narrows AC-0021. The owner
decided on 2026-10-06 that it does not: until the `.gitignore` exists, the
shadow audit store is unavailable, so a refused create falls under AC-0021's
fail-closed branch (a stable denial code, no effect success, and no claim
that an event was stored). The shadow sink now refuses any event while the
`.gitignore` is missing, and `test_sink_refuses_until_the_gitignore_exists`
fails against the earlier code.

## Quality-engineer review fixes (owner decision, 2026-10-06)

The quality-engineer review and post-gates security round 12 raised 15
findings. The adjudicator sustained 12 and refuted 3: the adapter-label
parametrization, a pinned AC-0001 baseline, and per-stage shadow
diagnostics. The owner overrode the retry cap and chose to fix all 12 in
one wave:

- the evidence store makes a same-identity retry idempotent and refuses a
  conflicting reused receipt or transaction ID, in memory and on replay, and
  bounds its advisory-lock wait (`denied-lock-timeout`);
- the subject projection hashes each file through the confined opener with
  the remaining byte budget, refusing an oversized or unsizable file without
  reading past the bound;
- the shadow audit store counts as initialised only when its `.gitignore`
  holds exactly the bytes `*\n`;
- tests now pin the AC-0002 import bindings (scope, envelope, intent, both
  digests), the AC-0017 reverse-read digests, the AC-0007 verdict through the
  persisted path with a planted cached verdict ignored, the AC-0016 shadow-on
  verdict and its absence of divergence, and the AC-0018 and AC-0019 verdict
  distributions;
- the stale CI comments, the misnamed broker-refusal test class, and two dead
  test helpers are corrected.

Each new test was checked against a mutation of the behaviour it guards.

## Evidence-store retry and concurrency fixes (owner decision, 2026-10-06)

Quality-engineer round 2, security round 13, and adversarial round 14 found
that the previous wave's idempotent retry skipped the authority check and
audit, and that two open store instances could each write a duplicate that
replay then refused, making the store unreadable. The owner overrode the retry
cap and chose to fix all of it:

- every append, a retry included, passes the producer-authority check and
  stores its allow first; an identical retry then writes nothing;
- the reuse decision is retaken against the durable log under the same lock as
  the write, so a stale instance cannot admit a duplicate;
- replay skips a frame that reuses an identity already seen, so the first
  admitted record stays authoritative and the store always opens (AC-0008
  rejects only checksum or reference corruption);
- a supersession retry is idempotent only under the same acceptance
  fingerprint;
- the subject projection charges the bytes it actually hashes and refuses a
  file whose size changes mid-read (`denied-product-drift`);
- the shadow `.gitignore` marker is read through the confined, bounded,
  non-blocking reader;
- the AC-0007 tests now plant the disagreeing cached verdict and delete the
  mechanical state before a fresh store open, and the audit tests check the
  shared operation ID and reason code.

The new retry, two-writer, and replay tests fail against the earlier code.

## Corrupt re-read and coverage fixes (owner decision, 2026-10-07)

Quality-engineer round 3, security round 14, and adversarial round 15
confirmed the previous wave and found that a corrupt frame met during the
re-read under the lock cleared the open store's indexes part-way and left the
allow event without a denial. The owner overrode the retry cap and chose to
fix all sustained findings:

- the re-read builds its view aside and swaps it in only on success; any
  failure keeps the last consistent view, poisons the instance until reopen,
  and refuses with `denied-log-corrupt`, paired with the allow event;
- tests now reach the re-read refusals (`denied-log-corrupt`,
  `denied-log-needs-recovery`, `denied-log-not-regular`), the mid-read
  `denied-product-drift`, a FIFO, linked, or overlong shadow `.gitignore`
  marker, and every bad-authority retry case with its exact code;
- the core 2.28.1 changelog entry has a Highlights bullet.

The replay skip signal and a narrower `except` in the shadow sink were
refuted and left unchanged.

## Release renumbering and final review fixes (owner decision, 2026-10-07)

Adversarial round 16 found that main had already released core 2.29.0, and
that the 2.28.1 Highlights bullet advertised an adopter invocation the spec
says this slice does not provide. Quality-engineer round 4 found a test gap
and three nits. The owner overrode the retry cap and chose to:

- merge current main and release this change as core 2.29.1;
- replace the Highlights bullet with a recorded no-Highlights verdict and its
  reason, because the slice gives adopters no new invocation;
- surface a malformed record behind a valid checksum as the documented
  `EvidenceStoreError` on replay and as `denied-log-corrupt` on re-read;
- pin the shadow `.gitignore` marker's two-byte read bound with a test;
- name both poisoning causes, and index records through one shared helper.

Quality-engineer round 5 and adversarial round 17 then found that a
checksum-valid frame with a non-list `ordered_record_ids` still escaped frame
verification as a raw `TypeError`. The owner overrode the retry cap once more;
frame verification now maps any structural fault to the same corruption error,
and four tests (reopen and re-read, two header shapes) fail against the earlier
code.

Adversarial round 18 found further inputs of the same class: a dict
`ordered_record_ids`, an over-long integer, and deep nesting. Rather than fix
shapes one at a time, the owner chose to close the class: replay now parses
every frame through one helper that checks the transaction header and each
record against their schemas before the checksum, and any other fault while
reading a frame surfaces as the same corruption error. Four new cases fail
against the earlier code; the re-read test now shows poisoning through the
public `denied-store-poisoned` refusal.

## Accepted-risk amendment re-approval (owner decision, 2026-10-05)

The owner re-approved the spec and the plan at their human gates on
2026-10-05, after pre-execute round 28 came back clean. The cohort re-pinned
both (`approved_spec_hash` `2bd45af18615…`, `approved_plan_hash`
`15bcaba7827e…`) and rescheduled the one unfinished task, T9b. The approvals
are recorded here rather than in the plan's Changelog because adding them
there after `approve-plan` would change the pinned plan.

## Security review stop rule (owner decision, 2026-10-04)

Security review rounds 3 to 6 each found narrow audit-hygiene edges at the launch
boundaries: odd caller-supplied values that could leave a refusal unaudited or
store a malformed event. In every case the launch already failed closed, and
the untrusted-launch boundary has no production caller yet. After the eighth
override, which fixes round 6, the owner set a stop rule. One final security
round runs. Any finding it raises in this audit-hygiene class at Concern or
below goes to a recorded follow-up backlog item, not another override. A
Blocker, or a finding outside this class, still stops the loop as usual.

The final security round, round 7, upheld 1 Concern outside the stop rule's
class and 1 Nit inside it. The Concern: redaction replaced sensitive values one
at a time, so a short value such as `1` could split a longer credential that
contains it and leak most of it. Under the ninth override, `_redact_bytes` now
finds every occurrence of every value in the original output, merges spans that
overlap, nest, or touch, and replaces each merged span once.
`TestRedactionOverlap` covers nested and partly overlapping values in both
orders, plus a real launch. Against the pre-fix code, 5 of its 6 tests fail;
the sixth is an order the old code already handled. The Nit, the effect
broker's unchecked operation and grant IDs, falls inside the audit-hygiene
class and goes to a follow-up backlog item under the stop rule. That item is
the `[backlog].open` defect entry in `workspace.toml` whose path is this ledger.

The focused redaction re-check, security round 8, upheld 2 Concerns in that
change, both still in the redaction fix the owner approved. First, a value cut
off at the hard cap could still surface as fragments, because truncation ran
after redaction and the tail drop removed the shortest matching prefix. Second,
the span search stepped one byte at a time, so a repeating value made redaction
quadratic. The fix has three parts. When the capture overflowed, each raw
stream's longest tail that is a strict prefix of any sensitive value is dropped
before redaction. Redaction emits only raw bytes before the output bound.
Overlapping occurrences of one value are covered as a single periodic run, so
the search is linear, and duplicate values are removed. Against the committed
code, the cut-off-value and longest-prefix tests fail. The old code takes 1.21 s
on 40 KB of repeating input. The new code redacts 1 MiB inside the test's 5 s
bound and passes 3,000 randomized cases against a brute-force reference.

The redaction re-check, security round 9, upheld 2 Concerns, both in the
round-8 fix. First, the overflow tail drop could cut through a complete value
that ended in another value's prefix, and leave its first part unredacted.
Second, each separate occurrence paid a fixed 64 KiB comparison, and the tail
check was quadratic in value length. Redaction now follows one rule: cover,
never cut. Every complete occurrence in the full raw capture is a span. On an
overflowed capture, the longest tail that is a strict prefix of any value is
one more span, so nothing is trimmed away before matching. Spans merge, and only
raw bytes before the bound are emitted. The run scan starts small and doubles,
and the tail check uses the prefix function, so both are linear.
`TestRedactionAtTheCapAndAtScale` checks 5,000 randomized cases against a
brute-force definition that includes bounds and overflow. It covers the
reviewer's launch-level repro and stderr filling the combined cap, and timing
bounds keep every slow case under 5 s. Against the committed code, the
complete-value, self-overlap, and overflowed-launch tests fail.

The redaction re-check, security round 10, confirmed the cover-never-cut logic
and its linear cost. It upheld 1 Concern, which sits just outside that logic.
The redaction set encoded secrets as lossy UTF-8, while the child receives
environment values encoded by `os.fsencode`. So a secret with non-UTF-8 bytes
was matched in a different form and leaked whole. The redaction set now holds
every byte form each environment value and caller-supplied string can take,
the `os.fsencode` form included. An environment value that cannot be encoded
for the process boundary is refused before the allow event.
`TestRedactionMatchesTheBoundaryEncoding` checks the collected forms and runs a
launch that echoes a surrogate-escaped value. Both tests fail against the
committed code.

Adversarial review round 8 upheld 3 Concerns and 3 Nits. Under the tenth
override the fixes are as follows. The three shadow record types,
`delivery-subject.v1`, `acceptance-property.v1`, and `acceptance-verdict.v1`,
are registered under Structured control in both the code registry and the
delivery-content-safety §4 table. Each shadow record now passes its profile
before it is written. The owner chose that the calling writer port, not the
confined-mutation primitive, audits file writes. The shadow facade writes
through `_shadow_record_write`, which stores an allow event before each write
and a denial for each refusal. The evidence store's log creation is audited
when a sink is given, and the runtime-security-primitives page says so.
`TestShadowWriterPort` covers these, and all three of its tests fail against
the pre-fix code. The maintainer procedure in `loop-infrastructure.md` §10 now
runs the forgery corpus for cross-adapter conformance and lists every suite the
evidence map cites. The benchmark evidence above is the run that passed on all
four shards. The follow-up backlog entry exists. The spec's Accepted Risk
records every owner-accepted residual risk.

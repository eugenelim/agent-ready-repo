# Subsystem Design — Acceptance and evidence

**Decision sought:** Make acceptance criteria the durable delivery authority
and evaluate completion from fingerprinted evidence rather than gate phases.
**Author(s):** Platform Core maintainers
**Status:** Draft
**Last updated:** 2026-10-01
**Reviewers:** Core pack maintainers

## 1. Scope and Context

| In scope | Out of scope | Why |
| --- | --- | --- |
| Accepted property identity and authority | Task scheduling | Acceptance meaning must not depend on execution order |
| Evidence admissibility, freshness, and satisfaction | Running tests or tools | Verification mechanisms belong to execution infrastructure |
| Criterion-level completion verdicts | Final closeout | `close-work` retains lifecycle authority |

It must produce the same verdict for the same facts under every runtime. It
does not choose commands, test frameworks, reviewers, or concurrency.

## 2. Structural Model

| Element | Type | Responsibility | State |
| --- | --- | --- | --- |
| Subject-source port | Provider boundary | Supply one canonical base and current-product manifest | Stateless |
| Delivery-subject projector | Pure component | Bind product, spec, evidence policy, and task-projection provenance without control records | Stateless |
| Property projector | Pure component | Normalize durable criteria into `acceptance-property.v1` | Stateless |
| Approval registry | Durable fact store | Bind authority to the accepted spec and its evidence policy | Spec-policy approval records |
| Execution-envelope projector | Pure component | Fingerprint current references to every owning protected approval | Stateless |
| Initial-plan-review registry | Durable process-fact store | Bind one baseline strategy, safety, dependency, scope, and intent review to an envelope | Initial review records |
| Evidence registry | Durable fact store | Atomically append semantic evidence transactions and index their records | Transactions and derived indexes |
| Freshness evaluator | Pure component | Reject evidence for a changed subject | Stateless |
| Satisfaction evaluator | Pure policy component | Return supported, contradicted, or insufficient | Stateless |

Criteria remain in the spec; normalization adds identity and evidence policy.

## 3. Runtime Model

| Scenario | Trigger | Result |
| --- | --- | --- |
| Supporting evidence arrives | Execution emits a receipt | Recompute the named property |
| Acceptance subject changes | Product tree, spec, evidence policy, or selected input changes | Reevaluate each receipt under its freshness mode |
| Evidence conflicts | Supporting and contradictory observations coexist | Return contradicted until an authorized evidence supersession is accepted |

Evaluation is a query over facts, not a stored phase. A missing receipt is an
unsatisfied property and creates another execution need.

1. A `subject-source.v1` provider supplies a canonical manifest. The projector
   derives `delivery-subject.v1`; observations bind its acceptance fingerprint.
2. The evidence port applies shared
   [`content-safety-policy.v1`](delivery-content-safety.md),
   then atomically appends `semantic-evidence-transaction.v1` before
   acknowledging the producer.
3. The evaluator first requires current criterion and evidence-policy approval,
   then reads receipts and supersessions; freshness rejects `exact-subject`
   receipts from another acceptance fingerprint and tests
   `path-set` receipts against every fingerprint in
   [Contracts and Invariants](#4-contracts-and-invariants).
4. The satisfaction evaluator emits a derived verdict without persisting a
   phase or completion flag.

1. A malformed, stale, or partially written record fails validation and is not
   admitted to the registry.
2. The port emits a bounded rejection reason; the property remains insufficient
   or contradicted.
3. An unapproved semantic-policy edit cannot guide new execution. A working-plan
   change inside the reviewed envelope needs no approval and never erases
   integrated history or otherwise-fresh receipts; a boundary-crossing change
   refuses until its owning amendment or risk decision is accepted.
4. On restart, the registry truncates only an incomplete final append, replays
   valid records, and recomputes the verdict from the approved subject.

## 4. Contracts and Invariants

What always holds?

| Contract | Producer → consumer | Identity | Compatibility and change authority | Failure semantics | Invariant |
| --- | --- | --- | --- | --- | --- |
| `subject-source.v1` | Legacy snapshot or protected-ref provider → subject projector | Provider, immutable base and result manifests, authority receipt, projection version | Core and integration owners approve; provider parity precedes cutover | Ambiguous authority, drift, or unreadable path blocks projection | Providers produce the same canonical manifest and product fingerprint |
| `delivery-subject.v1` | Subject projector → evidence, review, and execution contracts | Product, spec, evidence-policy, exclusion, and lineage acceptance fingerprint; task-projection revision/hash as execution provenance | Core owners approve; unknown majors block readiness | Unresolvable base or ambiguous identity blocks projection | Task-only change cannot alter the acceptance fingerprint |
| `acceptance-property.v1` | Property projector → evaluator and task projector | Spec plus stable criterion ID | Core policy owners approve schema changes; readers ignore additive optional fields and reject unknown major versions | Invalid projection blocks evaluation, not authoring | One authority per property |
| `approval-record.v1` | Named authority through approval port → evaluator and projector | Authority, decision scope, base, lineage, and spec-policy fingerprint | Canonical schema owns fields; policy owners approve decisions | Missing authority, base, or lineage blocks its scope | Only spec-policy approval changes acceptance identity |
| `reviewed-execution-envelope.v1` | Pure projector over owning approvals → initial review, task projector, and replan guard | Ordered references for spec policy, scope/non-goals, security/authority, public contracts, durable outputs, and accepted risk | Each source owner approves its fact; schema owners approve projection rules | Missing, ambiguous, stale, or conflicting references refuse derivation | The envelope summarizes authority but grants none; identical inputs produce one fingerprint |
| `initial-plan-review.v1` | Named plan-review authority → task projector and terminal guard | Envelope fingerprint, reviewed baseline plan hash, authorized terminal intent, reviewer, and decision | Review policy owns the gate; a new envelope or intent needs fresh review | Missing, rejected, wrong-envelope, or wrong-intent review blocks projection; task edits do not rewrite it | Proves initial strategy, safety, dependencies, and scope alignment were reviewed and authorizes intent, not tasks |
| `semantic-evidence-transaction.v1` | Evidence port → append log, assessment view, and evaluator | Transaction ID, ordered record IDs, acceptance fingerprint, checksum | Canonical schema owns fields; readers deploy first; unknown majors are inadmissible | Incomplete frame truncates; checksum or reference failure rejects the transaction | Embedded changes become visible together or not at all |
| `evidence-receipt.v1` | Execution or review-failure producer through evidence port → registry and evaluator | Receipt ID, acceptance fingerprint, lineage, selector, freshness mode; task-projection revision as provenance | Contract owners approve; readers precede writers; unknown majors are inadmissible | Malformed, stale, or refused receipt is inadmissible | Freshness is `exact-subject` or `path-set`; review failures use exact subject |
| `evidence-supersession.v1` | Named evidence authority or review bridge through evidence port → evaluator | Supersession ID plus superseded receipt IDs | Core policy owners approve authority rules; additive reasons remain optional; unknown major versions block supersession | Missing authority, provenance, or matching subject rejects the record | Only the review bridge supersedes a review-failure receipt, when its source report or assessment ceases to be current |
| `acceptance-verdict.v1` | Satisfaction evaluator → work-loop policy and closeout | Evaluation fingerprint | Core policy owners approve semantics; consumers reject unknown major versions and recompute after reader upgrade | Unknown remains unsatisfied | Every verdict traces to criteria and receipts |

Gate commands only produce evidence; their orchestration is not a contract.

Subject providers use Git path, mode, and blob bytes. They admit only tracked
paths and acknowledged regular task additions inside the write set, allowed by
committed ignore, denial, and content rules. Unknown, unreadable, ignored, or
unprovenanced additions fail closed. The subject fingerprints those path rules.

Projection excludes `.git`, spec, plan, delivery-control, and approved
mechanical paths. Spec enters acceptance identity; plan hash is execution
provenance. The approval record retains the immutable base manifest or tree.

In slices 1–4, `legacy-worktree-snapshot` accepts only an acknowledged result;
other drift blocks. Slice 5 adds `protected-product-ref`. Provider parity on
the same tree precedes the source switch.

`acceptance-property.v1` carries an author-owned, approval-bound evidence policy:

| Field | Deterministic meaning |
| --- | --- |
| `authority_ref` | Current approval for the criterion, spec, and evidence policy; initial plan review and later task projections do not grant criterion authority |
| `subject_selector` | Canonical paths or artifact identities plus the fingerprint algorithm that binds evidence |
| `required_observations` | Named terms with observation type, producer class, outcomes, count, and permitted freshness mode or completeness attestor |
| `freshness_scope` | Either `exact-subject` or canonical `path-set`, with no adapter-defined third mode |
| `satisfaction_rule` | Canonical `all`, `any`, and `at-least` expression over named observation terms; no executable code |
| `contradiction_rule` | Canonical expression over normalized contradictory outcomes, evaluated before satisfaction; every property includes the reserved `supported-review-failure` term |
| `policy_version` | Schema and evaluator semantics selected by the approving authority |

`evidence-receipt.v1` stores the observation, bounded outcome, producer and
attestation, subject, and identity. Digests and controlled raw-output references
are optional audit data, never verdict inputs.

| Current approval | Admissible contradiction rule | Satisfaction rule | Verdict |
| --- | --- | --- | --- |
| No | Any | Any | `unapproved` |
| Yes | True | Any | `contradicted` |
| Yes | False | True | `supported` |
| Yes | False | False | `insufficient` |

Validation and authorized supersession determine admissibility before this
table runs. The evaluator applies contradiction before satisfaction and emits
the same verdict for the same canonical property and receipt set.

A supported `finding-assessment.v1` causes the review bridge to atomically emit
one normalized `review-failure` observation per affected criterion. Its
deterministic identity binds the report lineage tip, finding, assessment
revision, criterion, and acceptance fingerprint.

The same transaction supersedes prior bridge receipts when the report or
assessment ceases to be current. No other authority can clear one.
`accept-risk` closes only review; a changed subject makes old evidence stale.

An `exact-subject` receipt requires the current acceptance fingerprint. A
`path-set` receipt also requires one approval lineage and matching claim,
policy, attestation, complete transitive reads, command, toolchain,
configuration, environment, and selected bytes.

The observation policy names a completeness attestor; absence or incomplete
coverage forces `exact-subject`. A mismatch or new lineage makes evidence stale.

## 5. Data and State

| Element | State it owns | Lifecycle | Consistency requirement |
| --- | --- | --- | --- |
| Spec | Accepted criteria | Approved, amended, shipped | Criterion authority changes only through approved amendment |
| Approval registry | Append-only spec-policy approval records | Proposed, approved, superseded within lineage | Latest valid spec-policy approval governs acceptance; earlier facts remain immutable |
| Reviewed execution envelope | Derived references to current owning approvals | Recomputed on any protected-fact change | One fingerprint binds all protected inputs and grants no new authority |
| Initial-plan-review registry | Append-only initial review records | Proposed, accepted, superseded by a new envelope or intent | One accepted review enables projection for that envelope and intent; it never pins task text |
| Delivery subject | Base, result, exclusions, spec, evidence policy, and task-projection provenance | Derived | Every path is included once; task replanning does not change acceptance identity |
| Evidence registry | Append-only semantic transactions containing receipts, assessments, and supersessions | Appended, invalidated by subject change, retained per policy | A complete checksummed frame is the only visibility boundary |
| Evaluators | Stateless | n/a | Deterministic for the same input set |
| Raw producer output | Optional adapter-private log outside Git | Retained for the adapter's declared bounded period, then deleted | Verdict rehydration never depends on the log or locator |

Tasks own no acceptance state. A task merely declares which criteria it tries
to satisfy.

Initial review accepts strategy against the envelope and authorizes terminal
intent, not tasks or envelope source facts. Task changes need no approval while
both stay fixed. A protected change needs owner action and fresh review.

## 6. Deployment and Operations

| Unit | Runs as | Scaling | Observability |
| --- | --- | --- | --- |
| Projector and evaluators | Local harness library | At most 100,000 product paths or 10 GiB traversed in 60 s on the CI reference worker; exceedance refuses the subject | Per-criterion verdict, path and byte counts, duration, refusal reason |
| Evidence registry | Local append log plus disposable indexes | Linear in semantic transactions | Transaction, receipt, stale, contradiction, and truncation counts |

## 7. Quality Scenarios and Verification

| Stimulus | Mechanism and response | Target | Verification |
| --- | --- | --- | --- |
| Tree changes after a passing test | Exact-subject evidence stales; path-set evidence survives only unrelated changes with every bound fingerprint unchanged | 100% agreement with the two-mode rule | Selected-path, unrelated-path, policy, criterion, attestation, and lineage mutation fixtures |
| A dependency, configuration, toolchain, command, or environment changes outside selected outputs | Completeness attestor stales path-set evidence; missing attestation uses exact-subject | Zero path-set receipts survive a changed observation input | Transitive-read, config, argv, toolchain, and environment mutation fixtures |
| Runtime changes | Pure satisfaction evaluator preserves the verdict | Identical verdict across conforming adapters | Cross-adapter fixture |
| Subject provider changes on the same tree | Providers emit identical manifests and product fingerprints | Zero verdict or review-subject change | Legacy-snapshot/protected-ref parity corpus |
| Contradictory evidence arrives | Contradiction invariant refuses support until an authorized supersession | Zero contradicted properties accepted | Negative fixture |
| A supported review finding is accepted as risk | Review emits contradictory evidence while disposition closes only the review obligation | Zero risk acceptances turn a false property true | Review-to-evidence bridge fixture |
| Current review assessment or report changes | Bridge atomically supersedes or replaces its deterministic receipts | Zero live receipts from non-current review sources | Supported-to-unsupported, supported-to-indeterminate, report-replacement, and accept-risk fixtures |
| Crash occurs around a review assessment change | One checksummed transaction exposes both assessment and receipt delta or neither | Zero split assessment/evidence visibility after restart or journal deletion | Crash injection before, within, and after append plus index-rebuild fixture |
| Producer returns detected protected or unbounded output | Evidence-port validation rejects before durable append | Zero scanner-corpus or oversize payloads enter Git | Secret, privacy, size, and raw-output fixtures |
| Spec or working plan changes after initial review | An unapproved spec edit cannot project work; an in-envelope task change reprojects without approval and preserves fresh evidence; a protected-boundary change refuses | Zero unapproved semantic change, zero approval prompts for in-envelope replanning, and zero evidence invalidation solely from task guidance | Fingerprint, task-revision, boundary-mutation, task-reprojection, and cache-deletion fixture |
| Legacy approved spec and plan are imported | Exact canonicalization verifies both digests and one transaction publishes spec-policy approval plus the initial-plan-review baseline | Zero partial imports and every imported criterion covered by the spec digest | Normalization corpus, malformed criterion, malformed plan, crash-point, retry, and reverse-reader fixtures |
| Two adapters emit equivalent normalized observations | Canonical policy and truth table produce one result | Identical verdict across every conforming adapter | Cross-adapter truth-table corpus |
| Delivery-control or product files change | Control-plane writes preserve the product hash; product writes change it | 100% deterministic subject separation | Projection mutation fixture |
| Untracked, ignored, excluded, or unreadable paths exist | Projector admits only acknowledged non-ignored task additions and otherwise refuses or excludes by policy | Zero ambient files or ignored credential/config fixtures enter a manifest or protected ref | Base-manifest, addition, ignored-secret, exclusion-change, and unreadable-path fixtures |
| Product source has unacknowledged drift | Active provider refuses instead of choosing a view | Zero drift reaches readiness | Legacy and protected-ref dirty fixtures |
| Product traversal reaches a path, byte, or time bound | Projector stops without emitting a partial subject | Refusal above 100,000 paths, 10 GiB, or 60 s | Bound-edge and oversized-repository fixtures on the CI reference worker |

## 8. Implementation Mapping

| Element | Source owner | Build unit | Verification |
| --- | --- | --- | --- |
| Subject providers, projectors, and schemas | Proposed `work_supervisor/acceptance.py`; schemas in `contracts/delivery/` | Supervisor bundle source and contracts | Provider parity, projection, and schema tests |
| Approval and initial-plan-review registries and ports | Proposed `packages/agentbundle/agentbundle/work_supervisor/approvals.py` | Supervisor bundle source; `agentbundle` builds/tests | Authority, lineage, initial-review, mutation, and rehydration tests |
| Legacy approval importer | Proposed `work_supervisor/legacy_approvals.py` reusing current canonicalization fixtures | Slice-1 supervisor service bundle | Spec/plan digest parity, criterion coverage, atomic append, refusal, and reverse-read tests |
| Evidence transaction log and indexes | Proposed `packages/agentbundle/agentbundle/work_supervisor/evidence_store.py` | Supervisor bundle source; `agentbundle` builds/tests | Atomic framing, crash, index rebuild, and invalidation tests |
| Freshness and satisfaction evaluators | Proposed `packages/agentbundle/agentbundle/work_supervisor/acceptance.py` | Supervisor bundle source; `agentbundle` builds/tests | Pure unit tests |
| Evidence policy | `packs/core/.apm/skills/work-loop/` | Core pack | Skill evals |

## 9. Decisions, Alternatives, and Risks

- **Decision:** Criteria, not tasks, own completion.
- **Rejected:** Task-complete flags and global phases can claim completion
  without proving accepted properties.
- **Rejected:** Fixed gate lists name mechanisms, not the properties they prove.
- **Risk:** Weak policy admits irrelevant proof. Exact property/subject fixtures
  mitigate it.
- **Risk:** Torn appends block rehydration. Framing, checksums, and final-record
  truncation preserve the last complete prefix.
- **Risk:** Volume slows evaluation. Disposable indexes rebuild from the log.

## 10. Rollout, Migration, and Reversal

The compatibility projector accepts only legacy forms whose missing fields have
one mechanical answer:

| Legacy spec or plan form | Mechanical `acceptance-property.v1` projection | Amendment condition |
| --- | --- | --- |
| Atomic criterion with stable ID and plan tests that cite it | Full result product-tree selector within `delivery-subject.v1`; one named term per cited test; `all` satisfaction; any normalized required-term failure contradicts | Any cited test lacks a deterministic producer or outcome |
| TDD behavior with named test seam and criterion reference | `test-result` observation from the declared test runner | Test seam, runner, or criterion link is absent |
| Goal-based check with exact command and expected result | `command-result` observation with bounded exit and normalized output assertion | Command, expected result, or subject is implicit |
| Manual or visual QA with recorded gesture and observable outcome | `manual-observation` from a named human authority | Gesture, observable outcome, authority, or subject is absent |
| Criterion with multiple unmapped predicates, subjective wording, or no testing-mode link | No projection | Approved semantic-policy amendment supplies every policy field; the working plan may then project matching tasks without separate approval |

The conservative full-tree default stales on any product change. Control
records stay outside it; no projector invents a narrower policy.

Eligible criteria and gate events dual-emit during shadowing. Parity covers
every projection and refusal row before phase removal; rollback ignores the new
receipts.

The importer reproduces `approve-plan` canonicalization, verifies both digests,
then atomically appends one spec-policy approval and one initial review bound to
the envelope and baseline plan while authorizing current terminal intent. The
plan digest is audit evidence, not continuing task authority.

Ambiguity, refusal, digest mismatch, missing authority, or either write failure
publishes neither record. Recovery recomputes from the legacy pin. The reverse
reader reconstructs the pair during dual-read. After cutover, downgrade needs
explicit approval of the current plan snapshot because the old engine cannot
represent mutable tasks. Task projections use mechanical revisions, not
approvals.

| Responsibility | Owner |
| --- | --- |
| Cutover and compatibility-window observation | Core pack maintainers |
| Legacy approval canonicalization and atomic import | Core pack and `agentbundle` contract maintainers |
| Evidence-store operation and recovery drill | `agentbundle` maintainers |
| Rollback authorization | Core pack maintainer on call after unexplained shadow divergence |

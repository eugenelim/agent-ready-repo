# Subsystem Design — Acceptance and evidence

**Decision sought:** Make acceptance criteria the durable delivery authority
and evaluate completion from fingerprinted evidence rather than gate phases.
**Author(s):** Platform Core maintainers
**Status:** Draft
**Last updated:** 2026-10-01
**Reviewers:** Core pack maintainers

## 1. Scope and Context

What does this subsystem own?

| In scope | Out of scope | Why |
| --- | --- | --- |
| Accepted property identity and authority | Task scheduling | Acceptance meaning must not depend on execution order |
| Evidence admissibility, freshness, and satisfaction | Running tests or tools | Verification mechanisms belong to execution infrastructure |
| Criterion-level completion verdicts | Final closeout | `close-work` retains lifecycle authority |

**Goals**

- No acceptance criterion reaches satisfied without fresh admissible evidence.
- The same facts produce the same verdict under every runtime.
- Task replacement does not invalidate evidence unless a bound freshness input changes.

**Non-goals**

- Choosing commands, test frameworks, reviewers, or concurrency.

## 2. Structural Model

What elements establish an accepted property?

| Element | Type | Responsibility | State |
| --- | --- | --- | --- |
| Subject-source port | Provider boundary | Supply one canonical base and current-product manifest | Stateless |
| Delivery-subject projector | Pure component | Bind product, spec, evidence policy, and plan provenance without control records | Stateless |
| Property projector | Pure component | Normalize durable criteria into `acceptance-property.v1` | Stateless |
| Approval registry | Durable fact store | Bind authority to the accepted spec and current approved plan revision | Approval records |
| Evidence registry | Durable fact store | Atomically append semantic evidence transactions and index their records | Transactions and derived indexes |
| Freshness evaluator | Pure component | Reject evidence for a changed subject | Stateless |
| Satisfaction evaluator | Pure policy component | Return supported, contradicted, or insufficient | Stateless |

The criterion remains authored in the spec. Normalization supplies stable
identity and machine-checkable evidence policy without creating a second source
of product truth.

## 3. Runtime Model

How is completion evaluated?

| Scenario | Trigger | Result |
| --- | --- | --- |
| Supporting evidence arrives | Execution emits a receipt | Recompute the named property |
| Acceptance subject changes | Product tree, spec, evidence policy, or selected input changes | Reevaluate each receipt under its freshness mode |
| Evidence conflicts | Supporting and contradictory observations coexist | Return contradicted until an authorized evidence supersession is accepted |

Evaluation is a query over facts, not a stored phase. A missing receipt is an
unsatisfied property and creates another execution need.

**Normal sequence**

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

**Failure and recovery sequence**

1. A malformed, stale, or partially written record fails validation and is not
   admitted to the registry.
2. The port emits a bounded rejection reason; the property remains insufficient
   or contradicted.
3. An edited spec or plan without approval cannot guide new execution. Plan
   revision never erases integrated history or otherwise-fresh receipts.
4. On restart, the registry truncates only an incomplete final append, replays
   valid records, and recomputes the verdict from the approved subject.

## 4. Contracts and Invariants

What always holds?

| Contract | Producer → consumer | Identity | Compatibility and change authority | Failure semantics | Invariant |
| --- | --- | --- | --- | --- | --- |
| `subject-source.v1` | Legacy snapshot or protected-ref provider → subject projector | Provider, immutable base and result manifests, authority receipt, projection version | Core and integration owners approve; provider parity precedes cutover | Ambiguous authority, drift, or unreadable path blocks projection | Providers produce the same canonical manifest and product fingerprint |
| `delivery-subject.v1` | Subject projector → evidence, review, and execution contracts | Product, spec, evidence-policy, exclusion, and lineage acceptance fingerprint; plan revision/hash as execution provenance | Core owners approve; unknown majors block readiness | Unresolvable base or ambiguous identity blocks projection | Plan-only change cannot alter the acceptance fingerprint |
| `acceptance-property.v1` | Property projector → evaluator and task projector | Spec plus stable criterion ID | Core policy owners approve schema changes; readers ignore additive optional fields and reject unknown major versions | Invalid projection blocks evaluation, not authoring | One authority per property |
| `approval-record.v1` | Named authority through approval port → evaluator and projector | Authority, decision scope, base, lineage; spec-policy fingerprint or plan revision/predecessor/hash | Canonical schema owns fields; policy owners approve decisions | Missing authority, predecessor, base, or lineage blocks its scope | Spec-policy approval changes acceptance identity; plan approval changes guidance only |
| `semantic-evidence-transaction.v1` | Evidence port → append log, assessment view, and evaluator | Transaction ID, ordered record IDs, acceptance fingerprint, checksum | Canonical schema owns fields; readers deploy first; unknown majors are inadmissible | Incomplete frame truncates; checksum or reference failure rejects the transaction | Embedded changes become visible together or not at all |
| `evidence-receipt.v1` | Execution or review-failure producer through evidence port → registry and evaluator | Receipt ID, acceptance fingerprint, lineage, selector, freshness mode; plan revision as provenance | Contract owners approve; readers precede writers; unknown majors are inadmissible | Malformed, stale, or refused receipt is inadmissible | Freshness is `exact-subject` or `path-set`; review failures use exact subject |
| `evidence-supersession.v1` | Named evidence authority or review bridge through evidence port → evaluator | Supersession ID plus superseded receipt IDs | Core policy owners approve authority rules; additive reasons remain optional; unknown major versions block supersession | Missing authority, provenance, or matching subject rejects the record | Only the review bridge supersedes a review-failure receipt, when its source report or assessment ceases to be current |
| `acceptance-verdict.v1` | Satisfaction evaluator → work-loop policy and closeout | Evaluation fingerprint | Core policy owners approve semantics; consumers reject unknown major versions and recompute after reader upgrade | Unknown remains unsatisfied | Every verdict traces to criteria and receipts |

Gate commands are evidence producers. Their names, order, and retry behavior
never enter these contracts.

Both subject providers use Git path, mode, and blob-byte semantics. They include
tracked paths plus task additions explicitly admitted by an acknowledged result,
but never ambient or ignored untracked paths. An addition must be regular,
within the task write set, non-ignored by committed repository rules, outside
policy denials, and accepted by the product-addition content profile.

The versioned path policy fingerprints committed ignore rules and denials in
`delivery-subject.v1`. Unknown, unreadable, non-regular, ignored, or
unprovenanced additions fail closed; they never enter a base manifest or the
protected ref.

The projection excludes `.git`, exact spec and plan paths, delivery-control
paths, and approved mechanical paths. Spec enters acceptance identity; plan
hash remains separate execution provenance. The approval record, not a host
default branch or merge base, retains the immutable base manifest or tree.

In slices 1–4, `legacy-worktree-snapshot` accepts only an existing-engine
acknowledged result boundary and snapshots it immutably; other drift blocks.
Slice 5 adds `protected-product-ref`, where worktree drift from the ref blocks.
Provider parity on the same tree is required before the source changes.

`acceptance-property.v1` carries an author-owned, approval-bound evidence policy:

| Field | Deterministic meaning |
| --- | --- |
| `authority_ref` | Current approval for the criterion, spec, and evidence policy; plan approval is separate execution guidance |
| `subject_selector` | Canonical paths or artifact identities plus the fingerprint algorithm that binds evidence |
| `required_observations` | Named terms with observation type, producer class, outcomes, count, and permitted freshness mode or completeness attestor |
| `freshness_scope` | Either `exact-subject` or canonical `path-set`, with no adapter-defined third mode |
| `satisfaction_rule` | Canonical `all`, `any`, and `at-least` expression over named observation terms; no executable code |
| `contradiction_rule` | Canonical expression over normalized contradictory outcomes, evaluated before satisfaction; every property includes the reserved `supported-review-failure` term |
| `policy_version` | Schema and evaluator semantics selected by the approving authority |

`evidence-receipt.v1` persists the named observation type, bounded normalized
outcome, producer class and attestation, subject fingerprint, and receipt
identity needed by that policy. Digests and controlled raw-output references
are optional audit enrichment and never required to recompute the verdict.

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

The same transaction supersedes prior bridge receipts when the source report
ceases to be current or its current assessment becomes unsupported or
indeterminate. No other evidence authority can clear such a receipt.
`accept-risk` closes only the review obligation, while acceptance-subject change or
an approved criterion amendment makes the old receipt inapplicable.

An `exact-subject` receipt is current only when its acceptance fingerprint
equals the current one. A `path-set` receipt remains current within one approval
lineage only while its criterion claim, evidence policy, producer attestation,
complete transitive read set, command and toolchain, configuration, execution
environment, and selected current bytes match their recorded fingerprints.

The
observation-type policy must name and validate a conforming completeness
attestor; an absent or incomplete attestor forces `exact-subject`. Any mismatch
or new base lineage makes the receipt stale without retargeting it.

## 5. Data and State

| Element | State it owns | Lifecycle | Consistency requirement |
| --- | --- | --- | --- |
| Spec | Accepted criteria | Approved, amended, shipped | Criterion authority changes only through approved amendment |
| Approval registry | Append-only approval records | Proposed, approved, superseded within lineage | Latest valid spec and plan revision governs new projection; earlier facts remain immutable |
| Delivery subject | Base, result, exclusions, spec, evidence policy, and plan provenance | Derived | Every path is included once; plan does not change acceptance identity |
| Evidence registry | Append-only semantic transactions containing receipts, assessments, and supersessions | Appended, invalidated by subject change, retained per policy | A complete checksummed frame is the only visibility boundary |
| Evaluators | Stateless | n/a | Deterministic for the same input set |
| Raw producer output | Optional adapter-private log outside Git | Retained for the adapter's declared bounded period, then deleted | Verdict rehydration never depends on the log or locator |

Tasks own no acceptance state. A task merely declares which criteria it tries
to satisfy.

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
| Spec or plan changes after approval | Unapproved edits cannot project work; plan-only revision preserves fresh evidence | Zero unapproved execution, reset, or evidence invalidation solely from plan guidance | Fingerprint, revision, task-reprojection, and cache-deletion fixture |
| Legacy approved spec or plan is imported | Exact canonicalization verifies both digests and one transaction publishes both scoped approvals | Zero partial imports and every imported criterion covered by the spec digest | Normalization corpus, malformed criterion, crash-point, retry, and reverse-reader fixtures |
| Two adapters emit equivalent normalized observations | Canonical policy and truth table produce one result | Identical verdict across every conforming adapter | Cross-adapter truth-table corpus |
| Delivery-control or product files change | Control-plane writes preserve the product hash; product writes change it | 100% deterministic subject separation | Projection mutation fixture |
| Untracked, ignored, excluded, or unreadable paths exist | Projector admits only acknowledged non-ignored task additions and otherwise refuses or excludes by policy | Zero ambient files or ignored credential/config fixtures enter a manifest or protected ref | Base-manifest, addition, ignored-secret, exclusion-change, and unreadable-path fixtures |
| Product source has unacknowledged drift | Active provider refuses instead of choosing a view | Zero drift reaches readiness | Legacy and protected-ref dirty fixtures |
| Product traversal reaches a path, byte, or time bound | Projector stops without emitting a partial subject | Refusal above 100,000 paths, 10 GiB, or 60 s | Bound-edge and oversized-repository fixtures on the CI reference worker |

## 8. Implementation Mapping

| Element | Source owner | Build unit | Verification |
| --- | --- | --- | --- |
| Subject providers, projectors, and schemas | Proposed `work_supervisor/acceptance.py`; schemas in `contracts/delivery/` | Supervisor bundle source and contracts | Provider parity, projection, and schema tests |
| Approval registry and port | Proposed `packages/agentbundle/agentbundle/work_supervisor/approvals.py` | Supervisor bundle source; `agentbundle` builds/tests | Authority, lineage, mutation, and rehydration tests |
| Legacy approval importer | Proposed `work_supervisor/legacy_approvals.py` reusing current canonicalization fixtures | Slice-1 supervisor service bundle | Spec/plan digest parity, criterion coverage, atomic append, refusal, and reverse-read tests |
| Evidence transaction log and indexes | Proposed `packages/agentbundle/agentbundle/work_supervisor/evidence_store.py` | Supervisor bundle source; `agentbundle` builds/tests | Atomic framing, crash, index rebuild, and invalidation tests |
| Freshness and satisfaction evaluators | Proposed `packages/agentbundle/agentbundle/work_supervisor/acceptance.py` | Supervisor bundle source; `agentbundle` builds/tests | Pure unit tests |
| Evidence policy | `packs/core/.apm/skills/work-loop/` | Core pack | Skill evals |

## 9. Decisions, Alternatives, and Risks

- **Decision:** Criteria, not tasks, own completion.
- **Alternative:** Store a task-complete flag. **Rejected because:** regenerated
  tasks permit completion claims without proving the accepted property.
- **Alternative:** Persist a global delivery phase. **Rejected because:** phase
  recovery becomes an authority problem instead of a query over durable facts.
- **Alternative:** Treat a fixed gate list as acceptance. **Rejected because:**
  mechanism names cannot express which accepted property each result proves.
- **Risk:** Weak evidence policies admit irrelevant proof. **Mitigation:**
  contract fixtures require exact property and subject binding.
- **Risk:** A torn evidence append prevents rehydration at 3 a.m.
  **Mitigation:** append framing, checksum validation, and final-record
  truncation preserve the last complete prefix.
- **Risk:** Receipt volume makes evaluation slow. **Mitigation:** derived indexes
  are disposable and rebuilt from the authoritative append log.

## 10. Rollout, Migration, and Reversal

The compatibility projector accepts only legacy forms whose missing fields have
one mechanical answer:

| Legacy spec or plan form | Mechanical `acceptance-property.v1` projection | Amendment condition |
| --- | --- | --- |
| Atomic criterion with stable ID and plan tests that cite it | Full result product-tree selector within `delivery-subject.v1`; one named term per cited test; `all` satisfaction; any normalized required-term failure contradicts | Any cited test lacks a deterministic producer or outcome |
| TDD behavior with named test seam and criterion reference | `test-result` observation from the declared test runner | Test seam, runner, or criterion link is absent |
| Goal-based check with exact command and expected result | `command-result` observation with bounded exit and normalized output assertion | Command, expected result, or subject is implicit |
| Manual or visual QA with recorded gesture and observable outcome | `manual-observation` from a named human authority | Gesture, observable outcome, authority, or subject is absent |
| Criterion with multiple unmapped predicates, subjective wording, or no testing-mode link | No projection | Approved spec and plan amendment supplies every policy field |

The full result product-tree default is conservative: any product change makes
the legacy observation stale. Delivery-control records remain outside that
tree. No projector invents a narrower selector, producer, or judgment rule.

Project eligible criteria and emit receipts alongside current gate events.
The parity corpus includes every mechanically projectable row and every refusal
row above. Shadow verdicts precede phase removal; rollback keeps the current
gate path while leaving new receipts unused.

The legacy importer first reproduces `approve-plan` canonicalization exactly:
newline and trailing-space normalization, status-token normalization, and the
artifact-specific checkbox rules. It verifies the current approved spec and
plan digests before deriving two linked `approval-record.v1` decisions in one
atomic append: spec-policy approval covering every projected criterion, and
plan-revision approval naming revision 1 and that approved plan digest.

An ambiguous criterion, projection refusal, digest mismatch, missing authority,
or failure of either record publishes neither. Recovery recomputes both from
the unchanged legacy pin; the reverse reader reconstructs the approved pair or
refuses a lossy projection. Later plan revisions append predecessor-linked
approvals; no global reset or completed-task-section pin enters the new model.

| Responsibility | Owner |
| --- | --- |
| Cutover and compatibility-window observation | Core pack maintainers |
| Legacy approval canonicalization and atomic import | Core pack and `agentbundle` contract maintainers |
| Evidence-store operation and recovery drill | `agentbundle` maintainers |
| Rollback authorization | Core pack maintainer on call after unexplained shadow divergence |

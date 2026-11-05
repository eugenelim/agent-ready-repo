# Work-loop acceptance and evidence

Completion is a verdict derived per acceptance criterion from fingerprinted
evidence. It is a query over facts, never a stored phase or completion flag. The
verdict is `unapproved`, `contradicted`, `supported`, or `insufficient`, and
contradiction is evaluated before satisfaction.

Evidence counts only when the
evidence port appended it atomically and its freshness mode matches the current
subject.

Under the supervisor, `delivery_subject()` builds the subject from the committed
tree of the authority's result commit.[^1] Criteria stay in the spec, and tasks
own no acceptance state.

**Status:** Current. Governing record:
[ADR-0144](../adr/0144-work-loop-supervisor-owns-procedure.md). The
[supervisor page](work-loop-execution-supervisor.md) owns procedure.

[Delivery content safety](delivery-content-safety.md) owns the content-safety
policy the evidence port applies.

**`STATUS: PLANNED`:** parallel result integration extends the subject and
evidence flow with three-tree apply and parallel results. The
[product result integration](work-loop-result-integration.md) page and the
[brief's delivery slices](../product/briefs/acceptance-centered-work-loop.md#proposed-delivery-slices)
own that design and its status.

## 1. Scope and Context

Acceptance evaluation produces the same verdict for the same facts under every
runtime. It does not choose commands, test frameworks, reviewers, or
concurrency.

| In scope | Out of scope | Why |
| --- | --- | --- |
| Accepted property identity and authority | Task scheduling | Acceptance meaning must not depend on execution order |
| Evidence admissibility, freshness, and satisfaction | Running tests or tools | Verification mechanisms belong to execution infrastructure |
| Criterion-level completion verdicts | Final closeout | `close-work` retains lifecycle authority |

## 2. Structural Model

Pure components project and evaluate. Durable registries hold the facts they
read.

| Element | Type | Responsibility | State |
| --- | --- | --- | --- |
| Delivery-subject projector | Pure component | Bind product, spec, evidence policy, and task-projection provenance without control records | Stateless |
| Property projector | Pure component | Normalize durable criteria into `acceptance-property.v1` | Stateless |
| Approval registry | Durable fact store | Bind authority to the accepted spec and its evidence policy | Spec-policy approval records |
| Execution-envelope projector | Pure component | Fingerprint current references to every owning protected approval | Stateless |
| Initial-plan-review registry | Durable process-fact store | Bind one baseline strategy, safety, dependency, scope, and intent review to an envelope | Initial review records |
| Evidence registry | Durable fact store | Atomically append semantic evidence transactions and index their records | Transactions and derived indexes |
| Freshness evaluator | Pure component | Reject evidence for a changed subject | Stateless |
| Satisfaction evaluator | Pure policy component | Return one of the four verdicts | Stateless |

The `_subject_source.py` module implements a `subject-source.v1` provider,
`legacy-worktree-snapshot`, that the supervisor does not call. It is retained.
No `subject-source.v1` schema exists in `contracts/delivery/`.[^2]

## 3. Runtime Model

| Scenario | Trigger | Result |
| --- | --- | --- |
| Supporting evidence arrives | Execution emits a receipt | Recompute the named property |
| Acceptance subject changes | Product tree, spec, evidence policy, or selected input changes | Reevaluate each receipt under its freshness mode |
| Evidence conflicts | Supporting and contradictory observations coexist | Return contradicted until an authorized evidence supersession is accepted |

A missing receipt is an unsatisfied property and creates another execution need.

Normal path:

1. `delivery_subject()` reads the committed tree entries at the authority's
   result commit, excludes the spec directory, and calls the projector to derive
   `delivery-subject.v1`. Observations bind its acceptance fingerprint.
2. The evidence port applies the shared
   [`content-safety-policy.v1`](delivery-content-safety.md), then atomically
   appends `semantic-evidence-transaction.v1` before acknowledging the producer.
3. The evaluator requires current criterion and evidence-policy approval, then
   reads receipts and supersessions. Freshness rejects `exact-subject` receipts
   from another acceptance fingerprint and tests `path-set` receipts against
   every fingerprint in [Contracts and Invariants](#4-contracts-and-invariants).
4. The satisfaction evaluator emits a derived verdict.[^3]

Failure and recovery:

1. A malformed, stale, or partially written record fails validation and is not
   admitted to the registry.
2. The port emits a bounded rejection reason. The property remains insufficient
   or contradicted.
3. An unapproved semantic-policy edit cannot guide new execution. A working-plan
   change inside the reviewed envelope needs no approval and never erases
   integrated history or otherwise-fresh receipts. A boundary-crossing change
   refuses until its owning amendment or risk decision is accepted.
4. On restart, the registry truncates only an incomplete final append, replays
   valid records, and recomputes the verdict from the approved subject.[^4]

## 4. Contracts and Invariants

Every schema is in `contracts/delivery/`.

| Contract | Producer → consumer | Identity | Failure semantics | Invariant |
| --- | --- | --- | --- | --- |
| `delivery-subject.v1` | Subject projector → evidence, review, and execution contracts | Product, spec, evidence-policy, exclusion, and lineage acceptance fingerprint; task-projection revision as execution provenance | Unresolvable base or ambiguous identity blocks projection; unknown majors block readiness | A task-only change cannot alter the acceptance fingerprint |
| `acceptance-property.v1` | Property projector → evaluator and task projector | Spec plus stable criterion ID | Invalid projection blocks evaluation, not authoring | One authority per property |
| `approval-record.v1` | Named authority through the approval port → evaluator and projector | Authority, decision scope, base, lineage, and spec-policy fingerprint | Missing authority, base, or lineage blocks its scope | Only spec-policy approval changes acceptance identity |
| `reviewed-execution-envelope.v1` | Pure projector over owning approvals → initial review, task projector, and replan guard | Ordered references for spec policy, scope and non-goals, security and authority, public contracts, durable outputs, and accepted risk | Missing, ambiguous, stale, or conflicting references refuse derivation | The envelope summarizes authority but grants none; identical inputs produce one fingerprint |
| `initial-plan-review.v1` | Named plan-review authority → task projector and terminal guard | Envelope fingerprint, reviewed baseline plan hash, authorized terminal intent, reviewer, and decision | Missing, rejected, wrong-envelope, or wrong-intent review blocks projection; task edits do not rewrite it | Proves initial strategy, safety, dependencies, and scope alignment were reviewed, and authorizes intent, not tasks |
| `semantic-evidence-transaction.v1` | Evidence port → append log, assessment view, and evaluator | Transaction ID, ordered record IDs, acceptance fingerprint, checksum | An incomplete frame truncates; a checksum or reference failure rejects the transaction; unknown majors are inadmissible | Embedded changes become visible together or not at all |
| `evidence-receipt.v1` | Execution or review-failure producer through the evidence port → registry and evaluator | Receipt ID, acceptance fingerprint, lineage, selector, freshness mode; task-projection revision as provenance | A malformed, stale, or refused receipt is inadmissible | Freshness is `exact-subject` or `path-set`; review failures use exact subject |
| `evidence-supersession.v1` | Named evidence authority or review bridge through the evidence port → evaluator | Supersession ID plus superseded receipt IDs | Missing authority, provenance, or matching subject rejects the record | Only the review bridge supersedes a review-failure receipt, when its source report or assessment ceases to be current |
| `acceptance-verdict.v1` | Satisfaction evaluator → work-loop policy and closeout | Evaluation fingerprint | Unknown remains unsatisfied | Every verdict traces to criteria and receipts |

Canonical schema owners approve field changes. Readers deploy before writers,
additive optional fields are ignored, and consumers reject unknown major
versions. Gate commands only produce evidence, and their orchestration is not a
contract.

### The subject

The subject manifest is the committed (path, blob object ID) pairs from the result tree. Projection excludes the spec
directory, which `delivery_subject()` passes as the exclusion prefix. The spec
enters acceptance identity through its fingerprint, and the plan hash is
execution provenance.[^1]

An adopted change to the product or the spec directory salts the spec
fingerprint with the `reanchor` commit, so evidence recorded before it does not
count.

`result_authority` in `supervisor-policy.json` picks the subject's provider:

| `result_authority` | Lineage provider | Result commit |
| --- | --- | --- |
| `protected-product-ref` | `protected-product-ref` | The commit the run store recorded for the product ref, so `HEAD` history the owner has not adopted changes nothing |
| `legacy-worktree` (the reversal setting) | `work-supervisor` | `HEAD` |

A subject recorded under the other provider does not count. Lineage names only
the authority, so a run taken back to an authority it already used can match
evidence from that stretch. Where the subject still reads `HEAD` (`status` while
foreign history sits there, and a run with no recorded ref) is in the
supervisor page's [Product ref](work-loop-execution-supervisor.md#product-ref)
section.[^5]

### Evidence policy

`acceptance-property.v1` carries an author-owned, approval-bound evidence
policy:

| Field | Deterministic meaning |
| --- | --- |
| `authority_ref` | Current approval for the criterion, spec, and evidence policy. Initial plan review and later task projections do not grant criterion authority |
| `subject_selector` | Canonical paths or artifact identities plus the fingerprint algorithm that binds evidence |
| `required_observations` | Named terms with observation type, producer class, outcomes, count, and permitted freshness mode or completeness attestor |
| `freshness_scope` | Either `exact-subject` or canonical `path-set`, with no adapter-defined third mode |
| `satisfaction_rule` | Canonical `all`, `any`, and `at-least` expression over named observation terms, with no executable code |
| `contradiction_rule` | Canonical expression over normalized contradictory outcomes, evaluated before satisfaction. Every property includes the reserved `supported-review-failure` term |
| `policy_version` | Schema and evaluator semantics selected by the approving authority |

`evidence-receipt.v1` stores the observation, bounded outcome, producer and
attestation, subject, and identity. Digests and controlled raw-output references
are optional audit data, never verdict inputs.

An `exact-subject` receipt requires the current acceptance fingerprint. A
`path-set` receipt also requires one approval lineage and matching claim,
policy, attestation, complete transitive reads, command, toolchain,
configuration, environment, and selected bytes.

The observation policy names a completeness attestor. Absence or incomplete coverage forces `exact-subject`,
and a mismatch or new lineage makes evidence stale.

### The verdict

| Current approval | Admissible contradiction rule | Satisfaction rule | Verdict |
| --- | --- | --- | --- |
| No | Any | Any | `unapproved` |
| Yes | True | Any | `contradicted` |
| Yes | False | True | `supported` |
| Yes | False | False | `insufficient` |

Validation and authorized supersession determine admissibility before this
table runs. The evaluator applies contradiction before satisfaction and emits
the same verdict for the same canonical property and receipt set.[^3]

### The review bridge

A supported `finding-assessment.v1` causes the review bridge to atomically emit
one normalized `review-failure` observation per affected criterion. Its
deterministic identity binds the report lineage tip, finding, assessment
revision, criterion, and acceptance fingerprint.

The same transaction supersedes prior bridge receipts when the report or
assessment ceases to be current. No other authority can clear one. `accept-risk`
closes only review, and a changed subject makes old evidence stale.[^6]

## 5. Data and State

| Element | State it owns | Lifecycle | Consistency requirement |
| --- | --- | --- | --- |
| Spec | Accepted criteria | Approved, amended, shipped | Criterion authority changes only through approved amendment |
| Approval registry | Append-only spec-policy approval records | Proposed, approved, superseded within lineage | The latest valid spec-policy approval governs acceptance; earlier facts remain immutable |
| Reviewed execution envelope | Derived references to current owning approvals | Recomputed on any protected-fact change | One fingerprint binds all protected inputs and grants no new authority |
| Initial-plan-review registry | Append-only initial review records | Proposed, accepted, superseded by a new envelope or intent | One accepted review enables projection for that envelope and intent and never pins task text |
| Delivery subject | Base, result, exclusions, spec, evidence policy, and task-projection provenance | Derived | Every path is included once; task replanning does not change acceptance identity |
| Evidence registry | Append-only semantic transactions containing receipts, assessments, and supersessions | Appended, invalidated by subject change, retained per policy | A complete checksummed frame is the only visibility boundary |
| Raw producer output | Optional adapter-private log outside Git | Adapter-private; the bounded retention period and deletion are **STATUS: PLANNED** and no code enforces them | Verdict rehydration never depends on the log or locator |

Initial review accepts strategy against the envelope and authorizes terminal
intent, not tasks or envelope source facts. Task changes need no approval while
both stay fixed. A protected change needs owner action and fresh review.

## 6. Deployment and Operations

The projector and evaluators run as a local harness library. The evidence
registry is a local append log plus disposable indexes, linear in semantic
transactions. Reporting transaction, receipt, stale, contradiction, and
truncation counts is **STATUS: PLANNED**; the registry emits no counters.

The legacy `legacy-worktree-snapshot` provider bounds traversal at 100,000
product paths, 10 GiB, and 60 seconds, and refuses the subject on exceedance.
`delivery_subject()` enforces no path, byte, or time bound.[^2]

## 7. Quality Scenarios and Verification

| Stimulus | Response | Verification |
| --- | --- | --- |
| Tree changes after a passing test | Exact-subject evidence stales. Path-set evidence survives only unrelated changes with every bound fingerprint unchanged | Selected-path, unrelated-path, policy, criterion, attestation, and lineage mutation fixtures |
| A dependency, configuration, toolchain, command, or environment changes outside selected outputs | The completeness attestor stales path-set evidence, and missing attestation uses exact-subject | Transitive-read, config, argv, toolchain, and environment mutation fixtures |
| Two adapters emit equivalent normalized observations | The canonical policy and truth table produce one verdict | Cross-adapter truth-table corpus |
| `result_authority` changes | Earlier subjects stop counting. Returning to an authority already used can rematch that stretch | Authority-switch fixtures |
| Contradictory evidence arrives | Support is refused until an authorized supersession | Negative fixture |
| A supported review finding is accepted as risk | Review emits contradictory evidence while disposition closes only the review obligation | Review-to-evidence bridge fixture |
| Crash around a review assessment change | One checksummed transaction exposes both the assessment and the receipt delta, or neither | Crash injection before, within, and after append plus index-rebuild fixture |
| A producer returns protected or unbounded output | Evidence-port validation rejects it before durable append | Secret, privacy, size, and raw-output fixtures |
| Spec or working plan changes after initial review | An unapproved spec edit cannot project work. An in-envelope task change reprojects without approval and preserves fresh evidence. A protected-boundary change refuses | Fingerprint, task-revision, boundary-mutation, and task-reprojection fixtures |
| Delivery-control or product files change | Control-plane writes preserve the product hash, and product writes change it | Projection mutation fixture |

## 8. Implementation Mapping

All sources are in `packs/core/.apm/skills/work-loop/scripts/`, and schemas are
in `contracts/delivery/`.

| Element | Source | Verification |
| --- | --- | --- |
| Subject construction | `_supervisor_readiness.py` `delivery_subject`, `_subject_projection.py` `project_delivery_subject` | Projection and schema tests |
| Approval and initial-plan-review registries, legacy importer | `_policy_import.py` | Authority, lineage, mutation, rehydration, and digest-parity tests |
| Evidence transaction log and indexes | `_evidence_store.py` | Atomic framing, crash, index rebuild, and invalidation tests |
| Envelope, freshness, and satisfaction evaluators | `_acceptance.py` | Pure unit tests |
| Review-to-evidence bridge | `_review_bridge.py` | Bridge fixtures |
| Retained legacy provider, no supervisor caller | `_subject_source.py` | Provider tests |

## 9. Decisions, Alternatives, and Risks

Criteria, not tasks, own completion. Task-complete flags, global phases, and
fixed gate lists can claim completion without proving accepted properties.
[ADR-0144](../adr/0144-work-loop-supervisor-owns-procedure.md) holds the
decision.

- **Risk:** weak policy admits irrelevant proof. **Mitigation:** exact
  property and subject fixtures.
- **Risk:** torn appends block rehydration. **Mitigation:** framing, checksums,
  and final-record truncation preserve the last complete prefix.
- **Risk:** volume slows evaluation. **Mitigation:** disposable indexes rebuild
  from the log.

## 10. Import of Legacy Specs and Plans

`start` imports an approved legacy spec and plan through `import_policy`. It
reproduces `approve-plan` canonicalization, verifies both digests, then
atomically appends one spec-policy approval and one initial review bound to the
envelope and baseline plan, which authorizes the current terminal intent.[^7]
The plan digest is audit evidence, not continuing task authority.

Ambiguity, refusal, digest mismatch, missing authority, or either write failure
publishes neither record. Recovery recomputes from the legacy pin.

`reverse_read` in `_policy_import.py` can reconstruct the original pair, and no
supervisor path calls it. The supervisor commits gate evidence directly, so no dual-emit or
shadow path exists (ADR-0144 D7). Task projections use mechanical revisions, not
approvals.

The importer accepts only legacy forms whose missing fields have one mechanical
answer:

| Legacy spec or plan form | Mechanical `acceptance-property.v1` projection | Amendment condition |
| --- | --- | --- |
| Atomic criterion with stable ID and plan tests that cite it | Full result product-tree selector within `delivery-subject.v1`; one named term per cited test; `all` satisfaction; any normalized required-term failure contradicts | Any cited test lacks a deterministic producer or outcome |
| TDD behavior with named test seam and criterion reference | `test-result` observation from the declared test runner | Test seam, runner, or criterion link is absent |
| Goal-based check with exact command and expected result | `command-result` observation with bounded exit and normalized output assertion | Command, expected result, or subject is implicit |
| Manual or visual QA with recorded gesture and observable outcome | `manual-observation` from a named human authority | Gesture, observable outcome, authority, or subject is absent |
| Criterion with multiple unmapped predicates, subjective wording, or no testing-mode link | No projection | An approved semantic-policy amendment supplies every policy field. The working plan may then project matching tasks without separate approval |

The conservative full-tree default stales on any product change. Control records
stay outside it, and no projector invents a narrower policy.

| Responsibility | Owner |
| --- | --- |
| Legacy approval canonicalization and atomic import | Core pack and `agentbundle` contract maintainers |
| Evidence-store operation and recovery drill | `agentbundle` maintainers |

The subject authority's rollout and reversal are in
[product result integration § 10](work-loop-result-integration.md#10-rollout-migration-and-reversal).

[^1]: `packs/core/.apm/skills/work-loop/scripts/_supervisor_readiness.py`:
    `delivery_subject` reads `ws.git.tree_entries(result)`, passes
    `exclusions=(prefix,)` for the spec directory, and calls
    `_subject_projection.py` `project_delivery_subject`.

[^2]: `_subject_source.py`: `MAX_PRODUCT_PATHS`, `MAX_PRODUCT_BYTES`, and
    `MAX_TRAVERSAL_S` apply only inside that module. No `_supervisor_*.py` module
    references it. `contracts/delivery/` holds `delivery-subject.v1` and
    `review-subject.v1` schemas and no `subject-source.v1`.

[^3]: `_acceptance.py`: `is_fresh` and `evaluate_verdict`.

[^4]: `_evidence_store.py`: the framed append log and its replay.

[^5]: `_supervisor_readiness.py`: `result_lineage`, and `supervisor-policy.json`
    `result_authority`.

[^6]: `_review_bridge.py`.

[^7]: `_supervisor_admission.py` calls `_policy_import.py` `import_policy`.

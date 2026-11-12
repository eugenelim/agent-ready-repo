# Spec: Discovery supervisor

- **Status:** Draft
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0162, ADR-0157, RFC-0115, RFC-0116
- **Brief:** brief:everyday-supervisors-delivery
- **Discovery:** none
- **Depends on:** spec:supervisor-manifest-contract, spec:spec-supervisor-core, spec:spec-supervisor-gates
- **Contract:** supervisor-manifest.v1, supervisor-request-envelope.v1; discovery sidecar schema
- **Shape:** service
- **Risk triggers:** security-boundary, structural-interface, persistent-representation

> **Contract:** Scope, Durable Outputs, Agent Rules, Testing Strategy, Acceptance Criteria and accepted risks govern completion; changes require amendment. Design belongs in the plan.

## Outcome

A session drives one opted-in intent from G0 through G3 and resumes from committed records after context loss. The script routes work; workers exercise judgment and humans answer gates. Discovery remains optional.

## What Changes

The product-engineering pack ships `discovery-loop/scripts/discovery-supervisor.py`, its skill-root `supervisor.toml`, session instructions, pack tests and eval updates. One discovery how-to, release records, self-host projections and the page 05 correction complete E2, including its E3 share.

## Scope and Non-goals

V1 admits only `start --adopt <intent-ref>` and Git-tracked discovery state (Tier A), with committed append-only `ledger.jsonl` and one commit per completed step. Admission creates the sidecar in its first tracked commit; an existing untracked directory is refused.

Tier B, local `.context/discovery/` ledgers, and their hash-chain runtime are a later slice. This does not remove the existing sidecar decision-log integrity requirements.

Ticket intake belongs to the ferryman controller brief: `start --from-ticket`, `intake-ticket`, `intake-confirm`, `ticket-<hash>`, tracker profiles and `[intake]` configuration are excluded. A ticket becomes an intent through manual `work-intake`.

Lens width is one; `next --width N` belongs to the pool brief. Services, schedulers, unattended control, new lint implementations, work-loop pin edits and shared E3 routing/prerequisites are excluded.

## Durable Outputs

eugenelim holds every repository, contract, review and risk owner role.

| Output | Destination | Closeout evidence |
| --- | --- | --- |
| Runtime and instructions | product-engineering discovery-loop and discovery-lead | pack suite and live G0–G3 run |
| User procedure | one discovery how-to under guides/product-engineering/how-to | guide checks and install trials |
| Release | pack versions, projections, evals, changelog and check registrations | release gates |
| Architecture | unattended-delivery-runner page 05 | corrected discovery Ready row |

## Agent Rules

### Always do

- Reuse the E0 manifest/envelope and E1 core/gates command, ledger, request, consent and `answer` contracts by reference; apply only the discovery substitutions below.
- Keep the script standard-library-only, installed at user or repository scope, as text the host runs.
- Use repository-scope core for the existing traceability lint; run the real script in verification.
- Preserve sidecar schema, classification, cascade, required reviewer and gate controls from discovery-loop.
- Run answer tests through a pseudo-terminal and record live human answers separately.

### Ask first

- Widening the request kinds, writable paths, answer authority or supported install combinations.
- Changing the sidecar schema or waiving any integrity requirement.

### Never do

- Let the supervisor choose a verdict, approve a gate, edit a slot, or write brief `Status: Ready`.
- Let an agent run `answer` or write answer, verdict, ledger, attempt or park records.
- Import core runtime code, edit work-loop pins, or create a second traceability lint.
- Put internal records or repository-only paths in shipped pack content.

## Shared contract and discovery substitutions

[E1 core](../spec-supervisor-core/spec.md) owns command wrappers, confinement, step commits, replay, protected-content precedence, read-only status, pin checking and bounded untrusted output. [E1 gates](../spec-supervisor-gates/spec.md) owns the human-run `answer`, first-answer rule, confirmation, pending-answer recovery and committed-answer consumption; E2 uses those controls without spec/plan approval or delegation.

The subject is the discovery directory, with the committed intent as its admission anchor. Consent binds the committed sidecar and the gate's named artifacts, including the G3 brief, rather than a spec/plan pair; only the brief's first preamble status token is excluded from its content binding.

The request set is `frame`, `diverge`, `lens`, `decompose`, `reconcile-review`, `lint`, `consent`, plus the E1 `human-decision` needed after G3. Worker kinds use headless/attach/session, lint uses supervisor-run, and both human kinds use human only; no delegation is declared.

Stages are `framing`, `diverging`, `converging`, `decomposing`, `reviewing`, `linting`, `awaiting-human`, `terminal`. The first six kinds pair respectively with the first six stages; both human kinds pair with `awaiting-human`.

Worker requests identify node, phase, input revision, allowed output paths and required slots. Worker results use E1's request envelope with `agent_definition`; reconcile results additionally name a bounded typed findings artifact, while lint exit status and consent answers come only from supervisor-observed evidence.

The phase route follows discovery-loop's gate ladder: frame/G0, strategy and divergence/G1.5, lenses and reconciliation/G2, decomposition/G3. Existing pre-G2 self-coverage, reviewer roster, success-metrics and validation-hook obligations remain prerequisites, not judgments made by the script.

G0, G1.5, G2 and G3 use the existing verdict set: `approve`, `approve-with-constraint`, `redirect/steer`, `explore-alternatives`, `abandon`, `park/defer`, `extend/override`. The gate-state-machine reference owns their transitions and impact-before-blast confirmation; workers apply authorized slot changes, while the supervisor records the human's supplied verdict and answer.

The existing `round_cap` is the round limit; the bound-pause uses consent with `extend/override`, including the new bound and rationale. No second review-round policy is introduced.

Admission pins include the supervisor scripts, manifest, discovery layout and the repository-installed core lint with its execution dependencies, checked against installation records. Root resolution uses configured discovery output, repository default, then read-only marker discovery; ambiguity refuses.

Protected content includes the ledger, answers, decision-log, attempt/store records, bound artifacts and brief Ready token. Ready is permitted only after a matching committed G3 approve answer; commit authorship is irrelevant, and the supervisor never makes that edit.

After G3 approve, a parked `human-decision` tells the human they may set `Status: Ready` themselves or explicitly ask the session agent to do it. It offers acknowledgement after that committed edit or abandonment; acknowledgement hands the bounded artifacts to the existing `work-intake` route, preserving `author-delivery-brief continue` readiness checks.

## Testing Strategy

- **T1 (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0043):** TDD; admission and interface.
- **T2 (AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0017, AC-0018):** TDD with real lint; routing and lint.
- **T3 (AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, AC-0029, AC-0030, AC-0031):** TDD; consent and persistence.
- **T4 (AC-0032, AC-0033):** integration and manual QA; pack and live evidence.
- **T5 (AC-0034, AC-0035):** goal-based checks; instructions and eval.
- **T6 (AC-0036, AC-0037):** goal-based checks; how-to.
- **T7 (AC-0038, AC-0039, AC-0040, AC-0041):** goal-based checks; release.
- **T8 (AC-0042):** goal-based check; architecture.

## Acceptance Criteria

- [ ] **AC-0001.** `start --adopt` admits a committed intent into a new tracked sidecar without changing the intent's bytes.
- [ ] **AC-0002.** Admission refuses without writes for the closed invalid-adoption set: absent or uncommitted intent, absent Git repository, existing untracked or ignored discovery directory, ambiguous discovery root, duplicate active admission, dirty checkout, detached HEAD or default branch.
- [ ] **AC-0003.** Every subject-path operation meets E1 core's confinement contract with the discovery subject substitution.
- [ ] **AC-0004.** No work request is issued for an intent without an admitted sidecar.
- [ ] **AC-0005.** The shipped manifest validates against the E0 schema.
- [ ] **AC-0006.** The manifest's request-kind set equals the kinds observed across the release's driven runs.
- [ ] **AC-0007.** Every emitted request conforms to the shared envelope and discovery kind/stage contract.
- [ ] **AC-0008.** At most one lens request is open at a time.
- [ ] **AC-0009.** Each next phase equals the gate-ladder route for the committed sidecar state.
- [ ] **AC-0010.** A worker result is refused when any required slot fails the existing sidecar schema or the required `proposed` status.
- [ ] **AC-0011.** A result with any changed path outside its request's declared write set is refused without writes.
- [ ] **AC-0012.** A reconcile report from an agent definition used by a lens writer in that round is refused.
- [ ] **AC-0013.** G2 consent is unavailable while any required discovery reviewer result is absent.
- [ ] **AC-0014.** Every lint result equals the observed exit of the existing core `lint-traceability.py` on the discovery input in the required mode.
- [ ] **AC-0015.** Lens-round lint uses default mode.
- [ ] **AC-0016.** G2 and G3 consent are blocked by a non-zero strict lint exit on their current input revision.
- [ ] **AC-0017.** Missing repository-scope core lint prevents admission in both supported supervisor installation scopes.
- [ ] **AC-0018.** Reaching `round_cap` yields bound-pause consent before another round opens.
- [ ] **AC-0019.** Every gate answer belongs to the existing discovery verdict enum.
- [ ] **AC-0020.** Gate advancement requires the matching committed human answer under E1 gates' consumption contract.
- [ ] **AC-0021.** Each accepted human gate answer has exactly one corresponding recorded verdict row.
- [ ] **AC-0022.** Each accepted verdict routes according to the gate-state-machine transition for that verdict.
- [ ] **AC-0023.** Every answer record states `identity: unverified`.
- [ ] **AC-0024.** `answer` meets E1 gates' terminal, confirmation, duplicate and interruption controls under the discovery binding substitution.
- [ ] **AC-0025.** Every completed step has exactly one committed ledger append under E1 core's step contract.
- [ ] **AC-0026.** Restart preserves the open request identity under E1 core's replay contract.
- [ ] **AC-0027.** Sidecar/ledger disagreement refuses without selecting either as authoritative replacement state.
- [ ] **AC-0028.** Every protected-content violation refuses under E1 core's precedence with the discovery protected set.
- [ ] **AC-0029.** No supervisor-owned write changes a slot or the brief Ready token.
- [ ] **AC-0030.** G3 approve leads to the parked human-decision defined above.
- [ ] **AC-0031.** Every user-visible untrusted field meets E1 core's output policy across requests, status, refusals, stdout, stderr and relayed lint diagnostics.
- [ ] **AC-0032.** The product-engineering pack suite passes against both supported install combinations.
- [ ] **AC-0033.** A recorded live G0–G3 run resumes after context loss with the same pending request and no lost or repeated record.
- [ ] **AC-0034.** Shipped discovery instructions assign every request kind its declared worker mode and result shape.
- [ ] **AC-0035.** The discovery-loop eval harness includes a supervisor-driven parked-gate resume case with a human-only answer expectation.
- [ ] **AC-0036.** One discovery how-to covers both supported install combinations and the adopt-to-G3 human procedure.
- [ ] **AC-0037.** The guide passes the repository's title, index and repository-only-reference checks.
- [ ] **AC-0038.** Both product-engineering version files equal the next minor version above fetched main.
- [ ] **AC-0039.** The release's self-host projections equal regenerated source output.
- [ ] **AC-0040.** The release changelog fragment passes validation.
- [ ] **AC-0041.** The release passes the pack-test boundary and parity checks with its new suites registered.
- [ ] **AC-0042.** Page 05's discovery session row assigns Ready writing to the human or explicitly requested session agent after recorded G3 approve.

- [ ] **AC-0043.** Every admission-reading verb refuses changed admission pins before processing state.

## Follow-ons

The repository owner eugenelim owns Tier B, pool width and controller ticket intake in later slices. E1 owns shared routing and install prerequisites, including the statement that ferryman is later and optional.

## Assumptions

- **Settled D-A/D-B:** Tier A and adopt-only admission scope the RFC's broader design; admission atomically creates and tracks a new sidecar rather than accepting an existing untracked tree.
- **Settled D-C:** the real lint's docstring and `main()` give exit 0 for clean/informational results, exit 1 for dangling edges/cycles in all modes, and exit 1 for structural orphans or UNREACHABLE nodes under strict mode.
- **Accepted limit:** lint exit 0 proves neither semantic connectedness nor validation; unresolved cross-repository references remain informational, and `main()` also returns 0 on unexpected checker exceptions.
- **Settled D-D:** recording a supplied verdict is not choosing one; Ready follows the recorded G3 approve and is never supervisor-written.
- **Accepted risk:** session answer identity is unchecked under the brief's identity-only waiver; profile names do not prove independent humans or agents.
- **Unresolved integrity prerequisite:** sidecar-schema's anchored decision log and agent-untokened attestation exceed what E1's file/terminal controls prove; no other control is waived. Repository owner eugenelim settles the conforming session mechanism before approval; it changes gate admission, answer persistence and tests.
- **Unresolved format binding:** E1 gates lists open answer-syntax/payload gaps, while discovery needs verdict rationale, constraints, impact confirmation and bound changes. Repository owner eugenelim settles the exact compatible payload before approval; it changes the public answer schema and verdict-transition fixtures.
- **Unresolved bounds:** RFC-0116 requires bounded slot validation but supplies no slot byte limit. Repository owner eugenelim settles the limit before approval; it changes boundary tests and input refusals.
- **Unresolved binding inventory:** the exact per-gate artifact/write set and drift-safe treatment of authorized slot transitions need confirmation against the implemented E1 seam. Repository owner eugenelim settles them before approval; they change digest invalidation and permitted edits, without changing D-D.

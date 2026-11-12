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

> **Contract:** Scope, Shared contract, Durable Outputs, Agent Rules, Testing Strategy, Acceptance Criteria and accepted risks govern completion; changes require amendment. Design belongs in the plan.

## Outcome

One opted-in intent moves from G0 through G3 with committed, resumable records. Workers exercise judgment; humans answer gates; the supervisor routes work.

## Scope and Non-goals

Tier A admits only `start --adopt <intent-ref>` into a newly committed sidecar, with append-only `ledger.jsonl` and one commit per step. Discovery remains optional; Tier B, `.context/discovery`, ticket intake, pool width, services, unattended control and new lint implementations are excluded.

E2 ships the product-engineering script, manifest, instructions, evals, how-to, release records, projections and page 05 correction. Work-loop pins and shared E3 routing/prerequisites stay with E1.

## Durable Outputs

eugenelim holds every owner role.

| Output | Destination | Evidence |
| --- | --- | --- |
| Runtime/instructions | discovery-loop and discovery-lead | pack tests, live run |
| Procedure | guides/product-engineering/how-to | indexed guide checks |
| Release | versions, projections, evals, changelog, registrations | release gates |
| Architecture | unattended-delivery-runner page 05 | corrected Ready row |

## Agent Rules

### Always do

- Reuse E0 and E1 contracts subject to the substitutions below.
- Keep runtime standard-library-only; support user/repository supervisor with repository core.
- Preserve discovery classification, cascade, reviewer and gate controls.
- Test answers through pseudo-terminals; record real human answers separately.

### Ask first

- Widening kinds, paths, authority, installation combinations or schema.

### Never do

- Let the supervisor choose verdicts, edit worker-owned slots or write Ready.
- Let agents run `answer` or write supervisor-owned records.
- Import core runtime, edit work-loop pins or ship internal citations.

## Shared contract and discovery substitutions

[E1 core](../spec-supervisor-core/spec.md) supplies commands, wrappers, step commits, replay, confinement, protection precedence and output policy. [E1 gates](../spec-supervisor-gates/spec.md) supplies human-only answers, confirmation, first-answer and recovery controls; discovery replaces its pair, answer payload and human-decision options, without delegation.

### Admission and pins

`<intent-ref>` matches `intent:[a-z0-9]+(?:-[a-z0-9]+)*`, resolved uniquely to a committed intent. Paths are repository-relative POSIX segments matching `[A-Za-z0-9._][A-Za-z0-9._-]*`, excluding `.`/`..`; path-bearing node ids use one such segment, maximum 64 characters, never raw typed ids. Assigned run/request path segments use that same grammar; all regex matches consume the whole value.

Root resolution is configured `[discovery].output_dir`, repository default `docs/discovery`, then read-only marker discovery. All three require repository confinement outside the git directory; `.context/discovery` is refused even when trackable.

Manifest `pinned_files` contains only skill-root scripts at every depth except `__pycache__`, manifest and carried policy/schema files, in E0 portable form. Admission alone holds external pins: repository core `lint-traceability.py`, `intent_delivery_relations.py`, `_file_safety.py`, selected `agentbundle-layout.toml` or absence, and interpreter identity.

Installed files match adapter/pack `files.sha` in repository `.agentbundle-state.toml` or user `<user-root>/.agentbundle/state.toml`; core always uses the repository record. Layout comparison remains the explicit assumption below; interpreter identity is captured at admission. Missing installation hashes refuse `installation-record-mismatch`; added/removed/changed pinned files refuse `supervisor-changed`.

Reversible resource defaults are 1 MiB per slot file, 256 slot files, tree depth 6 and 1 MiB ledger read per verb. eugenelim may amend these defaults; excess refuses `slot-too-large`, `slot-count-limit`, `tree-depth-limit` or `ledger-too-large`, without writes.

### Requests and routing

This closed table replaces core AC-0046's phase payload mapping.

| Phase | Kind / stage | Lint |
| --- | --- | --- |
| G0 frame | frame / framing | none |
| G1 de-risk | lens / converging | default |
| G1 decompose | decompose / decomposing | default |
| pre-G1.5 divergence | diverge / diverging | none |
| G1.5 frame-domain | frame / framing | none |
| convergence lenses | lens / converging | default |
| pre-G2 self-coverage; G2 decision-brief | lens / converging | default |
| G2 reviews | reconcile-review / reviewing | strict |
| G3 decompose | decompose / decomposing | strict |
| lint checkpoint | lint / linting | phase mode |
| gate or bound pause | consent / awaiting-human | preceding phase |
| post-G3 | human-decision / awaiting-human | none |

The five worker kinds declare headless/attach/session; lint declares supervisor-run; consent/human-decision declare human only. `next` exposes lint requests, executed only by the supervisor.

Beyond E0's five envelope keys, every request has exactly `node, phase, input_revision, allowed_paths, required_slots`; reconcile adds `role, exclude_profile, findings_path`, lint adds `mode`, consent adds `gate, sidecar_digest, brief_digest, verdicts, impact_digest`, human-decision adds `options, sidecar_digest, brief_digest`. Non-worker write sets are empty; unused brief/impact digests are null.

Replacing core AC-0010, results are `{request_id,facts}`: frame/diverge/lens/decompose facts are exactly `{agent_definition}`; reconcile facts are `{agent_definition,outcome,findings_path}`; lint/consent/human-decision facts are `{}`. E1 bounds/grammar apply; outcome is available/unavailable, and unavailable ends `reviewer-unavailable` without later requests.

Findings use the derived ignored `.context/reviews/<run_id>/<request_id>.json`, a link-free regular UTF-8 file ≤1 MiB, duplicate-key-free, depth ≤16. Its closed schema is `{schema_version:1,findings:[{id,severity,reference,disposition}]}`: at most 256 rows, id `[A-Za-z0-9_-]{1,64}`, severity blocker/concern/nit, disposition open/resolved/deferred, reference null or E1 checked reference; unavailable requires null path and no artifact.

G2 prerequisites are the decision-brief's completed seven-module `coverage-record` with resolved fresh-context findings, available `discovery-threat-reviewer` and `discovery-reliability-reviewer` results (plus installed optional reviewers), proposed `decision-brief.success_metrics`, and proposed `assumption-test.validation_hook`/`validation-plan` for every load-bearing assumption. Success metrics contain outcome/North-Star/done-criterion; hooks contain kill-condition/activity; meaning remains worker judgment.

Lint uses `--root <admitted-initiative>` so marker discovery selects only its `_state/traceability.json`; a missing/invalid admitted graph, competing nested graph or conflicting local/user layout selection refuses `lint-subject-mismatch`. Default failure blocks convergence (`lint-failed`); strict failure blocks G2/G3.

Lint execution uses the admission-pinned interpreter, isolated mode, no bytecode, scrubbed environment and shell-free argv, with 120-second timeout and 1 MiB combined captured output. Timeout, signal or overflow records failed lint, never exit 0.

A security-boundary crossing with only baseline reviewer depth uses the same risk-trigger consent route; reviewer depth never silently substitutes for full coverage. Cascade re-runs count against cost counters.

### Answers and binding

Consent binds the whole committed sidecar tree plus the G3 brief at G3, excluding supervisor-owned ledger/answers; only the brief's first preamble status token is masked. Any issue-to-answer content change follows core AC-0044's voiding table: rerun in-progress work; below cap reopen review; at cap issue fresh unreviewed bound consent.

Post-answer drift refuses `stale-digest`, except supervisor decision recording and named answer-authorized worker transitions; those carry ratified/stale slot status or parked/abandoned node lifecycle under sidecar-schema's namespace table. Proposal results remain proposed; no other promotion is authorized. At G3, decision-log recording follows the terminal binding check and worker transitions follow acknowledgement, so neither alters the tree awaiting that check.

The seven canonical verdicts are `approve`, `approve-with-constraint`, `redirect/steer`, `explore-alternatives`, `abandon`, `park/defer`, `extend/override`. Normal gates and fired G1 risk triggers offer all seven; bound pauses offer extend/override, narrow (constraint alias), park/defer, abandon, including round, cost, concentration, depth and open-sub-idea bounds.

Replacing gates AC-0004, each consent answer has exactly `run_id,request_id,by,at,identity,gate,verdict,rationale,sidecar_digest,brief_digest,park_commit` plus the fields below. E1 identity/time/by grammar applies; rationale/constraint are nonempty strings ≤512 characters, digests lowercase SHA-256, and `new_bound` is `{name,value}` with `name` in `round_cap,cost_budget,concentration,max_depth,max_open_sub_ideas`; cost is positive finite, concentration is in (0,1], and other values are positive integers.

| Verdict | Required extra fields; all others refused |
| --- | --- |
| approve; explore-alternatives; park/defer | none |
| approve-with-constraint | constraint |
| redirect/steer; abandon | impact_digest matching the shown impact list |
| extend/override | new_bound |

The supervisor checks presence, grammar and bounds only; it never judges rationale quality or chooses a verdict. Gate-state-machine transitions and impact-before-blast confirmation apply to every slot-changing verdict. Workers classify/redact content, never commit regulated facts verbatim, and keep externally sourced slots inert; the supervisor checks markers and routes one-way-door/over-threshold cascades to consent.

Replacing gates AC-0007, post-G3 options are exactly acknowledge/abandon; unoffered options refuse `option-not-offered`. Human-decision answers contain exactly E1 base fields plus `option`; acknowledge requires a Ready commit after the matching G3 approve and unchanged bound artifacts, else `ready-commit-pending` or `stale-digest`.

Acknowledge ends `handoff-ready`; abandon ends `abandoned`. Handoff is an instruction to the human/session agent to invoke `work-intake`, preserving readiness checks, never a supervisor write or delegation.

## Testing Strategy

- **T1 (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0017, AC-0043, AC-0049, AC-0053, AC-0055, AC-0061):** TDD with real Git/lint; plan Tests supply cases.
- **T2 (AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0018, AC-0048, AC-0050, AC-0051, AC-0052, AC-0056, AC-0057, AC-0058, AC-0059, AC-0060):** TDD with real Git/lint; plan Tests supply cases.
- **T3 (AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, AC-0029, AC-0030, AC-0031, AC-0044, AC-0045, AC-0046, AC-0047, AC-0062):** TDD with real Git/lint; plan Tests supply cases.
- **T4 (AC-0032, AC-0033):** integration/manual QA; plan Tests supply cases.
- **T5 (AC-0034, AC-0035, AC-0054):** goal-based checks; plan Tests supply cases.
- **T6 (AC-0036, AC-0037):** goal-based checks; plan Tests supply cases.
- **T7 (AC-0038, AC-0039, AC-0040, AC-0041):** goal-based checks; plan Tests supply cases.
- **T8 (AC-0042):** goal-based checks; plan Tests supply cases.

## Acceptance Criteria

- [ ] **AC-0001.** `start --adopt` admits a committed intent into a new tracked sidecar without changing the intent's bytes.
- [ ] **AC-0002.** Admission refuses without writes for the invalid-adoption set: missing/uncommitted intent (`intent-not-committed`), no repository (`repository-required`), untracked/ignored directory (`sidecar-untracked`/`sidecar-ignored`), ambiguity (`root-ambiguous`), active/ended admission (`already-admitted`/`admission-ended`), tracked sidecar without ledger (`ledger-missing`), dirty/detached/default/unknown branch (`checkout-dirty`/`detached-head`/`default-branch-refused`/`default-branch-unknown`), or ignored, untrackable, outside-repository or Tier-B root (`root-not-trackable`/`path-unsafe`/`tier-b-refused`).
- [ ] **AC-0003.** Every read, digest, enumeration or write of slots at any depth, decision log, answers, ledger, adopted intent, G3 brief, result/findings files and resolved root refuses without writes on non-confined/git-directory paths, links/reparse points, non-directory parents, non-regular/multiply-linked files or identity changes at open.
- [ ] **AC-0004.** No work request is issued for an intent without an admitted sidecar.
- [ ] **AC-0005.** The shipped manifest validates against the E0 schema.
- [ ] **AC-0006.** The manifest equals the declared kind/mode set.
- [ ] **AC-0007.** Every emitted request conforms to the shared envelope and discovery kind/stage contract.
- [ ] **AC-0008.** At most one lens request is open at a time.
- [ ] **AC-0009.** Each next phase equals the gate-ladder route for the committed sidecar state.
- [ ] **AC-0010.** Every accepted worker result meets the sidecar schema and its proposal or answer-authorized transition status contract.
- [ ] **AC-0011.** A result with any changed path outside its request's declared write set is refused without writes.
- [ ] **AC-0012.** A reconcile report from an agent definition used by a lens writer in that round is refused.
- [ ] **AC-0013.** G2 consent is unavailable until every named prerequisite has its required status.
- [ ] **AC-0014.** Each lint record matches the real core lint outcome on only the admitted initiative graph.
- [ ] **AC-0015.** Lens-round lint uses default mode.
- [ ] **AC-0016.** G2 and G3 consent are blocked by a non-zero strict lint exit on their current input revision.
- [ ] **AC-0017.** Missing repository-scope core lint prevents admission in both supported supervisor installation scopes.
- [ ] **AC-0018.** Every reached bound in the closed bound set, including any committed `paused-at-bound`, yields bound-pause consent before further work.
- [ ] **AC-0019.** Every accepted consent answer matches the closed discovery answer schema.
- [ ] **AC-0020.** Gate advancement requires the matching committed human answer under E1 gates' consumption contract.
- [ ] **AC-0021.** Each accepted human gate answer has exactly one corresponding recorded verdict row.
- [ ] **AC-0022.** Each accepted verdict routes according to the gate-state-machine transition for that verdict.
- [ ] **AC-0023.** Every answer record states `identity: unverified`.
- [ ] **AC-0024.** `answer` meets E1 gates' terminal, confirmation, duplicate and interruption controls under the discovery binding substitution.
- [ ] **AC-0025.** Every completed step has exactly one committed ledger append under E1 core's step contract.
- [ ] **AC-0026.** Restart preserves the open request identity under E1 core's replay contract.
- [ ] **AC-0027.** Sidecar/ledger disagreement refuses without selecting either as authoritative replacement state.
- [ ] **AC-0028.** Every protected-content violation refuses under E1 precedence for ledger, answers, decision-log, attempts/store, bound artifacts and Ready token.
- [ ] **AC-0029.** No supervisor-owned write changes a worker-owned slot or the brief Ready token.
- [ ] **AC-0030.** G3 approve leads to the parked human-decision defined above.
- [ ] **AC-0031.** Every visible untrusted field meets E1 output limits across requests, status, refusals, answer prompts, stdout/stderr and relayed lint diagnostics.
- [ ] **AC-0032.** The product-engineering pack suite passes against both supported install combinations.
- [ ] **AC-0033.** A live non-sensitive fixture G0–G3 receipt shows context-loss resume with identical pending request and no lost/repeated record.
- [ ] **AC-0034.** Shipped discovery instructions assign every request kind its declared worker mode and result shape.
- [ ] **AC-0035.** The discovery-loop eval harness includes a supervisor-driven parked-gate resume case with a human-only answer expectation.
- [ ] **AC-0036.** One discovery how-to covers the closed procedure set: both install combinations, adopt-to-G3 human steps and the O1 integrity limit/expiry.
- [ ] **AC-0037.** The guide passes the repository's title, index and repository-only-reference checks.
- [ ] **AC-0038.** Both product-engineering version files equal the next minor version above fetched main.
- [ ] **AC-0039.** The release's self-host projections equal regenerated source output.
- [ ] **AC-0040.** The release changelog fragment passes validation.
- [ ] **AC-0041.** The release passes the pack-test boundary and parity checks with its new suites registered.
- [ ] **AC-0042.** Page 05's discovery session row assigns Ready writing to the human or explicitly requested session agent after recorded G3 approve.
- [ ] **AC-0043.** Every admission-reading verb refuses changed local or external admission pins before state processing.
- [ ] **AC-0044.** Post-G3 acknowledgement refuses until the Ready commit and bound-artifact conditions hold.
- [ ] **AC-0045.** Each post-G3 option yields its declared terminal reason.
- [ ] **AC-0046.** The only permitted Ready edit changes the first preamble status token after matching committed G3 approve with every other brief byte unchanged.
- [ ] **AC-0047.** Every other Ready edit refuses `protected-content-changed` regardless of author.
- [ ] **AC-0048.** A fired G1 risk trigger yields consent offering the declared normal verdict set.
- [ ] **AC-0049.** Every admission pin has the declared scope and comparison source.
- [ ] **AC-0050.** Every accepted request/result conforms to its closed discovery shape.
- [ ] **AC-0051.** An unavailable reviewer ends the run with reason `reviewer-unavailable`.
- [ ] **AC-0052.** A non-zero default lint outcome blocks convergence with `lint-failed`.
- [ ] **AC-0053.** Every admission commit tracks every created sidecar file.
- [ ] **AC-0054.** Shipped discovery-loop/discovery-lead text contains no conflicting no-engine or upstream-supervisor claim while retaining prose fallback.
- [ ] **AC-0055.** Every path-bearing identifier meets the declared grammar.
- [ ] **AC-0056.** A worker result with any unclassified slot or sensitive/regulated slot lacking a redact-or-surface record refuses `classification-required` without writes.
- [ ] **AC-0057.** Every lint invocation satisfies the declared subprocess limits.
- [ ] **AC-0058.** Every one-way-door transition waits for matching consent.
- [ ] **AC-0059.** An invalidation exceeding one-third of active nodes or eight nodes waits for human impact confirmation.
- [ ] **AC-0060.** A result containing externally sourced slots without `untrusted:true` refuses `untrusted-marker-required`.
- [ ] **AC-0061.** Every resource-limit violation yields its named refusal without writes.
- [ ] **AC-0062.** Every recorded decision row satisfies the declared chain-tip integrity contract.

## Follow-ons

eugenelim owns Tier B, pool width, controller intake and T9's separate E1 gates amendment under that spec's release.

## Assumptions

- **Settled D-A/D-B:** Tier A and adopt-only admission scope the RFC's broader design; admission atomically creates and tracks a new sidecar rather than accepting an existing untracked tree.
- **Settled D-C:** the real lint's docstring and `main()` give exit 0 for clean/informational results, exit 1 for dangling edges/cycles in all modes, and exit 1 for structural orphans or UNREACHABLE nodes under strict mode.
- **Accepted limit:** lint exit 0 proves neither semantic connectedness nor validation; unresolved cross-repository references remain informational, and `main()` also returns 0 on unexpected checker exceptions.
- **Settled D-D:** recording a supplied verdict is not choosing one; Ready follows the recorded G3 approve and is never supervisor-written.
- **Accepted risk:** session answer identity is unchecked under the brief's identity-only waiver; profile names do not prove independent humans or agents.
- **Time-limited accepted risk (O1):** eugenelim accepts supervisor-written hash-chained decision-log rows with the tip committed in the ledger; spec and how-to describe tamper-evidence only against unanchored edits. Rows use sidecar-schema's canonical-field-order SHA-256 chain and supervisor clock, with no claimed external actor/time attestation. The risk ends when ferryman's scribe runs supervisors and anchors the tip outside agent reach; the Ready brief is unchanged.
- **Inherited E1 risks:** forged pseudo-terminal answers, single-line ledger steps, approval commits, history rewrites, self-reported reviewer independence, invisible attempt/store forgery and checker/pin replacement remain possible until guard/scribe and release comparison; content checks close none of these attribution gaps.
- **Narrow spelling:** SKILL.md offers narrow but its schema has seven verdicts; this draft treats narrow as approve-with-constraint, requiring constraint/re-convergence. eugenelim settles alias versus eighth verdict before approval; it changes answer grammar and bound fixtures.
- **Layout provenance:** layout is adopter-owned, not guaranteed installation-record content; admission captures its digest/absence rather than claiming an installed hash exists. eugenelim settles the required comparison source before approval; it changes admission pin evidence.

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

> **Contract:** Scope, Shared contract, Durable Outputs, Agent Rules, Testing Strategy, Acceptance Criteria and accepted risks require amendment; plan owns Design.

## Outcome

An opted-in intent moves through G0–G3 with resumable records, worker judgment and human gate answers.

## Scope and Non-goals

Optional Tier A admits only `start --adopt <intent-ref>` into a committed sidecar, append-only `ledger.jsonl`, one commit/step. Excluded: Tier B, `.context/discovery`, ticket intake, pool width, services, unattended control, new lints.

E1 retains work-loop pins and shared E3 routing/prerequisites.

## Durable Outputs

eugenelim owns all roles.

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

[E1 core](../spec-supervisor-core/spec.md) governs commands/wrappers/commits/replay/confinement/protection/output. [E1 gates](../spec-supervisor-gates/spec.md) governs human answers/confirmation/first-answer/recovery; discovery substitutes pair, answer payload and human-decision options, without delegation.

### Admission and pins

`<intent-ref>` matches `intent:[a-z0-9]+(?:-[a-z0-9]+)*`, resolved uniquely to a committed intent. Paths are repository-relative POSIX segments matching `[A-Za-z0-9._][A-Za-z0-9._-]*`, excluding `.`/`..`; path-bearing node ids use one such segment, maximum 64 characters, never raw typed ids. Run/request segments share this grammar; matches consume whole values.

Root resolution is configured `[discovery].output_dir`, repository default `docs/discovery`, then read-only marker discovery. Each requires repository confinement outside git; `.context/discovery` is refused even when trackable.

Manifest `pinned_files` contains only skill-root scripts at every depth except `__pycache__`, manifest and carried policy/schema files, in E0 portable form. External admission pins: repository core `lint-traceability.py`, `intent_delivery_relations.py`, `_file_safety.py`, selected `agentbundle-layout.toml` or absence, and interpreter identity.

Installed files match adapter/pack `files.sha` in repository `.agentbundle-state.toml` or user `<user-root>/.agentbundle/state.toml`; core always uses the repository record. Layout uses the Assumption; admission captures interpreter identity. Missing installation hashes refuse `installation-record-mismatch`; added/removed/changed pinned files refuse `supervisor-changed`.

Resource defaults in this spec are 1 MiB/slot, 256 slot files, depth 6 and 1 MiB/ledger; excess refuses `slot-too-large`, `slot-count-limit`, `tree-depth-limit`, `ledger-too-large` without writes. Supervisor decision-log/ledger appends are outside slot limits; prospective ledger overflow refuses before accepting work that needs the append. Resource amendments change this spec, not executable pins; active-run amendments remain unsettled below.

For slot size/count/depth refusals, restore pending worker changes to the last accepted bounded tree, then `next`/`report`; protected records remain intact. Interpreter drift refuses `supervisor-changed`: restore the admission interpreter identity, then retry the refused command. Already-committed excess, ledger exhaustion and unavailable interpreter restoration require the recovery decision below; no reset or repin command exists.

### Requests and routing

Core AC-0046 substitution:

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

Write sets derive from discovery-loop's [phase roster](../../../packs/product-engineering/.apm/skills/discovery-loop/SKILL.md#the-gate-ladder) and [sidecar schema](../../../packs/product-engineering/.apm/skills/discovery-loop/references/sidecar-schema.md). Initiative-relative paths permit edits only for the request node/declared affected set.

| Kind | Closed proposal write set |
| --- | --- |
| frame | `_state/{blackboard,open-questions,traceability,plan-tree,meta}.json`; G1.5 also `domain-framing.md`, `scope-boundary.md` |
| diverge | `_state/{blackboard,open-questions,traceability,plan-tree,meta}.json` (candidate shapes) |
| lens | `_state/{blackboard,open-questions,traceability,meta}.json`, `journey-map.md`, `service-blueprint.md`, `screens/<node>.md`, `decision-brief.md` |
| decompose | `_state/{blackboard,open-questions,traceability,plan-tree,meta}.json`, `backlog.md`; G3 also `delivery-contracts/<node>.md`, `delivery-briefs/<node>.md` |
| reconcile-review | derived findings file only; no sidecar writes |

G3 destinations are initiative-confined; the designated delivery brief is bound. Answer-authorized writes replace proposal sets with the schema's per-verdict set: approve—gate slot/node ratification and meta advance; constraint—scope-boundary and touched slots/node re-convergence; steer—intent steer, confirmed stale slots/edges/node; alternatives—node divergence/candidates; abandon—subtree stale slots/edges and abandoned node; defer—parked node/backlog; extend—named bound and prior lifecycle. These use only the table's corresponding artifact paths; decision-log/ledger/answers remain supervisor-owned.

Worker modes: headless/attach/session; lint: supervisor-run; consent/human-decision: human only. `next` exposes supervisor-executed lint requests.

Beyond E0’s five keys, requests contain exactly `node, phase, input_revision, allowed_paths, required_slots`; reconcile adds `role, exclude_profile, findings_path`, lint adds `mode`, consent adds `gate, sidecar_digest, brief_digest, verdicts, impact_digest, findings`, human-decision adds `options, sidecar_digest, brief_digest`. Non-worker write sets are empty; consent `findings` contains only assigned ids and valid checked references for open findings; unused brief/impact digests are null.

Core AC-0010 substitution: `{request_id,facts}`: frame/diverge/lens/decompose facts are exactly `{agent_definition}`; reconcile facts are `{agent_definition,outcome,findings_path}`; lint/consent/human-decision facts are `{}`. E1 bounds/grammar apply; outcome: available/unavailable; unavailable ends `reviewer-unavailable`.

Findings use the derived ignored `.context/reviews/<run_id>/<request_id>.json`, a link-free regular UTF-8 file ≤1 MiB, duplicate-key-free, depth ≤16. Its closed schema is `{schema_version:1,findings:[{id,severity,reference,disposition}]}`: at most 256 rows, id `[A-Za-z0-9_-]{1,64}`, severity blocker/concern/nit, disposition open/resolved/deferred, reference null or E1 checked reference; unavailable requires null path and no artifact.

Later findings-digest differences refuse `review-changed`.

G2 prerequisites are the decision-brief's completed seven-module `coverage-record` with resolved fresh-context findings, available `discovery-threat-reviewer` and `discovery-reliability-reviewer` results (plus installed optional reviewers), proposed `decision-brief.success_metrics`, and proposed `assumption-test.validation_hook`/`validation-plan` for every load-bearing assumption. Metrics: outcome/North-Star/done-criterion; hooks: kill-condition/activity; meaning is worker judgment.

Lint uses `--root <admitted-initiative>` so marker discovery selects only its `_state/traceability.json`; a missing/invalid admitted graph, competing nested graph or conflicting local/user layout selection refuses `lint-subject-mismatch`. Default failure blocks convergence (`lint-failed`); strict failure blocks G2/G3.

The lint process tree permits only admission-pinned application source and the admission-identified Python runtime/stdlib. Its environment is exactly `LANG=C`, `LC_ALL=C`, `TZ=UTC`, `HOME` pointing to an empty private directory, and on Windows admission-captured `SYSTEMROOT`; no inherited entries survive. Shell-free execution has a 120-second tree timeout and 1 MiB combined output; timeout, signal or overflow anywhere records failed lint.

A boundary crossing with baseline-only review depth requires risk-trigger consent, never silent degradation. Cascade re-runs count against cost counters.

### Answers and binding

Consent binds the whole committed sidecar tree plus the G3 brief at G3, excluding supervisor-owned ledger/answers; only the brief's first preamble status token is masked. Issue-to-answer changes follow core AC-0044: rerun in-progress work; below cap reopen review; at cap issue fresh unreviewed bound consent.

Post-answer drift refuses `stale-digest`, except supervisor decision recording and named answer-authorized worker transitions; those carry ratified/stale slot status or parked/abandoned node lifecycle under sidecar-schema's namespace table. Proposal results remain proposed; no other promotion is authorized.

Only G3 `approve` defers worker transitions until acknowledgement; its verdict row records before Ready, with the resulting tree bound for acknowledgement. Every other G3 verdict records immediately and authorizes its normal transition.

The seven canonical verdicts are `approve`, `approve-with-constraint`, `redirect/steer`, `explore-alternatives`, `abandon`, `park/defer`, `extend/override`. Normal/fired-G1 gates offer all seven; bound pauses offer extend/override, narrow (constraint alias), park/defer, abandon, including round, cost, concentration, depth and open-sub-idea bounds.

Gates AC-0004 substitution: consent answers contain exactly `run_id,request_id,by,at,identity,gate,verdict,rationale,sidecar_digest,brief_digest,park_commit` plus the fields below. E1 identity/time/by grammar applies; rationale/constraint are nonempty strings ≤512 characters, digests lowercase SHA-256, and `new_bound` is `{name,value}` with `name` in `round_cap,cost_budget,concentration,max_depth,max_open_sub_ideas`; cost is positive finite, concentration is in (0,1], and other values are positive integers.

| Verdict | Required extra fields; all others refused |
| --- | --- |
| approve; explore-alternatives; park/defer | none |
| approve-with-constraint | constraint |
| redirect/steer; abandon | impact_digest matching the shown impact list |
| extend/override | new_bound |

The supervisor checks presence/grammar/bounds, never rationale quality or verdict choice. Every slot-changing verdict requires gate-state-machine transitions and impact-before-blast confirmation. Workers classify/redact content, never commit regulated facts verbatim, and keep externally sourced slots inert; the supervisor checks markers and routes one-way-door/over-threshold cascades to consent.

Gates AC-0007 substitution: post-G3 options are acknowledge/abandon; unoffered options refuse `option-not-offered`. Human-decision answers contain exactly E1 base fields plus `option`; acknowledge requires a Ready commit after the matching G3 approve and unchanged bound artifacts, else `ready-commit-pending` or `stale-digest`.

Acknowledge ends `handoff-ready`; abandon ends `abandoned` only after any Ready token reverts to Draft. Abandon or stale post-G3 approval permits only that token reversion, with other bytes unchanged; `next`/`report` wait at `revert-pending` before terminal disposition while Ready persists. Handoff instructs human/session-agent `work-intake` invocation, preserving readiness checks without delegation.

## Testing Strategy

- **T1 (AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006, AC-0007, AC-0008, AC-0017, AC-0043, AC-0049, AC-0053, AC-0055, AC-0061):** TDD.
- **T2 (AC-0009, AC-0010, AC-0011, AC-0012, AC-0013, AC-0014, AC-0015, AC-0016, AC-0018, AC-0048, AC-0050, AC-0051, AC-0052, AC-0056, AC-0057, AC-0058, AC-0059, AC-0060, AC-0064, AC-0065, AC-0066, AC-0067, AC-0069, AC-0070):** TDD.
- **T3 (AC-0019, AC-0020, AC-0021, AC-0022, AC-0023, AC-0024, AC-0025, AC-0026, AC-0027, AC-0028, AC-0029, AC-0030, AC-0031, AC-0044, AC-0045, AC-0046, AC-0047, AC-0062, AC-0063):** TDD.
- **T4 (AC-0032, AC-0033):** Integration/manual QA.
- **T5 (AC-0034, AC-0035, AC-0054, AC-0068):** Goal-based.
- **T6 (AC-0036, AC-0037):** Goal-based.
- **T7 (AC-0038, AC-0039, AC-0040, AC-0041):** Goal-based.
- **T8 (AC-0042):** Goal-based.

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
- [ ] **AC-0011.** Each issued `allowed_paths` equals the closed kind/node/phase write set, unaffected by worker-supplied paths.
- [ ] **AC-0012.** A reconcile report from an agent definition used by a lens writer in that round is refused.
- [ ] **AC-0013.** G2 consent is unavailable until every named prerequisite has its required status.
- [ ] **AC-0014.** Each lint record matches the real core lint outcome on only the admitted initiative graph.
- [ ] **AC-0015.** Lens-round lint uses default mode.
- [ ] **AC-0016.** G2 and G3 consent are blocked by a non-zero strict lint exit on their current input revision.
- [ ] **AC-0017.** Missing repository-scope core lint prevents admission in both supported supervisor installation scopes.
- [ ] **AC-0018.** Every reached bound in the closed bound set, including any committed `paused-at-bound`, yields bound-pause consent before further work.
- [ ] **AC-0019.** Every accepted consent answer matches the closed discovery answer schema.
- [ ] **AC-0020.** Gate advancement requires the matching committed human answer under E1 gates' consumption contract.
- [ ] **AC-0021.** Every accepted answer records one verdict row before its authorized transition, including G3.
- [ ] **AC-0022.** Each verdict follows the schema transition, with only G3 `approve` transitions deferred until acknowledgement.
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
- [ ] **AC-0044.** G3 `approve` acknowledgement requires its later Ready commit and unchanged post-recording bound artifacts.
- [ ] **AC-0045.** Each post-G3 option yields its declared terminal reason.
- [ ] **AC-0046.** Ready promotion permits exactly the first preamble token's `Draft`→`Ready` change after matching committed G3 approve, with every other byte unchanged.
- [ ] **AC-0047.** Every status edit outside the declared promotion/reversion windows refuses `protected-content-changed` regardless of author.
- [ ] **AC-0048.** A fired G1 risk trigger yields consent offering the declared normal verdict set.
- [ ] **AC-0049.** Every admission pin has the declared scope and comparison source.
- [ ] **AC-0050.** Every accepted request/result conforms to its closed discovery shape.
- [ ] **AC-0051.** An unavailable reviewer ends the run with reason `reviewer-unavailable`.
- [ ] **AC-0052.** A non-zero default lint outcome blocks convergence with `lint-failed`.
- [ ] **AC-0053.** Every admission commit tracks every created sidecar file.
- [ ] **AC-0054.** Shipped discovery-loop/discovery-lead text contains no conflicting no-engine or upstream-supervisor claim while retaining prose fallback.
- [ ] **AC-0055.** Every path-bearing identifier meets its grammar.
- [ ] **AC-0056.** A worker result with any unclassified slot or sensitive/regulated slot lacking a redact-or-surface record refuses `classification-required` without writes.
- [ ] **AC-0057.** No Python process in the lint tree executes application code other than admission-pinned source bytes, regardless of planted bytecode, modules or import-path entries.
- [ ] **AC-0058.** Every one-way-door transition waits for matching consent.
- [ ] **AC-0059.** An invalidation exceeding one-third of active nodes or eight nodes waits for human impact confirmation.
- [ ] **AC-0060.** A result containing externally sourced slots without `untrusted:true` refuses `untrusted-marker-required`.
- [ ] **AC-0061.** Each resource/interpreter refusal follows its declared preservation/recovery contract, subject to the recovery Assumption.
- [ ] **AC-0062.** Every recorded decision row satisfies the declared chain-tip integrity contract.

- [ ] **AC-0063.** Abandon or stale post-G3 approval cannot reach terminal disposition while the brief reads Ready.
- [ ] **AC-0064.** G2 consent is unavailable while either required reviewer has an open blocker.
- [ ] **AC-0065.** Every issued G2 consent displays each open finding by assigned id and checked reference when valid.
- [ ] **AC-0066.** Recorded findings bind the file’s report-time digest.
- [ ] **AC-0067.** A reconcile request refuses `reviews-not-ignored` before issuance unless its discovery findings destination is ignored.
- [ ] **AC-0068.** Shipped discovery-loop SKILL.md, security-and-integrity.md and sidecar-schema.md state O1’s unanchored-edit-only tamper-evidence and lack of human-row attestation for the supervisor path.
- [ ] **AC-0069.** Worker changes outside issued paths refuse without writes.
- [ ] **AC-0070.** Every lint outcome meets the declared environment and process-tree limits.

## Follow-ons

eugenelim owns Tier B, pool width, controller intake and T9's separate E1 gates amendment under that spec's release.

## Assumptions

- **Settled D-A/D-B:** Tier A narrows RFC scope; adoption atomically creates/tracks new sidecars, refusing untracked trees.
- **Settled D-C:** lint docstring/`main()`: clean/informational=0; dangling/cycle=1; strict orphan/UNREACHABLE=1.
- **Accepted limit:** exit 0 proves neither semantic connectedness nor validation; unresolved cross-repository references are informational; unexpected checker exceptions also return 0.
- **Settled D-D:** recording is not verdict choice; Ready requires recorded G3 approve and is never supervisor-written.
- **Accepted risk:** the brief waives session identity checks only; profile names prove no human/agent independence.
- **Time-limited accepted risk (O1):** eugenelim accepts supervisor-written decision rows, canonical-field-order SHA-256 chain and ledger tip; spec/how-to claim only unanchored-edit tamper-evidence. The supervisor clock proves no external actor/time attestation. Risk expires when ferryman’s scribe runs supervisors with an externally anchored tip; Ready brief stays unchanged.
- **Inherited E1 risks:** forged pseudo-terminal answers/ledger steps/approval commits, history rewrites, self-reported independence, invisible attempt/store forgery and checker/pin replacement persist until guard/scribe/release comparison; content checks prove no attribution.
- **Narrow spelling:** SKILL.md’s narrow aliases approve-with-constraint/re-convergence despite the seven-verdict schema; eugenelim settles alias/eighth verdict at approval, changing grammar/bound fixtures.
- **Layout provenance:** adopter-owned layout lacks guaranteed installation hashes; admission captures digest/absence. eugenelim settles comparison source at approval, changing pin evidence.

- **Recovery:** Committed slot excess, ledger exhaustion, unavailable interpreter restoration and active-run limit amendment lack a six-command recovery preserving protected history; eugenelim settles the transition/configuration at approval, changing admission and recovery tests.
- **K1:** Closed gate enumeration remains open for G0/G1/G1.5/G2/G3, bound, one-way-door, cascade and security-depth consent; eugenelim settles it at approval, changing payload/answer validation.
- **K2:** One-way-door/cascade verdict sets and impact_digest remain open; eugenelim settles them at approval, changing AC-0058/AC-0059 consent.
- **K3:** Unreviewed bound consent lacks marker/verdict fields; eugenelim settles them at approval, changing answer eligibility.
- **K4:** Lint execution/recording verb and step commit remain open; eugenelim settles them at approval, changing lifecycle/replay.
- **K5:** Decision-row answer mapping (ts/gate/decision/ratified_by/reversibility_class), ledger tip field, chain bytes/genesis/verifying verbs/precedence/refusal remain open; eugenelim settles them at approval, changing AC-0062 integrity.
- **K6:** Park/listing sidecar-path-or-intent and sidecar_digest/brief_digest substitutions remain open; eugenelim settles them at approval, changing persisted/displayed fields.
- **K7:** Deferred-finding resolution and optional-reviewer names/install detection remain open; eugenelim settles them at approval, changing G2 prerequisites.
- **K8:** Classification floors/no-lowering, redact-or-surface grammar and external-provenance trigger remain open; T2’s regulated-verbatim test exceeds mechanical checks; eugenelim settles them at approval, changing result validation.
- **K9:** Baseline-depth surfacing lacks a criterion/mechanical absence condition; eugenelim settles it at approval, changing boundary consent.
- **K10:** AC-0034/AC-0041 omit Never-do citation/pin controls mapped by T5/T7; eugenelim settles coverage at approval, changing release proof.
- **K11:** Resource/chain/lint-subject refusal precedence against E1 core AC-0013/AC-0039 remains open; eugenelim settles it at approval, changing combined-fault outcomes.
- **K12:** T6 manual-ticket intake exceeds the closed procedure set; eugenelim settles removal at approval, changing guide tests.

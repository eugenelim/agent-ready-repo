# RFC-0099: Cut before adding and artifact shaping

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-27
- **Date closed:** 2026-08-27
- **Decision weight:** heavy — this amends the charter, changes published skill
  and agent contracts, supersedes accepted lifecycle decisions, introduces a
  compatibility migration, and changes delivery-state recovery.
- **Related:** [accepted feature intent](../product/intents/cut-before-adding-solution-ladder.md),
  [Charter](../CHARTER.md),
  [ADR-0009](../adr/0009-product-brief-layer-and-plan-owned-lld.md),
  [ADR-0019](../adr/0019-product-intent-ontology-and-brief-projection.md),
  [ADR-0042](../adr/0042-agent-additions-keyed-to-loop-and-work-type.md),
  [ADR-0076](../adr/0076-briefs-persist-dispatch-starts-from-specs.md),
  [ADR-0077](../adr/0077-feature-projection-and-tracker-authority.md),
  [ADR-0078](../adr/0078-standalone-intake-and-deterministic-workspace-index.md),
  [RFC-0083](0083-work-intake-and-artifact-routing.md),
  [RFC-0093](0093-intent-scoped-completion.md),
  [RFC-0094](0094-direct-light-execution-without-durable-planning-artifacts.md),
  [RFC-0096](0096-portable-delivery-artifact-lifecycle.md), and
  [RFC-0097](0097-agent-skill-engineering.md)

## Reviewer brief

- **Decision:** Adopt one cut-before-adding discipline across core guidance,
  artifact authoring, shaping review, technical design, and delivery without
  creating a generic orchestration layer or mandatory artifact chain.
- **Recommended outcome:** accept after the routing validation and mandatory
  heavy-review gates pass.
- **Change if accepted:**
  - Retain `work-intake`; add intent-only `intake-intent`; replace the two brief
    entry points with two modes of `author-delivery-brief` behind bounded aliases.
  - Add a cold, stateless `shaping-reviewer` for intent, delivery-brief, and spec
    contracts while keeping RFC, architecture, spec-plan, and code review with
    their existing owners.
  - Put the universal solution ladder in core guidance and add only
    artifact-specific enforcement to authoring and review contracts.
- **Affected surface:** the charter; core agent guidance; core intake, brief,
  spec, work-loop, and reviewer contracts; governance and product-engineering
  author/review skills; workspace routing; lifecycle fixtures; migration and
  adopter guides.
- **Stakes:** costly to reverse after names, reviewer roles, and state transitions
  ship across adapters and adopter repositories.
- **Review focus:** whether every behavior has one owner; whether the new agent
  clears the charter and ADR-0042; whether ordinary plan review and human gates
  survive; whether mid-build amendments can recover safely; and whether the
  reduced public surface is actually easier to route.
- **Not in scope:** adding a central rule loader, generic shaping skill, public
  `review-*` skills, durable shaping-review state, mandatory product-engineering,
  a universal tracker hierarchy, or implementation in this RFC change.

## The ask

**Recommendation.** Adopt a small universal rule—cut before adding—and enforce
it at the narrow owner for each artifact. Keep product meaning, repository
admission, governance, technical design, delivery contracts, and implementation
as independent axes. A request may move between them, but no route manufactures
an intent, brief, RFC, design document, or spec merely to reach the next skill.

Today the repository has several good simplification rules, but they live at
different cadences. Core guidance prefers the simplest solution. `new-rfc` asks
whether an RFC is the right artifact. `architect-design` requires a real choice
and permits stopping at a concept. `work-loop` selects direct-light where
possible, records declined additions, implements the smallest coherent unit,
and simplifies new code after gates. `adversarial-reviewer` suppresses
future-proofing and unrelated refactors. These rules should converge on one
principle without being copied into one oversized workflow.

At the same time, intake names expose internal processor boundaries, brief
authorship and readiness are split across two public skills, and intent/brief
review is ad hoc. The proposal fixes those entry points while preserving the
existing safety, spec-plan, human-approval, and delivery gates.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | Which public entry points survive? | Retain neutral `work-intake`; add intent-only `intake-intent`; replace brief entry points with two modes of `author-delivery-brief`. | Routing, intent authorship, and brief lifecycle are different jobs. | 2026-09-03 | Confirm names, modes, and authority boundaries. |
| D2 | Where does the universal discipline live? | One concise cut-before-adding ladder in core agent guidance, with narrow local deltas. | A new loader or copied checklist would increase the load this change is meant to remove. | 2026-09-03 | Confirm the canonical owner and non-duplication rule. |
| D3 | How is shaping reviewed? | Add one cold, stateless `shaping-reviewer` with `intent`, `delivery-brief`, and `spec` modes. | These artifacts need independent review before delivery, but not code-loop machinery. | 2026-09-03 | Confirm the charter amendment and ADR-0042 case. |
| D4 | Who reviews RFCs, architecture, plans, and code? | Keep their existing owners; add explicit RFC YAGNI checks to `adversarial-reviewer` and architecture YAGNI checks to `architect-review`. | Artifact-specific reviewers can enforce the shared rule without a fourth shaping mode. | 2026-09-03 | Confirm the author/reviewer matrix. |
| D5 | How does implementation handle a material contract finding? | Park the existing `work-loop`, revise and re-review both spec and plan, reapprove both, invalidate the stale baseline, reseal, and resume. | A separate shaping state machine would duplicate delivery authority; silently editing a sealed baseline is unsafe. | 2026-09-03 | Confirm the transition and preserved history. |
| D6 | How do old brief names retire? | Read old, write new for at least two minor releases and 90 days, then remove only through an Approver gate. | Immediate removal breaks adopters; permanent aliases preserve the confusion. | 2026-09-03 | Confirm the support window and removal evidence. |
| D7 | What proves the new routes are clearer? | Complete the predeclared five-adopter routing study and approve the implementation-fixture specifications and answer keys before acceptance. Executable fixtures gate their follow-on specs and release. | Owner agreement establishes architecture, not adopter usability, while implementation tests cannot precede the decision that authorizes implementation. | 2026-09-03 | Confirm the study and fixture designs as acceptance gates. |

## Problem & goals

### Problem

Four independent classifications are currently easy to conflate:

- **Product altitude:** what outcome or opportunity is being shaped.
- **Artifact form:** intent, RFC, architecture design, decision record, delivery
  brief, spec, plan, or defect context.
- **Delivery shape:** direct work, one spec, or coordinated multi-spec delivery.
- **Source form:** prose, tracker object, external document, repository finding,
  or existing local artifact.

A Jira Story can contain an intent, a complete spec, a defect, or a request that
needs no durable artifact. A feature intent can project to an RFC, design, spec,
brief, or settled decision. An RFC or architecture design may also begin
directly from a consequential direction or technical question. Treating any
one of these forms as the mandatory parent of the others creates wrapper
artifacts and makes adopters learn internal routing vocabulary.

Review has a related gap. Intent and brief authors may request critique, but
there is no durable cold-review contract. Specs already receive adversarial
spec-plan review, yet that reviewer also carries contract-shape checks. RFCs
already dispatch `adversarial-reviewer` without an explicit RFC mode.
Architecture designs already converge through `architect-review`, whose rubric
does not yet independently challenge unnecessary architectural surface.

Finally, a material spec discovery during implementation has no explicit legal
route from sealed delivery state back through contract and plan approval. The
desired shaping handoff therefore needs a delivery-owned pause and baseline
replacement, not a second state machine.

### Goals

- Make the least costly valid route the default at intake, authoring, review,
  and implementation.
- Give each artifact and lifecycle transition one public owner.
- Preserve core-only operation; product-engineering remains optional.
- Add independent intent, delivery-brief, and spec-contract review without
  adding public review skills or delivery-loop state.
- Preserve review for every completed spec-plan pair and the two human
  approvals before execution.
- Make RFC and architecture review independently reject unnecessary artifact
  and solution surface.
- Support out-of-repository product-intent promotion without making an external
  locator dispatchable.
- Retire old brief names through a bounded, testable migration.
- Ship each behavior change with the guide slice adopters need at that phase.

### Non-goals

- Requiring an intent before an RFC, architecture design, ADR, spec, or defect.
- Renaming `work-intake` into an intent-specific surface.
- Creating `author-intent-brief`, `review-intent`, `review-delivery-brief`, a
  generic shaping orchestrator, or a cut-before-adding skill.
- Reusing work-loop scripts, state, adjudication, or retry machinery inside
  shaping review.
- Making RFCs or ADRs executable delivery children.
- Removing validation, data-loss prevention, security, accessibility, explicit
  requirements, verification, or human approval in the name of simplification.
- Replacing the agent-skill-engineering author/review workflows accepted by
  RFC-0097 or copying their governed knowledge into core.

## Proposal

### 1. Keep source authority and artifact projection independent

Intent is an optional outcome authority, not a mandatory parent. Artifact
provenance forms a directed graph: a direct request, repository finding,
accepted intent, delivery brief, design result, or prior governance record may
be the closest sufficient authority for the next artifact.

| Starting condition | First useful artifact | Possible projection |
| --- | --- | --- |
| Product outcome or opportunity is unclear | Intent | RFC, architecture design, delivery brief, spec, or settled decision |
| Consequential direction remains unresolved | RFC | ADR, spec, migration, guide, or later delivery brief |
| A real technical choice needs trade-off analysis | Architecture design | RFC, ADR, or spec |
| One independently shippable behavior is clear | Spec | Plan and `work-loop` |
| One outcome needs several contracts or durable coordination | Delivery brief | Human-confirmed spec slices; RFCs and ADRs remain references |
| Existing behavior deviates from an established contract | Defect context | `bug-fix` |

Artifacts reference inherited decisions rather than copying them. A shared
request may legitimately produce an intent and an RFC or design, but no route
creates all of them by default.

### 2. Retain neutral intake and narrow the authoring surfaces

`work-intake` remains the public, cross-artifact router and safety boundary for
raw requests, tracker input, refresh, defects, direct work, RFCs, specs,
delivery briefs, and intents. It selects the least costly valid route by
content. Status requests continue to route directly to `workspace-status`.
Accepted-source refresh enters through the `work-intake` authority boundary;
configured acquisition and effect processors remain internal.

Public routing follows one precedence order:

1. A status request routes directly to `workspace-status`.
2. A request that explicitly names a known artifact, its owning skill, or a
   distinct work type such as product shaping, architecture design, or defect
   repair routes directly to that owning skill. The owner applies its own trust
   and authority controls.
3. A raw or ambiguous request, an acquisition or refresh, or a generic intake
   safety need routes to `work-intake`.

Here, **owning skill** means the workflow contract responsible for the
artifact or work type; it does not mean the human artifact owner recorded in an
intent. Delegation from `work-intake` to an owning skill is the same route, not
a second competing public answer.

`intake-intent` is intent-only. It creates a minimum Draft repository intent or
admits an existing repository-confined intent. The minimum contract is:

- outcome;
- boundary;
- owner;
- unresolved question;
- current projection; and
- source mode and revision needed for refresh or authority decisions.

This changes ADR-0078's core minimum field set explicitly:

| ADR-0078 field or lifecycle | Decision here | Workspace-boundary meaning |
| --- | --- | --- |
| `Status` | Retain, required. | `Draft | Accepted | Fulfilled | Superseded`; lifecycle is unchanged. |
| `Level` | Move from required core field to optional product-engineering enrichment. | Absence means altitude-neutral core intent, not an unknown workspace kind. |
| `Outcome` | Retain, required. | The intended result remains canonical in the artifact. |
| `Opportunity` | Make optional product enrichment. | Core intake need not invent an opportunity when the request already states an outcome. |
| `Assumptions` | Make optional product/de-risk enrichment. | Core instead requires explicit unresolved questions, including `none`. |
| `Source` | Retain, required when refresh or external authority exists; otherwise record repo-origin. | `workspace.toml` mirrors only the origin mode, durable locator, and revision needed for routing. |
| `Boundary` | Add, required. | Names what the accepted outcome does not authorize. |
| `Owner` | Add, required. | Names who may revise or accept the intent. |
| `Unresolved questions` | Add, required, permitting `none`. | Prevents hidden uncertainty from being mistaken for acceptance. |
| `Projection` | Add, required, permitting `undecided`. | Records the current least-artifact next route without making it executable. |

ADR-0078's repository-relative `path`, `kind`, `source`, `summary`, and `needs`
workspace fields; reconciliation rules; dispatchability rules; and shared
intent lifecycle otherwise remain unchanged.

Product-engineering may add `Level`, `Scale`, jobs-to-be-done fields, and
de-risk evidence in place. Core does not require those fields. `intake-intent`
may revise a minimal intent it authored; findings on a product-engineering or
human-authored intent return to that author or an explicitly authorized owner.

A chat-only or personal/vault product intent is source input, not a
workspace artifact. Admission requires a human-confirmed repository
destination. `intake-intent` creates a repository-canonical copy, pins the
source revision and back-reference, records authority transfer, and begins the
admitted artifact's identity at its repository path. `workspace.toml` never
indexes the external locator as dispatchable work.

All repository reads and writes use
`agentbundle.catalogue_tooling.file_safety` or a tested equivalent with the
same fail-closed semantics. Resolve and confine before access; reject empty,
absolute, drive-letter, backslash, dot-segment, non-regular, multiply linked,
symlink, junction, reparse-point, post-resolution identity-change, and
out-of-root targets. A confirmation does not bless an unsafe path.

An external locator is passive provenance during admission. Recording it
performs no filesystem, Hypertext Transfer Protocol (HTTP), Domain Name System
(DNS), shell, tracker, or credential operation. Persist only a minimized,
non-secret locator: strip query and fragment data, personal absolute-home
paths, credentials, tokens, and personal data, or refuse when minimization
would destroy identity. Stop on confidentiality mismatch.

`author-delivery-brief` has two mutually exclusive modes:

- **`create`:** authors a Draft brief from a direct request or sufficient
  trusted repository authority and stops. When the source is external or
  otherwise untrusted, it additionally applies passive containment,
  minimization, and provenance controls.
- **`continue`:** opens an existing repository brief, reviews readiness, and
  may set Ready only after human confirmation.

Neither mode copies a raw external payload into a committed artifact or
`workspace.toml`. It selects the requirement fields needed for the local
artifact, treats prompt-like or instruction-like source text as quoted data,
redacts secrets, credentials, personal data, and private paths, and refuses the
write when safe minimization is uncertain. Hostile brief, tracker, and
personal/vault-intent fixtures must prove refusal and redaction before the
authoring spec ships.

Ready approves the brief, not child materialization. A Ready brief may have
zero specs. When selection is requested, `continue` proposes the minimum slice
cut and invokes `new-spec` only after a separate human confirmation of that
cut.

The delivery map has two groups:

- **Governance references:** RFCs and ADRs that constrain, unlock, or explain
  delivery. They never affect execution or closure rollups.
- **Delivery slices:** specs, which alone become executable after their plan and
  approval gates and alone determine brief delivery rollups.

### 3. Put the universal solution ladder in core guidance

Core's canonical agent-guidance seed carries the concise baseline:

1. If the requested addition is not genuinely needed, skip it and say so once.
2. Search once, within the current decision boundary, for an adequate existing
   repository solution; reuse a hit or move on after a decisive empty result.
3. Prefer the standard library when it satisfies the outcome.
4. Prefer a native platform capability when it satisfies the outcome.
5. Prefer an already-installed dependency when it satisfies the outcome; an
   import absent from the owning manifest is a new dependency.
6. Use one obvious line when it is the complete, maintainable solution.
7. Otherwise write the minimum correct solution in the fewest statements and
   files that preserve ownership and tests.

The ladder stops at the first sufficient rung. It does not authorize ignoring
contradictory evidence, freshness-sensitive facts, required gates, or
correctness review. A bounded discovery check is not a cap on verification.

Never cut:

- validation at a trust boundary;
- error handling that prevents data loss;
- security or privacy controls;
- accessibility;
- an explicit accepted requirement;
- required tests, migrations, documentation, or human approval; or
- a policy or platform restriction the user cannot waive.

Core guidance also retains the small universal communication baseline: lead
with the useful outcome, avoid routine tool narration, preserve requested
substance, and end with changed state, verification, and remaining work.
Surface-specific rendering and workflow rules stay with their owners.

No dynamic rule loader, separate always-loaded cognitive-load file, generic
YAGNI skill, or full-ladder copy in every primitive is added. A scoped skill or
agent repeats only the safety control needed to make its own contract
self-contained.

The accepted intent's behavior register is the complete line-level assessment,
not an additional normative contract. This RFC is the decision authority. A
follow-on spec cites a row only when that identifier materially clarifies a
local acceptance criterion; it does not reproduce or globally remap the
register. A behavior that changes implementation must appear in this RFC or a
follow-on acceptance criterion; an omitted or conflicting intent row does not
override either. The register is coverage evidence, not text to paste into an
installed surface.

### 4. Pair each author with an independent artifact-specific review

| Artifact | Authoring checkpoint | Independent review |
| --- | --- | --- |
| Intent | `frame-intent` or `intake-intent` creates only the minimum outcome authority needed. | `shaping-reviewer` `intent` mode challenges artifact need, altitude, boundaries, assumptions, and projections. |
| Delivery brief | `author-delivery-brief` refuses a wrapper around one already-clear slice and materializes only confirmed children. | `shaping-reviewer` `delivery-brief` mode challenges coordination value, speculative slices, and governance/delivery separation. |
| RFC | `new-rfc` skips, reuses, amends, or routes to ADR/spec/PR/design before creating a file, then chooses the lightest warranted weight. | `adversarial-reviewer` `rfc` mode challenges wrong-artifact choice, avoidable governance, unnecessary solution surface, and mandatory follow-ons without evidence. |
| Architecture design | `architect-design` requires a real choice, reuses adequate prior design, and permits Stage 0 to be the final artifact. | `architect-review` challenges wrong-artifact choice, unnecessary components or boundaries, ignored existing/native/platform capabilities, and speculative scale or configurability. |
| Spec and plan | `new-spec` selects the smallest independently shippable contract and minimum construction plan. | `shaping-reviewer` tests the contract; `adversarial-reviewer` tests every completed spec-plan pair. |
| Implementation | `work-loop` selects direct-light or durable work, records declined additions, builds the smallest coherent unit, and simplifies new code after gates. | `adversarial-reviewer` checks conformance and suppresses future-proofing; `quality-engineer`, when triggered, tests maintainability and premature abstraction. |

Reviewer contracts carry only their artifact-specific questions and reference
the universal ladder. The existing adversarial “what not to flag” list remains
local because it governs review noise rather than authoring behavior. The
work-loop simplify pass remains local because it runs after green gates against
new code. In light mode that pass owns function-level simplification;
`quality-engineer` independently rechecks it only when its trigger fires.

### 5. Add a stateless shaping-review work type

The core pack gains `shaping-reviewer`, with exactly three modes:

- **`intent`:** outcome, boundaries, owner, assumptions, altitude when present,
  least-artifact projection, core-only viability, and falsifiability.
- **`delivery-brief`:** coherent shared outcome, coordination value,
  governance-reference versus delivery-slice separation, deferred scope,
  readiness, and confirmed materialization boundary.
- **`spec`:** objective, boundaries, acceptance criteria, governing
  constraints, contract-versus-construction separation, and testing strategy.

The reviewer is cold and read-only: it never edits an artifact, changes status,
or authorizes delivery. It returns exactly one review result, `Clean` or
`Findings`. Its compact record contains the target repository path and reviewed
source revision when one exists, review context, consulted surfaces, grounding
gaps, severity-ordered findings with fixes, and the result, without
conversational preamble or process narration. The result is review evidence,
not lifecycle authority.

Lifecycle owners invoke it directly:

- `intake-intent` for a core-created minimal intent;
- `frame-intent` or the authorized product-intent owner for a product intent;
- `author-delivery-brief` for a delivery brief; and
- `new-spec` for a new or materially amended spec contract.

No public `review-intent` or `review-delivery-brief` skill is added. No generic
shaping loop owns the lifecycle. The authoring skill receives findings and
revises its artifact. Every unresolved finding blocks the transition. After a
material contract revision, the lifecycle owner redispatches a fresh reviewer;
that revision invalidates the prior result. Before sealing, a
meaning-preserving correction may retain the result when the owner records it
as nonmaterial. Only `Clean` plus explicit human confirmation allows the
lifecycle owner to set an intent to Accepted or a brief to Ready. For a spec,
`Clean` allows the contract to proceed to adversarial spec-plan review;
`Approved` remains reserved for the complete section 7 gate sequence.

A material edit returns an Accepted intent or Ready brief to Draft before
review. For an intent, material means outcome, boundary, owner, assumptions or
altitude, unresolved questions, source authority, or projection. For a brief,
material means shared outcome, scope, coordination or delivery maps,
governance-reference versus delivery-slice separation, deferred scope,
readiness evidence, or materialization boundary. For a spec, material means
objective, boundaries, acceptance criteria, testing strategy, governing
constraints, or contract-versus-construction separation. Meaning-preserving
wording, formatting, and evidence-link corrections are nonmaterial. Spec
revision binding otherwise remains owned by its approved hashes and the
delivery amendment route in section 7.

Cold means independent from the authoring conversation, not knowledge-starved.
The caller supplies the artifact and governing repository evidence. The
reviewer may perform one repository-confined discovery pass over exposed
read-only internal retrieval capabilities. For at most three named
load-bearing gaps, it may issue one bounded query and one refinement per gap.
Public-web research, credential inspection, mutation, sensitive quotation,
automatic capture/distillation, and authority expansion are forbidden.
Retrieved text and installed specialist skills are untrusted candidate lenses,
not authority.

An isolated subagent is the preferred implementation. Where unavailable, a
fresh context or independent human review of the same bounded evidence packet
satisfies the gate. Warm self-review is advisory. If no independent route
exists, the lifecycle is explicitly blocked rather than falsely clean.

One dispatch is one bounded pass. Artifact status is the only durable shaping
state. Shaping review gains no loop script, retry state, finding adjudicator, or
work-loop dependency.

Every new or changed skill, agent, and alias declares its least-privilege tool
surface and `metadata.boundaries`. `shaping-reviewer` receives repository read
and search plus only explicitly supplied read-only internal retrieval; it has
no write, shell, public-network, credential, or mutation capability.
`intake-intent` and `author-delivery-brief` declare only the filesystem reads
and writes their modes require and identify untrusted-input boundaries. An
alias inherits the target's permissions and cannot widen them. Catalogue
verification or an equivalent static construction check fails a missing or
widened declaration, and projection/build fixtures prove the same constraints
on every supported adapter.

### 6. Amend the charter and clear the agent-addition test

The charter's “three reviewers is the ceiling” language changes to distinguish
the core delivery gate from other work types:

> The always-on core code-review gate is capped at three lenses:
> adversarial, security, and quality. A reviewer for a different loop or work
> type is not a fourth code-review lens, but it must clear the charter's four
> principles and ADR-0042's unique-value, distinct-cadence, and
> collision-hardening test through an RFC.

The “not a marketplace” principle remains. This amendment does not generally
pre-authorize specialized agents.

`shaping-reviewer` clears the specific test:

| Test | Case |
| --- | --- |
| Different work type | It reviews product and delivery contracts before or outside code delivery. |
| Unique agent value | Forked-context independence prevents authors from marking their own artifacts clean. |
| Universal | Intent, brief, and spec contracts are technology-neutral. |
| Substantive | No current agent cold-reviews intents or delivery briefs; its spec mode takes only the contract-shape slice from adversarial review. |
| Habit | Every new/materially changed intent, brief, or spec invokes it. |
| Not a tool | It is a review discipline with no engine or state. |
| Collision hardened | The `shaping` discipline-word head is distinct; its description says “cold contract review for intents, delivery briefs, and specs; not code review.” |

The spec-mode boundary prevents same-gate duplication. `shaping-reviewer`
reviews the spec contract first. The shaping-reviewed contract is fixed input
to the later adversarial spec-plan gate. `adversarial-reviewer` keeps plan/spec
mapping, duplicate-value, dependency-order, verification-mode, structural-plan,
and implementation-conformance checks; it does not ratify the contract's
product meaning.

Every current adversarial spec-stage check is preserved:

| Current check | Future owner | Required coverage |
| --- | --- | --- |
| Vague Objective | `shaping-reviewer` | Objective has observable outcomes. |
| Boundaries underspecified | `shaping-reviewer` | `Always do`, `Ask first`, and structural `Never do` rails are present. |
| Missing Acceptance Criteria | `shaping-reviewer` | Done remains a testable checklist. |
| Missing `Constrained by:` | `shaping-reviewer` | Governing RFC/ADR inheritance is explicit or explicitly absent. |
| Implementation detail in spec | `shaping-reviewer` | Contract stays in the spec; construction stays in the plan. |
| Plan/spec mismatch and duplicate values | `adversarial-reviewer` | Every task maps to the contract and each fact has one canonical home. |
| Contract versus construction confusion | Both, at different targets | Shaping checks the contract boundary; adversarial checks task/test placement against it. |
| Missing `Depends on:` | `adversarial-reviewer` | Every plan task names dependencies or `none`. |
| Derived-fixture scope | Both, at different targets | Shaping makes parent scope exact; adversarial verifies derived fixtures and tasks against it. |
| Verification-mode declaration | Both, at different targets | Shaping checks behavior-level Testing Strategy; adversarial checks every task's mode and artifact. |

Construction fixtures seed each row and fail if either future reviewer omits
its assigned check. No row may be removed merely because the mode split lands.

### 7. Preserve every spec-plan and human approval gate

`new-spec` continues to draft both `spec.md` and `plan.md`. The sequence becomes:

1. Draft the spec and plan.
2. Run `shaping-reviewer` `spec` mode against the contract.
3. Revise from shaping findings.
4. Run `adversarial-reviewer` against the complete spec-plan pair, including
   non-structural plans.
5. Revise from construction findings.
6. Obtain the existing human spec approval.
7. Obtain the existing human plan approval.
8. Seal both approved artifacts as the delivery baseline.

`work-loop` retains its additional pre-execution adversarial gate when a
delivery plan introduces a module boundary, dependency, abstraction layer, or
top-level directory. Mixed implementation/spec diffs still receive adversarial
conformance review. An unapproved material contract change is a blocker, not a
contract decision the code reviewer may settle.

A spec finding is material when it changes any section 5 contract axis:
objective, boundaries, acceptance criteria, testing strategy, governing
constraints, or contract-versus-construction separation. Before sealing, a
meaning-preserving wording, formatting, or evidence-link correction may retain
the shaping `Clean` result when the lifecycle owner records it as nonmaterial.
After sealing, the approved spec and plan are immutable: such a correction must
either remain solely in review history without editing those artifacts or enter
baseline replacement, human reapproval, and resealing for the changed exact
revision. A stale approved hash may never resume.

For this transition, **approved hashes** bind human approval to exact spec and
plan revisions; **reviewer-clean state** binds clean review results to those
same revisions; the **remaining-work schedule** is the executable sequence
derived only from unfinished plan tasks; **plan lock** prevents that sequence
from changing during execution; and **parked** means the controller may
preserve observations and the current diff but may not dispatch implementation
work.

For any requested edit to a sealed spec or plan, `work-loop` owns one guarded
`baseline-replacement-required` transition. It is legal from implementation,
verification, or review. The caller records whether the initiating finding is
material, but there is no reduced post-seal edit path: every changed exact
revision has these effects:

- return the run to spec-plan drafting;
- set the spec to `Draft` and plan to `Drafting`;
- invalidate approved spec and plan hashes;
- invalidate reviewer-clean state and the remaining-work schedule;
- preserve completed-work, attempt, and review history;
- retain the current diff as observed repository reality rather than rewriting
  history; and
- block further implementation until the normal shaping review, adversarial
  spec-plan review, human spec approval, human plan approval, baseline seal,
  remaining-work schedule, and plan lock all succeed.

The implementation spec may choose a different event name but must preserve
these guards and state effects. `new-spec` owns artifact revision while the
delivery controller is parked. The shaping reviewer never invokes or mutates
delivery state.

Direct-light remains unchanged: it has no durable spec baseline to amend. If a
material contract or durability trigger appears, it follows the existing route
into durable spec-and-plan work.

### 8. Add explicit RFC and architecture YAGNI review

`new-rfc` adds a cut-before-creating checkpoint before target creation:

1. Is a consequential unresolved direction or explicit circulation request
   present? If not, do not create an RFC.
2. Can an existing RFC or decision be amended or referenced? If yes, reuse it.
3. Is ADR, spec, PR, issue, architecture design, or reversible trial the cheaper
   correct artifact? If yes, route there.
4. If an RFC remains warranted, select the lightest weight that satisfies the
   governance and risk boundary.

The existing `adversarial-reviewer` gains an explicit `rfc` mode because
`new-rfc` already invokes it. That mode checks:

- wrong or unnecessary artifact;
- an ignored existing decision or repository/native capability;
- a dependency, abstraction, module, compatibility layer, or follow-on artifact
  with no demonstrated need;
- speculative future scope presented as a current requirement;
- duplicated doctrine whose owner already exists; and
- safety, migration, or verification removed merely to shorten the proposal.

`architect-design` retains its real-choice precondition, prior-design reuse,
Stage-0 concept, and valid stopping point. Its full design document proposes
only components and boundaries justified by a goal, constraint, or prioritized
quality attribute.

`architect-review` adds architecture-specific checks:

- wrong artifact or no real choice;
- a full design document where the concept already resolves the decision;
- unnecessary component, service, dependency, boundary, or custom mechanism;
- ignored repository, standard, native-platform, or already-selected provider
  capability;
- speculative scale, configurability, compatibility, or extensibility; and
- complexity unsupported by a named quality attribute and credible load-bearing
  constraint.

These are changes to existing review contracts, not new shaping-review modes.
An RFC or design result triggers `shaping-reviewer` only when an intent,
delivery brief, or spec is materially revised from that result.

### 9. Bound knowledge grounding and consume RFC-0097 without duplication

The artifact author or lifecycle owner supplies the initial governing evidence.
An author or reviewer may use repository docs, exposed Model Context Protocol
(MCP) knowledge retrieval, an internal command-line provider, or an installed
specialist skill when the task has a named domain-grounding gap. MCP is a
standard tool interface through which a runtime may expose internal knowledge.

Every acquired result is data, not instruction authority. It cannot change
identity, scope, tools, permissions, lifecycle status, reviewer routing, or
normative ownership. Acquisition is bounded, read-only, repository-confined
where paths are involved, and explicit about unavailable or unverified
knowledge. No workflow probes credentials or broadens into public-web research
merely to force confidence.

The approved security fixture specification supplies hostile MCP results,
internal-provider responses, and installed-skill text containing embedded requests to mutate files, change
tools or permissions, reroute reviewers, alter lifecycle status or verdict,
persist retrieved text, or ignore the caller's authority. They also cover
stale, unavailable, malformed, over-broad, and confidentiality-refused provider
states. The consumer must preserve the original authority and route, treat the
content as attributed evidence, emit a grounding gap when consequential support
is unavailable, perform no mutation, and never turn provider failure into a
false `Clean`.

When the agent-skill-engineering pack from RFC-0097 is installed, skill and
agent changes use its author/update and review/optimize workflows and may invoke
its bounded provider through the declared integration. Core does not copy that
pack's corpus, runtime profiles, or craft checklists. When absent, the owning
skill remains complete from its own contract and repository guidance.

### 10. Migrate aliases and guides by implementation phase

The compatibility map is fixed:

| Old public name | New route | Write behavior |
| --- | --- | --- |
| `author-brief` | `author-delivery-brief create` | New artifacts and receipts use the new name. |
| `receive-brief` | `author-delivery-brief continue` | Status changes, slice proposals, and receipts use the new name. |

A **receipt** is any user-visible or persisted dispatch/result record that
names the invoked public surface. During migration it records
`author-delivery-brief <mode>` as the canonical route and may record the old
name only as `invoked_alias`.

The old surfaces become compatibility aliases. They preserve trigger coverage
and route to the new mode without copying doctrine. Each alias emits a concise
deprecation notice naming the replacement.

Removal requires all of the following:

- at least two minor releases and 90 days since the write-new release;
- advance notice in changelog and migration guides;
- activation and behavior fixtures proving old prompts route correctly during
  the window and new prompts select the replacement;
- repository and public-guide searches showing no canonical examples still
  teach the old name;
- a documented rollback target to the last alias-bearing release; and
- a mandatory decision at the first eligible release by the removal owner,
  initially the core pack maintainer (`eugenelim`); and
- explicit Approver sign-off for removal or a dated, reasoned extension.

Permanent dual semantics are not an allowed outcome. `work-intake` is not part
of this rename and keeps its current public identity. Existing `capture-work`
compatibility remains governed by its current migration rather than being
reopened here.

Each implementation phase ships its guide slice:

- **Intake phase:** raw request, tracker, direct work, intent admission,
  status, and refresh journeys.
- **Brief phase:** create, continue, readiness, zero-spec Ready state,
  confirmed-slice materialization, and aliases.
- **Review phase:** cold versus warm review, runtime fallback, evidence packet,
  findings return, and human decision.
- **Technical shaping phase:** RFC and architecture cut-before-adding examples.
- **Delivery phase:** spec-plan reviews, human gates, amendment pause,
  rebaseline, recovery, and direct-light boundary.

Journey/explanation, how-to, and reference documentation for a capability ship
with that capability. A terminal documentation sweep does not satisfy the gate.

### 11. Supersede only the named prior holdings

Acceptance supersedes only the clauses below. An unlisted clause in a named ADR
remains authoritative.

| Prior authority | Affected holding | Replacement here | Effective phase |
| --- | --- | --- | --- |
| ADR-0009, Decision 1 | A brief has one spec-only coverage map. | Section 2 gives the map separate governance-reference and spec-slice groups; only specs retain rollup semantics. ADR-0009's brief altitude, linkage, and plan-owned low-level design remain. | Brief phase |
| ADR-0019, Decision 2 | A brief is necessarily a feature intent projected onto a repository, and `receive-brief` is the universal receiver. | Sections 1–2 make intent ancestry optional, define a delivery brief by coordination value, and assign create/continue modes to `author-delivery-brief`. The recursive product-intent ontology and staged contract maturity remain. | Intake and brief phases |
| ADR-0076, public receiver holding | `receive-brief` owns readiness and selected-slice handling. | Sections 2 and 10 move that behavior to `author-delivery-brief continue` behind a bounded alias. Ready-with-zero-specs and separately confirmed slice materialization remain unchanged. | Brief phase |
| ADR-0077, feature-projection table | Every listed route begins from a feature intent. | Sections 1–2 allow a direct artifact route when sufficient authority already exists. When a feature intent exists, ADR-0077's shippability/coordination gate still applies. Tracker-origin/repo-origin authority and refresh conflict rules remain unchanged. | Intake phase |
| ADR-0078, minimal core intent fields | Core requires `Status`, `Level`, `Outcome`, `Opportunity`, `Assumptions`, and `Source`. | Section 2's field-by-field map retains status, outcome, source, and lifecycle; makes product fields optional; and adds boundary, owner, unresolved questions, and projection. Workspace index and dispatch rules remain unchanged. | Intake phase |

Acceptance authorizes two exact decision records:

1. **Superseding ADR — artifact admission and delivery-brief lifecycle.** It
   records the five clause-level replacements above. Before a replacement phase
   begins, each affected frozen ADR receives only a metadata forward pointer to
   this new ADR, naming the refined clause; its historical body is not edited.
2. **New ADR — shaping-review work type and sealed-baseline replacement
   handoff.** It
   records sections 4–7, the charter conformance case, and the delivery-owned
   rebaseline boundary. It conforms to ADR-0042 rather than superseding it.

Frozen RFCs receive only the following clause-level dispositions after this
RFC is accepted. Their bodies remain untouched; the entries are added under
their legal `## Errata` headings before an affected implementation phase
begins.

| Prior RFC | Affected holding | Exact disposition |
| --- | --- | --- |
| RFC-0083 | `work-intake` authors the minimal repository intent and the public brief surfaces are `author-brief` and `receive-brief`. | Add an Errata entry naming RFC-0099 sections 2 and 10 as the replacement for those authoring and naming clauses. Retain RFC-0083's neutral routing, acquisition, refresh, authority, and compatibility-migration holdings. |
| RFC-0096 | An ordinary normalized `Paused` delivery state leaves artifact statuses unchanged. | Add an Errata clarification that RFC-0099 section 7's material contract amendment is the material case of guarded sealed-baseline replacement back to spec-plan drafting, not the normalized `Paused` state. Retain the ordinary `Paused` rule and RFC-0096's governance-outside-rollup holding. |
| RFC-0097 | No holding is changed. | Add no Errata. Implementations conform to its pack ownership and bounded-provider contracts without copying them. |

No other RFC disposition is authorized.

No unspecified “errata set” is permitted. If implementation discovers another
prior holding that must change, the RFC returns to Draft or receives an in-flight
Amendment before that change proceeds.

## Options considered

| Option | Advantage | Why not selected |
| --- | --- | --- |
| Keep current names and ad hoc review | No migration or new agent | Preserves processor leakage, split brief ownership, and self-review gaps. |
| Rename all work intake to `intake-intent` | One use of the word intent | Misnames direct work, defects, refresh, RFC, brief, and spec routing. |
| Add `author-intent-brief` | Carries “intent” across surfaces | Conflates outcome authority with a delivery coordination envelope. |
| Add public `review-intent` and `review-delivery-brief` skills | Discoverable manual review commands | Adds public surface and permits review to bypass lifecycle owners. |
| Extend `adversarial-reviewer` to all shaping | Reuses one agent | Overloads the code/spec-plan reviewer and leaves intent/brief cadence implicit. |
| Add one generic shaping orchestrator | Central control | Recreates the overloaded work-loop problem at a new altitude. |
| Reuse work-loop scripts for shaping review | Existing state and retries | Couples authoring review to delivery machinery and blocks lightweight runtimes. |
| Add a central rule loader | One apparent source | Adds runtime, trust, and failure surface for guidance that fits in core plus local deltas. |
| Remove old brief names immediately | Fastest conceptual cleanup | Breaks existing prompts, guides, and installed integrations. |
| Keep aliases indefinitely | No breaking removal | Makes dual semantics permanent and defeats the simplification outcome. |

## Risks & what would make this wrong

| Risk | Falsifying signal | Response |
| --- | --- | --- |
| The new names are not easier to route. | Fewer than four of five target adopters route every scenario correctly, any scenario yields two plausible answers, or a core-only route requires product-engineering. | Reject or rename before acceptance; do not explain around a failed test. |
| `shaping-reviewer` duplicates the code-review gate. | Its fixtures require implementation diffs, plan construction, or the same contract judgment at the same cadence as adversarial review. | Narrow or remove the overlapping mode; preserve one owner per gate. |
| The charter amendment becomes a reviewer marketplace loophole. | Later agents cite this RFC without independently clearing ADR-0042 and the charter principles. | Keep the amendment work-type-specific and require a new RFC for later additions. |
| Guidance duplication grows. | The full ladder or behavior register appears in multiple skills or agent files. | Keep one core baseline; test local surfaces for narrow deltas only. |
| The mid-build amendment loses progress or accepts stale work. | Completed history disappears, stale hashes remain accepted, or implementation resumes before both approvals and resealing. | Fail closed; test every source state, crash point, and resume path. |
| Cold review is unavailable on an adapter. | A runtime cannot isolate a subagent or start a fresh review context. | Use independent human review; block if no independent route exists. |
| Grounding becomes an authority escalation. | Retrieved text changes tools, scope, status, or normative ownership. | Treat it as untrusted evidence, cap acquisition, and refuse the transition. |
| Aliases never retire. | Removal evidence is repeatedly deferred after the support floor. | Require a named removal owner and Approver decision at the first eligible release. |
| “Fewest lines” harms maintainability or safety. | Review finds compressed code, lost validation, weak tests, or hidden behavior. | Apply the hard carve-outs and prefer obvious code over literal line minimization. |

The proposal is wrong if the routing study fails, if ordinary plan review or
human approvals must be removed to make it workable, or if the new reviewer
cannot remain independent and stateless across supported adapters.

## Evidence & prior art

- The [accepted intent](../product/intents/cut-before-adding-solution-ladder.md)
  records all 74 behavior dispositions and the cold-review convergence that
  produced this proposal.
- The [Charter](../CHARTER.md) establishes the four admission principles and the
  current three-reviewer language this RFC amends.
- [ADR-0042](../adr/0042-agent-additions-keyed-to-loop-and-work-type.md) limits
  the three-lens ceiling to the always-on code-review gate and defines the test
  for a different work-type agent.
- [RFC-0083](0083-work-intake-and-artifact-routing.md) establishes neutral
  intake, content-based routing, repository-canonical artifacts, and bounded
  compatibility migration.
- [RFC-0096](0096-portable-delivery-artifact-lifecycle.md) keeps governance
  records outside delivery-state rollups and makes specs the executable
  contracts.
- [RFC-0097](0097-agent-skill-engineering.md) establishes separate agent-skill
  author/review workflows, bounded provider integrations, and staged removal of
  duplicated craft guidance.
- Existing `new-rfc`, `architect-design`, `architect-review`, `new-spec`,
  `work-loop`, and `adversarial-reviewer` contracts already contain the author
  and review cadences this RFC narrows rather than replaces.

No external prior art is required. The decision changes repository-owned
workflow and published-contract boundaries whose authority is local.

## Experiment / validation

### Adopter routing study

Run a moderated card sort and tree test with five target adopters who did not
author or review this intent or RFC. Every participant must have used an
agent-assisted issue-to-build workflow. The cohort contains at least two
core-only maintainers, at least two practitioners who use optional product or
architecture shaping, and no more than two people from one team. Freeze the
participant criteria, installation profile, exact prompts, expected first
owner, and clarification policy before recruitment.

The answer key is:

| ID | Installed profile and exact card intent | Expected first owner and route |
| --- | --- | --- |
| R1 | Core-only: “Capture this stated product outcome as a repository intent.” | `intake-intent` |
| R2 | Core + product-engineering: “Shape this raw product idea before deciding its repository artifact.” | `frame-intent`, then `intake-intent` only when repository admission is requested |
| R3 | Core-only: “Start this Jira Story”; the card contains one shippable behavior but names no artifact. | `work-intake`, delegating to `new-spec` after classification |
| R4 | Core-only: “Create a spec for this already-clear behavior.” | `new-spec` directly |
| R5 | Governance installed: “Draft an RFC for this unresolved consequential direction.” | `new-rfc` directly; no intent required |
| R6 | Architecture installed: “How should we design this integration? Two viable technical shapes remain.” | `architect-design` directly |
| R7 | Core-only: “Turn this external multi-artifact brief into a repository brief.” | `author-delivery-brief create` |
| R8 | Core-only: “Continue this Ready brief, but select no delivery slice yet.” | `author-delivery-brief continue`; stop without `new-spec` |
| R9 | Core-only: “Propose the minimum spec cut from this Ready brief.” | `author-delivery-brief continue`; invoke `new-spec` only after separate confirmation |
| R10 | Core-only: “The established behavior regressed; diagnose and fix it.” | `bug-fix` directly |
| R11 | Core-only: “Refresh this accepted tracker-origin artifact.” | `work-intake` refresh boundary; processor remains internal |
| R12 | Core-only: “What is ready to work on?” | `workspace-status` directly |

The cards contain enough information to select an owner. Clarification is
permitted only on a separately scored ambiguity-control card; asking on an
answer-key card counts as a routing miss. Delegation from `work-intake` to the
expected specialist counts as the one expected route, not a second answer.

Pass only when at least four of five adopters route every scenario correctly,
no scenario produces two plausible public routes, and no core-only scenario
requires product-engineering. Any failed condition returns the RFC to Draft.

### Contract fixtures

Before acceptance, approve a versioned fixture specification containing each
fixture ID, prompt or seeded defect, installed profile, exact expected result,
and owner. The executable fixtures below are post-acceptance implementation
gates: each follow-on spec must run its applicable set clean before shipping.

- Activation fixtures distinguish `work-intake`, `intake-intent`,
  `author-delivery-brief create`, `author-delivery-brief continue`, `new-rfc`,
  `architect-design`, `new-spec`, and `bug-fix`, including near misses.
- Alias fixtures prove old prompts route to the correct new mode during the
  migration and that all new receipts write the new name.
- Shaping-review fixtures seed unnecessary intents, wrapper briefs,
  speculative slices, vague spec objectives, missing boundaries, and unsafe
  simplification; every applicable defect must be found.
- RFC and architecture-review fixtures seed wrong artifacts, ignored existing
  capabilities, unnecessary dependencies or components, and speculative
  future-proofing.
- Delivery-state tests enter `baseline-replacement-required` from implementation,
  verification, and review; exercise crash recovery at every mutation; verify
  stale hashes and schedules cannot resume; and prove completed history remains.
- Core-only fixtures install no product-engineering or architecture pack and
  still complete intake, intent, brief, spec, review fallback, and delivery
  routes.
- Boundary fixtures cover unsafe path shapes and identity changes; external
  locators that attempt filesystem, HTTP, DNS, shell, tracker, or credential
  access; raw payload and sensitive-data minimization; prompt-like external
  text; hostile MCP/provider/installed-skill authority changes; unavailable and
  stale providers; confidentiality refusal; and fail-closed recovery.

### Heavy-review gates

Before status becomes Open, run citation-integrity and self-claim checks,
adversarial RFC review, security review for retrieval, untrusted-input, and
state-transition boundaries, and a fresh-reader review. Before acceptance,
rerun every applicable review to clean after validation-driven changes.

## Follow-on artifacts

Acceptance warrants these artifacts, in dependency order:

1. **Charter amendment and decision records:** apply the exact reviewer-ceiling
   amendment; create the superseding artifact-admission/delivery-brief ADR and
   the new shaping-review/sealed-baseline-replacement ADR named in section 11;
   add only
   metadata forward pointers to the affected frozen ADRs; add the exact
   RFC-0083 and RFC-0096 Errata entries in section 11; and record conformance
   with ADR-0042 and RFC-0097.
2. **Spec — core guidance and artifact routing:** add the canonical ladder,
   `intake-intent`, repository promotion, `author-delivery-brief` modes,
   delivery-map separation, aliases, fixtures, and phase guides.
3. **Spec — shaping review and author integrations:** add
   `shaping-reviewer`, its three modes and runtime fallback, and the
   `intake-intent`, `frame-intent`, `author-delivery-brief`, and `new-spec`
   invocation contracts.
4. **Spec — RFC and architecture simplification:** add the `new-rfc`
   pre-file checkpoint, `adversarial-reviewer` RFC mode, `architect-design`
   authoring constraints, and `architect-review` YAGNI rubric with fixtures and
   guides.
5. **Spec — sealed-baseline replacement recovery:** add the guarded transition,
   baseline invalidation, reapproval/reseal sequence, recovery tests, and
   delivery guides.
6. **Migration and validation record:** publish the already-completed adopter
   study evidence, implement the approved executable fixtures, publish the
   route and alias migration guide, and retain the evidence required for the
   eventual removal gate.

Do not create a delivery brief merely because this RFC has several follow-on
specs. Create one later only if cross-spec coordination, deferred scope, or
multi-repository delivery cannot be carried cleanly by the accepted RFC and
individual specs.

## Errata

This RFC is Accepted: the body above is preserved as the original decision
record. Corrections are appended here, Approver-signed.

- **2026-08-27 (Approver: eugenelim) — the knowledge surfaces are installed
  skills and repository content.** References in the body to MCP or an internal
  provider do not establish another knowledge surface. Core MCP is only an
  invocation route to those same skill contracts and grants no additional
  authority, evidence class, knowledge owner, or permission. The lifecycle
  owner may gather bounded evidence through installed skills and repository
  content, whether directly invoked or reached through Core MCP, and supply
  that attributed evidence to `shaping-reviewer`. The reviewer itself receives
  repository read/search only; no independent retrieval, public-network,
  credential, or mutation capability is added or projected across adapters.
- **2026-08-27 (Approver: eugenelim) — a drifted plan remains recoverable
  without weakening its pin.** `baseline-replacement-required` is the sole
  plan-current-guard exception. When plan bytes already differ, explicit owner
  confirmation is bound to the run ID, sealed hash, and observed hash before
  the engine parks in `SPEC-PLAN-DRAFTING`. The mismatch is recorded as audit
  evidence and never becomes a new pin by itself; the complete review, human
  approval, sealing, remaining-work scheduling, and plan-lock sequence remains
  mandatory. Add no drift state and no advisory edit allowlist.
- **2026-08-27 (Approver: eugenelim) — spec and plan authoring must preserve
  implementation discovery.** Each acceptance checklist item carries one
  independently testable claim. A universal claim enumerates its closed set or
  names the exhaustive mechanism; no hard word budget is added. Plans name
  exact paths and symbols only when grounded, otherwise the discovery
  predicate, constraint, required outcome, and verification mode. A build-time
  contract question is recorded outside the pinned artifacts and may close
  without amendment only when a cited referent proves both still hold;
  otherwise it enters baseline replacement, even after plan drift.
- **2026-08-27 (Approver: eugenelim) — resolve-vs-surface records are
  run-control evidence, not plan content.** Light and full modes use the ignored
  `.context/work-loop/<run-id>/resolve-vs-surface.md` record. It contains only
  finding identity, `resolved-with-referent` or `surfaced-with-reason`, and
  closure status; DECIDE fails closed when it is absent or incomplete. The plan
  template carries no placeholder or copy.
- **2026-08-27 (Approver: eugenelim) — pre-EXECUTE Clean means planning-level
  sufficiency, not a prewritten implementation.** Specs and plans must make the
  observable contract, owner, boundaries, ordering, discovery predicate,
  required outcome, and verification mode sufficient to begin safely. A
  reviewer may block work that is impossible, unsafe, contradictory,
  untestable, ownerless, or unable to prove its contract. It must not require
  helper functions, fixture internals, module symbols, or exhaustive edge-case
  matrices that the implementation is meant to discover. A PLAN-time TDD stub
  is one compilable red assertion on a contract seam the accepted artifacts
  already determine, not the finished suite. When no callable seam is yet
  grounded, record `no stub (implementation-discovered)` with the discovery
  predicate, constraint, required outcome, and verification mode rather than
  inventing an interface. Finding adjudication refutes mechanism/test-shape
  demands that do not cross this planning-consequence bar.
- **2026-08-27 (Approver: eugenelim) — clustered findings trigger a root-cause
  simplification checkpoint before patching.** After adjudication, when
  sustained findings share a seam, owner, duplicated contract, or repeated
  remedy, the lifecycle owner names that common cause and applies the earliest
  sufficient cut-before-adding rung to it before responding finding by finding.
  Deletion, consolidation, or one owner-level fix is preferred when it resolves
  the cluster. Every original finding retains an auditable disposition;
  unrelated findings remain independent. This is an inline PLAN/DECIDE/REVIEW
  decision, not another reviewer, state, retry loop, script, or artifact.
- **2026-08-27 (Approver: eugenelim) — touched-seam debt is cleanup, not
  deferred product work.** A run resolves debt it introduces and pre-existing
  gaps in the exact seam it modifies, depends on, or tests through when the
  accepted contract authorizes the correction. It must not route around the
  gap, weaken verification, or create routine backlog merely to finish the
  requested delta. If the root correction requires new product authority or
  crosses a protected boundary, the run surfaces it explicitly and uses the
  existing amendment or owner-decision path before proceeding. A wholly
  separate or neighboring non-required module remains deferrable; record a
  discovered pre-existing gap there as a decision-shaped backlog item, and do
  not expand the current diff merely because the code is nearby. This adds no
  debt-review state, tracker, or cleanup artifact.
- **2026-08-27 (Approver: eugenelim) — the intent register is the sole
  row-level behavior inventory and assessment.** Follow-on specs do not copy or
  globally allocate its rows, and no cross-spec behavior-allocation fixture is
  added. A follow-on AC may cite the directly relevant row IDs, while the
  intent's per-row disposition and owner remain the audit record. This
  preserves line-level auditability without duplicate tables, range semantics,
  or construction claims that can drift.
- **2026-08-27 (Approver: eugenelim) — claim surface is subject to the same
  cut-before-adding rule.** Authored intents, briefs, RFCs, specs, plans, and
  architecture documents retain only claims needed to establish the accepted
  outcome, boundary, decision, acceptance condition, or verification. A
  necessary assertion about another document or repository surface requires
  one bounded search or read of that named target before it is stated as fact;
  otherwise it is explicitly an assumption or discovery predicate. Reviewers
  remove an unnecessary claim rather than demanding more prose or research to
  support it, and challenge unsupported assertions only when the claim is
  necessary. No claim ledger, citation framework, or extra review state is
  added.

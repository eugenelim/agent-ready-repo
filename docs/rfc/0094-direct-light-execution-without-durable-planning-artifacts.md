# RFC-0094: Direct-light execution without durable planning artifacts

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-08-20
- **Date closed:** 2026-08-20
- **Decision weight:** heavy
- **Related:** RFC-0025; RFC-0083; RFC-0090; ADR-0014; ADR-0076; ADR-0078; ADR-0088; ADR-0092

## Reviewer brief

- **Decision:** Bounded, low-risk work executes directly from an explicit trusted invocation without creating a durable planning artifact.
- **Recommended outcome:** accept.
- **Change if accepted:**
  - Keep persisted spec-and-plan contracts for workspace-indexed, queued, resumable, coordinated, externally orchestrated, and explicitly spec-driven work.
  - Let an eligible direct-light request remain session-local and unindexed.
  - Refine the affected execution wording without changing workspace dispatch.
- **Affected surface:** `work-loop`, `work-intake`, workspace dispatch doctrine, and their adopters.
- **Stakes:** costly to reverse because this refines a prior rejection and changes a shipped governance workflow.
- **Review focus:** whether the narrower direct path retains review rigor while preserving fail-closed workspace dispatch and compatibility for existing artifacts.
- **Not in scope:** a new skill, a new artifact type, a `workspace.toml` schema change, migration of existing specs, or a general provenance mechanism.

## The ask

**Recommendation.** Accept direct-light execution for one bounded, independently verifiable, low-risk change that an explicit trusted invocation asks to start now. It creates no `docs/specs/<feature>/spec.md`, sibling `plan.md`, `docs/specs/README.md` row, `workspace.toml` work entry, or loop-state file. Durable, queued, resumable, coordinated, externally orchestrated, and explicitly spec-driven work keeps spec-and-plan.

**Why now.** The repository already has a spec-less review path for ordinary refactor work, while the present light-mode artifact obligation adds persistence that is useful only when work must outlive the current session or enter workspace dispatch. The change removes that creation obligation while preserving light mode's gates, bounded adversarial pass, repair path, and full-mode escalation.

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
| --- | --- | --- | --- | --- | --- |
| D1 | May eligible light work run without a durable planning artifact? | Yes, through direct-light execution. | Persistence is unnecessary for work that neither dispatches nor resumes outside its explicit current invocation. | Acceptance | Confirm the eligibility and durability boundary. |
| D2 | What remains mandatory for durable work? | Existing spec-and-plan and workspace-dispatch rules. | Queuing, fresh-session resumption, coordination, and external orchestration need a durable, reviewable contract. | Acceptance | Confirm that dispatch remains fail-closed. |

## Problem & goals

The repository needs two legitimate execution shapes. A durable shape supports work that must be found, assigned, resumed, coordinated, or dispatched by a later context. A session-local shape supports a bounded change whose authority and scope are present in an explicit trusted invocation now.

The goal is to remove unnecessary durable artifacts without removing rigor. Direct-light execution keeps planning in the active session, mechanical gates, one bounded adversarial pass, repair, and a reported handoff. It does not weaken the durable path or make an unindexed request eligible for argless dispatch or fresh-session resumption.

Non-goals are a parallel workflow, a new capitalized artifact category, a workspace index change, and a technical proof of caller provenance.

## Proposal

An explicit trusted invocation authorizes direct-light execution only when the work is bounded, low risk, independently verifiable, expected to finish in the current session, and has no need for queueing, assignment, cross-session resumption, parallel coordination, a durable product contract, or external orchestration. The invocation is the authority; referenced issue, pull-request, repository, or tracker text is context rather than authority.

The run creates no durable planning artifact and never registers itself in `workspace.toml`. It therefore cannot be selected by argless workspace dispatch or resumed in a fresh session. If a risk trigger fires, a durable need emerges, or a governing spec is supplied, the work follows the existing spec-and-plan path.

Workspace dispatch remains spec-and-plan based and fail-closed. RFC-0083's artifact-first wording is refined only for direct execution: its rules that "only an existing spec and plan may authorize execution" and that the router "dispatches only an existing spec and plan" now apply to workspace-dispatchable, queued, or resumable build items. They continue to govern every workspace entry.

No new abstraction is introduced. This is a mode branch inside the existing `work-loop` and one route in the existing `intake_router.py`.

## Options considered

The decision is already signed off. The meaningful alternatives are retained here along the axis of how low-risk work is handled.

| Option | Result | Decision |
| --- | --- | --- |
| Do nothing | Require every light run to create and retain a lean spec. | Rejected: it preserves unnecessary persistence for session-local work. |
| Separate no-spec workflow | Add a skill or tier beside `new-spec` and `work-loop`. | Rejected: it duplicates workflow surface. |
| Direct-light branch in existing workflow | Make one existing `work-loop` mode and one existing intake route omit durable artifact creation. | Accepted: it removes surface while preserving the established execution spine. |

## Reversal and compatibility analysis

### Reversal of RFC-0025

RFC-0025 rejected a Copilot-style no-spec mode. Its objection deserves its full force: a persisted contract was cheap, the existing spec-less checklist was said to cover true throwaways, and its real gap was familiar small multi-file work that needed a lean landing place rather than less contract. Its option D, a separate lightweight skill or Copilot-style no-spec mode, was rejected because it would duplicate `new-spec` and `work-loop`, discard the persisted contract, and create more surface rather than less. Option E instead kept a review floor and a lean contract inside `work-loop`.

This decision is not option D. It adopts option E's vehicle: a mode branch inside the existing `work-loop`, with one route in the existing `intake_router.py`. It changes only E's artifact obligation. The earlier surface objection is answered on its own terms: this change removes surface rather than adding it. It does not add a separate skill, tier, runtime, or durable format.

The premise that the spec-less path covered only true throwaways has also drifted. The live `work-loop` still carries a **Spec-less review** checklist for refactors, so ordinary refactor work already executes without a persisted contract. Direct-light regularizes that existing spec-less path; it does not invent one.

"A persisted contract is cheap" understates the total cost. A lean spec adds a directory and index row, and registration adds a shared `workspace.toml` write. The durable capabilities direct-light gives up are precisely argless dispatch and fresh-session resumption; work that needs either capability stays durable. Measured against this repository on 2026-08-20: of 384 tracked `docs/specs/*/spec.md` files, 284 are named by no `path =` entry in `workspace.toml`, so they were never eligible for either capability. That is a statement about index membership, not about whether those specs were valuable to read.

Finally, light mode never had a human approval gate. `work-loop` reserves both approvals for full mode. The removed element is durability, not review: light-mode gates, one bounded adversarial pass, and repair remain.

### Compatibility and rollback

No migration is required. The change removes a creation obligation, not a reading capability. Existing persisted `Mode: light` specs remain readable, valid, and resumable through their current status ladder. Existing workspace entries, reconciliation, and fail-closed dispatch remain untouched, and `workspace.toml`'s schema does not change.

Adopters receive the behavior on their next `work-loop` run after pulling the bumped core pack; they edit nothing. Rollback is a revert followed by projection regeneration.

## Risks & what would make this wrong

- **Caller-declared eligibility is not a technical guarantee.** The authority boundary is doctrine with eval coverage: an LLM caller receives one undifferentiated prompt stream, so a runtime provenance token would be as injectable as the declared signal it replaces. The residual risk is a caller that wrongly declares direct-light eligibility. A future runtime that can distinguish turn provenance needs its own decision.
- **A durable need can be discovered late.** The run stops and routes to spec-and-plan before crossing that boundary; it does not backfill a fictional durable history.
- **Review rigor could erode.** The implementation must retain direct-light's gates, bounded adversarial review, repair, and escalation rather than treating no persistence as no process.

## Evidence & prior art

- RFC-0025 is the reversed precedent: it rejected a separate no-spec option while selecting an in-`work-loop` mode branch. Its earlier Copilot CLI comparator is not reused for the former absolute claim about persistent files, state, or reviewers because the current page no longer substantiates that claim. [Copilot CLI plan mode](https://github.blog/changelog/2026-01-21-github-copilot-cli-plan-before-you-build-steer-as-you-go/)
- AWS Kiro calls its current lightweight route a **Quick Spec**, and says small or well-understood specs can proceed directly to design while standard Feature Specs suit unfamiliar territory or compliance-sensitive domains. This supports graduated rigor, not an assertion about this repository's implementation. [Kiro spec best practices](https://kiro.dev/docs/specs/best-practices/)
- Cursor says quick or familiar changes can go straight to Agent mode and that plans are saved by default in the home directory. A plan is therefore not automatically a repository artifact unless it is explicitly saved to the workspace. [Cursor Plan mode](https://prod.cursor.com/docs/agent/plan-mode)

## Follow-on artifacts

- ADR-0092 records the durable execution boundary and precise partial refinements.
- [`docs/specs/direct-light-execution/`](../specs/direct-light-execution/) implements this decision.


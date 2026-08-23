# Journey-page decisions

- **Status:** Accepted
- **Owner:** eugenelim
- **Spec:** [`spec.md`](spec.md)
- **Decision date:** 2026-08-17

This ledger fixes the identifier and editorial choices that precede the
deterministic migration. Canonical identity is `(journey_id, humanGate.id)`.
IDs are internal, semantic, unique within a journey, stable across label and
order changes, and never derived by normalizing display text.

## Rendering and interaction contract

- `humanGates[].id` owns identity.
- `humanGates[].label` is the sole source of adopter-facing wording.
- `contract.decisionGateIds` contains only the ordered internal IDs.
- A chip is a real link to `#decision-<semantic-id>` and displays only the
  human label. It never displays the semantic ID, `globalGate`, or a legacy
  `G…` code.
- Displayed “Decision 1 of 2” ordinals derive from array order and are never
  stored as identity.
- Click or keyboard activation updates the URL fragment, brings the matching
  gate heading into view, moves focus to it, and provides a clear
  focused/targeted state in the renderer's existing palette.
- Missing, duplicate, malformed, or unresolved IDs fail generation.
- A direct fragment load resolves and targets the same gate without consulting
  its label.

Fixed section copy:

> **Where you decide**  
> The agent pauses at these points. You choose whether to continue, redirect,
> or stop.

## Approved migration mapping

A journey introduced after this migration has no legacy `G…` code to carry, so
its `Legacy value` is `none`. Inventing a retired code would assert a display
value adopters never saw.

| Journey | Legacy value | Internal ID | Adopter-facing label |
| --- | --- | --- | --- |
| `core` | `G-plan` | `approve-plan` | Approve the plan |
| `core` | `G-pr` | `merge-reviewed-change` | Merge the reviewed change |
| `product-engineering` | `G0` | `approve-intent` | Approve the intent |
| `product-engineering` | `G1.5` | `select-candidate` | Choose a candidate |
| `product-engineering` | `G2` | `approve-decision-brief` | Approve the decision brief |
| `product-engineering` | `G3` | `commit-to-build` | Commit to build |
| `release-engineering` | `G5` | `approve-production-release` | Approve the production release |
| `architect` | `G-current-state` | `correct-current-state-map` | Correct the conceptual current state |
| `architect` | `G-hotspots` | `choose-architecture-hotspots` | Choose the hotspot drill-downs |
| `architect` | `G-action` | `accept-architecture-action` | Accept the evidence and action priority |
| `experience-design` | `G-journey` | `approve-journey` | Approve the journey |
| `experience-design` | `G-aesthetic` | `approve-aesthetic-direction` | Approve the aesthetic direction |
| `experience-design` | `G-experience-review` | `review-experience-designs` | Review the experience designs |
| `atlassian` | `G-scope` | `confirm-backlog-scope` | Confirm the backlog scope |
| `atlassian` | `G-draft-review` | `review-story-drafts` | Review the story drafts |
| `atlassian` | `G-write-confirm` | `confirm-jira-writes` | Confirm the Jira changes |
| `atlassian` | `G-publish` | `approve-confluence-publish` | Approve publishing to Confluence |
| `github` | `none` | `review-github-route` | Review the repository route |
| `github` | `none` | `confirm-github-action` | Confirm one GitHub coordination action |
| `linear` | `none` | `review-linear-route` | Review the repository route |
| `linear` | `none` | `confirm-linear-action` | Confirm one Linear coordination action |
| `desk-research` | `G-scope` | `set-research-scope-and-depth` | Set the research scope and depth |
| `desk-research` | `G-synthesis` | `review-research-synthesis` | Review the research synthesis |
| `frontend-engineering` | `G-mode` | `choose-frontend-operating-mode` | Choose the frontend operating mode |
| `frontend-engineering` | `G-contract` | `approve-frontend-surface-contract` | Approve the frontend surface contract |
| `frontend-engineering` | `G-evidence` | `accept-frontend-evidence` | Accept the frontend implementation evidence |
| `frontend-engineering` | `G-review` | `review-frontend-implementation` | Review the frontend implementation |
| `governance-extras` | `G-draft` | `review-rfc-draft` | Review the RFC draft |
| `governance-extras` | `G-accept` | `decide-rfc` | Accept or decline the RFC |
| `governance-extras` | `G-merge` | `merge-accepted-adr` | Merge the accepted ADR |
| `iac-terraform` | `G-governance` | `approve-infrastructure-governance` | Approve the infrastructure governance |
| `iac-terraform` | `G-plan` | `approve-infrastructure-plan` | Approve the infrastructure plan |
| `iac-terraform` | `G4` | `merge-infrastructure-change` | Merge the infrastructure change |
| `iac-terraform` | `G5` | `approve-production-infrastructure-release` | Approve the production infrastructure release |
| `product-documentation` | `G-kind` | `confirm-documentation-page-kind` | Confirm the documentation page kind |
| `product-documentation` | `G-review` | `review-product-documentation` | Review the product documentation |
| `product-strategy` | `G-situation` | `approve-strategy-situation` | Approve the situation framing |
| `product-strategy` | `G-prfaq` | `approve-prfaq` | Approve the PR/FAQ |
| `product-strategy` | `G-cascade` | `approve-okr-cascade` | Approve the OKR cascade |

The Atlassian effect-authorizing IDs deliberately name Jira and Confluence so
future delivery-system variants do not collide semantically. These product
names are accurate public domain terms in this existing pack contract; the IDs
remain internal even though their fragments are durable.

## Priority journeys

The exact priority set is `core`, `product-engineering`, and
`release-engineering`. No other journey gains an eyebrow or transcript through
this spec.

### Core

Eyebrow: **From scoped work to a reviewed merge**

> **You:** Start work on adding export filters without changing the existing
> API route.  
> **Agent:** I routed this to the approved spec. The plan changes the query
> contract, handler, and emitted API tests. It adds no dependency or
> migration.  
> **You:** Approve the plan.  
> **Agent:** Implemented. Focused tests, type checking, lint, and the full suite
> pass. The emitted contract exposes filters and preserves existing defaults.  
> **Independent reviewer:** Clean — ready to commit.  
> **Agent:** The reviewed change is ready for your merge decision.

### Product engineering

Eyebrow: **From an uncertain idea to a build-ready decision**

> **You:** Use `discovery-loop` to take this feature idea to a build-ready
> decision brief. Release owners can see which automated check failed, but not
> what action will unblock it. Diverge before converging.  
> **Agent:** Initial framing: the affected user is the release owner; the
> failure names the rule but not the corrective action; success means choosing
> the next step without inspecting source code.  
> **You:** Approve the intent.  
> **Agent:** I compared three candidates: richer inline guidance, a linked
> runbook, and interactive remediation. I recommend concise inline guidance
> with a stable documentation link: it shortens recovery without creating a
> new runtime path.  
> **You:** Choose that candidate.  
> **Agent:** The decision brief now records the evidence, boundaries, risks,
> rejected alternatives, and success measures.  
> **You:** Approve the decision brief.  
> **Agent:** The capability map separates failure diagnosis, corrective
> guidance, and verification. The first build slice is specified and
> independently reviewable.  
> **You:** Commit to build.

### Release engineering

Eyebrow: **From a clean build to a verified production release**

> **You:** Use `release-loop` for the merged export-filter change. Deploy it to
> an isolated ephemeral environment, converge on end-to-end results and
> telemetry, then prepare the release-readiness record. Do not deploy to
> production without my approval.  
> **Agent:** The target is the merged, independently reviewed change. The
> environment is isolated from production data and traffic, and teardown is
> available. Starting the ephemeral deployment.  
> **Agent:** First iteration: the empty-result export flow failed end to end.
> Other checks and telemetry remained stable. I returned the defect to the
> inner loop, verified the reviewed fix, and redeployed.  
> **Agent:** Second iteration: all release end-to-end checks pass; latency and
> errors remain within the recorded service objectives; the deployed-diff
> security review is clean; and the rollback rehearsal passes. The
> release-readiness record links the evidence. Borderline gates: none.
> Production remains unchanged.  
> **You:** Approve the production release.

## Invocation and publication decisions

- Canonical journey content never uses `/skill-name`; slash syntax is
  client-specific.
- Use an ordinary outcome request when routing is the product behavior being
  demonstrated. Say “Use `<skill-name>`…” when the transcript depends on one
  specific supervising skill. Adapter/runtime tests—not copy alone—prove
  activation.
- `discovery-loop` and `release-loop` are real packaged skills. The transcript
  names them because it depends on their complete supervised journeys.
- Migrate canonical `packs/*/JOURNEY.md` first and regenerate copies through the
  existing projector; generated copies are never edited directly.
- Pack versions and Claude-plugin descriptions remain unchanged because this
  site/content migration does not change installed functional behavior. If
  implementation discovers a functional installed-payload change, it must stop
  and amend the spec before versioning.

## Evidence contract

- Validate all 35 IDs against the lowercase semantic-key contract, require
  uniqueness within each journey, and require every ordered decision reference
  to resolve exactly once.
- Mutation tests prove that changing a label or reordering gates leaves every
  fragment unchanged; only displayed ordinals follow order.
- Generated journey copies match canonical sources exactly.
- All 12 emitted journey pages contain one link and exactly one matching target
  per decision gate, use the approved labels, and expose no raw ID,
  `globalGate`, or legacy `G…` code as visible text.
- The three priority pages emit the exact eyebrow and transcript above.
- Invalid fixtures fail for duplicate, malformed, missing, and unresolved IDs.
- Existing route tests prove the journey route set is unchanged.
- Browser tests activate every priority chip with the keyboard at all approved
  widths and themes; the fragment changes, the correct heading receives focus
  and enters view, and direct fragment loads target the same gate.

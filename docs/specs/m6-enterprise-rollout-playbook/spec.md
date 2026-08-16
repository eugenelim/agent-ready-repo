# Spec: m6-enterprise-rollout-playbook

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (P5 Adopt); adopter-persona research
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An internal AI adoption champion can lead agent-ready-repo from a bounded pilot
through a measured team wave to an organization-wide operating model without
turning technical distribution instructions into adoption strategy. The
playbook gives the champion, CTO, platform team, and participating engineers a
shared sequence of decisions, evidence, ownership handoffs, and stop conditions.
It separates technical, enterprise, and non-technical rollout tracks, ends each
stage at a shareable artifact, and names the mid-market self-service path as an
unresolved risk instead of promising an unsupported route.

## Boundaries

### Always do

- Start with a role-proximate peer champion, a participant-known task that can
  be verified in minutes, and a named recipient for the resulting artifact.
- Put prerequisites, affected repositories, read/write boundaries, human
  control points, measurement, rollback, and stage-exit evidence before each
  rollout decision.
- Keep the technical, enterprise, and non-technical tracks distinct while
  using the same pilot → wave → organization-wide governance frame.
- Require an explicit champion → CTO → platform team → engineers ownership
  handoff and record who accepts each handoff.
- State artifact status and remote-mutation status in every stage receipt.
- Name the uncharacterized mid-market enterprise path and its evidence gap.

### Ask first

- Any move from pilot to wave or wave to organization-wide rollout.
- Any rollout that introduces credentials, external-system mutation,
  production data, compliance commitments, or a new distribution mechanism.
- Any substitution that removes a human control, changes the peer-champion
  model, or uses a first task the participant cannot independently verify.

### Never do

- Treat pack installation, skill count, generated-file count, or a capability
  tour as proof of adoption value.
- Present the technical catalogue distribution guides as a rollout strategy or
  duplicate their Artifactory, catalogue, profile, or pack-authoring procedures.
- Collapse the three tracks into one generic onboarding flow or hide track-
  specific binding constraints behind company-size labels.
- Promise a reliable self-service path for mid-market enterprise adopters while
  the research gap remains open.
- Add a skill, pack, dependency, top-level directory, telemetry service, or
  automatic control-plane behavior.
- Create a dependency on `m6-astro-work-index` or modify `ini-008`, any
  work-intake artifact, or workspace-routing code.

## Testing Strategy

- **Playbook contract: goal-based checks.** Guide validation confirms the
  external how-to frontmatter, shared-guide destination, index registration,
  internal links, and required sections. A focused pure-stdlib content test
  requires the four-role handoff, three rollout stages, three tracks, nine
  research requirements, stage gates, checklist, receipt, retrospective, and
  mid-market disclaimer while rejecting distribution-procedure duplication.
- **Decision usability: visual/manual QA.** A cold tabletop review follows one
  scenario per track. Each scenario identifies the first verifiable task,
  human decisions, stage evidence, share recipient, exit verdict, and safe-stop
  branch without consulting the spec.
- **Rendered documentation: goal-based and manual QA.** The documentation build
  publishes the guide at its generated route, the page has valid heading
  hierarchy, and all changed-page internal links resolve.

## Required playbook outline

### Role handoff

| Role | Owns | Evidence handed forward |
| --- | --- | --- |
| Champion | Candidate workflow, participant consultation, track selection, and pilot facilitation | Pilot charter with the participant-known task, recipient, baseline, human controls, and stop condition |
| CTO or executive sponsor | Risk appetite, budget boundary, success measure, and permission to widen | Signed stage decision and the business outcome the next stage must prove |
| Platform team | Pack/profile distribution, repository readiness, support path, safeguards, and operating guide | Reproducible environment, support owner, recovery path, and stage measurement record |
| Engineers and participating practitioners | Domain validation, workflow use, artifact review, and peer feedback | Shareable work artifact, verification result, friction record, and adoption verdict |

No role silently accepts another role's decision. The champion does not approve
platform controls, the CTO does not declare practitioner value, the platform
team does not infer domain correctness, and engineers do not self-authorize the
next rollout stage.

### Rollout stages

| Stage | Scope | Required evidence | Exit |
| --- | --- | --- | --- |
| Pilot | One role-proximate champion, one known workflow, one bounded team or repository | Verifiable baseline, shareable artifact, human-control log, recovery result, and named recipient feedback | Stop, revise, or approve one measured wave |
| Wave | Several teams in the same track, champion ratio and support capacity declared | Repeatable first value, adoption and quality measures, exception log, operating guide, and platform support load | Stop, hold, revise, or approve organization-wide expansion |
| Organization-wide | Approved tracks only; staged business-unit or portfolio expansion | Named owners, training and support coverage, measurement cadence, governance review, rollback, and durable documentation | Continue, narrow, or roll back through the operating review cadence |

### Track overlays

- **Technical:** solo engineers and technical PMs/product engineers. Preserve a
  short activation path, use outcome-first language, teach gate-based review,
  and prove value through a brief or spec another engineer can act on.
- **Enterprise:** FDE-mediated clients and enterprise AI champions. Require
  handoff completeness, governance depth, measurement infrastructure, a named
  internal owner, and an independently executed client run before external
  support exits.
- **Non-technical:** AI-naive knowledge workers and UX/experience designers.
  Use a same-role peer champion, identity-safe framing, source provenance, and a
  familiar deliverable whose quality the participant owns.
- **Mid-market enterprise:** treat as a discovery gap, not a fourth proven
  track. Do not widen past pilot without explicit sponsor acceptance that no
  characterized self-service path exists.

### Stage decision record

Each exit gate records: stage and track, scope, champion, executive sponsor,
platform owner, participating roles, baseline, shareable artifact and recipient,
quality result, adoption measure, support burden, exceptions, unresolved risks,
external mutations, rollback readiness, and the verdict (`stop`, `revise`,
`hold`, or `advance`).

## Acceptance Criteria

- [x] **AC1.** `guides/_shared/how-to/roll-out-agent-ready-repo-across-an-enterprise.md` exists with valid `title`, `summary`, `pack`, and `kind: how-to` frontmatter and opens with `Use this when`, `Prerequisites`, `Result`, and a copyable champion request within 120 words.
- [x] **AC2.** The playbook maps the champion → CTO → platform team → engineers adoption arc to distinct owned decisions and named evidence handoffs; no role silently accepts another role's decision.
- [x] **AC3.** Pilot, wave, and organization-wide stages each name scope, prerequisites, participant-verifiable task, human controls, measurement, rollback, shareable artifact, recipient, exit evidence, and `stop | revise | hold | advance` verdicts.
- [x] **AC4.** Technical, enterprise, and non-technical tracks retain the segment pairings and binding-constraint responses in Required playbook outline; the common stage frame does not collapse their onboarding paths.
- [x] **AC5.** The playbook applies all nine adopter-persona design requirements: decision-point prerequisites, outcome-first vocabulary, artifact status, credential lifecycle where applicable, mutation status, verifiable first task, explicit human controls, peer champion, and shareable-artifact value.
- [x] **AC6.** The rollout checklist covers sponsor and champion ownership, participant consultation, track choice, environment and repository readiness, permissions and credentials, safe inputs, expected reads/writes, support and escalation, measurement, recovery, artifact recipient, stage-gate evidence, and rollback.
- [x] **AC7.** A reusable stage decision record captures every field named in Required playbook outline and produces one explicit exit verdict.
- [x] **AC8.** A reusable retrospective template separates outcome evidence, adoption evidence, quality/verification, human-control effectiveness, platform/support burden, participant voice, identity or craft concerns, incidents and external mutations, unresolved risks, and changes required before another stage.
- [x] **AC9.** The playbook states that the mid-market enterprise segment is uncharacterized, names the FDE-outcome/self-service gap, and refuses a reliable self-service or expansion claim without new evidence.
- [x] **AC10.** The guide links to the existing live-demo and technical enterprise-distribution guides, explains their narrower ownership, and does not repeat catalogue source, Artifactory, profile, or org-stack implementation procedures.
- [x] **AC11.** `guides/_shared/how-to/README.md` registers the page; guide validation, guide-index, rendered-link, and full site construction gates pass.
- [x] **AC12.** Three recorded cold tabletop scenarios—one per track—reach an honest stage verdict using only the playbook and preserve the exclusions in this spec.
- [x] **AC13.** RFC-0064 Errata #9 records the enterprise rollout P5 slice complete, `docs/specs/README.md` reports this spec as Shipped, `docs/product/changelog.md` records the shipped playbook, and this exact five-field canonical entry is absent from `[work].queue` and `[work].active` and present once in `[work].shipped` with `needs = []`; the Astro slice remains independent with `needs = []`.

## Assumptions

- Technical: cross-pack adopter guidance belongs under `guides/_shared/how-to/` and is published by the generated documentation pipeline (source: `guides/AGENTS.md`; `author-product-docs` ownership contract).
- Technical: the existing enterprise-distribution guides own Artifactory, catalogue source, profile, and org-stack procedures, so this playbook links rather than duplicates them (source: `guides/_shared/how-to/configure-catalogue-enterprise-distribution.md`; `build-an-org-stack-pack.md`).
- Product: the minimum rollout model is three tracks—technical, enterprise, and non-technical—with peer champions, verifiable first tasks, explicit controls, and shareable artifacts (source: `docs/product/research/adopter-persona-brief.md`; user confirmation 2026-08-14).
- Product: mid-market enterprise remains an uncharacterized, high-churn-risk segment and must be named without promising a route (source: `docs/product/research/adopter-persona-brief.md`; user confirmation 2026-08-14).
- Process: RFC-0064 P5 fixes the role arc, three rollout stages, checklist, and retrospective deliverables (source: `docs/rfc/0064-ini-001-ai-native-ecosystem.md`; user confirmation 2026-08-14).
- Process: this slice is independent of `m6-astro-work-index` and excludes `ini-008`, work-intake, and workspace-routing (source: user confirmation 2026-08-15).

---
title: "Roll out agent-ready-repo across an enterprise"
summary: "Lead a bounded pilot through a measured team wave and into an organization-wide operating model with explicit owners, evidence, controls, and stop conditions."
pack: _shared
kind: how-to
---

# Roll out agent-ready-repo across an enterprise

**Use this when:** You are a peer champion preparing a controlled adoption rollout.
**Prerequisites:** A participant-known task, a named sponsor, a platform owner, a safe repository or work area, and a person who will receive the first artifact.
**Result:** A stage decision backed by a shareable artifact, verification evidence, and one explicit verdict. No stage advances automatically.
**Champion request:**

```text
Help me prepare a pilot for a task the participant already knows and can verify in minutes. Ask me to confirm the rollout track, reads and writes, human controls, artifact recipient, measures, rollback, and stop condition before we begin. Do not widen the rollout until the named owners accept the stage evidence.
```

Use the same pilot → wave → organization-wide frame for every rollout, but choose the track from the participants and their binding constraint. The track changes the onboarding path and evidence. The stage frame changes only after a human-owned decision.

## Choose a track

| Track | Participants | Binding constraint | First proof of value |
| --- | --- | --- | --- |
| **Technical** | Solo engineers and technical PMs or product engineers | A short activation window and the shift from reactive prompting to gate-based review | A brief or spec another engineer can act on |
| **Enterprise** | FDE-mediated clients and enterprise AI champions | Independent operation after external support exits, plus governance and career-risk evidence | A client-owned run and a result the sponsor can use |
| **Non-technical** | AI-naive knowledge workers and UX/experience designers | Verification burden, professional identity, and craft integrity | A familiar deliverable whose quality the participant owns |

Mid-market enterprise is an evidence gap, not a fourth proven track. Use the [mid-market constraint](#mid-market-enterprise-is-uncharacterized) before widening one of these pilots.

## Role handoff

| Role | Owns the decision | Hands forward | Who accepts the handoff |
| --- | --- | --- | --- |
| **Champion** | Consult the participant, select a candidate workflow and track, and facilitate the pilot | Pilot charter with the participant-verifiable task, recipient, baseline, human controls, and stop condition | CTO or executive sponsor accepts the handoff before funding or widening the pilot |
| **CTO or executive sponsor** | Set risk appetite, budget boundary, success measure, and permission to widen | Signed stage decision and the business outcome the next stage must prove | Platform team accepts the handoff before preparing a wider environment |
| **Platform team** | Own distribution readiness, repository safeguards, support, recovery, and measurement | Reproducible environment, support owner, recovery path, operating guide, and measurement record | Engineers and participating practitioners accept the handoff before using the workflow |
| **Engineers and participating practitioners** | Validate the domain, use the workflow, review its artifact, and report friction | Shareable artifact, verification result, participant feedback, and adoption verdict | Champion accepts the handoff before presenting the stage evidence to the sponsor |

Record each acceptance by name or accountable role in the [stage decision record](#stage-decision-record). No role silently accepts another role's decision: the champion cannot approve platform controls, the sponsor cannot declare practitioner value, the platform team cannot infer domain correctness, and participants cannot authorize the next stage.

## Prepare the stage

Complete the [rollout checklist](#rollout-checklist) with the participant and the four owners. Put prerequisites at the decision point. If a credential, permission, safe input, recovery route, or recipient is unknown, do not start and discover the omission through failure.

State the intended reads and writes in plain language. For every artifact, say whether it will exist only in chat or at an exact path and what status it will carry. For every external system, state either the approved mutation or `External mutation: none`.

Choose a task whose correctness the participant can judge in minutes. The first proof is not installation, a capability tour, pack count, or generated-file count. It is the moment a named recipient can use or review the artifact.

## Pilot

- **Scope:** One role-proximate peer champion, one participant-known workflow, and one bounded team or repository.
- **Prerequisites:** The track is selected; sponsor, platform owner, participant, and recipient are named; the baseline, safe inputs, repository boundary, permissions, expected reads and writes, measurement, recovery route, and stop condition are accepted.
- **Participant-verifiable task:** Produce one familiar artifact from a problem the participant already understands well enough to check in minutes.
- **Human controls:** The participant approves the input and judges domain quality. The platform owner approves safeguards and any credential or external mutation. The sponsor alone authorizes widening.
- **Measurement:** Record baseline time or effort, time to first usable artifact, verification result, participant confidence, support burden, and recipient feedback.
- **Rollback:** Stop the session, revert approved repository writes, revoke temporary access, and restore the isolated work state. Record what was restored and what remains outside the repository.
- **Shareable artifact:** One bounded work product with its status, provenance, verification result, and unresolved risks.
- **Recipient:** A named peer, reviewer, manager, client owner, or sponsor who can judge whether the artifact is useful.
- **Exit evidence:** Verifiable baseline, artifact and recipient feedback, human-control log, mutation receipt, recovery result, support burden, exceptions, and unresolved risks.
- **Verdicts:** `stop` ends the rollout; `revise` repeats the pilot after a named change; `hold` preserves the pilot scope while evidence is gathered; `advance` authorizes one measured wave.

Do not convert `advance` into a broad permission. It authorizes only the wave scope written in the decision record.

## Wave

- **Scope:** Several teams in the same track, with a declared champion ratio, support capacity, repository set, and timebox.
- **Prerequisites:** A pilot decision says `advance`; pilot exceptions have owners; the operating guide, training, escalation, measurement, permissions, credential lifecycle, and recovery exercise are ready for the declared teams.
- **Participant-verifiable task:** Each team completes the same first-value pattern on its own known work and names the person who independently verifies it.
- **Human controls:** Each participant retains artifact-quality judgment. Team owners approve workflow use, the platform team approves controls and exceptions, and the sponsor decides whether evidence permits wider adoption.
- **Measurement:** Compare time to first value, repeat use, artifact quality, participant confidence, exception rate, recovery success, champion load, and platform support load across teams.
- **Rollback:** Pause new starts, preserve evidence, withdraw the affected workflow or access, restore repositories or external state, and keep unaffected teams at their last approved scope.
- **Shareable artifact:** A stage report containing representative artifacts, verification outcomes, the exception log, operating guide, and support-capacity record.
- **Recipient:** The executive sponsor, platform owner, participating team owners, and the governance forum that would own wider operation.
- **Exit evidence:** Repeatable first value, adoption and quality measures, exception disposition, operating-guide use, recovery result, champion coverage, platform support load, and participant feedback.
- **Verdicts:** `stop` ends the rollout; `revise` reruns the wave after a named change; `hold` keeps the current teams without adding more; `advance` authorizes a bounded organization-wide expansion.

A successful average cannot hide a failed track or unsupported team. Record exceptions by track and role.

## Organization-wide

- **Scope:** Approved tracks only, expanded by named business unit or portfolio through a staged schedule rather than a single launch.
- **Prerequisites:** A wave decision says `advance`; accountable owners, training, support coverage, repository policy, credential lifecycle, measurement cadence, governance review, incident response, durable documentation, and rollback authority are in place.
- **Participant-verifiable task:** Every entering group starts with a role-familiar task and a local verifier; no group inherits another team's claim that the output is correct.
- **Human controls:** Business owners accept use in their area, practitioners retain domain and craft judgment, platform owners control technical safeguards, and the governance forum decides continuation or narrowing.
- **Measurement:** Review outcome value, sustained use, quality, incidents, exception volume, recovery performance, support demand, champion capacity, and track-specific participant feedback on a fixed cadence.
- **Rollback:** Stop expansion, narrow or disable affected workflows, revoke access, recover repository and external state, notify owners and recipients, and review the incident before re-entry.
- **Shareable artifact:** A durable operating review with adoption outcomes, verified artifacts, control effectiveness, support capacity, incidents, exceptions, and decisions by business unit and track.
- **Recipient:** The accountable executive, platform and governance owners, business-unit leaders, champion network, and participating practitioners.
- **Exit evidence:** Named owners, training and support coverage, measurement history, governance decision, tested rollback, current operating documentation, participant voice, and unresolved-risk disposition.
- **Verdicts:** `stop` retires the affected rollout; `revise` changes the operating model before another review; `hold` keeps the current approved scope; `advance` continues only the explicitly approved staged expansion.

Organization-wide is an operating cadence, not a terminal success label. Each review can narrow or roll back a track.

## Technical track

Use this overlay for solo engineers and technical PMs or product engineers. Preserve a short activation path and use outcome-first language before pack or skill terminology. The first task should end in a brief or spec another engineer can act on, then teach gate-based review by making assumptions, acceptance, and verification visible.

Keep optional setup out of the first-value path. A technical participant proves value by producing useful work and handing it to an engineer, not by installing more capabilities.

## Enterprise track

Use this overlay for FDE-mediated clients and enterprise AI champions. Require handoff completeness, governance depth, measurement infrastructure, a named internal owner, and an independently executed client run before external support exits. The client-owned run must exercise the documented support and recovery paths rather than repeat a demonstration led by the FDE.

The sponsor's evidence should connect a verified work outcome to budget, risk, and adoption measures. Do not let polished outcome-first copy substitute for control evidence.

## Non-technical track

Use this overlay for AI-naive knowledge workers and UX/experience designers. A same-role peer champion begins with a familiar deliverable, uses identity-safe framing, preserves source provenance, and produces work whose quality the participant owns. For design work, protect craft judgment: assistance may remove collation effort, but it does not take strategic authorship from the practitioner.

Do not ask the participant to verify an unfamiliar technical intermediate. Ask them to judge the deliverable they already know how to evaluate.

## Research constraints

Apply these requirements at every stage:

1. **Decision-point prerequisites:** Ask whether the required environment, access, input, verifier, and recovery path exist before attempting the task.
2. **Outcome-first vocabulary:** Name the work result before internal pack, skill, or workflow terms.
3. **Artifact status:** Every receipt says `chat-only` or gives the exact artifact path and status.
4. **Credential lifecycle:** Where credentials apply, name the owner, approved storage boundary, expiry or reauthentication trigger, reauthentication route, revocation step, and stage-end cleanup before use.
5. **Mutation status:** Every receipt lists approved repository or external changes, or says `External mutation: none`.
6. **Participant-verifiable first task:** Start in a domain the participant knows well enough to verify in minutes.
7. **Explicit human controls:** Say who decides at each approval, quality, mutation, exception, and widening point.
8. **Peer champion:** Use a role-proximate practitioner for consultation and facilitation instead of a top-down mandate or vendor-shaped tour.
9. **Shareable-artifact value:** End at the named recipient's use or review of the artifact, not at a capability claim.

## Rollout checklist

Copy this list into the stage workspace and complete it before work begins:

- [ ] **Sponsor and champion ownership:** Name both people or accountable roles and the decisions each owns.
- [ ] **Participant consultation:** Record the participant's problem, concerns, existing practice, and consent to the bounded attempt.
- [ ] **Track choice:** Select technical, enterprise, or non-technical from the participants and binding constraint; do not select by company size alone.
- [ ] **Environment and repository readiness:** Record the isolated work state, affected repositories, required packs, and readiness checks.
- [ ] **Permissions and credentials:** Record least privilege, owner, lifecycle, revocation, and whether credentials are unnecessary.
- [ ] **Safe inputs:** Confirm that inputs are sanitized and exclude secrets, personal information, and unapproved production data.
- [ ] **Expected reads and writes:** Name readable paths and systems, writable paths and systems, artifact destinations, and status.
- [ ] **Support and escalation:** Name the champion, platform support owner, response path, exception authority, and stop authority.
- [ ] **Measurement:** Record the baseline, outcome, adoption, quality, and support measures before the stage.
- [ ] **Recovery:** Rehearse or verify repository recovery and any external-system recovery that the stage can require.
- [ ] **Artifact recipient:** Name who receives the artifact and how they judge its usefulness.
- [ ] **Stage-gate evidence:** Name the records required for a verdict and who validates each one.
- [ ] **Rollback:** Name the trigger, authority, steps, communications, and evidence that rollback completed.

An unchecked item blocks the stage unless the decision record names the exception owner and the sponsor chooses `hold` or `stop`. It never defaults to `advance`.

## Stage decision record

Copy and complete one record at every stage exit:

```text
Stage and track:
Scope:
Champion:
Executive sponsor:
Platform owner:
Participating roles:
Baseline:
Shareable artifact and recipient:
Artifact path or chat-only status:
Quality result:
Adoption measure:
Support burden:
Exceptions:
Unresolved risks:
External mutations:
Rollback readiness:
Handoff acceptances:
Exit evidence reviewed by:
Verdict: stop | revise | hold | advance
Verdict owner and date:
Conditions before another stage:
```

The verdict is singular. If owners disagree or required evidence is absent, choose `hold`, `revise`, or `stop`; do not average the disagreement into `advance`.

## Retrospective

Run this after the decision record, including after `stop`:

```text
Stage and track:
Outcome evidence:
Adoption evidence:
Quality and verification:
Human-control effectiveness:
Platform and support burden:
Participant voice:
Identity or craft concerns:
Incidents and external mutations:
Unresolved risks:
Changes required before another stage:
Owners and due dates:
Evidence to preserve:
```

Separate evidence from interpretation. Preserve participant disagreement and failed recovery attempts instead of smoothing them into a success narrative.

## Mid-market enterprise is uncharacterized

Mid-market enterprise remains uncharacterized. The known problem is an FDE-outcome/self-service gap: organizations may be sold an externally supported outcome and then receive documentation without equivalent operating support. There is no reliable self-service path for enterprise-complexity adoption today.

Do not widen a mid-market pilot by borrowing the enterprise track's success claim. A sponsor may accept a bounded pilot with named support and stop conditions, but `advance` requires new evidence that characterizes the participants' binding constraint and demonstrates an independently repeatable path.

## Keep adoption and technical distribution separate

This playbook owns adoption stages, evidence, role handoffs, and rollout verdicts. Use the [live demo](../../core/how-to/run-a-live-demo.md) to facilitate a bounded first workflow and produce its delivery handoff.

The [enterprise distribution guide](configure-catalogue-enterprise-distribution.md) owns technical distribution through an internal catalogue channel. The [org-stack implementation guide](build-an-org-stack-pack.md) owns the technical distribution work for shared architecture, conventions, framework knowledge, and profiles. Those guides remain the source of truth for catalogue source, Artifactory, profile, and org-stack procedures; do not copy those procedures into an adoption plan.

## Completion receipt

End each stage with a receipt that another owner can inspect:

```text
Stage and track:
Verdict and owner:
Artifact: <chat-only | exact path>
Artifact status:
Share recipient and feedback:
Verification result:
Human decisions recorded:
Repository writes: <none | exact paths>
External mutations: <none | exact systems and changes>
Rollback status:
Unresolved risks:
Next allowed action:
```

The likely next request after a pilot is: `Review this stage decision with the sponsor, platform owner, and participants. Challenge missing evidence, then return exactly one verdict without widening the recorded scope.`

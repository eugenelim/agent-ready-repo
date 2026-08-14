---
title: "How to run a 30-minute live workflow demo"
summary: "Show a technical, enterprise, or non-technical team how shaping hands work to Core without turning the session into a capability tour."
pack: core
kind: how-to
---

# How to run a 30-minute live workflow demo

**Use this when:** You are a peer champion showing a team how agent-ready work moves from a familiar problem to a reviewable delivery handoff.
**Prerequisites:** The adopting organization's repository, a participant-verifiable problem, an isolated work state, the packs required by the chosen track, and—on the non-technical path—an existing repo-scoped Product Engineering output layout.
**Result:** One Draft spec/plan pair, with its real provenance and human controls visible, ready to share with a named reviewer; no implementation, work registration, or external-system mutation.

Choose a track below, copy its opening request, and run it against the team's
own repository. Say where the work enters, pause at the decisions owned by that
pack, and stop after the Draft spec and plan. The point is not to show how many
skills are installed. It is to let another person inspect a useful artifact and
see where human judgment controlled it.

## Choose the workflow, not the persona label

| If the input is… | Use | Scope | Path shown | End state |
| --- | --- | --- | --- | --- |
| One bounded, independently testable feature | **Technical** | Core at repo scope | `new-spec` | No brief; one Draft spec/plan pair |
| A structured multi-feature handoff | **Enterprise** | Core at repo scope | `receive-brief` → selected slice → `new-spec` | Source brief `Ready`; one Draft spec/plan pair |
| A feature-level product problem that still needs shaping | **Non-technical** | Product Engineering at user scope, then Core at repo scope | `frame-intent` → `de-risk-intent` → `decompose-intent` → `receive-brief` → `new-spec` | Draft intent, Ready leaf brief, one Draft spec/plan pair |

The labels name likely audiences; the **input shape chooses the workflow**. A
technical participant with a multi-feature handoff still uses the enterprise
path. A non-technical participant with an already structured brief can enter
Core directly.

Do not add a pack for atmosphere:

- Use `governance-extras` only when the desired artifact is an RFC, ADR, or
  conventions change—not merely because a pilot has controls.
- Use `product-strategy` when the open question is upstream strategy and the
  desired artifact is a PRFAQ, market analysis, or OKR cascade—not as a
  short-form feature-shaping path.
- Experience Design can supply journey, research, or craft evidence for a UX
  example. Product Engineering still owns intent shaping and Core owns the
  delivery handoff.

## Pre-flight — before starting the timer

Fill this card aloud. Do not start the clock until the participant accepts it.

```text
Track:
Participant who recognizes the problem:
Human approver for today's decisions:
Share recipient:
Installed pack and scope:
Agent may read:
Agent may write:
Expected artifacts and statuses:
Known verification signal:
Isolated work state:
Safe, sanitized inputs confirmed: yes / no
External mutation: none
Work-intake registration: none
Timer: 30 minutes maximum
```

Stop before the timer if the pack is missing at the required scope, the work
state is not isolated, the inputs contain secrets or personal/production data,
the readable or writable paths are unclear, or the participant cannot verify
the problem. Do not swap in a canned repository to save the demonstration.

## The five teaching beats

These are shared presentation timeboxes, not shared workflow states. Core does
not have Product Engineering's G0/G1.5/G2 ladder, and the non-technical path
below does not claim to run the full `discovery-loop`.

| Beat | Maximum | What it teaches |
| --- | ---: | --- |
| Pre-flight | 4 min | The participant can see the pack, scope, evidence, writes, recipient, and stop boundary. |
| Enter | 7 min | The shape of the input determines the correct workflow entry. |
| Shape or cut | 6 min | The human owns a real judgment defined by the invoked skill. |
| Draft delivery handoff | 9 min | Provenance survives into exactly one Draft spec/plan pair. |
| Receipt | 4 min | The group verifies what exists, what remains uncertain, and who acts next. |

Set one visible 30-minute timer. If any beat reaches its maximum, stop at the
current artifact, mark what is incomplete or unverified, and use the receipt's
**Safe stop** outcome. Do not borrow time from a later control point.

## Technical — Core direct feature path

Use this path for a known failing check, recurring manual repository task, or
bounded delivery friction that already fits one independently testable feature.
The peer champion facilitates with the engineer or technical PM who recognizes
the baseline. The share recipient is the engineer who would review or implement
the slice.

### Pre-flight — 4 min maximum

**Say:** “This is one feature-sized Core task. We will use `new-spec` directly,
create no brief, and stop before approval or implementation.”

**Reads:** the named failing check or command output, its owner files, the
repository's architecture and conventions, and no other paths.

**Writes:** `docs/specs/<demo-slug>/spec.md` and `plan.md` only.

**You see:** the baseline command and exact allowed paths on the pre-flight card.

**You decide:** whether the baseline is recognizable, reproducible, and worth
specifying now.

**Narrate:** Core permits a single feature to enter at `new-spec`; a placeholder
brief would add no useful product decision.

**Stop if:** the baseline cannot be reproduced or the request contains more than
one independently shippable feature.

### Enter — 7 min maximum

**Say:** Paste this request, substituting the bracketed values:

```text
Use Core's new-spec skill on [bounded problem]. Read only [evidence paths].
Surface and verify the technical, product, and process assumptions, then draft
one independently testable spec/plan pair at docs/specs/[demo-slug]/. Do not
create a brief, implement, approve, register work, or change an external system.
```

**Reads:** only the paths on the card plus the canonical project sources needed
to verify each candidate assumption.

**Writes:** the two scaffolded Draft files.

**You see:** `new-spec`'s verified and unverified assumptions, each with its
evidence source.

**You decide:** confirm, correct, or leave unresolved every surfaced assumption;
then confirm the feature shape and implementation stack.

**Narrate:** the agent must expose assumptions before it can fill Objective,
Boundaries, Testing Strategy, or Acceptance Criteria.

**Stop if:** a load-bearing assumption cannot be resolved inside the session.

### Shape or cut — 6 min maximum

**Say:** “Show us the proposed Objective, success criteria, Always do / Ask first
/ Never do boundaries, and the one-slice plan before completing the Draft.”

**Reads:** the approved assumption record and named baseline evidence.

**Writes:** the spec and plan bodies.

**You see:** a precise outcome, observable acceptance criteria, construction
tests, touched paths, dependencies, exclusions, and no brief backlink.

**You decide:** whether the scope is one feature, the success command is trusted,
and the structural `Never do` boundary prevents expansion.

**Narrate:** this is Core's feature-sizing and assumption checkpoint, not a
renamed G0/G1.5/G2 discovery sequence.

**Stop if:** the proposed slice is not independently testable or the success
command would not persuade the participant.

### Draft delivery handoff — 9 min maximum

**Say:** “Complete the Draft pair. Trace one acceptance criterion to the real
verification command and one plan task to its owning file. Do not run the plan.”

**Reads:** the current Drafts and the approved repo evidence.

**Writes:** only the same spec and plan.

**You see:** `Status: Draft`, `Brief: none`, one command-to-AC trace, and one
task-to-file trace.

**You decide:** whether the Draft pair is coherent enough to circulate for its
later, formal approvals.

**Narrate:** “ready to circulate” is a review-readiness judgment, not spec or
plan approval.

**Stop if:** either trace relies on a guessed command, path, or owner.

### Receipt — 4 min maximum

**Say:** “We have stopped at Draft. I will read the completion receipt; correct
any path, status, proof claim, decision, or unresolved item before sharing.”

**Reads:** the Draft spec/plan pair, baseline proof, elapsed timer, and named
recipient.

**Writes:** no repository file; render the shared
[completion receipt](#completion-receipt) in the conversation only.

**You see:** `Brief: none`, both Draft paths, the verified command result,
unresolved items, later approval as the next action, and the mutation statement.

**You decide:** confirm or correct the receipt, then choose whether to share it
with the named engineer.

**Narrate:** the verified handoff is the value; the demo created neither an
approval nor implementation.

**Stop if:** any receipt field is unknown or the elapsed time exceeds 30
minutes. Record **Safe stop** rather than filling the gap from memory.

## Enterprise — Core structured-handoff path

Use this path when an enterprise champion or FDE peer already has a structured,
sanitized multi-feature handoff. The domain owner recognizes the control gap;
the share recipient owns platform, risk, security, or engineering approval.

Prepare an **unqueued Draft brief** before the demo. It must name Outcome,
Scope, non-goals, Appetite, at least one Rabbit hole, and a Spec map placeholder.
This path deliberately skips `author-brief`, whose normal contract includes a
`workspace.toml` queue write.

### Pre-flight — 4 min maximum

**Say:** “We will receive an existing governed-pilot brief through Core, confirm
its cut, and spec one slice. We will not register the brief or create an RFC.”

**Reads:** the Draft brief, supplied policy/control text, sanitized repository
evidence, architecture, and conventions.

**Writes:** the existing brief plus one `docs/specs/<demo-slug>/spec.md` and
`plan.md` pair. `workspace.toml` is explicitly excluded.

**You see:** the brief path, named control owner, expected spec path, and
`External mutation: none` on the card.

**You decide:** whether the brief is a real handoff, the evidence is safe, and
the named owner can adjudicate its control language.

**Narrate:** enterprise depth comes from evidence, ownership, and traceability;
it does not silently activate `governance-extras`.

**Stop if:** the brief is unstructured raw intake, no domain owner is present,
or a policy claim cannot be shown to participants.

### Enter — 7 min maximum

**Say:** Paste this request:

```text
Use Core's receive-brief skill on [brief path]. Confirm its load-bearing
fields, propose independently shippable slices, and wait for the domain owner
to choose the first slice. Mark the brief Ready only if its gate passes, then
use new-spec for that slice. Do not implement, approve, register work, edit
workspace.toml, or change an external system.
```

**Reads:** the brief and only its declared evidence sources.

**Writes:** elicited corrections to the brief; no spec exists until the human
confirms the decomposition.

**You see:** Outcome and Scope gaps surfaced, proposed vertical slices, and any
uncovered outcome or epic-sized item called out.

**You decide:** resolve missing load-bearing facts and confirm, redirect, or
reject the independently shippable cut.

**Narrate:** `receive-brief` receives a handoff a level above a feature; it does
not accept a component-layer split as delivery slices.

**Stop if:** Outcome or Scope remains unknown, the proposed cut drops an outcome,
or the first slice cannot ship and test independently.

### Shape or cut — 6 min maximum

**Say:** “Before marking this Ready, show Outcome, Appetite, at least one Rabbit
hole, and the populated Spec map. For the selected pilot slice, show population,
excluded systems, accountable owner, success and stop measures, rollback
expectation, and who accepts residual risk.”

**Reads:** the confirmed brief and supplied policy/control evidence.

**Writes:** the confirmed Spec map row and Ready status in the brief only after
all four gate fields are visible.

**You see:** a policy/control source for each governed claim, a named owner, and
one selected slice. Other slices remain visible rather than being discarded.

**You decide:** confirm the decomposition and the pilot boundary; accept no
guessed control interpretation.

**Narrate:** a Ready brief records an agreed handoff. It does not approve the
derived spec or accept residual risk on the approver's behalf.

**Stop if:** any Ready field is absent, the policy owner disputes the reading,
approval evidence is unavailable, or rollback is undefined.

### Draft delivery handoff — 9 min maximum

**Say:** “Use `new-spec` for only the selected slice. Preserve the brief
backlink, surface its assumptions, and trace one policy statement through an
acceptance criterion to plan evidence. Do not implement.”

**Reads:** the Ready brief, selected slice, approved evidence, architecture, and
conventions.

**Writes:** one Draft spec/plan pair; the spec carries the brief backlink.

**You see:** policy/control → acceptance criterion → plan-evidence trace,
affected and excluded paths, success/stop measures, rollback expectation, and
a named residual-risk recipient.

**You decide:** confirm the `new-spec` assumptions and whether the Draft pair is
ready to circulate to the named approver.

**Narrate:** reviewability and auditability are the value—not generic speed,
compliance certification, or an ROI promise.

**Stop if:** the trace contains an unsupported compliance claim or the Draft
widens the confirmed pilot boundary.

### Receipt — 4 min maximum

**Say:** “We have stopped at Draft. I will read the completion receipt, including
the unresolved mid-market applicability; correct it before sharing.”

**Reads:** the Ready brief, Draft spec/plan pair, policy trace, elapsed timer,
and named approver.

**Writes:** no repository file; render the shared
[completion receipt](#completion-receipt) in the conversation only.

**You see:** the brief and Draft paths/statuses, policy-to-plan proof, owner and
residual-risk recipient, unresolved mid-market gap, later approvals, and the
mutation statement.

**You decide:** the domain owner confirms or corrects the receipt and chooses
whether to share it with the named approver.

**Narrate:** the mid-market enterprise segment remains uncharacterized; the
pilot and self-service path are not presented as proven for it.

**Stop if:** a receipt field or owner is unknown, a proof claim is unsupported,
or elapsed time exceeds 30 minutes. Record **Safe stop**.

## Non-technical — Product Engineering shaping into Core

Use this path for a participant-known workflow or onboarding problem that needs
product shaping before delivery. A role-proximate peer champion facilitates
with an AI-naive knowledge worker or UX/experience designer. The recipient is
the product, design, content, or operations owner who can act on the result.

Keep the example at **feature level** and **app scale**. Bring one existing
guide/process source plus two or three sanitized observations. This is the
short intent path, not the full 60–120 minute `discovery-loop`.

Before the session, require a repo-root `agentbundle-layout.toml` whose
`[product] output_dir` already resolves inside that repository. Surface the
resolved absolute path on the pre-flight card. The baseline demo never creates
or edits a user-home layout file; if the repo layout is absent or resolves
outside the repository, stop before starting the timer.

### Pre-flight — 4 min maximum

**Say:** “We will shape a feature in user-scoped Product Engineering, then hand
its leaf brief to repo-scoped Core. You retain the meaning and quality bar.”

**Reads:** only the named guide/process file, sanitized observations,
repository layout configuration, architecture, and conventions.

**Writes:** one intent under the configured Product Engineering output,
`docs/product/briefs/<demo-slug>.md`, and one Draft spec/plan pair.
`workspace.toml` is excluded.

**You see:** both installed packs and scopes, the resolved intent output path,
the Core handoff paths, and `External mutation: none` on the card.

**You decide:** confirm app scale, feature altitude, brownfield/greenfield
posture, the existing repo-scoped layout, readable sources, resolved output
path, and authorship boundary.

**Narrate:** Product Engineering can be installed for the user while its
artifacts remain anchored to the adopting repository; Core begins at the leaf.

**Stop if:** either pack is unavailable at its required scope, the repo-scoped
layout is absent, the resolved output escapes the intended repository, a
user-home layout write would be required, or the participant cannot correct the
source interpretation.

### Enter — 7 min maximum

**Say:** Paste this request:

```text
Use user-scoped Product Engineering to frame [workflow problem] at feature
level and app scale from [source paths]. Pause at G0 for my framing decision,
test the one riskiest assumption against a predeclared kill condition, and
project the surviving intent to one Core brief. Then use repo-scoped Core to
receive that brief and draft one spec/plan pair. Do not decide user meaning or
craft quality for me; do not implement, approve, register work, or change an
external system.
```

**Reads:** the declared sources and configured Product Engineering output path.

**Writes:** a Draft feature intent with the source and knowledge-surface
assumptions recorded.

**You see:** a named user, solution-independent problem, functional/emotional/
social jobs, struggling moment, steerable input, lagging outcome, guardrail,
and seeded assumptions.

**You decide:** G0—approve, correct, or reject the framing and the participant's
own vocabulary. Wait for an explicit verdict.

**Narrate:** the agent collates and structures evidence; the participant owns
the interpretation, vocabulary, and craft bar.

**Stop if:** the framing is generic, solution-led, or cannot cite the supplied
sources.

### Shape or cut — 6 min maximum

**Say:** “Name the single riskiest assumption, declare what result would kill
the bet before considering evidence, and record the real-world validation hook.
If it survives, project this feature leaf to a Core brief and show its Ready
fields.”

**Reads:** the ratified intent and named source evidence.

**Writes:** the assumption result and validation hook on the intent, then a Core
brief containing Outcome, Appetite, at least one Rabbit hole, and a one-row Spec
map skeleton.

**You see:** reversibility, the predeclared kill condition, survive/kill verdict,
and any desk-grounded claim marked `to-validate`; after a survive verdict, the
leaf brief preserves intent provenance and all four Ready fields.

**You decide:** accept or correct the kill condition and verdict; confirm the
leaf projection. Core then verifies the four Ready fields and the one-slice cut
before marking the brief `Ready`.

**Narrate:** desk grounding is not real-world validation. A killed assumption
stops here; it never gets decomposed into work.

**Stop if:** the assumption is killed, the validation hook is missing, a Ready
field is absent, or the brief loses the participant's correction.

### Draft delivery handoff — 9 min maximum

**Say:** “Use Core's `receive-brief` to confirm the one-slice cut, then
`new-spec` to draft one spec/plan pair. Preserve the intent and brief provenance
and show where my correction appears. Do not implement.”

**Reads:** the Ready leaf brief, source-backed intent, architecture, and
conventions.

**Writes:** one Draft spec/plan pair with the brief and discovery provenance.

**You see:** source → corrected intent → Ready brief → Draft acceptance-criterion
trace, plus the unresolved validation hook.

**You decide:** confirm the Core decomposition and `new-spec` assumptions, then
decide only whether the Draft pair is ready to circulate.

**Narrate:** the visible boundary between user-scoped shaping and repo-scoped
delivery preserves both product authorship and engineering reviewability.

**Stop if:** provenance breaks, the correction disappears, the quality bar is
silently agent-authored, or the run reaches the time limit.

### Receipt — 4 min maximum

**Say:** “We have stopped at Draft. I will read the completion receipt; correct
the interpretation, provenance, or validation status before sharing.”

**Reads:** the Draft intent, Ready brief, Draft spec/plan pair, correction and
validation-hook trace, elapsed timer, and named recipient.

**Writes:** no repository file; render the shared
[completion receipt](#completion-receipt) in the conversation only.

**You see:** both packs/scopes, every artifact and status, source-to-spec
provenance, the participant correction, the `to-validate` item, later approvals,
and the mutation statement.

**You decide:** the participant confirms or corrects the receipt, then chooses
whether to share it with the named product/design/content/operations owner.

**Narrate:** preserved authorship and a traceable delivery handoff are the
value; faster drafting alone does not make the demo successful.

**Stop if:** a receipt field is unknown, the participant disputes the
interpretation, provenance is broken, or elapsed time exceeds 30 minutes.
Record **Safe stop**.

## Completion receipt

Read this aloud and let the participant correct it before sharing:

```text
Outcome: Success / Safe stop
Track:
Packs and scopes used:
Skills invoked:
Changed paths and statuses:
Provenance links:
Verified proof:
Unresolved or unverified items:
Human decisions recorded:
Formal spec approval fired: no
Formal plan approval fired: no
Implementation started: no
Work-intake registration performed: no
External systems changed: no
Next reviewer and action:
Share recipient:
Elapsed time:
```

A successful receipt requires the selected canonical path, one verified Draft
spec/plan pair, and a named recipient within 30 minutes. Missing prerequisites,
a declined control, a killed assumption, an unverified output, or an expired
timer produces **Safe stop**, not a success claim.

## Continue after the demonstration

The demo-created spec and plan are still Draft. Circulate the spec for its
formal approval, then the plan. Only after both approvals should the team invoke
the normal [plan and execute non-trivial work](plan-and-execute-non-trivial-work.md)
flow.

For procedural depth:

- [Plan and execute non-trivial work](plan-and-execute-non-trivial-work.md) —
  Core `new-spec` and `work-loop`.
- [Receive a product brief and decompose it into specs](receive-a-product-brief-and-decompose-it-into-specs.md)
  — Core structured-handoff behavior.
- [Shape a feature intent](../../product-engineering/how-to/shape-a-feature-intent.md)
  — Product Engineering's feature-level intent-to-Core path.
- [Orient at session start](orient-at-session-start.md) — read workspace state
  when returning after the demo; the live demo itself does not register work.

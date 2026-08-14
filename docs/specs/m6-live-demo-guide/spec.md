# Spec: m6-live-demo-guide

- **Status:** Shipped
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (P5 Adopt)
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An internal peer champion can run a credible live demonstration on the adopting
organization's own repository in no more than 30 minutes. The guide teaches the
shaping → brief → spec relationship through three real pack journeys rather than
forcing three personas through one invented workflow: Core direct-to-spec for a
bounded technical feature, Core brief intake for an enterprise handoff, and
Product Engineering shaping followed by a visible Core handoff for a
non-technical participant. Each track ends with a shareable Draft spec/plan pair,
shows which pack and scope own every step, exposes the actual human controls of
the invoked skills, and stops before formal spec approval or implementation.

## Boundaries

### Always do

- Use a repo-local problem that the participants can verify in minutes.
- Name the selected pack, install scope, entry skill, input artifact, output
  artifact, and stopping point during pre-flight.
- Put prerequisites, permissions, expected writes, timing, and the no-external-
  mutation posture in the pre-flight checklist before the timer begins.
- Use only the human controls that the selected canonical skills actually
  define; do not relabel Product Engineering discovery gates as Core gates.
- End with exact artifact paths and statuses, the next reviewer, and a statement
  of whether any external system was changed.
- Give the facilitator exact words to open, narrate, pause, recover, and hand
  off each track; do not leave pack routing or track adaptation to improvisation.

### Ask first

- Any demo that writes outside the current repository or mutates a tracker,
  design tool, cloud service, or other external system.
- Any extension beyond the AC2 timebox, implementation of a Draft spec, or
  change from peer-champion facilitation to a vendor-led script.
- Any substitution that changes the owning pack, removes a human control, or
  uses a problem participants cannot independently verify.

### Never do

- Use credentials, secrets, production data, or protected personal information
  as demo input.
- Present a capability tour, canned vendor repository, or synthetic success as
  proof of value in place of the organization's own familiar problem.
- Treat `governance-extras` as an enterprise prerequisite merely because the
  example is governed, or treat `product-strategy` as a short-form substitute
  for Product Engineering shaping.
- Collapse the three tracks into one generic shaping flow or claim that all
  three use the same gates and intermediate artifacts.
- Approve or implement the generated spec/plan as part of the demo.
- Add a new skill, pack, dependency, top-level directory, or external service.
- Create a dependency on `rendered-site-link-debt` or modify `ini-008` or any
  work-intake artifact, including `workspace.toml` queue entries.

## Testing Strategy

- **Guide structure and workflow mapping: goal-based checks.** Guide validation
  confirms the how-to frontmatter, canonical path, index registration, unique
  routes, and internal links. `tools/test_live_demo_guide.py` confirms that the
  five budgets total 30 minutes; pins the Core/Core/Product Engineering map and
  install scopes; rejects a shared fictitious G0/G1.5/G2 sequence; and requires
  each track's prompt, inputs, skills, artifacts, decisions, proof, narration,
  recipient, and recovery cues.
- **Runbook usability: visual/manual QA.** Three cold walkthroughs—one per
  track—use a repo-specific scenario and a facilitator who did not author the
  guide. Each reaches its pack-specific intermediate artifacts and a Draft
  spec/plan pair within the timebox, records every human verdict, and produces
  the completion receipt without beginning implementation or registering work.
- **Boundary behavior: manual scenario checks.** The facilitator exercises the
  missing-pack, unsuitable-problem, declined-control, timebox-expiry, and
  unverified-output branches and can stop safely with an honest status.

## Required demo outline

### Pack and journey map

| Track | Owning journey | Install scope | Canonical path demonstrated | Successful end state |
| --- | --- | --- | --- | --- |
| Technical | Core | repo | bounded feature request → `new-spec` | no brief; one Draft `spec.md`/`plan.md` pair ready to circulate |
| Enterprise | Core | repo | existing structured Draft brief → `receive-brief` → one confirmed slice → `new-spec` | source brief reaches `Ready`; one Draft `spec.md`/`plan.md` pair ready to circulate |
| Non-technical | Product Engineering, then Core | user, then repo | feature-level `frame-intent` → `de-risk-intent` → `decompose-intent` → Core `receive-brief` → `new-spec` | Draft intent and Ready leaf brief preserve provenance; one Draft `spec.md`/`plan.md` pair ready to circulate |

The enterprise track does not invoke `author-brief`: its input is already a
structured external handoff, and `author-brief` would attempt to register that
brief in `workspace.toml`. `governance-extras` is relevant only when the actual
desired artifact is an RFC, ADR, or conventions change; that is outside this
demo. `product-strategy` is likewise outside the baseline because a PRFAQ,
market analysis, or OKR cascade sits upstream of the feature-level timebox.
Experience Design may supply source evidence for a UX-shaped example, but it
does not own the non-technical track's intent-to-delivery routing.

### Shared 30-minute teaching frame

The five timeboxes are shared presentation beats, not a claim that the three
pack journeys have identical internal states.

| Beat | Maximum | Common facilitator obligation | Track-specific work |
| --- | ---: | --- | --- |
| Pre-flight | 4 min | Name participant, approver, recipient, pack/scope, exact readable evidence, allowed writes, expected artifacts, timer, and `No external systems changed`; verify the participant recognizes the problem. | Technical confirms Core and a reproducible repo signal. Enterprise confirms Core and an existing unqueued Draft brief. Non-technical confirms user-scope Product Engineering plus repo-scope Core and sanitized source material. |
| Enter | 7 min | Paste the track's opening request and show why this is the correct journey entry point. | Technical invokes `new-spec` directly. Enterprise invokes `receive-brief` on the prepared handoff. Non-technical invokes feature-level `frame-intent` and confirms app scale at G0. |
| Shape or cut | 6 min | Surface the judgment the participant owns and wait for its actual verdict. | Technical confirms `new-spec` assumptions and boundaries. Enterprise confirms `receive-brief`'s independently shippable decomposition and selects one slice. Non-technical uses `de-risk-intent` for the one riskiest assumption, records the kill condition and validation hook, then confirms `decompose-intent`'s leaf brief. |
| Draft delivery handoff | 9 min | Produce one Draft spec/plan pair and show its provenance without starting implementation. | Technical completes `new-spec`. Enterprise lets `receive-brief` mark the brief `Ready`, then chains `new-spec` for only the chosen slice. Non-technical hands the projected leaf brief to Core `receive-brief`, confirms the one-slice cut, then chains `new-spec`. |
| Receipt | 4 min | Verify paths, statuses, provenance links, unresolved items, proof, next reviewer, recipient, elapsed time, and mutation statement; ask only whether the result is accurate and worth sharing. | All tracks stop before formal spec approval, plan approval, queue registration, or `work-loop` execution. |

### Technical track — Core direct feature path

- **Participants:** a role-proximate senior engineer champion with a solo
  engineer and/or technical PM/product engineer; the recipient is the engineer
  who would implement or review the slice.
- **Use this problem:** one known failing check, recurring manual repo task, or
  bounded delivery friction backed by an existing test, command output, issue,
  or source path. It must already be feature-sized; a multi-feature ask routes
  to the enterprise-style brief path instead.
- **Opening request:** “Use Core's `new-spec` on this bounded repo problem. Read
  only the named evidence, surface and verify the technical/product/process
  assumptions, and draft one independently testable spec/plan pair. Do not
  create a brief, implement, approve, register work, or change an external
  system.”
- **Decisions:** the participant confirms or corrects `new-spec`'s surfaced
  assumptions, Boundaries, success criteria, and shape/stack; the final
  checkpoint asks only whether the Draft pair is ready to circulate.
- **Proof and narration:** reproduce the baseline, then trace one acceptance
  criterion to the real verification command and one plan task to its owning
  file. Explain that Core permits a feature-sized request to enter directly at
  `new-spec`; no placeholder brief or discovery gates are manufactured.
- **Recovery:** if the baseline cannot be reproduced, the request is not one
  independently testable feature, or the success command is untrusted, record
  the gap and stop.

### Enterprise track — Core structured-handoff path

- **Participants:** an enterprise AI champion or FDE peer facilitates with the
  client domain owner; the recipient is the named platform, risk, security, or
  engineering approver who owns the relevant control.
- **Use this problem:** an existing, unqueued Draft brief describing a governed
  pilot with more than one potential feature, grounded in supplied policy or
  control text and sanitized repo evidence. The brief names Outcome, Scope,
  Appetite, at least one Rabbit hole, non-goals, and a Spec map placeholder.
- **Opening request:** “Use Core's `receive-brief` on this structured governed-
  pilot handoff. Confirm its load-bearing fields, propose independently
  shippable slices, and wait for the domain owner to select the first slice.
  Mark the brief Ready only if its gate passes, then use `new-spec` for that one
  slice. Do not implement, approve, register work, edit `workspace.toml`, or
  change an external system.”
- **Decisions:** the domain owner resolves missing Outcome/Scope facts, confirms
  the decomposition, fixes the pilot population, excluded systems, accountable
  owner, success/stop measures, rollback expectation, and residual-risk
  recipient, then confirms `new-spec` assumptions for the selected slice.
- **Proof and narration:** trace each control claim to the supplied source,
  show the brief-to-spec backlink and one policy → acceptance criterion → plan
  evidence chain, and explain that enterprise ceremony comes from stronger
  evidence and ownership—not from silently invoking `governance-extras`.
- **Recovery:** a missing policy owner, disputed control interpretation,
  absent Ready-gate field, unsuitable slice boundary, or unavailable approval
  evidence is a safe stop. State that the mid-market enterprise path remains
  uncharacterized.

### Non-technical track — Product Engineering shaping into Core

- **Participants:** a role-proximate peer champion facilitates with an AI-naive
  knowledge worker or UX/experience designer; the recipient is the product,
  design, content, or operations owner who can act on the handoff.
- **Use this problem:** one participant-known, feature-level workflow or
  onboarding friction grounded in an existing guide/process file and two or
  three sanitized observations. The participant can correct interpretation
  from lived or craft expertise.
- **Opening request:** “Use user-scoped Product Engineering to frame this known
  workflow problem at feature level and app scale. Cite the supplied sources,
  pause at G0 for my framing decision, test the one riskiest assumption against
  a predeclared kill condition, and project the surviving intent to one Core
  brief. Then use repo-scoped Core to receive that brief and draft one spec/plan
  pair. Do not decide user meaning or craft quality for me; do not implement,
  approve, register work, or change an external system.”
- **Decisions:** G0 confirms problem, named user, outcome, and participant
  language; the participant accepts the kill condition and survive/kill
  verdict; `decompose-intent` confirms the leaf and projects a Core brief with
  Outcome, Appetite, at least one Rabbit hole, and a one-row Spec map skeleton.
  Core verifies those four Ready-gate fields, confirms the one-slice cut, marks
  the brief `Ready`, and surfaces `new-spec` assumptions. The track does not
  claim to run `discovery-loop`'s G1.5 or G2 in the 30-minute window.
- **Proof and narration:** show intent → brief → spec provenance, invite one
  live correction and show it propagate, and carry any desk-grounded assumption
  as `to-validate` rather than calling it validated. Explain the user-scope to
  repo-scope handoff and preserve strategic and craft authorship as human.
- **Recovery:** a killed assumption, generic or untraceable synthesis, missing
  pack at either scope, or professionally unacceptable output stops the run.
  Faster drafting alone is not a successful outcome.

## Acceptance Criteria

- [x] **AC1.** `guides/core/how-to/run-a-live-demo.md` exists as a
  `kind: how-to` Core guide with `Use this when`, `Prerequisites`, and `Result`
  fields for a facilitator-led repository demonstration.
- [x] **AC2.** The guide contains the five Required demo outline beats and exact
  maximum durations—4, 7, 6, 9, and 4 minutes—whose total is 30 minutes.
- [x] **AC3.** A choose-your-track map names the owning pack, install scope,
  entry skill, canonical skill sequence, expected intermediate artifacts, and
  successful end state for all three tracks exactly as specified above.
- [x] **AC4.** Pre-flight covers repository access and write scope, installed
  pack/scope checks, isolated work state, safe inputs, expected paths, no-
  external-mutation and no-work-registration posture, named approver and
  recipient, participant-verifiable problem, and the AC2 timer.
- [x] **AC5.** Every beat tells the facilitator what to say, what may be read
  and written, what should be observed, which real decision is human-owned,
  what to narrate, and which condition takes the safe-stop branch.
- [x] **AC6.** The technical script uses repo-scoped Core `new-spec` directly,
  creates no brief, and includes the exact problem-sizing, assumption,
  trace-to-command, engineering-recipient, narration, and recovery contract in
  Required demo outline.
- [x] **AC7.** The enterprise script uses repo-scoped Core `receive-brief` on
  an existing structured, unqueued brief and then `new-spec` for one confirmed
  slice; it includes the exact governed-pilot decisions, policy trace, owner,
  proof, recipient, safe stops, and mid-market disclaimer above.
- [x] **AC8.** The non-technical script uses user-scoped Product Engineering
  `frame-intent` → `de-risk-intent` → `decompose-intent`, then repo-scoped Core
  `receive-brief` → `new-spec`; before Core marks the leaf brief `Ready`, the
  script visibly verifies Outcome, Appetite, at least one Rabbit hole, and a
  one-row Spec map skeleton. It includes source correction, validation-hook
  honesty, authorship narration, recipient, and recovery above.
- [x] **AC9.** The guide presents the five shared timeboxes as teaching beats,
  not common workflow states; it neither invents G0/G1.5/G2 for Core nor claims
  the short non-technical run executes the full `discovery-loop`.
- [x] **AC10.** The guide explains why `governance-extras`, `product-strategy`,
  and Experience Design are not baseline workflow owners, while naming the
  narrow condition under which each may provide a different artifact or input.
- [x] **AC11.** Each track ends with exactly one Draft spec/plan pair, preserves
  its appropriate brief/intent provenance, distinguishes ready-to-circulate
  from later formal spec and plan approvals, and stops before `work-loop`
  implementation.
- [x] **AC12.** The guide instructs a role-proximate peer champion to facilitate
  and frames value at the artifact handed to another person, not the installed
  skill count or generated-file count.
- [x] **AC13.** The completion receipt names selected track, packs/scopes and
  skills used, every changed path and status, provenance links, unresolved or
  unverified items, proof result, reviewer/next action, recipient, elapsed time,
  and `No external systems changed`.
- [x] **AC14.** Recovery stops safely when a prerequisite or pack is absent, no
  verifiable problem is available, a participant declines a control, the
  timebox expires, an assumption is killed, or output cannot be verified; it
  never converts a safe stop into claimed success.
- [x] **AC15.** The guide names the mid-market enterprise segment as unresolved
  and makes no reliability claim for the enterprise or self-service path.
- [x] **AC16.** The guide links to existing Core and Product Engineering
  journey/how-to guidance for the invoked skills, workspace orientation, and
  the normal implementation loop instead of duplicating full procedures.
- [x] **AC17.** `guides/core/README.md` registers the guide; generated navigation
  includes it without hand-editing sidebar configuration; and
  `tools/validate_guides.py`, `tools/check-guide-index.py`,
  `tools/test_documentation_entry_links.py`, `tools/test_live_demo_guide.py`,
  and relevant site construction checks pass independently of
  `rendered-site-link-debt` output.
- [x] **AC18.** Three recorded cold walkthroughs each complete the specified
  pack path within 30 minutes, exercise its exact prompt and proof standard,
  preserve its human controls, make no work-intake write, and end with the
  completion receipt; `docs/specs/README.md` reports this spec's true status.

## Assumptions

- Technical: Core is repo-only and explicitly supports `new-spec` as the direct
  route for a single feature without a brief (source: `packs/core/pack.toml`,
  `packs/core/JOURNEY.md`, and Core `new-spec/SKILL.md`).
- Technical: `receive-brief` is Core's route for a structured external,
  multi-feature handoff, while `author-brief` is inappropriate here because it
  queues unstructured intake in `workspace.toml` (source: Core
  `receive-brief/SKILL.md` and `author-brief/SKILL.md`).
- Technical: Product Engineering defaults to user scope, writes product
  artifacts per repository, and projects an app-scale feature leaf into a Core
  brief before `receive-brief` → `new-spec` (source:
  `packs/product-engineering/pack.toml`, `packs/product-engineering/JOURNEY.md`,
  and `decompose-intent/SKILL.md`).
- Product: “three representative team types” means technical, enterprise, and
  non-technical tracks mapped to the researched segments, not three company-
  size personas or three separate guides (source:
  `docs/product/research/adopter-persona-brief.md`; user confirmation
  2026-08-13).
- Product: each demo uses a participant-verifiable first task, exposes real
  human control points, is peer-champion-led, and ends at a shareable artifact
  (source: `docs/product/research/adopter-persona-brief.md` requirements 6–9;
  user confirmation 2026-08-13).
- Product: the guide names rather than resolves the uncharacterized mid-market
  segment (source: `docs/product/research/adopter-persona-brief.md`; user
  confirmation 2026-08-13).
- Process: RFC-0064 fixes the pre-flight, at-least-three-track, own-repository,
  shaping-to-brief-to-spec narration, and no-more-than-30-minute boundaries; it
  does not require identical artifact production in every track (source:
  RFC-0064 P5 Adopt; user confirmation 2026-08-13).
- Process: the slice has no dependency on `rendered-site-link-debt` and leaves
  `ini-008` and work-intake files untouched (source: user confirmation
  2026-08-13).

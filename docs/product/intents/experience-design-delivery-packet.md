# A practitioner can account for every deliverable the experience-design pack owes

- **Status:** Draft
- **Level:** capability
- **Owner:** eugenelim

## Outcome

A designer who has run a real agency engagement is handed the
`experience-design` pack's declared thread and can account for **every**
deliverable they would expect. Each one is either owned by a skill, satisfied by
an artifact the repository already carries, or named in the pack's own
documentation as out of scope. None is *missing and unexplained*.

They must be able to do this from the **guides**, not by reading SKILL.md
files. A deliverable that a skill technically produces but no guide teaches is
not accounted for.

**Acceptance test.** Give that practitioner the pack's stage list and the
deliverable inventory produced by step 1 below. They mark each line
`owned` / `referenced` / `declared out of scope`, and separately whether a guide
teaches it. The outcome holds when no line is marked `missing, unexplained` and
no `owned` line lacks guide coverage.

## Scope

**In scope: the agency baseline** — the deliverable set a design consultancy
produces for a fixed-scope engagement, from framing through handover.

**Out of scope: the enterprise operating additions.** An in-house UX function
also expects accessibility conformance reporting (ACR / VPAT), a research
repository with participant consent and PII handling, design-ops intake and
triage, a versioned design system with a contribution model, localisation, and
post-launch instrumentation. Those are excluded here **not** because they are
unimportant but because whether they belong in this pack, in a sibling pack, or
nowhere is a **positioning question above this intent's altitude**. It is named
below as an open question, and this intent must not silently decide it.

## Opportunity

The pack ships **20 skills** behind a **five-stage** declared thread with
**three human gates** (verified against `packs/experience-design/JOURNEY.md`
and its skill directory). Its declared stages are: map the customer journey,
derive the screen flow, establish design intent, design each screen, review
independently.

Read against how a design consultancy structures an engagement, that thread is
strong through the **middle** — journey, flow, direction, screen, review — and
thin at both ends. Thin **before**: the framing and evidence that decide what to
design. Thin **after**: the specification, rationale, and measurement that let
someone else build it and know whether it worked.

The consistency of that shape is what makes this a capability question rather
than a backlog of missing features.

Two specific observations, stated at the strength the repository actually
supports:

**The pack asks for a provenance it does not route.** `journey-mapping`
requires declaring `evidence-level: observational | survey-backed |
assumption-based`. The catalogue *can* support observational work —
`plan-validation` in `product-engineering` scaffolds interview guides and
usability-test plans and synthesises transcripts a human brings back, explicitly
leaving session-running to a person. But nothing connects an experience-design
journey's evidence level to it: the skill sits in another pack and is framed
around a converged product's assumptions. The gap is a **seam**, not an absence.
The observable consequence is real — this repository's own site principles
concede their source journeys are "planned rather than observation-backed."

**The declared thread is consultancy-shaped and ends at review.** It has no
concept of what happens after handover. That is a coherent choice for a
fixed-scope engagement and a hole for a standing team.

**The guides are currently the pack's thinnest surface, and this is measured.**
`tools/audit-guide-affordances.py` scores `guides/experience-design/` — five
files teaching twenty skills — at **0 of 5 showing a literal chat input**, 0 of 5
showing a sample output, 1 of 5 demonstrating what the user supplies, 1 of 5
stating an outcome, and 2 of 5 stating a job to be done. The skill surface was
brought to 20 of 20 documented invocation phrases; the guides were not touched.
So even the deliverables the pack *does* own are largely untaught, and a
practitioner cannot currently account for the packet from the guides at all.

## First move: research, not construction

**This intent authorises investigation, not skills.** The gap reading above came
from one session testing the thread against one brief. That is enough to justify
looking properly and nowhere near enough to authorise new pack surface.

1. Establish the deliverable inventory **from cited evidence**, not recollection
   — the agency baseline first, and separately what an enterprise function adds.
   The difference between the two lists is the finding. The `desk-research` pack
   accelerates this but is not required; a manually cited survey satisfies it, so
   this intent stays viable with only `core` installed.
2. Test the assumptions below in the order given, and stop if the first fails.
3. Classify each unowned deliverable as: warrants a skill, warrants a reference
   or template a human fills, or is declared out of scope.
4. **Author the guides** for whatever survives classification — including the
   deliverables the pack already owns but does not teach. This is part of the
   outcome, not a follow-on: the accounting in the acceptance test is done from
   the guides. New guides meet the repository's current standard — a literal
   chat input, a demonstrated input, a sample output, a stated outcome, and a
   stated job to be done — and the existing five are brought up with them.

Everything past step 4 — sequencing, surface budget, the upgrade proposal —
belongs in a research plan and then a delivery brief, not in this intent.

## Assumptions

Ordered so that the first failure is the cheapest. Each carries a kill
condition.

1. **A stable agency deliverable set exists.** *Kill:* the survey finds no
   recognisable common set — deliverables vary so much by firm and engagement
   that "every deliverable they would expect" has no referent. Then the outcome
   is meaningless as written and this intent is withdrawn.
2. **Practitioners want completeness over a bounded pack.** *Kill:* they prefer
   a small pack that does the middle well and leaves the ends to human judgement.
   Then the upgrade is documentation that names the boundary, not new skills.
3. **One pack is the right boundary for the agency baseline.** *Kill:* the
   baseline itself splits along a seam that argues for a sibling pack. Then this
   becomes a pack-topology decision and returns to the positioning question.
4. **The thin ends are omissions, not deliberate exclusions.** *Kill:* the pack's
   design record shows they were scoped out on purpose. Then the remedy is to
   state the boundary in the pack's documentation.

## Open question this intent must not decide

Whether `experience-design` serves design consultancies, in-house enterprise UX
functions, or both through separable extensions. It determines audience,
positioning, and pack topology, and it sits above this altitude. Route it to a
product-strategy decision before any enterprise deliverable is added here.

## Risks

- **Surface inflation.** Twenty skills is already a large discrimination
  surface; every addition is something each neighbouring description must
  distinguish itself from. The repository's standing rule is to cut before
  adding, so each proposed skill must argue why it is not a reference.
- **A research skill that manufactures provenance is worse than the seam it
  closes.** No agent recruits a participant or runs a session. Anything that
  looks like it supplies observational evidence without a human in the loop
  would let a team label an assumption as an observation — the exact failure
  `evidence-level` exists to prevent. `plan-validation`'s split — scaffold and
  synthesise, never run — is the boundary to preserve.
- **Compliance artifacts imply assurance.** An accessibility conformance report
  is a legal instrument in some jurisdictions. A skill that drafts one could
  read as attesting conformance it cannot verify. This is a further reason the
  enterprise additions stay out of scope until positioning is settled.

## Grounding

Verified against the repository: the skill count, stage count, and gate count;
the `evidence-level` requirement in `journey-mapping`; `plan-validation`'s
scaffold-and-synthesise charter; the "planned rather than observation-backed"
concession in `docs/design/principles/tech-site.md`; and the guide affordance
scores, reproducible with `python3 tools/audit-guide-affordances.py`.

**Not yet durably recorded, and therefore hypotheses rather than findings:** the
agency and enterprise deliverable inventories, the count and identity of
unowned deliverables, and the claim that neighbouring skill descriptions compete
for the same request. Step 1 exists to convert these into cited evidence or to
discard them. The brief that prompted this — a public-site redesign whose
centrepiece was to be a hand-built explanatory graphic — was owner direction in
session, not a repository artifact.

## Source

- Mode: repo-origin
- Locator: packs/experience-design/JOURNEY.md
- Revision: sha256-bytes-v1:11d854051dc997144fa857a627119debf94967e4376efcc61b15a1acac2579af

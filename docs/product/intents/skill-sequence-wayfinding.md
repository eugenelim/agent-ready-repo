# A practitioner always knows what to run next, and where they are in the sequence

- **Status:** Draft
- **Level:** capability

## Outcome

A practitioner part-way through a multi-skill piece of work knows, without
opening a maintainer document, what to run next and where the current step sits
in the sequence. The answer comes from the surface they are already on, and it
agrees with the sequence its owning pack declares.

**Falsifier — a closed set, not one example.** For each pack with a declared
sequence, enumerate every non-terminal edge and every terminal node. The outcome
is achieved when, for each one, a practitioner using **only the intended skill
or guide surface** can state three things: their current position, the correct
next step *or* that they have reached a terminal one, and the dependency reason
for that edge — and each answer matches the pack's declared sequence. Any edge
where the surface is silent, or disagrees with the declared sequence, fails it.
A practitioner who has to open a `DESIGN.md` to answer has also failed it.

## Opportunity

The catalogue declares sequences, and surfaces them inconsistently and by hand.

**Measured 2026-09-11 over the canonical corpus** — the 137 skills under
`packs/*/.apm/skills/*/SKILL.md`. (The literal tree holds 505 `SKILL.md` files;
the rest are projections and test fixtures, and are not the corpus.)

**24 of 137 skills already name a completion-time successor**, across ten packs:
`atlassian` 6, `product-engineering` 4, `experience-design` 3, `core` 3,
`governance-extras` 2, `desk-research` 2, and one each in `release-engineering`,
`linear`, `figma`, `converters`. `experience-status` carries an explicit "What
to run next"; the `desk-research-project-*` chain hands forward by name.

So the affordance is **wanted and already being written** — and that is the
problem. Every one of those 24 is hand-authored prose, written against no shared
source, with nothing checking it still matches the sequence its pack declares. A
successor can drift from its own pack's stated order and nothing fails. The
other 113 are silent, and silence is currently indistinguishable from "this step
is terminal".

**A derivable source already exists, and is better than expected.** All **14**
packs that ship a `JOURNEY.md` carry numbered, ordered stages — **62 stages**
in total, three to seven per pack — with the pack's skills listed and a
`contract:` block declaring `youProvide` and `youReceive`. Eighteen stages carry
a literal chat input and 27 carry a fenced sample-output block. `JOURNEY.md` is
therefore a broader source than `DESIGN.md`, which only eight packs ship and in
which only `experience-design` declares an internal craft sequence.

**The triggering evidence is first-hand and self-referential.** While building
the four-discipline sequence itself — slice S6 of
[`sdlc-guide-uplift-and-learning-paths`](../briefs/sdlc-guide-uplift-and-learning-paths.md)
— this repository's owner could not tell which experience-design skills to run,
in what order, to do that work. The pack whose subject is sequencing could not
sequence its own use. The craft sequence was skipped entirely and the result
shipped with no information architecture and no design review, which is exactly
the failure `packs/experience-design/DESIGN.md` predicts: "Skipping a step
doesn't save time — it pushes the missing input forward as an implicit
assumption, where it gets designed around rather than decided."

## What the decision requires

- A skill with a declared successor names it where the practitioner finishes,
  distinguishable from the routing-away prose already in `description`.
- A skill with **no** declared successor says it is terminal, rather than being
  silent — silence currently means both "terminal" and "unrecorded".
- The successor is **derived from, or checked against, the owning pack's
  declared sequence**. The 24 existing hand-written instances are the evidence
  that an unchecked copy drifts.
- Sequences that span packs are expressible. `desk-research` → `product-strategy`
  and the experience-design craft thread both cross pack lines, and a
  per-pack-only model cannot represent the walk this came from.

## Boundary

**In:** the shared sequence source and the skill-side forward affordance across
the packs that declare a sequence.

**Out — experience-design guide uplift.**
[`experience-design-delivery-packet`](experience-design-delivery-packet.md)
owns authoring that pack's guides "including the deliverables the pack already
owns but does not teach", and records that as "part of the outcome, not a
follow-on". `sdlc-guide-uplift` explicitly disclaims it. An earlier draft of
this intent attributed it to the wrong owner; corrected 2026-09-11 on review.

**Out — the four-discipline path's own next-links.** S7 of
`sdlc-guide-uplift-and-learning-paths` owns "every step states a literal
request, its result, and its next link" for that walk. This capability supplies
the source S7 can consume; it does not take S7's outcome. If S7 ships first it
states its next steps locally, and a later slice here replaces them with the
derived form.

**Out — the work-loop's own next action.**
[`work-loop-next-action`](../briefs/work-loop-next-action.md) (Draft) derives one
authoritative next action from persisted work-loop state and is explicitly
reporting-only. That is one skill's internal state machine.

**Out — consumer-side input readiness.**
[`stage-input-readiness`](../briefs/stage-input-readiness.md) (Draft) asks
whether the next stage *can* work from its input. Complementary: it validates a
handoff, it does not say which handoff is next.

**Out — workspace queue next actions.** `workspace-status-next-actions` is
Shipped and answers what to work on next from the queue, not what to run next
within a piece of work.

## Decomposition

**Sliced per pack, because the declared sequences are per pack.** Each slice
takes one pack's declared sequence, projects the forward affordance across that
pack's skills, and marks its terminal nodes.

1. **`experience-design` first.** It is the hardest to drive and has the most
   complete source: it is the only pack declaring an internal craft sequence,
   **all 20 of its skills are named in its own `DESIGN.md`**, and its
   `JOURNEY.md` carries five ordered stages, five literal inputs and five sample
   blocks. It is also the pack whose absence the owner personally hit.
2. Then the remaining packs that ship a `JOURNEY.md`, ordered by whether they
   already carry hand-written successors to reconcile.
3. The cross-pack edges last, because they need more than one pack's source
   settled first.

The shared sequence source is decided in slice 1 and reused, not re-decided per
slice. If slice 1 shows the source cannot generalise, that is a kill signal for
the projection approach and the capability reduces to authoring.

## Assumptions

- A declared sequence exists in enough packs to derive from. **Verified**: 14
  packs ship `JOURNEY.md` with 62 ordered stages between them. This was recorded
  as unverified in an earlier draft on the strength of `DESIGN.md` alone, which
  only eight packs ship.
- A successor can be expressed without a new runtime. This must stay habits and
  content; `experience-design`'s DESIGN.md records the pack as "habits, not
  infrastructure", and a sequencing daemon reverses that.

## Risks

- **Drift is the whole risk**, and it is already realised in the 24 hand-written
  successors. Whatever ships needs a check that a named successor still matches
  the declared one.
- A forward pointer in a skill body may be read by an agent as licence to invoke
  the next skill automatically. The affordance is for a human deciding; it must
  not become autonomous chaining.
- Reconciling the 24 existing instances may contradict their authors' intent
  where the hand-written successor is better than the declared one. Treat a
  mismatch as a question for the pack owner, not as an automatic overwrite.

## Unresolved questions

1. **Where does the successor live?** `contracts/skill.schema.json` sets
   `additionalProperties: false` on top-level keys, **but carries a `metadata`
   extension table** — "any additional frontmatter keys must be nested here" —
   so this is a seam rather than a closed door. The alternative is deriving it
   from `JOURNEY.md`'s ordered stages, which keeps one source but requires that
   document to be machine-readable. Not chosen here; slice 1 decides it.
2. **Is the successor a property of the skill, or of the path?** Revised
   2026-09-11: an earlier draft claimed `information-architecture` proves the
   point because six genre-direct skills replace it. That reasoning was wrong —
   `packs/experience-design/DESIGN.md` says they "are a replacement for
   `information-architecture` only. The full craft sequence runs; only the IA
   step changes", so all of them proceed to `interaction-design`. That is
   **branching into a slot, not divergent successors out of one skill.** The
   open question is therefore narrower: does any skill have *different*
   successors in two declared paths? If none does, a single successor per skill
   suffices and the path-membership model is unnecessary complexity.

## Owner

eugenelim.

## Projection

**Tracker:** none. The repository holds the truth for this work.

**Artifact:** a capability projecting one feature intent per pack slice, per
§ Decomposition. The first is `experience-design`. The capability itself ships
nothing; each slice is independently shippable, which is why this is not a
feature.

## Source

- Mode: chat-only
- Locator: chat/team-sop
- Revision: 2026-09-11
- Authority: transferred-to-repository

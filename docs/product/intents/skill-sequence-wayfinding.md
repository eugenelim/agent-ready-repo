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

**The canonical corpus is the 137 skills under
`packs/*/.apm/skills/*/SKILL.md`.** The literal tree holds 510 `SKILL.md`
files; the rest are projections and test fixtures, and are not the corpus.

**How many already name a successor is not yet a knowable number, and that is
the first finding.** Three predicates applied over the same corpus on 2026-09-11
returned **1**, **24**, and **17**. The first matched only a literal `Next:`
heading. The second added `run \`x\``, `move to`, `Then run`. The third added
`Hand off`, which alone surfaces six `experience-design` skills — `content-design`,
`copy-direction`, `creative-direction`, `journey-mapping`, `user-flow` and
`tone-of-voice` — that the earlier two missed entirely.

The spread is the evidence. **"Names a completion-time successor" has no
reproducible inclusion rule**, because the affordance is unstructured prose in
whatever shape each author chose: a `**Hand off.**` section, a "What to run
next" heading, an inline "Point the user to `user-flow`", or a sentence inside a
paragraph. A count cannot be trusted until the predicate is defined, and no
check can enforce agreement with a declared sequence while the thing being
checked cannot be located.

Two facts survive any predicate. Some skills already carry the affordance and
wrote it by hand against no shared source, so **nothing verifies it still
matches the sequence its pack declares** — `experience-status` says "What to run
next", `creative-direction` hands to `design-system`, `tone-of-voice` names both
`ux-writing` and `copy-direction`. And most carry nothing, where silence means
both "this step is terminal" and "nobody recorded one".

**A candidate source exists, and it is not yet an edge model.** All **14** packs
shipping a `JOURNEY.md` carry numbered, ordered stages — **62** in total, three
to seven per pack — with the pack's skills listed and a `contract:` block
declaring `youProvide` and `youReceive`. Eighteen stages carry a literal chat
input and 27 carry a fenced sample-output block. That is broader than
`DESIGN.md`, which only eight packs ship and in which only `experience-design`
declares an internal craft sequence.

**But it does not encode edges, and an earlier draft of this intent overclaimed
that it did.** The skills block is a flat pack-level inventory and the stages are
prose; nothing maps each skill to a stage. `experience-design`'s journey lists 20
skills against five stages, and one stage reads "`information-architecture` (or a
genre-direct skill) … then `interaction-design`" — a branch in prose, not a
relation. Cross-pack edges are absent too: that journey's `relatedJourneys` names
only `architect` and `core`, while `copy-direction` hands off to `ux-writing` in
`product-engineering`. And `youProvide`/`youReceive` are **pack-level** contracts,
not per-edge dependency reasons.

So `JOURNEY.md` supplies stage order and handoff vocabulary. **Building the edge
model is slice 1's first task, not an inherited asset**, and the closed-set
falsifier is finite but not enumerable until that model exists.

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
- **The dependency reason for an edge is visible on the same surface**, not only
  the successor's name. The falsifier asks a practitioner to state *why* this
  step follows that one; without this requirement a delivery could satisfy every
  other item and still fail the outcome.
- An inclusion rule for "names a completion-time successor" is defined before
  any count is claimed or any check is built.
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
3. **A final cross-pack edge slice**, which is its own feature intent and not
   part of any pack slice — no single pack owns an edge that leaves it. It runs
   last because it needs at least two packs' sources settled, and it owns the
   `desk-research` → `product-strategy` and `experience-design` →
   `product-engineering` edges that the per-pack slices structurally cannot.

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

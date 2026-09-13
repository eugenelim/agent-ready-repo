# A practitioner always knows what to run next, where they are in the sequence, and what the step leaves them holding

- **Status:** Draft
- **Level:** capability

## Outcome

A practitioner part-way through a multi-skill piece of work knows, without
opening a maintainer document, what to run next, where the current step sits in
the sequence, and **what the step is going to leave them holding**. The answers
come from the surface they are already on, and they agree with what the owning
pack declares.

**Two halves, one capability. Added 2026-09-11 on owner direction.** Sequence
wayfinding answers *where am I and what is next*. **Deliverable orientation**
answers *what am I producing, where does it land, and how do I know a good one*.
They are one capability because they share a source and a drift risk: both are
derived from what the pack declares, and both are currently hand-written prose
in whatever shape each author chose. Splitting them would mean building the
same derivation and the same drift check twice.

The second half is not a refinement of the first. These skills **write files**,
so a practitioner who knows the next skill's name and nothing about the artifact
still cannot tell whether the step they just ran succeeded, and cannot review
what the next step will consume.

**Falsifier — a closed set, not one example.** For each pack with a declared
sequence, enumerate every non-terminal edge and every terminal node. The outcome
is achieved when, for each one, a practitioner using **only the intended skill
or guide surface** can state five things: their current position; the correct
next step *or* that they have reached a terminal one; the dependency reason for
that edge; **the deliverable that step produces and the path it lands at**; and
**what that deliverable must contain for the next step to be able to use it** —
and each answer matches what the pack declares. Any edge where the surface is
silent, or disagrees with the declared sequence, fails it. A practitioner who
has to open a `DESIGN.md`, or open the skill's own template asset, to answer has
also failed it.

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

### The deliverable half is worse served than the sequence half

Measured 2026-09-11 over the **74 published skills and 25 journey stages of the
five packs a team needs to go from an idea to a merged change** —
`desk-research`, `product-strategy`, `experience-design`, `product-engineering`,
`core`. That is a subset of this intent's 137-skill corpus, and the numbers
below do not generalise to the other nine `JOURNEY.md` packs without being
re-run.

Predicates stated, because this intent already learned that an unstated
predicate produces three different answers to one question:

- *names a path* — the text contains a backticked token containing `docs/`,
  `packs/`, `guides/`, `web/`, `.claude/` or `.agents/`, or ending in `.md`,
  `.toml`, `.json`, `.yaml` or `.yml`.
- *states a shape* — a heading matching template, structure, sections, artifact
  shape, or output format/shape/structure; or a fenced block containing
  Markdown headings.
- *ships a template asset* — a non-empty `assets/` directory beside `SKILL.md`.

| Where a practitioner would look | Result |
| --- | --- |
| Journey stages with an `Output` line | 25 of 25 |
| Journey stages whose `Output` names a **path** | **6 of 25** |
| Skills naming a path in their own `SKILL.md` | 63 of 74 |
| Skills shipping a template asset | 18 of 74 |
| Skills stating the deliverable's shape in prose | 23 of 74 |
| Skills with **neither** a template asset nor a stated shape | **38 of 74** |

Two asymmetries follow, and they set the shape of any delivery here.

**Location is derivable; form mostly is not.** 63 of 74 skills already name a
path, so a step's artifact location can be projected from the skill rather than
authored. Form cannot: for 38 of 74 skills there is nothing to project from, and
`product-strategy` is 9 of 9 — every skill in that pack is silent on what its
deliverable should look like.

**The journey is the wrong place to look and the place a practitioner looks.**
Every stage states an `Output`; almost none says where it lands. So the
affordance that exists sits in `SKILL.md`, and the surface a practitioner
reaches for does not carry it.

**The silent skills are the same skills.** In `experience-design`, the eleven
with neither a template nor a stated shape overlap almost exactly with the ten
its journey never names — `analytical-design`, `conversion-design`,
`documentation-design`, `informational-design`, `marketplace-design`,
`design-review` and `workspace-design` appear in both sets. A skill invisible in
its pack's sequence is also silent about its output, which is the compound
reason that pack could not teach its own use.

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
- **A step names the deliverable it produces and the path it lands at**, on the
  surface the practitioner is already on. 63 of 74 skills already carry the
  path, so this is reconciliation and projection, not authoring.
- **A step says what the deliverable must contain**, in enough detail that a
  practitioner can reject a bad one. This is the expensive half: 38 of 74 skills
  have nothing to derive it from, so a delivery must decide whether to author
  the missing forms or to narrow the outcome to the skills that already declare
  one. That decision is not made here.
- **A declared form is checked against what the skill actually writes.** A
  template asset that has drifted from the skill's output is worse than none,
  because a practitioner reviewing against it rejects correct work.
- **An inclusion rule for "declares its deliverable's form" is defined before
  any count is claimed**, on the same grounds as the successor predicate above.
  The three predicates in the table are this intent's current best and are
  stated so a later delivery can disagree with them explicitly.

## Boundary

**In:** the shared sequence source and the skill-side forward affordance across
the packs that declare a sequence.

**Out — experience-design guide uplift.** Owned by
[`experience-design-delivery-packet`](experience-design-delivery-packet.md)
until 2026-09-11, when that pack's guide authoring moved to
`pack-guidebook-walkability`; the packet keeps the deliverable-accounting
question of whether every expected deliverable is owned, satisfied or explicitly
out of scope. Either way it is not this capability's, and an earlier draft of
this intent attributed it to the wrong owner. Ledger:
`docs/specs/pack-guidebook-walkability/notes/ownership-consolidation.md`.

**Out — the static guidebook for the five SOP packs.**
[`pack-guidebook-walkability`](../../specs/pack-guidebook-walkability/spec.md)
(S7 of `sdlc-guide-uplift-and-learning-paths`, Draft) fixes an eleven-obligation
guidebook step contract and satisfies it **by hand** for `desk-research`,
`product-strategy`, `experience-design`, `product-engineering` and `core`. Four
of its obligations are this capability's outcome stated as authored prose:
position in the sequence, what to run next, the deliverable's location, and the
deliverable's expected form.

This capability is the **derived** form of those four. It supplies the source
that slice consumes where one exists, and replaces its hand-written instances
later. The relationship is deliberate and recorded on both sides: that slice
proves what the obligations are worth on real content for five packs, and this
capability decides whether they can be generated rather than written. If that
slice finds an obligation satisfiable mechanically but useless to a reader, this
capability should not derive it.

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
pack's skills, marks its terminal nodes, and projects each step's deliverable
location — reconciling against the 63 skills that already name a path.

**Deliverable form is sliced separately from deliverable location**, because
they have different costs and different failure modes. Location is projection
and reconciliation; form is authoring for 38 of 74 skills, and authoring a
deliverable's expected shape is a pack-design decision rather than a wayfinding
one. A slice that bundled them would be a projection slice with an
open-ended authoring tail attached.

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

**Deliverable form has its own kill signal.** If slice 1 finds that the skills
which already declare a form declare it in shapes too varied to reconcile, the
form half narrows to "name the deliverable's type" and the full shape stays with
each pack's own documentation. The location half survives that outcome
independently, because it rests on a single well-formed field in 63 skills.

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
- **A declared deliverable form is a new drift surface, and a worse one than a
  successor.** A stale successor sends a practitioner to the wrong next step,
  which they notice. A stale form makes them reject correct output, which they
  do not. Whatever ships needs the form checked against what the skill writes,
  and the 18 existing template assets are the first place to look for drift that
  is already realised.
- **A stated form may be read as a schema.** These deliverables are prose
  documents whose shape is guidance, not validation. A form expressed too
  strictly invites a check that fails good work for missing a heading, which is
  the opposite of the outcome.

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
3. **Where does the deliverable descriptor live, and is it one field or two?**
   The same `metadata` extension seam in `contracts/skill.schema.json` is the
   candidate home for a path. The form is the harder question: a path is a
   string, while a form is a structure, and the 18 skills that ship a template
   asset already express it as a file rather than as metadata. Whether the
   descriptor points at that asset, duplicates its headings, or replaces it is
   not decided here.
4. **Is a deliverable's form a property of the skill or of the path it is on?**
   A `journey-mapping` output consumed by `user-flow` may need sections that a
   standalone run does not. If no deliverable's required form varies by path,
   one descriptor per skill suffices — the same shape of question as item 2, and
   it should be answered with the same evidence.

## Owner

eugenelim.

## Projection

**Tracker:** none. The repository holds the truth for this work.

**Artifact:** a capability projecting one feature intent per pack slice, per
§ Decomposition, plus a separate slice for deliverable form. The first is
`experience-design`. The capability itself ships nothing; each slice is
independently shippable, which is why this is not a feature.

## Source

- Mode: chat-only
- Locator: chat/team-sop
- Revision: 2026-09-11
- Amended: 2026-09-11 — deliverable orientation added as the capability's second
  half on owner direction, with its own measured baseline, its own kill signal,
  and its own slice. The boundary with `pack-guidebook-walkability` is restated
  in both documents.
- Authority: transferred-to-repository

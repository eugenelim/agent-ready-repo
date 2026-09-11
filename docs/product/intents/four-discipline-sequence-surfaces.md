# The four disciplines read as one sequence, on both published surfaces

- **Status:** Draft
- **Level:** feature

## Outcome

A first-time Claude Desktop user who has installed nothing can see, from the
published surfaces alone, that **product strategy → desk research → experience
design → product engineering** is one ordered sequence, and can walk it. Each
step names what it hands the next, so a reader can stop after any one of them
and still hold something usable.

**Falsifier.** The outcome is achieved when a reader who has seen only these
surfaces can name the four disciplines in order and say what one hands the
next. It is *not* achieved by any particular grouping, ordering widget, or
card treatment — those are mechanism, and the sketch below is explicitly not
the answer.

## Opportunity

Nothing on either surface presents the four as a workflow. Both halves are
measured, not asserted.

**The site half.** `web/src/pages/journeys/index.astro` renders every journey
into one flat `<ul class="journeys-grid">`. Its only ordering is a four-item
leading list — `core`, `product-engineering`, `release-engineering`,
`architect` — followed by everything else alphabetically by slug. Against the
20 journey files in `web/src/content/journeys/`, the four disciplines land at
positions **2, 9, 10 and 19 of 20**: product-engineering second, desk-research
ninth, experience-design tenth, product-strategy nineteenth. A reader is given
no signal that those four relate to each other at all, and the one ordering the
page does express groups product-engineering with the supervised loops rather
than with its own disciplines.

**The guides half.** `guides/README.md` publishes six ordered paths, P1–P6,
each with a prerequisite, a first-value moment and an "ends at". They are keyed
to **lifecycle stage, not discipline**: P2 "Shape what to build" covers
`desk-research`, `product-engineering` and `architect`, and **neither
`product-strategy` nor `experience-design` appears in any path at all**. Both
exist on the page only as rows in two unordered chooser tables — "Choose what
you want to achieve" and "Choose by role" — which name them as starting points
without ever ordering them against each other.

So the ordered-path mechanism already exists and is already trusted; what is
missing is a path for this sequence.

## The route constraint

Measured from `packs/*/.apm/agents/`: `product-engineering` ships 3 agents,
`desk-research` 2, `experience-design` 1, `product-strategy` 0.

Claude plugins (Anthropic's) carry agents, so all four install on that route
and the sequence is walkable. Agent Plugins (agent-plugins.org 1.0.0) define no
agent component type, so **three of the four are refused** and the sequence
cannot be walked on that route at all — only `product-strategy` survives.

This outcome is therefore a **Claude-plugins-route outcome**. The two routes are
not interchangeable here and must not be described as if they were. This is
also the concrete reason the outcome is separate from the profile work below:
a `profiles/*.toml` never reaches either plugin route.

## Boundary

**In:** the journeys index's grouping, ordering and group copy; a guides-side
ordered path covering the four disciplines, stated in the existing P-path shape
with prerequisites and a first-value moment; and whatever the four journeys must
each say about what they hand the next for the sequence to read as one.

**Out — the journey content itself.** `web/src/content/journeys/*.md` carry
`generated: true` and are projected by `tools/build-site.py --journeys-only`
from `packs/*/JOURNEY.md`. Editing a tagline or adding a handoff sentence there
is a **released pack change**, pulling in version bumps and changelog entries
for four packs. The sequence's connective copy therefore lives in the
hand-authored index page and the guides path, not in journey content. If a
handoff genuinely cannot be stated without changing a pack's `JOURNEY.md`, that
is a separate change with its own release surface, not a quiet addition here.

**Out — the profile.** `profiles/digital-product.toml`, the persona journey
page and the first-session profile workflow belong to
[`digital-product-maker-profile`](digital-product-maker-profile.md), which names
the same four disciplines as "the complete four-discipline toolkit". That intent
stays the owner and stays blocked on `ini-003`. It is not this outcome's
mechanism: it records itself that "a `profiles/*.toml` is read only by the
`agentbundle` CLI and never reaches the plugin route", and this reader has no
terminal.

**Out — the integrative tutorial.** The cross-pack end-to-end digital-product
tutorial and the per-pack intent indexes belong to
[`digital-product-guides-update`](digital-product-guides-update.md) under
RFC-0071 M6, behind M5 `cross-pack-experience-eval`. Two reasons it cannot
absorb this: its chain is strategy → PE → XD → **frontend-engineering** and
does not contain `desk-research` at all, and its own assumption is that the
cross-pack evaluation "will establish the validated journey that the guides
explain" — an input that does not exist. Presenting an existing order is not
publishing a validated integrative tutorial.

**Out — the marketing home and the docs-site guides index.** Owned by
[`cohort-orientation-surfaces`](cohort-orientation-surfaces.md), whose Boundary
also places journey pages explicitly out of its own scope. No overlap in either
direction.

**Out — affordance uplift inside the four packs' guides.** Chat inputs, worked
examples and sample outputs are S3–S5 of
[`sdlc-guide-uplift-and-learning-paths`](sdlc-guide-uplift-and-learning-paths.md).
This intent adds a path over existing guides; it does not rewrite their bodies.

**Out — any diagram of the sequence.** A guide cannot today carry an image that
renders on both GitHub and the docs site; see
`docs/specs/docs-site-build-contract-hardening/notes/guide-image-projection.md`.
The sequence must read as a sequence in text. If that defect is fixed later, a
diagram is a follow-on, not a silent addition here.

**Out — any first-value or install-success claim.** The dated Claude-apps
install-to-first-value probe required by
[`claude-apps-first-value-entry`](claude-apps-first-value-entry.md) has not been
run, so nothing here may assert that a reader who walks the sequence reaches a
working artifact. Same fence as AC12 of `claude-apps-route-docs`.

## The sketch, and why it is not the answer

A three-group journeys index was built in the session of 2026-09-10 and
rewritten before committing, so no commit contains it; it is reconstructed from
that session's transcript. Its shape: three `<Section>` blocks — an ordered
`<ol>` of the four disciplines, then the supervised loops (`core`,
`release-engineering`, `architect`), then everything else alphabetically — with
membership derived from the `journeys` collection so nothing can silently drop
out. That derivation is the one property worth keeping: a hardcoded list
previously dropped five journeys, including `product-strategy`.

It is a sketch for three reasons beyond never having been reviewed:

1. Its `.journeys-grid` rule drops the `list-style: none` the committed version
   carries, so both the `<ol>` and the `<ul>`s would render list markers.
2. `.journeys-grid--ordered` is applied with no rule defined for it.
3. `.journey-card--step` and `.journey-card__step` are applied with no rules
   defined, so the decorative step number renders unstyled.

It also reported rendering 19 journeys; there are 20 files in the collection,
all carrying a tagline. That discrepancy is unexplained and must be resolved
before any membership claim is made.

## Assumptions

- A guides-side path can be added in the existing P-path shape without moving
  any guide on disk, so generated navigation and published URLs survive. This
  is the same assumption `sdlc-guide-uplift` records, and it held for P1–P6.
- The four journeys already contain enough about their own inputs and outputs
  to state a handoff without authoring new pack content. **Untested** — if
  false, the guides half grows into authoring work and the boundary against
  S3–S5 needs restating rather than quietly crossing.
- Presenting an order that the catalogue already implies is not the same as
  certifying that the order is correct. This intent claims discoverability, not
  validation; the validating instrument is M5's, and it is unstarted.

## Unresolved questions

1. **Closed 2026-09-10 — the owner chose the order.** `product-strategy →
   desk-research → experience-design → product-engineering`: decide what to
   build, find out what is true, design how it should feel, then shape the bet
   and build it. Three sources had implied three orders — this one from the
   sketch and from `digital-product-maker-profile`'s deps-first composition;
   `guides/README.md`'s P2 gathers evidence *before* shaping and carries no XD
   at all; RFC-0071's accepted chain is strategy → PE → XD → FE, placing
   product-engineering second. The decision is the owner's, taken because
   publishing any order settles it in practice.

   **The conflict with P2 is not resolved by this decision and must not be
   glossed.** A reader who walks both surfaces meets research before shaping in
   P2 and shaping last in the new path. The spec must either reconcile the two
   or state the difference where both are reachable; it may not publish them as
   if they agreed.
2. **Do the two lifecycles stay orthogonal?**
   `docs/design/discovery/team-orientation-decision-log.md:52` flags that
   orthogonality as "our assertion", not a finding. A four-discipline sequence
   presented alongside the five-station adoption spine is a second ordering on
   the same surfaces; if the two are not orthogonal, this intent adds the
   confusion it is trying to remove.
3. **Is the blocker explanatory or commercial?** The same decision log leaves
   this open, and `cohort-orientation-surfaces` has already been partially
   killed on it — the top-ranked adoption blocker measured 47% organisational,
   with "I cannot re-explain it" documented nowhere. If the blocker is
   commercial here too, a better-sequenced index is a real but small
   improvement, and this intent should be sized accordingly rather than
   defended as an adoption fix.
4. **Which artifact this becomes.** One spec covering both surfaces is the
   obvious shape, because the two halves share one ordering decision and would
   otherwise settle it twice. Recorded as the recommendation, not chosen here.

## Owner

eugenelim.

## Projection

**Tracker:** none. The repository holds the truth for this work.

**Artifact:** one spec covering both surfaces, per unresolved question 4.

## Source

- Mode: chat-only
- Locator: chat/team-sop
- Revision: 2026-09-10
- Authority: transferred-to-repository

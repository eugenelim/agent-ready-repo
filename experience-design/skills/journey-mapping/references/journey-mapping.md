# Journey mapping — method and grounding

How to produce a customer/end-user journey map that the rest of the design
flow can act on. This page points to the recognized standards and explains
the load-bearing mechanics; it reprints no values, tables, or framework text.

## Grounding the map

Every journey map is a hypothesis about a customer's experience. Before
drawing any stage boundary, anchor the map in two things:

- **The persona** — who is the customer, framed as a role with a context
  (not a demographic profile). If no research artifact is present, elicit
  a working persona inline: "who is trying to do this, and what do they
  already know?" The persona sets the emotion baseline — what a pain feels
  like to *this* person in *this* context is the key design input.
- **The outcome** — what done looks like for the customer. The outcome
  defines the journey's end state; working backwards from it defines the
  start trigger and keeps stages from sprawling.

For deeper grounding in customer-centred framing, consult:
- **Nielsen Norman Group — journey mapping**
  ([nngroup.com/articles/journey-mapping-101](https://www.nngroup.com/articles/journey-mapping-101/)) —
  the canonical definition, the five components, and the most common
  mistakes. The evidence base for frontstage / outside-in framing.
- **Jeff Patton — user story mapping**
  ([jpattonassociates.com/user-story-mapping](https://www.jpattonassociates.com/user-story-mapping/)) —
  the activity / task / story hierarchy that tells you when a journey map
  is the right level versus when story-mapping is. Stages map roughly to
  Patton's user activities.
- **Teresa Torres — opportunity-solution tree**
  ([producttalk.org/opportunity-solution-tree](https://www.producttalk.org/opportunity-solution-tree/)) —
  the framework for turning the pains and opportunities in the journey's
  fourth row into a structured set of bets. The journey map is where you
  discover the opportunities; the opportunity-solution tree is where you
  select among them.

## Stage construction

A stage is a coarse phase of the customer's goal — not a screen, not a
feature, and not an internal process step. Good stages pass three tests:

1. **Named from the customer's perspective.** "Discover the product" not
   "landing-page visit." The name should make sense to the customer.
2. **Bounded by a visible state change.** The customer enters a stage when
   something meaningful changes for them; they leave it when the next
   meaningful change occurs. If you cannot name a visible state change at
   the boundary, the stage boundary is in the wrong place.
3. **Coarse enough to survive screen redesigns.** If renaming a button
   would split or merge a stage, the stage is too fine — it is describing
   the current implementation, not the customer's experience.

Three to six stages is the right grain for most products. Fewer than three
implies the outcome is too narrow for a journey map; more than six implies
the map is operating at the screen level, which is `user-flow`'s job.

## The four rows

For each stage, capture four rows. The column order is deliberate — actions
come first because they are observable, emotions come second because they
are the key design input, pains third because they are what the emotions
point to, and opportunities last because they are the reason the map exists.

**Actions** — what the customer physically or digitally does during this
stage, in the customer's words. Frontstage only: actions the customer
takes, not actions a system or support team takes. Keep each action
scannable — a short verb phrase, not a sentence.

**Emotions** — how the customer feels at each stage, marked as a valence
(positive / neutral / negative) and a word or short phrase. The emotional
arc across the stages is the single most useful signal for prioritising
where to invest design effort: the steepest negative dip is usually the
highest-opportunity problem.

**Pains** — the friction, confusion, or gaps the customer encounters. A
pain is a gap between what the customer expects and what actually happens.
Keep pains in the customer's words — "I don't know if my submission went
through" is a better pain than "lack of confirmation state feedback."

**Opportunities** — what would change if the pain were addressed. An
opportunity is solution-independent: "reduce the uncertainty about whether
the action succeeded" is an opportunity; "add a toast notification" is a
solution. Keep opportunities framed as customer outcomes, not features,
so that Torres's opportunity-solution tree can remain open when you
prioritise.

## Platform/surface axis

The surface value changes *what the journey map questions ask* at each
stage — it does not change what the map outputs or print platform values
into the artifact.

**iOS** — at stages where the customer navigates or returns to the product,
ask how the platform's navigation conventions (which Apple HIG documents)
shape what the customer expects. Point to
[Apple Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
for the navigation and gesture conventions relevant to each stage; reprint
no HIG values.

**Android** — at stages where the customer makes choices or moves between
contexts, ask how the platform's component vocabulary and adaptive-layout
guidance (which Material 3 documents) frame those actions. Point to
[Material 3](https://m3.material.io/) for the relevant patterns; reprint
no Material values.

**responsive-web** — at stages where the customer's context may shift
(device, connection, environment), ask how the responsive design contract
changes the experience. Point to
[MDN Responsive Design](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/CSS_layout/Responsive_Design)
for the responsive-design principles relevant to each stage; reprint no
breakpoint values.

**cross-platform** — design the journey once around the shared customer
outcome, then note where the stages' actions or emotions differ per surface.
The shared journey is the spine; per-surface notes are additive. Name the
surfaces where the experience diverges; do not design them separately unless
they represent genuinely distinct customer outcomes.

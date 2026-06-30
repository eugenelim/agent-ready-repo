# Grounding named goals in stable referents

After the interrogation converges on named goals, each goal must be
grounded in at least one **stable referent** before it can steer a
build decision. A referent is stable when it exists outside the
current session and can be pointed to — so a later choice traces back
to it, not to a fresh opinion.

## The four referent types

### 1 — Persona

Who is this for? A goal is grounded when it names the person it serves.

- **From the Domain Framing** — if a persona or user archetype already
  exists (from `frame-domain` or equivalent), load it and connect each
  goal to the persona it expresses. "Quiet confidence" is grounded when
  it names the persona who should feel it: the cautious first-time buyer
  who needs to trust the product before committing.
- **Elicit inline when absent** — if no persona exists, ask three
  questions to sketch one: who is the primary user, what is their
  dominant concern before they start, and what would make them
  immediately distrust the product? That sketch is enough to ground the
  goal; record it in the doc's open questions as a prompt to do the full
  persona work separately.

A goal grounded only in the team's taste is not grounded — it is a
preference. Push it back to the interrogation until a person's need
anchors it.

### 2 — Precedent

What comparable products carry this quality, and what do we take from them?

A precedent is a brief survey — two or three examples — of how other
products or categories express the quality the goal names. Precedent is
not a spec; it is evidence that the quality can be achieved and a
pointer to *how* others achieved it. Keep the survey short and refresh
it only when the grounding loop needs it (the session is the right
scope; outdated precedent is worse than none).

For each precedent named, record:
- **What quality you are after** — the specific attribute from this
  reference, not the product as a whole.
- **What you are leaving** — the attribute from this reference that
  does not belong to your direction. This prevents cargo-culting the
  whole reference and keeps the goal distinct.

If the interrogation produced "make it feel like X," the precedent step
is where X gets unbundled; the named qualities become grounding, not the
reference itself.

### 3 — Standards

What recognized design principles or bodies of guidance align with this goal?

Standards are the named, external bodies of guidance the field recognizes —
interaction-design principles (Nielsen heuristics, Laws of UX), accessibility
guidance (WCAG, APCA), motion guidance, typography research. Point to
the standard that the goal respects or draws from; do not reprint its
values.

A goal aligned with a recognized standard is more defensible than one
that is not — it can be explained without reference to taste. When a
goal has no standard behind it, it is either purely expressive
(record that honestly) or not yet sharp enough (push back to Stage 2
of the interrogation).

### 4 — Platform conventions

What does the target surface's platform guidance say about this quality?

The target surface (`responsive-web`, `iOS`, `Android`, or
`cross-platform`) determines which platform guidance is relevant. For
each goal, name how the platform's guidance shapes or bounds it:

- **iOS** — Apple Human Interface Guidelines (HIG) shape navigation
  patterns, gestures, and visual hierarchy on the platform. Point to
  the HIG guidance that the goal aligns with or must account for.
- **Android** — Material 3 provides the component vocabulary and
  adaptive-layout guidance. Point to the relevant Material 3 guidance.
- **responsive-web** — MDN's responsive-design documentation and, where
  relevant, PWA conventions. Point to the relevant MDN guidance.
- **cross-platform** — design the shared intent once, then name the
  per-surface adaptations the goal requires. Each surface's platform
  guidance applies to its own adaptation; the shared goal must clear
  all of them.

Platform conventions are not a ceiling — they are a floor and a
vocabulary. A goal that contradicts a platform's strong conventions
needs a strong justification; one that works within them is easier to
realize and maintain.

## Recording the grounding

For each named goal in the aesthetic-direction doc, record:

- **Persona** — the person this goal serves (one phrase or a pointer to
  the full persona artifact).
- **Precedent** — one or two examples that carry the quality, and which
  specific attribute you are taking from each.
- **Standards** — the named guidance or principle the goal aligns with
  (pointer, not reprint).
- **Platform conventions** — how the target surface's guidance shapes
  the goal.

A goal that clears all four is grounded. A goal that clears two or
three can proceed with the missing referents recorded as open questions.
A goal that clears none goes back to Stage 2 of the interrogation.

## What grounding does not mean

Grounding does not collapse the goal into a formula or a constraint
list. The goal is still a creative direction — "Quiet confidence" is
still a judgment call about the feel of a product. Grounding means the
judgment has a traceable basis: a person it serves, evidence it can be
achieved, guidance it respects, and a platform it fits. That traceability
is what lets a later build decision point back to the goal instead of
re-arguing taste.

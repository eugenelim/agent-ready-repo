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

Standards are the named, external bodies of guidance the field recognizes.
Point to the standard the goal respects or draws from; do not reprint its
values. A goal aligned with a recognized standard is more defensible — it
can be explained without reference to taste. When a goal has no standard
behind it, it is either purely expressive (record that honestly) or not yet
sharp enough (push back to Stage 2 of the interrogation).

**Accessibility floor (WCAG 2.1 / 2.2).** Named SCs that aesthetic goals
must clear, regardless of direction:

- **1.4.1 Use of Color** — information must not be conveyed by color alone;
  a goal around "color as the identity signal" must pair color with shape or
  label.
- **1.4.3 Contrast Minimum** — text must meet the WCAG-defined thresholds for
  normal and large/bold text respectively. A goal of "low-contrast, airy
  typography" is constrained by this floor; name the tension explicitly.
- **1.4.11 Non-text Contrast** — interactive components and their focus
  indicators must meet the Non-text Contrast threshold against adjacent
  colors. A "borderless" aesthetic must still clear this for inputs and buttons.
- **2.4.7 Focus Visible** — keyboard focus must be visually apparent. A
  dark-on-dark direction must name how focus is expressed without breaking
  the palette.
- **2.3.3 Animation from Interactions (WCAG 2.1 AAA)** — non-essential
  animation triggered by interaction must honor the OS-level reduced-motion
  preference. A goal with motion as a core quality should name the
  reduced-motion fallback up front.
- **APCA (Accessible Perceptual Contrast Algorithm)** — where WCAG
  contrast is the regulatory floor, APCA gives a perceptual complement
  that better models how lightness differences read. For large display text
  or decorative low-contrast intent, cite both: "clears 1.4.3 at X:1;
  APCA Lc Y for this usage."

**Interaction-design principles.** Heuristic anchors that connect a named
goal to a field-recognized mechanism:

- **Nielsen's 10 Heuristics** — especially #1 Visibility of System Status
  (a "calm" goal should name how loading / error / success states express
  calm, not just idle state), #4 Consistency and Standards (a "distinctive"
  goal must name what it is distinctive *against*), and #8 Aesthetic and
  Minimalist Design (every element competes for attention — the goal should
  name what earns its place).
- **Hick's Law** — time to decide grows with the number of options. A goal
  of "effortless first run" is grounded by naming how choice cost is reduced
  at key decision points (progressive disclosure, sensible defaults, default
  opt-in paths).
- **Information-scent (Peter Pirolli)** — users follow the path of highest
  perceived information-scent; a navigation goal is grounded when it names
  how the labeling strategy maximizes scent to the target content.

**Typography canon.** For goals with a typographic quality dimension:

- **Optical sizing** — display text at headline sizes benefits from optically-sized
  variants (`font-optical-sizing: auto` or explicit axis `opsz`); body text
  is set at the text optical size. A "premium, crafted" goal at large scale
  names whether the typeface has an optical size axis.
- **Fluid type scale via `clamp()`** — `font-size: clamp(min, preferred-vw,
  max)` produces a scale that grows smoothly between breakpoints. A goal of
  "consistent reading rhythm across viewports" is grounded by naming the
  scale strategy (min/max values and the preferred rate of growth).
- **Variable-font weight axes** — if the direction uses weight to carry
  hierarchy (heavy display / light body), name whether the chosen typeface
  has a `wght` axis for continuous interpolation rather than a step-function
  optical weight jump.
- **Line-length and leading** — body text reads best at 45–75 characters per
  line (Bringhurst); leading of 1.4–1.6 × the font-size for body, tighter
  (1.1–1.2) for display. A goal of "effortless reading" is grounded by
  naming the target measure and leading.

**Information-architecture rubrics.**

- **Progressive disclosure** — reveal only what the user needs at each
  decision point, surfacing complexity on demand. A "simple but powerful"
  goal should name the disclosure strategy: what is shown at first glance
  vs. one interaction deeper vs. in settings.
- **Diátaxis framework** (Procida) — for product documentation surfaces:
  tutorials (learning), how-to guides (doing), reference (information),
  explanations (understanding). A goal of "trustworthy documentation" is
  grounded by naming which Diátaxis quadrant the current surface belongs to
  and the structural standards that quadrant imposes.
- **Card sorting / IA testing** — when a goal involves navigation or
  categorization, name whether open-card-sort evidence (user-generated
  categories) or closed-card-sort validation (user-sorted into proposed
  categories) has informed the structure. Without evidence, the goal is a
  hypothesis.

### 4 — Platform conventions

What does the target surface's platform guidance say about this quality?

The target surface (`responsive-web`, `iOS`, `Android`, or
`cross-platform`) determines which platform guidance is relevant. For
each goal, name how the platform's guidance shapes or bounds it:

- **iOS (Apple HIG)** — The HIG's visual voice is *clarity, deference,
  depth*: the UI recedes so content is primary, spatial cues (depth,
  translucency) signal context. Named tensions with common aesthetic goals:
  a "branded, distinctive" direction must justify departing from system
  font (SF Pro) and system colors — the HIG calls this out as a legibility
  and trust risk. The **visionOS Spatial Design guidelines** extend this into
  three-dimensional surfaces where depth is a first-class layout axis.
  Cite the HIG chapter (e.g. "Visual Design → Color") rather than
  paraphrasing.
- **Android (Material 3 / Material You)** — Material 3's visual voice is
  *personal, adaptive, expressive*: dynamic color (extracted from the
  user's wallpaper) means brand color must coexist with user-sourced
  palettes. The **Expressive tier** (2024) introduces bolder, more
  personality-forward defaults — shapes, colors, and type at higher
  contrast ratios than Material 2. A goal of "distinctive brand color" must
  name how it degrades when the system overrides with dynamic color. Point
  to the Material 3 spec section (e.g. "Color System → Dynamic Color").
- **responsive-web** — MDN's Responsive Design guide and, where relevant,
  PWA conventions. For visual voice: the Stripe / Linear / Vercel design
  language has established a *dark hero + high-contrast type + single
  chromatic accent* pattern as the default "serious developer product"
  voice; a direction choosing this vocabulary should name what specifically
  is taken and what differentiates from that default (else the product reads
  as a Vercel clone). The **Inter** and **Geist** type families are now the
  de-facto "modern web app" signal; choosing them is a convention, not a
  distinction.
- **cross-platform** — design the shared intent once, then name the
  per-surface adaptations the goal requires. Each surface's platform
  guidance applies to its own adaptation; the shared goal must clear
  all of them. A "consistent brand across iOS + web" goal must name
  the tension point: SF Pro on iOS vs. brand typeface on web, and
  how brand color interacts with HIG's color semantics on iOS.

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

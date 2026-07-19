# The experience thread

> **Explanation** — understanding-oriented. Why this pack is shaped the way it
> is. For the steps, see the [how-to](../how-to/author-design-intent.md); for
> the per-skill contract, see the [reference](../reference/experience.md).

## Design as upstream intent

A UI build consumes more than a feature spec. It consumes **design intent**:
who the customer is and what they're trying to do, the screens that serve that,
the services behind those screens, what the product should feel like, how each
screen behaves, and whether the result holds up to scrutiny. When that intent is
implicit — living only in a designer's head or a pile of mockups — the build
re-derives it badly, and every later choice re-argues taste.

`experience` makes that intent explicit and durable, the way
`product-engineering` makes product intent explicit. It is the design-side twin
of that seam: the artifacts it produces (a journey map, a screen flow with
per-screen briefs, a service blueprint, a grounded aesthetic direction, a
critique) live in the repo and steer the build.

## One walkable thread, no broken link

The pack's bar is not skill count — it is that the design flow is a **complete,
walkable thread**:

**journey → screen flow + per-screen briefs → backing services → genre-specific
surface design → copy → review → realization**, with internal-process mapping as
the inside-out sibling and design-principles as the Define-phase anchor.

The skills compose along that thread, each connecting to the next by a named
seam (every skill declares its inputs and what consumes it):

- **`journey-mapping`** — the outside-in journey: stages × actions,
  emotions, pains, peak moments (Kahneman peak-end). Carries `evidence-level`
  (observational / survey-backed / assumption-based) and a `surface-genre`
  confirmation. The thread's head.
- **`design-principles`** — turns journey insights into 3–5 named, testable
  design principles (NNGroup 4-step model). Consumed by `creative-direction`,
  `information-architecture`, `content-design`, and `design-review`.
- **`user-flow`** — the journey's screens *sequenced*, with transitions
  and error/edge flows, a per-screen state matrix (with `surface-genre:`
  declared in each brief), and **one self-contained brief per screen**. It ends
  in a cross-brief consistency pass and a whole-journey **steel thread** (below).
- **`service-blueprint`** — the service blueprint behind the screens: five rows
  (evidence-of-service, frontstage, line-of-visibility, backstage, support), with
  explicit fail-point marking (critical / high / medium). The backstage column is
  the slicing instrument handed to `architect`/`contracts`.
- **`creative-direction` · `design-system` ·
  `information-architecture` · `interaction-design`** — the craft
  skills that design each screen from its brief: the felt direction (grounded in
  stable referents + genre canonical references), the token/scale system, the
  structure and wayfinding (with genre routing), and **how the screen behaves**
  (with 5 additional pattern families: wizard-and-stepper, data-table,
  destructive-action escalation, save-state, analytical-dashboard-widgets).
- **`conversion-design` · `documentation-design` · `analytical-design` ·
  `marketplace-design` · `informational-design` · `workspace-design`** —
  the six genre-specific skills, each specializing the IA and structure layer for
  one surface genre. Declare the genre once; the right skill applies.
- **`content-design` · `tone-of-voice`** — the copy layer: `tone-of-voice`
  names the brand voice; `content-design` applies it per screen.
- **`design-review`** — the authoring-time critique (design-principles
  integration chain + genre-specific rubrics + heuristics + taste mode) you run
  as you go.
- **`experience-reviewer`** — the forked-context agent that reviews the whole
  set independently (see below).
- **`process-mapping`** — the inside-out sibling: an internal business
  process (APQC L3→L4, as-is/to-be, SIPOC, swimlane, pain/waste), for the
  operations a customer journey never touches.

The one input the pack does *not* produce — generative user research (personas,
usability testing) — is consumed by detect-and-degrade: every connective skill
elicits it inline when it's absent, so no skill blocks on it.

## The steel thread — the thread's guarantee

`user-flow` never ends at "briefs emitted." It always runs a whole-journey
walk: a low-fidelity prototype when a design-tool MCP is connected, **else a
text-only steel thread** — a scripted walk through the briefs in journey order
asserting *every transition resolves* and *every action has a backing service*.
This verification is **non-droppable**: it degrades from prototype to text-only,
never to nothing. It is how a pack deliberately coarser than a maximalist
catalogue still guarantees no broken link from journey to realization.

## Macro flow vs micro behavior — the carve

Two skills touch states and transitions, and must not be conflated:

- **`user-flow`** owns the **macro flow *across* screens** — which screens,
  in what sequence, and the cross-screen error/edge routing.
- **`interaction-design`** owns the **micro behavior *within* a screen** — the
  in-component state machine, feedback and timing, input-validation flow, motion,
  gesture.
- The **shared quality floor** owns the **enumeration** of states both defer to.

Three state homes, one carve: the floor names the state *set*, `user-flow`
owns *cross-screen* routing, `interaction-design` owns the *in-component* state
machine.

## The shared `quality-floor`

Every artifact clears one shared **`quality-floor`** — three commitments no
design is done without:

- **Handle all states** — empty, loading, error, success, partial, disabled,
  plus `permission/denied` when gated. The happy path is one state among several.
- **Accessibility floor** — meet the recognized standard (WCAG, at your context's
  level), read from the source.
- **Motion communicates state, honor reduced-motion** — motion earns its place by
  carrying meaning, and always offers a reduced-motion path that keeps it.

It is one file, referenced by every consuming skill (and by the reviewer);
`design-review` and `experience-reviewer` apply it as an explicit pass.

## The independent review

`design-review` is the *authoring-time* skill — you run it in the session, with
the author. But a same-session critique marks its own homework. So the pack also
ships **`experience-reviewer`**: a forked-context, read-only agent that reviews
the journey, the screen flow and briefs, and the aesthetic against the grounded
reference, platform fit, cross-brief coherence, and the full quality floor —
including the accessibility section, the one independent a11y check between
human-value-add gates. It flags; it never rewrites; it never touches code diffs
or architecture docs. This lets the design step run autonomously between the
gates where a human adds judgment.

## Why framework-agnostic

A design pack is the most tempting place to bake in a stack — a default palette,
a spacing scale, a CSS snippet, a motion-curve table. The charter's rule is "not
a framework that picks your tech stack," so `experience` ships **method, not
values**. Two guardrails make that concrete:

- **Point to standards, never reprint values.** The skills name WCAG, the W3C
  Design Tokens shape, Apple HIG, Material 3, APQC, and BPMN, and teach you to
  *derive* your design — they never hand you a palette, a breakpoint table, or a
  duration.
- **Concepts, not platform primitives.** Wayfinding is orientation, not markup
  roles; a state machine is a statechart, not a state-management library; motion
  is the reduced-motion *principle*, not a media query.

The payoff: the discipline travels to any repo, any stack, any toolchain, and
survives a framework change because it never depended on one. A pack-scoped lint
enforces the guardrails so a well-meaning edit can't quietly erode them.

## What's deliberately not here

`experience` is **habits, not infrastructure**. No hooks, no engine, no in-pack
validator, no runtime, no pixel comps. The one shipped agent, `experience-reviewer`,
is a read-only review lens (admissible under the agent-addition policy because it
reviews a different surface at a different cadence than code review) — not a
runtime. The optional design-tool handover is *instructions* a generative tool
consumes, never a comp, and it names tool categories, never a winner. And the
pack maps design intent up to realization; the realization itself stays the
design tool's or a human's job.

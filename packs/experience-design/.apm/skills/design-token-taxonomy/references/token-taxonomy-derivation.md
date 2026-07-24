# Deriving a token/scale taxonomy

How to turn a named aesthetic direction into a token system — without ever
reprinting a values table. You ship the method and a symbolic shape; the
reader fills in the values for their context.

## Purpose before token

Decide what a token is *for* before anyone picks its value. A token is a named
decision, and the name should answer "what job does this do?" — not "what
number is it?" When purpose comes first, the value is a downstream choice you
can revisit; when the value comes first, you've baked a guess into the system
and you'll relitigate it every time the direction shifts.

Work top-down from intent:

1. Take a named goal from the aesthetic direction (e.g. "calm", "authoritative").
2. Ask what the system needs to express it — surfaces, emphasis levels,
   rhythm, density.
3. Name those needs as roles. Only then reach for values.

## Semantic-over-literal naming

Name a token for the **role it plays**, never the **appearance it has today**.

- A literal name describes the current value: it ties the name to a specific
  look. The moment the look changes, the name lies, and you either rename
  everywhere or live with a token whose name contradicts its value.
- A semantic name describes the job: "the surface a primary action sits on",
  "the emphasis level for a warning". The value behind it can change with the
  direction — light to dark, one hue family to another — and every consumer
  keeps working, because they referenced the *role*, not the look.

Rule of thumb: if renaming the token would be required after a visual refresh,
the name was literal. Fix it before the system grows.

Layer the names so intent flows downward:

- **Primitive** — a raw decision with no context ("the system's deepest
  surface tone"). Few of these; they are the source.
- **Semantic / alias** — a role that *references* a primitive ("the surface
  behind a primary action"). Consumers bind to these, never to primitives.

When the direction changes, you re-point the semantic layer at different
primitives. Consumers don't move.

## Ratio-as-concept scales

A scale is not a list of numbers you hand-pick — it's a **single ratio**
applied repeatedly to a base. The ratio *is* the design decision; the steps
fall out of it. This keeps spacing and type internally consistent and makes
the system explainable: every step has a reason, not a vibe.

- Pick **one base** and **one ratio** for spacing. Each step is the previous
  step transformed by the ratio. Express steps symbolically:

  ```
  step −2   step −1   base   step +1   step +2
  ```

  The base anchors the scale; the ratio sets how fast it grows. Tighter
  ratios read as dense and calm; wider ratios read as bold and spacious —
  derive the ratio from the *named goal*, not from a favorite number.

- Do the same for **type**: one base size, one ratio, symbolic steps up and
  down for headings and supporting text.

- Reuse the same conceptual ratio across spacing and type where the direction
  wants them to feel related. Divergence is a deliberate choice, not an
  accident.

Hand back the *shape* — base, ratio-as-concept, symbolic steps — and let the
reader resolve it to values for their medium and density.

## Accessibility as a floor

Accessibility is a constraint on **every token at derivation time**, not a
pass you run later. Two tokens that look fine in isolation can fail together;
catch that when you derive them, not after the system ships.

- Every text/background pairing must clear the **recognized standard — WCAG,
  at the conformance level your context requires**. Read the threshold from
  the source; this reference never reprints a ratio.
- Interactive targets must be large enough to hit and meaning must never ride
  on one channel alone. The shared `quality-floor` checklist
  (`../design-review/references/quality-floor.md`) is the full floor.

If a token can't clear the floor without breaking the direction, that's a
finding to surface — a tension between goals — not a detail to wave through.

## Contrast budget

Contrast is a finite resource on a screen. If everything shouts, nothing does.
Allocate a **contrast budget**: decide where the eye should land first,
second, third, and spend your strongest contrast there. Most of the surface
sits at low contrast so the few high-contrast elements carry real emphasis.

- The budget is a consequence of the hierarchy, which comes from the intent.
- Clearing the accessibility floor is the *minimum*; the budget is how you
  spend what's left to create emphasis — never by dropping below the floor.

## Portable serialization

Record the taxonomy in the **Design Tokens Community Group (DTCG) specification** format — the
standard, tool-neutral way to serialize tokens (a token has a name, a type,
and a value, and tokens nest into groups). Serializing to that shape means the
system travels across design and build tools instead of living in one editor.

Read the specification from the W3C Community Group (DTCG); this
reference points to it rather than embedding a schema or any values.

# Naming, layering, and scales

How to name what the system holds, how to layer it, and how a scale is
organised. `value-derivation.md` decides *what* a value should be; this page
decides what it is called and how it hangs together.

## Purpose before token

Decide what a token is *for* before fixing its value. A token is a named
decision, and the name should answer "what job does this do?" — not "what
number is it?" When purpose comes first, the value is a decision you can
revisit against the direction that justified it. When the value comes first,
you have baked a guess into the system and you will relitigate it every time
the direction shifts.

Work from intent:

1. Take a ranked goal from the approved direction.
2. Ask what the system needs to express it — surfaces, emphasis levels,
   rhythm, density.
3. Name those needs as roles.
4. Then resolve each role to a value.

Step 4 is not optional. A role with no value is a question handed to whoever
writes the code.

## Semantic-over-literal naming

Name a token for the **role it plays**, never the **appearance it has today**.

- A literal name describes the current value and ties the name to a specific
  look. The moment the look changes the name lies, and you either rename
  everywhere or live with a token whose name contradicts its value.
- A semantic name describes the job: "the surface a primary action sits on",
  "the emphasis level for a warning". The value behind it can change with the
  direction — light to dark, one hue family to another — and every consumer
  keeps working, because they referenced the *role*, not the look.

Rule of thumb: if renaming the token would be required after a visual refresh,
the name was literal. Fix it before the system grows — unless the token is an
incumbent one, in which case note it and leave it. Renaming a shipped token
costs every consumer and buys the product nothing it asked for.

## Layering, where the project supports it

Two layers, when the project's architecture already separates them:

- **Primitive** — a raw decision with no context. Few of these; they are the
  source.
- **Semantic** — a role that *references* a primitive. Consumers bind to these,
  never to primitives.

When the direction changes, you re-point the semantic layer at different
primitives and consumers do not move. That is the whole payoff, and it is why
the separation is worth preferring where a project has no convention yet.

It is a preference, not a requirement. A product whose system is six
well-named constants does not need two tiers, and imposing them adds overhead
the product will route around. Follow what the project already uses —
`incumbent-systems.md` covers the shapes.

## Ratio-as-concept scales

A scale is not a list of hand-picked numbers — it is **one ratio** applied
repeatedly to a base. The ratio *is* the design decision; the steps fall out of
it. This keeps spacing and type internally consistent and makes the system
explainable: every step has a reason.

- Pick **one base** and **one ratio** per scale. Each step is the previous step
  transformed by the ratio.
- Derive the ratio from a named goal, not from a favourite number. Tighter
  ratios read dense and calm; wider ratios read bold and spacious.
- Resolve the steps the product actually needs, and say which situation each
  serves. A scale with steps nothing uses is a scale you will have to defend.
- Reuse the same conceptual ratio across spacing and type where the direction
  wants them to feel related. Divergence is a deliberate choice, recorded.

## Portable serialization

Where the artifact is expected to travel between tools, record the values in
the W3C Design Tokens interchange shape — the standard, tool-neutral way to
serialize tokens, where a token has a name, a type and a value, and tokens nest
into groups. Read the format from the W3C Design Tokens specification; this
reference points at it rather than embedding a schema.

This is a serialization choice, not a requirement. A product with a theme
object or a constants module is not obliged to add an interchange file it has
no consumer for.

# Reading patterns and hierarchy

How the eye moves across a screen, and how to arrange meaning so the
movement lands where you want it. All relative — no measurements. The
point is the *order* things are noticed, never a number.

## How the eye scans

People don't read a screen top-to-bottom like a page. They scan, and the
scan has a shape. Pick the pattern your layout should reward, then lay the
important things along that path.

- **F-pattern** — text-dense, scannable surfaces: search results, feeds,
  documentation, long forms. The eye sweeps across the top, drops down the
  left edge, and makes shorter sweeps as it goes — tracing an F. Put the
  highest-value words first in each row and first down the left rail.
  Front-load headings and link text; a row that buries its point past the
  first few words gets skipped.
- **Z-pattern** — sparse, hero-style surfaces with few elements: a landing
  screen, a sign-up, a single call to action. The eye travels top-left to
  top-right, diagonally down to bottom-left, then across to bottom-right —
  tracing a Z. Place the brand or orientation cue top-left, the primary
  action where the Z ends, and let the diagonal carry the story between.
- **Layer-cake / spotted scans** are variants worth naming: when a page is
  clearly sectioned with strong headings, the eye reads heading-to-heading
  (layer cake); when it hunts for one specific thing, it fixates in spots.
  Both reward clear, repeated section markers over dense prose.

Choose the pattern from the surface's *job*, not from habit. A dense list
that you force into a Z fights the reader; a hero you cram with F-pattern
rows loses its focal point.

## Visual hierarchy — the relative levers

Hierarchy is what tells the eye *this before that*. You have a small set of
levers, and they all work by contrast — an element reads as important
because it differs from its neighbors, not because of any absolute value.

- **Size** — larger draws the eye first. Reserve the largest treatment for
  the one thing that matters most on the surface; if everything is large,
  nothing leads.
- **Weight** — heavier or bolder reads as more important than lighter.
  Weight separates a label from its value, a heading from its body.
- **Spacing** — the strongest, most-underused lever. Space *around* an
  element isolates it and lifts it forward; space *between* groups says
  "these belong together, those don't" (see proximity in
  `wayfinding-concepts.md`). Generous space signals calm and importance;
  crowding signals density and lowers each item's individual weight.
- **Position** — earlier in the scan path (above, leading edge) reads as
  more important than later. Top and leading positions are premium; the
  end of the scan is where you place the resolution, not the setup.
- **Color and contrast** — higher contrast against the surroundings
  advances; lower contrast recedes. Use contrast to rank, and never let it
  be the *only* channel carrying meaning (the accessibility floor in
  `quality-floor.md`).

The discipline: decide the rank order of everything on the surface first —
primary, secondary, tertiary — then assign levers so the visual order
matches the intended order. When two things compete for first place, the
eye stalls. Demote one.

## Progressive disclosure

Show the user what they need now; reveal the rest as they need it. A screen
that exposes every option at once is hard to scan and easy to abandon; one
that hides everything is a maze. The balance is *staged* complexity.

- Lead with the common path and the few choices most users want. Defer the
  advanced, rare, or destructive controls to a second layer — a detail
  view, an expandable section, a later step.
- Each reveal should be predictable and reversible: the user can see that
  more exists, open it on demand, and close it again without losing place.
- Stage by the user's task, not by the data model. The order options
  appear should match the order a person decides things, not the order a
  database stores them.
- Don't disclose-away the essential. If a choice is needed to proceed
  safely, it belongs on the first layer, not hidden behind a reveal.

Progressive disclosure is how a complex product feels simple: depth is
available, but the surface stays legible.

## Depth versus breadth in a navigation tree

Every information architecture trades **breadth** (many choices at each
level, a shallow tree) against **depth** (few choices per level, more
levels to traverse). Neither is free.

- **Too broad** — a single level with too many options overwhelms the scan
  and hides the structure; the user can't tell what groups with what.
- **Too deep** — few options per level, but many levels to descend; the
  user loses the thread, forgets where they are, and tires of clicking
  toward a goal they can't yet see.
- **The middle** — group related items so each level offers a handful of
  clearly distinct choices, and keep the path to any common destination
  short. Most reachable things should sit within a few steps of the start.
- Let real tasks set the shape. Frequent destinations deserve shallow,
  fast paths; rare ones can live deeper. Categories should map to how users
  think about the content, verified by how they actually look for it — not
  to the org chart or the schema.

A good tree is one a user can hold in their head: they can predict where a
thing lives before they go looking for it.

# Knowledge surfaces — drawing the system as it actually is

A diagram is only as accurate as the system it is read from. When you draw the
*as-is* topology, the most expensive errors are the **factual** ones — a box for
a service that doesn't exist, an arrow to the wrong neighbour, an edge label
guessed because the real contract lives outside the repo. In **document** and
**update** mode the skill already reads the code before drawing; this reference
extends *read the repo* to **read the landscape**, so the boxes, arrows, and
edge labels **beyond the repo boundary** are grounded instead of guessed. It is
loaded **only when** the mode is document or update **and** a knowledge surface
is reachable (see *Detection* below); in design or review mode, or when no
surface is present, this file is never loaded.

This is the **as-is-drawing lens**. It consults surfaces the way
`architect-design` does — to *build* an accurate artifact — not the way
`architect-review` does (which *checks* that a design was grounded and never
builds). But it is **narrower than design's**: an as-is diagram makes no
normative, advisory, historical, or anticipatory claims, so the lens turns on
**only the descriptive current-system facets — areas 2, 3, and 4** (the 2/3/4
adjacency seam below). And it is **mode-scoped**: it fires only in **document**
and **update** mode. It does **not** fire in **design** mode — there you draw
the user's *hypothetical*, where fabricating an unnamed component is
allowed-but-flagged and there is no as-is to ground against — and it does
**not** fire in **review** mode, which routes to `architect-review`. **This
taxonomy is the as-is-drawing-lens reuse of `architect-design`'s
knowledge-surfaces core: the eight areas and the modality×space axis are the
shared canonical core — only the trigger column, this lens paragraph, and the
detection/degrade framing change.**

## The eight knowledge areas (MECE)

Each area answers one question. An as-is diagram turns on only the descriptive
current-system facets — **areas 2, 3, and 4** — so those are the rows you draw
from; the other five are listed to keep the taxonomy whole but fall outside the
drawing lens (they belong to `architect-design`'s broader consult).

**What you may draw from a surface.** A box, an arrow, or an edge label beyond
the repo boundary may be drawn **named** only when a surface grounds it — the
service catalogue names the neighbour and its owner, the schema registry gives
the contract on the edge, the runbook gives the operational annotation. Add a
short **provenance note** (which surface) on or beside the grounded element so
the diagram is auditable. A beyond-repo element a surface does *not* ground
stays `<unnamed>` or becomes a question — never a guessed name. (Read the
trigger column below against this.)

| # | Area | The question it answers | Draw from a surface when… (as-is lens: areas 2/3/4) |
|---|---|---|---|
| 1 | Business domain & meaning | What do the terms, capabilities, and business rules *mean*? | — out of the as-is lens: a *meaning* question, not a topology fact (that is `architect-design`'s consult) |
| 2 | Current landscape | What systems, services, data, and ownership *exist* today? | the as-is system depends on or talks to something **beyond the repo boundary** the code doesn't name — a neighbouring service, its owner, the data it holds |
| 3 | Interfaces & contracts | What can I integrate with, and on what *terms*? | a drawn edge crosses the repo boundary and its protocol, topic, or contract *terms* aren't in the code you can read |
| 4 | Operational reality | How does it *behave* in production (SLOs, incidents, failure modes)? | the diagram annotates a runtime property of a beyond-repo dependency — an SLA, a queue, a failure mode — you'd otherwise guess |
| 5 | Constraints & standards | What *must / must-not* I do (policies, approved tech, security rules)? | — out of the as-is lens: *normative*; a diagram draws what **is**, not what **must** be |
| 6 | Patterns & references | How is this *done well* here (reference architectures, golden paths)? | — out of the as-is lens: *advisory*; reference shapes are design input, not as-is fact |
| 7 | Decisions & rationale | *Why* is it this way; what's *deprecated*? | — out of the as-is lens: *historical*; the *why* isn't drawn |
| 8 | In-flight & roadmap | What's *changing* or being built in parallel? | — out of the as-is lens: *anticipatory*; draw today's system, not the roadmap |

### Why these eight don't overlap (MECE)

The set is mutually exclusive along two axes — **modality** (what kind of
statement) × **space** (problem vs solution):

- **Descriptive** — area 1 (problem space) and areas 2/3/4 (solution space).
- **Normative** — area 5 (what must).
- **Advisory** — area 6 (what's recommended).
- **Historical** — area 7 (why it's so).
- **Anticipatory** — area 8 (what's coming).

**The one adjacency seam:** areas 2, 3, and 4 are three *facets of the current
system*, not duplicates — *what exists* (a service catalogue), *how to call it*
(an API/schema registry), and *how it runs* (runbooks, SLOs, incident history).
They come from different sources and answer different questions; keep them
distinct rather than collapsing them into "the landscape."

## Detection — find surfaces to draw from, name no tools

A knowledge surface can take **any form** — an MCP knowledge tool, an internal
CLI, an in-repo doc set, a search API. The skill therefore reasons about
*capabilities*, never specific tools. **Hardcode no tool or CLI name here or in
the skill body.**

Discover what's reachable from the session itself:

- If your harness **defers tools** behind a search/registry, issue a search for
  retrieval-shaped capabilities (a tool that *searches / queries / looks up /
  retrieves* over internal knowledge, or a knowledge CLI on `PATH`).
- If your harness **loads tools eagerly**, read your available tool list for the
  same shape.
- An in-repo knowledge set (`docs/`, an architecture index) is a surface too —
  you can already read it.

**Detection is gated on mode.** Run it **only** in document or update mode — the
two modes that draw a real as-is system. In design mode you draw the user's
hypothetical (no as-is to ground against), and review mode routes to
`architect-review`; in both, skip detection entirely. When the mode qualifies
and a surface is found, consult the descriptive facets (areas 2/3/4) your
diagram's beyond-repo elements turn on. If a found surface returns nothing
useful for an element, treat it as *absent* for that element and fall to the
degrade rule below.

- **Internal only.** A general **public web search / fetch** tool is *not* an
  internal knowledge surface — it can't tell you what *your* organisation's
  topology actually is. Don't count it, and don't claim enterprise grounding
  from it.

### Three honesty rails

- **Name what you drew from.** State on or beside each beyond-repo element which
  surface grounded it, and give the diagram an overall provenance line — the
  surface(s) used, or **"repo only / none"**. A grounded box that doesn't say
  where its name came from is self-attested, not auditable.
- **Never fabricate — leave it `<unnamed>` or ask.** A node or edge you can't
  ground from the repo or a surface stays `<unnamed>` or becomes a question to
  the user — never a guessed name. This **strengthens** the skill's standing
  never-fabricate-names anti-pattern; it is not a parallel rule.
- **A contradicted edge is flagged, not drawn over.** A single surface can be
  stale or wrong (the area-7 failure mode). When a surface-derived edge
  **contradicts** what the repo shows, draw the repo's truth and **flag** the
  conflict as a note or question — don't silently redraw the topology to match
  one unconfirmed source.

## When no surface is reachable — `<unnamed>`, don't guess

When the mode qualifies but no internal surface is reachable (or none grounds a
particular beyond-repo element), the diagram does **not** invent a name to fill
the box. Draw the element `<unnamed>` — or, when its very existence is uncertain,
ask the user rather than drawing a speculative node — and note "repo only / no
surface" as the diagram's provenance. The user, who has the enterprise context,
supplies the missing name; the diagram's job is to show the real topology and
make the gap visible, not to paper over it with a plausible guess.

## What the consult changes in the diagram

The consult never changes *how* you draw (notation, layout, and the rubric in
`references/diagram-rubric.md` still govern) — only *how grounded* the
beyond-repo elements are:

- A beyond-repo neighbour a surface names is drawn **named**, with a one-line
  provenance note (which surface), instead of `<unnamed>` or omitted.
- An edge whose protocol / topic / contract the surface supplies carries that
  **real label** instead of a bare or guessed one.
- An element no surface grounds stays `<unnamed>` (or a question), and the
  diagram's provenance line reads "repo only / none".
- A surface-derived fact the repo **contradicts** is drawn as the repo shows,
  and the conflict is **flagged** beside it — a note or a question, never a
  silent overwrite.

Grounding work rides on top of the skill's existing document-mode discipline
(read before drawing; never fabricate names); it adds reach — the landscape, not
just the repo — not a parallel mechanism.

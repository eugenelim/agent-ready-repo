---
type: screen-brief
slug: team-orientation-canvas
surface-genre: marketing
surface: responsive-web
status: active — IA half here, interaction half enriched in screens/team-orientation/operating-model-canvas.md
gap: C
governed_by:
  - docs/design/principles/tech-site.md
  - docs/specs/platform-site/aesthetic-direction.md
updated: 2026-09-04
---

- **Type:** screen-brief

# The operating-model canvas

**Why this is a screen brief.** No installed skill designs an explanatory
information graphic. `architect-diagram` is Mermaid and C4 — the wrong genre,
and the C4 FAQ itself states its audience is engineers reading about a system
that already exists. `mermaid-renderer` only rasterises. `interaction-design`
does screen behaviour. `frontend-engineering` builds but does not design. So the
canvas is treated as a screen: this document is the `information-architecture`
half — what the reader must be able to trace, in what order, in what states.
`interaction-design` owns the behaviour half. That is the Gap C workaround.

**This document does not contain the drawing.** It contains what the drawing must
make traceable, and the constraints any drawing must satisfy.

---

## 1. The metaphor

The peer audit is unambiguous that metaphor is the load-bearing layer, and that
applying composition and colour before the metaphor exists is the named failure
mode — metaphor inversion. So the metaphor comes first, with its mapping and its
limits stated.

**A rail line with five stations, where the second station is a depot that work
cycles through.**

**One word, used consistently.** The packet calls this the **arc** throughout —
the team's arc — while the drawing renders a straight line. That is deliberate:
"arc" names the *narrative* shape (a team's progression) and distinguishes it from
the "sequence" inside the enclosure. The geometry is a line; the word is arc; and
no artifact should mix them.

| Source domain | Target | What it buys |
| --- | --- | --- |
| A line running left to right | The adoption arc: evaluate → prove → win buy-in → roll out → default | Direction without arrows; a reader knows which way is forward without a legend |
| Five named stations | The five team states | A station is somewhere you can *be*. "We're at station three" is a sentence a champion can say to a budget holder. |
| A depot at station 2 | The work lifecycle | Repetition is native to a depot. Work enters, cycles, leaves — and the line continues past it. This is the nesting, made structural rather than annotated. |
| Signals on the line | The points where a human decides | A signal is precisely a place where something must be cleared by an operator before anything proceeds. It is the human decision expressed as a shape, with no code and no jargon. |
| A spur off the depot ending at a buffer stop | The tracker projection | **The single best thing the metaphor buys.** "Status never comes back" becomes a visible dead end. The one-way property is readable from the geometry, not from a caption. |
| Track that runs to the depot from off-map, versus track inside the yard | Shaping travels with the person; build and release belong to the repository | The scope boundary becomes a place rather than a legend entry |

**Stated limits, because a metaphor that is not bounded misleads:**

- **A rail journey leaves stations behind; adoption is cumulative.** A team that
  reaches "make it the default" still does everything from the earlier stations.
  Mitigation: stations stay lit once reached. The canvas shows accumulated state,
  not a train's current position — there is no train.
- **A rail line implies one fixed route.** Real teams skip stations, reorder, and
  revisit. Mitigation: the line is the common route, not a mandate, and the copy
  must say so once. It must not be drawn as a track with no junctions.
- **Rail iconography is a well-worn choice in technical marketing.** Identity
  specificity — the fourth named aesthetic goal — warns against borrowing a
  reference wholesale. Mitigation: the identity comes from the product's own
  structure, which is the buffer stop, the signals, and the depot nesting. It
  must not come from imitating a named transit system's styling.

**What the metaphor must not become.** Not boxes joined by arrows, which the peer
audit names as spaghetti wires and automatic failure. Not a C4 or UML idiom on a
persuasion surface. Not a flowchart, which would imply a decision tree the model
does not have.

---

## 2. What the reader must be able to trace, in order

The canvas's internal scan order. This is neither Z nor F; it is a traced path,
and the trace order is the design.

| # | The reader traces | And therefore knows |
| --- | --- | --- |
| 1 | The line, left to right, with five named stations | This is about a team over time, not a command to run |
| 2 | That station 2 is visibly larger and contains something | The detail is nested inside the arc, not beside it |
| 3 | The eight work steps inside the depot, in sequence | What actually happens to one piece of work |
| 4 | The signals, and that several sit inside the depot | A person decides at specific named points |
| 5 | The spur leaving the depot and ending at a buffer stop | Their tracker gets a report and sends nothing back |
| 6 | The boundary between the approach track and the yard | What travels with a person and what belongs to the repository |

**Steps 1 and 2 must complete inside five seconds without interaction.** Steps 3
to 6 may require reading, but must not require interacting.

**Rank.** Primary: the line and its five stations. Secondary: the depot and its
contents. Tertiary: signals, the spur, the scope boundary. If the drawing makes
the depot compete with the line for first place, the nesting has inverted and the
two-lifecycle problem is back.

---

## 3. Labels — sourced where a source exists, authored where none does

**An earlier draft claimed every label was derived from `guides/README.md`. Cold review showed that is false, and the corrected rule is narrower.**

| Labels | Source |
| --- | --- |
| The three human-decision steps — *a spec and plan you approved*, *a pull request you merge*, *you ratify the production ship* | **Adapted from** the published P3 and P5 *first value* and *ends at* fields. The last two are near-verbatim. |
| The five adoption station names | **Authored.** They come from the engagement's stated adoption lifecycle, which has no published copy. |
| The five non-decision work steps | **Authored** from the engagement's stated work lifecycle. |

The rule that matters is not "everything is derived" — it is that **where published, reviewed, gate-code-free copy exists for a label, it wins over a fresh phrasing.** That holds for the three decisions, which are the labels a champion has to repeat and the ones that replace the internal codes.

`ux-writing` owns final wording. The IA constraint is the sourcing rule and this
prohibition:

**No label may contain `G0`, `G1.5`, `G2`, `G3`, `G4`, or `G5`.** These are
machine contracts, not adopter copy. Eleven appear on the live page today; the
canvas is the element that replaces them, so it must not reintroduce them.
Signals carry the decision, phrased as a question a person answers.

---

## 4. The three renderings

One artifact, three contexts. The second one binds.

| | Context | Constraint | Consequence |
| --- | --- | --- | --- |
| **A** | Marketing home, above the fold | May be interactive | Interaction adds emphasis only |
| **B** | `README.md` on github.com | GitHub's Markdown sanitiser strips `<style>` blocks inside SVG, `class`, `id`, `<script>`, `<foreignObject>`, and `@import`. No animation of any kind plays — SMIL, CSS, and JS all fail. | **All presentation lives in element-level `fill` and `stroke` attributes.** No stylesheet. No classes. |
| **C** | Chat link unfurl (Teams, Slack) | SVG is not a valid preview image on any major platform. Raster required at 1200×630, under 1 MB, and under ~300 KB to survive WhatsApp. Slack fetches only 32 kB of the page. | A raster export path is a build requirement. And because Slack reads 32 kB, `og:title` and `og:description` do more work than the image. |

**Rendering B is the binding one.** Anything whose meaning depends on hover,
focus, scroll position, script, or a stylesheet cannot be part of the model. This
is not a degradation path bolted on afterwards; it is the design target, and A is
B plus emphasis.

**Rendering C reorders our own earlier priority.** We had assumed the unfurl
needed a picture of the canvas. The evidence says the text payload does the work
in a chat channel. So the champion-transfer surface is three meta tags *plus* a
raster — and `content-design` owns those three strings, which are as load-bearing
as the drawing.

**Verification owed, not assumed.** The sanitiser behaviour above is read from
documentation and practitioner reports. It governs a deliverable, so it must be
proved by rendering a probe SVG in a real README before the canvas is built.
Recorded as a build-handoff check.

---

## 5. States

All six. The canvas carries the model rather than decorating it, so an unhandled
state is a lost model, not a rough edge.

**Four rendering states beyond default, plus two cross-state requirements.**
Settled here after an earlier draft carried three different counts across three
artifacts.

| # | Rendering state | What the reader gets |
| --- | --- | --- |
| 1 | **default** | the whole model, legible, no interaction |
| 2 | **emphasis** | pointer-only weight change; carries no information |
| 3 | **reduced motion** | static — which is also the default |
| 4 | **narrow viewport** | replaced by the semantic ordered list |
| 5 | **sanitised static** | what a README renders |

Two things are **requirements on those states, not states of their own** — an
earlier draft miscounted both:

- **Focus visibility** applies to the component's one focusable element, the
  transcript control. It is not a state of the graphic, which has no focusable
  interior elements by design.
- **Screen-reader equivalence** is a requirement on states 1 and 4, satisfied by
  the same ordered list.

And **error** — the graphic failing to render — has no presentation of its own; it
recovers into state 4's artifact. One artifact serves the narrow viewport, the
screen reader, and the render failure.

| State | What the reader gets | Notes |
| --- | --- | --- |
| **Default** | The whole model, legible, no interaction | The only state that exists in renderings B and C |
| **Emphasis** | Hover or keyboard focus raises one station or one work step | Additive only. Removing it must lose nothing. |
| **Focus visible** | Every focusable element shows a visible focus indicator | The existing focus-ring system already handles dark carriers correctly with two documented scoped overrides — reuse it, do not re-derive it |
| **Reduced motion** | Static | The existing aesthetic decision already resolves this: static SVG, at most a one-shot entrance, no looping, grounded in a cited comprehension study. Rendering B makes it moot anyway. |
| **Narrow viewport** | The canvas is replaced by a semantic ordered list | See section 6 |
| **Sanitised static** | Rendering B | See section 4 |

No loading, empty, error, or partial states: the canvas has no data dependency
and is not gated. Stated so the absence is a decision rather than an omission.

---

## 6. Responsive collapse

**Replace-at-breakpoint.** Below the collapse width the canvas is not shown; a
semantic ordered list of the five stations is, with the eight work steps as a
nested list under station 2.

**The collapse width, stated as intent and corrected against a measurement.** An
earlier draft tied it to the 13px work-step labels. Rendering at a real 880px
content column showed those reach 9.5px and stay readable, while the **10px scope
group labels** reach 7.3px and are the first to fail.

So the threshold is set where the **scope group labels** stop being legible —
which is also the point at which the canvas stops carrying trace step 6, the
scope boundary. Below that, the ordered list is the better artifact.

The arc's 18px labels survive far past it, which is why the README rendering keeps
the graphic rather than replacing it: at 880px a reader still gets the five
stations and the nesting, and the list below supplies the rest.

It **must map to an existing marketing breakpoint** rather than introducing a new
one, because a new breakpoint would be a token-adjacent addition across two
renderers. `frontend-engineering` picks which existing one; the design constraint
is the legibility threshold, not a number.

Two things depend on it and are why it cannot stay unchosen: it is the only guard
in the component's state machine, and reflow at the narrowest supported viewport
is an accessibility requirement rather than a preference.

Why not the alternatives:

- **`viewBox` scaling alone** is the named near-universal failure for any
  text-bearing diagram — a wide canvas becomes illegible small text. This is
  reported as observed practice, not a hypothesis.
- **SVG-internal media queries** have patchy browser support, and rendering B
  strips the `<style>` block they would live in. They cannot work here.
- **Staged reveal on scroll** prevents the reader forming a model of the whole
  before engaging with parts, which is the one thing this canvas exists to do.

**The convergence that makes this cheap.** Replace-at-breakpoint requires the
canvas's information to exist in parallel textual form. WCAG 1.1.1 requires the
same thing for a diagram carrying information absent from adjacent text. **They
are the same artifact.** Build the ordered list once and it serves the narrow
viewport, the screen reader, and the reader who prefers text.

The nesting must survive the collapse: the work steps stay a *nested* list under
station 2, never a flat sequence of thirteen items. A flattened list is the
two-lifecycle collapse in text form.

---

## 7. Screen-reader equivalence

The current page's failure is the specification for this section. `ThreeLoops`
marks its pipeline `aria-hidden` on the reasoning that the cards below carry the
real content — but the cards each describe one loop and none states the sequence,
so the handoff chain exists only in the hidden element. The canvas must not
repeat that.

**The pattern.** `role="img"` on the graphic, with an accessible name and
description associated to it, plus an on-page disclosure transcript for the long
description. `role="img"` prevents inconsistent traversal into the SVG internals,
where a screen reader would otherwise emit raw text fragments or path
coordinates. The deprecated `longdesc` attribute must not be used.

**The transcript must convey four things a summary would flatten:**

1. The five stations, in order, as an ordered sequence.
2. **That the work steps are inside station 2** — the nesting is the design, and
   a transcript that lists thirteen items in a row has destroyed it.
3. **That the tracker spur has no return path.** The buffer stop is meaning, not
   decoration. A sighted reader gets "status never comes back" from the geometry;
   the transcript must state it.
4. The scope boundary: what travels with a person, what belongs to the
   repository.

**Applicable success criteria**, read from the standard rather than reprinted:
**1.1.1** — a short accessible name does not satisfy it for a complex diagram, so
the transcript is required, not optional. **1.4.1** — no station, signal, or
boundary may be distinguished by colour alone; each needs shape, label, or
position too. **1.4.3** — text inside the graphic meets the same contrast
requirement as page text, and the existing token set already provides the
text-safe accent for light backgrounds, which is a different token from the
display accent. **2.2.2** — moot, since the canvas is static.

**Hand-crafted beats generated here, and that is evidenced.** No diagram tool has
fully solved assistive-technology support for its generated SVG; hand-authored
SVG with explicit accessibility markup outperforms it. That is independent
corroboration for the owner's rejection of a Mermaid conversion.

---

## 8. Failure modes this canvas must be reviewed against

From the peer audit's compiled list. These are the review checklist at the
Validate gate.

| Failure mode | The specific risk here |
| --- | --- |
| Chartjunk | Gradient fills, shadows, or icons that index a category without encoding a relationship |
| Spaghetti wires | Connections routed behind stations or crossing each other |
| Abstraction-level mismatch | Team-level and work-step-level detail competing in one frame at equal weight |
| Metaphor inversion | Polishing the rail styling before the six trace steps are readable |
| Every-concept-in-one-panel | Adding a third level, which the two-level disclosure ceiling forbids |
| Wide-diagram mobile failure | Shipping `viewBox` scaling and calling it responsive |
| No static fallback | Working on the marketing page and stripping to nothing in `README.md` |
| Semantic void | Carrying the model with no accessible description, or hiding it like the current pipeline does |

One live dispute, resolved for this artifact: Tufte's data-ink ratio is contested
on the grounds that maximising data-ink can strip the redundant cues
accessibility needs. The position taken here — apply data-ink reasoning to
information density and cut chartjunk, but never to encoding redundancy, where
1.4.1 requires the redundant cue.

---

## 9. Open questions for the aesthetic-direction gate

1. **Does the rail metaphor survive the Identity specificity goal?** It is
   well-worn. The mitigation is that the identity comes from the buffer stop, the
   signals, and the depot nesting rather than from transit-map styling. That
   needs an owner's verdict, not a designer's assurance.
2. **Can one canvas serve four audiences?** The practitioner literature holds
   that generic collateral fails and each stakeholder needs different proof.
   Our reconciliation — the canvas is the shared model and the per-audience
   answers are entry points into it — is plausible and untested, and every source
   arguing the other way has a client-acquisition incentive.
3. **Is a raster export path in scope for the build handoff?** Rendering C needs
   one, and it is a pipeline change.

## Handoff

**To `interaction-design`:** the behaviour half — the in-component state machine
for emphasis, the
replace-at-breakpoint transition, and the disclosure transcript's open/close
behaviour. The emphasis-only rule is the hard constraint: any behaviour whose
removal loses information is out of contract.

**To `ux-writing`:** the three human-decision labels sourced from the published
path fields, the station names and remaining steps authored, the
signal questions, the one line that says the route is common rather than
mandatory, and the transcript prose. Plus the three unfurl strings, which
`content-design` scopes.

**To `creative-direction`:** the metaphor above is the amendment's subject. The
existing direction already resolved this element as a static SVG with accent on
the decision nodes; that decision is honoured, not re-litigated.

**To the build handoff:** the sanitiser probe, the raster export path, and the
requirement that presentation live in element-level attributes.

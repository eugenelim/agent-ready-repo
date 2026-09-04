---
type: canvas-composition
slug: operating-model-canvas-composition
surface: responsive-web
asset: operating-model-canvas.svg
spec: docs/design/screens/team-orientation-canvas.md
status: reference composition — not the shipped asset
carrier: dark hero band
revision: 2 — rebuilt after cold review
updated: 2026-09-04
---

# Operating-model canvas — composition record

The hand-crafted SVG is `operating-model-canvas.svg` beside this file. This
document records what it does, what was verified, the text alternative that
serves three jobs, and how it embeds in each of its three renderings.

**It is a reference composition, not the shipped asset.** Its colour literals are
resolved from the token source at `047bf0192` and must be regenerated at build
time — see the token verification's first finding for why hand-maintaining them
guarantees silent drift.

**Revision 2.** The first revision was composed on the light ground and cold
review caught that the IA places this element in the **dark hero band**, which
voided every contrast measurement taken against it. Everything below is measured
against the dark carrier. Three other blockers were fixed in the same rebuild and
are recorded in place.

## What the composition does

**The metaphor, executed:** a horizontal arc of five evenly spaced stations on the
dark hero carrier, with station two opened into an enclosure that hangs below it,
containing a **vertical** sequence of eight steps.

**The change of axis is the design.** Horizontal for what happens to a team,
vertical for what happens to one piece of work. A reader cannot lose which
lifecycle they are looking at, because the two run at ninety degrees to each
other and no caption is needed to say so. This does more work than any label and
it emerged from composing rather than from specifying.

**Rank, and how it is enforced.** The arc is primary. It gets primacy from
**position** (first in the scan path) and from **carrying the heaviest type in the
frame after the title** — 18px bold white station labels against the enclosure's
14px semibold heading and 13px steps. Revision 1 had this backwards: its
enclosure heading was heavier than every arc label, which is why the enclosure
dominated. Size still favours the enclosure because eight labelled steps need the
room; position and weight now outweigh it.

**Five human decisions are diamonds, three ordinary steps are circles.** Revision
1 drew only three diamonds and so told a reader that shaping is unsupervised
while the page's decision zone said the opposite. The two shaping decisions are
now on the drawing.

**Some steps carry more than one decision, and the legend says so.** The page
enumerates seven decision questions; the canvas shows five decision *points*. Two
questions collapse onto *An outcome you ratified* and two onto *A brief you agreed
to build from*. The legend states this rather than letting a reader infer a count.

**The tracker is one-way, and the direction is drawn rather than captioned.** A
dashed line with an arrowhead leaves the enclosure's edge — not any single step's
baseline — points at the tracker, and the line ends at a buffer stop *past* it.
Revision 1 had an undirected line with the terminus placed *before* the
destination, which read at least as easily as "the report never arrives", the
opposite of the claim.

**Scope is two labelled groups with a gap in the track**, rather than rotated
margin brackets. The gap carries the boundary and the labels are horizontal, so
they are no longer the first thing to become illegible at README width.

**Station spacing is even.** Revision 1's intervals were 320, 330, 150, 178,
which on a rail line reads as unequal distance or effort — an encoding nothing
intended. The caption also now says the spacing shows sequence rather than time.

**Zero gate codes.** Every decision is phrased as what a person does. Three of the
labels are near-verbatim from the published guide paths; the station names and the
remaining steps are authored, because no published copy exists for them.

## What was verified, and how

Not asserted. Each row is a check that could have failed.

| Check | Method | Result |
| --- | --- | --- |
| XML validity | parsed | valid |
| Survives GitHub's sanitiser | scanned for `<style>`, `class`, `style` attr, `<script>`, `<foreignObject>`, `@import`, `var(--`, SMIL — **with comments stripped first** | **0 constructs** |
| Text fits the enclosure | computed each interior label's right edge against the enclosure edge | widest 500 of 600 — fits |
| Arc labels do not collide | computed adjacent label spans at 18px | minimum gap 47px; left edge 113; right edge 1174 of 1200 |
| Station spacing is even | measured intervals | 240, 240, 240, 230 |
| Decision marks match the spec | counted diamonds | 5, as specified |
| Text contrast on the dark carrier | computed every text-on-ground pair | **11 of 11 pass** |
| Non-text contrast on the dark carrier | computed every meaningful graphical object | **8 of 8 pass** |
| It actually looks right | rendered to raster and inspected, three times | **four defects found this way** — see below |

**One methodology correction.** The first sanitiser scan reported a `<style>` and
an `@import` hit. Both were matching this file's own comment text, which
legitimately *names* the forbidden constructs. Stripping comments before scanning
is the correct method and gives zero. A scan that counts its own documentation as
a violation is a scan that cannot be trusted either way.

### Contrast on the dark hero carrier

Text, against the body-text requirement:

| Element | Ratio | Verdict |
| --- | --- | --- |
| Title, arc station labels, tracker label, decision steps | 19.34 | pass |
| Enclosure heading, decision steps on the enclosure | 18.23 | pass |
| Page caption | 12.40 | pass |
| Work steps on the enclosure | 11.68 | pass |
| Tracker sub-label, legend | 7.28 | pass |
| Enclosure sub-caption, scope group labels | 6.86 | pass |

Non-text, against the 3:1 requirement for meaningful graphical objects:

| Element | Ratio | Verdict |
| --- | --- | --- |
| Buffer stop | 19.34 | pass |
| Station rings, enclosure border | 8.07 | pass |
| Rail, spur | 7.28 | pass |
| Step rings, decision-diamond fills | 7.61 | pass |
| Interior track | 6.86 | pass |

**Zero failures.** Revision 1 had three, all in non-text contrast, all against a
carrier the IA had already ruled out.

### The role reversal the dark carrier forces

The two accent tokens swap jobs between carriers, and getting this wrong is how
revision 1 failed:

| On the light ground | On the dark carrier |
| --- | --- |
| the display accent fails as text (2.29) and as a meaningful mark (2.29) | the display accent **passes** both (8.07) — this is its documented role, "CTA fill on dark" |
| the text-safe accent passes as text (5.43) | the text-safe accent **fails** as text (3.41) |

So the canvas uses the display accent for every accent mark, and white or
composited-white neutrals for all text. That is the token file's own stated
intent; revision 1 inverted it by composing on the wrong ground.

### A token gap this exposed, correcting the token verification

The token verification concluded **zero new semantic tokens**. That conclusion
survives, but its reasoning was incomplete: it assumed the light ground.

On the dark carrier, **no dark-zone border token can carry a meaningful
graphical object.** `--ds-hero-border` measures 1.13 and `--ds-hero-border-card`
1.27, against a 3:1 requirement. Both are correctly designed as decorative
hairlines and neither is usable for a rail that carries the sequence.

The composition uses `--ds-hero-fg-muted` (7.28) for the rail, spur, and interior
track. That works and is token-backed, but its documented role is "muted /
caption on dark" — so it is being used **outside its stated intent**. The honest
finding: the dark palette has no *meaningful-rule* role, and the canvas is the
first element to need one. Still zero new tokens; one real gap, recorded rather
than papered over.

### Four defects that only rendering could find

| Revision | Defect | Why the spec could not catch it |
| --- | --- | --- |
| 1 | The enclosure dominated the arc, inverting the stated rank | The spec said the right thing; the type scale contradicted it |
| 1 | The stem struck through station two's label | A collision between two independently correct coordinates |
| 1 | The legend read as a ninth step | Correct in isolation, wrong in position |
| 2 | White text was invisible in the first raster | A preview-tool artifact, not an SVG defect — but it hid three arc labels and the whole tracker group until the preview was padded |

The last row is worth keeping because it is a trap: the render *looked* like a
defect and was not, and the way to tell was to reason about the tool rather than
edit the artifact.

## The text alternative — one artifact, three jobs

This is the ordered list that replaces the canvas below the collapse width,
serves as its accessible long description, and stands in when the graphic fails to
render.

**The nesting must survive.** The work steps are a *nested* list under station
two, never a flat run of thirteen items — a flattened list is the two-lifecycle
collapse in text form.

> **How a team takes this on.** The common route, in order. Teams skip stations
> and revisit them, and the spacing shows sequence rather than time.
>
> 1. **Evaluate**
> 2. **Prove it on real work** — what happens to one piece of work:
>
>     *Travels with you, across repositories:*
>     1. A signal arrives
>     2. **An outcome you ratified** — a person decides
>     3. **A brief you agreed to build from** — a person decides
>
>     *Lives in this repository:*
>     4. **A spec and plan you approved** — a person decides
>     5. Code past the gates and three cold reviews
>     6. **A pull request you merge** — a person decides
>     7. A deployment validated off production
>     8. **You ratify the production ship** — a person decides
>
>     Your tracker gets a report from this station, and nothing comes back from
>     the tracker into the work.
> 3. **Win buy-in**
> 4. **Roll out a cohort**
> 5. **Make it the default**
>
> Some steps carry more than one decision.

Note what the prose must state that the drawing shows: the one-way tracker
relationship. The drawing now carries direction through an arrowhead and a
terminus past the destination, so the caption reinforces rather than substitutes —
but the text alternative still has to say it, because a reader of the list has no
geometry at all.

## The three renderings

### A — inline on the marketing page

Inline SVG in the dark hero band, with an accessible name and description, and
the text alternative rendered as an on-page disclosure.

**One image, one focusable element.** The disclosure control is the component's
only tab stop. `role="img"` collapses the subtree, so there are deliberately no
focusable interior elements — see the screen brief's focus section for why the
alternative architecture was rejected. Emphasis is pointer-only and carries no
information.

### B — inside `README.md` on github.com, the binding rendering

```markdown
![How a team takes this on: five stations — Evaluate, Prove it on real work,
Win buy-in, Roll out a cohort, Make it the default — with the eight-step work
sequence nested inside the second station, five of which are points where a
person decides, and a one-way branch to your tracker.](docs/design/screens/team-orientation/operating-model-canvas.svg)
```

**Embedded as an image, and that changes the accessibility mechanism.** GitHub
strips `id`, which would break the name-and-description association — but it does
not matter, because an SVG loaded through `<img>` exposes no internals to
assistive technology at all. The alt string is the accessible name here, and the
ordered list must follow the image in Markdown to carry the long description.

**A correction to the packet's own reasoning.** Earlier artifacts said the
Markdown sanitiser is why `var()` cannot resolve. For an `<img>`-embedded SVG the
operative mechanism is different and stronger: the image is an isolated document,
so it receives **no host cascade and no page stylesheet** regardless of what the
sanitiser does. The constraint holds either way; the stated reason was wrong.
**Verification V1 is still owed** — the sanitiser behaviour is read from
documentation and needs a probe in a real README.

**What degrades here — measured at 880px, not estimated.** An earlier draft said
the 13px work-step labels become hard to read. Rendered at a real GitHub content
column, the effective sizes are:

| Element | Authored | At 880px | Legible? |
| --- | --- | --- | --- |
| Arc station labels | 18px | 13.2px | comfortably |
| Work-step labels | 13px | 9.5px | small but readable |
| Scope group labels | 10px | **7.3px** | **marginal — this is what degrades first** |

So the pessimistic claim was wrong in a useful direction: the canvas survives
README width better than stated, and **the first thing to fail is the scope group
labels, not the work steps.** The ordered list below the image carries both
regardless.

This matters because the collapse width was tied to the wrong element. Corrected
in the canvas spec.

### C — chat link unfurl

A raster export at 1200×630, the SVG's exact aspect, so the export is a direct
render with no reframing.

**The text payload does more work than the image**, because a chat client fetches
only a small prefix of the page. Those strings are in the copy deck and are
flagged there for a marketing-clarity rework — cold review found the current
title is a category statement with no reader problem in it.

## Known limits

- **The route reads as fixed.** The caption says teams skip stations and revisit
  them; the geometry does not show it. A branching arc would be worse — spaghetti
  wires are a named failure — so the caption carries it.
- **No station shows "you are here".** The direction resolved that the canvas
  shows the accumulated route rather than a position: no train, no progress state.
- **Station costs are absent from the drawing, deliberately.** No published cost
  exists for four of the five stations, and inventing one is barred. Zone 4 states
  what each station asks of a team instead, and cites durations only for the one
  station that has them.
- **The enclosure has spare width** — the widest label reaches 500 of 600.
  Tightening it further would crowd the longest step label.
- **The collapse width is not yet chosen.** It is the only guard in the state
  machine and it is owed as design intent, tied to where the 13px step labels stop
  being legible.

## Hand-off

`ux-writing` for the alt string, the preview strings, and the marketing-clarity
rework cold review asked for. The build handoff carries the generator, the raster
export, the contrast check, and V1.

---
type: creative-direction
slug: skill-html-views
surface: responsive-web
date: 2026-10-12
refined: 2026-10-16
status: selected
visual_target: none
---

# Aesthetic direction: skill-emitted HTML views

This direction covers every offline HTML file a catalogue skill emits:
- `navigate-intents`: the session-start worklist;
- `navigate-decisions`: the ADR and RFC explorer;
- `explain-diff`: a narrative explanation of a change;
- `render-proof`: a review proof of a converted document.

`markdown-to-html` output is a document an author publishes for their own readers. It keeps its author-chosen themes and is not covered by this direction.

It is one family with two densities:
- **worklist** density for navigators and explorers;
- **document** density for long prose.

The owner selected it on 2026-10-12 from three candidates, on the agent's advice, and refined it on 2026-10-16 after reviewing a prototype: soft panels for the zones, tinted state pills, and short reduced-motion-aware fades. The approved prototype is `docs/specs/intent-view-source-and-style/notes/prototype/approved-overlay.css`.

## Named goals (ranked)

1. **Scan, then act.** The eye finds the next thing and its state before anything else.
2. **Quiet surface.** Chrome recedes so content carries the page.
3. **Learned once.** Anything learned in one view works the same in every other.
4. **Every width earns its space.** Layout fills 320 to 2560px with content, not empty bands.

## Engagement mode

- **Primary mode:** operate. A maintainer decides and starts work.
- **Secondary mode:** read. `explain-diff` and `render-proof` serve the distinct job of reading a long argument through.
- **Surface genre:** workspace and analytical for the navigators; informational for documents.

## Product-specific visual thesis

- **Audience's situation:** a maintainer between agent sessions. They need to know what is open, what is broken and what to start, from records the repository already holds.
- **Distinctive mechanism:** every view is derived from the repository's own artifacts and stamped with when it was made. Nothing is stored or edited in it.
- **Honest proof:** real record counts, states, pointers and snapshot times. There are no screenshots or claims beyond what the payload holds.

## First-viewport thesis

- **Opening clarity:** what this view answers and when the snapshot was taken.
- **Exposed evidence or mechanism:** the first answer itself. In the navigator that is the work list in a startable stage; in a document, the title and its first section.
- **Primary action or continuation:** pick an item and copy its next-step prompt, or read on.

## Approved visual target

**Target:** none.

## Evidence and assets

- **Available evidence:** export payloads and snapshot times. Today's corpus has 169 intents, 24 briefs, 558 specs and 202 open items.
- **Available assets:** none. The views carry no images, fonts or icons beyond text glyphs.
- **Placeholders:** none.
- **Asset provenance:** not applicable.

## What each goal means

- **Scan, then act.** It means rows are single lines with aligned columns: name, state, context. The state is a word plus a shape, so it reads at a glance and without colour. It is violated by stacked cards, wrapping chips, or an id ahead of the name.
  - *Persona:* the returning maintainer choosing the next session's work.
  - *Precedent:* railway timetables (aligned columns and a fixed reading line), and the engineering logbook (one ruled line per entry).
  - *Standards:* WCAG 2.2 use of colour (state never by colour alone); Nielsen's recognition-over-recall heuristic.
  - *Platform conventions:* MDN responsive layout guidance for grids that reflow by width.
- **Quiet surface.** It means a light canvas holds two softly raised zones, the list and the detail, and inside them hairline rules and spacing group content. Rows, rail links and controls stay flat. One accent is spent only on links, focus and the current selection; state tints are pale and always sit behind a state word. It is violated by a shadow on every row, saturated status fills, gradients, or decorative headers.
  - *Persona:* the same maintainer, who opens these views many times a day.
  - *Precedent:* the ruled ledger page, where structure is lines and not frames.
  - *Standards:* WCAG 2.2 AA contrast in light and dark.
  - *Platform conventions:* the system light and dark preference.
- **Learned once.** It means one type scale, one state vocabulary, and one set of marks for selected, focused, broken and stale, in every view. It is violated by a view that styles state or emphasis its own way.
  - *Persona:* an adopter who meets these views through different skills.
  - *Precedent:* transit-map keys, where one key reads every line.
  - *Standards:* Nielsen's consistency-and-standards heuristic.
  - *Platform conventions:* native controls, so behaviour matches the browser.
- **Every width earns its space.** It means worklists widen into more columns and a wider detail zone. Document views keep a readable line length and use the spare width for margin heads and notes. It is violated by a centred fixed-width page with empty side bands.
  - *Persona:* a maintainer on a wide monitor or a phone.
  - *Precedent:* the technical manual's margin column.
  - *Standards:* WCAG 2.2 reflow at 320 CSS px.
  - *Platform conventions:* MDN responsive layout guidance.

## Direction sheet

| Axis | Token vocabulary | This direction commits to |
| --- | --- | --- |
| Grid grammar | see template | `[column]` `[rigid]` Worklists use fixed column tracks: rail, list and detail at wide widths, collapsing in order. Documents use one text column plus a margin column. |
| Alignment and equilibrium | see template | `[edge]` `[asymmetric]` Everything hangs from the left edge, with two alignment axes: label and value. |
| Spatial density | see template | `[dense]` In worklist density, one record per line and many lines per screen. Document density relaxes to a comfortable reading rhythm. |
| Whitespace distribution | see template | `[compact]` Tight within rows, with clear gaps only between groups. |
| Hierarchy and scale contrast | see template | `[moderate]` A small step from the page title to the section to the row, so the list stays the dominant mass. |
| Containment and boundary strength | see template | `[ruled]` `[soft-panel]` The list and the detail are each one soft panel on the canvas. Inside them, hairline rules divide rows; rows are never cards. |
| Section and scroll rhythm | see template | `[continuous]` `[regular]` One continuous list or text, with an even cadence. |
| Type voice | see template | `[sans-humanist]` The system UI sans, with tabular figures for counts. Monospace only for ids, paths and prompts. |
| Type hierarchy | see template | `[moderate]` Four levels: title, section, body and meta. |
| Chromatic intensity | see template | `[restrained]` Neutral greys plus one accent hue for links and selection. Each state has a pale tint and a text hue (violet in progress, green approved, red broken, amber stale), always paired with a word and a shape. |
| Form | see template | `[soft-rectilinear]` Small radii: 6px for chips, 8px for controls and callouts, 12px for zones. State marks are pills holding simple glyphs. |
| Material and depth | see template | `[low]` Two levels only: the zones carry one soft shadow, stronger on the detail once an item is picked; everything inside them is flat. |
| Ornament and texture | see template | `[none]` |
| Image treatment | see template | `[none]` |
| Motion character | see template | `[quiet]` Colour, border and shadow fades of 120ms on hover and selection, and a 160ms fade with a 4px rise as the detail renders, only when the reader's system allows motion. Nothing moves on scroll. |

## Signature device

**Signature device:** the ruled single-line row with an aligned state column — a word plus a shape — that reads like a timetable.

## Signature interaction

**Signature interaction:** picking a row fills the detail zone with that item's next step and a copyable prompt. It expresses the views' purpose, which is getting from orientation to action.

## Counterfactual check

**Comparator brief:** "Style an internal CI dashboard for an engineering team."

| Axis or goal | What the comparator produced | What it became | Why |
| --- | --- | --- | --- |
| Containment | Cards with shadows per item | Two soft zones holding hairline-ruled rows | Cards per item cut rows per screen and add chrome; "Scan, then act" keeps rows dense, while the two panels give the page a calm frame. |
| Chromatic intensity | Saturated red, amber and green status pills | Pale tints behind a word and a shape; one accent for links and selection | Saturated pills on every row are noisy and colour alone fails WCAG use of colour; pale tints let a state read at a glance while the word carries it. |
| Grid grammar | Modular tile grid of summary counts | Column grid with questions in a rail | Counts are answers to questions, not tiles; a rail keeps them in view while the list works. |
| Alignment | Centred, max-width page | Edge-aligned, width-filling | Centred caps left empty bands at 1680 and 2560px. |
| Type voice | Geometric sans throughout | Humanist system sans; monospace only for ids and prompts | Ids moved out of the reading line; system fonts satisfy the offline constraint. |

## Dominant goal for arbitration

**Dominant goal:** Scan, then act.

Resolved trade-offs:

- When **Scan, then act** and **Quiet surface** conflict over marking state, **Scan, then act** wins. The state mark stays visible on every row, but as a word plus a shape, not a filled pill.
- When **Learned once** and **Every width earns its space** conflict over a view-specific wide layout, **Learned once** wins. Views share zone order and marks, and only the column count varies.
- When document readability conflicts with worklist density, the view's genre decides. Document views use the reading measure, never worklist density.

## Open questions

- How the warning hue clears AA contrast in dark mode while staying distinct from the accent; `design-system` settles the values.
- `explain-diff` pages are written by a model; RFC-0108 D2 has its publisher inject the shared base as trusted bytes.

## Borrowed discipline

- **Donor candidate:** Field manual.
- **Discipline taken:** margin heads and a capped reading measure for document density. Spare width carries labels and notes beside the text instead of stretching the line.

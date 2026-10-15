---
type: creative-direction
slug: "docs-site"
surface: "responsive-web"
date: "2026-10-15"
status: "selected"
supersedes: docs/specs/docs-site-design-refresh/creative-direction.md
---

# Aesthetic direction: technical docs site (`docs-site/`)

The selection was delegated: on 2026-10-15 the owner asked the agent to choose
among four candidates and to build a preview. The owner approved the previewed
direction on 2026-10-15. This record replaces the docs-site direction in
`docs/specs/docs-site-design-refresh/creative-direction.md`; the marketing
site keeps its own records, and principle 4 in `docs/design/principles/tech-site.md`
(no shared palette or components between the two renderers) still holds.

Surface: responsive-web. Genre: documentation.

## Audience (ranked)

1. **Adopting engineer** — "When I have a job in front of me, I want the page
   for that job and the stage it belongs to, so I can act without learning the
   catalogue first." Arrives mid-task from search, a skill, or a teammate's link.
2. **Platform lead** — "When I decide whether my team adopts this, I want the
   site to look as finished as the tools I already trust." Judges by feel first.
3. **Pack author or catalogue operator** — long reading sessions in the Author,
   CLI, and Catalogue System tabs.

## Named goals (ranked)

1. **Know where you are** (dominant)
2. **Plain and quiet**
3. **One line through the work**
4. **Finished in every state**

## What each goal means

- **Know where you are** — means: every page shows its tab, its operating-model
  stage, and its place in the sidebar without the reader hunting. Violated by:
  a page whose stage you cannot name, two competing navigation bars, a sidebar
  where every entry has equal weight.
  - *Persona:* adopting engineer, mid-task.
  - *Precedent:* rail and road wayfinding (Kinneir and Calvert's UK signage) —
    take: one plain sans, plain-word labels, the line colour as the only
    identity; leave: road-sign grounds and capitals.
  - *Standards:* Nielsen information scent; Hick's law at the tab and group
    decision points.
  - *Platform conventions:* the docs-site three-column pattern (sidebar,
    content, on-this-page) readers already hold.
- **Plain and quiet** — means: nothing on the page that is not the work —
  one typeface family, no decorative rules under headings, no tinted boxes
  inside boxes. Violated by: display serifs, letter-spaced eyebrow labels,
  nested cards, accent colour on ordinary text.
  - *Persona:* platform lead (credibility skim) and the adopting engineer.
  - *Precedent:* opencode's docs intro (take: short pages, install as tabs,
    links that read as text); the best developer-tool docs (take: restraint as
    the signal of quality). Secondary references only.
  - *Standards:* Hemingway's iceberg — trust through precision, not adjectives.
  - *Platform conventions:* system-grade sans at body size; Starlight's
    built-in components restyled rather than replaced.
- **One line through the work** — means: the operating model is visible as a
  line: each stage has one colour, used only for its line, its station dot,
  and its stage chip. Violated by: stage colour on links, buttons, or
  backgrounds; more than five line colours; colour as the only cue.
  - *Persona:* adopting engineer and platform lead.
  - *Precedent:* Harry Beck's schematic rail map (take: a line per route,
    stations as dots, 90° geometry; leave: the multi-line tangle); the
    marketing site's rail-line canvas (metaphor shared, palette not).
  - *Standards:* WCAG 1.4.1 — every stage colour is paired with its stage name.
  - *Platform conventions:* the sidebar's left edge already carries a rule in
    every docs theme; the line replaces that rule.
- **Finished in every state** — means: both themes designed, focus visible,
  hover and current states on every link, reduced motion honoured. Violated
  by: an inverted-light dark theme, a missing hover state, contrast below AA.
  - *Persona:* platform lead; author on long sessions.
  - *Standards:* WCAG 2.2 AA floor, never traded.
  - *Platform conventions:* Starlight's skip link, landmarks, and Pagefind
    search are kept and restyled.

## Direction sheet

| Axis | Token vocabulary | This direction commits to |
| --- | --- | --- |
| Grid grammar | `[manuscript]` `[column]` `[modular]` `[hierarchical]` `[compound]` `[broken]` `[platform-default]`, then `[rigid]` `[relaxed]` `[platform-default]` | `[column]` `[rigid]` three tracks — sidebar, content, on-this-page — with the content measure fixed; no full-bleed sections inside docs pages |
| Alignment and equilibrium | `[edge]` `[centred]` `[baseline]` `[platform-default]`, then `[symmetric]` `[asymmetric]` `[platform-default]` | `[edge]` `[asymmetric]` everything hangs from the left edge of its column; the Intro is not centred |
| Spatial density | `[sparse]` `[comfortable]` `[dense]` `[platform-default]` | `[comfortable]` one idea per section; tables and code stay dense |
| Whitespace distribution | `[compact]` `[even]` `[expansive]` `[platform-default]` | `[even]` section gaps carry the structure instead of rules |
| Hierarchy and scale contrast | `[flat]` `[moderate]` `[steep]` `[platform-default]` | `[moderate]` the title leads clearly; H2 and H3 step down by weight more than size |
| Containment and boundary strength | `[open-field]` `[ruled]` `[panelled]` `[carded]` `[platform-default]` | `[open-field]` content sits on the ground; only code, tabs, link cards, and asides get a single hairline border |
| Section and scroll rhythm | `[continuous]` `[episodic]` `[platform-default]`, then `[regular]` `[varied]` `[platform-default]` | `[continuous]` `[regular]` long job pages read as one run with even section spacing |
| Type voice | `[serif]` `[sans-geometric]` `[sans-humanist]` `[monospace]` `[mixed]` `[platform-default]` | `[sans-humanist]` one sans for headings, body, and UI; mono only for code and commands |
| Type hierarchy | `[flat]` `[moderate]` `[dramatic]` `[platform-default]` | `[moderate]` four levels: title, H2, H3, body |
| Chromatic intensity | `[monochrome]` `[restrained]` `[saturated]` `[high-chroma]` `[platform-default]` | `[restrained]` neutral ground and ink; five stage hues spent only on the line, station dots, and stage chips |
| Form | `[rectilinear]` `[softened]` `[organic]` `[platform-default]` | `[softened]` small radii on bordered elements; round station dots |
| Material and depth | `[flat]` `[layered]` `[deep]` `[platform-default]` | `[flat]` one translucent layer: the sticky top bar |
| Ornament and texture | `[none]` `[pattern]` `[grain]` `[illustration]` `[platform-default]` | `[none]` the line is structure, not ornament |
| Image treatment | `[photographic]` `[illustrative]` `[abstract]` `[none]` `[platform-default]` | `[illustrative]` diagrams only, drawn in the line grammar |
| Motion character | `[still]` `[productive]` `[expressive]` `[platform-default]` | `[productive]` short state transitions on hover, focus, and disclosure; none under reduced motion |

## Signature device

**Signature device:** the stage line — each operating-model stage group in the
sidebar hangs from a thin vertical line in that stage's colour, the current page
is a station dot on it, and the same dot and stage name sit above the page title.

## Counterfactual check

**Comparator brief:** "Restyle a Starlight docs site to look like a modern
developer-tool docs site."

| Axis or goal | What the comparator produced | What it became | Why |
| --- | --- | --- | --- |
| Chromatic intensity | One brand accent on links, buttons, and the active sidebar item | Ink links; colour reserved for the five stage lines | The colour must carry the operating model, or it is decoration |
| Containment | Filled highlight pill on the current sidebar item | Station dot on the stage line | The current page should read as a position on a route |
| Hierarchy | Large hero on the start page | Intro is a normal page with install tabs | The reader came to install, not to be sold to |
| Know where you are | Breadcrumbs only | Stage chip above the title plus the line | A breadcrumb names the folder, not the stage of the work |

## Dominant goal for arbitration

**Dominant goal:** Know where you are.

Resolved trade-offs:

- When **Plain and quiet** and **Know where you are** conflict on adding a
  wayfinding mark (stage chip, station dot), **Know where you are** wins — one
  small mark is cheaper than a lost reader.
- When **One line through the work** and **Finished in every state** conflict
  on a stage hue that misses contrast, **Finished in every state** wins — shift
  the hue until the stage chip text clears AA.
- Stage hues never colour links, buttons, focus rings, or backgrounds.

## Open questions

- None blocking. Dark-theme stage hues are derived separately, not inverted.

## Borrowed discipline

**Donor candidate:** B, Operator's manual.

**Discipline taken:** commands are first-class — every install or CLI step is a
copyable code block with the command alone, never prose that contains a command.

## Compositional commitments

- One top bar: logo, tabs (Docs, CLI, Author, Catalogue System), then search,
  GitHub, and theme on the right. No product strip above it.
- Each tab owns its sidebar; Docs groups follow the operating-model stages.
- The page title carries a stage chip when the page belongs to a stage.

## Refinement amendment

| Axis | From | To | Why |
| --- | --- | --- | --- |

---
type: derived-screen-list
slug: team-orientation-screen-list
status: superseded-in-part
gate: approve-journey (passed 2026-09-04)
surfaces: 2
updated: 2026-09-04
---

# Derived screen list — for the approve-journey gate

The screens the two journey maps and the seam imply. This is the gate artifact,
not the full flow: `user-flow` owns the per-screen state matrix and the routing
in Define. Nothing here is designed yet — this is the list the owner approves
before design starts from it.

Each row names the journey stage that produced it, so the derivation is
checkable rather than asserted.

## The shared artifact

**C1 · The operating-model canvas.** One artifact, three renderings. It is
listed first because both surfaces depend on it and because its constraints are
the hardest in the engagement.

| Rendering | Context | Binding constraint |
| --- | --- | --- |
| C1a Interactive | marketing home, above the fold | Interaction may add emphasis only, never information |
| C1b Static SVG | `README.md` on github.com | GitHub's Markdown sanitiser strips `<style>` blocks, `class`, `id`, `<script>`, and `<foreignObject>` from SVG. Presentation must live in element-level `fill`/`stroke` attributes. No animation of any kind renders. |
| C1c Raster export | chat link unfurl (Teams, Slack) | SVG is not a valid `og:image` on any major platform. Needs a PNG at 1200×630, under 1 MB, and under 300 KB to survive WhatsApp's cap. |

C1b is the binding rendering: anything that does not survive sanitisation cannot
be part of the model's meaning. C1c makes a raster export path a build
requirement, not a design nicety.

**Derived from:** marketing journey Stages 3 and 5; documentation journey Stage 3;
seam Crossings A, B, and C.

**States to specify** — all six, because the canvas carries the model rather
than decorating it.

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

## Marketing surface

| ID | Screen / zone | Job | Derived from | New or existing |
| --- | --- | --- | --- | --- |
| M1 | Above the fold — canvas, headline, one action | Show the whole model and name the reader in one screen | Marketing Stages 1, 3 | **New structure**, replaces current hero framing |
| M2 | The problem | Give the reason before the menu | Marketing Stage 2 | Existing `TheProblem`, **relocated above** the outcome router |
| M3 | Adoption spine detail | The five stations, and what each asks of a team | Marketing Stage 5; documentation Stage 3 | **New.** Only station 2 carries durations, cited; no published cost exists for the other four. |
| M4 | Work-lifecycle detail | What happens to one piece of work, nested inside station 2 | Marketing Stage 3 | **New**, absorbs `ThreeLoops` |
| M5 | Human decisions | What each handoff asks of a person | Marketing Stage 3 | Existing `HumanGates`, **all six gate codes removed** |
| M6 | Outcome router | Recognise your work before you know pack names | Marketing Stage 2 | Existing `PackCatalogue`, **relocated below** the problem |
| M7 | Adapter trust checkpoint | Confirm my agent is supported | Marketing Stage 4 | Existing `AdapterMatrix`, unchanged — the best-built element on the page |
| M8 | Install | Give the one runnable thing | Marketing Stage 4 | Existing `InstallTerminal`, unchanged |
| M9 | Route into the ordered paths | Hand the champion the thing to give their team | Seam Crossing A; documentation Stage 1 | **New** — this is the seam fix |
| M10 | Catalogue ownership closer | Own the catalogue your team runs | Marketing Stage 5 | Existing `BuildYourOrg`, unchanged |

`StatStrip` is not in the list. Its three numbers size an install rather than
proving anything, and M1 now carries the orientation job it was doing. Whether it
is cut or re-tasked as a real proof signal is a `conversion-design` decision, not
a gate decision — flagged, not decided.

## Documentation surface

| ID | Screen / zone | Job | Derived from | New or existing |
| --- | --- | --- | --- | --- |
| D1 | Guides index — Start here | One link, one promise, above the fold | Documentation Stages 1, 2 | **New framing** of existing P1 |
| D2 | Guides index — the six ordered paths | The first-value moment, promoted to where it is found | Documentation Stage 3 | Existing content, **moved above** the pack-choosing copy |
| D3 | Guides index — prominent search | Serve a 229-page surface at its real tier | Documentation Stage 4 | **New** — current search is a header widget |
| D4 | Navigation model — job-grouped sidebar | Stop asking the reader to pick a pack | Documentation Stage 2 | **Restructure**, authored in `site.toml [[guide_groups]]` |
| D5 | Per-path landing pattern | Make one path followable end to end | Documentation Stage 3 | **New pattern**, applied to six existing paths |
| D6 | Route back to the internal case | Get from "I understand this" to "help me sell it" | Seam Crossing B | **New** — no route exists today in this direction |

**Superseded.** An earlier draft priced D4 as carrying a route-identity cost across 21 groups. The IA later established that `[[guide_groups]]` controls grouping and group labels only, and that page slugs are derived from the directory tree or from a page's own `slug:` frontmatter — so re-grouping changes **no URL** and needs no redirects. What is owed is a nav-label migration table, which the IA contains.

## Explicitly not in scope

- The pack catalogue, journey pages, and `/now/` — each needs its own review
  pass; none is in this engagement.
- `README.md` itself. C1b makes the canvas render there; restructuring the README
  is recorded as a follow-on despite being the highest-traffic surface.
- The 9 generated content files carrying gate codes (12 occurrences). Same violation, source is
  `packs/*/JOURNEY.md`.

## What the gate is being asked to approve

1. **The two current-state journey maps**, with their mixed evidence declared
   per stage rather than per map.
2. **The seam artifact** and its four falsifiable crossing invariants.
3. **This screen list** — in particular the six new items (C1, M1, M3, M4, M9,
   D1/D3/D5/D6) and the three relocations (M2, M5, M6).
4. **The dominance decision**: adoption is the spine, work is nested inside
   station 2, and they are not peer diagrams.

## Open questions the gate should settle

1. **Does `StatStrip` survive?** It has no job left once M1 carries orientation.
   Cut, or re-task as a real proof signal.
2. ~~**Is the D4 route-identity cost acceptable?**~~ **Resolved:** the cost is essentially zero — no URL changes. The real cost is different and larger: the re-grouping needs an amendment to a Shipped spec. See the IA.
3. **Is a raster export path in scope for the build handoff?** C1c needs one, and
   it is a pipeline change rather than a design artifact.

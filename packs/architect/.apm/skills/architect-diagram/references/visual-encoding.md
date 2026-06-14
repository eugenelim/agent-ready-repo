# Visual encoding — map channels to meaning, don't decorate

When a diagram distinguishes *kinds* of things or *kinds* of
relationships, every visual difference the reader sees is a claim. Pick
each channel deliberately — by what the data **is** — so the picture
reads at a glance. The opposite failure is decoration: colour and shape
that vary for no reason, which the reader still tries to decode and
can't.

This is the *encoding* lens. It rides on top of the shape and edge
tables in `references/mermaid-flowchart.md` and the consistency checks
in `references/diagram-rubric.md` — it doesn't restate them. Use it
whenever a diagram carries more than one category or dimension.

## The channels Mermaid actually gives you

Author-controllable and **robust** across enterprise wiki renderers
(GitHub, Confluence, Azure DevOps Wiki, GitLab):

| Channel | How | Best for |
| --- | --- | --- |
| **Position / direction** | `TB` vs `LR`, ordering | flow, layering, before/after |
| **Containment / grouping** | nested `subgraph` | boundaries, ownership, zones |
| **Shape** | node-shape table | the *category* of a thing |
| **Edge style** | `-->`, `-.->`, `--o`, `--x`, `===` | the *kind* of relationship |
| **Text marker / label** | emoji or word on the label | a flag (public/private), a value |

Author-controllable but **fragile** — renders inconsistently, so never
the *sole* carrier of meaning:

| Channel | Why fragile |
| --- | --- |
| **Colour** (`classDef` fill/stroke) | theming varies per renderer and breaks in grayscale / for colour-blind readers |
| **Opacity** | poorly or not supported across wiki Mermaid |

Not author-controllable in Mermaid: **size**. Node size is derived from
label length, not set by you — so "bigger = more important" isn't an
encoding you can make. Put the magnitude in the **label** ("12 nodes",
"P0") instead.

## Choose the channel by data type

| The data is… | Encode with | Not with |
| --- | --- | --- |
| **Categorical** — kind of component (service / queue / store / external) | shape, and/or grouping | colour alone |
| **Hierarchical / containment** — zones, accounts, layers | nested subgraphs, position | colour alone |
| **Ordinal / sequential** — request order, lifecycle stage | position / direction | shape |
| **Relationship type** — sync / async / read-only / failure | edge style | colour alone |
| **Boolean flag** — public/private, internal/external | text or emoji marker | colour alone |
| **Quantitative** — load, criticality, count | a **label** (Mermaid can't size nodes) | size, opacity |

## Rules

- **One channel, one meaning.** Don't make colour mean both "team that
  owns it" and "how critical it is." If you have two dimensions, spend
  two channels.
- **Reserve a channel; don't spend it on nothing.** A channel that
  carries no meaning stays at default. Varied-for-variety's-sake shape
  or colour is noise the reader still has to rule out. (This is the
  *why* behind the rubric's "pick one shape per category" check.)
- **Colour is reinforcement, never the carrier.** Encode the meaning in
  a robust channel first (shape, marker, grouping); add colour only to
  *restate* it. The diagram must read correctly in grayscale.
- **Name the encoding.** If a reader can't infer what a shape, marker,
  or colour means from context, add a one-line legend (a `%% comment`
  or a note line). An unlabelled encoding is a puzzle.

These extend, not replace, the "Styling — use sparingly" guidance in
`references/mermaid-flowchart.md`: encode meaning deliberately, and keep
everything that *isn't* meaning at the default.

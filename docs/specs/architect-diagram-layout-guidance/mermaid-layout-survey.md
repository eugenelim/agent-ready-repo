# Mermaid layout guidance — applied technique survey

> Discipline: applied (practitioner-pattern survey)

Research conducted 2026-07-17. All config properties verified against official
Mermaid schema docs (primary sources cited per section). Confidence ratings follow
GRADE applied-mode overlay (`references/confidence-schema.md`).

---

## A. Direction and rank structure

**User-facing config:** Yes — `direction` statement at diagram level or inside subgraphs.

Values: `TB` / `TD` (identical, top-to-bottom), `BT` (bottom-to-top), `LR`
(left-to-right), `RL` (right-to-left). [high, primary:
mermaid.js.org/syntax/flowchart.html]

**Sugiyama framework foundation.** Mermaid's default renderer (dagre) implements the
Sugiyama layered graph drawing method (Sugiyama et al., 1981). The `direction` keyword
selects the rank axis: `TB` places each rank on a horizontal layer flowing
top-to-bottom (containment / deployment hierarchies); `LR` places ranks on vertical
layers flowing left-to-right (pipelines, data-flows, request flows where reading
order matters). This is the single most impactful layout choice in a Mermaid flowchart.

**Subgraph direction override.** A `direction` statement as the *first* line inside a
subgraph body sets a local rank axis. [high, primary: mermaid.js.org/syntax/flowchart.html]

**Critical limitation (documented in official docs):** *"If any of a subgraph's nodes
are linked to the outside, subgraph direction will be ignored. Instead the subgraph
will inherit the direction of the parent graph."* This is irreversible from within the
subgraph. [high, primary: ibid.]

**`inheritDir`** (`config.flowchart.inheritDir`, default `false`): when `true`,
subgraphs without an explicit `direction` statement inherit the parent graph's
direction instead of using dagre's default. Useful for deeply nested subgraphs that
should flow with the parent. [moderate, primary: mermaid.js.org/config/schema-docs/
config-defs-flowchart-diagram-config.html]

**C4 direction.** Mermaid C4 diagrams have no configurable layout direction — element
ordering in the source controls approximate positioning. `Lay_U/D/L/R` directives are
listed as *unsupported* in the official C4 syntax docs. `Rel_U/D/L/R` are edge hints
only. [high, primary: mermaid.js.org/syntax/c4.html]

**Concrete guidance:** Use `TB` for hierarchy / deployment / ownership diagrams. Use
`LR` for sequential pipelines, ETL stages, CI-CD, and request flows. Put the
`direction` statement as the *first* line inside a subgraph body. Accept that any
cross-boundary edge overrules the local direction; design the subgraph to be
self-contained if direction control is important.

---

## B. Node sizing

**User-facing config:** Partial — no per-node size; sizing is always auto-derived from
label text. [high, primary: mermaid.js.org/config/schema-docs/config-defs-flowchart-diagram-config.html;
confirmed by GitHub issue #838, no implementation]

Mermaid implements the typography principle *"measure text before running layout;
derive node dimensions from actual labels"* automatically. No user override exists.
Implications: long labels widen the whole rank, not just one node; uneven label lengths
produce uneven rank heights; label consistency is a layout discipline, not just style.

Config knobs that affect node sizing:

| Property | Scope | Default | Effect |
|---|---|---|---|
| `config.flowchart.wrappingWidth` | flowchart | 200 | Max px before markdown-string label wraps |
| `config.flowchart.padding` | flowchart | 15 | Internal padding inside each node box |
| `config.flowchart.htmlLabels` | flowchart | `true` | Enable HTML-formatted labels (line breaks via `<br/>`) |
| `config.markdownAutoWrap` | global | `true` | Disable to prevent all auto-wrapping |
| `config.mindmap.maxNodeWidth` | mindmap | 200 | Hard width cap per mindmap node |

`\n` inside any label string forces a manual line break. `<br/>` works when
`htmlLabels: true`. [high, primary: mermaid.js.org/syntax/flowchart.html]

**Concrete guidance:** Keep node labels to ≤4 words or one short phrase. Labels that
run long should use `\n` for two-line form rather than trusting auto-wrap. Do not
attempt to set individual node dimensions — the engine ignores it. Use `wrappingWidth:
150` (lower than default) to force earlier wrapping when labels are naturally verbose.

---

## C. Edge routing

**User-facing config:** `curve` style and optional ELK engine.

**`curve`** (`config.flowchart.curve`, default `"basis"`): controls path interpolation
for flowchart edges. [high, primary: mermaid.js.org/syntax/flowchart.html]

| Value | Effect | Best for |
|---|---|---|
| `basis` (default) | Smooth Bézier curves | General-purpose; natural feel |
| `step` / `stepBefore` / `stepAfter` | Right-angle bends | Architecture diagrams; swimlanes; structured flows |
| `linear` | Straight lines | Simple graphs; maximum clarity |
| `monotoneX` / `monotoneY` | Monotone curves | Preserves directional flow |
| `cardinal` / `catmullRom` / `natural` | Smooth interpolations | Aesthetic preference |
| `bumpX` / `bumpY` | S-curves | Flow diagrams with alternating directions |

**Per-edge curve override** (v11+): `A --curve:step--> B` sets curve style on a single
edge without changing the diagram default. [moderate, primary: mermaid.js.org/syntax/flowchart.html]

**Dagre edge label placement:** Labels are placed at the geometric midpoint of each
edge with no `labelpos` control — equivalent to Graphviz's fixed midpoint. On dense
graphs this produces label-over-edge overlaps. [high, primary: GitHub issue #490,
#5796] ELK's routing passes handle this better.

**Invisible links** (`A ~~~ B`): zero-width force-edges used to nudge node positions
by creating a hidden dependency. Documented in official flowchart syntax. **Anti-pattern
to name and refuse:** invisible links indicate the diagram is too complex for the
layout engine; the correct response is to split the diagram, not to hack positions.
[moderate, primary: mermaid.js.org/syntax/flowchart.html]

**Concrete guidance:** Replace the default `curve: basis` with `curve: step` for
architecture and infrastructure diagrams — orthogonal bends make boundary crossings
and containment levels more legible. Use `curve: linear` for simple graphs. Never use
invisible links; the correct fix is to simplify the diagram.

---

## D. Spacing and density

### Flowchart config (`config.flowchart.*`)

| Property | Default | Effect |
|---|---|---|
| `nodeSpacing` | 50 | Between nodes on the same rank (diagram-global) |
| `rankSpacing` | 50 | Between successive ranks (diagram-global) |
| `diagramPadding` | 8 | Outer whitespace around the entire SVG |
| `padding` | 15 | Internal padding inside each node box |
| `titleTopMargin` | 25 | Space above the diagram `title:` heading |
| `subGraphTitleMargin` | `{top:0, bottom:0}` | Space above/below subgraph label text |
| `wrappingWidth` | 200 | Wrap threshold for node/edge/subgraph text |

[high, primary: mermaid.js.org/config/schema-docs/config-defs-flowchart-diagram-config.html]

**`subGraphTitleMargin.top`**: increase to 5–8 when subgraph title labels collide with
the first child node — common on dense nested diagrams. [high, primary: ibid.]

**`nodeSpacing`/`rankSpacing` placement bug:** these must be placed under the
`flowchart` key in init directives, not at top-level config. Top-level placement is
silently shadowed by flowchart-specific defaults. [high, primary: GitHub issue #7932]

### C4 config (`config.c4.*`)

| Property | Default | Effect |
|---|---|---|
| `c4ShapeInRow` | 4 | Number of shapes (Person/System/Container) packed per horizontal row |
| `c4BoundaryInRow` | 2 | Number of boundaries packed per row |
| `c4ShapeMargin` | 50 | Margin between shapes |
| `c4ShapePadding` | 20 | Padding inside shape boxes |
| `diagramMarginX` | 50 | Left/right outer margin |
| `diagramMarginY` | 10 | Top/bottom outer margin |
| `boxMargin` | 10 | Space around boundary boxes |
| `width` | 216 | Person box width |
| `height` | 60 | Person box height |

`c4ShapeInRow` and `c4BoundaryInRow` are the primary layout knobs for C4 diagrams —
they control how many elements fit on each row before wrapping, which determines the
overall diagram width vs height. Also settable inline via `UpdateLayoutConfig()`.
[high, primary: mermaid.js.org/config/schema-docs/config-defs-c4-diagram-config.html;
mermaid.js.org/syntax/c4.html]

### Mindmap config (`config.mindmap.*`)

| Property | Default | Effect |
|---|---|---|
| `padding` | 10 | Space around mindmap nodes |
| `maxNodeWidth` | 200 | Hard width cap per node |
| `layoutAlgorithm` | `"cose-bilkent"` | Layout algorithm selection |

[high, primary: mermaid.js.org/config/schema-docs/config-defs-mindmap-diagram-config.html]

---

## E. Layout engine selection

Four engines are available via the global `layout:` frontmatter key. [high, primary:
mermaid.ai/open-source/config/layouts.html]

### Dagre (default)

Implements the Sugiyama layered graph method via the dagre library. Fast; handles
small-to-medium diagrams well. No configurable routing algorithm. `curve` style is the
primary edge routing control.

Enable (explicit): `%%{init: { 'layout': 'dagre' } }%%` or `layout: dagre` in frontmatter.

### ELK (Eclipse Layout Kernel)

Advanced routing; better for large/complex diagrams with many crossings. Uses the
Brandes–Köpf (2002) coordinate-assignment algorithm (default `nodePlacementStrategy`)
which minimises edge bends and achieves more consistent placement than dagre's
barycentric method.

**Enable (preferred — Mermaid ≥ 10.5):**
```yaml
---
config:
  layout: elk
  elk:
    mergeEdges: true
    nodePlacementStrategy: LINEAR_SEGMENTS
---
flowchart LR
```

**Enable (older, still supported):**
```
%%{init: { 'layout': 'elk' } }%%
flowchart LR
```

**Complete ELK config schema** [high, primary:
mermaid.ai/open-source/config/schema-docs/config-properties-elk.html]:

| Option | Default | Values | Notes |
|---|---|---|---|
| `mergeEdges` | `false` | boolean | Consolidates parallel edges between same nodes |
| `nodePlacementStrategy` | `"BRANDES_KOEPF"` | `SIMPLE`, `NETWORK_SIMPLEX`, `LINEAR_SEGMENTS`, `BRANDES_KOEPF` | Coordinate-assignment algorithm |
| `cycleBreakingStrategy` | `"GREEDY_MODEL_ORDER"` | `GREEDY`, `DEPTH_FIRST`, `INTERACTIVE`, `MODEL_ORDER`, `GREEDY_MODEL_ORDER` | How DAG cycles are broken |
| `forceNodeModelOrder` | `false` | boolean | Enforce source declaration order |
| `considerModelOrder` | `"NODES_AND_EDGES"` | `NONE`, `NODES_AND_EDGES`, `PREFER_EDGES`, `PREFER_NODES` | Ordering scope |

`BRANDES_KOEPF`: fastest; good overall node alignment.
`LINEAR_SEGMENTS`: optimises for straight edge paths at cost of alignment.
`NETWORK_SIMPLEX`: stronger crossing minimisation; slower.

**Venue caveat — confirmed unavailable platforms** [high, primary/secondary]:
- **GitHub** — feature request open since Sep 2024; GitHub staff unresponsive; EUPL
  licensing concern raised as potential block for closed-source hosts. [secondary:
  GitHub Community Discussion #138426]
- **Quarto** — user-reported non-rendering. [secondary: quarto-dev Discussion #13736]
- **Joplin** — confirmed unavailable desktop/mobile. [secondary: Joplin Forum]
- **Obsidian (core)** — not available; community feature request open. [secondary:
  Obsidian Forum]
- **`mmdc` (Mermaid CLI)** — does NOT bundle `@mermaid-js/layout-elk`; parses the
  config but silently falls back to dagre. [high, inference from
  `@mermaid-js/layout-elk` being a separate npm package]

**Where ELK is available:** Mermaid Live Editor, Mermaid Chart platform, self-hosted
setups that explicitly register `@mermaid-js/layout-elk`.

### tidy-tree

Hierarchical, non-overlapping tree layout for mindmaps (Mermaid v9.4.0+). Uses a
non-layered tidy-tree algorithm (Reingold-Tilford family). "Automatically adjusts
spacing for readability." No user-configurable spacing parameters.

Enable (mindmap only): `layout: tidy-tree` in frontmatter.

Better than `cose-bilkent` for structured, hierarchical decomposition mindmaps.
`cose-bilkent` (force-directed) spreads organically — better for large-canvas displays.

### cose-bilkent

Compound Spring Embedder — force-directed layout. Default for mindmaps. Good for
organic spread; less predictable than tidy-tree for presentation-quality diagrams.

---

## F. Group and boundary semantics

**Subgraph containment signal:** The drawn boundary box exploits the Gestalt principle
of *common region* (Palmer 1992) — elements inside a shared enclosure are perceived as
a group regardless of spacing. `nodeSpacing`/`rankSpacing` are diagram-global;
per-subgraph spacing does not exist in Mermaid.

**Subgraph rules:**
- Only use a subgraph when the group has real semantic meaning: deployment unit,
  network zone, trust boundary, ownership boundary, lifecycle phase.
- Put `direction` as the first line inside the subgraph body (before any node declarations).
- Use `subGraphTitleMargin.top: 5` when title collides with the first child node.
- A subgraph can itself be the source or target of a flowchart edge (`A --> mySubgraph`).

**C4 boundary rules:**
- `Enterprise_Boundary`, `System_Boundary`, `Container_Boundary`, `Boundary` (generic)
  are distinct types; use the most specific one.
- Statement ordering controls approximate layout in Mermaid C4.
- `c4ShapeInRow: 4` and `c4BoundaryInRow: 2` control how many elements pack per row
  before wrapping (also adjustable inline via `UpdateLayoutConfig()`).
- Never mix C4 levels in one diagram (Context + Container + Component is three diagrams).

---

## G. Edge label quality

No enforced character limit exists. Key guidance:

- Labels should be verb phrases: `validates`, `returns token`, `on error`. "Uses",
  "calls", "reads" alone fail the structural rubric.
- Make labels **grammatical in the direction of the arrow**: "publishes events to"
  on A→B reads A publishes events to B. "reads from" on A→B reads A reads from B.
- ≤4 words as a practical limit before midpoint overlap becomes likely on dagre.
- `wrappingWidth: 200` applies to edge labels as well as node labels.
- `config.sequence.messageAlign: "center"` (default) / `"left"` / `"right"` for
  sequence diagram message labels.

If every edge in a diagram carries the same label, remove all edge labels — they add
no information.

---

## H. Typography

| Config | Default | Notes |
|---|---|---|
| `config.fontFamily` | `"trebuchet ms, verdana, arial, sans-serif"` | Global font |
| `config.fontSize` | 16 | Global font size (px) |
| `htmlLabels` | `true` | Enables HTML tags in node/edge labels |
| `config.markdownAutoWrap` | `true` | Set `false` to disable all auto-wrapping |
| `config.look` | `"default"` | `"handDrawn"` for Rough.js sketch style |

Horizontal text is the default in all Mermaid diagram types. Mermaid has no built-in
support for vertical or rotated text. Keep labels horizontal.

Do not change `fontFamily` from the default unless the render target guarantees font
availability. Use global `fontSize` to scale the whole diagram — do not set per-element
font sizes.

---

## I. Diagram scope (C4 model)

C4 model four-level hierarchy (c4model.com):

| Level | Question | Mermaid kind |
|---|---|---|
| System Context | Who interacts with the system? | `C4Context` |
| Container | What are the deployable building blocks? | `C4Container` |
| Component | What are the internal modules of one container? | `C4Component` |
| Code | How is one component implemented? | Class diagram (rarely drawn) |

Supporting diagrams: System Landscape (multiple systems), Dynamic (numbered runtime
scenario using `RelIndex`), Deployment (infrastructure mapping with `C4DeploymentView`).

**Rule:** Never mix levels in one diagram. A C4Container view spanning four systems is
a C4Context view in disguise.

---

## J. Tree and mindmap layout

Two layout algorithms available for mindmaps:

1. **`cose-bilkent`** (default) — force-directed Compound Spring Embedder. Organic
   spread; good for large-canvas exploration. No exposed spacing parameters.
2. **`layout: tidy-tree`** (v9.4.0+, Reingold-Tilford family) — deterministic tree
   layout; automatically balances branches; better for structured decomposition that
   will be read linearly.

`config.mindmap.maxNodeWidth: 200` and `config.mindmap.padding: 10` apply to both.

**Concrete guidance:** Use `layout: tidy-tree` for mindmaps that replace a numbered
list or document outline. Use `cose-bilkent` (default) for brainstorm / exploration
mindmaps displayed in a large canvas.

---

## K. What is provably NOT applicable

| Item | Status |
|---|---|
| Explicit x/y coordinates | Not exposed. GitHub issue #270 (2015, never implemented). |
| Per-node width/height | Not exposed. GitHub issue #838 (open). |
| Relative position constraints (`rank=same`) | No equivalent in Mermaid. |
| Orthogonal edge routing (`splines=ortho`) | Not exposed; ELK routing improves but doesn't expose full ortho mode. |
| Per-edge weight/priority | Not exposed (dagre supports internally, Mermaid does not pass it). |
| Force-directed layout for flowcharts | Not available; `cose-bilkent` is mindmap-only. |
| Per-subgraph spacing | Does not exist in Mermaid. |
| Interactive drag repositioning | Not applicable to static SVG output. |

---

## Known unknowns

- **Resolved:** `mmdc` v11.15.0 bundles `@mermaid-js/layout-elk@0.2.1` as a required
  dependency and renders ELK diagrams natively — it does not fall back to dagre. Confirmed
  by inspecting `@mermaid-js/mermaid-cli/package.json` and rendering a diff between ELK
  and dagre outputs for the same graph.
- **Known-unknown:** Exact `cycleBreakingStrategy` support in Mermaid v11.15.0 —
  sourced from schema page but the version where it was added is unconfirmed.
- **Known-unknown:** Whether Confluence's current Mermaid macro supports config
  frontmatter (`---` block). Closeable by: testing on a live instance.
- **Unknowable:** Exact rendering fallback behaviour (error vs silent dagre fallback)
  for ELK-specified diagrams on platforms without `@mermaid-js/layout-elk` — vendor-
  controlled and undocumented; varies per platform version.

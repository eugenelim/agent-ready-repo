# Why the architect-diagram skill works the way it does

This page is a Diátaxis *explanation* — it answers *why*, not *how*. If you
want step-by-step instructions, start with the how-to guides. If you want
syntax reference, see the `references/` files in the skill itself. This page
is for the reader who wants to understand the reasoning behind the skill's
defaults and constraints so they can make good judgment calls on diagrams the
skill doesn't cover exactly.

## Why Mermaid

Diagrams rot when they live in a separate tool from the prose that describes
them. A PowerPoint deck uploaded to a wiki quickly diverges from the code it
depicts, and nobody knows which is authoritative. Mermaid makes the diagram
source a text file that sits next to the prose — checked into the repo,
diffable, reviewable in a PR, and regeneratable.

Mermaid is specifically the right choice here because:

- **Venue breadth.** GitHub, GitLab, Confluence (with the Mermaid macro),
  Azure DevOps Wiki, Notion, and Obsidian all render it natively or with a
  minor plugin. A diagram written in Mermaid reaches every surface an
  engineering team actually uses.
- **Living diagrams.** Because the source is plain text, the diagram is
  updated when the code is updated — not when someone remembers to open a
  separate tool. Version history, blame, and PR review all apply.
- **No install for the reader.** Every venue listed above renders Mermaid
  in the browser. The reader sees a diagram, not a code block.

The trade-off is that Mermaid's layout engine is not as powerful as
dedicated tools like PlantUML, Structurizr, or draw.io. It cannot guarantee
that a complex graph will lay out elegantly. This is a deliberate trade:
portability and text-as-source are more valuable for the typical use case
than pixel-perfect layout.

## Direction defaults and the Sugiyama framework

The skill's two primary direction defaults — `flowchart TB` for hierarchies
and `flowchart LR` for flows — are grounded in how people read diagrams.

Mermaid's flowchart renderer uses **dagre**, which implements the
**Sugiyama layered graph framework** (Sugiyama et al. 1981). Sugiyama
decomposes graph layout into three stages: cycle removal, rank assignment
(which determines which layer each node sits on), and crossing minimisation
(which determines node order within a layer). The `direction TB` / `direction
LR` choice selects the rank axis — vertical or horizontal.

- **TB (top-to-bottom)** places nodes on horizontal ranks with edges
  flowing downward. This maps onto deployment hierarchies (region → VPC →
  subnet → service) and containment relationships where depth is meaningful.
  The eye moves top-down, matching how we read organisational charts.
- **LR (left-to-right)** places nodes on vertical ranks with edges flowing
  rightward. This maps onto process sequences — ETL pipelines, CI/CD stages,
  request flows — where the eye tracks left-to-right to follow the
  progression through time or transformation.

The choice is not aesthetic. It is functional: the wrong direction for a
diagram's semantic makes it harder to read even if the diagram is technically
correct.

## Layout philosophy: dagre and ELK

Mermaid's default layout engine is **dagre**, a JavaScript port of
Graphviz's directed-graph layout. Dagre implements Sugiyama using a
barycentric method for crossing minimisation and a simple coordinate
assignment for node placement. It is fast, widely supported, and embedded in
every Mermaid environment.

For complex graphs with many parallel edges or large fan-outs, dagre's
barycentric crossing minimiser can leave diagrams that look crowded. The
**ELK** (Eclipse Layout Kernel) alternative uses the **Brandes-Köpf (2002)**
coordinate-assignment algorithm, which minimises edge bends while keeping
nodes compact. The result is visually tighter graphs for complex topologies.

The skill exposes ELK via the `config: {layout: elk}` frontmatter setting,
but marks it with a venue caveat: ELK requires `@mermaid-js/layout-elk` to be
loaded by the rendering environment. `mmdc` v11+ bundles it as a required
dependency; Mermaid Live Editor and Mermaid Chart also load it. GitHub,
Quarto, Joplin, and Obsidian core do not bundle it — the diagram renders but
falls back to dagre silently. The skill's default is therefore dagre — it
works everywhere — and ELK is an opt-in for confirmed venues.

The `curve: step` orthogonal routing setting is the other major layout
lever. Smooth Bézier curves (`basis`, the default) look good for general
graphs. For architecture diagrams with nested subgraphs — cloud boundaries,
VPC subnets, service tiers — orthogonal routing (right-angle bends) aligns
edges to the grid and makes containment structure clearer. This is an
application of the **Gestalt principle of good continuation**: edges that
travel along predictable paths are easier to follow than curves that weave
through boundary boxes.

## Visual encoding

The skill assigns a specific Mermaid node shape to each *category* of
architectural element — service (rectangle), database (cylinder), queue
(subroutine), external actor (rounded rectangle), and so on. This is not
arbitrary. It applies the **Gestalt principle of similarity**: elements that
look the same are perceived as belonging to the same category. Using the same
shape for two elements that play different architectural roles confuses the
reader into thinking they are alike.

Trust boundaries are dashed (`classDef` + `stroke-dasharray`) because
dashed lines are the conventional encoding for "this is a boundary, not a
component" across architecture notations (C4, AWS architecture diagrams, TOGAF
artefacts). The dashed line signals a conceptual edge rather than a physical
one.

Subgraphs (boundary boxes) encode containment via the **Gestalt principle of
common region** (Palmer 1992): elements inside a shared enclosure are
perceived as belonging together. This is why nesting subgraphs inside-out —
region → VPC → subnet → service — works: the containment relationship is
conveyed by the visual structure itself, without needing labels to explain it.
`nodeSpacing` and `rankSpacing` are diagram-global in Mermaid; per-subgraph
spacing is not configurable. When a subgraph is too dense, the right response
is to split the diagram, not to try to coerce spacing.

**Colour is a fragile channel.** Mermaid's `classDef` fill and stroke colours
vary by renderer theme and break entirely in grayscale output or for
colour-blind readers. The skill uses colour only as reinforcement on top of a
robust primary channel — shape, grouping, or edge style — never as the sole
carrier of meaning. Use `classDef` for dashed trust-boundary borders (a
robust edge-style channel), not to colour-code service categories. The full channel-robustness reasoning lives in
`references/visual-encoding.md` in the skill source.

## Notation routing

The skill supports multiple Mermaid diagram types, each mapped to a specific
architectural question:

| Question | Notation |
| --- | --- |
| What is the deployment topology? What contains what? | `flowchart TB` |
| What is the request / data flow? What happens in what order? | `flowchart LR` or `sequenceDiagram` |
| Who talks to what system? | `C4Context` or `C4Container` |
| What are the states and transitions? | `stateDiagram-v2` |
| What are the data entities and relationships? | `erDiagram` |
| What is the hierarchical decomposition? | `mindmap` |
| What is the platform-level service graph? | `architecture-beta` |

Routing is not about using the "correct" notation in an abstract sense — it
is about matching the visual grammar of the notation to the semantic
structure of the information. A request flow expressed in a `flowchart TB`
forces the reader to read top-down through a sequence of events, which is
how no one naturally reads a flow. A `sequenceDiagram` gives the same
information in left-to-right time order with explicit actor lifelines — the
visual grammar matches the semantic.

`architecture-beta` is the skill's choice for platform-level service graphs
because it supports explicit port-based edge declarations (`service:R --> L:other`),
which give precise directional semantics that flowchart arrows lack.

## Portability constraint

Not every diagram type renders everywhere. The skill maintains a mental
venue matrix:

- **Universal** (renders in all major venues): `flowchart`, `sequenceDiagram`,
  `stateDiagram-v2`, `erDiagram`
- **Widely supported** (most modern venues, check for older wikis):
  `C4Context`, `C4Container`
- **Newer grammar** (confirm the venue first): `mindmap`, `architecture-beta`,
  `timeline`, `quadrantChart`

When the target venue is unknown, the skill defaults to the universal tier.
When a newer-grammar type offers a significant readability advantage and the
venue is known to support it, the skill offers it with the venue caveat
explicit.

The YAML frontmatter config block (`---`) and the `%%{init}%%` directive
are both supported configuration paths. Frontmatter is more readable for two
or more settings; `%%{init}%%` is the original path and is supported in
every Mermaid version. The skill uses whichever is clearer for the example —
they are equivalent in output.

## Anti-patterns register

The skill's anti-pattern rules are not stylistic preferences. Each one has a
specific failure mode it prevents:

- **Invisible links (`A ~~~ B`)** are a symptom, not a solution. They exist
  to force dagre to place nodes in a specific spatial relationship. The
  underlying problem is always that the diagram has too many nodes for the
  layout engine to place sensibly. The fix is to split the diagram.
- **Vague edge labels** (`"uses"`, `"calls"`) defeat the purpose of labeling.
  A label should communicate *what* crosses the edge — a protocol, a data
  payload, an action. Vague labels are worse than no label because they give
  the reader the false impression that the edge has been explained.
- **Shape inconsistency** — using different shapes for elements in the same
  architectural category — breaks the Gestalt similarity encoding and
  forces the reader to work out the categorisation from context instead
  of reading it from the shape.
- **Edge label overlap** is a signal to restructure. When edge labels stack
  illegibly, the diagram is encoding more connections than the visual space
  allows. The right fix is `curve: step` (orthogonal routing prevents
  label-path collisions) or a reduction in diagram scope — not smaller text.
- **One mega-diagram** violates the principle of one diagram, one question.
  A 30-node diagram cannot be taken in at a glance and therefore fails the
  primary test for a diagram: that it conveys structure faster than prose
  alone. Split by the scope sentence — the sentence that precedes the diagram
  and states what it shows — and each diagram becomes legible.

# Spec: architect-diagram — Mermaid layout guidance and skill design guide

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Contract:** none — guidance-only prose edits to skill reference files, new `.mmd`
  fixture files, a new test file, and a new Diátaxis explanation guide; no API/event/RPC surface.
- **Research grounding:** `mermaid-layout-survey.md` (this directory)

Mode: full (risk triggers: new `scripts/` directory in skill, new public-facing explanation guide,
scope change to C4 and mindmap reference files)

## Objective

Add Mermaid-native layout guidance — grounded in graph-drawing algorithm research and
visual cognitive science — to the `architect-diagram` skill's reference files. Establish
a TDD fixture suite that machine-validates the syntax of every supported diagram type.
Publish a Diátaxis *explanation* guide that explains the skill's design principles and
the research reasoning behind each choice.

The research survey (`mermaid-layout-survey.md`) is the source of truth for every
technique added. The spec below maps each research finding to a concrete AC.

### Research grounding summary

Full details in the survey. Key findings per reference file:

**`mermaid-flowchart.md` (survey §§A–E, G):**
- Sugiyama framework: `direction` keyword selects the rank axis; TB for hierarchies, LR
  for sequential flows. The *why* behind the skill's existing default.
- `curve` config (default `"basis"`) is the primary edge routing style lever —
  `step`/`stepBefore`/`stepAfter` produce orthogonal bends that make architecture
  boundaries more legible. Not currently documented anywhere in the skill.
- Subgraph `direction` override enables mixed-direction layouts; silently ignored when
  any subgraph node has an external edge (documented in official Mermaid docs, not in skill).
- `inheritDir: false` — when true, un-directed subgraphs inherit parent direction.
- `subGraphTitleMargin.top` — prevents subgraph title collision with first child node
  (common pain point, not documented).
- Spacing: `nodeSpacing`/`rankSpacing`/`diagramPadding`/`padding` under `flowchart` init
  key (known bug: top-level placement silently shadowed). All omitted from skill today.
- ELK renderer: Brandes–Köpf coordinate-assignment replaces dagre; improves edge routing
  on complex graphs. Full config including `NETWORK_SIMPLEX` and `cycleBreakingStrategy`.
  Venue caveat now confirmed platform-by-platform.
- Invisible links (`A ~~~ B`) are a positioning hack to name and refuse.
- Edge labels: grammatical in direction of arrow; ≤4 words for midpoint placement.

**`mermaid-c4.md` (survey §§D, F, I):**
- `c4ShapeInRow` and `c4BoundaryInRow` are the primary layout knobs for C4 diagrams —
  control how many elements pack per row. Not documented in skill.
- `c4ShapeMargin`/`c4ShapePadding` for spacing. Not documented.
- `UpdateLayoutConfig()` inline override. Not documented.
- C4 has *no configurable direction* — statement ordering controls layout; `Lay_*` is
  unsupported. The skill omits this caveat.

**`mermaid-mindmap.md` (survey §§D, E, J):**
- `layout: tidy-tree` (Reingold-Tilford family) is an undocumented alternative to the
  default `cose-bilkent` force-directed layout. Better for structured decomposition.
- `maxNodeWidth` and `padding` config. Not documented.

## Acceptance Criteria

### Flowchart reference — `references/mermaid-flowchart.md`

- [x] **AC1 — `curve` config section.** New section `## Edge routing — curve style`
      (or equivalent heading). Documents `curve` values with a decision table (survey
      §C): `step`/`stepBefore`/`stepAfter` recommended for architecture/infrastructure
      diagrams (orthogonal bends make boundary crossings legible); `linear` for simple
      graphs; `basis` default noted as general-purpose. Documents per-edge override
      syntax `A --curve:step--> B`. Names `curve: step` as the recommended default for
      architecture diagrams with subgraph boundaries.

- [x] **AC2 — Layout control section.** New section `## Layout control` covering:

      (a) **Subgraph direction override** — syntax `direction LR` as first line inside
      subgraph. Documents the **silent-ignore caveat** (any cross-boundary edge reverts
      the subgraph to parent direction). Working example with internal-edges-only
      subgraph.

      (b) **`inheritDir`** — when `true`, un-directed subgraphs inherit parent direction.
      Use case: ensuring nested subgraphs flow consistently without explicit `direction`
      in each.

      (c) **`subGraphTitleMargin.top`** — set to 5–8 when subgraph title collides with
      first child node. Grounded in `subGraphTitleMargin: {top:0, bottom:0}` default.

      (d) **Spacing init directives** — `nodeSpacing`, `rankSpacing`, `diagramPadding`,
      `padding` under the `flowchart` init key. Documents the **known bug**: top-level
      placement silently shadowed by flowchart defaults. Gestalt common-region note:
      containment is signaled by the subgraph boundary box; spacing is a global
      legibility lever, not a per-subgraph tool.

      (e) **Label wrapping** — `wrappingWidth` (default 200px) and `\n` for forced
      line-breaks. Grounded in text-drives-layout: label length determines node width
      in Mermaid's Sugiyama layout, so uneven lengths produce uneven rank heights.

- [x] **AC3 — ELK renderer section.** New section `## ELK renderer — for complex graphs`:

      (a) **When to reach for ELK vs dagre:** practitioner heuristic (many crossings
      on diagrams with > ~15–20 nodes; not a sourced threshold). Grounded in Brandes–Köpf
      (2002) coordinate-assignment vs dagre's barycentric method.

      (b) **Enable syntax** — config frontmatter (preferred, Mermaid ≥ 10.5) with
      `layout: elk` nested under `config:`. Older `%%{init}%%` form still supported.

      (c) **`nodePlacementStrategy`** — `BRANDES_KOEPF` (default, fastest, best
      alignment), `LINEAR_SEGMENTS` (straighter edge paths), `NETWORK_SIMPLEX` (stronger
      crossing minimisation). `mergeEdges: true` for parallel edges.

      (d) **Venue caveat** — ELK ships as a separate npm package (`@mermaid-js/layout-elk`);
      platforms must register it. Confirmed unavailable on: GitHub, Quarto, Joplin,
      Obsidian core. Confirmed available on: `mmdc` v11+ (bundled as required dependency),
      Mermaid Live Editor, Mermaid Chart platform, self-hosted installs.
      Same treatment as `architecture-beta`.

- [x] **AC4 — Anti-patterns updated.** `Common architecture pitfalls` gains:

      - **Invisible links as positioning hacks** — `A ~~~ B` creates a hidden force-edge
        to nudge layout. Named and refused: if the diagram needs position hacks, it is
        too complex; split it instead.
      - **Edge label overlap** — dagre places labels at edge midpoints with no
        repositioning control. Keep edge labels ≤4 words. Make labels grammatical in the
        direction of the arrow: "publishes events to", "reads from", not "uses" or "calls".
        ELK reduces but does not eliminate overlap.

### C4 reference — `references/mermaid-c4.md`

- [x] **AC5 — C4 layout config section.** New section `## Layout config` (or `## Adjusting
      the layout`):

      (a) **`c4ShapeInRow` and `c4BoundaryInRow`** — the primary layout knobs. `c4ShapeInRow`
      (default 4) controls how many Person/System/Container elements pack per row before
      wrapping; `c4BoundaryInRow` (default 2) controls boundary nesting. Example: set
      `c4ShapeInRow: 3` to produce a narrower diagram when elements have long labels.

      (b) **`UpdateLayoutConfig()` inline** — `UpdateLayoutConfig("c4ShapeInRow=2",
      "c4BoundaryInRow=1")` inside the diagram body overrides global config. More portable
      than `%%{init}%%` directives for C4 diagrams.

      (c) **Statement ordering controls layout** — in Mermaid C4, element declaration
      order influences approximate positioning. `Lay_U/D/L/R` directives are **not
      supported** in Mermaid C4 (`Rel_U/D/L/R` are edge hints only). Documents the
      existing caveat that direction is not configurable.

### Mindmap reference — `references/mermaid-mindmap.md`

- [x] **AC6 — Mindmap layout options section.** New section `## Layout algorithms`:

      (a) **`cose-bilkent`** (default) — Compound Spring Embedder, force-directed. Organic
      spread; less predictable; good for brainstorm / large-canvas exploration.

      (b) **`layout: tidy-tree`** (v9.4.0+) — Reingold-Tilford family; deterministic tree
      layout; automatically balances branches. Recommended when the mindmap replaces a
      numbered list or document outline, and when the output is read linearly.

      (c) **`maxNodeWidth: 200` and `padding: 10`** — the two spacing knobs available for
      both algorithms.

      Carry the rendering caveat: `tidy-tree` layout is version-dependent; test in the
      target venue before publishing.

### Fixtures and test

- [x] **AC7 — `.mmd` fixture files.** One fixture per diagram type under
      `packs/architect/.apm/skills/architect-diagram/scripts/testdata/`, covering all
      notation types and the new layout features:

      | Fixture | Demonstrates |
      |---|---|
      | `flowchart-tb.mmd` | TB hierarchy with subgraph |
      | `flowchart-lr.mmd` | LR pipeline with labeled edges |
      | `flowchart-curve-step.mmd` | `curve: step` via `%%{init}%%` (AC1) |
      | `flowchart-elk.mmd` | Config frontmatter with `layout: elk` (AC3) |
      | `flowchart-subgraph-direction.mmd` | `direction LR` with self-contained subgraph (AC2a) |
      | `flowchart-spacing.mmd` | `nodeSpacing`/`rankSpacing` under `flowchart` key (AC2d) |
      | `sequence.mmd` | sequenceDiagram with `alt`/`par`, activation bars |
      | `c4-context.mmd` | C4Context with Person, System_Ext, Rel+protocol |
      | `c4-container.mmd` | C4Container with `UpdateLayoutConfig()` (AC5b) |
      | `state.mmd` | stateDiagram-v2 with composite state and `note right of` |
      | `er.mmd` | erDiagram with cardinality, PK/FK |
      | `timeline.mmd` | timeline ≤6 periods, ≤3 events |
      | `quadrant.mmd` | quadrantChart with labeled axes and ≤8 points |
      | `mindmap-default.mmd` | mindmap with default cose-bilkent |
      | `mindmap-tidy.mmd` | mindmap with `layout: tidy-tree` (AC6b) |
      | `architecture-beta.mmd` | architecture-beta with port-based edges |

      Total: 16 fixtures (15 if `mindmap-tidy.mmd` fails to parse in mmdc — see
      Assumption 3).

- [x] **AC8 — Fixture test passes (local goal-based check).**
      `packs/architect/.apm/skills/architect-diagram/scripts/test_fixtures.py` exists.
      Parametrises over `scripts/testdata/*.mmd` via `glob`; invokes
      `mmdc -i <fixture> -o <tmp>` via subprocess; asserts exit code 0.
      Uses `shutil.which("mmdc")` and skips all cases when absent.
      Empty `parametrize` set (no `testdata/` yet) → 1 skipped item, session exits 0.

      **Scope:** syntactic validity only, not layout correctness or venue rendering.
      CI wiring is out of scope — see Boundaries.

      Run: `python -m pytest packs/architect/.apm/skills/architect-diagram/scripts/test_fixtures.py -v`

### Explanation guide

- [x] **AC9 — Explanation guide.** `guides/architect/explanation/architect-diagram-skill-design.md`
      exists. Diátaxis *explanation* type: explains *why* the skill works as it does;
      no step-by-step instructions; references (does not duplicate) the how-to guides.
      Contains the following sections, each grounded in `mermaid-layout-survey.md`:

      1. **Why Mermaid** — trade-off vs Graphviz (more layout control, no browser rendering)
         and draw.io (more visual fidelity, not plain text, not version-controlled).
         Plain-text, version-controlled, survives enterprise wiki rendering.
      2. **Why `flowchart TB` is the default** — Sugiyama rank axis: `TB` maps to
         deployment/containment hierarchies; `LR` maps to pipelines. The direction
         keyword is the single most impactful layout choice.
      3. **Layout philosophy: work with Mermaid's constraints** — no x/y coordinates,
         no per-node sizing, auto-sizing from label text, dagre as Sugiyama.
         Using ELK as a targeted escape hatch; Gestalt common-region as the containment
         signal (not spacing). Why fighting the layout engine (invisible links,
         over-long labels) produces worse results than accepting its constraints.
      4. **Why `curve: step` for architecture diagrams** — orthogonal bends make
         boundary crossings and containment levels legible; smooth curves obscure
         directionality on dense graphs.
      5. **Visual encoding principles** — the robust channels (shape, grouping,
         edge-style, position) vs the fragile channels (colour alone). Why colour is
         reinforcement-only. Grounded in `references/visual-encoding.md`.
      6. **Notation routing rationale** — one question, one diagram type. The C4
         four-level hierarchy as the decomposition model. Why mixing levels produces
         unreadable diagrams.
      7. **Enterprise wiki portability constraint** — the "survive enterprise wiki
         rendering" north star; how the venue-caveat system operationalises it (for
         `architecture-beta`, `timeline`, ELK, config frontmatter, tidy-tree layout).

- [x] **AC10 — Guide index updated.** `guides/architect/README.md` gains an
      `## Explanation` section linking to the guide with framing: "Explains *why* the
      skill's choices are designed as they are."

### Release

- [x] **AC11 — Release surface.** `packs/architect/pack.toml` and
      `.claude-plugin/plugin.json` bump from `0.11.0` to `0.12.0`;
      `.claude-plugin/marketplace.json` regenerated;
      `docs/product/changelog.md` `[Unreleased]` entry added.

## Boundaries

### Always do
- Ground every new guidance section in the survey's research finding (cite the survey
  section or the primary source).
- Apply the same venue-caveat treatment to ELK and `layout: tidy-tree` as to
  `architecture-beta` and `timeline`.
- Document the subgraph-direction silent-ignore caveat wherever the feature is mentioned.

### Ask first
- If a reference file not listed in the ACs needs a layout note to make a fixture
  meaningful.
- If CI wiring for `mmdc` is wanted alongside this change.
- If `mindmap-tidy.mmd` fails mmdc parse and the fixture count needs to drop to 15.

### Never do
- Never change `sequence`, `state`, `er`, `timeline`, `quadrant`, or `architecture-beta`
  reference prose in this change (they receive syntax coverage via fixtures only).
- Never change `visual-encoding.md`, `notation-routing.md`, or `diagram-rubric.md`.
- Never wire `mmdc` into `build-check.yml` or add a Node.js CI dependency in this PR.
- Never invent per-subgraph spacing — `nodeSpacing`/`rankSpacing` are diagram-global
  knobs; per-subgraph spacing does not exist in Mermaid.
- Never include invisible links in any fixture — they are an anti-pattern to refuse.

## Testing Strategy

- **Goal-based (AC7, AC8):** Write test harness first (empty glob → 1 skipped, exits 0);
  write each `.mmd` fixture; run passes when all 15–16 fixtures exit mmdc with code 0.
- **Goal-based (AC1–AC6, AC10, AC11):** `grep` confirms new section headings, pitfall
  text, README link, version bump.
- **Manual QA (AC9):** Guide read for Diátaxis compliance: no imperative instructions
  present; contains all seven sections from AC9; references (not duplicates) how-to guides.

## Assumptions

1. `mmdc` v11.15.0 at `/opt/homebrew/bin/mmdc` — confirmed.
2. ELK-specified fixtures parse and render via ELK in `mmdc` v11.15.0 — confirmed;
   `@mermaid-js/layout-elk@0.2.1` is bundled as a required dependency of `mermaid-cli`
   v11.15.0. The original survey §E claim that mmdc falls back to dagre was incorrect.
3. `layout: tidy-tree` in mindmap frontmatter parses in mmdc v11.15.0 — to be verified
   at Task 2. If it fails, drop `mindmap-tidy.mmd` and note it in Ask-first.
4. `scripts/testdata/` is the correct fixture location — matches `msg-to-markdown`
   convention and avoids the `evals/` reserved namespace (RFC-0037/ADR-0028).
5. C4 `UpdateLayoutConfig()` parses in mmdc — to be verified at Task 2.

## Declined patterns

- Tempted to update all Mermaid reference files with the full spacing tables —
  declining; only flowchart, C4, and mindmap have meaningful user-facing layout config.
  Sequence and state have spacing config but it is internal layout detail, not authoring
  guidance; adding it would exceed the scope of what makes diagrams better.
- Tempted to wire mmdc into CI — declining; separate structural decision, out of scope.
- Tempted to extract real embedded code snippets from reference files for fixtures —
  declining; snippets are embedded in Markdown prose, not in standalone `.mmd` files;
  extracting reliably requires a parser; new minimal files are simpler and unambiguous.
- Tempted to add `classDiagram` fixture — declining; no reference file in the skill;
  routing table calls it "rarely the right answer for architecture."

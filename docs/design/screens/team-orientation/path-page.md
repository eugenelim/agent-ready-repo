---
type: screen-flow-brief
screen: path-page
flow: team-orientation
surface: responsive-web
surface-genre: documentation
---

# Screen brief: path-page · agent-ready-repo · surface: responsive-web

# One pattern, six instances

The six existing paths each become an instance of this pattern. The pattern is
new; the content is not — every field below is already written in the guides
index today and is being given a page rather than a table row.

## Place in the whole

- **Type:** screen-brief
- Journey step(s): future-state Stage 4 (Roll out a cohort), Stage 5 (Make it the default)
- Enters from: S3 (picks a path) · S5 (a result is a path) · guide page (⚠ arrived from search with no context, routes up to its containing path)
- Exits to: guide page (follows a step) · S2 unfurl rendering (hands the path over) · S3 (⚠ from the partial state)
- Traces to outcome: a colleague can follow the sequence without the champion standing next to them
- Surface genre: documentation

## Job

Make one path followable end to end by somebody who was sent it.

## States

- **success/default:** prerequisite, audience, time cost, the ordered steps,
  first value, and the end state — which is a handoff, not a document.
- **loading:** layout preserved.
- **partial:** a path whose steps are not all written **shows what exists and
  marks what does not**, rather than hiding the path or silently listing a dead
  link. Recovery routes back to S3. This state is why the pattern earns a page:
  a table row cannot express it.
- empty / error / disabled: **not applicable.** A path always has at least its
  contract fields; a missing path is a routing error, not an empty state.
- permission/denied: not applicable — not gated.

## Data & actions

- **Shows:** the path's name and number; its prerequisite; who it is for; its
  rough time cost; its ordered steps as links; its stated first value; its end
  state; and — new — where the reader goes if they are handing this to someone
  else.
- **Actions:**
  - Open a step → guide page. Backing service: static page from the guides tree.
  - Hand the path over → S2 unfurl rendering. Backing service: link-preview
    metadata plus a raster export. **The raster export does not exist yet.**
  - ⚠ A step is unwritten → the partial state, which marks it rather than linking
    it, and offers S3 as recovery.
  - Return up → S3. Backing service: the generated guide navigation.

## Interaction & behavior

See `interaction-design` enrichment. Minimal: this is a reading surface. The one
behaviour worth specifying is how a marked-unwritten step reads and whether it is
focusable — it should be perceivable and skippable, not a focus trap on a
non-link.

## Copy

See `docs/design/content/docs-guides-index.md`. The path contract fields — prerequisite, first value, ends at — are **existing
published copy and are the source for the three human-decision labels** wherever
they appear, including on the marketing surface. They are not rewritten here.

**Narrowed after cold review.** An earlier draft called them "the canonical
register for the whole engagement, including the marketing surface", which
over-claims a *sourcing rule* into a *register crossing* — and a register
crossing is exactly what the fourth principle names as the thing most likely to
be violated while fixing the seam. The register is `docs/design/copy/brand-register.md`. `ux-writing` owns the partial-state marker and the
hand-over label only.

## Shared contract — REFERENCE, do not restate

- Design system: `docs-site/src/styles/tokens.css`.
- Aesthetic direction: `docs/specs/docs-site-design-refresh/creative-direction.md`.
- Navigation / chrome: Starlight's chrome, plus breadcrumbs showing job group and
  path.
- Quality floor: WCAG at the level this context requires · reduced-motion ·
  handle-all-states.

## Consistency invariants

- **Reuse, never reinvent:** Starlight's page frame, breadcrumbs, and pagination.
  Six instances share one pattern — a per-path bespoke layout is the failure.
- **Must stay consistent with:** S3 (which lists these paths and must not
  restate their contract fields differently), and the guide pages the steps link
  to.
- **The load-bearing invariant:** a path's *ends at* field is a human decision
  phrased in the reader's terms. Those phrasings are the source for the canvas's
  decision-point labels. Changing one here changes the canvas.
- Six instances, one pattern, and every instance handles partial. A path that
  cannot express an unwritten step will silently ship a broken sequence.

## Done

- [ ] all applicable states designed, including partial for all six instances
- [ ] every action wired to a named service
- [ ] error/edge flows route to a real screen or state
- [ ] copy in per state; contract fields taken from existing published text
- [ ] WCAG + reduced-motion honored
- [ ] uses the docs design system
- [ ] interaction/behavior section enriched
- [ ] design-review clean

### If documentation

- **Diátaxis type:** how-to at the path level — it achieves a stated goal — while
  the steps it links are a mix of tutorial, how-to, reference, and explanation.
  The path page must not absorb their content; it sequences them.
- **TTFV target:** the reader can state what the path produces and what it costs
  before following any step. For the first path this is the unresolved
  one-hour-versus-twenty-minute tension.
- **Navigation strategy:** progressive. The path is the spine; the steps are the
  spokes; breadcrumbs carry job group and path.
- **Machine-readability:** the steps are a true ordered sequence and must be
  marked up as one. The contract fields — prerequisite, audience, cost, first
  value, ends at — should carry a consistent structure across all six instances
  so they stay comparable and extractable.

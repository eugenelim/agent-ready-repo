# Spec: architect-diagram-knowledge-surfaces

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A solution architect using `architect-diagram` in **document** or **update**
mode to draw the system *as it is today* gets a diagram shaped only by what the
repo in scope reveals — the skill reads the code and the paths, but anything the
system integrates with **beyond the repo boundary** (a service it calls, the
team that owns it, the contract terms on that edge) is either guessed or left
`<unnamed>`. The skill's standing anti-pattern is exactly this: *fabricating
service or component names in document mode*. This is the diagram-side
counterpart of what `architect-design` gained in PR #297 and `architect-review`
in PR #299: design *consults* the enterprise's own knowledge to build a grounded
to-be design; review *checks* that a design was grounded; **diagram should
*consult* the enterprise's own knowledge to draw an accurate as-is diagram** —
extending "read the repo" to "read the landscape" so the boxes, arrows, and edge
labels beyond the repo boundary are grounded instead of guessed.

The lens is deliberately different from both siblings, and that difference is
the whole point. `architect-diagram` consults surfaces — like design, not like
review — but **only the descriptive current-system facets** (area 2 current
landscape, area 3 interfaces & contracts, area 4 operational reality — the 2/3/4
adjacency seam the canonical core already names), because an as-is diagram makes
no normative, advisory, historical, or anticipatory claims. And it consults them
**only in document and update mode**: design mode draws the user's *hypothetical*
(fabrication is allowed-but-flagged there, with no as-is to ground against), and
review mode routes to `architect-review`. The mechanism must be
**distribution-agnostic** (the skill ships to many IDEs/CLIs and cannot know an
adopter's knowledge topology) and **zero-cost when unused** — the reference loads
only when the mode is document/update *and* a surface is present; design mode,
review mode, and the no-surface case never load it.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Frame the reference as an **as-is-drawing consult guide scoped to the
  descriptive current-system facets** (areas 2/3/4 only) — the lens difference
  from both `architect-design` (all eight areas, to-be) and `architect-review`
  (verification, flag-don't-build) is the point of this spec.
- Reuse the **same 8-area MECE taxonomy and the modality×space axis** as the
  shared canonical core, kept **byte-identical** to the other two copies (the
  area rows; the table's `#`, `Area`, `The question it answers` columns; the
  modality×space subsection; the 2/3/4 adjacency seam), duplicating the file per
  the pack's per-skill convention.
- **Mode-scope the consult**: the conditional step fires **only** in document
  and update mode. It must **not** fire in design mode (the user's hypothetical)
  and must **not** fire in review mode (routes to `architect-review`).
- Detect knowledge surfaces **harness-agnostically** — from the tools/CLIs the
  session actually exposes — and name no concrete tool or CLI in the skill or
  reference.
- Carry the **three honesty rails recast for drawing**: (a) name what you drew
  from (the surface, or "repo only / none"); (b) a node or edge that can't be
  grounded stays `<unnamed>` or prompts a question rather than being guessed
  (strengthening the skill's existing never-fabricate-names discipline, not a
  parallel one); (c) a surface-derived edge the repo **contradicts** is flagged,
  not silently drawn over.
- Keep the `architect-diagram/SKILL.md` addition frugal (a single conditional
  step); put the substance in the progressive-disclosure reference.
- Bump the architect pack version, add a changelog entry, and run
  `make build-self` so `marketplace.json` reflects the bump.

### Ask first

- Extending the awareness to the `product-engineering` pack (a problem-space
  lens: domain, landscape, operational, in-flight) — still a deferred sibling
  after this PR.
- Introducing any declared registry, shared-config file, or `~/.agentbundle`
  lookup for knowledge surfaces.
- Any edit to `docs/CONVENTIONS.md` or `docs/CHARTER.md` (would require an RFC).

### Never do

- Ship an enterprise knowledge server, RAG index, or any retrieval *engine* —
  out of charter. We ship diagram *awareness*, not a backend.
- Read shared user-global state (`~/.agentbundle/…`) from the skill — it breaks
  skill isolation.
- Create a cross-pack or cross-skill shared artifact, or make `architect`
  depend on another pack. The reference is duplicated inside the
  `architect-diagram` skill (the rejected Route B from #297 stays rejected).
- Add a new dependency, a new module boundary, or a new top-level directory.
- Edit `architect-design/SKILL.md` or `architect-review/SKILL.md` in this PR
  (the T2 `git diff` check enforces byte-for-byte non-change).
- Fire the consult in **design** or **review** mode — the mode-scoping is the
  load-bearing constraint; firing outside document/update is a defect.
- Widen any of the **other two** references' canonical core, or let this third
  copy drift from them.
- Edit projected paths directly (this repo is self-hosting; edit `packs/…`
  source, then `make build-self`).

## Testing Strategy

- **Reference + SKILL.md content** — *goal-based check*. The artifacts are
  prose; correctness is verified by the lint/build gates (`lint-skill-spec`,
  `lint-packs`, `lint-agent-artifacts`, `validate`, `build`, the marketplace
  `pytest` suites) plus a `grep` proving no concrete tool/CLI name was
  hardcoded.
- **Canonical-core byte-identity across all three copies** — *goal-based check*.
  A `diff` scoped to the shared canonical core (the 8 area rows; the `#` /
  `Area` / `The question it answers` columns; the modality×space subsection; the
  2/3/4 adjacency seam) shows the new `architect-diagram` copy byte-identical to
  **both** the `architect-design` and `architect-review` copies. (Only the lens
  paragraph, the trigger column, and the detection/degrade framing differ.)
- **Sibling-skill non-change** — *goal-based check*. `git diff origin/main...`
  shows `architect-design/SKILL.md` and `architect-review/SKILL.md` byte-for-
  byte unchanged.
- **Marketplace drift** — *goal-based check*. `make build-self` runs clean and
  `marketplace.json` shows architect at `0.5.0`; `git status` shows no stray
  artifacts (`__pycache__`).
- **Mode-scoped consult behaviour** — *manual QA*, two halves, both recorded in
  the plan (T5). (1) A **real structural check**: `make build` projects the
  change and the projected `architect-diagram/SKILL.md` + reference are
  byte-identical to source — what an adopter install delivers. (2) A
  **decision-logic walkthrough**: an independent agent runs the new step against
  a fixed driver — a repo that names one component but integrates with an
  external service whose real name/owner/edge lives only in a (described)
  surface — across three scenarios: **(i)** document mode + surface present
  draws the surface-grounded neighbour (named, with a provenance note) instead
  of fabricating it; **(ii)** document mode + no surface marks the neighbour
  `<unnamed>` or asks rather than inventing; **(iii)** design mode + the same
  surface present does **not** trigger the consult (mode-scoping). **Harness
  limitation, stated honestly:** this session can't inject a *live* mock MCP
  knowledge tool, so per-scenario tool presence is *described* (a simulation of
  the branch logic), not a live MCP detection — the same deferred enhancement
  already tracked as `live-mock-mcp-detection-qa` in `docs/backlog.md`.

## Acceptance Criteria

- [ ] A new reference
  `packs/architect/.apm/skills/architect-diagram/references/knowledge-surfaces.md`
  exists and carries the **same 8-area MECE taxonomy** as the canonical core —
  (1) business domain & meaning, (2) current landscape, (3) interfaces &
  contracts, (4) operational reality, (5) constraints & standards, (6) patterns
  & references, (7) decisions & rationale, (8) in-flight & roadmap — with the
  table's `#`, `Area`, and `The question it answers` **columns byte-for-byte
  verbatim** (only the trigger column changes) and the modality×space MECE axis
  + the 2/3/4 adjacency seam preserved (the canonical core that does not change
  across lenses).
- [ ] The reference is framed as an **as-is-drawing consult lens scoped to the
  descriptive current-system facets**: an opening lens paragraph states the
  skill **consults surfaces to draw an accurate as-is diagram** and contrasts it
  explicitly with `architect-design` (consults all eight areas to build a to-be
  design) and `architect-review` (checks grounding, does not build). The
  reference makes clear the diagram lens turns on **areas 2/3/4 only** (the
  2/3/4 seam), since an as-is diagram makes no normative/advisory/historical/
  anticipatory claims. **All consult-framed prose is recast for this lens** — the
  trigger column and the Detection/degrade sections — so the verbatim canonical
  core is scoped to exactly the area rows + the three columns named above + the
  modality×space subsection + the 2/3/4 adjacency seam.
- [ ] The reference makes the **mode-scoping** explicit: the consult applies
  **only in document and update mode**; it does **not** apply in design mode
  (the hypothetical — fabrication allowed-but-flagged, no as-is to ground
  against) and does **not** apply in review mode (routes to `architect-review`).
- [ ] **Harness-agnostic detection** (grep- + read-verified): the reference
  describes discovering retrieval surfaces from the session's available
  tools/CLIs (tool search where the harness defers tools; the loaded tool list
  otherwise), contains **no hardcoded tool/CLI names**, and **excludes public
  web search** as an internal surface.
- [ ] **Three honesty rails, recast for drawing** (read-verified): (a)
  **name-what-you-drew-from** — the diagram states which surface it drew the
  beyond-repo topology from (or "repo only / none"); (b) **never fabricate** — a
  node or edge that can't be grounded stays `<unnamed>` or prompts a question
  rather than being guessed (this strengthens the skill's existing
  never-fabricate-names anti-pattern; it does not introduce a parallel
  discipline); (c) **a contradicted edge is flagged, not drawn over** — a
  surface-derived edge the repo contradicts is surfaced as a question/note, since
  one source is weak corroboration.
- [ ] `architect-diagram/SKILL.md` gains a single **conditional** procedure step
  that loads the reference **only when** the mode is document or update **and** a
  knowledge surface is reachable (progressive disclosure), and is skipped in
  design mode, review mode, and the no-surface case; the step names no concrete
  tool and reuses the skill's existing vocabulary (document-mode read-before-draw,
  the `<unnamed>`/never-fabricate discipline) rather than inventing a parallel
  mechanism.
- [ ] No registry, no shared-config file, no `~/.agentbundle` read, no new
  dependency, and no cross-pack/cross-skill shared artifact are introduced
  (verified by diff inspection). The reference lives wholly inside the
  `architect-diagram` skill.
- [ ] `architect-design/SKILL.md` and `architect-review/SKILL.md` are
  **byte-for-byte unchanged** (verified by `git diff origin/main...`), and the
  canonical core of all **three** `knowledge-surfaces.md` copies is byte-identical
  (re-verified, including the design-file marker widened in #299).
- [ ] The architect pack's `[pack]` version specifically (not the
  `[contract] version`, which stays `0.10`) is bumped `0.4.0 → 0.5.0` in both
  `packs/architect/pack.toml` and `packs/architect/.claude-plugin/plugin.json`.
- [ ] `docs/product/changelog.md` `[Unreleased]` has an entry describing the
  new diagram-side awareness behaviour.
- [ ] `make build-self` has been run; `marketplace.json` reflects architect
  `0.5.0`; `git status` shows no stray/untracked artifacts.
- [ ] All gates green: `lint-skill-spec`, `lint-packs`, `lint-agent-artifacts`,
  `validate`, `build`, and the marketplace `pytest` suites
  (`test_self_host_check.py`, `test_pipeline.py`).
- [ ] Mode-scoped consult QA recorded against a **fixed driver** in two halves:
  (1) **structural (real)** — projected `architect-diagram/SKILL.md` + reference
  byte-identical to source on both routes; (2) **decision-logic walkthrough** by
  an independent agent — three scenarios: document+surface draws the grounded
  neighbour (named, provenance noted) and not a fabrication; document+no-surface
  marks the neighbour `<unnamed>`/asks; design+surface does **not** trigger the
  consult. Live mock-MCP detection is *simulated* (harness limitation), already
  logged as `live-mock-mcp-detection-qa`.
- [ ] `docs/backlog.md`'s `architect-review-diagram-knowledge-surfaces` item is
  updated to record that all of `architect-design` / `architect-review` /
  `architect-diagram` have shipped, leaving only the `product-engineering`
  sibling (heading renamed/rescoped if that reads cleaner).

## Assumptions

- Technical: architect is currently `0.4.0`; bump target is `0.5.0`, with
  `[contract] version` left at `0.10` (source: `packs/architect/pack.toml:3,11`;
  `packs/architect/.claude-plugin/plugin.json:3`).
- Technical: architect is a user-scope-default pack, not projected into this
  repo's `.claude/` tree; a version bump drifts top-level `marketplace.json` (the
  aggregation at `_aggregate_marketplace` ignores the self-host filter) and
  `make build-self` refreshes it (source: `packs/architect/pack.toml:14`
  `default-scope=user`; prior sibling specs; memory).
- Technical: the SKILL.md hard lint cap is 1000 body lines (warn at 500);
  `architect-diagram/SKILL.md` is 96 lines pre-change, so a frugal few-line step
  stays far under the cap (source: `tools/lint-skill-spec.py:490`; `wc -l`).
- Technical: the architect pack duplicates references per-skill by convention (no
  cross-skill sharing), so duplicating `knowledge-surfaces.md` into
  `architect-diagram` matches the established pattern (source: prior two sibling
  PRs #297/#299; `packs/architect/.apm/skills/*/references/*.md`).
- Technical: the canonical core (8 area rows, `#`/`Area`/`question` columns,
  modality×space subsection, 2/3/4 seam) is currently byte-identical between the
  `architect-design` and `architect-review` copies (source: `diff` over both
  files, 2026-06-13).
- Technical: `architect-diagram` has four modes (design / document / review /
  update) and carries a never-fabricate-names anti-pattern in document mode that
  this surface strengthens (source:
  `packs/architect/.apm/skills/architect-diagram/SKILL.md:13-22,84-96`).
- Process: no RFC — the doctrine lives in the skill reference by the owner's
  decision, mirroring #297/#299, not in CONVENTIONS/CHARTER (source: user
  direction 2026-06-13).
- Process: changelog `[Unreleased]` is the home for user-visible skill changes
  (source: `docs/product/changelog.md`).
- Product: the lens is **consult-to-draw-accurate-as-is**, scoped to the
  descriptive current-system facets (areas 2/3/4) and to **document + update mode
  only**; design mode (hypothetical) and review mode (routes to architect-review)
  never trigger it; the `product-engineering` sibling is deferred to a separate
  PR (source: user direction 2026-06-13).

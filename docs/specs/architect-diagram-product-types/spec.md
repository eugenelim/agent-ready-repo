# Spec: architect-diagram-product-types

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

An architect using the `architect-diagram` skill can ask for three diagram
kinds the skill does not draw today — a **timeline** (roadmap, chronology,
release history), a **quadrant** (2×2 prioritization or positioning matrix),
and a **mindmap** (hierarchical decomposition / tree) — and get a correct,
intent-routed Mermaid diagram back. These join the existing structural set
(C4, sequence, state, ER, flowchart) as first-class, intent-routed options,
each with its own on-demand syntax reference and rubric checks. Because all
three are newer Mermaid grammars whose enterprise-wiki rendering is uneven,
the skill offers them with the **same rendering-support caveat it already
applies to `architecture-beta`** — the flowchart and C4 workhorses stay the
defaults. Alongside, the diagram rubric gains explicit per-type complexity
budgets so "fits one screen" is a checkable number per diagram kind, not a
single blanket node cap.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Follow the established `architect-diagram` reference pattern: one
  `references/mermaid-<kind>.md` syntax file per notation, loaded on demand
  from the `SKILL.md` procedure, mirroring the six existing `mermaid-*.md`
  files in shape and depth.
- Parse-check every Mermaid example added to a reference file with `mmdc`
  before committing (the rubric's "Renders" gate, mechanized).
- Carry the newer-grammar rendering caveat on all three new types, worded to
  match the existing `architecture-beta` treatment in `SKILL.md` and
  `notation-routing.md`.
- Bump the `architect` pack version in `pack.toml` and
  `.claude-plugin/plugin.json`, then regenerate
  `.claude-plugin/marketplace.json` by running `make build-self` (its
  `_aggregate_marketplace` step is the only regenerator of that file), and add
  a `docs/product/changelog.md` entry.

### Ask first

- Adding any diagram kind beyond the three named here (timeline, quadrant,
  mindmap) — the editorial SVG family (pyramid, venn, org-chart, layer-stack)
  is explicitly deferred to the backlog, not this spec.
- Lowering the existing universal node cap (`≤15 nodes`) or changing any
  **existing** per-type section (C4, sequence, state, ER, deployment). The
  universal sharpening this spec authorizes is **additive only** — new
  accent-count and edge-count sub-caps alongside the unchanged `≤15 nodes`.
- Making any of the three new types a routing **default** over flowchart/C4.

### Never do

- Add a new runtime dependency, new module boundary, or new top-level
  directory — this is prose + reference-file additions inside an existing
  skill, nothing structural.
- Introduce an SVG/HTML diagram output path — the skill stays Mermaid-only in
  this spec (SVG is the backlog item).
- Ship a reference-file example that `mmdc` cannot parse.
- Silently drop or rewrite existing routing rows, rubric sections, or the
  `architecture-beta` caveat while editing.

## Testing Strategy

- **Reference-file Mermaid examples: goal-based check**, exercised by the
  repo's existing block-extractor —
  `python packs/converters/.apm/skills/mermaid-renderer/scripts/render_mermaid.py
  --input <ref.md> --output-dir /tmp/mmcheck` — run once per new reference
  file; it extracts every fenced Mermaid block and renders each via `mmdc`
  (11.15.0 confirmed locally), exiting non-zero on any parse failure. This is
  the rubric's "Renders" bar made a rerunnable one-liner; a block that fails to
  parse fails the task.
- **Routing + rubric + SKILL.md prose wiring: goal-based check**, exercised by
  `grep` assertions that the new kinds appear in the intent→notation table,
  the SKILL.md reference-load step, the frontmatter description, and the
  rubric — plus `make lint-packs`, `agentbundle validate`, `make build`, and
  the projected-artifact lint (`tools/lint-agent-artifacts.py`) all green.
- **Skill behaves correctly end-to-end: manual QA** — the skill is a
  user-invoked artifact, so exercise its documented happy path: given a
  roadmap / prioritization / decomposition ask, confirm the routing table
  selects timeline / quadrant / mindmap respectively and the drafted diagram
  parses. Record the observed routing decision and the parsed output.

## Acceptance Criteria

- [x] Given a "show me the roadmap / timeline / release history" ask, the
  `notation-routing.md` decision table routes to `timeline`, and a
  `references/mermaid-timeline.md` syntax reference exists and its examples
  parse under `mmdc`.
- [x] Given a "prioritize / 2×2 / effort-vs-impact / positioning" ask, the
  decision table routes to `quadrantChart`, and a
  `references/mermaid-quadrant.md` reference exists and its examples parse
  under `mmdc`.
- [x] Given a "decompose / break down / hierarchy / mind map" ask, the
  decision table routes to `mindmap`, and a `references/mermaid-mindmap.md`
  reference exists and its examples parse under `mmdc`.
- [x] `SKILL.md`'s on-demand reference-load step (the one currently listing
  `mermaid-{flowchart,sequence,c4,state,er}.md`) also loads the three new
  `mermaid-*.md` references for the matching notation, and the frontmatter
  `description` names timeline, quadrant, and mindmap among the produced
  diagram types.
- [x] All three new types carry a rendering-support caveat matching the
  existing `architecture-beta` treatment (offered as an option contingent on
  renderer support, never the default); the flowchart/C4 defaults are
  unchanged.
- [x] `diagram-rubric.md` gains a per-type complexity budget for each of the
  three new types (timeline events, quadrant points, mindmap depth/branches)
  **and** an additive universal sharpening — new `accent`-count and
  `edge`-count sub-caps added alongside the **unchanged** `≤15 nodes` cap —
  while every pre-existing rubric section (Universal, Structural, Sequence,
  State, ER, Deployment, cloud, agentic) is retained unchanged.
- [x] `architect` pack version reads `0.10.0` in `pack.toml`,
  `.claude-plugin/plugin.json`, and `.claude-plugin/marketplace.json`, and
  `docs/product/changelog.md` carries an entry that names the pack distinctly
  (`architect 0.10.0`, not conflated with the unrelated `agentbundle` CLI
  entry already under `[Unreleased]`).
- [x] The pack gates pass: `make lint-packs`, `agentbundle validate`, and
  `make build-self` (regenerating `.claude-plugin/marketplace.json` with no
  residual drift), plus `tools/lint-agent-artifacts.py` on the projected
  artifacts. architect is a pure-markdown pack with no pack-owned pytest —
  the `mmdc` parse (above) is the behavioral gate, not a Python test suite.
- [x] The SVG / editorial-diagram distribution path is recorded as an open
  item in `docs/backlog.md` for a future RFC.

## Assumptions

- Technical: `architect` pack is v0.9.0, contract 0.10, user-scope-default
  (source: `packs/architect/pack.toml`).
- Technical: `architect-diagram` routes intent in `references/notation-routing.md`
  and loads per-notation `references/mermaid-*.md` on demand from `SKILL.md`
  step 4 (source: `packs/architect/.apm/skills/architect-diagram/SKILL.md`,
  `references/notation-routing.md`).
- Technical: `timeline`, `quadrantChart`, and `mindmap` parse under Mermaid
  11.15.0 via local `mmdc` (source: probe — three minimal examples rendered to
  SVG, 2026-06-30).
- Technical: the `architect` pack version is carried in `pack.toml` and
  `.claude-plugin/plugin.json` (both 0.9.0); `.claude-plugin/marketplace.json`
  (also 0.9.0) is regenerated from those by `make build-self`'s
  `_aggregate_marketplace` step — there is no repo-root `marketplace.json`
  (source: those files + `packages/agentbundle/agentbundle/build/self_host.py`).
- Process: user-visible skill/agent prose changes need a
  `docs/product/changelog.md` entry and a pack version bump in the same PR
  (source: `docs/CONVENTIONS.md`; project convention).
- Design: newer Mermaid grammars are offered with a renderer-support caveat
  rather than defaulted, mirroring the skill's existing `architecture-beta`
  handling (source: existing `SKILL.md` anti-pattern + step 6; user direction
  "do A", 2026-06-30).

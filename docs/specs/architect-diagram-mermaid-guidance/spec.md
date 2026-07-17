# Spec: architect-diagram — portable Mermaid guidance

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Contract:** none — guidance-only prose edits to skill reference files; no API/event/RPC surface.

Mode: light (no risk trigger fired)

## Objective

Improve `architect-diagram`'s Mermaid guidance with three portable,
Mermaid-native additions, and explicitly reject three renderer-proprietary
conventions that were proposed (`:::external`, `label|tech`, `%% title:`) —
they no-op or break in stock Mermaid (GitHub, Confluence, `mmdc`, and the
repo's own `render-proof` / `markdown-to-html` CDN renderers), contradicting
the skill's "survive enterprise wiki rendering" north star.

## Acceptance Criteria

- [x] **AC1 — pipeline/data-flow orientation.** `references/mermaid-flowchart.md`
      and `references/notation-routing.md` name `flowchart LR` for
      pipeline / ETL / CI-CD / data-flow diagrams where left-to-right reading
      order matters (strengthening the existing "best for request flows" text,
      not duplicating it).
- [x] **AC2 — portable title mechanism.** `references/mermaid-flowchart.md`
      documents the Mermaid config-frontmatter `title:` as the in-diagram title
      mechanism (v10.5+), and `references/diagram-rubric.md`'s universal
      "Title or scope sentence" bullet references it. The prose scope-sentence
      baseline stays the always-portable option; the frontmatter title carries
      the same venue-caveat the skill applies to other version-dependent
      features.
- [x] **AC3 — accessibility metadata.** `references/mermaid-flowchart.md`
      documents `accTitle` / `accDescr` for screen-reader accessibility, noting
      it applies across diagram types, and `references/diagram-rubric.md` carries
      a universal accessibility check gated on the target venue exposing it.
- [x] **AC4 — examples parse.** Every new Mermaid snippet parses under `mmdc`.
- [x] **AC5 — release surface.** `packs/architect/pack.toml` and
      `.claude-plugin/plugin.json` bump to `0.11.0`; `.claude-plugin/marketplace.json`
      regenerated to match; `docs/product/changelog.md [Unreleased]` gains an entry.

## Boundaries

Out of scope: adding the rejected conventions; a label-escaping pitfalls
section (belongs to a later change if wanted); editing the sequence / state /
er / c4 syntax references (title + a11y documented once in the flowchart ref
with a cross-type note); any change to the renderers themselves.

## Testing Strategy

Goal-based: `grep` the new guidance is present; `mmdc` parses each new snippet;
`python .claude/skills/work-loop/scripts/lint-spec-status.py --root .` clean.

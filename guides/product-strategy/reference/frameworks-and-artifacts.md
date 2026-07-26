# Reference: frameworks and artifacts

Every `product-strategy` skill, the framework it applies, and the artifact it
writes. All artifacts commit to `docs/product/shaping/` by default. The base path
is configurable through the `[product-strategy]` section of the repo's
`agentbundle-layout.toml`.

The tables below are grouped by pillar. Every row follows the same structure:
skill name, framework, artifact filename, output path.

## Pillar 1 — Market and competitive strategy

Seven skills.

| Skill | Framework | Artifact | Output path |
| --- | --- | --- | --- |
| `run-swot` | SWOT — Strengths, Weaknesses, Opportunities, Threats | `swot-analysis.md` | `docs/product/shaping/` |
| `run-porters-five-forces` | Porter's Five Forces — Supplier Power, Buyer Power, New Entrants, Substitutes, Rivalry | `competitive-landscape.md` | `docs/product/shaping/` |
| `run-pestle-analysis` | PESTLE — Political, Economic, Social, Technological, Legal, Environmental | `macro-environment.md` | `docs/product/shaping/` |
| `run-bcg-matrix` | BCG Matrix — Stars, Cash Cows, Question Marks, Dogs | `portfolio-position.md` | `docs/product/shaping/` |
| `run-okr-cascade` | OKR cascade — company → team → shaping-queue gaps | `okr-cascade.md` plus `workspace.toml` entries | `docs/product/shaping/` (and `workspace.toml`) |
| `write-prfaq` | PRFAQ — press release plus FAQ as altitude-0 forcing function | `prfaq.md` | `docs/product/shaping/` |
| `synthesize-stakeholder-research` | Research synthesis — strategic narrative by theme across stakeholder groups | `stakeholder-synthesis.md` | `docs/product/shaping/` |

`run-okr-cascade` writes two outputs: the `okr-cascade.md` artifact, and
`{type = "strategy"}` entries appended to `["ini-NNN".shaping_queue].backlog` in
`workspace.toml`.

## Pillar 2 — UX strategy

One skill.

| Skill | Frameworks | Artifact | Output path |
| --- | --- | --- | --- |
| `define-ux-strategy` | NN/g three-layer model · Jaime Levy four tenets · Gothelf/Seiden OKR-linked UX framing | `ux-strategy.md` | `docs/product/shaping/` |

## Pillar 3 — Content strategy

One skill.

| Skill | Framework | Artifact | Output path |
| --- | --- | --- | --- |
| `define-content-strategy` | Halvorson content strategy quad — Purpose + Process + Structure + Governance | `content-strategy.md` | `docs/product/shaping/` |

## Output path configuration

All artifacts default to `docs/product/shaping/`. The base path is set through the
`[product-strategy]` section of the repo's `agentbundle-layout.toml`, which is
adopter-owned and not shipped with the pack. Each skill documents the layout
contract in its own `references/agentbundle-layout.md`.

## Scope exclusions

The following are not part of this pack:

| Excluded | Where it belongs |
| --- | --- |
| Growth strategy — AARRR, product-led growth, PMF testing | A follow-on `growth` pack |
| Primary research production — interview guides, discussion scripts, survey templates | Upstream of `synthesize-stakeholder-research`, which consumes desk-research outputs |
| Per-surface content design | The `content-design` skill in the experience-design pack |
| Analytics and CRO tooling | Downstream of strategy |

## See also

- [Run a market and competitive analysis](../how-to/run-a-market-and-competitive-analysis.md) — using the Pillar-1 analysis frameworks.
- [Cascade OKRs into the shaping queue](../how-to/cascade-okrs-into-the-shaping-queue.md) — the Pillar-1 forcing functions.
- [Set UX and content strategy](../how-to/set-ux-and-content-strategy.md) — the Pillar-2 and Pillar-3 skills.
- [Why strategy is its own seat](../explanation/why-strategy-is-its-own-seat.md) — how the pillars fit together.

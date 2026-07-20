# product-strategy

The strategy seat upstream of product engineering and experience design. Installed to **user scope** so the skills travel across every workspace.

## Three pillars

**Pillar 1 — Market & competitive strategy** (7 skills): canonical frameworks that turn a market situation into committed artifacts in `docs/product/shaping/`. The OKR cascade feeds strategy-gap entries directly into the PE pack's `frame-situation` shaping queue.

| Skill | Framework | Artifact |
|---|---|---|
| `run-swot` | SWOT — Strengths, Weaknesses, Opportunities, Threats | `swot-analysis.md` |
| `run-porters-five-forces` | Porter's Five Forces — Supplier Power, Buyer Power, New Entrants, Substitutes, Rivalry | `competitive-landscape.md` |
| `run-pestle-analysis` | PESTLE — Political, Economic, Social, Technological, Legal, Environmental | `macro-environment.md` |
| `run-bcg-matrix` | BCG Matrix — Stars, Cash Cows, Question Marks, Dogs | `portfolio-position.md` |
| `run-okr-cascade` | OKR cascade — company → team → shaping-queue gaps | `okr-cascade.md` + `workspace.toml` entries |
| `write-prfaq` | PRFAQ — press release + FAQ as altitude-0 forcing function | `prfaq.md` |
| `synthesize-stakeholder-research` | Research synthesis — strategic narrative by theme across stakeholder groups | `stakeholder-synthesis.md` |

**Pillar 2 — UX strategy** (1 skill): sets the experience vision, goals/measures, and plan before design begins.

| Skill | Frameworks | Artifact |
|---|---|---|
| `define-ux-strategy` | NN/g three-layer model · Jaime Levy four tenets · Gothelf/Seiden OKR-linked UX framing | `ux-strategy.md` |

**Pillar 3 — Content strategy** (1 skill): the organizational/governance layer above per-surface content design.

| Skill | Framework | Artifact |
|---|---|---|
| `define-content-strategy` | Halvorson content strategy quad — Purpose + Process + Structure + Governance | `content-strategy.md` |

## Pack chain position

```
product-strategy (this pack)
        ↓                          ↓                      ↓
product-engineering          experience-design        content-design skill
(product-vision intent)  (journey → screen → services)  (experience-design)
```

`run-okr-cascade` → writes `{type = "strategy"}` gaps → `["ini-NNN".shaping_queue].backlog` in `workspace.toml` → PE pack's `frame-situation` reads them.

## Install

Default scope is **user** — installed under `~/.claude/skills/` (or your adapter's equivalent) so the skills load in every workspace.

```bash
agentbundle install product-strategy     # CLI route
```

Or via your adapter's plugin marketplace UI.

## What is NOT in this pack

- **Growth strategy** — AARRR, product-led growth, PMF testing; deferred to a follow-on `growth` pack (RFC-0063 OQ1)
- **Primary research production** — no interview guides, discussion scripts, or survey templates; `synthesize-stakeholder-research` consumes desk-research pack outputs
- **Per-surface content design** — that is the `content-design` skill in the experience-design pack; this pack covers the organizational/governance layer only
- **Analytics or CRO tooling** — measurement and experimentation belong downstream of strategy

## Artifact output path

All artifacts commit to `docs/product/shaping/` by default. Configure the base path via the `[product-strategy]` section in your repo's `agentbundle-layout.toml` (adopter-owned; never shipped with this pack — see each skill's `references/agentbundle-layout.md`).

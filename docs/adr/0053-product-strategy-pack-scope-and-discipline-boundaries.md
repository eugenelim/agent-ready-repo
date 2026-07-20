# ADR-0053: product-strategy pack — scope and discipline boundaries

- **Status:** Accepted
- **Date:** 2026-07-19
- **Decision-makers:** eugenelim
- **Supersedes:** none
- **Related:** RFC-0063 (driving RFC — D1–D10); RFC-0030 (product-engineering pack); RFC-0050 (experience-design pack); RFC-0062 (content-design and copy-direction — deferred content strategy to this pack); RFC-0004 (Rail A user-scope); ADR-0024 (pure-markdown guardrail extended by analogy); ADR-0030 (consolidated-pack-layout)

## Decision summary

- **Decision:** Create the `product-strategy` pack — a new, user-scope, pure-markdown pack housing the upstream strategy disciplines that sit above both the experience-design pack (which starts at journey mapping) and the product-engineering pack (which starts at product-vision intent).
- **Because:** The catalogue had no skills for the upstream work a strategist does before design and engineering begin: competitive landscape scanning, OKR alignment, PRFAQ authoring, UX strategy direction-setting, and content governance. Both RFC-0030 and RFC-0050 assumed this context already exists; this ADR creates the pack that produces it.
- **Applies to:** the `packs/product-strategy/` directory, its 9 skills, and the cross-pack routing contract between `run-okr-cascade` and the PE pack's `frame-situation`.
- **Tradeoff accepted:** `product-strategy` shadows the same-named intent level in `product-engineering` (`product-strategy` is both a pack name and an intent level in PE). The pack name was confirmed (D1) as clearer to strategists than alternatives (`strategy`, `market-strategy`); the shadowing is a vocabulary overlap, not a functional conflict — the two pack namespaces are independent.
- **Revisit if:** the growth-strategy or experience-mapping follow-ons (OQ1, OQ2 — see below) are ready to resolve, or if the `product-strategy` intent level in PE is renamed.

## Context

RFC-0063 (opened 2026-07-18, accepted 2026-07-19) identified a catalogue gap: the experience-design pack starts at journey mapping, and the product-engineering pack starts at product-vision intent, but neither covers the upstream strategy work that precedes both. Building the platform site (2026-07-01) and drafting RFC-0062 (content strategy deferred) both surfaced this gap. The resolution is a dedicated pack for strategist-role disciplines.

## The ten decisions (D1–D10)

**D1 — Create a `product-strategy` pack.** The disciplines are strategist-role work distinct from designer and engineer roles; a separate pack keeps the existing packs coherent. Confirmed: the name `product-strategy` shadows the PE intent level but is clearer to practitioners than alternatives.

**D2 — Market strategy and UX strategy as the two foundational pillars.** Both sit clearly upstream of product-engineering and experience-design; both have canonical discipline definitions and artifact chains.

**D3 — Content strategy as a third pillar.** Content strategy (Halvorson quad: Purpose + Process + Structure + Governance) is a planning/governance discipline distinct from content-design (per-surface design work). RFC-0062 explicitly deferred content strategy to this pack.

**D4 — Growth strategy deferred (OQ1 resolved as deferred).** Growth strategy (AARRR, PLG, PMF testing) has a distinct operational character — measurement, experimentation, activation loops — that warrants a separate `growth` pack. V1 excludes it.

**D5 — Seven Pillar-1 skills in v1.** `run-swot`, `run-porters-five-forces`, `run-pestle-analysis`, `run-bcg-matrix`, `run-okr-cascade`, `write-prfaq`, `synthesize-stakeholder-research`. All are canonical frameworks with clear artifact types and distinct elicitation triggers.

**D6 — UX strategy as a single compositing skill (`define-ux-strategy`).** The NN/g three-layer model, Jaime Levy's four-tenets framework, and Gothelf/Seiden OKR-linked UX framing are complementary lenses on one artifact (`ux-strategy.md`), not competing skills.

**D7 — Content strategy as a single skill (`define-content-strategy`).** The Halvorson quad is the canonical framework; one skill produces the organizational governance artifact that content-design and experience-design consume downstream.

**D8 — `synthesize-stakeholder-research` as a Pillar-1 capstone.** Stakeholder perspectives (executive, user, regulator) are market intelligence inputs; their synthesis produces strategic direction artifacts. The skill consumes desk-research pack outputs and does not produce primary research.

**D9 — OKR cascade → `frame-situation` routing contract: agent-mediated, shaping queue as handoff.** No mechanical cross-pack call avoids tight coupling; the shaping queue survives session boundaries. Gaps are written as `{slug = "<gap-slug>", type = "strategy"}` entries (no `needs` field) to the active initiative's `["ini-NNN".shaping_queue].backlog` in `workspace.toml`. `check-workspace` routes `{type = "strategy"}` entries to `frame-situation` (PE pack — M2) or `frame-intent` as interim.

**D10 — Market intelligence as a named concept, not a separate skill.** The accumulated committed outputs of `run-pestle-analysis` + `run-porters-five-forces` + `synthesize-stakeholder-research` constitute "market intelligence" in `docs/product/shaping/`. A separate skill would duplicate the three analysis skills.

## Cross-pack routing contract

`run-okr-cascade` writes OKR gaps to `workspace.toml`; the PE pack's `frame-situation` reads them. The contract is agent-mediated — neither pack calls the other directly. Full contract detail: `packs/product-strategy/.apm/skills/run-okr-cascade/references/cross-pack-routing.md`.

`check-workspace` (core pack) was updated (2026-07-19) to route `{type = "strategy"}` entries to `frame-situation` / `frame-intent` at both the output template (line 65) and the routing table (line 98).

## Growth strategy deferral (OQ1)

Growth strategy — AARRR metrics, product-led growth loops, PMF testing frameworks — has a distinct operational character (measurement, experimentation, activation) that warrants its own `growth` pack. It is not a Pillar-1 extension of market strategy. Deferred via `backlog.md` entry `growth-strategy-pack`.

## Experience mapping deferral (OQ2)

Experience mapping is closer in character to journey-mapping (experience-design pack) than to the upstream strategy skills here. Deferred to a follow-on RFC extending RFC-0050/RFC-0066 via `backlog.md` entry `experience-mapping-extension`.

## Consequences

- A new top-level pack directory (`packs/product-strategy/`) is created — approved by RFC-0063.
- The existing `product-engineering` and `experience-design` packs receive cross-reference notes but no functional change.
- `check-workspace` (core pack) receives a two-line routing update.
- `docs/backlog.md` receives two new open entries (growth-strategy-pack, experience-mapping-extension) and one resolved thread (content-strategy in content-strategy-and-marketing-copy-lens).

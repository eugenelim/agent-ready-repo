# RFC-0063: product-strategy pack

- **Status:** Draft
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-18
- **Date closed:**
- **Decision weight:** light
- **Related:** RFC-0030 (the product-engineering pack), RFC-0043 (the product rung above capability), RFC-0050 (the experience pack), RFC-0062 (content-design and copy-direction — deferred UX strategy and content strategy here; that RFC referred to this pack as `product-strategist` before the rename; reconciliation note in Follow-on), backlog `content-strategy-and-marketing-copy-lens`

## Reviewer brief

- **Decision:** Create a `product-strategy` pack — a new, user-scope, pure-markdown pack housing the upstream strategy disciplines that sit above both the experience pack (which starts at journey mapping) and the product-engineering pack (which starts at product-vision intent).
- **Recommended outcome:** Accept — create the pack name, scope, and discipline taxonomy; defer individual skill specs to follow-on work.
- **Change if accepted:** A new `packs/product-strategy/` directory scaffolded; `docs/rfc/README.md` updated; backlog items cross-referenced.
- **Affected surface:** New top-level pack directory (requires `AGENTS.md` approval per convention — this RFC is that approval).
- **Stakes:** Reversible — pack directory is additive; no existing pack changes behavior.
- **Review focus:** (1) Whether the discipline taxonomy (market strategy, UX strategy, content strategy — growth strategy deferred to OQ1 below) is correctly partitioned across this pack and the existing ones. (2) Whether growth strategy belongs here or in a separate `growth` pack.
- **Not in scope:** Individual skill specs (those land in follow-on RFCs per discipline); the product-engineering pack's existing rungs (`product-vision`, `product-strategy` at the intent level); the experience pack's existing skills.

## The ask

**Recommendation (BLUF — bottom line up front):** Create a `product-strategy` pack to house the upstream strategy disciplines — market/competitive strategy, UX strategy, and content strategy — that the current catalogue has no home for, with growth strategy and experience mapping as open questions (OQ1 and OQ2 below).

**Why now (SCQA — Situation, Complication, Question, Answer):** The experience pack starts at journey mapping and the product-engineering pack starts at product-vision intent. Both assume the upstream strategic context — who is the target market, what is the competitive position, what is the experience strategy, what is the content strategy — has already been resolved. Building the platform site (2026-07-01) and drafting RFC-0062 both surfaced this gap: the missing layer is not a skill in an existing pack but a strategist-role discipline set that precedes design and engineering entirely. The question is: what disciplines belong in this pack and how do they partition against what the existing packs already cover?

**Decisions requested:**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
|---|---|---|---|---|---|
| D1 | Create a `product-strategy` pack as the home for upstream strategy disciplines? | Yes | Disciplines are strategist-role work, not designer- or engineer-role work; a separate pack keeps the existing packs coherent | This review | Confirm or rename — note: `product-strategy` shadows the same-named intent level in `product-engineering`; justify the reuse or propose a distinct name (e.g. `strategy` or `market-strategy`) |
| D2 | Should the pack cover market/competitive strategy (competitive positioning, go-to-market (GTM), product-market fit) and UX strategy (Nielsen Norman Group (NN/g) vision + goals/measures + plan model) as the two primary pillars? | Yes — these two pillars as v1 scope | Both sit clearly upstream of product-engineering and experience; both have canonical discipline definitions and artifact chains; see Evidence & prior art | This review | Confirm or narrow |
| D3 | Should content strategy (Halvorson quad: Purpose + Process + Structure + Governance) be a third pillar of this pack, distinct from content-design (what a page says, per RFC-0062)? | Yes — content strategy here; content-design in experience | Content strategy is a planning/governance discipline; content-design is a per-surface design discipline. RFC-0062 explicitly deferred content strategy to this pack. | This review | Confirm or adjust |
| D4 | Does growth strategy (AARRR model, product-led growth, PMF testing) belong in this pack or in a separate `growth` pack? | Defer to OQ1 (defined in Open questions) | Growth strategy is related to product strategy but has a distinct operational character (measurement, experimentation, activation loops) that may warrant its own pack | OQ1 decide-by | Rule on scope |

## Problem & goals

The current catalogue has three strategy-adjacent entry points, none of which covers upstream strategy:

- **`product-engineering`** — starts at product-vision (why this product should exist) and product-strategy (the guiding policy and coherent actions). These are *intent-level* artifacts. They do not cover how to arrive at a product vision through market analysis, competitive research, or positioning work.
- **`experience`** — starts at customer journey mapping and service blueprinting. These assume the experience strategy (what the end-to-end experience should feel like across channels) has already been set.
- **`research`** — produces research briefs. It does not author strategy; it supplies evidence to strategy.

The gap: a strategist arriving at the catalogue has no skills for the upstream work — the competitive landscape scan, the positioning framework, the UX strategy document, the content strategy quad — that feeds the existing packs. This RFC creates the home for those disciplines.

**Goals:**
- A named pack with a scope declaration and a discipline taxonomy.
- At minimum two pillar disciplines in v1 scope: market/competitive strategy and UX strategy.
- Content strategy as a third pillar (deferred from RFC-0062).
- A clean partition with the existing packs: no overlap with `product-engineering`'s intent rungs, `experience`'s journey/screen skills, or `research`'s evidence-gathering.

**Non-goals:**
- Individual skill SKILL.md files — those land in follow-on specs per discipline.
- Growth strategy / growth model (deferred to OQ1).
- SEO strategy (deferred from RFC-0062; depends on OQ1 resolution).
- Market research production — the pack consumes research (`research` pack outputs); it does not produce primary research.
- Analytics or metrics tooling — strategy direction only; measurement is a separate concern.

## Proposal

**Pack name:** `product-strategy`

**Pack type:** User-scope, pure-markdown, no engine — same posture as `experience` (ADR-0024 extended by analogy: no values tables, no platform primitives, no analytics engine).

**Discipline taxonomy (v1):**

*Pillar 1 — Market & competitive strategy:* skills that help a strategist understand the competitive landscape (SWOT — Strengths, Weaknesses, Opportunities, Threats; Porter's Five Forces — supplier/buyer/entrant/substitute/rivalry analysis; PESTLE — Political, Economic, Social, Technological, Legal, Environmental macro scan; BCG Matrix — portfolio growth-share quadrants: Stars / Cash Cows / Question Marks / Dogs), define a positioning frame (Jobs to be Done market sizing, Blue Ocean strategy canvas, competitive feature matrix), align the organization to strategic objectives (OKR cascade — Objectives and Key Results, org-wide alignment from company down to product and team level), articulate product-market fit hypotheses (Lean Canvas, Superhuman PMF methodology, Sean Ellis PMF survey), and sketch a go-to-market motion. Sits upstream of `product-engineering`'s `product-vision` intent.

*Pillar 2 — UX strategy:* skills that bridge business goals and user experience design — the NN/g three-layer model (vision → goals + measures → plan), Jeff Gothelf/Josh Seiden's OKR-linked UX strategy approach (OKRs used here as an outcome-framing lens for UX design, distinct from Pillar 1's org-wide OKR cascade), and Jaime Levy's UX strategy framework (business strategy + value innovation + validated user research + killer UX design). Sits upstream of `experience`'s `map-customer-journey`.

*Pillar 3 — Content strategy:* skills grounded in the Halvorson content strategy quad (Brain Traffic, 2018 revision: Purpose — what content exists and why; Process — how content is made, governed, and maintained; Structure — content models and metadata; Governance — consistency, accuracy, and relevance standards). Distinct from `content-design` (RFC-0062) which is per-surface, design-time work — content strategy is organizational/governance-layer; content design is execution-layer. Sits upstream of content-design and informs the experience pack's design thread.

**Pack chain position:**
```
product-strategy (market strategy + UX strategy + content strategy)
        ↓                               ↓                        ↓
product-engineering           experience pack            content-design skill
(product-vision intent)   (journey → screen → services)  (experience pack)
```

*Practice chain (how the disciplines relate internally):* Market/competitive strategy → UX strategy (how the experience creates competitive differentiation) → experience mapping (cross-channel research synthesis upstream of design) → UX design (executes the strategy). Content strategy (organizational governance) → content-design (per-surface execution). Growth strategy runs in parallel to product strategy, not upstream of it.

**ADR-0024 posture:** All skills produce strategic direction documents — competitive maps, positioning briefs, UX strategy documents, content strategy quads — none of which contain values tables, platform primitives, or analytics engines. The same pure-markdown, direction-only posture as `experience`.

## Options considered

Axis: how to house upstream strategy disciplines in the catalogue.

| Option | Description | Trade-off | Prior art |
|---|---|---|---|
| **A — `product-strategy` pack (recommended)** | New pack; three v1 pillars (market, UX, content strategy); growth deferred to OQ1 | Adds a new pack; clean discipline partition; no overlap with existing packs | Separate strategist-role discipline is standard in agency practice (Huge Inc, IDEO, Frog Design all separate strategy from design execution) |
| **B — Extend `product-engineering` with strategy skills** | Add market/UX/content strategy skills to `product-engineering` | Avoids a new pack; but `product-engineering` is already engineer-oriented — adding strategist-role skills blurs its audience | No prior art for bundling market strategy with spec authoring |
| **C — Extend `experience` with UX strategy; extend `product-engineering` with market strategy** | Split across two existing packs | Closest match to current entry points; but cross-pack strategy discipline creates a "who do I invoke first?" confusion | None — content strategy in particular has no natural home in either existing pack |
| **D — Do nothing; let users compose strategy ad-hoc** | Preserve current catalogue; no new pack | Cost: strategists using the catalogue have no skill home; the gap noted in this session and RFC-0062 persists unaddressed | — |

## Risks & what would make this wrong

**Pre-mortem:**
- *Pack is too abstract to invoke* — strategy direction skills produce documents, not code; agents struggle to determine when to invoke them. Mitigation: each skill has a concrete elicitation trigger (e.g., "I need to understand the competitive landscape before writing the product-vision intent") and a well-defined artifact type.
- *Growth strategy boundary is unclear* — growth leaks into market strategy (GTM) and product strategy (PLG) via overlapping concerns. Mitigation: OQ1 resolves this before skill authoring begins.
- *Pillar 3 (content strategy) overlaps with RFC-0062's content-design* — both concern content. Mitigation: the partition is governance/planning vs. per-surface/design-time; the spec will nail this with a one-line boundary in each SKILL.md.
- *OKR appears in two pillars (Pillar 1: org-wide cascade; Pillar 2: UX outcome framing)* — could cause confusion about which pillar owns OKR work. Mitigation: each skill's elicitation trigger and artifact type are distinct; the boundary is stated in each pillar's description.

**Key assumptions (falsifiable):**
- Market/competitive strategy, UX strategy, and content strategy are distinct enough to be separate skills, not a single "strategy" skill with surface-type routing.
- A strategist-role adopter audience (separate from designer or engineer) exists and reaches for this pack.
- The pack can produce direction documents that clear ADR-0024's pure-markdown guardrails.

**Drawbacks:**
- A third strategy-adjacent pack (alongside `product-engineering` and `experience`) increases catalogue surface area.
- The strategist persona may overlap with the product manager persona already served by `product-engineering`.

## Evidence & prior art

**De-risk note:** No spike run for this lightweight RFC. The discipline boundaries are reasoned, not measured. Individual skill specs will carry their own de-risk spikes before implementation.

**Repo precedent:**
- RFC-0050 (`experience` pack) — explicitly deferred UX strategy and experience mapping as out of the design pack's scope; no home exists today.
- RFC-0062 (`content-design` and `copy-direction`) — explicitly deferred UX strategy, content strategy (Halvorson quad), and experience mapping to this future pack (see RFC-0062 Reviewer brief).
- RFC-0043 (`product-engineering` product rung) — added `product-vision` and `product-strategy` intent levels; market/competitive analysis that feeds the vision rung has no skill home.
- `docs/backlog.md` (`content-strategy-and-marketing-copy-lens`) — originally proposed a `growth` or `content-strategy` pack; this RFC supersedes the "content-strategy pack" thread of that item, leaving growth unresolved.

**External prior art:**
- NN/g — UX strategy as a three-layer discipline (vision → goals + measures → plan), explicitly distinct from UX design. ([nngroup.com/articles/ux-strategy/](https://www.nngroup.com/articles/ux-strategy/))
- Jaime Levy — *UX Strategy* (O'Reilly, 2nd ed. 2021): four tenets (business strategy + value innovation + validated user research + frictionless UX). Artifact chain: proto-personas → opportunity hypotheses → competitive analysis → validated concept.
- Brain Traffic / Kristina Halvorson — content strategy quad (2018 revision: Purpose + Process + Structure + Governance); the organizational/governance layer above content-design. ([braintraffic.com/blog/new-thinking-brain-traffics-content-strategy-quad](https://www.braintraffic.com/blog/new-thinking-brain-traffics-content-strategy-quad))
- Adaptive Path (Brandon Schauer, Chris Risdon) — *A Guide to Experience Mapping*: three components (Lens / Customer Journey Model / Takeaways). Cross-channel, higher-altitude, and upstream of the service blueprint; distinct from an operational customer journey map.
- Blue Ocean Strategy (Kim & Mauborgne) — strategy canvas + four-actions framework (Eliminate / Reduce / Raise / Create). Grounds the market strategy pillar's competitive-landscape artifact.
- Sean Ellis PMF survey (40%-disappointed threshold) and Lean Canvas (Ash Maurya) — canonical PMF measurement and hypothesis artifacts for Pillar 1.
- AARRR / Pirate Metrics (Dave McClure, ~2007) and PLG (Blake Bartlett / OpenView, ~2016) — growth strategy frameworks, grounding OQ1's scope question. Research finds growth strategy increasingly treated as its own function at scale, distinct from product strategy. ([amplitude.com/blog/pirate-metrics-framework](https://amplitude.com/blog/pirate-metrics-framework))

## Open questions

**OQ1 — Does growth strategy (AARRR, PLG, PMF testing, Sean Ellis) belong in `product-strategy` or in a separate `growth` pack?**
Growth strategy has strategic elements (GTM motion, growth model selection) and operational elements (experiment design, activation metrics, cohort analysis). The operational half may warrant a separate `growth` pack. Recommended default: defer growth entirely from `product-strategy` v1 and resolve the boundary in a follow-on RFC after the v1 skills are scoped. Owner: eugenelim. Decide-by: before `product-strategy` v1 spec authoring.

**OQ2 — Should experience mapping (Adaptive Path model — cross-channel arc, distinct from a customer journey map) be a fourth pillar in v1, or deferred to a follow-on?**
Experience mapping sits upstream of the experience pack's `map-customer-journey` skill but is closely related to it. It may make more sense as the experience pack's upstream entry point (extending RFC-0050) than as a `product-strategy` skill. Recommended default: defer experience mapping to the `experience` pack as an upstream extension (RFC-NNNN), not `product-strategy`. Owner: eugenelim. Decide-by: before `product-strategy` v1 spec authoring.

## Follow-on artifacts

- Spec: `docs/specs/product-strategy-pack/` (discipline taxonomy, pack contract, v1 skill list)
- ADR-NNNN: `product-strategy` pack scope and discipline boundaries
- Amend `docs/backlog.md`: mark `content-strategy-and-marketing-copy-lens`'s content-strategy thread as in-progress (RFC opened); add growth-strategy thread as open
- Cross-reference note added to `packs/product-engineering/` and `packs/experience/` README files noting the upstream pack
- Reconcile RFC-0062: update RFC-0062's two references from `product-strategist pack` to `product-strategy pack` (RFC-0062 D5 and Reviewer brief "Not in scope") — on acceptance of both RFCs

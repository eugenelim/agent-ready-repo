# Product Strategy Pack — Design Document

Living design reference for the product-strategy pack. Records the philosophy, pillar architecture, invariants, and key decisions so the reasoning survives beyond individual PRs and applies when extending or replacing any skill.

---

## TL;DR

`product-strategy` is the strategy seat upstream of every product initiative. It runs three pillars — market and competitive analysis, UX strategy, and content strategy — each producing committed artifacts in `docs/product/shaping/` that downstream packs read by path. The PRFAQ is the altitude-0 forcing function: the most tangible first step, and the artifact every initiative brief traces its strategic rationale back to. The OKR cascade is the bridge to `product-engineering` (gap entries feed the PE shaping queue). `ux-strategy.md` and `content-strategy.md` are the bridge to `experience-design` (read by `journey-mapping` and `content-design`). No growth tooling, no primary research production, no per-surface content design — those belong downstream.

---

## Non-Goals

Things a reasonable reader might expect this pack to solve. It doesn't, by design:

- **Growth strategy.** AARRR funnels, product-led growth, PMF testing, and cohort retention loops are deferred to a follow-on `growth` pack. Growth is downstream of strategy, not coextensive with it.
- **Primary research production.** This pack consumes desk-research project outputs via `synthesize-stakeholder-research`; it does not produce interview guides, discussion scripts, or survey templates. Research production belongs in the `desk-research` pack.
- **Per-surface content design.** `define-content-strategy` covers the organizational and governance layer above content (Purpose + Process + Structure + Governance). Per-screen copy intent belongs in the `experience-design` pack's `content-design` skill; per-state string writing belongs in the `product-engineering` pack's `ux-writing` skill.
- **Analytics and CRO tooling.** Measurement frameworks, A/B testing sequencing, and conversion rate optimization belong downstream of the strategy this pack sets.

---

## 1. The strategy seat

### Why upstream of everything

Strategy artifacts — the SWOT, the PRFAQ, the OKR cascade, the UX strategy — are pre-conditions for product engineering and design, not concurrent activities. Running `journey-mapping` without a UX strategy is possible, but the output is grounded in the journey author's assumptions rather than a committed experience direction. Running `frame-situation` without OKR-derived gaps means the shaping queue fills with team-driven work that may not connect to company objectives.

This pack's position upstream of both `product-engineering` and `experience-design` is the architectural invariant. Skills in this pack write artifacts that downstream packs read by path; this is a one-way dependency. No skill in this pack reads from the PE or experience-design packs.

### The committed artifact model

Every skill in this pack writes a durable artifact to `docs/product/shaping/`. The artifact path is resolved via the `[strategy]` section of the adopter-owned `agentbundle-layout.toml` — the same consolidated layout contract used across all artifact-writing packs.

The committed model is the point: strategy artifacts must outlive sessions. A SWOT that exists only in a chat log cannot be read by `run-okr-cascade` in the next session. A PRFAQ that isn't committed cannot be referenced by the initiative briefs that trace their strategic rationale back to it.

---

## 2. Three pillars

### Pillar 1 — Market and competitive strategy

Seven skills produce the situation picture and routing artifacts:

| Skill | Framework | Artifact |
|-------|-----------|---------|
| `run-pestle-analysis` | PESTLE — Political, Economic, Social, Technological, Legal, Environmental | `macro-environment.md` |
| `run-porters-five-forces` | Porter's Five Forces | `competitive-landscape.md` |
| `run-bcg-matrix` | BCG Matrix — Stars, Cash Cows, Question Marks, Dogs | `portfolio-position.md` |
| `run-swot` | SWOT — Strengths, Weaknesses, Opportunities, Threats | `swot-analysis.md` |
| `run-okr-cascade` | OKR cascade — company → team → shaping-queue gaps | `okr-cascade.md` + `workspace.toml` entries |
| `write-prfaq` | PRFAQ — press release + FAQ as altitude-0 forcing function | `prfaq.md` |
| `synthesize-stakeholder-research` | Research synthesis — strategic narrative by theme | `stakeholder-synthesis.md` |

The intended sequence is upstream-to-downstream: macro environment → competitive landscape → portfolio position → situation synthesis (SWOT) → altitude-0 direction (PRFAQ) → gap routing (OKR cascade). `synthesize-stakeholder-research` runs at the start when prior desk-research outputs exist.

### Pillar 2 — UX strategy

`define-ux-strategy` produces a three-layer document (Vision → Goals + Measures → Plan) that bridges the business strategy from Pillar 1 to the experience design work downstream. It uses the NN/g three-layer UX strategy model, Jaime Levy's four-tenets framework, and Gothelf/Seiden OKR-linked UX framing.

The artifact — `ux-strategy.md` — is read by the experience-design pack's `journey-mapping` as the stated strategic rationale for the journey. When absent, `journey-mapping` degrades gracefully but the journey has no explicit strategy anchor.

### Pillar 3 — Content strategy

`define-content-strategy` produces the organizational and governance layer above per-surface content work: Purpose (why content exists), Process (how it is produced), Structure (how it is organized), and Governance (who decides). This is the Halvorson content strategy quad.

The artifact — `content-strategy.md` — is read by the experience-design pack's `content-design` skill for organizational governance intent. It sets the constraints `content-design` operates within, not the per-surface copy itself.

---

## 3. The PRFAQ as altitude-0 forcing function

### Why the PRFAQ is the first-value skill

The PRFAQ forces specificity before any engineering begins. A strategist who cannot write a specific headline — naming the customer, the problem, and the benefit in one sentence — does not yet understand the product well enough to brief engineers or designers. The press-release format is the pressure: a press release that names no measurable benefit is obviously broken.

Every initiative brief in the PE pack traces its strategic rationale back to the PRFAQ. Without a committed PRFAQ, initiative briefs are grounded in the team's interpretation of the strategy — which diverges across team members and sessions.

### Why it precedes market analysis in the start-here path

The README puts `write-prfaq` as the first command, before the market analysis sequence. This is deliberate: a product concept that can't be stated as a specific press release is not ready for market analysis. The PRFAQ surfaces what you don't know about the concept before session time is spent analyzing a market for an underspecified product.

Teams that run market analysis first often use the analysis to confirm a concept they haven't yet examined critically. The PRFAQ-first order inverts this: pressure-test the concept, then validate it against the market picture.

---

## 4. OKR cascade and the PE bridge

### The gap-routing contract

`run-okr-cascade` is the primary bridge from this pack to `product-engineering`. Its output is not just a document — it is a workspace state change. Each identified gap becomes a `{type = "strategy"}` entry in the active initiative's `["ini-NNN".shaping_queue].backlog` array in `workspace.toml`.

The PE pack's `workspace-status` reads these entries and surfaces them as strategy-driven shaping items. The PE pack's `frame-situation` picks them up and shapes them into briefs. This cross-pack routing is documented in each skill's `references/cross-pack-routing.md`.

### Why gaps, not features

The OKR cascade identifies gaps between current state and OKR targets. It does not produce a feature list. Features are decisions made after shaping; gaps are facts about the current state. A strategy that outputs features has already made the implementation decisions; a strategy that outputs gaps leaves those decisions to the product engineers who shape them.

---

## 5. UX and content strategy bridge to experience-design

### The anchor contract

`ux-strategy.md` and `content-strategy.md` are the two strategy anchors the experience-design pack reads. Their relationship is one-directional and path-based: the experience-design pack reads them by path; it does not write them. If neither artifact exists, the experience-design pack degrades gracefully — `journey-mapping` runs without a strategy anchor, producing a journey grounded only in the stated user and outcome.

### Why set strategy before design

Setting the UX strategy before `journey-mapping` ensures the journey is designed to serve the stated experience goals, not the team's instinct about what the product should feel like. A journey map derived from a UX strategy is traceable to a business objective; a journey map derived only from user research is traceable to a researcher's synthesis.

The same logic applies to content strategy and `content-design`: without a committed organizational governance layer, per-surface content decisions are made locally and diverge over time. `content-strategy.md` sets the rules that keep local decisions coherent.

---

## 6. What "method" means in practice

### Pure method, no values

This pack ships canonical framework names and procedural steps, not values. No token tables, no organizational templates, no benchmark numbers. This mirrors the design principle in `experience-design` (§3): values are always project-specific; the method to derive them is not.

A SWOT that ships with example strengths produces a SWOT with those examples cargo-culted in. A SWOT that only ships the four-quadrant structure and the procedure for filling it produces a SWOT grounded in the actual organization.

### Frameworks are named, not reprinted

Each skill references its source framework by name (SWOT, Porter's Five Forces, Halvorson content strategy quad) and defines the procedure for applying it. The frameworks themselves are not reprinted — they are published and authoritative. Reprinting them would create a maintenance burden and an accuracy risk.

---

## 7. Safety invariants

1. **No skill writes to downstream pack output paths.** Skills in this pack write only to `docs/product/shaping/` (or the configured strategy output path). No skill writes to `docs/design/`, initiative task lists, or any PE-owned path other than the shaping-queue backlog array in `workspace.toml`.

2. **The cascade writes gaps, not features.** `run-okr-cascade` outputs `{type = "strategy"}` gap entries. It does not output `{type = "feature"}` entries or write to `work_queue`. Gap entries are for `frame-situation` to shape into briefs; they are not execution-ready tasks.

3. **Artifacts commit before downstream use.** No downstream pack references a strategy artifact that has not been committed to `docs/product/shaping/`. An uncommitted SWOT is not a strategic anchor.

4. **No growth tooling.** No skill in this pack implements AARRR, PMF testing, or cohort-level retention analysis. These belong in a follow-on `growth` pack.

5. **No primary research production.** `synthesize-stakeholder-research` consumes desk-research outputs; it does not produce interview guides, discussion scripts, or survey templates.

---

## 8. Design decisions and rationale log

### Why PRFAQ-first in the start-here path (2026-07-27)

The start-here command is `write-prfaq`, not `run-swot` or `run-pestle-analysis`. The rationale: a product concept that cannot be stated as a specific press release is not ready for market analysis. Teams that run market analysis first tend to use the analysis to confirm a concept they haven't yet examined critically. PRFAQ-first surfaces the underspecified areas of the concept before market analysis begins, so the analysis is shaped around real questions rather than rationalizing a predetermined direction.

**Alternative considered:** start with `run-swot` as the most comprehensive situation artifact. Rejected because SWOT is a synthesis skill — it consumes PESTLE, Porter's, and BCG outputs. Starting with SWOT before any market analysis exists means the agent produces a SWOT grounded in assumptions, not analysis. PRFAQ-first avoids this by not implying a market analysis sequence at all for teams that only need altitude-0 direction.

### Why UX and content strategy are in this pack, not experience-design (from pack inception)

`define-ux-strategy` and `define-content-strategy` produce organizational and governance artifacts that a product strategist authors, not artifacts that experience designers author. The UX strategy names the experience vision and the OKR-linked goals — decisions made at the strategy level before design begins. Placing these skills in `experience-design` would blur the upstream/downstream boundary and imply that design teams are responsible for setting the experience objectives their own work is measured against.

**Alternative considered:** place `define-ux-strategy` in `experience-design` as the first step of the design thread, with `journey-mapping` consuming it in the same session. Rejected because it collapses the strategy-to-design boundary: the UX strategy is set by a product strategist (or strategy/design collaboration), not by the designer running the thread. The strategy artifact must exist before the design thread starts, not be produced as the first step of it.

### Why no growth tooling in this pack (from pack inception)

Growth strategy (AARRR, PLG, PMF testing, cohort retention) is a distinct discipline with a distinct audience and distinct tooling. Including it here would expand the scope from "upstream strategy that all initiatives share" to "all strategic and growth work" — a scope boundary that loses its shape. Growth is deferred to a follow-on pack.

**Alternative considered:** add AARRR as a Pillar 4 skill. Rejected because AARRR is a growth measurement framework, not a market analysis or direction-setting framework. The three pillars of this pack produce pre-engineering artifacts that survive the strategy horizon; AARRR produces metrics that live in the measurement layer, which is post-engineering.

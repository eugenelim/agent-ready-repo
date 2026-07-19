# RFC-0065: Experience pack surface-genre uplift
<!-- "surface-genre uplift" identifies the proposal: adding a surface-genre taxonomy
     and the skills that consume it. The full explanation is in "The ask". -->
<!-- Write this RFC for a COLD READER who has not read the related RFCs: coined
     terms are glossed inline on first use. -->

- **Status:** Draft
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-18
- **Date closed:**
- **Decision weight:** standard <!-- Reversible: pure-markdown skills, user-scope default, no security boundary. Renames are breaking but follow established ADR-0038 precedent. -->
- **Related:** RFC-0050 (the experience pack — the founding RFC that established the experience-pack skill chain and its agnosticism posture; the chain is now 11 skills after RFC-0062 added two more), RFC-0062 (content-design and copy-direction — most recent experience-pack addition; introduced the 2-type copy-layer surface routing that coexists with this RFC's design-layer routing), ADR-0024 (framework-agnosticism guardrails: no values tables, no platform primitives), ADR-0038 (alias-free pack-rename precedent — the shape this RFC's skill renames follow)

## Reviewer brief

- **Decision:** Whether to add a **surface-genre contract** to the experience pack's screen brief (the per-screen artifact `map-screen-flow` produces and all downstream design skills consume — "surface genre" = what kind of surface this is: marketing, docs, analytical, etc.), add **one Define-phase skill plus four genre-specific design skills**, extend four existing skills with agency-practice gaps, and **rename nine experience-pack skills** to canonical design-industry terminology — all in one PR at experience 0.6.0.
- **Recommended outcome:** Accept D1–D8.
- **Change if accepted:**
  - One new field (`surface-genre:`) in the screen-brief template (the shared artifact all downstream design skills read)
  - Five new SKILL.md files with reference trees: `design-principles`, `conversion-design`, `documentation-design`, `analytical-design`, `marketplace-design`
  - Extensions to four existing skills: `map-customer-journey` (peak moments, evidence level, genre axis), `interaction-design` (five new pattern families), `blueprint-service` (evidence-of-service row, fail points), `layout-and-information-architecture` (success metric binding, genre routing)
  - Nine experience-pack skill renames following ADR-0038 precedent (rename live surface, bridge frozen governance, no install-time alias)
  - experience pack 0.5.0 → 0.6.0; new rename ADR as follow-on artifact
- **Affected surface:** `packs/experience/` (all 11 existing skills touched; 5 new skills added); `packs/experience/pack.toml` (version + evals list); `docs/product/changelog.md` (user-visible changes)
- **Stakes:** Reversible for new skills (can be amended or removed). Renames are breaking but follow the established alias-free precedent (ADR-0038); pack is user-scope, pre-stable.
- **Review focus:** (1) Whether the 7-genre taxonomy is MECE (mutually exclusive, collectively exhaustive) and the exhaustiveness argument holds. (2) Whether new skills clear ADR-0024's two guardrails (no values tables; no platform primitives). (3) Whether the rename sweep is complete (spike confirmed: ~43 files in `packs/experience/` + 4 files in `docs/guides/experience/` — roughly 6–7× larger by file count than frontmatter alone; verification grep is mandatory). (4) Whether the coexistence of `surface-genre` (design layer) and `content-design`'s `surface-type` (copy layer) is clear enough for adopters.
- **Not in scope:** Pixel comps or stack-specific values; SEO/analytics tooling; a fourth `work-loop` reviewer agent; post-launch measurement methodology; any change to `content-design`'s existing 2-type copy-layer surface routing.

## The ask

**Recommendation (BLUF — bottom line up front).** Add a `surface-genre` contract field to the experience pack's screen brief, add one Define-phase skill plus four genre-specific design skills, extend four existing skills with agency best practices, and rename nine experience-pack skills to canonical industry names — all in one PR at experience 0.6.0.

**Why now (SCQA — Situation / Complication / Question / Answer).** *Situation:* The experience pack ships 11 skills covering the design chain from journey mapping to screen flow to craft design and critique. RFC-0062 added content strategy and copy direction, including a 2-type copy-layer surface routing (acquisition vs. product/reference). *Complication:* A web audit of the repo's own marketing site (Astro) and docs site (MkDocs + Material) exposed a structural root cause: every design skill — IA, interaction, aesthetic direction, critique — treats all surfaces as the same design problem. Skills have no concept of what *kind* of surface is being designed, so marketing-specific patterns (hero-as-demo, social proof hierarchy), documentation patterns (density calibration, Diátaxis-shaped navigation), analytical patterns (dashboard IA, widget state hierarchy), and marketplace patterns (listing card IA, filter architecture) never enter the design chain. Anchoring against leading agency lifecycle practices (Work & Co, ustwo, Clearleft, R/GA, Huge, AKQA, Instrument) confirmed two additional gaps: the "Define" phase (research synthesis → named design principles) is entirely absent from the skill chain; and skill names don't align with canonical industry terminology. *Question:* Can the pack address all three gaps — surface-genre routing, Define-phase methodology, canonical naming — while preserving ADR-0024's framework-agnosticism posture?

**Decisions requested.**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
|---|---|---|---|---|---|
| D1 | Add `surface-genre:` to the screen-brief frontmatter (the contract `map-screen-flow` produces and all downstream design skills read), with inline elicitation fallback when no brief is available? | Yes | Concentrates genre declaration at the natural planning step; all downstream skills already read the brief; minimal additive change; standalone skills degrade to inline elicitation | This review | Confirm placement + standalone fallback |
| D2 | Use a fixed 7-type taxonomy: `marketing \| documentation \| informational \| analytical \| transactional-journey \| marketplace \| workspace`? | Yes — fixed 7, canonical but not exhaustive | MECE along "dominant UX design challenge"; grounded in NNGroup surface research and Morville & Rosenfeld IA theory; each type produces genuinely different optimal IA and interaction patterns | This review | Confirm types or amend; confirm "canonical but not exhaustive" posture |
| D3 | Add a new `design-principles` skill deriving 3–5 arbitration-ready design principles from journey insights? | Yes — new skill | Distinct outputs from journey mapping (insights → directives); NNGroup four-step derivation is a recognized standalone activity; fills the absent Define phase; passes CHARTER four-bar test (the four criteria every catalogue addition must clear — see `docs/CHARTER.md` § Principles: (1) universal across tech stacks, (2) substantive not duplicative, (3) a habit not a tool, (4) used often enough to stick) | This review | Confirm new skill + chain position |
| D4 | Add four new genre-specific skills: `conversion-design` (marketing), `documentation-design` (documentation), `analytical-design` (analytical), `marketplace-design` (marketplace)? | Yes — all four | Each fills a genuinely absent genre; each clears ADR-0024's agnosticism guardrails; each passes the CHARTER four-bar test; implementation prompts exist | This review | Confirm all four or phase any out |
| D5 | Extend four existing skills with agency-practice gaps: (a) `map-customer-journey` + peak moments + evidence level + genre axis; (b) `interaction-design` + 5 new pattern families; (c) `blueprint-service` + evidence-of-service row + fail-point marking; (d) `layout-and-IA` + success metric binding + genre routing? | Yes — all four extensions | Each is surgical and additive; none restructures existing skills; all grounded in agency best practice (NNGroup, Shostack, Kahneman, Pixelmatters) | This review | Confirm all four or scope any out |
| D6 | Coexistence: `surface-genre` (design-layer routing) coexists with `content-design`'s `surface-type` (copy-layer routing); no change to `content-design`? | Yes — parallel axes, no change | Different consumers (design skills vs. copy skill), different axes (design patterns vs. narrative structure); no routing conflict when documented | This review | Confirm coexistence or flag a conflict |
| D7 | Rename nine experience-pack skills to canonical industry names following ADR-0038's alias-free precedent, in the same PR? (The tenth rename, `voice-and-microcopy → ux-writing`, is in `product-engineering` — deferred to a separate product-engineering RFC.) | Yes — all nine experience renames, same PR | Names diverge from canonical terms; rename sweep surface is bounded (grep-verified: ~43 files in `packs/experience/` + 4 files in `docs/guides/experience/`); ADR-0038 precedent is established; one PR per scope decision | This review | Confirm all nine or hold any for follow-on |
| D8 | Bump experience pack 0.5.0 → 0.6.0? | Yes | Five new skills + extensions + renames; ADR-0038 precedent used minor bump for same-kind change; pre-stable, breaking acceptable | This review | Confirm |

*Default if no objection: adopt D1–D8 and proceed to implementation.*

## Problem & goals

**Diagnosis.** The experience pack's 11-skill chain covers the full design workflow from journey mapping to critique. Despite RFC-0062's addition of `content-design` (which introduced copy-layer surface routing), a structural gap remains: every design skill — IA, interaction, aesthetic direction — treats all surfaces as the same design problem.

A web audit of the repo's own marketing and documentation sites exposed this concretely. Five findings are surface symptoms of the same root cause:
- A1: No product artifact in the hero → marketing patterns absent from skill chain
- A2: No social proof strip → conversion hierarchy methodology absent
- B1: Documentation density too low → density-by-Diátaxis-type absent
- B3: Canonical URL bug → machine-readability checklist absent
- B5: Sidebar overload → navigation-at-scale strategy absent

Root cause: no skill in the chain asks what *kind* of surface is being designed, so genre-specific patterns never route in.

Anchoring against leading agency practice (ustwo's Discover/Shape/0-1/Boost model; the Design Council's double-diamond Discover/Define/Develop/Deliver model that agencies including Clearleft adopt; R/GA's four service disciplines; NNGroup's artifact-in-practice research) confirmed two additional gaps:

- **Define phase entirely absent.** All leading agencies derive 3–5 named design principles from journey insights before design work begins. This phase (NNGroup four-step model; IDEO experience principles; Clearleft design criteria) is the most consistently skipped in practice. Without it, design teams relitigate the same debates at every review.
- **Skill names diverge from canonical industry terms.** Teams reach for "journey mapping" and find `map-customer-journey`; "user flow" and find `map-screen-flow`; "design system" and find `design-system-foundations`. The mismatch is a legibility tax on every team familiar with agency vocabulary.

**Goals.**
- `surface-genre` contract field in the screen brief, available to all downstream design skills from a single declaration point.
- Four new genre-specific skills covering the highest-gap genres (marketing, documentation, analytical, marketplace).
- `design-principles` skill filling the Define-phase gap.
- Surgical extensions to four existing skills with agency best practices they currently lack.
- Nine experience-pack skill names aligned with canonical industry terminology.

**Non-goals** (could-have-been-goals, deliberately dropped):
- **`workspace` genre dedicated skill** — recognized in the taxonomy but pattern set is more experimental; deferred to follow-on RFC (see Open questions).
- **Post-launch measurement** — naming a success metric at brief time is the boundary; running analytics or iterating from data is the research pack's domain.
- **Changes to `content-design`'s 2-type copy routing** — RFC-0062's acquisition/product-reference split is untouched (D6).
- **A fourth `work-loop` reviewer agent** — the experience-reviewer agent already fills the design-time review slot (RFC-0050 D7).
- **Usability testing or competitive analysis methodology** — the research pack owns these.
- **Pixel comps or stack-specific values** — ADR-0024's guardrails remain fully in force.

## Proposal

### D1 — `surface-genre:` in the screen-brief contract

**Change to `map-screen-flow/assets/screen-brief-template.md`** — add one field:

```markdown
---
type: screen-flow-brief
screen: <screen-name>
flow: <slug>
surface: <responsive-web | iOS | Android | cross-platform>
surface-genre: <marketing | documentation | informational | analytical | transactional-journey | marketplace | workspace>
---
```

And in the `## Place in the whole` section:

```
- Surface genre: <genre> — determines design patterns and IA approach
```

**Change to `map-screen-flow/SKILL.md`** — add confirmation item 5 to "When to invoke":

> 5. **You know the surface genre.** Before drafting briefs, confirm the genre from `marketing | documentation | informational | analytical | transactional-journey | marketplace | workspace`. If absent from context, elicit inline: "What kind of surface is this?" Genre is orthogonal to platform — a marketplace surface on iOS is both `marketplace` AND `iOS`. Genre determines which design pattern families and IA approaches apply downstream.

**Standalone elicitation fallback.** Each downstream skill adds: "Check the per-screen brief for `surface-genre:`. If no brief exists, elicit: 'What kind of surface is this?'" This ensures genre is always available regardless of invocation order.

### D2 — 7-type surface genre taxonomy

| Genre | Primary user goal | Dominant UX design challenge |
|---|---|---|
| `marketing` | Convert | Persuasion hierarchy, proof structure, above-fold conversion, IC-first (IC = individual contributor; for developer tools: the homepage speaks to the IC, not the buyer) |
| `documentation` | Find / learn | Diátaxis-shaped density, navigation at scale, TTFV (time to first value — how quickly a new user completes their first meaningful task) |
| `informational` | Read / browse | Typography, editorial hierarchy, F/Z reading flow (F- and Z-shaped eye-scan paths across a page), "what's next" chain |
| `analytical` | Decide from data | Domain-model-first widget IA, three-tier hierarchy, Shneiderman's mantra (overview → zoom/filter → details on demand) |
| `transactional-journey` | Complete a task | Gate-by-gate validation, progress visibility, error recovery, save-state |
| `marketplace` | Discover + compare | Listing card IA, filter architecture, comparison affordances, browse-first vs. search-first |
| `workspace` | Work + persist | Context persistence, collaboration state, presence indicators, low-interruption patterns |

**Canonical but not exhaustive.** These seven are recognized patterns with settled methodology. Unrecognized genres are valid; skills treat them as unspecified and elicit inline context.

**Coexistence with `content-design`'s surface-type (D6).** `content-design` routes copy decisions on a 2-type taxonomy: `acquisition` (marketing surfaces → StoryBrand/CCD (Conversion-Centered Design) narrative arc) or `product/reference` (all others → Pyramid Principle, a structured communication framework where the conclusion leads and evidence follows). `surface-genre` is a design-layer taxonomy routing IA, interaction, and aesthetic decisions. They are parallel axes; `marketing` → `acquisition` for copy purposes; the other six genres → `product/reference` for copy purposes. The two fields are set independently in the screen brief; no lint enforces agreement. The declared default mapping above is the elicitation-time convention — if an adopter sets `surface-genre: marketing` with `surface-type: product/reference`, the copy skill uses the explicit `surface-type` value as authoritative; the genre field governs only design routing. No change to `content-design`.

### D3 — New `design-principles` skill

File: `packs/experience/.apm/skills/design-principles/SKILL.md`

**What it produces:** 3–5 named design principles — actionable directives that arbitrate competing design directions. Form: `[Imperative verb] + [what] + [why/for whom]`. The arbitration test: given two wireframes, can this principle distinguish between them? If not, rephrase.

Examples of well-formed principles:
- "Make the invisible visible" — show system state the user cannot otherwise infer
- "Reduce the burden of proof" — every screen shows evidence, not assertion
- "Honour the expert's speed" — never require an expert to do what a beginner needs

**Not brand values.** "Be bold", "Be human" → brand values, belong in `creative-direction`. Design principles are decision-making tools for the design team.

**Chain position.** Consumes `journey-mapping`'s (renamed from `map-customer-journey` in D7) peak moments and highest-opportunity pains. Consumed by `creative-direction` (renamed from `aesthetic-direction`), `information-architecture` (renamed from `layout-and-information-architecture`), `content-design`, and `design-review` (renamed from `design-critique`) — each references the principles when making trade-off decisions.

**Evidence level carries through.** If the journey map was `assumption-based`, derived principles are marked as hypotheses to validate.

**NNGroup grounding.** Four-step model (per NNGroup, "Design Principles to Support Better Decision Making"): (1) identify core product values → (2) articulate why each matters specifically to users → (3) surface known tradeoffs (where two values conflict, decide which wins) → (4) draft collaboratively then converge through critique. These four steps map to: insight → user-grounded → arbitration-aware → team-owned.

### D4 — Four new genre-specific skills

**`conversion-design`** (marketing surfaces). Covers: hero approach selection (five approaches: animated product UI, static screenshot, switchable multi-UI, embedded live, code/terminal output; for developer tools: code/terminal is default), above-fold six-element spec (headline ≤10 words + subheadline + primary CTA (call to action) + secondary CTA + first proof signal + friction-removal microcopy), IC-first principle (the homepage speaks to the individual contributor who will use the tool; buyer concerns on secondary surfaces), scroll story 7-zone structure with one-job-per-zone rule, social proof 6-tier hierarchy calibrated to product maturity stage, numbered product tour spine. Grounded in: Evil Martians' study of 100 developer tool landing pages (IC-first finding, hero pattern analysis); NNGroup page-fold manifesto; PLG.news developer-tool website guide. Pure method; no values, breakpoints, or framework names.

**`documentation-design`** (documentation surfaces). Covers: Diátaxis type mapping (tutorial/how-to/reference/explanation; each has a distinct density target — reference = densest for lookup mode, how-to = scannable-procedural, tutorial/explanation = intermediate), navigation-at-scale strategy selection (three strategies by page count and complexity: section-collapse sidebar, tab-lift for parallel content, progressive indexing for deep platforms), docs landing page as hub (numbered Start Here path + content-type entry points + search), TTFV (used as a design target for documentation onboarding paths), machine-readability requirements (per-page unique descriptions, canonical URL intent as a design-phase decision, heading hierarchy as semantic structure). Grounded in: Diátaxis framework; Tom Johnson navigation principles; Stripe docs case study. No tooling references (MkDocs, Docusaurus, Mintlify are not named — method is tool-agnostic).

**`analytical-design`** (analytical surfaces — dashboards, command centres, BI (business intelligence) tools, monitoring). Covers: domain-model-first (model objects/attributes/relationships/actions/arrival-moments before any widget placement; a widget not tied to an object-state-action triple is absent), business-question anchoring (3–5 explicit questions this surface answers; any widget that answers none is tertiary or absent), three-tier widget hierarchy (primary KPIs (key performance indicators) ≤9 / secondary context / tertiary detail), Shneiderman's mantra (overview first → zoom/filter → details on demand), role-based views (executive / manager / IC default views), spatial layout grammar (top row = state signals, left column = worklist/alert queue, centre = primary diagnostic, right rail = context + filter), per-widget state handling (each widget handles loading/empty/error/stale independently — no full-page spinner). **Scope boundary:** `analytical-design` covers dashboard IA and layout methodology — which widgets go where, what hierarchy, what role-based views. Individual chart and data visualization design (which chart type, encoding, scale choices) is outside this skill's scope. Teams should use their preferred chart design approach after the dashboard IA is defined.

**`marketplace-design`** (marketplace surfaces — listings, catalogues, browse/discover/buy, two-sided markets). Covers: listing card IA (card hierarchy, information density, what belongs on a card vs. on the detail page), filter and facet architecture (filter taxonomy design, chip vs. sidebar presentation, instant vs. apply-button filter, empty-filter vs. zero-results UX distinction), comparison affordances (when to offer comparison panels vs. detail-page comparison), browse-first vs. search-first entry path routing, cart/transaction bridge (the checkout sequence bridges to `interaction-design`'s wizard-and-stepper patterns for gate-by-gate validation on the transactional-journey genre). Pure method; no e-commerce platform references.

### D5 — Extensions to four existing skills

**(a) `map-customer-journey` — three surgical additions.**

After step 5 (populate emotion arc), add step 5b: **Identify peak moments.** From the populated emotion arc, name the 1–3 stages with the steepest negative dip and any single most-positive peak. Kahneman's peak-end rule: memory of the experience is shaped disproportionately by these moments and the final stage. Mark them explicitly in the artifact. All downstream design decisions are weighted toward improving peak moments and end state first.

In step 2 (elicit persona and outcome), add: **Declare the evidence level** — `observational` (direct research), `survey-backed`, or `assumption-based`. Record in frontmatter as `evidence-level:`. An assumption-based map is a hypothesis to validate, not a defect.

In step 1 (set the surface), add: **Confirm the surface genre** alongside the platform axis. Genre determines stage-shape templates. New reference file `references/surface-genre-journeys.md` provides canonical stage scaffolds for each genre: transactional-journey (trigger → orient → configure → commit → confirm); marketplace (discover → explore → evaluate → decide → transact); workspace (onboard → orient → work → persist → collaborate); analytical (arrive → orient → query → interpret → decide → act); marketing (arrive → evaluate → convince → commit → onboard); documentation (arrive → find → understand → apply → verify); informational (arrive → scan → read → absorb → depart).

**(b) `interaction-design` — five new pattern families** added to `references/pattern-families.md`:
1. **Wizard and stepper:** linear stepper (3–6 steps; validate on step exit not final submit; bidirectional navigation; expert non-linear jump), save-and-resume (autosave + explicit "save for later"; session-persistent state), conditional disclosure within a step (show fields when upstream choices make them relevant)
2. **Data table:** four filter types (global quick-filter / column-level / faceted sidebar / active filter chips); bulk operations (checkbox → sticky bulk action bar → count visible); row detail disclosure five options (expandable row → tooltip → modal → sidebar panel → full-screen); alignment (text left, numbers right with monospace)
3. **Destructive action 5-tier escalation:** inline confirmation → toast+undo (brief undo window) → modal (default focus on Cancel; verb+object label; "Cannot be undone" only when true) → typed confirmation (user types resource name) → two-person/2FA (two-factor authentication) approval
4. **Save-state:** autosave (trigger on blur or on a short input-pause debounce — do not specify a ms value, that is an implementation constraint; three indicator states: Saving / Saved [timestamp] / Failed — Retry; keep explicit save button for psychological safety even with autosave); unsaved-changes guard (modal: "Save changes" primary, "Discard" secondary — never reverse this priority); draft vs. published as two explicit states
5. **Analytical dashboard widgets:** KPI card anatomy (metric name + current value + trend direction + comparison period + drill-down affordance; ≤9 primary cards); alert/signal design (traffic-light never sole channel — pair with text label; timestamp on every signal); drill-down affordance (drawer = context-preserving default; detail page = full exploration; modal = focused decision)

**(c) `blueprint-service` — two additions:**
- **Evidence-of-service row** (a row in the original Shostack blueprint the current skill omits): physical or digital artifacts the customer encounters at each frontstage touchpoint — notifications, confirmation screens, receipts, error messages, emails. This row reveals friction between the service's intended experience and the artifacts it actually produces.
- **Fail-point marking:** Explicit identification of the steps most likely to fail from the customer's perspective, with design priority annotation (critical / high / medium). The current skill identifies gaps; fail points are a distinct construct with design priority.

**(d) `layout-and-information-architecture` — two additions:**
- **Success metric binding** (add to "When to invoke", item 4): Before designing hierarchy, name the measurable outcome this surface serves. "How will your team know this surface is working three months after launch?" A layout designed without a goal is designed for nothing in particular.
- **Genre routing** (add to Procedure step 1, after job-and-audience confirmation): Confirm `surface-genre` from the screen brief; route:
  - `marketing` → read `conversion-design` output for scroll story section assignments before designing hierarchy
  - `documentation` → read `documentation-design` output for density targets and nav structure
  - `analytical` → read `analytical-design` output for three-tier widget hierarchy and spatial grammar
  - `transactional-journey` → progressive disclosure toward gate-by-gate completion; next required action must be unambiguous at every step
  - `marketplace` → comparison-enabling IA; filter accessibility at every view state
  - `workspace` → context-persistent navigation; re-orientation for returning sessions
  - `informational` → typography hierarchy and reading flow dominant; F/Z scan pattern

### D7 — Nine skill renames

| Current slug | New slug | Canonical source |
|---|---|---|
| `map-customer-journey` | `journey-mapping` | NNGroup, Adaptive Path, IDEO |
| `blueprint-service` | `service-blueprint` | Shostack (coined the term); NNGroup canonical usage |
| `map-screen-flow` | `user-flow` | Figma, Pixelmatters, design practice universally |
| `map-internal-process` | `process-mapping` | APQC, BPM Institute |
| `aesthetic-direction` | `creative-direction` | Agency practice: Work & Co, Fantasy, AKQA |
| `layout-and-information-architecture` | `information-architecture` | Morville & Rosenfeld; Information Architecture Institute |
| `design-critique` | `design-review` | NNGroup distinguishes: critique = iterative improvement conversation; review = gate evaluation; this skill functions as a gate |
| `design-system-foundations` | `design-system` | Design Systems Slack, Figma, industry universally |
| `copy-direction` | `tone-of-voice` | UK GDS (UK Government Digital Service), Mailchimp Voice & Tone, brand industry standard |

`voice-and-microcopy → ux-writing` is intentionally excluded: `voice-and-microcopy` lives in `product-engineering`, not `experience`. Its rename requires a separate product-engineering RFC. Cross-pack references from experience skills to `voice-and-microcopy` continue to use the current name until that rename lands; those inbound pointers are noted in this RFC's follow-on artifacts.

**Rename procedure (following ADR-0038 shape exactly):**

The actual sweep surface is larger than description frontmatter alone. Grep-verified across the experience pack: ~43 files contain old slug references — SKILL.md bodies, `references/*.md`, `assets/*` templates, `README.md`, `pack.toml`, and `experience-reviewer.md`. Plus 4 files in `docs/guides/experience/` (Living-class docs — not frozen; must be updated per ADR-0038 precedent which explicitly swept the guides tier).

1. Rename each skill directory: `mv packs/experience/.apm/skills/<old>/ packs/experience/.apm/skills/<new>/`
2. In each renamed SKILL.md: update `name:` frontmatter; update `description:` frontmatter cross-references; update body text references to old slug names
3. In all `references/*.md` and `assets/*` files under each renamed skill: update every cross-reference to renamed slugs
4. In `packs/experience/.apm/agents/experience-reviewer.md`: update all skill slug references
5. In `packs/experience/README.md`: update all skill slug references
6. In `packs/experience/pack.toml` `[pack.evals]` list: replace old slugs with new slugs; bump version 0.5.0 → 0.6.0
7. In `docs/guides/experience/**` (4 files — Living-class, not frozen): update all old slug references; ADR-0038 explicitly swept this tier
8. Post-rename verification: `grep -r "map-customer-journey\|blueprint-service\|map-screen-flow\|map-internal-process\|aesthetic-direction\|layout-and-information-architecture\|design-critique\|design-system-foundations\|copy-direction" packs/experience/ docs/guides/experience/ --include="*.md" --include="*.toml"` must return zero results
9. New ADR (following ADR-0038 shape) as follow-on artifact: records old→new mapping, bridges frozen governance, no alias

**No install-time alias** — same posture as ADR-0038. Adopters with the old names must reinstall or update their references.

**Cross-pack inbound pointers.** Multiple experience skills reference `voice-and-microcopy` (in `product-engineering`) — these remain unchanged in this PR. They become inbound pointers that a future product-engineering rename will need to update in lockstep.

### D8 — Version bump: 0.5.0 → 0.6.0

Five new skills + four extended skills + nine renames (breaking) = minor version bump. ADR-0038 precedent: pack rename + 4 new skills → 0.1.1 → 0.2.0. Pre-1.0: breaking renames acceptable in minor bumps.

## Options considered

**On genre contract placement** (axis: where genre knowledge enters the design chain — MECE: the field can live at the brief layer, at each individual skill, at a new upstream skill, or nowhere):
- **A — Screen-brief contract field (proposed) ✓** — declared once, read by all. Prior art: `design-critique/references/quality-floor.md` (the shared quality checklist — handle-all-states, accessibility floor, reduced-motion — that all skills reference rather than restate) uses the same "declared once, referenced by all" pattern. Trade-off: standalone invocations need fallback elicitation.
- **B — Per-skill independent elicitation** — genre declared N times; high friction in multi-skill flows. Worse for the common full-chain case.
- **C — New upstream "surface-brief" skill** — cleaner separation; adds a required step before the current entry point; expands RFC scope unnecessarily.
- **D — Do nothing** — audit findings remain unaddressed; no genre routing available. Cost of delay: every design project produces A1/A2/B1-style findings.

**On taxonomy size** (axis: fixed closure vs. open — MECE: fixed-small / fixed-full / open-ended / do-nothing):
- **A — Fixed 7 (proposed) ✓** — MECE along "dominant UX design challenge"; grounded in NNGroup surface research and Morville & Rosenfeld IA theory (see Evidence).
- **B — Fixed 4** — excludes analytical, marketplace, workspace. These three have genuinely distinct requirements; omitting them leaves the most-absent genres uncovered.
- **C — Open-ended** — any string; loses mechanical routing guarantees; adds skill complexity.
- **D — Extend content-design's 2-type taxonomy** — wrong layer; conflates copy decisions with IA/pattern decisions.

**On design principles placement** (axis: standalone skill / sub-step in existing skill / do-nothing):
- **A — New standalone skill (proposed) ✓** — distinct inputs/outputs; separable session (NNGroup); passes CHARTER four-bar test.
- **B — Sub-step in journey-mapping** — bloats journey skill; couples principle quality to map quality. RFC-0050 D9 precedent: distinct ontology warrants a separate skill.
- **C — Section in creative-direction** — conflates design principles (experience arbiters) with aesthetic direction (visual personality).
- **D — Do nothing** — Define phase remains absent; teams relitigate the same debates at each review.

**On renames** (axis: same RFC / separate RFC / no rename — MECE):
- **A — Same RFC, same PR (proposed) ✓** — ADR-0038 precedent established; mechanical once decided; no alias mechanism exists (grep-confirmed in RFC-0048).
- **B — Separate RFC** — excess overhead for a mechanical change that requires exactly one decision (make the canonical-names commitment).
- **C — Do nothing** — names diverge from canonical terms; new skills added with canonical names create inconsistency within the pack.

## Risks & what would make this wrong

**Pre-mortem: assume this shipped and failed.**

1. **Agnosticism lint fails on new skills.** A new skill accidentally references a framework, library, or platform primitive. Mitigation: all five skills were audited against ADR-0024 guardrails before this RFC was drafted; lint-experience-agnostic.py runs in CI and is the mechanical floor.

2. **Rename sweep is incomplete.** A cross-reference is missed; old slugs remain in a description field. Mitigation: the post-rename grep verification step (D7 § procedure step 8) is mandatory and returns zero expected results. Pack.toml evals list is the secondary surface.

3. **`surface-genre` field breaks existing adopter briefs.** Adopters with hand-crafted briefs find the new field unexpected. Mitigation: the field is additive — not required by any lint; existing briefs without it are valid; skills degrade to inline elicitation when absent.

4. **7-type taxonomy doesn't cover an adopter's actual surface.** Mitigation: "canonical but not exhaustive" posture — unrecognized genres are elicited inline. No routing breaks; only routing optimizations are unavailable for custom types.

5. **`design-principles` is produced and forgotten.** Teams generate it once and never reference it at reviews. Mitigation: Open question 2 — add one sentence to `design-review` procedure: "Load the design-principles document and evaluate each finding against the named principles."

**Key assumptions (falsifiable):**
- A1: The 7 genres are distinct enough that a skill can recommend different patterns for two genres without overlap. *Falsifiable if: an adopter cannot distinguish between two genres' IA recommendations.*
- A2: The rename sweep is complete at the spike-confirmed surfaces (~43 files in `packs/experience/` + 4 files in `docs/guides/experience/`). *Falsifiable if: post-rename grep returns any old slug in a live surface.*
- A3: `surface-genre` (design layer) and `content-design`'s `surface-type` (copy layer) produce no routing confusion. *Falsifiable if: an adopter routes to the wrong skill because the two systems appear to conflict.*

**Drawbacks (there are some):**
- Pack grows from 11 to 16 skills. The README and pack description should document the skill chain clearly, segmented by design phase.
- Renames impose migration cost on adopters who have documented current skill names in internal wikis or prompts. Unavoidable given alias-free precedent and pre-stable window.
- One large PR (20+ file changes). Coherent (every change serves the surface-genre theme) but wide to review.

## Evidence & prior art

**Spike result.** Riskiest assumption tested: "The rename sweep is bounded." Grep-verified: old skill slug references appear in **~43 files** across `packs/experience/` — SKILL.md bodies (not just frontmatter), all `references/*.md` files, all `assets/*` templates, `README.md`, `pack.toml`, and `experience-reviewer.md` — plus **4 additional files** in `docs/guides/experience/` (Living-class docs, not frozen; ADR-0038 explicitly swept this tier). The initial spike incorrectly claimed the surface was "7 description frontmatter fields" — the actual surface is roughly 6–7× larger by file count (43 files in packs/experience/ alone is ~6×; adding the 4 guides files brings it to ~7×). The sweep remains mechanical and bounded (grep identifies every hit), but the PR is larger than early estimates. Assumption A2 is revised: the surface is fully bounded by the grep across `packs/experience/` + `docs/guides/experience/`; the verification step remains valid once the scope is correct.

**Repo precedent:**
- RFC-0050 + ADR-0024 (`docs/rfc/0050-the-experience-pack.md`, `docs/adr/0024-design-craft-upstream-intent-and-agnosticism.md`) — founding RFC and agnosticism guardrails. All new skills comply with both guardrails.
- RFC-0062 (`docs/rfc/0062-content-design-and-copy-direction-skills.md`) — most recent skill-addition RFC. Confirms: new SKILL.md + reference tree, pack.toml evals list addition, minor version bump, coexistence note between new and existing routing.
- ADR-0038 (`docs/adr/0038-rename-design-craft-pack-to-experience.md`) — alias-free rename precedent. D7's skill renames follow this shape: rename live surface, bridge frozen governance (frozen ADRs/RFCs/specs name the old skill — that is correct historical record; this new ADR is the bridge), no alias.
- RFC-0050 D9 (`docs/rfc/0050-the-experience-pack.md` Decision 9) — established that when two candidate features have distinct ontology (different inputs, different outputs, different grounding) they warrant separate skills rather than a sub-step. Grounds D3 (`design-principles` as a new skill rather than a sub-step of `journey-mapping`).

**External prior art** (web citations fetched-and-confirmed; print sources noted with journal/DOI or secondary confirmation path):
- Morville & Rosenfeld, "Information Architecture for the World Wide Web," 3rd ed. (O'Reilly, 2006) — taxonomy of site types (product catalogues, corporate sites, reference sites, news/entertainment, community) as methodology for classifying dominant user task by surface; this RFC's 7-type taxonomy extends their classification along the same axis. Print source; no direct URL; available via O'Reilly Learning.
- NNGroup, "Customer Journey Maps: When and How to Create Them" — five components, frontstage framing, organizational use patterns: https://www.nngroup.com/articles/customer-journey-mapping/
- NNGroup, "Design Principles to Support Better Decision Making" — four-step derivation model, principles as decision arbiters: https://www.nngroup.com/articles/design-principles/
- NNGroup, "Design Critiques: Encourage a Positive Culture" — critique vs. review distinction; critique = improvement conversation, review = gate: https://www.nngroup.com/articles/design-critiques/
- NNGroup, "Service Blueprinting in Practice" — evidence-of-service as a blueprint row; fail-point identification: https://www.nngroup.com/articles/service-blueprinting-practice/
- IDEO, "Designing a Journey Map: Consider These Tips" — moments that matter as high-leverage intervention points: https://www.ideou.com/blogs/inspiration/designing-a-journey-map-consider-these-tips
- Kahneman, Fredrickson et al. (1993), "When More Pain Is Preferred to Less," *Psychological Science*, 4(6), 401–405 (print source; DOI: 10.1111/j.1467-9280.1993.tb00589.x) — original peak-end rule experimental grounding. Peak-end rule application to customer experience design is confirmed via the NNGroup journey-mapping citation above, which cites this body of work directly.
- Evil Martians, "We studied 100 devtool landing pages" (2025) — IC-first principle, code/terminal as default hero, above-fold checklist: https://evilmartians.com/chronicles/we-studied-100-devtool-landing-pages-here-is-what-actually-works-in-2025
- Diátaxis, diataxis.fr — four documentation types; each with distinct reading mode and density requirement: https://diataxis.fr/
- Shneiderman, "The Eyes Have It: A Task by Data Type Taxonomy for Information Visualizations" (1996), IEEE Symposium on Visual Languages, DOI: 10.1109/VL.1996.545307 — introduces the visual information-seeking mantra: overview first, zoom and filter, details on demand. Print/conference proceedings source; DOI is the primary confirmation path.
- ustwo Services — four-phase engagement model (Discover/Shape/0-1/Boost): https://ustwo.com/services
- Design Council, "The Double Diamond" — original four-phase model (Discover / Define / Develop / Deliver) that makes the Define phase explicit as a structured convergence step between research and development; the foundation for how leading agencies name and sequence the design Define phase: https://www.designcouncil.org.uk/resources/the-double-diamond/
- Andy Budd, "Product Shearing Layers and the Double-Diamond Approach to Design" (Clearleft) — applies Stewart Brand's shearing layers to double-diamond iteration at product agencies, confirming agency adoption of the double-diamond model: https://andybudd.com/archives/2015/04/product_shearing_layers_and_the_double-d
- Pixelmatters, "Designing Beyond the Happy Path" — error states, edge cases, alternative entry points as required flow components: https://www.pixelmatters.com/insights/designing-beyond-the-happy-path

**Promoted research.** Full corpus — agency lifecycle findings, artifact-in-practice synthesis, gap analysis matrix, and self-contained implementation prompts for each change — is in `.context/agency-lifecycle-gap-analysis.md` in this repo. Working context; not projected to adopters.

## Open questions

1. **`workspace` genre dedicated skill: this RFC or follow-on?** Workspace surfaces (Notion/Figma/Slack paradigm) have distinct design challenges; the pattern set is more experimental than the four genres addressed here. **Recommended default:** defer to follow-on RFC; the genre is named in the taxonomy (D2) so `user-flow` and `information-architecture` can route against it. Owner: eugenelim. Decide by: follow-on RFC after 0.6.0 ships.

2. **Should `design-review` explicitly reference design-principles?** Without this, principles can be produced and forgotten (risk #5). **Recommended default:** yes, add one sentence to `design-review` procedure: "Load the design-principles document; map each finding to the principle it was judged against." Owner: eugenelim. Decide by: implementation PR.

3. **Should `content-design`'s description cross-references to `copy-direction` and `voice-and-microcopy` be updated in the rename sweep?** `content-design` references both renamed skills. **Recommended default:** yes, these are in-scope for the rename sweep. Owner: eugenelim. Decide by: implementation PR.

## Follow-on artifacts

On acceptance:
- **ADR-NNNN: Nine experience-pack skill renames** — following ADR-0038 shape exactly: live surface renamed, frozen governance bridged (old→new mapping table), no install-time alias. Created as part of the implementation PR.
- **`docs/product/changelog.md`** — user-visible entry: renamed skills list + new skills list + version 0.6.0.
- **`docs/rfc/README.md`** — add RFC-0065 row to the table.
- **`docs/product/journeys/designer-designs-surface.md` — update to final to-be state after implementation.** The journey document at that path records the current as-is gaps (Stage 1–6 "Now" rows) alongside the to-be improvement per RFC-0065. After the implementation PR merges and experience 0.6.0 ships, update the journey to reflect the confirmed as-built state: replace "Now" column content with the shipped reality, mark any gaps that were partially resolved differently than the RFC specified, and promote the journey's `status:` from `planned` to `live`. This keeps the journey document as the single source of truth for the design-chain state, not the RFC (which is frozen after acceptance).
- **Marketing site (`web/`) — update skill names and descriptions.** The implementation PR that ships the 9 renames must be accompanied by a corresponding update to the marketing site copy wherever experience pack skills are named. Old skill slugs in marketing copy will mismatch the installed pack and confuse adopters. Scope: any page in `web/` that lists experience pack skills by name or describes their triggers. Treat as blocking for the 0.6.0 release announcement.
- **Technical documentation (`docs/guides/experience/`) — update skill names, descriptions, and guide content.** The D7 rename sweep explicitly includes the 4 files in `docs/guides/experience/` (these are Living-class docs, not frozen). Beyond slug updates, verify that any guide that walks through a skill by name reads correctly with the new name, and that any guide referencing a skill's trigger description reflects the updated description (particularly: `user-flow` which gains the surface-genre confirmation step, `information-architecture` which gains genre routing, and all four new skills which need guide coverage). New skills (`design-principles`, `conversion-design`, `documentation-design`, `analytical-design`, `marketplace-design`) have no guide entries yet — guide stubs are in scope for a follow-on PR or can ride with the implementation PR if capacity allows.
- **Note: `voice-and-microcopy → ux-writing` deferred.** Multiple experience-pack skills reference `voice-and-microcopy` (in `product-engineering`) by its current name. A future product-engineering RFC that renames it must update these inbound experience-pack cross-references in lockstep. The inbound files are listed below using their **post-0.6.0 paths** (after this RFC's renames land): `tone-of-voice/SKILL.md` (was `copy-direction/`), `user-flow/SKILL.md`, `user-flow/assets/design-tool-handover-template.md`, `user-flow/assets/screen-brief-template.md`, `user-flow/references/screen-flow.md` (all were `map-screen-flow/`), `design-review/references/quality-floor.md` (was `design-critique/`), `content-design/SKILL.md`, and `README.md`.

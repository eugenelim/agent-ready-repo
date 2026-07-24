# RFC-0062: content-design and copy-direction skills

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-18
- **Date closed:** 2026-07-23
- **Decision weight:** standard
- **Related:** ADR-0024 (experience-pack posture), ADR-0038 (renamed the pack from its
  original design-craft name to experience), RFC-0050 (the experience pack),
  RFC-0071 (digital experience doctrine — accepts this RFC; `copy-direction`
  implementation tracked as `spec/xd-copy-direction` under ini-003),
  backlog `copy-direction-skill-rfc`, backlog `content-strategy-and-marketing-copy-lens`
- **Implementation:** `content-design` shipped (pre-acceptance). `copy-direction`
  tracked as `spec/xd-copy-direction` in `["ini-003".work].queue`; ships as
  fulfillment of this RFC.

## Reviewer brief

- **Decision:** Add two new skills to the `experience` pack — `content-design` and `copy-direction` — that cover the gap between product intent and screen design for web surfaces.
- **Recommended outcome:** Accept.
- **Change if accepted:** Two new SKILL.md files and their reference/asset trees land in `packs/experience/.apm/skills/`; the experience pack's design thread gains two upstream skills; `voice-and-microcopy` (the product-engineering skill for UI-state copy) gets an explicit cross-reference scope note; experience pack bumps minor version.
- **Affected surface:** `packs/experience/` (two new skills); `packs/product-engineering/.apm/skills/voice-and-microcopy/SKILL.md` (scope note cross-reference only).
- **Stakes:** Reversible — new skills can be amended or removed; no existing skill changes behavior; no cross-pack interface changes.
- **Review focus:** (1) Whether `content-design`'s acquisition sub-path (conversion architecture) is within charter scope without triggering the blocked growth/marketing charter question. (2) Whether the `voice-and-microcopy` / `copy-direction` boundary is clean enough to eliminate confusion.
- **Not in scope:** SEO (keyword targeting, meta descriptions); analytics/CRO tooling; user research production; pixel comps; any code output; the `product-strategy` pack's UX-strategy and content-strategy disciplines (RFC-0063, a future pack, not yet built).

## The ask

**Recommendation (BLUF — bottom line up front):** Add `content-design` (what a surface needs to say, in what form, to achieve what objective — upstream of `map-screen-flow`) and `copy-direction` (the copy twin of `aesthetic-direction` — voice and positioning goals grounded in persona, copy precedents, and persuasion standards) to the experience pack. Both are pure-markdown skills clearing ADR-0024's guardrails (no values tables, no platform primitives, no engine) and filling named broken links per RFC-0050's add-a-skill bar (design-flow completeness); neither requires a charter expansion because both are design-thread work, not growth analytics or tooling.

**Why now (SCQA — Situation, Complication, Question, Answer):** The experience pack's design thread runs from journey mapping through screen flow to interaction and layout design. It has no skill that asks "what should this page *say* and *sound like* before we design it." Building the platform marketing site (2026-07-01) exposed this gap concretely: hero copy, scroll narrative, and above-fold structure were written without any disciplined method, producing generic output requiring manual scrubbing. Two backlog items have been open since then. The `human-craft-check.md` extension (product-engineering 0.11.0 — a reference that catalogues vocabulary and structural tells for the voice-and-microcopy skill) addresses the editing layer; the authoring-direction layer — what to say and how to sound — still has no skill home.

**Decisions requested:**

| ID | Question | Recommendation | Why | Decide by | Reviewer action |
|---|---|---|---|---|---|
| D1 | Name the upstream-of-screen skill `content-design`? | Yes — `content-design` | GOV.UK / Nava PBC canonical discipline name; strong prior-art chain; project convention prefers discipline taxonomy over invented compounds | This review | Confirm or rename |
| D2 | Should `content-design` cover both acquisition and product/reference surfaces via a `surface-type` input? | Yes — both, with `surface-type` flag | Same discipline applies to both surface types; one skill with two sub-paths is cleaner than two separate skills | This review | Confirm or narrow |
| D3 | Does conversion architecture (above-fold order, scroll section arc, CTA placement) belong in `content-design`'s acquisition sub-path? | Yes — inside `content-design` | `content-design` fills a broken link in the chartered experience design thread (RFC-0050's design-flow completeness bar) and clears ADR-0024's guardrails — that is the design-scope argument. The growth-scope question: the backlog deferred conversion architecture alongside SEO as "not in experience pack scope" (see Evidence & prior art); this RFC splits that bundle — CTA placement and scroll-section sequencing are structural design-thread work (what to say in what order), not growth analytics or CRO (Conversion Rate Optimization) tooling. SEO stays deferred per D5 | This review | Confirm or defer |
| D4 | Scope boundary: `copy-direction` owns marketing/acquisition copy voice; `voice-and-microcopy` owns product UI copy states — with surface type as the explicit boundary? | Yes — surface type as the boundary | Cleanest split with no overlap at steady state; both files carry a cross-reference | This review | Confirm or adjust |
| D5 | SEO (keyword targeting, meta descriptions) explicitly out of scope for both skills? | Yes — deferred to `product-strategy` pack (RFC-0063) | Charter has no growth/marketing ruling; SEO requires specialized search-pattern research; out of scope per existing backlog decision | This review | Confirm |

## Problem & goals

The experience pack's design thread is a walkable chain from journey intent to shipped screen. The current chain:

```
map-customer-journey  →  map-screen-flow  →  blueprint-service
aesthetic-direction   ↗    (per-screen brief)   (backing services)
```

(`map-screen-flow` sequences the journey's screens into per-screen briefs; `blueprint-service` maps the backing services each screen requires.)

Two links are missing.

**Missing link 1 — what does this surface need to say?** Before `map-screen-flow` (the skill that sequences screens and produces per-screen briefs) can populate a copy slot, someone must decide: what is this page's objective, who is the audience and how aware are they, what narrative arc does the content follow, and what is the single desired action? This work happens today — but ad-hoc, without a skill, producing inconsistent results. The gap is most visible on acquisition surfaces (marketing pages, onboarding flows) where the absence of a narrative arc produces copy that is correct but inert: it answers none of the evaluator's questions in the first five seconds.

**Missing link 2 — what voice and register does the copy carry?** `aesthetic-direction` (an experience-pack skill that turns a vague visual vibe into named, ranked emotional/brand goals grounded in stable referents) has no copy equivalent. There is no interrogation sequence for manifesto vs. instructional vs. warm, no grounding in copy precedents, no arbitration rule for when voice conflicts with urgency. Copy passes `voice-and-microcopy`'s UI-state formulas but has no positioned voice — no point of view a reader can disagree with.

**Goals:**
- A `content-design` skill producing a per-surface content brief capturing surface type, audience awareness level, narrative arc, prioritized content, and success metric — feeding into `map-screen-flow`.
- A `copy-direction` skill producing a copy direction doc capturing copy voice goals, copy precedents, and copy arbitration rules — riding alongside `aesthetic-direction`, feeding into `voice-and-microcopy` and any copy written for the surface.
- Explicit scope boundaries eliminating confusion between `copy-direction` and `voice-and-microcopy`.
- Both skills clear ADR-0024's guardrails: pure-markdown, no values tables, no platform primitives.

**Non-goals:**
- SEO (keyword intent targeting, meta descriptions, page titles) — deferred; requires a charter ruling on growth scope.
- Conversion analytics / CRO (Conversion Rate Optimization) tooling — not a skill, a measurement practice.
- User research production — `content-design` consumes research (audience awareness level, VoC findings); it does not produce it.
- A new reviewer agent — the existing `experience-reviewer` (an experience-pack agent that reviews journeys, screen flows, and design briefs against grounded aesthetic reference, platform fit, and the quality floor) already reviews the outputs of both skills; scope extension deferred to OQ1.
- Changes to `voice-and-microcopy`'s behavior — the RFC adds a cross-reference scope note only.

## Proposal

### `content-design`

**What it does:** Produces a per-surface content brief — a text-first document answering "what does this surface need to say, for whom, in what form, to achieve what objective" — before any wireframe is opened. Runs after `map-customer-journey` (or inline if no journey exists) and before `map-screen-flow`.

**Inputs:** A persona and outcome (from `map-customer-journey` or elicited inline), and a surface type.

**Artifact:** `docs/design/content/<slug>.md` with `type: content-brief`. Path resolves via RFC-0050 D6's config→default→discover-by-marker contract under the `[experience]` layout parent; `content-brief` extends the pack's existing marker set (`customer-journey`, `service-blueprint`, `screen-flow`, `process-flow`). The literal path shown is the default.

**Surface-type routing:**

*Acquisition surfaces* (marketing pages, landing pages, web onboarding flows): elicits audience awareness level using the Schwartz five-stage ladder (Unaware → Problem Aware → Solution Aware → Product Aware → Most Aware, a framework from direct-response copywriting that describes how much a visitor knows about the problem and solution before arriving); selects a narrative arc (StoryBrand seven-element arc — Character + Problem + Guide + Plan + CTA + Stakes + Success, Donald Miller's framework for structuring acquisition copy around a customer's journey — for cold/warm audiences; Conversion-Centered Design seven principles — Attention, Context, Clarity, Congruence, Credibility, Closing, Continuance, Oli Gardner's framework — for bottom-of-funnel audiences); assigns scroll sections (each section gets one job: problem, guide proof, plan, stakes, CTA); defines above-fold structure (headline + subheadline answering what/who/why in five seconds); names primary and transitional CTAs; states the success metric. This sub-path is web-optimized by design — above-fold structure and scroll sections are web-page concepts tied to the viewport; a cross-platform extension (mobile onboarding, email) is deferred to a follow-on amendment.

*Product/reference surfaces* (help pages, feature reference, in-product wayfinding): elicits the user task (from journey or inline); selects content format (prose / steps / table / diagram, matched to task type); structures the content hierarchy (must-say → probably-say → might-say prioritisation following the Nava PBC text-prototype model); states the completion metric (task completion rate, search resolution).

**ADR-0024 compliance:** Points to standards (StoryBrand, CCD, Schwartz) — never reprints their frameworks verbatim. Produces direction (narrative arc, section jobs) — not values tables or copy strings.

**Procedure sketch** (to be refined in spec):
1. Confirm surface type (acquisition | product-or-reference); `docs` surfaces route as product-or-reference.
2. Elicit or confirm persona and outcome; consume `map-customer-journey` output if available.
3. Route to surface-type sub-path; run elicitation questions.
4. Resolve and surface output path; write the content brief.
5. Hand off to `map-screen-flow` (screen brief copy slot now references the content brief).

---

### `copy-direction`

**What it does:** Runs the same interrogation structure as `aesthetic-direction` — felt vibe → named goals → grounding → arbitration — applied to copy voice and positioning. Produces a `copy-direction.md` doc the rest of the build references when writing any copy for the surface.

**Inputs:** A persona and surface type (from `content-design` or elicited inline), a felt copy vibe.

**Artifact:** `docs/design/copy/<slug>.md` with `type: copy-direction`. Path resolves via RFC-0050 D6; `copy-direction` extends the discover-by-marker set alongside `content-brief`.

**Interrogation structure** (twinning `aesthetic-direction`'s 8-step procedure):
1. Map the audience — who reads this, ranked by reader type, each framed as a copy JTBD (Jobs to be Done — the progress the reader is trying to make, stated as a hire-this-copy-for task).
2. Run the interrogation — felt copy vibe → named copy goals (short noun phrases: "direct," "warm-but-not-cute," "earned authority"). Sharpen each against its opposite.
3. Ground each goal in stable referents: persona language (the words the audience actually uses), copy precedents (Stripe's "Payments infrastructure for the internet"; Linear's "The issue tracker you'll enjoy using"), persuasion standards (painkiller-first framing — lead with the pain the reader feels, then offer the solution as relief; tweet test — can the headline stand alone as a conviction statement?; five-second evaluator scan for above-fold copy).
4. Rank the goals — dominant goal wins ties.
5. Record copy arbitration — which goal wins which conflict (urgency vs. warmth; brevity vs. completeness).
6. Capture the doc.
7. Hold the copy floor — verify direction against plain-language and inclusivity standards: no jargon the reader didn't bring, no idioms that don't translate, no assumptions about who the reader is.
8. Hand off — referenced by `voice-and-microcopy` for per-surface UI copy.

**Scope boundary with `voice-and-microcopy`:** `copy-direction` owns marketing/acquisition copy voice and positioned copy (hero headlines, above-fold narrative, taglines, announcement copy). `voice-and-microcopy` (a product-engineering skill that writes blame-free, actionable copy for UI states: error messages, empty states, button labels, form labels) owns product UI copy. Onboarding copy lives in `voice-and-microcopy` (UI surface); the onboarding surface's narrative arc belongs in `content-design`. Both SKILL.md files carry a one-line cross-reference to the other.

**ADR-0024 compliance:** Points to copy precedents and persuasion standards — never reprints them. Produces named goals and arbitration rules — not a template or formula table.

---

### Skill chain after acceptance

```
content-design  ──→  map-screen-flow  (screen brief copy slot references content brief)
     │
     └──→  copy-direction  ──→  voice-and-microcopy  (copy per screen × state)
aesthetic-direction  ──→  design-system-foundations
```

`content-design` feeds `map-screen-flow` and informs `copy-direction`. `aesthetic-direction` feeds `design-system-foundations` (the skill that converts visual goals into tokens and a design system).
`copy-direction` rides alongside `aesthetic-direction`; `copy-direction` feeds `voice-and-microcopy` when writing per-surface copy.

## Options considered

Axis: how to fill the "what does this surface say" gap in the experience pack design thread.

| Option | Description | Trade-off | Prior art |
|---|---|---|---|
| **A — `content-design` + `copy-direction` (recommended)** | Two skills; `content-design` per-surface brief with surface-type routing; `copy-direction` twins `aesthetic-direction` | Adds two new skills; design thread complete; clean discipline boundaries | GOV.UK / Nava PBC text-prototype chain; Wolff Olins verbal identity model |
| **B — `content-design` only; fold copy voice into `aesthetic-direction`** | One new skill; extend `aesthetic-direction` to produce a copy goals section | Simpler; risks overloading `aesthetic-direction` which has a clear, single visual job | No prior art for conflating visual and copy direction in one artifact |
| **C — `copy-direction` only; defer `content-design`** | The original backlog proposal | Ships copy voice; page-level narrative arc still has no home | Original `copy-direction-skill-rfc` backlog item |
| **D — Extend `map-screen-flow` with a surface-intent step** | Add audience awareness + narrative arc as a pre-step inside `map-screen-flow` | Bloats a scoped skill; conflates "what to say" with "how to arrange screens" | None — content-first practice universally separates these |
| **E — Do nothing** | Leave gap; accept ad-hoc page strategy | Cost: broken design thread, generic copy, no skill home | — |

## Risks & what would make this wrong

**Pre-mortem — this shipped and the design thread still feels incomplete:**
- *`content-design` is used once per product, not per surface* — producing a generic direction doc rather than per-surface briefs. Mitigation: the output path includes a `<slug>` component that forces per-surface instantiation; the spec's acceptance criteria require at least one per-surface brief.
- *`copy-direction` is perceived as duplicating `voice-and-microcopy`* — leading to neither being used. Mitigation: scope boundary is documented as a cross-reference in both SKILL.md files; the distinction (surface type) is testable.
- *`content-design`'s acquisition sub-path drifts into growth analytics* — triggering the blocked charter question. Mitigation: the skill produces a direction brief (structure + objective), not a measurement framework; success metric is named but not tracked inside the skill.

**Key assumptions (falsifiable):**
- Content-design (deciding what to say in what form) is structural design-thread work that clears ADR-0024's guardrails; it is distinct from growth analytics (measuring whether it worked). The backlog's prior placement of conversion architecture ("not in experience pack scope" alongside SEO) is reversed by D3 for the structural-direction half only — the split argument: CTA/scroll-section sequencing belongs in the design thread because it is a structural direction brief, not analytics or tooling. If a reviewer argues that above-fold structure and scroll sections belong with the analytics bundle rather than the design thread, D3 should be rejected and the whole bundle returned to deferred.
- The `surface-type` flag cleanly routes the two sub-paths without the skill feeling like two skills wearing a coat.
- The `copy-direction` / `voice-and-microcopy` boundary (surface type) is clear enough that a designer knows which to invoke without reading both SKILL.md files.

**Drawbacks:**
- Two new skills increase the experience pack's surface area and onboarding cost for adopters.
- The acquisition sub-path borrows GOV.UK's product-surface content-first method; its application to marketing pages is adapted, not native to the original framework.
- `copy-direction` creates a soft coupling between the experience pack and `voice-and-microcopy` in `product-engineering` via cross-reference.

## Evidence & prior art

**De-risk spike:** ADR-0024's guardrails reasoned against both proposed skill shapes. `content-design` producing a narrative arc (problem → guide → plan → stakes sections) is structural content direction — no values table, no platform primitive, no analytics engine. Compliant. `copy-direction` producing named copy goals grounded in copy precedents is direction, same posture as `aesthetic-direction` producing named visual goals without palette values. Compliant. Acceptance criterion: both skills must pass `tools/lint-experience-agnostic.py` (ADR-0024's enforcement gate) before merging. No charter expansion required.

**Repo precedent:**
- `docs/adr/0024-design-craft-upstream-intent-and-agnosticism.md` — guardrails both skills must clear (confirmed compliant above).
- `docs/rfc/0050-the-experience-pack.md` — add-a-skill bar: "design-flow completeness." Both skills fill named broken links. RFC-0050 contains no SEO/conversion ruling; the actual prior scope placement is `docs/backlog.md` (`content-strategy-and-marketing-copy-lens` item 2, paraphrased: "Conversion + SEO — not in experience pack scope; belongs in a future growth or content-strategy pack, or as an opt-in rider on product-engineering. Blocked on charter decision."). This RFC splits that bundle: structural direction (what to say in what order) reverses the experience-scope exclusion with the design-thread argument; SEO stays deferred per D5.
- `packs/experience/.apm/skills/aesthetic-direction/SKILL.md` — 8-step structural template for `copy-direction` (audience map → interrogation → grounding → ranking → arbitration → capture → floor check → hand-off).
- `docs/backlog.md` lines 1205 and 1312 — original proposals and scope questions this RFC resolves.

**External prior art:**
- Nava PBC — text prototype artifact (user need + content strategy statement + prioritized information list + draft prose) produced before wireframing. Confirms `content-design` sits upstream of `map-screen-flow`. ([navapbc.com](https://www.navapbc.com/toolkits/apply-content-first-design-public-services))
- Defra Digital — content-first design (2026): "Writing out a narrative, structure of information or even the purpose of a page before choosing the visual design components." Confirms ordering and written-document artifact. ([defradigital.blog.gov.uk](https://defradigital.blog.gov.uk/2026/03/17/doing-content-first-design-at-defra-part-one/))
- Wolff Olins / Studio Noel — verbal identity document: upstream of a style guide; contains brand personality, brand story, voice, tone, grammar, naming conventions. Confirms `copy-direction`'s artifact shape. ([studionoel.co.uk](https://studionoel.co.uk/verbal-identity), [wolffolins.com](https://wolffolins.com/news/inside-wolff-olins-katherine-pisarro-grant-on-verbal-identities))
- Copyhackers / Joanna Wiebe — VoC research report: frequency-ranked messaging hierarchy required before headline writing. Confirms `copy-direction`'s grounding step. ([copyhackers.com](https://copyhackers.com/organize-your-voc-data/))
- Nielsen Norman Group (NN/G) — content strategy artifact chain: content-strategy statement → content-requirements checklist → style guidelines. Confirms upstream position of `content-design`. ([nngroup.com](https://www.nngroup.com/articles/content-strategy/))

## Open questions

**OQ1 — Does `content-design` need its own reviewer agent, or does `experience-reviewer` cover it?**
The `experience-reviewer` agent reviews journeys, screens, and briefs against grounded aesthetic reference, platform fit, and quality floor. Content briefs are a new artifact type not in the current scope. Recommended default: extend `experience-reviewer`'s scope to include content briefs in a follow-on RFC rather than blocking this one. Owner: eugenelim. Decide-by: spec authoring for `content-design`.

**OQ2 — Should `copy-direction` include a VoC (voice-of-customer) research step, or take VoC input as optional?**
Copyhackers' model requires a VoC research report before copy direction begins. The repo has a `research` pack (a pack that produces project-mode research briefs; it gathers evidence but does not author copy direction). Recommended default: `copy-direction` takes VoC findings as an optional input (elicited inline when absent, flagged as directional when absent) — same posture as `aesthetic-direction` taking persona as input without running user research. Owner: eugenelim. Decide-by: spec authoring.

## Follow-on artifacts

- ADR-NNNN: `content-design` and `copy-direction` skills added to experience pack
- Spec: `docs/specs/content-design-skill/`
- Spec: `docs/specs/copy-direction-skill/`
- Amend `docs/backlog.md`: mark `copy-direction-skill-rfc` and `content-strategy-and-marketing-copy-lens` as in-progress (RFC opened)
- Cross-reference note added to `packs/product-engineering/.apm/skills/voice-and-microcopy/SKILL.md`

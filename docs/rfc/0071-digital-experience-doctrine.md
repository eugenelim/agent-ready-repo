# RFC-0071: Digital Experience Doctrine

<!-- Written for a cold reader who has not read the related RFCs. Coined terms
are glossed on first use inline. -->

- **Status:** Accepted
- **Author:** eugenelim
- **Approver:** eugenelim
- **Date opened:** 2026-07-23
- **Date closed:** 2026-07-23
- **Decision weight:** heavy <!-- Multi-pack doctrine change: new cross-pack shared
  primitive (Digital Experience Contract), new skills (design-system-foundations,
  copy-direction), skill rename (voice-and-microcopy → ux-writing), definition-of-done
  change across four packs affecting all adopters. Not reversible without a follow-on
  RFC once the doctrine is in production use. -->
- **Related:**
  - [RFC-0030](0030-product-engineering-pack.md) (the product-engineering pack)
  - [RFC-0050](0050-experience-pack.md) (the experience pack founding RFC)
  - [RFC-0062](0062-content-design-and-copy-direction-skills.md) (content-design and
    copy-direction — Draft; this RFC accepts it and implements copy-direction)
  - [RFC-0063](0063-product-strategy-pack.md) (the product-strategy pack)
  - [RFC-0066](0066-experience-pack-surface-genre-and-skill-uplift.md) (experience pack
    skill uplift — deferred `voice-and-microcopy → ux-writing` rename in D7; this RFC
    implements that rename)
  - [RFC-0025](0025-work-loop-light-mode.md) (work-loop light mode — risk-trigger
    doctrine this RFC extends to the digital experience chain)

---

## Reviewer brief

- **Decision:** Whether to change the definition of done across four packs
  (`experience-design`, `product-engineering`, `product-strategy`, `core`) so
  that digital work is complete only when it produces a verified outcome — not
  merely a valid artifact, a green build, or an individual skill rubric that
  passes.
- **Recommended outcome:** Accept D1–D10.
- **Change if accepted:**
  - A shared **Digital Experience Contract** schema (pack-local markdown template in
    each pack's `references/`) binds strategy → PE → XD → FE with a common field set,
    risk-adaptive completeness tiers (explore / pilot / production), and a deterministic
    drift check enforced in `tools/`.
  - `product-strategy` pack gains explicit ownership of the adoption hypothesis,
    first-success event, value loop, and causal metric tree (14-point output
    structure). Strategy-to-experience implications become a named output section.
  - `product-engineering` pack gains a thin-slice requirement in `place-bet`, a
    post-launch learning contract, an evidence ladder, and plain-English gate
    language. The six-step shaping flow emits contract stubs XD extends.
  - `experience-design` pack gains: (1) a new `copy-direction` skill (RFC-0062
    accepted and implemented), (2) a new `design-system-foundations` skill (closes
    the phantom handoff between token taxonomy and token implementation), (3)
    `design-system` renamed to `design-token-taxonomy` (D3b — eliminates activation
    overlap with `design-system-foundations`; ADR-0038 alias-free precedent), (4)
    page archetype references (`references/page-archetypes.md`, ≥12 surface types),
    (5) product-object mapping guidance, (6) a complete 18-state coverage set,
    (7) three-pass `design-review` (experience-reviewer) structure with severity
    tiers, (8) natural-language trigger descriptions and near-miss guards across
    all skills.
  - `core` pack's `frontend-engineering` skill gains: four-mode structure
    (create / retrofit / audit / verify as conditional sections in one SKILL.md),
    a required page/screen contract, WCAG 2.2 AA as explicit baseline, Baseline
    Widely Available browser policy, Core Web Vitals targets (LCP ≤ 2.5 s /
    INP ≤ 200 ms / CLS ≤ 0.1 at p75), an asset-budget requirement, and an
    implementation evidence manifest as a required completion artifact.
  - `voice-and-microcopy` (product-engineering pack) renamed to `ux-writing`
    following ADR-0038 alias-free precedent (deferred in RFC-0066 D7).
  - All four packs receive non-cosmetic version bumps. Evals updated with weak
    fixtures. User guides updated with intent indexes and an end-to-end tutorial.
- **Affected surfaces:**
  - `packs/experience-design/` — 20 existing skills touched (19 + `copy-direction`);
    2 new skills added (`copy-direction`, `design-system-foundations`); `design-system`
    renamed to `design-token-taxonomy`; new `references/page-archetypes.md`
  - `packs/product-engineering/` — `place-bet`, `frame-situation`, and related shaping
    skills updated; `voice-and-microcopy` renamed to `ux-writing`
  - `packs/product-strategy/` — all 9 skills updated (triggers, outputs, evals)
  - `packs/core/` — `frontend-engineering` updated (modes, contract, evidence manifest)
  - `tools/` — new drift-check script for Digital Experience Contract equivalence
  - `docs/guides/` — intent indexes per pack; new end-to-end tutorial
- **Stakes:** Non-trivial to reverse once in production adoption. The definition-of-done
  change and contract schema affect adopters' workflows. New skills can be amended or
  removed; the rename follows ADR-0038 alias-free precedent (breaking, accepted risk for
  pre-stable packs). The `voice-and-microcopy` → `ux-writing` rename was designed and
  deferred in RFC-0066; adopters on PE pack pre-rename are warned via changelog.
- **Review focus:** All decisions resolved. D1, D3a, D3b, D4, D5, D6, D7, D8,
  D10 resolved in authoring session. D2 and D9 confirmed 2026-07-23:
  - D2 — fold `voice-and-microcopy → ux-writing` into `spec/product-engineering-shaping-doctrine`. Confirmed.
  - D9 — per-spec version bumps (one per implementing spec). Confirmed.
- **Not in scope:** Growth strategy / paid acquisition / SEO programs / lifecycle
  campaigns (deferred to future growth pack per RFC-0063 D4). `voice-and-microcopy →
  ux-writing` rename in adapters other than `experience-design` pack (cross-pack
  scope of the rename is PE pack only). New structural top-level directories. Any
  change to discovery-loop or work-loop gating logic. The `iac-terraform`, `atlassian`,
  `figma`, or any other non-digital-experience pack.

---

## The ask

**Recommendation (BLUF — Bottom Line Up Front):** Change the definition of done
across the four digital-product packs. Digital work is done only when it produces
an observable outcome supported by rendered evidence — not merely a complete
strategy document, a ratified product brief, a journey map, or a build that
passes. Implement this through a shared Digital Experience Contract, discipline-
level doctrine updates in all four packs, two new experience-design skills, one
skill rename, and a cross-pack golden-path eval.

**Why now (SCQA — Situation / Complication / Question / Answer):**

*Situation:* The catalogue ships four discipline packs covering strategy, product
engineering, experience design, and frontend engineering. Each pack produces
artifacts that individually pass their own rubric — a strategy deck, a product
brief, a journey map, a screen design, working code. The packs are individually
coherent.

*Complication:* A review of the repo's own marketing site, docs site, and pack
landing pages exposed a structural failure: artifacts that pass per-pack rubrics
can produce a product experience that is locally polished but globally broken.
The strategy has no adoption hypothesis. The product brief has no thin slice or
first-success event. The experience design references a `design-system-foundations`
skill that doesn't exist (phantom handoff). The `copy-direction` skill was designed
in RFC-0062, partially implemented (`content-design` landed; `copy-direction` did
not), and left in Draft. The frontend implementation has no evidence manifest, no
explicit performance targets, and declares completion at build + lint. The four
packs share no artifact that enforces continuity.

*Question:* Can the catalogue change the definition of done across all four packs
without breaking independent installability, without introducing rigid ceremony for
exploratory work, and without prematurely creating a growth pack?

*Answer:* Yes — via a risk-adaptive Digital Experience Contract as a pack-local
shared schema with a drift check; doctrine updates that enforce outcome evidence
at each discipline layer; and two new skills that fill documented gaps
(`copy-direction` from RFC-0062; `design-system-foundations` anticipated in
RFC-0062 and needed to close the phantom handoff).

---

## Decisions requested

| ID | Question | Recommendation | Rationale | Decide by | Reviewer action |
|----|----------|----------------|-----------|-----------|-----------------|
| D1 | Digital Experience Contract storage: (A) pack-local `references/digital-experience-contract.md` in each affected pack with a `tools/` drift check, or (B) a canonical schema in `core` projected to other packs? | **A — pack-local with drift check; each copy carries `schema-version: "1.0"` in its frontmatter** | Option B introduces a hard cross-pack runtime dependency, breaking independent installability (an adopter with only XD pack would pull in core's contract schema). Option A preserves installability; the drift check in `tools/check-contract-drift.py` (pure stdlib Python, never shipped) validates both field completeness and schema-version parity across all four copies. The `schema-version` field follows the `contract-version` convention in converters and the `schema-version` convention in adapt-to-project. Bumping the version is the mechanism for a future breaking field change — the drift check detects mismatched versions and fails the gate. | This review | Confirmed |
| D2 | `voice-and-microcopy → ux-writing` rename (deferred in RFC-0066 D7): fold into this initiative in `spec/product-engineering-shaping-doctrine`? | **Yes — fold in** | RFC-0066 D7 designed the rename and deferred it to "a separate PE RFC." This initiative's PE doctrine spec touches every PE skill boundary label — executing the rename here avoids a one-file stub RFC. ADR-0038 precedent applies (alias-free rename, breaking, pre-stable). The three-way copy boundary (copy-direction / ux-writing / content-design) is cleaner when all three are settled in one session. | This review | Confirm or defer to standalone PE RFC |
| D3a | `design-system-foundations` as a new XD skill vs. extending `design-system`? | **New skill** | `design-system` (64 lines, explicitly refuses to produce values) owns one job: derive the token taxonomy method. `design-system-foundations` owns a distinct job: take that taxonomy and set up the working token foundation for a specific project (lightweight or full mode). Two distinct trigger phrases, two distinct outputs, two distinct reviewers. RFC-0062 already anticipated this exact skill in its design thread diagram (`aesthetic-direction → design-system-foundations`). Independent installability is unaffected — both skills stay in `experience-design` pack. | This review | Confirmed |
| D3b | Rename `design-system` → `design-token-taxonomy` to eliminate activation overlap with `design-system-foundations`? | **Yes — rename** | Current `design-system` trigger description includes "set up design tokens" and "turn the direction into a system" — both of which would naturally activate `design-system-foundations` (the implementation step). The ambiguity is structural: any phrase containing "design system" could route to either skill. `design-token-taxonomy` is the precise canonical name for what the skill produces: a named, semantic token taxonomy derived from a direction (not a working implementation). Updated trigger phrases: "derive a token taxonomy", "name our tokens by semantic role", "what should our token naming convention be", "derive our spacing and type scale from the direction". Near-miss added: "set up / implement design tokens" → `design-system-foundations`. ADR-0038 alias-free precedent applies. | This review | Confirmed |
| D4 | RFC-0062 disposition: accepted by this RFC (RFC-0062 Status updated to Accepted, Date closed set to 2026-07-23); implementation tracked as `spec/xd-copy-direction` under ini-003 in fulfillment of RFC-0062 — not folded into RFC-0071's scope? | **Yes — RFC-0062 accepted here; implementation owned by RFC-0062, tracked under ini-003** | RFC-0062 is complete in design (full procedure, artifact shape, scope boundary with `ux-writing` / `content-design`, design thread diagram). `content-design` landed; `copy-direction` did not. This RFC accepts RFC-0062 (sets its Status to Accepted, Date closed to 2026-07-23). The implementation of `copy-direction` is the fulfillment of RFC-0062 — it belongs to RFC-0062's scope, not RFC-0071's. It is tracked in ini-003's work queue as `spec/xd-copy-direction` for coordination purposes; the spec's governance provenance is RFC-0062. RFC-0062 remains the authoritative design document for the skill. | This review | Confirmed |
| D5 | FE four modes (create / retrofit / audit / verify): conditional sections in one `frontend-engineering` SKILL.md vs. four separate skills? | **Conditional sections in one SKILL.md** | The four modes share the same page/screen contract requirement, the same evidence manifest output, and the same verification stack — they differ only in what they inspect and what they change. Four separate skills would duplicate the shared contract and evidence manifest; they would also create four frontmatter descriptions that must all be kept in sync. Mode is selected at invocation by context. Single SKILL.md; mode-specific sections gated by `### Mode: <mode>` headers. | This review | Confirm or propose separate skills |
| D6 | Thin coordinator skill: create one to route the Digital Experience Contract across packs, or rely on the contract artifact itself as the coordinator? | **No coordinator skill** | A coordinator skill that doesn't duplicate specialist doctrine would be a thin router — it reads the contract and calls other skills. This is what the contract itself does when skills are designed to read it. A coordinator skill adds an invocation layer without adding capability. Skills may read all contract areas; the constraint is that they must not silently rewrite another discipline's section. That constraint is a doc rule, not a skill. | This review | Confirm or identify a routing gap the contract can't cover |
| D7 | Cross-pack golden-path eval location: (A) fixtures in `experience-design` pack's `evals/` (it owns the whole journey), or (B) scattered per discipline pack, or (C) new `packs/digital-experience-eval/` pack? | **A — in `experience-design` evals** | The whole-experience view belongs to XD; XD's `design-review` skill is the terminal reviewer that evaluates across all disciplines. Concentrating the cross-pack eval fixtures in XD's evals directory means one owner, one pass, one place to calibrate. Per-discipline fixtures stay in their own packs (PS evals, PE evals, FE evals). The cross-pack golden-path eval is the integration test — it lives where the integrator lives. | This review | Confirm A or justify another location |
| D8 | Adoption-hypothesis ownership: does adding first-success event, value loop, and causal metric tree to `product-strategy` encroach on the deferred growth pack (RFC-0063 D4)? | **No encroachment — add to product-strategy** | RFC-0063 D4 deferred growth strategy (AARRR, PLG, PMF testing, experimentation operations, paid acquisition, lifecycle campaigns, SEO programs) to a future growth pack. What this RFC adds to `product-strategy` is the *upstream* work that precedes growth operations: "what does first success look like, and how will adoption compound?" — the logic a growth pack would consume, not the operational execution it would run. First-success without ownership is dangerous (no one checks if adoption is happening). The dividing line: product strategy owns the hypothesis; a future growth pack owns the programs. | This review | Confirm or narrow the addition |
| D9 | Version bump strategy: each pack bumps in its own implementing spec, not all at once? | **Yes — per-spec bumps** | Each spec is an independently shippable change. Batching version bumps into one PR risks shipping incomplete doctrine. `experience-design` gets four bumps (M3a / M3b / M3c / M3d — one per XD sub-spec); each bump is minor for a new skill or significant doctrine change, patch for mechanical boundary/trigger updates. `product-engineering`, `product-strategy`, and `core` each get one bump in their doctrine spec. | This review | Confirm or propose a single batch bump |
| D10 | `spec/xd-copy-direction` position in the queue: before `spec/xd-skill-boundaries` (M3a), since M3a's frontmatter updates assume copy-direction exists? | **Yes — before M3a** | The XD skill-boundary spec updates frontmatter near-miss guards to reference `copy-direction` by name. If `copy-direction` doesn't exist when M3a ships, those near-miss guards are phantom references. Order: RFC-0071 accepted → `spec/xd-copy-direction` → `spec/xd-skill-boundaries` → (remaining XD specs). | This review | Confirm |

*Default if no objection: adopt D1–D10 and proceed to implementation.*

---

## Problem and goals

**Diagnosis.** Four packs cover the digital product lifecycle:

| Pack | Entry point | Exit point |
|------|-------------|------------|
| `product-strategy` | Raw market signal | Strategic choices + differentiation |
| `product-engineering` | Opportunity or strategy | Testable product bet |
| `experience-design` | Product bet | Designed whole experience |
| `core` (`frontend-engineering`) | Design artifacts | Rendered, verified implementation |

Each pack individually passes its own rubric. The catalogue's marketing site, docs
site, and pack landing pages all confirm the structural failure: artifacts can be
locally polished and globally broken. Five concrete failure modes are active today:

1. **No adoption hypothesis in product-strategy.** Strategy outputs can be
   well-framed with no first-success event, no repeat-value behavior, and no
   metric tree. Who checks whether adoption is actually happening? No one, until
   a growth pack exists.
2. **No thin slice in product-engineering.** `place-bet` produces a committed
   direction without requiring a thin end-to-end slice that lets one user begin
   a real task, reach a meaningful result, and produce instrumentation. A complete
   brief is not a thin slice.
3. **Two phantom handoffs in experience-design.** (a) `design-system` produces a
   token taxonomy method but no skill applies it — `design-system-foundations` was
   anticipated in RFC-0062 but never created. (b) `copy-direction` was designed in
   RFC-0062, partially implemented, left in Draft for 5+ days; `content-design`
   landed, `copy-direction` did not.
4. **Completion without evidence in frontend-engineering.** `frontend-engineering`
   declares completion at build + lint + accessibility automation. No evidence
   manifest. No explicit performance targets. No browser policy.
5. **No cross-pack continuity check.** First-success defined in strategy can
   silently disappear by the time implementation ships. No eval tests the chain.

**Goals:**

- A shared artifact (the Digital Experience Contract) that enforces continuity
  across all four disciplines.
- Explicit adoption-hypothesis ownership in `product-strategy`.
- Thin-slice and learning-contract requirements in `product-engineering`.
- Two new `experience-design` skills filling the phantom handoffs.
- An evidence manifest as a required `frontend-engineering` completion artifact.
- A cross-pack golden-path eval that discriminates a coherent experience from a
  locally polished but globally weak one.
- All of the above risk-adaptive: explore-mode work is not buried in
  production-level ceremony.

**Non-goals:**

- Growth strategy / paid acquisition / SEO programs / lifecycle campaigns — deferred
  to a future growth pack per RFC-0063 D4.
- Any change to discovery-loop, work-loop, or new-spec skill logic.
- Any change to non-digital-experience packs.
- A thin coordinator skill that duplicates specialist doctrine.
- Replacing SAST/SCA scanners or manual security review.

---

## Proposal

### Area A — Digital Experience Contract

A lightweight shared schema connecting all four disciplines. Implemented as a
pack-local `references/digital-experience-contract.md` in each affected pack, with
a `tools/check-contract-drift.py` script (pure stdlib Python, never shipped) that
validates equivalence across all four copies.

**Risk-adaptive field tiers:**

| Tier | Delivery mode | Required fields |
|------|---------------|-----------------|
| Explore | Early discovery; prototypes | Target user, whole problem, user outcome, first-success event, primary journey, core assumptions, prototype/representation |
| Pilot | Pre-release; limited users | + States, permissions, accessibility requirements, instrumentation, support plan, rollout + recovery |
| Production | Public; all users | + Complete a11y evidence, browser matrix, CWV results, security + privacy, reliability, cross-channel continuity, measurement dashboard |

**Ownership map (skills may read all areas; they must not silently rewrite another
discipline's section — proposed changes are marked explicitly):**

| Area | Owner |
|------|-------|
| Target user, context, diagnosis, strategic choices, differentiation, adoption hypothesis, value loop, metric tree, assumptions + kill criteria | `product-strategy` |
| Opportunity + bet, evidence ladder, first-success operationalization, thin-slice, capabilities, rollout, learning plan | `product-engineering` |
| Whole journey, surface map, IA, content hierarchy, product objects, interaction + attention model, states + permissions, responsive behavior, design system | `experience-design` |
| Implemented behavior, semantic structure, design-system realization, responsive implementation, state implementation, a11y evidence, browser behavior, performance, instrumentation, rendered evidence | `core` (`frontend-engineering`) |

**Graceful capability detection:** A skill that attempts to hand off to an
unavailable skill must: (1) perform the smallest safe fallback, (2) label the
result provisional, (3) state what specialist work remains. No phantom handoff
may ship — every handoff must either resolve to an installed skill or degrade
explicitly.

### Area B — Product-strategy doctrine update

Update all nine `product-strategy` skills to:

- Require a 14-point strategy output structure including an adoption hypothesis
  section (acquisition context, promise, proof, first action, first-success event,
  repeat-value behavior, economic behavior where material).
- Add a `strategy-to-experience` output section with eight named fields (who must
  immediately recognize themselves; what problem must be named first; what must be
  demonstrated not claimed; which objections must be answered; which proof points
  are credible; which concepts should remain secondary; what action begins the
  value loop; what the product must make visibly true).
- Add an anti-pattern review covering: vision-without-choices, roadmap-as-strategy,
  target-everyone segment, feature-volume differentiation, moat-without-mechanism,
  metrics-without-user-behavior, launch-as-adoption, distribution-postponed,
  strategy-detached-from-experience, validated-without-evidence, stale-fixed-conclusions.
- Update trigger descriptions and near-misses to natural strategic questions (who
  should we serve / what is our product strategy / how do we differentiate / how
  will users discover and adopt this / etc.) with explicit near-misses for routine
  backlog shaping and copyediting without a strategy question.

### Area C — Product-engineering doctrine update

Update PE shaping flow to:

- Add a thin-slice required field to `place-bet` output.
- Add a post-launch learning contract (events, dashboards, qualitative feedback,
  review cadence, decision thresholds, rollback or expansion conditions).
- Implement an evidence ladder (observed / supported / inferred / assumed / unknown).
- Replace fixed-count options ritual with: "explore enough materially different
  options to expose the real decision; do not invent alternatives to satisfy a
  number."
- Replace internal gate IDs (G0/G1.5/G2) with plain English in all user-facing
  output.
- Rename `voice-and-microcopy` → `ux-writing` following ADR-0038 alias-free
  precedent. Update all cross-references in both the PE pack and the XD pack.
- Update evals with weak fixtures.

### Area D — Experience-design doctrine update

**New skills (two):**

1. `copy-direction` — the copy twin of `creative-direction`. Produces a
   `copy-direction.md` doc capturing copy voice goals, copy precedents, and copy
   arbitration rules. Rides alongside `creative-direction`; feeds `ux-writing`
   (renamed) and any copy written for the surface. Per RFC-0062's full design.

2. `design-system-foundations` — takes the token taxonomy produced by `design-system`
   and sets up the working token foundation for a specific project. Lightweight mode
   (semantic color roles, typography, spacing, radius, focus, key statuses, responsive
   rules, core components) and full mode (DTCG 2025.10-compatible token source,
   light + dark themes, semantic aliases, full component anatomy, generated platform
   outputs). Closes the phantom handoff between `design-system` and `frontend-engineering`.

**Existing skill updates:**

- `design-system` renamed to `design-token-taxonomy` (D3b): correct DTCG description
  (community group specification, not a W3C Recommendation); trigger description
  updated to "derive a token taxonomy / name our tokens by semantic role / derive our
  spacing and type scale from the direction"; near-miss added: "set up / implement
  design tokens → `design-system-foundations`". ADR-0038 alias-free precedent;
  grep-verified rename sweep required before shipping (mirrors RFC-0066 D7).
- All 19 skills: update trigger descriptions to natural requests; add near-miss
  guards for strategy, PE shaping, and routine FE.
- `tone-of-voice`: update frontmatter to make explicit that `copy-direction` is the
  upstream voice-direction skill and `ux-writing` is the downstream per-state skill.
- `design-review` (experience-reviewer): restructure as three-pass reviewer (cold-read
  / task-completion / contract-review) with severity tiers (blocker / concern /
  suggestion). Require rendered evidence when a rendered surface exists.
- `quality-floor.md` (shared reference): extend state set from 8 to 18 states.
- Add `references/page-archetypes.md`: ≥12 surface types, each with primary user,
  job, first-screen contract, primary action, expected result, next action, proof,
  read/write consequence, critical states, navigation behavior.
- Add product-object mapping guidance, attention contract, and read/write permission
  contract to relevant skills.

### Area E — Frontend-engineering doctrine update

- Add four-mode structure as conditional sections: create / retrofit / audit / verify.
- Require a page/screen contract (12 fields) before writing significant UI code;
  proportional to risk and scope — not a ritual for trivial components.
- Set WCAG 2.2 AA as explicit default accessibility baseline.
- Adopt Baseline Widely Available as the default browser policy.
- Add Core Web Vitals targets for public production surfaces: LCP ≤ 2.5 s / INP ≤ 200 ms /
  CLS ≤ 0.1, evaluated at p75 separately for mobile and desktop where field data exists.
- Add asset budget requirement (JS, images, fonts, third-party scripts, hydration,
  route-level loading, long tasks).
- Add brownfield inspection checklist.
- Require an implementation evidence manifest as a completion artifact.
- Add multi-surface shell contract (shared tokens, navigation, and terminology).
- Add conditional public-surface guidance (metadata, canonical URLs, sitemaps,
  structured data, search indexing intent).

### Area F — Cross-pack eval and deterministic checks

- Add a cross-pack golden-path eval in `experience-design` evals (XD is the
  terminal reviewer). Four fixture types: public marketing + docs, SaaS onboarding
  + workspace, internal dashboard, transactional service.
- Add deterministic checks in `tools/`: referenced skill exists, no phantom handoff,
  contract fields present for risk mode, pack-local contract copies have not drifted,
  evidence manifest entries present.
- All new integrated evals start report-only. Calibrate before promoting to gates.
- Update per-pack evals with weak fixtures for each discipline's failure modes.

---

## Implementation sequence

The eleven implementation specs below form a strict dependency DAG. The DAG is
encoded in `workspace.toml` `["ini-003".work].queue`.

```
RFC-0071 (this RFC — governance gate)
  └─ M1:  spec/digital-experience-contract
       ├─ M2a: spec/product-strategy-adoption-doctrine
       ├─ M2b: spec/product-engineering-shaping-doctrine
       │         (includes voice-and-microcopy → ux-writing rename)
       ├─      spec/xd-copy-direction          ← RFC-0062 implementation
       │    └─ M3a: spec/xd-skill-boundaries
       │         ├─ M3b: spec/xd-design-system-foundations
       │         └─ M3c: spec/xd-ia-archetypes-objects
       │              └─ M3d: spec/xd-state-reviewer-doctrine
       └─ M4:  spec/frontend-engineering-doctrine-update
            └─ M5:  spec/cross-pack-experience-eval (needs all M2–M4)
                 └─ M6:  spec/digital-product-guides-update
```

`spec/xd-copy-direction` must precede `spec/xd-skill-boundaries` (M3a) because
M3a's frontmatter near-miss guards reference `copy-direction` by name; the skill
must exist before those guards are installed.

---

## Alternatives considered

**Alt 1 — Canonical contract in `core` (D1 option B).** Single source of truth;
no drift. Rejected: introduces a hard cross-pack runtime dependency. An adopter
with only `experience-design` pack would pull in `core`'s contract schema at a
transitive distance. Independent installability is a charter commitment (RFC-0050
§ Charter, RFC-0030 §5). The drift check is the price of independence.

**Alt 2 — Extend `design-system` rather than a new `design-system-foundations`
skill (D3).** Simpler; one fewer skill. Rejected: `design-system` explicitly refuses
to produce values; it produces the method. Adding "and now produce the implementation"
to the same skill conflates two jobs with different reviewers, different outputs,
and different invocation moments. Confusion scales with skill length. The two-job
shape fails the catalogue's new-skill bar (distinct trigger, distinct output, distinct
review contract).

**Alt 3 — Extend `tone-of-voice` instead of implementing `copy-direction` (D4 original
plan).** One fewer skill, one less spec. Rejected: `copy-direction` was fully designed
in RFC-0062 with a distinct job (copy-voice positioning — the *what to sound like*)
vs. `tone-of-voice`'s job (marketing / acquisition copy voice — the *what to say and
how on a given surface*, which RFC-0062 more precisely names under `copy-direction`'s
scope). The RFC-0062 design is available; implementing it is less work than redesigning
the boundary.

**Alt 4 — Four separate FE skills for the four modes (D5).** Maximum granularity;
each mode is independently invocable. Rejected: the modes share the page/screen
contract, the evidence manifest, and the verification stack. Four skills would
duplicate these shared elements, creating four frontmatter descriptions requiring
synchronized near-miss maintenance. Mode is a contextual selection at invocation,
not a distinct natural-language user job. Context-conditional sections in one
SKILL.md is the right shape.

**Alt 5 — Add first-success to product-strategy without the causal metric tree
(D8 narrow option).** Safer w.r.t. growth pack boundary. Rejected: first-success
without a metric tree is an unverifiable aspiration. The adoption hypothesis is
only useful when it names the signal that confirms or refutes it. The metric tree
is that signal. What the metric tree does NOT include is the operational growth
machinery (experiments, paid acquisition, lifecycle campaigns) — those stay
deferred. The boundary is: hypothesis + metrics (this RFC) vs. programs (growth
pack).

---

## Open questions

**OQ1 — DTCG 2025.10 compatibility in `design-system-foundations` full mode.** DTCG
2025.10 is the current community group working draft. The full-mode implementation
should target it where practical, but "where practical" is context-dependent (some
design tooling doesn't yet export 2025.10 format). The spec for
`spec/xd-design-system-foundations` should document the compatibility posture and
the fallback for tooling that hasn't adopted 2025.10.

**OQ2 — `spec/xd-copy-direction` RFC-0062 errata.** RFC-0062's D3 accepted conversion
architecture (above-fold order, scroll section arc, CTA placement) as inside
`content-design`'s acquisition sub-path. That decision was made before the
`copy-direction` / `content-design` boundary was fully implemented. Once
`copy-direction` ships, a quick errata pass on RFC-0062 should confirm whether the
D3 boundary still holds or requires an amendment. This is a post-ship check, not a
blocker.

**OQ3 — `ux-writing` cross-pack reference update scope.** The rename from
`voice-and-microcopy` to `ux-writing` requires updating references in both
`product-engineering` and `experience-design` packs. A grep-verified count should
be recorded in `spec/product-engineering-shaping-doctrine` before the rename ships
(mirrors RFC-0066 D7's ~43-file verification requirement for experience pack renames).

---

## Follow-on work

The following items are explicitly out of scope for ini-003 and must not be
implemented as part of this initiative's specs:

- **Growth pack** — first-success and adoption hypothesis ownership is now
  in `product-strategy`. A future growth pack owns the operational programs
  (SEO, paid acquisition, lifecycle campaigns, experimentation operations,
  conversion optimization programs).
- **`voice-and-microcopy → ux-writing` in other adapters** — the rename scope
  is PE pack only. Other adapters referencing the old name are a follow-on sweep.
- **Promoting cross-pack eval to a gate** — all new evals start report-only.
  Promotion to gate requires calibration evidence from at least two weak-fixture
  runs and one real-product fixture.
- **DTCG platform outputs** — the `design-system-foundations` full mode targets
  DTCG 2025.10 "where practical." Generated platform outputs (Figma variables,
  iOS Swift UI tokens, Android Material tokens) are deferred until an adopter
  need surfaces.

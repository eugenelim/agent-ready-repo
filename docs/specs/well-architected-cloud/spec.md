# Spec: well-architected-cloud

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Contract:** none <!-- pure-markdown skill content; no API/event/RPC surface -->
- **Shape:** mixed <!-- skill prose + reference authoring across three skills; LLD pruned to decisions + decomposition -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A solution architect or founder using the `architect` pack designs *and* reviews
cloud architecture that meets the well-architected standard — across managed-service
clouds (AWS / Azure / GCP) **and** barebones primitives providers (Hetzner and its
class) — and the design skill now *converges* a design against the review skill instead
of producing a one-shot draft. Three things change, all pure-markdown, no subagents:

- **`architect-design` gains a concept-first stage, a by-construction pass, and a
  self-converging loop.** Before the full Google-style doc it produces a short
  *architecture concept* (problem + constraints, the one or two shapes on the table, the
  provider / provider-class, the top two-or-three load-bearing quality attributes) and
  waits for the user to agree the shape — this is where the design is made
  **well-architected by construction**. After drafting the full doc it runs a **convergence
  loop**: obtain a review pass, **auto-resolve the mechanical findings** by revising the
  doc without asking, re-review, repeat until none remain or a bounded cap is hit, then
  **surface only the judgment findings** (the tradeoff / sensitivity / business calls) to
  the human as decisions.
- **`architect-review` gains a well-architected / lens mode and tags every finding
  mechanical-vs-judgment.** Orthogonal to today's artifact-type routing, the WA mode
  reviews a design through a chosen **concern-lens** (security / FinOps / SRE / DR / data /
  compliance / green) and/or **workload-class lens** (ML / GenAI-agentic / SaaS /
  serverless) against the pillar spine, and emits a risk register of severity-tagged,
  scenario-anchored findings + a prioritized improvement plan. Every finding also carries a
  **mechanical** (determinate fix) vs **judgment** (human/business decision) tag — the
  signal the design loop consumes. Its existing **review-only mode** (critique someone
  else's artifact: findings + verdict, no auto-fix) is unchanged and remains the standalone
  default.

The loop is an *enhancement when both skills are present*; `architect-design` must still
work standalone (the pack forbids required composition), degrading to its own embedded
rubric self-check when `architect-review` is not installed. Success: for a given workload
and provider the skills surface the *provider-correct* pillar concerns (including, for
primitives providers, the capability gaps the provider does not supply), name the tradeoff
and sensitivity points rather than a flat checklist, auto-resolve the mechanical findings
so the human sees only real decisions, and do all of it without importing heavyweight
enterprise process, subagents, a new pack, or a scope change. The pack stays lean: no new
skills, no shared references, every `SKILL.md` under the pack's line ceiling.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Push all substantive new content into each skill's `references/`; keep every
  `SKILL.md` under the pack's <100-line progressive-disclosure principle — `SKILL.md`
  gets thin routing only. The convergence-loop *procedure* lives in a reference, not in
  `architect-design`'s `SKILL.md`.
- Honor "skill autonomy beats DRY": when two skills need the same content, **duplicate
  it per-skill with the one-line duplication note** the pack already uses.
- Make the loop **degrade gracefully**: when `architect-review` is not installed,
  `architect-design` runs the loop against its own embedded rubric self-check — the loop
  is never a hard dependency on a second skill.
- Treat **cross-pack composition with `research`** (the leading-edge path) as **optional-only**:
  use it when present, degrade to first-principles + flagged-novelty + lowered-confidence when
  absent. The README's "no required composition" principle is *intra-pack*; this is the first
  *cross-pack* reach, and it must stay optional — never a hard dependency on a second pack.
- Bound the loop: a fixed maximum number of review passes, and a **stasis escape** — a
  finding tagged mechanical that survives a pass is escalated to the human as a judgment
  finding rather than looped indefinitely.
- Run the loop's **review pass with reviewer independence** — prefer a fresh context (a new
  session, or the harness's review subagent where it has one); where that is unavailable, do
  a **disciplined cold re-read** that sets aside the authoring rationale. In every case seed
  the reviewer with the *artifact + agreed concept + constraints*, never the authoring
  chain-of-thought — independence must not mean reviewing blind. (This honors
  `architect-review`'s existing "no marking your own homework" anti-pattern.)
- Express the barebones-provider class as **generic cloud-primitives** reasoning with
  Hetzner as a named exemplar — the reusable substance is the primitives class, not
  Hetzner-specific structure.
- Keep mode/stage detection **inside the skill** (no user-facing flags); confirm provider /
  workload-class once only when genuinely ambiguous.
- Bump the pack version in `pack.toml` + `.claude-plugin/plugin.json`, regenerate
  `.claude-plugin/marketplace.json` via `make build-self` (the all-packs aggregation), and
  add a `docs/product/changelog.md` `[Unreleased]` entry in the same PR.

### Ask first

- Creating any **new skill** or **new pack** (the loop lives inside `architect-design`;
  do not add an `architect-loop` pack).
- Wording that changes `architect-design`'s default output for users who **never mention
  cloud** — confirm how universal the concept-first stage reads before finalizing.
- Adding any named provider beyond AWS / Azure / GCP / generic-primitives(Hetzner).

### Never do

- No new dependency, no new module boundary, no new top-level directory, **no subagents** —
  this is markdown skill content only, and the loop runs inline.
- Never auto-resolve a **judgment** finding (a tradeoff / sensitivity / business call);
  the loop only auto-resolves **mechanical** findings and surfaces judgment ones to the human.
- Never prescribe specific application / agent / UI frameworks (e.g. LangGraph, React,
  a named vector DB) as required — the toolkit reasons about architecture *quality*,
  boundaries, tradeoffs, and provider-fit, never framework choice. The **local-first**
  provider-class is bound by the same rule: it names the local→production delta + graduation
  path, never a local toolchain (no docker-compose recipes, no specific images).
- Never reproduce **ASVS / CASA** (or other) security *control checklists* in this pack — the
  security concern-lens stays at design altitude (trust boundaries, IAM design, data egress,
  OAuth scope minimization, assessability); route control-level verification to the repo's
  `security-reviewer` / `security-checklists`. CASA/ASVS are *named as a downstream gate*, not
  reproduced.
- Never let the concept template (`assets/concept.md`) grow into a second design doc — it stays
  a **one-page** shaping artifact; depth belongs in the full `design-doc.md` after the concept
  is agreed.
- Never ship **domain-specific content for a leading-edge domain** (e.g. an enterprise-brain /
  ontology / knowledge-stratum reference). The pack ships the *method* (`leading-edge-domains.md`);
  the *content* is researched per-engagement via the `research` skill, because living grey matter
  rots in a shipped file and would duplicate the `research` pack's job.
- Never import Track-2 enterprise **process**: no ARB-as-a-body, no submission/approval
  workflow, no gate authority, no multi-day ATAM ceremony, no TOGAF phases. Only the
  quality *techniques* (quality-attribute scenarios, tradeoff/sensitivity points,
  utility-tree-lite prioritization, the cross-cutting question bank) come across.
- Never couple the two skills via a shared/cross-referenced reference directory, and never
  make `architect-design` *require* `architect-review` to function.
- Never project `loop-cohort` (the work-loop supervisor state machine) into this pack, and
  never add a loop-management **script** or **state file**. The convergence loop is a
  **pure-prose, in-conversation procedure** — bounded by instructions, stasis-checked by the
  agent re-reading its own prior findings. A script would forfeit the pack's pure-markdown /
  zero-config / portable property and couple it to core machinery built for multi-agent code
  builds, not single-artifact design convergence.
- Never add Mermaid alternatives or publishing/integration surfaces (out of charter).

## Testing Strategy

Pure-markdown skill content, so verification mixes **goal-based checks** (structural,
mechanical) and **manual QA** (dogfooding the skills against committed brief fixtures).
No compressible code invariant, so no TDD.

- **Structural invariants — goal-based.** SKILL.md line ceiling; reference files exist at
  expected paths; no load-bearing cross-skill link; version bump consistent across
  `pack.toml`/`plugin.json`; `marketplace.json` regenerated; `lint-skill-spec` + `lint-packs`
  green; changelog entry present. Each is a one-liner (`wc -l`, `grep`, `make` target).
- **Skill behavior incl. the loop — manual QA, exercised by dogfooding.** Skill behavior
  only proves out by invoking it on a real brief and observing the artifact shape and the
  loop's convergence. Briefs are **committed fixtures** under
  `docs/specs/well-architected-cloud/fixtures/`, referenced by path so the gesture is
  replayable. This spans the full design→review→resolve flow (E2E-shaped manual QA).

## Acceptance Criteria

**`architect-design` — concept-first, by-construction, convergence loop**

- [x] Invoking `architect-design` on a design brief produces a **Stage-0 concept** first
  (≤ ~½ page: problem + constraints, 1–2 candidate shapes, provider / provider-class, top
  2–3 prioritized quality attributes) and expands to the full design doc only after the
  concept is acknowledged.
- [x] `architect-design` ships a **light concept template asset** (`assets/concept.md`),
  distinct from the existing heavy `assets/design-doc.md`, that the Stage-0 concept is drafted
  from. It is a **one-page** artifact in the spirit of the arc42 *Architecture Communication
  Canvas* ("elevator-pitch / zip-version", travel-light) — fields: **problem & context**,
  **constraints**, **1–2 candidate shapes** (one line each), **provider / provider-class**
  (+ the by-construction managed-vs-self-managed note), **top 2–3 prioritized quality
  attributes** (the utility-tree-lite pass, with *why*), **key tradeoff / open decision(s)**,
  and optional **open questions**. It carries **none** of the design doc's heavy sections
  (no full proposal, alternatives-with-rejection, risks table, or rollout).
- [x] The concept stage does **not** trip the existing *"just write the proposal section"*
  anti-pattern: the skill text distinguishes pre-full-doc *shaping* (carries context +
  constraints + the choice) from partial advocacy (a proposal stripped of those).
- [x] When a provider is named or inferred, the design names **how each relevant pillar**
  (Operational Excellence, Security, Reliability, Performance, Cost, + Sustainability) is
  *achieved on that provider*; for the **primitives class** it enumerates the
  **capability-gap categories the provider does not supply** (managed data tier, edge/CDN,
  managed identity, serverless, …) with **at least one concrete gap**, so the design names
  what it must build itself. (Specific named gaps are illustrative, not a pinned contract.)
- [x] The design surfaces at least one explicit **tradeoff point**, and a **sensitivity
  point** where one exists — not only a flat per-pillar list.
- [x] The by-construction pass supports a **local-first** provider-class (the founder on-ramp)
  alongside hyperscaler and primitives: it names the **local→production delta** (what local fakes
  that production must supply — TLS, real secrets, DB HA, object storage, CDN, observability) and
  the **graduation path** to a chosen provider class. It stays at architecture altitude and does
  **not** prescribe a local toolchain.
- [x] The concept stage **degrades gracefully for non-cloud design questions**: with no
  provider in play it still produces the Stage-0 concept (problem / constraints / shapes /
  quality attributes) without forcing provider selection or pillar-by-construction scaffolding.
- [x] The concept stage takes the **leading-edge path** (per `leading-edge-domains.md`) when no
  shipped pillar/lens/provider reference covers the domain: it flags the novelty, composes with
  the `research` skill (`applied`/`deep`) when available to survey current grey literature and
  synthesize an ad-hoc domain lens, and **degrades** (first-principles + flagged novelty + lowered
  confidence) when `research` is absent — never erroring or requiring it.
- [x] Leading-edge claims in the concept/design carry **source + confidence**, and any assumption
  resting on low-confidence / grey-lit evidence is classed as a **judgment** finding the loop
  surfaces, never auto-resolves.
- [x] After drafting the full doc, `architect-design` runs a **convergence loop**: it
  obtains review findings (from `architect-review` when installed, else from its embedded
  rubric self-check), **auto-resolves the mechanical findings** by revising the doc
  *without asking*, re-reviews, and repeats until no mechanical findings remain or the
  bounded pass cap is reached.
- [x] The loop **never auto-resolves a judgment finding**; it surfaces the judgment
  findings (tradeoff / sensitivity / business calls) to the user as an explicit decision list.
- [x] The loop **terminates**: a fixed pass cap, and a stasis escape that escalates a
  mechanical finding which survives a pass to the human rather than looping forever.
- [x] With `architect-review` **not installed**, `architect-design` still loops using its
  embedded rubric self-check — it does not error or require the second skill.
- [x] The loop's **reviewer-independence** handling is *documented* in `convergence-loop.md`
  (the checkable surface — the disposition itself is unobservable): it states the
  fresh-context-preferred → cold-re-read-floor ladder, the seed set (artifact + agreed concept +
  constraints, **not** the authoring narrative), and that the cold-read floor is **explicitly
  weaker isolation** than a fresh context.

**`architect-review` — well-architected / lens mode, finding tags, review-only mode**

- [x] `architect-review` detects a well-architected / lens review intent **orthogonally
  to** artifact-type routing and enters the WA mode.
- [x] The WA mode lets a **concern-lens** (security / FinOps / SRE / DR / data /
  compliance / green) and/or **workload-class lens** (incl. **GenAI/agentic**) be
  applied, inspecting against the pillar spine.
- [x] Every WA-mode finding carries a **mechanical** (determinate fix) vs **judgment**
  (human/business decision) tag, in addition to the existing severity tag — this is the
  signal `architect-design`'s loop consumes.
- [x] The mechanical-vs-judgment split is **operationally defined**, not just exemplified:
  `rubric-well-architected.md` states a decidable test — a finding is **mechanical** when its
  fix is fully determined by the pillar spine or a stated constraint with **no** business-value
  or risk-acceptance choice; **judgment** when resolving it requires choosing between defensible
  options (a tradeoff, a risk acceptance, **or a low-confidence / leading-edge assumption**). A
  reviewer can apply the test to a *novel* finding, not only the planted examples.
- [x] WA-mode output is a **risk register** of severity-tagged findings + a **prioritized
  improvement plan** + **documented risk-acceptance** + **documented non-risks**, reusing
  the skill's existing verdict + severity vocabulary.
- [x] Findings carry a **quality-attribute scenario** (source / stimulus / artifact /
  environment / response / response-measure) wherever a measurable claim is in play.
- [x] The existing **review-only mode** (critiquing an artifact authored elsewhere) is
  preserved: it emits findings + verdict and **does not auto-fix** — it is a critique, not
  a loop.

**Shared reference content (duplicated per skill, never shared)**

- [x] A generic **`cloud-primitives`** reference exists (Hetzner as named exemplar)
  carrying the **"capability gaps you must fill"** checklist, duplicated into each
  consuming skill with a duplication note.
- [x] A **`local-dev`** reference exists (the local-first provider-class) carrying the
  **local→production delta** + **graduation path**, architecture-altitude only (no toolchain
  prescription), duplicated into each consuming skill with a duplication note.
- [x] A **quality-attribute-scenario template**, a **tradeoff & sensitivity-point guide**, and
  the **pillar spine + cloud-agnostic distillation** exist as references in each consuming skill.
- [x] A **cross-cutting question bank** reference exists (strategic alignment, build-vs-buy/reuse,
  lock-in/exit, supportability-in-2-years, data ownership & integration contract, and
  **third-party security attestation / restricted-scope-data assessability** — names CASA/ASVS as
  a *downstream verification gate*, referenced not reproduced, control-level verification routed to
  `security-reviewer`/`security-checklists`).
- [x] A **GenAI/agentic lens** reference exists (prompt-injection, tool-use authz,
  data-egress-to-LLM, evals/observability, token cost), **distinct** from the existing
  managed-platform agentic *diagram* references (Bedrock AgentCore / AI Foundry / Vertex), and
  applying even when the agent runtime is self-hosted on primitives.
- [x] A **`leading-edge-domains`** reference exists describing the **method** for designing in a
  domain with no established pillar/lens/provider reference: detect novelty → (optionally) compose
  with the `research` skill in `applied`/`deep` mode to survey current grey literature with GRADE
  confidence → synthesize an *ad-hoc domain lens for this engagement* → carry source + confidence
  into the concept/design → degrade (design from first principles, flag novelty, lower confidence)
  when `research` is absent. It ships the **method only**, never domain-specific content.
- [x] A **`convergence-loop`** reference exists under `architect-design` describing the
  loop as a **pure-prose, in-conversation procedure (no script, no state file)**: review →
  auto-resolve mechanical → re-review → surface judgment, with the **reviewer-independence**
  handling (fresh-context-preferred / cold-re-read floor; reviewer seeded with
  artifact + concept + constraints), the pass cap, the stasis escape, and the
  no-`architect-review` degradation path.
- [x] `architect-diagram` gains a generic **cloud-primitives** diagram reference for
  parity with its existing `cloud-{aws,azure,gcp}.md` vocab.

**Process / gates**

- [x] Every `architect-*` `SKILL.md` remains under the pack's <100-line principle.
- [x] No inter-skill reference *sharing* is introduced: no load-bearing cross-skill link
  (a load/include directive pointing into another skill's `references/`). The prose
  duplication note that names a sibling file is the sanctioned exception and does not count.
- [x] `pack.toml` + `.claude-plugin/plugin.json` are bumped to **0.2.0** and consistent;
  `.claude-plugin/marketplace.json` is regenerated; `lint-skill-spec` + `lint-packs` are
  green; a `docs/product/changelog.md` `[Unreleased]` entry is added.

**Dogfood (manual QA — committed fixtures under `docs/specs/well-architected-cloud/fixtures/`)**

- [x] `fixtures/brief-agentic-hetzner.md`: enhanced `architect-design` yields a concept
  naming the primitives class + at least the data-tier and edge/CDN gaps, prioritizing
  Security (agentic) + Performance, and surfacing the self-host-inference-vs-external-LLM-API
  decision as a tradeoff / sensitivity point.
- [x] `fixtures/brief-agentic-hetzner.md` plants **two** findings that exercise the failure
  modes the Boundaries exist to prevent: (a) a cleanly-fixable mechanical finding (e.g. an
  unlabeled trust boundary) that the loop **auto-resolves** across iterations; (b) a mechanical
  finding the rubric **cannot determinately fix**, so the loop's **stasis escape** escalates it
  to the human rather than looping forever. The loop **surfaces** the self-host-vs-external
  decision as a judgment finding and does **not** auto-resolve it.
- [x] `fixtures/brief-agentic-hetzner.md`: `architect-review` WA mode under GenAI/agentic +
  security lenses produces a risk register naming the internal-data→external-LLM egress
  boundary and the A2UI surface-authority risk, with each finding mechanical/judgment-tagged.
- [x] `fixtures/brief-enterprise-brain.md` (a leading-edge domain with no shipped reference):
  `architect-design` takes the leading-edge path — flags novelty, composes with `research`
  (`applied`/`deep`) when available (else degrades + flags), synthesizes an ad-hoc enterprise-brain
  lens (memory types / knowledge stratums / provenance / governance), and surfaces the
  centralized-vs-federated-ontology decision as a judgment finding carrying source + confidence.
- [x] `fixtures/brief-local-first.md`: `architect-design` concept treats local-first as a
  legitimate starting topology, names the **local→production delta** (what local fakes) and a
  **graduation path** to a provider class, and prescribes **no** local toolchain.
- [x] `fixtures/brief-hyperscaler.md`: `architect-design` concept names provider-managed-service
  pillar achievement and does **not** apply the primitives "gaps" framing.
- [x] `fixtures/brief-non-cloud.md`: `architect-design`'s Stage-0 concept degrades gracefully —
  it shapes problem / constraints / choice / quality-attributes without forcing provider or
  pillar-by-construction scaffolding.

## Assumptions

- Technical: architect skills live at `packs/architect/.apm/skills/<skill>/{SKILL.md,references/,assets/}`, pure-markdown, ship no tests (source: `find packs/architect` — no test files)
- Technical: `architect-diagram` already ships `cloud-{aws,azure,gcp}.md` + `cloud-patterns.md` for diagram vocab; `architect-design` ships `nfr-checklist.md` + self-checks against `design-doc-rubric.md`; `architect-review` ships 6 genre rubrics (source: `ls packs/architect/.apm/skills/*/references`)
- Technical: SKILL.md line budget is tight — design 76 / diagram 96 / review 92 vs the pack's <100-line principle, so new detail (incl. the loop procedure) lives in `references/` (source: `wc -l` + `packs/architect/README.md:63`)
- Technical: `marketplace.json` lives at `.claude-plugin/marketplace.json` (architect at line 8) and is regenerated by `make build-self` via the all-packs aggregation (source: `find` + `packages/agentbundle/agentbundle/build/self_host.py:494,1028`)
- Process: in-charter → spec, not RFC — the README defers EA-platform TOGAF/ArchiMate/Wardley + integration/publishing, not cloud well-architected (source: `packs/architect/README.md:68-80`)
- Process: pack forbids inter-skill reference sharing and required composition; refs are duplicated per-skill with a note and each skill stands alone (source: `packs/architect/README.md:50-54,130-133`). This principle is **intra-pack**; the leading-edge path extends it to an **optional cross-pack** reach to `research` (degrades when absent) — a new category the README doesn't yet name, surfaced here rather than folded silently (source: README scope read + user direction 2026-06-12)
- Process: pack design excludes subagents by design — the loop must stay inline / agent-free (source: `packs/architect/README.md:72-73`)
- Process: distribution model projects content to a scope-specific *path*, not different content per scope — so a "lean user / loop repo" split would need two packs; instead the loop lives inline in `architect-design` and no scope/pack change is needed (source: `packages/agentbundle/agentbundle/scope.py` + `commands/install.py` scope branches are path/mode, not content)
- Process: user-visible skill prose change needs a `docs/product/changelog.md` `[Unreleased]` entry in the same PR (source: `docs/CONVENTIONS.md:466-467,602-603`)
- Process: non-cosmetic pack content change bumps version in `pack.toml` + `.claude-plugin/plugin.json` (source: `docs/CONVENTIONS.md:537` + repo convention)
- Product: audience = solution architects / founders / engineers designing or reviewing cloud architecture across AWS/Azure/GCP/Hetzner via the architect pack (source: user confirmation 2026-06-12)
- Product: scope is Track 1 only — no Track 2 artifacts (SAD authoring, ARB workflow, value-stream/capability mapping, DDD) (source: user confirmation 2026-06-12)
- Product: the barebones provider is expressed as generic cloud-primitives with Hetzner as exemplar (source: user confirmation 2026-06-12)
- Product: a **local-first** provider-class is the founder on-ramp (concept stage, not a new mode) — names the local→production delta + graduation path at architecture altitude, never a local toolchain (source: user confirmation 2026-06-12)
- Product: the architecture loop lives inside `architect-design`, agent-free, with `architect-review` retaining a standalone review-only mode; no `architect-loop` pack, no subagents (source: user confirmation 2026-06-12)
- Product: the loop is a pure-prose in-conversation procedure — no `loop-cohort`, no loop script, no state file (source: user confirmation 2026-06-12)
- Product: the loop's review pass runs with reviewer independence — fresh context preferred (new session / harness subagent), cold-re-read floor otherwise, seeded with artifact + concept + constraints (source: user confirmation 2026-06-12)
- Technical: CASA (Google Cloud Application Security Assessment) is built on OWASP ASVS, tiered (T1 self-scan → T3 lab-verified), and triggered by restricted-scope OAuth access to Google user data; folded in only as a *design-stage assessability pointer*, with control verification routed to the repo's ASVS-anchored `security-checklists`/`security-reviewer` (source: web — appdefensealliance.dev/casa, support.google.com/cloud/answer/13465431 + user confirmation 2026-06-12)
- Product: `architect-design` ships a light one-page concept template asset (`assets/concept.md`), modeled on arc42's Architecture Communication Canvas (travel-light), explicitly NOT a second design doc (source: web — arc42.org / canvas.arc42.org + user confirmation 2026-06-12)
- Technical: the `research` pack is user-scope-default (co-resides with `architect`) and its `research` skill carries `applied` (practitioner grey-literature, GRADE-confidence) and `deep` (auto devil's-advocate) modes — the composition target for the leading-edge path (source: `packs/research/pack.toml` + `packs/research/.apm/skills/research/SKILL.md`)
- Product: the pack handles leading-edge domains by shipping the *method* (`leading-edge-domains.md`) + composing with `research`, never shipping domain-specific content (which rots / duplicates research); composition is optional with a first-principles degradation (source: user confirmation 2026-06-12)
- Product: version target is 0.1.0 → 0.2.0 minor bump; `architect-diagram` gains a cloud-primitives diagram reference for parity (source: user confirmation 2026-06-12)

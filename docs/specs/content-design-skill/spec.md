# Spec: content-design-skill

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0062 (D1–D5), ADR-0024 (guardrails A+B, framework-agnosticism), RFC-0050 (experience pack design-thread completeness bar)
- **Brief:** none
- **Contract:** none — pure-markdown skill + asset template; no API/event/RPC interface. The content brief is a markdown artifact template (skill `assets/`), not a versioned interface contract.
- **Shape:** integration — a new skill directory under `packs/experience/.apm/skills/`; method-authoring, not application code.

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A `content-design` skill is added to the `experience` pack. Designers, product
people, and solo builders use it to produce a per-surface content brief — a
text-first document answering "what does this surface need to say, for whom, in
what form, to achieve what objective" — before any wireframe or screen flow is
started. The skill fills the first missing link in the experience pack's design
thread: it runs after `map-customer-journey` (or elicits inline when no journey
exists) and before `map-screen-flow`. It routes across two surface types:
**acquisition surfaces** (marketing pages, landing pages, web onboarding flows)
and **product/reference surfaces** (help pages, feature reference, in-product
wayfinding). Success means a designer can invoke `content-design` cold, answer a
structured elicitation sequence, and receive a content brief that the
`map-screen-flow` copy slot can reference directly, with no ad-hoc page strategy
required.

## Boundaries

### Always do

- Author `SKILL.md` + `references/` + `assets/` + `evals/` under
  `packs/experience/.apm/skills/content-design/`
- Keep every file pure-markdown per ADR-0024: point to named standards (Schwartz
  five-stage awareness ladder, StoryBrand seven-element arc, Conversion-Centered
  Design seven principles, Nava PBC text-prototype model) — never reprint their
  framework text verbatim
- Resolve the artifact path via RFC-0050 D6's config→default→discover-by-marker
  contract: default `docs/design/content/<slug>.md` with `type: content-brief` in
  frontmatter; document this in SKILL.md and a `references/agentbundle-layout.md`
- Add `content-design` to `[pack.evals] skills` in `packs/experience/pack.toml`
  and ship `evals/eval_queries.json` + `evals/evals.json` under the skill directory
- Run `tools/lint-experience-agnostic.py` after every SKILL.md edit; keep it clean

### Ask first

- Any edit to frozen governance (RFC-0033, ADR-0024, the Shipped `design-craft-pack`
  spec, or README index rows that name `design-craft` as historical record)
- Widening the acquisition sub-path beyond structural direction (what to say in what
  order) into analytics, CRO tooling, or SEO keyword targeting
- Extending surface-type routing beyond the two chartered types (acquisition,
  product/reference) — e.g. email, native mobile onboarding, or print — which are
  deferred per RFC-0062

### Never do

- Reprint the Schwartz ladder, StoryBrand arc, or CCD principles verbatim — name
  and reference them; never quote them wholesale
- Produce a copy template, values table, or pre-written copy strings
- Produce an analytics framework, CRO measurement guide, or SEO keyword plan
- Add hooks, engines, validators, or in-pack linters — the agnosticism lint in
  `tools/` is the enforcement surface (ADR-0024)

## Testing Strategy

All verification is goal-based or manual QA — there is no testable runtime logic.

- **Goal-based:** `tools/lint-experience-agnostic.py` exits 0 on `packs/experience/`
  after the skill lands (stack-token / values-table cleanliness).
- **Goal-based:** `grep` confirms required frontmatter fields (`name:`,
  `description:`) and numbered procedure steps (≥5) present in SKILL.md.
- **Goal-based:** `cat packs/experience/pack.toml` confirms `content-design` is
  present in the `[pack.evals] skills` list.
- **Goal-based:** `find packs/experience/.apm/skills/content-design/evals/ -name "*.json"`
  returns both eval files.
- **Manual QA:** Cold-prompt `content-design` with a sample persona and acquisition
  surface. Confirm the output content brief includes: surface type declaration,
  audience awareness level, narrative arc selection (with named framework and
  applicability rationale — verifying RFC-0062 D1 "GOV.UK / Nava PBC canonical
  discipline name" maps to the description's stated purpose), scroll section
  assignments with per-section job, above-fold structure (headline + subheadline),
  primary CTA and transitional CTA, success metric, and the
  `docs/design/content/<slug>.md` artifact path. Repeat for a product/reference
  surface: confirm user task, format selection (prose/steps/table/diagram), content
  hierarchy (must-say → probably-say → might-say), and completion metric appear.

## Acceptance Criteria

- [x] `packs/experience/.apm/skills/content-design/SKILL.md` exists; frontmatter
  includes `name: content-design` and a non-empty `description:` field; Procedure
  section has ≥5 numbered steps (verified by counting only within `## Procedure`,
  not the full file); Anti-patterns section present.
- [x] Acquisition sub-path procedure names: the Schwartz five-stage awareness ladder
  as the audience-level elicitation reference; StoryBrand and CCD as the two
  narrative-arc choices with their applicability conditions (audience awareness level
  drives the selection); scroll section assignment (each section gets one job:
  problem, guide proof, plan, stakes, CTA); above-fold structure contract (headline +
  subheadline answering what/who/why); primary and transitional CTA definition;
  success metric naming.
- [x] Product/reference sub-path procedure names: user task elicitation; content
  format selection (prose / steps / table / diagram, matched to task type); content
  hierarchy prioritisation using the Nava PBC must-say → probably-say → might-say
  model; completion metric (task completion rate or search resolution).
- [x] Artifact path `docs/design/content/<slug>.md` with `type: content-brief` is
  documented in SKILL.md and resolves via the three-tier layout contract (config →
  default → discover-by-marker) per RFC-0050 D6; `content-brief` is named as an
  extension to the pack's existing marker set.
- [x] `tools/lint-experience-agnostic.py` exits 0 on `packs/experience/` after the
  skill lands; no stack token or values-table shape violation introduced.
- [x] `content-design` is listed in `[pack.evals] skills` in
  `packs/experience/pack.toml`; `evals/eval_queries.json` and `evals/evals.json`
  exist under `packs/experience/.apm/skills/content-design/evals/`.
- [x] The skill is standalone-useful: it elicits persona and outcome inline when no
  `map-customer-journey` output is provided; no upstream artifact is required to
  invoke it.
- [x] The skill's hand-off step names `copy-direction` (for copy voice grounding) and
  `map-screen-flow` (for screen sequencing) as the downstream consumers of the
  content brief.
- [x] SEO keyword targeting, CRO tooling, and user research production are explicitly
  listed as out of scope in the SKILL.md Anti-patterns or a clearly marked scope note.
- [x] Experience-reviewer scope extension (OQ1) is deferred to a follow-on RFC;
  the SKILL.md hand-off step notes this explicitly; a `docs/backlog.md` entry
  under `### experience-reviewer-content-brief-scope` tracks the deferral with a
  reference to RFC-0062 OQ1 as the open question.
- [x] This spec ships in the same PR as `copy-direction-skill` (the two skills
  share a single pack version bump at 0.4.2 → 0.5.0 and a single `build-self` run;
  landing content-design alone would add a public skill with no semver record).
- [x] Acquisition sub-path elicitation in `references/surface-routing.md` includes an audience action goal step that names four action goals — Decision (commit), Understanding (grasp a concept), Execution (complete a task now), Belief shift (change mental model) — and states how each informs arc selection; SKILL.md Step 3's acquisition sub-path references this step.
- [x] `references/narrative-arc.md` names the Pyramid Principle (conclusion-first, top-down hierarchy, logical clustering, structured progression) as a third named framework for analytical and structured product/reference surfaces where the reader's primary action goal is Decision or Understanding at high prior knowledge; SKILL.md Step 3's product/reference sub-path loads `references/narrative-arc.md` so the Pyramid Principle is reachable by that path.

## Assumptions

- **Technical:** `tools/lint-experience-agnostic.py` already enforces ADR-0024
  guardrails on all Markdown under `packs/experience/` and will catch any
  values-table or stack-token leak without additional tooling.
  (source: tool inspection 2026-07-18)
- **Technical:** Pack evals follow the shape established by `aesthetic-direction`:
  `evals/eval_queries.json` (activation trigger phrases) + `evals/evals.json`
  (Tier-4 LLM-judge rubric per ADR-0028/RFC-0037).
  (source: file inspection 2026-07-18)
- **Product:** RFC-0062 D1–D5 are accepted as binding decisions governing this spec's
  scope, naming, surface-type routing, and the conversion-architecture inclusion
  argument (D3: CTA placement and scroll sections are structural direction, not
  analytics). The RFC has not been formally closed but the spec authoring proceeds on
  the Draft decisions pending adversarial review.
  (source: RFC-0062 Draft + user engagement 2026-07-18)
- **Product:** OQ1 (experience-reviewer scope extension) is resolved as deferred —
  extend experience-reviewer in a follow-on RFC rather than blocking this spec.
  (source: RFC-0062 OQ1 recommendation)

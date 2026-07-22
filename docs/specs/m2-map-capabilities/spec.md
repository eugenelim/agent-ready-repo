# Spec: m2-map-capabilities

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (M2 · Strategic Shaping; M2.5 map-capabilities); Sub-RFC pe-pack-strategic-shaping (RFC-00XX) not yet accepted — this spec proceeds under resolved constraints and may require minor revision on acceptance.
- **Brief:** none
- **Discovery:** none
- **Contract:** none — prompt-only skill (Charter Principle 3); no machine interface
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A product engineer or PM who has placed a bet runs `map-capabilities` in a
**single guided session** and gets a **Capability Map** typed artifact that
enumerates all capability areas the committed bet implies — organized by L1
domain, each entry carrying a stable id, Wardley evolution stage, strategic
criticality, and make/buy/partner/adopt disposition — plus a suggested build
sequence (Build-disposition capabilities only) the team can use to seed M3–M6
spec-writing and brief-authoring.

The skill reads `bet.md` as its required anchor and opportunistically reads
`situation-framing.md` for Wardley capability assessments already completed at
step 1. It elicits or confirms a product vision (1–2 sentences) and proposes
candidate L1 domains from the bet and vision for PE confirmation before
capability elicitation begins. The artifact is committed to
`<output_dir>/shaping/<slug>/capability-map.md` (the designed default for
`output_dir` is `docs/product/`; resolved via config-driven three-tier procedure).
The skill then suggests (but does not write) the `workspace.toml` shaping-queue
transition.

**Scope:** step 6 (final step) of the PE six-step shaping sequence — after
`place-bet`, before `lean-canvas` / `author-brief`. Does not produce a brief.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- **Confirm initiative scope before any elicitation.** When the input is clearly
  a single feature or endpoint (below capability level), name the altitude
  mismatch and redirect to `frame-intent`. When altitude is genuinely ambiguous,
  ask — never force one level.
- **Reuse the active shaping slug** — when working a `[shaping_queue]` item the
  slug is that item's slug; when invoked standalone, ask the PE which slug path
  to write to. Surface and confirm when multiple candidate paths exist under
  `<output_dir>/shaping/`. Never mint a new slug.
- **Read `bet.md`** from the resolved shaping path as the required anchor; surface
  the option, rationale, and appetite as context before capability elicitation.
  When absent, offer to run `place-bet` first; if the PE declines, proceed on
  free-form vision input and note the reduced traceability in the artifact.
- **Elicit or confirm a product vision** (1–2 sentences naming the outcome the
  initiative pursues) before capability elicitation begins. Do not silently derive
  a vision from the bet without surfacing it for PE confirmation.
- **Read `situation-framing.md` opportunistically** from the same shaping slug
  path; when present, carry its Wardley capability assessments as pre-assessed
  entries seeding the map. When absent, proceed on bet + vision without blocking.
- **Propose candidate L1 domains** derived from the bet and vision for PE
  confirmation before eliciting individual capabilities. Never fabricate domains
  from an underdetermined bet — when the bet is too thin to derive domains, elicit
  more context first. When the bet implies zero capability areas after elicitation,
  surface this explicitly and ask the PE whether to expand scope or confirm the
  map is empty.
- **Define the Wardley stage and strategic-criticality vocabularies once** in the
  SKILL.md body — inline, so Wardley-unfamiliar adopters can follow:
  *Genesis* — novel/uncertain; explore. *Custom-built* — hand-crafted; invest to
  differentiate. *Product* — widely available; buy/adopt over build.
  *Commodity* — utility; competing here is waste.
  *Differentiating* — creates competitive advantage; prioritize for Build.
  *Parity* — table stakes; match the market, do not over-invest.
  *Utility* — necessary overhead; minimize cost; Buy or Adopt.
- **Enumerate capabilities organized by L1 domain.** For each domain, emit a
  markdown table of capability entries with fields: id (kebab-case stable slug),
  name, description (one sentence), Wardley stage, strategic criticality,
  disposition, and dependencies (referencing other capability ids, or empty).
- **Define the four-term disposition vocabulary once** in the artifact:
  *Build* — Genesis/Custom-built; team owns full lifecycle; core to differentiation.
  *Buy* — Product/Commodity-stage commercial product or SaaS; standard function.
  *Partner* — mid-maturity; external expertise accelerates delivery; shared governance.
  *Adopt* — open-source or standards-body solution; minimal customization; distinct
  from Buy (no license, but carries maintenance obligation).
- **Flag Commodity-stage capabilities rated Differentiating** as a strategic
  tension requiring explicit PE acknowledgment before finalizing the map entry.
- **Emit a "Suggested build sequence"** listing only `Build`-disposition
  capabilities — dependency-ordered and Wardley-informed (Genesis/Differentiating
  first; blockers before dependents), with one-sentence rationale per position.
  Non-Build capabilities appear in the domain tables; their disposition is the
  action (procure, partner, adopt), not spec-writing. Mark the section explicitly
  as a recommendation; final sequencing authority stays with the PE.
- **Elicit L2 depth only when the bet explicitly scopes into a capability area.**
  Default depth is L1. L3 decomposition belongs in spec-writing, not here.
- **Emit `capability-map.md`** at `<output_dir>/shaping/<slug>/capability-map.md`
  with stable marker (`type: capability-map`) and YAML frontmatter carrying:
  `type`, `slug`, `date`, `bet-source` (path to `bet.md`), `vision`.
- **Resolve the write path via config-driven three-tier procedure**
  (repo-scope `agentbundle-layout.toml [product]` → user-scope →
  two-branch elicitation). Realpath-expand and symlink-resolve; reject `..`
  escapes and any symlink chain that exits the intended root. Surface the resolved
  absolute path before writing.
- **Suggest a `workspace.toml` shaping-queue transition** — print the TOML snippet;
  direct the user to `capture-work` or manual edit. Do not write to
  `workspace.toml`.
- **Degrade cleanly when `lean-canvas` / `author-brief` are not detected** — add
  a "Next step readiness" section to the artifact naming the missing skill and
  describing what brief-authoring provides. Artifact emission continues unblocked.

### Ask first

- Before decomposing any capability to L2 depth (only when the bet explicitly
  names that area as deeply in-scope).
- Before overwriting an existing `capability-map.md` at the resolved slug path —
  surface the existing file and confirm before overwriting.
- Before writing to any path that resolves outside the repo tree or via a
  realpath-escaped symlink.
- Before accepting input that is ambiguous in altitude (initiative vs. feature).

### Never do

- **Never** write to `workspace.toml` directly — the skill suggests the transition;
  the user commits the workspace change.
- **Never** write to a literal hardcoded path — always resolve via the three-tier
  config procedure; `docs/product/` is the designed default, not a constant.
- **Never** mint a new slug — reuse the shaping queue item slug or ask when
  standalone.
- **Never** decompose to L3 or deeper without explicit ask — L3 granularity
  belongs in spec-writing.
- **Never** produce a brief — `lean-canvas` / `author-brief` own that handoff.
- **Never** exceed 100 lines in `SKILL.md`.
- **Never** ship an engine, script, runtime hook, or validator in this skill.

## Testing Strategy

This is a prompt-only skill (Charter Principle 3) — no compressible invariant
logic. Verification is goal-based for structure and manual QA for judgment.

- **Skill file and lint gates: goal-based.** File exists at the conventional path,
  `tools/lint-skill-spec.py` passes, `lint-packs` passes, <100 lines, valid
  frontmatter.
- **Template asset: goal-based.** `assets/capability-map-template.md` exists with
  YAML frontmatter fields (`type`, `slug`, `date`, `bet-source`, `vision`),
  vocabulary definition block, L1 domain sections (each with a markdown table
  including an `id` column), and a "Suggested build sequence" section.
- **Path safety (AC10): goal-based grep.** `grep -F "reject"` on SKILL.md body
  (≥1 match — unique to the `..`/symlink-escape reject prose).
- **Bet-absent degrade (AC3): goal-based grep.** `grep -F "reduced traceability"`
  on SKILL.md body (≥1 match — unique to the absent-bet branch).
- **Situation-framing absent branch (AC4): goal-based grep.**
  `grep -F "proceed on bet"` on SKILL.md body (≥1 match — unique to the
  absent situation-framing branch).
- **Commodity-Differentiating tension flag (AC8): goal-based grep.**
  `grep -F "strategic tension"` on SKILL.md body (≥1 match).
- **Next step readiness degrade (AC13): goal-based grep.**
  `grep -F "Next step readiness"` on SKILL.md body (≥1 match).
- **Skill behavior (domain proposal, capability elicitation, disposition,
  tension flagging, sequencing, artifact emission): manual QA.** Two live runs
  exercised in the implementing PR — one on the worked-example topic and one on
  a distinct second topic — demonstrating slug-derivation, no-collision, domain
  organization, Wardley annotation, disposition vocabulary, and the suggested
  build sequence.
- **Diátaxis guide: goal-based for file existence, manual QA for accuracy.**
  Guide at `docs/guides/product-engineering/how-to/map-capabilities.md`.
- **Projection: goal-based.** `lint-packs`, `validate`, and `build` exit 0.
  Adopter-cleanliness verified by grep over SKILL.md body (no RFC-NNNN, no
  `agent-ready-repo`). `make build-self` is not run — the PE pack is user-scope
  and excluded from `_DEFAULT_SELF_HOST_PACKS`.

## Acceptance Criteria

- [x] **AC1.** `map-capabilities` ships at
  `packs/product-engineering/.apm/skills/map-capabilities/SKILL.md` — <100
  lines, valid frontmatter, passes `tools/lint-skill-spec.py` and `lint-packs`.

- [x] **AC2.** A template asset ships at
  `packs/product-engineering/.apm/skills/map-capabilities/assets/capability-map-template.md`
  with: YAML frontmatter (`type: capability-map`, `slug`, `date`, `bet-source`,
  `vision`); a vocabulary definition block (Build / Buy / Partner / Adopt, one
  sentence each); one or more L1 domain `##` sections each containing a markdown
  table with columns for capability id, name, description, Wardley stage, strategic
  criticality (Differentiating / Parity / Utility), disposition, and dependencies;
  and a "Suggested build sequence" section.

- [x] **AC3.** The skill reads `bet.md` from the resolved shaping path as the
  required input anchor. When `bet.md` is absent, the skill offers to run
  `place-bet` first; if the PE declines, the skill proceeds on free-form vision
  input and records in the artifact that reduced traceability applies. The SKILL.md
  body contains explicit prose specifying the absent-bet branch (goal-based grep:
  `grep -F "reduced traceability"` on SKILL.md body, ≥1 match).

- [x] **AC4.** The skill reads `situation-framing.md` opportunistically from the
  same shaping slug path; when present, carries its Wardley capability assessments
  as pre-assessed entries. When absent, the skill proceeds on bet + elicited vision
  without blocking. The SKILL.md body contains explicit prose for the absent branch
  (goal-based grep: `grep -F "proceed on bet"` on SKILL.md body, ≥1 match).

- [x] **AC5.** Before capability elicitation, the skill elicits or confirms a
  product vision (1–2 sentences). The vision is recorded in the `capability-map.md`
  YAML frontmatter under `vision`.

- [x] **AC6.** Before eliciting individual capabilities, the skill proposes
  candidate L1 domains derived from the bet and vision for PE confirmation. When
  the bet is too thin to derive domains, the skill elicits more context before
  proposing. When elicitation produces zero capability areas, the skill surfaces
  this explicitly and asks the PE whether to expand scope or confirm the map is
  empty — it does not silently emit an empty artifact.

- [x] **AC7.** The skill enumerates capabilities organized by L1 domain. For each
  domain, it emits a markdown table of capability entries. Each entry carries:
  id (kebab-case stable slug), name, description (one sentence), Wardley stage
  (Genesis / Custom-built / Product / Commodity), strategic criticality
  (Differentiating / Parity / Utility), disposition (Build / Buy / Partner /
  Adopt), and dependencies (referencing other capability ids, or empty). The
  Wardley stage, strategic-criticality, and disposition vocabularies are defined
  in the SKILL.md body. L2 depth is elicited only when the bet explicitly scopes
  a capability area; L3 is not produced.

- [x] **AC8.** When any capability entry is Commodity-stage and rated
  Differentiating, the skill flags it as a strategic tension and requires explicit
  PE acknowledgment before finalizing that entry. The SKILL.md body contains
  explicit prose specifying this flag (goal-based grep: `grep -F "strategic
  tension"` on SKILL.md body, ≥1 match).

- [x] **AC9.** The artifact includes a "Suggested build sequence" section listing
  only `Build`-disposition capability ids in dependency-order and Wardley-informed
  priority (Genesis/Differentiating first; blockers before dependents), with a
  one-sentence rationale per position. Non-Build capabilities appear in the domain
  tables but are excluded from this section (their disposition is the action).
  The section is explicitly marked as a recommendation; final sequencing authority
  rests with the PE.

- [x] **AC10.** The skill emits `<output_dir>/shaping/<slug>/capability-map.md`
  with stable marker `type: capability-map`. When working a shaping queue item,
  the slug is that item's slug. When invoked standalone, the skill asks the PE
  which slug to write to; when multiple candidate paths exist under
  `<output_dir>/shaping/`, it surfaces them and asks before proceeding. The skill
  never mints a new slug. A re-run on an existing slug confirms before overwriting.
  A run on a distinct second slug writes to a different path; no collision.

- [x] **AC11.** The skill resolves the write path via the config-driven three-tier
  procedure (repo-scope `agentbundle-layout.toml [product]` → user-scope →
  two-branch elicitation); realpath-expands and symlink-resolves the path; rejects
  `..` escapes and any symlink chain that exits the intended root; surfaces the
  resolved absolute path before writing. The SKILL.md body contains explicit prose
  for the reject step (goal-based grep: `grep -F "reject"` on SKILL.md body,
  ≥1 match).

- [x] **AC12.** After the artifact is written, the skill suggests a `workspace.toml`
  shaping-queue transition — printed as a TOML snippet with direction to apply via
  `capture-work` or manual edit. The skill does not write to `workspace.toml`.

- [x] **AC13.** When `lean-canvas` / `author-brief` are not detected in the
  available skills, the artifact adds a "Next step readiness" section naming the
  missing skill and describing what brief-authoring provides. Artifact emission
  continues unblocked. The SKILL.md body contains explicit prose specifying this
  degrade behavior (goal-based grep: `grep -F "Next step readiness"` on SKILL.md
  body, ≥1 match).

- [x] **AC14.** A worked example ships at
  `packs/product-engineering/.apm/skills/map-capabilities/examples/`
  demonstrating: bet intake → product vision confirmation → domain proposal → L1
  domain enumeration with stable ids, Wardley annotations, and dispositions (≥3
  domains, ≥2 capabilities per domain including ≥1 Build and ≥1 non-Build) →
  suggested build sequence (Build-only) → `capability-map.md` artifact.
  Adopter-clean (no RFC-NNNN, no `agent-ready-repo` references).

- [x] **AC15.** A Diátaxis how-to guide ships at
  `docs/guides/product-engineering/how-to/map-capabilities.md` covering: when to
  run `map-capabilities` (after `place-bet`, before brief-authoring); how to read
  the Wardley + strategic-criticality annotations; how to use the suggested build
  sequence (Build-disposition capabilities) to seed the M3–M6 spec queue.

- [x] **AC16.** `lint-packs`, `validate`, `build`, and the `packages/agentbundle`
  pack/contract tests exit 0. Grep over SKILL.md body confirms no adopter-facing
  internal-catalogue references. `make build-self` is not run — the PE pack is
  user-scope, excluded from `_DEFAULT_SELF_HOST_PACKS`, confirmed in plan.

## Assumptions

- **A1.** RFC-00XX · pe-pack-strategic-shaping has not been accepted. This spec
  proceeds under boundary decisions already resolved in RFC-0064; minor revision
  may be required on sub-RFC acceptance. (source: `docs/specs/m2-frame-situation/spec.md` A1)
- **A2.** The PE six-step sequence is anchored in RFC-0064 and stable enough to
  name in the skill body without the sub-RFC. (source: `docs/rfc/0064-ini-001-ai-native-ecosystem.md`)
- **A3.** Each capability entry carries seven fields: id, name, description, Wardley
  stage, strategic criticality, disposition, dependencies. The id field is a
  kebab-case stable slug enabling stable cross-references (dependencies, build
  sequence) without name-change fragility. Field set derived from BIZBOK/TOGAF BCM
  practice + Wardley mapping literature; "Adopt" is a valid distinct term for
  OSS/open-standards absorption (not yet in formal BCM standards; defined in the
  artifact). (source: research agent 2026-07-21 — BIZBOK, TOGAF, Wardley glossary,
  ITONICS, Haberlah)
- **A4.** L1 + selective L2 is the correct depth; L3 belongs in spec-writing.
  (source: BIZBOK/TOGAF via research agent 2026-07-21)
- **A5.** Capabilities are organized by L1 domain section (not grouped by Wardley
  stage) — stage annotates entries within domains. Domain grouping aligns with how
  briefs are written; Wardley-stage grouping conflates portfolio view with heat map.
  (source: Wardley Maps glossary via research agent 2026-07-21)
- **A6.** "Suggested build sequence" is included (Build-disposition only), marked
  as recommendation. Including sequencing is contested in BCM practice; the counter-
  argument is stronger for a shaping artifact that feeds specs immediately.
  (source: Productboard sequencing logic + research agent 2026-07-21)
- **A7.** Wardley stage and strategic-criticality vocabulary definitions belong in
  the SKILL.md body (inline, matching `frame-situation` A3 precedent). This tightens
  the 100-line budget — acknowledged as a risk in the plan. (source: `m2-frame-situation/spec.md` A3)
- **A8.** `docs/guides/product-engineering/how-to/` exists; `map-capabilities.md`
  guide does not yet exist. (source: `ls docs/guides/product-engineering/how-to/`,
  2026-07-21)
- **A9.** `workspace.toml` write-back is the `capture-work` front door's
  responsibility; this skill suggests verbally. (source: RFC-0064 Amendment #3;
  `docs/specs/m2-frame-situation/spec.md` A5)

# Plan: m2-map-capabilities

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

The whole deliverable is a single new **prompt-only skill** —
`packs/product-engineering/.apm/skills/map-capabilities/SKILL.md` — plus a
template asset, worked example, and how-to guide. No engine, script, or contract
file (Charter Principle 3).

The shape mirrors other M2 skills (`place-bet`, `identify-opportunities`): the
SKILL.md body defines the procedure and artifact schema; the executing agent
follows it to produce the typed artifact; path resolution is config-driven
three-tier. The key distinctive: this is the terminal step of the shaping sequence
and introduces the domain-organized capability table pattern plus the Wardley ×
strategic-criticality dual-annotation.

`make build-self` is **not** a verification gate — the PE pack is user-scope and
excluded from `_DEFAULT_SELF_HOST_PACKS`. Verification uses `lint-packs`,
`validate`, and `build`, matching sibling specs.

Order of operations: template asset first (T1) so the artifact schema is settled
before SKILL.md references it (T2); worked example (T3, requires two runs for
slug no-collision proof) and how-to guide (T4) in parallel after T2;
lint/build (T5) last.

## Constraints

- **RFC-0064 M2.5** — `map-capabilities` = step 6, terminal; reads `bet.md`;
  produces capability map anchoring M3–M6.
- **RFC-0064 D5** — capability maps are committed artifacts in `docs/product/shaping/`.
- **RFC-0064 Amendment #3** — workspace.toml write-back is `capture-work`'s
  responsibility; this skill suggests verbally only.
- **Charter Principle 3** — prompt-only; no runtime engine, script, or validator.
- **PE pack style** — SKILL.md <100 lines; depth in `assets/` only.
- **Phase-slice doctrine** — skill ships WITH its how-to guide (AC14).
- **File-per-slug path** — `<output_dir>/shaping/<slug>/capability-map.md`;
  slug in path prevents collision on multiple initiative runs.

## Construction tests

**Integration:** one manual-QA run on the worked example from T3 — end to end
from `bet.md` intake to committed `capability-map.md` — recorded in the PR as
the primary behavior verification (AC13 evidence).

**Grep assertions (all goal-based, per Testing Strategy):**
```
grep -F "reject"                packs/product-engineering/.apm/skills/map-capabilities/SKILL.md
grep -F "reduced traceability"  packs/product-engineering/.apm/skills/map-capabilities/SKILL.md
grep -F "proceed on bet"        packs/product-engineering/.apm/skills/map-capabilities/SKILL.md
grep -F "strategic tension"     packs/product-engineering/.apm/skills/map-capabilities/SKILL.md
grep -F "Next step readiness"   packs/product-engineering/.apm/skills/map-capabilities/SKILL.md
```
Each must return ≥1 match (unique phrases; a count-only grep would pass vacuously).

**Adopter-cleanliness:**
```
grep -E "RFC-[0-9]{4}|agent-ready-repo" \
  packs/product-engineering/.apm/skills/map-capabilities/SKILL.md && exit 1 || exit 0
```

## Design (LLD)

### Design decisions

- **Domain-first organization (not Wardley-grouped).** Grouping by Wardley stage
  conflates portfolio view with operational heat map; domain sections are more
  readable for PMs and align with how briefs are eventually written. Traces to:
  AC6.
- **Seven-field capability entry** (id, name, description, Wardley stage, strategic
  criticality, disposition, dependencies). Id is a kebab-case stable slug enabling
  stable cross-references in dependencies and build sequence without name-change
  fragility. Owner/metrics/cost-to-serve deferred — belong in spec-writing.
  Traces to: AC7.
- **"Adopt" as a distinct disposition term.** Distinct from Buy (no license cost;
  carries maintenance obligation); widely practiced in OSS/AI-era stacks. Not yet
  in formal BCM standards; defined once in the artifact so the distinction is
  explicit. Traces to: AC2, AC7.
- **Commodity + Differentiating = explicit tension flag** before finalizing. Makes
  the strategic mismatch visible without blocking map completion. Traces to: AC8.
- **Suggested build sequence: Build-disposition only.** Non-Build (Buy/Partner/Adopt)
  capabilities appear in domain tables; their disposition is the action, not
  spec-writing. Including sequencing is contested; the counter-argument is stronger
  for an artifact that feeds specs immediately. Traces to: AC9.
- **L1 + selective L2 only.** L3 granularity belongs in spec-writing.
  Traces to: AC7, Boundaries.
- **Wardley/criticality vocabulary in SKILL.md body.** Inline definitions for
  Wardley stages and strategic criticality, matching `frame-situation` A3.
  Tightens the 100-line budget — acknowledged in Risks. Traces to: AC7.

### Component / module decomposition

```
packs/product-engineering/.apm/skills/map-capabilities/
  SKILL.md                            ← procedure + artifact schema (T2)
  assets/
    capability-map-template.md        ← artifact template (T1)
  examples/
    <slug>/
      bet.md                          ← sample bet input (T3)
      capability-map.md               ← sample output artifact (T3)
docs/guides/product-engineering/how-to/
  map-capabilities.md                 ← Diátaxis how-to (T4)
```

### Behavior & rules

**Intake flow:**
1. Confirm initiative scope (not feature-scope); redirect to `frame-intent` if below capability level.
2. Resolve `output_dir` (three-tier: repo-scope → user-scope → two-branch elicitation).
3. Resolve slug: active shaping queue item slug, or ask PE when standalone; surface multiple candidates if they exist; never mint.
4. Look for `<output_dir>/shaping/<slug>/bet.md`. If found: surface option,
   appetite, rationale as elicitation context. If absent: offer `place-bet` first;
   if declined, proceed on free-form vision (note reduced traceability in artifact).
5. Look for `<output_dir>/shaping/<slug>/situation-framing.md`. If found: carry
   Wardley capability assessments as pre-assessed entries. If absent: proceed.
6. Elicit or confirm product vision (1–2 sentences). Record in frontmatter.

**Capability elicitation:**
- Propose candidate L1 domains from the bet + vision; confirm with PE.
  When bet is underdetermined, elicit more context first.
  When elicitation yields zero capability areas, surface this and ask PE to expand
  scope or confirm empty map — do not silently emit an empty artifact.
- For each domain, elicit capabilities one at a time, annotating seven fields
  (id, name, description, Wardley stage, criticality, disposition, dependencies).
- Default depth: L1. Elicit L2 only when the bet explicitly names a capability as
  deeply scoped.
- After all entries: scan for Commodity+Differentiating pairs; surface as tensions,
  require PE acknowledgment before finalizing each.

**Emit:**
- Write `capability-map.md` using `assets/capability-map-template.md` as shape.
- Prepend vocabulary block (Build/Buy/Partner/Adopt definitions).
- Append "Suggested build sequence" section — Build-disposition capabilities only,
  dependency-ordered + Wardley-informed, marked as recommendation.
- Append "Next step readiness" when lean-canvas/author-brief absent.
- Realpath-expand, reject `..`, confirm path before writing.

**Post-emit:**
- Print workspace.toml shaping-queue transition TOML snippet.
- Direct to `capture-work` or manual edit.

## Tasks

### T1 — Author `assets/capability-map-template.md`

**Depends on:** none

**Tests:**
- File exists at
  `packs/product-engineering/.apm/skills/map-capabilities/assets/capability-map-template.md`.
- YAML frontmatter contains `type`, `slug`, `date`, `bet-source`, `vision`.
- File contains a vocabulary definition block (Build/Buy/Partner/Adopt).
- File contains ≥1 L1 domain `##` section with a markdown table having columns:
  Id, Capability, Description, Wardley Stage, Strategic Criticality, Disposition,
  Dependencies.
- File contains a "Suggested build sequence" section.
- File contains a "Next step readiness" section.

**Approach:**
- Author the template to the artifact shape defined in AC2.
- Use placeholders (`<slug>`, `<vision>`, `Example Domain`, etc.) — not real content.
- The template is the contract for the artifact; SKILL.md references its path.

**Done when:** template file exists at the correct path, all required frontmatter
fields and sections present, adopter-clean.

### T2 — Author `SKILL.md`

**Depends on:** T1

**Tests:**
- File exists at
  `packs/product-engineering/.apm/skills/map-capabilities/SKILL.md`.
- Line count < 100.
- `tools/lint-skill-spec.py` exits 0.
- `lint-packs` exits 0.
- All five grep assertions from Construction tests pass (≥1 match each).
- Adopter-cleanliness grep: no RFC-NNNN or `agent-ready-repo` in body.

**Approach:**
- Frontmatter: `name: map-capabilities`; description covers when to invoke (step 6,
  after `place-bet`), what it produces (Capability Map artifact), and what NOT to
  use it for (don't use for a single feature — use `frame-intent`).
- "When to invoke": confirm scope is initiative-level; redirect if feature-scoped.
- "When to invoke" block: confirm initiative-scope; redirect to `frame-intent`
  if feature-scoped; ask when genuinely ambiguous.
- Inline vocabulary definitions: Wardley stages (Genesis/Custom-built/Product/
  Commodity) and strategic criticality (Differentiating/Parity/Utility) — brief
  one-liners matching `frame-situation` A3 precedent.
- Procedure (six numbered steps):
  1. Intake — confirm scope, resolve `output_dir`, resolve slug (shaping item or
     ask; surface multiple candidates; never mint), read `bet.md` (absent-bet
     branch with "reduced traceability" phrase), read `situation-framing.md`
     (absent branch with "proceed on bet" phrase).
  2. Elicit product vision — 1–2 sentences; confirm with PE; record in frontmatter.
  3. Propose + elicit domains and capabilities — propose L1 candidates; confirm;
     elicit zero-capability case; annotate seven fields; L2 only on explicit bet
     scope; flag Commodity+Differentiating "strategic tension".
  4. Build sequence — Build-disposition capabilities only; dependency-order +
     Wardley-informed; "recommendation not mandate" language.
  5. Emit `capability-map.md` — realpath, reject `..` ("reject" phrase), surface
     path, write. "Next step readiness" section when lean-canvas/author-brief absent.
  6. Suggest workspace.toml transition — TOML snippet; do not write.
- Anti-patterns block: <5 lines covering the Never-do boundaries.
- Unique grep-pinned phrases: "reject", "reduced traceability", "proceed on bet",
  "strategic tension", "Next step readiness".

**Done when:** all test assertions pass; file <100 lines.

### T3 — Author worked example

**Depends on:** T2

**Tests:**
- `examples/` directory exists under the skill directory.
- Sample `bet.md` exists as input reference.
- Primary `capability-map.md` demonstrates: ≥3 L1 domains, ≥2 capabilities per
  domain (≥1 Build + ≥1 non-Build per domain) with all seven fields populated
  including ids; vocabulary block present; suggested build sequence (Build-only)
  present with rationale per entry.
- Second run on a distinct slug writes to a distinct path; no file-collision.
- Adopter-clean: no RFC-NNNN, no `agent-ready-repo`.

**Approach:**
- Use a realistic but fictional initiative (not `agent-ready-repo`).
- Run `map-capabilities` on the primary topic with the sample `bet.md`; record
  the output artifact. Run again on a second distinct topic to prove no-collision.
- Verify both examples follow the template shape exactly.

**Done when:** both example files exist; no-collision demonstrated; adopter-clean.

### T4 — Author how-to guide

**Depends on:** T2

**Tests:**
- File exists at
  `docs/guides/product-engineering/how-to/map-capabilities.md`.
- File opens with a Diátaxis how-to header (goal-oriented, second-person).
- Covers: when to run `map-capabilities` (after `place-bet`), how to read Wardley
  + strategic-criticality annotations, how to use the suggested build sequence to
  seed the M3–M6 spec queue.

**Approach:**
- Mirror the shape of `frame-a-situation.md` and `identify-opportunities.md`
  how-to guides.
- Diátaxis how-to discipline: goal-oriented, second-person, no explanatory tangents.

**Done when:** file exists at correct path; covers the three required topics.

### T5 — Lint and build gates

**Depends on:** T1, T2, T3, T4

**Tests:**
- `lint-packs` exits 0.
- `validate` exits 0.
- `build` exits 0.
- `packages/agentbundle` pack/contract tests exit 0.
- Adopter-cleanliness grep passes on SKILL.md body.

**Approach:**
- Run the standard gate sequence. Fix any lint failures before declaring done.
- `make build-self` is NOT run — PE pack excluded from `_DEFAULT_SELF_HOST_PACKS`.

**Done when:** all gates green.

## Rollout

Pure skill addition — no infrastructure, no migration, no backwards-incompatible
change. Ships as a new directory under
`packs/product-engineering/.apm/skills/map-capabilities/`. Existing skills and
artifacts are unaffected.

## Risks

- **SKILL.md line budget.** The procedure has six steps, inline Wardley/criticality
  vocabulary definitions, and an anti-patterns block; the 100-line cap is tighter
  than siblings. Mitigation: vocabulary definitions are dense one-liners (four
  Wardley stages + three criticality tiers); step prose is dense; template shape
  description stays in the template asset, not the SKILL body.
- **Disposition vocabulary drift.** "Adopt" is not yet in formal BCM standards;
  it is defined once in the artifact. If a future spec narrows or renames it, that
  PR also updates the template and example.

## Changelog

- 2026-07-21: initial plan; field set (seven fields inc. stable id) and organization
  decisions informed by research agent (BIZBOK, TOGAF, Wardley). Adversarial review
  pass: added altitude-redirect AC, zero-capability case, domain-fabrication guard,
  slug reuse alignment, path-safety grep, build-sequence scoped to Build-disposition
  only, stable id field, Wardley/criticality vocab in SKILL body, two-run QA.

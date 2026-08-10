# Plan: xd-skill-boundaries

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Approved | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially,
> record why in the changelog.

## Approach

Build a 20-row boundary matrix before editing so every description and eval
change is grounded in the skill's actual job rather than a universal suffix.
Rewrite only frontmatter descriptions, add focused positive and negative
activation fixtures, then synchronize the marketing page and guide reference.
After content stabilizes, bump the pack, regenerate projections, build both
reader surfaces, and close with multi-viewport QA plus the repository gates. A
late rendered-QA finding adds the missing rich-text layout contract to the
existing shared pack-description container.

## Constraints

- RFC-0071 Area D defines the natural-language trigger and adjacent-discipline
  boundary obligation; its D9 decision requires a per-spec pack version bump.
- `.apm/` files are canonical and projections are generated only after all pack
  edits are complete.
- Non-cosmetic pack edits require synchronized manifest versions, changelog,
  eval updates, catalogue validation, and self-host regeneration.
- The current work changes published routing interfaces and the shared
  pack-description typography rules, but not skill workflow behavior, primitive
  inventory, navigation, visual tokens, or dependencies.

## PLAN record

### Assumption trio

- **Files:** Touch this spec directory; the 20 experience-design frontmatter
  descriptions and their activation fixtures; the experience-design marketing
  page and guide reference; the shared pack page's description styles; both pack
  manifests; the changelog; `workspace.toml`; and generator-owned projections.
- **Done tests:** Boundary-matrix checks, JSON/deep catalogue lint, guide and
  index validation, contract drift, catalogue verify, self-host/build checks,
  site builds, and recorded 375px/1280px reader QA all pass.
- **Not changing:** Skill/reviewer bodies, skill names or directories, primitive
  count, dependencies, template structure, navigation, or visual tokens. The
  approved exception is token-based spacing and containment for Markdown
  descendants of the existing shared pack-description container.

### Declined patterns

- **Replay the old same-slug commit:** declined because it covers one copy guard
  across 17 skills and omits the current 20-skill, cross-discipline, and page
  obligations.
- **Shared boundary schema or generator:** declined because each skill's natural
  request and nearest neighbors differ; a universal abstraction would erase the
  distinctions the change must express.
- **Workflow-body cleanup:** declined because routing frontmatter and evals are
  independently shippable; behavior changes require separate approval.
- **Pack-page redesign:** declined; rendered QA proved the template lacks a
  rich-text spacing contract, but its structure and visual system remain
  coherent. Fix only the descendant typography rules.
- **New dependency:** declined because repository-native validators, the eval
  fixtures, and the existing site toolchain cover the work.

### Resolve-vs-surface disposition record

- **Resolved in PLAN:** current contract vs. obsolete same-slug history, 20-skill
  inventory, patch release, canonical/editable surfaces, copy-layer ownership,
  and the user-approved shared pack-description typography amendment.
- **Surface during EXECUTE:** a boundary that requires changing workflow behavior,
  a description that cannot satisfy the boundary within the published length
  contract, a concurrent pack version advance, or inability to exercise the real
  generated reader surfaces.
- **Status:** open until DECIDE; every review finding receives an apply or defer
  disposition before closeout.

### Domain grounding

No new domain claim requires research: the accepted RFC, current skill
contracts, pack manifest, and grounded platform-site direction define the jobs,
ownership boundaries, and reader surface.

## Construction tests

**Cross-cutting integration gates:**

- `python3 tools/validate_guides.py`
- `python3 tools/check-guide-index.py`
- `python3 tools/check-contract-drift.py --root .`
- `agentbundle catalogue lint --root .`
- `agentbundle catalogue lint --root . --deep`
- `agentbundle catalogue verify --root .`
- `python3 tools/test-run-pack-evals.py`
- `FORCE=1 make build-self`
- `make site-build`
- `SKIP_SAST=1 make build-check`

**Manual verification:**

- Compare the final 20-row benchmark against every canonical frontmatter,
  changed eval file, marketing claim, and guide entry.
- Audit only added lines in `git diff --unified=0 -- packs/` against the banned
  governance-marker forms in `packs/AGENTS.local.md`; require zero newly
  introduced repository-internal citations while leaving its documented
  pre-existing illustrative exceptions out of the verdict.
- Exercise the built marketing pack page and generated documentation reference
  at 375px and 1280px; record five-second comprehension, navigation, focus,
  overflow, code-block containment, and boundary-language observations in
  `qa.md`.

## Design (LLD)

### Design decisions

- A spec-local boundary matrix is the evidence layer; it prevents one universal
  near-miss suffix from replacing skill-specific routing. Traces to AC1–AC4.
- Frontmatter remains the canonical routing interface; marketing and guide prose
  summarize it without becoming a second behavior contract. Traces to AC5–AC6.
- The existing pack-page structure and docs-site template remain unchanged. The
  pack page gains only token-based descendant typography and containment rules
  because the global reset otherwise erases authored Markdown hierarchy. Traces
  to AC5 and AC8–AC11.

### Component / module decomposition

- `benchmark.md`: 20-row internal inventory of job, output, natural requests,
  intra-pack neighbors, adjacent-discipline exits, and eval evidence.
- `packs/experience-design/.apm/skills/*/SKILL.md`: canonical routing interface.
- `packs/experience-design/.apm/skills/*/evals/eval_queries.json`: activation and
  near-miss evidence for each changed interface.
- `web/src/content/packs/experience-design.md`: marketing evaluation entry point.
- `web/src/pages/packs/[pack].astro`: existing shared container, amended only
  with rich-text descendant spacing and containment styles.
- `guides/experience-design/README.md`: documentation entry point and job-family
  router.
- `guides/experience-design/reference/experience-design.md`: detailed adopter
  reference and generated docs-site source.

Traces to AC1–AC8.

### State & control flow

The adopter path is natural request → pack-page job family → named skill →
frontmatter routing decision → guide reference for detailed boundaries. The
build path is canonical `.apm`/guide/page sources → self-host and site generators
→ adapter projections plus marketing/docs HTML. Traces to AC2–AC8.

### Behavior & rules

- Every description states the positive job before exclusions.
- Cross-discipline exclusions distinguish strategy decisions, product shaping,
  experience design, and frontend implementation without claiming those packs
  are always installed.
- Copy work routes by decision altitude and artifact: brand register, content
  structure, per-surface acquisition direction, then UI strings.
- Evals use realistic adjacent requests rather than keyword-only negations.

Traces to AC2–AC4.

### Quality attributes (NFRs)

- Published descriptions remain within the catalogue's length/schema contract.
- The page update preserves WCAG 2.2 AA posture, responsive layout, focus
  visibility, reduced-motion behavior, and no page-level overflow at 375px. Its
  shared rich-text styles use existing design tokens and preserve semantic
  headings, lists, tables, code, and blockquotes.
- All adopter-facing claims are traceable to canonical skill frontmatter.

Traces to AC2 and AC5–AC11.

### Dependencies & integration

The work uses the existing agentbundle catalogue validators, self-host projector,
guide/site generator, and Astro/Starlight builds. No new runtime or development
dependency is introduced. Traces to AC7–AC9 and Rollout.

## Tasks

### T1: Every experience-design skill has an explicit boundary baseline

**Depends on:** none

**Touches:** docs/specs/xd-skill-boundaries/benchmark.md

**Verification mode:** goal-based check

**Tests:**

- `no stub (goal-based check)`

- Parse `pack.toml` and confirm the matrix contains exactly the 20 manifest-listed
  skills, with no duplicate or omitted row (AC1).
- Confirm each row records current positive requests, output, intra-pack
  neighbors, strategy/shaping/frontend exits, copy-layer applicability, and eval
  disposition, with every proposed fixture labelled as a natural-positive,
  strategy-negative, product-shaping-negative, routine-frontend-negative, or
  copy-layer-negative case (AC1–AC4).

**Approach:**

- Inventory canonical frontmatter and activation fixtures.
- Quote RFC-0071 Area D's controlling scope—“All 19 skills: update trigger
  descriptions to natural requests; add near-miss guards for strategy, PE
  shaping, and routine FE”—together with its 2026-08-02 erratum correcting the
  inventory to 20. Use those boundary types plus current product-strategy,
  product-engineering, and frontend-engineering skill names as routing evidence.
- Record the obsolete commit only as historical evidence, never as current truth.

**Done when:** an independent reviewer can derive every planned description and
eval change from one complete 20-row matrix.

### T2: All 20 frontmatter descriptions route natural requests without discipline bleed

**Depends on:** T1

**Touches:** packs/experience-design/.apm/skills/*/SKILL.md

**Verification mode:** goal-based check

**Tests:**

- `no stub (goal-based check)`

- Compare manifest skill names to the edited frontmatter set; all 20 are present
  exactly once (AC2).
- Parse each description through deep catalogue lint and verify the matrix's
  positive job, output, and applicable adjacent-discipline exits are present
  (AC1–AC3).
- Confirm only frontmatter description lines changed under the 20 skill roots;
  bodies, names, directories, references, and reviewer files are unchanged
  (AC11).
- Audit added lines in the changed canonical skill files against the banned
  governance-marker forms in `packs/AGENTS.local.md`; confirm no
  repository-internal citation was introduced without treating pre-existing
  allowed examples elsewhere in `packs/` as failures (AC11).

**Approach:**

- Rewrite descriptions individually from the benchmark instead of appending a
  universal suffix.
- Keep natural positive requests first, then output, closest neighbor, and
  cross-discipline exclusions in decreasing relevance.
- Make the four copy-layer descriptions mutually exclusive and sequenced.

**Done when:** all 20 canonical routing interfaces are concise, lint-valid, and
traceable to the matrix without workflow-body changes.

### T3: Activation fixtures exercise every changed routing interface

**Depends on:** T2

**Touches:** packs/experience-design/.apm/skills/*/evals/eval_queries.json

**Verification mode:** goal-based check

**Tests:**

- `no stub (goal-based check)`

- Parse all 20 JSON files and confirm each changed skill adds at least one
  benchmark-derived positive and one adjacent-discipline negative (AC4).
- Confirm the union of false cases covers strategy, product shaping, routine
  frontend implementation, and every copy-layer neighbor (AC3–AC4).
- Run `agentbundle catalogue lint --root . --deep` and
  `python3 tools/test-run-pack-evals.py` (AC4, AC9).

**Approach:**

- Add realistic, skill-specific cases from the matrix; avoid duplicated keyword
  templates that do not represent a plausible routing decision.
- Preserve existing fixtures unless the benchmark proves one contradicts the
  final description.

**Done when:** every changed frontmatter interface has positive and near-miss
fixture evidence and the deep lint is green.

### T4: Adopter pages expose the same 20-skill boundary model

**Depends on:** T2, T3

**Touches:** web/src/content/packs/experience-design.md, web/src/pages/packs/[pack].astro, guides/experience-design/README.md, guides/experience-design/reference/experience-design.md

**Verification mode:** goal-based check plus visual / manual QA

**Tests:**

- `no stub (visual / manual QA)`

- Compare the marketing page, guide home, and reference inventories to
  `pack.toml`; each applicable inventory lists all 20 skills exactly once and
  uses matrix-consistent routing terms (AC5–AC6).
- Run guide and guide-index validation (AC6).
- Build both sites and run a five-second scan at 375px and 1280px; a cold reader
  identifies what, who, and the correct job family before the raw inventory,
  with no page-level overflow (AC5, AC8, AC10).

**Approach:**

- Replace the pack page's inventory-first paragraph with compact job-family and
  adjacent-discipline routing before the existing detailed skill inventory.
- Update the guide home's job-family route and the reference page's 20 skill
  sections to mirror canonical trigger, output, and nearest-boundary meaning.
- Preserve template structure, navigation, and visual tokens; add the approved
  descendant typography rules to the existing pack-description container.

**Done when:** marketing and reference readers receive one accurate routing model
and the two baseline scope findings are absent from rendered output.

### T5: The boundary release is versioned and projected coherently

**Depends on:** T2, T3, T4

**Touches:** packs/experience-design/pack.toml, packs/experience-design/.claude-plugin/plugin.json, docs/product/changelog.md, .claude-plugin/marketplace.json, generated adapter projections

**Verification mode:** goal-based check

**Tests:**

- `no stub (goal-based check)`

- Parse the current synchronized manifest version, confirm both manifests receive
  the patch release required by AC7, and confirm the changelog names the boundary,
  eval, and adopter-page changes (AC7).
- Run `FORCE=1 make build-self`, catalogue lint/deep lint/verify, and contract
  drift; confirm projections are current (AC7–AC9).
- Repeat the diff-scoped added-line governance-marker audit after regeneration;
  require no newly introduced repository-internal citation in canonical or
  projected pack changes (AC11).

**Approach:**

- Re-read both versions immediately before the patch bump.
- Regenerate only after every canonical pack edit is final.

**Done when:** metadata, changelog, marketplace, and every self-host projection
agree on the patch release specified by AC7.

### T6: Integrated reader and repository gates prove the spec complete

**Depends on:** T5

**Touches:** docs/specs/xd-skill-boundaries/qa.md, docs/specs/xd-skill-boundaries/spec.md, docs/specs/xd-skill-boundaries/plan.md, docs/specs/README.md, workspace.toml, web/src/pages/packs/[pack].astro

**Verification mode:** visual / manual QA plus goal-based repository gates

**Tests:**

- `no stub (visual / manual QA)`

- Satisfy AC10's complete `qa.md` evidence contract: record baseline and final
  design-review results; build commands and exits; routes; 375px and 1280px
  focus/navigation, code containment, horizontal-overflow, and five-second-scan
  observations; screenshots or DOM identifiers; the explicit in-scope versus
  documented-but-not-exercised session boundary; and final finding dispositions
  (AC8, AC10).
- Run the full construction-gate sequence and `SKIP_SAST=1 make build-check`
  after generated outputs are current (AC9).
- Confirm the final diff matches the allowlisted scope and moves the spec from
  queue to shipped only after all other criteria pass (AC11–AC12).

**Approach:**

- Reconcile final descriptions, evals, and pages back into `benchmark.md`.
- Run authoring-time design review, then independent experience, adversarial,
  security, and quality reviews as routed by full-mode `work-loop`.
- Update lifecycle metadata and workspace placement atomically at closeout.

**Done when:** durable evidence shows all 12 criteria satisfied, all repository
gates green, and no required reviewer finding remains open.

## Rollout

This ships as a reversible static-content and pack patch release. There is no
feature flag, infrastructure, migration, or external-system dependency. Revert
the commit to restore the prior routing descriptions and pages. Canonical pack
and guide sources are finalized before projection and site generation.

## Risks

- Long descriptions can exceed the published schema or bury the positive job.
  Rewrite and prioritize rather than appending every boundary mechanically.
- A universal near-miss phrase can make all skills look interchangeable. The
  matrix must justify skill-specific neighbors and examples.
- Guide and marketing prose can drift from frontmatter during review. Reconcile
  all three surfaces after the last edit, then regenerate.
- The pack may advance while the work is open. Re-read versions before applying
  AC7 and surface any concurrent advance.
- Source-valid Markdown can still fail the reader task at mobile width. Rendered
  QA and independent experience review remain shipping gates.

## Changelog

- 2026-08-09: Replaced the obsolete same-slug partial contract with the current
  RFC/queue scope after comparing commit `f7c24faa`; added the 20-skill matrix,
  cross-discipline eval coverage, adopter-page synchronization, and rendered QA.
- 2026-08-09: Applied pre-execution adversarial review: pinned fixture types to
  the RFC scope and erratum, bounded manual QA, made no-stub records explicit,
  named the eval self-test and governance grep, and centralized the release
  version contract in AC7.
- 2026-08-09: Replaced the repository-wide governance grep with an added-line
  diff audit that tolerates documented existing examples, and made T6 inherit
  AC10's complete QA evidence contract.
- 2026-08-10: Amended the approved scope after rendered QA proved content-only
  spacing edits cannot survive the global CSS reset. The user approved a
  token-based rich-text layout contract inside the existing shared
  pack-description container; template structure, navigation, and tokens remain
  unchanged.

# Spec: journey-template-revamp

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Contract:** none
- **Shape:** mixed <!-- ui (web journey pages/components) + data (frontmatter schema) + docs content -->

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

Journey pages and the task-oriented guides teach a reader how to *read them* the
first time and then reuse that skill on every subsequent page. Today each web
journey narrates its stages in free prose (`**You:** …`), skills and install sit
above the narrative, and there is no single above-the-fold summary of the deal a
reader is signing up for. The reader — an IC deciding whether to adopt a pack, or
a practitioner mid-task — has to re-parse each page's shape from scratch.

This revamp imposes one **fixed, learnable structure** across the journey and
guide surfaces, so structure never varies and only content does. A reader who
learns to read one journey can read all sixteen; a reader who learns one how-to
can scan any how-to. Concretely:

- **A compact contract block** opens every web journey, above the narrative, with
  four fixed lines: **Use it when · You provide · You receive · Your decisions**.
  It answers the reader's first question — *is this for me, what do I put in, what
  do I get out, what will I have to decide* — in one glance.
- **Fixed stage-card labels** structure every stage of every journey: the same
  label subset in the same order — **You provide · <Actor> does · You do · You
  decide · Output** — with `Output` always present. The actor varies (`Agent
  does` / `Reviewer does` / `Loop does`); the label shape never does.
- **Supporting material is demoted below the narrative** in a fixed order
  (transcript/artifact → approval checklist → typical timing → install → skills →
  technical reference), so the primary content leads and the catalogue/reference
  scaffolding follows.
- **Task-oriented guides** (Diátaxis how-to and tutorial quadrants) gain a
  per-quadrant contract header of the same spirit, phrased for their mode.
  **Reference and explanation guides are untouched** — forcing a contract block
  onto a cognition-mode page reintroduces the mode-mixing Diátaxis warns against.
- **Product-journey maps** (`docs/product/journeys/`) gain a light 4-line contract
  header derived from fields they already carry; their NN/g pains→opportunities
  stage tables are left intact.

Success: a reader can predict where any fact lives on any journey or task-guide
before scrolling, because the labels and order are identical across pages; and
the common drift modes — a journey missing its contract, a stage missing `Output`,
an unknown actor token, or a stage left in the old `## Stage N —` format — are
mechanically caught by a lint. (Prose-level wording quality stays a reviewer call;
the lint guards structure, not phrasing.)

The design is grounded in `.context/doc-template-learnability-survey.md` — the
consistency/recognition heuristics (NN/g H4/H6), progressive disclosure, the
cross-vendor "above-the-fold contract" convergence, and the Diátaxis
mode-separation constraint.

## Boundaries

### Always do

- Keep the four journey contract labels and the five stage-card labels **verbatim
  and in fixed order** on every web journey; the actor token in `<Actor> does`
  may vary, the label may not.
- Keep the web site building green: the frontmatter schema and all 16 journeys
  move together so the built site is never half-migrated at PR merge.
- Phrase `You receive` as concrete **artifacts** ("an agreed plan, a checked
  diff, review findings"), never as "you will learn X".
- Preserve each journey's existing `skills:` frontmatter list unchanged (the
  `lint-web-journey-parity` skill-count invariant must keep passing).
- For guides, obey the Diátaxis **link-out** rule: a contract header summarizes;
  it does not duplicate a fuller `## Prerequisites` section that already exists.

### Ask first

- Adding, renaming, or reordering any of the fixed labels (contract or stage
  card) — the label set is the load-bearing consistency contract.
- Extending the treatment to the reference or explanation guide quadrants.
- Any change to the journey `humanGates` / `typicalSession` frontmatter shape
  beyond adding the `contract` object.

### Never do

- Never mix Diátaxis modes: no contract header on reference/explanation guides;
  no teaching prose injected into a how-to's steps.
- Never introduce a new dependency, CSS framework, or top-level directory — the
  `--ds-*` token system stays the sole styling authority (web/AGENTS.md).
- Never move the stage narrative out of the journey `.md` body into frontmatter
  (the `<Content />` authoring model stays; only its internal format is fixed).
- Never drop or reword a journey's `skills:` entries to fit the new layout.

## Testing Strategy

- **Schema + component + renderer (T1, T3):** goal-based check — `npm run build`
  in `web/` succeeds and emits the journey pages; the contract block and reordered
  sections appear in the built HTML. The Astro build is the type/consumption gate.
- **Fixed-structure invariant (T3):** TDD — a stdlib lint (`lint-journey-contract.py`)
  asserts every `web/src/content/journeys/*.md` carries the four `contract` keys
  and every `## N.` stage carries the fixed labels; a paired self-test drives it
  over pass/fail fixtures (mirrors `test-lint-web-journey-parity.py`).
- **16 journeys / 84 guides / 11 product journeys (T2, T4, T5):** goal-based check
  — grep-level assertions that each target file carries its required header/labels
  (a resumable tracking file governs 100% completion); plus MkDocs (`site/mkdocs.yml`)
  and Astro builds pass.
- **Rendered experience (T1, T2):** visual / manual QA — build the site, open a
  converted journey (e.g. `core`), and confirm the contract block, fixed stage
  cards, and reordered sections render correctly and match the grounded aesthetic
  reference; reviewed by `experience-reviewer` in REVIEW.

## Acceptance Criteria

- [x] Every `web/src/content/journeys/*.md` (all 16) carries a `contract` object with `useItWhen`, `youProvide`, `youReceive`, and `yourDecisions`, and the zod schema requires it.
- [x] Every web-journey stage renders the fixed labels — `You provide` / `<Actor> does` / `You do` / `You decide` / `Output` — in that order, using only the applicable subset, with `Output` always present.
- [x] The rendered journey page shows sections in the fixed order: hero → contract → what-changes → narrative → good-output/transcript → human gates → typical session → install → skills → technical reference.
- [x] `JourneyContract.astro` renders the four contract lines above the narrative. (That each journey's `yourDecisions` correspond to its `humanGates` is a REVIEW/manual-QA check on the converted journeys, not a lint-enforced criterion.)
- [x] `npm run build` in `web/` succeeds and `lint-web-journey-parity.py` still passes (skill counts unchanged).
- [x] `lint-journey-contract.py` passes against the tree and fails on a fixture journey missing the contract or a stage label; its self-test is green.
- [x] All 68 how-to and 14 tutorial guides under `docs/guides/**` carry a per-quadrant contract header (how-to: `Use this when` / `Prerequisites` / `Result`; tutorial: `What you'll build` / `Prerequisites` / `Time`); the two per-quadrant framework-explainer READMEs (`_shared/how-to/README.md`, `_shared/tutorials/README.md`) and every reference or explanation guide are NOT modified.
- [x] The `new-guide` skill's `assets/how-to.md` and `assets/tutorials.md` templates carry the contract header so future guides inherit it.
- [x] All 11 product-journey maps under `docs/product/journeys/*.md` (the glob matches 12 files — the 11 maps plus `README.md`, which is the index and is NOT modified) carry a 4-line contract header (`Use it when` / `You provide` / `You receive` / `Your decisions`); their stage tables are unchanged.
- [x] `docs/specs/platform-site/journey-page-template.md` (a living template-reference doc, not frozen spec history) documents the new structure (contract block, fixed stage labels, reordered sections) and no longer prescribes the superseded per-stage `**You did:**` prose-narrative convention.
- [x] The MkDocs docs build (`site/mkdocs.yml`) succeeds with the guide and product-journey edits.

## Assumptions

- Technical: 16 web journeys render via an Astro `journeys` content collection with a zod schema; optional fields render only when present, so a new field can be introduced without breaking the build mid-rollout (source: web/src/content.config.ts; web/src/pages/journeys/[journey].astro).
- Technical: `lint-web-journey-parity.py` checks only the `skills:` list count against pack skill dirs, not body structure (source: tools/lint-web-journey-parity.py).
- Technical: guides are per-pack Diátaxis under docs/guides/<pack>/<quadrant>/ — 69 how-to, 15 tutorial, 53 reference/explanation — built by MkDocs (source: find over docs/guides; site/mkdocs.yml).
- Technical: the 11 product-journey maps already carry `Persona:` / `Outcome:` / `Trigger:` / `End state:` bold headers from which the contract lines derive; `docs/product/journeys/*.md` globs 12 files (the 12th is `README.md`, the index, excluded from the treatment) (source: docs/product/journeys/engineer-runs-work-loop.md).
- Process: this ships via work-loop spec/plan in a single PR, A/B/C together, not an RFC (source: user confirmation 2026-07-23).
- Process: a grounded aesthetic reference exists so design-intent ACs are checkable (source: docs/specs/platform-site/aesthetic-direction.md, design-system-foundations.md).
- Product: journey contract labels + fixed stage-card labels are the recommended set; guide headers are a per-quadrant variant; `You receive` states artifacts not learning (source: user confirmation 2026-07-23).

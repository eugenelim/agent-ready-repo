# Plan: journey-template-revamp

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn.

## Approach

Three surfaces, one PR, sequenced so the build is green at every gate and the two
mechanical batches run in parallel with the web work.

The riskiest part is the web foundation (T1): the schema, a new component, and the
renderer reorder must land before the 16 journeys can be converted. To keep the
build green throughout, `contract` enters the schema **optional** in T1 (the
renderer shows the block only when present, exactly as it already does for
`whatChanges`), the 16 journeys gain it in T2, and T3 tightens the schema to
**required** once every journey has one — then adds the lint that freezes the
invariant. The guide batch (T4, 84 files) and product-journey batch (T5, 11 files)
touch disjoint trees and depend on nothing in the web work, so they run
concurrently with T1–T3. T6 (the template-spec doc) trails T1 once the final
structure is settled.

Both large batches (T2, T4) are driven through a **resumable tracking file** and
**parallel `implementer` subagents** over disjoint file globs, per the work-loop
"scale with a tool" discipline — the tracking file, not agent stamina, guarantees
100% completion.

## Constraints

- web/AGENTS.md — no new dependency, no CSS framework; `--ds-*` tokens are the sole
  styling authority.
- Diátaxis (`docs/guides/README.md`, `new-guide` skill) — link-out rule; no
  mode-mixing; reference/explanation quadrants untouched.
- CONVENTIONS § 4 — spec metadata (status, ACs checked-or-deferred at ship).

## Construction tests

**Integration tests:** the Astro build (`npm run build` in `web/`) and the MkDocs
build (`site/mkdocs.yml`) are the cross-cutting integration gates — they prove the
schema, renderer, journeys, guides, and product journeys all parse and render
together.
**Manual verification:** build the site; open the `core` journey; confirm the
contract block, fixed stage cards, and reordered sections render and match the
aesthetic reference (`experience-reviewer` in REVIEW).

## Design (LLD)

`Shape: mixed` → ui (component/renderer/state) + data (schema).

### Design decisions

- **Stage narrative stays in the `.md` body**, not frontmatter — preserves the
  `<Content />` authoring model (spec Never-do) and keeps the diff to CSS + content.
  Rejected: moving stages into a `stages:` frontmatter array (empties the body,
  larger schema churn, no rendering benefit over styled bold-labels).
- **Contract is a frontmatter object + a dedicated component** (not body prose) —
  so it renders in a fixed styled block above the narrative and `lint-journey-contract`
  can check it structurally. Traces to: AC1, AC4.
- **`contract` optional → required across T1→T3** — keeps every task's build green.
  Traces to: AC1, AC5.

### Data & schema

`web/src/content.config.ts`, `journeys` collection — add:

```ts
contract: z.object({
  useItWhen: z.string(),
  youProvide: z.string(),
  youReceive: z.string(),
  yourDecisions: z.array(z.string()),
}),            // .optional() in T1; required in T3
```

Frontmatter shape (example, `core`):

```yaml
contract:
  useItWhen: "You're implementing a feature, fixing a bug, or changing an existing repo."
  youProvide: "The task and its important constraints."
  youReceive: "An agreed plan, a checked implementation, review findings, and a merge decision."
  yourDecisions:
    - "Approve the plan"
    - "Approve the final change"
```

Traces to: AC1 · web/src/content.config.ts.

### Component / module decomposition

- **New:** `web/src/components/journey/JourneyContract.astro` — renders the four
  contract lines as a definition-list card (label/value rows, same token vocabulary
  as `GateDetail.astro`'s `.gate-card__meta`). `yourDecisions` renders as a chip row.
- **Changed:** `web/src/pages/journeys/[journey].astro` — insert `<JourneyContract>`
  after the hero; reorder sections to the fixed order (below); add
  `.journey-narrative` CSS for the fixed stage-card labels.
- **Unchanged:** `JourneyHero.astro`, `GateDetail.astro`.

Traces to: AC3, AC4.

### State & control flow — fixed section order (renderer)

1. `JourneyHero` (hero) · 2. `JourneyContract` (**new**) · 3. What changes ·
4. The journey (narrative) · 5. What good output looks like (conditional) ·
6. Human gates · 7. Typical session · 8. Install · 9. Skills in this pack ·
10. Technical reference / next steps. Tones alternate surface/surface-alt.

### Behavior & rules — fixed stage-card format (journey `.md` body)

Each stage is `## N. <imperative outcome title>` followed by a bold-label list,
labels in this fixed order, applicable subset only, `Output` always present:

```markdown
## 1. Agree on the plan

- **You provide:** the requested change and constraints.
- **Agent does:** names scope, files, tests, risks, and exclusions.
- **You decide:** approve or redirect.
- **Output:** agreed plan.
```

The label run is `<Actor> does`; the actor token varies over a **closed set that
is observed, not asserted** — T2 authors the actor tokens across all 16 journeys
(seeded with `Agent` / `Reviewer` / `Loop`, extended as a journey genuinely needs
— e.g. `Supervisor` / `Implementer` for the swarm/coordination journeys), records
the final set at the top of the tracking file, and T3's lint enumerates **exactly
that observed set**. So the set can't reject a legitimately-needed actor mid-T2,
and once frozen in T3 any *later* widening is the `Ask first` action the spec
names. The label shape (`<Actor> does`) never varies. `.journey-narrative` CSS
styles `li > strong:first-child` label runs into aligned card rows. Traces to: AC2.

**What the lint enforces vs. what REVIEW enforces (AC2, AC6):** the lint checks
(a) the four `contract` keys are present, (b) each `## N.` stage carries `Output`,
(c) every label used is drawn from the fixed set and any actor token is in the
observed closed set T2 recorded, (d) labels appear in the fixed relative
order, and (e) **no `## Stage \d+ —`-format heading survives** (guards a
half-converted journey). It does NOT judge whether the *applicable* subset was
chosen correctly for a given stage, nor prose wording — those stay reviewer calls.

### Guide contract headers (per-quadrant variant)

Directly under the `# H1`, before intro prose:

- **how-to:**
  ```markdown
  **Use this when:** <the problem/trigger this guide solves>.
  **Prerequisites:** <one line; links to the fuller ## Prerequisites section if present>.
  **Result:** <what the reader has when done>.
  ```
- **tutorial:**
  ```markdown
  **What you'll build:** <the end artifact>.
  **Prerequisites:** <one line>.
  **Time:** <estimate>.
  ```

Link-out rule: if a `## Prerequisites` section already exists, the header's
Prerequisites line summarizes and points to it — no duplicated list. Traces to: AC7.

### Product-journey header (light)

Under the `# Journey: …` H1, a 4-line block derived from the existing
Persona/Trigger/Outcome/End-state prose:

```markdown
**Use it when:** <trigger>.
**You provide:** <the inputs the persona brings>.
**You receive:** <the outcome / end state>.
**Your decisions:** <the human gates in this journey>.
```

Stage tables unchanged. Traces to: AC9.

## Tasks

### T1: Web-journey foundation — schema, contract component, renderer reorder, stage CSS

**Depends on:** none
**Touches:** web/src/content.config.ts, web/src/components/journey/JourneyContract.astro, web/src/pages/journeys/[journey].astro

**Tests:**
- Goal-based: `npm run build` in `web/` succeeds with `contract` optional and no journey yet carrying it (block hidden, existing pages unchanged). Verifies AC5.
- Manual QA: temporarily add a `contract` to `core.md` locally, rebuild, confirm the block renders above the narrative and sections are reordered; revert the temp edit (real conversion is T2). Verifies AC3, AC4.

**Approach:**
- Add the optional `contract` zod object to the `journeys` schema.
- Create `JourneyContract.astro` (definition-list card; `yourDecisions` as chips; `--ds-*` tokens only).
- Reorder `[journey].astro` to the fixed 10-section order; render `<JourneyContract>` when `data.contract` present; fix tone alternation.
- Add `.journey-narrative` CSS to format `## N.` stage bold-label lists into aligned card rows.

**Done when:** `npm run build` green; a locally-added contract renders in the reordered page; no journey file committed with a contract yet.

### T2: Convert all 16 web journeys to the new template

**Depends on:** T1
**Touches:** web/src/content/journeys/*.md

**Tests:**
- Goal-based: for each of the 16 files, grep confirms the four `contract` keys and that every `## N.` stage carries the fixed labels with `Output` present. Verifies AC1, AC2.
- Goal-based: `npm run build` green; `lint-web-journey-parity.py` still passes. Verifies AC5.

**Approach:**
- Build a resumable tracking file listing the 16 journeys (`pending`/`done`).
- Dispatch parallel `implementer` subagents over disjoint batches; each adds the `contract` frontmatter and rewrites `## Stage N — …` bodies (`**You:**` prose) into `## N. <title>` + fixed bold-label lists, preserving skill/gate/session frontmatter.
- `youReceive` states artifacts, not learning; `yourDecisions` mirror `humanGates` labels.
- **Record the final actor-token set** (seeded `Agent`/`Reviewer`/`Loop`, plus any journey-specific actors like `Supervisor`/`Implementer`) at the top of the tracking file, so T3's lint enumerates exactly the observed set.

**Done when:** all 16 tracked `done`; the actor set is recorded; both greps and both builds/lints pass.

### T3: Enforce the invariant — schema required + lint + self-test

**Depends on:** T2
**Touches:** web/src/content.config.ts, tools/lint-journey-contract.py, tools/test-lint-journey-contract.py

**Tests:**
- TDD: `test-lint-journey-contract.py` drives the lint over a passing fixture and FOUR failing fixtures — (i) missing `contract` key, (ii) stage missing `Output`, (iii) an unknown actor token (`Team does`), (iv) a surviving `## Stage 1 — …`-format heading — asserting exit 0 / exit 1 for each. Verifies AC6.
- Goal-based: `lint-journey-contract.py` exits 0 against the real tree; `npm run build` green with `contract` required. Verifies AC1, AC6.

**Approach:**
- Flip the `contract` object to required in the schema.
- Write `lint-journey-contract.py` (stdlib only, fixture-mode env vars like the parity lint) enforcing the five checks named in Design § Behavior & rules: 4 contract keys present; each `## \d+\.` stage carries the fixed labels in order with `Output`; actor tokens ∈ `{Agent, Reviewer, Loop}`; and NO `## Stage \d+ —`-format heading survives.
- Write the paired self-test with inline fixtures (mirrors `test-lint-web-journey-parity.py`).

**Done when:** lint green on tree, red on all four fixtures; self-test green; build green.

### T4: Guide contract headers — how-to + tutorial (84 files) + new-guide templates

**Depends on:** none
**Touches:** docs/guides/**/how-to/*.md, docs/guides/**/tutorials/*.md, .claude/skills/new-guide/assets/how-to.md, .claude/skills/new-guide/assets/tutorials.md

**Tests:**
- Goal-based: grep confirms each of the 68 how-to files has `**Use this when:**` + `**Result:**` and each of the 14 tutorial files has `**What you'll build:**` + `**Time:**`, directly under H1 (the two `_shared/**/README.md` framework explainers are excluded). Verifies AC7.
- Goal-based: both `new-guide` templates — `.claude/skills/new-guide/assets/how-to.md` and `assets/tutorials.md` — carry their per-quadrant contract header (grep). Verifies AC8.
- Goal-based: no file under `*/reference/*` or `*/explanation/*` is modified (`git diff --name-only` check). Verifies AC7 (negative).
- Goal-based: MkDocs build succeeds. Verifies AC11 (the MkDocs criterion — AC10 is the template-doc, verified by T6).

**Approach:**
- Resumable tracking file of the 84 targets by quadrant.
- Parallel `implementer` subagents over disjoint pack/quadrant batches; each adds the per-quadrant header under H1, obeying the link-out rule (summarize, don't duplicate an existing `## Prerequisites`).
- Update the two `new-guide` templates to carry the header.

**Done when:** all 84 tracked `done`; greps pass; reference/explanation untouched; MkDocs builds.

### T5: Product-journey contract headers (11 files)

**Depends on:** none
**Touches:** docs/product/journeys/*.md (the 11 maps; `README.md` is excluded — it is the index, not a journey)

**Tests:**
- Goal-based: grep confirms each of the 11 map files (glob minus `README.md`) has the 4-line contract header (`Use it when` / `You provide` / `You receive` / `Your decisions`) and that stage tables are unchanged (`git diff` shows only additions near the top). Verifies AC9.
- Goal-based: `README.md` in the directory is NOT modified (`git diff --name-only` check). Verifies AC9 (negative).
- Goal-based: MkDocs build succeeds. Verifies AC11 (the MkDocs criterion — AC10 is the template-doc, verified by T6).

**Approach:**
- For each of the 11 maps (skip `README.md`), derive the 4 lines from its existing `Persona:` / `Trigger:` / `Outcome:` / `End state:` prose; insert under the `# Journey: …` H1.

**Done when:** all 11 carry the header; `README.md` untouched; grep passes; stage tables untouched; MkDocs builds.

### T6: Rewrite the journey-page-template spec doc

**Depends on:** T1
**Touches:** docs/specs/platform-site/journey-page-template.md

**Tests:**
- Goal-based: the doc describes the `contract` frontmatter object, the fixed stage-card labels, and the reordered section list; grep confirms the superseded per-stage `**You did:**` prose-narrative convention (the format actually in the doc today, lines ~135/144/150) is gone. Verifies the template-doc AC (the 10th acceptance criterion in spec.md).

**Approach:**
- Rewrite the frontmatter-schema, section-structure, and writing-guide sections to match the shipped design; keep the content-authoring priority table.

**Done when:** doc matches the implemented structure; no stale `**You did:**` per-stage narrative format guidance remains.

## Rollout

- **Delivery:** single PR, big-bang for the site (schema + 16 journeys land together
  → site never half-migrated at merge). Reversible: pure content/markup + one
  component; revert is a clean git revert. No data migration, no published event.
- **Infrastructure:** none.
- **External-system integration:** none.
- **Deployment sequencing:** within the PR, T1→T2→T3 order matters for green builds;
  T4/T5 independent; T6 after T1. CI runs the Astro + MkDocs builds and the lints.

## Risks

- **84-guide batch is large** — mitigated by the resumable tracking file (completion
  guaranteed by state, not stamina) and grep-level per-file verification.
- **Contract wording drift across 16 journeys** — mitigated by `lint-journey-contract`
  freezing the structural invariant and by a single worked `core` exemplar the
  implementers mirror.
- **Diátaxis mode-mixing creep** — a how-to header that teaches, or a header slipped
  onto reference/explanation — mitigated by the negative grep check in T4 and the
  Never-do boundary.

## Changelog

- 2026-07-23: initial plan (A/B/C in one PR, parallel batches per user direction).

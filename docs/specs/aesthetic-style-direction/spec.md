# Spec: Aesthetic style — parameterised direction, counterfactual gate, and divergence audit

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0033 (experience-design framework agnosticism)
- **Brief:** none
- **Discovery:** [`docs/product/research/aesthetic-style-blueprint.md`](../../product/research/aesthetic-style-blueprint.md)
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material.

## Objective

A designer naming a visual direction today writes ranked goals and their
referents, then hands off to `design-system`. Nothing in the direction doc says
*what the direction actually commits to*, so two directions can differ only in
adjective, and nothing catches a direction that is the generic default for its
brief. This delivery gives `creative-direction` a direction sheet of fifteen
named axes — seven of them structural, because structure carries at least as
much of a first impression as colour does — a self-administered counterfactual
gate that forces a revision when the plan matches what any similar brief would
produce, three pre-filled presets for the vendor-neutral style grammars whose
formal commitments are citable, and a divergence audit that reports whether N
candidate directions genuinely differ. It gives `design-review` eight validated
rating items so a critique can report perceived quality and perceived
genericness rather than only listing findings.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User promise | Applicable — two published skills gain user-visible steps and artifacts | `guides/experience-design/` | `author-product-docs` | Guide text covering the direction sheet, the counterfactual gate, the presets, and the divergence audit | Guide-agreement test passes and a named reviewer judges the guide sufficient |
| Current product truth | Applicable — the pack's skill surface changes | `packs/experience-design/.apm/skills/{creative-direction,design-review}/` | This spec | Edited `SKILL.md`, template, reference modules, and preset files | Files exist and the pack lint is clean |
| Interface compatibility | Applicable — `.apm/**` non-cosmetic change | `packs/experience-design/pack.toml`, `packs/experience-design/.claude-plugin/plugin.json`, and the regenerated `.claude-plugin/marketplace.json` | `packs/AGENTS.md` § Version bump rule | Matching patch bump in both source manifests; the marketplace projection regenerated, never hand-edited | All three read `2.0.6` |
| Release history | Applicable — a released artifact's version is bumped | `docs/product/changelog.md` | That file's own header rules | A free-standing `## [experience-design][2.0.6] — <date>` entry directly beneath `[Unreleased]`, carrying one `Highlights` subsection | The entry sits at the right heading level with single blank lines around every heading |
| Reusable learning | Applicable — evals are the pack's behavioural record | the two changed skills' `evals/evals.json` | `packs/AGENTS.md` § Security and authoring rules | New assertions for the direction sheet, the counterfactual record, and the rating instruments | Both files parse and carry the named assertions |
| Decision rationale | Applicable — Material was excluded by scope, and two governance files conflict on `FORCE=1` | This spec's `Follow-ons` and `Assumptions` | This spec | Both recorded with their evidence | Follow-ons name an owner |

## Boundaries

### Always do

- Express every axis, preset commitment, and rating item at the level of roles,
  classifications, and relationships — never a literal value.
- Keep the two declaration lines in `creative-direction/SKILL.md`
  byte-identical, **including their backticks** — the roster suite matches the
  backticked form, and an earlier draft of this spec quoted them unbackticked,
  which caused an implementer to strip them:
  `**Writes:** ` then a backticked `<output_dir>/direction/<slug>.md`, and
  `**Confinement:** ` then a backticked `references/containment.md`.
- Bump `pack.toml` and `.claude-plugin/plugin.json` together, in the same edit.
- Treat the fifteen axis names and their token vocabularies as one set defined
  by the template; every other file derives from it.

### Ask first

- Adding any new `<output_dir>/<folder>/` declaration to a skill, which the
  artifact-folder registry test cross-checks against `DESIGN.md` and
  `experience-status`.
- Changing the managed `agentbundle:output-rendering` block in either `SKILL.md`.
- Shipping a preset for a style whose formal commitments are not citable from a
  design-history or standards source.
- Passing `FORCE=1` to `make build-self`. `packs/AGENTS.local.md` prescribes it
  for a pack release; root `AGENTS.local.md` forbids automation passing it.
  This delivery runs the unforced form and surfaces a refusal rather than
  resolving the conflict on its own authority.

### Never do

- Write a colour literal, a **unit-bearing** dimension or duration literal
  (`px`, `ms`, `rem`, `em`, `pt`, `vh`, `vw`, decimal seconds), a contrast or
  scale ratio, a named easing curve, an ARIA role, CSS syntax, a UI-framework
  name, or a concrete typeface name into any file under
  `packs/experience-design/`. A **structural count** carries no unit and pins no
  stack — "a rigid five- or six-column grid", "two to six divisions without
  remainder" — and is permitted, because it is a relationship rather than a
  measurement (owner decision, 2026-09-18).
- Ship a preset for brutalism or neumorphism: brutalism is defined by rejecting
  the compositional rules a check would assert, and neumorphism has no
  canonical specification.
- Edit generated adapter projections directly instead of `.apm/` sources.
- Weaken or remove any existing anti-pattern, grounding requirement, or
  quality-floor precedence in either skill.
- Leave an axis cell blank. Undecided is written `[platform-default]`.

## Testing Strategy

Three modes are in use. Every criterion below is tagged with the one that
settles it.

- **Goal-based check** — for everything a command can establish: a file exists,
  a string is present at an expected count, a token set matches, a version
  reads, a gate exits 0. Each such criterion names its command and expected
  result in `plan.md`.
- **Manual QA** — for the four judgements no command reaches: whether each axis
  cell names a role rather than a value; whether each preset's commitments
  match their closed source; whether the divergence audit's comparison rules
  are stated; whether the guide is sufficient. A named reviewer's recorded
  verdict **is** the result for these. The contract accepts that and claims no
  mechanical proxy. The artifact is
  `docs/specs/aesthetic-style-direction/notes/verification-ledger.md`, carrying
  the reviewer's name and the date.
- **No TDD.** There is no compressible invariant and no Python surface in this
  change.

## Acceptance Criteria

### The direction sheet

- [ ] `creative-direction/assets/creative-direction-template.md` carries a
      direction-sheet section whose axis rows are exactly these fifteen, in
      this order: grid grammar, alignment and equilibrium, spatial density,
      whitespace distribution, hierarchy and scale contrast, containment and
      boundary strength, section and scroll rhythm, type voice, type hierarchy,
      chromatic intensity, form, material and depth, ornament and texture,
      image treatment, motion character. *(goal-based)*
- [ ] Each axis row states a token vocabulary, and every vocabulary includes
      `[platform-default]`. *(goal-based)*
- [ ] Each axis cell opens with one or more tokens in square brackets drawn
      from that row's vocabulary, followed by prose. An axis carrying two
      independent parameters carries two tokens. *(goal-based)*
- [ ] Every axis cell ships filled with its `[platform-default]` token rather
      than a placeholder, so an unedited copy is syntactically valid and
      visibly undecided. *(goal-based)*
- [ ] No axis cell matches any pattern in `tools/lint-experience-agnostic.py`.
      This is the literal-and-stack floor only. *(goal-based)*
- [ ] Each axis cell names a role, classification, or relationship rather than
      a value. *(manual QA)*

### The counterfactual gate

- [ ] `creative-direction/SKILL.md` carries a numbered procedure step directing
      the author to fill the direction sheet before capturing the doc.
      *(goal-based)*
- [ ] `creative-direction/SKILL.md` carries a numbered procedure step requiring
      the author to work through a similar brief, compare the result, revise
      any part that matches the generic default, and record what changed and
      why. *(goal-based)*
- [ ] That step names the revision record as a required field of the direction
      doc, and the template carries a section that holds it. *(goal-based)*

### The presets

- [ ] `creative-direction/assets/presets/` contains exactly three files, for
      Swiss / International Typographic, editorial broadsheet, and Bauhaus.
      *(goal-based)*
- [ ] Each preset carries a formal-commitments section, a line naming what a
      direction borrowing it leaves behind, a `Best used for:` line, and all
      fifteen axis rows filled. *(goal-based)*
- [ ] Every bracketed token used in a preset's axis row belongs to that row's
      vocabulary in the template, verified by extracting and comparing the two
      token sets per row. *(goal-based)*
- [ ] Each preset's formal commitments are those its style carries in
      `docs/product/research/aesthetic-style-blueprint.md` §F2.2, which is the
      closed source. *(manual QA)*
- [ ] `creative-direction/SKILL.md` names the preset set and states that a
      preset supplies precedent only and is never a finished direction.
      *(goal-based)*

### The divergence audit

- [ ] `creative-direction/references/divergence-audit.md` exists and specifies
      comparing N candidate directions pairwise across the fifteen axes.
      *(goal-based)*
- [ ] It reports the minimum pairwise distance across the candidate set and
      states that the mean is not the reported figure. *(goal-based)*
- [ ] It treats a pair as distinct when at least **six of the fifteen** axes
      differ, and records that six-of-fifteen is the ten-axis reasoned default
      of four carried across proportionally, not a measured value, naming the
      blueprint's Known-unknowns experiment as what would measure it.
      *(goal-based)*
- [ ] Its comparison rules are stated and unambiguous for the cases that arise:
      differing token tuples, paraphrased prose after identical tokens, and
      `[platform-default]` on both sides. *(manual QA)*

### The rating instruments

- [ ] `design-review/references/taste-critique.md` carries the four VisAWI-S
      items, each labelled with its facet. *(goal-based)*
- [ ] It carries the four UEQ Novelty word pairs. *(goal-based)*
- [ ] It states the response format for each instrument, attributes each to its
      source, and states that items are reported individually and never
      combined into one score. *(goal-based)*

### Release and registration

- [ ] `packs/experience-design/pack.toml` and
      `packs/experience-design/.claude-plugin/plugin.json` both read `2.0.6` —
      a patch bump, because additions inside an existing skill are changed
      content, not a new primitive. *(goal-based)*
- [ ] `.claude-plugin/marketplace.json` reads `2.0.6` for `experience-design`,
      regenerated by self-host rather than hand-edited. *(goal-based)*
- [ ] `docs/product/changelog.md` carries a free-standing
      `## [experience-design][2.0.6] — <YYYY-MM-DD>` entry at the top level,
      directly beneath `[Unreleased]` and not nested inside it. *(goal-based)*
- [ ] That entry carries one `Highlights` subsection one heading level below
      it, because the release changes what a consumer can do. *(goal-based)*
- [ ] Every heading added to `docs/product/changelog.md` has exactly one blank
      line above and below it. *(goal-based)*
- [ ] `creative-direction/evals/evals.json` carries an assertion naming the
      direction sheet and an assertion naming the counterfactual revision
      record, each matching the file's existing assertion shape. *(goal-based)*
- [ ] `design-review/evals/evals.json` carries an assertion naming the two
      rating instruments, matching the file's existing assertion shape.
      *(goal-based)*

### Gates

- [ ] `tools/lint-experience-agnostic.py` exits 0 over `packs/experience-design/`.
      *(goal-based)*
- [ ] The three `tests/roster/test_experience_design_*.py` suites pass.
      *(goal-based)*
- [ ] The five commands in `guides/AGENTS.md` § Essential commands each exit 0:
      `validate_guides.py`, `check-guide-index.py`, `lint-guide-titles.py`,
      `lint-guidebook-steps.py guides/experience-design`, and `build-site.py`.
      *(goal-based)*
- [ ] `catalogue lint --root . --deep` and `catalogue verify --root .` each exit
      0, run after the projection is regenerated. *(goal-based)*
- [ ] `docs/specs/aesthetic-style-direction/notes/verification-ledger.md`
      records all four manual-QA verdicts with the reviewer's name and date,
      and is committed in the same change. *(goal-based)*

### Documentation

- [ ] A guide under `guides/experience-design/` covers the direction sheet, the
      counterfactual gate, the presets, and the divergence audit. Sufficiency
      is the recorded reviewer verdict, not a keyword count. *(manual QA)*

## Follow-ons

- Product owner: `docs/product/research/aesthetic-style-blueprint.md` §F2.2 — a
  Material preset was excluded as a scope choice, not a governance bar. Naming
  Material 3 as a grounding standard is already permitted
  (`creative-direction/SKILL.md:89`), and §F2.2 supports value-free Material
  commitments on the same footing as the three presets that shipped. Revisit on
  request.
- Repository maintainer: `packs/AGENTS.local.md:29` and root
  `AGENTS.local.md:60` conflict on whether a pack release may pass `FORCE=1` to
  `make build-self`. This delivery routes around the conflict by surfacing;
  the conflict itself needs an owner decision.
- Product owner: `docs/product/research/aesthetic-style-blueprint.md` § Known
  unknowns — the six-of-fifteen distinctness threshold is a reasoned default
  carried across from four-of-ten, not a measured value. The blueprint names
  the experiment that would measure it.

## Assumptions

- Technical: `packs/experience-design/tests/` does not exist; this pack's tests
  live in `tests/roster/` (source: directory listing, 2026-09-18).
- Technical: no test hashes, snapshots, or line-counts the target files. The
  roster suite asserts at least the exact `**Writes:**` set, the exact
  creative-direction output path, the exact `**Confinement:**` lines, byte
  equality across `containment.md` copies, and bidirectional agreement between
  module citations and shipped copies; this list is not claimed complete
  (source: `tests/roster/test_experience_design_write_declaration_and_containment.py`).
- Technical: `tools/lint-experience-agnostic.py` takes no file argument and
  always scans the whole pack, so it is a post-wave controller check and never
  task-local evidence (source: `tools/lint-experience-agnostic.py:160-164`).
- Technical: `design-review/SKILL.md:69` already loads
  `references/taste-critique.md` as the full method, so new content there is
  integrated without editing that `SKILL.md` (source: adjudicated finding,
  round 1).
- Process: a non-cosmetic `.apm/**` change owes matching version bumps and an
  eval-harness update (source: `packs/AGENTS.md` § Version bump rule and
  § Security and authoring rules).
- Product: the axis set is fifteen, seven structural, on the evidence in
  blueprint §F2.1b that structural factors have broader and greater aesthetic
  effects than colour factors (source: user confirmation 2026-09-18).
- Product: Material is excluded from the preset set as a scope choice (source:
  user confirmation 2026-09-18). An earlier draft justified this on an RFC-0033
  bar; adjudicated finding 11 established no such bar exists.

# Spec: Creative direction — five operations, divergence generation, and a capability-gated visual step

- **Status:** Draft <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0033 (experience-design framework agnosticism); ADR-0116 (`direction/` folder)
- **Brief:** none — this spec stands alone; the consolidation work it surfaced is coordinated separately
- **Discovery:** [`docs/product/research/aesthetic-style-blueprint.md`](../../product/research/aesthetic-style-blueprint.md)
- **Contract:** none
- **Shape:** ui

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.

## Outcome

A designer naming a visual direction gets materially different candidates to
choose between, each expressed as concrete commitments rather than adjectives,
and records which one a human selected. They reach that through one skill with a
compact always-loaded body, its craft detail loading only when an operation needs
it.

## What Changes

- The ten-step procedure becomes five named operations — `frame`, `explore`,
  `visualize`, `converge`, `refine` — in `creative-direction/SKILL.md`.
- A route rule picks how much invention the work warrants — `inherit`, `extend`,
  `originate` — in `SKILL.md`.
- Divergence generation arrives as `references/explore.md`; the existing
  `references/divergence-audit.md` becomes its exit gate rather than a
  free-floating file.
- Human selection, the standing exit, and the borrowed-discipline record arrive
  as `references/converge.md`.
- A capability-gated visual step arrives as `references/visualize.md`, with a
  text schematic as its default representation.
- One refinement operation arrives as `references/refine.md`, carrying the
  request-wording-to-axis map.
- The genre canonical reference tier moves out of `SKILL.md` into
  `references/referents.md`, recast as craft calibration.
- The existing `## Anti-patterns to refuse` entries move into
  `references/refusals.md`.
- The direction template gains a `status` frontmatter field, a
  borrowed-discipline record, and a refinement-amendment record.
- `evals/` gains four behavioural cases and new trigger queries.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Current product truth | Applicable — a published skill's execution model changes | `packs/experience-design/.apm/skills/creative-direction/` | This spec | Rewritten `SKILL.md`, six new references, edited template | Files exist; pack lint and the roster suites are clean |
| Current product truth | Applicable — the reviewer's lens cites this skill's vocabulary | `packs/experience-design/.apm/agents/experience-reviewer.md` | This spec | Its grounded-aesthetic-fit lens names vocabulary the artifact still carries | The lens and the template agree |
| User promise | Applicable — the skill gains operations a user invokes | `guides/experience-design/` | `author-product-docs` | Guide text covering the route rule and the five operations | Guide-agreement test passes and a named reviewer judges the guide sufficient |
| Interface compatibility | Applicable — `.apm/**` non-cosmetic change | `packs/experience-design/pack.toml`, `.claude-plugin/plugin.json`, regenerated `.claude-plugin/marketplace.json` | `packs/AGENTS.md` § Version bump rule | Matching patch bump in both source manifests; marketplace projection regenerated, never hand-edited | All three read `2.0.10` |
| Release history | Applicable — a released artifact's version is bumped | `docs/product/changelog.md` | That file's own header rules | A free-standing `## [experience-design][2.0.10] — <date>` entry directly beneath `[Unreleased]`, carrying one `Highlights` subsection | The entry sits at the right heading level with single blank lines around every heading |
| Reusable learning | Applicable — evals are the pack's behavioural record | `creative-direction/evals/` | `packs/AGENTS.md` § Security and authoring rules | Four Tier-B cases and new Tier-A trigger queries | Both files parse and carry the named cases |

## Agent Rules

### Always do

- Keep exactly one `**Writes:**` line and exactly one `**Confinement:**` line in
  `creative-direction/SKILL.md`, byte-identical to their current form **including
  their backticks**. `tests/roster/test_experience_design_write_declaration_and_containment.py`
  asserts the parsed set equals a single expected value, so a second declaration
  line fails the suite even when the first is unchanged.
- Keep the artifact contract unchanged: target `<output_dir>/direction/<slug>.md`,
  frontmatter `type: creative-direction`. Three roster suites and
  `frontend-engineering`'s design-handoff read pin this pair.
- Keep the fifteen axis names and their token vocabularies exactly as the
  template defines them. `evals.json` names "fifteen axes"; the divergence audit
  and the new explore operation both compute over that set.
- Carry the counterfactual check and the direction-sheet fill forward intact.
  Both are Shipped acceptance criteria of `aesthetic-style-direction`, and the
  reorganisation must name which operation owns each rather than dissolving them
  into the new structure.
- Keep `references/containment.md` byte-identical to every other copy in the
  pack; a roster suite asserts byte equality across all five.
- Express every operation, axis, and anti-pattern at the level of roles,
  classifications, and relationships — never a literal value.
- Bump `pack.toml` and `.claude-plugin/plugin.json` together, in the same edit.
- Update `guides/experience-design/how-to/establish-design-intent.md` in the same
  change as any `SKILL.md` change the guide-agreement suite compares.

### Ask first

- Adding any new `<output_dir>/<folder>/` declaration. **This delivery declares
  none**: a visual artifact lands beside its direction doc under the existing
  `direction/` folder, or is not persisted at all.
- Changing the managed `agentbundle:output-rendering` block in `SKILL.md`.
- Removing or renaming any skill, or editing `frontend-engineering`'s
  genre-routing table. The sibling specs own that work.
- Passing `FORCE=1` to `make build-self`. `packs/AGENTS.local.md` prescribes it
  for a pack release; root `AGENTS.local.md` forbids automation passing it. This
  delivery runs the unforced form and surfaces a refusal rather than resolving
  the conflict on its own authority.

### Never do

- Cite a repository-internal record from any file under `.apm/`. `packs/AGENTS.md`
  § *Shipped pack content carries no internal-governance citations* forbids it,
  and no file under `packs/experience-design/.apm/` cites `docs/` today. A rule
  that research supports is stated directly in the reference; the provenance
  lives in this spec's `Assumptions`.
- Write a colour literal, a **unit-bearing** dimension or duration literal
  (`px`, `ms`, `rem`, `em`, `pt`, `vh`, `vw`, decimal seconds), a contrast or
  scale ratio, a named easing curve, an ARIA role, CSS syntax, a UI-framework
  name, or a concrete typeface name into any file under
  `packs/experience-design/`. A **structural count** carries no unit and pins no
  stack and is permitted (owner decision, 2026-09-18, carried forward).
- Write an **unprefixed** backticked folder span into `SKILL.md` naming a folder
  outside the declared set. `tests/roster/test_experience_design_artifact_folder_registry.py`
  exempts spans already prefixed with `<output_dir>/` or the configured base, so
  `` `<output_dir>/direction/` `` is safe and required, while a bare
  `` `references/` `` adds a phantom folder to the declared set and reds the
  suite against `DESIGN.md`.
- Reuse wording from any source the prior-art study examined. Take mechanisms
  only and write them in this pack's own voice. Reused text can carry an
  attribution obligation this pack does not otherwise have, so the rule holds
  however permissive the source licence is.
- Add a second quality floor. The pack's floor is
  `../design-review/references/quality-floor.md` and stays the single floor.
- Weaken or remove any existing anti-pattern, grounding requirement, accessibility
  requirement, or quality-floor precedence.
- Require a harness capability. No operation may block on image generation, a
  browser, a subagent, or a script. Every operation completes on a
  markdown-only harness.
- Leave an axis cell blank. Undecided is written `[platform-default]`.
- Edit generated adapter projections directly instead of `.apm/` sources.

## Testing Strategy

Two modes are in use. Every criterion below is tagged with the one that settles
it, and the two lists are exhaustive of each other — a judgement named here has a
criterion, and a criterion tagged manual QA appears here.

- **Goal-based check** — settleable by a command: a file exists, a named string
  is present or absent in a named file, a token set matches, a byte count falls
  below a stated ceiling, a version reads, a gate exits 0. `plan.md` carries the
  commands, split across two surfaces that partition this set rather than
  duplicating it: its **Verification command map** holds the cross-task
  criteria, the gate invocations, and the measurements more than one task reads;
  every criterion local to a single task is settled by that task's `Tests:`.
- **Manual QA** — the six judgements no command reaches:
  1. whether the four behavioural eval cases distinguish old behaviour from new;
  2. whether each operation's stability contract is complete and non-overlapping;
  3. whether the operation-selection rubric is decidable without loading a
     reference;
  4. whether the anti-pattern reference's era labelling is honest;
  5. whether the guide is sufficient;
  6. whether any sentence in `SKILL.md` or `references/` makes a visual artifact
     a precondition for writing the direction doc.

  A named reviewer's recorded verdict **is** the result. The artifact is
  `docs/specs/creative-direction-modes/notes/verification-ledger.md`, carrying the reviewer's name and the date.
- **No TDD.** There is no compressible invariant and no Python surface.

Behavioural evals are Tier-B rubric content. Automated Tier-B grading is deferred
repository-wide, so the four cases are authored to the existing assertion shape
and graded by the judge mode, not asserted by pytest.

## Acceptance Criteria

### The route rule

- [ ] `SKILL.md` carries a routing table with exactly three routes, named
      `inherit`, `extend`, and `originate`, each stating its trigger condition
      and which operations run. *(goal-based)*
- [ ] The table states that `inherit` runs no divergence and no visual step.
      *(goal-based)*
- [ ] The table states that a section, component, state, or feature added inside
      a surface that already has a direction takes `inherit`. *(goal-based)*
- [ ] The route rule directs a lookup of `<output_dir>/direction/` to decide
      whether a direction already owns the surface, and states that the lookup
      is evidence-gathering, not a reference load. *(goal-based)*

### Every surviving step and reference has an owner

- [ ] `SKILL.md` or an operation reference assigns each of the ten current
      procedure steps to exactly one operation, and the spec's own mapping is:
      map the audience → `frame`; run the interrogation → `frame`; ground each
      goal → `converge`; rank the goals → `converge`; record arbitration →
      `converge`; fill the direction sheet → **`explore` for each candidate's
      sheet, `converge` for the selected direction's sheet** (two distinct acts,
      named separately so each has one owner); run the counterfactual check →
      `converge`; hold the floor → `converge` **and** `refine`; capture the doc
      (`output_dir` resolution, the containment controls, the template copy) →
      `converge`; hand off to `design-system` → `converge`. *(goal-based)*
- [ ] Every reference the skill ships today is still reachable from the
      operation that owns it: `audience-jtbd.md` and `interrogation-sequence.md`
      from `frame`; `grounding.md`, `coherence-arbitration.md`,
      `divergence-audit.md`, `containment.md` and `agentbundle-layout.md` from
      the operations that use them. A reference no operation links is orphaned,
      and `grounding.md` is this skill's largest reference at 11,341 bytes. *(goal-based)*
- [ ] The capture sequence still applies every containment control in the order
      `references/containment.md` states, and still resolves `output_dir` before
      composing a target. The `**Writes:**` / `**Confinement:**` contract has no
      other operative procedure. *(goal-based)*

### The five operations

- [ ] `SKILL.md` names exactly five operations — `frame`, `explore`,
      `visualize`, `converge`, `refine` — each with a one-line purpose.
      *(goal-based)*
- [ ] Each of `explore`, `visualize`, `converge`, and `refine` links to the
      reference carrying its method. *(goal-based)*
- [ ] `frame` carries its method inline in `SKILL.md`, links at least the
      existing `references/audience-jtbd.md` and
      `references/interrogation-sequence.md` alongside the shared
      `references/refusals.md`, and ships no reference of its own. The list is
      a minimum, not a closed set. *(goal-based)*
- [ ] `frame` states the terse set it establishes: audience and ranked JTBD,
      target surface, incumbent constraints, intended effect, what must stay
      recognisable, what would read as generic, **and the named goals the
      interrogation produces — short noun phrases, each sharpened against its
      opposite**. The goals are the interrogation's output and `frame` owns that
      step, so a set omitting them reads as exhaustive and drops them.
      *(goal-based)*
- [ ] `frame` states that it does not recreate product discovery or journey
      design, and names where those belong. *(goal-based)*
- [ ] Each operation states what it may change and what must remain stable.
      *(manual QA — judgement 2)*
- [ ] `SKILL.md` carries a selection rubric that picks the operation from the
      request **without loading any reference**. *(manual QA — judgement 3)*

### Divergence generation

- [ ] `references/explore.md` exists and directs the author to name the category
      default arrangement for the brief **and** its predictable opposite, and to
      exclude both from the candidate set. *(goal-based)*
- [ ] It directs referent derivation from the audience's own world — naming at
      least publications, physical artifacts, instruments and notation, maps,
      architecture, packaging, signage, and historical graphic systems as source
      classes — and states that other software products are not the primary
      source. *(goal-based)*
- [ ] It states a material-family spread rule: when more than half the candidate
      referents share one material family, the derivation stopped at the obvious
      artifact and must continue. *(goal-based)*
- [ ] It requires each surviving candidate to carry its own filled direction
      sheet, so candidates differ by axis tokens rather than by adjective.
      *(goal-based)*
- [ ] It hands off to `references/divergence-audit.md` and states that a set
      failing the six-of-fifteen minimum pairwise distance is not a candidate set
      and sends the author back to derive more. *(goal-based)*
- [ ] It states that a candidate derived primarily from a named software product
      has not left the category default. *(goal-based)*

### Human selection and convergence

- [ ] `references/converge.md` requires presenting surviving candidates at equal
      salience, with a comparison limited to the axes on which they differ.
      *(goal-based)*
- [ ] It defines a standing exit — the category standard, played straight —
      offered in every divergence round, never recommended by the agent, and
      executed at full commitment when chosen. *(goal-based)*
- [ ] It requires recording, for the selected direction, one named discipline
      taken from a rejected candidate, or an explicit statement that none was.
      *(goal-based)*
- [ ] `converge.md` owns the counterfactual check and states that the record is a
      required field of the direction doc, preserving the behaviour
      `aesthetic-style-direction` shipped. *(goal-based)*
- [ ] `converge.md` owns the direction-sheet fill across all fifteen axes,
      preserving the behaviour `aesthetic-style-direction` shipped.
      *(goal-based)*
- [ ] `SKILL.md` states that the agent does not choose among materially different
      directions on its own; a delegated choice is recorded as delegated.
      *(goal-based)*

### The template

- [ ] The template's frontmatter carries a `status` field whose value is one of
      `proposed`, `selected`, `inherited`, and the template documents which
      operation sets each. *(goal-based)*
- [ ] The template carries a section holding the borrowed-discipline record,
      naming the donor candidate and the discipline taken. *(goal-based)*
- [ ] The template carries a section holding a refinement amendment: which axes
      moved, from which token to which, and why. *(goal-based)*
- [ ] The template still carries `type: creative-direction` in frontmatter and
      the target path is unchanged. *(goal-based)*
- [ ] The template retains its `## Counterfactual check` section and all fifteen
      direction-sheet axis rows. *(goal-based)*
- [ ] The template carries a named section holding an approved visual target's
      compositional commitments. Without one they land wherever the agent
      chooses, which is the reach failure the binding criterion exists to close.
      *(goal-based)*

### The visual step

- [ ] `references/visualize.md` defines exactly three representations and their
      binding force: a **semantic direction** (the filled sheet, binding), a
      **visualised candidate** (illustrative, non-binding), and an **approved
      visual target** (binding on composition only). *(goal-based)*
- [ ] It states that an approved visual target never binds colour, type, spacing,
      or motion values, which remain `design-system`'s to derive. *(goal-based)*
- [ ] It requires an approved visual target's compositional commitments to be
      written into `<output_dir>/direction/<slug>.md` itself. A file beside the
      direction doc sits off every path
      `frontend-engineering`'s handoff reads, so a commitment recorded only there
      reaches no consumer. *(goal-based)*
- [ ] It names a text schematic as the default representation and states the
      wireframe-over-screenshot rule directly, with no citation to any
      repository-internal record. *(goal-based)*
- [ ] It states that a rendered comp is produced only when the harness can
      produce one and the route is `originate`, and that its absence is a named
      skip, never a blocker. *(goal-based)*
- [ ] Searching `SKILL.md` and every file under `references/` for `comp`,
      `render`, `image`, `mock` and `wireframe` returns no hit inside a sentence
      whose main clause makes the direction doc conditional on producing one.
      *(manual QA — judgement 6)*

### Refinement

- [ ] `references/refine.md` defines one operation that takes a requested change
      in plain words and maps it to the axes that may move. *(goal-based)*
- [ ] It carries a mapping from common request wordings — at minimum bolder,
      quieter, distill, typeset, layout, colorize, and delight — to the axes each
      puts in play, and states that these are request wordings, not separate
      operations. *(goal-based)*
- [ ] It states the stability contract: ranked goals, dominant goal, grounding
      referents, the signature device, and every unnamed axis stay fixed.
      *(goal-based)*
- [ ] It requires the result to be recorded as an amendment to the existing
      direction doc and forbids writing a second direction doc for the same
      surface. *(goal-based)*
- [ ] It refuses to reopen goals, audience, or product strategy, and says where
      those belong. *(goal-based)*
- [ ] `refine` holds the quality floor before recording its amendment. A
      refinement that moves a chromatic or type axis can breach the floor, and
      `refine` writes without passing through `converge`, so without this the
      floor precedence the Agent Rules forbid weakening has a hole.
      *(goal-based)*

### The existing anti-patterns keep a home

- [ ] All seven entries of `SKILL.md`'s current `## Anti-patterns to refuse`
      section survive, in `references/refusals.md`, which every operation links.
      They are refusals about this skill's own failure modes — printing values,
      unranked goals, ungrounded goals, copying an example whole — and are a
      different artifact from the model-era classification in
      `references/referents.md`, whose entries are named products.
      *(goal-based)*
- [ ] No anti-pattern is reworded to a weaker obligation in the move.
      *(goal-based)*

### Referents demoted to craft calibration

- [ ] The genre canonical reference tier moves out of `SKILL.md` into
      `references/referents.md`. *(goal-based)*
- [ ] That reference states the tier calibrates craft level and is not a source
      of candidates during `explore`. *(goal-based)*
- [ ] It carries the existing requirement to name which qualities of a reference
      are taken and which are left. *(goal-based)*

### Model-era anti-patterns, separated from invariants

- [ ] `references/referents.md` carries a section classifying each of its entries
      as a **quality invariant**, a **useful heuristic**, or a **model-era
      anti-pattern**, with no entry unclassified. *(goal-based)*
- [ ] Every model-era entry carries the period it describes. *(goal-based)*
- [ ] Its era labelling distinguishes a dated observation from a durable one
      honestly. *(manual QA — judgement 4)*
- [ ] It states that the accessibility floor is not among its entries and points
      to `../design-review/references/quality-floor.md`. *(goal-based)*

### Context footprint

- [ ] `SKILL.md`'s authored body — the file's bytes minus its frontmatter and
      minus the managed `agentbundle:output-rendering` block, inclusive of both
      delimiter comments — is at most **6,500 bytes**. Measured: the pre-fold
      body is 9,699 bytes and the four departing sections total 8,126
      (procedure 4,062, genre tier 2,557, presets 342, anti-patterns 1,165),
      leaving 1,573; the route table, five operations and rubric arriving are
      budgeted at roughly 4,000, for about 5,573 against the ceiling. The real
      margin is roughly 900 bytes, not the 1.5 KB a rounded departure figure
      would imply. *(goal-based)*
- [ ] `SKILL.md` carries no enumeration of the fifteen axis names and no preset
      descriptions; both are reachable by link. *(goal-based)*
- [ ] The ten-step procedure body does not survive in `SKILL.md`; its method
      lives in the operation references. *(goal-based)*
- [ ] The sum of file bytes under
      `packs/experience-design/.apm/skills/creative-direction/` is at most
      **95,000 bytes**. Failing state: the directory grew by more than the six
      new reference files and the template's three new sections account for.
      *(goal-based)*
- [ ] The frontmatter `description` stays within 1024 characters and continues to
      name the skill's boundaries against `design-system`,
      `information-architecture`, and `design-review`. *(goal-based)*

### Behavioural evaluation

- [ ] `evals/evals.json` carries four new cases matching the file's existing
      shape, one per scenario: **A** incumbent extension, **B** generic new SaaS
      surface, **C** domain-rich product, **D** refinement of a selected
      direction. *(goal-based)*
- [ ] Case A asserts that no divergence round runs and no second direction doc is
      written. *(goal-based)*
- [ ] Case B asserts that the category default and its opposite are both named
      and both excluded, and that surviving candidates differ on at least six
      axes. *(goal-based)*
- [ ] Case C asserts that a majority of candidate referents come from the
      audience's domain rather than from software products. *(goal-based)*
- [ ] Case D asserts that only the named axes moved, that the ranked goals and
      dominant goal are unchanged, and that the existing doc was amended rather
      than replaced. *(goal-based)*
- [ ] Run against the pre-change skill, A and D pass and B and C fail.
      *(manual QA — judgement 1)*
- [ ] `evals/eval_queries.json` gains `should_trigger: true` entries for
      refinement-shaped requests against an existing direction, and
      `should_trigger: false` entries for requests that belong to `design-system`
      or `design-review`. *(goal-based)*

### Compatibility

- [ ] `references/containment.md` is unchanged and still byte-identical across
      all five copies. *(goal-based)*
- [ ] No new `<output_dir>` subfolder is declared, and `SKILL.md` contains no
      unprefixed backticked folder span naming a folder outside the declared
      set — the same test `_folder_mentions` applies, which permits
      `` `<output_dir>/direction/` ``. *(goal-based)*
- [ ] `experience-reviewer`'s grounded-aesthetic-fit lens and the revised
      template share this exact set of four grounding terms: **persona**,
      **precedent**, **standards**, **platform conventions**. Where the template
      renames one, the agent is updated in this change. *(goal-based)*
- [ ] `packs/experience-design/DESIGN.md` § 10 is **not** edited by this
      delivery. Its genre-skill entry is still accurate while all six skills
      exist, `xd-genre-router` authors the amendment once when they stop
      existing, and an entry written here would carry a known one-slice lifetime
      plus an owner this spec would have to invent. *(goal-based)*

### Release and registration

- [ ] `pack.toml` and `.claude-plugin/plugin.json` both read `2.0.10` — a patch
      bump, because reorganising an existing skill and adding references inside it
      is changed content, not a new primitive. *(goal-based)*
- [ ] `.claude-plugin/marketplace.json` reads `2.0.10` for `experience-design`,
      regenerated by self-host rather than hand-edited. *(goal-based)*
- [ ] `docs/product/changelog.md` carries a free-standing
      `## [experience-design][2.0.10] — <YYYY-MM-DD>` entry at the top level,
      directly beneath `[Unreleased]`, with one `Highlights` subsection and
      exactly one blank line above and below every heading added. *(goal-based)*

### Gates

- [ ] `python3 tools/lint-experience-agnostic.py` exits 0. *(goal-based)*
- [ ] These roster suites pass:
      `test_experience_design_write_declaration_and_containment.py`,
      `test_experience_design_artifact_folder_registry.py`,
      `test_experience_design_guide_agreement.py`,
      `test_experience_journey_composition.py`,
      `test_design_handoff_contract_matches_corpus.py`. *(goal-based)*
- [ ] `agentbundle catalogue lint --root . --deep` and
      `agentbundle catalogue verify --root .` each exit 0, run after the
      projection is regenerated. *(goal-based)*
- [ ] The five commands in `guides/AGENTS.md` § Essential commands each exit 0.
      *(goal-based)*
- [ ] `make lint-ruff lint-mypy` exits 0. *(goal-based)*
- [ ] `docs/specs/creative-direction-modes/notes/verification-ledger.md` records all six manual-QA verdicts with the
      reviewer's name and date, and is committed in the same change.
      *(goal-based)*

### Documentation

- [ ] A guide under `guides/experience-design/` covers the route rule and the
      five operations. *(manual QA — judgement 5)*
- [ ] That guide's `**Where it lands:**` path agrees with `SKILL.md`, which the
      guide-agreement suite already checks. *(goal-based)*

## Follow-ons

- Repository maintainer: investigating this skill surfaced a separate
  consolidation outcome — the pack's twenty registrations, their resident cost,
  and a stale cross-pack routing contract. That work is measured in
  [`experience-design-consolidation-analysis.md`](../../product/research/experience-design-consolidation-analysis.md)
  and coordinated by `brief:experience-design-skill-consolidation`. It shares no
  outcome with this spec; the only coupling is that both edit `DESIGN.md`,
  `pack.toml` and the changelog, so this spec lands first.
- Repository maintainer: `agentbundle-layout.md` exists in twelve copies across
  the pack in nine distinct versions, while `containment.md` in five copies has
  not drifted because a roster suite asserts byte equality. The asymmetry names
  its own fix. `digital-experience-doctrine-completion` routes that S8a family
  **out** of itself to an intake candidate named
  `experience-design-reference-reconciliation`, which has no admitted intent
  yet, so it is currently unowned rather than owned elsewhere.
- Product owner: the six-of-fifteen distinctness threshold remains a reasoned
  default, not a measured value, and now governs a generation step as well as an
  audit. `aesthetic-style-blueprint.md` § Known unknowns names the experiment.

## Assumptions

- Technical: `frontend-engineering`'s design-handoff read takes the first
  heading, the frontmatter as found, and the body as one opaque block, keying on
  no section name — so the template's internal structure may change freely
  (source: `packs/frontend-engineering/.apm/skills/frontend-engineering/references/design-handoff.md:36-57`).
- Technical: the roster suites pin the `**Writes:**` and `**Confinement:**`
  lines as a single-element set, the `direction/<slug>.md` + `creative-direction`
  pair, `containment.md` byte equality, the `direction/` folder registry derived
  from backticked folder spans, the guide's landing path, and the backticked
  crossing-artifact string in both JOURNEY files (source: consumer sweep over
  `tests/roster/`, 2026-09-24).
- Technical: `tools/lint-experience-agnostic.py` takes no file argument and
  always scans the whole pack, so it is a post-wave controller check and never
  task-local evidence.
- Technical: the pack ships no `tests/` directory; its gates are the roster
  suites and the `tools/` lints (source: directory listing, 2026-09-24).
- Technical: automated Tier-B eval grading is deferred repository-wide, so the
  four behavioural cases are judge-mode rubric content rather than pytest
  assertions (source: `guides/_shared/how-to/author-a-skill.md`).
- Product: structured visual input and iterative critique are supported by the
  repository's research, which also found simple wireframes outperformed
  detailed screenshots; plan-before-code as a sequence is not validated (source:
  `aesthetic-style-blueprint.md` § F3.4). This is why the text schematic is the
  default representation. The reference states the rule; it does not cite this
  source, because shipped pack content carries no internal-governance citation.
- Product: a craft floor does not belong under this skill. § 4 of the blueprint
  prescribes a two-layer split — mechanical rules in one place, art direction
  separately staged — and § F3.2 measures what merging them produced elsewhere.
- Legal: the prior-art study confirmed that the licences involved attach their
  attribution obligation to reused text, not to reused ideas. This delivery
  takes mechanisms only, so no notice obligation is incurred (source: licence
  and notice files checked during the study, 2026-09-24).

# Spec: design-output-addressing

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **T11 scope decision:** the four case families the plan's T11 names beyond
  this spec's own refusal criterion are scoped out by the owner, eugenelim,
  2026-09-17, under `plan.md`'s second completion branch. Recorded in
  [`notes/verification-ledger.md`](notes/verification-ledger.md) § Owner waiver.
  This is **not** an unstageability waiver under § Boundaries § Never do: those
  four cases are stageable, and the decision was taken on cost. The refusal
  criterion in § Acceptance Criteria is unaffected and is separately evidenced.
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0033 — it declares Guardrails A and B, which
  `tools/lint-experience-agnostic.py` enforces as their mechanical floor, and this
  change adds the token-taxonomy template to the tree that lint governs.
- **Brief:** none
- **Discovery:** none
- **Contract:** none — no synchronous, event, or RPC interface surface.
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Boundaries`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Objective`, `Durable Outputs`, `Follow-ons` and `Assumptions`
> are working material: an author corrects them in place as the work teaches.

## Objective

The guides stop promising artifacts that never appear, and the three skills that
genuinely write one get an address the adopter controls.

As this spec was written, nineteen how-to steps published a `**Where it lands:**`
path — the baseline the criteria below are measured against. Twelve do now,
because § *Already shipped ahead of this spec* corrected seven of them. The
nineteen divide as follows, and the four groups are exhaustive:

- **Seven** name a path the owning skill declares.
- **Three** name a real write the skill states no location for, one of them by a
  fixed repository path that ignores the adopter's configuration.
- **One** names a file for a skill that writes into a *different* skill's artifact.
- **Eight** name a file the skill never writes — the six genre skills have no
  output step, `design-review` only reads, and `design-system` stops at "record
  the taxonomy" with no file — so an adopter following the guide waits for a file
  that does not arrive.

One of those eight is treated differently. `design-system` is the only non-writer
with a named downstream consumer: the shared Digital Experience Contract carries a
`Design System Reference` field at pilot tier asking which token taxonomy a
surface uses, and the frontend pack fabricates its own tokens every session for
want of one. It gains a write step, because token seeding is how design actually
reaches code. The other seven produce in-session advice and gain nothing but an
honest guide line — and those seven are what the carve-out already shipped.

This change makes each of the nineteen say what its skill does, moves the three
existing writes and the one new one onto `[design] output_dir`, and repoints the
one read that a relocation would otherwise break. Because all four writes are
adopter-rooted, each carries the approval and confinement controls
`packs/AGENTS.md` requires.

## Already shipped ahead of this spec

The guide correction for the seven non-writers was taken as a deliberate
light-mode carve-out before this spec was approved, on the ground that correcting
prose creates no trust boundary while declaring a write path does. That change
edited only `guides/experience-design/how-to/design-each-screen.md` and
`review-independently.md`, replacing each of the seven steps' `**Where it lands:**`
label with `**Writes no artifact.**` and correcting the simulated agent-returns
line that claimed the file had been written.

`interaction-design`'s line was **not** part of it. Three further edits were
attempted and reverted, because each reached into an obligation beyond the
accepted intent and produced more findings than it closed across two review
rounds. None of the three is owed a follow-on: one is back in scope under a
criterion and the other two need no further work.

- **Repointing `interaction-design`'s line** — in scope, discharged by a criterion
  below and implemented by the plan. The path it publishes is orphaned, and
  correcting it introduces `<screen>` as a segment the page must then resolve.
- **Giving `information-architecture`'s invented path reader-visible provenance** —
  no follow-on owed. This spec's first criterion gives that skill a declared path,
  which removes the invented one rather than annotating it.
- **Trimming `review-independently`'s segment resolution** — no follow-on owed, and
  the attempt was simply wrong: `docs/guides/guidebook-step-contract.md:105-110`
  requires that line on every step, repetition included.

The one criterion below that the carve-out satisfies is marked `(shipped ahead)`;
it remains in the list because this spec is the record of the whole outcome, and a
reader comparing the spec to the tree needs to know why part of it is already
true.

## The skill set this spec quantifies over

Twenty skill directories exist under `packs/experience-design/.apm/skills/` and
this change adds none. Every universal claim below names one of these subsets.
The set is stated here rather than derived from the guides, because the guides are
a surface this change edits.

| Subset | Count | Skills |
| --- | --- | --- |
| **Declaring writers** — already resolve a write target through `output_dir` | 7 | `content-design`, `copy-direction`, `journey-mapping`, `process-mapping`, `service-blueprint`, `tone-of-voice`, `user-flow` |
| **The three** — state a write step but no `output_dir`-rooted location | 3 | `creative-direction`, `information-architecture`, `design-principles` |
| **The new writer** — states no write step, but its artifact has a named cross-pack consumer | 1 | `design-system` |
| **The enricher** — writes into an artifact another skill owns | 1 | `interaction-design` |
| **The seven** — state no write step and have no downstream consumer | 7 | `analytical-design`, `conversion-design`, `design-review`, `documentation-design`, `informational-design`, `marketplace-design`, `workspace-design` |
| **Reader-only** | 1 | `experience-status` |

`design-review` also reads the `design-principles` artifact by a fixed path, so it
appears in **the seven** as a non-writer and separately owes a read repair.
**The four writes** this spec addresses are the three plus the new writer.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| User-facing promise | Applicable — seven guide steps promise a file that never arrives | `guides/experience-design/how-to/` | Guide author | Each of the nineteen steps states what its skill does | The guide-agreement test passes and `tools/lint-guidebook-steps.py` exits 0 |
| Current product truth | Applicable — three registries name folders no skill writes | `packs/experience-design/DESIGN.md`, `pack.toml` subdirectory comment, `experience-status`'s folder-naming surfaces | Pack maintainer | No registry names a folder no skill declares | The registry-agreement test passes |
| Interface compatibility | Applicable — the shared containment module is the artifact the module criteria quantify over | a byte-identical copy in each of the four writes' `references/containment.md` | Pack maintainer | The module states every control its criteria require and every copy matches | The module exists and is byte-identical in all four before any skill cites it |
| Interface compatibility | Applicable — four declarations must satisfy the layout rule | each write's `references/agentbundle-layout.md` | Pack maintainer | `tests/conformance/test_pack_layout_declared_section.py` passes | Every layout reference states the pack's declared pair |
| Decision rationale | Applicable — `direction/` is a new folder name | `docs/adr/` plus a reproducible dataset beside it | ADR author | The dataset carries the queries, sampling frame and inclusion rule | ADR accepted and its dataset reproduces the sample |
| Operations | Applicable — the guide-agreement test is repository-level | `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py` | Maintainer | The test named as a step with a disposition | `tools/lint-ci-parity.py` exits 0 |
| Release history | Applicable — one pack bumps | `docs/product/changelog.md` | Release author | A released entry for `experience-design`, topmost for that artifact | Topmost entry names its new `pack.toml` version |
| Reusable learning | Applicable | `project-knowledge` seam | Work-loop | Receipt or `project-knowledge unavailable` | Recorded at the terminal gate |

## Boundaries

### Always do

- Write the source-aware approval of `output_dir` into each skill that resolves
  one, as skill text rather than as guidance to the implementer: an
  `output_dir` is approved only when its realpath is an admissible destination,
  and every later prefix check binds to that approved value.
- Re-canonicalize the final target, or its parent when the target does not exist,
  and re-check it under the approved `output_dir` immediately before the write.
- Check an existing target's `type:` before writing to it, and confirm product
  belonging when `output_dir` came from user-profile configuration.
- Trace every *reader* of a relocated artifact, not only its writer.
- Resolve a documented-guidance-versus-skill conflict in the owning source.

### Ask first

- Adding a write step to any skill that has none. This change corrects the guides
  for those eight; giving them artifacts is a different change.
- Changing `[design] output_dir` away from `docs/design`.
- Editing `packs/experience-design/JOURNEY.md` outside its transcript blocks.

### Never do

- Never add a new top-level directory, module, or dependency. This change is
  confined to `packs/experience-design/`, `guides/experience-design/`,
  `docs/adr/`, `docs/specs/`, `docs/product/`,
  `.github/workflows/build-check.yml`, `tools/lint-ci-parity.py`,
  `tests/roster/` for the repository-level guide-agreement test, and two generated
  surfaces reached only through their own regeneration mechanism:
  `web/src/content/journeys/experience-design.md` via
  `tools/build-site.py --journeys-only`, and `.claude-plugin/marketplace.json`
  via the `composite-marketplace` recipe.
- Never hand-edit a generated file. `web/src/content/journeys/` and
  `.claude-plugin/marketplace.json` are outputs of their own regeneration.
- Never ship a control with only a positive observation. If a negative case
  cannot be staged, that is a blocking condition needing a named owner waiver
  recorded in this spec.
- Never edit a lint, test, or checker to make a failing gate pass.

## Testing Strategy

- **The four writes declare a canonical target, and each carries containment** —
  goal-based check. A test asserts each of the four states the declaration line
  in the literal form the criteria fix, and that the same file references the
  shared containment module. Referencing one module rather than repeating prose
  is what makes the predicate exact: presence-of-paragraph certifies phrasing,
  a named reference does not drift across three copies.
- **Containment actually refuses** — visual / manual QA, paired. An agent
  instruction is not unit-testable and a benign fixture cannot separate a present
  control from an absent one, so each of the four is exercised against an
  inadmissible `output_dir`, a symlinked target, and a non-conforming slug, and
  the refusal recorded. Four skills, one module, so the runs test the module.
- **The guides state what their skills do** — goal-based check over all nineteen
  steps, classifying each against its owning skill's actual behaviour. This test
  reads `guides/` as well as `packs/`, so it is repository-level and belongs in
  the roster suite, which runs on no pull request until it is wired.
- **The registries name only declared folders** — goal-based check comparing every
  folder-naming surface against the declared set.
- **`design-review`'s read survives relocation** — visual / manual QA. Its load is
  a step the skill marks mandatory, so the observable is that the load resolves
  under a non-default `output_dir`.

## Acceptance Criteria

- [ ] `creative-direction` writes its doc to `<output_dir>/direction/<slug>.md`,
      `information-architecture` writes its doc to
      `<output_dir>/screens/<slug>-ia.md`, `design-principles` writes its doc to
      `<output_dir>/principles/<slug>.md`, and `design-system` writes its taxonomy
      to `<output_dir>/tokens/<slug>.md`.
- [ ] `design-system` states a write step that commits the derived taxonomy to
      that path.
- [ ] `design-system` ships a template emitting frontmatter `type: token-taxonomy`
      that names semantic roles and scale relationships symbolically and prints no
      colour literal, dimension, duration, ratio, or easing curve.
- [ ] `tools/lint-experience-agnostic.py` exits 0 over `packs/experience-design/`
      with that template present.
- [ ] Each of the four writes states its target in its own `SKILL.md` on a line of
      the literal form `**Writes:** ` followed by that path in backticks, and
      nothing else on the line.
- [ ] `packs/experience-design/.apm/skills/design-principles/SKILL.md` contains no
      occurrence of the literal `docs/design`.
- [ ] Each of the four writes ships a `references/agentbundle-layout.md`.
- [ ] The shared containment module exists at `references/containment.md` inside
      each of the four writes' skill directory, and every copy is byte-identical.
- [ ] Each of the four writes states a line of the literal form `**Confinement:** ` followed
      by a reference to the shared containment module in backticks.
- [ ] The shared containment module states that an `output_dir` is approved only
      when its realpath is neither **at nor beneath** any reserved tree, that the
      reserved set is stated for the user-profile branch as well as the repository
      one, and that an inadmissible value is refused rather than confirmed. A
      predicate testing directory *identity* admits every descendant, so
      `packs/<pack>/.apm/skills/<skill>` and `~/.claude/skills` would both pass; that a
      repo-root value resolving outside the repository tree takes explicit
      confirmation; that approval precedes the first read or write under the
      directory; that the approved root is recorded with the run on every
      approval path, not only that one; that a
      user-profile value is approved against its own declared absolute root; and
      that every later prefix check binds to the approved value.
- [ ] The shared containment module states that the final target, or its parent
      when the target does not exist, is re-canonicalized and re-checked under the
      approved `output_dir` immediately before the write.
- [ ] The shared containment module states that a `<slug>` is rejected before any
      path is composed unless the whole string matches `^[a-z0-9]+(-[a-z0-9]+)*$`
      and is at most 64 characters, so the refusal happens before a composed path
      can exceed a platform limit mid-write.
- [ ] The shared containment module states that an existing target's `type:` is
      read before writing, that a mismatch **or an absent or unparseable `type:`**
      is surfaced rather than overwritten, and that a blank template is never
      copied over an existing artifact.
- [ ] Each of the four writes emits a declared `type:` in its artifact, so the
      mismatch check has a value to compare against at every destination.
- [ ] The shared containment module states that when `output_dir` came from
      user-profile configuration, product belonging is confirmed before an
      existing target is replaced.
- [ ] The shared containment module states that an existing target carrying a
      **matching** `type:` is surfaced before replacement, not silently
      overwritten. `creative-direction` states an amend branch; `information-architecture`
      and `design-principles` state none, so for those two a second run on the same
      slug writes a freshly generated doc over a possibly hand-amended artifact,
      and the mismatch check cannot see it because the type agrees.
- [ ] The shared containment module states that an existing target read before
      amendment is treated as structured data — only the named fields extracted,
      any directive embedded in its body ignored — so all five controls the
      Assumptions claim are propagated are specified rather than four.
- [ ] The shared containment module states that each missing intermediate
      directory it creates is confined under the approved `output_dir` at the
      component being created, not at a nominal parent that may itself be absent.
- [ ] `creative-direction`'s template emits frontmatter `type: creative-direction`.
- [ ] `information-architecture` declares `type: information-architecture` as the
      marker its artifact emits, so the literal is fixed here rather than invented
      at implementation and joining the pack's discover-by-marker set unreviewed.
- [ ] `guides/experience-design/reference/experience-design.md` states no
      `docs/design/principles` path, since no skill declares one after the
      relocation.
- [ ] `packs/experience-design/.apm/skills/design-review/SKILL.md` resolves the
      `design-principles` artifact through `output_dir`, confirms its canonicalized
      real path under the approved `output_dir`, validates its declared `type:`,
      extracts only the principle entries while ignoring any directive embedded in
      the file, and confirms product belonging when `output_dir` came from
      user-profile configuration.
- [x] *(shipped ahead)* For each of the seven, its `artifact_location` obligation in
      `guides/experience-design/how-to/` reads `**Writes no artifact.**` rather than a
      path, and the step's simulated agent-returns line no longer claims a file was
      written.
- [ ] `interaction-design`'s `**Where it lands:**` line names the per-screen brief
      it enriches rather than denying a write or naming a file of its own.
- [ ] For every step whose declared path this change moves, the step's simulated
      agent-returns line names the same destination its `artifact_location` names,
      or states that nothing was written. `establish-design-intent.md:55` claims a
      write to `docs/design/principles/<slug>.md` and `design-each-screen.md:402`
      to the orphaned `<output_dir>/screens/<slug>.md`; both are published prose
      promising a path no skill will write.
- [ ] Every step's `artifact_location` obligation in
      `guides/experience-design/how-to/` is one of: a path its owning skill
      declares, `**Writes no artifact.**` where the skill states no write step, or
      a path naming the artifact the skill enriches. Quantifying over the
      `**Where it lands:**` label instead would make the second form unreachable,
      because it replaces that label rather than appearing on it.
- [ ] No file under `packs/experience-design/` or `guides/experience-design/` names
      an `aesthetic/` output folder.
- [ ] `web/src/content/journeys/experience-design.md` is byte-equal to the output
      of `python3 tools/build-site.py --journeys-only`.
- [ ] Every `docs/design` literal remaining in `packs/experience-design/JOURNEY.md`
      appears inside a fenced transcript block.
- [ ] Every folder named in `packs/experience-design/DESIGN.md`, in the
      `packs/experience-design/pack.toml` subdirectory comment, and in each
      folder-naming surface of `experience-status/SKILL.md` is one some skill declares.
- [ ] The verification ledger records, for each of the four writes, a refusal observed
      against an inadmissible `output_dir`, a symlinked target, and a
      non-conforming slug; and a successful `design-review` load under a
      non-default `output_dir`.
- [ ] `tools/lint-guidebook-steps.py` exits 0.
- [ ] `python3 -m pytest tests/conformance/test_pack_layout_declared_section.py -q` passes.
- [ ] `.github/workflows/build-check.yml` names a step for the guide-agreement
      test, and `tools/lint-ci-parity.py` exits 0 with that step name carrying a
      disposition.
- [ ] The ADR recording `direction/` cites a dataset, stored beside the ADR,
      carrying the queries, sampling frame, and inclusion rule needed to reproduce
      its sample.
- [ ] `agentbundle catalogue verify --root .` exits 0.
- [ ] `.claude-plugin/marketplace.json` is byte-identical to the output of a fresh
      self-host run.
- [ ] Each of the four writes has an `evals/evals.json` case covering its declared target.
- [ ] The topmost `## [experience-design][<version>] — YYYY-MM-DD` heading in
      `docs/product/changelog.md` names that pack's new `pack.toml` version, at the
      level directly beneath `[Unreleased]`.

## Follow-ons

- `docs/specs/design-handoff-read/` — the frontend read path, reading all three
  artifacts: the aesthetic direction, the per-screen brief, and the token taxonomy.
- `docs/specs/frontend-experience-composition/` — the composition and depth layer.
- Pack maintainer: giving the seven a write step is a capability change this spec
  explicitly declines, on the ground that none has a named downstream consumer.
  If one acquires a consumer, it joins the writes on the same terms
  `design-system` did.
- Pack maintainer: the seven declaring writers were not audited for containment
  depth. `user-flow` confines `output_dir` only and `content-design` states no
  canonicalization, so most of the seven likely owe the shared module this change
  introduces.
- Pack maintainer: two further reads resolve under `output_dir` and are not
  repaired here — `information-architecture` reads six sibling skills' outputs by
  role, and `conversion-design` consumes the `design-principles` artifact. Neither
  states a path today, so neither is broken by this change, but both owe the read
  controls once they get one.
- Pack maintainer: `packs/experience-design/.apm/skills/*/evals/*.json` pin literal
  `docs/design/...` paths.
- Pack maintainer: this repository's `docs/design/direction/` already holds two
  files, one carrying `type: design-system`, so the `type:` check will surface a
  collision against the self-hosting tree.
- Pack maintainer, owner-directed and deferred: flip `[design] output_dir` from
  `docs/design` to `docs/ux`, covering `pack.toml`, every
  `references/agentbundle-layout.md`, `workspace_mcp.py`, the five test fixtures
  carrying the literal, and this repository's own tree.


## Assumptions

- Technical: eight of the nineteen path-publishing guide steps name a skill that
  states no write step at all — `design-system`, whose procedure ends at
  "Serialize portably", and the seven with no output step: `analytical-design`,
  `conversion-design`, `documentation-design`, `informational-design`,
  `marketplace-design`, `workspace-design`, and `design-review`, which only reads.
  `design-principles` is **not** among them: it states a write, to the literal
  `docs/design/principles/<slug>.md`, which is why it sits in the three and why a
  criterion removes that literal
  (source: probe — enumerated every numbered procedure step in each, 2026-09-16;
  `design-principles/SKILL.md:91`)
- Technical: `interaction-design` writes into the per-screen brief `user-flow`
  owns — "Commit the state machine diagram … into the brief's interaction/behavior
  section" — so its `:8` disclaimer means it emits no artifact of its own, not that
  it writes nothing (source: `interaction-design/SKILL.md:56`, `:8`)
- Technical: the guide path for `interaction-design` collides with nothing. It is
  `screens/<slug>.md`; `user-flow` owns `screens/<slug>-flow.md` and
  `screens/<slug>/<screen>.md`. The defect is that the path is orphaned — no skill
  writes it and `experience-status` does not scan it
  (source: `design-each-screen.md:423`, `derive-the-screen-flow.md:287`)
- Technical: the guides' path lines for the eight were authored ahead of the
  skills; their own `rung: authored` annotations record it
  (source: read of those annotations)
- Technical: `map-the-customer-journey.md:287` already states
  `**Writes no artifact.**` for `experience-status` while keeping a
  `**What it looks like:**` block, so a rule requiring both labels to carry the
  form would fail on a conforming step (source: read of that step)
- Technical: "within the repository tree" admits `.github/workflows`,
  `.claude/skills` and `packs/` as an `output_dir`, so an in-tree test is not an
  admissibility test (source: probe — resolved each against the repository root,
  all in-tree)
- Technical: `creative-direction/SKILL.md:51` copies a blank template into the
  repository while `:40` instructs amendment when a doc exists, with no step that
  reads the target's `type:` to distinguish them; `copy-direction/SKILL.md:55`
  names and forbids that shape (source: read of all three)
- Technical: `packs/AGENTS.md:56-58` requires canonicalize-then-prefix-check,
  data-not-instruction extraction, and a current-project belonging check for a
  user-level config path; root `AGENTS.md` places trust-boundary validation in the
  non-waivable class (source: read of both files)
- Technical: `copy-direction` carries five controls — source-aware approval,
  final-target re-canonicalization, `type:` validation, user-profile belonging, and
  extract-as-data. This change propagates all five into one shared module rather
  than a subset into three copies (source: read of its steps 1, 3 and 6)
- Technical: the seven declaring writers phrase their target seven different ways,
  and `copy-direction`'s first `<output_dir>` match is a *read*, so no predicate
  over existing prose distinguishes a write from a read. The declaration form is
  therefore fixed literally by the criteria (source: read of all seven)
- Technical: a pack test may not read above its owning pack, so a test reading
  `guides/` belongs in the roster suite, which runs on no pull request unless
  named as a `build-check.yml` step with a matching `lint-ci-parity.py` disposition
  (source: `tools/lint-pack-test-boundary.py`; `tests/AGENTS.md`; `tools/lint-ci-parity.py:360-372`)
- Technical: `tools/check-guide-index.py` asserts only that every active pack has a
  direct link in `guides/README.md`; it cannot observe page reachability
  (source: read of that tool)
- Technical: `packs/AGENTS.md:45-47` reserves a minor bump for new primitives. This
  change adds no skill, command or agent, so it takes a patch
  (source: read of that rule)
- Technical: `.claude-plugin/marketplace.json` is generated by the
  `composite-marketplace` recipe from each pack's `plugin.json`
  (source: `packages/agentbundle/agentbundle/build/recipes/self-host.toml:51-54`)
- Technical: a skill installs standalone, so each needs its own `references/` copy
  (source: probe — `agentbundle install --help` lists `--skill NAME`)
- Technical: `packs/` is non-release-impacting, so no `agentbundle` release is owed
  (source: `tools/repo/check_release_impact.py:44`)
- Technical: inside a design tree, `direction/`, `creative-direction/` and
  `visual-direction/` each return zero on GitHub code search, so no external
  convention favours one; `docs/design/direction/` is this repository's own live
  choice (source: GitHub code-search API, sampled 2026-09-16)
- Technical: this repository's spec corpus holds 467 specs and 7,428 criteria, mean
  15.9, so this spec's count sits near the median
  (source: probe — `grep -c "^- \[[ xX]\]" docs/specs/*/spec.md`, 2026-09-16)
- Technical: `packs/experience-design/JOURNEY.md:242` marks stage 5
  `**State:** confirmed-write` although the only actor that stage names, the
  `experience-reviewer` agent, is read-only by construction
  (`packs/experience-design/.apm/agents/experience-reviewer.md:154`). This was
  raised as a defect during review and is **not** one. The catalogue already uses
  the token this way for an independent-review stage: `frontend-engineering`'s
  JOURNEY stage 6, "Get an independent frontend review", carries the same
  `confirmed-write` and runs `frontend-reviewer`, which is read-only in the same
  way. Both stages describe a net effect — XD's `**Output:**` is "a review-clean
  design set", FE's `**You decide:**` is "merge after clean review" — rather than
  the reviewer's own file access. A reading strict enough to condemn one condemns
  both, and nothing has flagged the frontend stage.
  The imprecision is in the shared vocabulary, not either journey:
  `docs/guides/how-to/ui-primitives.md:56` glosses `confirmed-write` as "Human
  confirmed; agent is writing", which does not describe how review stages use it.
  Correcting that gloss would touch every pack and is out of this spec's scope.
  A related review claim — that the stage runs `design-review` — is false: that
  skill appears in this journey only as a frontmatter roster entry at `:78`
  (source: read of both journeys, both agent definitions, and a sweep of every
  `confirmed-write` stage across `packs/*/JOURNEY.md`, 2026-09-16)
- Process: every non-cosmetic pack-content change bumps matching versions and
  updates that pack's eval harness (source: `packs/AGENTS.md`)
- Process: each phase ships its guide (source: `docs/CONVENTIONS.md:1130`)
- Process: a changelog entry is owed in the PR that bumps a released artifact, and
  a released heading sits directly beneath `[Unreleased]`
  (source: `docs/CONVENTIONS.md:717-726`)
- Product: the guides are corrected to match the skills, except that
  `design-system` gains a write step because its taxonomy has a named cross-pack
  consumer — the contract's `Design System Reference` field at pilot tier, and the
  frontend pack's per-session token fabrication
  (source: user confirmation 2026-09-16; `digital-experience-contract.md:116-118`;
  `frontend-engineering/SKILL.md:104-108`)
- Product: `direction/` and `tokens/` are the folder defaults; `aesthetic/` retires
  (source: user confirmation 2026-09-16)

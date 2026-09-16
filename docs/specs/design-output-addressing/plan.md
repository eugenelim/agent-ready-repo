# Plan: design-output-addressing

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (export boundary, version bump rule,
  § Security and authoring rules) and `docs/CONVENTIONS.md` § Phase-slice
  planning. Analogous implementation: `copy-direction/SKILL.md` steps 1, 3 and 6 —
  the only place in the pack that approves a resolved `output_dir`,
  re-canonicalizes a final target before writing, validates an existing target's
  `type:`, confirms product belonging for user-profile config, and extracts a
  loaded artifact as data. Those are the five controls this change moves into one
  module. Construction path:
  `tests/conformance/test_pack_layout_declared_section.py` for the declared pair,
  `tools/lint-ci-parity.py:360-372` for the disposition shape a new
  `build-check.yml` step must match. Named deviation: none — every control is
  already in `copy-direction`, so this propagates an in-repo pattern.

> **Plan contract:** implementation strategy. It may change substantively only
> while Status is `Drafting`. Execution observations belong in
> `notes/verification-ledger.md`.

## Approach

Thirteen tasks. Each task's subject is taken from the acceptance criteria it
discharges, not from a grouping of skills — that grouping is what drifted when
the spec narrowed twice, and re-deriving from the criteria is why this plan
replaces its predecessor rather than patching it.

Dependency shape, stated from the `Depends on:` fields rather than described
loosely: **T1 → T2** is the only hard serialisation in the skill work, because
the four writes reference a module that must exist first. T2 then forks three
ways — **T3, T4 and T5** touch different skills and are mutually independent.
**T6** depends on nothing. **T7** depends on T4. **T8** depends on T2, T5 and T7,
because a registry can only be checked against declarations that exist.
**T9** depends on T6, T7 and T8, since its three tests span guides, journeys and
registries. **T10** depends on T9. **T11** depends on T2. **T12** depends on
nothing. **T13** depends on everything.

Review shape is **MIXED**. T2 is uniform across four skills; T1 and T11 are the
deep tasks, because T1 authors a trust-boundary control and T11 is the only place
its behaviour is observed.

## Constraints

- The module is one body in four places. A skill installs standalone, so it
  cannot reach a sibling's `references/`; "shared" means byte-identical copies,
  and a criterion pins that rather than the plan asserting it.
- The declaration form is introduced by this change. The seven already-declaring
  writers phrase their target seven ways and `copy-direction`'s first
  `<output_dir>` match is a *read*, so no predicate over existing prose separates
  a write from a read.
- A pack test may not read above its owning pack, so the guide-agreement test is
  repository-level and runs on no pull request until T10 wires it.
- `tools/lint-experience-agnostic.py` rejects nine named token classes — not
  "every literal". A bare integer and a percentage pass; colour literals,
  digit-plus-unit dimensions, `N:1` ratios and named easing curves do not.

## Construction tests

Three test files, authored in T9 **after** the work they check and proven red by
mutating the artifact. Authoring them earlier cannot work: each quantifies over
state that T2-T8 create, so a test introduced before its subject exists can never
go green at the task that introduces it.

- **Declaration and containment** (pack suite). Subject: the four writes named at
  `spec.md`'s closed set — `creative-direction`, `information-architecture`,
  `design-principles`, `design-system`. Per skill, assert a `**Writes:**` line
  naming its declared target, a `**Confinement:**` line referencing
  `references/containment.md`, that the module copy is present and byte-identical
  to the others, and that the skill emits a declared `type:`. The seven
  already-declaring writers are out of subject: the spec defers their containment
  audit and none uses a `**Writes:**` line, so including them would red the test
  against work no task performs.
- **Guide agreement** (roster suite). For each step in
  `guides/experience-design/how-to/`, assert its `artifact_location` obligation —
  the label-agnostic name the guidebook lint uses — is a path its owning skill
  declares, `**Writes no artifact.**` where the skill states no write step, or a
  path naming the artifact the skill enriches.
- **Registry agreement** (pack suite). Assert the folder set named by `DESIGN.md`,
  the `pack.toml` subdirectory comment, and each folder-naming surface of
  `experience-status/SKILL.md` equals the set the skills declare.

## Durable-output map

| Durable output | Tasks | Evidence |
| --- | --- | --- |
| User-facing promise | T5, T6, T7, T12 | Guide-agreement test; `lint-guidebook-steps.py` |
| Current product truth | T8 | Registry-agreement test |
| Interface compatibility (module) | T1 | Module present and byte-identical in all four |
| Interface compatibility (layout) | T2 | Layout conformance test |
| Decision rationale | T12 | ADR accepted; its dataset reproduces the sample |
| Operations | T10 | `tools/lint-ci-parity.py` exits 0 with the step named |
| Release history | T13 | Topmost `experience-design` entry names the new version |
| Reusable learning | T13 | `project-knowledge` receipt or recorded unavailability |

## Design (LLD)

### Design decisions

**Approval precedes confinement, and admissibility is containment.** Without
approving the resolved `output_dir`, a prefix check confirms only that a path sits
under a root the adopter's config named — and a hostile `agentbundle-layout.toml`
in a cloned repository names any absolute root. Testing whether that root *is* a
reserved directory admits every descendant, so the predicate is at-or-beneath and
the reserved set is stated for the user-profile branch too.

**One module, four copies, equality pinned.** The controls live in one body so a
later weakening is one edit rather than four, and so the per-skill test asserts a
reference rather than a paragraph. Standalone install means the body ships four
times, so copy-equality is a criterion; without it, "shared" is an assertion the
tree does not support.

**`design-system` is a new capability, not a relocation.** The other three writes
already write and only lack a location. `design-system` stops at "record the
taxonomy" with no file, and gains a write because the shared contract's
`Design System Reference` field asks which token taxonomy a surface uses and the
frontend pack fabricates tokens every session for want of one.

**`interaction-design` names what it enriches; it does not deny a write.** It
writes into the brief `user-flow` owns. The guidebook step contract admits only a
backticked path or `**Writes no artifact.**`, so the path form is the one that is
both admissible and true — which also introduces `<screen>` as a segment the page
must resolve.

**Readers are repaired with writers.** Relocating `design-principles` without
repointing `design-review`'s load, and without the two promises the reference page
makes, leaves a mandatory step and published prose pointing at a path that
resolves only when `output_dir` happens to be the default.

### Interfaces & contracts

Each write resolves `[design] output_dir` by name and states its target relative
to it: `direction/<slug>.md`, `screens/<slug>-ia.md`, `principles/<slug>.md`, and
`tokens/<slug>.md`. The frontend read of these artifacts is a separate spec.

### Failure, edge cases & resilience

| Condition | Result |
| --- | --- |
| Repo-root `output_dir` resolving outside the repository tree | explicit confirmation before use, recorded with the run |
| Resolved `output_dir` at or beneath a reserved tree, either branch | refused, not confirmed |
| Target's parent absent | confinement re-established at each intermediate component as it is created |
| Slug non-conforming or over 64 characters | refused before any path is composed |
| Existing target with a foreign, absent or unparseable `type:` | surfaced as a collision; never overwritten, never a blank template copied over it |
| User-profile `output_dir`, target from another product | belonging confirmed before replacement; mismatch surfaced |
| Existing target read before amendment | treated as structured data; embedded directives ignored |

## Tasks

### T1: Author the shared containment module

**Depends on:** none

**Tests:**
- Goal-based: `references/containment.md` exists in each of the four writes' skill
  directory and all four copies are byte-identical.
- Goal-based: the module states every one of the seven module criteria — the
  at-or-beneath approval with its reserved set for both the repository and
  user-profile branches, its ordering before the first read or write under the
  directory, and the binding of every later resolution to the approved value;
  final-target re-canonicalization; confinement re-established at each missing
  intermediate directory as it is created; the slug class and its 64-character
  bound with refusal before path composition; the `type:` check treating absent or
  unparseable as a collision and forbidding a blank template over an existing
  artifact; user-profile product belonging before replacement; and extract-as-data
  for an existing target read before amending.

**Approach:**
- Author the body once, then write the other three copies from it so equality is
  produced rather than hand-matched.
- Take the content from `copy-direction`'s five controls in full. Its step 1 fixes
  the ordering and binds every later lookup to the validated value; reproducing
  the branch without the binding lets a skill re-resolve from configuration at its
  write step.

**Done when:** the module is present and byte-identical in all four skills and
states all seven module criteria.

### T2: Declare all four writes

**Depends on:** T1

**Tests:**
- Goal-based: each of `creative-direction`, `information-architecture`,
  `design-principles` and `design-system` states its target in its own `SKILL.md`
  on a `**Writes:**` line carrying that path in backticks and nothing else.
- Goal-based: each states a `**Confinement:**` line referencing
  `references/containment.md`.
- Goal-based: each ships a `references/agentbundle-layout.md`, and
  `python3 -m pytest tests/conformance/test_pack_layout_declared_section.py -q` passes.

**Approach:**
- Targets come from the acceptance criteria, which are the canonical statement —
  not from the guides, which name `aesthetic/` for two of them and which T7 corrects.
- All four, including `information-architecture`, which the criteria name among the
  four writes and which the previous plan left without an implementer.

**Done when:** the conformance test passes and all four carry both lines and a
layout reference.

### T3: `design-system`'s write step and token-taxonomy template

**Depends on:** T2

**Tests:**
- Goal-based: `design-system/SKILL.md` states a write step committing the derived
  taxonomy to its declared target.
- Goal-based: its template emits frontmatter `type: token-taxonomy` and names
  semantic roles and scale relationships symbolically.
- Goal-based: `tools/lint-experience-agnostic.py` exits 0 over
  `packs/experience-design/`.

**Approach:**
- Run the agnosticism lint before anything else in this task. The skill already
  states it "does not implement token values" and leaves the numbers to the
  reader, so a value-free artifact is its natural shape — but the lint is the
  binding check, not that reasoning.

**Done when:** the agnosticism lint exits 0 with the template present and the
skill states its write step.

### T4: `creative-direction`'s template frontmatter

**Depends on:** T2

**Tests:**
- Goal-based: the template emits frontmatter `type: creative-direction`.

**Approach:**
- The template today opens straight into an H1 with no frontmatter, while three
  shipped reference documents already claim it emits `type: creative-direction`.
  Add the frontmatter those documents assume, plus a `surface:` field so the
  amend-versus-new branch has something to compare.

**Done when:** the template carries the declared `type:`.

### T5: Repoint `design-principles`'s write and every reader of it

**Depends on:** T2

**Tests:**
- Goal-based: `design-principles/SKILL.md` contains no occurrence of the literal
  `docs/design`.
- Goal-based: `design-review/SKILL.md` resolves that artifact through `output_dir`,
  confirms its canonicalized real path under the approved `output_dir`, validates
  its declared `type:`, extracts only the principle entries while ignoring any
  embedded directive, and confirms product belonging for user-profile config.
- Goal-based: `guides/experience-design/reference/experience-design.md` states no
  `docs/design/principles` path.

**Approach:**
- The reader repairs belong in this task, not a later one: `design-review`'s load
  sits in a step the skill marks mandatory, and the reference page makes two
  promises about the old path. Relocating the writer alone leaves all three
  resolving only by luck.
- Scope the literal check to the files this task owns. A repository-wide ban on
  `docs/design` is not satisfiable — the pack's declared default is that literal,
  every `references/agentbundle-layout.md` must carry it, and the reference page
  legitimately names it as the pack default.

**Done when:** all three checks pass.

### T6: Name the artifact `interaction-design` enriches

**Depends on:** none

**Tests:**
- Goal-based: the `interaction-design` step's `artifact_location` names
  `<output_dir>/screens/<slug>/<screen>.md`, the brief `user-flow` writes, and does
  not deny a write.
- Goal-based: `design-each-screen.md` resolves `<screen>` in the segment line under
  its table, which naming that path newly requires.
- Goal-based: `tools/lint-guidebook-steps.py` exits 0.

**Approach:**
- The step contract admits only a backticked path or `**Writes no artifact.**`, and
  the skill does write — into another skill's file. The path form is the only one
  that is both admissible and true.
- Re-excerpt the preview from the brief template that defines that section and rung
  it to that template's repository-relative path; a higher rung than `authored`
  exists once the block names a template-backed artifact.

**Done when:** the step names the brief, `<screen>` is resolved, and the guidebook
lint exits 0.

### T7: Retire `aesthetic/`

**Depends on:** T4

**Tests:**
- Goal-based: no file under `packs/experience-design/` or
  `guides/experience-design/` names an `aesthetic/` output folder.
- Goal-based: every `docs/design` literal left in
  `packs/experience-design/JOURNEY.md` sits inside a fenced transcript block.
- Goal-based: `web/src/content/journeys/experience-design.md` is byte-equal to a
  fresh `python3 tools/build-site.py --journeys-only` run.
- Goal-based: the three journey lints exit 0.

**Approach:**
- Update the two `**Where it lands:**` lines in `establish-design-intent.md` and
  rewrite their rung annotations, whose second halves become false once T2 lands.
- Fix `establish-design-intent.md:76`, which hardcodes `docs/design/` where every
  sibling line uses `<output_dir>`.
- Edit the transcript lines in `JOURNEY.md`, including the `screen-flows/` one that
  names a folder the pack does not ship, then regenerate the web copy here rather
  than at release — no lint compares the two.

**Done when:** all four checks pass.

### T8: Reconcile the registries

**Depends on:** T2, T5, T7

**Tests:**
- Goal-based: every folder named in `DESIGN.md`, in the `pack.toml` subdirectory
  comment, and in each folder-naming surface of `experience-status/SKILL.md` is one
  some skill declares.

**Approach:**
- `DESIGN.md`: replace the `aesthetic/` row with `direction/` and `tokens/`, correct
  `screen-flows/` to the shipped `screens/`, move `design-principles` to
  `principles/`, add the missing `copy/` row, correct the `screens/` row that names
  `interaction-design` as a writer of its own file, and the `output_dir` comment that
  lists `briefs/`.
- `pack.toml`: make the subdirectory comment point at the registry rather than list
  four folders that are now nine.
- `experience-status`: extend all three folder-naming surfaces — the scan table, the
  readiness-gate table, and the report template — not only the first.

**Done when:** every folder-naming surface names only declared folders.

### T9: Author the three construction tests

**Depends on:** T6, T7, T8

**Tests:**
- TDD by mutation: the declaration test red when one write's `**Confinement:**`
  line is removed, and again when one module copy is altered so equality fails.
- TDD by mutation: the guide-agreement test red when the orphaned
  `screens/<slug>.md` path is restored to the `interaction-design` step.
- TDD by mutation: the registry test red when one stale `DESIGN.md` row is restored.

**Approach:**
- The declaration and registry tests are pack-confined. The guide-agreement test
  reads `guides/` and goes to `tests/roster/`.
- Authoring after the work is deliberate: all three quantify over state T2-T8
  create. Red by mutation is a stronger demonstration than the pre-change state.

**Done when:** all three are green against the tree and red against each named
mutation, recorded in the ledger.

### T10: Wire the roster test into CI

**Depends on:** T9

**Tests:**
- Goal-based: `.github/workflows/build-check.yml` names a step for the
  guide-agreement test and `tools/lint-ci-parity.py` exits 0.

**Approach:**
- Add the step and a matching `STEP_DISPOSITION` entry of the
  `LOCAL("test-after-build-check")` shape. Without both, the test runs under
  `pytest tests/` and on no pull request — green by never executing, which is how
  the guide claims survived in the first place.

**Done when:** the parity lint exits 0 with the step name carrying a disposition.

### T11: Observe the controls refusing

**Depends on:** T2

**Tests:**
- Visual / manual QA, paired per control: for each of the four writes, a benign run
  and then a run that must make the control fire — an `output_dir` at or beneath a
  reserved tree, a symlinked target, a non-conforming slug, an existing target with
  a foreign `type:`, a blank-template-over-artifact attempt, and a foreign-product
  target under user-profile config.
- Visual / manual QA: a `design-review` load under a non-default `output_dir`.

**Approach:**
- Stage fixtures with an absolute `output_dir` pointed at a temporary tree, which is
  what makes the symlink, reserved-tree and foreign-product cases stageable rather
  than hypothetical.
- Record paths relative to `output_dir` plus the configuration source. A staged
  user-profile case surfaces an absolute home path and the spec's `Never do` forbids
  committing it.
- An unstageable case is a blocking condition needing a named owner waiver recorded
  in the spec, not an unverified pass.

**Done when:** every control has both halves recorded in the ledger, or a waiver
recorded in the spec with its owner.

### T12: ADR and its dataset

**Depends on:** none

**Tests:**
- Goal-based: re-running the dataset's recorded queries reproduces its counts.

**Approach:**
- Record the queries, sampling frame and inclusion rule beside the ADR, then write
  the ADR citing it. A stored table of counts satisfies a path check without being
  reproducible, which is the failure this avoids.

**Done when:** the dataset's queries reproduce its counts and the ADR cites it.

### T13: Release surface

**Depends on:** T1 through T12

**Tests:**
- Goal-based: `agentbundle catalogue verify --root .` exits 0, which owns the
  `pack.toml` / `plugin.json` version agreement.
- Goal-based: `.claude-plugin/marketplace.json` is byte-identical to a fresh
  self-host run.
- Goal-based: each of the four writes has an `evals/evals.json` case covering its
  declared target.
- Goal-based: the topmost `experience-design` changelog heading names its new version.

**Approach:**
- Bump `experience-design` **patch** in `pack.toml` and `plugin.json`:
  `packs/AGENTS.md` reserves minor for new primitives and this change adds no skill,
  command or agent. Regenerate `marketplace.json` by self-host rather than editing it.
- Route learnings through the `project-knowledge` seam.

**Done when:** the four checks pass and `git status` is clean.

## Rollout

No runtime component. Adopters see declared paths on upgrade; nothing moves an
existing file, because the newly addressed artifacts had no address to move from.
Two exceptions are recorded as follow-ons rather than claimed clean: this
repository's own `docs/design/direction/` already holds two files, one with a
`type:` the collision rule will surface; and an adopter who followed the guide by
hand and used `aesthetic/` keeps files nothing will look for.

## Risks

- **The token-taxonomy template trips the agnosticism lint.** Mitigated by running
  the lint first in T3 and authoring symbolically.
- **The declaration form does not fit one of the four.** Then the form is wrong, not
  the skill; T2 surfaces it rather than special-casing.
- **A refusal case cannot be staged in T11.** A blocking condition needing a named
  owner waiver, per the spec's `Never do` — not an unverified pass.
- **The module's four copies drift during authoring.** Mitigated by writing three
  from the first and pinning equality in a criterion rather than in prose.

## Changelog

- 2026-09-16 — Rewritten from the acceptance criteria rather than patched. Its
  predecessor was aligned three times against a spec that narrowed twice, and each
  alignment dropped or contradicted something: a review round found ten of fifteen
  findings originating in the previous round's own repairs, one of the four writes
  left without an implementing task, and two repairs reported but absent from the
  file. Every task subject here is derived from the criteria it discharges, and the
  dependency shape is stated from the `Depends on:` fields rather than described.

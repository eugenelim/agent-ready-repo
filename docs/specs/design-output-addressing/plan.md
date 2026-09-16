# Plan: design-output-addressing

- **Spec:** [`spec.md`](spec.md)
- **Status:** Drafting <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/AGENTS.md` (export boundary, version bump rule,
  § Security and authoring rules) and `docs/CONVENTIONS.md` § Phase-slice
  planning. Analogous implementation: `copy-direction/SKILL.md` steps 1 and 6 —
  the only skill in the pack that both approves the resolved `output_dir` and
  re-canonicalizes the final target before writing; `tone-of-voice/SKILL.md:58`
  for the singleton variant. Construction path:
  `tests/conformance/test_pack_layout_declared_section.py` for the declared pair,
  and `tools/lint-ci-parity.py:360-372` for the disposition shape a new
  `build-check.yml` step must match. Named deviation: none — every control this
  change adds already exists in `copy-direction`, so this is propagation of an
  in-repo pattern rather than new design.

> **Plan contract:** implementation strategy. It may change substantively only
> while Status is `Drafting`. Execution observations belong in
> `notes/verification-ledger.md`.

## Approach

Ten tasks. The shape is a chain with one branch: T7 through T9 touch registries,
journeys and governance and depend only on the declarations landing, so they can
proceed alongside each other once T4 closes; everything rejoins at T10.

The tests are authored **after** the work they check and proven red by mutating
the artifact, not by the pre-change state. That is deliberate: a test introduced
before eleven declarations exist cannot go green at the task that introduces it,
which is the defect that made two earlier drafts unclosable.

Review shape is **MIXED**. T2 is mechanically uniform across ten skills and
carries a re-run check; T4 and T5 are the tasks that need reading.

## Constraints

- The declaration form is introduced by this change, not inferred from the tree.
  The seven declaring writers phrase their target seven different ways, so any
  predicate matching all seven also matches a read reference — and `design-review`
  will carry exactly such a read reference after T3.
- The guide-agreement test reads `guides/` as well as `packs/`, so it cannot live
  in the pack suite: `tools/lint-pack-test-boundary.py` fails a pack test whose
  source resolves above its owning pack. It goes to the roster suite, and a roster
  test runs on no pull request until T6 wires it.
- `tools/lint-experience-agnostic.py` rejects nine named token classes, not "every
  literal" — a bare integer or a percentage passes. The token-taxonomy template
  must avoid colour literals, digit-plus-unit dimensions, `N:1` ratios and named
  easing curves specifically.

## Construction tests

Two test files. The first is pack-confined; the second is not, which is what
obliges T6.

- **Per-skill declaration and containment** (pack suite). For each of the eleven
  skills the spec names, assert its `SKILL.md` states a write target on a line
  matching the canonical form, and that the same file states the final-target
  re-canonicalization step. One parse, two assertions, failing closed on a skill
  that declares a target without containment.
- **Guide agreement** (roster suite). For each step in
  `guides/experience-design/how-to/`, assert both the `**Where it lands:**` and
  `**What it looks like:**` labels read `**Writes no artifact.**` exactly when the
  owning `SKILL.md` disclaims a file-per-slug artifact, and otherwise name a path
  that `SKILL.md` declares. This is the check that would have caught the
  `interaction-design` claim.
- **Registry agreement** (pack suite). Compare the folder set named by `DESIGN.md`,
  the `pack.toml` comment, and `experience-status`'s scan table against the
  declared set; assert all four equal.

## Durable-output map

| Durable output | Tasks | Evidence |
| --- | --- | --- |
| User-facing promise | T1, T5, T9 | Guide-agreement test; `lint-guidebook-steps.py` |
| Current product truth | T8 | Registry-agreement test |
| Interface compatibility | T2, T3, T4 | Layout conformance test; declaration test |
| Decision rationale | T9 | ADR accepted; dataset reproduces the sample |
| Operations | T6 | `tools/lint-ci-parity.py` exits 0 with the step named |
| Release history | T10 | Topmost `experience-design` entry names the new version |
| Reusable learning | T10 | `project-knowledge` receipt or recorded unavailability |

## Design (LLD)

### Design decisions

**Approval precedes confinement.** `copy-direction` step 1 approves the resolved
`output_dir` before anything is read under it — a repo-root value must stay in the
repository tree or take explicit confirmation. Without that step a hostile
`agentbundle-layout.toml` in a cloned repository names any absolute root and every
prefix check passes against it. The two controls are one control in two parts.

**Containment is propagated from `copy-direction`, the deepest in-repo pattern.**
The pack carries three depths: `experience-status` stops at `..`-rejection,
`user-flow` confines `output_dir` only, and `copy-direction` re-canonicalizes the
final target and checks provenance. Copying the nearest neighbour rather than the
deepest would have spread the weakest pattern to ten more skills.

**The subject is the skills this change edits.** The seven declaring writers
probably owe the same containment — `user-flow` confines only the root — but
auditing them is separate work with its own risk, and quantifying a criterion over
skills no task touches is how an obligation ships with no implementer.

**The guide is corrected, not implemented.** `interaction-design` disclaims a
file-per-slug artifact; the guide assigns it one, at a path `user-flow` owns. The
skill is the owning source, and the guide-agreement test stops the class recurring.

**`design-review` is two fixes, not one.** It is a silent writer and a hardcoded
reader. Relocating the artifact it reads without repointing the read leaves a
step the skill marks mandatory pointing at a path that resolves only by luck.

### Interfaces & contracts

Each declaration resolves `[design] output_dir` by name and states its target
relative to it. `creative-direction` takes `direction/<slug>.md` and
`design-system` takes `tokens/<slug>.md`, both slug-keyed under the pack's
existing kind-first grammar. The frontend read of these artifacts is a separate
spec; this one only gives them addresses.

### Failure, edge cases & resilience

- `output_dir` resolving outside the repository tree from repo-root config:
  explicit confirmation before use, per `copy-direction`.
- A target whose parent does not exist: canonicalize the parent and prefix-check
  that, since the leaf cannot be resolved before creation.
- A slug carrying a separator: refused by the stated character class before any
  path is composed.
- An existing target with a foreign `type:`: out of scope here and recorded as a
  follow-on, because the collision rule belongs with the read path that relies on it.

## Tasks

### T1: Correct the guide claim against its owning skill

**Depends on:** none

**Tests:**
- Goal-based: `guides/experience-design/how-to/design-each-screen.md` carries
  `**Writes no artifact.**` for both the `**Where it lands:**` and
  `**What it looks like:**` labels of the `interaction-design` step, and names no
  path for it.
- Goal-based: `tools/lint-guidebook-steps.py` exits 0, which admits that form for
  both labels independently.

**Approach:**
- Convert both labels, not only the path line: the step contract admits the
  no-artifact form for the preview too, and leaving the preview in place would
  declare that the skill writes nothing while still showing a file outline.
- Record the conflict and its resolution, the skill being the owning source.

**Done when:** both labels read the no-artifact form and the guidebook lint exits 0.

### T2: Declare the ten silent writers

**Depends on:** T1

**Tests:**
- Goal-based: each of the ten states its target on a line matching the canonical
  form and states the re-canonicalization step.
- Goal-based: the layout conformance test passes with ten new references.
- Re-run check: the ten edits are mechanically uniform, so regenerating them from
  the same source produces a zero diff.

**Approach:**
- Introduce the canonical declaration form and use it for all ten.
- Take each path from the guides as corrected by T1.
- Carry `copy-direction`'s two-part control on each: approve the resolved
  `output_dir` source-aware, then re-canonicalize the final target or its parent
  immediately before writing.

**Done when:** the conformance test passes, each of the ten carries both the form
and the containment step, and the re-run produces no diff.

### T3: Repoint `design-principles`'s write and `design-review`'s read

**Depends on:** T2

**Tests:**
- Goal-based: `design-principles/SKILL.md` contains no `docs/design/principles`.
- Goal-based: `design-review/SKILL.md` resolves that artifact through `output_dir`
  and states the canonicalized-real-path check before loading it.

**Approach:**
- Replace the literal write path with `output_dir` resolution.
- Repoint the reader in the same task. The load sits in a step the skill marks
  mandatory, so a relocated writer without a repointed reader silently misses for
  any adopter on a non-default directory.

**Done when:** neither file names the literal and the read carries its check.

### T4: Give `creative-direction` and `design-system` addresses

**Depends on:** T3

**Tests:**
- Goal-based: `tools/lint-experience-agnostic.py` exits 0 — the binding check on
  the new template.
- Goal-based: each template's frontmatter carries its declared `type:` value.
- Goal-based: both skills state the canonical form and the containment step.

**Approach:**
- `creative-direction` to `direction/<slug>.md`; `design-system` to
  `tokens/<slug>.md`, both with the stated slug class.
- Add `type: creative-direction` and a `surface:` field to the existing template,
  which today opens straight into an H1 with no frontmatter.
- Author the token-taxonomy template describing roles and scale relationships
  symbolically. Run the agnosticism lint first, before any other work in this task.

**Done when:** the agnosticism lint exits 0 and both templates carry their `type:`.

### T5: Author the declaration and guide-agreement tests

**Depends on:** T4

**Tests:**
- TDD by mutation: the declaration test proven red by removing the containment
  step from one skill, and separately by rewriting one target off the canonical
  form. Green against the real tree.
- TDD by mutation: the guide-agreement test proven red by restoring the
  `interaction-design` path line T1 removed. Green against the real tree.

**Approach:**
- The declaration test is pack-confined. The guide-agreement test reads `guides/`
  and goes to `tests/roster/`.
- Authoring after the work is deliberate: both tests quantify over eleven
  declarations, so neither can go green at a task that precedes them. Red is
  demonstrated by mutation, which is a stronger demonstration than the pre-change
  state anyway.

**Done when:** both tests are green against the real tree and red against each
named mutation, recorded in the ledger.

### T6: Wire the roster test into CI

**Depends on:** T5

**Tests:**
- Goal-based: `.github/workflows/build-check.yml` names a step for the
  guide-agreement test, and `tools/lint-ci-parity.py` exits 0.

**Approach:**
- Add the step and a matching `STEP_DISPOSITION` entry of the
  `LOCAL("test-after-build-check")` shape. Without both, the test runs under
  `pytest tests/` and on no pull request — green by never executing, which is how
  the guide claim survived in the first place.

**Done when:** the parity lint exits 0 with the step name carrying a disposition.

### T7: Retire `aesthetic/`

**Depends on:** T4

**Tests:**
- Goal-based: no file under `packs/experience-design/` or
  `guides/experience-design/` names `aesthetic/`.
- Goal-based: every `docs/design` literal left in `JOURNEY.md` sits inside a
  fenced transcript block.
- Goal-based: the committed web journey copy is byte-equal to a fresh
  `build-site.py --journeys-only` run.
- Goal-based: the three journey lints exit 0.

**Approach:**
- Update the two `**Where it lands:**` lines in `establish-design-intent.md` and
  rewrite their `rung` annotations, whose second halves ("declares the record but
  not its path") become false once T4 lands.
- Fix `establish-design-intent.md:76`, which hardcodes `docs/design/` where every
  sibling line uses `<output_dir>`.
- Edit the transcript lines in `JOURNEY.md`, including the `screen-flows/` one that
  advertises a folder the pack does not ship, then regenerate the web copy here
  rather than at release.

**Done when:** all four checks pass.

### T8: Reconcile the three registries

**Depends on:** T7

**Tests:**
- TDD by mutation: the registry-agreement test, proven red by restoring one stale
  `DESIGN.md` row. Green against the real tree.

**Approach:**
- `DESIGN.md`: replace the `aesthetic/` row with `direction/` and `tokens/`,
  correct `screen-flows/` to `screens/`, move `design-principles` to `principles/`,
  add the missing `copy/` row, and correct the `screens/` row, which names
  `interaction-design` as a writer T1 established writes nothing.
- `pack.toml`: make the subdirectory comment point at the registry rather than list
  four folders that are now nine.
- `experience-status`: add the scan rows for the folders it does not read.

**Done when:** the registry test is green and red against the named mutation.

### T9: ADR and its dataset

**Depends on:** T7

**Tests:**
- Goal-based: the dataset sits beside the ADR, and re-running its recorded queries
  reproduces the sample's counts.

**Approach:**
- Record the queries, sampling frame and inclusion rule that produced the folder
  measurement, beside the ADR rather than under any `output_dir`, then write the
  ADR citing it. A stored table of counts satisfies a path check without being
  reproducible, which is the failure mode this avoids.
- Ship the guide index row for anything T1-T7 added, naming
  `guides/experience-design/README.md` as the file that holds it.

**Done when:** the ADR is accepted and its dataset's queries reproduce its counts.

### T10: Release surface

**Depends on:** T6, T8, T9

**Tests:**
- Goal-based: `agentbundle catalogue verify --root .` exits 0, which owns the
  `pack.toml` / `plugin.json` version agreement.
- Goal-based: `.claude-plugin/marketplace.json` is byte-identical to a fresh
  self-host run.
- Goal-based: the topmost `experience-design` changelog heading names its new version.
- Goal-based: every skill given a new or corrected target has an `evals/evals.json`
  case covering it.

**Approach:**
- Bump `experience-design` (minor — two new primitives) in `pack.toml` and
  `plugin.json`; regenerate `marketplace.json` by self-host rather than editing it.
- Route learnings through the `project-knowledge` seam.

**Done when:** the four checks pass and `git status` is clean.

## Rollout

No runtime component. Adopters see new declared paths on upgrade; nothing moves an
existing file, because the two newly addressed artifacts had no address to move
from. Two exceptions are recorded as follow-ons rather than claimed as clean: this
repository's own `docs/design/direction/` already holds two files, one with a
`type:` that will collide once the read path ships; and an adopter who followed the
guide by hand and used `aesthetic/` keeps files nothing will look for.

## Risks

- **The token-taxonomy template trips the agnosticism lint.** Mitigated by
  authoring symbolically and running the lint first in T4.
- **The canonical declaration form does not fit one of the eleven.** Then the form
  is wrong, not the skill; T2 surfaces it rather than special-casing.
- **A negative case cannot be staged in T2's manual QA.** That is a blocking
  condition needing a named owner waiver recorded in the spec, per its `Never do`.

## Changelog

- 2026-09-16 — Initial plan. Third structure for this work. A combined spec drew 48
  findings, its addressing half drew 53 more, and the convergent diagnosis was that
  the criteria quantified over a population derived from surfaces the change edits.
  The population is now a closed set stated in the spec, the frontend read path is a
  separate spec because it is the only new trust boundary, and the tests are
  authored after the work they check and proven red by mutation.

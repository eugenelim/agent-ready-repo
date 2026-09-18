# Plan: spec and plan prose discipline

- **Spec:** [`spec.md`](spec.md)
- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->
- **Repository anchors:** `packs/governance-extras/.apm/skills/new-adr/` and
  `docs/specs/new-rfc-readability/` are the two analogous deliveries — a
  skill's `SKILL.md` plus `assets/` template edited at pack source, projected
  by `make build-self`, pinned by a pack test, and released by a paired
  version bump. Their tests are
  `packs/governance-extras/tests/skills/new-adr/test_lint_adr_shape.py` and
  `packs/core/tests/skills/work-loop/test_plan_records_its_approval.py`.
  Named uncertainty: nothing mechanical parses `## Objective`, `## Boundaries`
  or `**Approach:**` today — verified by reading
  `work-loop/scripts/lint-spec-status.py` (only `## Acceptance Criteria` is
  matched), `work-loop/scripts/_loop_guards.py` (the `## Boundaries` mention is
  a comment), and `new-spec/scripts/lint-contract-item-alignment.py` (its
  `ENTRY` regex covers `Tests`/`Done when` only) — so the renames are prose
  changes, and the risk is a missed prose consumer rather than a broken parse.

> **Plan contract:** this is the implementation strategy. It may change
> substantively only while its Status is `Drafting`, before approval records its
> baseline. After approval, `spec.md` and `plan.md` are pinned in substance;
> only lifecycle bookkeeping is permitted, and execution observations belong in
> `docs/specs/spec-plan-prose-discipline/notes/verification-ledger.md`.
>
> **Not every field is contract.** `Touches`, `Tests` and `Done when` are what a
> completion gate reads, and they are pinned. `Design`, `Approach`, `Grounding`
> and `Risks` are working material.

## Approach

One sequential pass over pack source, innermost artifact outward: the two
templates first, then the new reference, then `SKILL.md`, then the surfaces
that cite those files, then the guide, then the pin, then the release surface.
The order is load-bearing only at its two ends — the pin must be written
against finished text so it cannot be calibrated to a draft, and the
projection rebuild must be last because every earlier task changes its input.

The riskiest part is the rename sweep. The claim "no mechanical consumer parses
these headings" is verified (see Repository anchors) but the prose consumers
are found by grep, and a grep only reaches what its pattern and its path
argument contain. T6 therefore greps the whole tree for each old heading and
resolves every hit rather than working from the list this plan happens to name.

## Constraints

- `AGENTS.md` § Cut before adding: the prose-discipline guidance is a new file,
  justified at rung 2 — the bounded search found
  `packs/experience-design/.apm/skills/*/references/editorial-quality-gates.md`,
  which is product-copy scoped and triplicated on purpose ("Skill autonomy
  beats DRY at this scale"), so it is precedent for shape and not a file
  `new-spec` may import.
- `references/spec-authoring-rubric.md` class 6 forbids gating a judgement over
  authored prose. The new reference is advisory and carries no check.
- `packs/core/.apm/skills/new-spec/SKILL.md` is 747 lines against a 1,000-line
  `CAT-S003` ceiling and a 500-line advisory, so the guidance lands in a
  reference and `SKILL.md` gains pointers, not prose.
- The output-rendering block inside every canonical `SKILL.md` is managed by
  `tools/add-rendering-directives.py` (`UNIVERSAL_LINES`, lines 21–60) and
  pinned by `tests/roster/test_cognitive_load_repository_contract.py:766`, one
  block per skill, naming no other skill. It already owns five of the eleven
  candidate rules — lead with the point, one fact per sentence, bullets for
  separate items, short resumable sections, no repeated summary — so the new
  reference cites it and covers only the remainder.
- "Cut manufactured significance" is excluded on measurement, not taste: a
  paired ablation on 2026-09-18 (8 runs, `gpt-5.6-sol` and `claude -p`
  opus-5, length-matched 626/648-word briefs, five planted spans plus one
  positive and one negative control) removed 5/5 spans in the control arm in
  every run.

## Construction tests

One new module, `packs/core/tests/skills/new-spec/test_artifact_prose_discipline.py`,
carries every arm. Tasks add arms to it; T8 adds the arms no earlier task
owns and checks the module as a whole.

Every content arm slices the file to the section it is about by heading
before asserting, so a phrase that survives by moving elsewhere fails. Every
absence arm is paired with the presence of its replacement, so deleting a
section wholesale does not pass.

## Design (LLD)

**Section slicing.** The arms need one helper: given file text and a `## `
heading, return the text from that heading to the next `## ` at the same level.
`test_plan_records_its_approval.py::_changelog_note` already does exactly this
for one heading; the new module carries a parameterised copy rather than
importing across test modules, because `lint-pack-test-boundary` scopes a pack
test to its own pack and the two modules are peers, not a library and a caller.

**Dual naming.** A consumer that tells a reader to read a renamed section names
both, in one sentence, in the form `Agent Rules` (`Boundaries` in specs
authored before this change). One sentence rather than two so a later editor
deleting the legacy clause has to notice it.

**Conditional `Approach:`.** The template states the rule as a test the author
applies, not as a permission: write `**Approach:**` when the task holds an
ordering decision (step B must follow step A for a reason a reader cannot
infer) or a seam decision (which module, which existing helper, which
boundary). Omit it when `Tests:` and `Done when:` already say what to build and
how it is observed. The three fields keep their order; only the middle one
becomes conditional.

**Where a settled assumption goes.** The routing rule is one question: does the
fact bound what the delivery does, or shape how it is built? The first goes to
`Outcome` or `Agent Rules`, the second to the plan's `## Design (LLD)` or
`## Constraints`. No third destination, and no residue left in `Assumptions`.

## Tasks

### T1: `assets/plan.md` — approvals-only Changelog, conditional `Approach:`

**Depends on:** none

**Touches:** packs/core/.apm/skills/new-spec/assets/plan.md, packs/core/tests/skills/new-spec/test_artifact_prose_discipline.py

**Tests:**
- New module, `Changelog` slice: both approval forms present verbatim; a
  regex over the slice for `^- YYYY-MM-DD:` returns exactly those two lines.
- Same slice: the approvals-only statement is present, and neither
  `initial plan` nor `switched from approach` survives.
- Same slice, inherited guard: the words `last`, `first`, `before` and
  `same edit` remain absent from the approval paragraph — re-running
  `test_plan_records_its_approval.py` covers this, and the new arm does not
  duplicate it.
- Task-shape slice: the conditional `Approach:` rule states both halves —
  when to omit and when it is required.
- Whole file: no surviving sentence requires `Tests:` to come before
  `Approach:` unconditionally, and the tier note still lists `Approach` as
  working material.

**Approach:**
- The `## Changelog` rewrite must keep the sentence `owns *when* each is
  written` and the reason clause `when the contract froze` / `on whose
  authority`: three arms of `test_plan_records_its_approval.py` read them, and
  that file may not be edited (AC-0013).

**Done when:** AC-0001, AC-0004 (its `comes *before* Approach` half), AC-0013
(the Changelog half) and AC-0014 hold: the new module's T1 arms and
`packs/core/tests/skills/work-loop/test_plan_records_its_approval.py` both
pass, and the ledger carries the reviewer's recorded verdict for AC-0013 and
AC-0014.

### T2: `assets/spec.md` — unresolved-only Assumptions, `Outcome`, `What Changes`, `Agent Rules`

**Depends on:** none

**Touches:** packs/core/.apm/skills/new-spec/assets/spec.md, packs/core/tests/skills/new-spec/test_artifact_prose_discipline.py

**Tests:**
- `Assumptions` slice: the unresolved-only instruction is present, `none` is
  named as the empty value, and no `(source:` string survives.
- Same slice (AC-0017): all four routing destinations are named — `Outcome`,
  `Agent Rules`, `## Design (LLD)`, `## Constraints`.
- Headings: `## Outcome` and `## What Changes` present in that order,
  `## Agent Rules` present with its three `### ` subsections; `## Objective`
  and `## Boundaries` absent.
- `Outcome` slice: its guidance states the two-sentence cap, and the
  `What Changes` slice calls for a bulleted delta. A reviewer records the
  followability verdict for AC-0019; the arms here only locate the text.
- Tier note: lists `Agent Rules` as contract and `Outcome` / `What Changes` as
  working material.
- Whole file: the claim that `plan.md` keeps a changelog of how the approach
  evolved is gone, and the corrected statement is present.

**Done when:** AC-0002, AC-0003, AC-0017, AC-0013 (the Assumptions half) and
AC-0019 hold: the new module's T2 arms pass and the ledger carries the
reviewer's recorded verdicts for AC-0013 and AC-0019.

### T3: `references/prose-discipline.md` — the advisory pass

**Depends on:** none

**Touches:** packs/core/.apm/skills/new-spec/references/prose-discipline.md, packs/core/.apm/skills/new-spec/references/spec-authoring-rubric.md, packs/core/tests/skills/new-spec/test_artifact_prose_discipline.py

**Tests:**
- File exists; its opening states it is advisory and never a gate, and names
  the managed output-rendering block in this skill's own `SKILL.md` as the
  owner of the form rules.
- Four `## ` sections present: signal-word scan, structural-tell list,
  restructure-not-word-swap, distinctiveness test.
- No instruction-position `exit`, `fail`, `blocks`, or numeric threshold. The
  arm establishes those forms are absent and nothing more; whether the
  reference reads as advisory is AC-0015's recorded verdict.
- AC-0018: `spec-authoring-rubric.md` contains exactly one occurrence of
  `prose-discipline`, placed in its `## How to use it` section, still opens
  with `Six failure classes`, and carries no `## 7.` heading.
- Running `python3 tools/add-rendering-directives.py` leaves the new reference
  byte-unchanged: it is not a managed surface.

**Approach:**
- The signal words are chosen for contract prose, not marketing copy. What a
  spec attracts is hedging, reassurance and filler — `robust`,
  `comprehensive`, `seamless`, `simply`, `just`, `of course`, `in order to`,
  `leverage`, `ensure that`, `it is important to` — not `unlock` or
  `best-in-class`. Taking the experience-design list unchanged would ship a
  scan that never fires here.
- The structural tells are the canned rhetorical shapes: `not just X, but Y`,
  `isn't merely A — it's B`, a reflexive rule of three, `Let's be clear:`, a
  paragraph whose last sentence restates its first.
- `restructure rather than word-swap` is the repair rule and carries an
  example of each: swapping `leverage` for `use` leaves the sentence
  generated; deleting the sentence and stating the constraint does not.
- Carry the "short sentences" carve explicitly. A byte layout, an exact key
  order, or an enumerated channel set stays long; `AGENTS.md` already says a
  readability score is a clue and not a reason to cut needed facts, and the
  reference must not license shortening a comparison value.

**Done when:** AC-0006, AC-0007, AC-0018 and AC-0015 hold: the new module's T3
arms and `tests/roster/test_cognitive_load_repository_contract.py` pass, and
the ledger carries the reviewer's recorded verdict for AC-0015.

### T4: `SKILL.md` — assumption routing, renamed sections, prose-discipline pointers

**Depends on:** T1, T2, T3

**Touches:** packs/core/.apm/skills/new-spec/SKILL.md, packs/core/tests/skills/new-spec/test_artifact_prose_discipline.py

**Tests:**
- Step 3: the routing instruction names both destinations; the
  copy-the-confirmed-list instruction and its `user confirmation YYYY-MM-DD`
  citation form are gone.
- Step 3 ordering, inherited: `When no corpus of real inputs is reachable`
  still precedes `Surface the Unverified list and wait` —
  `test_acceptance_criteria_discipline.py` owns this arm and must still pass.
- Whole file: `Objective` and `Boundaries` no longer name spec sections; the
  new names appear in each place that previously named them. `SKILL.md` takes
  the new name only, not the dual form T6 applies — it instructs an author
  writing a spec, and a spec this skill writes carries the new headings.
- Whole file: the `plan.md` keeps its own changelog claim is gone; the
  `Tests:`-outnumbers-`Approach:` smell is gone; the conditional rule is
  stated once.
- Steps 4 and 5 each link `references/prose-discipline.md`.
- Line count stays under the 500-line advisory delta this task may add: the
  file grows by at most 20 lines.

**Approach:**
- Nine known hits, from grep: lines 132, 187, 236, 292, 560, 730 name
  `Boundaries`; 324–328 carry the changelog exception; 456, 459, 511, 516
  carry the `Approach:` rules. Re-grep rather than trusting these ordinals —
  every earlier edit in this task moves them.

**Done when:** AC-0004 and AC-0005 hold: the new module's T4 arms pass and
`packs/core/tests/skills/new-spec/` passes whole.

### T5: `references/spec-and-plan-contract.md` — contract sections and the `Approach:` rule

**Depends on:** T2, T1

**Touches:** packs/core/.apm/skills/new-spec/references/spec-and-plan-contract.md, packs/core/tests/skills/new-spec/test_artifact_prose_discipline.py

**Tests:**
- The "four sections — Objective, Boundaries, …" sentence is replaced by one
  naming the current contract sections.
- The "the **Tests** subsection comes *before* Approach" sentence is replaced
  by the conditional rule, stated by reference to `assets/plan.md` rather than
  restated in full.

**Done when:** AC-0009 holds for `references/spec-and-plan-contract.md`: the
new module's T5 arms pass.

### T6: consumers — three reviewer agents and `pre-execute-review.md`

**Depends on:** T2

**Touches:** packs/core/.apm/agents/adversarial-reviewer.md, packs/core/.apm/agents/security-reviewer.md, packs/core/.apm/agents/quality-engineer.md, packs/core/.apm/skills/work-loop/references/pre-execute-review.md, packs/core/.apm/skills/work-loop/scripts/_loop_guards.py, packs/core/tests/skills/new-spec/test_artifact_prose_discipline.py

**Tests:**
- One arm per file: it names `Agent Rules` and the legacy `Boundaries` in the
  same sentence.
- Tree-wide: grepping the source packs for a spec-section sense of
  `## Objective` or `## Boundaries` returns only the six other skills'
  own `## Boundaries` headings, which are their own artifacts and out of scope.

**Approach:**
- `_loop_guards.py:796` is a code comment naming `## Boundaries`; update the
  comment. Its behaviour is unchanged — the function keys on
  `ac_section_only`, never on that heading.
- `lint-traceability.py:168` and `lint-brief-coverage.py:82` say "banned by
  the spec's Boundaries" about a *different* spec's rule, not the template
  section. Leave both.

**Done when:** AC-0008 holds: the new module's T6 arms pass and
`make lint-ruff lint-mypy` is clean.

### T7: `guides/core/how-to/plan-and-execute-non-trivial-work.md`

**Depends on:** T2, T1

**Touches:** guides/core/how-to/plan-and-execute-non-trivial-work.md

**Tests:**
- Goal-based: grepping the file for the three strings Objective, Boundaries,
  and before-Approach (written with its backticks, as the guide writes it)
  returns nothing, and the replacement sentences are present at the four hits
  this plan located — lines 26, 83, 84 and 130.

**Done when:** AC-0009 holds for the guide: the grep in the test returns the
replacements and no stale hit.

### T8: the pin, read whole

**Depends on:** T1, T2, T3, T4, T5, T6, T7

**Touches:** packs/core/tests/skills/new-spec/test_artifact_prose_discipline.py

**Tests:**
- Add the arms no earlier task owns, all under AC-0012: run
  `packs/core/tests/pack/test_construction_time_razor.py` and
  `packs/core/tests/skills/work-loop/test_plan_records_its_approval.py`, and
  assert `git diff --exit-code origin/main -- <those two paths>` is empty, so
  "unchanged by this PR" is observed rather than asserted.
- A guard arm asserting each section slice the module uses is non-empty, so a
  renamed or deleted heading fails loudly instead of making its arms vacuous.
- Mutation check: for each content arm, revert the one sentence it pins and
  confirm the arm reds. Record the result in the verification ledger.

**Approach:**
- The guard arm is the one thing the per-task arms cannot give themselves: a
  slice helper that returns `""` makes every `assertNotIn` pass.

**Done when:** AC-0012 and AC-0016 hold:
`python3 -m pytest packs/core/tests/skills/new-spec tests/roster/test_cognitive_load_repository_contract.py -q`
passes, and the ledger records one red per content arm plus the reviewer's
recorded verdict for AC-0016.

### T9: projection, version, release entry

**Depends on:** T8

**Touches:** .claude/, .agents/, packs/core/pack.toml, packs/core/.claude-plugin/plugin.json, docs/product/changelog.md

**Tests:**
- Goal-based: `make build-self` then `git diff --exit-code` over `.claude/`
  and `.agents/` is clean.
- Goal-based: the two manifests carry the same version, one patch above
  `2.26.15`.
- Goal-based: `docs/product/changelog.md` carries a dated entry naming that
  version, with one blank line above and below every heading.

**Approach:**
- `make build-self` refuses a dirty tree, so commit T1–T8 before running it.

**Done when:** AC-0010 and AC-0011 hold: `make build-self` is clean,
`git diff --exit-code` over the two projection trees is empty, and
`make lint-ruff lint-mypy` passes.

## Rollout

Prose and template change in one PR; nothing is flagged, staged or migrated.
Reversible by revert — no persistent state, no schema, no published event. The
one irreversible edge is the `packs/core` version bump: a revert needs a new
patch version rather than a rollback to `2.26.15`.

## Risks

- **A prose consumer is missed.** The rename is found by grep, and a grep
  reaches only what its pattern and path contain. T6's tree-wide arm is the
  mitigation; its residual is a consumer that paraphrases the heading rather
  than naming it.
- **The new reference drifts into a gate.** Someone later adds a lint over its
  word list. T3's third arm is the mitigation, and the `Never do` rule is the
  standing reason.
- **`SKILL.md` grows past its advisory.** It is already 747 of 1,000 lines.
  T4 caps its own growth at 20 lines; if the pointers need more, the content
  belongs in the reference instead.

## Changelog

Approvals only; this plan is authored in the shape it ships.

- 2026-09-18: spec approved by eugenelim
- 2026-09-18: plan approved by eugenelim

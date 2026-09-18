# Spec: spec and plan prose discipline

- **Status:** Implementing <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** none
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.
>
> **Not every section is contract.** `Agent Rules`, `Testing Strategy` and
> `Acceptance Criteria` are what a completion gate reads, and an amendment
> changes them. `Outcome`, `What Changes`, `Durable Outputs`, `Follow-ons` and
> `Assumptions` are working material.
>
> This spec is authored in the section shape it ships, so the shape is
> demonstrated rather than only described.

## Outcome

An author using `new-spec` gets a spec and plan that read as the current
contract rather than a record of the authoring session, and a scannable spec
whose reader reaches the delta in the first screen. Success is that every
sentence in a finished artifact is one a later reader acts on: no drafting
diary, no settled-assumption audit trail, no restated step the tests already
determine, and no filler that signals an author who was generating rather than
deciding.

## What Changes

- The plan's `## Changelog` holds approval entries only. Drafting history
  leaves the template.
- The spec's `## Assumptions` holds unresolved items only. A fact the author
  settled is routed into the artifact that acts on it, and its citation is not
  carried forward.
- The spec's `## Objective` becomes `## Outcome`, capped at two sentences —
  who it is for, and what success is — and a new `## What Changes` sits
  directly beneath it, near the top where a human reader lands, carrying the
  bulleted delta that orients them before any contract section.
- The spec's `## Boundaries` becomes `## Agent Rules`, with its three
  subsections unchanged.
- A plan task omits `**Approach:**` when `Tests:` and `Done when:` already
  determine the work, and carries it when the task holds a real ordering or
  seam decision.
- A new `references/prose-discipline.md` gives the author a pass over their own
  prose for cliché, inflated language and canned rhetorical structure, plus the
  rule that the repair is restructuring rather than word-swapping. Advisory,
  never a gate. `references/spec-authoring-rubric.md` gains one pointer to it
  and keeps its six convergence classes.

## Durable Outputs

| Semantic role | Applicability | Destination | Owner | Expected evidence | Closeout condition |
| --- | --- | --- | --- | --- | --- |
| Maintainer procedure | Applicable — the authoring rules live in the skill, its two templates, and one new reference | `packs/core/.apm/skills/new-spec/{SKILL.md,assets/spec.md,assets/plan.md,references/{prose-discipline.md,spec-and-plan-contract.md}}` | `new-spec` skill | Pack tests under `packs/core/tests/skills/new-spec/` | Edited files present and their suites green |
| Current architecture | Applicable — three reviewer agents and one work-loop reference name the renamed spec sections and must still resolve against both old and new specs | `packs/core/.apm/agents/{adversarial-reviewer,security-reviewer,quality-engineer}.md`, `packs/core/.apm/skills/work-loop/references/pre-execute-review.md` | `work-loop` | Pack test asserting each names the new heading and the legacy one | Every consumer updated |
| Interface compatibility | Applicable — installed copies are byte projections of pack source | `.claude/skills/`, `.claude/agents/`, `.agents/skills/`, `.agents/agents/` | `make build-self` | `make build-self` leaves no diff | Projections match pack source |
| Release history | Applicable — a published pack's behavior changes | `packs/core/pack.toml`, `packs/core/.claude-plugin/plugin.json`, `docs/product/changelog.md` | Release surface | Both manifests carry the same bumped version; the changelog carries a dated entry naming it | Entry present and topmost under `[Unreleased]`'s successor position |
| User promise | Applicable — the core how-to walks an adopter through the artifacts these sections live in | `guides/core/how-to/plan-and-execute-non-trivial-work.md` | Guides | Grep over `guides/core/` for each renamed heading and each removed rule returns either no hit or an updated one | Grep re-run at finish with every hit resolved |
| Reusable learning | Applicable — the prose-discipline reference is itself the durable learning | `packs/core/.apm/skills/new-spec/references/prose-discipline.md` | `new-spec` skill | The file and its pack test | Reference present and pinned |

## Agent Rules

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit pack source under `packs/core/.apm/`, then run `make build-self` to
  regenerate the tracked `.claude/` and `.agents/` projections, and commit both.
- Keep `packs/core/tests/skills/work-loop/test_plan_records_its_approval.py`
  passing unchanged: it pins the two approval entry forms verbatim, pins that
  there are exactly two, and forbids the words `last`, `first`, `before` and
  `same edit` inside the template's approval paragraph.
- Name both headings wherever a consumer tells a reader to *read* a renamed
  section — the new name and the legacy one — because roughly 490 specs already
  on disk carry `## Objective` and `## Boundaries` and a reviewer pointed only
  at the new name loses its standard on all of them. Four files are in that
  class: the three reviewer agents and `pre-execute-review.md`.
- Give `packs/core/.apm/skills/new-spec/SKILL.md` the new name only. It is a
  spec-heading consumer, but it instructs an author *writing* a spec, and a
  spec this skill writes always carries the new headings, so the legacy name
  there would be dead weight rather than compatibility.
- Repair every surviving statement this change falsifies, not only the one at
  the cited line. Three are known: that `plan.md` keeps a changelog of how the
  approach evolved (`assets/spec.md` and `SKILL.md`), that a task's `Tests:`
  lines outnumbering its `Approach:` lines is a smell (`SKILL.md`, twice), and
  that `Tests:` comes before `Approach:` (`assets/plan.md`,
  `references/spec-and-plan-contract.md`, `work-loop` `SKILL.md`).
- Bump `packs/core` in `pack.toml` and `.claude-plugin/plugin.json` together,
  and add the matching dated entry to `docs/product/changelog.md`.

### Ask first

- Any change to the chat-side `ASSUMPTIONS I'M MAKING:` checkpoint — its
  Verified/Unverified split, its verify-before-filing rule, or the sign-off
  wait. `guides/core/how-to/plan-and-execute-non-trivial-work.md` describes
  that block to adopters, so changing it changes a documented surface.
- Any change to `tools/add-rendering-directives.py`'s `UNIVERSAL_LINES`. That
  constant is the single source for the managed output-rendering block in
  every canonical skill, so a change there edits roughly thirty skills at once.
- Renaming a `## Boundaries` heading that belongs to a different artifact.
  Six other core skills carry their own `## Boundaries` section in their own
  `SKILL.md`; none of them is the spec template and none is in scope.

### Never do

- **Gate on the prose-discipline guidance.** `references/spec-authoring-rubric.md`
  class 6 forbids gating a judgement over prose whose author chose the wording,
  and requires an uncalibratable check to be guidance that never blocks. No
  lint, no blocking word list, no scored check.
- **Retrofit an existing spec or plan.** Approved, Implementing and Shipped
  artifacts are pinned; rewriting one needs the controlled-amendment path. This
  change governs what is authored from now on.
- **Leave a settled fact in `## Assumptions` with its citation.** That is the
  audit trail this change removes; a section that keeps it has not changed.
- **Make `**Approach:**` optional without stating when it is required.** A rule
  that only permits omission turns into "never write one", and the ordering and
  seam decisions it carries have no other home.
- **Hand-edit the managed output-rendering block** between
  `<!-- agentbundle:output-rendering:start -->` and its end marker in any
  `SKILL.md`. `tools/add-rendering-directives.py` owns that text and overwrites
  a local edit, and
  `tests/roster/test_cognitive_load_repository_contract.py:766` pins one block
  per skill that names no other skill.
- **Add a seventh failure class to `references/spec-authoring-rubric.md`.** Its
  six classes are the ones that stop a review loop converging; prose quality is
  a different axis, and the file's own preamble forbids a second copy of a rule
  another surface owns. It gains a pointer, nothing more.
- **Ship a "cut manufactured significance" rule.** A paired ablation on
  2026-09-18 — eight runs, two workers, length-matched briefs, five planted
  spans — removed every span in the control arm, so the rule measured zero
  marginal contribution against the house rules already in force.

## Testing Strategy

The deliverable is prose, so verification splits at two altitudes and neither
group borrows the other's authority.

- **Goal-based — AC-0001, AC-0002, AC-0003, AC-0004, AC-0005, AC-0006,
  AC-0007, AC-0008, AC-0009, AC-0010, AC-0011, AC-0012, AC-0017, AC-0018.**
  What a command
  settles outright: a heading present or absent, a regex over one section
  returning an exact line set, a file existing, a link resolving, two manifests
  carrying equal strings, `git diff --exit-code` empty, a named suite passing.
  These live in one new pack test module,
  `packs/core/tests/skills/new-spec/test_artifact_prose_discipline.py`. Every
  content arm slices the file to the section it is about by heading before
  asserting, so a phrase that survives by moving elsewhere fails, and one guard
  arm asserts each slice is non-empty so a renamed heading reds rather than
  making its arms vacuous.
- **Manual QA — AC-0013, AC-0014, AC-0015, AC-0016, AC-0019.** Everything
  turning on
  what the prose *means*: whether an instruction is followable, whether
  guidance reaches the case it names, whether a replacement carries what the
  removed sentence carried. The result is a named reviewer's recorded verdict
  in `notes/verification-ledger.md`, and it claims no mechanical proxy.
  Counting a keyword cannot establish that an instruction is unambiguous, and a
  `grep` written behind a semantic criterion is a false check rather than a
  weak one.

## Acceptance Criteria

- [ ] **AC-0001.** `[goal-based]` In `assets/plan.md`'s `## Changelog` section,
  the lines matching `^- YYYY-MM-DD:` are exactly
  `- YYYY-MM-DD: spec approved by <handle>` then
  `- YYYY-MM-DD: plan approved by <handle>`, and that section contains neither
  `initial plan` nor `switched from approach`.
- [ ] **AC-0002.** `[goal-based]` `assets/spec.md`'s `## Assumptions` section
  contains no `(source:` substring and does contain the literal `none`.
- [ ] **AC-0003.** `[goal-based]` `assets/spec.md` contains the headings
  `## Outcome`, `## What Changes` and `## Agent Rules` — the first two in that
  order — together with `### Always do`, `### Ask first` and `### Never do`,
  and contains neither `## Objective` nor `## Boundaries`.
- [ ] **AC-0004.** `[goal-based]` No file under
  `packs/core/.apm/skills/new-spec/` contains
  `changelog of how the approach evolved`, ``outnumber its `Approach:` ``, or
  `comes *before* Approach`.
- [ ] **AC-0005.** `[goal-based]` `SKILL.md` contains no
  `user confirmation YYYY-MM-DD` citation form, and links
  `references/prose-discipline.md` from both the spec-body step and the
  plan-body step.
- [ ] **AC-0006.** `[goal-based]`
  `packs/core/.apm/skills/new-spec/references/prose-discipline.md` exists and
  carries four `## ` sections: a signal-word scan, a structural-tell list, a
  restructure-not-word-swap rule, and a distinctiveness test.
- [ ] **AC-0007.** `[goal-based]` That reference contains no
  instruction-position `exit`, `fail`, or `blocks`, and no numeric threshold.
  This establishes the absence of those forms and nothing more; whether the
  reference reads as advisory is AC-0015's. Running
  `tools/add-rendering-directives.py` leaves the reference byte-unchanged.
- [ ] **AC-0008.** `[goal-based]` Each of
  `packs/core/.apm/agents/{adversarial-reviewer,security-reviewer,quality-engineer}.md`
  and `packs/core/.apm/skills/work-loop/references/pre-execute-review.md`
  contains `Agent Rules` and `Boundaries` in the same sentence.
- [ ] **AC-0009.** `[goal-based]`
  `guides/core/how-to/plan-and-execute-non-trivial-work.md` contains none of
  `Objective`, `Boundaries`, or ``before `Approach:` ``, and
  `references/spec-and-plan-contract.md` contains neither
  `four sections — Objective, Boundaries` nor `comes *before* Approach`.
- [ ] **AC-0010.** `[goal-based]` `make build-self` leaves `git diff
  --exit-code` empty over `.claude/` and `.agents/`.
- [ ] **AC-0011.** `[goal-based]` `packs/core/pack.toml` and
  `packs/core/.claude-plugin/plugin.json` carry the same version string, one
  patch above `2.26.15`, and `docs/product/changelog.md` contains that string.
- [ ] **AC-0012.** `[goal-based]`
  `packs/core/tests/skills/work-loop/test_plan_records_its_approval.py`,
  `packs/core/tests/pack/test_construction_time_razor.py`,
  `packs/core/tests/skills/new-spec/`, and
  `tests/roster/test_cognitive_load_repository_contract.py` all pass, and the
  first two are unchanged by this PR.
- [ ] **AC-0013.** `[manual QA]` A reviewer reads the rewritten `## Changelog`
  note and the rewritten `## Assumptions` note and records that each states its
  own rule without restating one another surface owns: the Changelog note
  defers approval *timing* to `work-loop`, and the Assumptions note defers the
  verify-before-filing discipline to `SKILL.md` step 3.
- [ ] **AC-0014.** `[manual QA]` A reviewer reads `assets/plan.md`'s task shape
  and records that the conditional `**Approach:**` rule states both halves
  followably — a named test for when to omit it, and a named test for when it
  is required — and that no surviving sentence elsewhere contradicts it.
- [ ] **AC-0015.** `[manual QA]` A reviewer reads
  `references/prose-discipline.md` against the `agentbundle:output-rendering`
  block inside `new-spec`'s own `SKILL.md` and records two verdicts: that the
  reference covers only what the block does not, citing the block as the owner
  of the form rules rather than repeating them; and that every instruction in
  it reads as advice an author weighs, with no imperative that a completion
  gate could be built to read.
- [ ] **AC-0016.** `[manual QA]` A reviewer reads every sentence this change
  replaced alongside its replacement and records that no obligation was lost —
  separately for the Changelog note, the Assumptions note, the two renamed spec
  sections, the `Approach:` rule, and each of the four consumer files.
- [ ] **AC-0017.** `[goal-based]` `assets/spec.md`'s `## Assumptions` section
  names all four routing destinations for a settled fact: `Outcome`,
  `Agent Rules`, `## Design (LLD)` and `## Constraints`.
- [ ] **AC-0018.** `[goal-based]` `references/spec-authoring-rubric.md`
  contains exactly one occurrence of `prose-discipline`, still opens with the
  words `Six failure classes`, and carries no `## 7.` heading.
- [ ] **AC-0019.** `[manual QA]` A reviewer reads `assets/spec.md`'s `## Outcome`
  and `## What Changes` guidance and records that the two-sentence cap is
  stated as something an author can apply, and that the `What Changes`
  guidance calls for a bulleted delta rather than a second telling of the
  Outcome.

## Follow-ons

<!--
- eugenelim: the requester, if raised — apply the same treatment to `new-rfc`
  and `new-adr`. Out of scope here: the request named `new-spec`.
-->

## Assumptions

- Product: whether adopters want the same treatment in `new-rfc` and `new-adr`.
  Would change scope only, and only after this ships. Settled by: the
  requester, if they raise it.

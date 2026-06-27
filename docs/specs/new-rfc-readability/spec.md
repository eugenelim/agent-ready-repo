# Spec: new-rfc human-readability polish (B-narrow)

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0014
- **Brief:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `new-rfc` skill produces proposals that are easier for a human reviewer to
consume and easier for a human author to invoke, **without** changing the
answer-first template spine or the research→draft→gate flow that RFC-0014 froze.
Three refinements land: (1) the skill draws an explicit *body-as-argument /
proof-as-linked-notes* line so the RFC body reads as the argument a reviewer
decides from, not an audit trail of the author's work; (2) the pre-handoff gate
keeps every check RFC-0014 mandates but hands the human a concise,
reviewer-oriented readiness summary with the heavy proof *linked*, rather than a
compliance dump; (3) the skill drafts short, identifying RFC titles, leaving the
fuller explanation to "The ask". The richer changes the critique proposed —
a decision-weight field, a reviewer-brief section, a decisions-as-table, a shape
phase — are deliberately **out of scope** here because each reverses or revises a
frozen RFC-0014 decision and is routed to a follow-on RFC instead.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit the pack source (`packs/governance-extras/.apm/skills/new-rfc/{SKILL.md,assets/rfc.md}`)
  then run `make build-self` to regenerate the `.claude/` and `.agents/` copies.
- Run both lint surfaces by hand — `lint-packs` (source) and
  `tools/lint-agent-artifacts.py` (projection).
- Keep `docs/guides/governance-extras/how-to/new-rfc.md` (a Living doc) in sync
  in the same PR when the gate's described behavior changes.

### Ask first

- Any change that would touch an RFC-0014 frozen decision — the template spine
  ("The ask" = BLUF + SCQA + numbered decisions; the fixed section set), the
  research→draft→gate flow, or the deliberately-cut decision-weight field.
  These escalate to the follow-on RFC; they are not made here.

### Never do

- **Add a new RFC body section or header field, or convert "The ask" decisions
  from numbered prose to a table** — that revises RFC-0014 decision 1 and is the
  RFC's job, not this PR's.
- **Remove or weaken any check the RFC-0014 pre-handoff gate mandates**
  (citation-integrity, verify-before-you-assert, per-subpoint backing, the
  completeness checklist, the mandatory `adversarial-reviewer` dispatch). This
  PR changes only how the gate's *result* is presented, never what it checks.
- **Edit `docs/CONVENTIONS.md`** — a hard title convention (or any convention
  change) is RFC-gated; this PR's short-title guidance lives in the skill only.
- Add a new dependency, module, or top-level directory.

## Testing Strategy

This is a prose-guidance change to a skill (no code logic), so verification is
**goal-based** with a light **manual-QA read** of the built artifact:

- *Each added guidance landed in the source and projected* — goal-based: `grep`
  the three changes in both the pack source and the regenerated `.claude/` +
  `.agents/` copies. (AC1, AC2, AC3, AC7)
- *No RFC-0014-mandated gate check was removed or weakened* — goal-based: `grep`
  for each check's **load-bearing clause** (not just its name) in step 5
  ("fetched"/"actually contain" for citation-integrity; "executed"/"never
  self-certified" for verify-before-you-assert; "mandatory" for the
  `adversarial-reviewer` dispatch), plus a manual diff of step 5's check bodies
  against RFC-0014 § Proposal → Drafting flow step 4 (Pre-handoff gate). (AC4)
- *No frozen-decision surface changed* — goal-based: `git diff` shows no new
  template section/field, no numbered→table conversion, and `docs/CONVENTIONS.md`
  is untouched. (AC5)
- *The build tree is clean and both lints pass* — goal-based: `make build-self`
  leaves no drift; `lint-packs` and `tools/lint-agent-artifacts.py` exit clean.
  (AC8)
- *The projected skill reads coherently end-to-end* — manual QA: read the
  regenerated `.claude/skills/new-rfc/SKILL.md` and confirm the new guidance is
  consistent with the surrounding (unchanged) procedure. (AC1–AC4)

## Acceptance Criteria

- [x] **AC1 — body-as-argument split rule.** `new-rfc` SKILL.md states, in the
  draft step, that a section which changes the reviewer's decision stays in the
  RFC body, while a section that mainly demonstrates the author did the work is
  summarized in the body and its detail moved to the optional `NNNN-notes/`
  companion; the anti-patterns list gains a "proof-of-work padding the body"
  entry.
- [x] **AC2 — humane gate output.** SKILL.md step 5 instructs the skill to emit,
  at handoff, a concise reviewer-oriented readiness summary (each line keyed to a
  reviewer-facing question — decision clear, do-nothing present, riskiest
  assumption tested, citations checked, open questions owned, adversarial pass
  result), with heavy proof (citation-fetch detail, adversarial transcript)
  **linked or summarized, not pasted**. SKILL.md states the readiness summary is
  emitted **to chat at handoff, not written into the RFC body or template** —
  closing the back door to a reviewer-brief surface RFC-0014 deferred.
- [x] **AC3 — short-title guidance.** SKILL.md states the RFC title should be a
  short identifier of the proposal with the fuller explanation living in "The
  ask"; the anti-patterns list gains a "title carries the whole abstract" entry;
  `assets/rfc.md` line 1 carries a short-title cue comment.
- [x] **AC4 — gate checks preserved (semantics, not just names).** All five
  RFC-0014 pre-handoff checks remain present and executed in SKILL.md step 5
  (citation-integrity protocol, verify-before-you-assert, per-subpoint backing,
  completeness checklist, mandatory `adversarial-reviewer` dispatch); none is
  removed or softened. Verified not by the five check-names alone but by each
  check's **load-bearing clause** surviving the reframe — e.g. citations are
  *fetched* and must *actually contain* the claim (not merely "checked");
  verify-before-you-assert is *executed and recorded, never self-certified*; the
  `adversarial-reviewer` dispatch stays *mandatory*. The reframe changes tone and
  adds the handoff summary; it does not weaken any check's required action.
- [x] **AC5 — no frozen-decision surface changed.** The diff introduces no new
  RFC body section or header field, does not convert "The ask" numbered
  decisions to a table, and does not modify `docs/CONVENTIONS.md`.
- [x] **AC6 — how-to guide synced.** `docs/guides/governance-extras/how-to/new-rfc.md`
  Step 4 reflects the reviewer-friendly readiness handoff — the **Step 4 prose**
  contains both the tokens **"readiness summary"** and **"proof"**
  (linked/summarized); the check is scoped to Step 4 so the pre-existing
  "proof" mention in the Pitfalls section can't satisfy it — with no other drift
  introduced.
- [x] **AC7 — projection regenerated.** `make build-self` has been run; the
  regenerated projected new-rfc skill copy/copies carry all three changes and
  `git status` shows no residual drift (the clean tree after build-self is the
  authoritative gate, independent of how many adapter copies the build emits).
- [x] **AC8 — version + changelog + lints + eval untouched.** `governance-extras`
  is bumped `0.3.1 → 0.3.2` in both `pack.toml` and `.claude-plugin/plugin.json`;
  a `docs/product/changelog.md` `[Unreleased]` entry is added; the new-rfc Tier-4
  eval (`evals/evals.json`) is unchanged by `git diff` (and remains consistent —
  it asserts on the RFC's observable output: structure, citation-verification,
  and completeness, all of which this PR preserves, because it changes only the
  skill's drafting/handoff prose, not the produced RFC's contract); `lint-packs`
  and `tools/lint-agent-artifacts.py` pass.

## Assumptions

- Process: B-narrow's three changes do not reverse/revise RFC-0014's frozen
  decisions — spine, flow, and the cut decision-weight field stay untouched
  (source: docs/rfc/0014-answer-first-rfc-format-and-drafting-flow.md, read 2026-06-27).
- Technical: the edit point is the pack source and `.claude/`+`.agents/` copies
  are generated via `make build-self` (source: RFC-0014 line 87; both source
  files read 2026-06-27).
- Process: two lint surfaces apply — `lint-packs` (source) and
  `tools/lint-agent-artifacts.py` (projection) (source: AGENTS.md §Code style; memory).
- Process: a user-visible skill prose change needs a `docs/product/changelog.md`
  `[Unreleased]` entry in the same PR (source: docs/product/changelog.md header, read 2026-06-27).
- Technical: pack version lives in both `pack.toml` and
  `.claude-plugin/plugin.json` (both 0.3.1) and co-bumps; `build-self` refreshes
  the `marketplace.json` aggregation (source: grep of both files 2026-06-27; memory).
- Process: the how-to guide is a Living doc; drift closes in the same PR
  (source: RFC-0014 line 159; memory).
- Process: version bump is PATCH (0.3.2) and the Tier-4 eval rubric is left
  untouched in B-narrow (source: user confirmation 2026-06-27).

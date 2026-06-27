# Plan: new-rfc human-readability polish (B-narrow)

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Three small, RFC-0014-clean prose edits to one skill, plus the mechanical
trailer every governance-extras change carries. All substantive edits land in
the pack source (`packs/governance-extras/.apm/skills/new-rfc/{SKILL.md,assets/rfc.md}`);
the `.claude/` and `.agents/` copies are regenerated, never hand-edited. The
riskiest part is *staying inside RFC-0014's lines* — the guard is the spec's
`Never do` list and a `git diff` check that no template section/field appears and
`CONVENTIONS.md` is untouched. Verification is goal-based (`grep` the guidance in
source + projection, lints, clean build tree) with a manual read of the projected
skill for coherence. Order: content edits first (T1–T3), then guide sync (T4),
then the version/changelog/projection trailer (T5).

## Constraints

- **RFC-0014** (Accepted, frozen) governs this skill's template and flow. This
  plan changes only presentation/guidance, never a frozen decision; the spine,
  the research→draft→gate flow, and the deliberately-cut decision-weight field
  are untouched.
- **CONVENTIONS § 3** routes format/convention changes through an RFC — hence the
  hard title convention and the spine changes are deferred to the follow-on RFC,
  not made here.

## Construction tests

Per-task `grep`/`diff` checks live under each task. No cross-cutting tests beyond
the final build-drift + lint gate in T5.

**Integration tests:** none beyond per-task checks.
**Manual verification:** read `.claude/skills/new-rfc/SKILL.md` after build-self
and confirm the three changes read coherently against the unchanged procedure.

## Tasks

### T1: body-as-argument / proof→notes split rule (AC1)

**Depends on:** none

**Tests:**
- `grep` in `packs/governance-extras/.apm/skills/new-rfc/SKILL.md`: the draft step
  states decision-changing content stays in the body; proof-of-work is summarized
  and its detail moved to the `NNNN-notes/` companion.
- `grep`: the anti-patterns list contains a "proof-of-work padding the body" entry.
- `grep` in `assets/rfc.md`: the `Evidence & prior art` guidance carries the
  one-line split-rule cue (no new section added).

**Approach:**
- In SKILL.md step 4 ("Draft the body, answer-first"), add the split rule:
  *if a section changes the reviewer's decision it stays in the body; if it mainly
  demonstrates the work was done, summarize it and move the detail to the optional
  `NNNN-notes/` companion.*
- Add an anti-pattern: padding the body with proof-of-work (full research
  transcripts, prior-art matrices, adversarial logs) that belongs in `NNNN-notes/`.
- Add the one-line cue to the template's `Evidence & prior art` comment block.

**Done when:** the three greps match and `git diff` shows no new template section.

### T2: humane pre-handoff gate output (AC2, AC4)

**Depends on:** none

**Tests:**
- `grep` in SKILL.md step 5: the `REVIEW READINESS:` label is present, with at
  least two of its six keyed sub-questions verifiable in the prose (e.g.
  "riskiest assumption tested", "adversarial pass") — so AC2's six-line *content*
  is checked, not just its framing.
- `grep` in SKILL.md step 5: instruction that heavy proof is linked/summarized,
  not pasted, AND that the readiness summary is a **chat handoff artifact, not an
  RFC body/template section** (AC2 back-door guard).
- `grep` confirms all five RFC-0014 gate checks still present *and not softened* —
  match each check's load-bearing clause, not just its name: "fetched" +
  "actually contain" (citation-integrity); "checked against the artifact, not
  asserted" (verify-before-you-assert's own bullet) under the step-5 preamble
  guard "executed and its result recorded, never self-certified" that covers all
  checks; per-subpoint "backed"; completeness checklist items; "mandatory"
  `adversarial-reviewer` dispatch. Manual diff of step-5 check
  bodies against RFC-0014 § Proposal → Drafting flow step 4 (Pre-handoff gate)
  confirms no action verb dropped (AC4, both halves: present *and* not softened).

**Approach:**
- Reframe step 5's register from compliance-audit to reviewer-confidence while
  keeping every check intact and executed.
- Add the `REVIEW READINESS:` handoff-summary shape (chat artifact, **not** an RFC
  body/template section): decision clear · do-nothing present · riskiest
  assumption tested (+link) · citations checked · open questions owned ·
  adversarial pass (clean | issues linked).
- State that the heavy proof (citation-fetch detail, adversarial transcript) is
  linked or summarized, never pasted into the RFC body.

**Done when:** the readiness-summary greps match, all five check-name greps still
match, and no new template section appears in `git diff`.

### T3: short-title drafting guidance (AC3)

**Depends on:** none

**Tests:**
- `grep` in SKILL.md: the title should be a short identifier; the fuller
  explanation lives in "The ask".
- `grep`: anti-patterns list contains a "title carries the whole abstract" entry.
- `grep` in `assets/rfc.md` line 1 region: short-title cue comment present.
- `git diff --stat` shows `docs/CONVENTIONS.md` is **not** in the change (AC5).

**Approach:**
- In SKILL.md step 2 (copy + rename to `NNNN-<kebab-title>.md`), add short-title
  guidance.
- Add the long-title anti-pattern.
- Add a `<!-- short, identifying title; fuller explanation goes in "The ask" -->`
  cue to `assets/rfc.md` line 1.

**Done when:** the title greps match and `CONVENTIONS.md` is untouched.

### T4: sync the how-to guide (AC6)

**Depends on:** T2

**Tests:**
- `grep` in `docs/guides/governance-extras/how-to/new-rfc.md` Step 4: prose
  contains the tokens "readiness summary" and "proof" (linked/summarized) —
  matching the literal tokens AC6 names.
- `git diff` on the guide shows only the Step 4 update (no unrelated drift).

**Approach:**
- Update Step 4 so it describes the gate handing back a reviewer-oriented
  readiness summary with proof linked, consistent with T2. Leave Steps 1–3, 5–6
  and Pitfalls unchanged.

**Done when:** the Step 4 grep matches and the guide diff is scoped to Step 4.

### T5: version bump + changelog + projection (AC7, AC8)

**Depends on:** T1, T2, T3, T4

**Tests:**
- `grep`: `pack.toml` and `.claude-plugin/plugin.json` both read `0.3.2`.
- `grep`: `docs/product/changelog.md` `[Unreleased]` has the new entry.
- `make build-self` then `git status` shows no residual drift; the projected
  new-rfc skill copy/copies carry all three changes.
- `git diff` shows `evals/evals.json` is untouched (AC8 eval-untouched guard).
- `lint-packs` and `tools/lint-agent-artifacts.py` exit clean.

**Approach:**
- Bump `governance-extras` `version` to `0.3.2` in `pack.toml` and
  `.claude-plugin/plugin.json`.
- Add a `docs/product/changelog.md` `[Unreleased] → Changed` entry describing the
  reviewer-readability refinements.
- Run `make build-self`; confirm `marketplace.json` aggregation updated and the
  tree is clean. Run both lint surfaces.

**Done when:** versions match, changelog entry present, build tree clean, both
lints green, projected copies updated.

## Risks

- **Local `make build-self` reads the sibling (main) editable install, not local
  edits** (known repo gotcha): pack *content* projection still works from source,
  but if drift appears, verify via a clean tree / CI, which is authoritative.
- **Tone-softening step 5 could accidentally weaken a mandated check** — mitigated
  by AC4's explicit five-check grep and the `Never do` guard.

## Changelog

- 2026-06-27: initial plan. B-narrow scope is the three RFC-0014-clean
  refinements — (a) body-as-argument / proof→notes split rule, (b) reviewer-
  friendly pre-handoff gate *output* (presentation only, no check changed),
  (c) short-title drafting guidance. The richer changes (decision-weight field,
  reviewer-brief section, decisions-as-table, shape phase) are deferred to a
  follow-on RFC because each reverses or revises an RFC-0014 frozen decision.

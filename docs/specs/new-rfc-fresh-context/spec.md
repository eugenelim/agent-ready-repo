# Spec: new-rfc fresh-context readability + decidable-in-chat decisions

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0014, RFC-0054
- **Brief:** none
- **Discovery:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `new-rfc` skill produces RFCs that **read from zero prior context** and
hands the author decisions that are **decidable in the chat message itself** —
without changing the answer-first template spine, the research→draft→gate flow,
or the section set that RFC-0014 / RFC-0054 froze. It serves the two humans
RFC-0054 named (the *author* who must decide, the *reviewer* who must consume),
closing a gap both readability waves left: an RFC drafted today leans on
vocabulary inherited from sibling RFCs (`sidecar`, `the gate arc`, `lens`,
`cascade-invalidation`) that a cold reader can't resolve, and the per-decision
handoff in chat is compressed to roughly one line — too terse for the author to
decide from without opening files. RFC-0053 is the exhibit: a reader had to
hand-patch it with inline glosses and "what X means" blocks *after* drafting,
because the skill never instructed the draft to be cold-readable in the first
place.

Four refinements land, all confined to the skill:

1. **Fresh-context drafting principle.** The skill writes every RFC for a reader
   who has *not* read the related RFCs: each project-coined term, acronym, or
   sibling-RFC back-reference is given a plain-language gloss on first use; the
   draft never leans on inherited vocabulary as if known.
2. **Decidable-in-chat decision handoff.** The chat decision block the skill
   emits at the research/de-risk checkpoint carries enough context per decision
   — plain-language question, the concrete options with their real trade-offs,
   the recommendation with its reasoning, and what accepting each option costs —
   that the author can decide in place without opening a file.
3. **A no-context readability check in the pre-handoff gate.** Before status →
   Open, the skill dispatches a **generic subagent in a fresh context with
   project context denied by the dispatch prompt** — given only the RFC text and
   instructed not to read the project docs, `CLAUDE.md`/`AGENTS.md`, or sibling
   RFCs — whose sole job is to list every term, acronym, or back-reference a cold
   reader can't resolve. It is a *generic* dispatch with a context-denial prompt,
   **not** a new named agent role. It runs *in addition to* the existing
   mandatory `adversarial-reviewer` (which loads project conventions by design
   and is the wrong instrument for a cold-reader test), and its result — the
   named unresolved terms, or an explicit noted skip when the harness offers no
   subagent dispatch — is recorded in the handoff, never silently dropped.
4. **Two anti-patterns** added to the refuse list: leaning on undefined
   sibling-RFC jargon, and a decision handoff too terse to decide from.

The answer-first spine, the fixed section set, the `Decision weight` field, the
`## Reviewer brief`, the decisions table, and every RFC-0014 pre-handoff gate
check are unchanged — this spec adds drafting discipline and one gate check, and
enriches one chat-only handoff format. It does not reverse a frozen decision.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- Edit the pack source
  (`packs/governance-extras/.apm/skills/new-rfc/{SKILL.md,assets/rfc.md}`) then
  run `make build-self` to regenerate the `.claude/` and `.agents/` copies.
- Run both lint surfaces by hand — `lint-packs` (source) and
  `tools/lint-agent-artifacts.py` (projection).
- Keep `docs/guides/governance-extras/how-to/new-rfc.md` (a Living doc) in sync
  in the same PR when the gate's or the handoff's described behavior changes.
- Specify the no-context readability check **harness-neutrally** — describe the
  context-denial and the dispatch the same way the existing `adversarial-reviewer`
  dispatch is described (a subagent matching a role; a noted skip if absent),
  not as one vendor's API.

### Ask first

- Any change that would touch an RFC-0014 / RFC-0054 frozen decision — the
  template spine, the fixed section set, the `Decision weight` field, the
  `## Reviewer brief`, the decisions table, or the research→draft→gate flow.
  These escalate to an RFC; they are not made here.
- Adding a **new mandatory RFC body section** (e.g. a required glossary) — the
  fresh-context principle is satisfied by inline define-on-first-use, not a new
  section; a new required section revises the frozen section set and is RFC work.

### Never do

- **Remove or weaken any check the RFC-0014 pre-handoff gate mandates**
  (citation-integrity, verify-before-you-assert, per-subpoint backing, the
  completeness checklist, the mandatory `adversarial-reviewer` dispatch). This
  PR *adds* a check; it changes none of them. The no-context readability check is
  additive and never substitutes for the adversarial pass.
- **Add a new RFC body section or header field, or convert any existing
  structure** — that revises a frozen decision and is an RFC's job.
- **Edit `docs/CONVENTIONS.md` or `docs/CHARTER.md`** — convention/charter change
  is RFC-gated; this PR's guidance lives in the skill only.
- Add a new dependency, module, or top-level directory.

## Testing Strategy

This is a prose-guidance change to a skill (no code logic), so verification is
**goal-based** with a light **manual-QA read** of the built artifact, plus a
**Tier-4 eval** update that asserts on the produced RFC's observable output:

- *Each added guidance landed in the source and projected* — goal-based: `grep`
  each of the four changes in both the pack source and the regenerated
  `.claude/` + `.agents/` copies. (AC1, AC2, AC3, AC4, AC9)
- *The no-context check is specified as a generic context-denied dispatch and
  additive* — goal-based: `grep` step 6 for the context-denial clause (a generic
  subagent denied project docs / sibling RFCs), the "in addition to" /
  non-substitution clause against the adversarial pass, and that the result (or
  the noted skip) is recorded in the `REVIEW READINESS` handoff. (AC3)
- *The no-context check actually produces a cold-reader finding* — manual QA: one
  real context-denied dispatch is run against a sample RFC and its output (the
  named unresolved terms) recorded in the PR / manual-QA notes, so AC3 has a
  behavioral anchor, not only a textual one. (AC3)
- *No RFC-0014 / RFC-0054 frozen-decision surface changed* — goal-based:
  `git diff` shows no new template section/field, no structural conversion, and
  `docs/CONVENTIONS.md` / `docs/CHARTER.md` untouched; manual diff of step 6's
  existing check bodies confirms each load-bearing clause survives. (AC5)
- *The build tree is clean and both lints pass* — goal-based: `make build-self`
  leaves no drift; `lint-packs` and `tools/lint-agent-artifacts.py` exit clean.
  (AC8)
- *The eval encodes the two new observable behaviors* — goal-based: a
  fresh-context-readability assertion is added to the existing draft-the-RFC
  eval, and a new `evals.json` eval entry exercises the decidable-in-chat
  handoff; `eval_queries.json` (trigger/activation only) is unchanged. (AC7)
- *The projected skill reads coherently end-to-end* — manual QA: read the
  regenerated `.claude/skills/new-rfc/SKILL.md` and confirm the new guidance is
  consistent with the surrounding (unchanged) procedure. (AC1–AC4)

## Acceptance Criteria

- [x] **AC1 — fresh-context drafting principle.** `new-rfc` SKILL.md, in the
  draft step (step 5), states that the RFC is written to be read from zero prior
  context: every project-coined term, acronym, or sibling-RFC back-reference is
  given a plain-language gloss on its first use in the body, and the draft does
  not lean on vocabulary inherited from related RFCs as if the reader knows it.
  The principle is satisfied by inline define-on-first-use, not a new mandatory
  section. `assets/rfc.md` carries a short cold-reader cue comment near the top.
- [x] **AC2 — decidable-in-chat decision handoff.** SKILL.md step 4's emitted
  decision/findings block is specified to be self-contained per decision —
  carrying, for each decision, the plain-language question, the concrete options
  with their real trade-offs, the recommendation with its reasoning, and the
  consequence of accepting each option — so the author can decide from the chat
  message without opening a file. The expanded format is shown in step 4's
  `RESEARCH FINDINGS` fenced **chat block** (the emitted-to-chat handoff, not the
  `assets/rfc.md` template).
- [x] **AC3 — no-context readability check in the gate.** SKILL.md step 6
  (pre-handoff gate) adds a check that dispatches a **generic subagent in a fresh
  context with project context denied by the dispatch prompt** — given only the
  RFC text and instructed not to read the project docs, `CLAUDE.md`/`AGENTS.md`,
  or sibling RFCs — to list every term, acronym, or back-reference a cold reader
  can't resolve; unresolved items are glossed before handoff. It is specified as
  a **generic** dispatch with a context-denial *prompt*, **not** a new named
  agent role or persona (so it adds no module — see Never do). The check is
  stated to run **in addition to**, and never as a substitute for, the mandatory
  `adversarial-reviewer`. Its result — the named unresolved terms, or an explicit
  noted skip when the harness offers no subagent dispatch at all — is recorded in
  step 6's `REVIEW READINESS` chat handoff (a new line in that block's specified
  shape), never silently. Behavioral anchor (per Testing Strategy): the
  context-denied dispatch was run once against RFC-0053 on 2026-06-30 and surfaced
  ~60 unresolved terms (e.g. `the sidecar` used before its gloss, `the gate arc`
  never defined, the seven self-coverage modules never enumerated, BLUF/ACH/SVPG
  unexpanded) — confirming the check emits a real cold-reader finding; the full
  output is in the PR description.
- [x] **AC4 — two new anti-patterns.** The Anti-patterns list gains (a) leaning
  on undefined sibling-RFC jargon / inherited vocabulary the cold reader can't
  resolve, and (b) a decision handoff too terse for the author to decide from
  (one-liner options with no trade-offs or consequences). Both entries are
  non-duplicative of the existing refuse list, and no prose in the skill states
  the list's cardinality — the count lives only in the list itself.
- [x] **AC5 — no frozen-decision surface changed.** The diff introduces no new
  RFC body section or header field, converts no existing structure, removes or
  weakens no RFC-0014 pre-handoff check — each load-bearing clause survives
  (semantics, not just the check name): citations *fetched* and must *actually
  contain* the claim; verify-before-you-assert *executed … never self-certified*;
  the `adversarial-reviewer` dispatch *mandatory* — and modifies neither
  `docs/CONVENTIONS.md` nor `docs/CHARTER.md`.
- [x] **AC6 — how-to guide synced.** `docs/guides/governance-extras/how-to/new-rfc.md`
  reflects the two reader-facing behavior changes: its research/de-risk step
  (Step 3) describes the decidable-in-chat decision handoff, and its pre-handoff
  gate step (Step 5) describes the no-context readability check — with no other
  drift introduced.
- [x] **AC7 — eval updated.** `evals/evals.json` gains coverage for both new
  behaviors as LLM-judged behavioral assertions on the skill's observable output:
  (a) an assertion on the existing draft-the-RFC eval that the produced RFC reads
  from zero prior context (coined terms/acronyms/back-references glossed on first
  use); and (b) a **new eval entry** whose prompt exercises the research/de-risk
  handoff (present the decisions for me to decide, don't draft yet) with
  assertions that each decision in the emitted block is self-contained — question
  + options-with-trade-offs + recommendation-with-why + cost-of-each. The
  pre-existing assertions are preserved; `evals/eval_queries.json` (trigger/
  activation only) is unchanged.
- [x] **AC8 — projection regenerated, tree clean, lints pass.** `make build-self`
  has been run; the regenerated projected new-rfc skill copies carry all four
  changes and `git status` shows no residual drift; `lint-packs` and
  `tools/lint-agent-artifacts.py` exit clean.
- [x] **AC9 — version + changelog.** `governance-extras` is bumped
  `0.4.0 → 0.5.0` in both `pack.toml` and `.claude-plugin/plugin.json`, and a
  `docs/product/changelog.md` `[Unreleased]` entry records the user-visible
  change.

## Assumptions

- Technical: edit point is the pack source
  (`packs/governance-extras/.apm/skills/new-rfc/{SKILL.md,assets/rfc.md}`) and
  `.claude/`+`.agents/` copies are generated via `make build-self`
  (source: docs/specs/new-rfc-readability/spec.md §Always-do; RFC-0014:87, read 2026-06-30).
- Technical: pack version lives in both `pack.toml` and `.claude-plugin/plugin.json`
  (both 0.4.0) and co-bumps; `build-self` refreshes the `marketplace.json`
  aggregation (source: grep of both files 2026-06-30; memory).
- Technical: the Tier-4 eval lives at `…/new-rfc/evals/evals.json` (one eval, an
  assertions list) and `eval_queries.json` (source: grep 2026-06-30).
- Process: two lint surfaces apply — `lint-packs` (source) and
  `tools/lint-agent-artifacts.py` (projection) (source: AGENTS.md §Code style; memory).
- Process: a user-visible skill prose change needs a `docs/product/changelog.md`
  `[Unreleased]` entry in the same PR (source: docs/product/changelog.md header, read 2026-06-30).
- Process: the how-to guide is a Living doc; drift closes in the same PR
  (source: RFC-0014:159; memory).
- Process: vehicle is a spec, not an RFC — these are additive readability/
  usability refinements that don't reverse a frozen RFC-0014/RFC-0054 decision,
  the B-narrow precedent (source: user confirmation 2026-06-30).
- Process: the no-context readability check is in scope and is a **separate,
  context-denied** subagent dispatched alongside the existing adversarial pass
  (source: user confirmation 2026-06-30).
- Process: version bump is MINOR (0.4.0 → 0.5.0) for new observable skill
  behavior (source: user confirmation 2026-06-30).
- Product: the change serves the RFC *author* (decidable handoff) and the cold
  *reviewer* (fresh-context readability), the two humans RFC-0054 named
  (source: user confirmation 2026-06-30).

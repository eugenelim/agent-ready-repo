# Plan: new-rfc, sized to its two humans

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

A single-PR prose + template change to one skill. Edit the two pack-source files
(`assets/rfc.md` for the template surface — D1 header, D2 section, D3 table; and
`SKILL.md` for the authoring procedure — D1 weight guidance + AC5 mapping, D2
drafting + REVIEW-READINESS-stays-chat, D3 table guidance, D4 guided intake step
+ renumber), then regenerate the projection with `make build-self` and close the
peripheral drift (how-to guide, version, changelog, eval). The riskiest part is
**not weakening any RFC-0014 gate check** while introducing weight-based
trimming — handled by treating the gate step as append/restructure-only and
diffing its load-bearing clauses against RFC-0014. Verification is goal-based
greps over source + projection, plus a manual read of the regenerated SKILL.md
for step-renumber coherence.

## Constraints

- **RFC-0054** — the accepted authority for all four changes (D1–D4) and the two
  resolved open questions (Reviewer brief above The ask, de-duplicated;
  weight→gate-trim mirrors work-loop light/full).
- **RFC-0014** — frozen; its five pre-handoff gate checks must all survive
  (Spec § Never do). This spec implements RFC-0054's revision of it, not an edit
  to RFC-0014 itself.
- **RFC-0025** — the light/full router model D1 borrows; the weight→gate-trim
  mapping mirrors it rather than inventing a new tiering.
- Self-hosting projection rules: edit pack source, never the `.claude/`/`.agents/`
  copies; `make build-self` regenerates them.

## Construction tests

Most construction tests live under **Tasks** below. Cross-cutting:

**Integration tests:** none beyond per-task greps — there is no executable code
in this change; the artifact is skill/template prose verified by grep + manual
read.
**Manual verification:** read the regenerated `.claude/skills/new-rfc/SKILL.md`
end-to-end and confirm the renumbered steps (D4 intake inserted before research)
flow coherently and the four changes are mutually consistent.

## Design (LLD)

Shape is `mixed` but the change carries no code design — it is documentation
surface. The only design decision worth recording:

### Design decisions

- **D4 intake is a new step *before* the existing research checkpoint, not a
  rewrite of it.** Insert the guided shape/intake as the step after "copy the
  template" and renumber the rest; the research-and-de-risk gate keeps its body
  verbatim. Rejected: folding intake into the research step — it would blur the
  offer-don't-force boundary and risk editing gate language. Traces to: AC4, AC6.
- **Weight trimming is described as *tier semantics in the gate step*, not a
  removal of checks.** The gate lists all five checks unconditionally; the weight
  tiers say how much ceremony each carries. Rejected: per-tier conditional check
  lists — they invite dropping a mandated check. Traces to: AC5, AC6.
- **`## Reviewer brief` is a distinct in-body section; `REVIEW READINESS` stays
  chat-only.** Two artifacts, two homes — the brief in the template, the
  readiness summary in the handoff. Traces to: AC2.

## Tasks

### T1: Template surface — `assets/rfc.md` carries D1 header, D2 section, D3 table

**Depends on:** none

**Tests:**
- `grep` `assets/rfc.md` for `Decision weight:` header field with the
  `light | standard | heavy` values + a cue comment. (AC1)
- `grep` `assets/rfc.md` for a `## Reviewer brief` heading positioned *above*
  `## The ask`, carrying the seven fields. (AC2)
- `grep` `assets/rfc.md`'s "The ask" for a Markdown table with header
  `ID | Question | Recommendation | Why | Decide by | Reviewer action`. (AC3)

**Approach:**
- Add the `- **Decision weight:**` line to the header block with a cue comment
  (default `standard`).
- Insert a `## Reviewer brief` section between the header block and `## The ask`,
  with commented field guidance for the seven fields.
- Replace the "Decisions requested: numbered" guidance in "The ask" with the
  six-column table form; keep BLUF + SCQA above it.

**Done when:** the three greps pass against `assets/rfc.md`.

### T2: Authoring procedure — `SKILL.md` D1/D2/D3/D4 + renumber

**Depends on:** none

**Tests:**
- `grep` SKILL.md for the Decision-weight instruction: right-sizes research +
  gate, defaults `standard`, suggested from work-loop risk triggers,
  author-overridable. (AC1)
- `grep` SKILL.md for the three-tier weight→gate-trim mapping (light/standard/
  heavy) with the trim semantics in AC5; confirm `light` keeps the **mandatory
  adversarial dispatch, re-run until clean** (trim is research depth + draft size,
  not the dispatch's required action). (AC5)
- `grep` SKILL.md for the Reviewer-brief drafting instruction + de-dup against
  The ask, AND the surviving "REVIEW READINESS … never an RFC body or template
  section" clause. (AC2)
- `grep` SKILL.md for the decisions-as-table instruction (replacing
  numbered-prose). (AC3)
- `grep` SKILL.md for the guided shape/intake step before the research
  checkpoint, marked offer-don't-force; confirm steps are renumbered. (AC4)
- Manual diff: the five pre-handoff gate checks' load-bearing clauses are
  unchanged vs. RFC-0014 § Drafting flow step 4. (AC6)

**Approach:**
- Add D4 guided shape/intake as a new numbered step after "copy template"; renumber
  the research checkpoint and all later steps.
- In the draft step, change "Decisions requested" guidance to the table; add the
  Reviewer-brief drafting instruction (above The ask, de-duplicated).
- Add the Decision-weight field guidance + the three-tier mapping (likely near
  step 2 / the draft step); keep the gate step's five checks verbatim, adding only
  the weight-trim framing.
- Leave the REVIEW READINESS block and its "chat-only, never a body section"
  clause untouched.

**Done when:** all greps pass and the gate-check load-bearing clauses diff clean
against RFC-0014.

### T3: Regenerate projection + lints

**Depends on:** T1, T2

**Tests:**
- `make build-self` then `git status` shows no residual drift. (AC8)
- The regenerated `.claude/skills/new-rfc/{SKILL.md,assets/rfc.md}` and
  `.agents/` copies carry all four changes (`grep`). (AC8)
- `lint-packs` and `tools/lint-agent-artifacts.py` exit clean. (AC9)

**Approach:**
- Run `make build-self`; if a sibling-worktree editable install masks local edits
  (memory: local make build-check uses site-packages), verify via the pack-source
  greps + `cd packages/agentbundle && pytest` and rely on CI as authoritative.
- Run both lint surfaces by hand.

**Done when:** clean tree after build-self; both lints pass; projection greps pass.

### T4: Sync the how-to guide

**Depends on:** T2

**Tests:**
- `docs/guides/governance-extras/how-to/new-rfc.md` reflects the guided
  shape/intake step and the four template changes; no unrelated drift
  (`git diff` scoped to the guide). (AC7)
- The guide's own `## Step N` headings are renumbered consistently after the
  intake step is inserted, and `grep "Step "` over the guide shows **no stale
  cross-reference** (e.g. a "see Step 5" that now points at the wrong step). (AC7)

**Approach:**
- Update the guide's step walk-through to add the intake step and mention the
  Decision-weight field, Reviewer brief, and decisions table; point at the skill
  block rather than re-enumerating it (memory: don't re-enumerate the list).
- The guide carries its own Step 1–6 numbering (Step 2 = the research phase);
  inserting intake before research renumbers Step 2 onward — fix the headings and
  every internal `Step N` cross-reference.

**Done when:** the guide describes the new procedure, its Step sequence is
renumbered, and no stale `Step N` reference remains.

### T5: Version bump + changelog + eval

**Depends on:** T1, T2

**Tests:**
- `governance-extras` is `0.4.0` in both `pack.toml` and
  `.claude-plugin/plugin.json` (`grep`). (AC9)
- `docs/product/changelog.md` has an `[Unreleased]` entry for the change. (AC9)
- `evals/evals.json` gains **three** assertions for the new criteria observable in
  a produced RFC (Decision-weight field present; Reviewer brief section present;
  decisions as a table), existing assertions intact (`git diff`). D4 intake is
  procedure not output → not an eval assertion. (AC9)

**Approach:**
- Bump `0.3.2 → 0.4.0` in `pack.toml` and `.claude-plugin/plugin.json`; let
  build-self refresh `marketplace.json` (memory: plugin.json drives marketplace
  aggregation).
- Add a changelog `[Unreleased]` entry naming the four changes.
- Extend the single eval's `assertions` array with three output-observable checks
  (Decision-weight field present; Reviewer brief section present; decisions as a
  table), keeping the existing six. Do **not** add an intake assertion — the eval
  grades the produced RFC, and intake leaves no trace in the output.

**Done when:** all three greps/diffs pass.

## Rollout

Pure documentation/skill-prose change. Delivery is big-bang on merge; fully
reversible (revert the PR). No infrastructure, no external-system integration.
Deployment sequencing: edit source → `build-self` → lints, all in one PR; the
version bump publishes on the next `governance-extras` release tag (a separate
decision, surfaced after merge).

## Risks

- **Local `make build-self` masks edits via the sibling-worktree editable
  install** (memory) → mitigate by trusting pack-source greps + CI as
  authoritative; don't conclude from a green local build alone.
- **Step renumber introduces a stale internal cross-reference** in SKILL.md
  ("see step 3") *and* in the how-to guide ("see Step 5") — both carry their own
  step numbering → grep for `step N` / `Step N` references in **both** files after
  renumbering and fix.
- **A weight-trim phrasing reads as licensing a dropped gate check** → keep the
  five checks listed unconditionally; the manual RFC-0014 diff (T2) is the guard.

## Changelog

- 2026-06-27: initial plan.

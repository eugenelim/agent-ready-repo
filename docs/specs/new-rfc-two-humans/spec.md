# Spec: new-rfc, sized to its two humans (RFC-0054 implementation)

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0054, RFC-0014
- **Brief:** none
- **Contract:** none
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

The `new-rfc` skill and its `assets/rfc.md` template serve their **two humans**
better: the *author* invoking the skill, and the *reviewer* consuming the
output. Four accepted changes from RFC-0054 land, each implementing one of that
RFC's decisions, without removing or weakening any pre-handoff gate check
RFC-0014 mandates:

- **D1 — `Decision weight` header field.** Both the template and the skill carry
  a `Decision weight: light | standard | heavy` header field. It right-sizes how
  much research depth and pre-handoff ceremony an RFC carries, borrowing
  `work-loop`'s light/full mental model; it defaults to `standard` (the
  omitted-field meaning) and the author picks it by consulting the same risk
  triggers `work-loop` uses — a prose heuristic, not a computed value.
- **D2 — `## Reviewer brief` section.** The template carries a top-of-doc
  `## Reviewer brief` orientation grid (Decision · Recommended outcome · Change
  if accepted · Affected surface · Stakes · Review focus · Not in scope),
  sitting *above* "The ask" and de-duplicated against it. The skill drafts it.
  The existing `REVIEW READINESS` handoff summary stays a chat-only artifact —
  it is not moved into the RFC body or template.
- **D3 — decisions as a table.** "The ask" → Decisions requested renders as a
  table (`| ID | Question | Recommendation | Why | Decide by | Reviewer action |`)
  rather than numbered prose, in both the template and the skill's guidance.
- **D4 — guided shape/intake before research.** The skill runs a guided
  shape/intake step *before* the research-and-de-risk checkpoint: when the
  author's intent is vague it asks a small set of framing questions and
  synthesizes a proposal frame for confirmation; when the ask is already
  well-specified it infers the frame and proceeds. It offers, never forces — no
  mandatory questionnaire. The downstream research gate is unchanged.

A reviewer reading the regenerated skill gets a coherent procedure; an author
gets ceremony that scales to the stakes and a guided way in. The change is
prose + template only — no new lint, hook, engine, dependency, or top-level
directory.

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
  in the same PR when the skill's described procedure changes.
- Preserve every RFC-0014 pre-handoff gate check (citation-integrity,
  verify-before-you-assert, per-subpoint backing, completeness checklist,
  mandatory `adversarial-reviewer` dispatch); right-sizing by weight changes how
  *much* ceremony a tier carries, never *whether* a mandated check runs when its
  tier reaches the gate.

### Ask first

- Any change beyond the four RFC-0054 decisions — a fifth template section, a
  header field RFC-0054 didn't authorize, or a flow change other than the
  shape/intake step. These escalate; they are not made here.
- Any change to the `evals.json` rubric that would assert on something other
  than the RFC's observable output (the eval grades produced RFCs, not the
  skill's internal procedure).

### Never do

- **Remove or weaken any check the RFC-0014 pre-handoff gate mandates.** The
  `light` tier trims ceremony (collapsed sections, one research sweep), but a
  citation that enters a `light` RFC is still fetched-and-confirmed, and the
  mandatory `adversarial-reviewer` dispatch is never dropped.
- **Move the `REVIEW READINESS` summary into the RFC body or template** — it
  stays a chat-only handoff artifact (the back door B-narrow closed stays
  closed; the `## Reviewer brief` is a *different*, in-body artifact).
- **Edit `docs/CONVENTIONS.md`** — RFC-0054 explicitly leaves §3 unchanged; any
  convention change is separately RFC-gated.
- Add a new lint, hook, engine, dependency, module, or top-level directory —
  RFC-0054 is prose + template only.

## Testing Strategy

This is a prose-guidance change to a skill + template (no code logic), so
verification is **goal-based** with a light **manual-QA read** of the built
artifact — the same shape as the shipped B-narrow spec:

- *Each accepted change landed in source and projection* — goal-based: `grep`
  each of the four changes in both the pack source and the regenerated
  `.claude/` + `.agents/` copies. (AC1–AC4, AC8)
- *The weight→gate-trim mapping is stated and mirrors work-loop light/full* —
  goal-based: `grep` SKILL.md for the three tiers and their trim semantics;
  manual diff against `work-loop` SKILL.md's light/full description. (AC5)
- *No RFC-0014-mandated gate check was removed or weakened* — goal-based: `grep`
  for each check's **load-bearing clause** (not just its name) in the gate step,
  plus a manual diff of the gate's check bodies against RFC-0014 § Drafting flow
  step 4. (AC6)
- *The `REVIEW READINESS` block stays chat-only* — goal-based: `grep` confirms
  the "never an RFC body or template section" clause survives and no
  `## Reviewer brief` text leaked into the readiness block. (AC2)
- *How-to guide synced* — goal-based: the guide reflects the new shape/intake
  step and the four template changes; no other drift. (AC7)
- *Version + changelog + eval + lints* — goal-based: `governance-extras` is
  `0.4.0` in both manifest files; a changelog `[Unreleased]` entry exists; the
  Tier-4 eval asserts on the three RFC-output-observable criteria (Decision weight
  field, Reviewer brief, decisions table; D4 intake excluded — procedure, not
  output); `lint-packs` and `tools/lint-agent-artifacts.py` pass; `make build-self`
  leaves a clean tree. (AC9)
- *The projected skill reads coherently end-to-end* — manual QA: read the
  regenerated `.claude/skills/new-rfc/SKILL.md` and confirm the new guidance is
  consistent with the surrounding procedure and the renumbered steps flow. (AC1–AC5)

## Acceptance Criteria

- [x] **AC1 — `Decision weight` field (D1).** `assets/rfc.md` carries a
  `- **Decision weight:** light | standard | heavy` header field with a cue
  comment (default `standard`), and `SKILL.md` instructs the author to **pick** it
  by consulting `work-loop`'s risk triggers as a **prose heuristic the author
  applies — not a value the skill computes**, stating it right-sizes research depth
  + the pre-handoff gate and defaults to `standard` when omitted. (No engine or
  computed field — consistent with the "no new engine" boundary.)
- [x] **AC2 — `## Reviewer brief` section (D2).** `assets/rfc.md` carries a
  `## Reviewer brief` section *above* `## The ask`, with the seven fields
  (Decision · Recommended outcome · Change if accepted · Affected surface ·
  Stakes · Review focus · Not in scope); `SKILL.md` instructs drafting it and
  de-duplicating it against "The ask". `SKILL.md` still states the
  `REVIEW READINESS` summary is emitted **to chat at handoff, never an RFC body
  or template section** (the B-narrow back door stays closed).
- [x] **AC3 — decisions as a table (D3).** `assets/rfc.md`'s "The ask"
  Decisions-requested guidance is a table with columns `ID | Question |
  Recommendation | Why | Decide by | Reviewer action`; `SKILL.md` step describing
  "Decisions requested" specifies the table form (replacing the numbered-prose
  instruction).
- [x] **AC4 — guided shape/intake step (D4).** `SKILL.md` carries a guided
  shape/intake step *before* the research-and-de-risk checkpoint: ask framing
  questions and synthesize a proposal frame for confirmation when intent is
  vague; infer and proceed when the ask is well-specified. It is explicitly
  **offer-don't-force** (no mandatory questionnaire), and the downstream research
  gate is unchanged. Subsequent steps are renumbered consistently.
- [x] **AC5 — weight→gate-trim mapping (D1 detail).** `SKILL.md` states the
  per-tier mapping mirroring `work-loop` light/full, where the trim is *the depth
  of research and the size of the draft*, never the required action of a mandated
  gate check: `light` = one research sweep + sections collapse to one-liners, run
  over a smaller draft — but the full pre-handoff gate still runs, including
  citation-integrity on any claim that enters and the **mandatory
  `adversarial-reviewer` dispatch, re-run until clean**; `standard` = full
  per-subpoint research + full gate as RFC-0014 specifies (the default); `heavy`
  = full research + full gate + a mandatory de-risk spike + explicit Approver
  sign-off (no silent default). No tier drops or weakens a gate check (see AC6).
- [x] **AC6 — gate checks preserved (semantics, not just names).** All five
  RFC-0014 pre-handoff checks remain present and executed in `SKILL.md`
  (citation-integrity, verify-before-you-assert, per-subpoint backing,
  completeness checklist, mandatory `adversarial-reviewer` dispatch); none is
  removed or softened. Verified by **each** check's **load-bearing clause**
  surviving — all five, not a subset: citations *fetched* and must *actually
  contain* the claim; verify-before-you-assert *executed and recorded, never
  self-certified*; per-subpoint backing stays *MECE along a stated axis and
  prior-art-grounded, not invented*; the completeness checklist's *YES/NO items
  survive verbatim*; and the `adversarial-reviewer` dispatch stays *mandatory,
  re-run until clean*. Weight-based trimming reduces research depth and draft
  size, never a mandated check at its tier.
- [x] **AC7 — how-to guide synced.** `docs/guides/governance-extras/how-to/new-rfc.md`
  reflects the new guided shape/intake step and the four template changes
  (Decision weight, Reviewer brief, decisions table, intake), with no unrelated
  drift. The guide carries its **own** `## Step N` numbering; inserting the intake
  step renumbers that sequence, so the guide's Step headings are renumbered
  consistently and **no stale `Step N` cross-reference remains** (grep the guide
  for `Step ` references after the edit).
- [x] **AC8 — projection regenerated.** `make build-self` has been run; the
  regenerated projected `new-rfc` skill + template copies carry all four changes
  and `git status` shows no residual drift (the clean tree after build-self is
  the authoritative gate, independent of how many adapter copies the build emits).
- [x] **AC9 — version + changelog + eval + lints.** `governance-extras` is bumped
  `0.3.2 → 0.4.0` in both `pack.toml` and `.claude-plugin/plugin.json`; a
  `docs/product/changelog.md` `[Unreleased]` entry is added; the Tier-4 eval
  (`evals/evals.json`) gains assertions only for the new criteria **observable in
  a produced RFC** — a `Decision weight` header field is present; a `## Reviewer
  brief` orientation section is present above "The ask"; the decisions are rendered
  as a table — while keeping its existing assertions intact. (D4's guided intake is
  a property of the skill's *procedure*, not of any produced RFC, so it is **not**
  an eval assertion — per the Ask-first boundary that the eval grades observable
  output only.) `lint-packs` and `tools/lint-agent-artifacts.py` pass.

## Assumptions

- Technical: edit point is `packs/governance-extras/.apm/skills/new-rfc/{SKILL.md,assets/rfc.md}`
  and `.claude/`+`.agents/` copies are generated via `make build-self`
  (source: both files read 2026-06-27; RFC-0014 §Migration).
- Technical: `governance-extras` version lives in `pack.toml` and
  `.claude-plugin/plugin.json` (both `0.3.2`) and co-bumps; `build-self`
  refreshes the `marketplace.json` aggregation (source: grep 2026-06-27; memory).
- Technical: the Tier-4 eval is `packs/governance-extras/.apm/skills/new-rfc/evals/evals.json`,
  one eval grading the produced RFC's observable output (source: read 2026-06-27).
- Process: this implements accepted RFC-0054 (merged #428); both RFC open
  questions are resolved per their recommended defaults — Reviewer brief above
  The ask de-duplicated, weight→gate-trim mirrors work-loop light/full
  (source: docs/rfc/0054-new-rfc-two-humans.md; user confirmation 2026-06-27).
- Process: a user-visible skill prose change needs a `docs/product/changelog.md`
  `[Unreleased]` entry; two lint surfaces apply — `lint-packs` (source) and
  `tools/lint-agent-artifacts.py` (projection) (source: changelog header read
  2026-06-27; memory).
- Process: the how-to guide is a Living doc; drift closes in the same PR
  (source: RFC-0014 §Migration; memory).
- Product: version bump is MINOR `0.3.2 → 0.4.0` for new template/skill surface
  (source: user confirmation 2026-06-27; RFC-0054 follow-on artifacts).

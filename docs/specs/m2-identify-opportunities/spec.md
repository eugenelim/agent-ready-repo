# Spec: m2-identify-opportunities

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** RFC-0064 (M2 · Strategic Shaping; D9 typed shaping queue entries); known-unknowns resolved 2026-07-18. Sub-RFC pe-pack-strategic-shaping (RFC-00XX) not yet accepted — this spec proceeds under resolved constraints and may require minor revision on sub-RFC acceptance.
- **Brief:** none
- **Discovery:** none
- **Contract:** none — prompt-only skill (Charter Principle 3); no machine interface
- **Shape:** mixed

> **Spec contract:** this document defines what "done" means. The implementing
> PR must match this spec, or update it. Verification must be derivable from it.

## Objective

A product engineer or PM working a shaping queue item runs `identify-opportunities`
and gets an **Opportunity Assessment** typed artifact that exhaustively surfaces
functional, emotional, and social jobs users are trying to get done, scores each
on importance and satisfaction using the Ulwick formula, and produces a ranked
opportunity list that shapes the `diverge-solutions` brief.

Input is free-form (a problem description, a shaping queue slug, or a raw topic
area). When a `situation-framing.md` artifact already exists at the resolved
shaping path for the same slug, the skill reads it for structured context
(finding type, Wardley assessment, recommended entry point) without requiring it.
Output lands at `<output_dir>/shaping/<slug>/opportunity-assessment.md` via the
three-tier config procedure used across all M2 shaping skills.

This is step 2 of the PE six-step shaping sequence (`frame-situation` →
`identify-opportunities` → `diverge-solutions` → validate → `place-bet` →
`map-capabilities`). It does not produce a brief — that is `place-bet` +
`author-brief`'s responsibility.

## Boundaries

The three-tier guard that keeps an implementing agent inside the lines.
*Always do* applies without asking; *Ask first* requires human sign-off
before proceeding; *Never do* is a hard rule, even under time pressure.

### Always do

- **Elicit context before surfacing jobs when input is too thin** — a one-word
  topic with no `situation-framing.md` is underdetermined; ask for the problem
  area, the user population, and what drives the current pain before beginning
  job discovery. Do not fabricate job tables from underdetermined input.
- **Surface all identified jobs exhaustively** in each tier (functional /
  emotional / social) without a preset floor or ceiling. No job is silently
  dropped; scores drive prioritization, not list capping.
- **Score every job** on importance (1–10) and satisfaction (1–10). Derive the
  opportunity score via the Ulwick formula: `importance + max(importance −
  satisfaction, 0)`. State the formula once in the artifact for reader
  transparency. Label agent-estimated ratings explicitly when inferred from
  context rather than supplied by the PE.
- **Rank all jobs across all three tiers** by opportunity score; surface the
  highest-scoring jobs as the top-opportunities list — the recommended inputs
  for `diverge-solutions`. Jobs with equal scores are listed in encounter order.
- **Read `situation-framing.md` opportunistically** — check
  `<output_dir>/shaping/<slug>/situation-framing.md` before beginning job
  elicitation; if present, extract finding type, Wardley assessment summary,
  and recommended entry point as elicitation context; if absent, proceed on
  free-form input only without blocking.
- **Emit `opportunity-assessment.md`** at
  `<output_dir>/shaping/<slug>/opportunity-assessment.md`, using
  `assets/opportunity-assessment-template.md` as the artifact shape. Include
  stable marker (`type: opportunity-assessment`), functional / emotional / social
  job tables with importance, satisfaction, and opportunity scores, a ranked
  top-opportunities list, and a "Step 3 readiness" section when `diverge-solutions`
  is absent.
- **Resolve the write path via config-driven three-tier procedure**
  (repo-scope `agentbundle-layout.toml [product]` → user-scope →
  two-branch elicitation). Realpath-expand and symlink-resolve; reject any `..`
  escape and any symlink chain that exits the intended root. Surface the resolved
  absolute path before writing.
- **Degrade cleanly when `diverge-solutions` is absent** — add a "Step 3
  readiness" section to the artifact naming the missing skill and describing
  what step 3 provides; artifact emission continues unblocked.

### Ask first

- Before accepting a user-supplied phrase as a job when it reads as a solution
  rather than a job — confirm the job framing is solution-independent before
  recording it.
- Before running step-2 job identification on an input that already carries a
  committed bet — if the topic reads as already-decided (downstream of
  `place-bet`), flag the altitude and offer to route to a different step.
- Before overwriting an existing `opportunity-assessment.md` at the resolved
  slug path — surface the existing file and confirm before overwriting.
- Before adding a second typed artifact to this skill.
- Before any write path that resolves outside the repo tree or via a
  realpath-escaped symlink.

### Never do

- **Never** write to `workspace.toml` directly.
- **Never** write to a literal hardcoded path — always resolve via the
  three-tier config procedure; `docs/product/` is the designed default, not
  a constant.
- **Never** silently cap the job list — if the input implies more jobs than a
  comfortable table, surface them all; scoring drives prioritization.
- **Never** produce a brief — `place-bet` + `author-brief` own that hand-off.
- **Never** exceed 100 lines in `SKILL.md`.
- **Never** ship an engine, script, runtime hook, or validator in this skill.

## Testing Strategy

This is a prompt-only skill (Charter Principle 3) — no compressible invariant
logic. Verification is goal-based for structure and manual-QA for behavior.

- **Skill file and lint gates: goal-based.** File exists at the conventional
  path, `tools/lint-skill-spec.py` passes, `lint-packs` passes, <100 lines,
  valid frontmatter.
- **Template file: goal-based.** `assets/opportunity-assessment-template.md`
  exists with frontmatter fields (`type`, `slug`, `date`, `source`), three
  job tables, a ranked top-opportunities section, and the Ulwick formula line.
- **Path safety (AC10): goal-based grep.** `grep -F "realpath"` and
  `grep -F ".."` (or equivalent reject phrase) on SKILL.md body confirm the
  reject-`..`/symlink-resolution prose is present.
- **Skill behavior (job elicitation, scoring, ranking, artifact emission):
  manual QA.** Two live runs exercised in the implementing PR: one on the
  worked-example topic, one on a second distinct topic — recording both
  artifacts demonstrates slug-derivation, no-collision, and exhaustive
  job coverage (AC4–AC9).
- **Opportunistic-read branch (AC3) and degrade branch (AC11): goal-based
  grep.** Pinned assertions (branch-unique phrases):
  AC3: `grep -F "proceed on free-form input"` on SKILL.md body (≥1 match);
  AC11: `grep -F "Step 3 readiness"` on SKILL.md body (≥1 match).
  A count-only or filename-token grep would pass vacuously; these phrases only
  exist when the branch prose exists.
- **Diátaxis guide: goal-based for file existence, manual QA for accuracy.**
  Guide at `docs/guides/product-engineering/how-to/identify-opportunities.md`;
  reads accurately against the shipped skill (review recorded in PR).
- **Projection: goal-based.** `lint-packs`, `validate`, and `build` exit 0.
  Adopter-cleanliness verified by grep over the SKILL body (no RFC-NNNN, no
  `agent-ready-repo`). `make build-self` is not run — the PE pack is
  user-scope and excluded from `_DEFAULT_SELF_HOST_PACKS`.

## Acceptance Criteria

- [x] **AC1.** `identify-opportunities` ships at
  `packs/product-engineering/.apm/skills/identify-opportunities/SKILL.md`
  — <100 lines, valid frontmatter, passes `tools/lint-skill-spec.py` and
  `lint-packs`.

- [x] **AC2.** A template ships at
  `packs/product-engineering/.apm/skills/identify-opportunities/assets/opportunity-assessment-template.md`
  with: YAML frontmatter (`type: opportunity-assessment`, `slug`, `date`,
  `source` — where `source` records `situation-framing` when a prior
  situation-framing artifact seeded the run, or `free-form` otherwise);
  three job tables (functional / emotional / social) each with columns for
  job description, importance (1–10), satisfaction (1–10), and opportunity
  score; a ranked top-opportunities section; and one line stating the Ulwick
  formula.

- [x] **AC3.** The skill accepts free-form input (problem description, shaping
  queue topic, or raw opportunity area) as its primary entry point. When
  `<output_dir>/shaping/<slug>/situation-framing.md` exists, the skill reads
  it for context; when absent, the skill proceeds on free-form input only
  without blocking. The SKILL.md body contains explicit prose specifying the
  if-absent branch (goal-based grep: `grep -F "proceed on free-form input"`).

- [x] **AC4.** The skill surfaces all identified **functional jobs** — what the
  user is trying to accomplish. In the worked example, the functional tier
  contains ≥2 distinct entries. Exhaustive coverage beyond the worked example
  is verified by manual QA judgment.

- [x] **AC5.** The skill surfaces all identified **emotional jobs** — how the
  user wants to feel or avoid feeling. In the worked example, the emotional
  tier contains ≥2 distinct entries. Exhaustive coverage beyond the worked
  example is verified by manual QA judgment.

- [x] **AC6.** The skill surfaces all identified **social jobs** — how the user
  wants to be perceived by others. In the worked example, the social tier
  contains ≥2 distinct entries. Exhaustive coverage beyond the worked example
  is verified by manual QA judgment.

- [x] **AC7.** Every job (across all three tiers) is scored on importance (1–10)
  and satisfaction (1–10). The opportunity score is derived as
  `importance + max(importance − satisfaction, 0)` (Ulwick formula), stated
  once in the artifact. Agent-estimated ratings are labelled as such when not
  PE-confirmed.

- [x] **AC8.** The artifact ranks all jobs by opportunity score and surfaces a
  top-opportunities list — the highest-scoring jobs regardless of tier — as
  the recommended focus inputs for `diverge-solutions`. Jobs with equal scores
  are listed in encounter order.

- [x] **AC9.** The skill emits `<output_dir>/shaping/<slug>/opportunity-assessment.md`
  with stable marker `type: opportunity-assessment`. The slug is derived from
  the input topic or carried from the `situation-framing.md` slug field. A
  second run on a different topic derives a different slug and writes to a
  different path; no collision. A re-run on the same slug confirms before
  overwriting an existing artifact (per Ask-first boundary).

- [x] **AC10.** The skill resolves the write path via the config-driven
  three-tier procedure (repo-scope → user-scope → two-branch elicitation);
  realpath-expands and symlink-resolves the path; rejects `..` escapes and
  any symlink chain that exits the intended root; surfaces the resolved
  absolute path before writing. The SKILL.md body contains explicit prose
  for the reject-`..`/realpath step (goal-based grep: `grep -F "realpath"` or
  equivalent reject phrase, ≥1 match).

- [x] **AC11.** When `diverge-solutions` is not detected in the available
  skills, the skill adds a "Step 3 readiness" section to the artifact naming
  the missing skill and describing what step 3 provides; artifact emission
  continues unblocked. The SKILL.md body contains explicit prose specifying
  this degrade behavior (goal-based grep: `grep -F "Step 3 readiness"`).

- [x] **AC12.** A worked example ships at
  `packs/product-engineering/.apm/skills/identify-opportunities/examples/`
  demonstrating the happy path: free-form problem area → functional /
  emotional / social job tables (≥2 entries per tier) with scores → ranked
  top opportunities → `opportunity-assessment.md` artifact. Adopter-clean
  (no RFC-NNNN, no `agent-ready-repo` references).

- [x] **AC13.** A Diátaxis how-to guide ships at
  `docs/guides/product-engineering/how-to/identify-opportunities.md` covering:
  when to run `identify-opportunities` (step 2 of the shaping sequence or
  standalone); how to seed job elicitation from a `situation-framing.md`;
  how to interpret and act on the opportunity score output.

- [x] **AC14.** `lint-packs`, `validate`, `build`, and the `packages/agentbundle`
  pack/contract tests exit 0. Grep over SKILL.md body confirms no
  adopter-facing internal-catalogue references. `make build-self` is not run
  (PE pack is user-scope, excluded from `_DEFAULT_SELF_HOST_PACKS`, confirmed
  in plan).

## Assumptions

- **A1.** RFC-00XX · pe-pack-strategic-shaping has not been accepted. This spec
  proceeds under boundary decisions already resolved in RFC-0064 (2026-07-18);
  minor revision may be required on sub-RFC acceptance. (source:
  `docs/specs/m2-frame-situation/spec.md` A1; `docs/rfc/0064-ini-001-ai-native-ecosystem.md`)
- **A2.** The PE six-step sequence is anchored in RFC-0064 and stable enough
  to name in the skill body without the sub-RFC.
- **A3.** The Ulwick formula (`importance + max(importance − satisfaction, 0)`)
  is the canonical opportunity scoring method for this skill; the skill states it
  once in the artifact so Ulwick-unfamiliar adopters can follow. (source: user
  confirmation 2026-07-21)
- **A4.** Job surfacing is exhaustive — all identified jobs per tier, no preset
  cap — with scores driving prioritization. (source: user confirmation 2026-07-21)
- **A5.** A template file ships at `assets/opportunity-assessment-template.md`
  alongside SKILL.md. (source: user confirmation 2026-07-21)
- **A6.** Free-form input is the primary entry point; reading `situation-framing.md`
  from the same slug path is opportunistic, not required. (source: user confirmation
  2026-07-21)
- **A7.** `docs/guides/product-engineering/how-to/` exists; `identify-opportunities.md`
  does not yet exist. (source: `ls docs/guides/product-engineering/how-to/`,
  2026-07-21)
- **A8.** `workspace.toml` write-back is the `capture-work` front door's
  responsibility; this skill does not write to `workspace.toml`. (source:
  `docs/specs/m2-frame-situation/spec.md` A5; RFC-0064 Amendment #3)

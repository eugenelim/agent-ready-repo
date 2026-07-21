# Plan: m2-identify-opportunities

- **Spec:** [`spec.md`](spec.md)
- **Status:** Done <!-- Drafting | Executing | Done -->

> **Plan contract:** this is the implementation strategy. Unlike the spec, this
> document is allowed to change as you learn. When it changes substantially
> (a different approach, not just a re-ordering), note why in the changelog
> at the bottom.

## Approach

Four-task sequential build: SKILL.md + template first (the adopter-facing
deliverable), worked example second (validates behavior and produces the PR
transcript), how-to guide third, and a gates sweep last. Tasks T2 and T3 can
run in parallel after T1.

The riskiest part is staying under 100 lines in SKILL.md while covering
exhaustive-job elicitation, Ulwick scoring, opportunistic-read, and the degrade
branch. Mitigation: keep procedure steps to one sentence each; reference the
template for artifact shape rather than inlining it; calibrate against
frame-situation/SKILL.md (72 lines).

No new module, no new dependency, no `workspace.toml` changes. The PE pack
is user-scope and excluded from `_DEFAULT_SELF_HOST_PACKS`
(`packages/agentbundle/agentbundle/build/self_host.py` lines 94–98);
`make build-self` is not run.

## Constraints

- RFC-0064 (M2 ACs; D9 shaping queue entry types)
- Charter Principle 3 — prompt-only; no engine, script, or runtime hook
- SKILL.md hard cap: <100 lines (`docs/specs/m2-frame-situation/spec.md` Never-do)
- Write-path: three-tier config procedure (`frame-situation/SKILL.md` precedent)
- Adopter-clean: no RFC-NNNN, no `agent-ready-repo` references in SKILL.md body or example

## Construction tests

**Integration tests:** none — skill is prompt-only with no cross-component logic.

**Manual verification:** run `identify-opportunities` twice — once against
the T2 worked-example topic and once against a second distinct topic. Record
both artifact outputs in the PR description. This covers the end-to-end happy
path (AC3, AC4–AC8) and slug-derivation / no-collision (AC9).

## Design (LLD)

### Design decisions

- **Ulwick formula over simpler alternatives** — matches RFC-0064 "JTBD opportunity
  score as portfolio handoff format"; one formula stated in the artifact is the
  transparency contract. Traces to: AC7.
- **Opportunistic read (not required)** — the chain is not forced to be linear;
  a PE starting at step 2 directly must not be blocked by a missing step-1
  artifact. Traces to: AC3.
- **Template file (`assets/opportunity-assessment-template.md`)** — gives adopters
  a hand-authored baseline and a consistent shape across runs; mirrors
  `frame-intent/assets/intent-template.md`. Traces to: AC2.
- **Exhaustive jobs, scores drive prioritization** — a capped list hides real
  opportunities; tables absorb depth cheaply without verbose prose. Traces to:
  AC4–6, AC8.

### Behavior & rules

1. **Slug resolution.** If input names a shaping queue slug, use it directly;
   otherwise derive from the topic noun phrase (kebab-case).
2. **Opportunistic read.** Check `<output_dir>/shaping/<slug>/situation-framing.md`;
   if present, extract `finding-type`, Wardley summary, and `shaping-entry` as
   elicitation context; if absent, proceed on free-form input.
3. **Elicitation order.** Functional → emotional → social. Complete each tier
   before scoring to avoid anchoring job discovery on early scores.
4. **Rating discipline.** Importance and satisfaction are stated explicitly by
   the PE or derived from context and labelled as agent-estimated. Never silently
   invent a rating.
5. **Degrade.** Detect `diverge-solutions` in available skills; if absent, append
   "Step 3 readiness" before closing.

## Tasks

### T1: SKILL.md + template

**Depends on:** none

**Touches:** `packs/product-engineering/.apm/skills/identify-opportunities/`

**Tests:**
- `wc -l SKILL.md` ≤ 100 — AC1
- `tools/lint-skill-spec.py` exits 0 — AC1
- `assets/opportunity-assessment-template.md` exists; frontmatter contains `type`,
  `slug`, `date`, `source`; three job tables present; ranked top-opportunities
  section present; Ulwick formula line present — AC2
- `grep -F "situation-framing"` on SKILL.md body returns ≥1 match — AC3
- `grep -F "Step 3 readiness"` on SKILL.md body returns ≥1 match — AC11
- `grep -E "RFC-[0-9]{4}|agent-ready-repo"` on SKILL.md body returns 0 matches — AC14

**Approach:**
- Author `packs/product-engineering/.apm/skills/identify-opportunities/SKILL.md`
  with: YAML frontmatter (name, description); `## When to invoke` (step-2 context,
  solution-independent job check, altitude note); `## Procedure` (9 steps: slug
  resolution, opportunistic `situation-framing.md` read, functional job elicitation,
  emotional job elicitation, social job elicitation, Ulwick scoring per job, rank
  + top-opportunities list, three-tier write-path resolution with realpath + reject
  `..` + surface path before write, artifact emit using template + Step 3 readiness
  degrade); `## Anti-patterns to refuse`.
- Author `assets/opportunity-assessment-template.md` with YAML frontmatter block,
  three markdown tables (functional / emotional / social — columns: job, importance,
  satisfaction, opportunity score), a ranked top-opportunities section, and one
  line: `Opportunity score = importance + max(importance − satisfaction, 0)`.
- Run `wc -l SKILL.md`; trim if over 100.

**Done when:** SKILL.md ≤100 lines, `lint-skill-spec.py` exits 0, template exists
with correct shape, both grep assertions match, adopter-clean grep returns 0.

### T2: Worked example

**Depends on:** T1

**Touches:** `packs/product-engineering/.apm/skills/identify-opportunities/examples/`

**Tests:**
- Example file exists in `examples/` — AC12
- `grep -E "RFC-[0-9]{4}|agent-ready-repo"` on example returns 0 matches — AC12 adopter-clean
- Example contains three job-tier tables and a top-opportunities section

**Approach:**
- Choose an adopter-clean problem area (not INI-002 or catalogue-internal).
- Write `examples/opportunity-assessment-worked-example.md` showing the happy
  path: free-form input → functional / emotional / social job tables with
  importance, satisfaction, and opportunity scores → ranked top-opportunities →
  the resulting `opportunity-assessment.md` artifact quoted inline.

**Done when:** example file present, adopter-clean, tables and top-opportunities
section present, and a live skill run against the example input has been
executed with the resulting artifact recorded in the PR description.

### T3: How-to guide

**Depends on:** T1

**Touches:** `docs/guides/product-engineering/how-to/identify-opportunities.md`

**Tests:**
- File exists at path — AC13
- Guide covers three required topics: when to run (step 2 or standalone),
  seeding from `situation-framing.md`, interpreting opportunity score output

**Approach:**
- Author `docs/guides/product-engineering/how-to/identify-opportunities.md`
  in Diátaxis how-to shape: goal-first, no JTBD theory, steps and decision
  points only. Section structure: "When to use this skill" (step-2 context,
  standalone), "Seeding from a situation-framing artifact" (what fields to
  look for, what to do when absent), "Interpreting the output" (score
  thresholds, how to hand off to `diverge-solutions`).

**Done when:** file exists and covers the three required topics.

### T4: Gates

**Depends on:** T1, T2, T3

**Tests:**
- `lint-packs` exits 0 — AC14
- `validate` exits 0 — AC14
- `build` exits 0 — AC14
- `packages/agentbundle` pack/contract tests exit 0 — AC14

**Approach:**
- Run `make lint-packs validate build` from repo root.
- Run pack/contract tests for `packages/agentbundle`.
- Grep SKILL.md body for adopter-clean violations; fix any found.

**Done when:** all gate commands exit 0; adopter-clean grep returns 0.

## Rollout

Prompt-only skill and documentation only. Ships as part of the PE pack
user-scope install. No infrastructure, no migrations, no `make build-self`
step (PE pack excluded from `_DEFAULT_SELF_HOST_PACKS`).

## Risks

- **SKILL.md line budget:** covering exhaustive-job + scoring + degrade +
  config-resolution in <100 lines may require multiple trim passes. Mitigation:
  one sentence per procedure step; cross-reference template for artifact shape.
  Calibrate against frame-situation SKILL.md (72 lines).
- **Agent-estimated ratings:** in a fully agent-driven run the PE may not supply
  importance/satisfaction ratings; unlabelled estimates could mislead. Mitigation:
  the "Always do" and "Rating discipline" rule require explicit labelling; the
  "Ask first" boundary covers accepting pre-rated inputs.

## Changelog

- 2026-07-21: initial plan

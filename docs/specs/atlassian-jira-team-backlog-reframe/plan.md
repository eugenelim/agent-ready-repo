---
name: atlassian-jira-team-backlog-reframe-plan
description: "Phase 2D implementation plan — Lane B (jira-team-status), Lane C (jira-story-triage), Lane D (integration owner)"
---

**Feature:** atlassian-jira-team-backlog-reframe
**Status:** Shipped

# Plan: Atlassian Phase 2D — Jira Team Backlog Reframe

## Tasks

### Lane A — Contract inventory (read-only; pre-work)

**Task A1 — Read existing skill sources and produce mismatch matrix**
Depends on: none
Verification mode: goal-based check (mismatch matrix produced; gaps enumerated)

Done when: mismatch matrix identifying gaps between spec decisions (D1–D5) and existing skill content is complete and reviewed.

### Lane B — jira-team-status

**Task B1 — Rewrite SKILL.md**
Depends on: Lane A complete
Verification mode: goal-based check (build-check passes; description ≤ 1024 chars; frontmatter version = 2.0.0)

Done when: SKILL.md reflects new team readiness rule (D2), header-block-first output structure (D3), paginate-to-completeness Stage 3 (D4), stage-by-stage lifecycle, cross-cutting flags, §6 recommendations, §7 follow-up actions; `make build-check` passes; description ≤ 1024 chars.

**Task B2 — Update eval_queries.json**
Depends on: Task B1
Verification mode: goal-based check (no duplicate queries; all positives cover D1/D2 natural language; negatives include cross-skill near-misses)

Done when: eval_queries.json contains natural team-backlog positives, explicit agent-readiness lens positives, and near-miss negatives (triage phrases, personal-assignment queries, one-issue updates).

**Task B3 — Create evals.json (16 fixtures)**
Depends on: Task B1
Verification mode: goal-based check (16 fixtures present; weak-output fixtures marked as negative evals)

Done when: 16 fixtures cover one-project/one-page, multi-project, pagination, ambiguous scope, permission-limited, no-sprint, empty backlog, Blocked+Unassigned overlap, unassigned ready work, missing story detail, explicit agent lens, stand-up, and four weak-output anti-patterns.

**Task B4 — Rewrite references/examples.md**
Depends on: Task B1
Verification mode: goal-based check (5 examples present; all show header block before sections)

Done when: 5 examples show updated output format (header block first, new section labels, coverage disclosure, explicit agent lens, stand-up).

**Task B5 — Update manifest.json**
Depends on: Task B1
Verification mode: goal-based check (version = 2.0.0)

Done when: manifest version is 2.0.0; description accurately reflects new skill behaviour.

### Lane C — jira-story-triage

**Task C1 — Rewrite SKILL.md**
Depends on: Lane A complete
Verification mode: goal-based check (build-check passes; five-question bar labeled as agent-execution readiness; write-confirmation loop complete; protected fields listed)

Done when: SKILL.md labels five-question bar as agent-execution readiness (D1); per-item output includes unresolved human questions column; Stage 9 surfaces unresolved questions before drafting; write payload shows old/new values, protected fields, total writes; partial write failure recovery described; paginate-to-completeness in Stage 3.

**Task C2 — Update eval_queries.json**
Depends on: Task C1
Verification mode: goal-based check (symmetric near-miss negatives; team-status explicit-lens phrases are false-negatives here)

Done when: eval_queries.json contains readiness-review positives, draft-only and confirmed-write positives, and near-miss negatives including team-status explicit-lens phrases.

**Task C3 — Create evals.json (9 fixtures)**
Depends on: Task C1
Verification mode: goal-based check (9 fixtures present; all cover key scenarios)

Done when: 9 fixtures cover draft-only triage, confirmed write, protected fields enforcement, partial failure, unresolved human questions, expected readiness after draft, stand-up redirect near-miss, hidden-write anti-pattern, agent-bar-as-team-bar anti-pattern.

**Task C4 — Rewrite references/examples.md**
Depends on: Task C1
Verification mode: goal-based check (5 examples present)

Done when: 5 examples cover draft-only triage, draft→confirm→write loop, unresolved human questions blocking improvement, confirmed write with protected fields, partial write failure with recovery.

**Task C5 — Update manifest.json**
Depends on: Task C1
Verification mode: goal-based check (version = 2.0.0)

Done when: manifest version is 2.0.0; description accurately reflects updated skill behaviour.

### Lane D — Integration owner

**Task D1 — Update pack.toml**
Depends on: B1, C1
Verification mode: goal-based check (version = 0.7.0; starter-prompt is team-oriented)

Done when: pack.toml version = 0.7.0; starter-task/prompt/expected-result/next-action reflect new team-oriented first-value prompt.

**Task D2 — Update plugin.json**
Depends on: Task D1
Verification mode: goal-based check (version = 0.7.0)

**Task D3 — README minimum accuracy corrections**
Depends on: B1, C1
Verification mode: goal-based check (README describes both skills accurately; does not promise features not in spec)

**Task D4 — Changelog [Unreleased] entry**
Depends on: B1, C1
Verification mode: goal-based check ([Unreleased] entry present with spec link)

**Task D5 — Run FORCE=1 make build-self + build-check**
Depends on: D1, D2, D3, D4
Verification mode: goal-based check (make build-check exits 0)

Done when: `FORCE=1 make build-self` succeeds; `make build-check` exits 0; no lint warnings for any changed skill; marketplace.json projection is up to date.

### Review

**Task R1 — Adversarial review (post-gates)**
Depends on: D5
Verification mode: judgment (adversarial-reviewer → iterate to Clean)

Done when: adversarial-reviewer reports `Clean — ready to commit.`; all Blocker and Concern findings resolved.

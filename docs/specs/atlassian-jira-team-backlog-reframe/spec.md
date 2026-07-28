---
name: atlassian-jira-team-backlog-reframe
description: "Phase 2D: align jira-team-status and jira-story-triage around safe team-backlog readiness — separating team readiness from agent-execution readiness, adding completeness pagination, moving summary before detail, renaming Needs story work, updating first-value prompt, adding evals/fixtures."
---

**Feature:** atlassian-jira-team-backlog-reframe
**Status:** Shipped
**Mode:** Full (structural/public-interface change, multi-feature, multi-dependent tasks)

# Spec: Atlassian Phase 2D — Jira Team Backlog Reframe

## Objective

Align `jira-team-status`, `jira-story-triage`, their activation routing, examples, and evaluations around a safe, natural team-backlog experience. The pack must support natural team-backlog language and distinguish two explicit readiness concepts — team readiness (the default) and agent-execution readiness (an explicit optional lens).

## Decisions

### Decision D1: Five-question bar = agent-execution readiness

The five questions (Q1 self-contained code change, Q2 reachable repo, Q3 ACs checkable by diff review, Q4 no human decision mid-flight, Q5 one-PR sized) are explicitly coding-agent execution criteria, not general team story quality. A PM asking "what can the team work on?" does not intend to filter out items that lack a repo URL in the description. The bar is preserved and labeled as **agent-execution readiness**. A team member can work on a story that passes team readiness without passing all five questions.

### Decision D2: New team readiness definition (for jira-team-status)

An item is **Ready to pull** for the team when all four hold:
1. In the selected team scope
2. In an eligible open-work state (default: `statusCategory = "To Do"`, team-overridable)
3. No known unresolved blocker
4. **Minimum definition**: non-empty summary + description that is not image-only, not a discovery artifact without ACs, and not wholly "TBD awaiting decision" throughout

Items failing clause 4 go to **Needs story work**. Items with undeterminable clause → **Needs confirmation**.

When the user explicitly requests **agent-execution readiness** ("agent-ready", "one-PR tasks", "coding-agent candidates", "diff-reviewable tasks"), apply the five-question bar as an additional filter over team-ready items.

### Decision D3: Output structure — summary before detail

Output starts with a header block (scope, coverage, read-only confirmation, summary counts) before the grouped sections. The current trailing summary line moves to the top.

### Decision D4: Pagination — fetch to completeness

Remove the `--limit 100` hard cap. Instruct the `jira` skill to paginate to completeness (Cloud: loop via nextPageToken/isLast; Server: loop via startAt until startAt ≥ total), or to a configured cap. Disclose completeness accurately:
- Cloud (no total until complete): `complete (N items)` or `cap reached at N` or `permission-limited`
- Server: `complete (N of M items)` or `cap reached at N of M`

Cloud cannot report total until all pages are fetched; do not promise a total on Cloud mid-fetch.

### Decision D5: Terminology

- "Needs detail" → **Needs story work** (jira-team-status output) — more natural PM language
- "Ready to pull" remains for team readiness; agent-execution readiness uses "Agent-ready" only when that explicit lens is active

### Decision D6: Version 0.7.0

Significant capability contract change; minor version bump from 0.6.3 → 0.7.0.

## Boundaries

### Always do
- `jira-team-status`: return header block (scope, coverage, read-only confirmation, summary counts) before grouped sections
- `jira-team-status`: use team readiness (D2) by default; agent-execution readiness only on explicit request
- `jira-team-status`: paginate to completeness; disclose completeness state
- `jira-team-status`: remain read-only; route improvement to `jira-story-triage`; only write on confirmed explicit single-field update
- `jira-story-triage`: label the five-question bar explicitly as agent-execution readiness
- `jira-story-triage`: for each not-ready item, output: issue ID/title, readiness result, missing info, why gap matters, proposed rewrite, proposed ACs where applicable, unresolved human question, expected readiness after draft, confirmation Jira not changed
- All evals: activation covers natural team-backlog language and near-miss negatives

### Ask first
- Any write to Jira — confirm exact issues, exact fields, old values, proposed values, protected fields, total writes before writing
- Changing the "eligible state" default away from `statusCategory = "To Do"`

### Never do
- Treat team readiness and agent-execution readiness as the same concept
- Report "whole backlog" without a completeness statement
- Write to Jira during orientation (jira-team-status) or drafting (jira-story-triage) without confirmed explicit approval
- Retrofit the six Atlassian guide pages (Phase 3 scope; minimum README/reference corrections only)
- Add a second general Jira writer (route writes through the existing `jira` skill only)

## Surfaces changed

**Lane B — jira-team-status:**
1. `packs/atlassian/.apm/skills/jira-team-status/SKILL.md` — new readiness rule, output format, pagination, stand-up support
2. `packs/atlassian/.apm/skills/jira-team-status/manifest.json` — version bump, new description
3. `packs/atlassian/.apm/skills/jira-team-status/evals/eval_queries.json` — new activation cases, near-miss negatives
4. `packs/atlassian/.apm/skills/jira-team-status/evals/evals.json` — NEW: deterministic + judgment fixtures
5. `packs/atlassian/.apm/skills/jira-team-status/references/examples.md` — updated examples

**Lane C — jira-story-triage:**
6. `packs/atlassian/.apm/skills/jira-story-triage/SKILL.md` — agent-execution label, per-item output fields, write-handoff clarity
7. `packs/atlassian/.apm/skills/jira-story-triage/manifest.json` — version bump, updated description
8. `packs/atlassian/.apm/skills/jira-story-triage/evals/eval_queries.json` — new cases, near-miss negatives
9. `packs/atlassian/.apm/skills/jira-story-triage/evals/evals.json` — NEW: deterministic + judgment fixtures
10. `packs/atlassian/.apm/skills/jira-story-triage/references/examples.md` — draft-only, confirmed write, protected fields examples

**Lane D — integration owner:**
11. `packs/atlassian/pack.toml` — first-value prompt (team query), version 0.7.0
12. `packs/atlassian/.claude-plugin/plugin.json` — version 0.7.0
13. `packs/atlassian/README.md` — minimum accuracy corrections (read-only label, team vs agent readiness)
14. `docs/product/changelog.md` — [Unreleased] entry

## Testing Strategy

Verification mode: **goal-based check** for skill content (activate eval self-consistency, build-check, lint); **visual/manual QA** for output format (trace each fixture).

- **Activation evals (goal-based):** Each eval_queries.json is self-consistent — natural team-backlog phrases trigger jira-team-status; readiness-review phrases trigger jira-story-triage; one-issue updates trigger jira skill; no phrase is positive in both sibling skills; near-misses prevent cross-skill absorption.
- **Fixture evals (goal-based):** evals.json for both skills covers the 16 fixture scenarios. Strong outputs satisfy all eight quality criteria; weak outputs contain at least one named failure pattern.
- **Deterministic tests (goal-based):** Team readiness rule, precedence rule, completeness disclosure, protected fields, write payload, partial failure — each testable via assertions in evals.json.
- **Build gates (goal-based):** `FORCE=1 make build-self` + `git status --short` confirms projection; `make build-check` passes; `python3 tools/lint-skill-spec.py` clean; `python3 tools/lint-agent-artifacts.py` clean.
- **Adversarial review (judgment):** `adversarial-reviewer` against spec + diff; iterate to Clean.

## Acceptance Criteria

- [x] AC1. Natural team-backlog requests activate jira-team-status ("show the team backlog", "what can the team pick up", "what is ready", "what is blocked", "what is unassigned", "sprint status", "stand-up summary", "stale team work").
- [x] AC2. Agent-execution readiness is a distinct optional lens; team readiness is the default.
- [x] AC3. Team scope can be resolved from board, project set, Team field, saved filter, or explicit JQL; ambiguous scope yields a compact clarification (not silence).
- [x] AC4. jira-team-status paginates to completeness (no 100-item silent truncation); coverage is disclosed with: scope, projects/boards, filters, items inspected, completeness state (complete/filtered/partial/capped/permission-limited).
- [x] AC5. Every whole-backlog result states scope and completeness before grouped sections.
- [x] AC6. jira-team-status is read-only for team orientation; only confirmed single-field updates are permitted.
- [x] AC7. Output header block (scope, coverage, read-only confirmation, summary counts) appears before grouped sections.
- [x] AC8. Ready to pull / Needs story work / Blocked / In progress / Other open work categories have documented deterministic precedence: Blocked → In progress → Needs story work → Ready to pull → Other open work.
- [x] AC9. Unassigned and stale work are exposed as cross-cutting flags (an item may be Blocked AND Unassigned).
- [x] AC10. jira-story-triage per-item output includes: issue ID/title, readiness result, missing info, why that gap matters, proposed rewrite, proposed ACs where applicable, unresolved human questions, expected readiness after draft, Jira-not-changed confirmation.
- [x] AC11. jira-story-triage default behavior = read-only inspection + draft output; no write by default.
- [x] AC12. Approved writes use the canonical `jira: update-issue` with exact issue, exact fields, old values (where available), proposed values, protected fields, total count — confirmed before writing.
- [x] AC13. Protected fields (status, assignee, sprint, priority, labels) remain unchanged unless explicitly named by the user.
- [x] AC14. Partial write failures have a safe recovery path (report success/failure per issue; no auto-retry of destructive/ambiguous writes).
- [x] AC15. Pack first-value starter-prompt is team-oriented ("Show me what Team Atlas can work on next. Start read-only and tell me if the result is incomplete.").
- [x] AC16. Pack claims (README, manifest descriptions, evals) agree with actual skill behavior.
- [x] AC17. Strong and weak fixtures (evals.json) discriminate safe from unsafe behavior for both skills.
- [x] AC18. Existing agent-ready behavior remains available through an explicit lens (not removed).
- [x] AC19. The five-question bar is labeled agent-execution readiness in jira-story-triage; jira-team-status uses the new team readiness rule by default.
- [x] AC20. Projection, build-check, lint, and adversarial review pass.
- [x] AC21. Guide page retrofit (atlassian-docs-retrofit six pages) completed in Phase 3 (PR #786).

## Assumptions

- Pack at 0.6.3; target 0.7.0.
- Cloud Jira `POST /search/jql` does not return `total` until all pages are fetched; Server/DC `GET /search` returns `total` in the first response. (Verified from jira/SKILL.md; accepted as architectural constraint.)
- The `jira` CLI's `--limit` cap is removable; pagination happens transparently via the CLI when limit is high enough or when the skill instructs explicit cursor-based pagination.
- No new Jira write skill is created; write handoff routes through `jira: update-issue` only.
- Guide pages (atlassian-docs-retrofit six pages) that reference the five-question bar as "readiness" may have slight terminology inaccuracies after this change; only minimum README/reference corrections are in scope.
- The five-question bar text stays identical between both skills (single source of truth for the agent-execution bar).

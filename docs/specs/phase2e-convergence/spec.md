# Spec: Phase 2E — Contract Convergence + Phase 3 Readiness Gate

- **Status:** Shipped <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** eugenelim
- **Mode:** full (multi-feature, structural change, public-interface change — journey validator, new tool)
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** Phase 2E convergence brief (`.context/attachments/U4CMzB/pasted_text_2026-07-28_21-51-04.txt`)

> **Spec contract:** this document defines what "done" means. The implementing PR must match this
> spec, or update it. Verification must be derivable from it.

## Objective

Complete the Phase 2E convergence baseline. The vast majority of prior-phase work (Phases 1, 2A,
2B, 2C-partial, 2D) has already shipped. Three genuine source defects remain that block an accurate
Phase 3 readiness assessment:

1. `lint-pack-journeys.py` enforces skill-count parity, coupling a primary journey to the complete
   pack skill inventory. A primary journey should reference only the skills its stages require.
2. No deterministic (non-LLM) behavior tests exist for the jira-team-status and jira-story-triage
   contract boundaries — only LLM-judge evals are present.
3. `tools/check-atlassian-phase3-readiness.py` does not exist.

This spec also records Phase 2C (`spec/site-ui-primitives`) as **not yet implemented** — the
readiness command reports it accurately as `fail`, and the overall Phase 3 readiness verdict
is `NOT READY FOR PHASE 3` because of this pre-existing gap.

## Boundaries

**In scope:**
- `tools/lint-pack-journeys.py` — remove count-parity check, keep reference-validity check
- `tools/test-lint-pack-journeys.py` — update one test, add one regression test
- `packs/atlassian/.apm/skills/jira-team-status/` — add behavior fixture tests
- `packs/atlassian/.apm/skills/jira-story-triage/` — add behavior fixture tests
- `tools/check-atlassian-phase3-readiness.py` — new readiness command
- `tools/test-check-atlassian-phase3-readiness.py` — test for readiness command
- Pre-PR wiring for readiness tool (if appropriate)

**Out of scope:**
- Do not rewrite `packs/atlassian/JOURNEY.md` (Phase 3 territory)
- Do not rewrite six Atlassian guide pages (Phase 3 territory)
- Do not implement Phase 2C UI primitives
- Do not touch `site.toml`, `catalogue.toml`, `workspace.toml` (no changes needed)
- Do not version-bump any pack (no skill behavior changes shipped in this PR)

## Convergence matrix

| Area | Hypothesis | Source fact | Mismatch | Severity | Action |
|---|---|---|---|---|---|
| A1: site.toml grouping | H1: user-guide-diataxis still grouped | user-guide-diataxis absent from site.toml | None | — | ✓ skip |
| A2: guides/README.md doctrine | H2: teaches physical quadrant dirs | 97-line nav index, no dir teaching | None | — | ✓ skip |
| A3: Legacy pack presentation | H3: competes as equal product | site.toml absent; pack deprecated | None | — | ✓ skip |
| B1: Journey contract gate | H4: live gate deferred | pre_pr_catalogue.py L114, exit 0 | None | — | ✓ skip |
| B2: Journey vs inventory | H5: parity forces full inventory | lint-pack-journeys.py L178-183 | **Confirmed** | Medium | Fix lint |
| C1: First-value verification | H6: personal "list my issues" prompt | pack.toml: "Show me what Team Atlas..." | None | — | ✓ skip |
| C2: README write attribution | H7: jira-story-triage assigned writes | README: "Draft only, do not update Jira" | None | — | ✓ skip |
| C3: README team starter | H8: no team starter example | README lines 13-19: team backlog example | None | — | ✓ skip |
| C4: Deterministic tests | H9: coverage incomplete | No behavior-contract tests exist | **Confirmed** | High | Add tests |
| D: Readiness command | H—: missing tool | No tools/check-atlassian-phase3-readiness.py | **Confirmed** | High | Create tool |
| X: Phase 2C UI primitives | —: not implemented | spec/site-ui-primitives: Implementing, 0/17 ACs | Pre-existing gap | Blocker | Report as fail |

## Assumptions

1. No skill behavior changes are needed — jira-team-status, jira-story-triage, and jira SKILL.md
   are already contract-correct per prior-phase shipping.
2. The deterministic behavior tests exercise SKILL.md contract logic via fixture assertions, not
   live Jira API calls. They use the established evals.json fixture pattern for behavior validation.
3. The readiness command is a milestone tool, not a permanent global gate — it exits non-zero
   because Phase 2C is not implemented; this is accurate, not a defect in the tool.
4. The atlassian JOURNEY.md listing all 11 skills is valid after the parity fix — all 11 refs
   exist. The fix allows subsets; it does not require them.

## Declined patterns

- Tempted to rewrite atlassian JOURNEY.md to only list primary journey skills — declining; Phase 3
  territory per the brief. The fix enables this but does not require it.
- Tempted to add a `--allow-subset` flag to lint-pack-journeys.py — declining; the new behavior
  should be the default, no flag needed.
- Tempted to implement Phase 2C UI primitives to make the readiness command exit 0 — declining;
  Phase 2C is a large separate spec with 17 ACs. The readiness command accurately reports reality.

## Acceptance Criteria

- [x] AC1: `lint-pack-journeys.py` accepts a JOURNEY.md that lists a strict subset of pack skills
  (all listed skills exist; unlisted pack skills are permitted). Exit 0.
- [x] AC2: `lint-pack-journeys.py` still rejects a JOURNEY.md that lists a skill not in the pack.
  Exit 1 with "not found" in the error.
- [x] AC3: `test-lint-pack-journeys.py` contains a test that proves a subset journey passes.
- [x] AC4: `test-lint-pack-journeys.py` still passes all existing non-count-parity tests (17 → 18).
- [x] AC5: Deterministic behavior test module exists at
  `packs/atlassian/.apm/skills/jira-team-status/tests/test_contract.py` covering all 16 scenarios
  from the mission brief without live Atlassian credentials.
- [x] AC6: All 16 test scenarios in AC5 pass on the unmodified SKILL.md contract.
- [x] AC7: `tools/check-atlassian-phase3-readiness.py` exists and exits non-zero (Phase 2C not
  implemented).
- [x] AC8: The readiness command produces machine-readable JSON (--json flag) with `ready: false`
  and a `checks` array covering all required prerequisite areas.
- [x] AC9: The readiness command correctly reports Phase 2C as `fail` with evidence.
- [x] AC10: The readiness command reports all other prerequisite checks as `pass` where they are
  implemented and verifiable without live credentials.
- [x] AC11: `tools/test-check-atlassian-phase3-readiness.py` passes.
- [x] AC12: `make build-check` exits 0 after all changes.
- [x] AC13: `python3 tools/lint-pack-journeys.py` exits 0 (both existing journeys still valid).
- [x] AC14: `python3 tools/lint-journey-contract.py` exits 0.
- [x] AC15: No pack version is bumped (no shipped skill behavior change in this PR).

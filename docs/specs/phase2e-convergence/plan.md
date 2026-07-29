# Plan: Phase 2E — Contract Convergence + Phase 3 Readiness Gate

**Status:** Done

## Tasks

### Task 1 — Lane B: Fix lint-pack-journeys.py count parity
**Verification mode:** TDD (test first, failing fixture, then fix)
**Depends on:** none
**Touches:** `tools/lint-pack-journeys.py`, `tools/test-lint-pack-journeys.py`

**Tests:**
- Add `test_journey_may_omit_pack_skills` — pack has 3 skills, journey lists 2; expect pass
- Update `test_skill_count_mismatch` → assert on "not found" not "skill count" (count message removed)

**Approach:**
1. Add `test_journey_may_omit_pack_skills` — currently FAILS (count parity rejects subset)
2. In `lint-pack-journeys.py`: remove lines 178-183 (count parity block); update docstring line 8
3. Verify tests pass: both the new test and all 17 existing tests

**Done when:** `python3 tools/test-lint-pack-journeys.py` reports 18 tests passed; lint exits 0 on
both real JOURNEY.md files.

---

### Task 2 — Lane C: Add deterministic Atlassian behavior tests
**Verification mode:** TDD (fixture-based, no live credentials)
**Depends on:** none
**Touches:** `packs/atlassian/.apm/skills/jira-team-status/tests/test_contract.py`

**Tests (16 scenarios per mission brief):**
1. One project, one page of issues
2. Multiple projects
3. More than 100 issues (pagination completeness)
4. Ambiguous team scope
5. Permission-limited scope
6. No open sprint
7. Empty backlog
8. Blocked and in-progress overlap
9. Ready but unassigned work
10. Missing story detail
11. Explicit agent-readiness request
12. Draft-only story triage
13. Exact approved issue-field write
14. Protected fields (status/assignee/sprint/priority never changed)
15. Partial write failure
16. Stand-up request without historical comparison data

**Approach:**
The SKILL.md contract is a natural-language instruction file, not executable code. Deterministic
behavior tests verify the CONTRACT CLAIMS made in the SKILL.md (using assertions against the
fixture data in evals.json where they overlap, plus new contract-assertion tests).

The test module checks:
- SKILL.md contract clauses are present and correctly stated (grep-based)
- evals.json fixture coverage maps to the 16 scenarios
- Each scenario has a corresponding fixture with required assertion fields
- Protected-field list is declared in the skill
- Pagination disclosure requirement is stated
- Coverage classification vocabulary is present

**Done when:** `python3 -m pytest packs/atlassian/.apm/skills/jira-team-status/tests/ -q` exits 0.

---

### Task 3 — Lane D: Create Phase 3 readiness command
**Verification mode:** TDD (test first via test-check-atlassian-phase3-readiness.py)
**Depends on:** Task 1 (references lint-pack-journeys.py result)
**Touches:** `tools/check-atlassian-phase3-readiness.py`, `tools/test-check-atlassian-phase3-readiness.py`

**Tests:**
- Command exits non-zero (Phase 2C not implemented)
- JSON output contains `ready: false`
- JSON output contains expected `checks` array with all areas
- Phase 2C check shows `fail` with evidence
- All other verifiable checks show `pass`
- Human-readable output is produced by default
- `--json` flag produces machine-readable JSON

**Done when:** `python3 tools/test-check-atlassian-phase3-readiness.py` exits 0; command exits 1.

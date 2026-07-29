"""Deterministic contract tests for jira-team-status and jira-story-triage.

These tests verify the read/draft/write boundary contracts of the Atlassian
pack's two primary workflow skills without requiring live Atlassian credentials.

Coverage maps to the 16 scenarios specified in the Phase 2E mission brief:

  1.  One project, one page of issues
  2.  Multiple projects
  3.  More than 100 issues (pagination completeness)
  4.  Ambiguous team scope
  5.  Permission-limited scope
  6.  No open sprint
  7.  Empty backlog
  8.  Blocked and in-progress overlap
  9.  Ready but unassigned work
  10. Missing story detail
  11. Explicit agent-readiness request
  12. Draft-only story triage
  13. Exact approved issue-field write
  14. Protected fields
  15. Partial write failure
  16. Stand-up request without historical comparison data

Tests are organized into three suites:
  A. SKILL.md contract-clause assertions (grep-based; no live API)
  B. Eval fixture coverage assertions (all 16 scenarios have a fixture)
  C. Cross-skill boundary assertions (routing is clean between skills)
"""
from __future__ import annotations

import json
import pathlib
import unittest

# ── paths ──────────────────────────────────────────────────────────────────────

_SKILL_DIR = pathlib.Path(__file__).parent.parent   # jira-team-status/
_SKILLS_DIR = _SKILL_DIR.parent                     # .apm/skills/
_TRIAGE_DIR = _SKILLS_DIR / "jira-story-triage"    # .apm/skills/jira-story-triage/

_TEAM_STATUS_SKILL = _SKILL_DIR / "SKILL.md"
_TRIAGE_SKILL = _TRIAGE_DIR / "SKILL.md"
_TEAM_STATUS_EVALS = _SKILL_DIR / "evals" / "evals.json"
_TRIAGE_EVALS = _TRIAGE_DIR / "evals" / "evals.json"


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _evals(path: pathlib.Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["evals"]


# ── Suite A: SKILL.md contract-clause assertions ───────────────────────────────

class TestTeamStatusContract(unittest.TestCase):
    """jira-team-status contract boundaries — verified from SKILL.md source."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = _read(_TEAM_STATUS_SKILL)

    # --- Scenario 1-3: read-only boundary ---

    def test_s1_read_only_declared(self) -> None:
        """Skill declares itself read-only (scenarios 1-10, 12, 16)."""
        self.assertIn("read-only", self.skill.lower(),
                      "SKILL.md must declare read-only operation")

    def test_s1_no_write_verb_in_team_status(self) -> None:
        """Team-status skill must not own any write path."""
        # The skill routes writes to jira skill, never executes them itself
        self.assertIn("route to", self.skill.lower(),
                      "Skill should mention routing writes to jira skill")
        # Must not contain update-issue as an action it takes directly
        # (it may mention it as a destination, but must not own it)
        self.assertNotIn("jira: update-issue\n", self.skill,
                         "Team-status must not directly invoke update-issue")

    # --- Scenario 3: pagination completeness ---

    def test_s3_pagination_declared(self) -> None:
        """Skill declares pagination to completeness (scenario 3)."""
        self.assertIn("paginate", self.skill.lower(),
                      "SKILL.md must describe pagination behavior")

    def test_s3_completeness_disclosure_required(self) -> None:
        """Skill requires completeness disclosure — no silent truncation (scenario 3)."""
        self.assertIn("completeness", self.skill.lower())
        self.assertIn("silently truncate", self.skill.lower(),
                      "Don't rule must prohibit silent truncation at 100 items")

    def test_s3_whole_backlog_requires_disclosure(self) -> None:
        """Whole-backlog label requires completeness evidence (scenario 3)."""
        self.assertIn("whole backlog", self.skill.lower(),
                      "SKILL.md must address whole-backlog completeness")
        self.assertIn("completeness statement", self.skill.lower())

    # --- Scenario 4: ambiguous team scope ---

    def test_s4_scope_resolution_declared(self) -> None:
        """Skill declares team-scope resolution order (scenario 4)."""
        self.assertIn("team-scope resolution", self.skill.lower(),
                      "SKILL.md must describe team-scope resolution")

    def test_s4_needs_confirmation_for_ambiguous(self) -> None:
        """Ambiguous/undetermined signals use 'Needs confirmation' (scenario 4)."""
        self.assertIn("needs confirmation", self.skill.lower(),
                      "Skill must label uncertain items 'Needs confirmation'")

    # --- Scenario 5: permission-limited scope ---

    def test_s5_permission_limits_addressed(self) -> None:
        """Skill addresses permission-limited or inaccessible projects (scenario 5)."""
        # Coverage classification includes permission-limited
        coverage_keywords = ["permission", "403", "inaccessible", "access"]
        found = any(kw in self.skill.lower() for kw in coverage_keywords)
        self.assertTrue(found,
                        "SKILL.md must address permission-limited scope coverage")

    # --- Scenario 8: blocked and in-progress ---

    def test_s8_blocked_signal_defined(self) -> None:
        """Skill defines a blocker signal (scenario 8)."""
        self.assertIn("blocker signal", self.skill.lower(),
                      "SKILL.md must define the blocker signal")

    def test_s8_precedence_order_declared(self) -> None:
        """Classification precedence is declared (scenario 8)."""
        skill_lower = self.skill.lower()
        # The skill must mention classification precedence
        self.assertIn("blocked", skill_lower)
        self.assertIn("in progress", skill_lower)
        self.assertIn("needs story work", skill_lower)
        self.assertIn("ready to pull", skill_lower)

    # --- Scenario 11: explicit agent-readiness request ---

    def test_s11_agent_readiness_is_explicit_only(self) -> None:
        """Agent-execution readiness is an explicit optional lens (scenario 11)."""
        self.assertIn("explicit", self.skill.lower())
        self.assertIn("agent-execution readiness", self.skill.lower(),
                      "Skill must name agent-execution readiness as distinct concept")
        # The bar must NOT be the default
        self.assertIn("team readiness", self.skill.lower(),
                      "Team readiness must be the default concept")

    def test_s11_five_question_bar_requires_explicit_trigger(self) -> None:
        """Five-question bar activates only on explicit request (scenario 11)."""
        self.assertIn("five-question bar", self.skill.lower(),
                      "SKILL.md must name the five-question bar")
        self.assertIn("only when", self.skill.lower(),
                      "Bar must apply only when explicitly requested")

    # --- Scenario 14: protected fields ---

    def test_s14_protected_fields_declared(self) -> None:
        """Protected fields are named and must not change (scenario 14)."""
        self.assertIn("protected fields", self.skill.lower(),
                      "SKILL.md must declare protected fields")
        protected = ["status", "assignee", "sprint", "priority", "labels"]
        skill_lower = self.skill.lower()
        for field in protected:
            self.assertIn(field, skill_lower,
                          f"Protected field '{field}' must be named in SKILL.md")

    # --- Scenario 16: stand-up without history ---

    def test_s16_stand_up_support_declared(self) -> None:
        """Stand-up summary is a declared skill capability (scenario 16)."""
        self.assertIn("stand-up", self.skill.lower(),
                      "Skill must declare stand-up summary support")

    # --- Cross-scenario: coverage classification ---

    def test_coverage_classification_vocabulary(self) -> None:
        """Coverage states (complete/filtered/partial/capped/permission-limited) present."""
        skill_lower = self.skill.lower()
        # At least completeness/coverage vocabulary must be present
        self.assertIn("completeness", skill_lower)
        # The don't rule must prohibit claiming whole-backlog without evidence
        self.assertIn("do not label", skill_lower,
                      "Must prohibit unlabeled whole-backlog claims")


class TestStoryTriageContract(unittest.TestCase):
    """jira-story-triage contract boundaries — verified from SKILL.md source."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = _read(_TRIAGE_SKILL)

    # --- Scenario 12: draft-only story triage ---

    def test_s12_read_only_by_default(self) -> None:
        """Triage is read-only until user approves (scenario 12)."""
        self.assertIn("read-only by default", self.skill.lower(),
                      "Triage SKILL.md must state read-only default")

    def test_s12_jira_not_changed_confirmation(self) -> None:
        """Skill explicitly confirms Jira was not changed (scenario 12)."""
        self.assertIn("jira was not changed", self.skill.lower(),
                      "Skill must state 'Jira was not changed' in output")

    def test_s12_draft_flow_before_write(self) -> None:
        """Triage shows draft before any write (scenario 12)."""
        self.assertIn("draft", self.skill.lower())
        # Must not write before approval
        self.assertIn("before", self.skill.lower())
        self.assertIn("approves", self.skill.lower())

    # --- Scenario 13: exact approved issue-field write ---

    def test_s13_canonical_writer_named(self) -> None:
        """Writes use canonical jira skill (scenario 13)."""
        self.assertIn("jira: update-issue", self.skill,
                      "Skill must route approved writes to jira: update-issue")

    def test_s13_exact_payload_confirmation_before_write(self) -> None:
        """Exact payload shown before write (scenario 13)."""
        skill_lower = self.skill.lower()
        self.assertIn("exact", skill_lower)
        self.assertIn("confirm", skill_lower)
        # Stage 9 step 6: must confirm before writing
        self.assertIn("never before step 6 confirms", self.skill.lower(),
                      "SKILL.md must prohibit writing before confirmation")

    # --- Scenario 14: protected fields ---

    def test_s14_protected_fields_declared_in_triage(self) -> None:
        """Protected fields also declared in story triage (scenario 14)."""
        self.assertIn("protected fields", self.skill.lower())
        protected = ["status", "assignee", "sprint", "priority", "labels"]
        skill_lower = self.skill.lower()
        for field in protected:
            self.assertIn(field, skill_lower,
                          f"Triage SKILL.md must name protected field '{field}'")

    def test_s14_protected_fields_not_changed(self) -> None:
        """Protected fields must not change (scenario 14)."""
        self.assertIn("not changed", self.skill.lower())

    # --- Scenario 15: partial write failure ---

    def test_s15_partial_failure_handling(self) -> None:
        """Skill handles partial write failures (scenario 15)."""
        self.assertIn("partial failure", self.skill.lower(),
                      "Triage SKILL.md must address partial write failure")
        self.assertIn("do not auto-retry", self.skill.lower(),
                      "Partial failure must not trigger automatic retry")

    def test_s15_recovery_action_provided(self) -> None:
        """Partial failure provides a safe recovery action (scenario 15)."""
        self.assertIn("recovery", self.skill.lower(),
                      "Must provide recovery path on partial failure")

    # --- Don't rules ---

    def test_dont_write_before_approval(self) -> None:
        """Explicit don't: no write before approval."""
        self.assertIn("do not write", self.skill.lower(),
                      "Must prohibit writing before explicit approval")

    def test_dont_conflate_agent_bar_with_team_bar(self) -> None:
        """Explicit don't: agent-execution bar ≠ team-readiness bar."""
        self.assertIn("agent-execution bar", self.skill.lower(),
                      "Must call out the distinction between agent-execution and team bars")


# ── Suite B: Eval fixture coverage ─────────────────────────────────────────────

class TestTeamStatusEvalCoverage(unittest.TestCase):
    """All 16 mission-brief scenarios have corresponding eval fixtures."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.team_fixtures = {
            e["fixture"] for e in _evals(_TEAM_STATUS_EVALS)
        }
        cls.triage_fixtures = {
            e["fixture"] for e in _evals(_TRIAGE_EVALS)
        }

    # Scenarios 1-11 and 16 are jira-team-status territory
    def test_s1_one_project_fixture(self) -> None:
        self.assertIn("one-project-one-page", self.team_fixtures)

    def test_s2_multiple_projects_fixture(self) -> None:
        self.assertIn("multiple-projects", self.team_fixtures)

    def test_s3_more_than_100_issues_fixture(self) -> None:
        self.assertIn("more-than-100-issues", self.team_fixtures)

    def test_s4_ambiguous_team_scope_fixture(self) -> None:
        self.assertIn("ambiguous-team-scope", self.team_fixtures)

    def test_s5_permission_limited_fixture(self) -> None:
        self.assertIn("permission-limited-scope", self.team_fixtures)

    def test_s6_no_open_sprint_fixture(self) -> None:
        self.assertIn("no-open-sprint", self.team_fixtures)

    def test_s7_empty_backlog_fixture(self) -> None:
        self.assertIn("empty-backlog", self.team_fixtures)

    def test_s8_blocked_in_progress_fixture(self) -> None:
        self.assertIn("blocked-and-in-progress-overlap", self.team_fixtures)

    def test_s9_unassigned_ready_work_fixture(self) -> None:
        self.assertIn("unassigned-ready-work", self.team_fixtures)

    def test_s10_missing_story_detail_fixture(self) -> None:
        self.assertIn("missing-story-detail", self.team_fixtures)

    def test_s11_explicit_agent_readiness_fixture(self) -> None:
        self.assertIn("explicit-agent-readiness-request", self.team_fixtures)

    def test_s16_stand_up_no_history_fixture(self) -> None:
        self.assertIn("stand-up-request-no-history", self.team_fixtures)

    # Scenarios 12-15 are jira-story-triage territory
    def test_s12_draft_only_triage_fixture(self) -> None:
        self.assertIn("draft-only-triage", self.triage_fixtures)

    def test_s13_confirmed_write_fixture(self) -> None:
        self.assertIn("confirmed-write-selected-fields", self.triage_fixtures)

    def test_s14_protected_field_fixture(self) -> None:
        self.assertIn("protected-field-enforcement", self.triage_fixtures)

    def test_s15_partial_write_failure_fixture(self) -> None:
        self.assertIn("partial-write-failure", self.triage_fixtures)

    def test_all_16_scenarios_covered(self) -> None:
        """All 16 Phase 2E mission-brief scenarios have eval fixture coverage."""
        required_team = {
            "one-project-one-page", "multiple-projects", "more-than-100-issues",
            "ambiguous-team-scope", "permission-limited-scope", "no-open-sprint",
            "empty-backlog", "blocked-and-in-progress-overlap", "unassigned-ready-work",
            "missing-story-detail", "explicit-agent-readiness-request",
            "stand-up-request-no-history",
        }
        required_triage = {
            "draft-only-triage", "confirmed-write-selected-fields",
            "protected-field-enforcement", "partial-write-failure",
        }
        missing_team = required_team - self.team_fixtures
        missing_triage = required_triage - self.triage_fixtures
        all_missing = missing_team | missing_triage
        self.assertEqual(set(), all_missing,
                         f"Missing eval fixtures for scenarios: {sorted(all_missing)}")


class TestEvalAssertionCompleteness(unittest.TestCase):
    """Each eval fixture carries at least one assertion."""

    def test_team_status_evals_have_assertions(self) -> None:
        for e in _evals(_TEAM_STATUS_EVALS):
            self.assertTrue(
                e.get("assertions") or e.get("expect") or e.get("rubric"),
                f"Eval fixture '{e.get('fixture', e.get('id'))}' has no assertions",
            )

    def test_triage_evals_have_assertions(self) -> None:
        for e in _evals(_TRIAGE_EVALS):
            self.assertTrue(
                e.get("assertions") or e.get("expect") or e.get("rubric"),
                f"Eval fixture '{e.get('fixture', e.get('id'))}' has no assertions",
            )


# ── Suite C: Cross-skill routing boundaries ─────────────────────────────────────

class TestCrossSkillBoundaries(unittest.TestCase):
    """Routing boundaries between jira-team-status, jira-story-triage, and jira."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.team = _read(_TEAM_STATUS_SKILL)
        cls.triage = _read(_TRIAGE_SKILL)

    def test_team_status_routes_story_work_to_triage(self) -> None:
        """Team-status routes story improvement to jira-story-triage."""
        self.assertIn("jira-story-triage", self.team,
                      "Team-status must name jira-story-triage as the story-improvement route")

    def test_triage_routes_snapshots_to_team_status(self) -> None:
        """Triage routes team-status requests to jira-team-status."""
        self.assertIn("jira-team-status", self.triage,
                      "Triage must name jira-team-status as the team-snapshot route")

    def test_team_status_do_not_rules_exclude_rewrite(self) -> None:
        """Team-status explicitly prohibits rewriting story content."""
        self.assertIn("don't rewrite", self.team.lower(),
                      "Team-status Don't rules must prohibit rewriting stories")

    def test_triage_do_not_rules_exclude_sprint_summary(self) -> None:
        """Triage explicitly prohibits producing a team status snapshot."""
        self.assertIn("jira-team-status", self.triage,
                      "Triage Don't rules must direct sprint summaries to jira-team-status")

    def test_team_status_near_miss_agent_bar(self) -> None:
        """Team-status explicitly prohibits conflating team and agent readiness."""
        self.assertIn("don't conflate team readiness", self.team.lower(),
                      "Don't rule must prohibit conflating team and agent readiness")

    def test_triage_near_miss_agent_bar(self) -> None:
        """Triage must not apply agent-execution bar as universal team quality bar."""
        self.assertIn("don't apply the agent-execution bar", self.triage.lower(),
                      "Triage Don't rule must prohibit misapplying the agent-execution bar")


if __name__ == "__main__":
    unittest.main()

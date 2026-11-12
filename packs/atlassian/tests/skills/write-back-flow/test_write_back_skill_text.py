"""Text tests: shipped skill text describes the preview-and-approve write flow.

Reads only this pack's own shipped skill files; no network, no credentials.
"""
from __future__ import annotations

import json
import pathlib
import re
import unittest

_SKILLS = pathlib.Path(__file__).resolve().parents[3] / ".apm" / "skills"
_JIRA = _SKILLS / "jira"
_ALIGN = _SKILLS / "jira-align"
_TRIAGE = _SKILLS / "jira-story-triage"
_TEAM = _SKILLS / "jira-team-status"

_CHANGED_SKILLS = (_JIRA, _ALIGN, _TRIAGE, _TEAM)

# A Jira write call names an issue key (or a placeholder for one) after the verb.
_JIRA_UPDATE = re.compile(r"update-issue\s+(?:[A-Z]|<)")
# A Jira Align write call names a resource and an id after the verb.
_ALIGN_UPDATE = re.compile(r"jira_align\.py'?\s+update\s+\S+\s+\S+|`update\s+\w+\s+(?:\d+|<id>)")
_NEGATED = re.compile(r"does not|do not|don't|never|no `--method`", re.IGNORECASE)


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def _shipped_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for skill in _CHANGED_SKILLS:
        files.append(skill / "SKILL.md")
        files.extend(sorted((skill / "references").glob("*.md")))
        evals = skill / "evals" / "evals.json"
        if evals.is_file():
            files.append(evals)
    return files


def _spans(text: str, pattern: re.Pattern[str]) -> list[str]:
    """Return each matching invocation with its backslash-continued lines."""
    lines = text.splitlines()
    found: list[str] = []
    for i, line in enumerate(lines):
        if not pattern.search(line):
            continue
        span = line
        j = i
        while lines[j].rstrip().endswith("\\") and j + 1 < len(lines):
            j += 1
            span += "\n" + lines[j]
        found.append(span)
    return found


class UpdateInvocationsCarryPlan(unittest.TestCase):
    def test_every_update_invocation_has_a_plan(self) -> None:
        offenders = []
        for path in _shipped_files():
            text = _read(path)
            for pattern in (_JIRA_UPDATE, _ALIGN_UPDATE):
                for span in _spans(text, pattern):
                    if "--plan" not in span:
                        offenders.append(f"{path.name}: {span.strip()[:120]}")
        self.assertEqual(offenders, [])

    def test_no_update_invocation_uses_no_notify(self) -> None:
        offenders = []
        for path in _shipped_files():
            for span in _spans(_read(path), _JIRA_UPDATE):
                if "--no-notify" in span:
                    offenders.append(f"{path.name}: {span.strip()[:120]}")
        self.assertEqual(offenders, [])

    def test_no_method_flag_remains_outside_a_negation(self) -> None:
        offenders = []
        for path in _shipped_files():
            for line in _read(path).splitlines():
                if "--method" in line and not _NEGATED.search(line):
                    offenders.append(f"{path.name}: {line.strip()[:120]}")
        self.assertEqual(offenders, [])


class CommandTables(unittest.TestCase):
    def _table_row_10(self, skill: pathlib.Path) -> str:
        rows = [ln for ln in _read(skill / "SKILL.md").splitlines() if ln.startswith("| 10 |")]
        self.assertEqual(len(rows), 1, f"{skill.name} exit table needs one code 10 row")
        return rows[0]

    def test_exit_table_names_guard_code_and_action(self) -> None:
        for skill in (_JIRA, _ALIGN):
            row = self._table_row_10(skill)
            self.assertIn("plan-update", row)
            self.assertIn("not an auth problem", row)
            self.assertIn("do not retry the same command", row)

    def test_exit_10_row_gives_the_folder_remedy(self) -> None:
        for skill in (_JIRA, _ALIGN):
            row = " ".join(self._table_row_10(skill).split())
            self.assertIn("tracker-write-back folder", row, skill.name)
            self.assertIn("owner-only", row, skill.name)
            self.assertIn("mode 700", row, skill.name)
            self.assertIn("owned by someone else", row, skill.name)
            self.assertIn("a link", row, skill.name)
            self.assertIn("`plans` folder", row, skill.name)
            self.assertIn("`prior` folder", row, skill.name)
            self.assertIn("running `plan-update` again does not fix", row, skill.name)

    def test_exit_10_row_covers_every_folder_preflight_refusal(self) -> None:
        for skill in (_JIRA, _ALIGN):
            row = " ".join(self._table_row_10(skill).split())
            for trigger in (
                "tracker-write-back folder, path, or path component",
                "a symlink or reparse point",
                "cannot be inspected or prepared",
            ):
                self.assertIn(trigger, row, skill.name)
            self.assertIn("`~/.agentbundle` itself must not be a link", row, skill.name)
            self.assertIn("does not follow links", row, skill.name)
            self.assertIn("a real folder owned by the person", row, skill.name)
            self.assertIn("no group or other access", row, skill.name)
            self.assertIn("a file sitting where a folder belongs", row, skill.name)

    def test_tables_list_the_new_commands(self) -> None:
        for skill, script in ((_JIRA, "jira.py"), (_ALIGN, "jira_align.py")):
            text = _read(skill / "SKILL.md")
            for command in ("plan-update", "plan-undo"):
                self.assertIn(f"{script}' {command}", text)
        self.assertIn("--replace-record", _read(_ALIGN / "SKILL.md"))

    def test_jira_transition_with_field_content_is_always_refused(self) -> None:
        text = _read(_JIRA / "SKILL.md")
        self.assertRegex(text, r"`transition` with `--field`[^.]*always\s+refused")


class ApprovalFlowSkills(unittest.TestCase):
    def test_triage_and_team_status_preview_before_write(self) -> None:
        for skill in (_TRIAGE, _TEAM):
            text = _read(skill / "SKILL.md")
            self.assertIn("plan-undo", text, skill.name)
            first_plan = text.index("plan-update")
            first_write = text.index("update-issue --plan") if "update-issue --plan" in text else -1
            self.assertGreaterEqual(first_write, 0, skill.name)
            # A plan-update mention must come before the first write command.
            self.assertLess(first_plan, first_write, skill.name)
            self.assertNotIn("there is no undo", text.lower(), skill.name)

    def test_undo_asks_for_digest_approval_and_dumps_no_plan_file(self) -> None:
        for skill in (_JIRA, _ALIGN, _TRIAGE):
            text = _read(skill / "SKILL.md")
            start = text.index("To undo, run")
            window = " ".join(text[start:].split("\n- ")[0].split("\n\n")[0].split())
            self.assertIn("digest", window, skill.name)
            self.assertIn("approve", window, skill.name)
            self.assertIn("Do not print the plan file or the record", window, skill.name)
            self.assertNotIn("preview", window.lower(), skill.name)
        self.assertNotIn("preview", _read(_TEAM / "SKILL.md").split("If the person wants the change reverted")[1][:300])

    def test_triage_asks_dispositions_and_ask_first_questions(self) -> None:
        text = _read(_TRIAGE / "SKILL.md")
        for needle in ("`keep`", "`append`", "`replace`", "--allow-lossy", "digest"):
            self.assertIn(needle, text)
        self.assertIn("One approval per record", text)

    def test_triage_partial_failure_is_a_replan(self) -> None:
        text = _read(_TRIAGE / "SKILL.md")
        start = text.index("**Partial failure:**")
        paragraph = text[start : text.index("\n\n", start)]
        self.assertIn("plan-update", paragraph)
        self.assertNotIn("same payload", paragraph)
        self.assertNotIn("Retry PROJ-99 manually", paragraph)


class AdversarialFieldEval(unittest.TestCase):
    def test_triage_has_adversarial_field_case(self) -> None:
        evals = json.loads(_read(_TRIAGE / "evals" / "evals.json"))["evals"]
        cases = [e for e in evals if "adversarial" in e.get("fixture", "")]
        self.assertEqual(len(cases), 1)
        case = cases[0]
        self.assertIn("allow-lossy", case["context"])
        self.assertGreaterEqual(len(case["assertions"]), 4)
        joined = " ".join(case["assertions"]).lower()
        for needle in ("plan-update", "disposition", "--allow-lossy", "approval", "digest"):
            self.assertIn(needle, joined)

    def test_evals_parse_with_unique_ids(self) -> None:
        for skill in _CHANGED_SKILLS:
            path = skill / "evals" / "evals.json"
            if not path.is_file():
                continue
            ids = [e["id"] for e in json.loads(_read(path))["evals"]]
            self.assertEqual(len(ids), len(set(ids)), skill.name)

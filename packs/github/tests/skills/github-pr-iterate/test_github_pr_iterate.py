"""Construction tests for the GitHub PR-iterate skill contract."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[3] / ".apm/skills/github-pr-iterate"
SKILL = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")


def _frontmatter() -> str:
    match = re.match(r"---\n(.*?)\n---\n", SKILL, re.DOTALL)
    assert match, "SKILL.md must open with frontmatter"
    return match.group(1)


def _command_blocks() -> str:
    return "\n".join(re.findall(r"```text\n(.*?)```", SKILL, re.DOTALL))


def test_frontmatter_declares_credentialed_boundary() -> None:
    front = _frontmatter()
    assert "name: github-pr-iterate" in front
    assert "allowed-tools: Read Edit Write Bash" in front
    for boundary in ("network_fetch", "filesystem_read_untrusted", "filesystem_write"):
        assert f"- {boundary}" in front
    assert "credentialed: true" in front


def test_manifest_and_evals_agree_with_skill() -> None:
    manifest = json.loads((SKILL_ROOT / "manifest.json").read_text(encoding="utf-8"))
    evals = json.loads((SKILL_ROOT / "evals/evals.json").read_text(encoding="utf-8"))
    queries = json.loads((SKILL_ROOT / "evals/eval_queries.json").read_text(encoding="utf-8"))
    assert manifest["id"] == evals["skill_name"] == "github-pr-iterate"
    assert all(case["assertions"] for case in evals["evals"])
    assert {q["should_trigger"] for q in queries} == {True, False}


@pytest.mark.parametrize(
    "required",
    [
        "untrusted data",
        "Silence, a",
        "Anything the\nuser did not approve is left untouched",
        "never amend",
        "HEAD:refs/heads/<headRefName>",
        "--repo <owner>/<repo>",
        "Judge \"repository rules\" from the base branch",
        "outside the working tree",
        "never force-push",
        "Only after the push",
        "Resolve a thread only when its fix has landed",
        "GitHub-only",
    ],
)
def test_safety_rules_are_stated(required: str) -> None:
    assert required in SKILL


def test_command_blocks_use_no_unapproved_mutation_or_account_switch() -> None:
    commands = _command_blocks()
    for forbidden in ("--force", "--amend", "gh pr merge", "gh pr review", "git push\n", "auth switch", "auth token"):
        assert forbidden not in commands
    # Reads precede the approval gate; every mutating call follows it.
    gate = SKILL.index("## 3. Plan, then wait")
    assert SKILL.index("gh pr checks") < gate
    for mutation in ("git push https://", "addPullRequestReviewThreadReply", "gh pr comment", "resolveReviewThread"):
        assert SKILL.index(mutation) > gate, mutation


def test_scope_excludes_other_hosts_and_open_mode() -> None:
    assert "supports GitHub only" in SKILL
    assert "Azure" not in SKILL
    assert "gh pr create" not in SKILL
    assert "does not open, merge, approve, or dismiss" in SKILL.replace("\n", " ")

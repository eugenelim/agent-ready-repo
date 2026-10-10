"""Impact-evidence routing: grep wording is gone from work-loop and bug-fix.

Spec: docs/specs/core-impact-evidence-routing/spec.md
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# File location: packs/core/tests/pack/test_impact_evidence_routing.py
#   parents[2] = packs/core/
PACK_ROOT = Path(__file__).resolve().parents[2]

# Literal paths within the pack — satisfies lint-pack-test-boundary.py.
_WORK_LOOP_SKILL = PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md"
_BUG_FIX_SKILL = PACK_ROOT / ".apm" / "skills" / "bug-fix" / "SKILL.md"


def _flat(path: Path) -> str:
    """Return the file's text with whitespace collapsed for phrase matching."""
    return " ".join(path.read_text(encoding="utf-8").split())


def test_work_loop_has_no_grep_for_callers() -> None:
    """The DECIDE execution-path check no longer says "grep for callers"."""
    assert "grep for callers" not in _flat(_WORK_LOOP_SKILL).lower()


def test_bug_fix_step_6_has_no_grep_for() -> None:
    """Step 6 of bug-fix says "search", not "Grep for"."""
    text = _flat(_BUG_FIX_SKILL)
    start = text.index("**Trace the root cause backward.**")
    end = text.index(" 7. ", start)
    assert "Grep for" not in text[start:end]


_EXPLORATION_SKILL = (
    PACK_ROOT / ".apm" / "skills" / "repository-exploration" / "SKILL.md"
)
_README = PACK_ROOT / "README.md"
_TESTS_DIR = PACK_ROOT / "tests"

_DESCRIPTION_REQUIRED = (
    "pending decision",
    "The caller keeps the decision",
    "no provider is required",
    "repository-grounding",
    "Do NOT use it to plan, build, or fix",
)
_DESCRIPTION_FORBIDDEN = (
    "blast radius",
    "what calls",
    "what depends on",
    "what breaks",
    "callers and callees",
    "find callers",
)
_PROVIDER_LITERALS = (
    "wicked estate",
    "wicked-estate",
    "code-intelligence pack",
    "code-intelligence skill",
    "`code-intelligence`",
    "packs/code-intelligence",
)


def _description(path: Path) -> str:
    """Return the single-line frontmatter ``description:`` value of a skill."""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("description: "):
            return line[len("description: "):]
    raise AssertionError(f"no description line in {path}")


def test_exploration_description_routes_pending_decisions() -> None:
    """The description carries the required phrases and none of the forbidden."""
    desc = _description(_EXPLORATION_SKILL)
    low = desc.lower()
    missing = [s for s in _DESCRIPTION_REQUIRED if s.lower() not in low]
    present = [s for s in _DESCRIPTION_FORBIDDEN if s in low]
    assert not missing, f"missing from description: {missing}"
    assert not present, f"forbidden in description: {present}"
    assert ": " not in desc, "plain YAML scalar must not contain a colon-space"


def test_pack_names_no_provider_outside_tests() -> None:
    """No shipped pack file names a provider pack, skill, or product."""
    offenders: list[str] = []
    for path in sorted(PACK_ROOT.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        if path.is_relative_to(_TESTS_DIR):
            continue
        try:
            text = path.read_text(encoding="utf-8").lower()
        except UnicodeDecodeError:
            continue
        if any(lit in text for lit in _PROVIDER_LITERALS):
            offenders.append(str(path.relative_to(PACK_ROOT)))
    assert not offenders, f"provider names found in: {offenders}"


def test_readme_exploration_section_names_both_callers() -> None:
    """The README section names both workflows that route to the skill."""
    text = _README.read_text(encoding="utf-8")
    start = text.index("## Repository exploration")
    end = text.find("\n## ", start + 1)
    section = text[start : end if end != -1 else len(text)]
    assert "`work-loop`" in section
    assert "`bug-fix`" in section


_EXPLORATION_QUERIES = (
    PACK_ROOT / ".apm" / "skills" / "repository-exploration" / "evals" / "eval_queries.json"
)
_BUG_FIX_QUERIES = PACK_ROOT / ".apm" / "skills" / "bug-fix" / "evals" / "eval_queries.json"
_EXPLORATION_EVALS = PACK_ROOT / ".apm" / "skills" / "repository-exploration" / "evals" / "evals.json"
_WORK_LOOP_EVALS = PACK_ROOT / ".apm" / "skills" / "work-loop" / "evals" / "evals.json"
_BUG_FIX_EVALS = PACK_ROOT / ".apm" / "skills" / "bug-fix" / "evals" / "evals.json"

_DECISION_MARKER = re.compile(
    r"\b(plan|planning|rename|renaming|refactor|refactoring|remove|removing|removal"
    r"|fix|fixing|finding|decide|deciding|decision|approve|approving|safe)\b",
    re.IGNORECASE,
)
_NO_PROVIDER_PHRASE = "No language-server, code-graph, or MCP capability is exposed."
_BANNED_PREFIXES = ("what calls", "what depends on", "what breaks if")


def _queries(path: Path) -> list[dict[str, object]]:
    """Load an activation-eval query list."""
    data: list[dict[str, object]] = json.loads(path.read_text(encoding="utf-8"))
    return data


def test_positive_queries_carry_a_decision_marker() -> None:
    """Every positive query names a pending decision; the fixture example does not."""
    for item in _queries(_EXPLORATION_QUERIES):
        if item["should_trigger"] is True:
            assert _DECISION_MARKER.search(str(item["query"])), item["query"]
    assert not _DECISION_MARKER.search(
        "Using the supplied fixture, list everything that depends on parse()"
    )


def test_negatives_include_bug_fix_and_implement_queries() -> None:
    """The negatives hold a bug-fix positive and an Implement request."""
    negatives = {
        str(i["query"]) for i in _queries(_EXPLORATION_QUERIES) if i["should_trigger"] is False
    }
    bug_fix_positives = {
        str(i["query"]) for i in _queries(_BUG_FIX_QUERIES) if i["should_trigger"] is True
    }
    assert negatives & bug_fix_positives
    assert any(q.startswith("Implement") for q in negatives)


def test_no_query_starts_with_a_bare_provider_question() -> None:
    """No query of either polarity opens with a bare provider-style question."""
    for item in _queries(_EXPLORATION_QUERIES):
        assert not str(item["query"]).lower().startswith(_BANNED_PREFIXES), item["query"]


def test_new_behavior_evals_state_no_provider_and_cite_search() -> None:
    """Each new case exists, states no capability is exposed, and expects search."""
    expected = (
        (_EXPLORATION_EVALS, "workflow-decision-dependents-no-provider"),
        (_WORK_LOOP_EVALS, "plan-touch-list-routes-dependents-to-exploration"),
        (_BUG_FIX_EVALS, "root-cause-trace-routes-callers-to-exploration"),
    )
    for path, case_id in expected:
        cases = {c["id"]: c for c in json.loads(path.read_text(encoding="utf-8"))["evals"]}
        assert case_id in cases, case_id
        assert _NO_PROVIDER_PHRASE in cases[case_id]["prompt"], case_id
        assert any("repository search" in a for a in cases[case_id]["assertions"]), case_id

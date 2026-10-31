"""Eval integrity tests for the github-pr skill: trigger queries, case shape, coverage, fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

EVALS = Path(__file__).resolve().parents[3] / ".apm/skills/github-pr/evals"
MODES = ("review", "iterate", "adopt")

# Behaviour criterion IDs marked (B) in the spec's Acceptance Criteria, copied once at authoring.
B_IDS = [
    "U2", "U3", "U5", "U5a", "U6", "U7", "C7a",
    "G1", "G5", "G6", "G8", "G9", "G9a", "G9b", "G9c", "G10", "G11", "G11a", "G12",
    "A2", "A3", "A5", "A5a", "A6", "A7", "A8", "A9", "A9a", "A9b", "A10", "A10a", "A11", "A12", "A13",
]  # fmt: skip

# Each case carries a `scenario` tag; E4 and E5 name the scenarios that must exist.
E4_SCENARIOS = {
    "approval-original-request-review", "approval-original-request-iterate",
    "approval-original-request-adopt", "fix-then-merge", "zero-fix-merge",
    "review-head-moves", "base-retargeted", "fork-pr-build-files",
    "review-run-tests-no-sandbox", "instruction-file-edit",
}  # fmt: skip
E5_SCENARIOS = {
    "hidden-html-comment", "ci-log-injection", "metachar-branch", "hook-config-change",
    "symlink-credential", "host-mismatch", "repo-mismatch", "contract-widening",
    "sandbox-alters-staged-iterate", "sandbox-alters-staged-adopt",
    "sandbox-writes-git-config", "sandbox-defined-by-pr-file",
}  # fmt: skip


def _cases() -> list[dict]:
    data = json.loads((EVALS / "evals.json").read_text(encoding="utf-8"))
    assert data["skill_name"] == "github-pr"
    return data["evals"]


def _queries() -> list[dict]:
    return json.loads((EVALS / "eval_queries.json").read_text(encoding="utf-8"))


def _hits(words: tuple[str, ...], flag: bool) -> list[str]:
    return [
        q["query"] for q in _queries()
        if q["should_trigger"] is flag and any(w in q["query"].lower() for w in words)
    ]  # fmt: skip


@pytest.mark.parametrize("mode,words", [
    ("review", ("review pr", "review this", "look over")),
    ("iterate", ("iterate", "feedback on my pr", "ci is red")),
    ("adopt", ("adopt", "take over")),
])  # fmt: skip
def test_s7_triggering_phrasings(mode: str, words: tuple[str, ...]) -> None:
    assert _hits(words, True), f"no triggering {mode} query"


@pytest.mark.parametrize("label,words", [
    ("open a pr", ("open a pull request", "open a pr", "create a pr")),
    ("plain merge", ("just merge", "merge pr")),
    ("auto-merge", ("auto-merge", "auto merge")),
    ("azure devops", ("azure devops",)),
])  # fmt: skip
def test_s8_non_triggering_phrasings(label: str, words: tuple[str, ...]) -> None:
    assert _hits(words, False), f"no non-triggering {label} query"


def test_queries_shape() -> None:
    for q in _queries():
        assert set(q) == {"query", "should_trigger"}
        assert isinstance(q["query"], str) and isinstance(q["should_trigger"], bool)


def test_e1_case_shape() -> None:
    cases = _cases()
    assert cases
    ids = [c["id"] for c in cases]
    assert len(ids) == len(set(ids))
    for c in cases:
        for field in ("id", "mode", "scenario", "covers", "fixtures", "expected_output", "assertions", "turns"):
            assert c.get(field), f"{c.get('id')}: missing {field}"
        assert c["mode"] in MODES
        assert len(c["assertions"]) >= 3, c["id"]
        assert all(isinstance(a, str) and a for a in c["assertions"])
        assert all(isinstance(i, str) and i for i in c["covers"])
        assert c["turns"], c["id"]
        for t in c["turns"]:
            assert isinstance(t.get("user"), str) and t["user"].strip(), c["id"]
            assert isinstance(t.get("canned"), str), c["id"]
    for mode in MODES:
        assert any(c["mode"] == mode for c in cases), f"no {mode} case"


def test_e2_every_behaviour_criterion_covered() -> None:
    covered = {i for c in _cases() for i in c["covers"]}
    assert not set(B_IDS) - covered, sorted(set(B_IDS) - covered)


def test_e3_no_symlink_under_evals() -> None:
    assert EVALS.is_dir()
    assert [str(p) for p in EVALS.rglob("*") if p.is_symlink()] == []


def test_e4_e5_required_scenarios_present() -> None:
    have = {c["scenario"] for c in _cases()}
    assert not (E4_SCENARIOS | E5_SCENARIOS) - have, sorted((E4_SCENARIOS | E5_SCENARIOS) - have)


def test_fixtures_supply_the_gather_commands_output() -> None:
    on_disk = {p.relative_to(EVALS).as_posix(): p for p in EVALS.rglob("*") if p.is_file()}
    for c in _cases():
        by_name = {rel.rsplit("/", 1)[1]: rel for rel in c["fixtures"]}
        if "pr_view.json" in by_name:
            view = json.loads(on_disk[by_name["pr_view.json"]].read_text(encoding="utf-8"))
            assert isinstance(view.get("body"), str), c["id"]
        if "origin.txt" in by_name:
            url = on_disk[by_name["origin.txt"]].read_text(encoding="utf-8")
            assert url.count("\n") == 1 and url.endswith(".git\n") and "\t" not in url, c["id"]


def test_fixtures_exist_and_are_regular() -> None:
    regular = {
        f.relative_to(EVALS).as_posix()
        for f in EVALS.rglob("*")
        if f.is_file() and not f.is_symlink()
    }
    for c in _cases():
        for rel in c["fixtures"]:
            assert rel.startswith(f"files/{c['id']}/"), rel
            assert rel in regular, rel

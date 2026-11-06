"""Anchor facts for the review tiers (review-obligation-policy T4, AC-0013).

The supervisor records one ``delivery/review-anchors.jsonl`` line per anchor round.
The classifier reads the anchor result, run base, changed paths, and patch ids
from the last line only, so an adopted rebase that rewrites the run's commits
does not change what it compares against. Real throwaway Git repositories.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

_HELPER = Path(__file__).resolve().parent / "supervisor_harness.py"


def _harness() -> ModuleType:
    alias = "core_work_loop_supervisor_harness"
    if alias not in sys.modules:
        spec = importlib.util.spec_from_file_location(alias, _HELPER)
        assert spec is not None and spec.loader is not None
        sys.modules[alias] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sys.modules[alias])
    return sys.modules[alias]


h = _harness()
tiers = h.cli._supervisor("_review_tiers.py")
commit_mod = h.cli._supervisor("_supervisor_commit.py")
review = h.cli._supervisor("_supervisor_review.py")
RULES: dict[str, Any] = review.load_rules()
CODE = "src/app.py"
RUN = "run-0123456789abcdef"


class Repo:
    """A throwaway repository with a supervisor Git port."""

    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir()
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "tests@example.invalid")
        self.git("config", "user.name", "tests")
        self.base = self.write({CODE: "".join(f"line{i}\n" for i in range(30))})
        self.port = commit_mod.GitPort(root, "docs/specs/calc", clock=lambda: "2026-11-05T00:00:00Z")

    def git(self, *args: str) -> str:
        done = subprocess.run(
            ["git", "-C", str(self.root), *args],
            capture_output=True,
            check=True,
            env={**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"},
        )
        return done.stdout.decode().strip()

    def write(self, files: dict[str, str]) -> str:
        for name, body in files.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", "step")
        return self.git("rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> Repo:
    return Repo(tmp_path / "repo")


class Ledger:
    """A workspace whose ``delivery/`` holds only the anchor file."""

    def __init__(self) -> None:
        self.files: dict[str, bytes] = {}
        self.git = SimpleNamespace(delivery_rel="delivery", show=self._show)
        self.ws = SimpleNamespace(git=self.git)

    def _show(self, rel: str) -> bytes | None:
        return self.files.get(rel.split("/", 1)[1])

    def append(self, record: dict[str, Any]) -> None:
        name = review.ANCHORS_FILE
        self.files[name] = self.files.get(name, b"") + json.dumps(record).encode() + b"\n"


def _record(repo: Repo, result: str, round_number: int = 1, **over: Any) -> dict[str, Any]:
    args: dict[str, Any] = {
        "run_id": RUN,
        "round_number": round_number,
        "review_subject_fingerprint": f"subject-{round_number}",
        "review_policy_fingerprint": "review-policy-t4",
        "anchor_result": result,
        "run_base": repo.base,
        "changed_paths": [CODE],
    }
    args.update(over)
    return review.anchor_record(repo.port, **args)


def _edit(line: int, text: str) -> str:
    lines = [f"line{i}" for i in range(30)]
    lines[line] = text
    return "\n".join(lines) + "\n"


def test_ac0013_each_anchor_round_appends_one_line_and_the_reader_returns_the_last() -> None:
    ledger = Ledger()
    assert review.latest_anchor(ledger.ws) is None
    first = {"run_id": RUN, "round": 1, "review_subject_fingerprint": "s1",
             "review_policy_fingerprint": "p", "anchor_result": "a" * 40, "run_base": None,
             "changed_paths": ["a.py", "b.py"], "patch_ids": None}
    second = {**first, "round": 2, "anchor_result": "b" * 40, "run_base": "c" * 40,
              "patch_ids": {"a.py": "1", "b.py": "2"}}
    ledger.append(first)
    ledger.append(second)
    assert len(review.parse_anchors(ledger.files[review.ANCHORS_FILE])) == 2
    facts = review.latest_anchor(ledger.ws)
    assert facts == tiers.AnchorFacts(
        "b" * 40, "c" * 40, frozenset({"a.py", "b.py"}), {"a.py": "1", "b.py": "2"}
    )


def test_ac0013_the_builder_records_patch_ids_only_when_they_can_be_trusted(
    repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    result = repo.write({CODE: _edit(2, "LINE2")})
    record = _record(repo, result)
    assert record["patch_ids"] == {CODE: repo.port.patch_id(repo.base, result, CODE)}
    assert record["changed_paths"] == [CODE] and record["round"] == 1
    assert _record(repo, result, run_base=None)["patch_ids"] is None
    monkeypatch.setattr(repo.port, "git_version", lambda: (2, 38))
    assert _record(repo, result)["patch_ids"] is None


def test_ac0013_after_a_rebase_the_classifier_compares_against_the_recorded_facts(
    repo: Repo,
) -> None:
    anchor_result = repo.write({CODE: _edit(2, "LINE2")})
    ledger = Ledger()
    ledger.append(_record(repo, anchor_result))

    # An adopted rebase: upstream edits another line of the run's path, and the
    # run's commits are rewritten on the new base.
    repo.git("checkout", "-q", repo.base)
    new_base = repo.write({CODE: _edit(25, "UPSTREAM")})
    current = repo.write({CODE: _edit(25, "UPSTREAM").replace("line2\n", "LINE2\n")})
    rewritten = subprocess.run(
        ["git", "-C", str(repo.root), "merge-base", "--is-ancestor", anchor_result, current],
        capture_output=True,
    )
    assert rewritten.returncode != 0  # the recorded anchor is no longer in the history

    facts = review.latest_anchor(ledger.ws)
    assert facts.anchor_result == anchor_result and facts.run_base == repo.base
    tier = tiers.classify(
        repo.port, RULES, facts, current=current, changed={CODE}, run_base=new_base,
        open_findings=False, adopted_reanchor=True, spec_dir_changed=False,
        selection_changed=False, review_tier=None,
    )
    assert tier.name == "rebase"


@pytest.mark.parametrize(
    "raw",
    [
        b'{"run_id": "r"}',
        b"not json\n",
        b"[]\n",
    ],
    ids=["truncated", "not-json", "not-an-object"],
)
def test_ac0013_a_malformed_ledger_refuses_with_a_named_error(raw: bytes) -> None:
    with pytest.raises(review.Refusal) as refused:
        review.parse_anchors(raw)
    assert refused.value.code == "review-anchor-invalid"


def test_ac0013_a_line_with_an_unsorted_path_list_an_extra_field_or_bad_ids_refuses() -> None:
    good = {"run_id": RUN, "round": 1, "review_subject_fingerprint": "s",
            "review_policy_fingerprint": "p", "anchor_result": "a" * 40, "run_base": None,
            "changed_paths": ["a", "b"], "patch_ids": {"a": "1", "b": "2"}}
    assert review.parse_anchors(json.dumps(good).encode() + b"\n") == [good]
    for bad in (
        {**good, "changed_paths": ["b", "a"]},
        {**good, "extra": 1},
        {**good, "round": 0},
        {**good, "round": True},
        {**good, "patch_ids": {"a": "1"}},
        {**good, "patch_ids": {"a": "1", "b": 2}},
        {k: v for k, v in good.items() if k != "run_base"},
    ):
        with pytest.raises(review.Refusal) as refused:
            review.parse_anchors(json.dumps(bad).encode() + b"\n")
        assert refused.value.code == "review-anchor-invalid"

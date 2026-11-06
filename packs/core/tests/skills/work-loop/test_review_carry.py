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
readiness = h.cli._supervisor("_supervisor_readiness.py")
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


# ── AC-0013: an anchor line the parser would refuse is never written ────────


def test_ac0013_a_touched_then_restored_path_is_recorded_in_a_form_the_parser_accepts(
    repo: Repo,
) -> None:
    repo.write({CODE: _edit(2, "LINE2")})
    result = repo.write({CODE: "".join(f"line{i}\n" for i in range(30))})  # restored to the base
    record = _record(repo, result)
    assert record["patch_ids"] == {CODE: ""}
    parsed = review.parse_anchors(json.dumps(record).encode() + b"\n")
    assert parsed == [record]
    ledger = Ledger()
    ledger.append(record)
    facts = review.latest_anchor(ledger.ws)
    assert facts.patch_ids == {CODE: ""}
    # The classifier reads the empty patch as "no change", so an unchanged restore is a rebase.
    why = tiers._rebase_refusal(
        repo.port, facts, result, repo.base, frozenset({CODE}),
        open_findings=False, spec_dir_changed=False,
    )
    assert why is None


def test_ac0013_a_line_the_parser_refuses_is_not_returned_for_the_commit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bad = {"run_id": RUN, "round": 1, "review_subject_fingerprint": "s",
           "review_policy_fingerprint": "p", "anchor_result": "a" * 40, "run_base": None,
           "changed_paths": ["b", "a"], "patch_ids": None}  # unsorted: the parser refuses it
    monkeypatch.setattr(readiness._review, "anchor_record", lambda git, **kw: bad)
    monkeypatch.setattr(readiness._review, "anchor_records", lambda ws: [])
    monkeypatch.setattr(readiness, "result_lineage", lambda ws, state: ("p", "a" * 40, "1"))
    monkeypatch.setattr(readiness, "run_base", lambda ws, state, result: None)
    reports = SimpleNamespace(get_semantic_records=lambda kind: [])
    ws = SimpleNamespace(git=SimpleNamespace(), open_evidence=lambda: reports)
    state = SimpleNamespace(run_id=RUN)
    view = {
        "flow": {"current_is_round": True, "roles": ["a"], "rounds_with_current": 1},
        "review_subject": {"review_subject_fingerprint": "s", "review_policy_fingerprint": "p"},
        "selection": {"changed_files": [{"path": "a"}, {"path": "b"}]},
    }
    line, why = readiness._anchor_line(ws, state, view, "a", {"terminal_status": "complete"})
    assert line is None
    assert "review-anchor-invalid" in why and why == why.strip() and "\n" not in why
    good = {**bad, "changed_paths": ["a", "b"]}
    monkeypatch.setattr(readiness._review, "anchor_record", lambda git, **kw: good)
    assert readiness._anchor_line(ws, state, view, "a", {"terminal_status": "complete"}) == (
        good, "",
    )


def test_one_builder_makes_the_anchor_facts_production_and_the_reader_use() -> None:
    line = {"run_id": RUN, "round": 1, "review_subject_fingerprint": "s",
            "review_policy_fingerprint": "p", "anchor_result": "a" * 40, "run_base": None,
            "changed_paths": ["a.py"], "patch_ids": None}
    ledger = Ledger()
    ledger.append(line)
    assert review.latest_anchor(ledger.ws) == review.anchor_facts(line)
    source = Path(readiness.__file__).read_text(encoding="utf-8")
    assert "AnchorFacts(" not in source and "_review.anchor_facts(line)" in source


# ── AC-0023: only the run's own repair is a round ───────────────────────────


def _fp(letter: str) -> str:
    return letter * 24


def _step(operation: str, name: str) -> SimpleNamespace:
    return SimpleNamespace(operation=operation, step=name)


def _subjects(*letters: str) -> list[dict[str, str]]:
    return [{"fp": _fp(letter), "acceptance": f"acceptance-{letter}"} for letter in letters]


def _rounds(
    monkeypatch: pytest.MonkeyPatch,
    commits: list[SimpleNamespace],
    *letters: str,
    current_reviewed: bool = True,
) -> tuple[int, bool]:
    monkeypatch.setattr(readiness, "_raised", lambda store, reports, fp: [{"role": "r"}])
    subjects = _subjects(*letters)
    reviewed = subjects if current_reviewed else subjects[:-1]
    return readiness._rounds(None, [], reviewed, subjects[-1], commits)


def test_ac0023_a_subject_changed_only_by_an_adopted_reanchor_is_not_a_round(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commits = [
        _step("implement", "implement:T1"),
        _step("review", f"review:adversarial-reviewer:{_fp('a')}:1"),
        _step("reanchor", "reanchor:upstream"),
        _step("review", f"review:adversarial-reviewer:{_fp('b')}:1"),
    ]
    assert _rounds(monkeypatch, commits, "a", "b") == (1, False)


def test_ac0023_a_subject_first_reached_after_the_runs_own_repair_is_a_round(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    commits = [
        _step("implement", "implement:T1"),
        _step("review", f"review:adversarial-reviewer:{_fp('a')}:1"),
        _step("implement", "implement:T1-repair"),
        _step("reanchor", "reanchor:upstream"),
        _step("review", f"review:adversarial-reviewer:{_fp('b')}:1"),
    ]
    assert _rounds(monkeypatch, commits, "a", "b") == (2, True)


def test_ac0023_a_current_subject_with_no_review_yet_counts_its_pending_repair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reanchor_only = [
        _step("review", f"review:adversarial-reviewer:{_fp('a')}:1"),
        _step("reanchor", "reanchor:upstream"),
    ]
    assert _rounds(monkeypatch, reanchor_only, "a", "b", current_reviewed=False) == (1, False)
    repaired = [*reanchor_only[:1], _step("implement", "implement:T1-repair")]
    assert _rounds(monkeypatch, repaired, "a", "b", current_reviewed=False) == (1, True)


def test_ac0023_a_subject_whose_commits_cannot_be_found_still_counts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert _rounds(monkeypatch, [], "a", "b") == (2, True)


# ── QE-3: the run base names why it is undefined; one cache per workspace ──


def test_the_run_base_names_the_condition_that_left_it_undefined(repo: Repo) -> None:
    first = repo.write({CODE: _edit(2, "LINE2")})
    head = repo.write({CODE: _edit(3, "LINE3")})
    mine = SimpleNamespace(sha=first, operation="implement")
    ws = SimpleNamespace(git=repo.port)
    assert readiness.run_base_checked(ws, SimpleNamespace(commits=[]), head)[1].startswith(
        "the run has no stub or implement commit"
    )
    foreign = readiness.run_base_checked(ws, SimpleNamespace(commits=[mine]), head)
    assert foreign[0] is None and "is not the run's" in foreign[1]
    both = SimpleNamespace(sha=head, operation="implement")
    assert readiness.run_base_checked(ws, SimpleNamespace(commits=[mine, both]), head) == (
        repo.base, "",
    )
    capped = SimpleNamespace(
        resolve=repo.port.resolve,
        rev_list=lambda base, result, limit=None: repo.port.rev_list(base, result, limit=5),
    )
    limited = readiness.run_base_checked(
        SimpleNamespace(git=capped), SimpleNamespace(commits=[mine, both]), head
    )
    assert limited[0] is None and "denied-git-output-too-large" in limited[1]


def test_a_memoized_answer_is_computed_once_per_workspace_object() -> None:
    ws = SimpleNamespace()
    calls: list[int] = []
    for _ in range(3):
        readiness._memoized(ws, ("k", 1), lambda: calls.append(1) or "v")
    readiness._memoized(ws, ("k", 2), lambda: calls.append(2) or "w")
    assert calls == [1, 2]

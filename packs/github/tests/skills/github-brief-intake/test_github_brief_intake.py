"""Construction tests for GitHub normalized intake."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[3] / ".apm/skills/github-brief-intake"


def _load_adapter():
    path = SKILL_ROOT / "scripts/intake_adapter.py"
    spec = importlib.util.spec_from_file_location("github_intake_adapter", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_github_normalizes_routes() -> None:
    adapter = _load_adapter()
    matrix = json.loads(
        (SKILL_ROOT / "evals/files/intake/matrix.json").read_text(encoding="utf-8")
    )
    profile = adapter.load_profile()
    for case in matrix["cases"]:
        handed_off: list[dict[str, object]] = []
        expected = case["normalized"]
        result = adapter.emit_and_handoff(
            content=expected["content"],
            requested_locator=expected["source"]["locator"],
            acquired=case["raw"],
            constraints=expected["constraints"],
            profile=profile,
            invoke_work_intake=lambda record, sink=handed_off: sink.append(record)
            or "accepted",
        )
        assert result == "accepted"
        assert handed_off == [expected]

    with pytest.raises(adapter.IntakePolicyError):
        adapter.emit_and_handoff(
            content=matrix["cases"][0]["normalized"]["content"],
            requested_locator="gh://items/999",
            acquired=matrix["cases"][0]["raw"],
            constraints={},
            profile=profile,
            invoke_work_intake=lambda record: record,
        )

    invented = json.loads(json.dumps(matrix["cases"][0]["normalized"]["content"]))
    invented["outcomes"] = ["Invented outcome absent from GitHub."]
    with pytest.raises(adapter.IntakePolicyError, match="not grounded"):
        adapter.emit_and_handoff(
            content=invented,
            requested_locator="gh://items/101",
            acquired=matrix["cases"][0]["raw"],
            constraints=matrix["cases"][0]["normalized"]["constraints"],
            profile=profile,
            invoke_work_intake=lambda record: record,
        )


def test_github_rejects_untrusted_hostname_before_gh() -> None:
    adapter = _load_adapter()
    profile = adapter.load_profile()
    calls: list[list[str]] = []

    def fake_runner(argv: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "[]", "")

    adapter.run_gh_read(
        "issues",
        configured_host="github.com",
        repository="example-org/example-repo",
        selector="release; touch /tmp/never",
        profile=profile,
        runner=fake_runner,
    )
    assert len(calls) == 1
    argv = calls[0]
    assert argv[argv.index("--milestone") + 1] == "release; touch /tmp/never"

    calls.clear()
    with pytest.raises(adapter.IntakePolicyError):
        adapter.run_gh_read(
            "issues",
            configured_host="github.com",
            repository="example-org/example-repo",
            selector="release",
            profile=profile,
            payload_host="attacker.example",
            runner=fake_runner,
        )
    assert calls == []

    with pytest.raises(adapter.IntakePolicyError):
        adapter.run_gh_read(
            "issues",
            configured_host="attacker.example",
            repository="example-org/example-repo",
            selector="release",
            profile=profile,
            runner=fake_runner,
        )


def test_github_resource_budget() -> None:
    adapter = _load_adapter()
    profile = adapter.load_profile()
    assert adapter.budget_result(pages=5, items=100, response_bytes=2097152, profile=profile) == {
        "complete": True,
        "result": "complete",
    }
    assert adapter.budget_result(pages=6, items=100, response_bytes=1, profile=profile) == {
        "complete": False,
        "result": "marked-incomplete",
    }

    def oversized_runner(
        argv: list[str], **_: object
    ) -> subprocess.CompletedProcess[str]:
        output = '"' + "x" * profile["budget"]["max_bytes"] + '"'
        return subprocess.CompletedProcess(argv, 0, output, "")

    with pytest.raises(adapter.IntakePolicyError):
        adapter.run_gh_read(
            "issues",
            configured_host="github.com",
            repository="example-org/example-repo",
            selector="release",
            profile=profile,
            runner=oversized_runner,
        )

    def invalid_runner(
        argv: list[str], **_: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(argv, 0, "[NaN]", "")

    with pytest.raises(adapter.IntakePolicyError):
        adapter.run_gh_read(
            "issues",
            configured_host="github.com",
            repository="example-org/example-repo",
            selector="release",
            profile=profile,
            runner=invalid_runner,
        )

    attempts = 0
    delays: list[float] = []

    def retrying_runner(
        argv: list[str], **_: object
    ) -> subprocess.CompletedProcess[str]:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise subprocess.CalledProcessError(1, argv)
        return subprocess.CompletedProcess(argv, 0, "[]", "")

    adapter.run_gh_read(
        "issues",
        configured_host="github.com",
        repository="example-org/example-repo",
        selector="release",
        profile=profile,
        runner=retrying_runner,
        sleeper=delays.append,
    )
    assert attempts == 2
    assert delays == [1.0]

    with pytest.raises(adapter.IntakePolicyError, match="retry budget"):
        adapter.run_gh_read(
            "issues",
            configured_host="github.com",
            repository="example-org/example-repo",
            selector="release",
            profile=profile,
            runner=lambda argv, **kwargs: (_ for _ in ()).throw(
                subprocess.TimeoutExpired(argv, kwargs["timeout"])
            ),
            sleeper=lambda _delay: None,
        )

    reads: list[int] = []
    killed: list[bool] = []

    class OversizedPipe:
        def read(self, size: int) -> bytes:
            reads.append(size)
            return b"x" * size

    captured, exceeded = adapter._read_bounded_pipe(
        OversizedPipe(), 8, lambda: killed.append(True)
    )
    assert captured == b"x" * 8
    assert exceeded is True
    assert reads == [9]
    assert killed == [True]


def test_github_boundary_metadata() -> None:
    body = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "allowed-tools: Read Bash" in body
    assert "network_fetch" in body
    assert "filesystem_read_untrusted" in body
    assert "filesystem_write" in body
    assert "missing dependency: work-intake" in body
    assert "Never use `gh issue create`, `edit`, `close`, `comment`" in body

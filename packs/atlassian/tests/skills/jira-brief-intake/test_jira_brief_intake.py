"""Construction tests for Jira normalized intake."""

from __future__ import annotations

import importlib.util
import json
import socket
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[3] / ".apm/skills/jira-brief-intake"


def _load_adapter():
    path = SKILL_ROOT / "scripts/intake_adapter.py"
    spec = importlib.util.spec_from_file_location("jira_intake_adapter", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _public_resolver(host: str, port: int, **_: object):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]


def test_jira_normalizes_routes() -> None:
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
            requested_locator="jira://EX-999",
            acquired=matrix["cases"][0]["raw"],
            constraints={},
            profile=profile,
            invoke_work_intake=lambda record: record,
        )

    invented = json.loads(json.dumps(matrix["cases"][0]["normalized"]["content"]))
    invented["outcomes"] = ["Invented outcome absent from Jira."]
    with pytest.raises(adapter.IntakePolicyError, match="not grounded"):
        adapter.emit_and_handoff(
            content=invented,
            requested_locator="jira://EX-101",
            acquired=matrix["cases"][0]["raw"],
            constraints=matrix["cases"][0]["normalized"]["constraints"],
            profile=profile,
            invoke_work_intake=lambda record: record,
        )


def test_jira_ssrf_precedes_credentials() -> None:
    adapter = _load_adapter()
    profile = adapter.load_profile()
    events: list[str] = []

    def load_credentials() -> str:
        events.append("credentials")
        return "opaque"

    adapter.validate_before_credentials(
        "https://tracker.example.test", profile, load_credentials, resolver=_public_resolver
    )
    assert events == ["credentials"]

    events.clear()
    with pytest.raises(adapter.IntakePolicyError):
        adapter.validate_before_credentials(
            "http://tracker.example.test", profile, load_credentials, resolver=_public_resolver
        )
    assert events == []

    def private_resolver(host: str, port: int, **_: object):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))]

    with pytest.raises(adapter.IntakePolicyError):
        adapter.validate_destination(
            "https://tracker.example.test", profile, resolver=private_resolver
        )


def test_jira_resource_budget() -> None:
    adapter = _load_adapter()
    profile = adapter.load_profile()
    assert adapter.budget_result(pages=5, items=250, response_bytes=2097152, profile=profile) == {
        "complete": True,
        "result": "complete",
    }
    assert adapter.budget_result(pages=6, items=250, response_bytes=1, profile=profile) == {
        "complete": False,
        "result": "marked-incomplete",
    }


def test_jira_boundary_metadata() -> None:
    body = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "allowed-tools: Read Bash" in body
    assert "network_fetch" in body
    assert "filesystem_read_untrusted" in body
    assert "filesystem_write" in body
    assert "missing dependency: work-intake" in body
    assert "create, update, delete, transition" in body

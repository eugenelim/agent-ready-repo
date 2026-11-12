"""Run the native-decision caller through the shipped CLI without network access."""

from __future__ import annotations

import importlib.util
import json
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / ".apm/skills/generate-iac/scripts/plan_bundle.py"
EXAMPLE = (
    Path(__file__).resolve().parents[3]
    / ".apm/skills/generate-iac/assets/native-adr-caller"
)
NOW = "2026-01-01T12:30:00Z"
FILES = (
    "README.md",
    "decision.md",
    "saved-plan.synthetic",
    "inspection.json",
    ".terraform.lock.hcl",
    "validation.txt",
    "policy.txt",
    "security.txt",
    "review.txt",
    "iac-plan-bundle.v1.json",
    "trusted-policy.json",
)
# Install the sentinel inside the child that executes the real __main__ entry point.
OFFLINE_ENTRY_POINT = """
import runpy
import socket
import sys
import urllib.request

def refuse(*args, **kwargs):
    raise AssertionError("network access attempted")

socket.socket = refuse
urllib.request.urlopen = refuse
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""


@pytest.fixture(scope="module")
def caller_module() -> Any:
    """Load the existing confined readers under a pack-qualified identity."""
    spec = importlib.util.spec_from_file_location(
        "iac_terraform_generate_iac_plan_bundle_caller", SCRIPT
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def no_network(monkeypatch: Any) -> None:
    """Refuse network calls in parent-side validation as well as the CLI child."""

    def refuse(*args: Any, **kwargs: Any) -> None:
        """Fail immediately if validation attempts a fetch."""
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(urllib.request, "urlopen", refuse)


@pytest.fixture
def caller_root(caller_module: Any, tmp_path: Path) -> Path:
    """Copy shipped bytes through the validator's bounded confined reader."""
    for name in FILES:
        (tmp_path / name).write_bytes(caller_module.read_manifest(EXAMPLE, name))
    return tmp_path


def run_cli(root: Path) -> subprocess.CompletedProcess[str]:
    """Exercise argv, entry-point output and exit status in a guarded process."""
    return subprocess.run(
        [
            sys.executable,
            "-c",
            OFFLINE_ENTRY_POINT,
            str(SCRIPT),
            "validate",
            "iac-plan-bundle.v1.json",
            "--root",
            str(root),
            "--policy",
            "trusted-policy.json",
            "--now",
            NOW,
        ],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=30,
    )


def test_caller_cli_integration_and_saved_plan_tamper(
    caller_module: Any, caller_root: Path
) -> None:
    """A portable copy validates; one altered saved-plan byte breaks that journey."""
    completed = run_cli(caller_root)
    assert completed.returncode == 0, completed.stdout
    assert completed.stderr == ""
    result = json.loads(completed.stdout)
    assert result == {
        "status": "valid",
        "issues": [],
        "evidence": [
            {"id": identifier, "verification": "verified"}
            for identifier in (
                "native-decision",
                "saved-plan",
                "plan-inspection",
                "dependency-lock",
                "validation-proof",
                "policy-proof",
                "security-proof",
                "review-proof",
            )
        ],
    }
    saved = caller_module.read_manifest(caller_root, "saved-plan.synthetic")
    (caller_root / "saved-plan.synthetic").write_bytes(bytes([saved[0] ^ 1]) + saved[1:])
    completed = run_cli(caller_root)
    assert completed.returncode == 1
    assert completed.stderr == ""
    result = json.loads(completed.stdout)
    assert result["status"] == "invalid"
    assert {issue["code"] for issue in result["issues"]} == {
        "digest-mismatch", "missing-evidence"
    }
    assert {"code": "digest-mismatch", "path": "$.evidence[1].sha256"} in result["issues"]


def test_native_decision_is_request_and_constraint(caller_module: Any, caller_root: Path) -> None:
    """Both governance references resolve to the shipped adopter decision bytes."""
    bundle = caller_module.parse_json(
        caller_module.read_manifest(caller_root, "iac-plan-bundle.v1.json")
    )
    assert bundle["request"] == "native-decision"
    assert bundle["constraints"] == ["native-decision"]
    decision = next(item for item in bundle["evidence"] if item["id"] == "native-decision")
    assert decision["locator"] == "decision.md"
    assert decision["sha256"] == caller_module.hash_evidence(caller_root, "decision.md")
    markdown = caller_module.read_manifest(caller_root, "decision.md").decode("utf-8")
    assert "## Context and Problem Statement" in markdown
    assert "## Decision Outcome" in markdown
    assert not markdown.startswith("---")


def test_caller_cli_external_evidence_never_fetches(caller_module: Any, caller_root: Path) -> None:
    """An external check report stays incomplete under the child network sentinel."""
    bundle = caller_module.parse_json(
        caller_module.read_manifest(caller_root, "iac-plan-bundle.v1.json")
    )
    bundle["evidence"][4]["locator"] = "https://example.invalid/validation.txt"
    (caller_root / "iac-plan-bundle.v1.json").write_text(json.dumps(bundle), encoding="utf-8")
    completed = run_cli(caller_root)
    assert completed.returncode == 1
    assert completed.stderr == ""
    result = json.loads(completed.stdout)
    assert result["status"] == "incomplete"
    assert {"id": "validation-proof", "verification": "unverified"} in result["evidence"]
    assert "unverified-evidence" in {issue["code"] for issue in result["issues"]}

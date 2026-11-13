"""Drive the shipped image-only example through the real CLI without network access."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

PACK = Path(__file__).resolve().parents[3]
SCRIPT = PACK / ".apm/skills/release-loop/scripts/release_handoff.py"
EXAMPLE = PACK / ".apm/skills/release-loop/assets/image-only-ci-caller"
spec = importlib.util.spec_from_file_location(
    "release_engineering_release_loop_release_handoff", SCRIPT
)
assert spec and spec.loader
handoff = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = handoff
spec.loader.exec_module(handoff)

NOW = "2026-01-01T12:30:00Z"
FILES = (
    "README.md",
    "ci-workflow.example.yml",
    "release-handoff.yaml",
    "trusted-policy.json",
    "image-manifest.json",
    "provenance-attestation.json",
    "test-report.json",
    "security-report.json",
    "approved-procedure.txt",
)

# Run the actual __main__ block with a sentinel in the child interpreter too.
NO_NETWORK_ENTRY = """
import runpy
import socket
import sys
import urllib.request

def no_network(*args: object, **kwargs: object) -> None:
    raise AssertionError("network forbidden")

socket.socket = no_network
urllib.request.urlopen = no_network
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""


@pytest.mark.parametrize("remove", [None, "tag", "digest"])
def test_image_only_caller_cli_integration(tmp_path: Path, remove: str | None) -> None:
    """Accept the copied caller and reject each incomplete image reference."""
    for name in FILES:
        (tmp_path / name).write_bytes(handoff.read_manifest(EXAMPLE, name))
    raw = handoff.read_manifest(tmp_path, "release-handoff.yaml")
    candidate = handoff.parse_yaml(raw)
    assert [item["kind"] for item in candidate["components"]] == ["oci-image"]
    original = candidate["components"][0]["image_ref"]
    if remove == "tag":
        changed = original.split("@", 1)[0].rsplit(":", 1)[0] + "@" + original.split("@", 1)[1]
        raw = raw.replace(original.encode(), changed.encode())
    elif remove == "digest":
        raw = raw.replace(original.encode(), original.split("@", 1)[0].encode())
    (tmp_path / "release-handoff.yaml").write_bytes(raw)
    proc = subprocess.run(
        [
            sys.executable,
            "-c",
            NO_NETWORK_ENTRY,
            str(SCRIPT),
            "validate",
            "release-handoff.yaml",
            "--root",
            str(tmp_path),
            "--policy",
            "trusted-policy.json",
            "--now",
            NOW,
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
        check=False,
    )
    result: dict[str, Any] = json.loads(proc.stdout)
    assert proc.stderr == ""
    assert set(result) == {"status", "issues", "evidence"}
    if remove is None:
        assert proc.returncode == 0, result
        assert result == {
            "status": "valid",
            "issues": [],
            "evidence": [
                {"id": item["id"], "verification": "verified"} for item in candidate["evidence"]
            ],
        }
    else:
        assert proc.returncode == 1, result
        assert result["status"] == "invalid", result
        assert result["issues"] == [
            {"code": "invalid-image-reference", "path": "$.components[0].image_ref"}
        ]


@pytest.mark.parametrize("quote", ["'", '"'])
@pytest.mark.parametrize("ending", ["\n", "\r\n"])
def test_quoted_unicode_caller(tmp_path: Path, monkeypatch: Any, quote: str, ending: str) -> None:
    """Only physical LF or CRLF separates lines inside the shipped caller."""
    import socket
    import urllib.request

    def refuse(*args: Any, **kwargs: Any) -> None:
        """Fail if validation attempts any fetch."""
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    for name in FILES:
        (tmp_path / name).write_bytes(handoff.read_manifest(EXAMPLE, name))
    raw = handoff.read_manifest(tmp_path, "release-handoff.yaml")
    text = "before\u2028middle\u2029next\u0085last\fafter"
    # JSON requires a control-character escape in double-quoted strings.
    scalar = text.replace("\f", "\\f") if quote == '"' else text
    raw += ("\nextensions:\n  text: " + quote + scalar + quote + "\n").encode()
    raw = raw.replace(b"\n", ending.encode())
    assert handoff.parse_yaml(raw)["extensions"]["text"] == text
    policy = handoff.parse_json(handoff.read_manifest(tmp_path, "trusted-policy.json"))
    assert handoff.validate_bytes(raw, root=tmp_path, policy=policy, now=NOW)["status"] == "valid"

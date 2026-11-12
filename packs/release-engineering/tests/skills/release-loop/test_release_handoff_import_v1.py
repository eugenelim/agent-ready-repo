"""Prove read-only legacy translation and exclusive confined publication."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

import pytest

PACK = Path(__file__).resolve().parents[3]
SCRIPT = PACK / ".apm/skills/release-loop/scripts/release_handoff.py"
EXAMPLE = PACK / ".apm/skills/release-loop/assets/image-only-ci-caller"
FIXTURES = Path(__file__).resolve().parent / "fixtures/v1"
spec = importlib.util.spec_from_file_location(
    "release_engineering_release_loop_release_handoff", SCRIPT
)
assert spec and spec.loader
handoff = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = handoff
spec.loader.exec_module(handoff)
NOW = "2026-01-01T12:30:00Z"


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Any network attempt fails the suite."""

    def refuse(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(urllib.request, "urlopen", refuse)


@pytest.fixture
def workspace(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """Copy only the pack's synthetic caller evidence and legacy fixture."""
    candidate = handoff.parse_yaml(handoff.read_manifest(EXAMPLE, "release-handoff.yaml"))
    for evidence in candidate["evidence"]:
        name = evidence["locator"]
        (tmp_path / name).write_bytes(handoff.read_manifest(EXAMPLE, name))
    (tmp_path / "policy.json").write_bytes(handoff.read_manifest(EXAMPLE, "trusted-policy.json"))
    (tmp_path / "input.yaml").write_bytes(handoff.read_manifest(FIXTURES, "image.yaml"))
    # Each legacy check needs its own identity, stage and actual bound evidence.
    test = candidate["checks"][0]
    security = candidate["checks"][1]
    candidate["checks"] = []
    for name in ("unit", "integration", "lint", "security_scan"):
        item = copy.deepcopy(security if name == "security_scan" else test)
        item["id"] = name
        item["stage"] = name
        candidate["checks"].append(item)
    policy = json.loads((tmp_path / "policy.json").read_bytes())
    policy["required_checks"] = []
    (tmp_path / "policy.json").write_text(json.dumps(policy))
    (tmp_path / "supplement.json").write_text(json.dumps(candidate))
    return tmp_path, candidate


def run_import(root: Path, **kwargs: Any) -> dict[str, Any]:
    """Snapshot the source around every successful or refused import call."""
    source = root / "input.yaml"
    before = source.read_bytes()
    try:
        return handoff.import_v1(
            "input.yaml",
            output=kwargs.pop("output", "output.yaml"),
            root=root,
            policy="policy.json",
            now=NOW,
            **kwargs,
        )
    finally:
        assert source.read_bytes() == before


def codes(result: dict[str, Any]) -> set[str]:
    """Read only fixed issue codes."""
    return {item["code"] for item in result["issues"]}


def test_incomplete(workspace: Any) -> None:
    """A claim carries no bound proof; absent facts stay absent."""
    root, _ = workspace
    result = run_import(root)
    assert result["status"] == "incomplete", result
    candidate = handoff.parse_yaml((root / "output.yaml").read_bytes())
    assert candidate["schema_version"] == "2.0"
    assert "target" not in candidate and "candidate_id" not in candidate
    assert candidate["created_at"] == "2026-01-01T12:00:00Z"
    assert candidate["producer"] == "example-ci"
    assert candidate["changes"]["baseline"] == "v0.9.0"
    assert all(check["status"] == "not-run" for check in candidate["checks"])
    assert all(
        "subjects" not in check and "evidence" not in check for check in candidate["checks"]
    )
    paths = {item["path"] for item in result["issues"] if item["code"] == "missing-field"}
    assert {"$.target", "$.sources", "$.repair_owner", "$.components[0].artifact"} <= paths
    for index in range(4):
        assert {"code": "missing-evidence", "path": f"$.checks[{index}]"} in result["issues"]
    assert (
        handoff.validate_bytes(
            (root / "output.yaml").read_bytes(),
            root=root,
            policy=json.loads((root / "policy.json").read_bytes()),
            now=NOW,
        )["status"]
        == "incomplete"
    )


def test_complete_cli_integration(workspace: Any, capsys: pytest.CaptureFixture[str]) -> None:
    """Exercise both real command routes and one-object JSON stdout."""
    root, _ = workspace
    before = (root / "input.yaml").read_bytes()
    try:
        status = handoff.main([
            "import-v1",
            "input.yaml",
            "--output",
            "output.yaml",
            "--root",
            str(root),
            "--policy",
            "policy.json",
            "--supplement",
            "supplement.json",
            "--now",
            NOW,
        ])
        captured = capsys.readouterr()
        assert status == 0, captured
        assert json.loads(captured.out)["status"] == "valid" and captured.err == ""
        assert (
            handoff.main([
                "validate",
                "output.yaml",
                "--root",
                str(root),
                "--policy",
                "policy.json",
                "--now",
                NOW,
            ])
            == 0
        )
        assert json.loads(capsys.readouterr().out)["status"] == "valid"
    finally:
        assert (root / "input.yaml").read_bytes() == before


@pytest.mark.parametrize("output", ["input.yaml", "./input.yaml", "alias.yaml", "link.yaml"])
def test_output_is_input(workspace: Any, output: str) -> None:
    """Resolve aliases and compare inode identity before any write."""
    root, _ = workspace
    if output == "alias.yaml":
        os.link(root / "input.yaml", root / output)
    if output == "link.yaml":
        (root / output).symlink_to("input.yaml")
    result = run_import(root, output=output)
    assert "output-is-input" in codes(result), result
    assert result["status"] != "valid"


@pytest.mark.parametrize(
    "output", ["../escape.yaml", "/escape.yaml", "sub/link.yaml", "existing.yaml", "dir/out.yaml"]
)
def test_output_refusals(workspace: Any, output: str) -> None:
    """Refuse escapes, existing paths and symlinks in any component."""
    root, _ = workspace
    (root / "sub").mkdir()
    (root / "sub/link.yaml").symlink_to("../existing.yaml")
    (root / "existing.yaml").write_bytes(b"keep")
    (root / "dir").symlink_to("sub", target_is_directory=True)
    result = run_import(root, output=output)
    assert result["status"] in ("invalid", "error"), result
    assert (root / "existing.yaml").read_bytes() == b"keep"
    assert not (root / "sub/out.yaml").exists()


@pytest.mark.parametrize("failure", ["write", "publish", "race", "fsync"])
def test_atomic_failures(workspace: Any, failure: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep a raced destination and remove all temporary bytes on failure."""
    root, _ = workspace
    original = {p.name for p in root.iterdir()}

    def fail(*args: Any) -> None:
        raise OSError("private failure detail")

    def race(directory: int, temporary: str, destination: str) -> None:
        (root / "output.yaml").write_bytes(b"winner")
        handoff.publish_candidate(directory, temporary, destination)

    kwargs: dict[str, Any] = {}
    if failure == "write":
        kwargs["write"] = fail
    elif failure == "publish":
        kwargs["publish"] = fail
    elif failure == "race":
        kwargs["publish"] = race
    else:
        monkeypatch.setattr(handoff.os, "fsync", fail)
    result = run_import(root, supplement="supplement.json", **kwargs)
    assert result["status"] == "error", result
    assert "private failure detail" not in json.dumps(result)
    if failure == "race":
        assert (root / "output.yaml").read_bytes() == b"winner"
        original.add("output.yaml")
    else:
        assert not (root / "output.yaml").exists()
    assert {p.name for p in root.iterdir()} == original


@pytest.mark.parametrize(
    "field", ["producer", "created_at", "image", "fail", "baseline", "remove-image"]
)
def test_supplement_conflict(workspace: Any, field: str) -> None:
    """Supplement cannot change facts or omit a failed legacy check."""
    root, supplement = workspace
    if field in ("producer", "created_at"):
        supplement[field] = "different"
    elif field == "image":
        supplement["components"][0]["image_ref"] = "registry.example/app:v1@sha256:" + "a" * 64
    elif field == "baseline":
        supplement["changes"]["baseline"] = "different"
    elif field == "remove-image":
        supplement["components"] = []
    else:
        source = root / "input.yaml"
        source.write_bytes(source.read_bytes().replace(b"unit: pass", b"unit: fail"))
    (root / "supplement.json").write_text(json.dumps(supplement))
    result = run_import(root, supplement="supplement.json")
    assert result["status"] == "invalid", result
    assert not (root / "output.yaml").exists()


@pytest.mark.parametrize(
    "proof", ["claim", "wrong-subject", "wrong-digest", "external", "too-large"]
)
def test_pass_needs_real_evidence(workspace: Any, proof: str) -> None:
    """An imported pass requires verified evidence of that same component."""
    root, supplement = workspace
    kwargs: dict[str, Any] = {}
    if proof == "claim":
        supplement["checks"][0].pop("subjects")
        supplement["checks"][0].pop("evidence")
    elif proof == "wrong-subject":
        supplement["checks"][0]["subjects"][0]["id"] = "different"
    elif proof == "wrong-digest":
        supplement["evidence"][0]["sha256"] = "sha256:" + "a" * 64
    elif proof == "external":
        for item in supplement["evidence"]:
            item["locator"] = "https://example.com/opaque"
    else:
        kwargs["evidence_limit"] = 1
    (root / "supplement.json").write_text(json.dumps(supplement))
    result = run_import(root, supplement="supplement.json", **kwargs)
    assert result["status"] in ("incomplete", "invalid"), result
    if proof == "claim":
        assert "missing-evidence" in codes(result)
        candidate = handoff.parse_yaml((root / "output.yaml").read_bytes())
        assert candidate["checks"][0]["status"] == "not-run"
    if proof == "too-large":
        assert "evidence-too-large" in codes(result)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("image", None),
        ("unknown-field", None),
        ("plan", None),
        ("unknown-version", "unsupported-version"),
        ("anchor", "unsupported-input"),
        ("flow", "unsupported-input"),
        ("duplicate", "duplicate-key"),
        ("unsafe-name", "unsafe-identifier"),
    ],
)
def test_synthetic_corpus(workspace: Any, name: str, expected: str | None) -> None:
    """Eight frozen synthetic inputs: three conversions and five refusals."""
    root, _ = workspace
    (root / "input.yaml").write_bytes(handoff.read_manifest(FIXTURES, name + ".yaml"))
    result = run_import(root)
    if expected:
        assert expected in codes(result), result
        assert not (root / "output.yaml").exists()
    else:
        assert result["status"] == "incomplete", result
        assert (root / "output.yaml").is_file()


def test_plan_reference_is_not_executable_proof(workspace: Any) -> None:
    """Inspection JSON never becomes a plan bundle by relabeling it."""
    root, _ = workspace
    (root / "input.yaml").write_bytes(handoff.read_manifest(FIXTURES, "plan.yaml"))
    result = run_import(root, supplement="supplement.json")
    assert result["status"] == "incomplete", result
    assert {"code": "missing-evidence", "path": "$.components"} in result["issues"]


def test_bound_plan_supplement(workspace: Any) -> None:
    """The missing plan identity can come from a locally verified bundle."""
    root, supplement = workspace
    (root / "input.yaml").write_bytes(handoff.read_manifest(FIXTURES, "plan.yaml"))
    raw = b"synthetic saved-plan bundle"
    (root / "bundle.json").write_bytes(raw)
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    supplement["components"].append({
        "id": "infra",
        "kind": "terraform-plan",
        "plan_bundle": "bundle",
    })
    evidence = copy.deepcopy(supplement["evidence"][0])
    evidence.update(
        id="bundle",
        locator="bundle.json",
        sha256=digest,
        subjects=[{"id": "infra", "sha256": digest}],
    )
    supplement["evidence"].append(evidence)
    supplement["evidence"][1]["subjects"].append({"id": "infra", "sha256": digest})
    supplement["phases"][0]["components"].append("infra")
    (root / "supplement.json").write_text(json.dumps(supplement))
    assert run_import(root, supplement="supplement.json")["status"] == "valid"


@pytest.mark.parametrize("raw", [b"x" * 1048577, b'{"x":NaN}', b'{"x":1,"x":2}', b"[]"])
def test_supplement_limits(workspace: Any, raw: bytes) -> None:
    """Supplements share bounded JSON reads, duplicate and numeric rules."""
    root, _ = workspace
    (root / "supplement.json").write_bytes(raw)
    result = run_import(root, supplement="supplement.json")
    assert result["status"] == "invalid", result
    assert not (root / "output.yaml").exists()


def test_tolerant_reader_contract() -> None:
    """Pin documented legacy outcomes without claiming a parser exists."""
    text = handoff.read_manifest(PACK, ".apm/skills/release-loop/SKILL.md").decode()
    assert (
        "**Tolerant reader.** Unknown fields are ignored — the outer loop reads what it knows\n"
        "and surfaces a warning for unknown `schema_version` values rather than hard-failing.\n"
        "Adopters may extend the schema with additional fields."
    ) in text
    unknown = handoff.parse_yaml(handoff.read_manifest(FIXTURES, "unknown-field.yaml"))
    version = handoff.parse_yaml(handoff.read_manifest(FIXTURES, "unknown-version.yaml"))
    assert unknown["adopter_extra"] == "inert"
    assert version["schema_version"] == "9.0"  # Legacy warning; strict import refuses it.


@pytest.mark.parametrize("failure", ["create", "publish-after-link"])
def test_more_publication_failures(
    workspace: Any, failure: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Publication failure includes allocation and errors after the link call."""
    root, _ = workspace
    original = {p.name for p in root.iterdir()}
    kwargs: dict[str, Any] = {}
    if failure == "create":
        original_open = handoff.os.open

        def refuse_temp(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
            if flags & os.O_CREAT:
                raise OSError("allocation failed")
            return original_open(path, flags, *args, **kwargs)

        monkeypatch.setattr(handoff.os, "open", refuse_temp)
    else:

        def link_then_fail(directory: int, temporary: str, destination: str) -> None:
            handoff.publish_candidate(directory, temporary, destination)
            raise OSError("failure after link")

        kwargs["publish"] = link_then_fail
    assert run_import(root, supplement="supplement.json", **kwargs)["status"] == "error"
    assert {p.name for p in root.iterdir()} == original


def test_phase_fact_conflict(workspace: Any) -> None:
    """A supplied phase cannot erase a known legacy phase identity."""
    root, supplement = workspace
    supplement["phases"][0]["id"] = "different"
    (root / "supplement.json").write_text(json.dumps(supplement))
    assert run_import(root, supplement="supplement.json")["status"] == "invalid"
    assert not (root / "output.yaml").exists()


def test_external_pass_is_downgraded(workspace: Any) -> None:
    """External claims remain not-run until actual local proof is supplied."""
    root, supplement = workspace
    supplement["evidence"][2]["locator"] = "https://example.com/check"
    (root / "supplement.json").write_text(json.dumps(supplement))
    result = run_import(root, supplement="supplement.json")
    assert result["status"] == "incomplete", result
    data = handoff.parse_yaml((root / "output.yaml").read_bytes())
    assert data["checks"][0]["status"] == "not-run"
    assert "missing-evidence" in codes(result)


def test_provenance_known_digest(workspace: Any) -> None:
    """A known v1 provenance subject digest cannot be contradicted."""
    root, _ = workspace
    source = root / "input.yaml"
    raw = source.read_bytes()
    start = raw.index(b"  subject_digest:")
    end = raw.index(b"\n", start)
    source.write_bytes(raw[:start] + b'  subject_digest: "sha256:' + b"a" * 64 + b'"' + raw[end:])
    result = run_import(root, supplement="supplement.json")
    assert result["status"] == "invalid", result
    assert not (root / "output.yaml").exists()


def test_plan_inspection_is_not_bundle(workspace: Any) -> None:
    """A supplement cannot relabel the referenced inspection as a plan bundle."""
    root, supplement = workspace
    (root / "input.yaml").write_bytes(handoff.read_manifest(FIXTURES, "plan.yaml"))
    raw = b'{"format_version":"1.2","planned_values":{}}'
    (root / "inspection.json").write_bytes(raw)
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    supplement["components"].append({
        "id": "infra",
        "kind": "terraform-plan",
        "plan_bundle": "bundle",
    })
    evidence = copy.deepcopy(supplement["evidence"][0])
    evidence.update(
        id="bundle",
        locator="inspection.json",
        sha256=digest,
        subjects=[{"id": "infra", "sha256": digest}],
    )
    supplement["evidence"].append(evidence)
    supplement["evidence"][1]["subjects"].append({"id": "infra", "sha256": digest})
    supplement["phases"][0]["components"].append("infra")
    (root / "supplement.json").write_text(json.dumps(supplement))
    result = run_import(root, supplement="supplement.json")
    assert result["status"] != "valid", result


@pytest.mark.parametrize("target", ["supplement.json", "policy.json", "input.yaml"])
def test_confined_input_reads(workspace: Any, target: str) -> None:
    """Every importer input goes through no-follow confined reads."""
    root, _ = workspace
    path = root / target
    path.rename(root / "stored")
    path.symlink_to("stored")
    result = run_import(root, supplement="supplement.json")
    assert result["status"] == "error", result
    assert "unreadable-input" in codes(result)
    assert not (root / "output.yaml").exists()


@pytest.mark.parametrize("outcome", ["valid", "incomplete", "refusal"])
def test_source_never_opened_for_writing(
    workspace: Any, outcome: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Inspect open flags as well as byte equality for all outcome classes."""
    root, _ = workspace
    source = root / "input.yaml"
    identity = source.stat()
    original_open = handoff.os.open
    writes = []

    def checked_open(path: Any, flags: int, *args: Any, **kwargs: Any) -> int:
        descriptor = original_open(path, flags, *args, **kwargs)
        info = os.fstat(descriptor)
        if (info.st_dev, info.st_ino) == (identity.st_dev, identity.st_ino):
            writes.append(flags & (os.O_WRONLY | os.O_RDWR | os.O_TRUNC | os.O_CREAT))
        return descriptor

    monkeypatch.setattr(handoff.os, "open", checked_open)
    kwargs: dict[str, Any] = {}
    if outcome == "valid":
        kwargs["supplement"] = "supplement.json"
    elif outcome == "refusal":
        source.write_bytes(source.read_bytes().replace(b'"1.0"', b'"9.0"', 1))
    result = run_import(root, **kwargs)
    assert (
        result["status"]
        == {"valid": "valid", "incomplete": "incomplete", "refusal": "error"}[outcome]
    )
    assert writes and not any(writes)


def test_unknown_supplement_key_is_redacted(workspace: Any) -> None:
    """Never print unknown field text or invalid identifier values."""
    root, supplement = workspace
    supplement["private secret marker"] = "private content"
    (root / "supplement.json").write_text(json.dumps(supplement))
    result = run_import(root, supplement="supplement.json")
    assert result["status"] == "invalid", result
    assert {"code": "unknown-field", "path": "$.<unknown>"} in result["issues"]
    assert "private" not in json.dumps(result)
    assert not (root / "output.yaml").exists()


@pytest.mark.parametrize("complete", [False, True])
def test_v1_twin_cli_process_integration(workspace: Any, complete: bool) -> None:
    """Drive a full documented v1 handoff and its supplemented twin as processes."""
    root, supplement = workspace
    (root / "input.yaml").write_bytes(handoff.read_manifest(FIXTURES, "plan.yaml"))
    if complete:
        raw = b"synthetic saved-plan bundle"
        (root / "bundle.json").write_bytes(raw)
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        supplement["components"].append({
            "id": "infra",
            "kind": "terraform-plan",
            "plan_bundle": "bundle",
        })
        evidence = copy.deepcopy(supplement["evidence"][0])
        evidence.update(
            id="bundle",
            locator="bundle.json",
            sha256=digest,
            subjects=[{"id": "infra", "sha256": digest}],
        )
        supplement["evidence"].append(evidence)
        supplement["evidence"][1]["subjects"].append({"id": "infra", "sha256": digest})
        supplement["phases"][0]["components"].append("infra")
        (root / "supplement.json").write_text(json.dumps(supplement))
    entry = """
import runpy
import socket
import sys
import urllib.request

def refuse(*args, **kwargs):
    raise AssertionError("network forbidden")

socket.socket = refuse
urllib.request.urlopen = refuse
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name="__main__")
"""
    argv = [
        sys.executable,
        "-c",
        entry,
        str(SCRIPT),
        "import-v1",
        "input.yaml",
        "--root",
        str(root),
        "--policy",
        "policy.json",
        "--output",
        "output.yaml",
        "--now",
        NOW,
    ]
    if complete:
        argv.extend(["--supplement", "supplement.json"])
    before = (root / "input.yaml").read_bytes()
    try:
        proc = subprocess.run(
            argv,
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
            check=False,
        )
        result = json.loads(proc.stdout)
        assert proc.stderr == ""
        assert set(result) == {"status", "issues", "evidence"}
        assert proc.returncode == (0 if complete else 1), result
        assert result["status"] == ("valid" if complete else "incomplete"), result
        validated = handoff.validate_bytes(
            (root / "output.yaml").read_bytes(),
            root=root,
            policy=json.loads((root / "policy.json").read_bytes()),
            now=NOW,
        )
        assert validated["status"] == result["status"], validated
    finally:
        assert (root / "input.yaml").read_bytes() == before


def test_supplement_supplies_check_stages(workspace: Any) -> None:
    """Legacy check names are identities, not facts about v2 stage names."""
    root, supplement = workspace
    for check in supplement["checks"]:
        check["stage"] = "security" if check["id"] == "security_scan" else "validation"
    (root / "supplement.json").write_text(json.dumps(supplement))
    result = run_import(root, supplement="supplement.json")
    assert result["status"] == "valid", result

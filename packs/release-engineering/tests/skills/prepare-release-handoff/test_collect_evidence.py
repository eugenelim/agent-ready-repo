"""Collect existing local evidence without executing or trusting input directives."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

PACK = Path(__file__).resolve().parents[3]
SCRIPT = PACK / ".apm/skills/prepare-release-handoff/scripts/collect_evidence.py"
VALIDATOR = PACK / ".apm/skills/release-loop/scripts/release_handoff.py"
EXAMPLE = PACK / ".apm/skills/release-loop/assets/image-only-ci-caller"
NOW = "2026-01-01T12:30:00Z"


def load(path: Path, name: str) -> ModuleType:
    """Load a pack-qualified module without changing the module search path."""
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def prohibit_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    """Use the admission suite's seam locally, without a cross-suite import."""
    def refuse(*args: Any, **kwargs: Any) -> Any:
        """Fail immediately on an attempted process or network operation."""
        raise AssertionError("external operation forbidden")

    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, refuse)
    for name in ("socket", "create_connection", "socketpair", "getaddrinfo"):
        monkeypatch.setattr(socket, name, refuse)
    monkeypatch.setattr(os, "system", refuse)


@pytest.fixture
def module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Exercise all in-process cases with external operations forbidden."""
    prohibit_execution(monkeypatch)
    return load(SCRIPT, "release_engineering_prepare_release_handoff_collect_evidence")


@pytest.fixture
def case(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """Prepare a complete request with every computable digest omitted."""
    for path in EXAMPLE.iterdir():
        if path.is_file():
            (tmp_path / path.name).write_bytes(path.read_bytes())
    validator = load(VALIDATOR, "release_engineering_prepare_release_handoff_fixture_validator")
    request = validator.parse_yaml((tmp_path / "release-handoff.yaml").read_bytes())
    for evidence in request["evidence"]:
        evidence.pop("sha256")
    for record in request["evidence"] + request["checks"]:
        for subject in record["subjects"]:
            subject.pop("sha256")
    return tmp_path, request


def invoke(module: ModuleType, case: tuple[Path, dict[str, Any]], capsys: Any,
           *, policy: str | None = "trusted-policy.json") -> tuple[int, dict[str, Any]]:
    """Run the real CLI parser and require one JSON result and empty stderr."""
    root, request = case
    (root / "request.json").write_text(json.dumps(request))
    args = ["collect", "request.json", "--root", str(root), "--output", "candidate.yaml",
            "--now", NOW]
    if policy is not None:
        args += ["--policy", policy]
    code = module.main(args)
    captured = capsys.readouterr()
    assert captured.err == ""
    return code, json.loads(captured.out)


def test_ready(module: ModuleType, case: Any, capsys: Any) -> None:
    """A complete request produces a validated candidate with exact-byte hashes."""
    root, request = case
    code, result = invoke(module, case, capsys)
    assert (code, result) == (0, {"status": "ready", "gaps": []})
    validator = load(VALIDATOR, "release_engineering_prepare_release_handoff_output_validator")
    candidate = validator.parse_yaml((root / "candidate.yaml").read_bytes())
    for evidence in candidate["evidence"]:
        assert evidence["sha256"] == "sha256:" + hashlib.sha256(
            (root / evidence["locator"]).read_bytes()).hexdigest()
    assert all("sha256" not in item for item in request["evidence"])


@pytest.mark.parametrize("shared_digest", [False, True])
@pytest.mark.parametrize("mismatch", [False, True])
def test_component_evidence_id_collision(
    module: ModuleType, case: tuple[Path, dict[str, Any]], capsys: Any,
    shared_digest: bool, mismatch: bool,
) -> None:
    """Component aliases cannot corrupt later evidence bindings or shared digests."""
    root, request = case
    request["components"][0]["id"] = "provenance"
    artifact_digest = "sha256:" + hashlib.sha256(
        (root / "provenance-attestation.json").read_bytes()).hexdigest()
    additional = ["worker", "worker-copy"] if shared_digest else ["worker"]
    for identifier in additional:
        request["components"].append({
            "id": identifier, "kind": "oci-image", "artifact": "provenance",
            "image_ref": "registry.example.com/worker:v1@" + artifact_digest,
        })
    for record in request["evidence"] + request["checks"]:
        record["subjects"][0]["id"] = "provenance"
        record["subjects"].extend({"id": identifier} for identifier in additional)
    request["phases"][0]["components"] = ["provenance", *additional]
    if mismatch:
        request["evidence"][-1]["subjects"][0]["sha256"] = artifact_digest
    code, result = invoke(module, case, capsys)
    if mismatch:
        assert code == 1 and result["status"] == "incomplete"
        assert {item["code"] for item in result["gaps"]} == {"subject-mismatch"}
        assert not (root / "candidate.yaml").exists()
        return
    assert (code, result) == (0, {"status": "ready", "gaps": []})
    validator = load(VALIDATOR, "release_engineering_prepare_release_handoff_collision_validator")
    candidate = validator.parse_yaml((root / "candidate.yaml").read_bytes())
    by_id = {item["id"]: item for item in candidate["evidence"]}
    for item in candidate["evidence"]:
        assert item["sha256"] == "sha256:" + hashlib.sha256(
            (root / item["locator"]).read_bytes()).hexdigest()
    identities = {
        item["id"]: by_id[item["artifact"]]["sha256"] for item in candidate["components"]
    }
    for record in candidate["evidence"] + candidate["checks"]:
        assert all(subject["sha256"] == identities[subject["id"]]
                   for subject in record["subjects"])


@pytest.mark.parametrize("mutation,expected,action", [
    ("missing", "missing-evidence", "produce-evidence"),
    ("unknown", "missing-evidence", "produce-evidence"),
    ("digest", "digest-mismatch", "reconcile-digest"),
    ("external", "unverified-external", "supply-digest"),
    ("not-run", "check-not-run", "run-check"),
    ("fail", "check-failed", "repair-and-rebuild"),
    ("provenance", "missing-provenance", "produce-evidence"),
    ("target", "missing-target", "supply-target"),
    ("unsupported", "unsupported-component", "route-to-owner"),
    ("stale", "stale", "fix-candidate"),
    ("invalid", "invalid-image-reference", "fix-candidate"),
    ("subject", "subject-mismatch", "fix-candidate"),
    ("required", "missing-evidence", "fix-candidate"),
])
def test_gaps(module: ModuleType, case: Any, capsys: Any, mutation: str,
              expected: str, action: str) -> None:
    """Each single gap names the field and action and writes no candidate bytes."""
    root, request = case
    if mutation == "missing":
        (root / "image-manifest.json").unlink()
    elif mutation == "unknown":
        request["checks"][0]["evidence"] = ["absent"]
    elif mutation == "digest":
        request["evidence"][0]["sha256"] = "sha256:" + "0" * 64
    elif mutation == "external":
        request["evidence"][0]["locator"] = "https://example.com/private-input"
    elif mutation in ("not-run", "fail"):
        request["checks"][0]["status"] = mutation
    elif mutation == "provenance":
        request["provenance"] = []
    elif mutation == "target":
        request.pop("target")
    elif mutation == "unsupported":
        request["components"][0]["kind"] = "unknown"
    elif mutation == "stale":
        request["created_at"] = "2020-01-01T00:00:00Z"
    elif mutation == "invalid":
        request["components"][0]["image_ref"] = "private-input"
    elif mutation == "subject":
        request["checks"][0]["subjects"][0]["sha256"] = "sha256:" + "0" * 64
    else:
        request["checks"] = []
    code, result = invoke(module, case, capsys)
    assert code == 1 and result["status"] == "incomplete", result
    assert any(gap["code"] == expected and gap["next_action"] == action
               for gap in result["gaps"]), result
    assert all(set(gap) == {"code", "path", "next_action"} and gap["path"].startswith("$")
               for gap in result["gaps"])
    assert not (root / "candidate.yaml").exists()
    assert "private-input" not in json.dumps(result)


def test_absent_procedure_evidence(module: ModuleType, case: Any, capsys: Any) -> None:
    """An absent procedure citation asks for evidence and writes no candidate."""
    root, request = case
    request["phases"][0]["procedures"] = ["absent"]
    code, result = invoke(module, case, capsys)
    assert code == 1 and result["status"] == "incomplete"
    matching = [item for item in result["gaps"] if item["path"] == "$.phases[0].procedures[0]"]
    assert matching == [{
        "code": "missing-evidence", "path": "$.phases[0].procedures[0]",
        "next_action": "produce-evidence",
    }]
    assert not (root / "candidate.yaml").exists()


@pytest.mark.parametrize("citation,path", [
    ("artifact", "$.components[0].artifact"),
    ("plan_bundle", "$.components[0].plan_bundle"),
    ("provenance", "$.provenance[0]"),
    ("check", "$.checks[0].evidence[0]"),
    ("procedure", "$.phases[0].procedures[0]"),
    ("snapshot", "$.sources[0].snapshot"),
])
def test_collector_resolves_citations(
    module: ModuleType, case: Any, capsys: Any, monkeypatch: pytest.MonkeyPatch,
    citation: str, path: str,
) -> None:
    """All evidence citations produce collection gaps before sibling validation."""
    root, request = case
    if citation in ("artifact", "plan_bundle"):
        if citation == "plan_bundle":
            request["components"][0] = {"id": "app", "kind": "terraform-plan"}
        request["components"][0][citation] = "absent"
    elif citation == "provenance":
        request["provenance"][0] = "absent"
    elif citation == "check":
        request["checks"][0]["evidence"][0] = "absent"
    elif citation == "snapshot":
        request["sources"][0].pop("revision")
        request["sources"][0]["snapshot"] = "absent"
    else:
        request["phases"][0]["procedures"][0] = "absent"
    validator = module.load_validator()
    original = module.assemble
    collected: list[dict[str, str]] = []
    expected = {"code": "missing-evidence", "path": path, "next_action": "produce-evidence"}

    def assemble(*args: Any) -> list[dict[str, str]]:
        """Record collection gaps independently of validator results."""
        collected.extend(original(*args))
        return collected

    def validate(*args: Any, **kwargs: Any) -> dict[str, Any]:
        """Require collection to have found the citation before this call."""
        assert expected in collected
        return {"status": "valid", "issues": [], "evidence": []}

    monkeypatch.setattr(module, "load_validator", lambda: validator)
    monkeypatch.setattr(module, "assemble", assemble)
    monkeypatch.setattr(validator, "validate_bytes", validate)
    code, result = invoke(module, case, capsys)
    assert code == 1 and result["status"] == "incomplete"
    assert expected in result["gaps"]
    assert not (root / "candidate.yaml").exists()


def test_validator_gap_action(
    module: ModuleType, case: Any, capsys: Any, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validator-originated issues retain their code and path with fix-candidate."""
    validator = module.load_validator()
    issue = {"code": "missing-evidence", "path": "$.phases[0].procedures"}
    monkeypatch.setattr(module, "load_validator", lambda: validator)
    monkeypatch.setattr(validator, "validate_bytes", lambda *args, **kwargs: {
        "status": "incomplete", "issues": [issue], "evidence": [],
    })
    code, result = invoke(module, case, capsys)
    assert (code, result) == (1, {"status": "incomplete", "gaps": [
        {**issue, "next_action": "fix-candidate"},
    ]})
    assert not (case[0] / "candidate.yaml").exists()


@pytest.mark.parametrize("location", ["top", "nested", "normative"])
@pytest.mark.parametrize("sign", ["", "-"])
def test_overlong_integer(
    module: ModuleType, case: Any, capsys: Any, location: str, sign: str,
) -> None:
    """Retain long numeric extension text while refusing normative numeric values."""
    root, request = case
    literal = sign + "9" * 4301
    if location == "top":
        request["extensions"] = {"number": "numeric-placeholder"}
    elif location == "nested":
        request["evidence"][0]["extensions"] = {"notes": [{"number": "numeric-placeholder"}]}
    else:
        request["schema_version"] = "numeric-placeholder"
    raw = json.dumps(request).replace('"numeric-placeholder"', literal)
    (root / "request.json").write_text(raw)
    code = module.main(["collect", "request.json", "--root", str(root), "--policy",
                        "trusted-policy.json", "--output", "candidate.yaml", "--now", NOW])
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert captured.err == ""
    if location == "normative":
        assert code == 2 and result["status"] == "error"
        assert not (root / "candidate.yaml").exists()
    else:
        assert (code, result) == (0, {"status": "ready", "gaps": []})
        validator = module.load_validator()
        written = (root / "candidate.yaml").read_bytes()
        candidate = validator.parse_yaml(written)
        value = (candidate["extensions"]["number"] if location == "top"
                 else candidate["evidence"][0]["extensions"]["notes"][0]["number"])
        assert value.text == literal
        policy = validator.parse_json((root / "trusted-policy.json").read_bytes())
        assert validator.validate_bytes(written, root=root, policy=policy, now=NOW)["status"] == "valid"


@pytest.mark.parametrize("route", [
    "https://reader:demo-value@example.invalid/repair",
    "https://reader@example.invalid/repair",
    "https://example.invalid/repair?api_key=demo-value",
    "https://example.invalid/repair?next=token-help",
    "https://example.invalid/token/help",
    "https://example.invalid/repair#password=demo-value",
    "https://example.invalid/repair#pass%2577ord=demo-value",
    "https://example.invalid/repair#PRIVATE_KEY=demo-value",
], ids=["userinfo", "username", "query-key", "query-value", "path", "fragment",
        "encoded", "separators"])
def test_unsafe_route(module: ModuleType, case: Any, capsys: Any, route: str) -> None:
    """Refuse credential-bearing routes without printing or writing their values."""
    root, request = case
    request["repair_owner"]["route"] = route
    code, result = invoke(module, case, capsys)
    expected = [{"code": "unsafe-route", "path": "$.repair_owner.route",
                 "next_action": "supply-route"}]
    if "next=token-help" not in route and "/token/help" not in route:
        expected.insert(0, {"code": "unsafe-url", "path": "$.repair_owner.route",
                            "next_action": "supply-url"})
    assert (code, result) == (1, {"status": "incomplete", "gaps": expected})
    assert route not in json.dumps(result)
    assert not (root / "candidate.yaml").exists()


def test_plain_route(module: ModuleType, case: Any, capsys: Any) -> None:
    """Keep a plain HTTPS repair route unchanged in the written candidate."""
    root, request = case
    route = "https://example.invalid/repair"
    request["repair_owner"]["route"] = route
    code, result = invoke(module, case, capsys)
    assert (code, result) == (0, {"status": "ready", "gaps": []})
    validator = module.load_validator()
    assert validator.parse_yaml((root / "candidate.yaml").read_bytes())["repair_owner"]["route"] == route


@pytest.mark.parametrize("locator", ["/private-input", "C:private-input", "a\\private-input",
    "./private-input", "../private-input", "a//private-input", "link", "hard", "fifo", "huge"])
def test_confinement(module: ModuleType, case: Any, capsys: Any, locator: str) -> None:
    """Unsafe and oversized evidence refuses without echoing the locator."""
    root, request = case
    (root / "link").symlink_to(root / "image-manifest.json")
    os.link(root / "test-report.json", root / "hard")
    os.mkfifo(root / "fifo")
    with (root / "huge").open("wb") as handle:
        handle.truncate(536_870_913)
    request["evidence"][0]["locator"] = locator
    code, result = invoke(module, case, capsys)
    assert code == 1
    assert any(gap["code"] == "missing-evidence" for gap in result["gaps"])
    assert "private-input" not in json.dumps(result)
    assert not (root / "candidate.yaml").exists()


@pytest.mark.parametrize("raw", [b'{"target":{},"target":{}}', b'{"policy":{}}',
    b'{"evidence":5}', b'{"created_at":NaN}', b'[' * 33 + b']' * 33,
    b' ' * 1_048_577, b'{"target":{"account":42}}', b'null'])
def test_bad_request(module: ModuleType, case: Any, capsys: Any, raw: bytes) -> None:
    """Strict request parsing rejects malformed structures and policy injection."""
    root, _ = case
    (root / "request.json").write_bytes(raw)
    code = module.main(["collect", "request.json", "--root", str(root),
                        "--policy", "trusted-policy.json", "--output", "candidate.yaml"])
    result = json.loads(capsys.readouterr().out)
    assert code == 2 and result["status"] == "error", result
    assert not (root / "candidate.yaml").exists()


@pytest.mark.parametrize("policy", [None, "absent", "../private-input", "broken", "linked"])
def test_policy(module: ModuleType, case: Any, capsys: Any, policy: str | None) -> None:
    """Only a confined, well-formed caller-supplied policy is accepted."""
    root, _ = case
    (root / "broken").write_text('{"id":"private-input"}')
    (root / "linked").symlink_to(root / "trusted-policy.json")
    code, result = invoke(module, case, capsys, policy=policy)
    assert code == 2 and result["status"] == "error"
    assert "private-input" not in json.dumps(result)
    assert not (root / "candidate.yaml").exists()


def test_no_overwrite(module: ModuleType, case: Any, capsys: Any) -> None:
    """An existing output remains unchanged."""
    root, _ = case
    (root / "candidate.yaml").write_bytes(b"keep")
    code, result = invoke(module, case, capsys)
    assert code != 0 and result["status"] != "ready"
    assert (root / "candidate.yaml").read_bytes() == b"keep"


def test_validator_absent(module: ModuleType, case: Any, capsys: Any,
                          monkeypatch: pytest.MonkeyPatch) -> None:
    """An installed collector without its sibling names the installation gap."""
    monkeypatch.setattr(module, "VALIDATOR", case[0] / "absent.py")
    code, result = invoke(module, case, capsys)
    assert (code, result) == (1, {"status": "incomplete", "gaps": [{
        "code": "validator-unavailable", "path": "$", "next_action": "install-validator"}]})
    assert not (case[0] / "candidate.yaml").exists()


@pytest.mark.parametrize("failure", ["write", "publish", "race"])
def test_atomic_failure(module: ModuleType, case: Any, capsys: Any,
                        monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    """Failed writes and competing publications leave no partial candidate."""
    validator = module.load_validator()
    monkeypatch.setattr(module, "load_validator", lambda: validator)
    root, _ = case

    def write(descriptor: int, raw: bytes) -> None:
        """Fail after a partial temporary write."""
        os.write(descriptor, raw[:10])
        raise OSError("private-input")

    def publish(directory: int, temporary: str, destination: str) -> None:
        """Fail before publication or after a competing output appears."""
        if failure == "race":
            (root / destination).write_bytes(b"competing")
        raise OSError("private-input")

    monkeypatch.setattr(validator, "write_candidate" if failure == "write" else "publish_candidate",
                        write if failure == "write" else publish)
    code, result = invoke(module, case, capsys)
    assert code == 2 and result["status"] == "error"
    assert "private-input" not in json.dumps(result)
    assert not list(root.glob(".release-handoff-*.tmp"))
    if failure == "race":
        assert (root / "candidate.yaml").read_bytes() == b"competing"
    else:
        assert not (root / "candidate.yaml").exists()


def test_replaced_evidence(module: ModuleType, case: Any, capsys: Any,
                           monkeypatch: pytest.MonkeyPatch) -> None:
    """A file replaced after open cannot contribute a digest or candidate."""
    root, _ = case
    original = os.read
    swapped = False

    def read(descriptor: int, count: int) -> bytes:
        """Replace the evidence pathname while its old inode remains open."""
        nonlocal swapped
        info = os.fstat(descriptor)
        target = root / "image-manifest.json"
        if not swapped and info.st_ino == target.stat().st_ino:
            replacement = root / "replacement"
            replacement.write_bytes(b"private-input")
            replacement.replace(target)
            swapped = True
        return original(descriptor, count)

    monkeypatch.setattr(os, "read", read)
    code, result = invoke(module, case, capsys)
    assert swapped and code == 1
    assert any(item["code"] == "missing-evidence" for item in result["gaps"])
    assert "private-input" not in json.dumps(result)
    assert not (root / "candidate.yaml").exists()


@pytest.mark.parametrize("argument", ["request", "policy", "output"])
@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo", "escape", "oversized"])
def test_file_arguments(module: ModuleType, case: Any, capsys: Any, argument: str, kind: str) -> None:
    """Every file argument rejects unsafe input without exposing its pathname."""
    root, request = case
    (root / "request.json").write_text(json.dumps(request))
    source = root / ("request.json" if argument == "request" else "trusted-policy.json")
    path = root / "private-input"
    if kind == "symlink":
        path.symlink_to(source)
    elif kind == "hardlink":
        os.link(source, path)
    elif kind == "fifo":
        os.mkfifo(path)
    elif kind == "oversized":
        with path.open("wb") as handle:
            handle.truncate(1_048_577)
    locator = "../private-input" if kind == "escape" else "private-input"
    args = ["collect", locator if argument == "request" else "request.json", "--root", str(root),
            "--policy", locator if argument == "policy" else "trusted-policy.json",
            "--output", locator if argument == "output" else "candidate.yaml", "--now", NOW]
    code = module.main(args)
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert code == 2 and result["status"] == "error"
    assert "private-input" not in captured.out + captured.err
    assert not (root / "candidate.yaml").exists()


def test_external_digest(module: ModuleType, case: Any, capsys: Any) -> None:
    """A supplied external digest stays unverified and cannot satisfy required evidence."""
    root, request = case
    request["evidence"][0]["locator"] = "https://example.com/private-input"
    request["evidence"][0]["sha256"] = request["components"][0]["image_ref"].split("@", 1)[1]
    code, result = invoke(module, case, capsys)
    assert code == 1
    assert any(item["code"] == "unverified-evidence" for item in result["gaps"])
    assert not any(item["code"] == "unverified-external" for item in result["gaps"])
    assert not (root / "candidate.yaml").exists()


@pytest.mark.parametrize("command,exit_code", [("collect", 0), ("private-input", 2)])
def test_installed_cli(case: Any, command: str, exit_code: int) -> None:
    """Exercise __main__, installed sibling resolution and UTF-8 under an ASCII locale."""
    root, request = case
    installed = root / "skills"
    collector = installed / "prepare-release-handoff/scripts/collect_evidence.py"
    validator = installed / "release-loop/scripts/release_handoff.py"
    for source, target in ((SCRIPT, collector), (VALIDATOR, validator)):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
    (root / "request.json").write_text(json.dumps(request))
    entry = """
import os, runpy, socket, subprocess, sys

def refuse(*args, **kwargs):
    raise AssertionError('external operation forbidden')
for name in ('Popen', 'run', 'call', 'check_call', 'check_output'):
    setattr(subprocess, name, refuse)
for name in ('socket', 'create_connection', 'socketpair', 'getaddrinfo'):
    setattr(socket, name, refuse)
os.system = refuse
sys.argv = sys.argv[1:]
runpy.run_path(sys.argv[0], run_name='__main__')
"""
    result = subprocess.run([sys.executable, "-c", entry, str(collector), command, "request.json",
                             "--root", str(root), "--policy", "trusted-policy.json",
                             "--output", "candidate.yaml", "--now", NOW],
                            env={**os.environ, "PYTHONIOENCODING": "ascii"},
                            capture_output=True, encoding="utf-8", timeout=10, check=False)
    assert result.returncode == exit_code, result.stdout + result.stderr
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert payload["status"] == ("ready" if exit_code == 0 else "error")
    assert "private-input" not in result.stdout


@pytest.mark.parametrize("value", ["overlong", "object"])
def test_unserializable_request(
    module: ModuleType, case: Any, capsys: Any,
    monkeypatch: pytest.MonkeyPatch, value: str,
) -> None:
    """Unsupported normative values return one safe error without a traceback."""
    root, request = case
    if value == "overlong":
        raw = json.dumps(request).replace('"schema_version": "2.0"',
                                          '"schema_version": ' + "1" * 4301)
        assert "1" * 4301 in raw
        (root / "request.json").write_text(raw)
    else:
        request["schema_version"] = object()
        monkeypatch.setattr(module, "read_json", lambda *args: request)
    code = module.main(["collect", "request.json", "--root", str(root),
                        "--policy", "trusted-policy.json", "--output", "candidate.yaml"])
    captured = capsys.readouterr()
    result = json.loads(captured.out)
    assert code == 2 and result["status"] == "error"
    assert captured.err == "" and "Traceback" not in captured.out
    assert not (root / "candidate.yaml").exists()


@pytest.mark.parametrize("field", ["repository", "locator", "image_ref", "route"])
@pytest.mark.parametrize("url", [
    "https://reader:meadow-finch@example.invalid/path",
    "//reader:meadow-finch@example.invalid/path",
    "//reader%252Fname:meadow-finch%2540example.invalid/path",
    "https://example.invalid/path#password=meadow-finch",
    "https://example.invalid/path?key=meadow-finch",
    "https://example.invalid/path?sig=meadow-finch",
    "https://example.invalid/path?%256bey=meadow-finch",
])
def test_every_collected_url(
    module: ModuleType, case: Any, capsys: Any, field: str, url: str,
) -> None:
    """Credential URLs in declared URL fields yield a field gap and no candidate."""
    root, request = case
    if field == "repository":
        request["sources"][0][field] = url
        path = "$.sources[0].repository"
    elif field == "locator":
        request["evidence"][0][field] = url
        path = "$.evidence[0].locator"
    elif field == "image_ref":
        request["components"][0][field] = url
        path = "$.components[0].image_ref"
    elif field == "route":
        request["repair_owner"][field] = url
        path = "$.repair_owner.route"
    code, result = invoke(module, case, capsys)
    assert code == 1 and result["status"] == "incomplete"
    assert {"code": "unsafe-url", "path": path, "next_action": "supply-url"} in result["gaps"]
    assert "meadow-finch" not in json.dumps(result)
    assert not (root / "candidate.yaml").exists()


def test_collected_query_aliases(module: ModuleType, case: Any, capsys: Any) -> None:
    """All credential query aliases, including mixed case, are refused at source URLs."""
    root, request = case
    for name in ("key", "sig", "signature", "apikey", "api_key", "access_token", "auth",
                 "pwd", "secret", "token", "password", "passwd", "credential", "session",
                 "cookie"):
        request["sources"][0]["repository"] = (
            "https://example.invalid/path?" + name.upper() + "=meadow-finch"
        )
        code, result = invoke(module, case, capsys)
        assert code == 1
        assert {"code": "unsafe-url", "path": "$.sources[0].repository",
                "next_action": "supply-url"} in result["gaps"]
        assert not (root / "candidate.yaml").exists()


def test_benign_collected_urls(module: ModuleType, case: Any, capsys: Any) -> None:
    """Safe URLs throughout the request survive collection with their exact spelling."""
    root, request = case
    url = "https://example.invalid/path?branch=main#overview"
    request["sources"][0]["repository"] = url
    request["repair_owner"]["route"] = "workflow:repair"
    request["extensions"] = {"nested": [url, "//example.invalid/path"]}
    code, result = invoke(module, case, capsys)
    assert code == 0 and result["status"] == "ready"
    candidate = module.load_validator().parse_yaml((root / "candidate.yaml").read_bytes())
    assert candidate["sources"][0]["repository"] == url
    assert candidate["repair_owner"]["route"] == "workflow:repair"
    assert candidate["extensions"] == request["extensions"]


@pytest.mark.parametrize("location", ["repository", "summary", "extensions", "nested-extensions"])
def test_url_checks_ignore_words_and_free_text(
    module: ModuleType, case: Any, capsys: Any, location: str,
) -> None:
    """Only URL fields reject structural credentials; prose and metadata stay opaque."""
    root, request = case
    url = "https://example.invalid/auth/token?branch=auth#overview"
    if location == "repository":
        request["sources"][0]["repository"] = url
    elif location == "summary":
        request["changes"]["entries"][0]["summary"] = "See " + url
    else:
        container = request if location == "extensions" else request["evidence"][0]
        container["extensions"] = {"reader:meadow-finch@example.invalid": [
            "//reader:meadow-finch@example.invalid/path",
        ]}
    code, result = invoke(module, case, capsys)
    assert (code, result) == (0, {"status": "ready", "gaps": []})
    written = module.load_validator().parse_yaml((root / "candidate.yaml").read_bytes())
    assert written["changes"] == request["changes"]
    assert "meadow-finch" not in json.dumps(result)


def test_gap_masks_extension_keys(module: ModuleType) -> None:
    """A diagnostic never echoes free-form mapping keys, even in nested metadata."""
    result = module.gap("unsafe-url", "$.evidence[0].extensions.reader:meadow-finch.url")
    assert result["path"] == "$.evidence[0].extensions.*"
    assert "meadow-finch" not in json.dumps(result)


@pytest.mark.parametrize("route", [
    "workflow:repair?key=value", "workflow:repair#sig=value", "#sig=value",
    "https://example.invalid/repair?branch=main", "workflow:repair?", "workflow:repair#",
    "https://example.invalid/repair?next=https://reader:value@other.invalid/path",
    "https://example.invalid/https://other.invalid/repair",
    "workflow:https://other.invalid/repair", "mailto:repair@example.invalid",
    "workflow:repair%253Fbranch=main", "workflow:repair%2523overview",
    "workflow:repair?client_secret=value", "workflow:repair?access_key=value",
    "https://", "http://", "https:", "workflow:", "https:///repair",
])
def test_routes_require_plain_endpoints(
    module: ModuleType, case: Any, capsys: Any, route: str,
) -> None:
    """Non-endpoint routes cannot be written or echoed by collection."""
    root, request = case
    request["repair_owner"]["route"] = route
    code, result = invoke(module, case, capsys)
    assert code == 1 and result["status"] == "incomplete"
    assert {"code": "unsafe-route", "path": "$.repair_owner.route",
            "next_action": "supply-route"} in result["gaps"]
    assert route not in json.dumps(result)
    assert not (root / "candidate.yaml").exists()


@pytest.mark.parametrize("suffix", [
    "?client_secret=value", "#client_secret=value", "?access_key=value",
    "#x-amz-signature=value", "?CLIENT%255FSECRET=value",
    "?next=https://reader:value@other.invalid/path",
    "/https://reader:value@other.invalid/path",
    "?next=https%253A%252F%252Freader%253Avalue%2540other.invalid/path",
])
def test_repository_url_checks_all_authorities_and_compound_names(
    module: ModuleType, case: Any, capsys: Any, suffix: str,
) -> None:
    """Outer URLs cannot hide credential names or a second authority's userinfo."""
    root, request = case
    request["sources"][0]["repository"] = "https://example.invalid/path" + suffix
    code, result = invoke(module, case, capsys)
    assert code == 1 and result["status"] == "incomplete"
    assert {"code": "unsafe-url", "path": "$.sources[0].repository",
            "next_action": "supply-url"} in result["gaps"]
    assert suffix not in json.dumps(result)
    assert not (root / "candidate.yaml").exists()


@pytest.mark.parametrize("levels", [1, 2, 7])
@pytest.mark.parametrize("route", ["workflow:repair", "https://example.invalid/repair"])
def test_encoded_harmless_repository_path(
    module: ModuleType, case: Any, capsys: Any, route: str, levels: int,
) -> None:
    """Harmless encoded paths reaching a fixpoint within eight passes survive."""
    root, request = case
    url = "https://example.invalid/repo%" + "25" * (levels - 1) + "2Ftree"
    request["sources"][0]["repository"] = url
    request["repair_owner"]["route"] = route
    code, result = invoke(module, case, capsys)
    assert (code, result) == (0, {"status": "ready", "gaps": []})
    candidate = module.load_validator().parse_yaml((root / "candidate.yaml").read_bytes())
    assert candidate["sources"][0]["repository"] == url
    assert candidate["repair_owner"]["route"] == route


def test_validator_check_identifiers_are_not_diagnostic_paths(
    module: ModuleType, case: Any, capsys: Any,
) -> None:
    """Real validator issues must not expose a policy-supplied check identifier."""
    root, request = case
    policy_path = root / "trusted-policy.json"
    policy = json.loads(policy_path.read_bytes())
    policy["required_checks"][0]["id"] = "password:value"
    policy_path.write_text(json.dumps(policy))
    request["checks"] = []
    code, result = invoke(module, case, capsys)
    assert code == 1 and result["status"] == "incomplete"
    assert {"code": "missing-evidence", "path": "$.checks.*",
            "next_action": "fix-candidate"} in result["gaps"]
    assert "password:value" not in json.dumps(result)
    assert not (root / "candidate.yaml").exists()


@pytest.mark.parametrize("path,expected", [
    ("$.checks.password:value", "$.checks.*"),
    ("$.evidence[0].reader:value.locator", "$.evidence[0].*.locator"),
    ("$.checks[reader:value].status", "$.checks[*].status"),
    ("$.evidence[0].extensions.id", "$.evidence[0].extensions.*"),
    ("$.phases[2].procedures[1]", "$.phases[2].procedures[1]"),
])
def test_gap_paths_allow_only_fields_and_indices(
    module: ModuleType, path: str, expected: str,
) -> None:
    """Diagnostic paths retain useful fields and mask every other segment."""
    assert module.gap("missing-evidence", path)["path"] == expected


@pytest.mark.parametrize("suffix", [
    "?%2525252525252570assword=value", "?%25252525256bey=value",
    "/repo%" + "25" * 7 + "2Ftree", "/repo%" + "25" * 8 + "2Ftree",
])
def test_url_decoding_refuses_hidden_credentials_or_exhaustion(
    module: ModuleType, case: Any, capsys: Any, suffix: str,
) -> None:
    """Hidden credential keys and decoding without a bounded fixpoint are refused."""
    root, request = case
    request["sources"][0]["repository"] = "https://example.invalid/path" + suffix
    code, result = invoke(module, case, capsys)
    assert code == 1 and result["status"] == "incomplete"
    assert {"code": "unsafe-url", "path": "$.sources[0].repository",
            "next_action": "supply-url"} in result["gaps"]
    assert suffix not in json.dumps(result)
    assert not (root / "candidate.yaml").exists()

"""Admission contract, immutable inputs and local-only confinement checks."""

from __future__ import annotations

import hashlib
import importlib.util
import io
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
SCRIPTS = PACK / ".apm/skills/release-loop/scripts"
EXAMPLE = PACK / ".apm/skills/release-loop/assets/image-only-ci-caller"
NOW = "2026-01-01T12:30:00Z"


def load_script(name: str) -> ModuleType:
    """Load independent skill modules without changing the import path."""
    path = SCRIPTS / "release_admission.py"
    if name == "release_handoff":
        path = SCRIPTS / "release_handoff.py"
    else:
        assert name == "release_admission"
    spec = importlib.util.spec_from_file_location("release_engineering_release_loop_" + name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def digest(raw: bytes) -> str:
    """Return the exact-byte digest used in admission records."""
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def prohibit_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reusable seam proving calls cannot execute processes or contact services."""

    def refuse(*args: Any, **kwargs: Any) -> Any:
        """Fail immediately on any attempted external operation."""
        raise AssertionError("external operation forbidden")

    for name in ("Popen", "run", "call", "check_call", "check_output"):
        monkeypatch.setattr(subprocess, name, refuse)
    for name in ("socket", "create_connection", "socketpair", "getaddrinfo"):
        monkeypatch.setattr(socket, name, refuse)
    monkeypatch.setattr(os, "system", refuse)


@pytest.fixture
def admission(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Load the shipped script with all external execution seams closed."""
    prohibit_execution(monkeypatch)
    return load_script("release_admission")


@pytest.fixture
def root(tmp_path: Path) -> Path:
    """Copy only the pack-owned image example into an isolated root."""
    for path in EXAMPLE.iterdir():
        if path.is_file():
            (tmp_path / path.name).write_bytes(path.read_bytes())
    handoff = load_script("release_handoff")
    candidate = handoff.parse_yaml((tmp_path / "release-handoff.yaml").read_bytes())
    (tmp_path / "candidate.yaml").write_bytes(handoff.yaml_bytes(candidate))
    return tmp_path


def invoke(module: ModuleType, root: Path, capsys: Any, *args: str) -> tuple[int, dict[str, Any]]:
    """Require exactly one JSON object and no stderr on each CLI call."""
    code = module.main([*args, "--root", str(root), *([] if "--now" in args else ["--now", NOW])])
    output = capsys.readouterr()
    assert output.err == ""
    result = json.loads(output.out)
    assert isinstance(result, dict)
    return code, result


def admit(module: ModuleType, root: Path, capsys: Any, *args: str) -> tuple[int, dict[str, Any]]:
    """Run the documented happy-path arguments plus a single mutation."""
    return invoke(
        module,
        root,
        capsys,
        "admit",
        "candidate.yaml",
        "--policy",
        "trusted-policy.json",
        "--expect-environment",
        "staging",
        "--expect-account",
        "example-account",
        "--output",
        "admission.json",
        *args,
    )


def assert_code(result: dict[str, Any], code: str) -> None:
    """Assert stable refusal codes without depending on diagnostic wording."""
    assert code in [issue["code"] for issue in result["issues"]], result


def snapshot(root: Path) -> dict[str, bytes]:
    """Capture each regular input's bytes for immutability assertions."""
    return {p.name: p.read_bytes() for p in root.iterdir() if p.is_file()}


def test_admit_and_verify(admission: ModuleType, root: Path, capsys: Any) -> None:
    """Pin every exact digest, default and trusted policy locator."""
    before = snapshot(root)
    assert admit(admission, root, capsys)[0] == 0
    record = json.loads((root / "admission.json").read_bytes())
    candidate = admission.handoff.parse_yaml(before["candidate.yaml"])
    assert record == {
        "candidate": {
            "id": candidate["candidate_id"],
            "locator": "candidate.yaml",
            "sha256": digest(before["candidate.yaml"]),
        },
        "policy": {
            "id": "example-image-policy",
            "locator": "trusted-policy.json",
            "sha256": digest(before["trusted-policy.json"]),
        },
        "target": candidate["target"],
        "evidence": [
            {"id": e["id"], "sha256": digest(before[e["locator"]])} for e in candidate["evidence"]
        ],
        "admitted_at": NOW,
        "attempt": 1,
        "max_attempts": 3,
        "replaces": None,
    }
    assert invoke(admission, root, capsys, "verify", "admission.json") == (
        0,
        {"status": "current", "issues": []},
    )
    assert all((root / name).read_bytes() == raw for name, raw in before.items())


@pytest.mark.parametrize(
    "change", ["invalid", "incomplete", "error", "stale", "check", "evidence"]
)
def test_invalid_candidate(
    admission: ModuleType, root: Path, capsys: Any, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    """Every non-valid validator outcome and changed assembled input refuses."""
    if change in ("invalid", "incomplete", "error"):
        monkeypatch.setattr(
            admission.handoff, "validate_bytes", lambda *a, **k: {"status": change}
        )
    elif change == "evidence":
        (root / "test-report.json").write_bytes(b"changed")
    else:
        candidate = admission.handoff.parse_yaml((root / "candidate.yaml").read_bytes())
        if change == "check":
            candidate["checks"] = []
        else:
            candidate["evidence"][0]["observed_at"] = "2025-01-01T00:00:00Z"
        (root / "candidate.yaml").write_bytes(admission.handoff.yaml_bytes(candidate))
    before = snapshot(root)
    code, result = admit(admission, root, capsys)
    assert code == 1
    assert_code(result, "candidate-invalid")
    assert snapshot(root) == before


@pytest.mark.parametrize(
    "option,value", [("--expect-environment", "production"), ("--expect-account", "other")]
)
def test_target_mismatch(
    admission: ModuleType, root: Path, capsys: Any, option: str, value: str
) -> None:
    """Both caller target expectations are binding."""
    code, result = admit(admission, root, capsys, option, value)
    assert code == 1
    assert_code(result, "target-mismatch")
    assert not (root / "admission.json").exists()


def test_missing_policy_and_existing_output(
    admission: ModuleType, root: Path, capsys: Any
) -> None:
    """Missing policy refuses and existing output bytes survive."""
    code, result = invoke(
        admission,
        root,
        capsys,
        "admit",
        "candidate.yaml",
        "--expect-environment",
        "staging",
        "--output",
        "admission.json",
    )
    assert code == 1
    assert_code(result, "policy-missing")
    (root / "admission.json").write_bytes(b"preserve")
    code, result = admit(admission, root, capsys)
    assert code == 1
    assert_code(result, "exists")
    assert (root / "admission.json").read_bytes() == b"preserve"


@pytest.mark.parametrize(
    "change,expected",
    [
        ("candidate.yaml", "candidate-changed"),
        ("trusted-policy.json", "policy-changed"),
        ("delete-policy", "policy-changed"),
        ("test-report.json", "evidence-changed"),
        ("target", "target-changed"),
        ("clock", "stale"),
        ("record", "record-malformed"),
    ],
)
def test_verify_changes(
    admission: ModuleType, root: Path, capsys: Any, change: str, expected: str
) -> None:
    """One isolated change invalidates the pinned admission with its own code."""
    assert admit(admission, root, capsys)[0] == 0
    if change == "delete-policy":
        (root / "trusted-policy.json").unlink()
    elif change == "target":
        record = json.loads((root / "admission.json").read_bytes())
        record["target"]["account"] = "changed"
        (root / "admission.json").write_text(json.dumps(record))
    elif change == "record":
        (root / "admission.json").write_text("{}")
    elif change != "clock":
        with (root / change).open("ab") as stream:
            stream.write(b" ")
    before = snapshot(root)
    args = ["--now", "2026-01-02T12:30:00Z"] if change == "clock" else []
    code, result = invoke(admission, root, capsys, "verify", "admission.json", *args)
    assert code == 1
    assert_code(result, expected)
    assert snapshot(root) == before


def test_replacement_attempts(admission: ModuleType, root: Path, capsys: Any) -> None:
    """Carry forward limits and the exact digest of each replaced record."""
    assert admit(admission, root, capsys, "--max-attempts", "2")[0] == 0
    previous = (root / "admission.json").read_bytes()
    (root / "previous.json").write_bytes(previous)
    (root / "admission.json").unlink()
    code, result = admit(admission, root, capsys, "--replaces", "previous.json")
    assert code == 1
    assert_code(result, "replaces-invalid")
    with (root / "candidate.yaml").open("ab") as stream:
        stream.write(b" ")
    assert admit(admission, root, capsys, "--replaces", "previous.json")[0] == 0
    record = json.loads((root / "admission.json").read_bytes())
    assert (record["attempt"], record["max_attempts"], record["replaces"]) == (
        2,
        2,
        digest(previous),
    )
    (root / "previous.json").write_bytes((root / "admission.json").read_bytes())
    (root / "admission.json").unlink()
    with (root / "candidate.yaml").open("ab") as stream:
        stream.write(b" ")
    code, result = admit(admission, root, capsys, "--replaces", "previous.json")
    assert code == 1
    assert_code(result, "attempt-limit")
    code, result = admit(
        admission, root, capsys, "--replaces", "previous.json", "--max-attempts", "5"
    )
    assert code == 2
    assert_code(result, "usage")


@pytest.mark.parametrize(
    "raw", [b"{}", b'{"attempt":NaN}', b'{"a":1,"a":2}', b"[]", b"[" * 33 + b"0" + b"]" * 33]
)
def test_malformed_records(admission: ModuleType, root: Path, capsys: Any, raw: bytes) -> None:
    """Malformed records cannot verify or extend an attempt chain."""
    (root / "previous.json").write_bytes(raw)
    code, result = admit(admission, root, capsys, "--replaces", "previous.json")
    assert code == 1
    assert_code(result, "replaces-invalid")
    code, result = invoke(admission, root, capsys, "verify", "previous.json")
    assert code == 1
    assert_code(result, "record-malformed")


def unsafe_input(
    path: Path, kind: str, monkeypatch: pytest.MonkeyPatch, *, limit: int = 1_048_576
) -> str:
    """Reusable confinement fixture for aliases, non-files, size and replacement races."""
    root = path.parent
    original = path.read_bytes()
    if kind == "symlink":
        backup = root / "private-input"
        backup.write_bytes(original)
        path.unlink()
        path.symlink_to(backup)
    elif kind == "hardlink":
        os.link(path, root / "private-input")
    elif kind == "fifo":
        path.unlink()
        os.mkfifo(path)
    elif kind == "oversize":
        with path.open("wb") as stream:
            stream.truncate(limit + 1)
    elif kind == "swap":
        real_read = os.read
        replaced = False

        def swap(fd: int, size: int) -> bytes:
            """Replace the pathname while the original descriptor stays open."""
            nonlocal replaced
            if not replaced and os.fstat(fd).st_ino == path.stat().st_ino:
                replaced = True
                replacement = root / "private-input"
                replacement.write_bytes(original)
                replacement.replace(path)
            return real_read(fd, size)

        monkeypatch.setattr(os, "read", swap)
    if kind == "escape":
        outside = root.parent / (root.name + "-private-input")
        outside.write_bytes(original)
        return "../" + outside.name
    return path.name


@pytest.mark.parametrize("operation", ["admit", "verify"])
@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo", "escape", "oversize", "swap"])
@pytest.mark.parametrize("argument", ["candidate", "policy", "replaces", "record", "evidence"])
def test_confined_inputs(
    admission: ModuleType,
    root: Path,
    capsys: Any,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
    argument: str,
    operation: str,
) -> None:
    """Every read boundary rejects aliases, non-files, traversal, size and races."""
    assert admit(admission, root, capsys)[0] == 0
    names = {
        "candidate": "candidate.yaml",
        "policy": "trusted-policy.json",
        "replaces": "admission.json",
        "record": "admission.json",
        "evidence": "test-report.json",
    }
    path = root / names[argument]
    locator = unsafe_input(
        path, kind, monkeypatch, limit=536_870_912 if argument == "evidence" else 1_048_576
    )
    if operation == "verify":
        if kind == "escape" and argument in ("candidate", "policy"):
            record = json.loads((root / "admission.json").read_bytes())
            record[argument]["locator"] = locator
            (root / "admission.json").write_text(json.dumps(record))
        elif kind == "escape" and argument == "evidence":
            candidate = admission.handoff.parse_yaml((root / "candidate.yaml").read_bytes())
            candidate["evidence"][2]["locator"] = locator
            raw = admission.handoff.yaml_bytes(candidate)
            (root / "candidate.yaml").write_bytes(raw)
            record = json.loads((root / "admission.json").read_bytes())
            record["candidate"]["sha256"] = digest(raw)
            (root / "admission.json").write_text(json.dumps(record))
        code, result = invoke(
            admission,
            root,
            capsys,
            "verify",
            locator if argument in ("record", "replaces") else "admission.json",
        )
    elif argument == "record":
        code, result = invoke(admission, root, capsys, "verify", locator)
    elif argument == "evidence":
        if kind == "escape":
            candidate = admission.handoff.parse_yaml((root / "candidate.yaml").read_bytes())
            candidate["evidence"][2]["locator"] = locator
            (root / "candidate.yaml").write_bytes(admission.handoff.yaml_bytes(candidate))
        code, result = admit(admission, root, capsys, "--output", "new.json")
    else:
        options = {
            "candidate": [],
            "policy": ["--policy", locator],
            "replaces": ["--replaces", locator],
        }
        if argument == "candidate":
            code, result = invoke(
                admission,
                root,
                capsys,
                "admit",
                locator,
                "--policy",
                "trusted-policy.json",
                "--expect-environment",
                "staging",
                "--output",
                "new.json",
            )
        else:
            code, result = admit(
                admission, root, capsys, "--output", "new.json", *options[argument]
            )
    assert code in (1, 2), result
    assert result["status"] not in ("admitted", "current")
    assert not (root / "new.json").exists()
    assert "private-input" not in json.dumps(result)
    assert locator not in json.dumps(result)


def test_cli_utf8_and_usage(root: Path) -> None:
    """Exercise real argv, streams and exits under an ASCII process locale."""
    script = SCRIPTS / "release_admission.py"
    base = [sys.executable, "-X", "utf8=0", str(script)]
    env = {**os.environ, "PYTHONIOENCODING": "ascii", "LC_ALL": "C"}
    for args, expected in [
        (
            [
                "admit",
                "candidate.yaml",
                "--policy",
                "trusted-policy.json",
                "--expect-environment",
                "staging",
                "--output",
                "admission.json",
            ],
            0,
        ),
        (["verify", "admission.json"], 0),
        (
            ["admit", "candidate.yaml", "--expect-environment", "staging", "--output", "new.json"],
            1,
        ),
        (["private-input"], 2),
    ]:
        proc = subprocess.run(
            [*base, *args, "--root", str(root), "--now", NOW],
            capture_output=True,
            env=env,
            check=False,
            timeout=10,
        )
        assert proc.returncode == expected
        assert proc.stderr == b""
        result = json.loads(proc.stdout.decode("utf-8"))
        assert "private-input" not in json.dumps(result)


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo", "escape", "directory-link"])
def test_confined_output(admission: ModuleType, root: Path, capsys: Any, kind: str) -> None:
    """Publishing never follows output aliases or overwrites existing entries."""
    destination = root / "new.json"
    source = root / "test-report.json"
    before = source.read_bytes()
    if kind == "symlink":
        destination.symlink_to(source)
    elif kind == "hardlink":
        os.link(source, destination)
    elif kind == "fifo":
        os.mkfifo(destination)
    elif kind == "directory-link":
        (root / "linked").symlink_to(root, target_is_directory=True)
    output = (
        "../private-input"
        if kind == "escape"
        else ("linked/new.json" if kind == "directory-link" else "new.json")
    )
    code, result = admit(admission, root, capsys, "--output", output)
    assert code in (1, 2)
    assert source.read_bytes() == before
    assert output not in json.dumps(result)
    assert not list(root.glob(".release-handoff-*.tmp"))


@pytest.mark.parametrize(
    "mutation",
    [
        "unknown",
        "boolean",
        "zero",
        "limit",
        "duplicate",
        "digest",
        "first-replaces",
        "later-without-replaces",
        "time",
        "policy-id",
    ],
)
def test_record_shape(admission: ModuleType, root: Path, capsys: Any, mutation: str) -> None:
    """Reject unknown fields, ambiguous counters, duplicate ids and malformed pins."""
    assert admit(admission, root, capsys)[0] == 0
    record = json.loads((root / "admission.json").read_bytes())
    if mutation == "unknown":
        record["waive"] = True
    elif mutation == "boolean":
        record["attempt"] = True
    elif mutation == "zero":
        record["attempt"] = 0
    elif mutation == "limit":
        record["attempt"] = 4
    elif mutation == "duplicate":
        record["evidence"].append(record["evidence"][0])
    elif mutation == "digest":
        record["candidate"]["sha256"] = "invalid"
    elif mutation == "first-replaces":
        record["replaces"] = digest(b"previous")
    elif mutation == "later-without-replaces":
        record["attempt"] = 2
    elif mutation == "time":
        record["admitted_at"] = "invalid"
    elif mutation == "policy-id":
        record["policy"]["id"] = "different"
    (root / "admission.json").write_text(json.dumps(record))
    before = snapshot(root)
    code, result = invoke(admission, root, capsys, "verify", "admission.json")
    assert code == 1
    assert_code(result, "record-malformed")
    assert snapshot(root) == before


@pytest.mark.parametrize("value", ["0", "-1", "NaN", "private-input"])
def test_invalid_attempt_option(
    admission: ModuleType, root: Path, capsys: Any, value: str
) -> None:
    """Attempt limits are positive integers and parser failures never echo argv."""
    code, result = admit(admission, root, capsys, "--max-attempts", value)
    assert code == 2
    assert_code(result, "usage")
    assert "private-input" not in json.dumps(result)


def test_stream_configuration(
    admission: ModuleType, root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both streams switch to UTF-8 before any output, even for usage errors."""
    configured: list[str] = []

    class Stream(io.StringIO):
        """Record the encoding contract before accepting the first printed text."""

        def reconfigure(self, *, encoding: str) -> None:
            """Record both stream configuration calls."""
            configured.append(encoding)

        def write(self, value: str) -> int:
            """Require stdout and stderr configuration before the first write."""
            assert configured == ["utf-8", "utf-8"]
            return super().write(value)

    stdout, stderr = Stream(), Stream()
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", stderr)
    assert admission.main(["private-input"]) == 2
    assert json.loads(stdout.getvalue())["status"] == "error"
    assert stderr.getvalue() == ""


def test_size_checked_before_read(
    admission: ModuleType, root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Oversized descriptors are rejected without reading even one byte."""
    path = root / "oversized"
    with path.open("wb") as stream:
        stream.truncate(536_870_913)

    def refuse_read(*args: Any, **kwargs: Any) -> bytes:
        """Any read of the oversized input violates the pre-read limit."""
        raise AssertionError("read before size check")

    monkeypatch.setattr(os, "read", refuse_read)
    for helper in (admission.read_manifest, admission.hash_evidence):
        with pytest.raises(admission.handoff.Refusal):
            helper(root, "oversized")


@pytest.mark.parametrize("failure", ["partial-write", "publish", "directory-swap"])
def test_atomic_output_failure(
    admission: ModuleType, root: Path, capsys: Any, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    """Failed writes, publication and replaced output parents leave no record."""
    (root / "out").mkdir()
    if failure == "partial-write":

        def fail_write(fd: int, raw: bytes) -> None:
            """Leave a partial temporary file then fail."""
            os.write(fd, raw[:10])
            raise OSError("private-input")

        monkeypatch.setattr(admission.handoff, "write_candidate", fail_write)
    else:
        publish = admission.handoff.publish_candidate

        def fail_publish(directory: int, temporary: str, destination: str) -> None:
            """Inject a publication failure or replace its pinned parent."""
            if failure == "publish":
                raise OSError("private-input")
            (root / "out").rename(root / "moved")
            (root / "out").mkdir()
            publish(directory, temporary, destination)

        monkeypatch.setattr(admission.handoff, "publish_candidate", fail_publish)
    code, result = admit(admission, root, capsys, "--output", "out/new.json")
    assert code == 2
    assert "private-input" not in json.dumps(result)
    assert not list(root.rglob("new.json"))
    assert not list(root.rglob(".release-handoff-*.tmp"))


@pytest.mark.parametrize("command", ["admit", "verify"])
def test_unreadable_top_level(
    admission: ModuleType, root: Path, capsys: Any, command: str
) -> None:
    """Missing primary input has exit 2, while an unavailable replacement refuses."""
    args = (
        [
            "--policy",
            "trusted-policy.json",
            "--expect-environment",
            "staging",
            "--output",
            "new.json",
        ]
        if command == "admit"
        else []
    )
    code, result = invoke(admission, root, capsys, command, "private-input", *args)
    assert code == 2
    assert_code(result, "unreadable-input")
    assert "private-input" not in json.dumps(result)
    code, result = admit(admission, root, capsys, "--replaces", "private-input")
    assert code == 1
    assert_code(result, "replaces-invalid")

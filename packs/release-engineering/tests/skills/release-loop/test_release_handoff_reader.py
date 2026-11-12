"""Exercise the release-owned YAML grammar and bounded reader."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[3] / ".apm/skills/release-loop/scripts/release_handoff.py"
)
spec = importlib.util.spec_from_file_location(
    "release_engineering_release_loop_release_handoff", SCRIPT
)
assert spec and spec.loader
handoff = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = handoff
spec.loader.exec_module(handoff)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("key: value # comment\n", {"key": "value"}),
        ("key: a#b\n", {"key": "a#b"}),
        ('key: "# : ! & * [ ] | >" # tail\n', {"key": "# : ! & * [ ] | >"}),
        ("key: 'it''s # safe: yes'\n", {"key": "it's # safe: yes"}),
        ('key: "a\\n\\t\\u263a\\\\\\""\n', {"key": 'a\n\t☺\\"'}),
        (
            'a: []\nb: {}\nc: true\nd: false\ne: null\nf: -12\ng: 01\nh: "2.0"\n',
            {"a": [], "b": {}, "c": True, "d": False, "e": None, "f": -12, "g": "01", "h": "2.0"},
        ),
        (
            "items:\n  - id: one\n    values:\n      - a\n      - b\n  - id: two\n",
            {"items": [{"id": "one", "values": ["a", "b"]}, {"id": "two"}]},
        ),
        ("- - a\n  - b\n- - c\n", [["a", "b"], ["c"]]),
        ('"a: b": value\n', {"a: b": "value"}),
    ],
)
def test_accept_subset(text: str, expected: Any) -> None:
    """Keep quoted punctuation distinct from structural syntax."""
    assert handoff.parse_yaml(text.encode()) == expected


@pytest.mark.parametrize(
    "text",
    [
        "a: !tag x",
        "a: &name x",
        "a: *name",
        "a: [one]",
        "a: {one: two}",
        "---\na: b",
        "a: b\n...",
        "<<: x",
        '"<<": x',
        "\ta: b",
        "a:\n\t- b",
        "a: |\n  text",
        "a: >-\n  text",
    ],
)
def test_reject_unsupported(text: str) -> None:
    """Every excluded syntax class has an explicit refusal."""
    with pytest.raises(handoff.Refusal, match="unsupported-input"):
        handoff.parse_yaml(text.encode())


@pytest.mark.parametrize("text", ["a: 1\na: 2", 'a: 1\n"a": 2', "'a': 1\na: 2"])
def test_duplicate_keys(text: str) -> None:
    """Compare decoded key spellings."""
    with pytest.raises(handoff.Refusal, match="duplicate-key"):
        handoff.parse_yaml(text.encode())


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        (b"x" * 1_048_577, "manifest-too-large"),
        (('a: "' + "é" * 32769 + '"').encode(), "string-limit"),
        (("a" * 65537 + ": x").encode(), "string-limit"),
        (("a:\n" + "  - x\n" * 1001).encode(), "list-limit"),
        (("".join("  " * i + "a:\n" for i in range(33))).encode(), "depth-limit"),
        (b"\x1f\x8b" + b"x" * 20, "unsupported-input"),
        (b"PK\x03\x04" + b"x" * 20, "unsupported-input"),
    ],
)
def test_limits_precede_semantics(raw: bytes, code: str) -> None:
    """Parsing refuses budgets before interpreting normative fields."""
    with pytest.raises(handoff.Refusal, match=code):
        handoff.parse_yaml(raw)


@pytest.mark.parametrize("shape", ["line", "escapes", "keys", "comments"])
def test_linear_megabyte(shape: str) -> None:
    """Adversarial input finishes under the public two-second budget."""
    seeds = {
        "line": b"a: " + b"x" * (1048576 - 3),
        "escapes": b'a: "' + b"\\n" * 524285 + b'"',
        "keys": b"".join(f"k{i}: x\n".encode() for i in range(80000)),
        "comments": b"# comment\n" * 104857,
    }
    raw = seeds[shape][:1048576].ljust(1048576, b" ")
    start = time.perf_counter()
    with contextlib.suppress(handoff.Refusal):
        handoff.parse_yaml(raw)
    assert time.perf_counter() - start < 2


NOW = "2026-11-12T12:00:00Z"


def yaml_bytes(value: Any, indent: int = 0) -> bytes:
    """Serialize fixture data using only supported block forms."""
    prefix = " " * indent
    lines: list[str] = []
    if isinstance(value, dict) and value:
        for key, child in value.items():
            label = prefix + json.dumps(key) + ":"
            if isinstance(child, (dict, list)) and child:
                lines.append(label + "\n" + yaml_bytes(child, indent + 2).decode().rstrip("\n"))
            else:
                lines.append(label + " " + json.dumps(child))
    elif isinstance(value, list) and value:
        for child in value:
            if isinstance(child, (dict, list)) and child:
                lines.append(prefix + "-\n" + yaml_bytes(child, indent + 2).decode().rstrip("\n"))
            else:
                lines.append(prefix + "- " + json.dumps(child))
    else:
        lines.append(prefix + json.dumps(value))
    return ("\n".join(lines) + "\n").encode()


@pytest.fixture
def candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build real local artifact, provenance, check and procedure bytes."""

    def no_network(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket, "socket", no_network)
    monkeypatch.setattr(urllib.request, "urlopen", no_network)
    artifact = b"image bytes"
    digest = "sha256:" + hashlib.sha256(artifact).hexdigest()
    subject = {"id": "app", "sha256": digest}
    evidence = []
    for identifier, raw in [
        ("artifact", artifact),
        ("proof", b"attestation"),
        ("procedure", b"approved steps"),
    ]:
        (tmp_path / identifier).write_bytes(raw)
        evidence.append({
            "id": identifier,
            "kind": "test",
            "locator": identifier,
            "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
            "media_type": "application/octet-stream",
            "producer": "ci",
            "observed_at": NOW,
            "subjects": [dict(subject)],
        })
    data = {
        "schema_version": "2.0",
        "candidate_id": "candidate-1",
        "created_at": NOW,
        "producer": "ci",
        "sources": [{"repository": "example", "revision": "a" * 40}],
        "target": {"environment": "test", "account": "example"},
        "components": [
            {
                "id": "app",
                "kind": "oci-image",
                "image_ref": "registry.example/app:v1@" + digest,
                "artifact": "artifact",
            }
        ],
        "evidence": evidence,
        "provenance": ["proof"],
        "checks": [
            {
                "id": "security",
                "stage": "security",
                "status": "pass",
                "subjects": [dict(subject)],
                "evidence": ["proof"],
            }
        ],
        "changes": {"baseline": "v0", "entries": []},
        "phases": [
            {"id": "deploy", "depends_on": [], "components": ["app"], "procedures": ["procedure"]}
        ],
        "repair_owner": {"id": "operations"},
    }
    policy = {
        "id": "policy",
        "max_age_seconds": 60,
        "required_checks": [
            {
                "id": "security",
                "stage": "security",
                "component_kind": "oci-image",
                "allowed_not_applicable_reasons": ["approved exception"],
            }
        ],
        "approved_procedures": [{"id": "procedure", "sha256": evidence[2]["sha256"]}],
    }
    return data, policy


def validate(data: dict[str, Any], policy: Any, root: Path, **kwargs: Any) -> dict[str, Any]:
    """Drive the real YAML reader and semantic validator together."""
    return handoff.validate_bytes(yaml_bytes(data), root=root, policy=policy, now=NOW, **kwargs)


def codes(result: dict[str, Any]) -> set[str]:
    """Extract fixed diagnostic codes."""
    return {issue["code"] for issue in result["issues"]}


def test_complete_candidate(candidate: Any, tmp_path: Path) -> None:
    """An image-only candidate has verified local evidence."""
    data, policy = candidate
    result = validate(data, policy, tmp_path)
    assert result["status"] == "valid", result
    assert {item["verification"] for item in result["evidence"]} == {"verified"}


def test_plan_only(candidate: Any, tmp_path: Path) -> None:
    """Plan bundles need byte validation without a cross-pack import."""
    data, policy = candidate
    data["components"][0] = {"id": "app", "kind": "terraform-plan", "plan_bundle": "artifact"}
    policy["required_checks"][0]["component_kind"] = "terraform-plan"
    assert validate(data, policy, tmp_path)["status"] == "valid"


@pytest.mark.parametrize(
    ("field", "value", "code", "status"),
    [
        ("components", [], "empty-components", "invalid"),
        (
            "components",
            [{"id": "app", "kind": "future"}],
            "unsupported-component-kind",
            "incomplete",
        ),
        ("schema_version", "3.0", "unsupported-version", "error"),
        ("candidate_id", "SECRET/unsafe", "unsafe-identifier", "invalid"),
        ("producer", 5, "malformed-type", "invalid"),
        ("SECRET-field", "SECRET-value", "unknown-field", "invalid"),
        ("extensions", {"required_checks": []}, None, "valid"),
    ],
)
def test_root_mutations(
    candidate: Any, tmp_path: Path, field: str, value: Any, code: str | None, status: str
) -> None:
    """Validate structure and sanitize all untrusted output."""
    data, policy = candidate
    data[field] = value
    result = validate(data, policy, tmp_path)
    assert result["status"] == status, result
    if code:
        assert code in codes(result)
    assert "SECRET" not in json.dumps(result)


@pytest.mark.parametrize(
    "field",
    [
        "candidate_id",
        "created_at",
        "producer",
        "sources",
        "target",
        "components",
        "evidence",
        "provenance",
        "checks",
        "changes",
        "phases",
        "repair_owner",
    ],
)
def test_missing_root_fields(candidate: Any, tmp_path: Path, field: str) -> None:
    """Absent facts stay incomplete rather than crashing semantic checks."""
    data, policy = candidate
    del data[field]
    result = validate(data, policy, tmp_path)
    assert result["status"] == "incomplete", result
    assert "missing-field" in codes(result)


@pytest.mark.parametrize(
    ("location", "field", "value", "code", "status"),
    [
        (
            "component",
            "image_ref",
            "registry.example/app@sha256:" + "a" * 64,
            "invalid-image-reference",
            "invalid",
        ),
        (
            "component",
            "image_ref",
            "registry.example/app:v1",
            "invalid-image-reference",
            "invalid",
        ),
        ("component", "plan_bundle", "artifact", "unknown-field", "invalid"),
        ("check", "status", "fail", "check-failed", "invalid"),
        ("check", "status", "not-run", "missing-evidence", "incomplete"),
        ("check", "status", "not-applicable", "invalid-applicability", "invalid"),
        (
            "check",
            "subjects",
            [{"id": "app", "sha256": "sha256:" + "0" * 64}],
            "subject-mismatch",
            "invalid",
        ),
        ("check", "evidence", [], "missing-evidence", "incomplete"),
        (
            "evidence",
            "locator",
            "https://example.invalid/proof",
            "unverified-evidence",
            "incomplete",
        ),
        (
            "evidence",
            "locator",
            "https://user:SECRET@example.invalid/proof",
            "credential-locator",
            "invalid",
        ),
        (
            "evidence",
            "locator",
            "https://example.invalid/proof?X-Amz-Signature=SECRET",
            "credential-locator",
            "invalid",
        ),
        ("evidence", "locator", "../SECRET", "unsafe-path", "invalid"),
        ("evidence", "observed_at", "2026-11-12T11:58:59Z", "stale", "incomplete"),
        ("evidence", "observed_at", "2026-11-12T12:00:01Z", "future-time", "invalid"),
        ("phase", "depends_on", ["deploy"], "invalid-phase-order", "invalid"),
        ("phase", "components", ["unknown"], "missing-evidence", "incomplete"),
        ("phase", "procedures", ["proof"], "unapproved-procedure", "invalid"),
    ],
)
def test_bound_mutations(
    candidate: Any, tmp_path: Path, location: str, field: str, value: Any, code: str, status: str
) -> None:
    """Change one trust boundary at a time."""
    data, policy = candidate
    targets = {
        "component": data["components"][0],
        "check": data["checks"][0],
        "evidence": data["evidence"][1],
        "phase": data["phases"][0],
    }
    targets[location][field] = value
    result = validate(data, policy, tmp_path)
    assert result["status"] == status, result
    assert code in codes(result), result
    assert "SECRET" not in json.dumps(result)


def test_evidence_tampering_and_size(candidate: Any, tmp_path: Path) -> None:
    """Separate byte identity from the streamed evidence budget."""
    data, policy = candidate
    (tmp_path / "artifact").write_bytes(b"tampered")
    assert "digest-mismatch" in codes(validate(data, policy, tmp_path))
    assert "evidence-too-large" in codes(validate(data, policy, tmp_path, evidence_limit=2))


@pytest.mark.parametrize(
    "locator",
    [
        "/absolute",
        "C:drive",
        "dir\\file",
        "./artifact",
        "folder//artifact",
        "link",
        "directory",
        "hardlink",
    ],
)
def test_confined_evidence(candidate: Any, tmp_path: Path, locator: str) -> None:
    """Refuse ambiguous paths and non-regular or linked objects."""
    data, policy = candidate
    (tmp_path / "link").symlink_to(tmp_path / "artifact")
    (tmp_path / "directory").mkdir()
    import os

    os.link(tmp_path / "artifact", tmp_path / "hardlink")
    data["evidence"][1]["locator"] = locator
    assert "unsafe-path" in codes(validate(data, policy, tmp_path))


def test_policy_is_required_and_trusted(candidate: Any, tmp_path: Path) -> None:
    """Candidate metadata cannot remove external requirements."""
    data, policy = candidate
    assert "policy-missing" in codes(validate(data, None, tmp_path))
    data["checks"] = []
    data["extensions"] = {"required_checks": []}
    assert "missing-evidence" in codes(validate(data, policy, tmp_path))
    policy["max_age_seconds"] = True
    assert "malformed-type" in codes(validate(data, policy, tmp_path))


def test_allowed_applicability_and_age_boundary(candidate: Any, tmp_path: Path) -> None:
    """Only trusted exceptions pass; exact age boundaries are inclusive."""
    data, policy = candidate
    data["checks"][0].update(
        status="not-applicable", reason="approved exception", policy_basis="policy/security"
    )
    data["created_at"] = "2026-11-12T11:59:00Z"
    assert validate(data, policy, tmp_path)["status"] == "valid"


def test_cli_integration(candidate: Any, tmp_path: Path) -> None:
    """The shipped CLI emits exactly one JSON object with stable exits."""
    data, policy = candidate
    (tmp_path / "input.yaml").write_bytes(yaml_bytes(data))
    (tmp_path / "policy.json").write_text(json.dumps(policy))
    args = [
        sys.executable,
        str(SCRIPT),
        "validate",
        "input.yaml",
        "--root",
        str(tmp_path),
        "--now",
        NOW,
    ]
    for extra, expected in [
        (["--policy", "policy.json"], 0),
        ([], 1),
        (["--policy", "missing"], 2),
    ]:
        proc = subprocess.run(args + extra, capture_output=True, text=True, check=False)
        assert proc.returncode == expected, (proc.stdout, proc.stderr)
        assert set(json.loads(proc.stdout)) == {"status", "issues", "evidence"}
        assert proc.stderr == ""


def test_schema_parity() -> None:
    """The shipped schema matches record fields, enums and closed objects."""
    path = (
        Path(__file__).resolve().parents[3]
        / ".apm/skills/release-loop/references/release-handoff.v2.schema.json"
    )
    schema = json.loads(path.read_text())
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    for name, fields in handoff.RECORDS.items():
        record = schema["$defs"][name]
        assert record["additionalProperties"] is False
        assert set(record["required"]) == {key for key in fields if not key.endswith("?")}
        assert set(record["properties"]) == {key.rstrip("?") for key in fields} | {"extensions"}
        for key, descriptor in fields.items():
            field = record["properties"][key.rstrip("?")]
            if descriptor in handoff.ENUMS:
                assert field["enum"] == list(handoff.ENUMS[descriptor])
            if descriptor == "version":
                assert field["const"] == "2.0"


@pytest.mark.parametrize("raw", [b'a: "unterminated', b'a: "bad\\xescape"', b"a: 1\n  b: 2"])
def test_malformed_yaml(raw: bytes) -> None:
    """Malformed grammar never partially passes."""
    with pytest.raises(handoff.Refusal, match="malformed-input"):
        handoff.parse_yaml(raw)


def test_exact_depth_and_list_boundaries() -> None:
    """A scalar after 32 sequence containers stays within the depth limit."""
    raw = ("- " * 32 + "value").encode()
    value = handoff.parse_yaml(raw)
    for _ in range(32):
        value = value[0]
    assert value == "value"
    assert len(handoff.parse_yaml(("- x\n" * 1000).encode())) == 1000


@pytest.mark.parametrize("collection", ["components", "evidence", "checks", "phases"])
def test_duplicate_record_ids(candidate: Any, tmp_path: Path, collection: str) -> None:
    """IDs are unique in every owned record collection."""
    data, policy = candidate
    data[collection].append(dict(data[collection][0]))
    assert "duplicate-id" in codes(validate(data, policy, tmp_path))


def test_evidence_replacement_is_refused(
    candidate: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A directory-entry replacement cannot borrow the old descriptor's digest."""
    import os

    original = os.read
    replaced = False

    def replace_after_read(fd: int, count: int) -> bytes:
        nonlocal replaced
        raw = original(fd, count)
        if raw == b"attestation" and not replaced:
            replacement = tmp_path / "replacement"
            replacement.write_bytes(b"attestation")
            replacement.replace(tmp_path / "proof")
            replaced = True
        return raw

    monkeypatch.setattr(os, "read", replace_after_read)
    data, policy = candidate
    assert "unsafe-path" in codes(validate(data, policy, tmp_path))


@pytest.mark.parametrize(
    "query", ["access_token", "api-key", "%6bey", "PASSword", "authorization"]
)
def test_credential_query_tokens(candidate: Any, tmp_path: Path, query: str) -> None:
    """Decode and split credential query keys before any network work."""
    data, policy = candidate
    data["evidence"][1]["locator"] = "oci://example.invalid/ref?" + query + "=SECRET"
    result = validate(data, policy, tmp_path)
    assert "credential-locator" in codes(result)
    assert "SECRET" not in json.dumps(result)

"""Exercise the shipped plan contract without infrastructure or network access."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import UTC
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / ".apm/skills/generate-iac/scripts/plan_bundle.py"
SCHEMA = (
    Path(__file__).resolve().parents[3]
    / ".apm/skills/generate-iac/references/iac-plan-bundle.v1.schema.json"
)
NOW = "2026-01-01T12:00:00Z"


@pytest.fixture(scope="module")
def module() -> Any:
    """Load the portable script under a unique module identity."""
    spec = importlib.util.spec_from_file_location("iac_terraform_generate_iac_plan_bundle", SCRIPT)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = result
    spec.loader.exec_module(result)
    return result


@pytest.fixture(autouse=True)
def no_network(monkeypatch: Any) -> None:
    """Fail on any attempted network operation."""

    def refuse(*args: Any, **kwargs: Any) -> None:
        """Exercise refuse."""
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "socket", refuse)
    monkeypatch.setattr(urllib.request, "urlopen", refuse)


@pytest.fixture
def bundle(tmp_path: Path) -> tuple[dict[str, Any], dict[str, Any], Path]:
    """Create synthetic saved-plan bytes and complete bound local evidence."""
    evidence = []
    for name in ["saved", "inspection", "request", "constraint", "lock", "proof"]:
        content = ("synthetic-" + name).encode()
        (tmp_path / name).write_bytes(content)
        evidence.append({
            "id": name,
            "kind": "artifact",
            "locator": name,
            "sha256": "sha256:" + hashlib.sha256(content).hexdigest(),
            "media_type": "application/octet-stream",
            "producer": "fixture",
            "observed_at": NOW,
            "subjects": [],
        })
    subject = {"id": "saved", "sha256": evidence[0]["sha256"]}
    for item in evidence:
        item["subjects"] = [copy.deepcopy(subject)]
    data = {
        "schema_version": "iac-plan-bundle.v1",
        "source": {"repository": "local", "revision": "a" * 40},
        "request": "request",
        "constraints": ["constraint"],
        "evidence": evidence,
        "toolchain": {
            "engine": "terraform",
            "version": "1.9.0",
            "providers": [{"source": "vendor/provider", "version": "1.0"}],
            "lock": "lock",
        },
        "target": {"environment": "test", "account": "example"},
        "state": {"backend": "local", "workspace": "default", "lineage": "lineage", "serial": 0},
        "plan": {"saved_plan": "saved", "inspection": "inspection"},
        "created_at": NOW,
        "freshness": {"policy_id": "trusted", "max_age_seconds": 60},
        "checks": [
            {
                "id": stage,
                "stage": stage,
                "status": "pass",
                "subjects": [copy.deepcopy(subject)],
                "evidence": ["proof"],
            }
            for stage in ["validation", "policy", "security", "review"]
        ],
        "effects": {
            "changes": [{"address": "resource.example", "actions": ["create"]}],
            "stateful_impacts": [],
            "cost": None,
        },
    }
    policy = {
        "id": "trusted",
        "max_age_seconds": 120,
        "required_checks": [],
        "approved_procedures": [],
    }
    return data, policy, tmp_path


def validate(
    module: Any, bundle: tuple[dict[str, Any], dict[str, Any], Path], **kwargs: Any
) -> dict[str, Any]:
    """Drive real encoded input rather than bypassing the input reader."""
    data, policy, root = bundle
    return module.validate_bytes(
        json.dumps(data).encode(), root=root, policy=policy, now=NOW, **kwargs
    )


def codes(result: dict[str, Any]) -> set[str]:
    """Return stable issue codes for outcome assertions."""
    return {item["code"] for item in result["issues"]}


def test_complete(module: Any, bundle: Any) -> None:
    """A complete local bundle verifies every evidence file."""
    result = validate(module, bundle)
    assert result["status"] == "valid"
    assert result["issues"] == []
    assert len(result["evidence"]) == 6
    assert all(e["verification"] == "verified" for e in result["evidence"])


@pytest.mark.parametrize(
    "field",
    [
        "source",
        "request",
        "constraints",
        "evidence",
        "toolchain",
        "target",
        "state",
        "plan",
        "created_at",
        "freshness",
        "checks",
        "effects",
        "schema_version",
    ],
)
def test_missing_root_fields(module: Any, bundle: Any, field: str) -> None:
    """Missing root facts are incomplete rather than valid."""
    del bundle[0][field]
    result = validate(module, bundle)
    assert result["status"] == "incomplete"
    assert "missing-field" in codes(result)


@pytest.mark.parametrize(
    "path,value",
    [
        (["state", "serial"], True),
        (["freshness", "max_age_seconds"], True),
        (["target", "account"], 2),
        (["evidence"], {}),
        (["checks", 0, "evidence"], "proof"),
        (["effects", "cost"], False),
        (["extensions"], []),
        (["source"], None),
    ],
)
def test_types(module: Any, bundle: Any, path: list[Any], value: Any) -> None:
    """Wrong normative types, including boolean integers, are invalid."""
    target = bundle[0]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    result = validate(module, bundle)
    assert result["status"] == "invalid"
    assert "malformed-type" in codes(result)


@pytest.mark.parametrize(
    "path,value",
    [
        (["toolchain", "engine"], "other"),
        (["checks", 0, "status"], "ok"),
        (["checks", 0, "stage"], "deploy"),
        (["effects", "changes", 0, "actions"], ["replace"]),
        (["state", "serial"], -1),
        (["freshness", "max_age_seconds"], 0),
        (["source", "revision"], "main"),
    ],
)
def test_present_invalid_values(module: Any, bundle: Any, path: list[Any], value: Any) -> None:
    """Enums, integer ranges and full revisions are enforced."""
    target = bundle[0]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    assert validate(module, bundle)["status"] == "invalid"


def test_unknown_fields_and_inert_extensions(module: Any, bundle: Any) -> None:
    """Unknown normative keys are redacted; metadata has no authority."""
    bundle[0]["extensions"] = {"required_checks": [], "secret-key": "sensitive"}
    assert validate(module, bundle)["status"] == "valid"
    bundle[0]["sensitive-key"] = "sensitive-value"
    result = validate(module, bundle)
    assert "unknown-field" in codes(result)
    output = json.dumps(result)
    assert "sensitive" not in output
    assert "<unknown>" in output


@pytest.mark.parametrize(
    "raw,code",
    [
        (b'{"x":1,"x":2}', "duplicate-key"),
        (b"{", "malformed-input"),
        (b'{"x":NaN}', "non-finite-number"),
        (b'{"x":Infinity}', "non-finite-number"),
        (b'{"x":-Infinity}', "non-finite-number"),
        (b'{"x":1e999}', "non-finite-number"),
        (b"\x1f\x8bxxx", "unsupported-input"),
        (b"PK\x03\x04xxx", "unsupported-input"),
        (b"\xff", "malformed-input"),
    ],
)
def test_reader_refusals(module: Any, tmp_path: Path, raw: bytes, code: str) -> None:
    """Invalid syntax and unsupported compression never reach validation."""
    result = module.validate_bytes(raw, root=tmp_path, policy=None, now=NOW)
    assert code in codes(result)


@pytest.mark.parametrize(
    "raw,code",
    [
        (b" " * 1048577, "manifest-too-large"),
        (b"[" * 33 + b"]" * 33, "depth-limit"),
        (json.dumps([0] * 1001).encode(), "list-limit"),
        (json.dumps({"x": "a" * 65537}).encode(), "string-limit"),
        (json.dumps({"a" * 65537: 0}).encode(), "string-limit"),
        (json.dumps({"x": "\u00e9" * 32769}).encode(), "string-limit"),
    ],
)
def test_first_limits(module: Any, tmp_path: Path, raw: bytes, code: str) -> None:
    """Each resource limit fires before normative shape checks."""
    result = module.validate_bytes(raw, root=tmp_path, policy=None, now=NOW)
    assert codes(result) == {code}


@pytest.mark.parametrize("value", ["[{}] " * 100, '\\"{}[]' * 100])
def test_depth_ignores_quoted_punctuation(module: Any, bundle: Any, value: str) -> None:
    """Escaped string contents do not count as containers."""
    bundle[0]["extensions"] = {"text": value}
    assert validate(module, bundle)["status"] == "valid"


@pytest.mark.parametrize(
    "raw",
    [
        b" " * 1048576,
        b'"' + b"\\n" * 524287 + b'"',
        b"{" + b'"x":0,' * 149796 + b'"z":0}',
        b"[" + b"0," * 524286 + b"0]",
    ],
)
def test_adversarial_linear_work(module: Any, tmp_path: Path, raw: bytes) -> None:
    """Full-budget hostile inputs complete within the reader time bound."""
    raw = raw.ljust(1048576, b" ")
    assert len(raw) == 1048576
    start = time.monotonic()
    module.validate_bytes(raw, root=tmp_path, policy=None, now=NOW)
    assert time.monotonic() - start < 2


@pytest.mark.parametrize(
    "locator",
    ["../outside", "/tmp/outside", "C:/outside", "a\\b", "a/../saved", "./saved", "a//saved"],
)
def test_unsafe_paths(module: Any, bundle: Any, locator: str) -> None:
    """Local locators cannot select an unconfined path."""
    bundle[0]["evidence"][0]["locator"] = locator
    result = validate(module, bundle)
    assert [issue for issue in result["issues"] if issue["code"] == "unsafe-path"] == [
        {"code": "unsafe-path", "path": "$.evidence[0].locator"}
    ]
    assert len([item for item in result["evidence"] if item["verification"] == "verified"]) == 5


def test_symlinks_and_nonregular(module: Any, bundle: Any) -> None:
    """Links, directories and FIFOs are refused without blocking."""
    data, _, root = bundle
    (root / "alias").symlink_to(root / "saved")
    data["evidence"][0]["locator"] = "alias"
    assert "unsafe-path" in codes(validate(module, bundle))
    (root / "dir").mkdir()
    data["evidence"][0]["locator"] = "dir"
    assert "unsafe-path" in codes(validate(module, bundle))
    (root / "linked").symlink_to(root, target_is_directory=True)
    data["evidence"][0]["locator"] = "linked/saved"
    assert "unsafe-path" in codes(validate(module, bundle))
    os.mkfifo(root / "fifo")
    data["evidence"][0]["locator"] = "fifo"
    assert "unsafe-path" in codes(validate(module, bundle))


@pytest.mark.parametrize(
    "locator",
    [
        "https://user:password@example.test/a",
        "https://example.test/a?access_token=secret",
        "https://example.test/a?api-key=secret",
        "https://example.test/a?X-Amz-Signature=secret",
        "https://example.test/a?%6bey=secret",
        "oci://example.test/a?AUTHORIZATION=secret",
    ],
)
def test_credentials_redacted(module: Any, bundle: Any, locator: str, capsys: Any) -> None:
    """Credential-bearing external locators are refused without output."""
    bundle[0]["evidence"][0]["locator"] = locator
    result = validate(module, bundle)
    assert "credential-locator" in codes(result)
    assert locator not in json.dumps(result)
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize(
    "locator", ["https://example.test/a?monkey=ok", "oci://example.test/image"]
)
def test_external_no_fetch(module: Any, bundle: Any, locator: str) -> None:
    """Required external artifacts remain unverified without any fetch."""
    bundle[0]["evidence"][0]["locator"] = locator
    result = validate(module, bundle)
    assert result["status"] == "incomplete"
    assert "unverified-evidence" in codes(result)
    assert result["evidence"][0] == {"id": "saved", "verification": "unverified"}


@pytest.mark.parametrize("index", [0, 1, 5])
def test_tamper(module: Any, bundle: Any, index: int) -> None:
    """Changed stored bytes invalidate their declared identity."""
    (bundle[2] / bundle[0]["evidence"][index]["locator"]).write_bytes(b"changed")
    assert "digest-mismatch" in codes(validate(module, bundle))


def test_stream_budget(module: Any, bundle: Any) -> None:
    """Evidence has a separate injectable streaming budget."""
    result = validate(module, bundle, evidence_limit=3)
    assert "evidence-too-large" in codes(result)
    assert "digest-mismatch" not in codes(result)


@pytest.mark.parametrize("record", ["inspection", "check", "proof"])
@pytest.mark.parametrize("field", ["id", "sha256"])
def test_subject_binding(module: Any, bundle: Any, record: str, field: str) -> None:
    """Subject IDs and digests must match assessed artifacts."""
    data = bundle[0]
    subject = (
        data["checks"][0]
        if record == "check"
        else data["evidence"][1 if record == "inspection" else 5]
    )["subjects"][0]
    subject[field] = "other" if field == "id" else "sha256:" + "0" * 64
    assert "subject-mismatch" in codes(validate(module, bundle))


@pytest.mark.parametrize("stage", ["validation", "policy", "security", "review"])
def test_mandatory_stages(module: Any, bundle: Any, stage: str) -> None:
    """Caller policy cannot remove any of the four plan stages."""
    bundle[0]["checks"] = [c for c in bundle[0]["checks"] if c["stage"] != stage]
    result = validate(module, bundle)
    assert result["status"] == "incomplete"
    assert "missing-evidence" in codes(result)


def test_failure_precedence(module: Any, bundle: Any) -> None:
    """A failed mandatory check wins over missing-stage gaps."""
    bundle[0]["checks"][0]["status"] = "fail"
    bundle[0]["checks"].pop()
    result = validate(module, bundle)
    assert result["status"] == "invalid"
    assert {"check-failed", "missing-evidence"} <= codes(result)


@pytest.mark.parametrize("seconds,expected", [(60, "valid"), (61, "incomplete"), (-1, "invalid")])
@pytest.mark.parametrize("field", ["created_at", "observed_at"])
def test_freshness(module: Any, bundle: Any, seconds: int, expected: str, field: str) -> None:
    """The exact maximum age passes; stale and future times do not."""
    from datetime import datetime, timedelta

    value = (
        (datetime(2026, 1, 1, 12, tzinfo=UTC) - timedelta(seconds=seconds))
        .isoformat()
        .replace("+00:00", "Z")
    )
    if field == "created_at":
        bundle[0][field] = value
    else:
        bundle[0]["evidence"][0][field] = value
    result = validate(module, bundle)
    assert result["status"] == expected
    if seconds == 61:
        assert "stale" in codes(result)
    if seconds == -1:
        assert "future-time" in codes(result)


@pytest.mark.parametrize(
    "name",
    [
        "environment",
        "account",
        "backend",
        "workspace",
        "lineage",
        "serial",
        "engine",
        "engine_version",
    ],
)
def test_expectations(module: Any, bundle: Any, name: str) -> None:
    """Each explicit consumer expectation is checked independently."""
    result = validate(module, bundle, expectations={name: 3 if name == "serial" else "other"})
    assert "expectation-mismatch" in codes(result)


def test_policy_requirements(module: Any, bundle: Any) -> None:
    """Additional checks and applicability come only from trusted policy."""
    data, policy, root = bundle
    assert (
        module.validate_bytes(json.dumps(data).encode(), root=root, policy=None, now=NOW)["status"]
        == "incomplete"
    )
    policy["required_checks"] = [
        {
            "id": "extra",
            "stage": "review",
            "component_kind": "terraform-plan",
            "allowed_not_applicable_reasons": ["approved"],
        }
    ]
    assert "missing-evidence" in codes(validate(module, bundle))
    extra = copy.deepcopy(data["checks"][0])
    extra.update(
        id="extra",
        stage="review",
        status="not-applicable",
        reason="approved",
        policy_basis="trusted/extra",
    )
    data["checks"].append(extra)
    assert validate(module, bundle)["status"] == "valid"
    extra["reason"] = "unapproved"
    assert "invalid-applicability" in codes(validate(module, bundle))


def test_new_workspace_and_source(module: Any, bundle: Any) -> None:
    """Alternative state and source identities retain exact bindings."""
    data = bundle[0]
    data["state"].pop("lineage")
    data["state"].pop("serial")
    data["state"]["new_workspace"] = "request"
    data["source"].pop("revision")
    data["source"]["snapshot"] = "constraint"
    assert validate(module, bundle)["status"] == "valid"
    assert "expectation-mismatch" in codes(
        validate(module, bundle, expectations={"lineage": "lineage"})
    )
    data["state"]["lineage"] = "lineage"
    assert validate(module, bundle)["status"] == "invalid"


@pytest.mark.parametrize("unsafe", ["secret value", "x/y", "", "a" * 129, "\nsecret"])
def test_unsafe_identifiers(module: Any, bundle: Any, unsafe: str) -> None:
    """Unsafe IDs are rejected and never included in evidence results."""
    bundle[0]["evidence"][0]["id"] = unsafe
    result = validate(module, bundle)
    assert "unsafe-identifier" in codes(result)
    assert all(e["id"] != unsafe for e in result["evidence"])
    if unsafe:
        assert unsafe not in json.dumps(result)


def test_duplicate_ids(module: Any, bundle: Any) -> None:
    """Check identities cannot collide within their collection."""
    bundle[0]["checks"][1]["id"] = bundle[0]["checks"][0]["id"]
    assert validate(module, bundle)["status"] == "invalid"


def test_schema_structure_parity(module: Any) -> None:
    """Deliberate schema drift breaks the structural comparison."""
    schema = json.loads(SCHEMA.read_text())
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema_parity(module, schema) == []
    for mutation in ["required", "enum", "closure", "version"]:
        changed = copy.deepcopy(schema)
        if mutation == "required":
            changed["$defs"]["Subject"]["required"].remove("id")
        if mutation == "enum":
            changed["$defs"]["Check"]["properties"]["status"]["enum"].append("maybe")
        if mutation == "closure":
            changed["$defs"]["Target"]["additionalProperties"] = True
        if mutation == "version":
            changed["$defs"]["Bundle"]["properties"]["schema_version"]["const"] = "other"
        assert schema_parity(module, changed)


def test_cli_smoke_and_errors(module: Any, bundle: Any) -> None:
    """The real UTF-8 CLI emits one JSON object and safe exit codes."""
    data, policy, root = bundle
    (root / "bundle.json").write_text(json.dumps(data))
    (root / "policy.json").write_text(json.dumps(policy))
    command = [
        sys.executable,
        str(SCRIPT),
        "validate",
        "bundle.json",
        "--root",
        str(root),
        "--policy",
        "policy.json",
        "--now",
        NOW,
    ]
    run = subprocess.run(command, capture_output=True, encoding="utf-8", check=False)
    assert run.returncode == 0, run.stderr + run.stdout
    assert json.loads(run.stdout)["status"] == "valid"
    assert run.stderr == ""
    assert module.main(command[2:] + ["--expect-environment", "other"]) == 1
    (root / "bundle.json").write_bytes(b'{"secret":NaN}')
    run = subprocess.run(command, capture_output=True, encoding="utf-8", check=False)
    assert run.returncode == 1
    assert "non-finite-number" in codes(json.loads(run.stdout))
    assert "secret" not in run.stdout + run.stderr
    for args in [
        [],
        ["validate", "missing", "--root", str(root), "--policy", "policy.json"],
        command[2:] + ["--unknown-secret"],
    ]:
        run = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            encoding="utf-8",
            check=False,
        )
        assert run.returncode == 2
        assert run.stderr == ""
        assert "secret" not in run.stdout
        json.loads(run.stdout)


@pytest.mark.parametrize("record", ["Subject", "Evidence", "Check"])
def test_record_id_uniqueness(module: Any, bundle: Any, record: str) -> None:
    """Every record collection with IDs enforces uniqueness."""
    data = bundle[0]
    if record == "Subject":
        data["evidence"][0]["subjects"] *= 2
    elif record == "Evidence":
        data["evidence"].append(copy.deepcopy(data["evidence"][0]))
    else:
        data["checks"].append(copy.deepcopy(data["checks"][0]))
    assert "duplicate-id" in codes(validate(module, bundle))


def test_all_evidence_subjects_bind(module: Any, bundle: Any) -> None:
    """An unrelated evidence record cannot carry a false Subject identity."""
    bundle[0]["evidence"][2]["subjects"][0]["sha256"] = "sha256:" + "0" * 64
    assert "subject-mismatch" in codes(validate(module, bundle))


@pytest.mark.parametrize("fault", ["future", "failed", "tamper"])
def test_missing_field_cannot_mask_invalid(module: Any, bundle: Any, fault: str) -> None:
    """Invalid semantic facts still win when another required field is missing."""
    del bundle[0]["request"]
    if fault == "future":
        bundle[0]["created_at"] = "2026-01-01T12:00:01Z"
    elif fault == "failed":
        bundle[0]["checks"][0]["status"] = "fail"
    else:
        (bundle[2] / "saved").write_bytes(b"tampered")
    assert validate(module, bundle)["status"] == "invalid"


def test_approved_policy_subject_ids_unique(module: Any, bundle: Any) -> None:
    """Policy subject collections follow the common ID rule."""
    subject = bundle[0]["evidence"][0]["subjects"][0]
    bundle[1]["approved_procedures"] = [subject, subject]
    assert validate(module, bundle)["status"] == "invalid"


def test_subject_extensions_are_inert(module: Any, bundle: Any) -> None:
    """Subject metadata does not change its ID/digest binding."""
    for item in bundle[0]["evidence"] + bundle[0]["checks"]:
        for subject in item["subjects"]:
            subject["extensions"] = {"metadata": "inert"}
    assert validate(module, bundle)["status"] == "valid"


def test_missing_source_identity(module: Any, bundle: Any) -> None:
    """An absent alternative source identity is a gap, not a bad value."""
    del bundle[0]["source"]["revision"]
    result = validate(module, bundle)
    assert result["status"] == "incomplete"
    assert "missing-field" in codes(result)


@pytest.mark.parametrize("operation", ["replace", "mutate", "symlink"])
def test_file_race_refused(module: Any, bundle: Any, monkeypatch: Any, operation: str) -> None:
    """Detect file identity or byte changes after opening the descriptor."""
    root = bundle[2]
    saved = root / "saved"
    inode = saved.stat().st_ino
    original_read = os.read
    fired = False

    def changing_read(descriptor: int, count: int) -> bytes:
        """Exercise changing read."""
        nonlocal fired
        content = original_read(descriptor, count)
        if not fired and os.fstat(descriptor).st_ino == inode:
            fired = True
            if operation == "replace":
                (root / "replacement").write_bytes(b"replacement")
                Path(root / "replacement").replace(saved)
            elif operation == "symlink":
                saved.unlink()
                saved.symlink_to(root / "proof")
            else:
                saved.write_bytes(b"changed-in-place")
        return content

    monkeypatch.setattr(os, "read", changing_read)
    assert "unsafe-path" in codes(validate(module, bundle))
    assert fired


def test_stream_budget_stops_at_first_excess_byte(
    module: Any, bundle: Any, monkeypatch: Any
) -> None:
    """Reach the separate evidence cap without allocating a large fixture."""
    root = bundle[2]
    original = os.read
    sizes = []

    def counted_read(descriptor: int, count: int) -> bytes:
        """Exercise counted read."""
        chunk = original(descriptor, count)
        sizes.append(len(chunk))
        return chunk

    monkeypatch.setattr(os, "read", counted_read)
    with pytest.raises(module.Refusal) as raised:
        module.hash_evidence(root, "saved", 3)
    assert raised.value.code == "evidence-too-large"
    assert sum(sizes) == 4


def test_manifest_bounded_read(module: Any, tmp_path: Path, monkeypatch: Any) -> None:
    """The reader stops at exactly one byte beyond the encoded budget."""
    (tmp_path / "large").write_bytes(b"x" * 1048578)
    original = os.read
    sizes = []

    def counted_read(descriptor: int, count: int) -> bytes:
        """Exercise counted read."""
        chunk = original(descriptor, count)
        sizes.append(len(chunk))
        return chunk

    monkeypatch.setattr(os, "read", counted_read)
    with pytest.raises(module.Refusal) as raised:
        module.read_manifest(tmp_path, "large")
    assert raised.value.code == "manifest-too-large"
    assert sum(sizes) == 1048577


@pytest.mark.parametrize(
    "raw",
    [
        b" " * 1048574 + b"{}",
        b"[" * 32 + b"]" * 32,
        json.dumps([0] * 1000).encode(),
        json.dumps("x" * 65536).encode(),
    ],
)
def test_exact_parser_limits_accepted(module: Any, raw: bytes) -> None:
    """Boundary values pass the reader before normative validation."""
    module.parse_json(raw)


@pytest.mark.parametrize(
    "path",
    [
        "source.repository",
        "target.environment",
        "target.account",
        "toolchain.engine",
        "toolchain.version",
        "toolchain.providers",
        "toolchain.lock",
        "toolchain.providers.0.source",
        "toolchain.providers.0.version",
        "state.backend",
        "state.workspace",
        "state.lineage",
        "state.serial",
        "plan.saved_plan",
        "plan.inspection",
        "freshness.policy_id",
        "freshness.max_age_seconds",
        "effects.changes",
        "effects.stateful_impacts",
        "effects.cost",
        "effects.changes.0.address",
        "effects.changes.0.actions",
        "evidence.0.id",
        "evidence.0.kind",
        "evidence.0.locator",
        "evidence.0.sha256",
        "evidence.0.media_type",
        "evidence.0.producer",
        "evidence.0.observed_at",
        "evidence.0.subjects",
        "evidence.0.subjects.0.id",
        "evidence.0.subjects.0.sha256",
        "checks.0.id",
        "checks.0.stage",
        "checks.0.status",
        "checks.0.subjects",
        "checks.0.evidence",
        "checks.0.subjects.0.id",
        "checks.0.subjects.0.sha256",
    ],
)
def test_missing_nested_field(module: Any, bundle: Any, path: str) -> None:
    """Missing nested facts remain gaps rather than invented bad bindings."""
    parts = [int(part) if part.isdecimal() else part for part in path.split(".")]
    record = bundle[0]
    for part in parts[:-1]:
        record = record[part]
    del record[parts[-1]]
    result = validate(module, bundle)
    assert result["status"] == "incomplete", result
    assert "missing-field" in codes(result)


def schema_parity(module: Any, schema: dict[str, Any]) -> list[str]:
    """Compare published structure with the validator's closed record tables."""
    differences: list[str] = []
    definitions = schema.get("$defs", {})
    for name, fields in module.RECORDS.items():
        record = definitions.get(name, {})
        required = {key for key in fields if not key.endswith("?")}
        properties = record.get("properties", {})
        if set(record.get("required", [])) != required:
            differences.append(name + ".required")
        if record.get("additionalProperties") is not False:
            differences.append(name + ".additionalProperties")
        if set(properties) != {key.rstrip("?") for key in fields} | {"extensions"}:
            differences.append(name + ".properties")
        for key, descriptor in fields.items():
            field = properties.get(key.rstrip("?"), {})
            if descriptor.endswith("[]"):
                field = field.get("items", {})
                descriptor = descriptor[:-2]
            if descriptor in module.ENUMS and field.get("enum") != list(module.ENUMS[descriptor]):
                differences.append(name + "." + key + ".enum")
            if descriptor == "version" and field.get("const") != "iac-plan-bundle.v1":
                differences.append(name + "." + key + ".const")
    return differences


def test_check_evidence_collectively_covers_subjects(module: Any, bundle: Any) -> None:
    """Several verified records can together cover a check's subjects."""
    data = bundle[0]
    lock = data["evidence"][4]
    lock_subject = {"id": "lock", "sha256": lock["sha256"]}
    lock["subjects"] = [lock_subject]
    data["checks"][0]["subjects"].append(lock_subject)
    data["checks"][0]["evidence"] = ["proof", "lock"]
    assert validate(module, bundle)["status"] == "valid"


def test_unused_external_evidence_is_reported_unverified(module: Any, bundle: Any) -> None:
    """An unused locator does not become a required check through metadata."""
    extra = copy.deepcopy(bundle[0]["evidence"][0])
    extra.update(id="optional", locator="https://example.test/optional")
    bundle[0]["evidence"].append(extra)
    result = validate(module, bundle)
    assert result["status"] == "valid"
    assert result["evidence"][-1] == {"id": "optional", "verification": "unverified"}


def test_missing_local_required_evidence_is_gap(module: Any, bundle: Any) -> None:
    """A required artifact that is absent is incomplete evidence."""
    (bundle[2] / "saved").unlink()
    result = validate(module, bundle)
    assert result["status"] == "incomplete"
    assert "missing-evidence" in codes(result)


def test_version_and_policy_cli_results(module: Any, bundle: Any, capsys: Any) -> None:
    """Distinguish unsupported versions, missing policy and unreadable policy."""
    data, policy, root = bundle
    (root / "bundle.json").write_text(json.dumps(data))
    args = ["validate", "bundle.json", "--root", str(root), "--now", NOW]
    assert module.main(args) == 1
    assert "policy-missing" in codes(json.loads(capsys.readouterr().out))
    assert module.main(args + ["--policy", "absent.json"]) == 2
    assert "unreadable-input" in codes(json.loads(capsys.readouterr().out))
    (root / "policy.json").write_text("{")
    assert module.main(args + ["--policy", "policy.json"]) == 1
    assert "malformed-input" in codes(json.loads(capsys.readouterr().out))
    (root / "policy.json").write_text(json.dumps(policy))
    data["schema_version"] = "other-version"
    (root / "bundle.json").write_text(json.dumps(data))
    assert module.main(args + ["--policy", "policy.json"]) == 2
    assert "unsupported-version" in codes(json.loads(capsys.readouterr().out))


def test_trusted_freshness_is_stricter(module: Any, bundle: Any) -> None:
    """A bundle cannot weaken its caller's maximum evidence age."""
    bundle[1]["max_age_seconds"] = 30
    bundle[0]["created_at"] = "2026-01-01T11:59:29Z"
    result = validate(module, bundle)
    assert result["status"] == "incomplete"
    assert "stale" in codes(result)


def test_relative_filename_colon_is_not_drive_path(module: Any, bundle: Any) -> None:
    """A colon within a relative path segment is not a Windows drive prefix."""
    root = bundle[2]
    (root / "artifacts").mkdir()
    (root / "saved").rename(root / "artifacts" / "plan:1")
    bundle[0]["evidence"][0]["locator"] = "artifacts/plan:1"
    assert validate(module, bundle)["status"] == "valid"


def test_nonpass_check_evidence_references_resolve(module: Any, bundle: Any) -> None:
    """All declared evidence references resolve, including non-pass checks."""
    check = copy.deepcopy(bundle[0]["checks"][0])
    check.update(id="optional-check", status="not-run", evidence=["missing"])
    bundle[0]["checks"].append(check)
    result = validate(module, bundle)
    assert result["status"] == "incomplete"
    assert "missing-evidence" in codes(result)


def test_ancestor_directory_activity_is_not_replacement(module: Any, tmp_path: Path) -> None:
    """Entries added beside the target do not make a confined read refuse."""
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "input.json").write_bytes(b'{"key": "value"}\n')
    with module.confined_file(tmp_path, "nested/input.json") as descriptor:
        (tmp_path / "sibling-dir").mkdir()
        (tmp_path / "nested" / "sibling.txt").write_bytes(b"x")
        assert module.os.read(descriptor, 64) == b'{"key": "value"}\n'


@pytest.mark.parametrize("sign", ["", "-"])
def test_overlong_integer_metadata_and_field(module: Any, bundle: Any, sign: str) -> None:
    """Accept exact numeric metadata but refuse it as a normative integer."""
    data, policy, root = bundle
    literal = sign + "9" * 70000
    data["extensions"] = {"number": "INTEGER"}
    raw = json.dumps(data).replace('"INTEGER"', literal).encode()
    value = module.parse_json(raw)["extensions"]["number"]
    assert type(value) not in (str, int) and value.text == literal
    assert module.validate_bytes(raw, root=root, policy=policy, now=NOW)["status"] == "valid"
    data.pop("extensions")
    data["state"]["serial"] = "INTEGER"
    raw = json.dumps(data).replace('"INTEGER"', literal).encode()
    result = module.validate_bytes(raw, root=root, policy=policy, now=NOW)
    assert result["status"] == "invalid"
    assert result["issues"] == [{"code": "malformed-type", "path": "$.state.serial"}]


@pytest.mark.parametrize("digits", [4300, 4301])
@pytest.mark.parametrize("sign", ["", "-"])
def test_integer_conversion_boundary(module: Any, digits: int, sign: str) -> None:
    """The sign does not count toward the fixed conversion threshold."""
    literal = sign + "9" * digits
    value = module.parse_json(('{"number":' + literal + '}').encode())["number"]
    if digits == 4300:
        assert type(value) is int and str(value) == literal
    else:
        assert type(value) not in (str, int) and value.text == literal


def test_json_linear_megabyte_integer(module: Any) -> None:
    """Full-budget integer decoding stays numeric and finishes promptly."""
    raw = b'{"number":' + b"9" * (1048576 - 11) + b"}"
    start = time.perf_counter()
    value = module.parse_json(raw)["number"]
    assert time.perf_counter() - start < 2
    assert value.text.encode() == raw[10:-1]

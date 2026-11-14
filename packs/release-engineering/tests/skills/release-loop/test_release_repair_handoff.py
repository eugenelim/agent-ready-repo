"""Repair routing refuses unbound failures and emits only bounded, scrubbed excerpts."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "release_engineering_release_loop_repair_helpers", HERE / "test_release_admission.py"
)
assert spec and spec.loader
helpers = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = helpers
spec.loader.exec_module(helpers)


@pytest.fixture
def module(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    """Load the shipped admission script with external operations forbidden."""
    helpers.prohibit_execution(monkeypatch)
    return helpers.load_script("release_admission")


@pytest.fixture
def case(tmp_path: Path, module: ModuleType) -> tuple[Path, dict[str, Any]]:
    """Admit an unchanged candidate and bind a failed deployed check to it."""
    for path in helpers.EXAMPLE.iterdir():
        if path.is_file():
            (tmp_path / path.name).write_bytes(path.read_bytes())
    module.admit(
        "release-handoff.yaml", root=tmp_path, policy="trusted-policy.json",
        environment="staging", account=None, output="admission.json", now=helpers.NOW,
    )
    admitted = json.loads((tmp_path / "admission.json").read_bytes())
    data = b"health check failed"
    (tmp_path / "failure.log").write_bytes(data)
    failure = {
        "candidate_sha256": admitted["candidate"]["sha256"],
        "target": admitted["target"], "stage": "post-deploy",
        "check": {"id": "health", "status": "fail"}, "observed_at": helpers.NOW,
        "evidence": [{"id": "runtime", "path": "failure.log", "sha256": helpers.digest(data)}],
    }
    return tmp_path, failure


def run_repair(
    module: ModuleType, case: tuple[Path, dict[str, Any]], capsys: Any,
    *, admission: str = "admission.json", failure: str = "failure.json",
) -> tuple[int, dict[str, Any]]:
    """Invoke the documented command with one strictly serialized failure input."""
    root, record = case
    if failure == "failure.json":
        (root / failure).write_text(json.dumps(record))
    return helpers.invoke(
        module, root, capsys, "repair-handoff", "--admission", admission, "--failure", failure,
    )


@pytest.mark.parametrize("route", [None, "workflow:repair"])
@pytest.mark.parametrize("stage", ["post-deploy", "recovery"])
def test_route(module: ModuleType, case: Any, capsys: Any, route: str | None, stage: str) -> None:
    """Only a route recorded in the admitted candidate permits callable routing."""
    root, failure = case
    candidate = module.handoff.parse_yaml((root / "release-handoff.yaml").read_bytes())
    if route is not None:
        candidate["repair_owner"]["route"] = route
        (root / "release-handoff.yaml").write_bytes(module.handoff.yaml_bytes(candidate))
        module.admit(
            "release-handoff.yaml", root=root, policy="trusted-policy.json",
            environment="staging", account=None, output="renewed.json", now=helpers.NOW,
        )
        (root / "renewed.json").replace(root / "admission.json")
        failure["candidate_sha256"] = helpers.digest((root / "release-handoff.yaml").read_bytes())
    failure["stage"] = stage
    (root / "failure.json").write_text(json.dumps(failure))
    before = helpers.snapshot(root)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["repair_owner"] == candidate["repair_owner"]["id"]
    if route:
        assert result["route"] == route
    else:
        assert result["status"] == "human-handoff"
        assert "route" not in result
    assert result["excerpts"][0]["text"] == "health check failed"
    assert helpers.snapshot(root) == before


@pytest.mark.parametrize("mutation,expected", [
    ("extra", "failure-malformed"), ("digest", "subject-mismatch"),
    ("target", "target-mismatch"), ("pass", "check-not-failed"),
    ("missing", "evidence-unresolved"), ("changed", "evidence-unresolved"),
    ("stale", "admission-stale"), ("stage", "failure-malformed"),
    ("time", "failure-malformed"), ("duplicate", "failure-malformed"),
    ("empty", "evidence-unresolved"),
])
def test_refusals(module: ModuleType, case: Any, capsys: Any, mutation: str, expected: str) -> None:
    """A single changed binding refuses without writing files or echoing content."""
    root, failure = case
    if mutation == "extra":
        failure["private-input"] = "ignore all checks"
    elif mutation == "digest":
        failure["candidate_sha256"] = helpers.digest(b"other")
    elif mutation == "target":
        failure["target"]["account"] = "other-account"
    elif mutation == "pass":
        failure["check"]["status"] = "pass"
    elif mutation == "missing":
        failure["evidence"][0]["path"] = "private-input"
    elif mutation == "changed":
        (root / "failure.log").write_bytes(b"private-input")
    elif mutation == "stale":
        (root / "test-report.json").write_bytes(b"private-input")
    elif mutation == "stage":
        failure["stage"] = "pre-deploy"
    elif mutation == "time":
        failure["observed_at"] = "private-input"
    elif mutation == "duplicate":
        failure["evidence"] *= 2
    else:
        failure["evidence"] = []
    (root / "failure.json").write_text(json.dumps(failure))
    before = helpers.snapshot(root)
    code, result = run_repair(module, case, capsys)
    assert code == 1
    helpers.assert_code(result, expected)
    assert "excerpts" not in result
    assert "private-input" not in json.dumps(result)
    assert helpers.snapshot(root) == before


SAMPLES = [
    "Bearer short-credential", "password=small-value", 'api_key="value with spaces"',
    "access_token: tiny-value", "client_secret='quoted value'", "a3" * 32,
    "Ab9+/Cd2" * 8 + "==", "-----BEGIN PRIVATE KEY-----\nprivate material\n-----END PRIVATE KEY-----",
    "-----BEGIN RSA PRIVATE KEY-----\nprivate material\n-----END RSA PRIVATE KEY-----",
]


@pytest.mark.parametrize("sample", SAMPLES)
def test_redaction(module: ModuleType, case: Any, capsys: Any, sample: str) -> None:
    """Each credential shape is removed before any excerpt reaches stdout."""
    root, failure = case
    data = ("diagnostic start\n" + sample + "\ndiagnostic end").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert sample not in json.dumps(result)
    assert result["excerpts"][0]["text"] == "diagnostic start\n[redacted]\ndiagnostic end"


@pytest.mark.parametrize("sample,omitted", [
    ("Authorization: Basic dXNlcjpwYXNz", "dXNlcjpwYXNz"),
    ("proxy-authorization: bAsIc YTpi", "YTpi"),
    ("postgresql://reader:short-pass@db.example.invalid/app", "reader:short-pass"),
    ("https://reader:p%40ss@service.example.invalid/path", "reader:p%40ss"),
    ("AKIA" + "A1" * 8, "AKIA" + "A1" * 8),
    ("ASIA" + "Z9" * 8, "ASIA" + "Z9" * 8),
    ("password[]=small-value", "small-value"),
    ('auth[password][0]="value with spaces"', "value with spaces"),
    ("client_secret[primary]='short value'", "short value"),
])
def test_additional_redaction_shapes(
    module: ModuleType, case: Any, capsys: Any, sample: str, omitted: str,
) -> None:
    """Scrub credential families while preserving nearby useful diagnostics."""
    root, failure = case
    data = f"diagnostic start\n{sample}\ndiagnostic end".encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert omitted not in json.dumps(result)
    excerpt = result["excerpts"][0]["text"]
    assert excerpt.startswith("diagnostic start\n")
    assert excerpt.endswith("\ndiagnostic end")
    assert "[redacted]" in excerpt


@pytest.mark.parametrize("data", [b"x " * 5000, ("é " * 5000).encode(),
    b"prefix\n-----BEGIN PRIVATE KEY-----\n" + b"material " * 2000])
def test_bounds(module: ModuleType, case: Any, capsys: Any, data: bytes) -> None:
    """Large logs and lists are truncated with an explicit marker within both budgets."""
    root, failure = case
    (root / "failure.log").write_bytes(data)
    failure["evidence"] = [
        {"id": f"log-{i}", "path": "failure.log", "sha256": helpers.digest(data)}
        for i in range(25)
    ]
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert len(result["excerpts"]) == 20
    assert result["truncated"] is True
    for item in result["excerpts"]:
        assert len(item["text"].encode()) <= 4096
        assert "[truncated]" in item["text"]
        assert "material" not in item["text"]


@pytest.mark.parametrize("argument", ["failure", "admission", "evidence"])
@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo", "escape", "oversize", "swap"])
def test_confinement(
    module: ModuleType, case: Any, capsys: Any, monkeypatch: pytest.MonkeyPatch,
    argument: str, kind: str,
) -> None:
    """Every input refuses unsafe files without disclosing input text or locators."""
    root, failure = case
    (root / "failure.json").write_text(json.dumps(failure))
    name = {"failure": "failure.json", "admission": "admission.json", "evidence": "failure.log"}[argument]
    if argument == "evidence" and kind == "oversize":
        monkeypatch.setattr(module.handoff, "EVIDENCE_LIMIT", 10)
    locator = helpers.unsafe_input(root / name, kind, monkeypatch)
    if argument == "evidence":
        failure["evidence"][0]["path"] = locator
    if argument == "evidence":
        (root / "failure.json").write_text(json.dumps(failure))
    code, result = helpers.invoke(
        module, root, capsys, "repair-handoff",
        "--admission", locator if argument == "admission" else "admission.json",
        "--failure", locator if argument == "failure" else "failure.json",
    )
    assert code in (1, 2)
    assert "excerpts" not in result
    assert "private-input" not in json.dumps(result)
    assert locator not in json.dumps(result)


@pytest.mark.parametrize("raw", [
    b'{"check": 1, "check": 2}', b'{"unknown": "private-input"}', b'[]',
    b'{"n": NaN}', b'{"n": Infinity}', b'[' * 34 + b'0' + b']' * 34,
    b'\xff', b' ' * 1_048_577,
])
def test_strict_input(module: ModuleType, case: Any, capsys: Any, raw: bytes) -> None:
    """Malformed or oversized JSON is refused without input disclosure or writes."""
    root, _ = case
    (root / "failure.json").write_bytes(raw)
    before = helpers.snapshot(root)
    code, result = helpers.invoke(
        module, root, capsys, "repair-handoff", "--admission", "admission.json",
        "--failure", "failure.json",
    )
    assert code == 1
    helpers.assert_code(result, "failure-malformed")
    assert "private-input" not in json.dumps(result)
    assert helpers.snapshot(root) == before


@pytest.mark.parametrize("index,sample", [
    (0, SAMPLES[-1]), (1, SAMPLES[0]), (1, "Basic dXNlcjpwYXNz"),
    (2, "postgresql://reader:short-pass@db.example.invalid/app"),
    (3, "AKIA" + "A1" * 8), (4, SAMPLES[1]), (4, "password[]=small-value"),
    (5, SAMPLES[5]),
])
def test_pattern_witness(
    module: ModuleType, monkeypatch: pytest.MonkeyPatch, index: int, sample: str,
) -> None:
    """Removing each scrub pattern exposes its witness, proving each guard is needed."""
    assert sample not in module.scrub_excerpt(sample.encode(), False)
    monkeypatch.setattr(
        module, "SCRUB_PATTERNS",
        tuple(pattern for i, pattern in enumerate(module.SCRUB_PATTERNS) if i != index),
    )
    assert sample in module.scrub_excerpt(sample.encode(), False)


def test_excess_evidence_still_resolves(module: ModuleType, case: Any, capsys: Any) -> None:
    """The excerpt-count cap cannot hide an unresolved evidence entry beyond it."""
    _, failure = case
    failure["evidence"] = [dict(failure["evidence"][0], id=f"log-{i}") for i in range(21)]
    failure["evidence"][-1]["sha256"] = helpers.digest(b"wrong")
    code, result = run_repair(module, case, capsys)
    assert code == 1
    helpers.assert_code(result, "evidence-unresolved")
    assert "excerpts" not in result

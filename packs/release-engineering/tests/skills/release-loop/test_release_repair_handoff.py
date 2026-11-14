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


def credential_corpus() -> list[tuple[str, tuple[str, ...]]]:
    """Generate header, escaped-string and compact-credential disclosure probes."""
    rows: list[tuple[str, tuple[str, ...]]] = []
    for header in ("Cookie", "Set-Cookie", "Authorization", "Proxy-Authorization"):
        for name in (header, header.lower(), header.upper()):
            value = "session=header-fragment; mode=second-fragment"
            rows.append((f"{name}: {value}", ("header-fragment", "second-fragment")))
    for key in ("password", "passwd", "pwd", "client_secret", "access_token",
                "api_key", "credential", "auth[password][0]"):
        for value in ('first"escaped-fragment', 'first\\"escaped-fragment',
                      'first\\\\"escaped-fragment'):
            rows.append((json.dumps({key: value}), ("escaped-fragment",)))
    for width in (0, 1, 7):
        for signature in ("", "a", "a-_9"):
            value = "eyJ" + "a" * width + ".eyJ" + "b" * width + "." + signature
            rows.append((value, (value,)))
    return rows


@pytest.mark.parametrize("surrounding", [
    "diagnostic start\n{}\ndiagnostic end",
    '{{\n"before": "diagnostic start",\n{}\n,"after": "diagnostic end"\n}}',
    "before=diagnostic start&\n{}\n&after=diagnostic end",
    "export BEFORE='diagnostic start'\n{}\nexport AFTER='diagnostic end'",
    "before: diagnostic start\n  {}\nafter: diagnostic end",
], ids=["plain", "json", "query", "shell", "yaml"])
@pytest.mark.parametrize("sample,omitted", credential_corpus())
def test_structural_redaction_corpus(
    module: ModuleType, case: Any, capsys: Any, surrounding: str,
    sample: str, omitted: tuple[str, ...],
) -> None:
    """Every credential shape is scrubbed in varied diagnostic surroundings."""
    root, failure = case
    data = surrounding.format(sample).encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    excerpt = result["excerpts"][0]["text"]
    assert all(value not in excerpt for value in omitted), excerpt
    assert "[redacted]" in excerpt
    assert "diagnostic start" in excerpt and "diagnostic end" in excerpt


@pytest.mark.parametrize("sample,closed", [
    ('"credentials": {\n"value": "first-fragment"\n}', True),
    ('"credentials": [\n"first-fragment"\n]', True),
    ('"credentials": {"value":\n"first-fragment"\n}', True),
    ('"credentials": [{"value":\n"first-fragment"},\n{"value": "second-fragment"}]', True),
    ('"credentials": {\n"nested": [{\n"value": "first-fragment"\n}]\n}', True),
    ('"credentials": {\n"value": "} ] { [",\n"next": "first-fragment"\n}', True),
    ('"credentials": {\n"value": ' + json.dumps('escaped " } \\ [')
     + ',\n"next": "first-fragment"\n}', True),
    ('{"credentials": {\n"value": "first-fragment"\n}}', True),
    ('"credentials": {\n"value": "first-fragment"', False),
    ('"credentials": [\n"first-fragment"', False),
    ('"credentials": {\n"value": "first-fragment"\n]\n"second-fragment"\n}', False),
    ('"credentials": {\n"value": "first-fragment",\n}\nsecond-fragment', False),
    ('"credentials": {\n"value": "unterminated }\nsecond-fragment', False),
], ids=["object", "array", "inline-start", "array-of-objects", "nested",
        "quoted-brackets", "escaped-quote-and-backslash", "outer-object",
        "unclosed-object", "unclosed-array", "mismatched-close", "malformed", "unclosed-string"])
def test_nested_json_values(
    module: ModuleType, case: Any, capsys: Any, sample: str, closed: bool,
) -> None:
    """Drop complete credential containers and fail closed on broken structures."""
    root, failure = case
    data = ("diagnostic start\n" + sample + "\ndiagnostic end").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    ending = "\ndiagnostic end" if closed else ""
    assert result["excerpts"][0]["text"] == "diagnostic start\n[redacted]" + ending


def fail_closed_corpus() -> list[str]:
    """Generate credential lines and continuation blocks across supported formats."""
    rows: list[str] = []
    for key in ("password", "passwd", "client_secret", "access_token", "api_key",
                "credential", "Authorization", "Cookie", "Proxy-Authorization",
                "bearer", "private_key", "session", "signature"):
        for spelling in (key, key.upper(), key.replace("_", "-")):
            for encoded in (spelling, "".join(f"\\u{ord(char):04x}" for char in spelling)):
                rows.append('{"' + encoded + '":"first-fragment; second-fragment"}')
    for option in ("-u", "-u ", "--user ", "--user="):
        rows.append(f"curl {option}reader:pw https://example.invalid/health")
    for key in ("password", "client_secret"):
        for indent in ("", "  "):
            for scalar in ("|", ">", "|-", ">+", "|2", ">2-"):
                rows.append(f"{indent}{key}: {scalar} # diagnostic\n"
                            f"{indent}  first-fragment\n\n{indent}  second-fragment")
        for delimiter in ('"""', "'" * 3):
            rows.append(f"{key} = {delimiter}first-fragment\n"
                        f"second-fragment\n{delimiter}")
            rows.append(f"{key} = {delimiter}first-fragment\nsecond-fragment")
        rows.append(f'{key} = """first-fragment\n'
                    'escaped \\""" middle-fragment\nsecond-fragment\n"""')
        for length in (1, 3):
            rows.append(f"{key}=first-fragment " + "\\" + "\n"
                        + ("middle-fragment " + "\\" + "\n") * length
                        + "second-fragment")
    return rows


@pytest.mark.parametrize("sample", fail_closed_corpus())
def test_fail_closed_lines(
    module: ModuleType, case: Any, capsys: Any, sample: str,
) -> None:
    """The real command suppresses whole credential lines and all their continuations."""
    root, failure = case
    # An unclosed multiline string consumes the remaining excerpt conservatively.
    unclosed = sample.count('"""') == 1 or sample.count("'" * 3) == 1
    ending = "" if unclosed else "\ndiagnostic end"
    data = ("diagnostic start\n" + sample + ending).encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "diagnostic start\n[redacted]" + ending


@pytest.mark.parametrize("sample", [
    "status: healthy\n  detail: ready",
    'message = """first\nsecond\n"""',
    "curl --user-agent diagnostic https://example.invalid/health",
])
def test_benign_lines_survive(module: ModuleType, sample: str) -> None:
    """Ordinary diagnostics retain their exact text when neither scrub layer applies."""
    assert module.scrub_excerpt(sample.encode(), False) == sample


@pytest.mark.parametrize("key", [
    "passphrase", "pwd", "passwd", "apikey", "x-api-key", "auth", "credentials",
    "pass%77ord", "%70%61%73%73%77%6f%72%64",
])
@pytest.mark.parametrize("form", ["{}=short-fragment", '{}: short-fragment'])
def test_additional_credential_keys(
    module: ModuleType, case: Any, capsys: Any, key: str, form: str,
) -> None:
    """Common names and percent-encoded keys suppress the entire diagnostic line."""
    root, failure = case
    data = ("diagnostic start\nline prefix " + form.format(key) + " line suffix\n"
            "diagnostic end").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "diagnostic start\n[redacted]\ndiagnostic end"


@pytest.mark.parametrize("ending", ["\n", "\r\n", "\u2028", "\x85"])
@pytest.mark.parametrize("opening", ["password:", "password: # value follows",
                                      "password: |", "password: >"])
def test_following_line_values(
    module: ModuleType, case: Any, capsys: Any, ending: str, opening: str,
) -> None:
    """Bare keys and YAML scalars hide indented values across supported line endings."""
    root, failure = case
    data = ending.join([
        "diagnostic start", opening, "  first-fragment", "  second-fragment", "diagnostic end",
    ]).encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == ending.join([
        "diagnostic start", "[redacted]", "diagnostic end",
    ])


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
    (0, "Cookie: session=header-fragment"),
    (1, SAMPLES[-1]), (2, SAMPLES[0]), (2, "Basic dXNlcjpwYXNz"),
    (3, "postgresql://reader:short-pass@db.example.invalid/app"),
    (4, "AKIA" + "A1" * 8), (5, "eyJ.eyJ."),
    (6, SAMPLES[1]), (6, "password[]=small-value"), (7, SAMPLES[5]),
])
def test_pattern_witness(
    module: ModuleType, monkeypatch: pytest.MonkeyPatch, index: int, sample: str,
) -> None:
    """Each fallback pattern independently protects lines without name classification."""
    monkeypatch.setattr(module, "CREDENTIAL_WORDS", ())
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

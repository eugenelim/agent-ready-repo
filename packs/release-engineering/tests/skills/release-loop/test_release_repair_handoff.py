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


@pytest.mark.parametrize("route", [
    None, "workflow:repair", "https://reader:demo-abc123@example.invalid/repair",
    "https://example.invalid/repair?password=demo-abc123",
    "https://example.invalid/repair?access_token=demo-abc123",
    "https://example.invalid/repair?pass%77ord=demo-abc123",
])
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
        expected = "[redacted]" if "demo-abc123" in route else route
        assert result["route"] == expected
        assert "demo-abc123" not in json.dumps(result)
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
    "shared: &a healthy\ncopy: *a",
    'message: "first\nsecond\n"',
    "message: first\n  second",
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


def following_value_corpus() -> list[tuple[str, str]]:
    """Cross bare-key spellings, value structures, indentation and line endings."""
    rows: list[tuple[str, str]] = []
    for key in ("credentials", "credentials:", '"credentials":', "credentials =",
                "pass%77ord:", r'"pass\u0077ord":', "credentials: # value follows",
                '{"credentials":', "'credentials':"):
        for key_indent in ("", "  "):
            for value_indent in ("", "  ", "    "):
                for ending in ("\n", "\r\n", "\u2028", "\x85"):
                    for value in (
                        ["demo-abc123"],
                        ["- demo-abc123", "  detail: second-fragment", "- third-fragment"],
                        ["detail: demo-abc123", "  child: second-fragment"],
                        ["-", "  detail: demo-abc123", "-", "  detail: second-fragment"],
                        ['{', '"nested": [{"value": "demo-abc123"},',
                         '{"value": "second-fragment", "braces": "} ["}]', '}'],
                        ['[', '{"value": "demo-abc123"},', '"second-fragment"', ']'],
                        ['{', '"value": "demo-abc123"'],
                        ['[', '"demo-abc123"', '}'],
                    ):
                        closed = not (
                            value[0] == "{" and value[-1] != "}"
                            or value[0] == "[" and value[-1] != "]"
                        )
                        sample = ending.join([
                            "before: diagnostic start", key_indent + key, "", "   ",
                            *(value_indent + line for line in value),
                            "after: diagnostic end", "detail: healthy",
                        ])
                        expected = ending.join(["before: diagnostic start", "[redacted]"])
                        if closed:
                            expected += ending + ending.join([
                                "after: diagnostic end", "detail: healthy",
                            ])
                        rows.append((sample, expected))
    return rows


@pytest.mark.parametrize("sample,expected", following_value_corpus())
def test_following_value_layouts(module: ModuleType, sample: str, expected: str) -> None:
    """Bare keys consume their next value and its full structure in every layout."""
    assert module.scrub_excerpt(sample.encode(), False) == expected


@pytest.mark.parametrize("properties", [
    "&db_password", "!!str", "!tag", "*db_password", "!<tag:example.invalid,2026:str>",
    "&db_password !!str", "!tag &db_password", "*db_password !tag",
])
@pytest.mark.parametrize("value", [
    "|\n  demo-abc123\n  second-fragment",
    ">-\n  demo-abc123\n  second-fragment",
    "|2+ # diagnostic\n  demo-abc123\n  second-fragment",
    "\n- demo-abc123\n  detail: second-fragment\n- third-fragment",
    '\n{\n"value": "demo-abc123",\n"nested": ["second-fragment"]\n}',
    '[\n{"value": "demo-abc123"},\n"second-fragment"\n]',
    '{\n"value": "demo-abc123"',
])
def test_yaml_properties_continue_redaction(
    module: ModuleType, properties: str, value: str,
) -> None:
    """YAML node properties cannot hide a credential value's continuation."""
    sample = f"before: healthy\npassword: {properties} {value}\nafter: healthy"
    expected = "before: healthy\n[redacted]"
    if value != '{\n"value": "demo-abc123"':
        expected += "\nafter: healthy"
    assert module.scrub_excerpt(sample.encode(), False) == expected


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


YAML_VALUE_CASES = [
    "password: |\n# explanation\n\n  meadow-finch\n  second-fragment",
    "password: >\n# explanation\n\n  meadow-finch\n  second-fragment",
    "password:\n# explanation\n\n  meadow-finch",
    "password:\n\n# explanation\n- meadow-finch\n- second-fragment",
    "shared: &a meadow-finch\npassword:\n# explanation\n\n  *a\ncopy: *a",
    "shared: &a |\n  meadow-finch\n  second-fragment\npassword:\n# explanation\n\n  *a\ncopy: *a",
    'passphrase: "\n  meadow-finch\n  "',
    "passphrase: '\n  meadow-finch\n  '",
    'passphrase: "first-fragment\n  meadow-finch\\\" detail\n  last-fragment"',
    "passphrase: 'first-fragment\n  meadow-finch'' detail\n  last-fragment'",
    "passphrase: meadow-finch\n  second-fragment\n\n  last-fragment",
    "? password\n: meadow-finch\n  second-fragment",
    '? password\n: "\n  meadow-finch\n  "',
    "? password\n: |\n  meadow-finch\n  second-fragment",
    "shared: &login meadow-finch\npassword: *login\ncopy: *login",
    "shared: &a meadow-finch\npassword:\n  *a",
    "shared: &a meadow-finch\n? password\n: *a",
    "shared: &a |\n  meadow-finch\n  second-fragment\npassword: *a\ncopy: *a",
    'shared: &a "\n  meadow-finch\n  "\npassword: *a',
    "shared: &a '\n  meadow-finch\n  '\npassword: *a",
    "shared: &a meadow-finch\n  second-fragment\npassword: *a",
    "shared: &a meadow-finch\nindirect: &b *a\npassword: *b\ncopy: *a",
    "password: *a\nshared: &a |\n  meadow-finch\n  second-fragment",
]


@pytest.mark.parametrize("sample", YAML_VALUE_CASES)
@pytest.mark.parametrize("location", ["excerpt", "route"])
def test_yaml_scalar_and_alias_handoff(
    module: ModuleType, case: Any, capsys: Any, sample: str, location: str,
) -> None:
    """The real handoff removes complete YAML values from logs and routes."""
    root, failure = case
    data = f"before: healthy\n{sample}\nafter: healthy"
    if location == "route":
        candidate = module.handoff.parse_yaml((root / "release-handoff.yaml").read_bytes())
        candidate["repair_owner"]["route"] = data
        (root / "release-handoff.yaml").write_bytes(module.handoff.yaml_bytes(candidate))
        module.admit(
            "release-handoff.yaml", root=root, policy="trusted-policy.json",
            environment="staging", account=None, output="renewed.json", now=helpers.NOW,
        )
        (root / "renewed.json").replace(root / "admission.json")
        failure["candidate_sha256"] = helpers.digest((root / "release-handoff.yaml").read_bytes())
    else:
        (root / "failure.log").write_bytes(data.encode())
        failure["evidence"][0]["sha256"] = helpers.digest(data.encode())
    code, result = run_repair(module, case, capsys)
    assert code == 0
    rendered = json.dumps(result)
    for value in ("meadow-finch", "second-fragment", "last-fragment"):
        assert value not in rendered
    output = result["route"] if location == "route" else result["excerpts"][0]["text"]
    assert output == "before: healthy\n[redacted]\nafter: healthy"


@pytest.mark.parametrize("value", [
    "|-\n  meadow-finch\n  second-fragment",
    ">2+\n  meadow-finch\n  second-fragment",
    '"meadow-finch\n  second-fragment"',
    "'meadow-finch\n  second-fragment'",
    "meadow-finch\n  second-fragment",
    "meadow-finch",
])
@pytest.mark.parametrize("indent", ["", "  "])
@pytest.mark.parametrize("properties", ["&a", "!tag &a"])
@pytest.mark.parametrize("comment", ["", "# explanation\n\n"])
def test_yaml_sequence_alias_handoff(
    module: ModuleType, case: Any, capsys: Any,
    value: str, indent: str, properties: str, comment: str,
) -> None:
    """Aliased sequence values lose their full scalar and preserve safe siblings."""
    root, failure = case
    item = f"- {properties} {value}"
    rows = "\n".join(indent + line for line in item.splitlines())
    data = (
        f"before: healthy\nitems:\n{rows}\n{indent}- healthy\n"
        f"password:\n{comment}  *a\ncopy: *a\nafter: healthy"
    ).encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    rendered = json.dumps(result)
    assert "meadow-finch" not in rendered
    assert "second-fragment" not in rendered
    assert result["excerpts"][0]["text"] == (
        f"before: healthy\nitems:\n[redacted]\n{indent}- healthy\n"
        "[redacted]\nafter: healthy"
    )


@pytest.mark.parametrize("padding", [800, 6000])
def test_yaml_alias_after_excerpt_lookahead(
    module: ModuleType, case: Any, capsys: Any, padding: int,
) -> None:
    """Aliases beyond the old prefix and read chunk still redact early anchors."""
    root, failure = case
    middle = "".join(f"entry-{index}: healthy\n" for index in range(padding))
    data = (f"shared: &a meadow-finch\n{middle}password: *a\n").encode()
    assert data.index(b"password") > 8192
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert "meadow-finch" not in json.dumps(result)
    excerpt = result["excerpts"][0]["text"]
    expected = ("[redacted]\n" + middle).encode()[:4096 - len(b"\n[truncated]")]
    assert excerpt == expected.decode() + "\n[truncated]"
    assert len(excerpt.encode()) <= 4096


def test_best_effort_contract(module: ModuleType, case: Any, capsys: Any) -> None:
    """The handoff and portable procedure declare the human review boundary."""
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["redaction"] == "best-effort"
    procedure = (helpers.EXAMPLE.parents[1] / "SKILL.md").read_text(encoding="utf-8")
    assert "reviewed by a human before it leaves the team" in " ".join(procedure.split())


@pytest.mark.parametrize("command,option", [
    ("curl", "-u reader:meadow-finch"),
    ("curl", "--user reader:meadow-finch"),
    ("curl", "--header 'Authorization: meadow-finch'"),
    ("wget", "--user reader:meadow-finch"),
    ("http", "--auth reader:meadow-finch"),
])
@pytest.mark.parametrize("continued", [False, True])
def test_transfer_authentication_options(
    module: ModuleType, case: Any, capsys: Any, command: str, option: str, continued: bool,
) -> None:
    """Handoffs drop authentication on direct and continued transfer commands."""
    separator = " " + chr(92) + "\n  " if continued else " "
    sample = separator.join((command, option, "https://example.invalid"))
    data = ("before: healthy\n" + sample + "\nafter: healthy").encode()
    root, failure = case
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    rendered = result["excerpts"][0]["text"]
    assert "meadow-finch" not in rendered
    assert "before: healthy\n" in rendered
    assert rendered.endswith("after: healthy")


@pytest.mark.parametrize("option", [
    "-u reader:shortElevenValue", "--user reader:shortElevenValue",
    "-u shortElevenValue", "--user shortElevenValue",
    "-ureader:shortElevenValue", "--user=reader:shortElevenValue",
    '-u "shortElevenValue"', "--user='shortElevenValue'",
    '"-u", "shortElevenValue"', '"--user", "shortElevenValue"',
])
@pytest.mark.parametrize("layout", [
    "{}", "diagnostic {}", "diagnostic |{}", "arguments: ({})",
    "download completed\n{}",
])
def test_user_options_without_command_context(
    module: ModuleType, case: Any, capsys: Any, option: str, layout: str,
) -> None:
    """The real handoff removes option values without requiring a command name."""
    root, failure = case
    sample = layout.format(option)
    data = ("before: healthy\n" + sample + "\nafter: healthy").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    rendered = result["excerpts"][0]["text"]
    assert "shortElevenValue" not in json.dumps(result)
    assert "[redacted]" in rendered
    assert rendered.startswith("before: healthy\n")
    assert rendered.endswith("after: healthy")
    for benign in ("tool -u", "tool -u --verbose", "tool -u | next",
                   'arguments: ["-u", "--verbose"]'):
        assert module.scrub_excerpt(benign.encode(), False) == benign


@pytest.mark.parametrize("sample", [
    "curl -u", "curl -u --verbose", "wget --user", "wget --user --verbose",
])
def test_transfer_options_without_values_survive(module: ModuleType, sample: str) -> None:
    """A command name does not turn a plain option flag into a credential."""
    assert module.scrub_excerpt(sample.encode(), False) == sample


@pytest.mark.parametrize("command", ["curl ", "wget ", "http ", ""])
@pytest.mark.parametrize("option", ["-u", "--user"])
@pytest.mark.parametrize("continuation", ["", " " + chr(92)])
@pytest.mark.parametrize("ending", ["\n", "\r\n"])
@pytest.mark.parametrize("argument", ["guest:saffron-713", "saffron-713"])
def test_user_option_next_line_value(
    module: ModuleType, case: Any, capsys: Any, command: str, option: str,
    continuation: str, ending: str, argument: str,
) -> None:
    """A handoff removes the next-line value of a trailing authentication option."""
    root, failure = case
    data = ending.join((
        "before: healthy", command + option + continuation,
        f"  {argument} https://example.invalid", "after: healthy",
    )).encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert "saffron-713" not in json.dumps(result)
    rendered = result["excerpts"][0]["text"]
    assert "[redacted]" in rendered
    assert rendered.startswith("before: healthy" + ending)
    assert rendered.endswith("after: healthy")


@pytest.mark.parametrize("command", ["curl ", "wget ", "http ", ""])
@pytest.mark.parametrize("option", ["-u", "--user"])
@pytest.mark.parametrize("continuation", ["", " " + chr(92)])
@pytest.mark.parametrize("ending", ["\n", "\r\n"])
def test_user_option_next_line_option_survives(
    module: ModuleType, command: str, option: str, continuation: str, ending: str,
) -> None:
    """An option on the next line is not consumed as an authentication value."""
    data = ending.join((
        command + option + continuation, "  --verbose https://example.invalid", "healthy",
    ))
    assert module.scrub_excerpt(data.encode(), False) == data


@pytest.mark.parametrize("sample", [
    "shared: &inner meadow-finch\nouter: &outer\n  field: *inner\npassword: *outer",
    "shared:\n  &a |\n    meadow-finch\n    second-fragment\npassword: *a",
    "shared:\n  !tag &a |\n    meadow-finch\npassword: *a",
    "--user=\nreader:meadow-finch",
    "--user= \\\nreader:meadow-finch",
    "ewoiYWxnIjoibm9uZSIKfQ",
    "ewoiYWxnIjoibm9uZSIKfQ.e30",
    "ewoiYWxnIjoibm9uZSIKfQ.e30.",
    "ewoiYWxnIjoibm9uZSIKfQ.e30.c2lnbmF0dXJl",
])
def test_additional_redaction_layouts(
    module: ModuleType, case: Any, capsys: Any, sample: str,
) -> None:
    """The handoff removes transitive YAML values, continued options and JSON JWTs."""
    root, failure = case
    data = ("before: healthy\n" + sample + "\nafter: healthy").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    output = result["excerpts"][0]["text"]
    assert "meadow-finch" not in output
    assert "second-fragment" not in output
    assert "ewoiYWxnIjoibm9uZSIKfQ" not in output
    assert "c2lnbmF0dXJl" not in output
    assert "before: healthy" in output and "after: healthy" in output

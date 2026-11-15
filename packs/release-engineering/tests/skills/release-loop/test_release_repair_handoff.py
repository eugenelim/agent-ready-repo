"""Repair routing refuses unbound failures and emits only bounded, scrubbed excerpts."""

from __future__ import annotations

import importlib.util
import json
import subprocess
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
    None, "workflow:repair", "https://example.invalid/repair",
    "mailto:repair@example.invalid", "chat-hook:repair-room",
    "https://example.invalid/hooks/repair?channel=operations",
    "https://reader:demo-abc123@example.invalid/repair",
    "https://reader@example.invalid/repair",
    "https://example.invalid/repair?password=demo-abc123",
    "https://example.invalid/repair?access_token=demo-abc123",
    "https://example.invalid/repair?pass%77ord=demo-abc123",
    "workflow:repair?key=value", "workflow:repair#sig=value", "#sig=value",
    "workflow:repair?client_secret=value", "workflow:repair?access_key=value",
    "workflow:repair?", "workflow:repair#", "workflow:repair%253Fbranch=main",
    "https://example.invalid/repair?next=https://reader:value@other.invalid/path",
    "https://example.invalid/https://other.invalid/repair",
    "workflow:https://other.invalid/repair",
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
        unusable = route not in {
            "workflow:repair", "https://example.invalid/repair", "chat-hook:repair-room",
        }
        expected = "[redacted]" if unusable else route
        assert result["status"] == ("human-handoff" if unusable else "handoff")
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
    assert result["excerpts"][0]["text"] == (
        "diagnostic start\n[redacted]\ndiagnostic end"
        if sample in SAMPLES[5:7] else "[redacted]"
    )


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
    """Withhold named credentials and scrub standalone value shapes."""
    root, failure = case
    data = f"diagnostic start\n{sample}\ndiagnostic end".encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert omitted not in json.dumps(result)
    excerpt = result["excerpts"][0]["text"]
    if sample.startswith(("AKIA", "ASIA")):
        assert excerpt == "diagnostic start\n[redacted]\ndiagnostic end"
    else:
        assert excerpt == "[redacted]"


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
    if not sample.startswith("eyJ"):
        assert excerpt == "[redacted]"
    else:
        assert "diagnostic start" in excerpt and "diagnostic end" in excerpt


@pytest.mark.parametrize("sample", [
    ('"credentials": {\n"value": "first-fragment"\n}'),
    ('"credentials": [\n"first-fragment"\n]'),
    ('"credentials": {"value":\n"first-fragment"\n}'),
    ('"credentials": [{"value":\n"first-fragment"},\n{"value": "second-fragment"}]'),
    ('"credentials": {\n"nested": [{\n"value": "first-fragment"\n}]\n}'),
    ('"credentials": {\n"value": "} ] { [",\n"next": "first-fragment"\n}'),
    ('"credentials": {\n"value": ' + json.dumps('escaped " } \\ [')
     + ',\n"next": "first-fragment"\n}'),
    ('{"credentials": {\n"value": "first-fragment"\n}}'),
    ('"credentials": {\n"value": "first-fragment"'),
    ('"credentials": [\n"first-fragment"'),
    ('"credentials": {\n"value": "first-fragment"\n]\n"second-fragment"\n}'),
    ('"credentials": {\n"value": "first-fragment",\n}\nsecond-fragment'),
    ('"credentials": {\n"value": "unterminated }\nsecond-fragment'),
], ids=["object", "array", "inline-start", "array-of-objects", "nested",
        "quoted-brackets", "escaped-quote-and-backslash", "outer-object",
        "unclosed-object", "unclosed-array", "mismatched-close", "malformed", "unclosed-string"])
def test_nested_json_values(
    module: ModuleType, case: Any, capsys: Any, sample: str,
) -> None:
    """Drop complete credential containers and fail closed on broken structures."""
    root, failure = case
    data = ("diagnostic start\n" + sample + "\ndiagnostic end").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"


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
    """All supported credential layouts withhold the whole document."""
    root, failure = case
    # Include incomplete strings as well as closed multi-line forms.
    unclosed = sample.count('"""') == 1 or sample.count("'" * 3) == 1
    ending = "" if unclosed else "\ndiagnostic end"
    data = ("diagnostic start\n" + sample + ending).encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"


@pytest.mark.parametrize("sample", [
    "status: healthy\n  detail: ready",
    'message = """first\nsecond\n"""',
    "--user-agent diagnostic example.invalid/health",
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
    """Common names and percent-encoded keys withhold the document."""
    root, failure = case
    data = ("diagnostic start\nline prefix " + form.format(key) + " line suffix\n"
            "diagnostic end").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"


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
    assert result["excerpts"][0]["text"] == "[redacted]"


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
                        sample = ending.join([
                            "before: diagnostic start", key_indent + key, "", "   ",
                            *(value_indent + line for line in value),
                            "after: diagnostic end", "detail: healthy",
                        ])
                        expected = "[redacted]"
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
    assert module.scrub_excerpt(sample.encode(), False) == "[redacted]"


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
        if b"PRIVATE KEY" in data:
            assert item["text"] == "[redacted]"
        else:
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


@pytest.mark.parametrize("sample", [
    "AKIA" + "A1" * 8, "ASIA" + "A1" * 8, "eyJ.eyJ.", SAMPLES[5],
])
def test_value_shapes_without_credential_words(module: ModuleType, sample: str) -> None:
    """Recognised standalone values are scrubbed while benign context remains."""
    data = f"before: healthy\n{sample}\nafter: healthy"
    assert module.scrub_excerpt(data.encode(), False) == "before: healthy\n[redacted]\nafter: healthy"


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
    assert output == "[redacted]"


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
    """Sequence anchors beside credential lines suppress the whole excerpt."""
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
    assert result["excerpts"][0]["text"] == "[redacted]"


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
    assert excerpt == "[redacted]"
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
    assert rendered == "[redacted]"


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
    assert rendered == "[redacted]"
    for flag_only in ("tool -u", "tool -u --verbose", "tool -u | next",
                   'arguments: ["-u", "--verbose"]'):
        assert module.scrub_excerpt(flag_only.encode(), False) == "[redacted]"


@pytest.mark.parametrize("sample", [
    "curl -u", "curl -u --verbose", "wget --user", "wget --user --verbose",
])
def test_transfer_options_without_values_withheld(module: ModuleType, sample: str) -> None:
    """Credential flags withhold a document even when their value is absent."""
    assert module.scrub_excerpt(sample.encode(), False) == "[redacted]"


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
    assert rendered == "[redacted]"


@pytest.mark.parametrize("command", ["curl ", "wget ", "http ", ""])
@pytest.mark.parametrize("option", ["-u", "--user"])
@pytest.mark.parametrize("continuation", ["", " " + chr(92)])
@pytest.mark.parametrize("ending", ["\n", "\r\n"])
def test_user_option_next_line_option_withheld(
    module: ModuleType, command: str, option: str, continuation: str, ending: str,
) -> None:
    """A following option does not weaken the whole-document decision."""
    data = ending.join((
        command + option + continuation, "  --verbose https://example.invalid", "healthy",
    ))
    assert module.scrub_excerpt(data.encode(), False) == "[redacted]"


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
    if not sample.startswith("ewo") or "." in sample:
        assert output == "[redacted]"
    else:
        assert "before: healthy" in output and "after: healthy" in output


@pytest.mark.parametrize("command,expected", [
    ("verify", "record-malformed"),
    ("check-review", "admission-stale"),
    ("check-stage", "reassessment-required"),
    ("repair-handoff", "admission-stale"),
])
@pytest.mark.parametrize("binding", ["target", "subject", "owner"])
def test_commands_refuse_admission_swap_after_verification(
    module: ModuleType, case: Any, capsys: Any,
    monkeypatch: pytest.MonkeyPatch, command: str, expected: str, binding: str,
) -> None:
    """Every consumer refuses a replacement at the shared verification seam."""
    root, failure = case
    admitted = json.loads((root / "admission.json").read_bytes())
    replacement = json.loads(json.dumps(admitted))
    if binding == "target":
        replacement["target"]["environment"] = "other"
    elif binding == "subject":
        replacement["candidate"]["id"] = "other"
    else:
        candidate = module.handoff.parse_yaml((root / "release-handoff.yaml").read_bytes())
        candidate["repair_owner"] = {"id": "other-owner", "route": "workflow:other"}
        raw = module.handoff.yaml_bytes(candidate)
        (root / "other-candidate.yaml").write_bytes(raw)
        replacement["candidate"]["locator"] = "other-candidate.yaml"
        replacement["candidate"]["sha256"] = helpers.digest(raw)

    # Bind the failure to the replacement to expose any trust in its new bytes.
    failure["target"] = replacement["target"]
    failure["candidate_sha256"] = replacement["candidate"]["sha256"]
    review = {
        "subject": {key: admitted["candidate"][key] for key in ("id", "sha256")},
        "target": admitted["target"], "stage": "pre-deploy",
        "rubric": {
            "id": "security", "role": "security",
            "sha256": helpers.digest(
                (helpers.PACK / ".apm/skills/release-loop/references/security-review.md").read_bytes()
            ),
        },
        "reviewer": {"id": "focused-reviewer", "kind": "local"},
        "permissions_digest": helpers.digest(b"permissions"),
        "evidence": [{**failure["evidence"][0], "kind": "test-report", "observed_at": helpers.NOW}],
        "areas": [
            {"area": area, "coverage": "covered", "evidence": ["runtime"], "findings": []}
            for area in module.REVIEW_AREAS["security"]
        ],
        "result": "pass",
    }
    (root / "rubric.md").write_bytes(
        (helpers.PACK / ".apm/skills/release-loop/references/security-review.md").read_bytes()
    )
    (root / "review.json").write_text(json.dumps(review))
    (root / "failure.json").write_text(json.dumps(failure))
    (root / "replacement.json").write_text(json.dumps(replacement))
    original = module.verified_admission
    swapped = False
    after_swap: dict[str, bytes] = {}

    def swap_after_verification(*args: Any, **kwargs: Any) -> Any:
        """Replace the admission only after its original pins have passed."""
        nonlocal swapped, after_swap
        result = original(*args, **kwargs)
        if not swapped:
            (root / "replacement.json").replace(root / "admission.json")
            swapped = True
            after_swap = helpers.snapshot(root)
        return result

    monkeypatch.setattr(module, "verified_admission", swap_after_verification)
    if command == "verify":
        args = [command, "admission.json"]
    elif command == "check-review":
        args = [command, "review.json", "--admission", "admission.json", "--rubric", "rubric.md"]
    elif command == "check-stage":
        args = [command, "--stage", "admission", "--admission", "admission.json"]
    else:
        args = [command, "--admission", "admission.json", "--failure", "failure.json"]
    code, result = helpers.invoke(module, root, capsys, *args)
    assert swapped and code == 1
    helpers.assert_code(result, expected)
    assert "excerpts" not in result and "repair_owner" not in result and "route" not in result
    assert helpers.snapshot(root) == after_swap


@pytest.mark.parametrize("sample", [
    "shared: !!str\n  &a\n  meadow-finch\npassword: *a",
    "shared: &a meadow-finch\nouter: &b\n- *a\npassword: *b",
    "shared: &a meadow-finch\nouter: &b [\n*a,\nhealthy]\npassword: *b",
    "shared: &a meadow-finch\npassword: unrelated",
    "copy: *a\npassword: unrelated",
])
def test_yaml_properties_redact_whole_excerpt(
    module: ModuleType, case: Any, capsys: Any, sample: str,
) -> None:
    """Any YAML property beside a credential line suppresses the whole excerpt."""
    root, failure = case
    data = ("before: healthy\n" + sample + "\nafter: healthy").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"


def test_yaml_properties_without_credential_lines_survive(module: ModuleType) -> None:
    """Benign anchors and aliases alone do not cause whole-excerpt suppression."""
    data = "shared: &a healthy\ncopy: *a"
    assert module.scrub_excerpt(data.encode(), False) == data


@pytest.mark.parametrize("option", ["-u", "--user", "--user="])
@pytest.mark.parametrize("gap", ["", "\n", "  " + chr(92) + "\n", "\n  " + chr(92) + "\n\n"])
def test_user_option_withholds_continued_document(
    module: ModuleType, case: Any, capsys: Any, option: str, gap: str,
) -> None:
    """Credential flags withhold all continued command arguments."""
    root, failure = case
    slash = chr(92)
    data = (
        f"before: healthy\ncurl {option} {slash}\n{gap}"
        f"  reader:meadow-finch {slash}\n\n"
        f"  following-fragment {slash}\n  last-fragment\nafter: healthy"
    ).encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    output = result["excerpts"][0]["text"]
    for value in ("meadow-finch", "following-fragment", "last-fragment"):
        assert value not in output
    assert output == "[redacted]"
    flag_only = f"curl {option} {slash}\n{gap}  --verbose https://example.invalid\nhealthy"
    assert module.scrub_excerpt(flag_only.encode(), False) == "[redacted]"


@pytest.mark.parametrize("option", ["--user=-reader:meadow-finch", "-u=-reader:meadow-finch"])
def test_user_option_attached_hyphen_value(
    module: ModuleType, case: Any, capsys: Any, option: str,
) -> None:
    """An equals sign binds even a hyphen-leading argument as the option value."""
    root, failure = case
    data = ("before: healthy\n" + option + "\nafter: healthy").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"


def test_redaction_guide_rules() -> None:
    """The reference names the conservative excerpt and command boundaries."""
    guide = helpers.PACK.parents[1] / "guides/release-engineering/reference/release-admission.md"
    prose = " ".join(guide.read_text(encoding="utf-8").split())
    assert "whole document" in prose
    assert "protected store" in prose
    assert "linear" in prose


@pytest.mark.parametrize("sample", [
    'curl --user="' + chr(92) + '\nreader:meadow-finch"',
    "curl -u-guest:meadow-finch",
    '{"password"\n: "meadow-finch"}',
    "curl --user= " + chr(92) + "\n-guest:meadow-finch",
    "password mentioned without any assignment",
])
def test_document_level_withholding(
    module: ModuleType, case: Any, capsys: Any, sample: str,
) -> None:
    """Any indicator withholds the document, regardless of value layout."""
    root, failure = case
    data = ("before: healthy\n" + sample + "\nafter: healthy").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"
    assert result["redaction"] == "best-effort"


def test_document_indicator_beyond_excerpt(module: ModuleType, case: Any, capsys: Any) -> None:
    """A late credential word withholds an otherwise benign prefix as well."""
    root, failure = case
    data = b"healthy diagnostic\n" * 5000 + b"password mentioned"
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"


def test_redaction_linear_time() -> None:
    """Bound adversarial scans with a deadline and size-scaled timing budgets."""
    program = """
import importlib.util
import sys
import time
path = sys.argv[1]
spec = importlib.util.spec_from_file_location("release_engineering_release_loop_timing", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
for seed in (b"a", b"healthy diagnostic: ready\\n", b"%252521 ", b"://a "):
    baseline = None
    for size in (65536, 524288, 4194304):
        raw = (seed * (size // len(seed) + 1))[:size]
        start = time.perf_counter()
        module.scrub_excerpt(raw, False)
        elapsed = time.perf_counter() - start
        if baseline is None:
            baseline = max(elapsed, 0.01)
        assert elapsed < baseline * (size / 65536) * 8 + 0.05, (size, elapsed, baseline)
        print(size, elapsed, flush=True)
"""
    script = helpers.PACK / ".apm/skills/release-loop/scripts/release_admission.py"
    result = subprocess.run(
        [sys.executable, "-c", program, str(script)], capture_output=True, text=True, timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("identifier", ["password:value", "access-token:demo", "pwd:demo"])
def test_handoff_metadata_withholding(
    module: ModuleType, case: Any, capsys: Any, identifier: str,
) -> None:
    """Credential-shaped evidence identifiers never appear in serialized output."""
    root, failure = case
    failure["evidence"][0]["id"] = identifier
    failure["check"]["id"] = identifier
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert identifier not in json.dumps(result)
    assert result["excerpts"][0]["id"] == "evidence-1"


@pytest.mark.parametrize("kind", ["terraform-plan", "terraform-state", "plan", "state"])
def test_plan_kind_withholding(
    module: ModuleType, case: Any, capsys: Any, kind: str,
) -> None:
    """Explicit plan and state evidence retains only safe metadata."""
    root, failure = case
    data = b"opaque-private-plan-material"
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0].update(kind=kind, sha256=helpers.digest(data))
    code, result = run_repair(module, case, capsys)
    assert code == 0
    excerpt = result["excerpts"][0]
    assert excerpt["text"] == "withheld: sensitive-plan"
    assert excerpt["id"] == "runtime"
    assert excerpt["sha256"] == helpers.digest(data)
    assert excerpt["size"] == len(data)
    assert data.decode() not in json.dumps(result)


@pytest.mark.parametrize("structure", [
    {"planned_values": {"value": "meadow-finch"}},
    {"resource_changes": [{"value": "meadow-finch"}]},
    {"prior_state": {"value": "meadow-finch"}},
    {"terraform_version": "1.0", "configuration": {"value": "meadow-finch"}},
    {"sensitive_values": {"value": "meadow-finch"}},
    {"nested": [{"planned_values": {"value": "meadow-finch"}}]},
])
def test_plan_structure_withholding(
    module: ModuleType, case: Any, capsys: Any, structure: dict[str, Any],
) -> None:
    """Plan structures are withheld even without a caller-supplied kind."""
    root, failure = case
    data = json.dumps(structure).encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    excerpt = result["excerpts"][0]
    assert excerpt["text"] == "withheld: sensitive-plan"
    assert excerpt["sha256"] == helpers.digest(data)
    assert excerpt["size"] == len(data)
    assert "meadow-finch" not in json.dumps(result)


@pytest.mark.parametrize("userinfo", [
    "reader%2Fname:value", "reader%20name:value", "reader%2fname:value",
])
def test_encoded_userinfo_withholding(
    module: ModuleType, case: Any, capsys: Any, userinfo: str,
) -> None:
    """Encoded authority characters cannot hide URL credentials."""
    root, failure = case
    data = f"healthy https://{userinfo}@example.invalid/path healthy".encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"


@pytest.mark.parametrize("ending", ["...", ".", ",", ";", ")", "!"])
@pytest.mark.parametrize("segments", ["e30.e30", "e30.e30.YWJj", "trace.e30.e30.YWJj"])
def test_adjacent_jwt_withholding(
    module: ModuleType, case: Any, capsys: Any, segments: str, ending: str,
) -> None:
    """Object-header JWTs withhold the document even beside punctuation."""
    root, failure = case
    data = f"before healthy {segments}{ending} after healthy".encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"


@pytest.mark.parametrize("sample", [
    r'{"pass\x77ord": "meadow-finch"}',
    r'{"pass\U00000077ord": "meadow-finch"}',
    r'{"endpoint": "https:\/\/reader:meadow-finch@example.invalid"}',
    "curl --us'er'=reader:meadow-finch",
    'curl --us"er"=reader:meadow-finch',
    "curl --us" + chr(92) + "\ner=reader:meadow-finch",
    r'{"endpoint": "https:\x2f\x2freader:meadow-finch@example.invalid"}',
    r'{"endpoint": "https:\U0000002f\U0000002freader:meadow-finch@example.invalid"}',
])
def test_normalized_document_withholding(
    module: ModuleType, case: Any, capsys: Any, sample: str,
) -> None:
    """Escapes, shell quotes and joins cannot conceal a document indicator."""
    root, failure = case
    data = ("before: healthy\n" + sample + "\nafter: healthy").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"


@pytest.mark.parametrize("option,normalized", [
    (r"--us\er=value", "--user=value"),
    (r"-\u value", "-u value"),
    (r"--\user=value", "--user=value"),
    (r"--u\ser=value", "--user=value"),
    (r"--use\r=value", "--user=value"),
])
def test_backslash_quoted_options(
    module: ModuleType, case: Any, capsys: Any, option: str, normalized: str,
) -> None:
    """Shell backslash quoting cannot hide authentication options in excerpts."""
    assert module.normalize_excerpt(option) == normalized
    root, failure = case
    data = ("before: healthy\ncurl " + option + "\nafter: healthy").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"


@pytest.mark.parametrize("sample", [
    r"https:\/\/reader%2Fname:value@example.invalid/path",
    r"https:\/\/reader%2520name:value%2540example.invalid/path",
    r"https:%252f%252freader%252Fname:value%2540example.invalid/path",
    r"\u0041KIA" + "A1" * 8,
    r"%5Cu0041KIA" + "A1" * 8,
    "AKIA" + "A1" * 8 + r" and \u0041KIA" + "A1" * 8,
    r"pass%255Cu0077ord: meadow-finch",
    r"curl --us%255Cu0065r=reader:meadow-finch",
    r"%255Cu0042asic cmVhZGVyOnZhbHVl",
    r"%255Cu0043ookie: meadow-finch",
    r"shared: %2526a meadow-finch\npass%255Cu0077ord: *a",
    r"%255Cu006530%252ee30%252eYWJj",
    r"-----BEGIN %255Cu0052SA PR%255Cu0049VATE KEY-----",
    r"%255Cu0070lanned_values: {}",
])
def test_combined_encoding_withholding(
    module: ModuleType, case: Any, capsys: Any, sample: str,
) -> None:
    """Every decoded representation is checked before any handoff text is emitted."""
    root, failure = case
    data = ("before: healthy\n" + sample + "\nafter: healthy").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    expected = "withheld: sensitive-plan" if "lanned_values" in sample else "[redacted]"
    assert result["excerpts"][0]["text"] == expected


@pytest.mark.parametrize("depth", [4, 5, 8])
def test_unsettled_normalization_withholding(module: ModuleType, depth: int) -> None:
    """Changing text at the fourth pass is withheld even without a known shape."""
    sample = "before %" + "25" * (depth - 1) + "21 after"
    assert module.scrub_excerpt(sample.encode(), False) == "[redacted]"


@pytest.mark.parametrize("depth", [0, 1, 2, 3])
def test_settled_normalization_preserves_bounded_text(module: ModuleType, depth: int) -> None:
    """Benign text that settles within the budget keeps its original spelling."""
    part = "healthy ! " if depth == 0 else "healthy %" + "25" * (depth - 1) + "21 "
    for size in (100, 5000):
        sample = part * size
        output = module.scrub_excerpt(sample.encode(), False)
        assert output != "[redacted]"
        assert len(output.encode()) <= 4096
        if len(sample) <= 4096:
            assert output == sample
        else:
            assert output.endswith("\n[truncated]")


@pytest.mark.parametrize("kind", [None, "diagnostic"])
@pytest.mark.parametrize("candidate_kind", ["terraform-plan-bundle", "diagnostic"])
def test_copied_plan_component_withholding(
    module: ModuleType, case: Any, capsys: Any, kind: str | None, candidate_kind: str,
) -> None:
    """Copies of admitted plan components are withheld by content, even if unlabelled."""
    root, failure = case
    fixture = HERE / "fixtures/journey/infrastructure-only"
    for path in fixture.iterdir():
        (root / path.name).write_bytes(path.read_bytes())
    candidate = json.loads((root / "request.json").read_bytes())
    data = b"opaque-private-material"
    (root / "plan-bundle.json").write_bytes(data)
    for item in candidate["evidence"]:
        item["sha256"] = helpers.digest((root / item["locator"]).read_bytes())
        for subject in item["subjects"]:
            subject["sha256"] = helpers.digest(data)
    candidate["evidence"][0]["kind"] = candidate_kind
    for check in candidate["checks"]:
        for subject in check["subjects"]:
            subject["sha256"] = helpers.digest(data)
    raw = module.handoff.yaml_bytes(candidate)
    (root / "candidate.yaml").write_bytes(raw)
    module.admit(
        "candidate.yaml", root=root, policy="trusted-policy.json", environment="staging",
        account=None, output="renewed.json", now=helpers.NOW,
    )
    (root / "renewed.json").replace(root / "admission.json")
    failure["candidate_sha256"] = helpers.digest(raw)
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    if kind is not None:
        failure["evidence"][0]["kind"] = kind
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "withheld: sensitive-plan"
    assert data.decode() not in json.dumps(result)


@pytest.mark.parametrize("sample", [
    "curl -vu reader:meadow-finch https://example.invalid",
    "curl -su reader:meadow-finch https://example.invalid",
    "curl --us$'er'=reader:meadow-finch",
    r"curl --\u0073ilent meadow-finch",
    "curl --user-agent=meadow-finch",
    "wget -q https://example.invalid/meadow-finch",
    "http GET https://example.invalid/meadow-finch",
    "https GET https://example.invalid/meadow-finch",
    "ssh reader@example.invalid meadow-finch",
    "scp meadow-finch reader@example.invalid:/tmp/",
    "sftp reader@example.invalid meadow-finch",
    "docker login example.invalid meadow-finch",
    "psql -d meadow-finch",
    "mysql -pmeadow-finch",
    "aws s3 cp meadow-finch s3://example/",
    "gcloud storage cp meadow-finch gs://example/",
    "kubectl get meadow-finch",
    "helm show values meadow-finch",
    "git clone https://example.invalid/meadow-finch",
    "cu" + chr(0) + "rl -vu reader:meadow-finch",
])
def test_client_invocation_withholds_whole_excerpt(
    module: ModuleType, case: Any, capsys: Any, sample: str,
) -> None:
    """Client invocations suppress all text without parsing their shell options."""
    root, failure = case
    data = ("before: healthy\n" + sample + "\nafter: healthy").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"


@pytest.mark.parametrize("control", ["%0A", "%0D"])
def test_decoded_userinfo_controls_withhold_document(
    module: ModuleType, case: Any, capsys: Any, control: str,
) -> None:
    """Decoded controls cannot separate URL userinfo from its authority marker."""
    root, failure = case
    data = f"before https://reader{control}:meadow-finch%40example.invalid after".encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"


def test_command_invocation_guide_rule() -> None:
    """The reference states the whole-excerpt client invocation rule."""
    guide = helpers.PACK.parents[1] / "guides/release-engineering/reference/release-admission.md"
    prose = " ".join(guide.read_text(encoding="utf-8").split())
    assert "command invocation" in prose
    assert "without parsing" in prose
    assert "substring match" in prose
    assert "harmless text" in prose


@pytest.mark.parametrize("sample", [
    "curl</dev/null -vu x:y",
    "mysql</dev/null -pvalue",
    "cu$'rl' -vu x:y",
    '["curl","-u","x:y"]',
    'c""url -vu x:y',
    "prefixCURLsuffix -vu x:y",
    "--user-agent diagnostic https://example.invalid/health",
])
def test_client_substring_bypasses_withhold_excerpt(
    module: ModuleType, case: Any, capsys: Any, sample: str,
) -> None:
    """Redirection, arrays and shell quoting cannot hide a client name."""
    root, failure = case
    data = ("before: healthy\n" + sample + "\nafter: healthy").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"


@pytest.mark.parametrize("name", [
    "curl", "wget", "http", "ssh", "scp", "sftp", "psql", "mysql", "aws",
    "gcloud", "kubectl", "helm", "docker login",
])
@pytest.mark.parametrize("joining", ["", "$", "'", '"', "\\", "`", "{", "}", "(", ")", "\t", "\n", "\x00"])
def test_dequoted_client_substrings_withhold_excerpt(
    module: ModuleType, name: str, joining: str,
) -> None:
    """Every client is detected inside text after removing shell syntax and controls."""
    sample = "prefix" + name[0].upper() + joining + name[1:].upper() + "suffix"
    assert module.scrub_excerpt(sample.encode(), False) == "[redacted]"


@pytest.mark.parametrize("sample", [
    "CURL", "healthy", "before: healthy\nafter: healthy", "build completed (exit 0)",
])
def test_client_substring_preserves_existing_results(module: ModuleType, sample: str) -> None:
    """Uppercase clients stay withheld and benign text stays byte-for-byte intact."""
    expected = "[redacted]" if sample == "CURL" else sample
    assert module.scrub_excerpt(sample.encode(), False) == expected


@pytest.mark.parametrize("suffix", [
    "/repair#password=value",
    "/token/value",
    "/repair?next=token-help",
    "/repair#pass%77ord=value",
    "/repair#pass%2577ord=value",
    "/repair?next=AKIA1234567890123456",
    "/eyJhbGciOiJIUzI1NiJ9.e30.c2ln/repair",
    "/repair#" + "x" * 40,
], ids=["fragment", "path", "query-value", "escaped", "nested-escape",
        "access-key", "object-header", "opaque-value"])
def test_route_credentials_anywhere(
    module: ModuleType, case: Any, capsys: Any, suffix: str,
) -> None:
    """Withhold the whole route when any URL component carries credentials."""
    root, failure = case
    candidate = module.handoff.parse_yaml((root / "release-handoff.yaml").read_bytes())
    candidate["repair_owner"]["route"] = "https://example.invalid" + suffix
    (root / "release-handoff.yaml").write_bytes(module.handoff.yaml_bytes(candidate))
    module.admit(
        "release-handoff.yaml", root=root, policy="trusted-policy.json",
        environment="staging", account=None, output="renewed.json", now=helpers.NOW,
    )
    (root / "renewed.json").replace(root / "admission.json")
    failure["candidate_sha256"] = helpers.digest((root / "release-handoff.yaml").read_bytes())
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["status"] == "human-handoff"
    assert result["route"] == "[redacted]"
    assert suffix not in json.dumps(result)


@pytest.mark.parametrize("sample", [
    "docker --config cfg login -p meadow-finch registry",
    "docker --context staging --debug login -p meadow-finch registry",
    "docker --config=cfg --log-level=error login -p meadow-finch registry",
    "docker -H unix:///var/run/docker.sock login -p meadow-finch registry",
    "docker --config cfg lo'gin' -p meadow-finch registry",
    "docker --config cfg LOGIN -p meadow-finch registry",
])
def test_docker_global_options_withhold_document(
    module: ModuleType, case: Any, capsys: Any, sample: str,
) -> None:
    """Global options cannot hide docker login from whole-document withholding."""
    root, failure = case
    data = ("before: healthy\n" + sample + "\nafter: healthy").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"
    assert "meadow-finch" not in json.dumps(result)


@pytest.mark.parametrize("sample", [
    "//reader:meadow-finch@example.invalid/path",
    "//reader@example.invalid/path",
    "//reader%252Fname:meadow-finch%2540example.invalid/path",
    "%2f%2freader:meadow-finch%40example.invalid/path",
    "%252f%252freader:meadow-finch%2540example.invalid/path",
    r"\u002f\u002freader:meadow-finch@example.invalid/path",
    r"\/\/reader:meadow-finch@example.invalid/path",
])
def test_scheme_relative_credentials(
    module: ModuleType, case: Any, capsys: Any, sample: str,
) -> None:
    """Scheme-relative userinfo withholds the entire excerpt after each decoding pass."""
    root, failure = case
    data = ("before: healthy " + sample + " after: healthy").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"
    assert module.scrub_route(sample) == "[redacted]"


def test_handoff_url_query_aliases(module: ModuleType) -> None:
    """Every credential alias withholds routes and excerpts for both URL forms."""
    for name in ("key", "sig", "signature", "apikey", "api_key", "access_token", "auth",
                 "pwd", "secret", "token", "password", "passwd", "credential", "session",
                 "cookie", "%256bey", "%2573ig"):
        for prefix in ("https://", "//"):
            url = prefix + "example.invalid/path?" + name.upper() + "=meadow-finch"
            assert module.scrub_route(url) == "[redacted]"
            assert module.scrub_excerpt(("before " + url + " after").encode(), False) == (
                "[redacted]"
            )


@pytest.mark.parametrize("prefix", ["//", "https://"])
@pytest.mark.parametrize("joining", [" ", "\t", "\n", "\r\n"])
def test_split_userinfo_withholds_handoff(
    module: ModuleType, case: Any, capsys: Any, prefix: str, joining: str,
) -> None:
    """Whitespace and controls inside userinfo cannot survive in handoff text."""
    root, failure = case
    sample = prefix + "reader:short" + joining + "value@example.invalid/path"
    assert module.url_credentials(sample)
    data = ("before: healthy " + sample + " after: healthy").encode()
    (root / "failure.log").write_bytes(data)
    failure["evidence"][0]["sha256"] = helpers.digest(data)
    code, result = run_repair(module, case, capsys)
    assert code == 0
    assert result["excerpts"][0]["text"] == "[redacted]"
    assert "short" not in json.dumps(result)

"""Direct validate output: the AC21 envelope, its exits, and its help."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from agentbundle.commands import validate as validate_cmd
from agentbundle.direct_source import validate_direct_source
from agentbundle.direct_validate import (
    render_direct_validation_json,
    render_direct_validation_text,
)

ENVELOPE_KEYS = {
    "schema_version",
    "command",
    "operation",
    "agentbundle_version",
    "catalogue_schema_version",
    "ok",
    "diagnostics",
    "summary",
}
DIAGNOSTIC_KEYS = {
    "code", "severity", "pack", "path", "line", "col", "message", "remediation",
}


def _write_skill(path: Path, name: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "SKILL.md").write_text(f"---\nname: {name}\n---\n# {name}\n")


def test_direct_validate_json_contract(tmp_path: Path):
    # AC7, AC21 — the established envelope keys plus `summary`, rendered with
    # sort_keys=True and indent=2 so the bytes are stable across runs.
    source = tmp_path / "good"
    _write_skill(source, "good")
    rendered = render_direct_validation_json(validate_direct_source(source))
    payload = json.loads(rendered)

    assert set(payload) == ENVELOPE_KEYS, set(payload) ^ ENVELOPE_KEYS
    assert payload["command"] == "validate"
    assert payload["operation"] == "direct"
    assert payload["ok"] is True
    assert payload["diagnostics"] == []
    # The direct route has no catalogue, so its default is 1 rather than a
    # value read from a catalogue that is not there.
    assert payload["catalogue_schema_version"] == 1
    assert payload["summary"] == {"shape": "root-single", "selected_skills": ["good"]}

    assert rendered == json.dumps(payload, sort_keys=True, indent=2)
    assert rendered == render_direct_validation_json(validate_direct_source(source))

    # A refusal fills `diagnostics` with the full established field set.
    refused = tmp_path / "bad"
    _write_skill(refused / "skills" / "one", "one")
    _write_skill(refused / ".claude" / "skills" / "two", "two")
    failed = json.loads(render_direct_validation_json(validate_direct_source(refused)))
    assert failed["ok"] is False
    assert failed["diagnostics"], "a refusal must report at least one diagnostic"
    for diagnostic in failed["diagnostics"]:
        assert set(diagnostic) == DIAGNOSTIC_KEYS
        assert diagnostic["severity"] == "ERROR"
        assert diagnostic["code"].startswith("CAT-D")
    assert failed["summary"]["shape"] is None


def test_direct_validate_exit_codes(tmp_path: Path, capsys):
    # AC21 — success is 0 and a refusal is 1. Usage errors stay argparse's 2.
    source = tmp_path / "good"
    _write_skill(source, "good")
    assert validate_cmd._run_direct(source, "json") == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True

    refused = tmp_path / "bad"
    _write_skill(refused / "skills" / "one", "one")
    _write_skill(refused / ".claude" / "skills" / "two", "two")
    assert validate_cmd._run_direct(refused, "json") == 1
    assert json.loads(capsys.readouterr().out)["ok"] is False

    assert validate_cmd._run_direct(tmp_path / "missing", "text") == 1
    capsys.readouterr()


def test_direct_validate_text_form(tmp_path: Path):
    # A refusal's text form carries the code, the path, and the recovery.
    refused = tmp_path / "bad"
    _write_skill(refused / "skills" / "one", "one")
    _write_skill(refused / ".claude" / "skills" / "two", "two")
    rendered = render_direct_validation_text(validate_direct_source(refused))
    assert rendered.startswith("FAIL:")
    assert "CAT-D009" in rendered

    source = tmp_path / "good"
    _write_skill(source, "good")
    assert render_direct_validation_text(validate_direct_source(source)).startswith("ok:")


@pytest.mark.parametrize("shape", ["root-single", "collection", "direct-pack"])
def test_summary_reports_every_shape(tmp_path: Path, shape):
    # AC21 — the summary names the shape and the selected skills for each form.
    root = tmp_path / shape
    if shape == "root-single":
        # The identity is the envelope directory name, so it is `shape` here;
        # `solo` in the frontmatter is only a display string.
        _write_skill(root, "solo")
        expected = [shape]
    else:
        _write_skill(root / "skills" / "alpha", "alpha")
        _write_skill(root / "skills" / "beta", "beta")
        expected = ["alpha", "beta"]
        if shape == "direct-pack":
            (root / "pack.toml").write_text(
                'schema = 1\n[pack]\nname = "pack"\nversion = "1.0.0"\n'
            )
    admission = validate_direct_source(root)
    assert admission.ok, admission.diagnostics
    payload = json.loads(render_direct_validation_json(admission))
    assert payload["summary"] == {"shape": shape, "selected_skills": expected}


def test_validate_help_describes_the_direct_form():
    # AC7 — help for validate describes the direct source form.
    result = subprocess.run(
        [sys.executable, "-m", "agentbundle", "validate", "--help"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parents[2],
    )
    assert result.returncode == 0, result.stderr
    assert "--format" in result.stdout
    assert "direct source" in result.stdout

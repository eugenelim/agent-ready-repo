"""Eval-manifest checks in verifier step 18."""

import json
from pathlib import Path

import pytest
from agentbundle.catalogue_tooling.verify import _step_fixture_checks


def _evals(root: Path, pack: str = "alpha") -> Path:
    path = root / "packs" / pack / ".apm" / "skills" / "demo" / "evals"
    path.mkdir(parents=True)
    return path


def test_valid_eval_queries_pass(tmp_path):
    target = _evals(tmp_path) / "eval_queries.json"
    target.write_text(
        json.dumps([{"query": "use demo", "should_trigger": True}]), encoding="utf-8"
    )
    assert _step_fixture_checks(tmp_path, None, None, tmp_path / "tmp") == []


def test_malformed_eval_queries_json_is_reported(tmp_path):
    target = _evals(tmp_path) / "eval_queries.json"
    target.write_text("{", encoding="utf-8")
    findings = _step_fixture_checks(tmp_path, None, None, tmp_path / "tmp")
    assert findings[0].code == "CAT-V-018"
    assert "not valid JSON" in findings[0].message


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ([], "at least one query"),
        ([{"should_trigger": True}], "query must be a non-empty string"),
        ([{"query": "use demo", "should_trigger": "yes"}], "must be a boolean"),
    ],
)
def test_eval_queries_structural_errors_are_reported(tmp_path, content, message):
    target = _evals(tmp_path) / "eval_queries.json"
    target.write_text(json.dumps(content), encoding="utf-8")
    findings = _step_fixture_checks(tmp_path, None, None, tmp_path / "tmp")
    assert findings[0].code == "CAT-V-018"
    assert message in findings[0].message


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("{", "not valid JSON"),
        ("", "not valid JSON"),
        (
            json.dumps({"skill_name": "demo", "evals": []}),
            "must contain at least one entry",
        ),
        (
            json.dumps({"skill_name": "demo", "evals": [{"id": 1}]}),
            "prompt must be a non-empty string",
        ),
    ],
)
def test_evals_json_errors_are_reported(tmp_path, content, message):
    target = _evals(tmp_path) / "evals.json"
    target.write_text(content, encoding="utf-8")
    findings = _step_fixture_checks(tmp_path, None, None, tmp_path / "tmp")
    assert findings[0].code == "CAT-V-018"
    assert message in findings[0].message


def test_opaque_payload_is_not_parsed(tmp_path):
    evals = _evals(tmp_path)
    payload = evals / "files" / "payload.jsonl"
    payload.parent.mkdir()
    payload.write_text("not json\n", encoding="utf-8")
    (evals / "evals.json").write_text(
        json.dumps(
            {
                "skill_name": "demo",
                "evals": [
                    {
                        "id": 1,
                        "prompt": "p",
                        "expected_output": "e",
                        "files": ["evals/files/payload.jsonl"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    assert _step_fixture_checks(tmp_path, None, None, tmp_path / "tmp") == []


def test_linked_manifest_is_refused(tmp_path):
    evals = _evals(tmp_path)
    outside = tmp_path / "outside.json"
    outside.write_text("[]", encoding="utf-8")
    try:
        (evals / "eval_queries.json").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks not available")
    findings = _step_fixture_checks(tmp_path, None, None, tmp_path / "tmp")
    assert any("link-like eval manifest" in item.message for item in findings)


def test_relative_catalogue_root_is_supported(tmp_path, monkeypatch):
    target = _evals(tmp_path) / "eval_queries.json"
    target.write_text(
        json.dumps([{"query": "use demo", "should_trigger": True}]), encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    assert _step_fixture_checks(Path(), None, None, Path("tmp")) == []


def test_pack_selection_does_not_scan_unrelated_eval_manifests(tmp_path):
    alpha = _evals(tmp_path, "alpha") / "eval_queries.json"
    alpha.write_text(
        json.dumps([{"query": "use demo", "should_trigger": True}]), encoding="utf-8"
    )
    beta = _evals(tmp_path, "beta") / "eval_queries.json"
    beta.write_text("{", encoding="utf-8")
    assert _step_fixture_checks(tmp_path, None, "alpha", tmp_path / "tmp") == []

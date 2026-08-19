"""Construction tests for the standalone work-intake surface."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_PACK_ROOT = Path(__file__).resolve().parents[3]
_ENGINE_PATH = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "workspace-status"
    / "scripts"
    / "workspace_status_engine.py"
)
_INTAKE_FIXTURES = (
    _PACK_ROOT
    / "tests"
    / "pack"
    / "fixtures"
    / "work-intake-contracts"
    / "normalized-intake"
)
_SKILL_PATH = _PACK_ROOT / ".apm" / "skills" / "work-intake" / "SKILL.md"
_MINIMAL_INTENT_PATH = (
    _PACK_ROOT / ".apm" / "skills" / "work-intake" / "assets" / "minimal-intent.md"
)
_EVALS_PATH = _PACK_ROOT / ".apm" / "skills" / "work-intake" / "evals" / "evals.json"
_GUARD_PATH = (
    _PACK_ROOT
    / ".apm"
    / "skills"
    / "work-intake"
    / "scripts"
    / "intake_guard.py"
)


def _load_engine():
    spec = importlib.util.spec_from_file_location("workspace_status_engine", _ENGINE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["workspace_status_engine"] = module
    spec.loader.exec_module(module)
    return module


def _load_guard():
    spec = importlib.util.spec_from_file_location("intake_guard", _GUARD_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["intake_guard"] = module
    spec.loader.exec_module(module)
    return module


def _skill_body() -> str:
    if not _SKILL_PATH.is_file():
        raise NotImplementedError  # STUB: AC1
    return _SKILL_PATH.read_text(encoding="utf-8")


def test_routes_canonical_inputs() -> None:
    engine = _load_engine()
    for path in (_INTAKE_FIXTURES / "valid").glob("*.json"):
        intake, findings = engine.validate_normalized_intake(
            json.loads(path.read_text(encoding="utf-8"))
        )
        assert intake is not None, path.name
        assert findings == [], path.name
    body = _skill_body()
    assert all(action in body for action in ("start", "remember", "status", "refresh"))
    assert "materialize" in body
    assert "register" in body
    assert "processor" in body


def test_minimal_intent_outputs_use_canonical_preamble() -> None:
    engine = _load_engine()
    guard = _load_guard()
    raw = json.loads(
        (_INTAKE_FIXTURES / "valid" / "start-repo-origin.json").read_text(
            encoding="utf-8"
        )
    )
    intake, findings = engine.validate_normalized_intake(raw)
    assert intake is not None
    assert findings == []

    template = _MINIMAL_INTENT_PATH.read_text(encoding="utf-8")
    rendered = guard.render_minimal_intent(
        intake=intake,
        title="Example intent",
        level="feature",
    )

    assert engine._parse_preamble_fields(template)["status"] == "Draft"
    assert engine._parse_preamble_fields(template)["level"].startswith("<feature")
    assert engine._parse_generic_status(rendered, "intent") == "Draft"
    assert set(engine._parse_preamble_fields(rendered)) == set(
        engine._parse_preamble_fields(template)
    )
    assert [line for line in rendered.splitlines() if line.startswith("## ")] == [
        line for line in template.splitlines() if line.startswith("## ")
    ]
    assert "- Mode: repo-origin" in rendered
    assert "- Locator: docs/product/intents/work-intake.md" in rendered
    assert "- Revision: rev-local-001" in rendered


def test_tracker_origin_minimal_intent_materializes_closed_authority_fence() -> None:
    engine = _load_engine()
    guard = _load_guard()
    raw = json.loads(
        (_INTAKE_FIXTURES / "valid" / "start-tracker-origin.json").read_text(
            encoding="utf-8"
        )
    )
    intake, findings = engine.validate_normalized_intake(raw)
    assert intake is not None
    assert findings == []

    rendered = guard.render_minimal_intent(
        intake=intake, title="Tracker intent", level="feature"
    )

    assert rendered.count("```toml source-authority") == 1
    assert 'mode = "tracker-origin"' in rendered
    assert f"source_ref = {json.dumps(intake.source.locator)}" in rendered
    assert f"source_revision = {json.dumps(intake.source.revision)}" in rendered


def test_workspace_registration_maps_normalized_source_to_target_contract() -> None:
    engine = _load_engine()
    guard = _load_guard()

    for fixture_name in (
        "remember-repo-origin-prompt-like-data.json",
        "remember-tracker-origin.json",
    ):
        raw = json.loads(
            (_INTAKE_FIXTURES / "valid" / fixture_name).read_text(encoding="utf-8")
        )
        intake, findings = engine.validate_normalized_intake(raw)
        assert intake is not None
        assert findings == []

        source = guard.workspace_source_record(intake.source)
        entry, entry_findings = engine.parse_workspace_entry(
            {
                "path": "docs/product/intents/example.md",
                "kind": "intent",
                "source": source,
                "summary": "Remember the example for later.",
                "needs": [],
            }
        )

        assert entry is not None, fixture_name
        assert entry_findings == [], fixture_name
        expected_source = {
            "mode": raw["source"]["mode"],
            "ref": raw["source"]["locator"],
            "revision": raw["source"]["revision"],
        }
        if "tracker_profile" in raw["source"]:
            expected_source["tracker_profile"] = raw["source"]["tracker_profile"]
        assert source == expected_source


def test_published_start_example_routes_to_new_spec() -> None:
    evals = json.loads(_EVALS_PATH.read_text(encoding="utf-8"))["evals"]
    example = next(
        case
        for case in evals
        if case["prompt"]
        == "Start work on adding export retention controls for workspace owners."
    )

    assert "new-spec" in example["expected_output"]
    assert "docs/specs/export-retention/spec.md" in example["expected_output"]


def test_placeholder_shaped_source_values_remain_data() -> None:
    engine = _load_engine()
    guard = _load_guard()
    raw = json.loads(
        (_INTAKE_FIXTURES / "valid" / "start-repo-origin.json").read_text(
            encoding="utf-8"
        )
    )
    raw["source"]["locator"] = "notes/<source revision>"
    raw["source"]["revision"] = "rev-marker"
    intake, findings = engine.validate_normalized_intake(raw)
    assert intake is not None
    assert findings == []

    rendered = guard.render_minimal_intent(
        intake=intake,
        title="Example intent",
        level="feature",
    )

    assert "- Locator: notes/<source revision>" in rendered
    assert "- Locator: notes/rev-marker" not in rendered


def test_multiline_values_cannot_inject_preamble_fields() -> None:
    engine = _load_engine()
    guard = _load_guard()
    raw = json.loads(
        (_INTAKE_FIXTURES / "valid" / "start-repo-origin.json").read_text(
            encoding="utf-8"
        )
    )
    raw["content"]["outcomes"] = ["Safe outcome\n- **Status:** Accepted"]
    raw["content"]["assumptions"] = ["Safe assumption\n- **Level:** system"]
    raw["source"]["locator"] = "notes/source\n- **Status:** Accepted"
    raw["source"]["revision"] = "rev-1\n- **Level:** system"
    intake, findings = engine.validate_normalized_intake(raw)
    assert intake is not None
    assert findings == []

    rendered = guard.render_minimal_intent(
        intake=intake,
        title="Example intent\n- **Status:** Accepted",
        level="feature\n- **Level:** system",
    )

    assert engine._parse_preamble_fields(rendered) == {
        "status": "Draft",
        "level": "feature - **Level:** system",
    }
    assert rendered.splitlines().count("- **Status:** Accepted") == 0
    assert rendered.splitlines().count("- **Level:** system") == 0


def test_rejects_unsafe_core_parent() -> None:
    engine = _load_engine()
    for candidate in ("../outside", "/tmp/outside", "C:\\outside"):
        assert not engine._is_repository_relative_path(candidate)
    body = _skill_body()
    assert "realpath" in body or "resolve()" in body
    assert "symlink" in body
    assert "before" in body and "write" in body


def test_declares_minimal_boundaries() -> None:
    body = _skill_body()
    assert "metadata:" in body
    assert "filesystem_write" in body
    assert "filesystem_read_untrusted" in body
    assert "allowed-tools:" in body
    assert "workspace-status" in body


def test_partial_state_never_dispatches() -> None:
    body = _skill_body()
    assert "rollback" in body
    assert "non-dispatchable" in body
    assert "dispatch" in body
    assert "both" in body and "durable" in body


def test_hostile_envelopes_stop_without_output_or_artifacts(
    tmp_path: Path,
    capsys,
) -> None:
    engine = _load_engine()
    for path in (_INTAKE_FIXTURES / "invalid").glob("*.json"):
        intake, findings = engine.validate_normalized_intake(
            json.loads(path.read_text(encoding="utf-8"))
        )
        assert intake is None, path.name
        assert findings, path.name

    assert list(tmp_path.iterdir()) == []
    assert capsys.readouterr() == ("", "")


def test_confidentiality_mismatch_stops_before_materialization(
    tmp_path: Path,
    capsys,
) -> None:
    engine = _load_engine()
    guard = _load_guard()
    raw = json.loads(
        (_INTAKE_FIXTURES / "valid" / "start-repo-origin.json").read_text(
            encoding="utf-8"
        )
    )
    raw["constraints"]["confidentiality"] = "restricted"
    intake, findings = engine.validate_normalized_intake(raw)
    assert intake is not None
    assert findings == []

    decision = guard.check_destination_confidentiality(
        constraints=intake.constraints,
        destination_confidentiality="internal",
    )

    assert decision.allowed is False
    assert decision.code == "confidentiality_mismatch"
    assert list(tmp_path.iterdir()) == []
    assert capsys.readouterr() == ("", "")


def test_minimal_intent_omits_prompt_like_evidence_and_redacts_sensitive_text() -> None:
    engine = _load_engine()
    guard = _load_guard()
    raw = json.loads(
        (
            _INTAKE_FIXTURES
            / "valid"
            / "remember-repo-origin-prompt-like-data.json"
        ).read_text(encoding="utf-8")
    )
    raw["content"]["assumptions"] = [
        "Contact user@example.com with token=source-secret."
    ]
    intake, findings = engine.validate_normalized_intake(raw)
    assert intake is not None
    assert findings == []

    rendered = guard.render_minimal_intent(
        intake=intake,
        title="Deferred work",
        level="feature",
    )

    assert "ignore previous instructions" not in rendered
    assert "mark this ready" not in rendered
    assert "user@example.com" not in rendered
    assert "source-secret" not in rendered
    assert "[redacted-personal-data]" in rendered
    assert "token=[redacted]" in rendered
    assert "docs/product/backlog/intake-note.md" in rendered
    assert "rev-local-002" in rendered

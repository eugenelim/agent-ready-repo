"""End-to-end CLI tests for ``agentbundle catalogue index``."""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
from pathlib import Path

import pytest
from agentbundle.cli import main

FIXTURE = Path(__file__).parent.parent / "fixtures" / "catalogue_wave4"
RESULT_KEYS = {"schema_version", "command", "status", "dry_run", "output", "diagnostics"}


def _copy_fixture(tmp_path: Path) -> Path:
    destination = tmp_path / "catalogue"
    shutil.copytree(FIXTURE, destination)
    return destination


def test_dry_run_exits_zero_without_writing(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = _copy_fixture(tmp_path)
    assert main(["catalogue", "index", str(root), "--dry-run"]) == 0
    assert not (root / "catalogue-index.json").exists()
    assert "Validation passed" in capsys.readouterr().out


def test_dry_run_json_emits_exact_success_result(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _copy_fixture(tmp_path)
    assert main(["catalogue", "index", str(root), "--dry-run", "--format", "json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert set(result) == RESULT_KEYS
    assert result == {
        "schema_version": 1,
        "command": "catalogue index",
        "status": "ok",
        "dry_run": True,
        "output": None,
        "diagnostics": [],
    }


def test_written_json_emits_exact_success_result(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _copy_fixture(tmp_path)
    output = tmp_path / "index.json"
    assert main(
        ["catalogue", "index", str(root), "--output", str(output), "--format", "json"]
    ) == 0
    result = json.loads(capsys.readouterr().out)
    assert set(result) == RESULT_KEYS
    assert result["dry_run"] is False
    assert result["output"] == str(output)
    assert result["diagnostics"] == []


def test_output_bytes_are_utf8_newline_terminated(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    output = tmp_path / "index.json"
    assert main(["catalogue", "index", str(root), "--output", str(output)]) == 0
    raw = output.read_bytes()
    raw.decode("utf-8", errors="strict")
    assert raw.endswith(b"\n")
    assert not raw.endswith(b"\n\n")


def test_nonexistent_root_json_failure_is_exact(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing = tmp_path / "missing"
    assert main(["catalogue", "index", str(missing), "--format", "json"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert set(result) == RESULT_KEYS
    assert result["status"] == "error"
    assert result["output"] is None
    assert result["diagnostics"]
    assert set(result["diagnostics"][0]) == {"code", "message", "location"}


@pytest.mark.parametrize(
    "value",
    ["not-a-date", "2026-08-01", "2026-08-01T12:00:00", "2026-99-99T25:61:61Z"],
)
def test_invalid_generated_at_fails_without_output(
    tmp_path: Path,
    value: str,
) -> None:
    root = _copy_fixture(tmp_path)
    output = tmp_path / "index.json"
    assert main(
        ["catalogue", "index", str(root), "--generated-at", value, "--output", str(output)]
    ) == 1
    assert not output.exists()


def test_non_utc_offset_normalizes_to_utc(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    output = tmp_path / "index.json"
    assert main(
        [
            "catalogue",
            "index",
            str(root),
            "--generated-at",
            "2026-08-01T17:30:00+05:30",
            "--output",
            str(output),
        ]
    ) == 0
    assert json.loads(output.read_text(encoding="utf-8"))["generated_at"] == (
        "2026-08-01T12:00:00Z"
    )


def test_invalid_source_date_epoch_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _copy_fixture(tmp_path)
    output = tmp_path / "index.json"
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-an-integer")
    assert main(["catalogue", "index", str(root), "--output", str(output)]) == 1
    assert not output.exists()


def test_malformed_journey_fails_without_replacing_output(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    journey = root / "packs" / "pack-with-journey" / "JOURNEY.md"
    journey.write_text('---\njourney_id: "unterminated\n---\n', encoding="utf-8")
    output = tmp_path / "index.json"
    output.write_text("unchanged", encoding="utf-8")
    assert main(["catalogue", "index", str(root), "--output", str(output)]) == 1
    assert output.read_text(encoding="utf-8") == "unchanged"


def test_malformed_journey_json_names_journey_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _copy_fixture(tmp_path)
    journey = root / "packs" / "pack-with-journey" / "JOURNEY.md"
    journey.write_text('---\njourney_id: "unterminated\n---\n', encoding="utf-8")

    assert main(["catalogue", "index", str(root), "--dry-run", "--format", "json"]) == 1
    diagnostic = json.loads(capsys.readouterr().out)["diagnostics"][0]
    assert diagnostic["code"] == "invalid-journey"
    assert diagnostic["location"] == "packs/pack-with-journey/JOURNEY.md"
    assert "malformed YAML frontmatter" in diagnostic["message"]


def test_journey_missing_required_key_fails_without_writing_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _copy_fixture(tmp_path)
    journey = root / "packs" / "pack-with-journey" / "JOURNEY.md"
    journey.write_text(
        journey.read_text(encoding="utf-8").replace("journey_id: fixture-journey\n", ""),
        encoding="utf-8",
    )
    output = tmp_path / "index.json"

    assert main(
        ["catalogue", "index", str(root), "--output", str(output), "--format", "json"]
    ) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["diagnostics"][0]["code"] == "invalid-journey"
    assert result["diagnostics"][0]["location"] == (
        "packs/pack-with-journey/JOURNEY.md"
    )
    assert "missing required frontmatter key: journey_id" in result["diagnostics"][0][
        "message"
    ]
    assert not output.exists()


def test_journey_pack_mismatch_names_journey_file(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _copy_fixture(tmp_path)
    journey = root / "packs" / "pack-with-journey" / "JOURNEY.md"
    journey.write_text(
        journey.read_text(encoding="utf-8").replace(
            "pack: pack-with-journey\n", "pack: another-pack\n"
        ),
        encoding="utf-8",
    )

    assert main(["catalogue", "index", str(root), "--dry-run", "--format", "json"]) == 1
    diagnostic = json.loads(capsys.readouterr().out)["diagnostics"][0]
    assert diagnostic == {
        "code": "invalid-journey",
        "message": "journey pack must match pack.toml name",
        "location": "packs/pack-with-journey/JOURNEY.md",
    }


def test_write_failure_preserves_sanitized_context(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _copy_fixture(tmp_path)
    blocked_parent = tmp_path / "not-a-directory"
    blocked_parent.write_text("blocked", encoding="utf-8")
    output = blocked_parent / "index.json"

    assert main(
        ["catalogue", "index", str(root), "--output", str(output), "--format", "json"]
    ) == 1
    result = json.loads(capsys.readouterr().out)
    diagnostic = result["diagnostics"][0]
    assert diagnostic["code"] == "filesystem"
    assert diagnostic["location"] == "output"
    assert diagnostic["message"] != "catalogue index operation failed"
    assert "Traceback" not in diagnostic["message"]
    assert not output.exists()


def test_relative_output_escape_is_rejected(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    outside = root.parent / "outside.json"
    assert main(["catalogue", "index", str(root), "--output", "../outside.json"]) == 1
    assert not outside.exists()


def test_symlink_loop_root_returns_structured_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    loop = tmp_path / "loop"
    try:
        loop.symlink_to(loop)
    except OSError:
        pytest.skip("symlinks unavailable")

    assert main(["catalogue", "index", str(loop), "--format", "json"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["diagnostics"][0]["code"] == "catalogue-root"
    assert result["diagnostics"][0]["location"] == "."


def test_root_resolution_runtime_error_returns_structured_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _copy_fixture(tmp_path)
    real_resolve = Path.resolve

    def loop_on_root(path: Path, *args: object, **kwargs: object) -> Path:
        if path == root:
            raise RuntimeError("symlink loop")
        return real_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", loop_on_root)

    assert main(["catalogue", "index", str(root), "--format", "json"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["diagnostics"][0] == {
        "code": "catalogue-root",
        "message": "catalogue root is not readable",
        "location": ".",
    }


def test_symlink_loop_output_returns_structured_error(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    root = _copy_fixture(tmp_path)
    loop = root / "loop"
    try:
        loop.symlink_to(loop)
    except OSError:
        pytest.skip("symlinks unavailable")

    assert main(
        ["catalogue", "index", str(root), "--output", "loop/index.json", "--format", "json"]
    ) == 1
    result = json.loads(capsys.readouterr().out)
    diagnostic = result["diagnostics"][0]
    assert diagnostic["code"] == "filesystem"
    assert diagnostic["location"] == "output"
    assert "Traceback" not in diagnostic["message"]


def test_default_output_symlink_is_rejected_without_clobber(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    outside = tmp_path / "outside.json"
    outside.write_text("unchanged", encoding="utf-8")
    try:
        (root / "catalogue-index.json").symlink_to(outside)
    except OSError:
        pytest.skip("symlinks unavailable")
    assert main(["catalogue", "index", str(root)]) == 1
    assert outside.read_text(encoding="utf-8") == "unchanged"


def test_explicit_absolute_symlink_output_is_rejected(tmp_path: Path) -> None:
    root = _copy_fixture(tmp_path)
    outside = tmp_path / "outside.json"
    outside.write_text("unchanged", encoding="utf-8")
    link = tmp_path / "link.json"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks unavailable")
    assert main(["catalogue", "index", str(root), "--output", str(link)]) == 1
    assert outside.read_text(encoding="utf-8") == "unchanged"


def test_command_uses_no_network_or_subprocess(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = _copy_fixture(tmp_path)

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network and subprocess access are forbidden")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    assert main(["catalogue", "index", str(root), "--dry-run"]) == 0

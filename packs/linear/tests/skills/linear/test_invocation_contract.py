"""Source contract for installed skill entry-point resolution."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "linear"
SYNC_SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "linear-brief-sync"
ENTRY_POINTS = ("linear.py",)
TEXT_SUFFIXES = {".js", ".json", ".md", ".py", ".toml"}
WINDOWS_RENDERER_SOURCE = SKILL_ROOT / "scripts" / "linear.py"


def _surface_text() -> str:
    """Return all shipped text that can teach, request, relay, or emit a command."""
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(SKILL_ROOT.rglob("*"))
        if path.is_file() and path.suffix in TEXT_SUFFIXES and "__pycache__" not in path.parts
    )


def _windows_renderer():
    """Load the pure Windows renderer from the shipped source in isolation."""
    tree = ast.parse(WINDOWS_RENDERER_SOURCE.read_text(encoding="utf-8"))
    function = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_render_windows_command"
    )
    module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    namespace: dict[str, object] = {}
    exec(compile(module, str(WINDOWS_RENDERER_SOURCE), "exec"), namespace)  # noqa: S102
    return namespace["_render_windows_command"]


def test_skill_defines_fail_closed_installed_entry_contract() -> None:
    raw_skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    skill = " ".join(raw_skill.split())
    assert "actual\\nvalidated" not in raw_skill

    for phrase in (
        "installer-supplied directory",
        "Replace `<skill-dir>` with that actual",
        "never infer it from the current working directory",
        "regular file",
        "symlink loop",
        "remain beneath",
        "stop before launching",
        "discrete argument vector",
        "both quote characters",
        "$()",
        "backticks",
        "variable-shaped text",
        "refuse instead of invoking",
        "Interpret exit codes only after this preflight succeeds",
    ):
        assert phrase in skill


def test_every_entry_uses_resolved_form_and_no_bare_command_survives() -> None:
    surfaces = _surface_text()

    for entry in ENTRY_POINTS:
        assert f"<skill-dir>/scripts/{entry}" in surfaces
        bare = re.compile(rf"\b(?:python3?|node)\s+(?:\./)?scripts/{re.escape(entry)}\b")
        assert not bare.search(surfaces)


def test_resolution_diagnostic_is_bounded_and_not_remediation() -> None:
    skill = " ".join((SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8").split())

    assert "error: installed skill entry point is unavailable: <entry>" in skill
    assert "Do not expose an absolute, home, profile" in skill
    assert "do not relay raw runtime stderr" in skill
    assert "do not offer credential, SSO-capture, token, scope, or dependency remediation" in skill


def test_windows_renderer_refuses_cmd_and_powershell_expansion() -> None:
    render = _windows_renderer()
    fallback = "the installed entry.py entry point"
    safe = [r"C:\Program Files\Python\python.exe", r"C:\Agent Skills\scripts\entry.py"]
    assert render(safe, fallback) == (
        r'"C:\Program Files\Python\python.exe" '
        r'"C:\Agent Skills\scripts\entry.py"'
    )

    for unsafe in (
        "single'quote",
        'double"quote',
        "$()",
        "`command`",
        "$env:PROFILE",
        "%PROFILE%",
        "!PROFILE!",
    ):
        argv = [safe[0], rf"C:\Agent Skills\{unsafe}\scripts\entry.py"]
        assert render(argv, fallback) == f"{fallback} (use an argv-capable terminal)"


def test_runtime_help_uses_the_resolved_entry() -> None:
    entry = SKILL_ROOT / "scripts" / "linear.py"
    proc = subprocess.run(
        [sys.executable, "-B", str(entry), "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.returncode == 2 and "missing dependency" in proc.stderr:
        pytest.skip("runtime dependency is not installed")
    assert proc.returncode == 0
    assert str(entry.resolve()) in proc.stdout
    assert "<skill-dir>" not in proc.stdout


def test_linear_refresh_metadata_is_least_privilege() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "allowed-tools: Read Bash" in skill
    assert "credentialed: true" in skill
    assert "auth: creds" in skill
    assert "namespace: linear" in skill
    assert 'keys: ["API_KEY"]' in skill
    assert "network_fetch" in skill
    assert "filesystem_read_untrusted" in skill
    assert "filesystem_write" in skill.split("---", 2)[1]


def test_linear_brief_sync_is_compatibility_wrapper() -> None:
    skill = (SYNC_SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    compact = " ".join(skill.split())
    manifest = json.loads(
        (SYNC_SKILL_ROOT / "manifest.json").read_text(encoding="utf-8")
    )
    assert "compatibility skill" in compact
    assert "delegates refresh authority" in compact
    assert "configured `work-intake` Linear refresh processor" in compact
    assert "does not own a separate lifecycle or authority model" in compact
    assert "allowed-tools: Read Bash" in skill
    assert "Invoke `work-intake` by its skill name" in skill
    for private_sync_instruction in (
        "linear: get-issue",
        "## Status guard",
        "Re-fetch the Linear Issue",
        "Diff Linear-sourced fields",
        "Present for PE approval",
        "Write approved changes",
    ):
        assert private_sync_instruction not in skill
    assert [dependency["name"] for dependency in manifest["deps"]["skills"]] == [
        "work-intake"
    ]
    assert "re-fetch" not in manifest["description"].lower()
    assert manifest["output"]["artifacts"] == []


def test_linear_refresh_profile_matches_production_registration() -> None:
    profile = json.loads(
        (SKILL_ROOT / "references/refresh-profile.json").read_text(encoding="utf-8")
    )
    source = WINDOWS_RENDERER_SOURCE.read_text(encoding="utf-8")
    assert "def load_refresh_profile" in source
    assert "profile = load_refresh_profile()" in source
    assert profile["id"] == "linear-default"
    assert profile["version"] == "1.0"

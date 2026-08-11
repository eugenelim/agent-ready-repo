"""Source contract for installed skill entry-point resolution."""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[5]
SKILL_ROOT = REPO_ROOT / "packs" / "atlassian" / ".apm" / "skills" / "confluence-publisher"
ENTRY_POINTS = ("publish_page.py",)
TEXT_SUFFIXES = {".js", ".json", ".md", ".py", ".toml"}
WINDOWS_RENDERER_SOURCE = SKILL_ROOT / "scripts" / "publish_page.py"


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

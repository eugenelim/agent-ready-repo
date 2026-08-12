"""Source contract for installed skill entry-point resolution."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = PACK_ROOT / ".apm" / "skills" / "markdown-to-html"
ENTRY_POINTS = ("render.js",)
TEXT_SUFFIXES = {".js", ".json", ".md", ".py", ".toml"}


def _surface_text() -> str:
    """Return all shipped text that can teach, request, relay, or emit a command."""
    return "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(SKILL_ROOT.rglob("*"))
        if path.is_file() and path.suffix in TEXT_SUFFIXES and "__pycache__" not in path.parts
    )


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

    assert "npm --prefix '<skill-dir>' install" in surfaces
    assert "npm --prefix '<skill-dir>' ls" in surfaces
    assert 'npm --prefix "<skill-dir>"' not in surfaces
    assert not re.search(r"(?<![\w-])npm[ \t]+install\b", surfaces)


def test_resolution_diagnostic_is_bounded_and_not_remediation() -> None:
    skill = " ".join((SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8").split())

    assert "error: installed skill entry point is unavailable: <entry>" in skill
    assert "Do not expose an absolute, home, profile" in skill
    assert "do not relay raw runtime stderr" in skill
    assert "do not offer credential, SSO-capture, token, scope, or dependency remediation" in skill


def test_runtime_help_uses_the_resolved_entry_without_node_packages() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    entry = SKILL_ROOT / "scripts" / "render.js"
    proc = subprocess.run(
        [node, str(entry), "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0
    assert str(entry.resolve()) in proc.stdout
    assert "<skill-dir>" not in proc.stdout
    assert "missing dependency" not in proc.stderr


def test_windows_renderer_refuses_cmd_and_powershell_expansion() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    entry = SKILL_ROOT / "scripts" / "render.js"
    check = r"""
const render = require(process.argv[1]).renderWindowsCommand;
const fallback = 'the installed render.js entry point';
const safe = ['C:\\Program Files\\node.exe', 'C:\\Agent Skills\\scripts\\render.js'];
const expected = '"C:\\Program Files\\node.exe" "C:\\Agent Skills\\scripts\\render.js"';
if (render(safe, fallback) !== expected) process.exit(10);
for (const unsafe of ["single'quote", 'double"quote', '$()', '`command`',
                      '$env:PROFILE', '%PROFILE%', '!PROFILE!']) {
  const argv = [safe[0], `C:\\Agent Skills\\${unsafe}\\scripts\\render.js`];
  if (render(argv, fallback) !== `${fallback} (use an argv-capable terminal)`) {
    process.exit(11);
  }
}
"""
    proc = subprocess.run(
        [node, "-e", check, str(entry)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stderr


def test_dependency_hint_preserves_argv_and_quotes_shell_expansion_syntax() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("node is not installed")
    entry = SKILL_ROOT / "scripts" / "render.js"
    check = r"""
const render = require(process.argv[1]).dependencyInstallHint;
const tick = String.fromCharCode(96);
const hostile = '/tmp/skill"$()' + tick + 'command' + tick;
const expected = "'npm' '--prefix' '" + hostile + "' 'install'";
if (render(hostile, 'linux') !== expected) process.exit(10);
const fallback = "install this skill's npm dependencies from its installed directory";
if (render('C:\\Agent Skills\\$()\\skill', 'win32') !==
    `${fallback} (use an argv-capable terminal)`) process.exit(11);
"""
    proc = subprocess.run(
        [node, "-e", check, str(entry)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0, proc.stderr

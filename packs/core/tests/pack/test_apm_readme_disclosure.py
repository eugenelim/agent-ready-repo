"""Core pack README disclosure checks pending relocation."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]  # pack tests -> repository root


def _read_core_readme() -> str:
    return (REPO_ROOT / "packs" / "core" / "README.md").read_text(encoding="utf-8")


def test_core_readme_discloses_apm_manual_fallback():
    assert "agentbundle adapt --scope" in _read_core_readme()


def test_core_readme_names_four_covered_targets():
    body = _read_core_readme()
    for target in ("Claude Code", "Copilot", "Cursor", "Gemini"):
        assert target in body


def test_core_readme_names_three_uncovered_targets():
    body = _read_core_readme()
    for target in ("Codex", "OpenCode", "Windsurf"):
        assert target in body


def test_core_readme_disclosure_substrings_share_one_section():
    body = _read_core_readme()
    needed = {
        "Claude Code",
        "Copilot",
        "Cursor",
        "Gemini",
        "Codex",
        "OpenCode",
        "Windsurf",
        "agentbundle adapt --scope",
    }
    window_size = 1000
    assert any(
        all(item in body[start : start + window_size] for item in needed)
        for start in range(max(1, len(body) - window_size + 1))
    )

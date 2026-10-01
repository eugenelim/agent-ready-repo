"""AC-0009 and AC-0010 for the experience-design visual-target release.

Lives in tests/roster/ and not tests/conformance/: a conformance test may name
no shipped pack and may not reach docs/, and this one must do both.
tools/lint-conformance-portability.py enforces that on every pull request.
tests/AGENTS.md names tests/roster/ as the repository-level home.

Run mode: build-check.yml triggers on pull_request and its carve-out step runs
`python -m pytest tests/ -q`, so the PR gate runs this. No corpus dispatch is
needed.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]  # tests/roster/ -> repo root
PACK = REPO_ROOT / "packs" / "experience-design"
BASELINE = "4.1.1"


def _tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


# STUB: AC-0009, AC-0010  (spec: visual-target-field)
def test_release_surface_is_consistent() -> None:
    """visual-target-field AC-0009 and AC-0010."""
    pack = tomllib.loads((PACK / "pack.toml").read_text(encoding="utf-8"))
    version = pack["pack"]["version"]
    plugin = json.loads(
        (PACK / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    marketplace = json.loads(
        (REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
    )
    entry = next(
        item
        for item in marketplace["plugins"]
        if item.get("name") == "experience-design"
    )

    assert plugin["version"] == version, "AC-0009: plugin.json disagrees"
    assert entry.get("version") == version, "AC-0009: marketplace entry disagrees"
    assert _tuple(version) > _tuple(BASELINE), (
        f"AC-0009: {version} does not exceed the slice-start baseline {BASELINE}"
    )

    changelog = (REPO_ROOT / "docs" / "product" / "changelog.md").read_text(
        encoding="utf-8"
    )
    heading = f"## [experience-design][{version}]"
    starts = [
        line for line in changelog.splitlines() if line.startswith(heading)
    ]
    assert len(starts) == 1, (
        f"AC-0010: expected exactly one free-standing '## ' entry for {version}. "
        "A substring test would also accept a '### ' entry nested under "
        "[Unreleased], which never publishes."
    )
    body = changelog.split("\n" + heading, 1)[1].split("\n## ", 1)[0]
    assert "### Highlights" in body, "AC-0010: entry carries no Highlights"
    highlights = body.split("### Highlights", 1)[1].split("\n### ", 1)[0]
    bullets = [
        line for line in highlights.splitlines() if line.strip().startswith("- ")
    ]
    assert any("visual_target" in bullet for bullet in bullets), (
        "AC-0010: no Highlights bullet names visual_target. The /now/ projection "
        "extracts only bullets, so a paragraph is dropped silently."
    )

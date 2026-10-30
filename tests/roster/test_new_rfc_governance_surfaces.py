"""Cross-tree checks for the confined write helper's copies and its AGENTS.md entry.

`close-work`'s `file_safety.py` is the declared source. Pack scripts run from
their own projection, so every copy carries the same bytes; nothing regenerates
the hand-vendored ones, so this byte pin is what keeps them from drifting.
"""

from __future__ import annotations

import json
import re
import subprocess
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "packs/core/.apm/skills/close-work/scripts/file_safety.py"
COPY_NAME = re.compile(r"(?:^|/)_?file_safety\.py$")
MINIMUM_COPIES = 13


def _tracked_copies() -> list[str]:
    listed = subprocess.run(
        ["git", "ls-files", "--", "packs", "packages/agentbundle/agentbundle"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.splitlines()
    return [name for name in listed if COPY_NAME.search(name)]


def test_every_file_safety_copy_is_byte_identical_to_the_source() -> None:
    """Re-copy the source over a drifted copy when this fails."""
    copies = _tracked_copies()
    assert len(copies) >= MINIMUM_COPIES
    source = SOURCE.read_bytes()
    assert b"def write_confined_regular_file(" in source
    drifted = [name for name in copies if (REPO_ROOT / name).read_bytes() != source]
    assert drifted == []


def test_agents_md_names_the_confined_write_helper() -> None:
    text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    entry = text.split("Filesystem confinement:", 1)[1].split("\n- ", 1)[0]
    assert "write_confined_regular_file" in entry


GUIDE = REPO_ROOT / "guides/repo-governance/how-to/set-up-governance.md"
PREVIEW_PREFIXES = [
    "GOVERNANCE PREVIEW:",
    "- Target:",
    "- Kind:",
    "- Current:",
    "- Proposed:",
    "- Approval required:",
    "- Approved by:",
    "- Characters made visible:",
    "--- content ---",
    "--- end content ---",
]


def test_guide_forbids_a_standing_write_permission_and_is_listed() -> None:
    """AC-0062: the guide carries the sentence, and its README lists it."""
    text = GUIDE.read_text(encoding="utf-8")
    assert "Do not add a standing permission rule for the script's `write` command." in text
    readme = (REPO_ROOT / "guides/repo-governance/README.md").read_text(encoding="utf-8")
    assert "how-to/set-up-governance.md" in readme


def test_pack_manifests_carry_the_release_version() -> None:
    """AC-0096: parsed pack.toml and plugin.json carry 2.5.1."""
    root = REPO_ROOT / "packs/repo-governance"
    pack = tomllib.loads((root / "pack.toml").read_text(encoding="utf-8"))["pack"]
    plugin = json.loads((root / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    assert pack["version"] == "2.5.1"
    assert plugin["version"] == "2.5.1"


def test_guide_preview_block_follows_the_script_line_order() -> None:
    """The guide's preview block holds the preview lines in the script's order."""
    text = GUIDE.read_text(encoding="utf-8")
    block = text.split("GOVERNANCE PREVIEW:", 1)[1].split("```", 1)[0]
    lines = ["GOVERNANCE PREVIEW:", *block.splitlines()]
    found = [p for line in lines for p in PREVIEW_PREFIXES if line.startswith(p)]
    assert found == PREVIEW_PREFIXES

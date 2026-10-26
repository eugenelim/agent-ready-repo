"""Cross-tree checks for the confined write helper's copies and its AGENTS.md entry.

`close-work`'s `file_safety.py` is the declared source. Pack scripts run from
their own projection, so every copy carries the same bytes; nothing regenerates
the hand-vendored ones, so this byte pin is what keeps them from drifting.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "packs/core/.apm/skills/close-work/scripts/file_safety.py"
COPY_NAME = re.compile(r"(?:^|/)_?file_safety\.py$")
# The spec requires 13 copies once the new-rfc skill vendors its own; until that
# copy exists the count is 12.
MINIMUM_COPIES = 12


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

"""This repository's own pull-request form, and the guide that installs it.

These live outside the pack because a pack test may not read above its pack:
`.github/` and `guides/` are repository surfaces, not `core` content.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def _repo_root() -> Path:
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False,
    )
    return Path(out.stdout.strip()) if out.returncode == 0 else Path.cwd()


ROOT = _repo_root()
FORM = ROOT / ".github" / "pull_request_template.md"
GUIDE = ROOT / "guides" / "core" / "how-to" / "adapt-to-project.md"
ASSET = "pull-request-template.md"
DESTINATIONS = {
    ".github/pull_request_template.md",
    ".gitlab/merge_request_templates/Default.md",
}
TASK_LIST_MARKER = re.compile(r"^\s*- \[[ x]\]", re.M)


def _guide_section() -> str:
    text = GUIDE.read_text(encoding="utf-8")
    return text.split("## Install the pull-request template", 1)[1].split("\n## ", 1)[0]


# ------------------------------------------------------------------- AC-0009

def test_this_repositorys_form_carries_no_task_list_marker():
    assert not TASK_LIST_MARKER.search(FORM.read_text(encoding="utf-8"))


# ------------------------------------------------------------------- AC-0011

def test_the_guide_gives_one_copy_command_per_forge():
    commands = re.findall(r"^cp (\S+|\"[^\"]+\") (\S+)$", _guide_section(), re.M)
    assert len(commands) == 2
    sources = {src.strip('"') for src, _ in commands}
    assert len(sources) == 1
    source = sources.pop()
    assert source.endswith(f"work-loop/assets/{ASSET}")
    # Adapter-independent: the skills root is a variable, not `.agents` or
    # `.claude`, because the asset lands under whichever adapter is installed.
    assert source.startswith("$") or source.startswith("${")
    assert {dst for _, dst in commands} == DESTINATIONS


# --------------------------------------------------- deletion pin (no AC)

def test_the_guide_still_says_an_existing_convention_wins():
    """Deletion pin. Catches removal; does not certify wording."""
    assert "should keep it" in _guide_section()

"""Cross-tree parity: navigate-decisions vendors the blessed confinement helper.

Pack scripts run standalone from their projection, so `navigate-decisions`
carries its own `file_safety.py`. `close-work`'s copy is the declared source of
truth (see `test_architect_design_reviewer_projection.py`); nothing regenerates
this mirror, so this byte pin is what keeps it from drifting.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "packs/core/.apm/skills/close-work/scripts/file_safety.py"
MIRROR = (
    REPO_ROOT
    / "packs/governance-extras/.apm/skills/navigate-decisions/scripts/file_safety.py"
)


def test_navigate_decisions_file_safety_mirror_is_byte_identical() -> None:
    """Re-copy the source over the mirror when this fails."""
    assert MIRROR.read_bytes() == SOURCE.read_bytes()

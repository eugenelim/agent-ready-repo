"""Cross-tree parity: work-loop vendors close-work's cooling resolver.

`work-loop`'s dispatch reads lifecycle records without loading another skill, so
it carries its own `cooling.py` and the `close_work.py` that `cooling.py` loads
as a sibling. `close-work`'s copies are the source of truth; nothing regenerates
these mirrors, so this byte pin is what keeps them from drifting.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS = REPO_ROOT / "packs/core/.apm/skills"


@pytest.mark.parametrize("name", ["cooling.py", "close_work.py"])
def test_work_loop_cooling_mirror_is_byte_identical(name: str) -> None:
    """Re-copy the close-work source over the work-loop mirror when this fails."""
    source = SKILLS / "close-work" / "scripts" / name
    mirror = SKILLS / "work-loop" / "scripts" / name
    assert mirror.read_bytes() == source.read_bytes()

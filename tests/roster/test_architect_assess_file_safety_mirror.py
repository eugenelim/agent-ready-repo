"""Cross-tree parity: architect-assess carries a copy of the blessed confinement helper.

Pack scripts run standalone from their projection, so `architect-assess` ships its own
`file_safety.py` beside `render_html.py`. The agentbundle helper is the source; nothing
regenerates this copy, so this byte pin keeps it from drifting. It lives here, not in the pack
tree, because a pack test may not read above its own pack.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "packages/agentbundle/agentbundle/catalogue_tooling/file_safety.py"
COPY = REPO_ROOT / "packs/architect/.apm/skills/architect-assess/scripts/file_safety.py"


def test_architect_assess_file_safety_copy_is_byte_identical() -> None:
    """Re-copy the source over the copy when this fails."""
    assert COPY.read_bytes() == SOURCE.read_bytes()

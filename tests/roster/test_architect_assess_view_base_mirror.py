"""Cross-tree parity: architect-assess carries a copy of the shared view stylesheet.

The canonical `view-base.css` lives in navigate-intents. The architect report inlines a byte
copy beside its renderer, and nothing regenerates it, so this byte pin keeps it from drifting.
It lives here because a pack test may not read another pack's tree.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "packs/core/.apm/skills/navigate-intents/scripts/view_assets/view-base.css"
COPY = (
    REPO_ROOT / "packs/architect/.apm/skills/architect-assess/scripts/report_assets/view-base.css"
)


def test_architect_assess_view_base_copy_is_byte_identical() -> None:
    """Re-copy the canonical file over the copy when this fails."""
    assert COPY.read_bytes() == SOURCE.read_bytes()

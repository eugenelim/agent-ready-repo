"""Repository-specific minimum pack roster."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKS_DIR = REPO_ROOT / "packs"


def test_at_least_the_known_packs_are_present() -> None:
    present = {
        path.name
        for path in PACKS_DIR.iterdir()
        if path.is_dir()
        and not path.name.startswith("_")
        and (path / "pack.toml").exists()
    }
    assert {"core", "desk-research", "product-engineering"} <= present
    assert len(present) >= 12

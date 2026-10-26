"""AC-0006: the release archive carries the rename map byte for byte."""

from __future__ import annotations

import tarfile
from pathlib import Path

from agentbundle.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]
MAP = Path("contracts/renames/pack-renames.toml")


def test_archive_carries_the_map_unchanged(tmp_path: Path) -> None:
    out = tmp_path / "out"
    code = main([
        "catalogue", "package", "--root", str(REPO_ROOT), "--bundle", "demo",
        "--release", "0.1.0", "--channel", "stable", "--output", str(out),
    ])
    assert code == 0
    archive = out / "catalogues" / "demo" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    with tarfile.open(archive) as tar:
        names = [n for n in tar.getnames() if n.endswith(MAP.as_posix())]
        assert len(names) == 1, tar.getnames()[:20]
        member = tar.extractfile(names[0])
        assert member is not None
        assert member.read() == (REPO_ROOT / MAP).read_bytes()

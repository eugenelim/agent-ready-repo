"""AC-0006: the release archive carries the rename map byte for byte."""

from __future__ import annotations

import io
import subprocess
import tarfile
from pathlib import Path

from agentbundle.cli import main

REPO_ROOT = Path(__file__).resolve().parents[2]
MAP = Path("contracts/renames/pack-renames.toml")


def test_archive_carries_the_map_unchanged(tmp_path: Path) -> None:
    # Package a clean copy of the tracked tree so working-tree build
    # artefacts (for example __pycache__) cannot fail the package step.
    clean = tmp_path / "clean"
    clean.mkdir()
    archived = subprocess.run(
        ["git", "archive", "HEAD"], cwd=REPO_ROOT, capture_output=True, check=True
    ).stdout
    with tarfile.open(fileobj=io.BytesIO(archived)) as tracked:
        tracked.extractall(clean, filter="data")
    out = tmp_path / "out"
    code = main([
        "catalogue", "package", "--root", str(clean), "--bundle", "demo",
        "--release", "0.1.0", "--channel", "stable", "--output", str(out),
    ])
    assert code == 0
    archive = out / "catalogues" / "demo" / "releases" / "0.1.0" / "catalogue-0.1.0.tar.gz"
    with tarfile.open(archive) as tar:
        names = [n for n in tar.getnames() if n.endswith(MAP.as_posix())]
        assert len(names) == 1, tar.getnames()[:20]
        member = tar.extractfile(names[0])
        assert member is not None
        assert member.read() == (clean / MAP).read_bytes()

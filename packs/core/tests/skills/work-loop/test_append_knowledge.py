"""Compatibility coverage for the retired flat-JSONL writer."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[3]
    / ".apm/skills/work-loop/scripts/append-knowledge.py"
)


def test_retired_writer_refuses_without_creating_legacy_corpus(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--kind",
            "pattern",
            "--scope",
            "packs/core",
            "--title",
            "Retired path",
            "--body",
            "This input must not be persisted.",
            "--source",
            "local evidence",
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "project-knowledge --capture" in result.stderr
    assert not (tmp_path / "docs/knowledge/patterns.jsonl").exists()


def test_retired_writer_help_remains_discoverable() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Retired compatibility shim" in result.stdout

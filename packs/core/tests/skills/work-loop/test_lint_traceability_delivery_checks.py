# STUB: AC-0013
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

APM = Path(__file__).resolve().parents[3] / ".apm"
LINTER = APM / "skills" / "work-loop" / "scripts" / "lint-traceability.py"
BINS = APM / "adapter-root-bins"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_ac0013_diagnosed_spec_keeps_component_dangling_check(tmp_path: Path) -> None:
    for source in BINS.glob("*.py"):
        target = tmp_path / ".agentbundle" / "bin" / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    _write(tmp_path / "docs/product/briefs/anchor.md", "# Brief\n\n- **Slug:** `anchor`\n")
    _write(
        tmp_path / "docs/product/intents/alpha.md",
        "# Alpha\n\n- **Slug:** `alpha`\n- **Level:** feature\n- **Decomposed:** 2026-10-05 spec\n",
    )
    for slug in ("s1", "s2"):
        _write(
            tmp_path / f"docs/specs/{slug}/spec.md",
            f"# Spec: {slug}\n\n- **Status:** Draft\n- **Discovery:** `intent:alpha`\n"
            + ("- **Component:** ghost-comp\n" if slug == "s1" else ""),
        )

    proc = subprocess.run(
        [sys.executable, str(LINTER), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert proc.returncode == 1
    assert "ghost-comp" in proc.stderr

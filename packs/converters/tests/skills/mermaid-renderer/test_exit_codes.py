"""Pin Mermaid Renderer's published exit bands and dependency remediation."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = (
    PACK_ROOT
    / ".apm"
    / "skills"
    / "mermaid-renderer"
    / "scripts"
    / "render_mermaid.py"
)


def test_exit_constants_and_mmdc_remediation_are_stable() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    constants = {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id.startswith("EXIT_")
    }

    assert constants == {
        "EXIT_OK": 0,
        "EXIT_USER_ACTION": 2,
        "EXIT_PARTIAL": 1,
    }
    assert "NEED-INPUT: mmdc not found on PATH" in source
    assert "npm install -g @mermaid-js/mermaid-cli" in source


def test_runtime_help_uses_the_resolved_entry() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", str(SCRIPT), "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert proc.returncode == 0
    assert str(SCRIPT.resolve()) in proc.stdout
    assert "<skill-dir>" not in proc.stdout

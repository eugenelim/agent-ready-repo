"""PLAN-time contract stub for shaping-reviewer boundaries."""

import re
from pathlib import Path


CORE = Path(__file__).resolve().parents[2]
AGENT = CORE / ".apm" / "agents" / "shaping-reviewer.md"


def test_shaping_reviewer_declares_read_only_boundaries() -> None:
    """The new reviewer cannot gain authoring or retrieval authority."""
    # STUB: AC6
    assert AGENT.is_file()
    text = AGENT.read_text(encoding="utf-8")
    frontmatter_match = re.match(r"---\n(.*?)\n---\n", text, flags=re.DOTALL)
    assert frontmatter_match is not None
    frontmatter = frontmatter_match.group(1)
    tools_match = re.search(r"^tools:\s*(.+)$", frontmatter, flags=re.MULTILINE)
    assert tools_match is not None
    assert {tool.strip() for tool in tools_match.group(1).split(",")} == {
        "Read",
        "Grep",
        "Glob",
    }
    boundaries_match = re.search(
        r"^\s+boundaries:\s*\[([^]]+)\]$",
        frontmatter,
        flags=re.MULTILINE,
    )
    assert boundaries_match is not None
    assert {
        boundary.strip() for boundary in boundaries_match.group(1).split(",")
    } == {"filesystem_read_untrusted"}
    for prohibited in ("Bash", "Write", "Edit", "WebFetch", "WebSearch", "skills:"):
        assert prohibited not in frontmatter

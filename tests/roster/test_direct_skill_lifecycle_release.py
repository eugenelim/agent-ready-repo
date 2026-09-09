"""Release-surface assertions for the direct skill lifecycle."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE_SURFACES = (
    "packages/agentbundle/CHANGELOG.md",
    "packages/agentbundle/README-pypi.md",
    "docs/product/changelog.md",
)


def test_release_surfaces_name_only_moved_source_path_recovery() -> None:
    """Different-ref and moved-path refusals keep their distinct remedies."""

    expected = (
        "Remove-then-install is the terminating remediation for the "
        "moved-`source-path` collision."
    )
    stale = "terminating remediation for the two install refusals"
    for relative in RELEASE_SURFACES:
        text = (ROOT / relative).read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        assert expected in normalized, relative
        assert stale not in normalized, relative

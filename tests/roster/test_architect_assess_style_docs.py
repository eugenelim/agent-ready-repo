"""Docs and release surface of the architect-assess HTML report style.

These checks read the family token file, the guide, the parent spec, and the pack manifests,
which sit outside the pack tree, so they live with the roster tests.
"""

import json
import re
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOKENS = REPO_ROOT / "docs/design/tokens/skill-html-views.md"
GUIDE = REPO_ROOT / "guides/architect/reference/architecture-assessment.md"
PARENT_SPEC = REPO_ROOT / "docs/specs/architect-assess-html-report/spec.md"
PACK = REPO_ROOT / "packs/architect"


def _flat(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_token_file_records_the_report_view_rules() -> None:
    text = _flat(TOKENS)
    assert "`architect-assess`" in text.split("## Authority and route")[0]
    section = text.split("## Report view (`architect-assess`)")[1].split("## What may adapt")[0]
    assert "Layout-file colour rule" in section and "var(--c-" in section
    assert "Document density" in section
    for glyph in (
        "\u25ae\u25ae\u25ae",
        "\u25ae\u25ae\u25af",
        "\u25ae\u25af\u25af",
        "\u25af\u25af\u25af",
    ):
        assert glyph in section
    assert "ranking" in section
    assert "filled and the provenance pill is outlined on purpose" in section
    for level in ("low", "medium", "high", "unknown"):
        assert f"| {level} |" in section
    assert "none uses the ok, warn, bad, active or accent roles" in section
    assert "starts at 64rem" in _flat(TOKENS)
    for glyph in ("\u25d4", "\u25d1", "\u25d5"):
        assert glyph in section


def test_guide_states_the_style_and_the_rail() -> None:
    text = _flat(GUIDE)
    assert "maintainer-view style" in text and "contents rail" in text


def test_parent_spec_cites_the_style_spec_as_owner_of_the_lists() -> None:
    lines = PARENT_SPEC.read_text(encoding="utf-8").splitlines()
    owned = [
        line
        for line in lines
        if re.match(r"- \[.\] Every (element|attribute) in the parsed output", line)
    ]
    assert len(owned) == 2
    assert all("architect-assess-html-report-style" in line for line in owned)


def test_pack_versions_match_and_exceed_the_released_version() -> None:
    pack = tomllib.loads((PACK / "pack.toml").read_text(encoding="utf-8"))["pack"]["version"]
    plugin = json.loads((PACK / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))[
        "version"
    ]
    assert pack == plugin

    def as_tuple(version: str) -> tuple[int, ...]:
        return tuple(int(part) for part in version.split("."))

    assert as_tuple(pack) > (0, 15, 23)

"""Pins architect-design's physical architecture and BOM reference and asset."""

from __future__ import annotations

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[3] / ".apm/skills/architect-design"
SKILL = SKILL_DIR / "SKILL.md"
REFERENCE = SKILL_DIR / "references/physical-bom.md"
ASSET = SKILL_DIR / "assets/physical-architecture-bom.md"

BOM_COLUMNS = (
    "Line", "Deployment unit", "Kind", "Identifier", "Tier / size",
    "Qty", "Unit price", "Monthly", "Price status", "Source",
)  # fmt: skip


def _collapsed(path: Path) -> str:
    """Return the file text with whitespace collapsed."""
    return " ".join(path.read_text(encoding="utf-8").split())


def _step_7(text: str) -> str:
    """Return the text of procedure step 7."""
    return text.split("\n7. **", 1)[1].split("\n8. **", 1)[0]


def _headers(path: Path) -> list[list[str]]:
    """Return every table header row's cells in the file."""
    rows: list[list[str]] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for line, nxt in zip(lines, lines[1:], strict=False):
        if line.startswith("|") and nxt.startswith("| ---"):
            rows.append([c.strip() for c in line.strip("|").split("|")])
    return rows


def _missing(text: str, phrases: tuple[str, ...]) -> list[str]:
    """Return the phrases absent from the text."""
    return [p for p in phrases if p not in text]


AC_0004 = (
    "no deployment model gets no BOM",
    "offer to write the design first",
    "maps to at least one BOM line",
    "not costed with a reason",
)
AC_0013 = (
    "`cloud service`, `container image`,"
    " `open-source library`, `hardware`, `network connection`, or `licence`",
    "provider SKU and service identifier",
    "the tier",
    "registry URI",
    "package URL (purl) with version, plus SPDX licence identifier",
    "vendor model or part number",
    "CPU, memory, storage and network interface",
    "link type, both endpoints, and port or circuit identifier",
    "the bandwidth",
    "vendor product, edition and licence SKU",
    "`registry/repository:tag`",
    "`@sha256:",
    "only from evidence",
    "visible placeholder",
    "Never invent a URI or a digest",
    "version comes from a lock file or manifest, never from memory",
)
AC_0014 = (
    "`priced`",
    "`unpriced`",
    "`no direct cost`",
    "cites its source, date, and region",
    "out of the total and count them",
    "names the line that carries its cost",
    "states why the item is free to use",
    "SPDX identifier",
    "No price comes from model memory",
)
AC_0015 = ("delta BOM", "`Change` of add, remove, or resize", "net monthly change")


def test_ac_0004_step_7_offers_and_reference_gates_on_deployment_model() -> None:
    """AC-0004: step 7 names the reference; the reference states the gate."""
    step = " ".join(_step_7(SKILL.read_text(encoding="utf-8")).split())
    assert "references/physical-bom.md" in step
    assert "offer once" in step
    assert _missing(_collapsed(REFERENCE), AC_0004) == []


def test_ac_0013_line_identity_rules() -> None:
    """AC-0013: kinds, identifiers, and image URI rules are stated."""
    assert _missing(_collapsed(REFERENCE), AC_0013) == []


def test_ac_0014_price_status_rules() -> None:
    """AC-0014: price status values and grounding rules are stated."""
    assert _missing(_collapsed(REFERENCE), AC_0014) == []


def test_ac_0015_delta_bom_for_architecture_change() -> None:
    """AC-0015: the change altitude produces a delta BOM."""
    assert _missing(_collapsed(REFERENCE), AC_0015) == []


def test_ac_0005_asset_shape() -> None:
    """AC-0005: topology, mermaid, both BOM tables, and totals phrases."""
    text = ASSET.read_text(encoding="utf-8")
    headers = _headers(ASSET)
    assert list(BOM_COLUMNS) in headers
    assert [BOM_COLUMNS[0], "Change", *BOM_COLUMNS[1:]] in headers
    assert any(h[:2] == ["Environment", "Region / zone"] for h in headers)
    assert "```mermaid" in text
    totals = text.split("## 4. Totals", 1)[1].lower()
    for phrase in ("currency", "unpriced lines", "excluded costs", "net monthly change"):
        assert phrase in totals, phrase
    assert "<registry>/<repository>:<tag>" in text
    assert "no direct cost" in text
    for kind in ("open-source library", "hardware", "network connection"):
        assert f"| {kind} |" in text, kind
    assert "cloud resource" not in text


def test_mutation_dropping_unpriced_is_reported() -> None:
    """A reference with `unpriced` removed fails the AC-0014 pin."""
    mutated = _collapsed(REFERENCE).replace("unpriced", "")
    assert _missing(mutated, AC_0014) != []


def test_ac_0013_kinds_are_exactly_the_six_and_the_old_name_is_gone() -> None:
    """The retired `cloud resource` kind appears nowhere in the reference."""
    assert "cloud resource" not in _collapsed(REFERENCE)

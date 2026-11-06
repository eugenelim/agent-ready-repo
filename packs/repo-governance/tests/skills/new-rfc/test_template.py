"""Shape tests for the RFC template asset and its seeded copy."""

from __future__ import annotations

import re
from pathlib import Path

PACK = Path(__file__).resolve().parents[3]
ASSET = PACK / ".apm/skills/new-rfc/assets/rfc.md"
SEED = PACK / "seeds/docs/rfc/template.md.tmpl"

H2 = [
    "Summary",
    "Motivation",
    "Proposal",
    "Design details",
    "Costs and what could go wrong",
    "Alternatives",
    "How we will know it works",
    "Migration",
    "Open questions",
    "Evidence",
]
FIELDS = ["Status", "Author", "Date opened", "Date closed", "Decision weight", "Related"]


def _text() -> str:
    return ASSET.read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return " ".join(text.split())


def _outside_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def _section_comment(text: str, heading: str) -> str:
    match = re.search(rf"^{re.escape(heading)}\n\n<!--(.*?)-->", text, flags=re.S | re.M)
    assert match, heading
    return _flat(match.group(1))


def test_ac1_asset_and_seed_are_byte_identical() -> None:
    assert ASSET.read_bytes() == SEED.read_bytes()


def test_ac2_headings_in_order() -> None:
    body = _outside_comments(_text())
    assert re.findall(r"^## (.+)$", body, flags=re.M) == H2
    assert re.findall(r"^### (.+)$", body, flags=re.M) == ["Goals", "Non-goals"]
    motivation = body.index("## Motivation")
    assert (
        motivation
        < body.index("### Goals")
        < body.index("### Non-goals")
        < body.index("## Proposal")
    )


def test_ac3_header_fields_exact() -> None:
    body = _outside_comments(_text())
    assert re.findall(r"^- \*\*([^*]+):\*\*", body, flags=re.M) == FIELDS
    assert "Approver" not in _text()


def test_ac4_placeholder_cue_and_errata_scaffold() -> None:
    text = _text()
    assert "- **Author:** <account-handle>" in text
    assert "Write for a reader who has not read related RFCs" in text
    assert re.search(r"<!--[^>]*`## Errata`[^>]*`## Amendments`", text)


def test_ac5_decision_weight_line() -> None:
    line = next(x for x in _text().splitlines() if x.startswith("- **Decision weight:**"))
    assert "standard" in line.split("<!--")[0]
    for tier in ("light:", "standard:", "heavy:"):
        assert tier in line
    assert (
        "Use core's work-loop risk triggers when core is installed, otherwise these definitions"
        in line
    )


def test_ac6_header_comment_names_only_the_rfc_script() -> None:
    text = _text()
    header = _flat(text.split("- **Status:**")[0])
    assert "python3 -I docs/rfc/rfc.py" in header
    assert len(re.findall(r"\b[\w./-]+\.py\b", text)) == 1


def test_ac7_summary_and_proposal_comments() -> None:
    text = _text()
    summary = _section_comment(text, "## Summary")
    assert "two or three sentences" in summary and "why" in summary
    assert "one bullet per decision" in summary
    assert "End with any follow-on work" in _section_comment(text, "## Proposal")


def test_ac38_decider_is_a_suggestion() -> None:
    flat = _flat(_text())
    assert "a decider named inside an RFC is a suggestion" in flat
    assert "only the repository's rules and a listed maintainer's merge accept an RFC" in flat


def test_ac45_no_internal_identifiers() -> None:
    assert not re.search(r"\b(?:RFC|ADR)-\d", _text())

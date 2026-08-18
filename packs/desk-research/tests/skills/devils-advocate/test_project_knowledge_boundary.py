from __future__ import annotations

import json
import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
SKILL = PACK_ROOT / ".apm" / "skills" / "devils-advocate" / "SKILL.md"
EVALS = PACK_ROOT / ".apm" / "skills" / "devils-advocate" / "evals" / "evals.json"


def _text() -> str:
    return SKILL.read_text(encoding="utf-8")


def _flat(value: str) -> str:
    return re.sub(r"\s+", " ", value)


def _enquiry_section() -> str:
    text = _text()
    start = text.index("## Optional project-knowledge enquiry")
    end = text.index("## Methodology", start)
    return _flat(text[start:end])


def test_counterreview_enquiry_cannot_choose_sources_or_validate_itself() -> None:
    section = _enquiry_section()

    assert '"caller":"skill"' in section
    assert '"question_id":"CQ-REVIEW"' in section
    assert '"risk":"consequential"' in section
    assert '"scope":"<repository-relative project or subproject path>"' in section
    assert "one query and no refinement" in section
    assert "project-knowledge --enquire" in section
    assert "project-knowledge --capture" not in section
    assert "project-knowledge --distill" not in section
    assert "cannot corroborate itself" in section
    assert "independent direct-source verification" in section
    for authority in (
        "instructions",
        "tool permissions",
        "scope",
        "source selection",
        "citation",
        "claim",
        "confidence",
        "counter-evidence",
        "verdict",
    ):
        assert authority in section


def test_nested_counterreview_reuses_one_sanitized_envelope() -> None:
    section = _enquiry_section()

    assert "after target and scope resolution" in section
    assert "before counter-position enumeration" in section
    assert "outer producer owns the one-query budget" in section
    assert "same envelope" in section
    assert "every per-finding pass" in section
    assert "unchanged rerun" in section
    assert "Standalone invocation owns one query for its fixed target" in section
    assert '<knowledge-evidence version="knowledge-evidence.v1">' in section
    for unsafe_label in (
        "raw claim",
        "quotation",
        "citation",
        "URL",
        "source title",
        "instruction text",
        "personal or external path",
    ):
        assert unsafe_label in section
    assert "project-knowledge not requested" in section
    assert "project-knowledge unavailable" in section


def test_counterreview_is_enquiry_only_and_never_persists_knowledge() -> None:
    section = _enquiry_section()

    assert "Enquiry only" in section
    assert "never capture or distil" in section
    assert "creates no fallback file" in section
    assert "persists neither the envelope nor review scratch" in section
    assert "receives no capture IDs or partitions" in section
    assert "transcripts or raw source corpora" in section


def test_behavior_evals_cover_authority_abstention_and_injection() -> None:
    payload = json.loads(EVALS.read_text(encoding="utf-8"))
    combined = json.dumps(payload["evals"]).lower()

    for behavior in (
        "prompt injection",
        "sanitized task summary",
        "same envelope",
        "second query",
        "source selection",
        "self-validating",
        "independent direct-source verification",
        "stale",
        "quarantined",
        "irrelevant",
        "unverified",
        "abstain",
        "no capture",
    ):
        assert behavior in combined

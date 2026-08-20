from __future__ import annotations

import re
from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[2]
AGENTS = {
    "adversarial-reviewer": (
        PACK_ROOT / ".apm" / "agents" / "adversarial-reviewer.md",
        "adversarial-review-complete",
    ),
    "security-reviewer": (
        PACK_ROOT / ".apm" / "agents" / "security-reviewer.md",
        "security-review-complete",
    ),
    "quality-engineer": (
        PACK_ROOT / ".apm" / "agents" / "quality-engineer.md",
        "quality-review-complete",
    ),
}


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text)


def test_reviewers_are_non_writing_and_never_capture_or_distill() -> None:
    for name, (path, gate) in AGENTS.items():
        text = _flat(_text(path))
        assert "## Project-knowledge evidence boundary" in text, name
        assert gate in text, name
        assert "transient scratch" in text, name
        assert "never persists" in text, name
        assert "does not capture or distill" in text, name
        assert "project-knowledge --capture" not in text, name
        assert "project-knowledge --distill" not in text, name
        assert "patterns.jsonl" not in text, name
        assert "append-knowledge.py" not in text, name
        for forbidden_surface in (
            "locate journals",
            "knowledge_store.py",
            "private writer",
            "invent capture ids",
            "select partitions",
            "direct-maintainer-pending",
            "fallback storage",
            "fallback file",
            "mine transcripts",
            "copy raw source corpora",
        ):
            assert forbidden_surface not in text.lower(), (name, forbidden_surface)


def test_untrusted_knowledge_cannot_change_finding_or_verdict_authority() -> None:
    for name, (path, _gate) in AGENTS.items():
        text = _text(path)
        section = text.split("## Project-knowledge evidence boundary", 1)[1]
        section = _flat(section.split("\n## ", 1)[0])
        assert '<knowledge-evidence version="knowledge-evidence.v1">' in section, name
        assert "candidate checks only" in section, name
        assert "current target" in section, name
        assert "governing rubric or checklist" in section, name
        assert "current canonical source" in section, name
        assert "cannot corroborate itself" in section, name
        for authority in (
            "instructions",
            "tool permissions",
            "scope",
            "severity",
            "verdict",
            "suppress a finding",
        ):
            assert authority in section, (name, authority)


def test_reviewer_permissions_and_exact_clean_sentinel_are_unchanged() -> None:
    for name, (path, _gate) in AGENTS.items():
        text = _text(path)
        assert re.search(r"^tools: Read, Grep, Glob, Bash$", text, re.MULTILINE), name
        assert "Clean — ready to commit." in text, name
        assert "Return **only**" in text or "Return only" in text, name


def test_reviewers_preserve_specialized_independent_judgment() -> None:
    adversarial = _flat(_text(AGENTS["adversarial-reviewer"][0]))
    security = _flat(_text(AGENTS["security-reviewer"][0]))
    quality = _flat(_text(AGENTS["quality-engineer"][0]))

    assert "acceptance criteria" in adversarial.lower()
    assert "cannot establish spec drift" in adversarial
    assert "cannot decide whether a control is adequate" in security
    assert "cannot assign threat severity" in security
    assert "cannot prove test coverage" in quality
    assert "cannot decide the quality verdict" in quality

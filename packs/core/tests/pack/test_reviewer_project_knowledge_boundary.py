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


def test_reviewers_self_test_against_adjudicator_predicates() -> None:
    """Require findings to expose the evidence gap rather than disappear."""
    heading = "### Predicate self-check before emission"
    for name, (path, _gate) in AGENTS.items():
        text = _text(path)
        assert heading in text, name
        # Scope the predicate list to its own section. "authority",
        # "existing handling", and "reachability" all occur in unrelated
        # reviewer prose, so a whole-file search would still pass with the
        # list deleted.
        section = _flat(text.split(heading, 1)[1].split("\n## ", 1)[0])
        assert "finding-adjudicator's six predicates" in section, name
        for predicate in (
            "observation",
            "authority",
            "reachability",
            "existing handling",
            "consequence",
            "proposed mechanism",
        ):
            assert predicate in section, (name, predicate)
        assert "untraced consequence" in section, name
        assert "downgraded with that gap named" in section, name
        # The self-check exists to make findings carry their evidence, never to
        # emit fewer of them. Without these two, an edit could keep every
        # phrase above while turning the section into a suppression path.
        assert "still emits" in section, name
        # adversarial-reviewer ties this to its closed suppressible list;
        # the other two state it directly. Either discharges the constraint.
        assert (
            "does not add a suppressible category" in section
            or "it is not suppressed" in section
        ), name


def test_predicate_self_check_does_not_weaken_flagging() -> None:
    """Pin the calibration constraint: carry more evidence, not flag less."""
    adversarial = _text(AGENTS["adversarial-reviewer"][0])
    flat = _flat(adversarial)

    # The measured refutations were confident findings with untraced
    # consequences, not doubt-hedged ones, so removing this instruction would
    # not have prevented any of them.
    assert "**When in doubt, flag.**" in flat

    # The suppressible list must stay closed, and the new section must not
    # become an entry in it.
    assert "the complete enumeration of suppressible categories" in flat
    assert "anything not on this list is not suppressible" in flat
    assert "this does not add a suppressible category" in flat


def test_security_report_always_includes_not_checked_footer() -> None:
    """Keep the anti-silent-gap footer in both finding and clean reports."""
    text = _text(AGENTS["security-reviewer"][0])
    report = text.split("## Report numbered findings", 1)[1].split(
        "## Honest about your limits", 1
    )[0]
    assert "## Not checked" in report
    assert "<issue class not checked and why>" in report
    # Flatten before matching: pinning the prose at its current line wrap
    # would redden on any reflow of a paragraph this test does not own.
    assert "followed in either case by the `## Not checked` footer" in _flat(report)


def test_active_work_loop_has_no_reviewer_knowledge_enquiry() -> None:
    """Keep captured knowledge outside reviewer dispatch and review evals."""
    skill = _text(PACK_ROOT / ".apm" / "skills" / "work-loop" / "SKILL.md")
    evals = _text(
        PACK_ROOT / ".apm" / "skills" / "work-loop" / "evals" / "evals.json"
    )
    assert "CQ-REVIEW" not in skill
    assert "project-knowledge --enquire" not in skill
    assert "knowledge-evidence" not in skill
    # Guard the eval payload, not just the id prefix: a retained review-time
    # enquiry eval renamed off "review-enquiry-" would still train the
    # behaviour this change removes.
    assert "review-enquiry-" not in evals
    assert "CQ-REVIEW" not in evals
    assert "knowledge-evidence" not in evals
    assert "enquiry seam" not in evals
    # Reviewer dispatch must still name its inputs, and must not reacquire the
    # envelope. Flattened so a reflow of the paragraph cannot redden this.
    dispatch = _flat(skill)
    assert (
        "Select a subagent matching `adversarial-reviewer`. Pass the diff and spec path."
        in dispatch
    )

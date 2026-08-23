"""Focused repository-idiom delta contracts for review surfaces."""

from pathlib import Path

PACK_ROOT = Path(__file__).resolve().parents[3]
PRE_EXECUTE = PACK_ROOT / ".apm/skills/work-loop/references/pre-execute-review.md"
ADVERSARIAL = PACK_ROOT / ".apm/agents/adversarial-reviewer.md"
QUALITY = PACK_ROOT / ".apm/agents/quality-engineer.md"


def _compact(path: Path) -> str:
    return " ".join(path.read_text(encoding="utf-8").split())


def test_all_review_surfaces_use_the_same_idiom_delta_finding() -> None:
    phrase = (
        "This proposal introduces X. A mapped repository source or canonical "
        "production example uses Y for the same responsibility. Confirm or "
        "justify the deviation."
    )
    for path in (PRE_EXECUTE, ADVERSARIAL, QUALITY):
        assert phrase in _compact(path), path


def test_idiom_delta_is_limited_to_load_bearing_mechanisms() -> None:
    for path in (PRE_EXECUTE, ADVERSARIAL, QUALITY):
        text = _compact(path)
        assert "load-bearing structural mechanism" in text
        assert "one incidental neighboring file" in text
        assert "cosmetic uniformity" in text
        assert "product scope" in text
        assert "core pack's file layout" in text


def test_reviewers_independently_inspect_only_when_assurance_is_weak() -> None:
    for path in (ADVERSARIAL, QUALITY):
        text = _compact(path)
        assert "Convergent, Tentative, Contradictory, unavailable, or outcome-critical" in text
        assert "independently inspect" in text
        assert "Strong Explicit or Framework-owned" in text

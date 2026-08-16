"""Construction test for work-intake dispatch guards."""

from pathlib import Path

_WORK_LOOP = (
    Path(__file__).resolve().parents[3]
    / ".apm"
    / "skills"
    / "work-loop"
    / "SKILL.md"
)


def test_missing_contract_fails_closed() -> None:
    body = _WORK_LOOP.read_text(encoding="utf-8")
    assert "canonical.ready" in body
    assert "canonical.active" in body
    assert "missing_plan" in body
    assert "unapproved_spec" in body
    assert "never reconstruct" in body.lower()

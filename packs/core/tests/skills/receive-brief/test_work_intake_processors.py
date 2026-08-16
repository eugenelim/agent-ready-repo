"""Construction tests for work-intake processor boundaries."""

from pathlib import Path

_SKILLS = Path(__file__).resolve().parents[3] / ".apm" / "skills"


def _body(name: str) -> str:
    return (_SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def test_ready_brief_without_specs() -> None:
    body = _body("receive-brief")
    assert "zero specs" in body
    assert "Ready" in body
    assert "placeholder" not in body or "not required" in body


def test_only_confirmed_slices_materialize() -> None:
    body = _body("receive-brief")
    assert "confirmed slice" in body
    assert "new-spec" in body
    assert "ask" in body.lower() or "confirm" in body.lower()


def test_processor_boundary_metadata() -> None:
    for name in ("author-brief", "receive-brief", "new-spec"):
        body = _body(name)
        assert "metadata:" in body, name
        assert "boundaries:" in body, name
        assert "allowed-tools:" in body, name
